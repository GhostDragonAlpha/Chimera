# THE DYAD EYE — which model, which quant, and what actually costs the time

> **RULE 0 — every membrane is a theory.** This is a *decision* membrane about the
> instrument's own configuration. Every number below was measured on this box, not
> cited from a leaderboard; where evidence is thin it says so.

## STATEMENT

The eye's wall-clock is dominated by **how long an answer we ask for**, not by the
image resolution, the quant, or the model's size. A dyad that asks bounded
questions sweeps many frames at ~18s each; one that asks for open-ended reports
pays ~70s for the same picture.

## PREDICTION (not yet measured)

Tiering the ask — a cheap one-sentence triage sweep across all poses, then a deep
read only on the frames triage flags — will cut a full pose sweep to roughly a
quarter of its current cost **while finding the same defects**, because the
defects worth chasing are named in the one-sentence answers too.

## FALSIFIER

If a one-sentence triage sweep over N poses fails to name a defect that the
full-report pass on the same frames names, triage is not a cheaper instrument, it
is a blinder one — and the tiering is dropped rather than tuned.

---

## THE MEASUREMENTS (all on this box: RTX 4090 24 GB, LM Studio, native 2K frames)

### Context is the biggest single lever — proven

| loaded context | one 2560×1440 read |
|---|---|
| 130,048 | **483 s** |
| ~16,000 | **56 s** |

8.7× from right-sizing alone. The context is fixed when LM Studio **loads** a
model; a request cannot change it, and pushing `num_ctx` at the server can trigger
a reload (the eviction war `core/lm_gateway` exists to prevent). **The operator
sets it; the instrument records what the server reports and never overrides it.**
Current standard: 16,000 (operator: "I can fit all that on GPU").

### Decode dominates, not prefill — proven

Same 2K image, same model, two asks:

| ask | time | chars |
|---|---|---|
| "one sentence, name the single worst defect" | **18.4 s** | 146 |
| the full body-defect prompt | **70.5 s** | 1,893 |

Time tracks the ANSWER, not the picture. The 18.4 s figure is essentially the
prefill floor for a full 2K frame.

### Resolution barely matters, and geometry survives downscaling — proven

| frame | time | defects found |
|---|---|---|
| 2560×1440 (3,600 img tokens) | 76.8 s | 6/6 |
| 1536×864 | 69.2 s | 6/6 |
| 1280×704 (~880 img tokens) | 63.0 s | 6/6 |

Halving the pixels bought 14 s. Shortening the ask bought 52 s.

### OCR is correct even downscaled — proven against ground truth

The HTTP twin serves the SAME strings the glass draws, so this has a known answer.
Asked to quote the status bar verbatim, the eye returned, correctly, at **both**
2560 and 1280:

```
B7 ARTICULATE    36 fps  24.60 ms    NVIDIA GeForce RTX 4090   2560x1440
EARLIEST NON-GREEN GATE: B7 articulate -- the next stage [next]
```

(Caveat: text in this UI is ~12 px advance at 2K, so ~6 px at 1280. It read it.
Do not generalise this to genuinely tiny text without re-measuring.)

---

## THE QUANT QUESTION — the answer is: stop worrying about it

`dirk-qwen3.8-27b` is a **native** VLM (`Qwen3_5ForConditionalGeneration`). Its
`Q4_K_XL` quantises the **language model only**; the vision tower ships separately
as `mmproj` and Qwen provides it at **F16 (1,105 MB) or Q8_0 (717 MB)** — nothing
lower. llama.cpp's own guidance: *"Multimodal components are usually kept in a
high-quality format such as bf16 or q8. The impact on speed and memory from using
a smaller quant is negligible, but overall quality could be impacted."*

So the vision path is already running at ~F16. Chasing a lower `mmproj` would save
under a gigabyte and put the OCR at risk for no measured gain.

| target | verdict |
|---|---|
| LLM Q6_K / Q5_K_M / Q4_K_M / Q4_K_XL | safe; Q4_K_XL is the community default |
| LLM IQ4_XS / Q3_K_XL | avoid for fine visual detail |
| mmproj F16 / Q8_0 | correct choice; keep it |
| mmproj ≤ Q5 | not recommended, no upside |

## THE MODEL QUESTION

**Keep `dirk-qwen3.8-27b` as the daily driver.** It is 18.49 GB, so it *fits* the
4090 — 100% of weights in HBM, no PCIe streaming.

**Do not use the 101 GB MoE for this.** `qwen3.8-flash-next` is 101.20 GB on a
24 GB card, so ~77 GB of experts live in system RAM and every prefill token must
stream them over PCIe. That is the measured ~2× penalty (105–130 s vs 56–90 s).
It *is* more verbose and it read HUD text the 27B ignored — a real capability —
but for a single-image latency job on one 4090 the offload costs more than it
buys.

Alternatives worth trialling if more speed is wanted (all fit 24 GB whole;
**latencies are estimates, not measured**):

| model + quant | size | note |
|---|---|---|
| Gemma-4-12B-it Q6_K + mmproj-Q8_0 | ~9.8 GB | exposes an explicit visual token budget {70…1120}; Google: use higher budgets for small text |
| Gemma-4-26B-A4B UD-Q5_K_M | ~20.9 GB | MoE but 3.8B active and fits; best quality-per-latency candidate |
| Qwen3-VL-8B-Instruct Q6_K | ~7.5 GB | strongest sub-10B VLM; would let us sweep a lot of frames |

**No benchmark exists for "find torn triangles in a 3D render."** RealWorldQA,
MMMU-Pro and OCRBench are proxies. Model choice here is a hypothesis to measure,
not a fact — which is exactly why the falsifier above is written down.

## ONE FINDING THAT WAS ALMOST LOST

A truncated report is a **lost** report. At `max_tokens` 1400 the verbose eye had
5 of 6 reads cut off mid-word and 2 come back empty. `finish_reason` is now
captured and recorded per read, and `dyad_scan` flags truncation instead of filing
a sentence that stops mid-phrase. The budget is 2600. Counter-intuitively the
smaller cap was *not* faster — it made the eye generate to the cap and then cut.

## OPERATIONAL NOTES

- The eye is named and hard-coded (`CHIMERA_SENSES_MODEL`). `lm_gateway` **adopts
  the resident model** and rewrites every request at it, so naming a model does
  not *select* one — which is why `can_see()` reads back which model actually
  served and warns when it differs from the decree.
- `senses.can_see()` sends an 8×8 PNG to test image acceptance before a scan
  builds anything. A text-only model (`type: llm`) refuses images outright;
  without this a run fails after minutes instead of in a second.
- The glass needs a **presented** image: a minimized window makes `/glass` refuse
  loudly rather than return a stale frame.
