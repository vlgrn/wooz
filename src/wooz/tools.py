"""Tool schemas + implementations for the agent loop. Filled in Phase D."""

from __future__ import annotations


def tool_schemas() -> list[dict[str, object]]:
    """Stub — Phase D returns the Anthropic tool-use schemas for all 5 tools."""
    raise NotImplementedError("Phase D")


def dispatch(name: str, args: dict[str, object]) -> dict[str, object]:
    """Stub — Phase D maps a tool name + args to its Python implementation."""
    raise NotImplementedError("Phase D")
