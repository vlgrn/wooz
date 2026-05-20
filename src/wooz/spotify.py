"""Spotify backend — confidential OAuth 2.0 via spotipy.

First run opens a browser; user approves; tokens cached at ~/.wooz/spotify.json.
Subsequent runs load from cache and auto-refresh when expired.

We use confidential OAuth (client_id + client_secret) rather than PKCE because
Spotify rejects PKCE-issued tokens on certain write endpoints (e.g. create
playlist) with a generic 403.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import time
from pathlib import Path

import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth

from wooz.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
    SPOTIFY_TOKEN_FILE,
    ensure_config_dir,
    get_spotify_client_secret,
)

LAUNCH_WAIT_ATTEMPTS = 10
LAUNCH_WAIT_DELAY_S = 1.0


class SpotifyAuthError(RuntimeError):
    """Raised when Spotify auth cannot be completed."""


def _auth_manager(open_browser: bool = True) -> SpotifyOAuth:
    ensure_config_dir()
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=get_spotify_client_secret(),
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        cache_handler=CacheFileHandler(cache_path=str(SPOTIFY_TOKEN_FILE)),
        open_browser=open_browser,
    )


def has_valid_token() -> bool:
    """True if a cached token exists and is still usable (refresh OK)."""
    try:
        manager = _auth_manager(open_browser=False)
        token_info = manager.cache_handler.get_cached_token()
        if not token_info:
            return False
        # Refresh if near expiry; returns None if refresh fails.
        manager.validate_token(token_info)
        return True
    except Exception:
        return False


def get_client() -> spotipy.Spotify:
    """Return an authed Spotify client. Triggers browser auth on first run."""
    try:
        return spotipy.Spotify(auth_manager=_auth_manager(open_browser=True))
    except Exception as exc:
        raise SpotifyAuthError(f"could not authenticate with Spotify: {exc}") from exc


def search_tracks(client: spotipy.Spotify, query: str, limit: int = 10) -> list[dict[str, str]]:
    """Search Spotify tracks. Returns a list of {uri, name, artist, album, duration_ms}."""
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


def _try_launch_spotify() -> bool:
    """Best-effort launch of the native Spotify app. Returns True if a launch was attempted."""
    system = platform.system()
    if system == "Darwin":
        if Path("/Applications/Spotify.app").exists():
            subprocess.Popen(["open", "-a", "Spotify"])
            return True
        return False
    if system == "Linux":
        if shutil.which("spotify"):
            subprocess.Popen(["spotify"], start_new_session=True)
            return True
        return False
    return False


def _wait_for_devices(client: spotipy.Spotify) -> list[dict[str, object]]:
    """Poll for a Spotify device to appear after we launched the app."""
    for _ in range(LAUNCH_WAIT_ATTEMPTS):
        devices: list[dict[str, object]] = (client.devices() or {}).get("devices", [])
        if devices:
            return devices
        time.sleep(LAUNCH_WAIT_DELAY_S)
    return []


def play_tracks(
    client: spotipy.Spotify,
    track_uris: list[str],
) -> dict[str, object]:
    """Start playback of `track_uris` (in order) on the user's best available device.
    If no device is found, tries to auto-launch the native Spotify app, then waits
    briefly for it to register as a Connect device."""
    devices = (client.devices() or {}).get("devices", [])
    auto_launched = False
    if not devices and _try_launch_spotify():
        auto_launched = True
        devices = _wait_for_devices(client)

    if not devices:
        hint = (
            " (we tried to launch the Spotify app but it did not register in time)"
            if auto_launched
            else " — open Spotify on a device, then try again"
        )
        raise SpotifyAuthError(f"no Spotify devices available{hint}.")

    active = next((d for d in devices if d.get("is_active")), None)
    target = active or devices[0]
    target_id = target["id"]
    target_name = target.get("name", "")

    if not active:
        client.transfer_playback(target_id, force_play=False)

    client.start_playback(device_id=target_id, uris=track_uris)
    return {
        "started_count": len(track_uris),
        "device_name": target_name,
        "auto_launched": auto_launched,
    }


def get_active_device(client: spotipy.Spotify) -> dict[str, str] | None:
    """Find an active (or first available) Spotify Connect device."""
    devices = (client.devices() or {}).get("devices", [])
    if not devices:
        return None
    active = next((d for d in devices if d.get("is_active")), devices[0])
    return {"id": active["id"], "name": active.get("name", "")}


def play_playlist(
    client: spotipy.Spotify,
    playlist_id: str,
    device_id: str | None = None,
) -> None:
    """Start playback of a playlist on the given device (or active device if None)."""
    client.start_playback(
        device_id=device_id,
        context_uri=f"spotify:playlist:{playlist_id}",
    )
