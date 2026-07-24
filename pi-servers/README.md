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

## DS4 (DeepSeek-V4 CPU brain) — superseded

`START DS4.cmd` / `STOP DS4.cmd` remain for reference only. **Superseded 2026-07-19** by the
model-swapping Council (`core/council.py`). If the STOP script uses `coli stop` or reads
`/proc`, it has the same Windows bug the GLM stop script did — verify before trusting it.

## The lesson worth keeping

A local model server must **bind `127.0.0.1`**, must **actually stop when told** (a stop
script that prints success without verifying is worse than none — the GLM one burned 11.9
CPU-hours that way), and must be **something you can audit**. A model you cannot inspect,
running slower than it is worth, is a liability however capable it is.
