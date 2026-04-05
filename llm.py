"""Ollama LLM integration for Dario-chan."""

import json
import urllib.request
import urllib.error
from typing import Any


class LLMError(Exception):
    pass


class OllamaClient:
    """Simple Ollama client — no external deps."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:0.5b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _post(self, path: str, data: dict) -> dict:
        url = f"{self.base_url}{path}"
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise LLMError(f"Ollama connection failed: {e}. Is Ollama running? (ollama serve)")
        except Exception as e:
            raise LLMError(f"LLM error: {e}")

    def check_model(self) -> bool:
        """Check if the model is available."""
        try:
            result = self._post("/api/tags", {})
            models = [m.get("name", "") for m in result.get("models", [])]
            return self.model in models
        except LLMError:
            return False

    def pull_model(self) -> None:
        """Pull the model if not available."""
        print(f"⬇️  Pulling model: {self.model} (this may take a while)...")
        print(f"   If this hangs, run: ollama pull {self.model} manually")
        try:
            url = f"{self.base_url}/api/pull"
            payload = json.dumps({"name": self.model, "stream": False}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=600) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                print(f"✅ Model ready: {result.get('status', 'done')}")
        except Exception as e:
            print(f"⚠️  Could not auto-pull: {e}")
            print(f"   Run manually: ollama pull {self.model}")

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """
        Send a chat request and return the response.

        messages: list of {"role": "user"|"assistant"|"system", "content": "..."}
        tools: list of tool definitions in OpenAI format
        returns: {"text": "...", "tool_calls": [...]} or {"text": "..."}
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_ctx": 4096,
            }
        }

        if tools:
            payload["tools"] = tools

        result = self._post("/api/chat", payload)

        message = result.get("message", {})
        text = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        return {
            "text": text,
            "tool_calls": tool_calls,
        }

    def generate(self, prompt: str, system: str = "") -> str:
        """Simple completion for non-chat use cases."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        result = self._post("/api/generate", payload)
        return result.get("response", "")
