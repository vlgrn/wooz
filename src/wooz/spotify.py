"""Spotify backend — thin subprocess wrapper around the `spogo` CLI.

We deliberately do NOT implement our own OAuth flow. spogo (by @steipete) handles
cookie-based auth, has no rate limits, and exposes a `--json` output mode designed
for agents. Users install it once: `brew install steipete/tap/spogo`.
"""

from __future__ import annotations

import shutil


class SpogoMissingError(RuntimeError):
    """Raised when the `spogo` binary is not on PATH."""


SPOGO_INSTALL_HINT = (
    "wooz needs the `spogo` CLI for Spotify control.\n"
    "Install:  brew install steipete/tap/spogo\n"
    "Then:     spogo auth import --browser chrome"
)


def find_spogo() -> str:
    """Return the path to `spogo` on PATH, or raise SpogoMissingError."""
    path = shutil.which("spogo")
    if not path:
        raise SpogoMissingError(SPOGO_INSTALL_HINT)
    return path


def search(query: str, kind: str = "track", limit: int = 10) -> list[dict[str, object]]:
    """Phase D: subprocess.run(['spogo', 'search', kind, query, '--limit', N, '--json'])."""
    raise NotImplementedError("Phase D")


def create_playlist(name: str, description: str, track_uris: list[str]) -> str:
    """Stub — Phase D will create + populate a playlist via spogo, return playlist id."""
    raise NotImplementedError("Phase D")


def play(playlist_id: str, device: str | None = None) -> None:
    """Stub — Phase D will subprocess.run(['spogo', 'play', playlist_id, ...])."""
    raise NotImplementedError("Phase D")
