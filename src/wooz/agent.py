"""Orchestrator: initial agent run, then a chat REPL on top."""

from __future__ import annotations

from anthropic import Anthropic
from rich.console import Console
from rich.live import Live
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.text import Text

from wooz.config import (
    MissingAnthropicKeyError,
    get_anthropic_key,
    save_anthropic_key,
)
from wooz.errors import report_anthropic_error
from wooz.llm import (
    AgentEvent,
    DoneEvent,
    TextEvent,
    ThinkingEvent,
    ToolCallEvent,
    ToolResultEvent,
    UsageEvent,
    make_client,
    run_agent,
)
from wooz.playback import PlaybackTracker
from wooz.prompts import SYSTEM_PROMPT, build_user_prompt
from wooz.slash import EXIT_COMMANDS, handle_slash
from wooz.spotify import SpotifyError, current_track, ensure_spotify_open
from wooz.state import WoozState
from wooz.theme import SPOTIFY_GREEN
from wooz.tools import tool_schemas
from wooz.ui import (
    assistant_text,
    format_footer,
    read_user_input,
    thinking,
    tool_call,
    tool_result,
)


def run(
    console: Console, mood: str | None = None, verbose: bool = False, once: bool = False
) -> int:
    """Entry point: check setup, do the first track pick, drop into the REPL.

    With ``once=True`` the agent picks and plays a single track, then exits — no
    interactive prompts — so it can be driven by an automation/agent loop.
    """
    if once:
        try:
            get_anthropic_key()
        except MissingAnthropicKeyError:
            console.print(
                "[red]error:[/] no Anthropic API key. Run [bold]wooz[/] once interactively "
                "to set it up, or set ANTHROPIC_API_KEY."
            )
            return 1
    else:
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
    tracker = PlaybackTracker()
    tracker.start()

    try:
        _run_one_turn(console, claude, state, tracker, hint=mood, verbose=verbose)
        if once:
            return 0
        console.print()
        console.print("[dim]type /help for commands, or just chat in natural language[/]")
        return _repl(console, claude, state, tracker, verbose=verbose)
    finally:
        tracker.stop()


def _repl(
    console: Console,
    claude: Anthropic,
    state: WoozState,
    tracker: PlaybackTracker,
    *,
    verbose: bool,
) -> int:
    while True:
        try:
            user_input = read_user_input(console, tracker=tracker, state=state).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye.[/]")
            return 0

        if not user_input:
            continue
        if user_input in EXIT_COMMANDS:
            console.print("[dim]bye.[/]")
            return 0
        if user_input == "/next":
            _run_one_turn(console, claude, state, tracker, verbose=verbose)
            continue
        if user_input == "/skip":
            _run_one_turn(
                console,
                claude,
                state,
                tracker,
                hint="The last track wasn't right, go in another direction",
                verbose=verbose,
            )
            continue
        if user_input.startswith("/"):
            handle_slash(console, state, user_input)
            continue

        # Free-form text → another agent turn with the user's hint.
        _run_one_turn(console, claude, state, tracker, hint=user_input, verbose=verbose)


def _run_one_turn(
    console: Console,
    claude: Anthropic,
    state: WoozState,
    tracker: PlaybackTracker,
    *,
    hint: str | None = None,
    verbose: bool = False,
) -> None:
    """One agent run: search + play. Mutates `state`. REPL stays alive on recoverable errors."""
    events = run_agent(
        client=claude,
        tools=tool_schemas(),
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(state, current_track(), hint),
    )

    def make_live() -> Spinner:
        footer = format_footer(tracker, state)
        label = f" thinking   {footer}" if footer else " thinking"
        return Spinner("dots", text=Text(label, style=f"bold {SPOTIFY_GREEN}"))

    try:
        with Live(
            make_live(),
            console=console,
            refresh_per_second=4,
            transient=True,
        ) as live:
            while True:
                try:
                    event = next(events)
                except StopIteration:
                    return
                _render_event(console, state, event, verbose=verbose)
                live.update(make_live())
                if isinstance(event, DoneEvent):
                    return
    except Exception as exc:
        report_anthropic_error(console, exc)


def _render_event(
    console: Console,
    state: WoozState,
    event: AgentEvent,
    *,
    verbose: bool,
) -> None:
    if isinstance(event, ThinkingEvent):
        thinking(console, event.text, verbose=verbose)
    elif isinstance(event, ToolCallEvent):
        tool_call(console, event.name, event.input)
        if event.name == "spotify_play_track":
            state.remember(
                uri=str(event.input.get("track_uri", "")),
                vibe=str(event.input.get("vibe", "")),
            )
    elif isinstance(event, ToolResultEvent):
        tool_result(console, event.name, event.output)
    elif isinstance(event, TextEvent):
        assistant_text(console, event.text)
    elif isinstance(event, UsageEvent):
        state.tokens_in += event.input_tokens
        state.tokens_out += event.output_tokens


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
