"""
Master Graph: Strategic Intelligence Manager (Human-in-the-Loop Version)

This is the top-level orchestrator that coordinates:
- Phase 1: Competitive Analyzer (Manager 1)
- CHECKPOINT: Present results and wait for user confirmation
- Phase 2: Audience-to-Creative Strategy (Manager 2)

The human-in-the-loop pattern uses LangGraph's `interrupt_before` to pause
execution and wait for user input before proceeding to Phase 2.
"""
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from src.state.schemas import MasterState
from src.graphs.manager1_graph import run_manager1
from src.graphs.manager2_graph import run_manager2


# ============================================================
# PHASE 1: RUN COMPETITIVE ANALYZER
# ============================================================

async def run_phase1(state: MasterState) -> MasterState:
    """
    Execute Phase 1: Competitive Intelligence Collection.
    Delegates to Manager 1 (Competitive Analyzer).
    """
    try:
        # Run Manager 1 graph
        result = await run_manager1()

        # Extract the competitive intelligence report
        competitive_report = result.get("final_report", "")

        # Extract structured data for Phase 2 (CEP-specific competitor info)
        cep_tables = result.get("cep_tables", "")
        cep_analysis = result.get("cep_analysis", "")

        return {
            **state,
            "competitive_intelligence": competitive_report,
            "cep_tables": cep_tables,  # Pass structured tables to Phase 2
            "cep_analysis": cep_analysis,  # Pass detailed analysis to Phase 2
            "messages": state["messages"] + [
                AIMessage(content=competitive_report)
            ],
            "current_phase": "checkpoint",
            "error": None,
        }

    except Exception as e:
        return {
            **state,
            "error": f"Phase 1 failed: {str(e)}",
            "current_phase": "checkpoint",
        }


# ============================================================
# CHECKPOINT: PRESENT TO USER AND AWAIT CONFIRMATION
# ============================================================

def present_checkpoint(state: MasterState) -> MasterState:
    """
    Present Phase 1 results to user and prepare checkpoint message.

    This node formats the output for user review.
    The actual interruption happens via `interrupt_before` on the next node.
    """
    checkpoint_message = f"""
# Phase 1 Complete: Competitive Intelligence Report

I've completed the first workflow analyzing M&M's competitive positioning across Category Entry Points. Please review the following findings:

{state['competitive_intelligence']}

---

## ✅ Checkpoint: Please Review and Confirm

Before I proceed to Phase 2 (Audience & Creative Strategy Analysis), please confirm:

1. **Does this competitive intelligence align with your expectations?**
2. **Are there any specific insights or CEPs you'd like me to emphasize in the final synthesis?**
3. **Should I proceed to the audience-creative analysis?**

Please reply with:
- **"Proceed"** or **"Continue"** to move to Phase 2
- **"Stop"** if you want to end here
- **Any specific guidance** you'd like me to incorporate into the final synthesis
"""

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=checkpoint_message)],
        "current_phase": "checkpoint",
    }


def process_user_input(state: MasterState) -> MasterState:
    """
    Process user input from the checkpoint.

    This node runs AFTER the interrupt, when the user provides input.
    """
    # Get the latest user message
    messages = state.get("messages", [])
    user_input = ""

    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_input = msg.content.lower().strip()
            break

    # Determine user decision
    proceed_signals = ["proceed", "continue", "yes", "go ahead", "move to phase 2", "ok", "okay"]
    stop_signals = ["stop", "no", "end", "halt"]

    if any(signal in user_input for signal in proceed_signals):
        decision = "proceed"
        guidance = None
    elif any(signal in user_input for signal in stop_signals):
        decision = "stop"
        guidance = None
    else:
        # User provided guidance
        decision = "guidance"
        guidance = user_input

    return {
        **state,
        "user_decision": decision,
        "user_guidance": guidance,
        "current_phase": "phase2" if decision in ["proceed", "guidance"] else "complete",
    }


# ============================================================
# ROUTING: DECIDE NEXT STEP BASED ON USER INPUT
# ============================================================

def route_after_checkpoint(state: MasterState) -> Literal["phase2", "complete"]:
    """Route based on user decision at checkpoint."""
    decision = state.get("user_decision", "proceed")

    if decision == "stop":
        return "complete"
    else:
        return "phase2"


# ============================================================
# PHASE 2: RUN AUDIENCE-TO-CREATIVE STRATEGY
# ============================================================

async def run_phase2(state: MasterState) -> MasterState:
    """
    Execute Phase 2: Audience & Creative Strategy Collection.
    Delegates to Manager 2 (Audience-to-Creative Strategy Orchestrator).

    Uses competitive data from Phase 1 as input.
    """
    try:
        # Use structured data from Phase 1 (stored in state)
        # This includes CEP-specific competitor information
        cep_tables = state.get("cep_tables") or ""
        cep_analysis = state.get("cep_analysis") or ""

        # Include any user guidance
        if state.get("user_guidance"):
            cep_analysis += f"\n\nUser Guidance: {state['user_guidance']}"

        # Run Manager 2 graph with structured competitive data
        result = await run_manager2(
            competitive_tables=cep_tables,
            competitive_dynamics=cep_analysis
        )

        creative_output = result.get("final_output", "")

        return {
            **state,
            "creative_intelligence": creative_output,
            "messages": state["messages"] + [
                AIMessage(content=f"Phase 2 Complete:\n\n{creative_output}")
            ],
            "current_phase": "complete",
        }

    except Exception as e:
        return {
            **state,
            "error": f"Phase 2 failed: {str(e)}",
            "current_phase": "complete",
        }


# ============================================================
# FINAL OUTPUT
# ============================================================

def deliver_final_output(state: MasterState) -> MasterState:
    """
    Deliver the final output to the user.
    """
    if state.get("user_decision") == "stop":
        final_message = """
## Workflow Stopped

Phase 1 (Competitive Intelligence) has been completed.
Phase 2 was not executed per your request.

The competitive analysis is available above for your reference.
"""
    elif state.get("error"):
        final_message = f"""
## Workflow Error

An error occurred during execution:
{state['error']}

Please retry the request or contact support if the issue persists.
"""
    else:
        final_message = f"""
## Strategic Intelligence Report Complete

Both phases have been successfully executed:

✅ **Phase 1**: Competitive Intelligence Report
✅ **Phase 2**: Audience-to-Creative Strategy Analysis

The complete Phase 2 output has been delivered above.

### Key Deliverables:
- CEP Competitive Analysis with visualizations
- Audience-to-CEP mapping with creative recommendations
- Strategic insights connecting competitive position to audience strategy
- PowerPoint presentations for both phases
"""

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=final_message)],
        "current_phase": "complete",
    }


# ============================================================
# CREATE THE MASTER GRAPH
# ============================================================

def create_master_graph():
    """
    Create the Master Strategic Intelligence Manager graph.

    Flow:
    START → phase1 → present_checkpoint → [INTERRUPT] → process_user_input
          → (route) → phase2 OR complete → deliver_final → END

    The interrupt happens before `process_user_input`, allowing the user
    to see the Phase 1 results and provide their decision.
    """
    graph = StateGraph(MasterState)

    # Add nodes
    graph.add_node("phase1", run_phase1)
    graph.add_node("present_checkpoint", present_checkpoint)
    graph.add_node("process_user_input", process_user_input)
    graph.add_node("phase2", run_phase2)
    graph.add_node("deliver_final", deliver_final_output)

    # Add edges
    graph.add_edge(START, "phase1")
    graph.add_edge("phase1", "present_checkpoint")
    graph.add_edge("present_checkpoint", "process_user_input")

    # Conditional routing after user input
    graph.add_conditional_edges(
        "process_user_input",
        route_after_checkpoint,
        {
            "phase2": "phase2",
            "complete": "deliver_final",
        }
    )

    graph.add_edge("phase2", "deliver_final")
    graph.add_edge("deliver_final", END)

    return graph


def compile_master_graph(checkpointer=None):
    """
    Compile the Master graph with HITL interrupt.

    The interrupt_before on 'process_user_input' creates the checkpoint
    where execution pauses for user input.

    Args:
        checkpointer: Required for HITL - stores state between interrupts

    Returns:
        Compiled graph with interrupt capabilities
    """
    graph = create_master_graph()

    # CRITICAL: checkpointer is required for interrupts to work
    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["process_user_input"]  # Pause BEFORE processing user input
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _extract_tables_and_dynamics(report: str) -> tuple[str, str]:
    """Extract CEP tables and competitive dynamics from Phase 1 report."""
    import re

    # Handle None or empty report
    if not report:
        return "", ""

    # Extract tables (everything between ## Strategic Analysis and next ##)
    tables_match = re.search(
        r'## Strategic Analysis\s*([\s\S]*?)(?=##|$)',
        report
    )
    tables = tables_match.group(1).strip() if tables_match else report

    # Extract competitive dynamics section
    dynamics_match = re.search(
        r'(?:Competitive Dynamics|competitive dynamics)[:\s]*([\s\S]*?)(?=##|\n\n\n|$)',
        report,
        re.IGNORECASE
    )
    dynamics = dynamics_match.group(1).strip() if dynamics_match else ""

    return tables, dynamics


# ============================================================
# EXECUTION HELPERS
# ============================================================

async def run_strategic_intelligence(thread_id: str = "default"):
    """
    Run the complete Strategic Intelligence workflow with HITL.

    This is the main entry point for executing the workflow.

    Args:
        thread_id: Unique identifier for this conversation thread

    Returns:
        Generator that yields state updates, pausing at checkpoint
    """
    checkpointer = MemorySaver()
    graph = compile_master_graph(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": thread_id}}

    # Initial state
    initial_state = {
        "messages": [HumanMessage(content="Generate the strategic intelligence report")],
        "competitive_intelligence": None,
        "creative_intelligence": None,
        "user_guidance": None,
        "current_phase": "phase1",
        "user_decision": None,
        "error": None,
    }

    # Run until interrupt (Phase 1 complete)
    async for event in graph.astream(initial_state, config, stream_mode="updates"):
        yield event

    # At this point, execution is paused at the checkpoint
    # The calling code should:
    # 1. Display the checkpoint message to the user
    # 2. Get user input
    # 3. Resume with: graph.ainvoke(Command(resume=user_input), config)


async def resume_after_checkpoint(graph, config: dict, user_input: str):
    """
    Resume execution after the HITL checkpoint.

    Args:
        graph: The compiled master graph
        config: Configuration with thread_id
        user_input: User's response at checkpoint

    Returns:
        Final state after Phase 2 completion
    """
    from langgraph.types import Command

    # Resume with user input
    result = await graph.ainvoke(
        Command(resume=HumanMessage(content=user_input)),
        config
    )

    return result
