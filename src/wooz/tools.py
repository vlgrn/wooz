"""Tool schemas + dispatch table for the agent loop.

Each tool exposes one capability to Claude. Schemas follow Anthropic's tool-use
format (https://docs.anthropic.com/en/docs/build-with-claude/tool-use). Dispatch
maps the name Claude picks to the actual Python implementation.
"""

from __future__ import annotations

from typing import Any

from wooz.context import read_claude_session, read_project_context
from wooz.spotify import get_client, search_tracks


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
        {
            "name": "spotify_search",
            "description": (
                "Search Spotify for tracks. Use this to find songs that match the vibe "
                "you decided on. Queries: natural language vibe/mood/genre phrases "
                "(e.g. 'instrumental lofi for focus', 'energetic synthwave') work best. "
                "Returns track URIs you will need for creating playlists."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query. Natural language vibe phrases.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (default 10, MAX 10).",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["query"],
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
    if name == "spotify_search":
        query = str(args["query"])
        limit = min(int(args.get("limit", 10)), 10)
        tracks = search_tracks(get_client(), query=query, limit=limit)
        return {"tracks": tracks}
    raise ValueError(f"Unknown tool: {name}")
