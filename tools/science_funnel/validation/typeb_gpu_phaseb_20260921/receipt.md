# TypeB Phase-B receipt — the reflex core, Python side (2026-09-21)

Agent: GLM 5.3 · branch `agent/typeb-gpu-phaseb-20260921` · commits
db681031 (prereg, on the physics lane's final 0763d27) → 295c9a9c (oracle +
runs) → d4ce9371 (walker_reflex.py + harness, LEVELS GREEN) → this receipt.

## VERDICT: GREEN on all three preregistered falsifiers — with the scope
honestly bounded to the CPU-side replay surface (the SPLIT deal).

## THE ORACLE (independent of this lane's code)

- The committed `gait_controller.hpp` bytes compiled natively with
  `-DGAIT_EVENT_TRACE`; the plain walk reproduces the port lane's committed
  anchor: refusal 302 gait_positional_correction_budget EXACT, and the
  observation stream (OBS t=k+1 == cpu_walk.txt tick=k, the pre-step vs
  post-step sampling) is BYTE-EXACT for q3/q4/q2/v3/phi0/phi1 across all 302
  ticks (0 mismatches).
- The decision stream is the controller's own trace bytes: 238 decision
  events on the plain walk, 244 on the commanded runs, byte-identical between
  the single-issue and the 20 Hz re-issue commanded runs (the value-only ZOH
  law, F_ZOH_CLOCK class).
- Banked cross-checks visible in the oracle before any Python existed:
  first hind fire 98 slot; the waive fires EXACTLY ONE (L@161) as
  receipt_wave38 pre-registered; the stand-first first engagement the 176
  decision as receipt_wave33 pre-registered; the height-fire margin
  0.039326 m = the receipts' 39.3 mm.

## F-REFLEX-TRACE-PARITY: GREEN

Replay = walker_reflex.ReflexCore consuming ONLY the per-tick (q, v)
observation stream (everything else derived through the committed
walker_model FK mirror). Compare: (kind, tick, leg) sequence EXACT; floats
within the trace's own print precision (5e-7 on %.6f fields; the full table
in reflex_replay.py).

| Run | Level | Decision events | Parity |
|---|---|---|---|
| walk (plain, 303) | L2 | 238/238 | EXACT (0 mismatches) |
| walk (plain, 303) | L3 | 238/238 | EXACT (0 mismatches) |
| cmd 150:0.60 (refuses 297) | L3 | 244/244 | EXACT (0 mismatches) |
| reissue 150+15k:0.60 | L3 | 244/244 | EXACT (0 mismatches) |
| stand (60) / freefall (120) | L1-L3 | 0 | clean (frozen/advance clock parity below) |

- PB-L1 (clocks): the mirror's phi vs the trace columns: worst absolute
  drift 0.0 (BIT-EXACT) at L1/L2/L3 on walk, cmd, reissue, stand; freefall
  0.0 at L>=1 after the harness config was corrected (below).
- PB-L2 (holds/alternation): every census class reproduced event-for-event:
  18 hind fires (98 slot first), 17 TDs, 22 holdreturns, 15 standholds,
  14 unloadgates, 1 waivefire (L@161), 25 guardblocks, 19 fore lifts,
  34 in-place re-plants, 18 fore TDs, 3 deflifts, 3 pocket holds, 1
  convergence, 46 paw captures, 1 height latch (margin 39.3 mm exact).
- PB-L3 (adapter): the mirror's census — first plant-law consumption tick
  157 EXACT (7 ticks after the 150 issue, the receipt's M2 onset class);
  xoff = 0.145479 = 0.60 * 0.2424650 EXACT at EVERY post-issue fire while
  the measured v3 was 0.672 (the command, not the measurement, entered the
  plant law — the authority law end-to-end); 20 consumptions; the ZOH
  re-issue run census-identical (fires=20, first=157) and its decision
  stream event-identical.

## F-REFLEX-LEVEL-MONOTONE: GREEN

- L0 emits ZERO events on every feed (pure physics; the layer is inert).
- No level < 3 issues a command (the command census is live=false and the
  issue list empty at L0/L1/L2 on every run, including the commanded feeds).
- L1's stream is a subsequence of L2's and L2's of L3's on every feed.
- L3 == L2 exactly when no command is issued (walk/stand/freefall) — the
  adapter is INERT WHEN UNUSED, as declared.
- Note: cross-feed comparisons (cmd vs plain at L<3) are NOT a monotonicity
  requirement — the commanded oracle embeds a live L3 command in the C++
  itself, so those feeds are different trajectories BY DESIGN; the binding
  checks are the same-feed ones above.

## F-REFLEX-SCOPE: GREEN

`git status --porcelain` at receipt time: added files only
(walker_reflex.py; the phaseb validation dir). Zero modifications to
walker_nb_env.py / walker_gpu.py / postgen.py / walker_numba_gen.py /
gait_controller.hpp / cpu_probe.cpp / any physics-lane file. The oracle
binary and runs live in-repo under this lane's validation dir only.

## FIDELITY MANIFEST (FIDELITY_MANIFEST_PHASEB.md)

- Level 1: 4/4 law families PORTED (clock, wave-16 discipline, wave-22
  touch classes, wave-21 capture arming).
- Level 2: 21 families carried — 19 PORTED, 1 NOT-CARRIED (wave 34, reverted
  upstream; parity with the ship), 1 superseded-and-carried (wave 30's
  unload-lift face inside the wave-32/33 machinery).
- Level 3: 1/1 PORTED (the typea adapter channel).
- Total: 25 law families ported; deferred in this lane: the tau/application
  path (the env kernel's, judged by the physics lane's anchors), the reset
  law (carried via walker_model), the energy ledgers (diagnostics), and the
  live-GPU leg (deferred WITH the physics lane's tick-0 hang — their final
  receipt's honest UNMEASURED state — not tuned away).

## WHAT FIRED (honest, during the run)

1. My FIRST parity run failed massively (177 vs 238 events): a real mirror
   bug — `_capture_paw` double-halved the already-halved paw reference,
   planting the fore targets ~5 cm off, which silently re-scheduled the
   whole fore clock. Fixed; then 238/238. The prereg's predictions were
   written before this was found; the failure is in the commit history.
2. My freefall harness config wrongly set gait_enabled=false; the C++
   freefall keeps gait ON (clocks advance once the settle ends — the
   measured 0.2723 drift at t118 = 58/213 exactly, the clock law's own
   signature). Harness fixed; the drift went to 0.0.
3. Two harness-level falsifier accounting errors (cross-feed monotonicity,
   L2-parity demanded on commanded feeds) were identified as checker bugs —
   the C++ oracle on a commanded feed IS an L3 controller — and corrected
   with the reasoning recorded above, never by loosening the same-feed
   checks.
4. Labeling note: the height latch is stamped tick 76 in this lane's
   pre-step convention; the wave receipts' "75" is the same state (the
   margin 0.039326 m is the identity anchor, exact).
5. The wave-37 graze-yield clause IS in the ship bytes; this lane ported it
   AS SHIPPED and corrected the physics lane's manifest row (their
   "REVERTED upstream" note contradicts the 9808dc94 bytes).

## ARTIFACTS

- walker_reflex.py — the reflex core (this lane's only runtime file).
- reflex_oracle.cpp + runs/ — the observation oracle and the five committed
  run pairs (obs + decision trace).
- reflex_replay.py / replay_results.json — the parity harness and its output.
- PREREG_PHASEB.md / FIDELITY_MANIFEST_PHASEB.md — frozen before the run.

## NEXT

- Phase C (or the hang-repair lane) inherits the live-GPU monotonicity leg:
  feed a batched env's status stream through ReflexCore and diff against
  this lane's CPU streams (the harness is ready; only the env's tick-0 is
  missing).
