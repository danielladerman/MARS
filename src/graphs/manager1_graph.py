"""
Manager 1 Graph: Competitive Analyzer

This graph orchestrates the 5 worker agents in sequence:
1.1 Data Merger → 1.2 CEP Prioritizer → 1.3 Insight Analyzer → 1.4 Visualizer → 1.5 Slide Builder

The graph runs autonomously once triggered with "Build me the CEP brief".
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.state.schemas import Manager1State
from src.agents.workers.manager1_workers import (
    agent_1_1_data_merger,
    agent_1_2_cep_prioritizer,
    agent_1_3_insight_analyzer,
    agent_1_4_visualizer,
    agent_1_5_slide_builder,
    compile_manager1_report,
)


def should_continue(state: Manager1State) -> str:
    """Determine the next step based on current state."""
    if state.get("error"):
        return "error"
    return state.get("current_step", "step1")


def handle_error(state: Manager1State) -> Manager1State:
    """Handle errors in the workflow."""
    return {
        **state,
        "final_report": f"Error occurred: {state.get('error', 'Unknown error')}",
        "current_step": "complete",
    }


def create_manager1_graph():
    """
    Create the Manager 1: Competitive Analyzer graph.

    Flow:
    START → step1 (Data Merger) → step2 (CEP Prioritizer) → step3 (Insight Analyzer)
          → step4 (Visualizer) → step5 (Slide Builder) → compile → END
    """
    # Create the graph with Manager1State
    graph = StateGraph(Manager1State)

    # Add all nodes
    graph.add_node("step1_data_merger", agent_1_1_data_merger)
    graph.add_node("step2_cep_prioritizer", agent_1_2_cep_prioritizer)
    graph.add_node("step3_insight_analyzer", agent_1_3_insight_analyzer)
    graph.add_node("step4_visualizer", agent_1_4_visualizer)
    graph.add_node("step5_slide_builder", agent_1_5_slide_builder)
    graph.add_node("compile", compile_manager1_report)
    graph.add_node("error", handle_error)

    # Add edges - sequential flow
    graph.add_edge(START, "step1_data_merger")
    graph.add_edge("step1_data_merger", "step2_cep_prioritizer")
    graph.add_edge("step2_cep_prioritizer", "step3_insight_analyzer")
    graph.add_edge("step3_insight_analyzer", "step4_visualizer")
    graph.add_edge("step4_visualizer", "step5_slide_builder")
    graph.add_edge("step5_slide_builder", "compile")
    graph.add_edge("compile", END)
    graph.add_edge("error", END)

    # Add conditional edge for error handling
    # (Optional: add error checks between steps)

    return graph


def compile_manager1_graph(checkpointer=None):
    """
    Compile the Manager 1 graph with optional checkpointing.

    Args:
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Compiled graph ready for execution
    """
    graph = create_manager1_graph()

    if checkpointer:
        return graph.compile(checkpointer=checkpointer)

    return graph.compile()


# Create a default compiled graph
manager1_graph = compile_manager1_graph()


async def run_manager1(initial_state: dict = None) -> Manager1State:
    """
    Run the Manager 1 workflow.

    Args:
        initial_state: Optional initial state override

    Returns:
        Final state with complete report
    """
    # Default initial state
    state = {
        "messages": [],
        "raw_data_png_url": None,
        "raw_data_json": None,
        "cep_analysis": None,
        "cep_tables": None,
        "key_insights": None,
        "visualization_png_url": None,
        "visualization_pdf_url": None,
        "powerpoint_url": None,
        "final_report": None,
        "current_step": "step1",
        "error": None,
    }

    if initial_state:
        state.update(initial_state)

    # Run the graph
    result = await manager1_graph.ainvoke(state)

    return result
