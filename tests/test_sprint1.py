import unittest
import subprocess
import sys
import json


class Sprint1Tests(unittest.TestCase):
    def test_runner_prompt_ping(self):
        proc = subprocess.run([sys.executable, "-m", "core.runner", "--prompt", "ping"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertIn("id", out)
        self.assertIn("response", out)
        self.assertIn("status", out)
        # response should contain 'pong' (case-insensitive) or be a simulated reply
        resp = out.get("response", "") or ""
        self.assertTrue(
            ("pong" in resp.lower()) or ("simulated" in resp.lower()),
            msg=f"unexpected response: {resp}",
        )

    def test_gemini_adapter_test(self):
        proc = subprocess.run([sys.executable, "agents/llm_adapter_local.py", "--test"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("OLLAMA_OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
