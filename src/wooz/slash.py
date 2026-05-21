"""Slash commands available in the REPL."""

from __future__ import annotations

from rich.console import Console

from wooz.spotify import SpotifyError, pause_playback, player_state, resume_playback
from wooz.state import WoozState
from wooz.theme import SPOTIFY_GREEN

EXIT_COMMANDS = {"/exit", "/quit", "/q"}

SLASH_HELP = f"""\
[bold]commands[/]
  [{SPOTIFY_GREEN}]/next[/]            play a different track (re-reads context)
  [{SPOTIFY_GREEN}]/skip[/]            skip to the next track (ban this music)
  [{SPOTIFY_GREEN}]/pause[/]           pause playback
  [{SPOTIFY_GREEN}]/play[/]            resume playback
  [{SPOTIFY_GREEN}]/vibe[/]            show the current vibe
  [{SPOTIFY_GREEN}]/help[/]            show this help
  [{SPOTIFY_GREEN}]/exit[/]            quit (also /quit, /q, Ctrl+D)
or just type anything in natural language ([dim]e.g. "more upbeat"[/])"""


def handle_slash(console: Console, state: WoozState, cmd: str) -> None:
    head = cmd.split(maxsplit=1)[0]
    if head == "/help":
        console.print(SLASH_HELP)
    elif head == "/vibe":
        console.print(
            f"[bold]current vibe:[/] {state.vibe}" if state.vibe else "[dim]no vibe set yet.[/]"
        )
    elif head == "/pause":
        try:
            pause_playback()
            console.print("[dim]⏸  paused[/]")
        except SpotifyError as exc:
            console.print(f"[red]{exc}[/]")
    elif head == "/play":
        try:
            resume_playback()
            console.print(f"[dim]▶  {player_state()}[/]")
        except SpotifyError as exc:
            console.print(f"[red]{exc}[/]")
    else:
        console.print(f"[red]unknown command:[/] {head}  [dim](/help)[/]")
