# P04 — correction note: superseded by P05

Appended to the P04 evidence set AFTER its publication (the P04 package and
manifest are preserved untouched so the P04 manifest remains valid). This note
records which P04 predictions the P05 implementation supersedes.

**Context:** P04 published a platform-boundary spec. Before any P05 execution,
the assignment corrected several overclaims in that spec. The corrections are
now backed by P05's implemented seam + evidence, not just by instruction.

## Superseded predictions (each with the replacement fact)

1. **"The surface check is the engine's only Linux blocker."** — Not
   established. The Windows-coupled regions beyond the surface are real and
   were deliberately left untouched by P05: Win32 window class registration,
   `g_hwnd` creation and the message loop in `main.cpp`, plus WSI feature
   queries. The seam proves the surface boundary can be extracted; it does not
   make a Linux engine exist. A Linux engine remains blocked by the window/
   input layer.
2. **"S1 authorizes headless init, skipped presentation, or an offscreen
   runtime."** — It does not, and none exist. `plat::kUnavailable` causes
   `Engine::init` to hard-fail with an explicit "no headless engine path"
   message. The unavailable backend is a harness artifact only.
3. **"A portable seam harness is a compiled Linux engine."** — It is not. The
   P05 probe (`tools/platform_surface_probe`) is a standalone boundary probe
   that runs BOTH backends against the real loader on the Windows host. A
   Linux-native engine build was recorded NOT TESTED (this WSL has no Vulkan
   headers).
4. **"The unchanged PNG encoder proves unchanged rendered pixels."** — It does
   not. `tools/platform_probe/check.py` (PASS 9/9) validates byte transport
   only. Rendered-pixel parity is unmeasured: runtime is NOT TESTED.
5. **(implicit) hash parity as a build-parity signal.** — Baseline and
   candidate executable hashes differ by construction. The correct parity
   signals are: byte-identical shader inputs AND outputs (23/23 `.spv`,
   verified), harness behavior on the real loader (27/27 checks), and
   untouched-code proof via diff (teardown etc.). Exe hashes are recorded as
   facts, never as equality claims:
   - baseline  `9B7C547D...93A37C` (688 640 B)
   - candidate `D74A0672...BFAB24` (691 200 B)

## Does P04 fail a gate because of this?

The P04 package remains valid as a historical boundary SPEC. Its manifest is
intact and self-consistent. This note is the standard correction channel: the
spec's overclaims are retired point-by-point above; P05 carries the measured
replacement. Nothing in P04's evidence (ladder run, regression-gate frames,
gait-capture merit) is affected by the surface-extraction findings.

Author: P05 (A line). Verified-by: the P05 harness, build matrix, and diff
records in `docs/evidence/p05/`.