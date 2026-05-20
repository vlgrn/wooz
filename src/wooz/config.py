"""Runtime configuration: env vars, paths, defaults."""

from __future__ import annotations

import os
from pathlib import Path

ENV_ANTHROPIC = "ANTHROPIC_API_KEY"
ENV_SPOTIFY_CLIENT_ID = "WOOZ_SPOTIFY_CLIENT_ID"

DEFAULT_MODEL = "claude-sonnet-4-6"

CONFIG_DIR = Path.home() / ".wooz"
SPOTIFY_TOKEN_FILE = CONFIG_DIR / "spotify.json"

# Baked-in Client ID for the Spotify dev app (PKCE flow — no secret needed).
# Env var overrides for development / testing.
SPOTIFY_CLIENT_ID = os.environ.get(ENV_SPOTIFY_CLIENT_ID, "9fd508c4c6564b58af5011f5780ef6da")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8765/callback"
SPOTIFY_SCOPES = (
    "playlist-modify-private "
    "playlist-modify-public "
    "user-modify-playback-state "
    "user-read-playback-state "
    "user-read-recently-played"
)


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
