# The Walk Campaign Synthesis, Second Edition — waves 13 through 32 (2026-09-21)

Append-only synthesis document, the successor to the first edition
(docs/research/20260919_walk_campaign_synthesis.md on `agent/walk-campaign-doc`; that
file is untouched and remains the canonical record of waves 1-11 with wave 12 in
flight). This edition organizes what the campaign's receipts already record from
wave 12's verdict through wave 31's bank; it contains no new claims and no new numbers.
Every claim cites the receipt it came from. A new agent should be able to inherit the
whole arc from the first edition, this page, and the cited receipts without
re-deriving anything.

The campaign's discipline did not change: every wave banked a STATEMENT / PREDICTION /
FALSIFIER triple before building, measured after, and recorded red as red. Every wave
receipt below banks a false pass verdict — the walk has still never passed its own
falsifier suite (waves 30/31 record `pass` null at the top level and false in the
measurements block) — and the campaign advanced anyway, on banked rungs. That is the
shape of this edition: 291 ticks at the top of the ladder, 307 at the bottom, and a
biped question closed twice over in between.

## 0. The receipts (the citation key)

All wave receipts live at `tools/science_funnel/validation/gait_zero_20260919/`;
data-program receipts at the paths shown. Canonical fetch pattern:
`git show <branch>:<path>`.

| Cited as | File | Branch @ tip (short sha) |
|---|---|---|
| (first edition) | `docs/research/20260919_walk_campaign_synthesis.md` | `agent/walk-campaign-doc` |
| (wave12) | `receipt_wave12.json` | `agent/gait-wave12-planted-struts` @ e7dce7e2 |
| (wave13) | `receipt_wave13.json` | `agent/gait-wave13-stepping-struts` @ 554f40ed |
| (wave14) | `receipt_wave14.json` | `agent/gait-wave14-entry-pose` @ b5886451 |
| (wave15) | `receipt_wave15.json` | `agent/gait-wave15-level-entry` @ c3db49cd |
| (wave16) | `receipt_wave16.json` | `agent/gait-wave16-load-strut-trade` @ 47d30cb4 |
| (wave17) | `receipt_wave17.json` | `agent/gait-wave17-seat-law` @ c03ddf41 |
| (wave18) | `receipt_wave18.json` | `agent/gait-wave18-partial-lean` @ 17936d83 |
| (wave19) | `receipt_wave19.json` | `agent/gait-wave19-leaned-entry` @ 74fc0195 |
| (wave20) | `receipt_wave20.json` | `agent/gait-wave20-midentry-replant` @ 5c94fb4b |
| (wave21) | `receipt_wave21.json` | `agent/gait-wave21-hind-ride` @ 8a17c500 |
| (wave22) | `receipt_wave22.json` | `agent/gait-wave22-touch-reset` @ 17b6bdde |
| (wave23) | `receipt_wave23.json` | `agent/gait-wave23-joint-wall` @ 3cf3674c |
| (wave24) | `receipt_wave24.json` | `agent/gait-wave24-glide-pocket` @ ecddf6eb |
| (wave25) | `receipt_wave25.json` | `agent/gait-wave25-gate-cadence` @ 40811bdd |
| (wave26) | `receipt_wave26.json` | `agent/gait-wave26-wall-wait` @ 6efb3ef0 |
| (wave27) | `receipt_wave27.json` | `agent/gait-wave27-sinking-shoulder` @ d981bc04 |
| (wave27b) | `receipt_wave27b.json` | `agent/gait-wave27b-posture-sink` @ d907f888 — NOT on canonical; carried byte-identical on THIS branch (blob b0f56bb4) |
| (wave27c) | `receipt_wave27c.json` | `agent/gait-wave27c-decay-seats` @ 4198dbdc |
| (wave28) | `receipt_wave28.json` | `agent/gait-wave28-hind-step` @ 0557fc99 |
| (wave28b) | `receipt_wave28b.json` | `agent/gait-wave28b-load-share` @ 0759f4b2 |
| (wave29) | `receipt_wave29.json` | `agent/gait-wave29-alternation` @ ab60a20b — carried on THIS branch (blob b1de13b8) |
| (wave30) | `receipt_wave30.json` | `agent/gait-wave30-knee-demand` @ 5ff710f2 — carried on THIS branch (blob f0c35a2b) |
| (wave31) | `receipt_wave31.json` | `agent/gait-wave31-glide-return` @ 5b5c1b13 — carried on THIS branch (blob 4a428c41) |
| (torque book) | `tools/science_funnel/validation/hind_torque_book_20260921/receipt.json` | `agent/hind-torque-book-20260921` @ b17cbf6c |
| (ankle arms) | `tools/science_funnel/validation/ankle_arms_20260921/receipt.json` | `agent/ankle-arms-20260921` @ b15ff31e |
| (caps statics) | `tools/science_funnel/validation/measured_caps_statics_20260921/receipt.json` | `agent/measured-caps-statics-20260921` @ eab707f5 |
| (ankle unblocked) | `tools/science_funnel/validation/ankle_unblocked_statics_20260921/receipt.json` | `agent/ankle-unblocked-statics-20260921` @ 90636814 |
| (re-hearing) | `tools/science_funnel/validation/rehearing_20260921/receipt.json` | `agent/measured-caps-collocation-20260921` @ 4347f152 |
| (k forensics) | `tools/science_funnel/validation/k_forensics_20260921/receipt.json` | `agent/k-scale-forensics-20260921` @ 5a5914b3 |
| (deposit mass) | `tools/science_funnel/validation/deposit_mass_20260921/receipt.json` | `agent/deposit-mass-forensics-20260921` @ 5f54a161 |

The four carried receipts were copied byte-identically (git blob shas verified equal to
the original lanes' `HEAD:<path>` blobs) because their branches had not been pushed to
canonical at synthesis time; their citation lines name the original branch and commit
for the lineage. Lane genealogy, from the receipts' own `lane`/`base` fields: wave 12
based on wave 11 (f0efbba7); 13 on 12; 14 on 13; 15 on 14; 16 on 15; 17 on 16; 18 on
17; 19 FORKED from wave 17's head (c03ddf41 — wave 18's lean authoring was retired by
its own falsification and is not inherited, wave19); 20 on 19; 21 on 20; 22 on 21; 23
on 22; 24 on 23; 25 on 24; 26 on 25; 27, 27b and 27c all raced from wave 26's head
(6efb3ef0); 28 and 28b from wave 27's head (d981bc04); 29 on 28; 30 on 29; 31 on 30
(wave12..wave31 `base` fields). The wave-12/13 scene-sha discipline became the
campaign's standing proof standard from wave 22 on: regenerate the scene
byte-identically, reproduce the parent's refusal tick and ledgers verbatim, then and
only then edit (wave22..wave31 `base` fields).

## 1. The coverage contract (Rule 0-lite, pre-registered)

Before this document was written, its claims-vs-receipts coverage table was
pre-registered: every section below names the receipts it may cite, and no section
cites outside its row. The pre-registration is part of the working record of this
lane; the table's count is 30 receipts (23 wave receipts + 7 data-program receipts)
plus the first edition. The document's own falsifiers: every number in it appears in a
cited receipt (spot-checked against the raw receipt files before commit); no claim
without a citation marker; the first edition untouched.

---

## 2. Where the first edition left us

The first edition closed with wave 12 in flight: planted fore struts, the named target
of tick 426, the s-bisect pre-registered behind it (first edition §4.1). Wave 12's
receipt is now banked, and it FALSIFIED its membrane (wave12): the 2-DOF analytic
closure itself was exact (1e-16 m FK round-trip; a world-frame formulation falsified
and replaced by the pelvis-frame law the same day), but the body out-walks the
world-fixed paw plants — reach annulus hit at ticks 114/122, 176/291 ticks saturated,
tracked paw error 0.314 m, worst forepaw gap 4.22e-2 m — and the walk refused at tick
291 with worst ledger 30.776609 J. The pre-registered load-share falsifier fired as a
finding, not a tuning prompt: the bisect is FLAT in fore share (291/291/291 at s =
0.25/0.45/0.55, s=0.55 bit-identical to s=0.45; the failing joint, trunk_pitch_HAT
saturated + hind heel poscorr, identical) — load share does not modulate a
reach/topple failure (wave12). The next membrane was inherited by wave 13: make the
plants step (wave12, wave13).

## 3. The ladder continues — one rung per refusal

The walk-refusal ticks, in wave order, from the receipts' `refusal` fields. The
ladder is the spine of this edition the way it was of the first.

| Wave | Mechanism | Refusal tick (budget) | What the wave banked |
|---|---|---|---|
| 12 | world-fixed planted struts | 291 (poscorr; flat in s) | the plants must step; load share does not own a reach failure |
| 13 | stepping struts, two runs | 290, then 120 (impact budget) | the stepping law vindicated on its own terms; the entry pose doubly starved |
| 14 | derived entry fore pose (standing pin) | 30, before the capture | exactly two poses exist under the seating pin; the forward branch cannot settle |
| 15 | the level entry | 180, twice | the strut law derived and validated; the level reset UNLOADS the fore pads |
| 16 | the load/strut trade + hind reset repair | 110 (contact_impact_gain honesty require) | branch A infeasible at derivation (lever clamps to 0); the hind reset repaired |
| 17 | the seat law (containment), two runs | 49, then 41 | the seat's statics true and built to the micron; the balanced entry has no load path |
| 18 | the partial-lean tip | 40 | the fold dominates: the static razor edge never binds in the run |
| 19 | the leaned entry, reconciled | 82 | the entry clause PASSED its direct test; the known-risk double-swing killed the run |
| 20 | the mid-entry re-plant | 80 | zero both-fore-airborne windows; the chase law corrected (torque-limited) |
| 21 | the hind ride (reflex arming law) | 80, unchanged | the reflex exonerated: the death is invariant to it |
| 22 | the touch-reset law | 83 | slam census zero; the ladder moved for the first time in three waves |
| 23 | the joint walls | 84 | zero loaded pins; the [0,65] proof standard; the actual-side dive named |
| 24 | the glide pocket (joint-admissible hold) | 99 | the wall-bound glide's transit is joint-inadmissible; the pocket-clear hold shipped |
| 25 | the gate's cadence law | 97 (regressed 2, honestly recorded) | contact-truth scheduling shipped; the starvation dive re-attributed to the actual |
| 26 | the wall-adjacent wait override | 105 | the override fired at exactly its arithmetic tick; the ladder advanced 8 |
| 27 | the height-hold feed-forward (27a) | 122 | the sink decomposed onto the base drop; the arrest bought 17 ticks |
| 27b | the posture-sink race (candidate b) | 105, verbatim | the posture lever falsified AND causally sealed (0.000 mm) |
| 27c | the decay-aware seats (candidate c) | 105, identical | falsified at derivation; the seat census shipped as instrumentation |
| 28 | the hind step law | 298 (contact_impact_gain) | +176 ticks, the campaign's largest single advance |
| 28b | the load-share map (race-C bank) | no run (map on the 27 baseline) | the honest negative: the share collapse is designed, servo-authored, geometry-forced, lever-less |
| 29 | the hind alternation + lift-first glide | 298 base; 288 (A); 299 (B) | the fold is a joint-CAPACITY death, not scheduling; the fold budget mined at 45 |
| 30 | the standing knee's demand side | 299 (bracket 282, GATED-ON-K) | the fold is demand-subrail at the fold tick; demand-relief is life-shortening |
| 31 | the glide-return law | 299 -> 307 | the replant became a touchdown; the unload-lift deadline banked as wave 32 |

F-G1/F-G2/F-G3 (trajectory envelope, duty/phase, GRF closure) remain UNMEASURED
through wave 31 — every life stayed under the 649-tick F-G1 window mouth; each
receipt carries the honest NOT MEASURED row (wave13..wave31 falsifier scoreboards).
The always-green battery held everywhere it was measured: F-G5 free fall at
-9.806650 m/s² exact (wave13..wave31), F-G7 determinism bit-identical with plain and
trace binaries byte-equal (wave22..wave31 report byte-equality explicitly), the
creature-graph suite green (19 tests through wave 26; 37 tests at wave 27's count —
wave27), and the fore-elbow ceiling never exceeded (measured peak 0.30 N·m against
the doc-derived 3.76 N·m, wave13).

## 4. The entry's solution arc (waves 13-19)

**The statics purifications that shortened the walk.** Waves 13-19 are one arc: each
wave purified one more entry-statics quantity — reach (13), pose (14), strut height
(15), load (16), seat (17), trunk moment (18) — and each purification, though derived
true and built to spec, SHORTENED the walk: the ladder fell monotonically
291 -> 290/120 -> 30 -> 180 -> 110 -> 49/41 -> 40 (wave13..wave18 run fields; the
ladder as wave19 states it). The structural lesson, banked by wave 18 and named by
wave 19: this walker's entry is carried by the LEANED composition's load path, and the
best run so far was still wave 11/12's tick 291 — the original entry (full vault lean
theta*(0) = -0.2064, the back fore pose, the fore seat) whose lean pressed the fore
pads and whose walk phase, not entry, owned the death (wave19).

- **Wave 13 — the stepping struts.** The fore clock steps each paw ahead of the
  walking shoulder by the symmetric-reach offset x_off = v*t_stance/2 on the hind
  period and duty. Run 1's falsifiers caught a real derivation blunder — the entry
  stance violated the derivation's own annulus inequality (51/56 saturated ticks,
  refusal 290). Run 2 enforced it (one implementation repair, no tuning): 0/0
  saturated ticks, true-stance paw band clean to 7e-6 m, IK closure exact to ~1e-15,
  and the ledger peak COLLAPSED 30.78 -> 1.714904 J over the shorter life — but the
  envelope-bounded entry lifted both fores within 3.8 ticks of each other, the front
  lost its entire reaction path, and the storm refused at 120. Front support outweighs
  reach in the entry (wave13).
- **Wave 14 — the entry pose is over-determined.** The compile-time seating pin
  admits exactly TWO fore poses (the pad-flat + 2e-6 seating equations; the back
  branch reproduces the wave-12 pose to 6e-5 rad), the measured settle fold transfers
  -0.095 m of capture offset regardless of the authored pose (the soft servos fold
  -51.7 -> -84.3 deg around the planted pads while the pads slip only 1.1 mm), so the
  forward branch's capture lands at -0.019 m and the run dies at tick 30, before the
  capture. The strut-height difference at the leaned entry is 0.205*d(x) — it depends
  only on the paw's forward position (wave14).
- **Wave 15 — the strut law.** D(lean) = the TD-side hind heel's raw height minus the
  seat's lowest raw height, measured on the Assembly at three leans, validated against
  the wave-14 runtime tick-0 gap to 9e-5 m: D(0) = 4.6162e-2 m (in band, margin
  1.28 cm), D(-0.2064) = 1.05190e-1 m, slopes +0.2840 leaned / +0.2081 nose-up per
  rad — theta_e = 0 is the derived unique minimum, admissible band theta_e >=
  -0.0449. Built: the settle strut storm was gone, the capture FIRED (the first past
  the wave-14 branch), and the run still refused at 180 — the level reset leaves the
  fore pads UNLOADED (tick-0 fore reactions 1.92+3.28 N decaying to 0, slip
  0.79 m/s; the body tips BACKWARD, CoM 0.117 m behind the hind line) (wave15).
- **Wave 16 — the load/strut trade and the hind reset.** Branch A (the trade on the
  assembly the runtime actually assembles) is infeasible AT DERIVATION: with the right
  hind stuck at the 1.0==0.0 TD column the lever law clamps the fore reaction to 0
  across the whole band (no lean reaches even the 5.199 N slide ceiling). Branch B
  executed the owed hind-reset repair — the right hind moved to its 0.5 clock column,
  verified to 0.07 mm. The run refused at 110 on gait_contact_impact_gain: an HONESTY
  require in the impact solver (a sliding contact's discrete-cone solve produced
  share_n/share_t above tolerance) — a real accounting refusal, banked as the
  next lane's known terrain (wave16).
- **Wave 17 — the seat law.** The seating pair is the pair whose support polygon
  CONTAINS the CoM with margin: the hind pair contains it (margins 0.203/0.196 m;
  statics ratio 0.584 on reactions 52.42/46.02 N), the fore pair fails at -0.32 (the
  wave-16 measured tip-over). Built to the micron in both runs (the L heel at the
  seat: 2.016e-6 / 2.000e-6 m) — and refused at 49 and 41 with NO saturated joint
  (the L knee folded to -64.9 deg from its -31.6 deg target at only 2.81 of
  6.6375 N·m): the seat's statics are true and the balanced entry still has no load
  path (wave17).
- **Wave 18 — the partial-lean tip, and the fold's dominance.** The exact
  single-support trunk moment on the Assembly is the contact-frame gravity moment,
  tau == W*(x_com - x_heel) (machine-checked identity at 1e-9): 11.2024 N·m at level
  = 0.9992 of the posture cap, relieved to 10.526 at theta_e = -0.015309. Derived,
  built, refused at 40 — and the falsification upgraded the structure: the razor edge
  NEVER BINDS IN THE RUN. The velocity-level entry opens in free-sink (tick-0 hind
  reaction 35.7 N < W; tick-0 posture demand 3.774 N·m, three times below the static
  value), and the hind PDs fold under the settle's load ramp at a
  geometry-independent rate — the pitch trajectory is identical at lean 0 and at
  theta_e, and the passive lean's 0.6875 N·m of static relief bought minus one tick
  of life (wave18). This is §11's first named honest red.
- **Wave 19 — the leaned entry, reconciled.** Forked from wave 17 (wave 18's lean
  authoring retired by its own receipt), rebuilt the 291-class composition on the
  corrected assembly. ITS ENTRY CLAUSE PASSED ITS DIRECT TEST — the press (>= 5.199 N
  total) arrived by tick 10, the capture fired at 60 with offsets -0.2294/-0.2246 m
  and settle-exit speed v = 0.607 m/s — and the run refused at 82, inside the
  pre-registered KNOWN RISK window: the behind capture's envelope bound cuts both
  entry stances to 8.9/11.1 ticks and the machine's own lifts fired at 68/71 into the
  double swing. The banked successors: derive the settle-exit's SPEED (what sets v at
  the arm), and the landing-tick law — the landing tick is dangle over the body's
  sink rate at the seat (the R hind's measured 2.06 mm/tick replaces the carried
  1.53) (wave19).

## 5. The fore machinery (waves 20-26)

With wave 19's entry clause proven, waves 20-26 built the fore machinery the walk
phase needed, one law at a time, each verified by the proof standard (the [0,65]
trace fence line-identical, named ticks exact) before its own verdict was read.

- **Wave 20 — the mid-entry re-plant.** The entry clock law changed from "hold to
  the envelope, then swing" to "hold to a derived re-plant point, then step forward
  with minimal air time under a no-double-swing gate." The derivation closed exactly:
  t_air = ceil((T_CYCLE - DUTY_SAMPLED)/dt_) = ceil(8.1) = 9 ticks, independently
  equal to the coverage bound 9.146 (agreement to 0.15 ticks). Measured: ZERO
  both-fore-airborne windows (the wave-19 death mechanism structurally removed),
  every named tick landed, and the walk still refused at 80 — the pre-registered open
  risk (fold + hind skid) kills independently of the fore clause. The step-law bands
  went RED on both runs, honestly, and the corrected law was banked: the entry step's
  achieved advance is TORQUE-LIMITED and target-speed-independent, ~1.27 mm/tick x
  t_air with a +/-2 mm leg residual (measured L1 +11.5 mm) — the baseline's
  slow-glide chase band was the wrong error term, and the falsifier caught it.
  Consequence banked: at v = 0.607 the offsets PIN near the annulus and the body
  rides its hinds; the refusal tick is noise under the fold (80 vs 82) (wave20).
- **Wave 21 — the hind ride, and the reflex's exoneration.** Rule-1 mining found the
  capture reflex's arming test ran on the lexicographically sorted point cloud
  instead of the monotone-chain convex hull: the tick-65 fire armed on a pseudo-edge
  (+0.0046 m "outside") while the true hull held the CoM strictly INSIDE. The rebuilt
  three-clause arming law (true-hull containment; swing-clock phase; the 0.2089 m/s
  slip cone) removed the spurious fires — capture_events 2 -> 0, the phase-0.95
  fingerprints gone — and the death did not move: refusal tick 80 and worst ledger
  0.291120 J IDENTICAL with and without the reflex. The reflex was NOT the walk's
  root; the pre-registered skid and fold predictions were falsified on the same run
  (2.030 m/s at tick 78; 14 negative-pspd ticks in [65,79]) (wave21). §11's second
  named honest red.
- **Wave 22 — the touch-reset law.** The two touch classes separate by FOUR ORDERS OF
  MAGNITUDE on both signatures: legitimate touchdowns arrive from departure depths
  6.5e-2 / 1.17e-1 m and close 1.951e-3 / 1.210e-3 m in their final tick, descending
  and loaded; the killer graze (tick 64) excursed 1.6e-7 m above the band edge. The
  shipped classification (kTouch 1e-5; kStab 1e-6; kReleaseBand the solver's own gap
  quantum; HOLD state between) produced a zero slam census, kept the pre-registered
  known-good list (L@40, R@55 LEGIT), and the ladder MOVED for the first time in
  three waves: 80 -> 83, at a new named fore-side cause (wave22).
- **Wave 23 — the joint walls.** The wave-22 death held its TARGET inside the joint
  range (shoulder margin 0.0467 rad) while the ACTUAL sat 0.0511 rad below it — the
  capped servo's loaded deflection — so the in-place re-plant's advance loop pinned
  a planted leg against the joint wall (64 pins at drive 8, tick 83). The hold law
  gained the joint-wall guard; the census split pins LOADED/AIRBORNE; zero loaded
  pins through the life including the refusing step; the [0,65] fence measured
  2991 lines, 0 diffs. Refusal 84 (wave23).
- **Wave 24 — the glide pocket.** The pocket map (exact IK replica verified to
  <0.01 deg) proved the wall-bound glide's world line transits a branch-(-1)
  JOINT-RANGE HOLE: all nine per-tick line points joint-inadmissible (q1u -1.945..
  -2.433 through the mid-swing shoulder wall; q2u +1.085..+2.682 through the elbow).
  The three candidates were derived against the map: the pocket-arc (no above-ground
  corridor exists at any pocket-column dx), the branch-flip (the +1 branch exits at
  the elbow immediately past the seat, q2 up to +5.1), and the re-time (sprint clause
  rejected on the mined rates) — the surviving clause SHIPPED as the pocket-clear
  hold. The run moved 84 -> 99, both wall-bound glides transited pin-free
  (swing_wall_touches (0,0)), and the new face was named: the R's gate-held
  starvation dive [89,99] (loaded (0,123), airborne (0,18)) (wave24).
- **Wave 25 — the gate's cadence law.** The wave-24 death decomposes into
  gate-and-bookkeeping holds: the no-double-swing gate's clause (a) counted the L
  "airborne" through its HELD glides [83,91]+[94,99] although the held pads were LIVE
  (gaps 1e-6..3e-6, in-band, touching). The shipped contact-aware clause (a) gates
  only a TRUE airborne glide; the cadence falsifier was derived, not tuned — planted
  span <= floor(kWallMargin / dive_rate) = floor(0.0511/0.0039) = 13 ticks — and the
  baseline measured RED on it (the R's [81,99+] span) as the separation test demands.
  The run REGRESSED 2 ticks (99 -> 97) and the receipt says so verbatim: the law
  works on its own face and the run still regressed; the dive re-attributed to the
  ACTUAL side (wave25).
- **Wave 26 — the wait override.** During the R's lawful gate-held wait [83,91] the
  R's ACTUAL dove hr 0.026927@81 -> 0.000000@89, and the wave-23 follow's target
  restores did NOT restore it — the follow's convergence premise is measured FALSE
  under load. The shipped mechanism (candidate (c), the early-step override; (a) the
  weight-shift micro-unload rejected on the recovery arithmetic, (b) the hind-side
  stance shift rejected on the phase arithmetic) arms kWaitFloor = 2*kDiveRateMax
  over the mined kDiveRateMax and lifts early. The override fired at EXACTLY its
  pre-registered crossing tick 88 (hr 0.005897 < 0.008040 <= 0.009348@86), the hold
  armed with last=8, and the ladder advanced 8 ticks: 97 -> 105 (wave26).

## 6. The height law and the sink races (27a/b/c)

Three lanes raced from wave 26's head on one measured death: the assembly's vertical
collapse — the R shoulder sink 0.113737@60 -> 0.042536@104 = -71.2 mm — decomposes
EXACTLY into the base drop -78.4 mm (110%) plus the pitch coupling +7.2 mm (-10%,
the measured pitch rise already SOFTENS the sink); the base drop itself is the hind
chain's loaded fold (wave27, wave27b).

- **27a — the height-hold feed-forward (the race winner).** The shipped law latches
  a height emergency at a derived crossing (fire at tick 75: sh_min margin 39.3 mm
  <= the 39.75 mm floor, live rate 0.416 m/s) and feeds the hind drives forward with
  ff = last_torque/kp on the pads-live ticks, against named constants kSinkRateMax =
  0.002349 m/tick (the baseline's own worst) and the kHeightFloor. The posture/
  load-shift candidate was rejected on MEASUREMENT (the trunk drive is railed at its
  exact cap 11.2125 with a growing 16.4 deg deficit — no posture authority exists),
  and the decay-aware-seats candidate on the F-G23 march's own verdict. The arrest
  bought +17 ticks (105 -> 122) at a priced cost: worst ledger rose 0.291120 ->
  0.987027 J (the arrest's ~20-tick double-saturation transient books real actuator
  work; window-caveated, reported, never tuned) (wave27).
- **27b — the posture-sink race, and the 0.000-mm seal.** Candidate (b) held that
  the posture table's slow trajectory owns the sink. The derivation measured the
  closed form sh_y = base_y + 0.2689*sin(theta) - 0.1331*cos(theta) (empirically to
  -0.06..-0.46 mm), the lever dsh_y/dtheta = +0.25195..+0.25265 m/rad, and the
  decomposition [88,104]: -32.58 mm = -32.58 (base) + 1.07 (posture) — WRONG SIGN,
  +3.3% of the sink; the command channel delivers +1.08 mm over the whole death
  window against a -32.6 mm sink (30.3x too small, opposite sign; tracking gain
  0.02401 with the servo railed from tick 82). The causal seal: the refined
  zero-table intervention (walk-window nodes frozen at +0.0171 rad, entry-consuming
  nodes 0,1,2,19,20 byte-exact; the blunt strip was VOID — the entry consumes the
  table and refused at 40) left the dynamics BIT-IDENTICAL — [0,90] line-identical,
  first divergence exactly tick 91 in the command print only, EVERY shoulder tick
  0.000 mm apart on both legs, the refusal at 105 verbatim, the output JSON
  byte-equal. An 8.57-degree command change; 0.000 mm of dynamics. The negative is
  SEALED with its completeness argument: demanding more nose-up keeps the rail;
  demanding less un-rails only toward nose-down; the shoulder's height is
  base_trans_y, an UNDRIVEN base DOF (wave27b). §11's third named honest red.
- **27c — the decay-aware seats, falsified at derivation.** Candidate (c) would
  re-anchor the machinery's admissible seats to the live shoulder transform each
  tick. Four measured legs closed it BEFORE shipping (a scratch probe evaluated the
  machinery's own IK on a 0.25 mm ground-line grid at every live tick), the candidate
  seat law was NOT SHIPPED, and the lane's lasting contribution is instrumentation:
  the seat-region census (F-G27's seat face — the 2401-point ground-line scan with
  per-tick region width) shipped read-only, with the full-life line-identity proof
  (4725/4725 trace lines, 0 diffs) and every parent number byte-identical (wave27c).

The sink races' combined bank, handed to wave 28: the arrest's horizontal ground path
is the next death — the body's advance outruns the hind schedule (wave27, wave28).

## 7. The hind gait (28-31)

- **Wave 28 — the hind step law (+176).** The hinds received the replanting
  machinery the fores earned (the wave-20 minimal-air-time pattern on the hind
  clock's own lateral grid). The death it owned, mined engine-natively: the hind
  clock's lift slot fires into a STALL — at phi >= TOE_OFF the pads are still live
  and loaded (gap 2.4e-6 m, reaction 62.2 N at t=98), the swing columns pull the
  joints against the planted paw, the ankle reaches its wall (0.0032 rad at 120), the
  paw skids (1.2455 m/s at 121) into the budget refusal at 122. The calendar was
  pre-registered and landed on its named ticks (the R's fire at 98, TD at 107 — the
  tick wave 29's fold-budget mining anchors on). Refusal 298:
  THE LADDER ADVANCED 176 TICKS (122 -> 298), the campaign's largest single advance,
  at the priced ledger 30.139317 J (the [226,298] airborne-collapse transient's real
  actuator work; window-caveated) (wave28).
- **Wave 28b — the load-share map (the honest negative).** The race-C bank ("the
  sink-grown LOAD is the diver") mined the full load map on the byte-reproduced
  wave-27 baseline through a scratch probe proven dynamics-free by byte-equality. The
  fore share's collapse (9.4%@60 -> 28%@80 -> 10.3%@100; the hinds carry ~90% and
  fold) is (1) DESIGNED (the wave-8 vault transfer, h = -0.1487 m/rad), (2)
  SERVO-AUTHORED (the split is the two equilibria's bargain, 93.5 pp off the static
  line), (3) GEOMETRY-FORCED at the endgame (the recede flattens the fore legs onto
  their walls; their load decays below 0.5 N with pads closed, then the pads lift —
  the unload precedes the lift), and (4) LEVER-LESS (the vault channel sealed x0.024
  and height-capped; the hind-table channel is fence-confined; the seat channel
  measured closed). No amendment path fired; the negative is the bank (wave28b).
- **Wave 29 — the alternation, and the three-point capacity proof.** The fold budget
  is MINED, not geometric: the R's TD 107 to the touch law's own release at 152 =
  45 ticks (kFoldBudgetTicks, the kSinkRateMax precedent) — the kinematic envelope
  read 143 ticks where the death came at 45, so the fold is CAP-LIMITED DYNAMICS.
  The L's natural slot (~204) is outside the budget; the deadline arithmetic (the
  other's TD + 45 - t_air - g, the wave-20 tau1 form hind-side) put the lawful fire
  window at [108,142]; the [hindgate] per-decision instrument proved NO lawful
  promise exists in that window (both fores' stance remainders negative — the churn
  regime), so the deadline override fired at EXACTLY its arithmetic tick 142. THE
  THREE-POINT PROOF, one baseline, three fires: no L fire (wave-28 baseline) ->
  refusal 298 with the L's forced liftoff at 152; the L's fire at 108 (BUILD A) ->
  288; the L's fire at 142 (BUILD B) -> 299 with the fold resuming FOUR TICKS after
  the L's own replant (155). The hind step moves the PAW; it does not restore the
  JOINT's load capacity — the fold is a joint-capacity death, and no fire timing owns
  it (wave29). The lift-first glide amendment shipped green at its own letter:
  swing-start drag 0 ticks, worst slip 0.0374 m/s against the baseline's 1.8674 (the
  mined drag face: the pad cleared at the fire, sagged 1.4 mm under the 4.8 m/s
  haul, re-entered the band at 104) (wave29).
- **Wave 30 — the standing knee's demand side, and the demand-relief paradox.** The
  new [dvq] instrument (per-tick per-hind-drive {torque, cap}, proven stdout-inert
  three ways) measured the demand curve the banked wave-4 table predicted as
  bimodal: band A exits at phi 0.2778, the static valley runs to the re-cross at
  phi* = 0.42844, and the fold's first tick 155 reads phi 0.4507 — the fold tick IS
  the binding node's crossing tick. THE MEASUREMENT FALSIFIED THE PREMISE: the L
  knee's rails are the arrest transient [77,117] and it reads 12.6% OF CAP with
  rxn = 0 at the fold's resumption — the fold is DEMAND-SUBRAIL; the R's rails are
  the replant transients [88,97] and [108,128]. The k-gated bracket made it a
  paradox: at the muscle-book knee cap 9.576795 (1.44x, GATED-ON-K, scene-only) the
  refusal moved EARLIER, 299 -> 282, the fold's first tick to 133 — the higher cap
  lets the servo track the designed valley columns, which unload the standing pad
  early, and the deadline fire lands airborne. The demand-relief direction is
  life-shortening (wave30). The table lever was derived to closure (sensitivity
  -13.0611 N·m/rad; the correction +0.051228665336 rad passed all five
  pre-registered checks) and the BUILT amendment falsified the fence — the reset's
  phase-slope speed seed probes phi 0.45 with weight 0.9, so node 9 is entry-coupled
  (divergence at tick 0, the settle dead at 41); the revised fence-legal domain
  {7,8} cannot reach the binding band (2%/0% interpolation weight); the lever was
  dead three ways and REVERTED, the shipped tables re-verified as the wave-29 bytes
  (wave30).
- **Wave 31 — the glide-return, and the falsified pin.** The wave-30 bank (the L
  pads never re-enter the touch band: 11.5 mm at the 151 replant event, 56 mm by
  200, rxn 0 — the replant is a CLOCK event with no touchdown) got its anatomy:
  the PIN-STALENESS hypothesis was FALSIFIED (the plant pin is the liftoff height
  re-captured at every fire; pin error 0.0100 mm — the touch gap itself; the body
  recovered 7.2 mm since the capture; fire-time IK closure 4.441e-16) and the
  DELIVERY owns the miss (the pad tracked the arch's rise to 0.1-0.3 mm then
  under-tracked the commanded descent monotonically, +1.4 -> +10.4 mm, the
  haul-dominated rate). The shipped law holds the plant point (the glide's own sg
  clamp; zero new constants) until the pair-min gap <= kTouch, and ONLY then
  completes the replant — the replant became a TOUCHDOWN. The numbers landed on the
  pre-registration: completion at 160 (predicted 160 +/- 6), held 9 ticks [151,159]
  inside the 21-tick kinematic ceiling, descent accelerating 13.13 -> 1.24 mm, rxn
  growing to 42 N, the two-legged ride resumed, the fold class pushed 155 -> 162
  past the resumption, the fence green in full ([0,65] 2970/0; first divergence
  EXACTLY tick 151). And one new face, honestly mined: the L's landing UNLOADED the
  R (rxn 0 by 161), the unloaded R's feed-forward lifted its pad out of the band at
  161, and the R was STRANDED AIRBORNE (its 195 deadline and ~252 slot both require
  touching pads) — one-legged to the impact budget's refusal at 307. REFUSAL
  299 -> 307: THE RUNG IS BANKED (the death class changed; worst ledger improved
  32.861605 -> 30.265367 J); the wave's own support falsifier fired honestly
  (min_legs 1, 14 sub-2 ticks in [142,163]) (wave31). §11's fifth named honest red
  (the pin) is here; the wave-32 bank is §8.

## 8. The wave-32 line (IN FLIGHT, not yet receipted)

No `receipt_wave32.json` exists at synthesis time (verified by file listing across
the canonical branches and the local chain; the wave-32 worktree sits at the wave-31
head 5b5c1b13 with nothing banked). The bank is wave 31's own: THE UNLOAD-LIFT
DEADLINE — the second hind's fire window is bounded by its own unload face (the
receipt measures ~1 tick past its share's vanish), not by the other's 45-tick fold;
the alternation must fire the standing hind at/before the landing, and the deadline
arithmetic must take min(the other's last_td + 35, the standing leg's own unload)
(wave31). The campaign's standing rule applies: until a receipt exists, wave 32 is a
named target with pre-registered falsifiers, not a result.

## 9. The biped's closure — the data program and the re-hearing

While the quadruped ladder climbed, a parallel program audited what the walk's caps
are made of, and it closed the first edition's oldest open question — the quadruped
window (first edition §4.4) — from the biped's side, twice independently.

**The doc-cap audit (torque book).** Every live hind cap is DOC-DERIVED STATICS:
hip 11.2125 / knee 6.6375 / ankle 7.4 / MP 0.8875 N·m = 1.25 x the DOC-ROUNDED Oku
measured walk peaks (exact 8.9746 / 5.3144 / 5.9171 / 0.7051) — measured Oku numbers
processed through a doc rounding and a derived 25% headroom, with NO musculature
behind them; the wave-5 assembly-statics amendment was banked, measured, falsified,
and restored (not live); 71 audit entries, none unaccounted (torque book). The
muscle book then re-derived the caps from measured arms (the pulley lane's deposit
arms) at measured Oku walk forces: knee 9.576795 N·m (1.44x the live cap), MP
1.657925 N·m (1.87x); the PCSA x sigma provisional variants 36.247782 / 4.636664
(5.46x / 5.22x); every pre-registered sign and band HELD, determinism byte-exact
across three runs (torque book).

**The ankle cell.** The torque book's one BLOCKED cell — the ankle, whose admitted
record's straight-line arms fall 1.8-3.7x short of the measured walk demand 5.9171
N·m — was closed by the ankle-arms lane: the angle-direction measured arm curve
gives the measured ankle caps (plantarflexion 6.247077 N·m at the Oku walk peaks,
covering the demand at 1.0558x; triceps-only subenvelope 5.318868 = 0.8989x, the
coverage carried by FDL's inclusion; provisional 18.595726; the S2 collapse
0.748112; dorsiflexion 1.251106 per the sign gate the downstream receipts pin), and
the k gate held on its own class: k_ankle = 0.11976026, inside the pre-registered
MTP-class spread (torque book, ankle arms).

**The statics reversal.** The measured-caps lane re-ran the wave-4 stance-hold
statics BYTE-EXACT (the banked table's own generator vendored and executed
unmodified; the one pre-registered pin fired on exactly 6 MP cells and was resolved
by consuming the generator — the MP-Jacobian fix carried as a named variant under
which the windlass flags VANISH 0/15) and re-priced the verdicts at three cap sets:
knee over-cap nodes 9 -> 4 -> 0 of 15 (worst 2.0711 -> 1.4354 -> 0.3793; entry
1.0960 -> 0.7596 -> 0.2007), and the wave-10/25 margin wall CROSSES 1.0 under the
measured caps: 1.322776 (a, knee-bound at phi=0.75, the wave-10 deliverable's own
banked max reproduced as identity) -> 0.977235 (b) -> 0.977235 (c), the binder
migrating knee -> ankle (caps statics). THE REVERSAL: wave 4's statics said the caps
cannot hold the poses and "the walk needs momentum, not bigger caps" (first edition
§3.7, citing wave 4); at the measured knee/MP caps the statics REVERSE — the stance
table's knee binding vanishes (0 of 15 under (c)) and the wave-10/25 wall CROSSES 1.0
for the first time (0.977235 under both (b) and (c)). But the margin stayed honest:
the 0.9 margin is UNREACHABLE at the banked optimum under every set (at (a)-(c) the
ankle plus the 0.9-posture saturation own it), and the fourth set closed the door the
crossing opened: with the MEASURED ankle (set (d)) the crossing REVERTS — the ankle
goes over-cap at 6 of 15 stance nodes (worst 1.154940 at phi=0.3), the wall
re-prices to 1.157587 ankle-bound at phi=0.5, while the dorsal class holds at
0.987926 — 98.8% of the measured dorsal cap (ankle unblocked). The
book's own wall prose (0.9112/0.785) was recorded as resolving to NO banked
artifact, never tuned to match (caps statics).

**The re-hearing — the trajectory-level closure.** The statics lane's crossing left
one open door (F6: maybe a different trajectory re-opens the biped under (d)). The
re-hearing shut it by measurement: the wave-10 collocation optimizer, re-run at the
measured (d) caps with the vendored generator reproduced to the LAST DIGIT (PR1:
max_ratio 1.3227763257041534 and objective 0.894190750157879 exactly, the written
file BYTE-EQUAL to the pinned deliverable), finds NO admissible trajectory — minimum
achievable wall 1.155776 over three independent starts (warm-start 1.157112,
fresh-wave8 1.157055), every run ankle-bound, every run above the maximin LOWER
BOUND 1.042502 at phi=0.4 (registered 1.043892 +/- 0.004, refined IN BAND; a bound
that closes the question regardless of what the optimizer finds). The mechanism:
at phis 0.30-0.45, shifting the ankle load saturates the UNCHANGED hip cap before
the ankle clears its measured cap — at the bound node hip 1.04250 and ankle 1.04250
co-bind exactly — so the (d) re-block is a property of the ENVELOPE. VERDICT: the
measured-caps biped is CLOSED at the trajectory level and the QUADRUPED LINE STANDS
ALONE at S1 (re-hearing). PR4's theta-shift sub-prediction fired and was recorded
(registered -0.72 in [-1.0,-0.3]; measured -0.075119694 — the wave-10 mean-of-maxima
objective does not drive the node-wise minimax shift); the CLOSED verdict stands on
the bound plus the runs, and PR6's determinism chain repair is recorded in the
receipt, falsifier-honest (re-hearing).

**Two independent closures.** The biped is closed on MUSCLE grounds and on
MEASURED-ARMS grounds, and the two closures do not share a binder: at the LIVE DOC
caps the wall is 1.322776, knee-bound at phi=0.75 (the wave-10 deliverable's own
banked face, reproduced as an identity by two independent lanes, caps statics and
re-hearing); at the MEASURED-ARMS caps the wall is 1.157587 ankle-bound in statics
(ankle unblocked) with the trajectory envelope closed under it at 1.042502 (the
re-hearing's bound). Whether the caps are bookkeeping (doc-derived) or muscle
(measured), no admissible bipedal vault exists at this body's mass distribution and
inertia set — and the quadruped line is not a convenience anymore; it is the only
standing architecture at S1 (re-hearing).

**The k-gate, stated.** Every verdict above carries the scale gate: S1 stands on the
DEPOSIT arm scale; at the SI-matched scale (arms x k = 0.11975394, the pulley lane's
fitted per-taxon scalar) the books collapse (knee 1.146859, MP 0.198543, ankle
plantar 0.748112) and EVERY S1 verdict INVERTS (S2 walls 9.642983-9.661652 over the
maximin bound 8.435635 at phi 0.4) — no engine consumption is lawful until the
operator resolves the deposit-vs-SI absolute-scale divergence (torque book, caps
statics, ankle unblocked, re-hearing). The forensics that framed the gate: the
k-forensics lane measured the sha-pinned Zenodo meshes (4/4 byte-exact vs the
committed manifest) — femur max length 173.13 mm / tibia 156.81 mm, both INSIDE the
adult-female year-mean ranges of the Cayo Santiago skeletal series (Francis & Wang
2023, 635 mature specimens: femur 158.92-175.21, tibia 146.47-161.64 mm; males
178.36-207.39 / 165.06-184.45) — the deposit IS anatomically scaled, an adult-female
rhesus; the SI's k-implied scales are absurd in BOTH unit readings (SI-in-mm gives a
20.73 mm femur and a ~10.3 g implied mass, FETAL class, impossible for the source of
measured adult walk data; SI-in-cm gives 207.33 mm, the top of the adult male range
against a female-band deposit); the angle columns are 26/26 IDENTICAL
(scale-invariant) and only the length columns diverge, at 8.35x; the SI package
carries ZERO absolute-scale anchors; a single global unit artifact is FALSIFIED by
the three per-taxon constants. Force evidence, not verdict: deposit-scale arms cover
the measured adult walk at all three joints (ankle 1.0558x); SI-scale arms collapse
it (0.1264x ankle; 0.17x knee / 0.22x MP) (k forensics).

**The mass smoking gun.** The deposit-mass lane measured the anomaly that makes the
scale divergence a body problem, not a units problem: the Wiseman macaque model's
pelvis + both hindlimb chains sum to 0.7717839 kg against an expected
0.997-1.656 kg for an adult female rhesus (hindlimb chains 18.5-24% of body mass by
both literature anchors — the Oku/Ogihara CT model 0.1847 and Zihlman dissection
0.20-0.24 — on a 5.4-6.9 kg body), a REAL deficit of 1.29-2.15x before the pelvis is
even counted; the set is not a uniform stamp (masses carry 5-7 decimals; L/R
thigh/shank/toes byte-equal), not k-scaled (neither the linear nor the cube-law
arithmetic closes — the cube law demands a 449.393 kg template class), and its
bilateral anomaly is measured (foot_l = 10.897259x foot_r) (deposit mass).

## 10. The instruments — the campaign's reusable legacy

The meters the second edition built (each named first in the receipt cited):

- **Trace lines** (all stderr, GAIT_EVENT_TRACE-only, each proven stdout-inert by
  byte-equality before its data was used): the wave-5/7/9 lines [pt], [ledger10],
  [trunk] (first edition §5); [body] and the [ik] trace (wave12, wave13); [foreclk]
  — the fore clock's arm offsets and mode transitions, the wave-14/15 capture-equation
  instrument (wave15); [dv]/[dvp]/[dvj]/[dvf] — the wave-23 mining family whose lines
  ARE the [0,65] proof-standard fence (wave23, and every fence thereafter);
  [hindgate] — the wave-29 per-decision instrument that enumerated every lawful fire
  candidate (wave29); [dvq] — the wave-30 per-tick per-hind-drive {torque, cap}
  print, the demand-census instrument (wave30); [hindstep] — the wave-31 hold-return
  print (wave31).
- **The falsifier census suite, F-G14..F-G29** (the first edition's F-G1..F-G8
  continued; each defined in its naming receipt): F-G14 support census (wave14,
  dual-reading wave25); F-G15 strut census (wave15); F-G16 pair-min census (wave18);
  F-G17 hind tick-0 load (wave17, cited wave18); F-G19 hind_landing status edge
  (wave22); F-G20 replant-run disjointness (wave20, cited wave21); F-G21 fold census
  (wave21, cited wave22); F-G23 joint-wall pins + admissibility (wave23); F-G24
  glide admissibility + law conformance (wave24); F-G25 cadence spans (wave25);
  F-G26 wall-adjacent wait/headroom (wave26); F-G27 the height census of 27a
  (wave27) — its name carried by 27c's seat-region census, the SEAT CENSUS: the
  2401-point ground-line admissibility scan at the live state, shipped read-only
  (wave27c); F-G28 hind-step census (wave28); F-G29 alternation census (wave29);
  and the f30_*/f31_ demand and touchdown censuses (wave30, wave31).
- **The scratch-probe pattern** (wave28b): a byte-copy of the harness plus read-only
  per-tick prints, proven dynamics-free by byte-equality of its stdout against the
  plain run on two scenes — the instrument class that let 27b/27c/28b measure without
  touching a source byte (wave27b, wave27c, wave28b).
- **The proof standard** (wave22 and every receipt after): scene regenerated
  byte-identically (sha recorded twice), parent refusal tick and ledgers reproduced
  verbatim, the [0,65] trace fence line-identical, THEN the verdict numbers.

## 11. The honest-reds ledger — the falsified predictions that taught the most

The first edition's rule stands: the campaign's value is as much in what it refused
to keep. The five named falsifications of this edition, each with what it taught:

1. **The fold's dominance over the statics (wave18).** The derived razor edge was
   real and exact — 11.2024 N·m at level, 0.9992 of the posture cap — and it never
   bound: the run opens in free-sink (tick-0 hind reaction 35.7 N < W, tick-0 posture
   demand 3.774 N·m, 3x below static), the pitch trajectory is IDENTICAL at lean 0
   and at theta_e, and the lean's static relief bought minus one tick. Taught: in
   this velocity-level entry, quasi-static feasibility is not the binding physics;
   the servo fold under the load ramp is.
2. **The capture reflex's exoneration (wave21).** The arming law was a real repair
   (spurious fires 2 -> 0; the pseudo-edge hull test fixed) and the death did not
   move — refusal tick 80 and ledger 0.291120 J byte-identical with and without the
   fires. Taught: the death triad's tick-ordering was measured before the fix, and
   the reflex was a symptom-carrier, not the root; "fix the machinery the walk
   misuses" is not "fix the walk."
3. **The 0.000-mm intervention (wave27b).** The posture-table hypothesis survived a
   30.3x lever deficit on paper until the intervention sealed it: freeze the
   walk-window table nodes (an 8.57-degree command change) and every shoulder tick
   is 0.000 mm apart, the refusal verbatim, the output JSON byte-equal. Taught: a
   railed servo makes its command channel a NO-OP — the causal test is the
   intervention, and the sealed negative (base_trans_y is an undriven DOF) is what
   pointed wave 28 hind-side.
4. **The demand-relief paradox (wave30).** The k-gated bracket at the 1.44x knee cap
   SHORTENED the walk (299 -> 282, fold first tick 133): relieving the standing
   knee's demand let the servo track the valley columns, which unload the standing
   pad early and strand the deadline fire airborne. Taught: in a coupled gait the
   demand curve is not a wish list — capacity interacts with scheduling, and a
   bigger cap can spend the ride.
5. **The pin falsification (wave31).** The pin-staleness hypothesis (the plant pin
   frozen at the settle era) predicted the return miss; the measurement gave the pin
   error 0.0100 mm and handed the miss to delivery (+1.4 -> +10.4 mm of under-track
   against a 13.1 mm peak). Taught: decompose before you legislate — the shipped law
   (hold to kTouch) cost zero new constants because the anatomy, not taste, picked it.

Recorded alongside them, banked as honest negatives and findings: the flat bisect —
load share does not modulate a reach failure (wave12); the entry-stance annulus
violation the wave-13 falsifiers caught in their own derivation (wave13); the
step-law bands RED as committed, producing the corrected torque-limited chase law
(wave20, re-confirmed wave21, trajectory-dependence named wave22); the fore-load
lever clamping to 0 at derivation (wave16); and the lever-less load-share map
(wave28b). No red was tuned away; every correction above traces to a falsifier that
fired on its own pre-registered letter.

## 12. The meters — what to run, what to read

The standing commands are the first edition's (first edition §5): compile the scene
(`python -B -m tools.science_funnel.gait_scene`), build and run the suite
(`gait_unit` / `gait_unit_trace` under
`ChimeraEngine/engine/tests_coupled_arm`), the graph suite on both PYTHONPATH roots,
and the derivation scripts under `tools/science_funnel/validation/gait_zero_20260919/`
— now including the entry-arc derivations (derive_entry_pose.py, derive_level_entry.py,
derive_leaned_entry.py, derive_load_strut_trade.py, derive_seat_law.py,
derive_height_hold.py) and the wave-28b mining pair (derive_load_map_wave28b.py,
derive_share_lever_wave28b.py) (wave14..wave28b file listings). Read the derivations
before trusting any statics number; the MP-Jacobian correction remains the known trap
(first edition §5), and the caps-statics lane's P1 finding adds the operational rule:
pin the GENERATOR commit, not the script head — the banked table's generator is
724f2464 (caps statics).

New since the first edition: the trace instruments of §10 (turn on GAIT_EVENT_TRACE
and read [dvf]/[dvq]/[hindgate]/[hindstep] for the fore wall, knee demand, fire
decisions, and glide returns), the scratch-probe pattern for read-only mining
(wave28b), and the data-program books with their pinned-input refuses —
`hind_torque_book_20260921/`, `ankle_arms_20260921/`, `measured_caps_statics_20260921/`,
`ankle_unblocked_statics_20260921/`, `rehearing_20260921/`, `k_forensics_20260921/`,
`deposit_mass_20260921/` under `tools/science_funnel/validation/`, each with a
receipt whose falsifiers re-run from the pinned shas (torque book..deposit mass).

---

*End of the second synthesis. Nothing in this document is a new claim; every number
above is quoted from the cited receipt. The walk still refuses — 307 ticks, the
impact-event budget, one hind stranded airborne by its own unload — and the next
measurement belongs to wave 32 (§8), whose falsifiers are already written
(wave31).*

Agent: GLM 5.3
