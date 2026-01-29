"""
FastAPI backend for the Strategic Intelligence Multi-Agent System.

Endpoints:
- POST /run - Start a new workflow
- GET /status/{session_id} - Get workflow status
- POST /resume/{session_id} - Resume after checkpoint
"""
import asyncio
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Verify API key
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY not set in environment")

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from src.graphs.master_graph import compile_master_graph

app = FastAPI(
    title="Strategic Intelligence API",
    description="API for M&M's Strategic Intelligence Multi-Agent Workflow",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for sessions
sessions = {}
checkpointer = MemorySaver()


class RunRequest(BaseModel):
    trigger: str = "Generate the strategic intelligence report"


class ResumeRequest(BaseModel):
    user_input: str = "proceed"


class SessionStatus(BaseModel):
    session_id: str
    status: str  # "running", "checkpoint", "completed", "error"
    current_phase: Optional[str] = None
    phase1_output: Optional[str] = None
    phase2_output: Optional[str] = None
    checkpoint_message: Optional[str] = None
    error: Optional[str] = None


@app.post("/run", response_model=dict)
async def start_workflow(request: RunRequest, background_tasks: BackgroundTasks):
    """
    Start a new Strategic Intelligence workflow.

    Returns session_id immediately, workflow runs in background.
    """
    session_id = str(uuid.uuid4())[:8]

    sessions[session_id] = {
        "status": "running",
        "current_phase": "phase1",
        "phase1_output": None,
        "phase2_output": None,
        "checkpoint_message": None,
        "error": None,
    }

    # Run Phase 1 in background
    background_tasks.add_task(run_phase1, session_id, request.trigger)

    return {"session_id": session_id, "message": "Workflow started"}


async def run_phase1(session_id: str, trigger: str):
    """Run Phase 1 of the workflow."""
    try:
        graph = compile_master_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": session_id}}

        initial_state = {
            "messages": [HumanMessage(content=trigger)],
            "competitive_intelligence": None,
            "creative_intelligence": None,
            "user_guidance": None,
            "current_phase": "phase1",
            "user_decision": None,
            "error": None,
        }

        # Run until checkpoint
        result = None
        async for event in graph.astream(initial_state, config, stream_mode="updates"):
            for node_name, node_output in event.items():
                if node_name == "present_checkpoint":
                    # Extract checkpoint message
                    messages = node_output.get("messages", [])
                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            sessions[session_id]["checkpoint_message"] = msg.content
                result = node_output

        # Phase 1 complete, waiting at checkpoint
        sessions[session_id]["status"] = "checkpoint"
        sessions[session_id]["current_phase"] = "checkpoint"
        sessions[session_id]["phase1_output"] = sessions[session_id]["checkpoint_message"]

    except Exception as e:
        sessions[session_id]["status"] = "error"
        sessions[session_id]["error"] = str(e)


@app.get("/status/{session_id}", response_model=SessionStatus)
async def get_status(session_id: str):
    """
    Get the current status of a workflow session.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionStatus(
        session_id=session_id,
        **sessions[session_id]
    )


@app.post("/resume/{session_id}", response_model=dict)
async def resume_workflow(session_id: str, request: ResumeRequest, background_tasks: BackgroundTasks):
    """
    Resume workflow after checkpoint with user decision.

    user_input options:
    - "proceed" / "continue" - Continue to Phase 2
    - "stop" - End workflow at Phase 1
    - Any other text - Guidance for Phase 2
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if sessions[session_id]["status"] != "checkpoint":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume: workflow status is '{sessions[session_id]['status']}'"
        )

    sessions[session_id]["status"] = "running"
    sessions[session_id]["current_phase"] = "phase2"

    # Run Phase 2 in background
    background_tasks.add_task(run_phase2, session_id, request.user_input)

    return {"message": f"Resuming workflow with: {request.user_input}"}


async def run_phase2(session_id: str, user_input: str):
    """Run Phase 2 of the workflow."""
    try:
        graph = compile_master_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": session_id}}

        # Resume with user input
        result = await graph.ainvoke(
            Command(resume=HumanMessage(content=user_input)),
            config
        )

        # Extract final output
        messages = result.get("messages", [])
        final_output = ""
        for msg in messages[-3:]:  # Get last few messages
            if isinstance(msg, AIMessage):
                final_output += msg.content + "\n\n"

        sessions[session_id]["status"] = "completed"
        sessions[session_id]["current_phase"] = "complete"
        sessions[session_id]["phase2_output"] = final_output

    except Exception as e:
        sessions[session_id]["status"] = "error"
        sessions[session_id]["error"] = str(e)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Strategic Intelligence API"}


@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    return {
        "sessions": [
            {"session_id": sid, "status": data["status"], "phase": data["current_phase"]}
            for sid, data in sessions.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
