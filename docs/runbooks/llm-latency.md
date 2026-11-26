# Runbook: why is the local model slow?

A method for finding where inference time goes, written while debugging the
AI Team router. The same method applies to any HPC performance problem:
**predict, measure, break the time down, change one thing, re-measure.**

## 1. The symptom (2026-11-26)

`ai-team eval` with `qwen3:8b` on a GTX 1060 6 GB, 30 routing requests:

| Run | Change | Accuracy | Errors | Median | Min | Max |
|---|---|---|---|---|---|---|
| 1 | baseline (tool output, thinking on) | 86.7% | 3 | 27 s | 17 s | 120 s |
| 2 | constrained JSON output, thinking off | 96.7% | 0 | 31 s | 18 s | 132 s |

The fix in run 2 removed the errors but **not** the latency. So the slow part is
not the model "thinking". Something underneath is wrong.

## 2. Predict first: what *should* it take?

Never debug a slow system without an expected number. Without one, you can't
tell "slow" from "normal".

LLM inference has two phases with different bottlenecks:

| Phase | What happens | Bound by | Rough cost |
|---|---|---|---|
| **Prefill** (prompt eval) | Reads all input tokens at once | **Compute** (FLOPs), parallel | ~0.5-1 s for ~600 tokens on this GPU |
| **Decode** (generation) | One token at a time | **Memory bandwidth**: every token re-reads all the weights | see below |

Decode ceiling, back of the envelope (a roofline-style estimate):

```
tokens/sec  ≈  memory bandwidth / bytes read per token (≈ model size)
GTX 1060:      ~192 GB/s / ~5 GB  ≈  ~38 tok/s ceiling, ~25-30 tok/s in practice
CPU (DDR4):    ~40-50 GB/s / ~5 GB ≈  ~8-10 tok/s ceiling
```

A routing answer is ~60 output tokens, so the prediction is:
**~1 s prefill + ~2-3 s decode + network ≈ 3-5 s.**
Observed: 18-30 s. That's a **5-10x gap**, too big to be tuning. It's a structural cause.

## 3. Hypotheses, ranked by how well they explain a 5-10x gap

| # | Hypothesis | Would explain | How to check |
|---|---|---|---|
| H1 | **Partial CPU offload**: model + KV cache doesn't fit in 6 GB, so Ollama puts some layers on the CPU | 5-10x (CPU bandwidth is ~4x lower, and the slowest layer sets the pace) | `ollama ps` → PROCESSOR column; `nvidia-smi` memory use |
| H2 | **Model reload per call**: unloaded between requests | +3-10 s per call | `load_duration` in the timing breakdown; `ollama ps` UNTIL column |
| H3 | **Hidden thinking tokens** still generated | 2-10x more output tokens | `eval_count` (output tokens) in the timing breakdown |
| H4 | **Large context window** reserved (e.g. 32k) inflates the KV cache, which causes H1 | indirect | `ollama show qwen3:8b`, `OLLAMA_CONTEXT_LENGTH` |
| H5 | **Retries**: invalid output triggers a second or third call | 2-3x on some requests | count model requests per route (Day 4 audit log) |
| H6 | Network / proxy | < 0.1 s on a LAN | ping; time a tiny request |

H1 is the prime suspect: `qwen3:8b` at ~5.2 GB on a 6 GB card leaves almost no
room for the KV cache and CUDA overhead.

## 4. Measure: break one request into parts

Ollama's native API reports where the time went (all durations in nanoseconds).
`scripts/latency_probe.ps1` sends one request and prints the breakdown:

| Field | Meaning | Points to |
|---|---|---|
| `load_duration` | time to load the model into memory | H2 if > 1 s on repeat calls |
| `prompt_eval_count` / `prompt_eval_duration` | input tokens / prefill time | prefill speed (tok/s) |
| `eval_count` / `eval_duration` | output tokens / decode time | decode speed, and H3 if count is high |
| `total_duration` | everything | compare with client-side time: the gap is network + client |

Run it twice: the first call may include a load, the second shows steady state.

```powershell
.\scripts\latency_probe.ps1 -Model qwen3:8b
.\scripts\latency_probe.ps1 -Model qwen3:8b
.\scripts\latency_probe.ps1 -Model llama3.2:3b
ollama ps
nvidia-smi
```

How to read it:
- **Decode < ~15 tok/s on qwen3:8b** → H1 (offload). Confirm with `ollama ps`.
- **load_duration high on the 2nd call** → H2. Fix: `OLLAMA_KEEP_ALIVE=30m`.
- **eval_count in the hundreds** for a short JSON answer → H3.
- **llama3.2:3b (2 GB, fits easily) is many times faster per token** → confirms memory, not code.

## 5. Fixes, in order of cost (change one at a time, re-measure each)

| Fix | Targets | Trade-off |
|---|---|---|
| Use a smaller model for routing (`llama3.2:3b`, `qwen3:4b`) | H1 | possibly lower accuracy: measure it with `ai-team eval` |
| Cap the context: `num_ctx` 2048-4096 | H1, H4 | prompts must stay short (routing prompts are ~600 tokens) |
| Quantize the KV cache: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0` | H1 | tiny quality loss |
| Keep models loaded: `OLLAMA_KEEP_ALIVE=30m` | H2 | holds VRAM while idle |
| Don't route with an LLM at all for clear requests (embedding fast path) | all | another component to build; see decision record 0001 |
| Bigger GPU | H1 | money: the last resort, not the first |

## 6. Results

| Date | Test | Finding |
|---|---|---|
| 2026-11-26 | eval runs 1-2 | latency independent of thinking; gap 5-10x vs prediction |
| 2026-11-26 | `ollama ps` | **qwen3:8b = 6.0 GB, 27% CPU / 73% GPU** at a 4096 context. **H1 confirmed**: it doesn't fit in 6 GB, so about a quarter of the model runs from system RAM |
| 2026-11-26 | `ai-team eval --model llama3.2:3b` (2 GB, fully on GPU) | **1.6 s average vs 36 s**: ~23x faster, which confirms the bottleneck is memory, not code. But accuracy fell to 73% (vs 93-97%), so it's too inaccurate to route |
| 2026-11-26 | `ai-team eval --model qwen3:4b`, 30 cases | **55 s average: slower than the 8B model** despite fitting in VRAM. Breaks H1 for this model, so something else dominates |
| 2026-11-26 | qwen3:4b, 5 cases, `/no_think` in the prompt | 621 output tokens, 22.4 s median |
| 2026-11-26 | same, Ollama `"think": false` | 695 output tokens, 27.5 s: **ignored** |
| 2026-11-26 | same, `"reasoning_effort": "none"` | **48 output tokens, 1.7 s median**: **H3 confirmed**, thinking was never off |

**Diagnosis (final):** two causes stacked.
1. **H3, hidden thinking (the main one):** ~600 tokens of reasoning before every ~50-token
   answer. Only `reasoning_effort: "none"` switches it off through Ollama's OpenAI-compatible
   API; the `/no_think` prompt switch and the `think` field were silently ignored. 13x faster.
2. **H1, partial CPU offload:** qwen3:8b runs 27% on the CPU, so it stays slower than qwen3:4b.

**After the fix, 30 cases:** qwen3:4b 1.9 s median (90% accurate); qwen3:8b 6.2 s median
(100% accurate). Down from 31 s median: **5x faster for the 8B, with better accuracy**. The
remaining 8B gap vs the 4B is H1 (27% on the CPU); next experiment: `num_ctx` 2048 and
`OLLAMA_KV_CACHE_TYPE=q8_0` to fit it fully on the GPU.

**Lesson about metrics:** the library reported `reasoning_tokens: 0` on every run, including
the slow ones; the reasoning was counted in `output_tokens`. Cross-check one metric against
another before trusting it.

**Diagnosis:** H1, partial CPU offload. The slowest tier (system RAM, ~4x less bandwidth
than VRAM) sets the pace for every token, the same way the slowest rank sets the step
time in an HPC job.

**Trade-off exposed:** on this GPU, the accurate model (qwen3:8b) doesn't fit and the
fitting model (llama3.2:3b) isn't accurate. The next experiment looks for a model that
does both, before spending money on hardware.

## 7. The HPC parallel (for interviews)

| Here | In HPC |
|---|---|
| Predict tok/s from memory bandwidth | Roofline model: is the kernel compute- or bandwidth-bound? |
| Model spills from GPU to CPU | Working set exceeds cache/HBM, falls to slower memory tier |
| Slowest layer sets the pace | Amdahl's law / load imbalance: the slowest rank sets the step time |
| load_duration on every call | Job startup cost, data staging, cold caches |
| Break one request into phases | Profiling: time per phase before optimizing anything |
| Change one thing, re-measure | Controlled experiments; never tune two knobs at once |

**The interview story:** "The router was 5-10x slower than a bandwidth estimate
predicted. I broke one request into load, prefill and decode, found two stacked causes (hidden reasoning tokens and a model spilling onto the CPU), fixed
the first with one API setting, and cut median latency from 31 s to 6 s (and 2 s on a smaller model) while accuracy went up. The first fix I tried
(turning off reasoning) didn't move latency at all, which is why I measure before
changing things."
