"""Rollback / safety scaffold (Sprint 3).

Implements a safe, file-backed rollback point registry for development and testing.
This avoids making System Restore changes; a real implementation can replace this
with Windows System Restore or more advanced snapshot logic behind the same API.
"""
import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

ROLLBACK_DIR = Path(__file__).resolve().parent.parent / ".rollback"
ROLLBACK_DIR.mkdir(exist_ok=True)


def create_rollback(name: str | None = None):
    rid = str(uuid.uuid4())
    ts = int(time.time())
    meta = {
        "id": rid,
        "name": name or "manual",
        "created_at": ts,
        "note": "file-backed rollback point (dev/test only)",
    }
    path = ROLLBACK_DIR / f"{rid}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f)
    return {"status": "ok", "rollback_id": rid, "path": str(path)}


def list_rollbacks():
    items = []
    for p in ROLLBACK_DIR.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception:
            continue
    return {"status": "ok", "items": items}


def restore_rollback(rid: str):
    path = ROLLBACK_DIR / f"{rid}.json"
    if not path.exists():
        return {"status": "not_found", "rollback_id": rid}
    # In real system, execute restore actions. Here we just acknowledge.
    return {"status": "restored", "rollback_id": rid}


def verify_restore(rid: str):
    """Verify the rollback point exists and is readable. Returns dict with status."""
    path = ROLLBACK_DIR / f"{rid}.json"
    if not path.exists():
        return {"status": "not_found", "rollback_id": rid}
    try:
        with open(path, "r", encoding="utf-8") as f:
            _ = json.load(f)
        return {"status": "ok", "rollback_id": rid}
    except Exception as e:
        return {"status": "corrupt", "rollback_id": rid, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Core safety/rollback scaffold")
    parser.add_argument("--create", action="store_true", help="Create a rollback point")
    parser.add_argument("--name", type=str, help="Name for the rollback point")
    parser.add_argument("--list", action="store_true", help="List rollback points")
    parser.add_argument("--restore", type=str, help="Restore rollback point by id")
    args = parser.parse_args()

    if args.create:
        res = create_rollback(args.name)
        print(json.dumps(res))
        sys.exit(0)

    if args.list:
        res = list_rollbacks()
        print(json.dumps(res))
        sys.exit(0)

    if args.restore:
        res = restore_rollback(args.restore)
        print(json.dumps(res))
        if res.get("status") == "restored":
            sys.exit(0)
        else:
            sys.exit(2)

    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
