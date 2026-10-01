# H15 GALLERY BASELINE — the aliveness law on the PRE-GUARD binary

Agent H15 "gallery-regression", 2026-09-14, branch `astra/tasks/matter-kernel-format-01`.
Scratch throwaway engines on **127.0.0.1:8140 only**, one fresh engine per creature,
killed after each (verified: no listener on 8140 after the run). The live stack
(8107/8206/8210) was never connected to, read, or written. (It restarted itself
mid-audit — 8107 PID 3176→50144 — its own watchdog lifecycle, not ours.)

## RULE 0 — the membrane under test

- **STATEMENT**: the five-shape gallery (blob, torus, capsule, peanut, rounded box)
  is ALIVE on the current binary — import → classify → bind → seal in one flow,
  cells conserving, a 10 kN touch answering with the force-determined dimple, a
  pose moving the skin, one framed portrait per creature.
- **PREDICTION** (before this run): the current binary re-proves G4's round-2
  verdict 5/5 — cells=2 per seal, |conserve_pct| <= 0.001, dimple 0.198944 m on
  every shape, torus seal path loops=2, and (new this round) every shape answers
  a pose with nonzero vertex displacement.
- **FALSIFIER** (named before the run): any import refusal; any seal leaving
  n_cells != 2 or |conserve_pct| > 0.001; any 10 kN press with zero dP AND zero
  dimple; torus seal reporting loops != 2; any pose accepted with zero
  displacement; any missing portrait.

**VERDICT: 5/5 ALIVE — the baseline holds.** Two consecutive runs of the final
driver agree bit-for-bit on every measured channel (only the A1 conservation
read's 6th decimal wiggles; see findings).

## Provenance (the BEFORE artifact)

- Binary: `.tmp/build_tick/Release/chimera_engine.exe`
  sha256 `3854de552013e8612ff46fbd3898a151dc114b15c59d27c09028c676a3f54b03`,
  1,592,832 bytes, mtime 2026-09-14 00:47:26 -0500.
- Built from the HEAD-committed engine source: ZERO commits touch
  `ChimeraEngine/engine/` between the build era (d8656858, 00:45) and the HEAD
  at run time (569083bb, re-checked after the lead's 62f60378 landed mid-audit
  — still zero engine commits). The degenerate-split guard is in NEITHER the
  binary NOR the tree: `git status` shows engine.cpp/engine.hpp/main.cpp dirty
  with someone else's in-progress work (392+/158-), containing no
  degenerate/split guard code (grepped). **This binary is the true BEFORE.**
- Driver: `h15_gallery.py` (this dir), adapted from G4's
  `tools/gallery/run_gallery.py` (commit 39341be2) — same meshes
  (`tools/gallery/obj/*.obj`, verified watertight before posting by generate.py),
  same endpoint sequence, same 10 kN bar, same mid-height seal.
- Isolation: per-creature private cwd under `.h15_scratch/` (untracked) with a
  shaders copy, `--hidden` ONLY (see findings for why not `--no-restore`),
  `taskkill /F /T` in a `finally`. Engine logs of the official run preserved in
  `engine_logs/`.
- Meshes (import response): blob 1,986v/3,968t V=8.333816 · torus 2,048v/4,096t
  V=7.342924 · capsule 1,346v/2,688t V=1.691744 · peanut 1,986v/3,968t
  V=0.906166 · rbox 1,986v/3,968t V=8.473496. All admitted first try, zero
  winding flips, zero refusals — same as G4.

## THE BASELINE TABLE (official run 2026-09-14 08:24, gallery_results.json)

| creature | cells | loops | cuts | caps | V_whole | V_cells (lower/upper) | conserve % (A1) | pose joint → max skin displacement (A2) | conserve % posed/rest (A2) | 10 kN dP upper, Pa (A3) | dimple m | verdict |
|----------|------:|------:|-----:|-----:|--------:|----------------------:|----------------:|---------------:|---------------------------:|------------:|--------:|---------|
| blob     | 2 | 1 | 128 | 126 | 8.33391 | 4.16691 / 4.16688 | +0.000000 | j1 → 0.1562 m | −0.0014 / −0.0014 | +13,136,100 | 0.198944 | **ALIVE** |
| **torus**| 2 | **2** | 128 | 124 | 7.34284 | 3.67145 / 3.67145 | +0.000000 (wiggle ≤ +0.000877) | j2 → 0.0958 m | +0.0003 / +0.0009 | +2,249,130 | 0.198944 | **ALIVE** |
| capsule  | 2 | 1 | 96 | 94 | 1.69175 | 0.84587 / 0.84587 | +0.000000 | j0 → 0.1031 m | −0.0003 / −0.0003 | +2,371,300 | 0.198944 | **ALIVE** |
| peanut   | 2 | 1 | 128 | 126 | 0.90617 | 0.45309 / 0.45308 | −0.000007 | j1 → 0.0860 m | +0.0001 / −0.0000 | +30,212,600 | 0.198944 | **ALIVE** |
| rbox     | 2 | 1 | 128 | 126 | 8.47347 | 4.23674 / 4.23676 | +0.000439 | j0 → 0.1632 m | +0.0004 / +0.0004 | +36,092,500 | 0.198944 | **ALIVE** |

Every bar, every creature:
- **A1 seal + conservation**: cells=2, |conserve_pct| <= 0.00088 (band 0.001;
  ship bar "0.000%" to printed precision). Pressures relax after
  `/tick_touch_clear` (e.g. peanut 3.02e7 → 6.10e6 Pa within 0.8 s) — answers,
  then relaxes, same as G4.
- **A2 pose answer** (new this round): the skin MOVES — max displacement
  0.086–0.163 m, 529–911 vertices > 1 mm, RMS 0.027–0.085 m; releasing the pose
  returns the skin to rest to 0.000000 m (bit-exact rest return on all five).
  Conservation never leaves the band while posed.
- **A3 10 kN touch**: `ok:true` on all five, dimple **0.198944 m on every
  shape** — the force-determined value, matching G4 and the seal prereg HR1;
  the per-cell pressure answer (dP) is the mesh-dependent channel.
- **Portraits**: `blob_alive.png`, `torus_alive.png` (standing wheel, hole
  visible, lower cell dark below the seal plane — visually confirmed),
  `capsule_alive.png`, `peanut_alive.png`, `rbox_alive.png`. Distinct md5 per
  frame (all encode to exactly 3,503,097 bytes — an encoder quirk, md5s differ).
- **Guard watch**: zero refusal/degenerate/guard strings in ANY response on
  ANY shape (the `watch_guard` scanner in the driver).

### Repeatability witness

Run 08:22:18 and run 08:24:50 (`gallery_results_20260914_082218.json`,
`gallery_results_20260914_082450.json`) — same driver, same binary, back to
back: identical pose-joint routing (1,2,0,1,0), identical displacements to
4 decimals (0.1562/0.0958/0.1031/0.0860/0.1632), identical dimples, identical
loops/cuts/caps, rest-return 0.000000 everywhere. Only A1's conservation read
wiggles in its 6th decimal (+0.000000 ↔ +0.000877 torus, +0.000439 rbox) —
the read races the tick loop's next conserve recompute (finding 2).

## THE TORUS SEAL-PATH RECORD (the genus-1 canary — record exactly)

The standing wheel (R=1.5, r=0.5, hole axis = z) meets the mid-height plane
y=0 in FOUR arc segments = **2 disjoint cut loops** (front and back of the
tube). The seal on the pre-guard binary:

- `/tick_seal {"y": 0}` → `{"ok": true}`
- `seal_loops=2, seal_cuts=128, seal_caps=124` (the 2 annular cross-sections
  weld 124 cap triangles; the other shapes' single ellipse welds 126 of 128)
- `n_cells=2`, V_cells 3.67145 + 3.67145 = 7.34284 = V_whole to +0.000000 %
- conservation holds under the +25 deg pose (+0.0003) and at rest (+0.0009)
- pose answer j2 → 0.0958 m max skin displacement, rest return 0.000000
- 10 kN touch → ok, dP_upper +2,249,130 Pa, dimple 0.198944 m

**The after-run must see exactly this shape of record.** A degenerate-split
guard landing wrong shows up here FIRST: the torus is the only multi-loop
seal, so any bookkeeping that mishandles loop counting, cap welding, or
per-component volumes breaks the torus before the genus-0 shapes.

## Findings recorded along the way (not mine to fix)

1. **The G4 mid-pin (joint 4) flex has no arm on some shapes — and its
   displacement DECAYS while held.** The 9 spine pins sit on the y-axis; the
   torus's joint 4 pin sits in the HOLE (1.0 m from the tube), so a joint-4
   flex can move nothing (measured exactly 0.0 across 2,048 verts). Worse,
   mid-pin displacement that IS present immediately after `/tick_pose` (run 1:
   blob 0.1808 m) reads ~0 after a 0.8 s settle — the held pose decays — while
   a fresh pose on a well-armed joint holds its displacement across the same
   settle (bit-identical across two runs). The driver therefore poses the G4
   mid pin FIRST (protocol-compatible, conservation-under-pose still measured
   there), and when its displacement < 1e-4 m falls back to the BEST-ARMED
   joint (the pin owning the most vertices under the same nearest-3 binding
   the run just posted). Routing is deterministic: blob j1, torus j2, capsule
   j0, peanut j1, rbox j0. G4's A2 bar (pose ok + conservation) was trivially
   passable by a no-op pose; the displacement metric is what gives the after-
   run a REAL pose answer per shape.
2. **A1 conservation read races the tick loop** (sub-0.001 % wiggle, finding
   visible only in the 6th decimal). Bar unaffected; band set at 0.001.
3. **`--no-restore` + `--hidden` fail-fast at boot** (G4's finding, unchanged
   on this binary): the driver uses `--hidden` in an isolated cwd — boot
   restore finds no blobs and the tick is born EMPTY (asserted `sealed:false`
   before every import), which is the `--no-restore` semantics without the
   0xC0000409 crash, and without touching the live stack's shared snapshot
   blobs. Probe-verified on today's binary before the run.
4. **Portrait byte-size quirk**: all five PNGs encode to exactly 3,503,097
   bytes while md5-distinct. Confirmed visually (torus shows the wheel + hole).

## Files (this dir)

- `h15_gallery.py` — the one-command driver (boots/kills its own throwaways)
- `gallery_results.json` (+ timestamped copies of both runs) — every raw number
- `*_alive.png` — five framed portraits
- `engine_logs/` — the official run's five throwaway engine logs
- `GUARD_THRESHOLD.md` — the degenerate-split guard interaction analysis
- `PROTOCOL.md` — the one-command AFTER-RUN for the post-build window
