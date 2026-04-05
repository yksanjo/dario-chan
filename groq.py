"""Groq API client — fast inference, free tier available."""

import json
import requests


class GroqError(Exception):
    pass


class GroqClient:
    """Groq API client using OpenAI-compatible endpoint."""

    DEFAULT_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "dario-chan/0.5.0",
        })

    def check_connection(self) -> bool:
        """Verify API key and connection."""
        try:
            resp = self.session.get(f"{self.base_url}/models", timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """
        Send a chat request.

        messages: list of {"role": "user"|"assistant"|"system", "content": "..."}
        tools: list of tool definitions in OpenAI format
        returns: {"text": "...", "tool_calls": [...]}
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        if tools:
            payload["tools"] = tools

        try:
            resp = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=120,
            )

            if resp.status_code != 200:
                raise GroqError(f"Groq API error {resp.status_code}: {resp.text}")

            result = resp.json()
        except requests.RequestException as e:
            raise GroqError(f"Groq request failed: {e}")

        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        text = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        return {
            "text": text,
            "tool_calls": tool_calls,
        }

    def list_models(self) -> list[str]:
        """List available models."""
        try:
            resp = self.session.get(f"{self.base_url}/models", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return [m["id"] for m in data.get("data", [])]
        except Exception:
            pass
        return self.DEFAULT_MODELS
