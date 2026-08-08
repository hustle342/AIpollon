import unittest
import subprocess
import sys
import json


class OllamaAdapterTests(unittest.TestCase):
    def test_self_test(self):
        proc = subprocess.run([sys.executable, "agents/llm_adapter_local.py", "--test"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("OLLAMA_OK", proc.stdout)

    def test_prompt_fallback(self):
        # If Ollama not running locally, adapter should fallback to simulated reply
        proc = subprocess.run([sys.executable, "agents/llm_adapter_local.py", "--prompt", "ping"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertIn("response", out)
        self.assertTrue(isinstance(out.get("response"), str))


if __name__ == "__main__":
    unittest.main()
