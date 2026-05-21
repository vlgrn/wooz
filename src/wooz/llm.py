"""Anthropic Claude client + tool-use loop."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic

from wooz.config import DEFAULT_MODEL, get_anthropic_key
from wooz.tools import dispatch

MAX_TOKENS = 2048
MAX_ITERATIONS = 12  # safety: stop runaway loops
SDK_MAX_RETRIES = 4  # SDK retries 429/5xx/timeouts with exponential backoff


def make_client() -> Anthropic:
    return Anthropic(api_key=get_anthropic_key(), max_retries=SDK_MAX_RETRIES)


@dataclass
class TextEvent:
    text: str


@dataclass
class ThinkingEvent:
    text: str


@dataclass
class ToolCallEvent:
    name: str
    input: dict[str, Any]


@dataclass
class ToolResultEvent:
    name: str
    output: dict[str, Any]


@dataclass
class DoneEvent:
    pass


AgentEvent = TextEvent | ThinkingEvent | ToolCallEvent | ToolResultEvent | DoneEvent


def run_agent(
    client: Anthropic,
    tools: list[dict[str, Any]],
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
) -> Iterator[AgentEvent]:
    """Drive the tool-use loop. Yields events the UI layer can render."""
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]

    for _ in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=tools,
            messages=messages,
            thinking={"type": "enabled", "budget_tokens": 1024},
        )

        # Surface thinking + text Claude produced this turn.
        for block in response.content:
            if block.type == "thinking" and block.thinking.strip():
                yield ThinkingEvent(text=block.thinking)
            elif block.type == "text" and block.text.strip():
                yield TextEvent(text=block.text)

        # Record the assistant turn verbatim for the next iteration.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            yield DoneEvent()
            return

        # Execute each tool call, append the results.
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            yield ToolCallEvent(name=block.name, input=dict(block.input))
            try:
                output = dispatch(block.name, dict(block.input))
                is_error = False
                content_payload = json.dumps(output)
            except Exception as exc:
                output = {"error": str(exc)}
                is_error = True
                content_payload = json.dumps(output)
            yield ToolResultEvent(name=block.name, output=output)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": content_payload,
                    "is_error": is_error,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    yield DoneEvent()
