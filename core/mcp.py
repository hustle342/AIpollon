"""Simple MCP CLI: publish and list-tools for Sprint 4.

Usage:
  python -m core.mcp publish --file scripts/ps_examples/sample_queries.ps1 --name reset_bluetooth
  python -m core.mcp list-tools
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

from mcp_tools.tool_schema import validate_tool
from mcp_tools import registry
from tools.fastmcp_adapter import build_wrapper


def cmd_publish(file: str, name: str):
    p = Path(file)
    if not p.exists():
        print(json.dumps({"status": "error", "error": "file_not_found"}))
        sys.exit(2)
    script_text = p.read_text(encoding="utf-8")
    meta = {"name": name, "description": f"Published from {file}", "version": "0.1.0", "created_by": "developer"}
    try:
        validate_tool(meta)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(2)
    saved = registry.add_tool(meta, code=build_wrapper(name, script_text))
    print(json.dumps({"status": "ok", "tool": saved}))
    sys.exit(0)


def cmd_list():
    items = registry.list_tools()
    print(json.dumps({"status": "ok", "tools": items}))
    sys.exit(0)


def cmd_run(name: str):
    meta = registry.get_tool(name)
    if not meta or not meta.get("entrypoint"):
        print(json.dumps({"status": "error", "error": "tool_not_found"}))
        sys.exit(2)
    entrypoint = Path(meta["entrypoint"])
    if not entrypoint.exists():
        print(json.dumps({"status": "error", "error": "entrypoint_not_found"}))
        sys.exit(2)
    try:
        spec = importlib.util.spec_from_file_location(f"mcp_tool_{name}", entrypoint)
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise RuntimeError("entrypoint is not importable")
        spec.loader.exec_module(module)
        result = module.run()
        print(json.dumps({"status": "ok", "tool": name, "result": result}, ensure_ascii=False))
        sys.exit(0 if result.get("exit_code") == 0 else 1)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="MCP CLI (publish/list-tools)")
    sub = parser.add_subparsers(dest="cmd")
    p_pub = sub.add_parser("publish")
    p_pub.add_argument("--file", required=True)
    p_pub.add_argument("--name", required=True)
    p_list = sub.add_parser("list-tools")
    p_run = sub.add_parser("run")
    p_run.add_argument("--name", required=True)

    args = parser.parse_args()
    if args.cmd == "publish":
        cmd_publish(args.file, args.name)
    elif args.cmd == "list-tools":
        cmd_list()
    elif args.cmd == "run":
        cmd_run(args.name)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
