from typing import Any, Dict
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class MCPProxyTool:
    def __init__(self, mcp_url: str, tool_name: str, description: str = ""):
        self.mcp_url = mcp_url
        self.tool_name = tool_name
        self.name = tool_name
        self.description = description or f"Remote {tool_name} via MCP"
        self.token = os.getenv("MCP_API_KEY")  # None se não definido

    def run(self, input: Any) -> Dict[str, Any]:
        async def _call():
            args = dict(input)
            args["token"] = self.token
            async with streamablehttp_client(self.mcp_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(self.tool_name, args)
                    if hasattr(result, "structuredContent") and result.structuredContent:
                        return result.structuredContent
                    elif hasattr(result, "content") and result.content:
                        return {"text": getattr(result.content[0], "text", "")}
                    return {"error": "No result returned"}
        return asyncio.run(_call())
