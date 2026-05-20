"""Live playback tracking — polls Spotify in a background thread."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from wooz.spotify import SpotifyError, run_osascript

POLL_INTERVAL_S = 2.0


@dataclass
class PlaybackState:
    name: str = ""
    artist: str = ""
    position_s: float = 0.0
    duration_s: float = 0.0
    is_playing: bool = False
    fetched_at: float = field(default_factory=time.monotonic)

    @property
    def has_track(self) -> bool:
        return bool(self.name) and self.duration_s > 0

    def extrapolated_position(self) -> float:
        """Position interpolated against wall time so the bar moves between polls."""
        if not self.is_playing:
            return self.position_s
        elapsed = time.monotonic() - self.fetched_at
        return min(self.duration_s, self.position_s + elapsed)


def playback_status() -> PlaybackState | None:
    """One-shot AppleScript fetch. Returns None on any failure."""
    try:
        name = run_osascript('tell application "Spotify" to get name of current track')
        if not name:
            return None
        artist = run_osascript('tell application "Spotify" to get artist of current track')
        position = run_osascript('tell application "Spotify" to get player position')
        duration = run_osascript('tell application "Spotify" to get duration of current track')
        state = run_osascript('tell application "Spotify" to get player state')
    except SpotifyError:
        return None
    try:
        return PlaybackState(
            name=name,
            artist=artist,
            position_s=float(position),
            duration_s=float(duration) / 1000.0,  # AppleScript duration is ms
            is_playing=state.lower() == "playing",
        )
    except ValueError:
        return None


class PlaybackTracker:
    """Daemon thread that refreshes a shared PlaybackState on a fixed interval."""

    def __init__(self, interval_s: float = POLL_INTERVAL_S):
        self.interval_s = interval_s
        self._state = PlaybackState()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True, name="wooz-playback")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def snapshot(self) -> PlaybackState:
        with self._lock:
            return self._state

    def _loop(self) -> None:
        while not self._stop.is_set():
            state = playback_status()
            if state is not None:
                with self._lock:
                    self._state = state
            self._stop.wait(self.interval_s)
