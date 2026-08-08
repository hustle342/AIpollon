import unittest
import subprocess
import sys
import json
import os
import io
import base64
from contextlib import redirect_stdout
from unittest.mock import patch

from agents import controller


class ControllerTests(unittest.TestCase):
    def test_orchestrator_dry_run_rejects_missing_candidate(self):
        proc = subprocess.run([sys.executable, "-m", "agents.controller", "--prompt", "Bluetooth missing", "--dry-run"], capture_output=True, text=True)
        out = json.loads(proc.stdout)
        if proc.returncode == 1:
            self.assertEqual(out.get("error"), "candidate_generation_failed")
            self.assertNotIn("rollback_created", out["steps"])
        else:
            self.assertEqual(out.get("status"), "ok")
            self.assertIn("candidate_path", out)
            self.assertTrue(os.path.exists(out["candidate_path"]))

    def test_natural_language_candidate_is_rejected_before_rollback(self):
        with patch.object(controller.runner, "call_gemini_adapter", return_value={"response": "I cannot generate that fix.", "status": "ok"}):
            output = io.StringIO()
            with patch.object(sys, "argv", ["controller", "--prompt", "Bluetooth missing", "--live"]), redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    controller.main()

        self.assertEqual(raised.exception.code, 1)
        out = json.loads(output.getvalue())
        self.assertEqual(out.get("error"), "candidate_generation_failed")
        self.assertNotIn("rollback_created", out["steps"])

    def test_fenced_powershell_candidate_is_extracted(self):
        with patch.object(controller.runner, "call_gemini_adapter", return_value={"response": "```powershell\nWrite-Output 'ok'\n```"}):
            candidate = controller.generate_candidate_from_llm("test")

        self.assertIn("$ErrorActionPreference = 'Stop'", candidate)
        self.assertTrue(candidate.endswith("Write-Output 'ok'"))

    def test_brightness_prompt_generates_wmi_remediation_without_llm(self):
        with patch.object(controller.runner, "call_gemini_adapter", side_effect=AssertionError("LLM must not be called")):
            candidate = controller.generate_candidate_from_llm("ekran parlaklığını %50 yap")

        self.assertIn("WmiMonitorBrightnessMethods", candidate)
        self.assertIn("$brightness = 50", candidate)

    def test_brightness_prompt_without_accusative_suffix_is_supported(self):
        with patch.object(controller.runner, "call_gemini_adapter", side_effect=AssertionError("LLM must not be called")):
            candidate = controller.generate_candidate_from_llm("parlaklığı %50 yap")

        self.assertIn("$brightness = 50", candidate)

    def test_brightness_remediation_does_not_require_admin_heuristically(self):
        candidate = controller.generate_candidate_from_llm("parlaklığı %50 yap")
        self.assertFalse(controller.candidate_requires_admin(candidate))

    def test_arbitrary_prompt_is_sent_to_llm_as_script_task(self):
        requests = []

        def generate_response(request):
            requests.append(request)
            script = "$ErrorActionPreference = 'Stop'\nStop-Service -Name bthserv"
            return {"response": base64.b64encode(script.encode()).decode(), "status": "ok"}

        with patch.object(controller.runner, "call_gemini_adapter", side_effect=generate_response):
            candidate = controller.generate_candidate_from_llm("bluetooth kapat")

        self.assertIn("Stop-Service -Name bthserv", candidate)
        self.assertIn("Base64", requests[0])
        self.assertIn("bluetooth kapat", requests[0])

    def test_token_split_cmdlet_is_normalized(self):
        response = "```powershell\nStop - Service -Name bthserv\n```"
        with patch.object(controller.runner, "call_gemini_adapter", return_value={"response": response, "status": "ok"}):
            candidate = controller.generate_candidate_from_llm("bluetooth kapat")

        self.assertIn("Stop-Service -Name bthserv", candidate)

    def test_spaced_base64_script_is_decoded(self):
        script = "$ErrorActionPreference = 'Stop'\nStop-Service -Name bthserv"
        encoded = " ".join(base64.b64encode(script.encode()).decode())
        response = f"```base64\n{encoded}\n```"
        with patch.object(controller.runner, "call_gemini_adapter", return_value={"response": response, "status": "ok"}):
            candidate = controller.generate_candidate_from_llm("bluetooth kapat")

        self.assertIn("Stop-Service -Name bthserv", candidate)


if __name__ == "__main__":
    unittest.main()
