"""
Worker agents for Manager 2: Audience-to-Creative Strategy Orchestrator.

Each worker is a node function that performs a specific step:
- 2.1 Audience CEP Analyzer: Analyzes audience CEP priorities
- 2.2 Audience Data Extractor: Extracts detailed audience attributes
- 2.3 Audience Creative Slide Builder: Builds PowerPoint slide
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from src.state.schemas import Manager2State
from src.tools.mcp_tools import (
    analyze_audience_cep_priorities,
    get_demo_audiences,
    build_audience_strategy_slides,
    get_all_tools_for_agent,
)

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)


# ============================================================
# AGENT 2.1: AUDIENCE CEP ANALYZER
# ============================================================

AGENT_2_1_SYSTEM = """When tasked with analyzing audience CEP priorities, do the following:

1. Call the `analyze_audience_cep_priorities` tool without any input.

2. Display the complete output of the tool, which includes priority tables and overlap analysis.

3. Generate strategic insights focusing on M&M's messaging and creative strategy, ensuring to analyze common opportunities, unique segment highlights, and actionable recommendations.

OUTPUT FORMAT:

# Audience CEP Strategic Analysis: M&M's

## Tool Output: Priority Analysis

[PASTE THE COMPLETE TOOL OUTPUT HERE]

[Include all priority tables, shared analysis, unique analysis, and summary]

---

## Strategic Insights

### 1. Shared CEPs Analysis: Common Opportunities

#### Universal Opportunities (All 3 Segments)

[Analyze CEPs appearing in all segments]

- Discuss what makes these opportunities universally relevant.
- Outline the strategic implications.
- Provide campaign recommendations.

#### Two-Segment Overlaps

[Analyze CEPs appearing in 2 segments]

- Identify which segments share these CEPs.
- Explain the significance of these overlaps.
- Explore hybrid messaging opportunities.

### 2. Unique CEPs Analysis: Segment-Specific Focus

#### Switch Audience Priorities

[Analyze Switch-only CEPs]

- Explore what drives competitive switching.
- Discuss the implications for creative strategy.
- Provide targeting recommendations.

#### Recruit Audience Priorities

[Analyze Recruit-only CEPs]

- Investigate what attracts new category entrants.
- Develop trial and acquisition strategies.
- Identify potential entry points.

#### Grow Audience Priorities

[Analyze Grow-only CEPs]

- Examine what deepens existing relationships.
- Identify loyalty and frequency drivers.
- Propose retention strategies.

### 3. Strategic Recommendations

- Highlight flagship campaign themes.
- Outline media strategies for broad reach.
- Address consistency and customization in messaging.

## Conclusion

[Provide 2-3 sentences on the strategic path forward]"""


async def agent_2_1_audience_cep_analyzer(state: Manager2State) -> Manager2State:
    """
    Agent 2.1: Audience CEP Analyzer
    Analyzes audience CEP priorities using the MCP tool.
    """
    tools = await get_all_tools_for_agent("audience_cep")

    agent = create_react_agent(llm, tools, prompt=AGENT_2_1_SYSTEM)

    # Call the tool without any specific input as per Lyzr instructions
    result = await agent.ainvoke({
        "messages": [HumanMessage(content="Analyze audience CEP priorities")]
    })

    last_message = result["messages"][-1].content

    # Parse the response to extract structured data
    audience_data = _parse_audience_analysis(last_message)

    return {
        **state,
        "audience_segments": audience_data["segments"],
        "priority_ceps": audience_data["cep_mapping"],
        "current_step": "step2",
    }


# ============================================================
# AGENT 2.2: AUDIENCE DATA EXTRACTOR
# ============================================================

AGENT_2_2_SYSTEM = """Use the demo_audiences tool to create intelligent insights of the new filtered list.

## INPUT
Expect the output from the demo_audiences tool, which is index reports for each audience with indices for each attribute and percent of the audience with the attribute.

Use this the above's output to proceed with the steps. The brand of interest is M&M's.

## STEPS
1. Infer which attributes for each audience are key in delivering personalized creative. You should think about the TOP attributes that are most representative of M&M's audience that would be useful in building content that is relatable. Provide rationale for picking these TOP attributes for each audience segment.

2. Based on the attributes think of creative ideas to sell M&M's that will resonate with each audience.

## OUTPUT
Natural language insights and recommendations with key factors about the audience that would matter in developing a personalized creative strategy. You should bring up creative ideas that would include the factors or think of how factors can influence the way we communicate with that audience. Deliver the same for each audience separately.

OUTPUT TEXT
DO NOT ASK THE USER IF THEY WOULD ALSO LIKE A PDF JUST PROVIDE IT
DO NOT FORGET TO ALSO OUTPUT THE TEXT NOT JUST THE PDF

## GUIDANCE
TOP attributes = weight in factors including the index, proportion, and relevance to creative content"""


async def agent_2_2_audience_data_extractor(state: Manager2State) -> Manager2State:
    """
    Agent 2.2: Audience Data Extractor
    Extracts detailed audience attributes from MCP tool.
    """
    tools = await get_all_tools_for_agent("audience_data")

    agent = create_react_agent(llm, tools, prompt=AGENT_2_2_SYSTEM)

    result = await agent.ainvoke({
        "messages": [HumanMessage(content="Use tool")]
    })

    # Capture ALL AI messages (not just the last one) to get full exploration output
    all_ai_messages = []
    for msg in result["messages"]:
        if hasattr(msg, 'content') and msg.content:
            # Skip tool calls and human messages, keep AI responses
            msg_type = type(msg).__name__
            if msg_type == "AIMessage" or "AI" in msg_type:
                all_ai_messages.append(msg.content)

    # Combine all AI responses for complete exploration data
    full_exploration = "\n\n".join(all_ai_messages) if all_ai_messages else result["messages"][-1].content

    # Parse attributes from response
    attributes = _parse_audience_attributes(full_exploration)

    return {
        **state,
        "audience_attributes": attributes,
        "current_step": "step3",
    }


# ============================================================
# STEP 3 & 4: BUILD STRATEGIC TABLE AND INSIGHTS
# (These are done by the Manager itself, not sub-agents)
# ============================================================

STRATEGIC_TABLE_SYSTEM = """You are building a strategic Audience-CEP-Creative table.

Create a markdown table with these columns:
| Audience Segment | Key Attributes | Priority CEPs | Creative Ideas | Competitor Brands |

Rules:
1. List each segment once with ALL attributes consolidated in ONE cell
2. Each CEP gets its OWN ROW
3. Brainstorm 3-5 SPECIFIC creative ideas per CEP (not generic like "social media campaign")
4. **CRITICAL: For Competitor Brands column, extract the TOP COMPETITORS for EACH SPECIFIC CEP from the competitive data**
   - Look at the cluster analysis tables to find which brands have the HIGHEST indices for each CEP
   - For "Winning" CEPs: List the brands M&M's is beating (lower indices)
   - For "Underperforming" CEPs: **IMPORTANT** - Find the brands with indices HIGHER than M&M's for that specific CEP. Look in the 🟥 Underperforming cluster for competitor indices.
   - For "White Space" CEPs: List the brands currently leading that CEP
   - For "Parity" CEPs: List brands with similar performance
   - DO NOT use generic "top 2 competitors" - extract ACTUAL brand names and indices from the data!

**UNDERPERFORMING CEPs SPECIAL ATTENTION:**
When you see a CEP in the Underperforming cluster (🟥), you MUST:
1. Look at that CEP's row in the competitive data
2. Find which competitor brands have indices > M&M's index for that CEP
3. List those specific brands in the Competitor Brands column (e.g., "Twix (142), Snickers (138)")

Creative ideas should be:
- Relevant to BOTH the audience attributes AND the specific CEP
- Actionable and specific (e.g., "Instagram Reels series featuring real customer transformation stories")
- Diverse in format (content types, channels, experiences)
- Consider the competitive landscape: what are competitors doing in this CEP?"""


async def build_strategic_table(state: Manager2State) -> Manager2State:
    """
    Step 3: Build the strategic Audience-CEP-Creative table.
    This is done by the manager using data from agents 2.1 and 2.2.
    """
    messages = [
        SystemMessage(content=STRATEGIC_TABLE_SYSTEM),
        HumanMessage(content=f"""Build the strategic table using:

AUDIENCE SEGMENTS & CEP PRIORITIES:
{state['audience_segments']}
{state['priority_ceps']}

AUDIENCE ATTRIBUTES (from demo_audiences tool - use for Target Exploration):
{state['audience_attributes']}

---
COMPETITIVE DATA FROM PHASE 1 (CRITICAL - use this for CEP-specific competitor brands):
---

CEP PERFORMANCE CLUSTERS & COMPETITOR RANKINGS:
{state['competitive_tables']}

DETAILED CEP ANALYSIS (extract competitor brands per CEP from here):
{state['competitive_dynamics']}

---

INSTRUCTIONS:
1. For EACH CEP in the table, find the corresponding competitors from the competitive data above
2. Extract the TOP 2-3 competitors FOR THAT SPECIFIC CEP based on who is outperforming or leading
3. **FOR UNDERPERFORMING CEPs (🟥 cluster)**: You MUST find which competitors have HIGHER indices than M&M's for that CEP and list them with their index values (e.g., "Twix (142), Snickers (138)")
4. For BELOW THRESHOLD CEPs (M&M's index < 120): List the top competitors beating M&M's in that CEP
5. Include a "Below Threshold CEPs" section at the bottom with:
   - The CEP name
   - M&M's index for that CEP
   - The TOP 2-3 competitors with their indices
   - Brief recommendation for improvement""")
    ]

    response = await llm.ainvoke(messages)

    # Extract table and below threshold analysis
    table, below_threshold = _extract_table_and_analysis(response.content)

    return {
        **state,
        "strategic_table": table,
        "below_threshold_analysis": below_threshold,
        "current_step": "step4",
    }


STRATEGIC_INSIGHTS_SYSTEM = """You are generating strategic insights for the Audience-to-Creative analysis.

For EACH audience segment, provide:
1. **Audience Overview** - Who they are and what defines them
2. **CEP Strategy Analysis** - Why these CEPs matter, how they connect to attributes
3. **Creative Opportunity Assessment** - Most promising territories, challenges
4. **Strategic Implications** - Investment priorities, testing needs

Also provide an **Overall Strategic Summary** with:
- Key patterns across all audiences
- Portfolio-level recommendations
- Priority actions and sequencing

IMPORTANT: Highlight and make bold any BELOW THRESHOLD CEPs and which audiences should be targeted for them."""


async def generate_strategic_insights(state: Manager2State) -> Manager2State:
    """
    Step 4: Generate natural language strategic insights.
    """
    messages = [
        SystemMessage(content=STRATEGIC_INSIGHTS_SYSTEM),
        HumanMessage(content=f"""Generate strategic insights based on:

STRATEGIC TABLE:
{state['strategic_table']}

BELOW THRESHOLD ANALYSIS:
{state['below_threshold_analysis']}

AUDIENCE DATA:
{state['audience_segments']}
{state['audience_attributes']}

COMPETITIVE CONTEXT:
{state['competitive_dynamics']}""")
    ]

    response = await llm.ainvoke(messages)

    return {
        **state,
        "strategic_insights": response.content,
        "current_step": "step5",
    }


# ============================================================
# AGENT 2.3: AUDIENCE CREATIVE SLIDE BUILDER
# ============================================================

AGENT_2_3_SYSTEM = """# ROLE

You are the **Audience-to-Creative Strategy Agent**, a specialized agent that transforms Strategic Audience-CEP-Creative tables into PowerPoint presentations. When you receive a table in the specified format, you convert it to JSON and generate a presentation slide using the `build_audience_strategy_slides` tool.

You do NOT create the strategy yourself. Instead, you process the provided table data and deliver a presentation link to the user.

---

# TRIGGER

When you receive text that starts with:
- "Strategic Audience-CEP-Creative Table"
- Or contains a table with columns: Audience Segment, Key Attributes, Priority CEPs, Creative Ideas, Competitor Brands

You immediately begin the autonomous workflow without asking for additional input.

---

# AUTONOMOUS WORKFLOW

Execute these steps sequentially:

## STEP 1: Parse the Table
**Extract data from the provided table:**

Identify:
- **Audience Segments** (e.g., SWITCH, RECRUIT, GROW)
- **Key Attributes** for each segment (bullet points describing the audience)
- **Priority CEPs** (Category Entry Points) for each segment
- **Creative Ideas** (numbered list of 5 tactical ideas per CEP)
- **Competitor Brands** for each CEP
- **Below Threshold CEPs** across all segments

Also extract:
- **Below Threshold CEPs** at the bottom (especially below-threshold CEPs to monitor/test)

---

## STEP 2: Transform to JSON
**Convert the table into this exact JSON structure:**

```json
{
  "segments": [
    {
      "name": "SEGMENT_NAME",
      "key_attributes": [
        "attribute 1",
        "attribute 2",
        "attribute 3",
        "attribute 4"
      ],
      "ceps": [
        {
          "name": "CEP_NAME",
          "creative_ideas": [
            "1) creative idea text",
            "2) creative idea text",
            "3) creative idea text",
            "4) creative idea text",
            "5) creative idea text"
          ],
          "competitor_brands": ["Brand1", "Brand2", "Brand3"]
        }
      ]
    }
  ],
"below_threshold_slide": {
      "title": "Below-Threshold CEP Opportunities",
      "ceps": [
        {
          "name": "CEP_NAME",
          "top_competitors": ["Brand1", "Brand2", "Brand3"],
          "target_explorations": [
            {
              "audience": "SWITCH",
              "rationale": "rationale for targeting this audience"
            },
            {
              "audience": "GROW",
              "rationale": "rationale for targeting this audience"
            }
          ]
        }
      ]
    },
  "presentation_title": "Strategic Audience-CEP-Creative Insights"
}
```

**Formatting rules:**
- Each segment is an object in the "segments" array
- Key attributes should be an array of strings (one per bullet point)
- Each CEP under a segment includes: name, creative_ideas array, competitor_brands array
- Creative ideas should preserve their numbering: "1)", "2)", etc.
- Competitor brands should be extracted as an array of individual brand names
- Always use "Strategic Audience-CEP-Creative Insights" as the presentation_title

---

## STEP 3: Generate Presentation
**Feed the JSON to the tool:**

Call: `build_audience_strategy_slides` with the complete JSON object created in Step 2

**What you receive back:**
- PowerPoint slide URL/link

---

## STEP 4: Deliver Final Output

**Present only the presentation link to the user.**

---

# OUTPUT FORMAT

Simply present the presentation link to the user:

```markdown
✅ **Your Audience-to-Creative Strategy Presentation is ready!**

🔗 **Presentation Link:** [URL from tool]
```

**That's it.** The user receives only the presentation link.

---

# PARSING GUIDELINES

## Handling Audience Segments
- Each audience segment (SWITCH, RECRUIT, GROW) becomes one object in the segments array
- If an audience segment appears multiple times with different CEPs, consolidate all CEPs under that single segment object

## Handling Key Attributes
- Extract all bullet points under the audience segment
- Each bullet becomes one string in the key_attributes array
- Preserve original wording and formatting (including "•" if present)

## Handling CEPs
- Each Priority CEP becomes one object in the ceps array
- If the same CEP appears multiple times for a segment, treat each occurrence as a separate CEP object

## Handling Creative Ideas
- Extract all 5 numbered creative ideas
- Preserve the numbering format: "1)", "2)", "3)", "4)", "5)"
- Keep the full text of each idea, including quotes, parentheses, and details
- Each idea is one string in the creative_ideas array

## Handling Competitor Brands
- Extract competitor brand names (usually appears after the creative ideas)
- Split into individual brand names
- Create an array of strings with each brand name

## Handling Table Notes
- Notes at the bottom (especially about below-threshold CEPs) are for context only
- Do NOT include table notes in the JSON structure
- They inform your understanding but are not part of the output

---

# EXAMPLE TRANSFORMATION

**Input Table Row:**
```
SWITCH | • Deal-driven: heavy coupon users
        • Stock-up shoppers
        | Sharing Moment | 1) "Share & Save" BOGO coupons
                          2) Department-store endcap bundles
                          3) Direct mail invite kit
                          4) CTV shoppable ad units
                          5) TikTok creator series
        | Crunch, Milkyway, Snickers
```

**Output JSON:**
```json
{
  "name": "SWITCH",
  "key_attributes": [
    "Deal-driven: heavy coupon users",
    "Stock-up shoppers"
  ],
  "ceps": [
    {
      "name": "Sharing Moment",
      "creative_ideas": [
        "1) \"Share & Save\" BOGO coupons",
        "2) Department-store endcap bundles",
        "3) Direct mail invite kit",
        "4) CTV shoppable ad units",
        "5) TikTok creator series"
      ],
      "competitor_brands": ["Crunch", "Milkyway", "Snickers"]
    }
  ]
}
```

---

# QUALITY CHECKS

Validate before calling tool (internally, don't show to user):
- **After Step 1:** Confirm all segments, CEPs, and creative ideas were extracted
- **After Step 2:** Confirm JSON structure matches required format exactly
  - Check: segments array exists
  - Check: each segment has name, key_attributes, and ceps
  - Check: each CEP has name, creative_ideas (5 items), and competitor_brands
  - Check: presentation_title is included
  - Check: below_threshold_slide is included in the JSON
- **After Step 3:** Confirm presentation link was returned

---

# ERROR HANDLING

If any step fails:
- **Step 1 fails:** Report that table parsing failed; check if table format matches expected structure
- **Step 2 fails:** Report JSON transformation error; verify all required fields are present
- **Step 3 fails:** Report tool error; the `build_audience_strategy_slides` tool may be unavailable

---

# COMMUNICATION STYLE

## With Tool:
- Pass the complete, valid JSON object to `build_audience_strategy_slides`
- Ensure JSON is properly formatted with ALL required fields

## With User:
- **At Start:** Brief acknowledgment
Perform workflow
- **At End:** Deliver only the presentation link
- **On Error:** Clearly explain what failed (parsing, JSON, or tool)
- **Keep it simple:** User just needs the link

---

# CRITICAL RULES

1. **Always parse the complete table** - Don't skip any segments or CEPs
2. **Preserve exact wording** - Don't paraphrase or summarize creative ideas
3. **Maintain numbering** - Creative ideas should keep their "1)", "2)", etc. format
4. **Follow JSON structure exactly** - The tool expects specific field names
5. **Deliver only the link** - Don't include the JSON or parsing details in final output
6. **Execute autonomously** - Once you receive the table, process it completely
7. **Use exact presentation title** - Always "Strategic Audience-CEP-Creative Insights"

---

# SUCCESS CRITERIA

You've succeeded when:
- ✅ User receives a working PowerPoint presentation link
- ✅ All audience segments from the table are included in the presentation
- ✅ All CEPs and creative ideas are accurately represented
- ✅ Competitor brands are correctly extracted
- ✅ Workflow executed smoothly without user intervention
- ✅ Output is just the link (no unnecessary explanation)

---

# REMEMBER

You are a data transformer and presentation generator. Once triggered, you:
1. Parse the strategy table
2. Transform to JSON
3. Generate presentation via tool
4. Deliver the link

The user should feel like they provided a strategy table and instantly received a professional presentation - without seeing the intermediate JSON transformation or parsing steps.

Your value is in:
- Accurate table parsing without data loss
- Precise JSON transformation matching tool requirements
- Seamless presentation generation
- Clean, simple output (just the link)"""


async def agent_2_3_slide_builder(state: Manager2State) -> Manager2State:
    """
    Agent 2.3: Audience Creative Slide Builder
    Creates PowerPoint slide with table and analysis.
    """
    tools = await get_all_tools_for_agent("audience_slide")

    agent = create_react_agent(llm, tools, prompt=AGENT_2_3_SYSTEM)

    # Extract audience attributes for target exploration
    audience_attrs = state.get('audience_attributes', {})
    if isinstance(audience_attrs, dict):
        audience_attrs_text = audience_attrs.get('raw_attributes', str(audience_attrs))
    else:
        audience_attrs_text = str(audience_attrs) if audience_attrs else ""

    request = f"""Create a PowerPoint slide with this content:

TABLE:
{state['strategic_table']}

BELOW THRESHOLD ANALYSIS (highlight this - include CEP names and competitor brands):
{state['below_threshold_analysis']}

TARGET EXPLORATION (use for target_explorations rationale in below_threshold_slide):
{audience_attrs_text}"""

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
# COMPILE FINAL OUTPUT
# ============================================================

async def compile_manager2_output(state: Manager2State) -> Manager2State:
    """
    Compile all outputs into the final deliverable format.
    """
    # Extract audience attributes for target exploration section
    audience_attrs = state.get('audience_attributes', {})
    if isinstance(audience_attrs, dict):
        audience_attrs_text = audience_attrs.get('raw_attributes', str(audience_attrs))
    else:
        audience_attrs_text = str(audience_attrs) if audience_attrs else "No audience attribute data available"

    output = f"""# Audience-to-Creative Strategy Analysis

## Overview
This analysis maps audience segments to their priority Category Entry Points and provides strategic creative recommendations based on audience attributes and competitive dynamics.

✅ **Your Audience-to-Creative Strategy Presentation is ready!**

{state['powerpoint_url']}

---

## Target Exploration: Audience Attributes

The following attributes were identified as key differentiators for each audience segment, providing the foundation for personalized creative strategies:

{audience_attrs_text}

---

## Strategic Audience-CEP-Creative Table

{state['strategic_table']}

*Table Notes:*
- Audience segments are listed with all key attributes consolidated
- Each CEP is shown in a separate row with tailored creative ideas
- **Competitor brands are specific to each CEP** based on Phase 1 competitive analysis

**BELOW THRESHOLD CEPs REQUIRING ATTENTION:**
{state['below_threshold_analysis']}

---

## Strategic Insights by Audience Segment

{state['strategic_insights']}

---

## Deliverables Summary

✅ **Strategic Table**: Audience segments mapped to CEPs with creative ideas and competitive context
✅ **Target Exploration**: Detailed audience attributes for GROW, SWITCH, RECRUIT segments
✅ **Audience Insights**: Deep dive analysis for each segment
✅ **Creative Recommendations**: Tailored creative territories per audience-CEP pairing
✅ **Competitive Intelligence**: CEP-specific brand examples and differentiation opportunities
✅ **Below Threshold Analysis**: CEPs requiring attention with competitor benchmarks
✅ **PowerPoint URL**: {state['powerpoint_url']}

**Next Steps:** Review creative recommendations by segment priority, validate concepts with target audiences, and develop detailed creative briefs for top-priority CEPs."""

    return {
        **state,
        "final_output": output,
        "current_step": "complete",
    }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _parse_audience_analysis(text: str) -> dict:
    """Parse audience analysis into structured data."""
    # This is a simplified parser - adjust based on actual LLM output format
    return {
        "segments": text,  # Keep as text for now
        "cep_mapping": {},
    }


def _parse_audience_attributes(text: str) -> dict:
    """Parse audience attributes from tool response."""
    return {"raw_attributes": text}


def _extract_table_and_analysis(text: str) -> tuple[str, str]:
    """Extract table and below-threshold analysis from response."""
    import re

    # Find markdown table (capture all table rows)
    table_match = re.search(r'(\|.*\|[\s\S]*?)(?=\n\n[^|]|\n\n##|\Z)', text)
    table = table_match.group(1).strip() if table_match else text

    # Find below threshold section (greedy to capture all details including competitors)
    below_match = re.search(
        r'(?:below threshold|threshold ceps|underperforming|attention|monitor)[\s\S]*$',
        text,
        re.IGNORECASE
    )
    below_threshold = below_match.group(0).strip() if below_match else ""

    return table, below_threshold


def _extract_ppt_url(text: str) -> str:
    """Extract PowerPoint URL from agent response."""
    import re
    match = re.search(r'https?://[^\s]+', text)
    return match.group(0) if match else ""
