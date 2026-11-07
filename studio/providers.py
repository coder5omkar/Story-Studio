"""LLM providers: local Ollama or an OpenAI-compatible endpoint.

OpenCode Go and OpenCode Console (pay-as-you-go) are both OpenAI-compatible,
but they use different base URLs and Go expects a stable session header:

    Go chat base:  https://opencode.ai/inference/go/openai/v1
    Go models:     https://opencode.ai/inference/go/v1/models
    Console chat:  https://opencode.ai/inference/openai/v1

The session ID is stored per project so every chapter/scene call shares one
conversation. A non-generic user agent identifies Story Studio to the gateway.
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any
from urllib.parse import urlparse

import requests

from . import store

OPENCODE_GO_BASE = store.OPENCODE_GO_BASE
OPENCODE_ZEN_BASE = store.OPENCODE_ZEN_BASE
DEFAULT_API_BASE = store.DEFAULT_API_BASE
USER_AGENT = "StoryStudio/1.0"

# Curated fallbacks shown when the models endpoint cannot be queried (no key,
# network error, or a free-tier restriction). The API remains authoritative.
OPENCODE_GO_MODELS = [
    "kimi-k3.1-pro",
    "kimi-k3",
    "kimi-k2.7-code",
    "glm-5.3",
    "glm-5.3-flash",
    "glm-5.2",
    "deepseek-v4.1-flash",
    "deepseek-v4-pro",
    "qwen3.8-max",
    "qwen3.8-flash",
    "qwen3.7-plus",
    "claude-haiku-5-5",
    "gemini-4-argon",
    "gpt-6-luna",
    "gpt-5.6-luna",
    "grok-4.7",
    "minimax-m3.1-flash",
    "minimax-m3",
    "mimo-v2.6-flash",
    "mimo-v2.6-pro",
    "mimo-v2.5",
    "mimo-v2.5-pro",
    "longcat-2.0",
    "step-5-preview",
    "hy4",
    "hy4-preview",
    "hy3",
    "crouton-alpha-free",
    "beam-free",
    "iceman-contributor-free",
]

OPENCODE_ZEN_MODELS = [
    "deepseek-v4.1-flash",
    "deepseek-v4-pro",
    "kimi-k3",
    "kimi-k2.7-code",
    "glm-5.3",
    "glm-5.3-flash",
    "glm-5.2",
    "qwen3.8-max",
    "qwen3.8-flash",
    "claude-haiku-5-5",
    "gemini-4-argon",
    "gpt-6-luna",
    "gpt-5.6-luna",
    "grok-4.7",
    "minimax-m3",
    "minimax-m3.1-flash",
    "mistral-large-4",
    "big-pickle",
    "deepseek-v4.1-flash-free",
    "glm-5.3-flash-free",
]


class ProviderError(RuntimeError):
    pass


def _llm(settings: dict) -> dict:
    return settings.get("llm", settings)


def normalize_api_base(api_base: str | None) -> str:
    """Accept a host, a /v1 base, or a full endpoint and return a chat base."""
    base = (api_base or DEFAULT_API_BASE).strip().rstrip("/")
    for suffix in ("/chat/completions", "/completions", "/responses"):
        if base.endswith(suffix):
            base = base[: -len(suffix)].rstrip("/")

    if base in ("https://opencode.ai/inference/go", "https://opencode.ai/inference"):
        return base + "/openai/v1"
    if base.endswith("/inference/go/openai") or base.endswith("/inference/openai"):
        return base + "/v1"
    if base == "https://opencode.ai/zen":
        return base + "/v1"
    # A pasted models URL such as .../inference/go/v1.
    if base.endswith("/inference/go/v1"):
        return base[: -len("/v1")] + "/openai/v1"
    if base.endswith("/inference/v1"):
        return base[: -len("/v1")] + "/openai/v1"
    return base


def _is_opencode(api_base: str) -> bool:
    try:
        return urlparse(api_base).netloc.endswith("opencode.ai")
    except Exception:
        return "opencode.ai" in api_base


def _is_go(api_base: str) -> bool:
    return "opencode.ai/inference/go" in api_base or "opencode.ai/zen/go" in api_base


def _models_url(api_base: str) -> str:
    base = normalize_api_base(api_base)
    if "opencode.ai/inference/go" in base:
        return "https://opencode.ai/inference/go/v1/models"
    if "opencode.ai/zen/go" in base:
        return "https://opencode.ai/zen/go/v1/models"
    if "opencode.ai/inference" in base:
        return "https://opencode.ai/inference/v1/models"
    return base.rstrip("/") + "/models"


def _session_id(settings: dict) -> str:
    llm = _llm(settings)
    sid = str(llm.get("session_id") or "").strip()
    if not sid:
        sid = "ses_" + uuid.uuid4().hex
        llm["session_id"] = sid
    if not sid.startswith("ses_"):
        sid = "ses_" + sid
    return sid


def _headers(settings: dict, api_base: str, api_key: str = "", json_body: bool = False) -> dict:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if json_body:
        headers["Content-Type"] = "application/json"
    if _is_opencode(api_base):
        headers["x-opencode-session"] = _session_id(settings)
    return headers


def _suggestions(api_base: str) -> list[str]:
    if _is_go(api_base):
        return list(OPENCODE_GO_MODELS)
    if _is_opencode(api_base):
        return list(OPENCODE_ZEN_MODELS)
    return []


def list_ollama_models(base_url: str) -> list[str]:
    url = (base_url or "http://127.0.0.1:11434").rstrip("/") + "/api/tags"
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
    if not r.ok:
        raise ProviderError(f"Ollama {r.status_code}: {r.text[:300]}")
    data = r.json()
    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]


def list_openai_models(settings: dict, api_base: str, api_key: str) -> list[str]:
    base = normalize_api_base(api_base)
    url = _models_url(base)
    r = requests.get(url, headers=_headers(settings, base, api_key), timeout=20)
    if not r.ok:
        raise ProviderError(f"Models {r.status_code}: {r.text[:300]}")
    data = r.json()
    items = data.get("data", data if isinstance(data, list) else [])
    out = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("id") or item.get("name")
            if name:
                out.append(name)
    return sorted(set(out))


def list_models(settings: dict) -> dict:
    llm = _llm(settings)
    provider = llm.get("provider", "ollama")
    base = normalize_api_base(llm.get("api_base") or DEFAULT_API_BASE)
    try:
        if provider == "ollama":
            models = list_ollama_models(llm.get("ollama_url") or settings.get("ollama_url", ""))
        else:
            models = list_openai_models(settings, base, store.get_api_key())
        return {
            "ok": True,
            "provider": provider,
            "models": models,
            "suggestions": [],
            "base_url": base,
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "provider": provider,
            "models": [],
            "suggestions": _suggestions(base),
            "base_url": base,
            "error": str(exc),
        }


def chat(
    settings: dict,
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    num_predict: int = 4096,
    timeout: float = 1800,
) -> str:
    llm = _llm(settings)
    provider = llm.get("provider", "ollama")
    model = model or llm.get("model")
    temperature = float(llm.get("temperature", 0.85) if temperature is None else temperature)
    if not model:
        raise ProviderError("No model selected")

    if provider == "ollama":
        base = (llm.get("ollama_url") or settings.get("ollama_url") or "http://127.0.0.1:11434").rstrip("/")
        body = {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"num_predict": num_predict, "temperature": temperature},
        }
        r = requests.post(
            f"{base}/api/chat",
            json=body,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        if not r.ok:
            raise ProviderError(f"Ollama {r.status_code}: {r.text[:1000]}")
        data = r.json()
        content = data.get("message", {}).get("content", "")
    else:
        base = normalize_api_base(llm.get("api_base") or DEFAULT_API_BASE)
        key = store.get_api_key()
        if not key:
            raise ProviderError(
                "No API key configured. Add your OpenCode key in Settings "
                "(it starts with oc_sk_)."
            )
        headers = _headers(settings, base, key, json_body=True)
        # Reasoning models spend output tokens on hidden reasoning. A small
        # max_tokens can leave content empty with finish_reason="length".
        budget = min(32768, max(8192, int(num_predict) * 2))

        def request_completion(tokens: int) -> dict:
            body = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": tokens,
                "stream": False,
            }
            r = requests.post(f"{base}/chat/completions", json=body, headers=headers, timeout=timeout)
            if not r.ok:
                hint = ""
                if _is_go(base) and r.status_code in (401, 403):
                    hint = " Check that the key belongs to a Go-enabled workspace and that your region is allowed."
                raise ProviderError(f"LLM {r.status_code}: {r.text[:1000]}{hint}")
            return r.json()

        data = request_completion(budget)
        content, reasoning, finish_reason = _completion_parts(data)
        attempts = 0
        while finish_reason == "length" and budget < 32768 and attempts < 2:
            attempts += 1
            next_budget = min(32768, budget * 2)
            retry_data = request_completion(next_budget)
            retry_content, retry_reasoning, retry_finish = _completion_parts(retry_data)
            # Prefer a complete answer; otherwise keep the longer truncated one.
            if retry_content and (
                retry_finish != "length" or len(retry_content) > len(content)
            ):
                data = retry_data
                content, reasoning, finish_reason = retry_content, retry_reasoning, retry_finish
            budget = next_budget
        if not content:
            if reasoning:
                raise ProviderError(
                    "The model returned only reasoning and no final answer "
                    f"(finish_reason={finish_reason or 'unknown'}). "
                    "Use a non-reasoning model or raise the token budget."
                )
            raise ProviderError(f"Empty model response: {json.dumps(data)[:1000]}")

    if not content or not content.strip():
        raise ProviderError(f"Empty model response: {json.dumps(data)[:1000]}")
    return content.strip()


def _message_text(value: Any) -> str:
    """Extract text from a Chat Completions message field."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for part in value:
            if isinstance(part, dict) and part.get("type") in (None, "text", "output_text"):
                text = part.get("text") or part.get("content") or ""
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return ""


def _completion_parts(data: dict) -> tuple[str, str, str]:
    try:
        choice = data["choices"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError(f"Unexpected LLM response: {json.dumps(data)[:1000]}") from exc
    message = choice.get("message") or {}
    return (
        _message_text(message.get("content")),
        _message_text(message.get("reasoning_content")),
        str(choice.get("finish_reason") or ""),
    )


def extract_json(text: str) -> Any:
    """Pull the first JSON array/object out of a model response."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    starts = [i for i in (text.find("["), text.find("{")) if i >= 0]
    start = min(starts, default=-1)
    if start < 0:
        raise ValueError("No JSON found in model response")
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text[start:])
    return obj
