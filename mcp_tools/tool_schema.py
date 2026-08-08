"""Tool schema and lightweight validator for MCP tools.

This is a minimal schema used in Sprint 4. It does not depend on jsonschema,
but provides `validate_tool` to perform basic required-field checks.
"""
from typing import Any, Dict

TOOL_SCHEMA = {
    "required": ["name", "description", "version"],
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": "string"},
        "entrypoint": {"type": "string"},
        "created_by": {"type": "string"},
    },
}


def validate_tool(tool: Dict[str, Any]) -> None:
    """Raise ValueError if tool dict does not conform to minimal schema."""
    if not isinstance(tool, dict):
        raise ValueError("tool must be a dict")
    for k in TOOL_SCHEMA["required"]:
        if k not in tool:
            raise ValueError(f"missing required field: {k}")
    # basic type checks
    for k, spec in TOOL_SCHEMA["properties"].items():
        if k in tool and spec.get("type") == "string":
            if not isinstance(tool[k], str):
                raise ValueError(f"field {k} must be a string")


__all__ = ["TOOL_SCHEMA", "validate_tool"]
