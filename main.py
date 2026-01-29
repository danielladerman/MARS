"""
Strategic Intelligence Multi-Agent System - Main Entry Point

This demonstrates how to run the complete workflow with Human-in-the-Loop.

Usage:
    python main.py

The workflow:
1. Runs Phase 1 (Competitive Analysis)
2. Presents results and pauses for user confirmation
3. After user confirms, runs Phase 2 (Audience-to-Creative Strategy)
4. Delivers final output
"""
import asyncio
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

# Load environment variables
load_dotenv()

# Verify OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set")
    print("Create a .env file with: OPENAI_API_KEY=your-key-here")
    exit(1)


async def run_interactive_workflow():
    """
    Run the Strategic Intelligence workflow interactively.

    This function demonstrates the Human-in-the-Loop pattern where:
    1. Phase 1 runs automatically
    2. Execution pauses for user input
    3. Phase 2 runs after user confirms
    """
    # Import here to avoid circular imports
    from src.graphs.master_graph import compile_master_graph

    print("=" * 60)
    print("STRATEGIC INTELLIGENCE MULTI-AGENT SYSTEM")
    print("=" * 60)
    print("\nStarting Phase 1: Competitive Intelligence Collection...")
    print("-" * 60)

    # Create checkpointer for state persistence
    checkpointer = MemorySaver()

    # Compile the master graph with HITL interrupt
    graph = compile_master_graph(checkpointer=checkpointer)

    # Configuration with thread ID for state tracking
    thread_id = "strategic-intel-session-1"
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

    # Run Phase 1 (will pause at checkpoint)
    print("\n[Running Phase 1...]\n")

    result = None
    async for event in graph.astream(initial_state, config, stream_mode="updates"):
        # Print progress updates
        for node_name, node_output in event.items():
            if node_name == "phase1":
                print("✓ Phase 1 complete - Competitive analysis generated")
            elif node_name == "present_checkpoint":
                print("\n" + "=" * 60)
                print("CHECKPOINT: AWAITING USER CONFIRMATION")
                print("=" * 60)

                # Display the checkpoint message
                messages = node_output.get("messages", [])
                for msg in messages:
                    if isinstance(msg, AIMessage):
                        print(msg.content)

        result = node_output

    # Get user input at checkpoint
    print("\n" + "-" * 60)
    user_input = input("\nYour response: ").strip()

    if not user_input:
        user_input = "proceed"

    print("-" * 60)
    print(f"\nReceived: '{user_input}'")

    # Resume execution with user input
    if user_input.lower() in ["stop", "no", "end"]:
        print("\n[Stopping workflow as requested]")
        # Resume with stop command
        final_result = await graph.ainvoke(
            Command(resume=HumanMessage(content=user_input)),
            config
        )
    else:
        print("\n[Proceeding to Phase 2: Audience-to-Creative Strategy...]")
        final_result = await graph.ainvoke(
            Command(resume=HumanMessage(content=user_input)),
            config
        )

    # Display final output
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)

    # Print the final messages
    messages = final_result.get("messages", [])
    for msg in messages[-2:]:  # Show last 2 messages
        if isinstance(msg, AIMessage):
            print(msg.content)

    return final_result


async def run_phase1_only():
    """
    Run only Phase 1 (Competitive Analysis) without HITL.
    Useful for testing or when only competitive data is needed.
    """
    from src.graphs.manager1_graph import run_manager1

    print("Running Phase 1 only (Competitive Analysis)...")
    result = await run_manager1()
    print("\n" + result.get("final_report", "No report generated"))
    return result


async def run_phase2_only(competitive_data: str, dynamics: str):
    """
    Run only Phase 2 (Audience-to-Creative) with provided competitive data.
    Useful for testing or re-running Phase 2 with different inputs.
    """
    from src.graphs.manager2_graph import run_manager2

    print("Running Phase 2 only (Audience-to-Creative Strategy)...")
    result = await run_manager2(competitive_data, dynamics)
    print("\n" + result.get("final_output", "No output generated"))
    return result


def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "phase1":
            asyncio.run(run_phase1_only())
        elif command == "phase2":
            # For phase2, you'd need to provide the competitive data
            print("Phase 2 requires competitive data from Phase 1")
            print("Run the full workflow instead: python main.py")
        else:
            print(f"Unknown command: {command}")
            print("Usage: python main.py [phase1|phase2]")
    else:
        # Run full interactive workflow
        asyncio.run(run_interactive_workflow())


if __name__ == "__main__":
    main()
