#!/usr/bin/env python3
"""Main CLI: interactive prompt REPL that sends prompts to the local LLM adapter

Usage:
  python main.py            # starts interactive REPL
  python main.py --prompt "hello"   # single prompt and exit

This file tries to use the in-process `OllamaAdapter` from
`agents.llm_adapter_local` when available. If that import fails it falls
back to calling the adapter script as a subprocess which itself falls back
to a simulated reply when Ollama is not running.
"""
import argparse
import json
import os
import subprocess
import sys
from typing import Optional

PROJECT_ROOT = __file__


def call_adapter_subprocess(prompt: str) -> str:
    proc = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(PROJECT_ROOT), "agents", "llm_adapter_local.py"), "--prompt", prompt],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return f"adapter error: {proc.stderr.strip()}"
    try:
        out = json.loads(proc.stdout)
        return out.get("response", proc.stdout.strip())
    except Exception:
        return proc.stdout.strip()


def make_adapter():
    try:
        from agents.llm_adapter_local import OllamaAdapter

        return OllamaAdapter()
    except Exception:
        return None


def single_prompt(adapter, prompt: str) -> None:
    if adapter is not None:
        res = adapter.generate(prompt)
        print(res.get("response"))
    else:
        print(call_adapter_subprocess(prompt))


def repl(adapter) -> None:
    print("AIPOLLON REPL — type prompt and press Enter. Ctrl-D or 'exit' to quit.")
    try:
        while True:
            try:
                prompt = input("> ")
            except EOFError:
                print()
                break
            if not prompt:
                continue
            if prompt.strip().lower() in ("exit", "quit"):
                break
            # Get assistant response
            if adapter is not None:
                res = adapter.generate(prompt)
                text_resp = res.get("response")
            else:
                text_resp = call_adapter_subprocess(prompt)
            print(text_resp)

            # Ask user if they'd like an automated fix attempt
            try:
                ans = input("Attempt to fix this issue automatically? (y/N): ")
            except EOFError:
                ans = "n"
            if ans.strip().lower() in ("y", "yes"):
                # call controller in live confirm mode
                print("Preparing to run automated remediation (requires admin).")
                name = "from_repl"
                # invoke controller as subprocess with confirm
                try:
                    proc = subprocess.run(
                        [sys.executable, "-m", "agents.controller", "--prompt", prompt, "--confirm", "--name", name],
                        capture_output=True,
                        text=True,
                        timeout=90,
                    )
                except subprocess.TimeoutExpired:
                    print("Controller timed out after 90 seconds.")
                    continue
                print("--- Controller output ---")
                if proc.stdout:
                    print(proc.stdout)
                if proc.stderr:
                    print(proc.stderr, file=sys.stderr)
    except KeyboardInterrupt:
        print()


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="AIPOLLON main interactive prompt")
    parser.add_argument("--prompt", type=str, help="Single prompt to send and exit")
    args = parser.parse_args(argv)

    adapter = make_adapter()

    if args.prompt:
        single_prompt(adapter, args.prompt)
        return 0

    repl(adapter)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
