import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import HTTPException
from pydantic import BaseModel

API_KEY = os.getenv("MCP_API_KEY")

PROME_DOCS = {
    "metrics_summary": "Resumo: CPU usage alta entre 18-22h, baixe alertas!",
    "config_prev": "Prometheus configs: scrape_interval: 15s, retention: 72h",
    "alert_tip": "Dica: use 'sum(rate(errors_total[1m]))' para detectar picos!"
}
EXAMPLE_QUERIES = [
    "avg_over_time(cpu_usage[1h])",
    "max(memory_usage_total)",
    "sum(rate(requests_total[5m]))"
]


class PrometheusSettings(BaseModel):
    scrape_interval: str = "15s"
    retention: str = "72h"
    alerting: bool = True


def check_auth(token):
    if not API_KEY or token != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def register(mcp):
    @mcp.tool()
    def prometheus_query(query: str, token: str = "") -> dict:
        check_auth(token)
        return {
            "status": "success",
            "data": [{"metric": "cpu_usage", "value": 0.13, "q": query}]
        }

    @mcp.resource("file://documents/{name}")
    def read_document(name: str) -> str:
        return PROME_DOCS.get(name, f"Documento {name} não encontrado.")

    @mcp.resource("prometheus://example_queries")
    def prometheus_example_queries() -> str:
        return "\n".join(EXAMPLE_QUERIES)

    @mcp.resource("config://prometheus")
    def get_prometheus_settings() -> dict:
        return PrometheusSettings().dict()
