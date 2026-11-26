# 0001: How requests reach the right agent

**Status:** proposed (Day 3). Finalised on Day 4 after the two-model comparison.
**Date:** 2026-11-26

## Context
Every request goes to one of 8 agents. Wrong routing makes the whole team feel broken.
Several agents overlap (Assistant/Prioritizer, CMO/Strategist, Advertiser/Money Saver).
Everything runs on local models on a GTX 1060 (6 GB).

## Options
| Option | Pessimistic | Optimistic | Realistic |
|---|---|---|---|
| A. I name the agent every time | I stop using it; too much to remember | 100% right, instant | Great as an override, bad as the only way |
| B. LLM router only | 65-70% on overlapping agents; 1-6 s per request | 90%+ with good descriptions | ~80%; most misses in 2 agent pairs |
| C. Embedding router (nomic-embed-text) | Weak on unusual wording | ~50 ms, no LLM call | Good for clear-cut requests only |
| D. One generalist agent with all tools | Degrades as tools grow; hard to audit per agent | Simplest to build | Fine for 3 tools, not 8 agents |
| E. Learn from my corrections | No data yet | Gets better with use | A v2 idea |

## Decision
B with A as an override: `@agent ...` skips the router. When the router's confidence is
below 0.6 it asks one question instead of guessing. C is added only if B is too slow.

## Consequences
- The specialist descriptions (`agents/registry.py`, incl. a "not this" line per agent) are
  now the main thing that decides accuracy, so they are tested on every change.
- Every routing change is scored against `eval/routing_cases.jsonl`.

## Known weakness
The first 30 test cases were written by Claude, not by me, so the score is likely optimistic.
My own requests get added as they come in.

## Revisit if
- `qwen3:8b` routing averages over 8 s → add the embedding fast path (C).
- Accuracy stays under 80% after fixing descriptions → reconsider the agent split itself.

## Results
| Date | Model | Accuracy | Hard cases | Avg time |
|---|---|---|---|---|
| 2026-11-26 | qwen3:8b (run 1, tool output) | 86.7% (3 errors) | 100% | 42 s |
| 2026-11-26 | qwen3:8b (constrained JSON, no thinking) | 93.3-96.7% | 88.9% | 36 s |
| 2026-11-26 | llama3.2:3b | 73.3% | 55.6% | 1.6 s |
| 2026-11-26 | qwen3:4b (thinking still on) | 93.3% | 88.9% | 55 s |
| 2026-11-26 | qwen3:4b, reasoning_effort none, 5 cases | 100% | 100% | 1.7 s |

Findings so far:
- qwen3:8b runs 27% on the CPU (doesn't fit in 6 GB): that's the latency. See `docs/runbooks/llm-latency.md`.
- Self-reported confidence is useless as an "ask" trigger: every wrong answer had confidence 0.8-1.0, and 0 misses were rescued.
- The LLM should not decide sensitivity; privacy needs a deterministic rule.
- Most of the latency was hidden thinking that `/no_think` did not switch off; `reasoning_effort: none` does (13x faster).
