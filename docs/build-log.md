# Build log

One row per session, newest last. Record what was built, what broke and how it was fixed.

| Date | Day | Session goal | Result | Problems and fixes |
|---|---|---|---|---|
| 2026-11-21 | 1 | Job descriptions for all 8 agents; create the repo | Spec drafted in `docs/agents.md`; repo created | |
| 2026-11-22 | 2 | Project skeleton: package, PydanticAI, model settings, `.env` | Package, model router with privacy rule, test agent, CLI, 8 tests, CI. 12 local models installed on the workstation | `mv` of Career-Pivot failed (folder already in Downloads): left repo in place |
| 2026-11-26 | 3 | Router, 8 stub agents, instructions for all 8, 30-case test set | Router (qwen3:8b) 100% on 30 cases, 6.2 s median; 18 tests; ADR 0001 accepted; latency runbook | Router took 30 s: hidden thinking (fixed with reasoning_effort none, 13x) + 27% CPU offload. Stale file copies to the PC (now verified after every write). Commit blocked for private email (switched to noreply). Days 3-5 slipped 3 days |
| 2026-11-27 | — | VS Code + Claude Code setup | VS Code 1.147.0; Claude Code extension v2.1.330. Workspace trusted in VS Code and in Claude Code (own repo only). Built-in Copilot disabled via `chat.disableAIFeatures`. Extensions audited: no other AI assistants. Permission mode set to Manual. Read-only smoke test passed. **Why it matters:** trusting a workspace lets its repo config (hooks, MCP servers) run commands on this machine, so trust goes only to repos I own | VS Code opened in Restricted Mode, which disabled the Claude Code extension (fixed by trusting the workspace). VS Code ships a built-in Copilot chat panel even with no Copilot extension installed (fixed by setting `chat.disableAIFeatures` to true) |
