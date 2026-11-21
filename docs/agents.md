# Agent job descriptions (v1 spec)

**Author:** Manny Bate · Drafted Day 1 (2026-11-21). Edit freely: this file is the contract each agent is built
and tested against.

Every agent follows the same rules:

- **One job, done well.** Anything else goes on the "Later" list at the bottom.
- **Typed output.** Each agent returns a Pydantic model, never free text, so results can be checked and tested.
- **No external actions.** Sending, posting, publishing and buying go to the approval queue.
- **Model choice.** `local` = Ollama on my hardware (private, free). `cloud` = Claude (better reasoning, costs money,
  never sees client data).

---

## 1. Assistant (orchestrator)

**Mission:** Be the single front door. Understand what I asked for and hand it to the right agent, or answer
directly if it's simple.

| | |
|---|---|
| Input | A chat message from me |
| Output | `Routing { agent, task, reason }`, then the specialist's result; once a day a `MorningBrief` |
| Tools | All other agents; the task store; the approval queue |
| Model | local |
| Approval | None (it only delegates) |
| Done when (v1) | Routes 20 sample requests to the right agent at least 18 times; the morning brief shows today's top 3 and pending approvals |

## 2. Prioritizer

**Mission:** Turn my task list into today's plan: what matters, in what order, and why.

| | |
|---|---|
| Input | Tasks from a Markdown checklist or CSV (title, due date, effort, project) |
| Output | `RankedTasks { tasks[{title, score, urgent, important, reason}], top3 }` |
| Tools | Task store (read/write) |
| Model | local |
| Approval | None |
| Done when (v1) | Given 15 real tasks, the top 3 match my own judgment, and every rank has a one-line reason |

## 3. Money Saver

**Mission:** Save me money two ways: tell me when something I want drops to my target price, and show me where
my money leaks.

| | |
|---|---|
| Input | (a) Watch list: item, target price, sources. (b) A bank or card CSV export |
| Output | `PriceAlert { item, price, source, link }`; `SavingsReport { subscriptions[], recurring[], suggestions[], monthly_savings }` |
| Tools | Deal RSS feeds and search for prices; CSV reader |
| Model | local (spending data stays on my machine) |
| Approval | None: it never buys or cancels anything |
| Done when (v1) | Catches a real price drop on Black Friday (Nov 27); lists every subscription in a month of statements |

## 4. Strategist

**Mission:** Turn goals into a weekly plan with milestones I can actually hit.

| | |
|---|---|
| Input | Goals, deadlines, available hours; for the job search: resume and target roles |
| Output | `WeeklyPlan { goals[], milestones[], daily_blocks[], risks[] }` |
| Tools | Task store; Prioritizer (pushes the plan's tasks into it) |
| Model | cloud |
| Approval | None |
| Done when (v1) | Produces my job-search plan for one week that fits my real hours and matches the 90-Day Roadmap week |

## 5. CMO

**Mission:** Plan marketing for my consulting business: who to reach, what to say, where and when.

| | |
|---|---|
| Input | Services offered, ideal client, budget, past results (if any) |
| Output | `MarketingPlan { audience, positioning, channels[], content_calendar[4 weeks] }` |
| Tools | None in v1 (planning only) |
| Model | cloud |
| Approval | None (it only plans) |
| Done when (v1) | A 4-week content calendar I would actually post from, built from my consulting services |

## 6. Advertiser

**Mission:** Turn the CMO's plan into ready-to-use ads and a budget split.

| | |
|---|---|
| Input | Campaign brief from the CMO; total budget |
| Output | `AdSet { channel, variants[3]{headline, body, call_to_action}, budget }` |
| Tools | Approval queue |
| Model | cloud |
| Approval | **Yes.** Every ad waits in the queue; nothing is posted or paid for automatically |
| Done when (v1) | 3 variants each for 2 channels, within platform character limits, sent to the queue |

## 7. Web Builder

**Mission:** Build a clean one-page website from a short brief.

| | |
|---|---|
| Input | Brief: offer, audience, contact details, tone |
| Output | `WebPage { html, title, sections[] }`, a single self-contained HTML file |
| Tools | HTML template; HTML validator; approval queue |
| Model | cloud (copy), template (layout) |
| Approval | **Yes**, before publishing anywhere |
| Done when (v1) | Builds a landing page for the consulting business that passes validation and looks right on a phone |

## 8. Video Editor

**Mission:** Turn a raw recording into a transcript, captions and short clips.

| | |
|---|---|
| Input | A video or audio file (under 15 minutes in v1) |
| Output | `VideoJob { transcript, captions_srt, clips[{start, end, title, file}] }` |
| Tools | Whisper (transcription), ffmpeg (cut silences, burn captions, export clips) |
| Model | local (Whisper and Ollama) |
| Approval | **Yes**, before posting anywhere |
| Done when (v1) | Turns a 5-minute recording into a captioned video and two 30–60 s clips |

---

## Later (not in v1)

- Posting to social media or ad platforms (behind approval)
- Sending email; calendar booking
- Client-facing agents for the consulting business (needs a privacy review first)
- Voice interface
