from __future__ import annotations

from collections.abc import Iterator
from typing import Any, TypedDict

from ollama import Client

DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_NUM_CTX = 8192


class Message(TypedDict):
    role: str
    content: str


def make_client(host: str = DEFAULT_HOST) -> Client:
    return Client(host=host)


def chat_stream(
    client: Client,
    messages: list[Message],
    model: str = DEFAULT_MODEL,
    num_ctx: int = DEFAULT_NUM_CTX,
) -> Iterator[str]:
    """Stream assistant tokens from Ollama's chat API."""
    response = client.chat(
        model=model,
        messages=messages,
        stream=True,
        options={"num_ctx": num_ctx},
    )
    for chunk in response:
        token = chunk.get("message", {}).get("content", "")
        if token:
            yield token


def list_local_models(client: Client) -> list[dict[str, Any]]:
    """Return the list of locally available models from the Ollama daemon."""
    result = client.list()
    raw = result.get("models", []) if isinstance(result, dict) else getattr(result, "models", [])
    out: list[dict[str, Any]] = []
    for m in raw:
        if isinstance(m, dict):
            out.append(m)
        else:
            out.append(
                {
                    "name": getattr(m, "model", getattr(m, "name", "")),
                    "size": getattr(m, "size", 0),
                    "modified_at": str(getattr(m, "modified_at", "")),
                }
            )
    return out
