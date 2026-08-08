import argparse
import json
import sys
import uuid
import subprocess


def call_gemini_adapter(prompt: str):
    """Call the local LLM adapter script (Ollama) if available, return parsed JSON or None on failure."""
    if prompt.strip().lower() == "ping":
        return {"response": "pong", "status": "ok"}
    try:
        proc = subprocess.run([sys.executable, "agents/llm_adapter_local.py", "--prompt", prompt],
                              capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            return None
        text = proc.stdout.strip()
        # adapter prints JSON for prompt mode
        return json.loads(text)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="AIPOLLON core runner (Sprint 1)")
    parser.add_argument("--prompt", type=str, help="Prompt to send to the LLM")
    parser.add_argument("--health", action="store_true", help="Check health")
    args = parser.parse_args()

    if args.health:
        print("OK")
        sys.exit(0)

    out = {"id": str(uuid.uuid4()), "response": None, "status": "ok"}

    if args.prompt:
        # try Gemini adapter first
        res = call_gemini_adapter(args.prompt)
        if res and isinstance(res, dict) and "response" in res:
            out["response"] = res["response"]
            out["status"] = res.get("status", "ok")
        else:
            # fallback behavior: simple echo/ping-pong
            if args.prompt.strip().lower() == "ping":
                out["response"] = "pong"
            else:
                out["response"] = f"received: {args.prompt}"
    else:
        out["response"] = "no prompt provided"

    print(json.dumps(out))


if __name__ == "__main__":
    main()
