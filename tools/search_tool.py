"""A toy search tool that looks up keywords in a small in-memory corpus."""

from __future__ import annotations

from typing import Any, Dict


class SearchTool:
    name = "search"
    description = "Search a small corpus for a keyword 'q'"
    parameters = {
        "type": "object",
        "properties": {"q": {"type": "string", "description": "Query keyword"}},
        "required": ["q"],
    }

    CORPUS = {
        "agent": "This is an example agent that calls tools and reasons.",
        "python": "Python is a programming language.",
        "openai": "OpenAI provides LLM models like gpt-4o.",
    }

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        q = input.get("q")
        if not q:
            return {"error": "q is required"}
        results = {k: v for k, v in self.CORPUS.items() if q.lower() in k.lower() or q.lower() in v.lower()}
        return {"hits": results}
