from tools.echo_tool import EchoTool
from tools.calc_tool import CalcTool
from tools.search_tool import SearchTool
from tools.file_tool import FileTool
from tools.current_time_tool import CurrentTimeTool
from tools.graph_tool import GraphTool


def get_tools():
    """Return a dict of tool instances keyed by name."""
    return {t.name: t for t in [EchoTool(), CalcTool(), SearchTool(), FileTool(), CurrentTimeTool(), GraphTool()]}


def get_functions():
    """Return a list of JSON-schema function definitions for LLM function-calling.

    Each function follows the OpenAI function schema: {name, description, parameters}.
    """
    funcs = []
    for t in get_tools().values():
        params = getattr(t, "parameters", None)
        if params is None:
            # default: accept an object with free-form properties
            params = {"type": "object", "properties": {}}
        funcs.append({"name": t.name, "description": getattr(t, "description", ""), "parameters": params})
    return funcs
