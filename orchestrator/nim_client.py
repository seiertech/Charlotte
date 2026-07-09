"""Placeholder NIM/OpenAI-compatible client for Charlotte.

Wire this to your preferred model endpoint when moving from deterministic scaffold to live generation.
"""

import os
import json
import urllib.request
from typing import List, Dict


class NimClient:
    def __init__(self, base_url: str, model: str, api_key_env: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = os.getenv(api_key_env) if api_key_env else None

    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.4) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        with urllib.request.urlopen(req, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]
