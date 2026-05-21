"""Spotify backend: catalog search + local desktop playback control.

Search uses Spotify's `client_credentials` flow with a baked-in app key
(read-only, no user OAuth). Playback is driven through the local Spotify
desktop app via AppleScript on macOS (no API, no Premium dance via web).
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import time
from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Public app key — only used for catalog search. No user data passes through.
WOOZ_PUBLIC_CLIENT_ID = "9fd508c4c6564b58af5011f5780ef6da"
WOOZ_PUBLIC_CLIENT_SECRET = "b2355016f52e424580be7c1d690a763d"

LAUNCH_WAIT_ATTEMPTS = 10
LAUNCH_WAIT_DELAY_S = 0.5


class SpotifyError(RuntimeError):
    """Generic Spotify failure (no app open, no track, etc)."""


# ── Search (Web API) ────────────────────────────────────────────────────────


def get_search_client() -> spotipy.Spotify:
    auth = SpotifyClientCredentials(
        client_id=WOOZ_PUBLIC_CLIENT_ID,
        client_secret=WOOZ_PUBLIC_CLIENT_SECRET,
    )
    return spotipy.Spotify(auth_manager=auth)


def search_tracks(client: spotipy.Spotify, query: str, limit: int = 10) -> list[dict[str, str]]:
    res = client.search(q=query, type="track", limit=limit)
    items = (res or {}).get("tracks", {}).get("items", [])
    return [
        {
            "uri": t["uri"],
            "id": t["id"],
            "name": t["name"],
            "artist": ", ".join(a["name"] for a in t.get("artists", [])),
            "album": t.get("album", {}).get("name", ""),
            "duration_ms": str(t.get("duration_ms", 0)),
        }
        for t in items
    ]


# ── Desktop playback (AppleScript) ──────────────────────────────────────────


def run_osascript(script: str) -> str:
    """Run AppleScript; raise SpotifyError with friendly text on common failures."""
    if platform.system() != "Darwin":
        raise SpotifyError(
            "playback control is currently macOS-only (AppleScript). Linux/Windows coming soon."
        )
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        # -1743: not authorized to send Apple events.  -600: app not running.
        if "-1743" in stderr or "not allowed" in stderr.lower():
            raise SpotifyError(
                "macOS hasn't allowed wooz to control Spotify yet. "
                "Open System Settings -> Privacy & Security -> Automation and "
                "enable your terminal app's access to Spotify, then try again."
            )
        if "-600" in stderr or "isn't running" in stderr.lower():
            raise SpotifyError("Spotify is not running. Open it and try again.")
        raise SpotifyError(stderr or "AppleScript failed")
    return result.stdout.strip()


def _spotify_installed() -> bool:
    if platform.system() == "Darwin":
        return Path("/Applications/Spotify.app").exists()
    if platform.system() == "Linux":
        return shutil.which("spotify") is not None
    return False


def _spotify_running() -> bool:
    if platform.system() != "Darwin":
        return False
    out = run_osascript(
        'tell application "System Events" to (name of processes) contains "Spotify"'
    )
    return out.lower() == "true"


def ensure_spotify_open() -> None:
    """Launch Spotify if installed but not running; wait briefly for it to be ready."""
    if _spotify_running():
        return
    if not _spotify_installed():
        raise SpotifyError(
            "Spotify is not installed. Get it from https://spotify.com/download"
            "or open it in a browser at https://open.spotify.com"
        )
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Spotify"])
    elif platform.system() == "Linux":
        subprocess.Popen(["spotify"], start_new_session=True)

    for _ in range(LAUNCH_WAIT_ATTEMPTS):
        if _spotify_running():
            return
        time.sleep(LAUNCH_WAIT_DELAY_S)


def play_track(uri: str) -> None:
    ensure_spotify_open()
    run_osascript(f'tell application "Spotify" to play track "{uri}"')


def pause_playback() -> None:
    run_osascript('tell application "Spotify" to pause')


def resume_playback() -> None:
    run_osascript('tell application "Spotify" to play')


def player_state() -> str:
    """Return 'playing' | 'paused' | 'stopped'."""
    return run_osascript('tell application "Spotify" to get player state').lower()


def current_track() -> dict[str, str] | None:
    """Return {name, artist, uri} for the loaded track, or None."""
    try:
        name = run_osascript('tell application "Spotify" to get name of current track')
        artist = run_osascript('tell application "Spotify" to get artist of current track')
        uri = run_osascript('tell application "Spotify" to get spotify url of current track')
    except SpotifyError:
        return None
    if not name:
        return None
    return {"name": name, "artist": artist, "uri": uri}
