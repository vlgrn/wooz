"""Read project + Claude Code session context. Pure functions, no LLM."""

from __future__ import annotations

from pathlib import Path


def read_project_context(cwd: Path | None = None) -> dict[str, object]:
    """Stub — Phase C will fill this in (cwd, git branch, recent commits, file types)."""
    raise NotImplementedError("Phase C")


def read_claude_session(cwd: Path | None = None, limit: int = 20) -> list[dict[str, str]]:
    """Stub — Phase C will read ~/.claude/projects/<encoded-cwd>/<session>.jsonl."""
    raise NotImplementedError("Phase C")
