from .manager1_workers import (
    agent_1_1_data_merger,
    agent_1_2_cep_prioritizer,
    agent_1_3_insight_analyzer,
    agent_1_4_visualizer,
    agent_1_5_slide_builder,
    compile_manager1_report,
)
from .manager2_workers import (
    agent_2_1_audience_cep_analyzer,
    agent_2_2_audience_data_extractor,
    build_strategic_table,
    generate_strategic_insights,
    agent_2_3_slide_builder,
    compile_manager2_output,
)

__all__ = [
    # Manager 1 workers
    "agent_1_1_data_merger",
    "agent_1_2_cep_prioritizer",
    "agent_1_3_insight_analyzer",
    "agent_1_4_visualizer",
    "agent_1_5_slide_builder",
    "compile_manager1_report",
    # Manager 2 workers
    "agent_2_1_audience_cep_analyzer",
    "agent_2_2_audience_data_extractor",
    "build_strategic_table",
    "generate_strategic_insights",
    "agent_2_3_slide_builder",
    "compile_manager2_output",
]
