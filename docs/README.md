# Docs & Demos

This folder contains quick demo instructions and examples for using AIPOLLON from the CLI.

Demo: synthesize a tool from a script

```
python -m tools.fastmcp_adapter --script scripts/ps_examples/sample_queries.ps1 --name example_tool
python -m core.mcp list-tools
python -m core.mcp run --name example_tool

python -m core.mcp publish --file scripts/ps_examples/sample_queries.ps1 --name reset_bluetooth
```

Demo: quick LLM prompt (uses local Ollama if available, otherwise simulated reply)

```
python agents/llm_adapter_local.py --prompt "How to reset Bluetooth driver on Windows?"
```

Demo: orchestrator dry-run (safe)

```
python -m agents.controller --prompt "Bluetooth not showing in device manager" --dry-run
```

Demo: orchestrator live (requires admin and careful review)

```
python -m agents.controller --prompt "Bluetooth not showing in device manager" --confirm --name reset_bt
```

Notes
- All operations that change the system require explicit `--confirm` and admin privileges.
- Use `AIPOLLON_FORCE_ADMIN=1` environment variable for CI/mocked admin in tests.
