# Build log

One row per session, newest last. Record what was built, what broke and how it was fixed.

| Date | Day | Session goal | Result | Problems and fixes |
|---|---|---|---|---|
| 2026-11-21 | 1 | Job descriptions for all 8 agents; create the repo | Spec drafted in `docs/agents.md`; repo created | |
| 2026-11-22 | 2 | Project skeleton: package, PydanticAI, model settings, `.env` | Package, model router with privacy rule, test agent, CLI, 8 tests, CI. 12 local models installed on the workstation | `mv` of Career-Pivot failed (folder already in Downloads): left repo in place |
| 2026-11-26 | 3 | Router, 8 stub agents, instructions for all 8, 30-case test set | Router (qwen3:8b) 100% on 30 cases, 6.2 s median; 18 tests; ADR 0001 accepted; latency runbook | Router took 30 s: hidden thinking (fixed with reasoning_effort none, 13x) + 27% CPU offload. Stale file copies to the PC (now verified after every write). Commit blocked for private email (switched to noreply). Days 3-5 slipped 3 days |
