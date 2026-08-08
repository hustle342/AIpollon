"""Auto-generated MCP wrapper for from_repl
"""
import tempfile
import json
import os
from core.powershell import run_powershell

SCRIPT_CONTENT = r"""$ErrorActionPreference = 'Stop'
$brightness = 50
$methods = Get-WmiObject -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods
if (-not $methods) { throw 'No WMI monitor brightness method is available.' }
$methods | ForEach-Object { $_.WmiSetBrightness(1, $brightness) | Out-Null }
Write-Output "Brightness set to $brightness percent."
"""


def run():
    # write script to temp file and execute via PowerShell wrapper
    fd, path = tempfile.mkstemp(suffix=".ps1")
    os.close(fd)
    with open(path, "w", encoding="utf-8-sig") as f:
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
