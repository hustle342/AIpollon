"""FastMCP adapter (Sprint 5)

Converts a script into a simple MCP tool: validates metadata, generates a Python wrapper,
and registers the tool in the local registry.

Usage:
  python -m tools.fastmcp_adapter --script scripts/ps_examples/sample_queries.ps1 --name reset_bluetooth
  python -m tools.fastmcp_adapter --script scripts/ps_examples/sample_queries.ps1 --meta meta.json

Meta file can be JSON or a simple YAML-like `key: value` plain text file.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict

from mcp_tools.tool_schema import validate_tool
from mcp_tools import registry


def read_meta_file(path: Path) -> Dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    # very lightweight YAML-like parser for simple key: value pairs
    meta = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta


WRAPPER_TEMPLATE = '''"""Auto-generated MCP wrapper for {name}
"""
import tempfile
import json
import os
from core.powershell import run_powershell

SCRIPT_CONTENT = r"""{script_content}"""


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
'''


def build_wrapper(name: str, script_text: str) -> str:
    # Escape triple quotes in script content
    esc = script_text.replace('"""', '""\'"')
    return WRAPPER_TEMPLATE.format(name=name, script_content=esc)


def main():
    parser = argparse.ArgumentParser(description="FastMCP adapter: script -> MCP tool")
    parser.add_argument("--script", required=True)
    parser.add_argument("--meta", help="Metadata file (json or simple yaml)")
    parser.add_argument("--name", help="Tool name override")
    args = parser.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        print(json.dumps({"status": "error", "error": "script_not_found"}))
        sys.exit(2)
    script_text = script_path.read_text(encoding="utf-8")

    meta = {"version": "0.1.0"}
    if args.meta:
        meta_path = Path(args.meta)
        if not meta_path.exists():
            print(json.dumps({"status": "error", "error": "meta_not_found"}))
            sys.exit(2)
        meta.update(read_meta_file(meta_path))

    # name resolution
    name = args.name or meta.get("name") or script_path.stem
    meta["name"] = name
    meta.setdefault("description", f"Synthesized from {str(script_path)}")

    try:
        validate_tool(meta)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(2)

    wrapper = build_wrapper(name, script_text)
    saved = registry.add_tool(meta, code=wrapper)
    print(json.dumps({"status": "ok", "tool": saved}))
    sys.exit(0)


if __name__ == "__main__":
    main()
