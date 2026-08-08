"""Auto-generated MCP wrapper for example_tool
"""
import tempfile
import json
import os
from core.powershell import run_powershell

SCRIPT_CONTENT = r"""# Sample PowerShell queries for safe testing
# List Bluetooth service status
Get-Service -Name bthserv | Select-Object Name, Status

# Simple output for testing
Write-Output "hello from powershell sample"

# Sleep example (used for timeout tests)
Start-Sleep -Seconds 5
"""


def run():
    # write script to temp file and execute via PowerShell wrapper
    fd, path = tempfile.mkstemp(suffix=".ps1")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(SCRIPT_CONTENT)
    res = run_powershell("& '" + path.replace("'", "''") + "'")
    # cleanup
    try:
        os.remove(path)
    except Exception:
        pass
    return res


if __name__ == "__main__":
    print(json.dumps(run()))
