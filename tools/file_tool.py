"""A tiny file tool that reads a file path from input and returns first N lines."""

from __future__ import annotations

from typing import Any, Dict


class FileTool:
    name = "read_file"
    description = "Read a file and return up to 'lines' lines"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Filesystem path to read"},
            "lines": {"type": "integer", "description": "Max number of lines to return"},
        },
        "required": ["path"],
    }

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        path = input.get("path")
        lines = int(input.get("lines") or 20)
        if not path:
            return {"error": "path is required"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                content_lines = []
                for i, l in enumerate(f):
                    if i >= lines:
                        break
                    content_lines.append(l.rstrip("\n"))
            return {"lines": content_lines}
        except Exception as e:
            return {"error": str(e)}
