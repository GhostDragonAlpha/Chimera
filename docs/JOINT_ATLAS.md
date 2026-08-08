# THE JOINT ATLAS — the irreducible mathematics of the human body

> **THE ATLAS RULE (operator law, 2026-08-08):** no row enters on the model's
> say-so. Every joint's DoF, axis geometry, and range carries a pointer to RAW
> data — a dataset file, a measurement table in a primary paper, a mocap
> sequence. Textbook summaries and model memory are LEADS, never sources.
> Anything the raw data does not cover is marked **UNKNOWN**. Every
> irreducibility claim carries a sign-off box for the operator (THE HUMAN
> terminal). Sources are fetched and read before they are believed;
> `VERIFIED LIVE` means the artifact URL returned the artifact on the date
> noted.

---

## 0. THE IRREDUCIBLE LAYER — sign-off requested

CLAIM: every joint in the human body (and every mechanism, human or
inorganic) is one of six **lower pairs** (Reuleaux, 1876), and all six are
one mathematical object: a **subspace of the 6-D rigid-body velocity space**
(3 rotations + 3 translations). A joint = "which velocities are allowed."
The constraint math of any joint = the basis of its allowed subspace and of
its reciprocal (forbidden) subspace. Screw theory is the unifying formalism:
one screw axis per allowed motion, pitch coupling rotation to translation.

- [ ] OPERATOR SIGN-OFF: the six-pair set is the atomic joint set

| Pair | Allowed motion | DoF | Math (allowed subspace) | Human instances |
|---|---|---|---|---|
| Revolute (R) | 1 rotation, fixed axis | 1 | v = ω·S | fingers (IP), elbow (humeroulnar) |
| Prismatic (P) | 1 translation, fixed axis | 1 | v = t | none pure in the body |
| Screw (H) | 1 rotation + coupled translation (pitch h) | 1 | v = ω·(S + h·t) | **the knee** (screw-home; moving axis) |
| Cylindrical (C) | 1 rotation + 1 translation, one axis | 2 | span{ω·S, t} | radioulnar (forearm twist) |
| Spherical (S) | 3 rotations about a point | 3 | span{ωx, ωy, ωz} at p | hip, glenohumeral |
| Planar (F) | 2 translations + 1 rotation, one plane | 3 | span{tx, ty, ωz} | intercarpals, facet joints (spine) |

Traps the naive table hides (recorded, not smoothed over):
- **The knee is not a hinge.** The cruciate ligaments form a four-bar
  linkage; the instantaneous axis MOVES through flexion and couples tibial
  rotation (screw-home). Modeling it as a revolute is an approximation with
  a known, measured error — UNKNOWN: the pitch curve vs flexion angle from
  raw data (cadaveric kinematics literature; not yet fetched).
- **Condyloid/ellipsoid joints** (wrist, knuckles) are 2-DoF universals with
  surface-coupled translation — a universal pair plus a rolling constraint,
  not a clean lower pair.
- **The thumb CMC is a saddle** — 2 DoF on a hyperbolic-paraboloid surface;
  the two axes are NOT orthogonal intersecting lines but surface principal
  curvatures.
- **The spine is not a joint.** Per-segment small 3-DoF motion sums to the
  curve the operator named (datum 5); the facet pair is the atomic unit.

---

## 1. THE VERIFIED RAW SOURCES

| # | Source | What it is | Status |
|---|---|---|---|
| S1 | **ISB Joint Coordinate Standards** — Wu et al. 2002, Part I (ankle, hip, spine), *J Biomech* 35:543-8, [PubMed](https://pubmed.ncbi.nlm.nih.gov/11934426/); Wu et al. 2005, Part II (shoulder, elbow, wrist, hand), *J Biomech* 38:981-992, [PDF](https://media.isbweb.org/images/documents/standards/Wu%20et%20al%20J%20Biomech%2038%20(2005)%20981%E2%80%93992.pdf) | The international standard: the local axis system for every articulating bone and the rotation decomposition per joint. THE math-of-joints document | Part II PDF **VERIFIED LIVE 2026-08-08** (572 KB). Part I located (PubMed); PDF not yet fetched |
| S2 | **Rajagopal 2016 full-body OpenSim model** — [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC5507211/), model free at simtk.org/home/full_body; mirror `.osim` [here](https://raw.githubusercontent.com/wwrzesien/squat-analysis/master/Rajagopal2015.osim) | Machine-readable XML: 37 DoF joint definitions (coordinates, axes, ranges) + 80 muscle-tendon units, parameters derived from **21 cadaver specimens + 24 MRI subjects** | `.osim` mirror **VERIFIED LIVE 2026-08-08** (753 KB). simtk.org requires registration; mirror is a third-party copy — checksum against simtk original pending |
| S3 | **CMU Motion Capture Database** — [mocap.cs.cmu.edu](https://www.roboticscenter.ai/datasets/cmu-mocap) | 2,605 sequences, 144 subjects, walk/run/balance/dance; BVH/AMC/C3D; free for all uses, direct download | Located; direct-download URL not yet fetched |
| S4 | **AMASS** — [amass.is.tue.mpg.de](https://amass.is.tue.mpg.de/license.html) | 40+ hours, 11,000+ sequences, 15 datasets unified in SMPL pose parameters | Academic license, **requires registration** — friction; prefer S3 first |
| S5 | **Measured standing-balance norms** — [Winter 1998 stiffness control](https://pubmed.ncbi.nlm.nih.gov/9744933/); [Suzuki 2012 intermittent control](https://www.sciencedirect.com/science/article/pii/S0022519312003062); walking ankle moment ~0.8 N·m/kg [Nature 2021](https://www.nature.com/articles/s41598-021-02059-8.pdf); ankle torque capacity 150–216 N·m [McErlain-Naylor 2017](https://www.stuartmcnaylor.com/publication/Thesis/McErlain-Naylor_2017.pdf) | The load/sway envelope the servo must live inside: sway ~1 cm, ankle-torque-primary below 1 Hz | Papers located; quantitative tables not yet fetched |

---

## 2. THE JOINT ROWS (v0 — every row awaits fetch + sign-off)

Format: joint · pair · DoF · axis/geometry source · range source · status · sign-off

### Lower limb
- [ ] **Hip** · spherical · 3 · S1 Part I + S2 (`hip_flexion_r` etc.) · S2 · SOURCES LOCATED
- [ ] **Knee** · screw (four-bar, moving axis) · 1 (+ coupled rotation) · S2 (knee_angle with coupled tibial translation) · S2 · SOURCES LOCATED — screw-home pitch curve UNKNOWN
- [ ] **Ankle (talocrural)** · revolute (oblique axis through malleoli) · 1 · S1 Part I + S2 · S2 · SOURCES LOCATED
- [ ] **Subtalar** · revolute, oblique (~42° inclination, ~16° deviation — textbook numbers, RAW SOURCE NEEDED) · 1 · UNKNOWN primary source · **UNKNOWN**
- [ ] **MTP (toes)** · condyloid, windlass-coupled · 2 (1 dominant) · S1 (foot recommendations limited) · arch/windlass mechanics UNKNOWN

### Spine and head (operator datum 5: ankle→spine(curve)→hip→neck(leads))
- [ ] **Lumbar facet (per segment)** · planar, small range · 3 small · S1 Part I (spine JCS) · per-segment ranges UNKNOWN
- [ ] **Atlanto-axial (neck pivot)** · revolute · 1 (rotation) · UNKNOWN primary source
- [ ] **Atlanto-occipital** · condyloid · 2 (nod) · UNKNOWN

### Upper limb
- [ ] **Sternoclavicular** · saddle · 3 · S1 Part II · SOURCES LOCATED
- [ ] **Acromioclavicular** · planar · 3 · S1 Part II · SOURCES LOCATED
- [ ] **Glenohumeral** · spherical · 3 · S1 Part II + S2 · SOURCES LOCATED
- [ ] **Scapulothoracic** · constrained plane on ribcage · 3 · S1 Part II · not a true articulation — modeling choice, SIGN-OFF NEEDED
- [ ] **Elbow (humeroulnar)** · revolute (carrying-angle oblique) · 1 · S1 Part II + S2 · SOURCES LOCATED
- [ ] **Radioulnar (proximal+distal)** · cylindrical pair · 2 · S1 Part II · SOURCES LOCATED
- [ ] **Wrist (radiocarpal)** · condyloid/universal + roll · 2 · S1 Part II + S2 · SOURCES LOCATED
- [ ] **Thumb CMC** · saddle · 2 · S1 Part II · SOURCES LOCATED
- [ ] **Finger MCP / IP** · condyloid 2 / revolute 1 · S1 Part II · SOURCES LOCATED

---

## 3. THE EXTRACTION PLAN (what we pull from the raw data)

From S2 (.osim XML, machine-readable, no registration): every joint's
coordinate list, axes, and ranges → a `joint_atlas.json` the skeleton spec
can DIFF against (the kernel's `joint_dof`/`joint_axes` vs measured
anatomy, row by row; every mismatch gets a verdict, not a patch).
From S1: the standard axis definitions those numbers mean.
From S3: motion the joints actually perform (sway envelopes, gait cycles).
From S5: the load envelope the servo must live inside.

Expansion (operator's directive): the same six-pair table covers inorganic
mechanisms verbatim — it was born there (Reuleaux, machine kinematics).
The atlas schema does not change; only the rows do.

## 4. NEXT FETCHESES (awaiting operator clearance)
1. S2 `.osim` → extract joint coordinate table (no registration needed).
2. S1 Part I PDF (ankle/hip/spine axes).
3. S3 CMU walking + standing sequences (direct download URLs).
4. S5 quantitative tables (sway mm, torque N·m/kg, frequencies).

## 5. KERNEL DIFF VERDICTS (atlas vs LightEngine skeleton spec)

**VERDICT 1, 2026-08-08 — the kernel's mass distribution is a design-load
scaffold, NOT anthropometry.** `skeleton_spec.py:165-177`
(`_normalize_mass`) derives link masses from `design_load_kg` in the
skeleton-scaling table — its own docstring admits "load_fraction ... is a
design load, not a true mass fraction."  Measured against the atlas
(de Leva 1996 adjusted Zatsiorsky-Seluyanov,
`external/atlas/anthropometry.json`, male):

| region | kernel (77 links, 80 kg) | de Leva male | ratio |
|---|---|---|---|
| feet | 14.7% (11.8 kg) | 2.6% (2.1 kg) | **5.7× too heavy** |
| head | 0.4% (0.3 kg) | 6.9% (5.5 kg) | **0.06×** |
| arms | 1.8% | 9.9% | 0.18× |
| thighs+shanks | 13.0% | 39.4% | 0.33× |
| trunk+pelvis | 70.2% | 43.5% | 1.6× |

Consequence chain (recorded, not yet re-run): the entire standing-fall
saga — foot whipping, the 1.18 kg forefoot kicked by 157 N/point springs,
the backward ratchet, the toe fold — ran through feet 5.7× heavier than
anatomy, a head 18× lighter than anatomy, and legs carrying a third of
their real mass.  The saga's measurements stand as measurements OF THAT
BODY; they do not transfer to an anatomic body.  Corrective named:
ANATOMIC-MASS membrane — redistribute the 77 links' masses onto the
de Leva segment table (map each link to its parent segment, split segment
mass across its links by link volume from the scaling table), then RE-RUN
the saga battery before any friction/servo conclusion is trusted.
Inertias: the kernel uses solid-cylinder formulas from the scaling table's
diameters (`_solid_rod_inertia`); the atlas carries radii of gyration per
segment — diff after the mass membrane lands.
Joint ranges: ankle in the .osim is [-40°, +47°]; the kernel spec's ankle
row range — UNKNOWN, not yet diffed.

**VERDICT 2, 2026-08-08 — mass distribution WAS a saga driver; the anatomic
body falls by a different clock (446, outside 1416-1429).** ANATOMIC-MASS
landed as `build_spec(mass_model="deleva")` (`skeleton_spec.py`:
`_DELEVA_PCT`, `_deleva_segment`, `_deleva_mass`; paired segments ×2 sides;
legacy `mass_model="design"` default bit-identical).  Battery
(`.tmp/probe_anatomic_mass.py`, ghost-free fr=2, MAIN 8000 + CONTROL 1500,
saga ruler `find_bounds(hz_all, 0.5*hz@100, side="below")`):
(a) distribution exact — worst group deviation 0.000 pp (bar 0.01);
(b) fall tick **446** — OUTSIDE the invariant 1416-1429 (same ruler);
(c) no simmer — max KE 3264 J, 0 samples >= 1e4 J;
(d) control falls — head_z 3.26 m sag over 1499 ticks.
Two mechanism reads, recorded not assumed: (i) the scaffold's 5.7×-heavy
feet were an anchor — the real body is top-heavier and falls SOONER;
(ii) the ratchet REVERSED SIGN: +208.5/+206.2 mm forward (scaffold:
-27 mm backward) — the ratchet is mass-distribution-sensitive, so every
ratchet/cliff verdict of the old saga is quarantined to the scaffold body
until re-run on this one.  Also measured: head_z @8000 = -50.8 m — after
the fall the body passes THROUGH the floor (contacts exist only on feet).
G0 world floor (every link collides) is now the blocking gap.

**VERDICT 3, 2026-08-08 — rod inertia: transverse HOLDS, axial is
bone-only (3-30× small).** Probe `.tmp/probe_inertia_diff.py` vs
Rajagopal2015 inertias (now merged into
`external/anatomy/rajagopal_extract.json`; axis semantics checked: atlas
long-bone frames are Y-long, kernel rod is [ix, ix, iz=axial]).
Transverse ratios (kernel/atlas): femur 1.67, tibia 0.81, humerus 1.49,
forearm 0.96 — all inside [0.5, 2.0]; transverse is the term that drives
swing dynamics, and the rod model earns its keep there.  Axial ratios
0.03-0.07 — the anatomical_diameter is bone-only; the atlas axial inertia
includes the flesh cylinder around the bone.  Absolute error is small
(axial is the small term) but wrong in kind; matters for twist DoFs
(hip rotation, spine torsion) when those get trained.  Foot group 0.17 —
a foot is not a rod; noted, not gated.  Segmentation cross-study note:
de Leva thigh (kernel 11.59 kg) vs Rajagopal femur_r (9.30 kg) — different
dissection boundaries, both recorded.

**FINDING (joint ranges) — the kernel has NO per-joint angular range
table.** Ligaments are rope-derived capture bands (`_build_ligament_specs`,
S_WALL..d_eq), not angular stops.  The atlas carries ranges for all 23
joints (e.g. hip flexion [-30°, +120°], knee [0°, +120°], ankle
[-40°, +47°], elbow [0°, +150°], subtalar [-20°, +20°], mtp [-30°, +30°],
lumbar ±90°×3, wrist flex [-70°, +70°]).  DoF classes DO match 1:1:
ball-cup=hip 3-DoF, hinge=knee/ankle/elbow PinJoint, saddle=wrist
UniversalJoint.  Open question (operator terminal): are angular stops a
membrane (derived from ligament geometry) or an atlas datum (typed in from
the table)?  Range enforcement is the operator's standing datum
("it's more like a range enforcement").

**VERDICT 4, 2026-08-08 — G0 WORLD-FLOOR: two falsifiers fired and named;
CONTACT-RECOVERY is the membrane under test.** G0 (every link carries
endpoint ground contacts, default-off `floor_links=True`, 154 records)
falsified twice on `.tmp/probe_world_floor.py` (anatomic body, ghost-free,
contact_friction=2, DROP servo-off 4000 + STAND servo-on 3000):
F1 STANDING COLLAPSE (head_z 0.013 m @2999) — the actuator-table
supported-side derivation (`muscles.py:238`) counted floor contacts as
feet, declaring the SMALLER TREE the grounded side and sizing every servo
to hold ~1 kg instead of the body above it.  Fixed with five side-"W"
filters (muscles.py, muscle_controller.py ×2, serve_standing_demo.py,
demo_kinematic.py): world-floor records are floor, never feet.  Legacy
bit-identical (44/44).
F2 THE PILE SINKS — DROP came to rest (KE 0.105 J) with **71/154
endpoints below -0.05 m**, deepest scapula_R dist **-0.357 m**, sinking
progressively through the crumple (first crossings ticks 560-1630;
shoulder girdle + arms pinned under the trunk).  Root cause named by
reading: the in-solve ground (`step_core_direct`) is a ONE-WAY VELOCITY
GATE — contact rows stop downward motion but nothing pushes a sunk point
back up (the penalty spring lives only in the sweep path); under
joint-chain crush the unilateral row's lambda goes negative, the
active-set ejects it as "liftoff", and the point re-gates deeper next
tick — a downward ratchet.  The naive cure is MEASURED-POISON:
position-level contact projection fought the joint projection over the
slop band and pumped 1->220 m/s in 100 ticks (position_pass NOTE,
2026-08-08).  Membrane CONTACT-RECOVERY: `row_bias = BETA *
min(depth, slop) / dt` on the contact rows — the kernel's own Baumgarte
idiom (mode-4 lock rows), solved SIMULTANEOUSLY with the joints so the
cross-pass fight has no structure, correction capped at one slop per tick
(the THETA_CLAMP argument), default-off `state["contact_recovery"]`.
RUN 2 outcome (same bars + NO-PUMP leg): **REST PASS (KE 0.097 J), NO-PUMP
PASS (KE max 324 J), sink IMPROVED but failing** — DROP rest -0.2495 m
(was -0.3568), min ever -0.3088, STAND -0.8266 (was -1.1477).  The
simultaneous-solve shape kills the pump; the slop-capped recovery
(0.26 m/s max) cannot lift a link the joint chain pins — at rest the deep
rows must be ejecting or statically balanced (a biased ACTIVE row cannot
be stationary).  Diagnostic `.tmp/probe_recovery_diag.py` (ejected vs
balanced vs working-slowly, named before the run) decides the next shape:
if EJECTED, recovery must work THROUGH the joint chain (lift the
connected support set), not through the single contact row.
DIAG OUTCOMES: capped-bias rows measured EJECTED at rest (clavicle_L
-0.245 m carrying 0-4 N, still sinking -0.245->-0.255 over 200 quiet
ticks; working-slowly and balanced both refuted).  The UNCAPPED diag
(BETA*depth/dt, 49 m/s target at depth) measured **every deep endpoint
RECOVERED to the slop surface** (+1-3 mm @4000, force bursts 50-60 N as
the pile breathes; T4 drifting to +31 mm = buoyancy overshoot) —
**ejection is NOT structural; the slop cap was the weakness**: a target
above the chain's pull-down keeps lambda positive and the row survives.
Run 3 = the full probe on the uncapped form; falsifier named: pump
(KE >= 1e4 J) -> cap by the derived spring period (T = 162 ticks),
never a sweep.
RUN 3 OUTCOME: falsifier fired in a different arm than named.  NO PUMP
held (KE max 383.8 J < 1e4) and NO SINK held (final min endpoint
-0.0008 m), but **REST failed (KE 4.896 J @3999, bar < 1.0) and NO
TUNNEL failed (min z ever -0.2127 m)**.  Reading: the uncapped
BETA*depth/dt is a launcher, not a lifter — at 0.21 m depth it
targets 42 m/s; the pile breathes forever and launched points
re-impact deep.  The failure is the one the named cure anticipated:
recovery must not outrun the spring it replaces.
RUN 4 = SPRING-PACED recovery (`contact_recovery=3`): v = depth/T
with T = 2*pi*sqrt(5*d_eq/g) = 0.162 s derived from k_contact
(dynamics.py `_contact_constants`, n = 5 support-polygon points).
Exponential settle, no launch.  Falsifier for run 4 named in
`.tmp/probe_world_floor.py`: REST jitter -> pace still wrong in kind;
crush-phase tunnel -> SPECULATIVE ACTIVATION (row enters when
z - v_z*dt < slop, derived from the point's own velocity).
RUN 4 OUTCOME: **the floor holds a dead body — DROP arm all four legs
PASS**: REST KE 0.224 J @3999 (run 3: 4.896), NO SINK -0.0132 m,
NO TUNNEL -0.0901 m (run 3: -0.2127), NO PUMP 339.9 J.  The
spring-paced lift is the right shape for an unpowered body.
**STAND arm leg (d) FAIL**: head_z @2999 = 0.020 m (the expected ~446
fall), but min endpoint z = **-0.3586 m** — with the standing servo
LIVE, endpoints tunnel far deeper than any drop.  Two candidate
mechanisms, distinguishable only by the force on the deep rows while
they sink: (i) EJECTED — motor+joint crush drives lambda negative and
the active-set sacrifices the contact row (F2's mechanism surviving
mode 3); (ii) OUTPACED — the row works (force present) but the servo
shoves the limb down faster than depth/T lifts, i.e. an actuator
domain violation (a standing servo has no domain in a fallen body —
the demo's push path already REFUSES outside the standing frame,
serve_standing_demo.py:98).  Diag `.tmp/probe_stand_tunnel_diag.py`
decides; the speculative-activation membrane waits on its verdict.
DIAG OUTCOME: **MIXED — the named falsifier fired**.  Over the sink
window, 62% of buried-point samples carried ~0 N (EJECTED) and 38%
carried force (WORKING); late-run the floor slowly wins once the
crush eases (min z -0.135 -> -0.081 over the last 360 ticks).  Both
membranes are implicated.  Order by physics: (1) **SERVO DOMAIN
REFUSAL** — the actuator fix, implemented 2026-08-08 in
`muscle_controller.apply` (opt-in `state["servo_domain_refusal"]`,
latched, same derived frame as the push path: COM inside the foot
polygon and h > 0; legacy bit-identical).  With the shove source
gone the post-fall body IS the proven DROP regime.  (2) if buried
rows still die with no live actuator: **PENETRATING-CONTACT
PRIORITY** — a penetrating row is never ejected; the bounded motor
rows absorb the residual (the floor is immovable, the muscle is
not).  Run 5 = the full probe with refusal on, STAND arm re-framed
into (d1) pre-fall floor safety and (d2) post-fall recovery
(`.tmp/probe_world_floor.py` RUN 5 triplet).
RUN 5 OUTCOME: DROP arm identical, all legs PASS (the refusal does
not touch the dead-body regime).  Fall tick 451; refusal latched at
tick 1181 (COM exited the foot polygon — anatomically late but
honest: you give up standing when your mass leaves your base).
**(d1) FAIL: min endpoint z -0.2867 m over [0, 451]** — the legs
crumple through the floor while the head is still up (the hz ruler
calls the fall by the head; the bottom of the body goes first).
**(d2) FAIL: -0.2202 m @2999**, 1.8 s after the servo quit — the
DROP arm recovered fully from the same floor in fewer ticks, so the
persistent killer is row ejection under the pile's own weight crush,
no servo needed: the diag's 62% signature.  The refusal membrane is
correct and stays (it ended the shove), but the remaining membrane
is the named one: **PENETRATING-CONTACT PRIORITY** in the active-set.
RUN 6 OUTCOME: the evidence partitions by REGIME.  **(d2) PASS
(-0.0246 m @2999, was -0.2202)** — retention lets the joint chain
lift a RESTING buried point; the named membrane is proven for the
quasi-static case.  **NO TUNNEL FAIL (-0.2132 m, was -0.0901 in
run 4)** and NO SINK hair-fail (-0.0506 m, 0.6 mm past the bar) —
retention during the violent CRUSH steals force authority from rows
that were holding; plain ejection handled impacts fine (run 4).
KE did not grow (0.253 J vs 0.224) — not a pump.  Reading: eject on
IMPACT, retain when STUCK.  Derived boundary (the same spring
timescale): a point sinking faster than the lift pace
(-v_n > depth/T) is an impact -> eject; otherwise it is stuck ->
retain.  Run 7 = REGIME-GATED priority.
RUN 7 OUTCOME: **the gate lands in a mushy middle on every axis —
the regime distinction is real but velocity-at-assembly does not
draw it**.  REST 1.038 J (marginal FAIL), NO SINK PASS (-0.0351),
NO TUNNEL FAIL (-0.1624 m, between run 4's -0.0901 and run 6's
-0.2132), (d1) FAIL -0.2262, (d2) hair-FAIL -0.0508 (run 6 passed
-0.0246).  During a collapse most points are quasi-static most of
the time while the pile still presses, so retention keeps taxing
the holding rows all the way down.  THE LESSON THAT CLOSES THE
BAUMGARTE LINE: any form that couples buried-point lift into the
shared K solve either starves the holders (retention, any gate) or
abandons the buried (ejection).  A real floor is not a shared
resource -- each point pushes back independently, force ~ depth.
That is a penalty spring, the candidate named-and-never-tried since
the run-2 falsifier.  NEXT MEMBRANE: **PENALTY-FLOOR** -- W floor
points routed to an independent per-point spring (k_contact
derived: body weight over 5 points compressing d_eq; per-point
critical damping c = 2*sqrt(m_eff*k) with m_eff from the K
diagonal), removed from the unilateral rows entirely.  Feet keep
the saga-proven in-solve path.
RUN 8 OUTCOME: **the spring's STRUCTURE is proven, its stiffness
regime is not**.  (d2) PASS +0.0004 m (every buried point back at
exactly the surface; it is not a row, so nothing ejects) and
NO SINK PASS -0.0002 m at rest.  But REST FAIL 7.773 J (the spring,
applied pre-solve, fights the joint projection across the tick
boundary), NO TUNNEL FAIL -0.1690 m (k is derived for the STATIC
standing load; crush forces run 5-25x static, so the spring yields
~17 cm before pushing back), refusal false-positive @84 (sagging
foot geometry quit the servo early; fall tick unchanged 448).
THE SYNTHESIS THE TABLE POINTS AT: the brake and the lifter are
different physics -- run 4's velocity GATE is the best impact
brake (-0.0901 m), run 8's SPRING is the best lifter (+0.0004 m,
never ejects).  They compose: the spring lifting a point reads as
positive normal velocity to the gate, which releases (liftoff --
correct); the gate brakes the crush in-tick while the spring lifts
underneath, so gate ejection under crush no longer abandons the
buried.  RUN 9 = GATE + SPRING: W endpoints back in the unilateral
rows with NO bias (pure gate), penalty spring active.
RUN 9 OUTCOME: **WORST ON EVERY AXIS -- the synthesis falsified
itself, and the reason is structural**.  REST FAIL 23.5 J (3x run
8's jitter), (d2) FAIL -0.148 m (was +0.0004 with spring alone).
THE MEASURED LESSON: **a direct-solve unilateral row is an
EQUALITY CLAMP while it is active -- it holds the point at the
constraint boundary and cancels the spring's lift every tick.
A row and a spring on the SAME point are mutually exclusive.**
The gate does not release the clamp under a resting pile (normal
velocity ~ 0, so the gate reads "still crushing" and holds), so
the spring's lift is eaten tick after tick and the accumulated
fight shows up as REST energy.  Composition must be EXCLUSIVE,
not additive: a point is served by the row XOR the spring, never
both.  The floor work is FROZEN here pending the sourced-data
re-derivation (operator directive 2026-08-08: measured contact
constants from the atlas, not another kernel variant).
RUN 10 CANDIDATES (sourced, 2026-08-08): the 1-DOF measured-floor
probe (.tmp/probe_measured_floor.py, log agent_logs/
measured_floor_probe.json) FALSIFIED its own statement that no
constant k in the Wearing band can meet both bars -- constant
k = 212 kN/m (Wearing FINAL stiffness) passes crush (0.051 m) and
rest (0.0 J) in 1-DOF.  The bilinear 32k->212k with rigid pad
bottom at 10.4 mm (Lopez-Lopez 2019) passes with 3x margin
(0.0155 m) and matches anatomy.  CAVEAT the probe cannot see:
1-DOF has no solver boundary, so run 8's 7.8 J jitter (spring x
solver-tick fight) is untested by it.  RUN 10 = full-skeleton test
of BOTH candidates under the run-9 EXCLUSIVE composition rule
(spring XOR row per point, never both).  Validation reference now
on disk: external/grf/standing_reference.json (5 subjects, quiet
ankle moments -3..+5 N m, sacrum sway std, Zenodo 3819630) and
7 CMU mocap traces (external/mocap/traces/, Vitruvian-checked).
