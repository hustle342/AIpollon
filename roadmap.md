Roadmap for AIPOLLON — 10 Sprints (CLI-first, test-ready)

Overview
- Goal: Build a comprehensive, production-grade, CLI-first Windows repair agent that converts fixes into MCP tools. The project will be delivered in 10 sprints. Each sprint ends with a test-ready deliverable that the user will run and validate.
- Sprint length: 1 week per sprint (10 weeks total). Adjust duration if you prefer longer sprints.
- Testing strategy: All interactions are CLI-driven. Sprint 1 uses a local Ollama model (`qwen2.5-coder:7b`) for LLM-driven tests. CI can fall back to mocked endpoints if Ollama is not available.

Sprint format (applies to every sprint)
- Objective: short sentence describing the sprint goal.
- Scope: concrete list of features/tasks.
- Deliverables: files, CLI commands, and artifacts produced.
- Acceptance criteria (must be testable via CLI): explicit commands and expected outputs.
- Tasks: granular engineering steps.
- Dependencies & risks: short note.

Sprint 1 — Foundation & Ollama (qwen2.5-coder:7b) integration
- Objective: Create repository skeleton, basic CLI runner, and verify LLM workflow using Gemini Spark.
- Scope:
  - Project skeleton and folders: `core/`, `agents/`, `mcp_tools/`, `scripts/`, `tests/`, `docs/`.
  - Minimal `core/runner.py` CLI that accepts commands and prints structured JSON responses.
  - `agents/llm_adapter_local.py`: adapter to call local Ollama (test harness + HTTP shim).
  - `roadmap.md`, updated `readme.md` with Gemini testing instructions.
- Deliverables:
  - `core/runner.py` (CLI entrypoint)
  - `agents/llm_adapter_gemini.py` (stub + test script)
  - Example test script `tests/sprint1_gemini_test.sh` showing how to run a prompt and assert output fields
- Acceptance criteria / Test commands:
  - Run: `python -m core.runner --prompt "ping"` => returns valid JSON with keys `id`, `response`, `status`.
  - Run Ollama test harness: `python agents/llm_adapter_local.py --test` => exits 0 and prints `OLLAMA_OK` on success.
- Tasks:
  - Create skeleton folders and `__init__.py` stubs.
  - Implement `core/runner.py` with argparse and JSON output.
  - Implement Gemini adapter with a mockable HTTP client and environment-driven API key.
  - Add tests that assert CLI exit codes and JSON structure.
  - Dependencies & risks: Requires Ollama running locally (`qwen2.5-coder:7b`) at the configured host. If not available, use a mocked endpoint.

Sprint 2 — PowerShell execution layer
- Objective: Implement a safe PowerShell execution wrapper and basic command library.
- Scope:
  - `core/powershell.py`: run PowerShell commands, capture stdout/stderr/exit, timeouts, encoding.
  - `scripts/ps_examples/` with safe sample commands (query adapters, services).
  - Unit tests validating outputs and enforced timeouts.
- Deliverables: `core/powershell.py`, tests, sample scripts.
- Acceptance criteria:
  - `python -m core.powershell --cmd "Get-Service -Name bthserv"` prints structured JSON with `stdout` and `exit_code`.
  - Timeout test: long-running script killed and returns non-zero status.
- Tasks: implement subprocess wrapper, sanitization, tests.
- Risks: Running PowerShell requires safe defaults; tests must use mocked commands or harmless queries.

Sprint 3 — WMI & system helpers, rollback scaffold
- Objective: Add WMI helpers and a rollback/snapshot abstraction.
- Scope:
  - `core/wmi.py` wrappers for common queries (devices, drivers).
  - `core/safety.py` with rollback point API (create/restore) using PowerShell System Restore or file backups (abstracted behind interface).
  - Tests for simulated rollback flows.
- Deliverables: `core/wmi.py`, `core/safety.py`, tests.
- Acceptance criteria:
  - CLI: `python -m core.wmi --list-devices` returns JSON list.
  - `python -m core.safety --create --name "test"` returns success and `rollback_id`.
- Tasks: implement wrappers, define `RollbackPoint` data model, add tests.
- Risks: System Restore API requires admin; tests should be non-destructive or mocked.

Sprint 4 — MCP tool format & local registry
- Objective: Define MCP tool schema and local registry for generated tools.
- Scope:
  - `mcp_tools/tool_schema.py` (JSON/Python schema for tools)
  - `mcp_tools/registry.py` (local registry to list/add/remove tools)
  - CLI to publish a script as MCP tool: `aipollon publish --file scripts/xyz.ps1 --name reset_bluetooth`
- Deliverables: schema, registry, CLI commands, tests.
- Acceptance criteria:
  - Publish flow creates a registry entry and a tool file under `mcp_tools/`.
  - `aipollon list-tools` shows the new tool.
- Tasks: design schema, implement registry, wire CLI.
- Risks: Schema iteration needed as features expand.

Sprint 5 — FastMCP adapter & synthesis workflow
- Objective: Implement `fastmcp_adapter.py` that converts working scripts into MCP objects.
- Scope:
  - Adapter that accepts script path + metadata and outputs an MCP JSON and Python wrapper.
  - CLI: `aipollon synthesize --script scripts/reset_bt.ps1 --meta meta.yml`.
- Deliverables: `tools/fastmcp_adapter.py`, example conversion, tests.
- Acceptance criteria:
  - `aipollon synthesize` produces `mcp_tools/<name>.py` and a JSON metadata file.
- Tasks: implement template generation, metadata validation, tests.
- Risks: Template compatibility and metadata completeness.

Sprint 6 — Autonomous remediation flow (manual trigger)
- Objective: Wire LLM -> plan -> execute -> synthesize pipeline, triggerable from CLI.
- Scope:
  - `agents/controller.py` that orchestrates: query LLM, generate candidate script, run in dry-run, create rollback, execute, synthesize.
  - Dry-run mode only for safety by default.
- Deliverables: controller, CLI, integration tests (mock LLM and PS layer).
- Acceptance criteria:
  - `aipollon run --prompt "Bluetooth missing" --dry-run` produces a candidate script, logs steps, and exits success.
- Tasks: implement orchestration, logging, dry-run enforcement.
- Risks: Safety and false-positive actions; ensure dry-run is default.

Sprint 7 — Tests, CI, and Windows runner setup
- Objective: Add CI workflows, run unit tests and integration tests in Windows runners.
- Scope:
  - GitHub Actions workflows `ci.yml` for Windows and matrix builds.
  - Test harness scripts to run test suites and smoke tests using GitHub Windows runner.
- Deliverables: `.github/workflows/ci.yml`, test reports, badges.
- Acceptance criteria:
  - CI pipeline completes for the main branch with tests passing (mocked system interactions where required).
- Tasks: create workflows, ensure tests are deterministic.
- Risks: Runner environment differences; use mocks where destructive.

Sprint 8 — Local LLM adapter & fallback to Gemini
- Objective: Implement local LLM adapter (Ollama/Qwen) and keep Gemini Spark adapter as CI/test fallback.
- Scope:
  - `agents/llm_adapter_local.py` with config and fallback logic.
  - Tests to verify same structured output for both adapters.
- Deliverables: local adapter, docs on switching providers, tests.
- Acceptance criteria:
  - CLI: `aipollon llm --provider local --test` and `--provider gemini --test` both pass.
- Tasks: implement adapter, adapter interface, tests.
- Risks: model resource requirements; include clear docs.

Sprint 9 — Hardening: permissions, audit, and rollback verification
- Objective: Harden permission checks, audit logging, and fully exercise rollback flows.
- Scope:
  - Add `core/auth.py` (admin-check wrapper), structured audit logs, and full rollback end-to-end test harness.
  - Integration tests that create and restore rollback points in a safe sandbox mode.
- Deliverables: `core/auth.py`, audit logs, tests.
- Acceptance criteria:
  - `aipollon run --unsafe` blocked without admin; audit logs contain full action trail.
  - Rollback test completes and verifies state restored.
- Tasks: implement audit format, add admin guard, write sandboxed rollback tests.
- Risks: System-level operations must be isolated.

Sprint 10 — Polish, docs, demos, and release
- Objective: Finalize docs, create demo scenarios, package release artifacts and a contributor guide.
- Scope:
  - `docs/` with step-by-step CLI demos (Bluetooth reset, driver reinstall), `CONTRIBUTING.md`, `CHANGELOG.md`, `setup.py`/`pyproject.toml` and `requirements.txt` finalization.
  - Create release candidate and verification checklist.
- Deliverables: docs, packaged distribution, release notes.
- Acceptance criteria:
  - All CLI demos run end-to-end in dry-run and live modes (where safe) following docs.
  - Release candidate build succeeds locally and in CI.
- Tasks: finalize docs, run full test matrix, prepare release tags.
- Risks: Last-minute compatibility issues; freeze features before release.

Appendix — Testing checklist templates (apply to each sprint)
- Basic CLI health: `python -m core.runner --health` => `OK`.
- JSON contract validation: tool outputs must validate against schema using `tests/validate_contract.py`.
- Exit codes: 0 success, non-zero for controlled failures.
- Logging: `--log-level debug` shows actionable steps and timestamps.

Notes
- Keep everything CLI-first; no GUI required.
- Make mocks and dry-run the default for any system-modifying operation; require explicit `--confirm` for live runs.
- Use environment variables (and `.env.example`) for provider API keys and to switch Gemini/local LLM.

Next steps
- If you approve, I will scaffold the repository skeleton and implement Sprint 1 artifacts (runner + Gemini adapter stubs).