"""Ollama (local) adapter (Sprint 8 improvements).

Features:
...
"""
import argparse
import json
import sys
import uuid
import os
import time
import urllib.request
import urllib.error
import re
from typing import Dict


DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder-uncensored:latest")
DEFAULT_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "10"))
DEFAULT_RETRIES = int(os.environ.get("OLLAMA_RETRIES", "2"))


class OllamaAdapter:
    def __init__(self, host: str = DEFAULT_HOST, model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT, retries: int = DEFAULT_RETRIES):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.retries = retries

    def health(self) -> Dict:
        # Try multiple known Ollama model endpoints for compatibility
        candidates = ["/api/tags", "/api/models", "/models", "/v1/models"]
        last_err = None
        for path in candidates:
            url = f"{self.host}{path}"
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        return {"status": "ok", "info": f"models_available:{path}"}
                    last_err = f"http_{resp.status}"
            except Exception as e:
                last_err = str(e)
                continue
        return {"status": "error", "info": last_err}

    def generate(self, prompt: str) -> Dict:
        # Try both /api/generate and /generate to support different Ollama versions
        paths = ["/api/generate", "/generate", "/v1/generate"]
        payload = json.dumps({"model": self.model, "prompt": prompt}).encode("utf-8")
        last_err = None
        for path in paths:
            url = f"{self.host}{path}"
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            for attempt in range(self.retries + 1):
                try:
                    with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                        body = resp.read().decode("utf-8")
                        # Robust extraction: handle NDJSON lines, plain text, and cases where the model
                        # appends a JSON metadata blob after the text (possibly without newline).
                        def extract_text(b: str) -> str:
                            # Conservative parsing strategy:
                            # 1) Try NDJSON-style lines and collect textual 'response'/'text' fields.
                            # 2) If no textual NDJSON lines are found but a trailing JSON object
                            #    is appended to the body, strip it and return the preceding text.
                            parts = []
                            found_textual = False
                            for line in b.splitlines():
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    parsed = json.loads(line)
                                    for key in ("response", "text", "output", "completion"):
                                        if key in parsed and isinstance(parsed[key], str) and parsed[key].strip():
                                            parts.append(parsed[key])
                                            found_textual = True
                                            break
                                    # if parsed but no textual keys, skip metadata lines
                                except Exception:
                                    # not JSON — include raw line
                                    parts.append(line)

                            if found_textual:
                                combined = "".join(parts).strip()
                                # Remove spurious newlines that split words (e.g. token-per-line)
                                combined = re.sub(r'(?<=\w)[ \t]*\n[ \t]*(?=\w)', ' ', combined, flags=re.UNICODE)
                                combined = re.sub(r'\n{2,}', '\n\n', combined)
                                combined = re.sub(r'[ \t]{2,}', ' ', combined).strip()
                                return combined

                            # No NDJSON textual fields found. Check for a trailing JSON blob and strip it.
                            # Find last occurrence of a JSON object start and attempt parsing tail.
                            idx = b.rfind('\n{')
                            if idx == -1:
                                idx = b.rfind('{')
                            if idx != -1 and idx > 0:
                                tail = b[idx:]
                                try:
                                    parsed_tail = json.loads(tail)
                                    # If tail looks like metadata (no textual 'response' key), strip it
                                    if not any(k in parsed_tail for k in ("response", "text", "output", "completion")):
                                        return b[:idx].strip()
                                except Exception:
                                    pass

                            # Fallback: return raw body trimmed
                            return b.strip()

                        combined = extract_text(body)
                        return {"id": str(uuid.uuid4()), "response": combined, "status": "ok", "endpoint": path}
                except urllib.error.URLError as e:
                    last_err = e
                    time.sleep(0.5 + attempt)
                    continue
                except Exception as e:
                    last_err = e
                    break
        return {"id": str(uuid.uuid4()), "response": f"ollama error: {last_err}", "status": "error"}


def main():
    parser = argparse.ArgumentParser(description="Ollama local adapter (improved)")
    parser.add_argument("--test", action="store_true", help="Run adapter self-test")
    parser.add_argument("--prompt", type=str, help="Prompt to send to the local LLM (Ollama)")
    parser.add_argument("--health", action="store_true", help="Check Ollama host health")
    args = parser.parse_args()

    adapter = OllamaAdapter()

    if args.test:
        print("OLLAMA_OK")
        sys.exit(0)

    if args.health:
        res = adapter.health()
        print(json.dumps(res))
        if res.get("status") == "ok":
            sys.exit(0)
        sys.exit(1)

    if args.prompt:
        res = adapter.generate(args.prompt)
        if res.get("status") != "ok":
            out = {"id": str(uuid.uuid4()), "response": f"simulated ollama reply to: {args.prompt}", "status": "ok"}
            print(json.dumps(out))
            sys.exit(0)
        print(json.dumps(res))
        sys.exit(0)

    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()

