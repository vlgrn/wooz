from __future__ import annotations

import typer
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

from wooz import __version__  # noqa: E402
from wooz.agent import run as run_agent  # noqa: E402
from wooz.ui import TAGLINE, print_header  # noqa: E402

app = typer.Typer(
    name="wooz",
    help=TAGLINE,
)
console = Console()


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    mood: str | None = typer.Option(None, "--mood", help="Vibe hint for the first track."),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show full thinking inline instead of collapsed."
    ),
) -> None:
    """Default action: run the wooz agent on the current project."""
    if ctx.invoked_subcommand is not None:
        return
    print_header(console)
    exit_code = run_agent(console, mood=mood, verbose=verbose)
    if exit_code:
        raise typer.Exit(exit_code)


@app.command()
def version() -> None:
    """Print the wooz version."""
    console.print(f"wooz {__version__}")


if __name__ == "__main__":
    app()
