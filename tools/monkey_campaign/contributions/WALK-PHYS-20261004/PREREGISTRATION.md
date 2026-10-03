# PREREGISTRATION DRAFT — WALKPHYS-V1: limb-transmitted propulsion evidence on the certified articulated walk line

Status: **DRAFT (chain stop 1).** Authored by wk-walk-physicalization,
2026-10-02, phase 1 (design + prereg DRAFT only; ZERO runner jobs launched by
this lane). This draft awaits the Lieutenant's pin; the final freeze (the
FINALIZE-AT-FREEZE slots below) happens at run time per the standing prereg
law, and any required prereg commits go through the publication owner BEFORE
any gated experiment. Nothing here is a run claim.

Design of record: DESIGN_RANKING.md Rank 1 (Option A') — the sealed W03-class
articulated walk scene (`chimera.earth_scene.v1` scene sha256
`f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`) with its
physical bytes UNCHANGED; a NEW declared instrument arm that records, per
tick, the force-transmission channels the native state already computes
(per-contact-point gap/touching/reaction_N/friction_force_N/slip_speed_m_s,
per-drive torque/work, base pose/momentum, the full energy-ledger term split),
qualified against the sealed anchor identity and a declared discriminator-arm
battery. Source of record: revision `17ba94b948ca217c1bbf8f7dee5b51b995b387bb`
blobs (`5863348f2deef1f01e3cf761d0c4151a10035a6d` gait_controller.hpp,
`a7bfe15e34e25a34c5316d65038b072d79ac529a` gait_unit_viswalk_dump.cpp,
`8cd6004fc4a65f2f804ff1e00c18f1962bbaa9f0` build_dump.ps1), extracted
read-only from the shared object database and hash-pinned in the sealed
package (the W03 extract pattern; NO worktree, NO clone).

## 0. The claim this prereg qualifies (and the claim it never makes)

QUALIFIES: in ONE runtime body (14 bodies / 18 coordinates /
10.037998000000004 kg), the walk's propulsion is SOLVER-PHYSICAL through the
limbs — every tick's horizontal momentum change traces to recorded contact
impulses at the 8 declared pads (hind feet + fore knuckles), the drive->work
->contact->momentum split is energy-accounted, and visible motion has no
force source outside the declared set.

NEVER CLAIMS: a launchable build (PLAYABLE_BUILD.json nulls stand), real-time
play (TC-11), uneven-ground traversal (F06's measured negatives stand —
NAMED FOLLOW-ON, not folded in), a trained policy, an anatomical hand or
grasp/climb transfer, any change to any sealed W10/W03 row.

## 1. Declared control law (the command-channel role, exactly)

This scene has NO COM command channel. The complete control law, declared:

1. ENTRY (tick 0, once): the sealed entry law — joint targets from
   `tables_rad`/`zero_map_rad` at the sealed entry phases {0.0, 0.5},
   the 60-tick settle, and the DECLARED INITIAL base speed
   (`base_speed_x_m_s`, the stance-contact-still value derived by the sealed
   scene compiler). An initial condition, never a per-tick channel.
2. RUN: the gait phase clock advances; joint targets follow the sealed
   tables through the 12 certified capped servos (torque = k*(target-angle)
   - c*rate; caps 11.2125/6.6375/7.4/0.8875 hind, 4.229/3.76 fore N*m).
3. NOTHING ELSE writes state. Enforcement: P9 (state-write injection) and
   the config census (every config key recorded in the receipt).

The W10 8-command interface is a DIFFERENT scene's law (the certified
surrogate line) and is neither present nor replaced here.

## 2. Frozen predictions (all evaluated with named variables; acceptance = sealed receipt)

P1 ANCHOR IDENTITY (regression floor; anti-perturbation proof): the clean
instrument arm reproduces, EXACTLY at recorded precision: scene sha
f6844eea...a8db342; stdout sha 8c537cdb...; stderr sha c6f9b6c0...; q-dump
run1 sha b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93;
run2 == run1 bit-identical; ticks 302 (0..301); base dx 0.9131056683968011,
dy -0.7178374101385098; worst ledger balance 30.970714 J at tick 300 (raw
30.970713623726674). FAILURE = the recording layer perturbs physics — the
lane records the failure and stops (no tuning to recover).

P2 SUPPORT CENSUS (closes the recorded MISSING duty factor): every tick of
the declared walk window [60, 300] records >= 1 touching contact point with
reaction_N > 0 within 1e-9 N; the full per-pad census (per contact point:
touching ticks, impulse sums, first/last touch) is emitted. PASS = complete
census, zero unexplained touches.

P3 PROPULSION ATTRIBUTION IDENTITY: for every tick in [60, 300], the
recorded generalized contact impulse on base_trans_x equals the finite
difference of body horizontal momentum mapped through the recorded channels,
within declared window 1e-9 (relative per-tick house identity class). PASS =
all 240 ticks inside the window; any violating tick names its force source
or fires FB-P5.

P4 ENERGY LEDGER SPLIT (both-ways frozen): per tick, the recorded split
|d(KE) + d(PE_grav) - (W_actuator + W_contact_impact + W_friction_heat +
W_damping_heat + W_brake_heat + W_external)| is computed and emitted; the
cumulative balance at tick 300 must EQUAL the sealed 30.970713623726674 J
(identity with the anchor, proving the split accounts the SAME imbalance).
QUALIFICATION GATE G-E: the walk window [60, 300] sub-ledger closes within
the declared window (FINALIZE-AT-FREEZE: 1e-6 J/tick class, justified by the
G04/K02 1e-12..1e-16 closures and the native float path). IF THE GATE FIRES
- the recorded outcome is the honest NEGATIVE: the imbalance is localized
(tick/term where it accumulates), the receipt says "energy ledger NOT closed
on the native walk line; closure is engine debt", and the lane verdict is
MIXED_AS_MEASURED with P3 carrying the propulsion claim. No repair in this
lane; an engine ledger fix is a NEW prereg through the publication owner.

P5 ZERO-FRICTION DISCRIMINATOR (the no-animation law, executed): declared
control arm, scene friction = 0 (single declared delta; the G04 zero-mu
control class), everything else identical, same seed. DERIVED INVARIANT
(Newton; gravity and contact normals are vertical, so with mu=0 no external
horizontal force exists): whole-body horizontal COM displacement over
[60, 300] satisfies |COM_x(300) - COM_x(60)| <= 1e-4 m (8+ orders above the
1e-12-class identity noise, 3+ orders below any gait displacement).
FIRES if the COM advances with zero friction = an undeclared horizontal
force source = animation/command propulsion exposed.

P6 DRIVE-CUT DISCRIMINATOR: declared control arm, `power=false` engaged at
declared tick t_cut=150 (an existing scene config; the coupled-native
cut-drive class). DERIVED INVARIANT: horizontal COM momentum is
non-increasing from t_cut through t_cut+100 within declared window
(friction and damping only remove it; no hidden cruise channel may hold it).
FIRES if COM momentum rises beyond the window after the cut.

P7 CAP-RAISE TAMPER (anti-tuning detector proof): scratch arm, one drive cap
x1.5. MUST be caught by the declared cap/work-envelope detector (the
f4_work_envelope channel class) or refuse. A clean-running cap-raise = the
detector is vacuous = FB fired.

P8 DETERMINISM: two full passes, byte-identical receipts and traces
(house standard).

P9 STATE-WRITE INJECTION: a declared attempt to write base/COM state at a
declared tick must be refused or visibly diverge against the clean
continuation (the certificate-gate I1 class; U02 no-force invariant / W07
clause / TC-4 pose authority).

## 3. Qualification gates (the F7 bar)

- G-PROPULSION: P3 passes on the clean arm (propulsion work/momentum traced
  to contact forces every tick).
- G-COMMAND-ROLE: section 1's declaration is complete AND P9 holds (no
  undeclared state writer; the entry-speed initial condition is the only
  declared momentum input and P6 proves no channel sustains it).
- G-ENERGY: P4's gate as written (both-ways; a firing is the localized
  negative, recorded, never repaired by tuning).
- G-DETERMINISM: P8.
- G-ANTI-TUNING-BACKSTOP: P1 (nothing moved) + P7 (the tamper detector
  bites).
VERDICT CLASSES: SUPPORTED (all gates green), MIXED_AS_MEASURED (G-ENERGY
negative, others green — the honest F7-partial verdict with the named debt),
REFUSED/FALSIFIED (any other gate; the negative is the result).

## 4. Anti-tuning law (standing, extended)

No drive cap, friction value, gait table, zero map, mass, inertia, entry
speed, servo gain/frequency, tick rate, substep count, contact point, or
plane height may differ between the sealed scene and any CLEAN arm. The only
declared deltas are the three CONTROL arms (P5 mu=0, P6 power-cut, P7
cap-raise), each of which is EXPECTED to lose support/motion. Instrument
schema, windows, and tolerances are declared in this prereg BEFORE any run
and never swept; a FINALIZE-AT-FREEZE constant may be set once at freeze
with its derivation, never after seeing data. Any gate that would pass only
under a clean-arm parameter change is a tune_to_success refusal: the lane
records it and stops.

## 5. Execution plan (phase 2, not started)

- All execution through `E:/PythonChimera/tools/monkey_campaign/
  task_package.py seal|run` (NO_WORKTREES.md obeyed; runner slots per the
  dispatch; BUSY = wait/retry).
- PRE-GATED FEASIBILITY PROBE (declared, before the gated battery; not a
  qualification run): the package builds the pinned dump binary from blobs
  `5863348f...`/`a7bfe15e...` with recipe `8cd6004f...` inside a slot and
  runs 1 tick; outcomes: OK / BLOCKED(toolchain) — a BLOCKED is reported as
  the smallest missing prerequisite (MSVC/native toolchain availability in
  the runner), never worked around by tuning or by moving the run outside
  the runner.
- Battery: P1 clean arm (302 ticks, ~7-14 s CPU at the measured 23-46
  ms/tick), P2-P4 channels on the same arm, P5/P6/P7 control arms, P8
  second pass, P9 injection. All receipts + traces declared with --keep;
  evidence anchored through anchor.py before any reference.
- Cost estimate from receipts: < 15 min CPU total (six arms x 302 ticks).

## 6. Honest-absent list (declared BEFORE any run)

- Launchable build / playable loop: ABSENT (PLAYABLE_BUILD.json UNQUALIFIED,
  all null; engine-wiring/runtime qualification unowned).
- Interactive real-time 300 Hz: ABSENT (TC-11 COST-GAP; 6.7-13.7x over).
- Measured friction for volar skin/pads: ABSENT (0.6/0.4 NAMED PLACEHOLDERS;
  NB-01/02; this lane treats them as fixed declared inputs, never tuned).
- x_press and all actuator-cap measurements: ABSENT (TC-8 0/8; caps are
  declared scene data).
- Native-walk energy-ledger closure: UNKNOWN-AT-DRAFT (30.970714 J sealed
  imbalance; P4 measures and localizes it; the negative is pre-accepted).
- The 22-DOF anatomical hand chain dynamics: ABSENT (statics map only);
  hand transmission here = the forelimb knuckle pads (2-joint chains).
- Uneven ground / grade / step-over: OUT OF SCOPE (F06 measured negatives
  stand: stall grade 0.0365707, step-over ceiling 0.11599999 vs 0.128476 m;
  NAMED FOLLOW-ON, new runbook, not this lane).
- Trained policy: ABSENT (the sealed reflex tables are the controllers).
- Continuous ten-phase loop, GPU backend, whole-loop review protocol: ABSENT
  (matrix sections 2/4).
- Fore-pad support during gait: UNKNOWN-AT-DRAFT (the sealed trace cannot
  answer; P2 measures it and the census is the result either way).

## 7. Preservation law

The W10 sealed rows (trace_walk.json 0dc4dc75..., receipts, captures), the
W03 anchor set, every store row, and every other lane's bytes are UNTOUCHED.
This lane's writes: this lane directory only (phase 1) + a NEW package
contribution directory (phase 2) emitting NEW artifacts. No Git mutation
from this lane; proposals go through the serialized publication path; no
merge authority is claimed anywhere.
