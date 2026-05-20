"""High-level orchestrator: first agent run, then a chat REPL on top."""

from __future__ import annotations

from dataclasses import dataclass, field

from anthropic import Anthropic
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
from wooz.spotify import (
    SpotifyError,
    ensure_spotify_open,
    pause_playback,
    player_state,
    resume_playback,
)
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
    "4. spotify_play_track — ONCE, the single best track. Include a short `vibe` "
    "phrase capturing this track's mood.\n"
    "5. Final summary — ONE short sentence describing the vibe (no narration "
    "between tool calls).\n"
    "\n"
    "Rules:\n"
    "- Single track only. Never queue or play more than one.\n"
    "- No artist:X queries — they return noise."
)

SLASH_HELP = """\
[bold]commands[/]
  [cyan]/next[/]            play a different track (re-reads context)
  [cyan]/pause[/]           pause playback
  [cyan]/play[/]            resume playback
  [cyan]/vibe[/]            show the current vibe
  [cyan]/help[/]            show this help
  [cyan]/exit[/]            quit (also /quit, /q, Ctrl+D)
or just type anything in natural language ([dim]e.g. "more upbeat"[/])"""

EXIT_COMMANDS = {"/exit", "/quit", "/q"}


@dataclass
class WoozState:
    vibe: str = ""
    recent_tracks: list[str] = field(default_factory=list)  # most-recent-last URIs

    def remember(self, uri: str, vibe: str) -> None:
        if uri and uri not in self.recent_tracks:
            self.recent_tracks.append(uri)
            # cap to last 20
            self.recent_tracks = self.recent_tracks[-20:]
        if vibe:
            self.vibe = vibe


def _build_user_prompt(state: WoozState, hint: str | None) -> str:
    if not state.vibe and not state.recent_tracks and not hint:
        return "DJ me a track for what I'm working on right now."
    parts = ["DJ me another track for what I'm working on right now."]
    if state.vibe:
        parts.append(
            f"Current vibe: {state.vibe}. Find a different track in the same vibe "
            "(unless the user hint below asks to shift it)."
        )
    if state.recent_tracks:
        avoid = ", ".join(state.recent_tracks[-15:])
        parts.append(f"DO NOT repeat any of these recently played URIs: {avoid}")
    if hint:
        parts.append(f"User hint: {hint}")
    return "\n\n".join(parts)


def _ensure_anthropic_key(console: Console) -> str:
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


def _run_one_turn(
    console: Console,
    claude: Anthropic,
    state: WoozState,
    *,
    hint: str | None = None,
    verbose: bool = False,
) -> None:
    """Drive one agent run: search + play one track. Updates state in place."""
    user_prompt = _build_user_prompt(state, hint)

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
            # Capture vibe + URI as soon as Claude commits to a track.
            if event.name == "spotify_play_track":
                state.remember(
                    uri=str(event.input.get("track_uri", "")),
                    vibe=str(event.input.get("vibe", "")),
                )
        elif isinstance(event, ToolResultEvent):
            tool_result(console, event.name, event.output)
        elif isinstance(event, TextEvent):
            assistant_text(console, event.text)
        elif isinstance(event, DoneEvent):
            return


def _handle_slash(console: Console, state: WoozState, cmd: str) -> None:
    head = cmd.split(maxsplit=1)[0]
    if head == "/help":
        console.print(SLASH_HELP)
    elif head == "/vibe":
        if state.vibe:
            console.print(f"[bold]current vibe:[/] {state.vibe}")
        else:
            console.print("[dim]no vibe set yet.[/]")
    elif head == "/pause":
        try:
            pause_playback()
            console.print("[dim]⏸  paused[/]")
        except SpotifyError as exc:
            console.print(f"[red]{exc}[/]")
    elif head == "/play":
        try:
            resume_playback()
            state_name = player_state()
            console.print(f"[dim]▶  {state_name}[/]")
        except SpotifyError as exc:
            console.print(f"[red]{exc}[/]")
    else:
        console.print(f"[red]unknown command:[/] {head}  [dim](/help)[/]")


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

    claude = make_client()
    state = WoozState()

    # First run: full discovery, pick a track, play it.
    _run_one_turn(console, claude, state, hint=mood, verbose=verbose)

    console.print()
    console.print("[dim]type /help for commands, or just chat in natural language[/]")

    # Chat REPL.
    while True:
        try:
            user_input = Prompt.ask("[bold green]>[/]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye.[/]")
            return 0

        if not user_input:
            continue
        if user_input in EXIT_COMMANDS:
            console.print("[dim]bye.[/]")
            return 0
        if user_input == "/next":
            _run_one_turn(console, claude, state, verbose=verbose)
            continue
        if user_input.startswith("/"):
            _handle_slash(console, state, user_input)
            continue

        # Free-form natural language → new agent turn with the hint
        _run_one_turn(console, claude, state, hint=user_input, verbose=verbose)
