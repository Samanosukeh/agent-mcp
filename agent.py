"""Minimal standalone Agent runner for experimentation.

This file contains a compact AgentRunner that accepts a user query,
asks an LLM (gpt-4o) for a plan in a constrained JSON format, executes
registered tools in order, streams tool execution to stdout, and finally
asks the LLM for a final answer.

The implementation intentionally avoids any dependency on the main
project and is designed for reading and learning.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol

from llm import OpenAIGPT4o

# --- MCP Dynamic Tool Integration ---
from tools.mcp_proxy_tool import MCPProxyTool
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import sys
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


class Tool(Protocol):
    name: str
    description: str

    def run(self, input: Any) -> Dict[str, Any]:
        ...


@dataclass
class AgentConfig:
    name: str = "me-agent"
    max_iterations: int = 5
    system_prompt: str = (
        "IMPORTANTE: Você SEMPRE deve planejar, perguntar, explicar e responder "
        "em português (pt-BR), mesmo que as informações brutas das tools estejam "
        "em inglês.\n"
        # instrução original abaixo
        "You are an agent that plans tool calls.\n"
        "When asked a user query, respond with a JSON object with the following "
        "shape:\n"
        "{\n"
        "  \"final\": boolean,\n"
        "  \"thought\": string,\n"
        "  \"action\": { \"tool\": string, \"input\": object } | null,\n"
        "  \"answer\": string | null\n"
        "}\n"
        "If \"final\" is true, include the \"answer\" field and set \"action\" to null."
    )
    user_prompt_template: Optional[str] = None


@dataclass
class AgentRunner:
    llm: OpenAIGPT4o
    tools: Dict[str, Tool]
    config: AgentConfig = field(default_factory=AgentConfig)
    history: list = field(default_factory=list)  # Histórico completo de turns

    MAX_HISTORY_LEN: int = 20  # preserva no máximo 20 turns antigos

    def _parse_llm_plan(self, content: str) -> Dict[str, Any]:
        """Parse LLM output trying to recover JSON. Falls back to first JSON found."""
        print("\n--- BEGIN PLAN RAW LLM OUTPUT ---", file=sys.stderr)
        print(content, file=sys.stderr)
        print("--- END PLAN RAW LLM OUTPUT ---\n", file=sys.stderr)
        try:
            return json.loads(content.replace('```json', '').replace('```', ''))
        except Exception:
            import re
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    print("[WARN] LLM respondeu, mas o JSON estava truncado ou inválido.", file=sys.stderr)
        print("[WARN] Retornando fallback: repassando resposta bruta do modelo como answer.", file=sys.stderr)
        return {
            "final": True,
            "thought": "Resposta do modelo fora do padrão JSON, conteúdo bruto exibido ao usuário.",
            "action": None,
            "answer": content
        }

    def run(self, user_query: str, print_hooks: dict = None) -> str:
        # Permite CLI customizar cor dos logs. Exemplo de uso: print_hooks={"thought": fn, ...}
        iteration = 0
        observation = None
        seen_action_obs = set()

        self.history.append({"role": "user", "content": user_query})
        if len(self.history) > self.MAX_HISTORY_LEN:
            self.history = self.history[-self.MAX_HISTORY_LEN:]

        def _pretty(msg):
            # Identifica se é JSON e retorna formatado
            try:
                if isinstance(msg, str) and (msg.startswith('{') or msg.startswith('[')):
                    obj = json.loads(msg)
                    return json.dumps(obj, indent=2, ensure_ascii=False)
            except Exception:
                pass
            return msg

        def _hook(kind, msg):
            # tool_call e tool_result tentam identar se JSON
            if kind in ("tool_call", "tool_result"):
                pretty = _pretty(msg)
                if print_hooks and kind in print_hooks:
                    print_hooks[kind](pretty)
                else:
                    print(pretty)
            elif print_hooks and kind in print_hooks:
                print_hooks[kind](msg)
            else:
                print(msg)

        while iteration < self.config.max_iterations:
            iteration += 1
            prompt = [
                {"role": "system", "content": self.config.system_prompt},
            ]
            if self.history:
                prompt.extend(self.history)

            tools_description = []
            for tname, tobj in (self.tools or {}).items():
                try:
                    desc = getattr(tobj, "description", "")
                except Exception:
                    desc = ""
                tools_description.append({"name": tname, "description": desc})

            try:
                prompt.append({
                    "role": "system",
                    "content": f"Available tools: {json.dumps(tools_description)}"
                })
            except Exception:
                prompt.append({
                    "role": "system",
                    "content": f"Available tools: {tools_description}"
                })

            logger.info("Requesting plan from LLM (iteration=%d)", iteration)
            functions = []
            for tname, tobj in (self.tools or {}).items():
                try:
                    desc = getattr(tobj, "description", "")
                except Exception:
                    desc = ""
                functions.append({
                    "name": tname,
                    "description": desc,
                    "parameters": {"type": "object", "properties": {}}
                })

            response = self.llm.chat(prompt, functions=functions)

            if isinstance(response, dict) and response.get("function_call"):
                fc = response["function_call"]
                fc_name = fc.get("name")
                fc_args = fc.get("arguments")
                try:
                    tool_input = json.loads(fc_args) if isinstance(fc_args, str) else fc_args or {}
                except Exception:
                    tool_input = {}
                if fc_name not in self.tools:
                    observation = {"error": f"Tool '{fc_name}' not found"}
                else:
                    tool = self.tools[fc_name]
                    try:
                        observation = tool.run(tool_input)
                    except Exception as e:
                        observation = {"error": str(e)}
                self.history.append({
                    "role": "function",
                    "name": fc_name,
                    "content": json.dumps(tool_input)
                })
                self.history.append({
                    "role": "assistant",
                    "content": json.dumps(observation)
                })
                if len(self.history) > self.MAX_HISTORY_LEN:
                    self.history = self.history[-self.MAX_HISTORY_LEN:]
                _hook(
                    "tool_call",
                    f">>> Invoking tool '{fc_name}' with input: {json.dumps(tool_input, indent=4, ensure_ascii=False)}"
                )
                _hook(
                    "tool_result",
                    f"<<< Tool '{fc_name}' returned: {json.dumps(observation, indent=4, ensure_ascii=False)}\n"
                )
                continue

            if isinstance(response, dict) and response.get("content") is not None:
                plan = self._parse_llm_plan(response.get("content"))
            elif isinstance(response, str):
                plan = self._parse_llm_plan(response)
            else:
                raise ValueError("Unexpected LLM response format")

            thought = plan.get("thought")
            action = plan.get("action")
            final = plan.get("final")
            answer = plan.get("answer")

            if thought:
                self.history.append({"role": "assistant", "content": thought})
                if len(self.history) > self.MAX_HISTORY_LEN:
                    self.history = self.history[-self.MAX_HISTORY_LEN:]

            _hook("thought", f"\n[Iteration {iteration}] Thought: {thought}")

            if final:
                _hook("thought", "Agent indicated final answer.\n")
                if answer:
                    self.history.append({"role": "assistant", "content": answer})
                return answer or ""

            if not action:
                _hook("default", "No action proposed by LLM; stopping.")
                return answer or ""

            tool_name = action.get("tool")
            tool_input = action.get("input")
            action_obs_key = (
                tool_name,
                json.dumps(tool_input, sort_keys=True),
                json.dumps(observation, sort_keys=True)
                if observation is not None else None
            )
            if action_obs_key in seen_action_obs:
                _hook("default", "Detected repeated action/observation -> stopping to avoid loop.")
                return answer or "Agent stopped due to repeated tool loop"
            if tool_name not in self.tools:
                observation = {"error": f"Tool '{tool_name}' not found"}
                self.history.append({
                    "role": "function",
                    "name": tool_name,
                    "content": json.dumps(tool_input)
                })
                self.history.append({
                    "role": "assistant",
                    "content": json.dumps(observation)
                })
                if len(self.history) > self.MAX_HISTORY_LEN:
                    self.history = self.history[-self.MAX_HISTORY_LEN:]
                continue
            tool = self.tools[tool_name]
            _hook("tool_call", f">>> Invoking tool '{tool_name}' with input: {json.dumps(tool_input)}")
            try:
                observation = tool.run(tool_input)
            except Exception as e:
                observation = {"error": str(e)}
            _hook("tool_result", f"<<< Tool '{tool_name}' returned: {json.dumps(observation)}\n")
            self.history.append({
                "role": "function",
                "name": tool_name,
                "content": json.dumps(tool_input)
            })
            self.history.append({
                "role": "assistant",
                "content": json.dumps(observation)
            })
            if len(self.history) > self.MAX_HISTORY_LEN:
                self.history = self.history[-self.MAX_HISTORY_LEN:]
            seen_action_obs.add((
                tool_name,
                json.dumps(tool_input, sort_keys=True),
                json.dumps(observation, sort_keys=True)
            ))

        return "Agent reached max iterations without final answer"


def discover_and_register_mcp_tools(mcp_url: str, tools_dict: dict):
    async def _list():
        async with streamablehttp_client(mcp_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                return tools_response.tools
    tools_info = asyncio.run(_list())
    for tool in tools_info:
        tool_name = tool.name
        desc = getattr(tool, "description", "")
        tools_dict[tool_name] = MCPProxyTool(mcp_url, tool_name, desc)

# Uso: tools = get_tools(); discover_and_register_mcp_tools(url, tools)
