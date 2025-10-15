# Werbo IA / me — Guia Rápido

## Pré-requisitos
- Python 3.10+ (recomendado Python 3.13)
- Para isolar dependências, crie um ambiente virtual (venv):
  ```bash
  python3.13 -m venv venv
  source venv/bin/activate
  ```
- `pip install -r requirements.txt` (ou instale: `mcp`, `matplotlib` etc)
- **Importante para contribuidores:**
  Para garantir que os padrões de código sejam seguidos em todos os commits, rode:
  ```bash
  pip install pre-commit
  pre-commit install
  ```
  Assim, os hooks definidos no arquivo `.pre-commit-config.yaml` serão executados automaticamente em cada commit, bloqueando commits que não passem no lint.
- (Opcional/recomendado) Crie um arquivo `.env` contendo:
  ```
  MCP_API_KEY=changeme
  ```

## Estrutura
```
data/
me/
├── agent.py          # Agent principal
├── cli.py            # CLI interativa
├── tools/            # Tools locais (incluindo gráficos)
├── mcp/
│   ├── server.py       # FastMCP server
│   └── tools/          # Contextos MCP (prometheus, weather)
└── ...
```

## Subir o Servidor MCP

1. Acesse a pasta do projeto:
   ```
   cd /Users/65a/Workspace/Flauberth/IA/werbo-ia/api/me
   ```
2. Execute o server MCP:
   ```
   cd mcp
   python server.py
   # ou (preferencial):
   uvicorn server:app --host 127.0.0.1 --port 8000
   ```
- O servidor estará disponível em: `http://127.0.0.1:8000/mcp`
- As tools requerem o token (do .env) para autenticação.

## Subir o Agent/autônomo

No terminal, na pasta raiz:
```bash
python agent.py
# ou, modo interativo CLI:
python cli.py
```
- O agent descobre tools locais e MCPS remotos automaticamente.
- O prompt instruirá sempre a responder em português e correta validação dos dados (ex: gráficos).

## Exemplos de queries (CLI ou agent)
- **Tempo:**
  > Me diga o clima em São Paulo
- **Prometheus:**
  > Execute a query 'avg_over_time(cpu_usage[1h])' no Prometheus
- **Gráfico:**
  > Gera um gráfico de pizza com dados: [10, 30, 25, 35] e rótulos: ["A", "B", "C", "D"]
- **Documentos/Resources:**
  > Leia o documento "metrics_summary" do Prometheus

## Tips de Debug
- Logs brutos do LLM aparecem no terminal (stderr) ao executar agent.
- Após criar gráficos, arquivos PNG estarão na subpasta `tmp_graphs/`.
- Para resetar tokens ou configs, altere `.env` e reinicie os servidores.

Qualquer dúvida, consulte os arquivos de cada tool/contexto ou abra uma issue.
