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
            "name": "list_tools",
            "description": (
                "Returns the full catalog of tools you can call, with a short "
                "description of when each is useful. Call this first to see what's "
                "available before deciding what to do."
            ),
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "name": "read_project_context",
            "description": (
                "Reveals what the user is building right now: working directory, "
                "project name, git branch, last 5 commit messages, top file "
                "extensions, and a short README excerpt. Use this when you need to "
                "infer the user's mood or activity from their work. Skip it if the "
                "user has already told you what they want to hear."
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
                "Surfaces the last N messages from the user's current Claude Code "
                "session for this project. Best signal for their emotional state — "
                "stuck, flowing, debugging, exploring. Use when project context "
                "alone doesn't tell you enough about their headspace, and skip it "
                "if the user has already named what they want to hear."
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
                "Searches Spotify and returns real track URIs. Any query works — "
                "vibe phrases ('instrumental lofi for focus'), genres, artist "
                "names, song titles. Call as many times as you need to find a "
                "track you can confidently play."
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
                "Plays ONE Spotify track on the user's local Spotify app. Only "
                "call when you're confident the track fits the user's request. "
                "wooz plays one track at a time — never queue more than one."
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
    if name == "list_tools":
        return {
            "tools": [
                {"name": t["name"], "description": t["description"]}
                for t in tool_schemas()
                if t["name"] != "list_tools"
            ],
        }
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
