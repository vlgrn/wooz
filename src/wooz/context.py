"""Read project + Claude Code session context.

Pure functions, no LLM. Outputs are Pydantic models so they serialise cleanly
when passed to Claude as tool inputs.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "target",
}
MAX_FILE_WALK = 2000
MAX_DEPTH = 4
TOP_EXTENSIONS = 8
README_EXCERPT_CHARS = 240


class ProjectContext(BaseModel):
    cwd: str
    project_name: str
    git_branch: str | None = None
    recent_commits: list[str] = []
    file_counts: dict[str, int] = {}
    readme_excerpt: str | None = None


class SessionMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str
    timestamp: str


def _encode_cwd(cwd: Path) -> str:
    """Claude Code encodes /Users/... as -Users-..."""
    return str(cwd.resolve()).replace("/", "-")


def _git_branch(cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=2,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _git_recent_commits(cwd: Path, n: int = 5) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "log", f"-n{n}", "--pretty=format:%s"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if out.returncode != 0:
            return []
        return [line for line in out.stdout.splitlines() if line.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _walk_extensions(cwd: Path) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for idx, path in enumerate(_walk_files(cwd, depth=0)):
        if idx >= MAX_FILE_WALK:
            break
        ext = path.suffix.lower()
        if ext:
            counter[ext] += 1
    return dict(counter.most_common(TOP_EXTENSIONS))


def _walk_files(root: Path, depth: int) -> Iterator[Path]:
    if depth > MAX_DEPTH:
        return
    try:
        entries = list(root.iterdir())
    except (OSError, PermissionError):
        return
    for entry in entries:
        if entry.is_symlink():
            continue
        if entry.name.startswith(".") and entry.name not in {".github"}:
            continue
        if entry.is_dir():
            if entry.name in SKIP_DIRS:
                continue
            yield from _walk_files(entry, depth + 1)
        elif entry.is_file():
            yield entry


def _readme_excerpt(cwd: Path) -> str | None:
    for name in ("README.md", "README.rst", "README.txt", "README"):
        path = cwd / name
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            text = text.strip()
            if not text:
                continue
            excerpt = text[:README_EXCERPT_CHARS].strip()
            if len(text) > README_EXCERPT_CHARS:
                excerpt += "..."
            return excerpt
    return None


def read_project_context(cwd: Path | None = None) -> ProjectContext:
    """Snapshot the project: cwd, git, file mix, readme."""
    cwd = (cwd or Path.cwd()).resolve()
    return ProjectContext(
        cwd=str(cwd),
        project_name=cwd.name,
        git_branch=_git_branch(cwd),
        recent_commits=_git_recent_commits(cwd),
        file_counts=_walk_extensions(cwd),
        readme_excerpt=_readme_excerpt(cwd),
    )


def _extract_text(content: object) -> str:
    """Claude Code message content can be a string OR a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                txt = block.get("text", "")
                if isinstance(txt, str):
                    parts.append(txt)
        return "\n".join(parts)
    return ""


def _latest_session_file(session_dir: Path) -> Path | None:
    if not session_dir.is_dir():
        return None
    candidates = [p for p in session_dir.iterdir() if p.is_file() and p.suffix == ".jsonl"]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def read_claude_session(
    cwd: Path | None = None,
    limit: int = 20,
) -> list[SessionMessage]:
    """Return the last `limit` user/assistant messages from the most recent session
    for `cwd`. Empty list if no session exists for this project."""
    cwd = (cwd or Path.cwd()).resolve()
    session_dir = CLAUDE_PROJECTS_DIR / _encode_cwd(cwd)
    session_file = _latest_session_file(session_dir)
    if session_file is None:
        return []

    messages: list[SessionMessage] = []
    try:
        with session_file.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rtype = record.get("type")
                if rtype not in ("user", "assistant"):
                    continue
                message = record.get("message") or {}
                role = message.get("role")
                if role not in ("user", "assistant"):
                    continue
                text = _extract_text(message.get("content"))
                if not text.strip():
                    continue
                messages.append(
                    SessionMessage(
                        role=role,
                        text=text,
                        timestamp=str(record.get("timestamp", "")),
                    )
                )
    except OSError:
        return []

    return messages[-limit:]
