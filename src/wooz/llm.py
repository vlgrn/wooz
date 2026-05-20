"""Anthropic Claude client + tool-use loop. Filled in Phase D."""

from __future__ import annotations

from anthropic import Anthropic

from wooz.config import DEFAULT_MODEL, get_anthropic_key


def make_client() -> Anthropic:
    return Anthropic(api_key=get_anthropic_key())


def run_agent(
    client: Anthropic,
    tools: list[dict[str, object]],
    user_prompt: str,
    model: str = DEFAULT_MODEL,
) -> None:
    """Stub — Phase D drives the tool-use loop."""
    raise NotImplementedError("Phase D")
