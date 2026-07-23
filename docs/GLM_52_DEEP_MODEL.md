# GLM-5.2 — the local DEEP model (colibrì)

> **744B MoE, int4, 357 GB on disk. Runs entirely offline on this box.**
> Use it when you want a *more considered* answer and can afford to wait minutes.
> **It is not interactive.** Budget the time before you call it.

---

## 1. THE SPEED REALITY — read this first

**~0.26 tokens/sec on CPU** (measured 2026-07-23, 64 tokens in 222 s).

| You ask for | It takes |
|---|---|
| 64 tokens | ~4 minutes |
| 250 tokens | ~16 minutes |
| 500 tokens | ~32 minutes |
| a full agent turn | **many minutes to an hour** |

Plus **prefill**: a 2,900-token prompt costs ~6–18 min *before the first token*. A long
system prompt is expensive here in a way it is not on a normal model.

**THEREFORE:**
- **Cap `max_tokens`.** Ask for 100 tokens, not 4000. The cost is linear.
- **Keep the prompt short.** Prefill dominates for short answers.
- **Set a client timeout of 1800 s or more**, or you will kill it mid-answer and see
  `Stream ended without finish_reason` (see §5).
- **Never put it on an interactive path.** It is a batch/consultation tool.
- If you need a fast local model, use **LM Studio on :1234** instead — 50+ tok/s.

---

## 2. START / STOP

| Action | Command |
|---|---|
| Start (default, **CPU**, 0 VRAM) | `E:\pi-servers\START GLM-5.2.cmd` |
| Start (GPU — only if LM Studio unloaded) | `E:\pi-servers\START GLM-5.2 (GPU).cmd` |
| Stop | `E:\pi-servers\STOP GLM-5.2.cmd` |

**CPU mode is the default on purpose.** GPU mode measured **0.289 vs 0.26 tok/s** — an 11%
gain that costs **13–18 GB of VRAM**. LM Studio runs 50+ tok/s on that same VRAM, so
giving the GPU to GLM is a bad trade. Only use the GPU script when LM Studio is unloaded
*and* you specifically want GLM marginally faster.

**Check it is up** (instant, does not load anything):
```powershell
Invoke-RestMethod "http://127.0.0.1:8080/v1/models"
```

---

## 3. HOW TO CALL IT

OpenAI-compatible. **Endpoint `http://127.0.0.1:8080/v1`, model id `glm-5.2-colibri`.**

### From the PI CLI
```powershell
pi --provider colibri --model glm-5.2-colibri -p "<your question>" -nt --no-session
```

### From Python
```python
import requests
r = requests.post("http://127.0.0.1:8080/v1/chat/completions",
    json={"model": "glm-5.2-colibri",
          "messages": [{"role": "user", "content": "..."}],
          "max_tokens": 120},          # KEEP THIS SMALL - it is ~4 s per token
    timeout=1800)                      # 30 min. Do NOT use a short timeout.
print(r.json()["choices"][0]["message"]["content"])
```

### From PowerShell
```powershell
$b = @{ model="glm-5.2-colibri"; messages=@(@{role="user";content="..."}); max_tokens=120 } | ConvertTo-Json -Depth 5
Invoke-RestMethod "http://127.0.0.1:8080/v1/chat/completions" -Method Post -Body $b -ContentType "application/json" -TimeoutSec 1800
```

> **This is NOT `core.lm_gateway`.** The gateway arbitrates the *LM Studio* endpoint and
> adopts whatever model is resident there. GLM-5.2 is a separate server on :8080 that
> must be started explicitly. Do not route gateway traffic at it — a 0.26 tok/s model
> behind a FIFO queue will stall every other agent waiting in line.

---

## 4. WHEN TO USE IT (and when not to)

**USE IT FOR:**
- A second opinion on a decision you have already reasoned through, where being wrong is
  expensive and thirty minutes is cheap.
- Dense reasoning over a *small* amount of context — the prompt is expensive, the thinking is free.
- Anything you would otherwise escalate to a frontier model but cannot, offline.

**DO NOT USE IT FOR:**
- Anything on a loop, a gate, a nightly job, or a per-file pass. It will not finish.
- Bulk text work (summarise 50 files) — that is hours.
- Anything a fast local model can do. Try LM Studio (:1234) first, escalate only if it fails.
- Structured/schema output you plan to retry on mismatch — each retry is another 10+ minutes.

**H-3 STILL APPLIES.** A response containing its own reasoning dump is a retry, not a
verdict — but here a retry costs 10+ minutes, so schema-validate the *first* answer and
prefer a shorter, better-specified prompt over a second attempt.

**AN LLM IS NEVER A WHY-CHAIN TERMINAL** (`core/why.py`). GLM-5.2's answer is another
claim, not evidence. Being big and slow does not make it PHYSICS or THE HUMAN.

---

## 5. TROUBLESHOOTING — the three faults found 2026-07-23

### `Stream ended without finish_reason`
**The server's queue timeout fired while the engine was still working.** The default is
**300 s**, which is shorter than GLM-5.2's own prefill — so it kills itself, returns 429,
and every streaming client reports this message. Proven: the engine was at layer 25/78
*after* the 429 was sent.

`--queue-timeout 3600` is in both START scripts and is **load-bearing — do not remove it.**
If you see this error, also check the *client* timeout (§3: use ≥1800 s).

### `500 {"code":"engine_error"}` instantly (~0.1 s)
**More than one `coli serve` instance is running.** Only one can own :8080, but the others
stay alive; requests landing on a frontend that does not own the engine throw, and
`openai_server.py:1036` relabels *any* exception as this generic message.

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {$_.CommandLine -match 'coli'}
```
Expect **exactly one**. Kill the extras, or run `STOP GLM-5.2.cmd` and start once.

### It is running but produces nothing for many minutes
That is normal — see §1. Confirm it is alive rather than hung by watching the engine log
for `[prefill] layer N/78` advancing:
```powershell
Get-Content "E:\colibri\run.err.log" -Tail 5
```

---

## 6. CONFIGURATION — every value measured, not guessed (2026-07-23)

```
COLI_MODEL=E:\glm52_i4              # primary copy (357 GB)
COLI_MODEL_MIRROR=D:\glm52_i4       # second copy; both drives serve expert reads
COLI_DISK_WEIGHTS=1047,515          # primary,mirror bandwidth ratio - DO NOT REMOVE
PIN_GB=all                          # keep the whole expert set resident
--ctx 128000 --queue-timeout 3600 --gpu none
```

**Why `COLI_DISK_WEIGHTS` is explicit:** colibrì's startup probe reads the mirror through
the OS page cache and reported **5.53 GB/s from a SATA SSD whose interface caps at ~550
MB/s**, then handed it 80% of the reads. That mis-split measured **7.50 s/layer**; the
corrected 67/33 measured **4.50**. A 40% swing from one wrong number.

**Why `--ctx 128000`:** context competes with the expert cache for RAM.

| ctx | experts pinned | decode |
|---:|---:|---:|
| 32,768 | 621 | 0.289 tok/s |
| **128,000** | **621** | — |
| 262,144 | 387 | 0.168 tok/s |

At 262,144 the KV reservation evicts a third of the experts and decode drops **42%**.
128,000 keeps the full 621-expert hot set — it is the knee of the curve.

**Tuning that helped prefill but NOT decode** (kept in the GPU script only): expert tier
8→13 GB (7.50→5.63 s/layer), `COLI_CUDA_PIPE=2` (5.63→4.77), mirror (4.77→4.50).
Prefill improved ~10× overall; **decode moved 0.26→0.289.** Decode is what you wait on.

**Known unexplored lever:** `[MTP] disabled in multiplexed serve` prints on every start.
MTP is multi-token speculation and it is *enabled* in single-client `coli chat` but off in
the server. If decode speed ever becomes critical, that is the thread to pull.

---

## 7. THE OTHER LOCAL MODELS

| Model | Endpoint | Speed | Use for |
|---|---|---|---|
| **LM Studio** (whatever is resident) | `:1234` | 50+ tok/s | everything by default; `core.lm_gateway` adopts it |
| **GLM-5.2** (this doc) | `:8080` | 0.26 tok/s | a considered second opinion, when you can wait |

`core/council.py` runs FAST vs DEEP as two LM Studio models. GLM-5.2 is a *third*, slower
tier that must be invoked deliberately — it is not wired into the council, and should not
be, at this speed.
