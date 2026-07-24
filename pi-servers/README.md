# pi-servers — local LM server launchers (version-controlled copies)

> **These are BACKUP COPIES. The live scripts run from `E:\pi-servers\`.**

## GLM-5.2 / colibrì — REMOVED 2026-07-23

The GLM-5.2 launchers were deleted at the operator's call. The model was a **744 GB local
liability** (357 GB × 2 mirrors on E: and D:), ran at **~0.26 tok/s** (one agent turn was
tens of minutes), was opaque and unauditable, and spin-waited a CPU core when idle without
anyone noticing. **Do not reinstate it.**

Everything it was for is covered without it:

- **Fast local inference** — LM Studio on `:1234` (50+ tok/s), arbitrated by
  `core/lm_gateway.py`, which adopts whatever model is resident.
- **A fast/deep split** (what GLM's size was meant to provide) — `core/council.py` swaps
  between two LM Studio models on demand. No second engine, no 744 GB, no 0.26 tok/s.

## DS4 (DeepSeek-V4 CPU brain) — REMOVED 2026-07-24

Deleted with its launchers, its stub (`core/ds4_brain.py`), and its memory. It was the same
kind of dead end as GLM-5.2: a separate slow local model server (~1.6 tok/s CPU, 80 GB RAM)
that the model-swapping Council made pointless. **The "deep brain" concept is LM Studio now**
— `core/council.py` swaps a fast MoE and a deep dense model on demand through `lm_gateway`.
There is no separate deep-model server, and there does not need to be.

## The lesson worth keeping

A local model server must **bind `127.0.0.1`**, must **actually stop when told** (a stop
script that prints success without verifying is worse than none — the GLM one burned 11.9
CPU-hours that way), and must be **something you can audit**. A model you cannot inspect,
running slower than it is worth, is a liability however capable it is.
