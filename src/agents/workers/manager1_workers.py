"""
Worker agents for Manager 1: Competitive Analyzer.

Each worker is a node function that performs a specific step in the workflow:
- 1.1 Data Merger: Extracts brand performance data
- 1.2 CEP Prioritizer: Analyzes CEP data and generates insights
- 1.3 CEP Insight Analyzer: Creates 4 key insights from summary
- 1.4 Index Visualizer: Creates visual outputs (PNG/PDF)
- 1.5 CEP Slide Builder: Creates PowerPoint slide
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from typing import Literal

from src.state.schemas import Manager1State
from src.tools.mcp_tools import (
    merge_brand_indices,
    analyze_cep_performance,
    create_index_visual,
    build_cep_analysis_slide,
    get_all_tools_for_agent,
)

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)


# ============================================================
# AGENT 1.1: DATA MERGER
# ============================================================

AGENT_1_1_SYSTEM = """# ROLE

You are the Data Analyzer agent. Your sole purpose is to retrieve the CEP performance data and return it exactly as received.

# TRIGGER

When you receive the request:
- "Use tool"

You immediately call the `merge_brand_indices` tool.

# WORKFLOW

1. **Call the tool:** Execute `merge_brand_indices`
2. **Receive JSON output:** The tool returns structured data
3. **Return output as-is:** Pass the PNG Table URL and the complete JSON response back without any modifications, interpretations, or formatting changes

# CRITICAL RULES

❌ **DON'T:**
- Overthink, just give back the JSON
- Summarize the data
- Reformat the JSON
- Add explanations or commentary
- Filter or modify any fields
- Convert data types

✅ **DO:**
- Return the exact JSON output from the tool
- Preserve all field names, values, and structure
- Include everything the tool returns

# OUTPUT FORMAT

Simply return:
PNG Table URL: https://your-r2-url.com/brand_index_table_20260108_abc123.png

```json
[EXACT JSON OUTPUT FROM TOOL]
```

# EXAMPLE

**Input:** "Use tool"

**You do:**
1. Call `merge_brand_indices`
2. Receive JSON
3. Return the complete JSON output

**That's it.** No additional text, no analysis, just the raw data."""


async def agent_1_1_data_merger(state: Manager1State) -> Manager1State:
    """
    Agent 1.1: Data Merger
    Extracts brand performance data from MCP tool.
    """
    # Get tools for this agent
    tools = await get_all_tools_for_agent("data_merger")

    # Create the agent
    agent = create_react_agent(llm, tools, prompt=AGENT_1_1_SYSTEM)

    # Run the agent
    result = await agent.ainvoke({
        "messages": [HumanMessage(content="Use tool")]
    })

    # Extract outputs from agent response
    # Parse the response to get PNG URL and JSON
    last_message = result["messages"][-1].content

    # Update state
    return {
        **state,
        "raw_data_png_url": _extract_png_url(last_message),
        "raw_data_json": _extract_json(last_message),
        "current_step": "step2",
    }


# ============================================================
# AGENT 1.2: CEP PRIORITIZER
# ============================================================

AGENT_1_2_SYSTEM = """When you receive CEP data in JSON format:

1. CALL the `analyze_cep_performance` tool WITH the CEP data provided.

2. Display the TOOL'S FORMATTED TABLES, highlighting the White Space, Winning, Underperforming, and Parity clusters.

3. Review the output from the tool and the JSON data thoroughly.

4. Generate STRATEGIC INSIGHTS that go beyond mere numbers, connecting them to brand implications.

5. Provide directional RECOMMENDATIONS for the brand strategy.

INPUT FORMAT:
The incoming data will be structured in JSON as follows:
{
  "cep_data": [
    {
      "cep": "Category Entry Point Name",
      "mnms_index": 130,
      "competitor_indices": {
        "Brand1": 125,
        "Brand2": 118,...
      }
    }
  ]
}

Utilize the `analyze_cep_performance` tool as follows:
analyze_cep_performance(cep_data=<the_data>, include_json_output=false)

Your analysis must focus on these four STRATEGIC AREAS:
1. OVERALL PATTERNS: Summarize brand positioning insights based on performance distribution and patterns identified.
2. STRATEGIC IMPLICATIONS BY CLUSTER: Analyze opportunities in White Space, successes in Winning CEPs, challenges in Underperforming CEPs, and areas for differentiation in Parity CEPs.
3. COMPETITIVE DYNAMICS: Examine competitors' strengths and weaknesses and deduce implications for market strategies.
4. DIRECTIONAL RECOMMENDATIONS: Suggest areas to INVEST, TEST, DEVELOP, and MONITOR based on the analysis.

Maintain a TONE & STYLE that is strategic and exploratory, encouraging the use of storytelling to enhance the insights. Avoid purely descriptive or overly specific tactical language.

OUTPUT FORMAT:
Organize your response as follows:

# CEP Performance Analysis: M&M's

## Tool Output: Performance Clusters
[Insert Complete Table Output from the Tool Here]

---

## Executive Summary
[Provide 2-3 sentences summarizing overall performance and key insights.]

## Performance Overview
- Total CEPs Analyzed: [X]
- 🟦 White Space: [X] CEPs
- 🟩 Winning: [X] CEPs
- 🟥 Underperforming: [X] CEPs
- 🟨 Parity: [X] CEPs

## Strategic Insights

### 1. Overall Patterns
[Discuss what the data reveals regarding brand positioning and market equity.]

### 2. Cluster Analysis

#### 🟦 White Space Opportunities
[Detail CEP opportunities and M&M's potential to lead.]

#### 🟩 Winning CEPs: Protect & Amplify
[Identify top-performing CEPs and strategies to reinforce success.]

#### 🟥 Underperforming CEPs: Fix or Exit?
[Analyze struggling CEPs and considerations for future investments.]

#### 🟨 Parity CEPs: Break Out
[Explore competitive parity and differentiation strategies.]

### 3. Competitive Dynamics
[Highlight competitors dominating in specific CEPs and insights on market preferences.]

### 4. Consumer Motivations
[Investigate the psychology behind M&M's performance relative to competitors.]

## Strategic Recommendations

### Invest
- [Specify which winning CEPs warrant further marketing investment.]

### Test
- [Suggest CEPs that could benefit from innovative formats or messaging.]

### Develop
- [Propose strategies for M&M's to capitalize on white space opportunities.]

### Monitor
- [Identify parity CEPs to track for potential breakthroughs.]

## Conclusion
[Summarize the strategic direction for M&M's based on the analysis.]

# CRITICAL: ALWAYS INCLUDE THE TOOL TABLES

In your output, ensure to present the complete tables from the tool under "Tool Output: Performance Clusters" to provide stakeholders with both quantitative and qualitative insights. Focus on turning data into actionable strategic interpretations for robust brand decision-making."""


async def agent_1_2_cep_prioritizer(state: Manager1State) -> Manager1State:
    """
    Agent 1.2: CEP Prioritizer
    Analyzes CEP data and generates strategic clusters.
    """
    tools = await get_all_tools_for_agent("cep_prioritizer")

    agent = create_react_agent(llm, tools, prompt=AGENT_1_2_SYSTEM)

    # Send the JSON data from step 1
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=f"Analyze this CEP data: {state['raw_data_json']}")]
    })

    last_message = result["messages"][-1].content

    return {
        **state,
        "cep_analysis": last_message,
        "cep_tables": _extract_tables(last_message),
        "current_step": "step3",
    }


# ============================================================
# AGENT 1.3: CEP INSIGHT ANALYZER
# ============================================================

AGENT_1_3_SYSTEM = """1. Thoroughly READ the provided long CEP brief.
2. IDENTIFY and EXTRACT the 4 MAIN POINTS from the text.
3. Make the insights ACTIONABLE and DETAILED.
4. FORMAT the output as follows:
[
   "TITLE A - Analysis in lower case.",
   "TITLE B - Analysis in lower case.",
   "TITLE C - Analysis in lower case.",
   "TITLE D - Analysis in lower case."
]
5. Ensure that one insight relates to the white space.
6. Each point should be presented clearly and concisely, limited to 150 characters for each point's analysis.
7. When you mention a CEP category, include a parenthesis with an example CEP (e.g., social (Sharing Moment, After Dinner, etc...)).
8. GIVE a title for each point and present each point on a new line.
9. VERIFY that the extracted points accurately reflect the essential content of the brief.
10. Do not add phrases like "Gift Giving - Office Sharing" at the end of each insight.
11. When mentioning a CEP make sure its first letters are capitalized (e.g. Comfort Food)"""


async def agent_1_3_insight_analyzer(state: Manager1State) -> Manager1State:
    """
    Agent 1.3: CEP Insight Analyzer
    Creates 4 key insights from the CEP analysis.
    """
    # This agent uses LLM directly (no special tools)
    messages = [
        SystemMessage(content=AGENT_1_3_SYSTEM),
        HumanMessage(content=f"Create 4 key insights from this analysis:\n\n{state['cep_analysis']}")
    ]

    response = await llm.ainvoke(messages)
    insights = _parse_insights(response.content)

    return {
        **state,
        "key_insights": insights,
        "current_step": "step4",
    }


# ============================================================
# AGENT 1.4: INDEX VISUALIZER
# ============================================================

AGENT_1_4_SYSTEM = """You are a data visualization specialist that transforms brand index metrics into clear, publication-ready scatter plot graphics.

When called, execute the index_visual MCP tool which automatically reads brand index data from the hardcoded Excel file and generates both PNG and PDF visualizations. The tool creates a scatter plot showing all brands' deviations from category averages (Index - 100) across Category Entry Points.

After the tool executes, share the public URLs (if uploaded to R2 cloud storage) or local file paths with the user, and briefly explain that the visualization shows which brands are performing above or below category average at each CEP, with positive values indicating better-than-average performance and negative values indicating below-average performance."""


async def agent_1_4_visualizer(state: Manager1State) -> Manager1State:
    """
    Agent 1.4: Index Visualizer
    Creates PNG and PDF visualizations.
    """
    tools = await get_all_tools_for_agent("visualizer")

    agent = create_react_agent(llm, tools, prompt=AGENT_1_4_SYSTEM)

    result = await agent.ainvoke({
        "messages": [HumanMessage(content="Use tool")]
    })

    last_message = result["messages"][-1].content

    return {
        **state,
        "visualization_png_url": _extract_png_url(last_message),
        "visualization_pdf_url": _extract_pdf_url(last_message),
        "current_step": "step5",
    }


# ============================================================
# AGENT 1.5: CEP SLIDE BUILDER
# ============================================================

AGENT_1_5_SYSTEM = """You are a PowerPoint slide builder agent for CEP (Category Entry Point) analysis.

TASK:
You receive two inputs from another agent and create a PowerPoint slide.

INPUTS YOU RECEIVE:
1. chart_image_url: URL to a scatter plot image (e.g., "https://pub-xxx.r2.dev/chart.png")
2. insights: Array or object with 4 insight strings

YOUR JOB:
1. VALIDATE the insights format:
   - Must be exactly 4 insights
   - Each should be formatted as "Title - Body description"
   - Accept array format: ["Title A - Body A", ...]
   - Accept object format: {"point_a": "Title A - Body A", ...}

2. If format is wrong:
   - If missing " - " separator: Add generic title like "Key Insight 1 - {insight}"
   - If wrong count (not 4): Return error "Need exactly 4 insights, got {count}"
   - If not array/object: Return error "Insights must be array or object"

3. Call build_cep_analysis_slide(chart_image_url, insights)

4. Extract the PowerPoint URL from the tool's response

5. Return the download URL to the user

EXAMPLE TOOL CALL:
build_cep_analysis_slide(
    chart_image_url="https://pub-xxx.r2.dev/scatter.png",
    insights=[
        "Strong Brand Portfolio - M&M's excels in celebrations...",
        "Competitive Landscape - Major rivals lead in gifting...",
        "Underperforming Contexts - Key challenges in Feel Better...",
        "Strategic Recommendations - Focus on enhancing moments..."
    ]
)

RESPONSE TO USER:
Extract the PowerPoint URL from tool output and say:
"✅ Your CEP Analysis PowerPoint is ready! Download: [URL]"

VALIDATION EXAMPLES:

✅ GOOD - Correct format:
insights = [
    "Strong Brand Portfolio - M&M's excels in celebrations...",
    "Competitive Landscape - Major rivals lead in gifting...",
    "Underperforming Contexts - Key challenges in Feel Better...",
    "Strategic Recommendations - Focus on enhancing moments..."
]
→ Call tool directly

⚠️ FIXABLE - Missing separator:
insights = [
    "M&M's excels in celebrations",
    "Major rivals lead in gifting",
    "Key challenges in Feel Better",
    "Focus on enhancing moments"
]
→ Fix by adding titles:
formatted = [f"Key Insight {i+1} - {insight}" for i, insight in enumerate(insights)]
→ Then call tool

❌ ERROR - Wrong count:
insights = ["Insight 1", "Insight 2", "Insight 3"]  # Only 3!
→ Return error: "Need exactly 4 insights, got 3"

DO NOT:
- Generate the chart yourself (you receive the URL)
- Create the insights yourself (you receive them)
- Run any other tools
- Skip validation

DO:
- Validate insight count (must be 4)
- Validate insight format (check for " - " separator)
- Fix format if needed (add generic titles)
- Call the tool with validated inputs
- Return the PowerPoint URL to the user"""


async def agent_1_5_slide_builder(state: Manager1State) -> Manager1State:
    """
    Agent 1.5: CEP Slide Builder
    Creates PowerPoint slide with insights and visuals.
    """
    tools = await get_all_tools_for_agent("slide_builder")

    agent = create_react_agent(llm, tools, prompt=AGENT_1_5_SYSTEM)

    # Format the request with insights and PNG URL
    request = f"""Create a PowerPoint slide with:

url: {state['visualization_png_url']}
insights:
{state['key_insights']}"""

    result = await agent.ainvoke({
        "messages": [HumanMessage(content=request)]
    })

    last_message = result["messages"][-1].content

    return {
        **state,
        "powerpoint_url": _extract_ppt_url(last_message),
        "current_step": "compile",
    }


# ============================================================
# COMPILE FINAL REPORT
# ============================================================

async def compile_manager1_report(state: Manager1State) -> Manager1State:
    """
    Compile all outputs into the final report format.
    """
    report = f"""# Competitive Analysis Report: M&M's Category Entry Points

## Overview
M&M's brand performance has been analyzed across Category Entry Points,
comparing performance against competitor brands. This report provides
strategic insights and recommendations based on performance clustering.

---

## Visual Outputs

The analysis has been visualized in the following formats for easy sharing
and presentation:

**PowerPoint Slide (Link):** {state['powerpoint_url']}

**CEP Competitive Landscape Table (PNG):** {state['raw_data_png_url']}

---

## Strategic Analysis

{state['cep_analysis']}

---

## Key Insights

{chr(10).join(f"- {insight}" for insight in (state['key_insights'] or []))}

---

## Deliverables Summary

✅ **Visual Outputs**: PowerPoint Slide + PNG charts
✅ **CEP Performance Clusters**: White Space, Winning, Underperforming, Parity
✅ **Strategic Insights & Recommendations**: Invest, Test, Develop, Monitor strategies

**Next Steps:** Review the strategic recommendations and prioritize actions based
on brand objectives and resource availability. Focus on the Winning CEPs to
amplify strengths and evaluate the Underperforming CEPs for strategic decisions."""

    return {
        **state,
        "final_report": report,
        "current_step": "complete",
    }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _extract_png_url(text: str) -> str:
    """Extract PNG URL from agent response."""
    import re
    match = re.search(r'https?://[^\s]+\.png', text)
    return match.group(0) if match else ""


def _extract_pdf_url(text: str) -> str:
    """Extract PDF URL from agent response."""
    import re
    match = re.search(r'https?://[^\s]+\.pdf', text)
    return match.group(0) if match else ""


def _extract_ppt_url(text: str) -> str:
    """Extract PowerPoint URL from agent response."""
    import re
    match = re.search(r'https?://[^\s]+\.(pptx?|powerpoint)', text, re.IGNORECASE)
    if match:
        return match.group(0)
    # Try generic URL if specific extension not found
    match = re.search(r'https?://[^\s]+', text)
    return match.group(0) if match else ""


def _extract_json(text: str) -> dict:
    """Extract JSON data from agent response."""
    import json
    import re
    # Try to find JSON block
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def _extract_tables(text: str) -> str:
    """Extract markdown tables from agent response."""
    import re
    tables = re.findall(r'\|.*\|[\s\S]*?(?=\n\n|\Z)', text)
    return "\n\n".join(tables)


def _parse_insights(text: str) -> list[str]:
    """Parse insights from agent response."""
    import re
    # Try to parse as JSON array
    try:
        import json
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            return json.loads(match.group(0))
    except:
        pass

    # Fallback: parse as bullet points or numbered list
    lines = text.strip().split('\n')
    insights = []
    for line in lines:
        line = line.strip()
        if line and (line.startswith('-') or line.startswith('*') or line[0].isdigit()):
            # Remove bullet/number prefix
            cleaned = re.sub(r'^[-*\d.)\s]+', '', line)
            if cleaned:
                insights.append(cleaned)

    return insights[:4]  # Return max 4 insights
