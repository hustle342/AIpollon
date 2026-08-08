"""Local MCP tool registry.

Stores tool metadata under `.mcp_registry/` and tool code under `.mcp_tools/`.
This is intentionally simple for Sprint 4 and suitable for unit tests.
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REG_DIR = PROJECT_ROOT / ".mcp_registry"
TOOLS_DIR = PROJECT_ROOT / "mcp_tools_files"
REG_DIR.mkdir(exist_ok=True)
TOOLS_DIR.mkdir(exist_ok=True)


def registry_path(name: str) -> Path:
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("tool name must contain only letters, numbers, '_' or '-'")
    return REG_DIR / f"{name}.json"


def _resolve_entrypoint(value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return str(path.resolve())


def add_tool(meta: Dict[str, Any], code: str | None = None) -> Dict[str, Any]:
    name = meta.get("name")
    if not name:
        raise ValueError("tool meta must include 'name'")
    meta = dict(meta)
    meta.setdefault("created_at", datetime.utcnow().isoformat() + "Z")
    if code is not None:
        tool_path = TOOLS_DIR / f"{name}.py"
        with open(tool_path, "w", encoding="utf-8") as f:
            f.write(code)
        meta["entrypoint"] = str(tool_path.resolve())
    path = registry_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return meta


def list_tools() -> List[Dict[str, Any]]:
    items = []
    for p in REG_DIR.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                item = json.load(f)
            entrypoint = item.get("entrypoint")
            if not entrypoint:
                candidate = TOOLS_DIR / f"{item.get('name', p.stem)}.py"
                if candidate.exists():
                    item["entrypoint"] = str(candidate.resolve())
            else:
                item["entrypoint"] = _resolve_entrypoint(entrypoint)
            items.append(item)
        except Exception:
            continue
    return items


def get_tool(name: str) -> Dict[str, Any] | None:
    p = registry_path(name)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        item = json.load(f)
    entrypoint = item.get("entrypoint")
    if entrypoint:
        item["entrypoint"] = _resolve_entrypoint(entrypoint)
    else:
        candidate = TOOLS_DIR / f"{name}.py"
        if candidate.exists():
            item["entrypoint"] = str(candidate.resolve())
    return item


def remove_tool(name: str) -> bool:
    p = registry_path(name)
    if p.exists():
        p.unlink()
    tool_file = TOOLS_DIR / f"{name}.py"
    if tool_file.exists():
        tool_file.unlink()
    return True


__all__ = ["add_tool", "list_tools", "get_tool", "remove_tool"]
