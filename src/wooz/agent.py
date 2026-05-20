"""High-level orchestrator: kicks off the agent loop, handles top-level errors."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt

from wooz.config import (
    MissingAnthropicKeyError,
    get_anthropic_key,
    save_anthropic_key,
)
from wooz.llm import (
    DoneEvent,
    TextEvent,
    ThinkingEvent,
    ToolCallEvent,
    ToolResultEvent,
    make_client,
    run_agent,
)
from wooz.spotify import SpotifyError, ensure_spotify_open
from wooz.tools import tool_schemas
from wooz.ui import assistant_text, thinking, tool_call, tool_result

SYSTEM_PROMPT = (
    "You are wooz, an AI DJ for developer terminals. Pick ONE track that matches "
    "what the user is working on right now.\n"
    "\n"
    "STRICT workflow:\n"
    "1. read_project_context — ONCE\n"
    "2. read_claude_session — ONCE\n"
    "3. spotify_search — at most TWO calls, focused vibe queries\n"
    "4. spotify_play_track — ONCE, the single best track from your searches\n"
    "5. Final summary — ONE short sentence describing the vibe\n"
    "\n"
    "Rules:\n"
    "- Single track only. Never queue or play more than one.\n"
    "- No narration between tool calls.\n"
    "- No artist:X queries — they return noise."
)

USER_PROMPT = "DJ me a track for what I'm working on right now."


def _ensure_anthropic_key(console: Console) -> str:
    """Return the key, prompting + saving it if not configured anywhere."""
    try:
        return get_anthropic_key()
    except MissingAnthropicKeyError:
        pass
    console.print(
        "[yellow]No Anthropic API key found.[/]  "
        "[dim](get one at https://console.anthropic.com/settings/keys)[/]"
    )
    key = Prompt.ask("[bold]Paste your key[/]").strip()
    while not key.startswith("sk-ant-"):
        console.print("[red]That doesn't look like an Anthropic key (starts with sk-ant-).[/]")
        key = Prompt.ask("[bold]Paste your key[/]").strip()
    save_anthropic_key(key)
    console.print("[green]✓[/] saved to [dim]~/.wooz/.env[/]\n")
    return key


def run(
    console: Console,
    mood: str | None = None,
    verbose: bool = False,
) -> int:
    _ensure_anthropic_key(console)
    console.print("[green]✓[/] anthropic key ready")

    try:
        ensure_spotify_open()
    except SpotifyError as exc:
        console.print(f"[red]error:[/] {exc}")
        return 1
    console.print("[green]✓[/] spotify ready\n")

    user_prompt = USER_PROMPT
    if mood:
        user_prompt += f"\n\nVibe hint from the user: {mood}."

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
