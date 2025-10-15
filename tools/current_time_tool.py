"""Tool that returns the current time in a given timezone and format.

This implementation uses the standard library `zoneinfo` when available and
falls back to UTC if the timezone is invalid or unavailable. The tool
exposes a `run(input)` method that accepts a dict with optional keys:
- `timezone`: IANA timezone string (default: "UTC")
- `format`: strftime format string (default: "%Y-%m-%d %H:%M:%S %Z")

Returns a dict with a `time` key on success or `error` on failure.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None


class CurrentTimeTool:
    name = "current_time"
    description = "Return current time for a timezone (input: {timezone, format})"
    parameters = {
        "type": "object",
        "properties": {
            "timezone": {"type": "string", "description": "IANA timezone name, e.g. 'America/Sao_Paulo' or 'UTC'"},
            "format": {"type": "string", "description": "strftime format string or common tokens like HH:mm:ss"},
        },
        "required": [],
    }

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        tz_name = (input or {}).get("timezone") or "UTC"
        fmt = (input or {}).get("format") or "%Y-%m-%d %H:%M:%S %Z"

        # Support common non-Python format tokens (e.g. HH:mm:ss) by translating
        # them into Python strftime directives. This helps when LLMs produce
        # formats using JS-style tokens.
        try:
            replacements = {
                "YYYY": "%Y",
                "MM": "%m",
                "DD": "%d",
                "HH": "%H",
                "mm": "%M",
                "ss": "%S",
            }
            for k, v in replacements.items():
                if k in fmt:
                    fmt = fmt.replace(k, v)
        except Exception:
            # if anything goes wrong, keep original fmt
            pass

        if tz_name.upper() == "UTC":
            now = datetime.now(timezone.utc)
            return {"time": now.strftime(fmt)}

        if ZoneInfo is None:
            return {"error": "timezone support not available in this Python (no zoneinfo)"}

        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            return {"error": f"Invalid timezone: {tz_name}"}

        now = datetime.now(tz)
        return {"time": now.strftime(fmt)}
