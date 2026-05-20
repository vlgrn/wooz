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
    "You are wooz, an AI DJ for developer terminals. Given the user's current project "
    "context, infer the right music vibe for what they are working on. "
    "Use the tools to gather context first. Be concise."
)

USER_PROMPT = (
    "Look at the user's current project. In 2-3 sentences, describe the vibe of music "
    "that would fit what they are working on right now (energy, mood, genre). "
    "Be specific to what you find."
)


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
