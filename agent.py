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

    def _parse_llm_plan(self, content: str) -> Dict[str, Any]:
        """Parse LLM output trying to recover JSON. Falls back to first JSON found."""
        print("\n--- BEGIN PLAN RAW LLM OUTPUT ---", file=sys.stderr)
        print(content, file=sys.stderr)
        print("--- END PLAN RAW LLM OUTPUT ---\n", file=sys.stderr)
        try:
            return json.loads(content)
        except Exception:
            # try to extract JSON block
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(content[start: end + 1])
                except Exception:
                    pass
        raise ValueError("LLM did not return valid JSON plan")

    def run(self, user_query: str) -> str:
        iteration = 0
        scratchpad = []
        observation = None
        seen_action_obs = set()

        while iteration < self.config.max_iterations:
            iteration += 1
            prompt = [
                {"role": "system", "content": self.config.system_prompt},
            ]

            # include brief tools description so the LLM knows what it can call
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

            # finally add the interactive user query
            prompt.append({"role": "user", "content": user_query})

            # include scratchpad
            if scratchpad:
                prompt.append({"role": "assistant", "content": json.dumps(scratchpad)})

            if observation is not None:
                prompt.append({
                    "role": "user",
                    "content": f"Observation: {json.dumps(observation)}"
                })

            logger.info("Requesting plan from LLM (iteration=%d)", iteration)

            # build functions schema for OpenAI function-calling (best-effort)
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

            # If the LLM asked for a function call (OpenAI style), execute it now and
            # inject the observation back into the next loop iteration.
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

                print(
                    f">>> Invoking tool '{fc_name}' with input: "
                    f"{json.dumps(tool_input)}"
                )
                print(
                    f"<<< Tool '{fc_name}' returned: "
                    f"{json.dumps(observation)}\n"
                )

                scratchpad.append({
                    "thought": f"function_call:{fc_name}",
                    "action": {"tool": fc_name, "input": tool_input},
                    "observation": observation
                })
                # continue to next iteration so the LLM can see the observation
                continue

            # otherwise assume we received a textual plan
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

            print(f"\n[Iteration {iteration}] Thought: {thought}")

            if final:
                print("Agent indicated final answer.\n")
                return answer or ""

            if not action:
                print("No action proposed by LLM; stopping.")
                return answer or ""

            tool_name = action.get("tool")
            tool_input = action.get("input")
            # detect simple loops: same action + same observation
            action_obs_key = (
                tool_name,
                json.dumps(tool_input, sort_keys=True),
                json.dumps(observation, sort_keys=True)
                if observation is not None else None
            )
            if action_obs_key in seen_action_obs:
                print(
                    "Detected repeated action/observation -> "
                    "stopping to avoid loop."
                )
                return answer or "Agent stopped due to repeated tool loop"
            if tool_name not in self.tools:
                observation = {"error": f"Tool '{tool_name}' not found"}
                scratchpad.append({
                    "thought": thought,
                    "action": action,
                    "observation": observation
                })
                continue

            tool = self.tools[tool_name]
            print(
                f">>> Invoking tool '{tool_name}' with input: "
                f"{json.dumps(tool_input)}"
            )
            try:
                observation = tool.run(tool_input)
            except Exception as e:
                observation = {"error": str(e)}

            print(
                f"<<< Tool '{tool_name}' returned: "
                f"{json.dumps(observation)}\n"
            )

            scratchpad.append({
                "thought": thought,
                "action": action,
                "observation": observation
            })
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
