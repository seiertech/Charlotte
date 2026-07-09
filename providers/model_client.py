"""Model provider abstraction for Charlotte.

This keeps Charlotte agent-agnostic: workflows call ModelClient, not a specific tool.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional


Message = Dict[str, str]


@dataclass
class ModelResponse:
    content: str
    provider: str
    model: str
    raw: Optional[dict] = None


class ModelClient:
    def complete(self, messages: List[Message], temperature: float = 0.4) -> ModelResponse:
        raise NotImplementedError


class MockModelClient(ModelClient):
    """Deterministic no-network client for wiring tests."""

    def __init__(self, model: str = "mock") -> None:
        self.model = model

    def complete(self, messages: List[Message], temperature: float = 0.4) -> ModelResponse:
        last = messages[-1]["content"] if messages else ""
        content = (
            "# Mock Agent Output\n\n"
            "This is a deterministic placeholder response used to validate the Charlotte workflow.\n\n"
            "## Received Context\n\n"
            f"{last[:2000]}\n"
        )
        return ModelResponse(content=content, provider="mock", model=self.model)


class OpenAICompatibleClient(ModelClient):
    """Client for OpenAI-compatible /chat/completions endpoints, including many NIM deployments."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key_env: str = "CHARLOTTE_API_KEY",
        provider_name: str = "openai_compatible",
        timeout_seconds: int = 180,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.api_key = os.getenv(api_key_env)
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds

    def complete(self, messages: List[Message], temperature: float = 0.4) -> ModelResponse:
        if not self.base_url:
            raise ValueError("Missing model base_url")
        if not self.model:
            raise ValueError("Missing model name")
        if not self.api_key:
            raise ValueError(f"Missing API key environment variable: {self.api_key_env}")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
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

    if provider_type == "mock":
        return MockModelClient(model=provider.get("model", "mock"))

    if provider_type in {"openai_compatible", "nim"}:
        return OpenAICompatibleClient(
            base_url=provider.get("base_url", ""),
            model=provider.get("model", ""),
            api_key_env=provider.get("api_key_env", "CHARLOTTE_API_KEY"),
            provider_name=provider_type,
            timeout_seconds=int(provider.get("timeout_seconds", 180)),
        )

    raise ValueError(f"Unsupported provider type: {provider_type}")
