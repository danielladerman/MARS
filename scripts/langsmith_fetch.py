#!/usr/bin/env python3
"""
LangSmith Trace Fetcher - Fetch and analyze traces from LangSmith.

Usage:
    python scripts/langsmith_fetch.py                    # Fetch last 5 traces
    python scripts/langsmith_fetch.py --limit 10        # Fetch last 10 traces
    python scripts/langsmith_fetch.py --errors          # Fetch only error traces
    python scripts/langsmith_fetch.py --trace-id <id>   # Fetch specific trace
    python scripts/langsmith_fetch.py --json            # Output as JSON
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "default")


def get_headers():
    """Get API headers."""
    return {
        "x-api-key": LANGSMITH_API_KEY,
        "Content-Type": "application/json",
    }


def fetch_traces(
    limit: int = 5,
    errors_only: bool = False,
    project_name: Optional[str] = None,
) -> list:
    """Fetch recent traces from LangSmith."""
    project = project_name or LANGSMITH_PROJECT

    # First get the project ID
    url = f"{LANGSMITH_ENDPOINT}/api/v1/sessions"
    params = {"name": project}

    response = httpx.get(url, headers=get_headers(), params=params, timeout=30)
    response.raise_for_status()

    projects = response.json()
    if not projects:
        print(f"Project '{project}' not found")
        return []

    project_id = projects[0]["id"]

    # Fetch runs (traces)
    url = f"{LANGSMITH_ENDPOINT}/api/v1/runs/query"

    # Build payload - session is a list of project IDs
    payload = {
        "session": [project_id],
        "limit": limit,
        "is_root": True,  # Only top-level runs
        "select": [
            "id",
            "name",
            "run_type",
            "status",
            "error",
            "start_time",
            "end_time",
            "total_tokens",
            "prompt_tokens",
            "completion_tokens",
            "inputs",
            "outputs",
            "feedback_stats",
        ],
    }

    if errors_only:
        payload["error"] = True

    response = httpx.post(url, headers=get_headers(), json=payload, timeout=30)
    response.raise_for_status()

    return response.json().get("runs", [])


def fetch_trace_detail(trace_id: str) -> dict:
    """Fetch detailed trace information including child runs."""
    url = f"{LANGSMITH_ENDPOINT}/api/v1/runs/{trace_id}"

    response = httpx.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    run = response.json()

    # Fetch child runs using trace filter
    children_url = f"{LANGSMITH_ENDPOINT}/api/v1/runs/query"
    payload = {
        "trace": [trace_id],
        "limit": 100,
        "select": [
            "id",
            "name",
            "run_type",
            "status",
            "error",
            "start_time",
            "end_time",
            "inputs",
            "outputs",
        ],
    }

    try:
        response = httpx.post(children_url, headers=get_headers(), json=payload, timeout=30)
        response.raise_for_status()
        run["child_runs"] = response.json().get("runs", [])
    except Exception:
        run["child_runs"] = []  # Gracefully handle if child fetch fails

    return run


def format_trace_summary(trace: dict) -> str:
    """Format a trace for human-readable output."""
    lines = []

    status_emoji = "✅" if trace.get("status") == "success" else "❌"

    lines.append(f"\n{'='*60}")
    lines.append(f"{status_emoji} **{trace.get('name', 'Unknown')}**")
    lines.append(f"   ID: {trace.get('id')}")
    lines.append(f"   Type: {trace.get('run_type')}")
    lines.append(f"   Status: {trace.get('status')}")

    if trace.get("start_time"):
        start = datetime.fromisoformat(trace["start_time"].replace("Z", "+00:00"))
        lines.append(f"   Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")

    if trace.get("end_time") and trace.get("start_time"):
        start = datetime.fromisoformat(trace["start_time"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(trace["end_time"].replace("Z", "+00:00"))
        duration = (end - start).total_seconds()
        lines.append(f"   Duration: {duration:.2f}s")

    if trace.get("total_tokens"):
        lines.append(f"   Tokens: {trace['total_tokens']} (prompt: {trace.get('prompt_tokens', 0)}, completion: {trace.get('completion_tokens', 0)})")

    if trace.get("error"):
        lines.append(f"\n   🔴 ERROR: {trace['error']}")

    # Truncate inputs/outputs for summary
    if trace.get("inputs"):
        inputs_str = json.dumps(trace["inputs"])[:200]
        lines.append(f"\n   📥 Inputs: {inputs_str}...")

    if trace.get("outputs"):
        outputs_str = json.dumps(trace["outputs"])[:200]
        lines.append(f"   📤 Outputs: {outputs_str}...")

    return "\n".join(lines)


def format_trace_detail(trace: dict) -> str:
    """Format detailed trace with child runs."""
    lines = [format_trace_summary(trace)]

    if trace.get("child_runs"):
        lines.append(f"\n   📊 Child Runs ({len(trace['child_runs'])}):")

        for child in trace["child_runs"][:20]:  # Limit to 20 child runs
            status = "✅" if child.get("status") == "success" else "❌"
            name = child.get("name", "Unknown")[:40]
            run_type = child.get("run_type", "")
            lines.append(f"      {status} [{run_type}] {name}")

            if child.get("error"):
                error_short = str(child["error"])[:100]
                lines.append(f"         🔴 {error_short}")

    # Full error details
    if trace.get("error"):
        lines.append(f"\n{'='*60}")
        lines.append("🔴 FULL ERROR DETAILS:")
        lines.append(trace["error"])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch traces from LangSmith")
    parser.add_argument("--limit", type=int, default=5, help="Number of traces to fetch")
    parser.add_argument("--errors", action="store_true", help="Fetch only error traces")
    parser.add_argument("--trace-id", type=str, help="Fetch specific trace by ID")
    parser.add_argument("--project", type=str, help="Project name (default: from .env)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not LANGSMITH_API_KEY:
        print("Error: LANGSMITH_API_KEY not set in environment")
        sys.exit(1)

    try:
        if args.trace_id:
            trace = fetch_trace_detail(args.trace_id)
            if args.json:
                print(json.dumps(trace, indent=2, default=str))
            else:
                print(format_trace_detail(trace))
        else:
            traces = fetch_traces(
                limit=args.limit,
                errors_only=args.errors,
                project_name=args.project,
            )

            if args.json:
                print(json.dumps(traces, indent=2, default=str))
            else:
                print(f"\n🔍 LangSmith Traces - Project: {args.project or LANGSMITH_PROJECT}")
                print(f"   Fetched: {len(traces)} traces")

                if not traces:
                    print("\n   No traces found.")
                else:
                    for trace in traces:
                        print(format_trace_summary(trace))

                print(f"\n{'='*60}")
                print(f"View in LangSmith: https://smith.langchain.com/o/default/projects/{args.project or LANGSMITH_PROJECT}")

    except httpx.HTTPStatusError as e:
        print(f"API Error: {e.response.status_code} - {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
