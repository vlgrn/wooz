"""Step renderer + bordered input prompt with a live playback footer."""

from __future__ import annotations

from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel

from wooz.playback import PlaybackState, PlaybackTracker
from wooz.theme import ASSISTANT_PINK, SPOTIFY_GREEN

PROGRESS_BAR_WIDTH = 14

_PT_STYLE = Style.from_dict(
    {
        "prompt": f"bold fg:{SPOTIFY_GREEN}",
        "bottom-toolbar": f"fg:{SPOTIFY_GREEN} bg:default",
    }
)


# ── Agent-loop renderers ────────────────────────────────────────────────────


def tool_call(console: Console, name: str, args: dict[str, Any]) -> None:
    console.print(f"[bold {SPOTIFY_GREEN}]▸[/] [dim]{name}[/]")


def tool_result(console: Console, name: str, output: dict[str, Any]) -> None:
    # Quiet by default; only surface errors and the play action.
    if "error" in output and len(output) == 1:
        console.print(f"  [red]error:[/] {output['error']}")
        return
    if name == "spotify_play_track":
        np = output.get("now_playing", "")
        if np:
            console.print(f"  [{SPOTIFY_GREEN}]♪[/] [bold]{np}[/]")


def thinking(console: Console, text: str, verbose: bool = False) -> None:
    """Hidden by default; full text only with --verbose."""
    if not verbose:
        return
    for line in text.strip().splitlines():
        console.print(f"  [italic dim]{line}[/]")


def assistant_text(console: Console, text: str) -> None:
    console.print(Panel(text.strip(), border_style=ASSISTANT_PINK, padding=(0, 1)))


# ── Input prompt with live footer ───────────────────────────────────────────


_pt_session: PromptSession[str] | None = None


def _get_session() -> PromptSession[str]:
    global _pt_session
    if _pt_session is None:
        _pt_session = PromptSession()
    return _pt_session


def _mmss(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def _format_progress(state: PlaybackState) -> str:
    if not state.has_track:
        return "  waiting for playback…"
    position = state.extrapolated_position()
    pct = min(1.0, position / state.duration_s) if state.duration_s > 0 else 0.0
    filled = int(PROGRESS_BAR_WIDTH * pct)
    bar = "▰" * filled + "▱" * (PROGRESS_BAR_WIDTH - filled)
    icon = "♪" if state.is_playing else "⏸"
    track = f"{state.name} — {state.artist}" if state.artist else state.name
    return f"  {icon} {track}  {bar}  {_mmss(position)} / {_mmss(state.duration_s)}"


def read_user_input(console: Console, tracker: PlaybackTracker | None = None) -> str:
    """One line of input inside a green-bordered zone, with optional live playback footer."""
    width = max(20, console.width - 1)
    rule = "─" * (width - 2)
    console.print(f"[bold {SPOTIFY_GREEN}]╭{rule}╮[/]")
    bottom_toolbar = (
        (lambda: _format_progress(tracker.snapshot())) if tracker is not None else None
    )
    try:
        return _get_session().prompt(
            HTML(f'<style fg="{SPOTIFY_GREEN}"><b>│ ❯ </b></style>'),  # noqa: RUF001
            bottom_toolbar=bottom_toolbar,
            refresh_interval=1.0 if tracker is not None else 0,
            style=_PT_STYLE,
        )
    finally:
        console.print(f"[bold {SPOTIFY_GREEN}]╰{rule}╯[/]")
