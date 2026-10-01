# PREREG — TypeB GPU Phase B: the reflex core, Python side (2026-09-21)

Rule 0 preregistration, written and committed BEFORE any Phase-B replay ran.
Branch `agent/typeb-gpu-phaseb-20260921` (from the physics lane's committed
checkpoint `agent/typeb-gpu-fullport-20260921` @ `a336955`; the branch name is
not yet on the canonical remote — the checkpoint was fetched read-only from the
lane's local repository at that committed hash, uncommitted work excluded).
SPLIT deal honored: no physics-lane file touched; Phase A/C and the tick-0 hang
diagnostic stay theirs. Trailer Agent: GLM 5.3.

## STATEMENT (disagreeable)

The gait controller's DETERMINISTIC REFLEX CORE — the wave-16-disciplined
contact-reset hybrid clock (T_CYCLE=0.71, per-leg offsets {0, 0.5}, reset at
the kTouch rising edge, dt/T_CYCLE advance), the wave-22 touch classes
(kTouch=1e-5 any-point band, kReleaseBand=1e-6 genuine-departure hysteresis),
the hind step law's full decision structure (wave-28 slot fire at phi>=TOE_OFF
with gates (a)-(d); wave-29 alternation-due + the wave-35 concentration
repair; wave-31 band-entry completion; wave-32 min-form deadline
kFoldBudgetTicks=45 / kUnloadTicks=1; wave-33 stand-first arming read;
wave-35/36 carrier waive + waive-ridden hand-off preservation; wave-37
completion-tick graze yield AS SHIPPED in the 9808dc94 bytes; wave-38
stall-era-link calendar guard), the fore stepping clock's schedule decisions
(waves 13/14/15/20 arm/tau1/grid convergence, the wave-20/23/25 gate scopes,
thin-seat deferral, the wave-23 follow seat, wave-26 wait override, wave-24
pocket hold arm), the wave-21 capture arming, and the typea adapter channel
(ZOH at tick boundary, v >= 0 domain, the authority law
xoff = v_cmd*(DUTY_SAMPLED*T_CYCLE)/2 at BOTH plant sites) — is a pure
function of a per-tick observation stream, and a Python mirror of it that
consumes ONLY that stream (no engine state access) reproduces the C++
controller's recorded decisions event-for-event on the shipped walk and on a
commanded walk.

## ORACLE (defined before the replay)

The oracle is the committed `gait_controller.hpp` @ the base (9808dc94 bytes),
compiled natively HERE with `-DGAIT_EVENT_TRACE` from this checkout's own
bytes: (a) its stdout physics columns reproduce the port lane's committed
`cpu_walk.txt` byte-exactly through all 302 ticks (verified BEFORE this prereg
was committed; the committed anchor was generated CP_NO_STATUS — its
hf/fm/tL/tR columns are template constants); (b) the trace stderr carries the
controller's own decision stream ([foreclk]*/[hindstep]* lines); (c) a NEW
probe (this lane's file, `reflex_oracle.cpp`) dumps the per-tick observation
stream (the tick-start state the decisions consume: q, v, per-point gaps,
point world positions, pelvis frame, touching classes, phi, settle/capture/
latch flags, and the reflex bookkeeping for state cross-check). The scene is
the deterministic recompilation `gait_scene.py` output: file sha256
f6844eea..., bundle digest e61ad386... — byte-identical to the wave campaign's
and the port lane's prereg scene. Banked cross-checks already visible in the
oracle stream before any Python existed: refusal 302
gait_positional_correction_budget EXACT; waive fires EXACTLY ONE (L@161) as
receipt_wave38 predicted; stand-first first engagement the 176 decision as
receipt_wave33 predicted.

## PREDICTIONS (made before the replay)

- PB-L1 (clocks): the level-1 mirror reproduces the trace's phi columns
  exactly (the clock law: rising-edge reset, dt/T_CYCLE advance, settle
  freeze) on walk (302 ticks), stand (60), freefall (120, clocks frozen).
- PB-L2 (holds/alternation): the level-2 decision stream matches the C++
  recorded stream event-for-event: 18 hind fires (98 slot; 142 alt; then the
  exchange chain), 17 hind TDs, 22 lift-first holdreturns, 15 standholds,
  14 unloadgates, 1 waivefire (L@161), 25 guardblocks, and the fore stream
  (2 arms, 19 lifts, 34 in-place re-plants, 18 TDs, 1 convergence, 3
  deflifts, 3 pocket holds), each with leg/tick/class and the float payload
  (xoff, from/to, plant_y) to <= 1e-12 relative.
- PB-L3 (adapter): with the command schedule 150:0.60 (the receipt's R2), the
  mirror's v_cmd census matches the authority class: first plant-law
  consumption 7 ticks after issue (onset 157, the M2 class), xoff at that
  fire = 0.60 * 0.2424650 EXACT (f64), and the 20 Hz re-issue variant of the
  same schedule is decision-identical to the single issue (value-only ZOH).
- PB-MONOTONE: at every tick, the decision events of level N are a superset
  of level N-1's on the same observation feed; no level < 3 issues a command;
  the observation stream consumed is identical across levels (verified by
  feeding one dump through all levels and hashing the consumed rows).

## FALSIFIERS (named before the replay)

- F-REFLEX-TRACE-PARITY: fires if any replayed decision (tick, leg, class;
  integers exact, floats > 1e-12 relative) mismatches the C++ recorded
  stream at its level, on EITHER run (plain, commanded), or if a level's
  clock state diverges from the trace phi columns.
- F-REFLEX-LEVEL-MONOTONE: fires if any level < 3 issues a command, or any
  level-N stream is not a superset of level N-1's, or the observation feeds
  differ across levels.
- F-REFLEX-SCOPE: fires if `git status --porcelain` at receipt time shows any
  modified/deleted tracked file (added files only are legal), or any
  modification to walker_nb_env.py / walker_gpu.py / postgen.py /
  walker_numba_gen.py / gait_controller.hpp / cpu_probe.cpp.

## SCOPE + HONESTY

- The live-GPU leg of level monotonicity (status-byte identity of the numba
  env at levels 0..2) CANNOT run this lane: the env's tick-0 hang is the
  physics lane's open Phase-A defect (their checkpoint says so verbatim).
  CPU-side replay is the validation surface per the SPLIT deal; the GPU leg
  is deferred WITH the hang, not tuned away, and the receipt says so.
- Deferred reflex laws are itemized in FIDELITY_MANIFEST_PHASEB.md (ported vs
  deferred per level, the 47-wave law census) BEFORE the replay; a deferral
  that turns out engaged-class on the oracle stream near a mismatch is
  reported as such, never silently back-ported.
- The wave-37 completion-tick re-lock row of the PHYSICS lane's
  FIDELITY_MANIFEST.md says "REVERTED upstream; the ship does not carry it" —
  the 9808dc94 bytes DO carry its graze-yield clause; this lane follows THE
  BYTES and ports it at level 2.
