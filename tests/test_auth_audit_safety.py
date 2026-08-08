import unittest
import subprocess
import sys
import json
import os


class AuthAuditSafetyTests(unittest.TestCase):
    def test_is_admin_env_override(self):
        env = os.environ.copy()
        env["AIPOLLON_FORCE_ADMIN"] = "1"
        proc = subprocess.run([sys.executable, "-m", "core.auth"], capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0)
        out = proc.stdout.strip()
        self.assertIn("is_admin", out)

    def test_audit_log_and_dump(self):
        # log an action
        proc = subprocess.run([sys.executable, "-m", "core.audit", "--log", "test_action", "tester", "--details", '{"k": "v"}'], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        entry = json.loads(proc.stdout)
        self.assertEqual(entry.get("action"), "test_action")
        # dump entries
        proc2 = subprocess.run([sys.executable, "-m", "core.audit", "--dump"], capture_output=True, text=True)
        self.assertEqual(proc2.returncode, 0)
        items = json.loads(proc2.stdout).get("items", [])
        self.assertTrue(any(i.get("action") == "test_action" for i in items))

    def test_verify_rollback(self):
        # create rollback then verify
        proc = subprocess.run([sys.executable, "-m", "core.safety", "--create", "--name", "verify_test"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        rid = out.get("rollback_id")
        proc2 = subprocess.run([sys.executable, "-m", "core.safety", "--restore", rid], capture_output=True, text=True)
        self.assertEqual(proc2.returncode, 0)
        proc3 = subprocess.run([sys.executable, "-m", "core.safety", "--list"], capture_output=True, text=True)
        self.assertEqual(proc3.returncode, 0)
        list_out = json.loads(proc3.stdout)
        self.assertTrue(any(item.get("id") == rid for item in list_out.get("items", [])))
        # verify_restore function via module call (direct CLI not added)
        proc4 = subprocess.run([sys.executable, "-c", f"import json,core.safety as s; print(json.dumps(s.verify_restore('{rid}')))"], capture_output=True, text=True)
        self.assertEqual(proc4.returncode, 0)
        v = json.loads(proc4.stdout)
        self.assertEqual(v.get("status"), "ok")


if __name__ == "__main__":
    unittest.main()
