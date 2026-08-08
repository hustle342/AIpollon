import unittest
import subprocess
import sys
import json
import os


class FastMcpTests(unittest.TestCase):
    def test_synthesize_script(self):
        sample = os.path.join("scripts", "ps_examples", "sample_queries.ps1")
        proc = subprocess.run([sys.executable, "-m", "tools.fastmcp_adapter", "--script", sample, "--name", "synth_tool"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out.get("status"), "ok")
        tool = out.get("tool")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.get("name"), "synth_tool")
        # ensure entrypoint file exists
        entry = tool.get("entrypoint")
        self.assertTrue(entry is not None and os.path.exists(entry))


if __name__ == "__main__":
    unittest.main()
