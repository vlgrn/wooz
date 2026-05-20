"""High-level orchestrator: kicks off the agent loop, handles top-level errors."""

from __future__ import annotations

from rich.console import Console

from wooz.config import MissingAnthropicKeyError, get_anthropic_key
from wooz.spotify import SpogoMissingError, find_spogo


def run(
    console: Console,
    mood: str | None = None,
    duration: int | None = None,
) -> int:
    """Phase A: verify environment + dependencies. Phases C-F replace this with the real loop."""
    try:
        get_anthropic_key()
    except MissingAnthropicKeyError as exc:
        console.print(f"[red]error:[/] {exc}")
        return 1
    console.print("[green]✓[/] anthropic key found")

    try:
        find_spogo()
    except SpogoMissingError as exc:
        console.print(f"[red]error:[/] {exc}")
        return 1
    console.print("[green]✓[/] spogo found on PATH")

    console.print("[yellow]agent loop not implemented yet[/] (Phase D)")
    if mood:
        console.print(f"[dim]  mood override:[/] {mood}")
    if duration:
        console.print(f"[dim]  duration target:[/] {duration} min")
    return 0
