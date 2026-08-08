import unittest
import subprocess
import sys
import json


class WmiSafetyTests(unittest.TestCase):
    def test_list_devices_cli(self):
        proc = subprocess.run([sys.executable, "-m", "core.wmi", "--list-devices"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertIn("devices", out)

    def test_create_and_list_rollback(self):
        # create
        proc = subprocess.run([sys.executable, "-m", "core.safety", "--create", "--name", "testpoint"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertIn("rollback_id", out)
        rid = out["rollback_id"]
        # list
        proc2 = subprocess.run([sys.executable, "-m", "core.safety", "--list"], capture_output=True, text=True)
        self.assertEqual(proc2.returncode, 0)
        out2 = json.loads(proc2.stdout)
        self.assertTrue(any(item.get("id") == rid for item in out2.get("items", [])))
        # restore
        proc3 = subprocess.run([sys.executable, "-m", "core.safety", "--restore", rid], capture_output=True, text=True)
        self.assertEqual(proc3.returncode, 0)
        out3 = json.loads(proc3.stdout)
        self.assertEqual(out3.get("status"), "restored")


if __name__ == "__main__":
    unittest.main()
