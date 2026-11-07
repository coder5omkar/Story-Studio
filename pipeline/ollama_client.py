"""Small Ollama chat helper used by the story and scene steps."""

from __future__ import annotations

import json
import re
from typing import Any

import requests


class OllamaError(RuntimeError):
    pass


def chat(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    num_predict: int = 4096,
    temperature: float = 0.8,
    timeout: float = 900,
) -> str:
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {"num_predict": num_predict, "temperature": temperature},
    }
    r = requests.post(f"{base_url.rstrip('/')}/api/chat", json=body, timeout=timeout)
    if not r.ok:
        raise OllamaError(f"Ollama {r.status_code}: {r.text[:2000]}")
    data = r.json()
    content = data.get("message", {}).get("content", "")
    if not content.strip():
        raise OllamaError(f"Empty Ollama response: {json.dumps(data)[:1000]}")
    return content.strip()


def extract_json(text: str) -> Any:
    """Pull the first JSON array/object out of a model response."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    start = min([i for i in (text.find("["), text.find("{")) if i >= 0], default=-1)
    if start < 0:
        raise ValueError("No JSON found in model response")
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text[start:])
    return obj
