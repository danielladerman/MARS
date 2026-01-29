"""
Manager 2 Graph: Audience-to-Creative Strategy Orchestrator

This graph orchestrates the workflow:
2.1 Audience CEP Analyzer → 2.2 Audience Data Extractor → Step 3 (Build Table)
→ Step 4 (Generate Insights) → 2.3 Slide Builder → Compile

The graph requires competitive data as input (from Phase 1).
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.state.schemas import Manager2State
from src.agents.workers.manager2_workers import (
    agent_2_1_audience_cep_analyzer,
    agent_2_2_audience_data_extractor,
    build_strategic_table,
    generate_strategic_insights,
    agent_2_3_slide_builder,
    compile_manager2_output,
)


def handle_error(state: Manager2State) -> Manager2State:
    """Handle errors in the workflow."""
    return {
        **state,
        "final_output": f"Error occurred: {state.get('error', 'Unknown error')}",
        "current_step": "complete",
    }


def create_manager2_graph():
    """
    Create the Manager 2: Audience-to-Creative Strategy graph.

    Flow:
    START → step1 (Audience CEP Analyzer) → step2 (Audience Data Extractor)
          → step3 (Build Table) → step4 (Generate Insights) → step5 (Slide Builder)
          → compile → END
    """
    # Create the graph with Manager2State
    graph = StateGraph(Manager2State)

    # Add all nodes
    graph.add_node("step1_audience_cep_analyzer", agent_2_1_audience_cep_analyzer)
    graph.add_node("step2_audience_data_extractor", agent_2_2_audience_data_extractor)
    graph.add_node("step3_build_table", build_strategic_table)
    graph.add_node("step4_generate_insights", generate_strategic_insights)
    graph.add_node("step5_slide_builder", agent_2_3_slide_builder)
    graph.add_node("compile", compile_manager2_output)
    graph.add_node("error", handle_error)

    # Add edges - sequential flow
    graph.add_edge(START, "step1_audience_cep_analyzer")
    graph.add_edge("step1_audience_cep_analyzer", "step2_audience_data_extractor")
    graph.add_edge("step2_audience_data_extractor", "step3_build_table")
    graph.add_edge("step3_build_table", "step4_generate_insights")
    graph.add_edge("step4_generate_insights", "step5_slide_builder")
    graph.add_edge("step5_slide_builder", "compile")
    graph.add_edge("compile", END)
    graph.add_edge("error", END)

    return graph


def compile_manager2_graph(checkpointer=None):
    """
    Compile the Manager 2 graph with optional checkpointing.

    Args:
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Compiled graph ready for execution
    """
    graph = create_manager2_graph()

    if checkpointer:
        return graph.compile(checkpointer=checkpointer)

    return graph.compile()


# Create a default compiled graph
manager2_graph = compile_manager2_graph()


async def run_manager2(competitive_tables: str, competitive_dynamics: str, initial_state: dict = None) -> Manager2State:
    """
    Run the Manager 2 workflow.

    Args:
        competitive_tables: Tables from Phase 1 (White Space, Winning, etc.)
        competitive_dynamics: Competitive dynamics analysis from Phase 1
        initial_state: Optional initial state override

    Returns:
        Final state with complete output
    """
    # Default initial state with competitive data
    state = {
        "messages": [],
        "competitive_tables": competitive_tables,
        "competitive_dynamics": competitive_dynamics,
        "audience_segments": None,
        "priority_ceps": None,
        "audience_attributes": None,
        "strategic_table": None,
        "strategic_insights": None,
        "below_threshold_analysis": None,
        "powerpoint_url": None,
        "final_output": None,
        "current_step": "step1",
        "error": None,
    }

    if initial_state:
        state.update(initial_state)

    # Run the graph
    result = await manager2_graph.ainvoke(state)

    return result
