# Chimera — Project Manual

> **THE GOAL: a space game.**
> Funded and fed by a pipeline that turns real 3D scans and authored assets into
> **labeled, isolated, re-composable object genomes** — shape + material, with serial
> numbers — so one person can build at a scale that normally needs a studio.

> **The Unreal Engine 5 generation pipeline is RETIRED (2026-07-23).** It is archived at
> `archive/unreal-era/`, not deleted. Do not start the editor, do not run the old
> preflight/task-board/gauntlet workflow, and do not treat anything in that folder as
> current. If a doc there contradicts this file, this file wins.

---

## NEW AGENT? START HERE

1. Read this file, then **`Construction/SPLAT_DNA_WORKFLOW.md`** — the live pipeline,
   with honest `PROVEN` / `DESIGNED` / `FRONTIER` status marked on every stage.
2. Read **`docs/EXPERIMENTAL_METHOD.md`** before diagnosing anything. It is ten rules
   for finding out what is true about a running system, each attached to the specific
   mistake that produced it.
3. **The GPU is mandatory.** Never run rendering, segmentation, or DNA recovery on CPU.
   An RTX 4090 is present; use it (`torch`, `cuda`).
4. Work in small measured steps. **Record negative results** — an unrecorded failure
   gets re-run by the next agent at full cost.

---

## THE PIPELINE (Construction/)

**An object = morphology-DNA (shape) + material-DNA (substance).**
Material-DNA lives in the *splat configuration* — joint distributions of size, shape,
angle, colour and opacity — **not in averages**, and it is a **range**, not a value.
Recognised genomes get **serial numbers** (a codebook): compress, identify, regenerate.

| Stage | Code | Status |
|---|---|---|
| Decode `.ksplat` / `.splat` / `.ply` | `Construction/ksplat_io.py` | PROVEN |
| GPU rasterisation (no gsplat needed) | `Construction/gpu_render_torch.py` | PROVEN — 9 views, 120 ms |
| SAM 2 segment + multi-view lift | `Construction/multiview_sam_lift.py` | PROVEN |
| Morphology signatures | `Construction/morphology_signatures.py` | PROVEN — 6/6 synthetic |
| Material recovery (inverse rendering) | `Construction/material_dna.py` | PROVEN on known oak/copper |
| Splat-config DNA + identify | `Construction/take_dna_full.py` | PROVEN — 82.5% vs 33% chance |
| Serial-number codebook | `Construction/codebook.py` | PROVEN — 8 genomes |
| Hull material library | `Construction/space_materials.py` | PROVEN — 10 surface genomes |
| Format calibration regression | `Construction/calibrate_formats.py` | PROVEN — caught a real bug |
| Grain/orientation features | — | **DESIGNED — the next real lever** |
| Emissive genome (lasers, engine glow) | — | DESIGNED |
| Mesh for an engine / re-composition | — | DESIGNED |
| Relighting, unseen geometry | — | FRONTIER |

**Full detail, including the four facts a successor must not re-derive** (two intake
methods, format calibration, the emissive genome, and why spatial voting is refuted):
`Construction/SPLAT_DNA_WORKFLOW.md`.

**Photo → textured 3D tree** is a sibling pipeline with its own recipe:
`Construction/REFERENCE_TO_NOUN.md` (run it, don't improvise) and
`Construction/MORPHOLOGY.md` (the cited concept catalog).

---

## KEY PATHS

| Path | Purpose |
|---|---|
| `Construction/` | **The DNA pipeline** — all current extraction work |
| `Construction/SPLAT_DNA_WORKFLOW.md` | The canonical workflow, status-marked per stage |
| `WorldModel/clay.py` | Procedural ship hulls — `SHIP_PARAMS`, 24 parameters |
| `WorldModel/splat_io.py` | `.ply` splat I/O (SH-DC colour decode — see calibration) |
| `WorldModel/training_data/downloads/` | **The corpus, ~35 GB, gitignored** |
| `docs/GLM_52_DEEP_MODEL.md` | The local 744B deep model — **read its speed section first** |
| `docs/EXPERIMENTAL_METHOD.md` | How to diagnose a live system without fooling yourself |
| `pi-servers/` | Local LM server launchers (backup copies; live ones at `E:\pi-servers\`) |
| `web/view.html` | Interactive 3D orbit viewer — output the operator can actually see |
| `archive/unreal-era/` | **The retired UE5 project's docs. Historical only.** |

---

## THE CORPUS (~35 GB, license-clean, gitignored)

28 splat scans + 39 INRIA trained models (13 scenes) + 489 CC objects across 20
space-game categories + 4D emissive FX captures + **611 camera poses**
(bonsai 292, bicycle 194, stump 125).

**bicycle is the first real multi-view material-recovery target** — it has 194 posed
cameras *and* metal surfaces.

**Gating lesson:** nearly every large splat corpus on HuggingFace is `gated: auto` —
instant approval but requires a signed-in account, and there is no ungated mirror.
**Objaverse and INRIA are the exceptions and carry the most value per byte.**

---

## LOCAL MODELS

| Model | Endpoint | Speed | Use for |
|---|---|---|---|
| **LM Studio** (whatever is resident) | `:1234` | 50+ tok/s | everything by default |
| **GLM-5.2** (744B, colibrì) | `:8080` | **0.26 tok/s** | a considered second opinion, when you can wait |

**Never pin a model id.** `core/lm_gateway.py` adopts whatever LM Studio currently has
resident; change the model by loading a different one in LM Studio. If nothing is loaded
it raises `NoModelLoaded` — it does **not** fall back and JIT-load, because two clients
each forcing a different model evict each other mid-load and both die.

**GLM-5.2 is a deliberate escalation, not a default.** At 0.26 tok/s a 500-token answer
takes half an hour and a full agent turn can take longer. Cap `max_tokens`, keep prompts
short, use a client timeout ≥1800 s, and never put it on a loop, gate, or per-file pass.
Start it with `E:\pi-servers\START GLM-5.2.cmd` (CPU mode, 0 VRAM, so LM Studio keeps the
GPU). Full manual and all three known failure modes: `docs/GLM_52_DEEP_MODEL.md`.

---

## HARDWARE AND ITS TRAPS

- **RTX 4090, 24.5 GB VRAM.** GPU is mandatory for render/segment/recover.
- **128 GB RAM.**
- **Drives:** `C:` PCIe NVMe (OS + pagefile) · `D:` SATA SSD · `E:` spanned QLC NVMe pair
  (models, corpus) · `F:` USB SSD.

**Measured traps, do not re-derive:**
- **`E:` is fast sequential (4,782 MB/s) and slow random (352 MB/s at 4 MB).** MoE model
  reads are random. Sequential benchmarks mislead here.
- **Never put a memory-mapped model on `C:`** — it competes with `pagefile.sys` and the
  drive degrades past ~80% full. Measured 50% slower in place than a "5.3× faster" benchmark predicted.
- **System Restore was entitled to 15% of `C:` (279 GB)** and silently consumed ~190 GB
  during large file operations, failing two transfers. Cap it:
  `vssadmin resize shadowstorage /for=C: /on=C: /maxsize=25GB` (admin).

---

## CONVENTIONS

- **Git: commit directly to `master`, never open feature branches.** State the exact
  branch and commit SHA on every push. All git/GitHub management is delegated — keep the
  tree clean and push without asking each time; surface only destructive actions.
- **Large artifacts stay gitignored** — model weights, the corpus, `web/*.npz`,
  `web/object.json`. A 154 MB file once blocked six commits.
- **Show the operator real output.** Renders they cannot see do not count. Use
  `web/view.html` and the preview server, not files in a temp directory.
- **Opinions must be science-grounded.** A judgement is only trusted when a physical
  constraint forces it. Render the evidence, look at it, name the physics.
- **Record what failed, with the number.** `docs/EXPERIMENTAL_METHOD.md` §7.

---

## SESSION MEMORY

`C:\Users\allen\.claude\projects\E--PythonChimera\memory\`, indexed in `MEMORY.md` there.
