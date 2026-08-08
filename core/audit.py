"""Simple audit logger for actions.

Writes line-delimited JSON records to `.audit/log.jsonl`.
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List

AUDIT_DIR = Path(__file__).resolve().parent.parent / ".audit"
AUDIT_DIR.mkdir(exist_ok=True)
LOG_FILE = AUDIT_DIR / "log.jsonl"


def log(action: str, user: str = "system", details: Any = None) -> Dict:
    entry = {
        "ts": int(time.time()),
        "action": action,
        "user": user,
        "details": details,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_all() -> List[Dict]:
    items: List[Dict] = []
    if not LOG_FILE.exists():
        return items
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Audit logger CLI")
    parser.add_argument("--log", nargs=2, metavar=("ACTION", "USER"), help="Log an action with user")
    parser.add_argument("--details", type=str, help="JSON string details")
    parser.add_argument("--dump", action="store_true", help="Dump all audit entries")
    args = parser.parse_args()
    if args.log:
        action, user = args.log
        details = None
        if args.details:
            try:
                details = json.loads(args.details)
            except Exception:
                details = args.details
        entry = log(action, user, details)
        print(json.dumps(entry))
        return
    if args.dump:
        items = read_all()
        print(json.dumps({"items": items}))
        return
    parser.print_help()


if __name__ == "__main__":
    main()
