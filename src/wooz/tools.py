"""Tool schemas + dispatch table for the agent loop.

Each tool exposes one capability to Claude. Schemas follow Anthropic's tool-use
format. Dispatch maps the name Claude picks to the actual Python implementation.
"""

from __future__ import annotations

from typing import Any

from wooz.context import read_claude_session, read_project_context
from wooz.spotify import get_search_client, play_track, search_tracks


def tool_schemas() -> list[dict[str, Any]]:
    return [
        {
            "name": "read_project_context",
            "description": (
                "Snapshot the user's current project: working directory, project name, "
                "git branch, last 5 commit messages, top file extensions, and a short "
                "README excerpt if available. Call this first to understand what the "
                "user is building."
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
                "for this project. Use to infer mood/tone — debugging, building, "
                "frustrated, focused?"
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
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
                "Search Spotify for tracks. Natural-language vibe/mood/genre phrases "
                "work best (e.g. 'instrumental lofi for focus'). Returns track URIs."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "spotify_play_track",
            "description": (
                "Play ONE Spotify track on the user's local Spotify app. Pass the "
                "spotify:track:... URI of the single track you want to play right "
                "now. wooz plays one track at a time — never queue multiple."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "track_uri": {
                        "type": "string",
                        "description": "Spotify track URI to play.",
                    },
                    "track_name": {
                        "type": "string",
                        "description": "Display name 'Track — Artist' for the UI.",
                    },
                    "vibe": {
                        "type": "string",
                        "description": (
                            "Short phrase capturing the vibe of this track "
                            "(e.g. 'focused instrumental lofi'). Used to find "
                            "the next track in the same mood."
                        ),
                    },
                },
                "required": ["track_uri", "track_name", "vibe"],
            },
        },
    ]


def dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "read_project_context":
        return read_project_context().model_dump()
    if name == "read_claude_session":
        limit = int(args.get("limit", 20))
        messages = read_claude_session(limit=limit)
        return {"messages": [m.model_dump() for m in messages]}
    if name == "spotify_search":
        query = str(args["query"])
        limit = min(int(args.get("limit", 10)), 10)
        tracks = search_tracks(get_search_client(), query=query, limit=limit)
        return {"tracks": tracks}
    if name == "spotify_play_track":
        uri = str(args["track_uri"])
        play_track(uri)
        return {"now_playing": str(args.get("track_name", uri))}
    raise ValueError(f"Unknown tool: {name}")
