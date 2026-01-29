"""
Streamlit UI for the Strategic Intelligence Multi-Agent System.

Run with: streamlit run app.py
"""
import streamlit as st
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="M&M's Strategic Intelligence",
    page_icon="🍬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
    }
    .phase-indicator {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .phase-complete {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }
    .phase-running {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
    }
    .phase-pending {
        background-color: #e2e3e5;
        border: 1px solid #d6d8db;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🍬 M&M's Strategic Intelligence System")
st.markdown("---")

# Initialize session state
if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = "idle"  # idle, running_phase1, checkpoint, running_phase2, complete
if "phase1_output" not in st.session_state:
    st.session_state.phase1_output = None
if "phase2_output" not in st.session_state:
    st.session_state.phase2_output = None
if "error" not in st.session_state:
    st.session_state.error = None


def get_phase_status(phase_num):
    """Get status indicator for a phase."""
    state = st.session_state.workflow_state

    if phase_num == 1:
        if state == "idle":
            return "pending", "⏸️"
        elif state == "running_phase1":
            return "running", "⏳"
        else:
            return "complete", "✅"
    else:  # Phase 2
        if state in ["idle", "running_phase1", "checkpoint"]:
            return "pending", "⏸️"
        elif state == "running_phase2":
            return "running", "⏳"
        else:
            return "complete", "✅"


# Sidebar - Phase Indicators
with st.sidebar:
    st.header("Workflow Progress")

    status1, icon1 = get_phase_status(1)
    status2, icon2 = get_phase_status(2)

    st.markdown(f"""
    <div class="phase-indicator phase-{status1}">
        {icon1} <strong>Phase 1:</strong> Competitive Analysis
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="phase-indicator phase-{status2}">
        {icon2} <strong>Phase 2:</strong> Audience Strategy
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Reset button
    if st.button("🔄 Reset Workflow"):
        st.session_state.workflow_state = "idle"
        st.session_state.phase1_output = None
        st.session_state.phase2_output = None
        st.session_state.error = None
        st.rerun()


async def run_workflow_phase1():
    """Run Phase 1 of the workflow."""
    from langchain_core.messages import HumanMessage, AIMessage
    from langgraph.checkpoint.memory import MemorySaver
    from src.graphs.master_graph import compile_master_graph

    checkpointer = MemorySaver()
    graph = compile_master_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "streamlit-session"}}

    initial_state = {
        "messages": [HumanMessage(content="Generate the strategic intelligence report")],
        "competitive_intelligence": None,
        "creative_intelligence": None,
        "user_guidance": None,
        "current_phase": "phase1",
        "user_decision": None,
        "error": None,
    }

    checkpoint_message = None
    async for event in graph.astream(initial_state, config, stream_mode="updates"):
        for node_name, node_output in event.items():
            if node_name == "present_checkpoint":
                messages = node_output.get("messages", [])
                for msg in messages:
                    if isinstance(msg, AIMessage):
                        checkpoint_message = msg.content

    return checkpoint_message, graph, config


async def run_workflow_phase2(graph, config, user_input):
    """Run Phase 2 of the workflow."""
    from langchain_core.messages import HumanMessage, AIMessage
    from langgraph.types import Command

    result = await graph.ainvoke(
        Command(resume=HumanMessage(content=user_input)),
        config
    )

    # Extract final output
    messages = result.get("messages", [])
    final_output = ""
    for msg in messages[-3:]:
        if isinstance(msg, AIMessage):
            final_output += msg.content + "\n\n"

    return final_output


# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # Start workflow section
    if st.session_state.workflow_state == "idle":
        st.header("Generate Strategic Intelligence Report")
        st.markdown("""
        This workflow will:
        1. **Phase 1**: Analyze M&M's competitive positioning across Category Entry Points
        2. **Checkpoint**: Present findings for your review
        3. **Phase 2**: Generate audience-specific creative strategies

        Click below to start the analysis.
        """)

        if st.button("🚀 Start Analysis", type="primary"):
            st.session_state.workflow_state = "running_phase1"
            st.rerun()

    # Running Phase 1
    elif st.session_state.workflow_state == "running_phase1":
        st.header("Running Phase 1: Competitive Analysis")
        with st.spinner("Analyzing competitive positioning... This may take a few minutes."):
            try:
                output, graph, config = asyncio.run(run_workflow_phase1())
                st.session_state.phase1_output = output
                st.session_state.graph = graph
                st.session_state.config = config
                st.session_state.workflow_state = "checkpoint"
                st.rerun()
            except Exception as e:
                st.session_state.error = str(e)
                st.session_state.workflow_state = "idle"
                st.rerun()

    # Checkpoint
    elif st.session_state.workflow_state == "checkpoint":
        st.header("📋 Phase 1 Complete - Review Results")

        # Display Phase 1 output
        with st.expander("View Phase 1 Results", expanded=True):
            st.markdown(st.session_state.phase1_output)

        st.markdown("---")
        st.subheader("Proceed to Phase 2?")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("✅ Proceed to Phase 2", type="primary"):
                st.session_state.user_decision = "proceed"
                st.session_state.workflow_state = "running_phase2"
                st.rerun()

        with col_b:
            if st.button("⏹️ Stop Here"):
                st.session_state.workflow_state = "complete"
                st.session_state.phase2_output = "Workflow stopped at Phase 1 per user request."
                st.rerun()

        # Optional guidance
        guidance = st.text_area(
            "Optional: Add guidance for Phase 2",
            placeholder="e.g., Focus on the Switch segment, emphasize digital channels..."
        )

        if guidance and st.button("Proceed with Guidance"):
            st.session_state.user_decision = guidance
            st.session_state.workflow_state = "running_phase2"
            st.rerun()

    # Running Phase 2
    elif st.session_state.workflow_state == "running_phase2":
        st.header("Running Phase 2: Audience Strategy")
        with st.spinner("Generating audience-specific strategies... This may take a few minutes."):
            try:
                user_input = st.session_state.get("user_decision", "proceed")
                output = asyncio.run(run_workflow_phase2(
                    st.session_state.graph,
                    st.session_state.config,
                    user_input
                ))
                st.session_state.phase2_output = output
                st.session_state.workflow_state = "complete"
                st.rerun()
            except Exception as e:
                st.session_state.error = str(e)
                st.session_state.workflow_state = "checkpoint"
                st.rerun()

    # Complete
    elif st.session_state.workflow_state == "complete":
        st.header("🎉 Analysis Complete!")

        tab1, tab2 = st.tabs(["Phase 1: Competitive Analysis", "Phase 2: Audience Strategy"])

        with tab1:
            if st.session_state.phase1_output:
                st.markdown(st.session_state.phase1_output)
            else:
                st.info("Phase 1 output not available")

        with tab2:
            if st.session_state.phase2_output:
                st.markdown(st.session_state.phase2_output)
            else:
                st.info("Phase 2 was not executed")

# Error display
if st.session_state.error:
    with col2:
        st.error(f"Error: {st.session_state.error}")

# Right column - Info
with col2:
    st.header("ℹ️ About")
    st.markdown("""
    **Strategic Intelligence System**

    This multi-agent workflow analyzes:

    **Phase 1** - Competitive Analysis
    - Brand index data across CEPs
    - Performance clustering
    - Strategic insights

    **Phase 2** - Audience Strategy
    - GROW, SWITCH, RECRUIT segments
    - Priority CEP mapping
    - Creative recommendations

    **Outputs:**
    - PowerPoint presentations
    - PNG visualizations
    - Strategic recommendations
    """)

    st.markdown("---")
    st.markdown("""
    **Data Sources:**
    - MCP Server: web-dan
    - Visual Tools: web-aditi

    **LangSmith Tracing:**
    Check your traces at [smith.langchain.com](https://smith.langchain.com)
    """)
