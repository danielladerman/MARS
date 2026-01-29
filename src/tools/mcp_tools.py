"""
MCP Tool integrations for the Strategic Intelligence workflow.

Connects to the LyzrToolBox MCP server via Streamable HTTP transport.
Server URL: https://web-dan.up.railway.app/
"""
import httpx
import json
from typing import Any
from langchain_core.tools import tool


# ============================================================
# MCP SERVER CONFIGURATION
# ============================================================

# Primary server (competitive analysis tools)
MCP_SERVER_DAN = "https://web-dan.up.railway.app"

# Secondary server (visualization and audience tools)
MCP_SERVER_ADITI = "https://web-aditi.up.railway.app"

# Legacy alias
MCP_SERVER_URL = MCP_SERVER_DAN


class MCPClient:
    """HTTP client for calling MCP tools via Streamable HTTP transport with session management."""

    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url.rstrip("/")
        self.session_id = None
        self._request_id = 0

    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    def _parse_sse_response(self, text: str) -> dict:
        """Parse SSE format response to extract JSON data."""
        # SSE format: event: message\ndata: {...}\n\n
        for line in text.split('\n'):
            if line.startswith('data: '):
                try:
                    return json.loads(line[6:])
                except json.JSONDecodeError:
                    pass
        # Try parsing as plain JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": f"Failed to parse response: {text[:200]}"}

    async def _ensure_session(self, client: httpx.AsyncClient) -> None:
        """Initialize MCP session if not already done."""
        if self.session_id:
            return

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        init_payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-01-15",
                "capabilities": {},
                "clientInfo": {
                    "name": "langgraph-mcp-client",
                    "version": "1.0.0"
                }
            }
        }

        response = await client.post(self.base_url, json=init_payload, headers=headers)
        response.raise_for_status()

        self.session_id = response.headers.get("mcp-session-id")
        if not self.session_id:
            raise Exception("Failed to obtain MCP session ID")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] = None) -> Any:
        """
        Call an MCP tool via HTTP POST.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Ensure we have a session
            await self._ensure_session(client)

            # MCP Streamable HTTP requires both Accept types and session ID
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": self.session_id
            }

            payload = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                }
            }

            response = await client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()

            # Parse SSE response
            result = self._parse_sse_response(response.text)

            if "error" in result:
                raise Exception(f"MCP Error: {result['error']}")

            return result.get("result", result)


# Global MCP client instances
mcp_client_dan = MCPClient(MCP_SERVER_DAN)
mcp_client_aditi = MCPClient(MCP_SERVER_ADITI)

# Legacy alias
mcp_client = mcp_client_dan


def get_mcp_client() -> MCPClient:
    """Get the primary MCP client instance (web-dan)."""
    return mcp_client_dan


def get_mcp_client_aditi() -> MCPClient:
    """Get the secondary MCP client instance (web-aditi)."""
    return mcp_client_aditi


def get_mcp_tools() -> list:
    """Get all available MCP tools."""
    return get_manager1_tools() + get_manager2_tools()


# ============================================================
# MANAGER 1 TOOLS (Competitive Analyzer)
# ============================================================

@tool
async def merge_brand_indices(
    min_valid_brands: int = 1,
    include_json_output: bool = True,
    include_markdown_tables: bool = True,
    output_format: str = "simple",
    generate_png_table: bool = True
) -> str:
    """
    Agent 1.1: Data Merger Tool

    Merges 10 brand CEP index reports (M&M's + 9 competitors) and performs
    comparative analysis. Returns PNG URL of the CEP table and JSON with
    all CEPs and brand indices.

    Returns:
        Markdown tables with brand comparison and JSON output
    """
    result = await mcp_client.call_tool("merge_brand_indices", {
        "min_valid_brands": min_valid_brands,
        "include_json_output": include_json_output,
        "include_markdown_tables": include_markdown_tables,
        "output_format": output_format,
        "generate_png_table": generate_png_table
    })

    # Extract text from MCP response
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and len(content) > 0:
            return content[0].get("text", str(result))
    return str(result)


@tool
async def analyze_cep_performance(
    cep_data: list[dict[str, Any]],
    include_json_output: bool = True
) -> str:
    """
    Agent 1.2: CEP Prioritizer Tool

    Analyzes Category Entry Points and clusters them into White Space,
    Winning, Underperforming, and Parity groups based on M&M's performance
    vs competitors.

    Args:
        cep_data: Array of CEP records with 'cep', 'mnms_index', and 'competitor_indices'

    Returns:
        Formatted tables with CEP clusters, summary statistics, and JSON output
    """
    result = await mcp_client.call_tool("analyze_cep_performance", {
        "cep_data": cep_data,
        "include_json_output": include_json_output
    })

    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and len(content) > 0:
            return content[0].get("text", str(result))
    return str(result)


@tool
async def build_cep_analysis_slide(
    chart_image_url: str,
    insights: list[str],
    slide_title: str = "CEP Analysis and Insights",
    dark_theme: bool = True
) -> str:
    """
    Agent 1.5: CEP Slide Builder Tool

    Creates PowerPoint slide with CEP scatter plot and strategic insights.

    Args:
        chart_image_url: URL to the visualization PNG
        insights: 4 key strategic insights as array

    Returns:
        Success message with slide URL
    """
    result = await mcp_client.call_tool("build_cep_analysis_slide", {
        "chart_image_url": chart_image_url,
        "insights": insights,
        "slide_title": slide_title,
        "dark_theme": dark_theme
    })

    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and len(content) > 0:
            return content[0].get("text", str(result))
    return str(result)


# ============================================================
# VISUALIZATION TOOLS (from web-aditi server)
# ============================================================

@tool
async def create_index_visual() -> str:
    """
    Agent 1.4: Index Visualizer Tool

    Creates scatter plot visualizations for brand indices across Category Entry Points.
    Generates PNG and PDF visualizations showing which brands are performing above
    or below category average at each CEP.

    Positive values indicate better-than-average performance.
    Negative values indicate below-average performance.

    Returns:
        URLs to generated PNG and PDF visualizations
    """
    result = await mcp_client_aditi.call_tool("index_visual", {})

    # Extract text from MCP response
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and len(content) > 0:
            return content[0].get("text", str(result))
    return str(result)


@tool
async def get_demo_audiences() -> str:
    """
    Agent 2.2: Audience Data Tool

    Filters and displays audience index data from GROW, RECRUIT, and SWITCH segments.
    Returns index reports for each audience with indices for each attribute and
    percentage of the audience with the attribute.

    Returns:
        Audience attribute data for all three segments
    """
    result = await mcp_client_aditi.call_tool("demo_audiences", {})

    # Extract text from MCP response
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and len(content) > 0:
            return content[0].get("text", str(result))
    return str(result)


# ============================================================
# MANAGER 2 TOOLS (Audience-to-Creative)
# ============================================================

@tool
async def analyze_audience_cep_priorities(
    threshold: int = 120,
    include_json_output: bool = True
) -> str:
    """
    Agent 2.1: Audience CEP Analyzer Tool

    Analyzes Category Entry Points by audience segment (Switch, Recruit, Grow).
    Identifies priority CEPs (Index > threshold) for each segment.

    Args:
        threshold: Minimum index value to qualify as priority CEP (default 120)

    Returns:
        Formatted tables with priority CEPs by segment and JSON output
    """
    result = await mcp_client.call_tool("analyze_audience_cep_priorities", {
        "threshold": threshold,
        "include_json_output": include_json_output
    })

    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and len(content) > 0:
            return content[0].get("text", str(result))
    return str(result)


@tool
async def build_audience_strategy_slides(
    segments: list[dict[str, Any]],
    below_threshold_slide: dict[str, Any],
    presentation_title: str = "Strategic Audience-CEP-Creative Insights"
) -> str:
    """
    Agent 2.3: Audience Creative Slide Builder Tool

    Creates professional PowerPoint presentation with 4 slides showing
    Strategic Audience-CEP-Creative insights.

    Args:
        segments: Array of 3 audience segments (SWITCH, RECRUIT, GROW)
                  with key_attributes and ceps
        below_threshold_slide: Data for fourth slide with below-threshold CEPs

    Returns:
        Success message with presentation URL
    """
    result = await mcp_client.call_tool("build_audience_strategy_slides", {
        "segments": segments,
        "below_threshold_slide": below_threshold_slide,
        "presentation_title": presentation_title
    })

    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and len(content) > 0:
            return content[0].get("text", str(result))
    return str(result)


# ============================================================
# TOOL COLLECTIONS FOR AGENTS
# ============================================================

def get_manager1_tools() -> list:
    """Get all tools for Manager 1 (Competitive Analyzer) agents."""
    return [
        merge_brand_indices,
        analyze_cep_performance,
        create_index_visual,
        build_cep_analysis_slide,
    ]


def get_manager2_tools() -> list:
    """Get all tools for Manager 2 (Audience-to-Creative) agents."""
    return [
        analyze_audience_cep_priorities,
        get_demo_audiences,
        build_audience_strategy_slides,
    ]


async def get_all_tools_for_agent(agent_type: str) -> list:
    """
    Get relevant tools for a specific agent type.

    Args:
        agent_type: One of:
            - 'data_merger' (1.1)
            - 'cep_prioritizer' (1.2)
            - 'visualizer' (1.4) - uses merge_brand_indices PNG
            - 'slide_builder' (1.5)
            - 'audience_cep' (2.1)
            - 'audience_data' (2.2)
            - 'audience_slide' (2.3)

    Returns:
        List of tools for the agent
    """
    tool_mapping = {
        "data_merger": [merge_brand_indices],
        "cep_prioritizer": [analyze_cep_performance],
        "visualizer": [create_index_visual],  # Uses web-aditi index_visual tool
        "slide_builder": [build_cep_analysis_slide],
        "audience_cep": [analyze_audience_cep_priorities],
        "audience_data": [get_demo_audiences],  # Uses web-aditi demo_audiences tool
        "audience_slide": [build_audience_strategy_slides],
    }

    return tool_mapping.get(agent_type, [])


# ============================================================
# LEGACY EXPORTS (for backwards compatibility)
# ============================================================

# These are kept for any imports that reference the old names
extract_brand_data = merge_brand_indices
analyze_cep_data = analyze_cep_performance
generate_visualizations = merge_brand_indices
build_cep_slide = build_cep_analysis_slide
extract_audience_data = analyze_audience_cep_priorities
build_audience_slide = build_audience_strategy_slides
