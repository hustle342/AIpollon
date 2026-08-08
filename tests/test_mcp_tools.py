import unittest
import subprocess
import sys
import json
import os


class McpToolsTests(unittest.TestCase):
    def test_publish_and_list(self):
        # publish sample PS script as a tool
        sample = os.path.join("scripts", "ps_examples", "sample_queries.ps1")
        proc = subprocess.run([sys.executable, "-m", "core.mcp", "publish", "--file", sample, "--name", "sample_tool"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertEqual(out.get("status"), "ok")
        # list tools
        proc2 = subprocess.run([sys.executable, "-m", "core.mcp", "list-tools"], capture_output=True, text=True)
        self.assertEqual(proc2.returncode, 0)
        out2 = json.loads(proc2.stdout)
        self.assertTrue(any(t.get("name") == "sample_tool" for t in out2.get("tools", [])))


if __name__ == "__main__":
    unittest.main()
