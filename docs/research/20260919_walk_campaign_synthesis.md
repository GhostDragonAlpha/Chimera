# The Walk Campaign Synthesis — a walking macaque on Earth (2026-09-19)

Append-only synthesis document. It organizes what the walk campaign's receipts already
record; it contains no new claims and no new numbers. Every claim cites the receipt it
came from. A new agent should be able to inherit the whole campaign from this page plus
the cited receipts, without re-deriving anything.

## The receipts (the citation key)

All paths under `tools/science_funnel/validation/`:

| Cited as | File |
|---|---|
| (impl receipt) | `gait_impl_20260919/receipt.json` — the controller implementation lane (`lane/gait-impl-20260919`) |
| (receipt.json) | `gait_zero_20260919/receipt.json` — wave 1, the zeros |
| (wave2) … (wave11) | `gait_zero_20260919/receipt_wave2.json` … `receipt_wave11.json` |
| (wave8_trunk_vault) | `gait_zero_20260919/receipt_wave8_trunk_vault.json` — Buffy's trunk-vault lane |
| (quad-share receipt) | `quadruped_share_20260919/receipt_quadruped_share.json` — **not on this branch**; commit `14caff74` on `buffy/quadruped-share-20260919` (read via `git show 14caff74:<path>`) |

Lane genealogy, from the receipts' own `lane`/`base` fields: wave 1-6 ran in-session on
`codex/force-data-runtime-20260916`; wave 7 (`buffy/gait-wave7-sole-contact`) was merged
(84ff1747); wave 8 ran in-session and merged wave 7 under the trunk freedom (fdc74523);
`buffy/gait-wave8-trunk-vault` branched from f7ddbd07 and was integrated as wave 9
(`buffy/gait-wave9-integration`, merged e6bd7def); wave 10
(`buffy/gait-wave10-admissible-vault`) based on 54472e63; wave 11
(`buffy/gait-wave11-quadruped`, this branch) based on 7e0904ec.

**Wave 12 does not exist yet.** No `receipt_wave12.json` is on this branch (verified by
file listing at synthesis time). A wave-12 lane is RUNNING on planted fore struts; it is
recorded in §4.1 as in-flight, with its named target only.

---

## 1. The question

**Can the simulator produce a walking macaque on Earth — honestly, with every number
derived and every falsifier pre-registered?**

The concrete target, from the implementation lane and the falsifier suite
(impl receipt; `docs/research/20260918_gait_controller_derivation.md`): a planar
14-coordinate (later 18) bipedal walker driven by the admitted 21-node gait tables
(stride 0.72 m, period 0.71 s, average speed 1.01 m/s, duty 0.68), body weight
98.4391527 N (mass 10.038 kg) (wave8_trunk_vault scene measurement; wave9 scene),
under Earth gravity — where "on Earth" is itself a maintained falsifier: F-G5 measures
free fall at -9.806650 m/s² with the controller powered off, because "a creature that
cannot FALL cannot walk: the simulator falls honestly" (impl receipt).

The campaign's discipline is Rule 0: every wave banked a STATEMENT / PREDICTION /
FALSIFIER triple before building, measured, and recorded red as red (every receipt in
the campaign carries `"pass": false` — the walk has never passed; the falsifiers that
are green, F-G5 and F-G7, are recorded green everywhere).

The start of the measured record: the controller implemented the tables, the falsifier
suite F-G1..F-G8, the scene compiler, and admission machinery; F-G5 was green and the
walk entered an event/energy-integrator storm inside the first cycle, with four named
root causes (impl receipt). The campaign below is the closing of those causes, one
membrane at a time.

---

## 2. The ladder — one rung per mechanism

The campaign's walk-refusal ticks, in the campaign's ladder order. Each rung is a
mechanism with its measured refusal tick and what failed there. The rungs are NOT in
time order (the receipts' dates interleave; see the chronology note at the end of this
section). Before the ladder, the pre-ladder record: tick 40 (wave 1-2, integrator-limit
refusal, fully diagnosed), tick 118 (wave 3-5, the sentinel bug fixed, then the honest
fall), tick 88 (wave 6), tick 66 and tick 127 (wave 8, entry schemes), tick 86 (wave 7
merged).

| # | Mechanism | Wave / receipt | Refusal tick | What failed there |
|---|---|---|---|---|
| 1 | **86** — the migrating sole-segment contact (one CoP row per foot replacing the two point contacts) | wave 7 (wave7) | 86 | Falsifier f2 FAIL: refused earlier than wave 6's 88 and the 118 target. The flat-phase geometric demand passed (3.0516137 N·m at the 0.031 m midpoint lever, under the ~4 N·m bar) but the dynamic walk did not survive; ledger RED pre-existing at 2.999892 J. F-G5/F-G7 green. |
| 2 | **116** — the composition: continuous trunk-vault table + settled sole-contact entry + E8 booking, merged | wave 9 (wave9) | 116 | Falsifier f1 FAIL: the mechanisms did not compose under sole-contact loading — refused two ticks before the main-only 127 and far before the vault-only 181. The trunk target swept a cap-saturated transition (posture motor hit its 11.21250 N·m cap; [trunk] ticks 70→100: -4.46° → +18.24°) while the planted soles skid (left heel slip 0.781 m/s at tick 110). Ledger PASS vs the wave-9 10 J bar (3.441343 J). Bisects: no-sole contact ran the 710-tick budget but ledger 43.183718 J; settle=0 refused at 107 — settling helps (107→116), the vault table is what is dynamically too abrupt. |
| 3 | **181** — the continuous trunk vault: theta*(phi) as a load-bearing DOF, phase-tracked from the 21-node 0.5-periodic table | wave 8 trunk-vault lane (wave8_trunk_vault) | 181 | Crossed the 118 wall for the vault lane, then failed dynamically: the feet skated rather than forming a stable vault (sole slip 0.03-0.48 m/s; representative late reactions 2.011/10.489/9.327 N), ledger broke to 37.870489 J, full_cycle=false. The static membrane itself passed strongly (worst min-max ratio 0.8809). F-G1..G3 unmeasured (refusal before the transient window); F-G5/F-G7 green. |
| 4 | **206** — the reachability-constrained "admissible" vault: SLSQP direct collocation over periodic theta/theta-dot, attempted in the walk | wave 10 (wave10) | 206 | Both parts falsified. Part B static FAIL: the best collocated table kept posture demand (10.091250 N·m) under the 11.2125 N·m cap but the COMBINED stance/posture envelope reached ratio 1.322776 of cap at phi=0.85 — no table meeting the 0.9-cap bound exists. Part B dynamic FAIL: the attempted table saturated posture torque on 21/21 sampled [trunk] lines and refused at 206, ledger 26.040517 J. Part A FAIL: the no-contact vault+settle run that completes 2130 ticks is NOT a gait — duty 1.0/1.0, no touchdown pairs, no GRF closure, base ends at x=3.8596 m, y=-244.04 m (falling/sliding, not walking), ledger 43.183718 J with brake heat dominant (86.847731 J). |
| 5 | **291** — the quadruped forelimb struts: two-coordinate (shoulder/elbow) fore chains at fore share s=0.45, four hind + four forepaw contacts | wave 11 (wave11) | 291 | Refused on `gait_positional_correction_budget` after the fore strut contacts had lifted — before the named target of tick 426 (two full cycles). Worst ledger 30.202201 J (F-G8 fail). F-G1/G2/G3 RED-not-measured (refusal before the transient window), F-G4 GREEN per hind drives (fore rows not emitted before refusal), F-G6 RED/incomplete (armed capture_events=0). F-G5 green (free fall -9.806650 m/s², stand fold 5.00842°), F-G7 bit-identical. Graph tests 19 passed, 27 subtests. The refusal is banked as a dynamic contact/settle finding. |

Chronology note (from the receipts' lanes and the branch log): wave 7 measured 86
(commit f43b0e02, merged 84ff1747); wave 8 in-session measured trunk-freedom-only at
88, merged 86, then TD-entry+settle at **127** — past the 118 wall for the first time
(wave8, commits a8f3f8e4, fdc74523); the trunk-vault lane measured 181 (e6bd7def); wave
9's composition measured 116 (54472e63); wave 10 measured 206 (7e0904ec); wave 11
measured 291 (f0efbba7). The ladder orders the rungs by the campaign's mechanism
sequence, not by date; the receipts hold the dates and commits.

---

## 3. The laws established

These are the campaign's settled results — each derived, measured, and banked with its
receipt. "Settled" means the falsifiers passed and nothing since has reverted them.

1. **The zero map** (receipt.json). The Oku table angle conventions were
   underdetermined by the admitted bytes (impl receipt, named root cause 1); wave 1
   closed it by model selection over three frame premises under one closure law
   (rolling plantigrade contact rides one level over the 14 stance nodes). The joint
   premise won at 5.8 mm stance ride (inside the tables' own 6-12 mm reconstruction
   noise); the segment premise was falsified at 47.1 mm; the mixed premise was
   degenerate (7.0 mm) but the joint frame shipped as the physical frame. Banked zeros:
   hip -0.044399, knee -0.080389, ankle -0.862213, MP -0.768513 rad. The lane's +1 hip
   stem had been correct all along; the composed 72.5° TD heel-dig was the missing
   ankle and MP zeros. The MP plantarflexion stop was amended -0.35 → -1.2 rad,
   falsified by the admitted M-table bytes under the derived zero. Banked as
   `model.dynamics.gait_walker` revision 2, idempotent, falsifier replays green on
   re-run. The composed cycle is a plantigrade macaque walk: heel-first TD +15.9°,
   flat phase with windlass toes, progressive heel-off to -33° push-off, knee flexed
   31-73°.

2. **The entry laws** (wave2, wave3, wave6, wave8). Four laws, each superseding the
   last, each retained where measured better:
   - *No-skid entry* (wave2): the paper's 1.01 m/s is the cycle average; the periodic
     entry requires the stance contact's ground-relative horizontal velocity to be
     zero, giving entry speed +0.764 m/s from the tables at compile time. Halved the
     transient ledger 2.58 → 1.33 J.
   - *Single-support entry* (wave3): the TD state is over-determined (the tables'
     closure residual leaves the two stance contacts 2.96 mm apart at double support);
     the lawful entry is the vertical-thigh instant phi=0.449, seated on the stance MP
     head, at 0.849 m/s.
   - *Settling-contact entry* (wave6): the entry phase is the nearest-vertical thigh
     SUBJECT TO the stance contact not opening (contact_vy <= 0; the plane-arming gate
     rejects opening faster than ~4 mm/s). The bare vertical-thigh instant sat on a
     +64 mm/s rising limb — the wave-5 bounce. The law lands at phi=0.359, and produced
     the first load transfer ever measured: nonzero seated reaction 0.24 N at tick 0,
     both feet carrying 46 N by tick 20, skate gone by tick 60 (slip 0.001-0.06 m/s,
     was 1.206).
   - *TD entry + settling* (wave8): the best entry architecture measured. The clock
     holds the TD pose under load for the servo's settling time (3 periods at 4 Hz,
     zeta 0.8 ≈ 0.19 s → 60 ticks), then releases. Refused at 127 — past the 118 wall;
     single-support entry + settle instead refused at 66 (the settle left both feet
     penetrating). The settle absorbs the TD bounce exactly as derived.

3. **The settle** (wave8). The settle is the orbit-capture mechanism: 60 ticks
   (`settle_ticks` in the scene defaults), frozen-clock load-carrying before release.
   Measured combinations: single-support+settle 66; TD+settle 127. Wave 9's bisect
   confirmed it composes: settling improved the sole-contact branch 107 → 116 (wave9).

4. **The sentinel namespaces** (wave3). The engine bug the walk exposed the moment it
   survived past tick 40: `advance()`'s event discriminator used `which==2` as the
   CONTACT sentinel while drive events used `which` = drive index 0..7 — and drive 2 IS
   `ankle_dorsiflexion_left`. At tick 117 the drive event (which=2, khit=-1) was
   mistaken for a contact and `probe[(size_t)-1]=0` wrote out of bounds; the heap smear
   killed the suite with the "vector out of range" popup. The law: drive events are
   `which` = 0..7, contact events are `which` = -2 (khit = the point), none is -1,
   guarded by `require(gait_event_namespace)`; the fp-level clamp branch pins ANY
   drive's wall (the old `which<2` pinned only drives 0/1 — a second latent bug in the
   same branch). Falsifier: the tick-117/118 crash reproduced in every prior run and is
   gone in every run after the fix.

5. **The E8 booking** (wave5; wave4's instrumentation; confirmed wave9). The discrete
   constraint impulse work is booked (trapezoidal) in the ledger identity and the
   energy report. Measured magnitude: 57 µJ over the walk (wave5) — real but tiny;
   -1.133e-6 J by tick 110 in the merged run (wave9). It is NOT the growing ledger
   channel.

6. **The MP-Jacobian correction** (wave8). The wave-4 statics gave FOOT-BODY contact
   points (heel, MP head) a nonzero moment column on the MP coordinate — but the MP
   joint is distal to those points: they do not move when the MP rotates; the column
   must be zero. The wave-4 "MP demand 7.8-8.4 N·m windlass flags" (wave4) were this
   artifact. Fixed in both `derive_stance_hold.py` and `derive_trunk_pitch.py`; the
   knee/ankle/hip columns were correct throughout, so wave 4's cap conclusions stand
   (wave8).

7. **The statics feasibility reversal** (wave8; extended wave8_trunk_vault). After the
   Jacobian fix, at every single-support node (phi 0.20-0.50) a trunk pitch theta*
   exists with worst demand/cap ratio 0.92-0.95 (0.64-0.66 at phi 0.20-0.25); theta* is
   a forward lean of +5..+30°; the posture drive pays 0.08-0.79 of its cap. The
   trunk-vault extension (base rotation as a rigid-assembly DOF, sole CoP free on
   [-0.012, 0.074] m) found worst min-max ratio 0.8809, knee 5.70-5.85 vs 6.643 N·m,
   ankle -6.36..-6.51 vs 7.396 N·m, posture peak 8.21 vs 11.218 N·m — and its theta=0
   calibration reproduces the wave-4 rows exactly (wave8_trunk_vault). Conclusion,
   verbatim in spirit from (wave8): THE 2x-UNDER-PROVISIONED HYPOTHESIS IS DEAD — the
   biped is statically feasible at every stance node; nothing in the statics forces the
   quadruped; the remaining gap is the DYNAMIC orbit. Caveat measured: the theta*
   landscape is multi-basin (adjacent-node jumps of +4.6 → +29.8° are unreachable at
   the 11.2 N·m posture cap — rotating the HAT inertia 25° in one phase interval needs
   ~100 N·m) (wave8). This is the statics background against which the stance-hold
   finding must be read: wave 4 measured the caps cannot hold the poses STATICALLY in
   single support (knee 7.28 vs 6.6 N·m at the entry instant; 33-60% over at window
   center; push-off window over every cap), the source walk is DYNAMICALLY supported
   (GRF closure 2·I = BW·T holds at -1.3% while the measured knee peak is 5.31 N·m
   against 9+ N·m static demand), and "the walk needs momentum, not bigger caps"
   (wave4). Both results survive the Jacobian fix, which touched only the MP column
   (wave8).

8. **The dynamic inadmissibility of the periodic vault** (wave10). Direct collocation
   over 21 periodic theta/theta-dot nodes (T=0.71 s, HAT inertia 0.5335 kg·m², gravity
   moment amplitude 20.097 N·m) cannot produce a vault that is both statically
   admissible and dynamically survivable: the best table holds posture under cap
   (10.091250 vs 11.2125 N·m) but the combined stance/posture ratio reaches 1.322776 of
   cap at phi=0.85; attempted in the walk it saturates posture on every [trunk] line
   and refuses at tick 206. Verdict recorded: "the bipedal admissible-vault path is not
   established at this cap; the quadruped comparison becomes the architecture headline"
   (wave10). Also wave 10, Part A: the long no-contact vault+settle run is not a gait
   under the pre-registered duty falsifier (duty 1.0/1.0, no TD pairs, catastrophic
   height loss).

9. **The quadruped relief numbers** (quad-share receipt). The fore-share statics
   (NQ=15 planar: two 4-DOF hind chains + two 2-DOF fore chains; hind contact carries
   (1-s)W, each fore paw sW/2; MP-column-zero correction included): fixed-pose hind
   worst single-support ratio is monotone in the share — 1.6288 (s=0), 1.2269 (0.25),
   0.9858 (0.4), 0.7447 (0.55) — with signed demands affine in s to a 1.776e-15 N·m
   residual (falsifier f1 PASS). The stronger predictions FAILED: the hind ratio is not
   below 0.6 at the mission shares (0.9858 at s=0.4), the theta*-reoptimized track is
   non-monotone (0.9661 / 0.9839 / 1.1361 / 1.1064 — the binding constraint switches
   between posture and limb rows; reported as a separate pose-selection effect), and
   the segment-scaled fore-elbow cap is exceeded at s=0.55 (ratio 1.0727) though the
   document's 3.76 N·m triceps cross-check stays under cap at the mission shares
   (falsifier f2 FAIL). Replication anchors: full-HAT biped theta* worst 0.9661,
   banked trunk-vault anchor 0.8809, carved-HAT baseline 0.8885. Fore data gap declared:
   the assembly document gives total arm mass 0.406001 kg/side and lengths
   0.125/0.132 m but no per-segment masses; the hind thigh:shank proportion
   (0.557:0.269) transfers to humerus:forearm (0.2737 kg / 0.1323 kg), lengths as
   documented (quad-share receipt; used by wave11's struts).

---

## 4. The open membranes

### 4.1 Wave 12 — planted fore struts (IN FLIGHT, not yet receipted)

No `receipt_wave12.json` exists on this branch (verified at synthesis time). The
wave-12 lane is running on PLANTED struts: wave 11's refusal happened "after the fore
strut contacts have lifted" (wave11), so the next membrane holds the fore paws planted
through the loaded window instead of letting them lift. Its named target, inherited
from wave 11's pre-registered prediction: exceed **tick 426** (two full cycles at
cycle_ticks=213, wave7) with ledger under 10 J, and the F-G1..G3 first measurement
(tracking, duty/phase, GRF closure) — none of which has ever been measured, because
every run so far refused before the transient window (wave8_trunk_vault, wave9, wave10,
wave11). Wave 11 also pre-registered the fallback: a refusal before 426 triggers a
bisect at s=0.25, 0.45, 0.55, recording the named joint and tick (wave11).

### 4.2 The ledger question (OPEN, deprioritized but not closed)

The moving-walk ledger has never closed at the qualified tier. The measured chain:
tick-0 baseline bug fixed (-0.591 J constant offset; tick-0 balance now 0.0087 J)
(wave4); the residual ~3.5 J growth characterized as the core constrained-RK4 drift
(~35 mJ per loaded tick) after the positional correction was EXONERATED by ablation
(GAIT_NO_POSCORR: byte-comparable leak, identical tick-118 refusal) and the clamp-pin
path measured zero (wave4, wave5 addendum); E8 booked at 57 µJ (wave5). Under the
mechanisms the residual scales with the violence of the trajectory: 2.999892 J
(wave7), 3.441343 J (wave9), 30.202201 J (wave11), 37.870489 J (wave8_trunk_vault),
43.183718 J (wave10 no-contact run, with brake heat 86.847731 J dominant and
constraint work correctly 0.0 with contact disabled). The books themselves are
consistent (bal == stor at every tick) — the leak is in the shared mechanical terms
(wave4). The standing rule from wave 4 still governs: "a broken meter cannot tune a
walk" — but note the campaign has since measured anyway, treating the ledger as a
recorded red rather than a blocker, per wave 5 ("a meter over a crashing body
conflates book errors with physics").

### 4.3 The posture-cap price tag (OPEN)

The periodic vault is inadmissible at the current caps (combined ratio 1.322776 at
phi=0.85, wave10), and the posture motor saturates during the table's transitions
(11.21250 N·m cap hit, wave9). What raising the caps would COST is unnamed: wave 4
established that no rescale is derivable from the admitted data alone (the GRF closure
identity pins the hindlimb share at 1.0, so a static-capable walker needs either the
quadruped forelimb load path or "a cap amendment with NEW provenance (named, not
derived today)") (wave4). The price tag — which cap, raised to what, with what
provenance, falsified how — has not been written. The trunk-vault table's own
multi-basin caveat (wave8) and wave 9's verdict ("the next membrane is a
reachability-constrained vault trajectory, not another local contact membrane")
delimit it: wave 10 ran exactly that membrane and it failed (wave10).

### 4.4 The quadruped window (OPEN at the dynamic layer)

The statics say the biped does not NEED forelimbs (§3.7); the share statics say
forelimbs buy real monotone fixed-pose relief but not the predicted <0.6 (§3.9); and
the one dynamic quadruped measurement (wave 11, s=0.45) refused at 291 on positional
correction after the fore contacts lifted, with the fore-cap falsifier intact (the
3.76 N·m doc-derived cap is never to be raised away; demands beyond it are banked as a
red finding, wave11). The window between "static relief is real" and "dynamic
four-contact walking works" is unmeasured. Wave 12 (planted struts) is the current
occupant of this window; the s-bisect at 0.25/0.45/0.55 is pre-registered behind it
(wave11).

---

## 5. The meters — what to run, what to read

**The falsifier suite F-G1..F-G8** lives in `ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp`,
with its definitions in `docs/research/20260918_gait_controller_derivation.md`:
F-G1 trajectory envelope (±5°, ≥95% of samples after 3 cycles), F-G2 duty/phase
(0.68 in [0.63,0.73], offset 0.50±0.02), F-G3 GRF envelope (1.08 BW ±10%, closure),
F-G4 per-drive energy within budget, F-G5 free fall/stand fold (controller off),
F-G6 push/capture reflex, F-G7 bit-identical determinism, F-G8 ledger closure
(impl receipt; derivation doc).

**Compile the scene** (derives everything from the store; nothing hardcoded):

```
python -B -m tools.science_funnel.gait_scene     # -> .tmp/gait-walker/scene.json
```

**Build and run the suite** (receipt.json reproduce list; wave receipts):

```
cmake -S ChimeraEngine/engine/tests_coupled_arm -B .tmp/gait-tests
cmake --build .tmp/gait-tests --config Release --target gait_unit gait_unit_trace
.tmp/gait-tests/Release/gait_unit.exe .tmp/gait-walker/scene.json        # the suite
.tmp/gait-tests/Release/gait_unit_trace.exe .tmp/gait-walker/scene.json  # the traces
```

`gait_unit_trace` is the same file compiled with `GAIT_EVENT_TRACE`
(`ChimeraEngine/engine/tests_coupled_arm/CMakeLists.txt`); `gait_unit_noposcorr_trace`
compiles with `GAIT_NO_POSCORR` — the positional-correction ablation target used by
wave 4 (wave4, wave5).

**The named traces** (all under `GAIT_EVENT_TRACE` in gait_unit.cpp):
- `[pt]` — every 10 ticks, per contact point: `cop_x`, `cop_y`, `gap`, `touching`,
  `reaction_N`, `slip_speed_m_s`. Introduced wave 5 (gap/touching/reaction/slip),
  extended wave 7 with the migrating-CoP position reported under both endpoint names;
  the active sole reaction is booked once on the heel representative so the GRF sum
  does not double-count (wave5, wave7).
- `[ledger10]` — every 10 ticks, the full energy books (KE, grav, work, damp, imp,
  fric, brake, ext) — the instrument that localized the wave-4 leak and identified
  brake heat as the wave-10 dominant term (wave4, wave9, wave10). `[ledger]` lines add
  first-breach and growth markers.
- `[trunk]` — phase, angle, target, torque, speed of the posture drive; added in wave 9
  (the trunk-vault lane could not add it — its harness file was outside that lane's
  boundary), and it is the instrument that caught the cap-saturated transition (wave9).

**The derivations** (pure-Python, rerunnable, each tied to its receipt):
`derive_gait_zeros.py` (wave 1), `derive_stance_hold.py` (wave 4), `derive_trunk_pitch.py`
(wave 8 in-session), `derive_trunk_vault.py` (wave8_trunk_vault, emits
`trunk_vault.json` consumed by gait_scene.py), `derive_reachable_vault.py` (wave 10),
plus `derive_quadruped_share.py` on `buffy/quadruped-share-20260919` (quad-share
receipt). Read them before trusting any statics number; the MP-Jacobian correction
(§3.6) is the known trap.

**Graph tests** (both PYTHONPATH roots; the count matches every wave receipt since
wave8_trunk_vault):

```
PYTHONPATH="<repo root>:<repo root>/tools" python -m pytest -q tools/creature_graph/tests
# -> 19 passed, 27 subtests passed
```

(Verified green on this branch's worktree at synthesis time. The wave-1-era count of
"33 OK" is the historical figure; the current pytest reports 19 tests / 27 subtests /
46 assertions — wave8_trunk_vault reconciles the two counts.)

---

## 6. The honest ledger — what was falsified and reverted

The campaign's value is as much in what it refused to keep. Three entries are the
named ones; the rest are recorded so the next agent does not re-pay for them.

1. **The caps amendment — banked, measured, FALSIFIED, REVERTED** (wave5). Revision 3
   banked the rescaled caps (knee 6.64 → 13.18, ankle 7.40 → 9.01 N·m, provenance =
   1.25× our assembly's measured quasi-static demands). The pre-registered falsifier
   fired: the walk refused identically — tick 118, fall depth y=0.1345 vs 0.1343 with
   the old caps; the caps were never binding. Reverted per the membrane's own law (the
   admitter detects the banked state and restores the source-peak caps with the
   falsification recorded in the contract note); store rebuilt, baseline confirmed
   (tick 118, ledger 3.593, F-G7 bit-identical).

2. **The segment-angle premise — falsified at model selection** (receipt.json; impl
   receipt). The implementation lane's declared segment-angle mapping (absolute
   angles, 0 constants) composed the 21-node tables into a 72° nose-up heel-dig at
   phi=0 (impl receipt, root cause 1); wave 1's measurement put the segment premise at
   47.1 mm stance ride vs the winner's 5.8 mm — falsified, and the joint frame shipped
   instead. The related degenerate premise (mixed hip-absolute + knee/ankle zeros,
   7.0 mm) was measured, disclosed, and not shipped (receipt.json).

3. **The mirror pairing — falsified as an identification law** (commit f7ddbd07,
   `tools/science_funnel/data/morphosource_ct/identify_bones.py` +
   `bone_identification.json`). The pre-registered bilateral law (mirror within 3 mm
   about the mid-sagittal plane, 5% length agreement) refuses 20-22 of 23 bones per
   specimen: both CT specimens are curled infants, so contralateral limb bones do not
   mirror. Honest negative recorded: mirror pairing is inapplicable to curled
   specimens; shape classification or manual annotation is owed. This commit sits in
   this branch's history between waves 6 and 8 (it is the trunk-vault lane's base,
   f7ddbd07).

Recorded alongside them, falsified but RETAINED (kept as laws or banked findings, per
their receipts):
- The stop-priority tier law: implemented in wave 2, honestly did NOT fix tick 40
  (the winning masks were already stop-inclusive); retained as the correct enumeration
  law (wave2).
- The clamp-pin "fix" of wave 4 was a no-op (u_pin computed before the wall snap =
  identically zero); the real order bug was found and fixed in wave 5, and the
  clamp branch's measured contribution to the walk is zero (wave5).
- The wave-4 MP windlass "load" (7.8-8.4 N·m) was a Jacobian artifact, corrected in
  wave 8 (§3.6) — a measured claim un-measured by a bug fix (wave4, wave8).
- The premise "the long no-contact vault+settle run is a gait" — falsified by Part A
  of wave 10 (duty 1.0/1.0, no TD pairs, falling) (wave10).
- The premise "forelimb sharing delivers hind ratio < 0.6" — falsified by the
  quad-share statics (0.9858 at s=0.4) (quad-share receipt).
- The single-support entry + settle combination (refused 66, both feet penetrating) —
  superseded by TD entry + settle (127) on measurement (wave8).

---

*End of synthesis. Nothing in this document is a new claim; every number above is
quoted from the cited receipt. The next measurement belongs to wave 12 (§4.1), and
its falsifiers are already written (wave11).*
