"""Session memory: current vibe + recently played tracks."""

from __future__ import annotations

from dataclasses import dataclass, field

RECENT_LIMIT = 20


@dataclass
class WoozState:
    vibe: str = ""
    recent_tracks: list[str] = field(default_factory=list)  # most-recent-last
    tokens_in: int = 0
    tokens_out: int = 0

    def remember(self, uri: str, vibe: str) -> None:
        if uri and uri not in self.recent_tracks:
            self.recent_tracks.append(uri)
            self.recent_tracks = self.recent_tracks[-RECENT_LIMIT:]
        if vibe:
            self.vibe = vibe
