"""Simple OpenAI wrapper for GPT-4o (chat completions).

This module implements only the minimal interface used by the standalone
agent: `chat(prompt_messages)` where `prompt_messages` is a list of dicts
with `role` and `content`.

It expects `OPENAI_API_KEY` in the environment. No external packages
are required besides Python standard library.
"""
from __future__ import annotations

import os
import json
import urllib.request
import urllib.error
from typing import List, Dict


class OpenAIGPT4o:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4.1-2025-04-14"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")
        self.model = model

    def chat(
        self,
        messages: List[Dict[str, str]],
        functions: list | None = None,
        function_call: str | dict | None = None
    ) -> dict:
        """Call OpenAI chat completions and return a normalized dict.

        Returns either {"content": str} or {"function_call": {"name": str, "arguments": str}}
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 800,
        }
        if functions:
            payload["functions"] = functions
        if function_call is not None:
            payload["function_call"] = function_call

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            # include response body for easier debugging
            # fixme: nao dar  se for só timeout
            raise RuntimeError(f"OpenAI API error: {e.read().decode('utf-8')}")

        j = json.loads(body)
        try:
            message = j["choices"][0]["message"]
        except Exception:
            raise RuntimeError("Unexpected response from OpenAI API")

        if message.get("function_call"):
            return {"function_call": message.get("function_call")}

        return {"content": message.get("content", "")}
