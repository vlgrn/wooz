"""Runtime configuration: env vars, paths, defaults."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

ENV_ANTHROPIC = "ANTHROPIC_API_KEY"

DEFAULT_MODEL = "claude-sonnet-4-6"

CONFIG_DIR = Path.home() / ".wooz"
USER_ENV_FILE = CONFIG_DIR / ".env"


def ensure_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def _load_user_env() -> None:
    """Populate os.environ from ~/.wooz/.env so values persist across sessions."""
    if not USER_ENV_FILE.exists():
        return
    for key, value in dotenv_values(USER_ENV_FILE).items():
        if value is not None and key not in os.environ:
            os.environ[key] = value


class MissingAnthropicKeyError(RuntimeError):
    """Raised when ANTHROPIC_API_KEY is not set."""


def get_anthropic_key() -> str:
    """Return the Anthropic API key from env (cwd .env or ~/.wooz/.env), or raise."""
    _load_user_env()
    key = os.environ.get(ENV_ANTHROPIC)
    if not key:
        raise MissingAnthropicKeyError(
            f"Missing {ENV_ANTHROPIC}. Get one at https://console.anthropic.com/settings/keys"
        )
    return key


def save_anthropic_key(key: str) -> None:
    """Persist the Anthropic key to ~/.wooz/.env (mode 0600)."""
    ensure_config_dir()
    existing: list[str] = []
    if USER_ENV_FILE.exists():
        for line in USER_ENV_FILE.read_text().splitlines():
            if line.startswith(f"{ENV_ANTHROPIC}="):
                continue
            existing.append(line)
    existing.append(f"{ENV_ANTHROPIC}={key}")
    USER_ENV_FILE.write_text("\n".join(existing).strip() + "\n")
    USER_ENV_FILE.chmod(0o600)
    os.environ[ENV_ANTHROPIC] = key
