"""Rich-based step renderer for the visible agent loop."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel

THINKING_PREVIEW_LINES = 2


def tool_call(console: Console, name: str, args: dict[str, Any]) -> None:
    args_preview = ", ".join(f"{k}={v!r}" for k, v in args.items()) if args else ""
    suffix = f"  [dim]({args_preview})[/]" if args_preview else ""
    console.print(f"[bold cyan]▶[/] [bold]{name}[/]{suffix}")


def tool_result(console: Console, name: str, output: dict[str, Any]) -> None:
    if "error" in output and len(output) == 1:
        console.print(f"  [red]error:[/] {output['error']}")
        return
    lines = _summarise(name, output)
    for i, line in enumerate(lines):
        prefix = "⎿ " if i == 0 else "  "
        console.print(f"  [dim]{prefix}{line}[/]")


def thinking(console: Console, text: str, verbose: bool = False) -> None:
    """Render Claude's thinking — collapsed by default, full with --verbose."""
    text = text.strip()
    if verbose:
        for line in text.splitlines():
            console.print(f"  [italic dim]{line}[/]")
        return

    lines = text.splitlines()
    preview = lines[:THINKING_PREVIEW_LINES]
    for line in preview:
        # Truncate each preview line so multi-line thinking doesn't explode.
        if len(line) > 100:
            line = line[:97] + "..."
        console.print(f"  [italic dim]{line}[/]")
    if len(lines) > THINKING_PREVIEW_LINES:
        hidden = len(lines) - THINKING_PREVIEW_LINES
        console.print(f"  [dim italic](+ {hidden} more lines · rerun with --verbose)[/]")


def assistant_text(console: Console, text: str) -> None:
    console.print(
        Panel(
            text.strip(),
            border_style="magenta",
            padding=(0, 1),
        )
    )


def _summarise(name: str, output: dict[str, Any]) -> list[str]:
    """Return 1-4 lines summarising the tool result for display under the tool call."""
    if name == "spotify_play_track":
        np = output.get("now_playing", "")
        return [f"♪ now playing: [bold]{np}[/]"]

    if name == "spotify_search":
        tracks = output.get("tracks") or []
        if not tracks:
            return ["no tracks found"]
        lines = [f"{len(tracks)} track(s)"]
        for t in tracks[:3]:
            artist = t.get("artist", "")
            name_ = t.get("name", "")
            line = f"♪ {name_}  [dim]— {artist}[/]" if artist else f"♪ {name_}"
            if len(line) > 90:
                line = line[:87] + "..."
            lines.append(line)
        if len(tracks) > 3:
            lines.append(f"... + {len(tracks) - 3} more")
        return lines

    if name == "read_claude_session":
        messages = output.get("messages") or []
        if not messages:
            return ["no session found for this project"]
        lines = [f"{len(messages)} message(s)"]
        last = messages[-1]
        preview = last.get("text", "").splitlines()[0] if last.get("text") else ""
        if len(preview) > 70:
            preview = preview[:67] + "..."
        if preview:
            lines.append(f"latest [{last.get('role', '?')}]: {preview}")
        return lines

    if name == "read_project_context":
        lines = []
        head = []
        if output.get("project_name"):
            head.append(f"project={output['project_name']}")
        if output.get("git_branch"):
            head.append(f"branch={output['git_branch']}")
        if head:
            lines.append(" · ".join(head))
        counts = output.get("file_counts") or {}
        if counts:
            top = ", ".join(f"{ext}({n})" for ext, n in list(counts.items())[:5])
            lines.append(f"files: {top}")
        commits = output.get("recent_commits") or []
        if commits:
            first = commits[0]
            if len(first) > 70:
                first = first[:67] + "..."
            extra = f" (+{len(commits) - 1} more)" if len(commits) > 1 else ""
            lines.append(f"latest commit: {first}{extra}")
        readme = output.get("readme_excerpt")
        if readme:
            first_line = readme.splitlines()[0]
            if len(first_line) > 70:
                first_line = first_line[:67] + "..."
            lines.append(f"readme: {first_line}")
        return lines or ["ok"]

    return [f"{len(json.dumps(output))} bytes"]
