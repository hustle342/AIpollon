"""PowerShell execution wrapper for Sprint 2.

Provides a safe CLI entrypoint to run PowerShell commands and return structured JSON.
Usage examples:
  python -m core.powershell --cmd "Write-Output 'hello'"
  python -m core.powershell --cmd "Start-Sleep -Seconds 5" --timeout 2
"""
import argparse
import json
import locale
import os
import subprocess
import sys
import time


def run_powershell(cmd: str, timeout: int = 30, binary: str | None = None):
    binary = binary or os.environ.get("AIPOLLON_POWERSHELL", "powershell")
    cmd_list = [binary, "-NoProfile", "-NonInteractive", "-Command", cmd]
    start = time.time()
    try:
        proc = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            encoding=locale.getpreferredencoding(False),
            errors="replace",
            timeout=timeout,
        )
        duration = time.time() - start
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
            "duration": duration,
            "status": "ok" if proc.returncode == 0 else "error",
        }
    except subprocess.TimeoutExpired as e:
        duration = time.time() - start
        # attempt to kill child process if still running
        try:
            if e.spawn:
                e.spawn.kill()
        except Exception:
            pass
        return {
            "stdout": e.stdout or "",
            "stderr": (e.stderr or "") + "\nCommand timed out",
            "exit_code": -1,
            "duration": duration,
            "status": "timed_out",
        }
    except FileNotFoundError as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -2,
            "duration": 0,
            "status": "binary_not_found",
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -3,
            "duration": time.time() - start,
            "status": "failed",
        }


def main():
    parser = argparse.ArgumentParser(description="Run a PowerShell command and return JSON")
    parser.add_argument("--cmd", type=str, required=True, help="PowerShell command to run (wrap in quotes)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    parser.add_argument("--binary", type=str, help="PowerShell binary to use (overrides env var)")
    args = parser.parse_args()

    res = run_powershell(args.cmd, timeout=args.timeout, binary=args.binary)
    print(json.dumps(res))
    if res.get("exit_code", 1) == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
