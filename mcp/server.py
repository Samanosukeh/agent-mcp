# MCP Server Example (MCP + demo tools)
from mcp.server.fastmcp import FastMCP
from tools import prometheus_tools, weather_tools

mcp = FastMCP("Exemplo Servidor MCP")

# ---- Importa e registra tools (contextos) ----
prometheus_tools.register(mcp)
weather_tools.register(mcp)

app = mcp.streamable_http_app()

if __name__ == "__main__":
    import uvicorn
    print("Iniciando FastMCP via Uvicorn em http://127.0.0.1:8000/mcp ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
