"""A trivial tool that echoes input back."""


class EchoTool:
    name = "echo"
    description = "Return the input as-is"
    parameters = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}

    def run(self, input):
        return {"echo": input}
