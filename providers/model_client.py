"""Model provider abstraction for Charlotte.

This keeps Charlotte agent-agnostic: workflows call ModelClient, not a specific tool.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


Message = Dict[str, str]


@dataclass
class ModelResponse:
    content: str
    provider: str
    model: str
    raw: Optional[dict] = None


class ModelClient:
    def complete(self, messages: List[Message], temperature: Optional[float] = None) -> ModelResponse:
        raise NotImplementedError


class MockModelClient(ModelClient):
    """Deterministic no-network client for wiring tests."""

    def __init__(self, model: str = "mock") -> None:
        self.model = model

    def complete(self, messages: List[Message], temperature: Optional[float] = None) -> ModelResponse:
        last = messages[-1]["content"] if messages else ""
        content = (
            "# Mock Agent Output\n\n"
            "This deterministic placeholder validates the Charlotte workflow without a live provider.\n\n"
            "## Received Context\n\n"
            f"{last[:2000]}\n"
        )
        return ModelResponse(content=content, provider="mock", model=self.model)


class OpenAICompatibleClient(ModelClient):
    """Client for OpenAI-compatible /chat/completions endpoints, including NVIDIA NIM."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key_env: str,
        provider_name: str,
        timeout_seconds: int,
        defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.api_key = os.getenv(api_key_env)
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        self.defaults = defaults or {}

    def complete(self, messages: List[Message], temperature: Optional[float] = None) -> ModelResponse:
        if not self.base_url:
            raise ValueError("Missing model base_url")
        if not self.model:
            raise ValueError("Missing model name")
        if not self.api_key:
            raise ValueError(f"Missing API key environment variable: {self.api_key_env}")

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.defaults.get("temperature", 0.1),
            "top_p": self.defaults.get("top_p", 1.0),
            "max_tokens": self.defaults.get("max_tokens", 16384),
        }

        # NIM supports these on selected models; keep them configurable and harmless if ignored upstream.
        if self.defaults.get("reasoning_effort"):
            payload["reasoning_effort"] = self.defaults["reasoning_effort"]
        # tool_choice is only valid when tools are also supplied; sending it alone is a 400 on many models.
        tools = self.defaults.get("tools")
        if tools:
            payload["tools"] = tools
            if self.defaults.get("tool_choice"):
                payload["tool_choice"] = self.defaults["tool_choice"]

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        return ModelResponse(content=content, provider=self.provider_name, model=self.model, raw=raw)


def client_from_config(config: dict) -> ModelClient:
    provider = config.get("provider", {})
    provider_type = provider.get("type", "mock")
    defaults = config.get("runtime_defaults", {})

    if provider_type == "mock":
        return MockModelClient(model=provider.get("model", "mock"))

    if provider_type in {"openai_compatible", "nim"}:
        return OpenAICompatibleClient(
            base_url=provider.get("base_url", ""),
            model=provider.get("model", ""),
            api_key_env=provider.get("api_key_env", "CHARLOTTE_API_KEY"),
            provider_name=provider_type,
            timeout_seconds=int(provider.get("timeout_seconds", 180)),
            defaults=defaults,
        )

    raise ValueError(f"Unsupported provider type: {provider_type}")
