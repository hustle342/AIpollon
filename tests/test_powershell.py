import unittest
import subprocess
import sys
import json
import os


class PowerShellTests(unittest.TestCase):
    def test_write_output(self):
        # Use a simple Write-Output command that should work on PowerShell
        proc = subprocess.run([sys.executable, "-m", "core.powershell", "--cmd", "Write-Output 'hello'"],
                              capture_output=True, text=True)
        # The module exits 0 on success
        self.assertEqual(proc.returncode, 0, msg=f"stderr: {proc.stderr}")
        out = json.loads(proc.stdout)
        self.assertEqual(out.get("exit_code"), 0)
        self.assertIn("hello", out.get("stdout", ""))

    def test_timeout(self):
        # Run a sleep longer than timeout to trigger TimeoutExpired handling
        proc = subprocess.run([sys.executable, "-m", "core.powershell", "--cmd", "Start-Sleep -Seconds 5", "--timeout", "1"],
                              capture_output=True, text=True)
        # The module should return non-zero exit code on timeout
        self.assertNotEqual(proc.returncode, 0)
        # parse JSON if any output produced
        try:
            out = json.loads(proc.stdout)
            self.assertEqual(out.get("status"), "timed_out")
            self.assertEqual(out.get("exit_code"), -1)
        except Exception:
            self.fail("Powershell wrapper did not produce JSON output on timeout")


if __name__ == "__main__":
    unittest.main()
