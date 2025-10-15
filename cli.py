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


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--api-key", help="OpenAI API key (optional, otherwise uses env OPENAI_API_KEY)")
    parser.add_argument("-p", "--prompt-file", help="Path to prompt file (overrides default me/prompt.txt)")
    args = parser.parse_args(argv)
    # load tools
    tools = get_tools()
    MCP_URL = os.getenv("MCP_URL")
    discover_and_register_mcp_tools(MCP_URL, tools)

    # load prompt file if provided or present in package
    prompt_text = None
    if args.prompt_file:
        if os.path.isabs(args.prompt_file):
            prompt_path = args.prompt_file
        else:
            prompt_path = os.path.join(os.getcwd(), args.prompt_file)
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_text = f.read().strip()
    else:
        # default location: me/prompt.txt next to this module
        default_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
        if os.path.exists(default_path):
            with open(default_path, "r", encoding="utf-8") as f:
                prompt_text = f.read().strip()

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
