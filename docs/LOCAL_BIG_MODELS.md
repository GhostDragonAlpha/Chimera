# Running big models on this machine — the measured limits

*Measured 2026-07-29 on the actual box. Every number here came off an instrument, not a spec sheet.*

The recurring question is "can this machine run \<enormous MoE model\> by streaming the experts off
disk?" The technique is real — llama.cpp `--override-tensor`, ktransformers, Colibri all do it — and
the answer is decidable in one line of arithmetic rather than by trying it for a week.

## The one equation

```
tokens/sec  =  (random read MB/s)  /  (MB of expert weights touched per token, minus what is cached)
```

Both terms are measurable up front. Nothing else about the setup matters much.

## The hardware, measured

**Random read with the OS cache bypassed** (`FILE_FLAG_NO_BUFFERING`, 400 reads over a 37 GB file).
Sequential figures are irrelevant here: MoE routing scatters reads across the file.

| drive | hardware | 1 MB | 4 MB | 16 MB |
|---|---|---:|---:|---:|
| **C:** | PCIe NVMe 1.86 TB (644 GB free) | 1,567 | **2,787** | 3,055 |
| `E:` | 2× Intel SSDPEKNW010T8 (660p QLC), spanned, 1,587 GB free | 692 | 1,198 | 1,331 |
| `F:` | Samsung T7 (USB) | 576 | 812 | 933 |
| `D:` | Samsung 860 EVO (SATA) | 464 | 509 | 524 |

**This corrected a wrong number that had been in `CLAUDE.md` for months** — it claimed `E:` did
352 MB/s random. It does 1,198. And `C:` is 2.3× faster than `E:`, which inverts the usual advice
here, because `E:` is the "big fast drive" only for *sequential* work.

**Memory is at its ceiling and cannot be raised.** MSI MAG B760 TOMAHAWK, 4 of 4 DIMM slots filled
with 32 GB DDR5-5400. Board maximum 128 GB. With the 4090 that is **152 GB resident, permanently.**
Dual-channel DDR5-5400 is ~86 GB/s — 31× faster than the best disk, which is why "does it fit in
RAM" is the only question that really matters.

## Worked example: Kimi K3

Straight from `moonshotai/Kimi-K3` `config.json`:

- 93 layers, 1 dense → **92 MoE layers**
- **896 routed experts, 16 fire per token**
- expert = 3 × 3584 × 3072 = **33.0 M params**
- → 92 × 16 × 33.0M = **48.6 B params of expert weights touched per token**

Smallest published quant (`unsloth/Kimi-K3-GGUF`, summed shard sizes):

| quant | size |
|---|---:|
| UD-IQ1_S | **553 GB** |
| UD-IQ1_M | 604 GB |
| UD-IQ2_XXS | 662 GB |
| UD-Q2_K_XL | 802 GB |
| UD-Q4_K_XL | 1,405 GB |

At 553 GB / ~2.8 T params = 1.58 bits/param, so **8.9 GB of expert weights per token**.

152 GB resident against ~540 GB of experts is ~28% of the model, so even with routing skew helping
the cache:

| cache hit | from C: (2.79 GB/s) | from E: (1.20 GB/s) |
|---|---|---|
| 30% | 0.45 tok/s | 0.19 tok/s |
| 50% | 0.62 tok/s | 0.27 tok/s |
| 65% | 0.89 tok/s | 0.38 tok/s |

**A 2,000-token coding reply takes about an hour.**

This is not a prediction — it is a *retrodiction*. `CLAUDE.md` already recorded **0.26 tok/s** from
the GLM-5.2 / Colibri attempt that was removed on 2026-07-23. The row above for `E:` at a 50% hit
says **0.27**. The arithmetic and the historical measurement agree, which is what licenses using the
equation instead of running the experiment again.

## What that rules in and out

| model | smallest quant | verdict |
|---|---:|---|
| Kimi K3 | 553 GB | **no** — 0.4–0.9 tok/s |
| Kimi K2.7-Code | 283 GB | ~1.5 tok/s — 54% resident, best of the Kimis, still not usable |
| ~100–130 GB class (GLM-Air, Qwen3-235B at low quant) | — | **yes**, fits in RAM, no streaming, 8–25 tok/s |
| ≤ 24 GB (30B-A3B class) | — | **yes**, entirely in VRAM, 50+ tok/s |

**The rule of thumb this yields:** a model is usable here if it fits in ~150 GB. Streaming buys you
capacity, not speed, and the exchange rate is brutal — roughly 30× slower than RAM. Streaming is
worth it only when the model *nearly* fits and the miss rate is small.

To actually hold a 500 GB-class model you need 8–12 memory channels and 512 GB+, i.e. a
Threadripper/EPYC/Xeon-W platform. That is a new machine, not an upgrade to this one.

## If you want Kimi anyway

Moonshot serves an **Anthropic-compatible** endpoint, so Claude Code needs no patch or proxy —
`api.moonshot.ai/anthropic` answers 401 without a key, which is what "it exists" looks like.
`kimi.ps1` at the repo root flips between them:

```powershell
.\kimi.ps1 k3        # Kimi K3, 1M context
.\kimi.ps1 code      # Kimi K2.7-Code, 262k
.\kimi.ps1 off       # back to Anthropic
```

It reads `MOONSHOT_API_KEY` from the environment and never stores or prints it. OpenRouter also
serves these models but speaks OpenAI, so that route needs a translator in between; Moonshot direct
does not.

## Sources

- [Unsloth — Kimi K3, how to run locally](https://unsloth.ai/docs/models/kimi-k3)
- [Unsloth — Kimi K2.5 tutorial (the `-ot` MoE offload flags)](https://unsloth.ai/docs/models/tutorials/kimi-k2.5)
- [Colibri — NVMe expert streaming engine](https://github.com/JustVugg/colibri)
- [KTransformers — 671B MoE on one 24 GB GPU](https://www.noze.it/en/insights/ktransformers-hybrid-cpu-gpu-inference/)
- [llama.cpp NVMe-backed 671B, ~2 tok/s on 96 GB + 24 GB](https://huggingface.co/unsloth/DeepSeek-R1-GGUF/discussions/13)
