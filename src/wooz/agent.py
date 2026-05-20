"""High-level orchestrator: kicks off the agent loop, handles top-level errors."""

from __future__ import annotations

from rich.console import Console

from wooz.config import MissingAnthropicKeyError, get_anthropic_key
from wooz.spotify import SpotifyAuthError, get_client, has_valid_token


def run(
    console: Console,
    mood: str | None = None,
    duration: int | None = None,
) -> int:
    """Verify environment + auth. Phases D-F replace this with the real agent loop."""
    try:
        get_anthropic_key()
    except MissingAnthropicKeyError as exc:
        console.print(f"[red]error:[/] {exc}")
        return 1
    console.print("[green]✓[/] anthropic key found")

    if not has_valid_token():
        console.print("[dim]first run — opening Spotify auth in your browser...[/]")
    try:
        client = get_client()
        # Force a real API call so PKCE actually runs and the token is cached.
        user = client.current_user()
    except SpotifyAuthError as exc:
        console.print(f"[red]error:[/] {exc}")
        return 1
    except Exception as exc:
        console.print(f"[red]error:[/] spotify auth failed: {exc}")
        return 1
    who = user.get("display_name") or user.get("id")
    console.print(f"[green]✓[/] spotify authed as [bold]{who}[/]")

    console.print("[yellow]agent loop not implemented yet[/] (Phase D)")
    if mood:
        console.print(f"[dim]  mood override:[/] {mood}")
    if duration:
        console.print(f"[dim]  duration target:[/] {duration} min")
    return 0
