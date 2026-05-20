"""Tool schemas + dispatch table for the agent loop.

Each tool exposes one capability to Claude. Schemas follow Anthropic's tool-use
format (https://docs.anthropic.com/en/docs/build-with-claude/tool-use). Dispatch
maps the name Claude picks to the actual Python implementation.
"""

from __future__ import annotations

from typing import Any

from wooz.context import read_claude_session, read_project_context


def tool_schemas() -> list[dict[str, Any]]:
    """All tool schemas Claude can choose from."""
    return [
        {
            "name": "read_project_context",
            "description": (
                "Snapshot the user's current project: working directory, project name, "
                "git branch, last 5 commit messages, top file extensions, and a short "
                "README excerpt if available. Use this first to understand what the user "
                "is building."
            ),
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "name": "read_claude_session",
            "description": (
                "Read the last N messages from the user's current Claude Code session "
                "for this project. Use this to infer mood/tone — are they debugging, "
                "building something new, frustrated, focused? Returns role + text per "
                "message."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of recent messages to return (default 20).",
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": [],
            },
        },
    ]


def dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by name. Returns a JSON-serialisable dict."""
    if name == "read_project_context":
        return read_project_context().model_dump()
    if name == "read_claude_session":
        limit = int(args.get("limit", 20))
        messages = read_claude_session(limit=limit)
        return {"messages": [m.model_dump() for m in messages]}
    raise ValueError(f"Unknown tool: {name}")
