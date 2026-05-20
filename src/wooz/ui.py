"""Rich-based step renderer for the visible agent loop. Filled in Phase E."""

from __future__ import annotations

from rich.console import Console


def step(console: Console, action: str, detail: str) -> None:
    """Phase A: plain-text step output. Phase E will upgrade to panel-based UI."""
    console.print(f"[bold cyan]▶[/] [bold]{action:<20}[/] [dim]{detail}[/]")


def reason(console: Console, why: str) -> None:
    """Phase A: print the agent's reasoning for the current step. Plain for now."""
    console.print(f"  [italic dim]why: {why}[/]")
