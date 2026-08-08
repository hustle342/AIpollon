"""Auto-generated MCP wrapper for content_smoke
"""
import tempfile
import json
import os
from core.powershell import run_powershell

SCRIPT_CONTENT = r"""$p = Join-Path $Env:USERPROFILE 'Desktop'
$path = Join-Path $p 'seyrantepe.txt'
Set-Content -Path $path -Value 'gaziantep''i çok seviyorum' -Encoding UTF8
Write-Output "Created: $path"
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
