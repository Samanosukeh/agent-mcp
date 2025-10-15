import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import HTTPException

API_KEY = os.getenv("MCP_API_KEY")


def check_auth(token):
    if not API_KEY or token != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def register(mcp):
    @mcp.tool()
    def weather_now(city: str, token: str = "") -> dict:
        check_auth(token)
        return {
            "status": "success",
            "city": city,
            "weather": "Sunny",
            "temperature": 27
        }

    @mcp.tool()
    def weather_forecast(city: str, days: int = 1, token: str = "") -> dict:
        check_auth(token)
        return {
            "status": "success",
            "city": city,
            "forecast": [
                {"day": i + 1, "weather": "Sunny"} for i in range(days)
            ]
        }
