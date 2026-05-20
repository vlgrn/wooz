"""Tool schemas + dispatch table for the agent loop.

Each tool exposes one capability to Claude. Schemas follow Anthropic's tool-use
format. Dispatch maps the name Claude picks to the actual Python implementation.
"""

from __future__ import annotations

import re
from typing import Any

from spotipy.exceptions import SpotifyException

from wooz.context import read_claude_session, read_project_context
from wooz.spotify import SpotifyError, get_search_client, play_track, search_tracks

TRACK_URI_RE = re.compile(r"^spotify:track:[A-Za-z0-9]{22}$")


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
        try:
            tracks = search_tracks(get_search_client(), query=query, limit=limit)
        except SpotifyException as exc:
            return {
                "error": (
                    f"Spotify API error during search ({exc.http_status}): {exc.msg}. "
                    "Try again with a different query."
                ),
            }
        except Exception as exc:
            return {"error": f"search failed: {exc}. Try again."}
        if not tracks:
            return {
                "tracks": [],
                "note": (
                    f"no tracks matched '{query}'. Broaden the query "
                    "(drop specific artists, use mood/genre words only) and try again."
                ),
            }
        return {"tracks": tracks}
    if name == "spotify_play_track":
        uri = str(args["track_uri"])
        if not TRACK_URI_RE.match(uri):
            return {
                "error": (
                    f"invalid track URI: {uri!r}. Must be a real Spotify URI returned "
                    "by spotify_search (format: spotify:track:<22-char-id>). "
                    "Do not invent URIs — call spotify_search first."
                ),
            }
        try:
            play_track(uri)
        except SpotifyError as exc:
            return {"error": str(exc)}
        return {"now_playing": str(args.get("track_name", uri))}
    raise ValueError(f"Unknown tool: {name}")
