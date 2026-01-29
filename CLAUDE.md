# Claude Code Instructions for This Project

## Project Overview
Multi-agent LangGraph workflow for M&M's Strategic Intelligence with:
- Phase 1: Competitive Analysis (Manager 1 with 5 sub-agents)
- Phase 2: Audience-to-Creative Strategy (Manager 2 with 3 sub-agents)
- Human-in-the-loop checkpoint between phases
- MCP integration with two servers (web-dan, web-aditi)

## LangSmith Debugging Skill

When debugging workflow issues or when the user mentions "traces", "LangSmith", or "debug", use the custom fetch script:

### Quick Commands

**Fetch recent traces:**
```bash
python3 scripts/langsmith_fetch.py --limit 5
```

**Fetch only error traces:**
```bash
python3 scripts/langsmith_fetch.py --errors --limit 10
```

**Fetch specific trace by ID:**
```bash
python3 scripts/langsmith_fetch.py --trace-id <trace-id>
```

**Output as JSON for analysis:**
```bash
python3 scripts/langsmith_fetch.py --limit 5 --json
```

### Debugging Workflow

1. **After running the workflow**, fetch recent traces to see execution flow
2. **For errors**, use `--errors` flag to filter to failed runs
3. **For detailed analysis**, use `--trace-id` with a specific ID to see child runs
4. **JSON output** is useful for parsing specific fields

### LangSmith Project
- Project name: `mars` (configured in .env)
- View UI: https://smith.langchain.com

## Running the Workflow

**CLI mode:**
```bash
python3 main.py
```

**Streamlit UI:**
```bash
streamlit run app.py
```

**FastAPI server:**
```bash
uvicorn api:app --reload
```

## MCP Servers

- **web-dan**: `https://web-dan.up.railway.app` - Competitive analysis tools, slide builders
- **web-aditi**: `https://web-aditi.up.railway.app` - Visual tools (index_visual, demo_audiences)

## Key Files

- `src/graphs/master_graph.py` - Main orchestrator with HITL checkpoint
- `src/agents/workers/manager1_workers.py` - Phase 1 agents (1.1-1.5)
- `src/agents/workers/manager2_workers.py` - Phase 2 agents (2.1-2.3)
- `src/tools/mcp_tools.py` - MCP client and tool wrappers
- `scripts/langsmith_fetch.py` - LangSmith trace fetcher
