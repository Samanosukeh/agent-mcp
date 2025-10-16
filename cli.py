"""Simple CLI to run the standalone agent in `/me`.

Usage: run `python -m me.cli` and follow prompts.
"""
from __future__ import annotations

import argparse
import sys
import os
from dotenv import load_dotenv

from llm import OpenAIGPT4o
from agent import AgentRunner, AgentConfig, discover_and_register_mcp_tools
from tools import get_tools

load_dotenv()


SYSTEM_PROMPT_SUFFIX = (
    "You are an agent that plans tool calls.\n"
    "When asked a user query, respond with a JSON object with the following shape:\n"
    "{\n"
    "  \"final\": boolean,\n"
    "  \"thought\": string,\n"
    "  \"action\": { \"tool\": string, \"input\": object } | null,\n"
    "  \"answer\": string | null\n"
    "}\n"
    "If \"final\" is true, include the \"answer\" field and set \"action\" to null."
)
SYSTEM_PROMPT_SUFFIX += (
    "\nIMPORTANTE: Você deve responder SEMPRE e SOMENTE no formato JSON especificado acima",
    "nunca em texto livre ou explicação. Não retorne explicações, só JSON puro."
)


PROMPT_FIXED_PATH = os.path.join(os.path.dirname(__file__), "prompt.txt")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--api-key", help="OpenAI API key (optional, otherwise uses env OPENAI_API_KEY)")
    parser.add_argument(
        "-p",
        "--prompt-file",
        help="Path to prompt file (modifica as INSTRUÇÕES, sempre concatena com o sistema fixo)"
    )
    parser.add_argument("--mock", action="store_true", help="Use mock LLM responses (offline testing)")
    args = parser.parse_args(argv)
    # load tools
    tools = get_tools()
    MCP_URL = os.getenv("MCP_URL")
    discover_and_register_mcp_tools(MCP_URL, tools)

    # Sempre carrega o prompt.txt fixo (nunca sobrescrito, sempre incluído)
    with open(PROMPT_FIXED_PATH, "r", encoding="utf-8") as f:
        user_prompt = f.read().strip()
    prompt_text = user_prompt.strip()
    # Garante que a especificação fixa será SEMPRE concatenada no final
    prompt_text = prompt_text + "\n\n" + SYSTEM_PROMPT_SUFFIX

    # create agent config (split system vs user prompt if marker present)
    agent_config = AgentConfig()
    if prompt_text:
        marker = "---USER_PROMPT---"
        if marker in prompt_text:
            system_part, user_part = prompt_text.split(marker, 1)
            agent_config.system_prompt = system_part.strip()
            agent_config.user_prompt_template = user_part.strip()
        else:
            agent_config.system_prompt = prompt_text

    try:
        llm = OpenAIGPT4o(api_key=args.api_key)
    except Exception as e:
        print(f"Error initializing OpenAI LLM: {e}")
        print("If you want to test offline, re-run with --mock")
        sys.exit(1)

    runner = AgentRunner(llm=llm, tools=tools, config=agent_config)

    print("Standalone Agent CLI — type your query and press Enter. Ctrl+C to quit.")
    if prompt_text:
        print("\n[Loaded agent system prompt]\n")
        print(prompt_text)
        print("\n---\n")
    try:
        while True:
            query = input("Query> ")
            if not query.strip():
                continue
            result = runner.run(query)
            print("\n=== Final Answer ===")
            print(result)
            print("====================\n")
    except KeyboardInterrupt:
        print("\nExiting")
        sys.exit(0)


if __name__ == "__main__":
    main()
