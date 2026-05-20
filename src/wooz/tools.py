"""Tool schemas + dispatch table for the agent loop.

Each tool exposes one capability to Claude. Schemas follow Anthropic's tool-use
format (https://docs.anthropic.com/en/docs/build-with-claude/tool-use). Dispatch
maps the name Claude picks to the actual Python implementation.
"""

from __future__ import annotations

from typing import Any

from wooz.context import read_project_context


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
    ]


def dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by name. Returns a JSON-serialisable dict."""
    if name == "read_project_context":
        return read_project_context().model_dump()
    raise ValueError(f"Unknown tool: {name}")
