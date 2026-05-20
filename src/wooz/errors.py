"""Friendly REPL messages for Anthropic SDK errors."""

from __future__ import annotations

from anthropic import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    PermissionDeniedError,
    RateLimitError,
)
from rich.console import Console

# Errors the REPL stays alive through.
ANTHROPIC_RECOVERABLE = (
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    APITimeoutError,
    InternalServerError,
    APIConnectionError,
    APIStatusError,
)


def report_anthropic_error(console: Console, exc: Exception) -> None:
    if isinstance(exc, AuthenticationError):
        console.print(
            "[red]anthropic auth failed[/] — your API key looks invalid.\n"
            "[dim]Edit ~/.wooz/.env or unset ANTHROPIC_API_KEY and re-run wooz.[/]"
        )
    elif isinstance(exc, PermissionDeniedError):
        console.print(
            "[red]permission denied[/] — your key may not have access to this model.\n"
            f"[dim]{exc}[/]"
        )
    elif isinstance(exc, RateLimitError):
        console.print("[yellow]rate limited[/] by Anthropic. Wait a moment, then try /next.")
    elif isinstance(exc, APITimeoutError):
        console.print("[yellow]request timed out[/] after retries. Try /next.")
    elif isinstance(exc, InternalServerError):
        console.print("[yellow]Anthropic 5xx[/] — they had a hiccup. Try /next.")
    elif isinstance(exc, APIConnectionError):
        console.print(
            "[yellow]network issue[/] reaching Anthropic. Check your connection, then /next."
        )
    elif isinstance(exc, APIStatusError):
        console.print(f"[red]Anthropic error[/] (status {exc.status_code}): {exc.message}")
    else:
        console.print(f"[red]error during agent turn:[/] {exc}")
