<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/LLM-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/protocol-MCP-orange?style=for-the-badge" />
</p>

<h1 align="center">🤖 Agent MCP</h1>

<p align="center">
  <strong>A lightweight, tool-augmented AI agent powered by GPT-4o and the Model Context Protocol.</strong>
</p>

<p align="center">
  Think → Plan → Act → Observe → Answer<br/>
  A reasoning loop that connects an LLM to the real world through pluggable tools — both local and remote.
</p>

---

## ✨ What is this?

**Agent MCP** is a minimal yet powerful autonomous agent that:

1. **Receives** a natural language query from the user
2. **Plans** a sequence of tool calls using GPT-4o (with structured JSON reasoning)
3. **Executes** tools one by one — calculators, web search, file I/O, chart generation, and more
4. **Observes** each tool's output and feeds it back into the reasoning loop
5. **Answers** with a final, human-friendly response

It supports both **local tools** (bundled in the project) and **remote tools** discovered dynamically via a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server — making it easily extensible without touching the agent core.

---

## 🏗️ Architecture

```
                          ┌─────────────────────┐
                          │     User Query      │
                          └─────────┬───────────┘
                                    ▼
                          ┌─────────────────────┐
                          │    Agent Runner     │
                          │  (think → act loop) │
                          └─────────┬───────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼               ▼
              ┌─────────────┐ ┌───────────┐  ┌─────────────┐
              │ Local Tools │ │  LLM API  │  │ MCP Server  │
              │ (calc, io…) │ │ (GPT-4o)  │  │  (remote)   │
              └─────────────┘ └───────────┘  └──────┬──────┘
                                                    │
                                           ┌────────┴────────┐
                                           │  Remote Tools   │
                                           │ (prometheus,    │
                                           │  weather, etc.) │
                                           └─────────────────┘
```

---

## 🧰 Built-in Tools

| Tool | Description |
|------|-------------|
| `echo` | Echoes input back — useful for testing |
| `calc` | Evaluates mathematical expressions |
| `search` | Performs web searches |
| `file` | Reads and writes local files |
| `current_time` | Returns the current date and time |
| `graph` | Generates charts (bar, pie, line) as PNG images |
| `mcp_proxy` | Bridges any remote MCP tool into the local agent |

Remote tools (Prometheus queries, weather data, etc.) are auto-discovered from the MCP server at startup.

---

## 📂 Project Structure

```
agent-mcp/
├── agent.py                # Core agent loop (think → act → observe)
├── cli.py                  # Interactive CLI interface
├── llm.py                  # Minimal OpenAI GPT-4o wrapper (zero dependencies)
├── mcp/
│   ├── server.py           # FastMCP server (exposes remote tools)
│   └── tools/              # MCP tool definitions (prometheus, weather)
├── tools/
│   ├── __init__.py         # Tool registry & discovery
│   ├── calc_tool.py        # Math expression evaluator
│   ├── current_time_tool.py
│   ├── echo_tool.py
│   ├── file_tool.py        # File read/write operations
│   ├── graph_tool.py       # Chart generation (matplotlib)
│   ├── mcp_proxy_tool.py   # Remote MCP tool proxy
│   └── search_tool.py      # Web search integration
├── tests/
│   └── test_agent_basic.py
├── requirements.txt
└── TODO.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (3.13 recommended)
- An **OpenAI API key** (`OPENAI_API_KEY`)

### Installation

```bash
# Clone the repository
git clone https://github.com/Samanosukeh/agent-mcp.git
cd agent-mcp

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key
MCP_API_KEY=changeme
MCP_URL=http://127.0.0.1:8000/mcp
```

> `MCP_URL` is optional — if omitted, the agent runs with local tools only.

---

## ▶️ Usage

### Start the MCP Server (optional)

```bash
python -m mcp.server
# or directly with uvicorn:
uvicorn mcp.server:app --host 127.0.0.1 --port 8000
```

The server exposes:
- `/mcp` — MCP protocol endpoint
- `/mcp/overview` — lists all registered remote tools

### Run the Agent

```bash
# Interactive CLI
python cli.py

# With a custom prompt file
python cli.py -p my_prompt.txt
```

### Example Queries

```
Query> What time is it?
Query> Calculate 2^10 + 37 * 4
Query> Generate a pie chart with data [10, 30, 25, 35] and labels ["A", "B", "C", "D"]
Query> Run the Prometheus query 'avg_over_time(cpu_usage[1h])'
Query> What's the weather in São Paulo?
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/
```

---

## 🤝 Contributing

To ensure code quality, set up pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

This runs linting checks (flake8) automatically on every commit.

---

## 📌 Roadmap

- [ ] ChromaDB vector store for long-term memory
- [ ] Conversation persistence via `conversation_id`
- [ ] Web frontend for browser-based interaction
- [ ] Customizable agent strategies (decision modes, tool prioritization)
- [ ] Colored, human-friendly log output

---

<p align="center">
  Built with curiosity and coffee ☕
</p>