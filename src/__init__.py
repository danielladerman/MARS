"""
Strategic Intelligence Multi-Agent System

A LangGraph implementation of a marketing intelligence workflow with:
- Master Orchestrator with Human-in-the-Loop
- Manager 1: Competitive Analyzer
- Manager 2: Audience-to-Creative Strategy Orchestrator
"""
from .graphs.master_graph import (
    compile_master_graph,
    run_strategic_intelligence,
    resume_after_checkpoint,
)
from .graphs.manager1_graph import run_manager1, manager1_graph
from .graphs.manager2_graph import run_manager2, manager2_graph
from .state.schemas import MasterState, Manager1State, Manager2State

__all__ = [
    "compile_master_graph",
    "run_strategic_intelligence",
    "resume_after_checkpoint",
    "run_manager1",
    "run_manager2",
    "manager1_graph",
    "manager2_graph",
    "MasterState",
    "Manager1State",
    "Manager2State",
]
