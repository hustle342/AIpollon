"""Gemini Spark adapter stub for Sprint 1.

Usage:
  python agents/llm_adapter_gemini.py --test
  python agents/llm_adapter_gemini.py --prompt "hello"

The `--test` command prints GEMINI_OK and exits 0. The `--prompt` command returns a small JSON object.
"""
import argparse
import json
import sys
import uuid


def main():
    parser = argparse.ArgumentParser(description="Gemini Spark adapter stub (Sprint 1)")
    parser.add_argument("--test", action="store_true", help="Run adapter self-test")
    parser.add_argument("--prompt", type=str, help="Prompt to send to Gemini Spark (simulated)")
    args = parser.parse_args()

    if args.test:
        print("GEMINI_OK")
        sys.exit(0)

    if args.prompt:
        # Simulate a JSON response from Gemini Spark
        out = {
            "id": str(uuid.uuid4()),
            "response": f"simulated gemini reply to: {args.prompt}",
            "status": "ok"
        }
        print(json.dumps(out))
        sys.exit(0)

    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
