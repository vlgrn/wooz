"""High-level orchestrator: kicks off the agent loop, handles top-level errors."""

from __future__ import annotations

from rich.console import Console

from wooz.config import MissingAnthropicKeyError, get_anthropic_key
from wooz.llm import (
    DoneEvent,
    TextEvent,
    ThinkingEvent,
    ToolCallEvent,
    ToolResultEvent,
    make_client,
    run_agent,
)
from wooz.spotify import SpotifyAuthError, get_client, has_valid_token
from wooz.tools import tool_schemas
from wooz.ui import assistant_text, thinking, tool_call, tool_result

SYSTEM_PROMPT = (
    "You are wooz, an AI DJ for developer terminals. "
    "\n\n"
    "STRICT workflow — do not deviate:\n"
    "1. read_project_context — ONCE\n"
    "2. read_claude_session — ONCE\n"
    "3. spotify_search — AT MOST 2 calls, each with a single focused query that "
    "captures the vibe directly. Aim for ~20 tracks across the two calls.\n"
    "4. Final summary — ONE short sentence stating the vibe you picked.\n"
    "\n"
    "RULES:\n"
    "- Do NOT narrate between tool calls. No 'let me check', no 'going deeper', no "
    "'let me round out'. Just call the next tool silently.\n"
    "- Do NOT refine searches after the first two. Commit to what you got.\n"
    "- Do NOT use artist:X queries — they return poor results. Use vibe/genre/mood "
    "phrases instead."
)

USER_PROMPT = "DJ me a set for what I'm working on right now."


def run(
    console: Console,
    mood: str | None = None,
    duration: int | None = None,
    verbose: bool = False,
) -> int:
    """Run wooz: verify auth, then drive the Claude agent loop with a visible UI."""
    try:
        get_anthropic_key()
    except MissingAnthropicKeyError as exc:
        console.print(f"[red]error:[/] {exc}")
        return 1
    console.print("[green]✓[/] anthropic key found")

    if not has_valid_token():
        console.print("[dim]first run — opening Spotify auth in your browser...[/]")
    try:
        sp = get_client()
        user = sp.current_user()
    except SpotifyAuthError as exc:
        console.print(f"[red]error:[/] {exc}")
        return 1
    except Exception as exc:
        console.print(f"[red]error:[/] spotify auth failed: {exc}")
        return 1
    who = user.get("display_name") or user.get("id")
    console.print(f"[green]✓[/] spotify authed as [bold]{who}[/]\n")

    user_prompt = USER_PROMPT
    if mood:
        user_prompt += f"\n\nThe user wants the vibe to lean: {mood}."
    if duration:
        user_prompt += f"\n\nTarget playlist length: ~{duration} minutes."

    claude = make_client()
    events = run_agent(
        client=claude,
        tools=tool_schemas(),
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    while True:
        with console.status("[bold cyan]thinking[/]", spinner="dots"):
            try:
                event = next(events)
            except StopIteration:
                break

        if isinstance(event, ThinkingEvent):
            thinking(console, event.text, verbose=verbose)
        elif isinstance(event, ToolCallEvent):
            tool_call(console, event.name, event.input)
        elif isinstance(event, ToolResultEvent):
            tool_result(console, event.name, event.output)
        elif isinstance(event, TextEvent):
            assistant_text(console, event.text)
        elif isinstance(event, DoneEvent):
            return 0

    return 0
