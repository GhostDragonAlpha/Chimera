# pi-servers — local LM server launchers (version-controlled copies)

> **These are BACKUP COPIES. The live scripts run from `E:\pi-servers\`.**
> Edit the live ones, then re-copy here. Running them from the repo works, but the
> doc, the shortcuts and the operator's muscle memory all point at `E:\pi-servers\`.

Full operating manual for GLM-5.2: **`Chimera/docs/GLM_52_DEEP_MODEL.md`** — read its
speed section before calling the model.

| Script | Purpose |
|---|---|
| `START GLM-5.2.cmd` | **The default.** GLM-5.2 on **CPU** (`--gpu none`), 0 VRAM, so LM Studio keeps the GPU. `--ctx 128000 --queue-timeout 3600`, mirror on D:. |
| `START GLM-5.2 (GPU).cmd` | Alternate. GPU mode (`CUDA_EXPERT_GB=13`, `COLI_CUDA_PIPE=2`, `--vram 13`). **Only when LM Studio is unloaded** — it takes 13–18 GB of VRAM for an 11% decode gain. |
| `START GLM-5.2 (CPU).cmd` | **Redundant** — kept only so an old shortcut doesn't break. Identical intent to the default script above, which is already CPU mode. Prefer the default. |
| `STOP GLM-5.2.cmd` | `coli stop --port 8080` — the correct shutdown, releases the engine too. |
| `START DS4.cmd` / `STOP DS4.cmd` | DeepSeek-V4 CPU brain. **Superseded 2026-07-19** by model-swapping through `core/council.py` (see CLAUDE.md); kept for reference. |

## The two settings that are load-bearing

**`--queue-timeout 3600`** — the colibrì default is **300 s**, which is *shorter than
GLM-5.2's own prefill*. The server kills its own in-flight request and returns 429, and
every streaming client reports it as **`Stream ended without finish_reason`**. Proven
2026-07-23: the engine was still working at layer 25/78 *after* the 429 was sent.
**Never remove this flag.**

**`COLI_DISK_WEIGHTS=1047,515`** — colibrì's startup probe reads the D: mirror through the
OS page cache and reported **5.53 GB/s from a SATA SSD whose interface caps at ~550 MB/s**,
then routed 80% of expert reads to it. That mis-split measured **7.50 s/layer**; the
corrected 67/33 split measured **4.50**. Without this line the probe re-runs and gets it
wrong again.

## Run exactly one

More than one `coli serve` on :8080 produces an instant `500 {"code":"engine_error"}` —
only one instance owns the port, but the others stay alive and throw. `openai_server.py`
catches *every* exception and relabels it with that one generic message, so the error text
tells you nothing. Check with:

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {$_.CommandLine -match 'coli'}
```

Expect one. `STOP GLM-5.2.cmd` before starting if unsure.
