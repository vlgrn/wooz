"""Runtime configuration: env vars, paths, defaults."""

from __future__ import annotations

import os
from pathlib import Path

ENV_ANTHROPIC = "ANTHROPIC_API_KEY"
ENV_SPOTIFY_CLIENT_ID = "WOOZ_SPOTIFY_CLIENT_ID"
ENV_SPOTIFY_CLIENT_SECRET = "WOOZ_SPOTIFY_CLIENT_SECRET"

DEFAULT_MODEL = "claude-sonnet-4-6"

CONFIG_DIR = Path.home() / ".wooz"
SPOTIFY_TOKEN_FILE = CONFIG_DIR / "spotify.json"

# Baked-in Client ID for the Spotify dev app. Env var overrides for testing.
SPOTIFY_CLIENT_ID = os.environ.get(ENV_SPOTIFY_CLIENT_ID, "9fd508c4c6564b58af5011f5780ef6da")
# Client secret — REQUIRED for confidential OAuth flow (write operations).
# Set via .env: WOOZ_SPOTIFY_CLIENT_SECRET=...
SPOTIFY_CLIENT_SECRET = os.environ.get(ENV_SPOTIFY_CLIENT_SECRET, "")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8765/callback"
SPOTIFY_SCOPES = (
    "playlist-modify-private "
    "playlist-modify-public "
    "user-modify-playback-state "
    "user-read-playback-state "
    "user-read-recently-played"
)


class MissingSpotifySecretError(RuntimeError):
    """Raised when WOOZ_SPOTIFY_CLIENT_SECRET is not set."""


def get_spotify_client_secret() -> str:
    if not SPOTIFY_CLIENT_SECRET:
        raise MissingSpotifySecretError(
            f"Missing {ENV_SPOTIFY_CLIENT_SECRET}. Get it from your Spotify dev app "
            "Settings page (View client secret) and add to .env."
        )
    return SPOTIFY_CLIENT_SECRET


class MissingAnthropicKeyError(RuntimeError):
    """Raised when ANTHROPIC_API_KEY is not set in the environment."""


def get_anthropic_key() -> str:
    key = os.environ.get(ENV_ANTHROPIC)
    if not key:
        raise MissingAnthropicKeyError(
            f"Missing {ENV_ANTHROPIC}. Get one at https://console.anthropic.com/settings/keys "
            f"and export it: export {ENV_ANTHROPIC}=sk-ant-..."
        )
    return key


def ensure_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR
