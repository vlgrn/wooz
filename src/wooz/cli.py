from __future__ import annotations

import typer
from rich.console import Console

from wooz import __version__

BANNER = r"""██╗    ██╗ ██████╗  ██████╗ ███████╗
██║    ██║██╔═══██╗██╔═══██╗╚══███╔╝
██║ █╗ ██║██║   ██║██║   ██║  ███╔╝
██║███╗██║██║   ██║██║   ██║ ███╔╝
╚███╔███╔╝╚██████╔╝╚██████╔╝███████╗
 ╚══╝╚══╝  ╚═════╝  ╚═════╝ ╚══════╝"""

TAGLINE = "AI DJ for your terminal — reads what you are working on, plays the right music."

app = typer.Typer(
    name="wooz",
    help=TAGLINE,
)
console = Console()


def _print_header() -> None:
    console.print(BANNER, style="bold cyan")
    console.print(f"wooz {__version__} — [dim]{TAGLINE}[/]\n")


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    mood: str | None = typer.Option(None, "--mood", help="Override the inferred vibe."),
    duration: int | None = typer.Option(
        None, "--duration", help="Target playlist length in minutes."
    ),
) -> None:
    """Default action: run the wooz agent on the current project."""
    if ctx.invoked_subcommand is not None:
        return
    _print_header()
    console.print("[yellow]MVP in progress.[/] Agent loop coming next commit.")
    if mood:
        console.print(f"[dim]mood override:[/] {mood}")
    if duration:
        console.print(f"[dim]duration target:[/] {duration} min")


@app.command()
def version() -> None:
    """Print the wooz version."""
    console.print(f"wooz {__version__}")


if __name__ == "__main__":
    app()
