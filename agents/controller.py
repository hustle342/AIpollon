"""Orchestrator: LLM -> candidate script -> dry-run -> rollback -> (optional) execute -> synthesize

Usage:
  python -m agents.controller --prompt "Bluetooth missing" [--dry-run] [--confirm] [--name tool_name]

Default is dry-run. Use --confirm to perform live execution and synthesis.
"""
import argparse
import json
import sys
import tempfile
import os
import base64
from pathlib import Path
import re
import unicodedata

from core import runner
from core import safety
from core import powershell
from core import auth
from core import audit
from mcp_tools import registry

try:
    from tools.fastmcp_adapter import build_wrapper
except Exception:
    build_wrapper = None


def generate_candidate_from_llm(prompt: str) -> str | None:
    # Handle well-defined local operations without asking the LLM to invent commands.
    import re
    lower = prompt.lower()
    normalized = "".join(
        char for char in unicodedata.normalize("NFD", lower)
        if unicodedata.category(char) != "Mn"
    )
    brightness = re.search(
        r"(?:parlaklik|parlakligi|parlaklig?ini|brightness)\s*(?:%\s*|yuzde\s+)?(\d{1,3})\b",
        normalized,
        re.IGNORECASE,
    )
    if brightness:
        value = int(brightness.group(1))
        if 0 <= value <= 100:
            return (
                "$ErrorActionPreference = 'Stop'\n"
                f"$brightness = {value}\n"
                "$methods = Get-WmiObject -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods\n"
                "if (-not $methods) { throw 'No WMI monitor brightness method is available.' }\n"
                "$methods | ForEach-Object { $_.WmiSetBrightness(1, $brightness) | Out-Null }\n"
                "Write-Output \"Brightness set to $brightness percent.\"\n"
            )
    is_folder_request = (
        ("masaüst" in lower or "desktop" in lower)
        and re.search(r"(?:klas(?:ö|o)r|folder|directory)", lower, re.IGNORECASE)
        and re.search(r"(?:olu[sş]tur|create|make|new)", lower, re.IGNORECASE)
    )
    if is_folder_request:
        name_match = (
            re.search(r"([A-Za-z0-9_.-]+)\s+ad(?:ı|i)nda\b", lower, re.IGNORECASE)
            or re.search(r"(?:name|named|called)\s*(?:is\s*)?[=:]?\s*[\"']?([A-Za-z0-9_. -]+?)[\"']?(?:\s*$|\s+(?:on|at)\s+desktop)", lower, re.IGNORECASE)
        )
        if name_match:
            folder_name = name_match.group(1).strip(" .\"'")
            if folder_name and not re.search(r"[\\/:*?\"<>|]", folder_name):
                safe_name = folder_name.replace("'", "''")
                return (
                    "$ErrorActionPreference = 'Stop'\n"
                    "$desktop = [Environment]::GetFolderPath('Desktop')\n"
                    f"$path = Join-Path $desktop '{safe_name}'\n"
                    "New-Item -Path $path -ItemType Directory -Force | Out-Null\n"
                    "Write-Output \"Created: $path\"\n"
                )
    if "masaüst" in lower and ("oluştur" in lower or "yaz" in lower or "ekle" in lower) and not is_folder_request:
        # try extract filename like 'merhaba.txt' from prompt
        matches = re.findall(r"(?<!\w)([A-Za-z0-9_.-]+\.txt)\b", prompt, re.IGNORECASE)
        filename = matches[-1] if matches else "output.txt"
        content_match = re.search(r"\biçine\s+(.+?)\s+yaz\b", prompt, re.IGNORECASE | re.DOTALL)
        content = content_match.group(1).strip() if content_match else ""
        content = content.strip(" \t\r\n\"'")

        def ps_single_quote(value: str) -> str:
            return value.replace("'", "''")

        filename = ps_single_quote(filename)
        content = ps_single_quote(content)
        return (
            f"$p = Join-Path $Env:USERPROFILE 'Desktop'\n"
            f"$path = Join-Path $p '{filename}'\n"
            + (f"Set-Content -Path $path -Value '{content}' -Encoding UTF8\n" if content else f"New-Item -Path $path -ItemType File -Force\n")
            + "Write-Output \"Created: $path\"\n"
        )

    remediation_prompt = (
        "You are the Windows remediation engine for AIPOLLON.\n"
        "Convert the user's request into one complete, executable Windows PowerShell 5.1 script.\n"
        "Return ONLY the UTF-8 Base64 encoding of the script: no explanation, no Markdown fences, and no whitespace inside the encoded value.\n"
        "Start with $ErrorActionPreference = 'Stop'.\n"
        "Use the least-privileged Windows API or cmdlet that can perform the requested change.\n"
        "If the request cannot be performed on Windows, return a PowerShell script that fails clearly with throw.\n"
        f"User request: {prompt}\n"
        "PowerShell script:"
    )
    powershell_command = re.compile(
        r"\b(?:Get|Set|New|Remove|Restart|Start|Stop|Write|Add|Out|Invoke|Enable|Disable|Test|Install|Uninstall|Copy|Move|Rename|Convert|Select|Where|ForEach|Join|Import|Export|Clear)-[A-Za-z]+\b",
        re.IGNORECASE,
    )
    rejected_candidate = ""
    for attempt in range(2):
        request = remediation_prompt
        if attempt:
            request = (
                remediation_prompt
                + "\nThe following candidate failed PowerShell parsing. Rewrite it into valid PowerShell and return only its UTF-8 Base64 encoding."
                + "\nInvalid candidate:\n"
                + rejected_candidate
                + "\nReturn only the corrected script."
            )
        res = runner.call_gemini_adapter(request)
        if not res or not isinstance(res, dict) or not res.get("response"):
            continue
        resp = res["response"].strip()
        encoded_source = resp
        encoded_fence = re.search(r"```(?:base64|text)?\s*\n?(.*?)```", resp, re.IGNORECASE | re.DOTALL)
        if encoded_fence:
            encoded_source = encoded_fence.group(1)
        encoded = re.sub(r"\s+", "", encoded_source.strip("`"))
        try:
            decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            decoded = ""
        if decoded:
            candidate = decoded.strip()
            if not candidate.startswith("$ErrorActionPreference"):
                candidate = "$ErrorActionPreference = 'Stop'\n" + candidate
            if is_parseable_powershell(candidate):
                return candidate
            rejected_candidate = candidate
            continue
        fenced = re.search(r"```(?:powershell|pwsh|ps1)?\s*\n?(.*?)```", resp, re.IGNORECASE | re.DOTALL)
        candidate = fenced.group(1).strip() if fenced and fenced.group(1).strip() else resp
        candidate = re.sub(
            r"\b(Get|Set|New|Remove|Restart|Start|Stop|Write|Add|Out|Invoke|Enable|Disable|Test|Install|Uninstall|Copy|Move|Rename|Convert|Select|Where|ForEach|Join|Import|Export|Clear)\s*-\s*(?=[A-Za-z])",
            r"\1-",
            candidate,
            flags=re.IGNORECASE,
        )
        if candidate.startswith(("#", "$")) or powershell_command.search(candidate):
            if not candidate.startswith("$ErrorActionPreference"):
                candidate = "$ErrorActionPreference = 'Stop'\n" + candidate
            if is_parseable_powershell(candidate):
                return candidate
            rejected_candidate = candidate

    # Do not execute or synthesize natural-language model output.
    return None


def write_candidate(script_text: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".ps1")
    os.close(fd)
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(script_text)
    return path


def is_parseable_powershell(script_text: str) -> bool:
    """Validate syntax and command names without executing the candidate."""
    encoded = base64.b64encode(script_text.encode("utf-16le")).decode("ascii")
    check = (
        "$s = [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('"
        + encoded
        + "'));"
        "$tokens = $null; $errors = $null;"
        "$ast = [System.Management.Automation.Language.Parser]::ParseInput($s, [ref]$tokens, [ref]$errors);"
        "if ($errors.Count -gt 0) { exit 1 };"
        "$unknown = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true) | "
        "ForEach-Object { $name = $_.GetCommandName(); if ($name -and -not (Get-Command $name -ErrorAction SilentlyContinue)) { $name } };"
        "if ($unknown) { exit 1 }"
    )
    result = powershell.run_powershell(check, timeout=15)
    return result.get("exit_code") == 0 and not result.get("stderr", "").strip()


def candidate_requires_admin(script_text: str) -> bool:
    """Heuristic: return True if script likely needs admin privileges.
    Checks for service/registry/system paths or privileged cmdlets.
    """
    low_priv_patterns = [
        r"Write-Output",
        r"Set-Content",
        r"Out-File",
        r"Add-Content",
        r"Write-Error",
        r"New-Item -Path \$?Env:USERPROFILE",
        r"Desktop",
        r"\$Env:USERPROFILE",
        r"WmiMonitorBrightnessMethods",
    ]
    high_priv_patterns = [
        r"Set-Service",
        r"Install-Module",
        r"Install-WindowsFeature",
        r"New-Item\s+-Path\s+" + re.escape("C:\\Windows"),
        r"New-Item\s+-Path\s+" + re.escape("C:\\Program Files"),
        r"sc\s+",
        r"reg\s+add",
        r"net\s+start",
        r"net\s+stop",
        r"Restart-Computer",
    ]
    txt = script_text or ""
    # if any high-priv pattern appears, require admin
    for p in high_priv_patterns:
        if re.search(p, txt, re.IGNORECASE):
            return True
    # Unknown scripts require admin approval by default.
    if not any(re.search(p, txt, re.IGNORECASE) for p in low_priv_patterns):
        return True

    # otherwise assume low-privilege if it matches only low_priv patterns
    # If it contains any path outside user profile, require admin
    if re.search(r"C:\\\\Windows|C:\\\\Program Files|C:\\Users\\\\All Users", txt, re.IGNORECASE):
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Orchestrator controller")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--dry-run", action="store_true", default=True, help="Perform a dry-run (default)")
    parser.add_argument("--live", action="store_true", help="Perform live run (implies --confirm)")
    parser.add_argument("--confirm", action="store_true", help="Confirm live execution and synthesis")
    parser.add_argument("--name", type=str, help="Tool name for synthesis")
    args = parser.parse_args()

    dry_run = args.dry_run and not args.live and not args.confirm
    do_live = args.live or args.confirm

    result = {"status": "ok", "steps": []}

    # 1. Generate candidate
    candidate = generate_candidate_from_llm(args.prompt)
    if not candidate:
        result["status"] = "error"
        result["error"] = "candidate_generation_failed"
        result["steps"].append("candidate_generation_failed")
        audit.log("candidate_generation_failed", user="local", details={"prompt": args.prompt})
        print(json.dumps(result))
        sys.exit(1)
    candidate_path = write_candidate(candidate)
    result["candidate_path"] = candidate_path
    result["steps"].append("candidate_generated")

    # 2. Create rollback point
    rb = safety.create_rollback(name=args.name or "orchestrator")
    audit.log("rollback_created", user="local", details={"rollback_id": rb.get("rollback_id")})
    result["rollback"] = rb
    result["steps"].append("rollback_created")

    # 3. Dry-run or live execution
    # read candidate content to decide privilege needs
    try:
        with open(candidate_path, 'r', encoding='utf-8') as fh:
            candidate_text = fh.read()
    except Exception:
        candidate_text = None

    safe_without_admin = False
    if candidate_text is not None and not candidate_requires_admin(candidate_text):
        safe_without_admin = True

    if dry_run:
        result["dry_run"] = True
        result["steps"].append("dry_run_complete")
        result["synthesized"] = False
        print(json.dumps(result))
        sys.exit(0)

    # 4. Live execution
    # admin check: allow non-admin if candidate is low-privilege (e.g., writing to user Desktop)
    if not auth.is_admin() and not safe_without_admin:
        result["status"] = "error"
        result["error"] = "admin_required"
        audit.log("execute_blocked_no_admin", user="local", details={"prompt": args.prompt})
        print(json.dumps(result))
        sys.exit(1)
    try:
        # execute the script via powershell wrapper
        exec_cmd = f"& '{candidate_path}'"
        exec_res = powershell.run_powershell(exec_cmd, timeout=60)
        audit.log("executed_script", user="local", details={"path": candidate_path, "exit_code": exec_res.get("exit_code")})
        result["execution"] = exec_res
        result["steps"].append("executed")
        if exec_res.get("exit_code") != 0 or exec_res.get("stderr", "").strip():
            result["status"] = "error"
            result["error"] = "script_execution_failed"
            audit.log("execute_failed", user="local", details={"path": candidate_path, "exit_code": exec_res.get("exit_code")})
            print(json.dumps(result))
            sys.exit(1)
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(json.dumps(result))
        sys.exit(1)

    # 5. Synthesize into MCP tool if execution successful and synthesis available
    synthesized = False
    if exec_res.get("exit_code") == 0 and build_wrapper is not None:
        name = args.name or Path(candidate_path).stem
        wrapper = build_wrapper(name, candidate)
        meta = {"name": name, "description": f"Synthesized from prompt: {args.prompt}", "version": "0.1.0", "created_by": "orchestrator"}
        try:
            saved = registry.add_tool(meta, code=wrapper)
            result["synthesized_tool"] = saved
            result["steps"].append("synthesized")
            synthesized = True
        except Exception as e:
            result["synthesis_error"] = str(e)

    result["synthesized"] = synthesized
    print(json.dumps(result))
    if result.get("status") == "ok":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
