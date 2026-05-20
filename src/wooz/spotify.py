"""Spotify backend — OAuth 2.0 PKCE via spotipy.

First run opens a browser; user approves; tokens cached at ~/.wooz/spotify.json.
Subsequent runs load from cache and auto-refresh when expired.
"""

from __future__ import annotations

import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyPKCE

from wooz.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
    SPOTIFY_TOKEN_FILE,
    ensure_config_dir,
)


class SpotifyAuthError(RuntimeError):
    """Raised when Spotify auth cannot be completed."""


def _auth_manager(open_browser: bool = True) -> SpotifyPKCE:
    ensure_config_dir()
    return SpotifyPKCE(
        client_id=SPOTIFY_CLIENT_ID,
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


def create_playlist(
    client: spotipy.Spotify,
    name: str,
    description: str,
    track_uris: list[str],
    public: bool = False,
) -> dict[str, str]:
    """Create a new playlist on the user's account and add the given track URIs.
    Returns {id, name, url}."""
    user = client.current_user()
    playlist = client.user_playlist_create(
        user=user["id"],
        name=name,
        public=public,
        description=description,
    )
    if track_uris:
        # Spotify caps at 100 per add — chunk just in case.
        for i in range(0, len(track_uris), 100):
            client.playlist_add_items(playlist["id"], track_uris[i : i + 100])
    return {
        "id": playlist["id"],
        "name": playlist["name"],
        "url": playlist.get("external_urls", {}).get("spotify", ""),
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
