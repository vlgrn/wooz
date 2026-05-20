from __future__ import annotations

from datetime import datetime

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from wooz import __version__
from wooz.client import (
    DEFAULT_MODEL,
    Message,
    chat_stream,
    list_local_models,
    make_client,
)

BANNER = r"""██╗    ██╗ ██████╗  ██████╗ ███████╗
██║    ██║██╔═══██╗██╔═══██╗╚══███╔╝
██║ █╗ ██║██║   ██║██║   ██║  ███╔╝
██║███╗██║██║   ██║██║   ██║ ███╔╝
╚███╔███╔╝╚██████╔╝╚██████╔╝███████╗
 ╚══╝╚══╝  ╚═════╝  ╚═════╝ ╚══════╝"""

EXIT_COMMANDS = {"/exit", "/quit", "/q"}
SLASH_HELP = """\
[bold]commands[/]
  [cyan]/model[/] [dim][name][/]   show or switch the active model
  [cyan]/clear[/]           clear conversation history
  [cyan]/help[/]            show this help
  [cyan]/exit[/]            quit (also /quit, /q, Ctrl+D)"""

app = typer.Typer(
    name="wooz",
    help="AI DJ for your terminal — reads what you are working on, plays the right music.",
)
console = Console()


def _user_panel(text: str) -> Panel:
    return Panel(
        Text(text, style="white"),
        title="[bold]you[/]",
        title_align="right",
        border_style="green",
        padding=(0, 1),
    )


def _bot_panel(content: str, model: str) -> Panel:
    body = Markdown(content) if content else Text("", style="dim")
    return Panel(
        body,
        title=f"[bold]{model}[/]",
        title_align="left",
        border_style="magenta",
        padding=(0, 1),
    )


def _print_header(model: str) -> None:
    console.print(BANNER, style="bold cyan")
    console.print(
        f"wooz {__version__} — model: [bold cyan]{model}[/] — [dim]/help for commands[/]\n"
    )


def _handle_slash(
    cmd: str,
    current_model: str,
    history: list[Message],
    client_models: list[str],
) -> str:
    """Process a /slash command. Returns the (possibly updated) model name."""
    parts = cmd.split(maxsplit=1)
    head = parts[0]
    arg = parts[1].strip() if len(parts) > 1 else ""

    if head == "/help":
        console.print(SLASH_HELP)
    elif head == "/clear":
        history.clear()
        console.clear()
        _print_header(current_model)
    elif head == "/model":
        if not arg:
            console.print(f"current model: [bold cyan]{current_model}[/]")
        elif arg not in client_models:
            console.print(
                f"[red]unknown model:[/] {arg}\n"
                f"[dim]installed:[/] {', '.join(client_models) or '(none)'}"
            )
        else:
            console.print(f"[dim]switched to[/] [bold cyan]{arg}[/]")
            return arg
    else:
        console.print(f"[red]unknown command:[/] {head}  [dim](/help)[/]")
    return current_model


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help="Ollama model tag."),
) -> None:
    """Default action: start the interactive chat."""
    if ctx.invoked_subcommand is None:
        chat(model=model)


@app.command()
def chat(
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help="Ollama model tag."),
) -> None:
    """Start an interactive chat session."""
    _print_header(model)

    client = make_client()
    history: list[Message] = []

    while True:
        try:
            user_input = Prompt.ask("[bold green]▶[/]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye.[/dim]")
            break

        if not user_input:
            continue
        if user_input in EXIT_COMMANDS:
            console.print("[dim]bye.[/dim]")
            break

        if user_input.startswith("/"):
            try:
                installed = [m["name"] for m in list_local_models(client)]
            except Exception:
                installed = []
            model = _handle_slash(user_input, model, history, installed)
            continue

        console.print(_user_panel(user_input))
        history.append({"role": "user", "content": user_input})

        chunks: list[str] = []
        stream = chat_stream(client, history, model=model)

        try:
            with console.status("[bold cyan]thinking[/]", spinner="dots"):
                first_token = next(stream)
            chunks.append(first_token)
        except StopIteration:
            console.print("[red]empty response[/]")
            history.pop()
            continue
        except Exception as exc:
            console.print(f"[red]error:[/] {exc}")
            history.pop()
            continue

        try:
            with Live(
                _bot_panel("".join(chunks), model),
                console=console,
                refresh_per_second=18,
                transient=False,
            ) as live:
                for token in stream:
                    chunks.append(token)
                    live.update(_bot_panel("".join(chunks), model))
        except KeyboardInterrupt:
            console.print("\n[dim](interrupted)[/]")
            history.pop()
            continue
        except Exception as exc:
            console.print(f"[red]error mid-stream:[/] {exc}")
            history.pop()
            continue

        history.append({"role": "assistant", "content": "".join(chunks)})


@app.command()
def models() -> None:
    """List locally available Ollama models."""
    client = make_client()
    try:
        items = list_local_models(client)
    except Exception as exc:
        console.print(f"[red]could not reach ollama daemon:[/] {exc}")
        raise typer.Exit(1) from exc

    if not items:
        console.print("[dim]no models installed.[/] use [bold]ollama pull <name>[/]")
        return

    table = Table(title="local models", title_style="bold cyan", show_lines=False)
    table.add_column("name", style="cyan")
    table.add_column("size", justify="right")
    table.add_column("modified", style="dim")
    for m in items:
        size_gb = float(m.get("size", 0)) / 1e9
        modified = str(m.get("modified_at", ""))
        if modified:
            try:
                modified = datetime.fromisoformat(modified.replace("Z", "+00:00")).strftime(
                    "%Y-%m-%d %H:%M"
                )
            except ValueError:
                modified = modified[:19]
        table.add_row(str(m.get("name", "")), f"{size_gb:.2f} GB", modified)
    console.print(table)


@app.command()
def version() -> None:
    """Print the wooz version."""
    console.print(f"wooz {__version__}")


if __name__ == "__main__":
    app()
