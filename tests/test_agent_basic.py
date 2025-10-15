import unittest
import os
from unittest import mock
from agent import AgentRunner, AgentConfig
from llm import OpenAIGPT4o
from tools import get_tools


class TestAgentBasic(unittest.TestCase):
    def setUp(self):
        self._env_patcher = mock.patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key"})
        self._env_patcher.start()
        self.llm = OpenAIGPT4o(api_key="test")  # mock/placeholder
        self.tools = get_tools()
        self.config = AgentConfig()
        self.runner = AgentRunner(llm=self.llm, tools=self.tools)

    def tearDown(self):
        self._env_patcher.stop()

    def test_runner_instantiation(self):
        self.assertIsNotNone(self.runner)
        self.assertEqual(self.runner.llm, self.llm)
        self.assertTrue(isinstance(self.runner.tools, dict))

    def test_prompt_response_mock(self):
        # Como o LLM real depende de chave/env e API externa,
        # aqui apenas validamos a interface
        # Procedimento real exigiria mock do LLM
        self.assertTrue(hasattr(self.runner, "llm"))
        self.assertTrue(hasattr(self.runner, "tools"))


if __name__ == "__main__":
    unittest.main()
