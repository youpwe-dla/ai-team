# AI Team

**Author:** Manny Bate · [github.com/youpwe-dla](https://github.com/youpwe-dla)

A personal team of 8 AI agents that run my day, my job search and the marketing for my consulting
practice. One Assistant takes every request and hands it to the right specialist. Everything runs on
my own hardware with a local model; a cloud model is used only for harder reasoning.

**Status:** Day 3 of 18 (target: Dec 8, 2026). See the [build log](docs/build-log.md).

## The team

| Agent | Job | Approval needed before it acts outside my machine |
|---|---|---|
| Assistant | Front door: routes requests, writes the morning brief | No |
| Prioritizer | Ranks tasks, picks today's top 3 | No |
| Money Saver | Price alerts on a watch list; finds waste in spending | No (never buys) |
| Strategist | Turns goals into a weekly plan | No |
| CMO | Marketing plan and content calendar for the consulting business | No |
| Advertiser | Ad copy variants and budget split | **Yes** |
| Web Builder | One-page website from a brief | **Yes** |
| Video Editor | Recording → transcript, captions, short clips | **Yes** |

Full job descriptions: [docs/agents.md](docs/agents.md).

## Ground rules

- No agent sends, posts, publishes or buys anything. External actions go to an **approval queue**.
- Every agent call is logged: agent, model, tokens, cost, result.
- Client data never goes to a cloud model.
- API keys live in `.env`, which is never committed.
- Cloud spend cap for the whole build: **$20**.

## Stack (planned)

Python 3.12 · PydanticAI · Ollama (`qwen3:8b` default, `llama3.2:3b` fast, `deepseek-r1:8b` reasoning) · Claude (cloud, optional) · SQLite ·
FastAPI · Whisper + ffmpeg · Docker · GitHub Actions · Argo CD on a k3s homelab cluster.

## Repository layout

```
docs/
  agents.md        job description for each agent (the spec)
  build-log.md     dated log of every session, problem and fix
src/ai_team/
  settings.py      config from .env
  models.py        Task, Business (budget / consulting / personal), Sensitivity, Tier
  llm.py           picks the model; client data always stays local
  router.py        picks one of the 8 agents, or asks when unsure
  agents/          registry (who handles what), stubs, one module per agent as built
  prompts/         each agent's instructions
  eval_routing.py  scores the router against eval/routing_cases.jsonl
  cli.py           `ai-team check | ask | route | eval`
eval/              labeled test requests and saved results
docs/decisions/    one record per design decision
tests/             privacy-rule and agent tests (run in CI)
```

## Quick start (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
ai-team check
ai-team ask "what should i work on first"
ai-team ask "@money is a 7020 for 250 a good deal"   # skip the router
ai-team eval                                     # score the router
pytest -q
```
