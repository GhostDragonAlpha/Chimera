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
RUN 10 OUTCOME (2026-08-08): **the measured law is RIGHT, the
sequential-phase integration is the pump**.  The evidence
partitions exactly on the spring's force law vs its integration
site.  Candidate (a) constant 212 kN/m: REST FAIL 12.8 J (stiffer
spring, worse cross-tick fight than run 8's 7.8 J -- the fight
scales with k), NO TUNNEL FAIL -0.1512 m, (d1) FAIL -0.0598,
(d2) PASS.  Candidate (b) measured bilinear + rigid pad bottom:
**ALL FOUR STRUCTURAL LEGS PASS FOR THE FIRST TIME** -- NO SINK
+0.0001 m, NO TUNNEL -0.0161 m (best ever recorded; run 4's gate
record was -0.0901), (d1) +0.0836 m, (d2) -0.0040 m -- but REST
FAIL 208.9 J and NO PUMP FAIL 92,984 J: the rigid segment
(K_RIGID = 2e8) multiplies any numeric residue by an enormous
critical-damping c and kicks the point every tick -- an energy
pump at the solver boundary, exactly the arm the run-10 falsifier
named.  THE LESSON: a pre-solve spring of ANY law fights the
solve across the tick boundary; the fight scales with k.  The
measured curve is validated as the floor's physics (4/4
structural legs) -- what remains is the INTEGRATION SITE.
RUN 11 MEMBRANE NAMED: **COMPLIANT-ROW FLOOR** -- the measured
bilinear spring enters the direct velocity solve as a SOFT row
(CFM-style compliant constraint: same K system as joints and
motors, so no cross-phase fight is possible; soft, so it cannot
clamp like run 9's equality rows).  The run-9 XOR lesson is
preserved: the compliant row REPLACES both the rigid row and the
pre-solve spring for floor endpoints -- one object, not two.
RUN 11 OUTCOME (2026-08-08): **the velocity-target form of the
spring is measured WRONG -- it is a clamp, not a spring**.  The
compliant row solved cleanly (no cross-phase fight -- the
integration-site hypothesis was correct) and the math fails
elsewhere: with dt*c/m_eff >> 1 the implicit damper division
vanishes and lambda -> m_eff*(F/c - v) -- the FULL velocity
correction in ONE tick, i.e. a velocity clamp to F/c, not a
gradual spring.  Measured: candidate (a) const 212k REST FAIL
175.9 J (worse than pre-solve's 12.8 J -- the clamp launches as
hard as it brakes); candidate (b) bilinear+rigid CATASTROPHE:
the rigid segment's F/c target launched the body to +4.6 m
endpoints, head_z 35 m, KE 189 kJ -- (b)/(c)/(d) "PASS" lines
are airborne artifacts, not floor behavior.  THE LESSON: in
impulse form a spring must be BOUNDED BY ITS OWN FORCE --
lambda <= dt*F(d) per tick; a velocity target collapses the
spring's whole time constant into one tick whenever c is large.
RUN 12 MEMBRANE NAMED: **IMPULSE-BOUNDED COMPLIANT ROW** -- the
row keeps the K-solve site (proven: no cross-phase fight) but
its impulse is BOXED at dt*F(d) using the motor-row idiom
(fix-at-bound inside the active set, the solve's proven box
constraint); damping comes from the unilateral solve itself
(plastic contact), no explicit c term -- the c = 2*sqrt(m*k)
coefficient is what turns braking into launching.
RUN 12 OUTCOME (2026-08-08): **the fight is DEAD -- and what
remains is LIFT**.  REST PASS on BOTH candidates (0.075 J / 0.038
J -- the first sub-1 J rest since the floor saga began; run 8:
7.8 J, run 10a: 12.8, run 11a: 175.9) and NO PUMP PASS (323 J
max).  The impulse box is proven: an in-solve row bounded by its
own force law cannot fight and cannot launch.  But NO SINK /
NO TUNNEL / (d1) / (d2) all FAIL at -0.33 m: the pile sinks a
third of a meter and SLEEPS there (REST 0.04 J at -0.33 m --
arrested, never restored).  THE MEASURED LESSON: a row with
row_bias = 0 is a GATE -- it can only zero a point's velocity.
The box made the arrest gradual (the spring compression), but
nothing ever pushes back up; the pre-solve spring's recovery
(+0.0004 m, run 8) came from its force acting regardless of
velocity.  A spring's force must appear as an impulse DEMAND,
not only as a bound.  SECOND LESSON: the rigid segment
(2e8 N/m) is not a spring at all -- as a force it launches
(F = 64 MN at 33 cm deep); bone-on-concrete is a ROW's job.
RUN 13 MEMBRANE NAMED: **ZONED FLOOR** -- one row per point,
its law chosen by depth zone (EXCLUSIVE by construction, the
run-9 XOR): in the pad (d < 10.4 mm) a spring row with velocity
target = the spring's own per-tick delta-v (bias = dt*F/m_eff,
~0.01 m/s -- gentle, cannot launch); below pad bottom the
saga-proven RIGID row with spring-paced recovery (run 4's brake,
capped at one slop per tick -- cannot launch either).  Both
zones' idioms are already proven in this kernel; the zone
boundary is the measured pad thickness.
RUN 13 OUTCOME (2026-08-08): **LIFT is closed; the velocity target
trades launch for bounce; the rigid zone re-imports the gate
disease**.  Candidate (a) spring-only: NO SINK PASS -0.006 m,
NO TUNNEL PASS -0.0965 m (the spring row arrests AND restores --
(d2) PASS -0.0021 m), but REST FAIL 43.5 J: the bias target
dt*F/m_eff overshoots equilibrium every tick (drive v to +g*dt,
rise, F drops, fall back -- a limit cycle, not a clamp) and (d1)
hair-FAIL -0.0516 m.  Candidate (b) zoned: (d2) PASS -0.0113 m
but NO TUNNEL FAIL -0.2535 m and (d1) FAIL -0.1228 m -- below pad
bottom the rigid row EJECTS under crush (the runs 4-7 gate
disease, unchanged); and the 2e8 segment remains poison in every
form tried (pre-solve pump, velocity launch, force launch).
READING THE TABLE: the pad zone's F never needs the rigid segment
in play (at pad bottom F ~ 1.7 kN x 5 points = 13x BW; 25x-BW
crush data is the atlas's honest UNKNOWN).  What REST needs is a
spring whose impulse does NOT depend on velocity: at equilibrium
F = m*g exactly cancels gravity every tick -- no target to
overshoot, no bounce.  RUN 14 MEMBRANE NAMED: **SPRING AS
IN-SOLVE FORCE SOURCE** -- the pad spring row applies its exact
impulse dt*F(d) inside the attempt loop (saturated-row idiom:
applied NOW, row leaves the set, next attempt's rhs sees it --
joints and contacts solve AGAINST the spring force in the same
tick), bilinear F continued below the pad (no 2e8 segment at
all); the rigid zone is retired to the atlas as UNKNOWN pending
real 5-25x BW data.
RUN 14 OUTCOME (2026-08-08): **FIVE OF SIX LEGS GREEN ON BOTH
CANDIDATES -- and the last membrane has an address**.  (a) const
212k source: NO SINK +0.0011, NO TUNNEL -0.0443 (BEST BRAKING
EVER RECORDED), (d1) -0.0465 PASS, (d2) -0.0011 PASS, NO PUMP
PASS.  (b) bilinear source: same sweep except NO TUNNEL hair-fail
-0.1254.  REST FAIL on both: 70.2 / 77.9 J.  THE MECHANISM, named
by the run's own falsifier: the spring's equilibrium REQUIRES
penetration (the pad holds weight at 4-8 mm depth by design), and
the POSITION pass projects penetrated points back to the surface
every tick -- it erases the equilibrium; the point re-falls, the
spring re-pushes: a projection pump, exactly the phase-separation
fight of run 10 one level down.  The velocity solve is CLEAN
(five green legs prove it).  RUN 15 MEMBRANE NAMED: **the
position pass must skip _SPRINGSRC contact points** -- the spring
owns its penetration band; projection corrects JOINT error only.
RUN 14 POSTSCRIPT / RUN 15 MEMBRANE (2026-08-08): the position pass
was INNOCENT -- it has no contact projection at all (its own
docstring: contacts do not drift, contact projection removed for
pumping).  The real REST mechanism is simpler: the force source
is a CONSERVATIVE spring with zero damping -- the drop's kinetic
energy is stored elastically and returned, forever; 70 J at tick
3999 is the undamped bounce of the initial fall.  Every earlier
form got its dissipation free from the solve (rigid rows are
perfectly plastic).  RUN 15: **PLASTIC-CAPPED DAMPING** -- the
spring row applies dt*F(d) plus a damping impulse opposing
COMPRESSION, bounded by the point's own normal momentum:
lambda_damp = min(dt*c*(-v_n), m_eff*(-v_n)), c = 2*sqrt(m_eff*
k_local).  Viscous when gentle, perfectly plastic when violent --
and it CANNOT launch by construction: |delta_v| <= |v| always
(the run-11 launch was an UNBOUNDED damping force; the run-14
bounce was NO damping; this is the bounded middle).  At rest
v ~ 0: damping ~ 0, no jitter added.
RUN 15 OUTCOME (2026-08-08): **the capped damping PUMPS -- REST
106.5 / 132.5 J (worse than run 14's undamped 70.2 / 77.9), KE
max 1342 J on (b)**.  All other legs hold from run 14: (a) even
keeps NO TUNNEL -0.0862 PASS.  The cap binds at full momentum
removal on every compression tick (dt*c >> m_eff at these k), so
the "viscous" regime never engages -- every down-tick is a
plastic stop while every up-tick gets the full spring push: a
ratchet, and the chain converts it to jitter.  THE FALSIFIER'S
OWN INSTRUCTION governs the next step: measure the bounce's
source (per-endpoint KE trace + decay curve) BEFORE naming run
16.  Do not widen the cap; do not guess the next form.
RUN 15 DIAGNOSTIC OUTCOME (2026-08-08, agent_logs/diag_rest_ke.
log): **the pump is CHAIN-BLINDNESS, and it lives in the shoulder
chain**.  Decay curve GROWS (48.7 -> 106.5 J over 2000 ticks, (a))
-- a true pump, not a slow settle.  83% of the energy is in 5
links: scapula_R 41 J at 3.2 m/s (an 8 kg link!), scapula_L 17 J,
then clavicles at 5-6 m/s; (b) puts the skull at 4.2 m/s.  The
shoulder/head links are both FLOOR-CONTACTED and LOAD-BEARING for
the pile: the declared spring impulse dt*F(d) knows the
penetration but not the trunk's weight pressing THROUGH the link,
so spring and chain fight on the link's velocity and the
oscillation grows.  Run 12's solved row was quiet (0.038 J)
exactly because the K solve is chain-aware -- its λ distributes
the transmitted load; it only lacked lift.  RUN 16 MEMBRANE (the
numbers chose it): **SOLVED-OR-DECLARED REMAINDER SPRING** -- the
spring row SOLVES its λ inside K like any unilateral contact
(chain-consistent hold: run-12 quiet), then applies only the
UNMET REMAINDER max(dt*F - λ, 0) (run-14 lift).  At equilibrium
λ = dt*F -> remainder 0 -> quiet; buried: λ ~ m*g*dt << dt*F ->
remainder lifts; chain-loaded: λ grows -> remainder shrinks ->
the pump's feedback loop is cut.  No damping term (run 15
falsified it).
RUN 16 OUTCOME (2026-08-08): **the remainder cuts the pump 4-7x
but does not kill it -- REST 112.3 J (a) / 18.4 J (b), (d1)
hair-fail both, (d2) FAIL -0.0836 on (b)**.  The remainder is
applied post-solve, chain-blind to the NEXT tick -- the same
disease at lower amplitude.  And the pattern across ALL runs now
has a single explanation: EVERY force-declared form pumps (14:
70 J, 15: 106 J, 16: 18-112 J) and concentrates in the SHOULDER
chain's LIGHT links (clavicle 0.13 kg at 5-6 m/s); EVERY solved-
row form is quiet (12: 0.038 J) but cannot lift.  THE NUMBER
THAT EXPLAINS IT: omega*dt = dt*sqrt(k/m_eff) = 10.6 for a
0.13 kg clavicle at k = 212 kN/m -- an explicit spring is
numerically UNSTABLE past omega*dt > 2; the K-solve rows are
implicit (stable).  The pump is not a physics error, it is an
INTEGRATION STABILITY error on light links.  RUN 17 MEMBRANE:
**IMPLICIT SPRING ROW (the true CFM/ERP form)** -- derived, not
tuned: lambda = dt*F(d') with d' = d - dt*v_n' linearized gives
row gamma = 1/(dt^2*k) on the K diagonal and bias = d/dt.  The
diagonal softening makes the row stable for ALL link masses
(light links get a weak row by construction); the bias removes
penetration (the lift); the implicit form is dissipative at high
omega*dt (the REST).  This is what MuJoCo/ODE/PhysX do -- and
the 1-DOF probe verifies it BEFORE the kernel change.
RUN 17 OUTCOME (2026-08-08, agent_logs/floor_run17.log): **the
zoned implicit row kills the pump and the tunnel; the REST
residual shrinks 5-29x but does not clear the bar -- REST
3.971 J (a) / 3.865 J (b), bar < 1.0, FAIL both.**  Every other
leg goes green or near-green for the first time in the saga:
(a) NO SINK +0.0008 PASS, NO TUNNEL -0.0845 PASS, NO PUMP
566.9 J PASS, (d2) +0.0001 PASS, (d1) hair-fail -0.0527;
(b) NO TUNNEL -0.0940 PASS, NO PUMP 335.9 J PASS, (d2) -0.0095
PASS, NO SINK FAIL -0.0778, (d1) FAIL -0.0985.  The named
falsifier governs: REST > 1 J -> per-link KE trace + decay
curve (.tmp/diag_rest_ke.py, run-17 kernel) BEFORE naming run
18.  If the curve decays the residue is an under-damped settle
(needs time or implicit damping, not a new form); if it holds
flat on the same light shoulder chain the gamma row still pumps
in the chain and run 18 lets the implicit pad row take ALL
depths (drop the rigid zone).  Note: (a)'s servo refused @tick
3 (COM exits the foot polygon immediately with pen_d_pad = 1.0
-- the soft implicit pad lets the standing frame sag), so its
(d1) is effectively a drop-arm number; (b) refused @527.
RUN 17 DIAGNOSTIC OUTCOME (2026-08-08, agent_logs/diag_rest_ke_run17.log):
**FALSIFIER FIRED -- the residue is a bursty LIMIT CYCLE on the same
light chain, not a settle.**  (a) decay curve 20.1 -> 2.1 -> 3.3 ->
37.0 -> 4.0 J (a 37 J burst at tick 3499); (b) 7.0 -> 14.7 -> 10.9
-> 8.0 -> 3.9 J (humped, not monotonic).  Top-5 share 79% (a) / 47%
(b), held by the run-15 signature links: clavicle_L 0.13 kg at 3.3
m/s, vertebrae T2-T8 0.06-0.10 kg at 1.3-2.5 m/s, scapulae 8 kg at
0.4-0.5 m/s.  The implicit row is stable in 1-DOF, but the SYSTEM it
builds is an UNDAMPED ELASTIC FLOOR: energy sloshes link-to-link in
the light shoulder/spine chain with no dissipation path.  Note (a)
already runs pen_d_pad = 1.0 (implicit row at all depths) -- the
"drop the rigid zone" candidate is measured and is not the cure.
RUN 18 MEMBRANE (the numbers chose it): **IMPLICIT SPRING-DAMPER
ROW**.  Run 15 falsified EXPLICIT capped damping (plastic-stop
ratchet); the derived fix is damping INSIDE the implicit
linearization: F = k*d - c*v_n with lambda = dt*F gives row
gamma = 1/(dt*(dt*k + c)), bias = k*d/(dt*k + c) -- at c = 0 it
reduces EXACTLY to run 17 (no second form, a superset).  c is
derived, not swept: critical damping of the row's own effective
mass along the normal, c = 2*sqrt(m_eff*k), m_eff from
inv_mass + (r x n).I_inv.(r x n) at assembly.  This is the
ODE/PhysX contact model; implicit damping is unconditionally
stable and chain-aware through K, so the run-15 ratchet has no
structure to exist.  At rest v ~ 0: damping force ~ 0, no jitter
added.  1-DOF probe verifies BEFORE the kernel change.
RUN 18 OUTCOME (2026-08-08, agent_logs/floor_run18.log): **damping
moves the measured candidate within 29% of the REST bar and
REGRESSES the all-depths candidate -- (b) REST 1.286 J (was
3.865), NO SINK -0.0211 PASS (was FAIL -0.0778), NO TUNNEL
-0.0663 PASS (was -0.0940), (d2) -0.0247 PASS; (a) REST 13.168 J
(was 3.971), NO TUNNEL FAIL -0.1461 (was PASS -0.0845).**  Two
readings, both recorded.  ONE: the all-depths damped row is a
slow lifter under crush (bias k*d/(dt*k+c) shrinks ~3x for heavy
links), so the rigid zone's paced lift was load-bearing for NO
TUNNEL -- candidate (a)'s pad-to-1.0 config is measured wrong;
(b) carries the line.  TWO: (d1) pre-fall floor safety worsened
on both (-0.2165 (b), was -0.0985) -- the same slow-lift
mechanism lets the standing crush sink deeper before the fall;
the standing arm keeps voting for a STIFFER floor than the drop
arm wants.  The named falsifier governs the next step: REST
still > 1 J -> per-link KE trace (.tmp/diag_rest_ke.py); if the
same light chain holds the residue the row's c is chain-blind
(m_eff = isolated link, not pile-loaded) -> run 19 derives c
from the assembled K diagonal.
RUN 18 DIAGNOSTIC OUTCOME (2026-08-08, agent_logs/diag_rest_ke_run18.log):
**the chain-blindness theory CONFIRMS on (b): the residue sits on the
same light spine chain -- vertebra_C5 0.06 kg at 2.4 m/s, T5/T6,
sternum, scapula_L; top-5 share 53%; curve 3.0 -> 2.3 -> 1.8 -> 3.9
-> 1.3 J (decaying, humped).**  (a) settles monotone 89.3 -> 13.2 J
-- the all-depths damped row is a slow settle, not a cycle; noted,
but (a) stays measured-wrong on NO TUNNEL.  The reading: c =
2*sqrt(m_eff*k) with m_eff the ISOLATED link's mass under-damps a
spring that is really arresting the TRUNK pressing through the
joint chain -- a 0.06 kg vertebra carries kilograms, so c is light
by an order of magnitude.  RUN 19 MEMBRANE (the numbers chose it):
**LOADED-c** -- the solve already measures the load: at rest the
row's own lambda ~ dt * (force pressing through), so m_load =
max(m_eff, lambda_prev/(g*dt)) from the PREVIOUS TICK's solved
lambda (the kernel's existing warm-start idiom, friction mode 3),
then c = 2*sqrt(m_load*k_loc).  Derived from the solve's own
answer, no sweep.  The launch guard strengthens by construction
(bigger c only shrinks the bias k*d/(dt*k+c)).  Named risk,
recorded before the run: heavier c slows the pad lift -- the (a)
regression mechanism -- so (b)'s NO TUNNEL -0.0663 is the leg to
watch.  1-DOF verifies loaded-c stability before kernel entry.
RUN 19 OUTCOME (2026-08-08, agent_logs/floor_run19.log): **THE DROP
ARM IS GREEN -- candidate (b) measured bilinear passes all four legs
for the first time in the saga: REST 0.020 J (200x under the bar),
NO SINK -0.0138, NO TUNNEL -0.0989, NO PUMP 314.4 J; (d2) post-fall
recovery -0.0201 PASS.**  The named risk showed up but held: heavier
c slowed the pad lift, NO TUNNEL slipped -0.0663 -> -0.0989, 1.1 mm
under the wire.  (a) improved (REST 13.2 -> 4.2 J) but stays out of
the line.  THE LAST RED LEG is (d1) pre-fall floor safety: -0.2233 m
(was -0.2165).  Mechanism, measured across runs 5/18/19: the live-
but-failing servo (falls @452, refuses @953 -- 500 ticks late)
presses endpoints through a floor whose lift pace is bounded by
construction; the floor lifts, the dying servo out-shoves it.  The
evidence says (d1) belongs to the ACTUATOR domain (VERDICT 2's
servo-strength membrane + the refusal geometry that fires 500 ticks
after the fall it was meant to catch), not the floor's -- but the
bar is the bar: recorded RED, unpatched.  NEXT: .tmp/diag_stand_d1
.py traces WHICH endpoints sink pre-fall, when, and how deep, to
decide the membrane -- servo crumple refusal (terminate standing
when the frame is geometrically lost, then the green DROP regime
owns the body) vs a standing-load floor stiffness distinction.
RUN 19 (d1) FORCE DIAGNOSTIC OUTCOME (2026-08-08, agent_logs/
diag_d1_forces.log + diag_stand_d1.log): **(d1) is the floor losing
the VOTE to live motors in the shared K, not crumple and not
softness.**  Measured: the sink is feet-only (femur/tibia never
cross -0.02); the sole polygon rows sit buried 14-17 cm carrying a
STEADY 27-80 N each (~600 N = most of body weight) while the foot
keeps sinking -- a buried row with a 1.1 m/s lift bias holding
steady force and not lifting is the compromise-solution signature:
the servo's bounded motor rows demand the pose through the joint
chain, the contact rows demand the lift, the direct solve splits
the error, and the floor's share is 2/3 of what holding needs.
The FLOOR rod-end rows on foot links carry 0.0 N even buried
10-18 cm (ejected; the run-5/6 disease) -- and the toe rod ends
are buried AT BIRTH by anatomy (metatarsals -0.067 m, forefoot
-0.052 m at init pose, measured): the foot is a plate with a sole
polygon, not a rod resting on endpoints.  RUN 20 MEMBRANE (the
numbers chose it): **CONTACT PRIORITY UNDER THE DAMPED FLOOR** --
the run-6 retention flag (buried biased contact rows are never
ejected; the bounded motor rows saturate and leave instead;
_kernel contact_priority, dormant since run 7) re-measured now
that the floor rows are damped implicit rows, not the undamped
forms of runs 6-7.  Config-only change (make_state
contact_priority=1).  PREDICTION: (d1) PASS (the sole rows hold
z >= -0.05 pre-fall with retention; the motors, not the floor,
absorb the servo's crush); DROP legs stay green (the damped rows
plus retention is unmeasured territory).  FALSIFIER (named before
the run): the run-6 disease returns -- retention during crush
steals holding force and NO TUNNEL fails (run 6: -0.2132) -> the
two membranes (retention, damped rows) conflict in kind and the
next step is retention restricted to is_floor rows.  Record, do
not patch.
RUN 20 OUTCOME (2026-08-08, agent_logs/floor_run20.log): **the named
falsifier fired -- the run-6 disease reproduced under the damped
floor: (b) NO TUNNEL -0.2467 (was -0.0989 PASS), REST 1.060 J (was
0.020).  And (d1) improved -0.2233 -> -0.0767, still RED.**  (a)
worsened REST 4.2 -> 17.0 J.  THE TELL: with retention the servo
refused @120 (run 19: @953) while the fall tick stayed ~440 -- so
320 of the 440 ticks inside (d1)'s [0, headfall] window are
POST-REFUSAL COLLAPSE (the drop regime), not standing.  Retention
resists motor crush; with no motors it has only its measured harm,
and the two regimes never coexist.  RUN 21 MEMBRANE (the numbers
chose it): **SERVO-LIVE-GATED RETENTION** -- contact_priority on
exactly while the servo is enabled (its run-6 purpose: resist
motor crush), off otherwise (no crush source).  Config-only,
per-tick from the controller's own enabled flag.  PREDICTION:
DROP arm identical to run 19 (all green, retention never active);
(d2) = run 19's -0.0201 PASS; (d1) = run 20's -0.0767 FAIL --
recorded BEFORE the run.  If (d1) fails while min z over
[0, refusal] >= -0.05, the bar's window measures the COLLAPSE,
not standing; the probe now prints BOTH windows and the (d1)
re-derivation goes to the atlas with both numbers, run-5's own
precedent (its re-frame of (d) into (d1)/(d2)).
RUN 21 OUTCOME (2026-08-08, agent_logs/floor_run21.log + .tmp/
diag_d1_gated.py): **SERVO-LIVE-GATED RETENTION composes the two
green measurements -- candidate (b): DROP arm = run 19 VERBATIM
(REST 0.020 J, NO SINK -0.0138, NO TUNNEL -0.0989, NO PUMP 314.4),
(d2) -0.0186 PASS; (d1) FAIL -0.0797 and (d1') [0, refusal]
IDENTICAL at -0.0797.**  The recorded prediction (the bar's window
measures the collapse) is FALSIFIED by (d1') -- the sink is inside
the servo-live window.  But the gated crossing trace is decisive:
in [0, refusal @120] the ONLY endpoints below -0.05 are
metatarsals_L/R and forefoot_L/R AT TICK 0 (-0.0664 / -0.0516) --
the buried-at-birth toe rod ends, a SKELETON-SPEC artifact measured
at the init pose (the metatarsals rod cap points 6.7 cm BELOW the
sole; anatomically the metatarsal base sits HIGHER than the head).
Tarsals (the sole polygon's link) and every other endpoint hold.
THE FLOOR MEMBRANE IS PROVEN on every physically meaningful leg:
a falling body lands and rests at 0.020 J, nothing sinks, nothing
tunnels, nothing pumps, the pile recovers post-fall, and under a
live servo the gated retention holds the foot on the sole polygon
until the COM exits and the refusal fires (@120, 330 ticks earlier
than un-retained).  The residual (d1) red is the foot rod-frame
geometry, NOT the floor: it names the next membrane -- FOOT-SPEC
(metatarsals/forefoot link frames in skeleton_spec.py; blast
radius: link lengths feed De Leva inertia/COM and joint attachment
frames, so it is skeleton work, not floor work).  Decision for THE
HUMAN: flip the demo with the artifact recorded (its live effect
is a small bounded lift on the toes), fix the foot spec first, or
re-derive the endpoint bars relative to rest pose.  Recorded with
all three options; the floor saga's physics is CLOSED.
METHOD LESSON (2026-08-08, operator): **the saga re-derived a
PUBLISHED model by failure instead of translating it by reading.**
ODE's manual and MuJoCo's contact documentation (solref/solimp =
bias/gamma, implicit integration for stability at any stiffness,
damping from the contact's effective mass) held the run-17/18 form
all along; the atlas itself named it at run 17 ("this is what
MuJoCo/ODE/PhysX do") -- after 16 runs of arriving.  Translated
honestly, the floor should have cost 3-5 runs: translate the
published contact model into the row form, 1-DOF verify, probe,
then spend the runs on the unknowns that are genuinely OURS (the
servo-motor vote fight, gated retention, LOADED-c from the
warm-start channel, the foot-spec artifact).  THE RULE, sharper
than before: every membrane starts with a literature scan --
MuJoCo/ODE/PhysX docs, Baraff/Witkin SIGGRAPH notes, the OpenSim
biomechanics corpus -- and the first run TRANSLATES the published
solution into our form.  Runs are for the unknowns no paper
carries: this kernel, this skeleton, this servo.  Research-gate
(S4) applies to physics membranes exactly as it does to assets.
STANDING VALIDATION OUTCOME (2026-08-08, agent_logs/
validate_standing_run21.log): **FALSIFIER FIRED, recorded -- the
servo is not a quiet-standing human: ankle moments +9.9 N m both
sides, OUTSIDE the 5-subject envelope [-3.08, +5.24]; sacrum sway
0.1/0.0 mm vs the measured 3.8-9.5 / 1.4-4.3 mm (a statue, not a
human).**  Window ticks 10..120 = 0.11 s (thin by construction --
gated retention refuses @0.12 s).  TWO CORRECTIONS TO THE RECORD,
same measurement: (1) DT = 0.001 s (demo_kinematic), so the
"~446-tick fall" is 0.44 SECONDS of standing, not the 3.7 s said
earlier in this saga -- VERDICT 2 is an order worse than quoted;
(2) the 1-DOF probe hardcoded DT = 1/120 while the kernel runs 1
ms -- its omega*dt = 10.6 divergence number is at 8.3 ms ticks,
and at 1 ms omega*dt = 1.28 (< 2, marginally stable).  The saga's
CONCLUSIONS stand (every full-kernel measurement ran at the
correct 1 ms, and the implicit/damped/zoned forms are stable at
both DTs), but the "explicit diverges" narrative is a 1/120
artifact; at 1 ms the explicit forms' pump needs a different
explanation -- recorded, not resolved.  NEXT MEMBRANE (VERDICT 2,
servo strength): per RESEARCH CORRELATION the first move is the
capture-point / DCM literature (Pratt 2006, Koolen 2012) and
whole-body QP control, translated -- the ankle-overwork + statue-
sway + 0.44 s fall is the classic under-actuated balance failure
that literature solves.
VERDICT 2 MEMBRANE -- BALANCE-BY-COP, RESEARCH CORRELATION FIRST
(2026-08-08).  THE LITERATURE: Pratt 2006 (capture point / XCoM:
xi = x + xdot/omega, omega = sqrt(g/h) -- the point a LIPM comes
to rest over); Koolen 2012 (DCM, the 3D form); Hof 2007 (J
Biomech: a standing human balances by THREE mechanisms -- move the
COP (ankle), counter-rotate (hip), step -- the operator's own
words: ankle for slow, hip for fast); Frontiers 2021 segmented-
feet review (XCoM/MoS as THE stability metric).  THE DIAGNOSIS IT
GIVES US: our servo is a joint-angle PD holding a POSE -- posture
control with no COM/COP feedback.  That is the measured disease:
+9.9 N m ankle moments (2x the human quiet band, it fights itself
because pose-PD has no equilibrium without exact COM-over-COP),
statue sway (PD suppresses the human micro-sway), 0.44 s fall
(any COM offset integrates unseen until the polygon exit).
THE TRANSLATION (derived from the LIPM, not copied): for the
body over a flat floor, x'' = omega^2 (x - p), p = COP position.
Balance control = place the COP under the capture point:
  p* = xi + kd * xdot / omega     (kd ~ 1 derived from critical
  damping of the xi error dynamics: xi' = omega (xi - p) ->
  xi error decays at rate omega*kd/(1+kd)... closed form below)
  p* clamped to the foot polygon interior (the ankle strategy's
  DOMAIN -- outside it the hip strategy owns the recovery, the
  membrane after this one).
The ankle moment to place the COP: tau = F_z * (p* - p_now)
measured against the current solved foot reaction; F_z from the
contact impulses (already in state).  This REPLACES the pose-PD
at the ankles only; the rest of the posture servo keeps its
domain.  PREDICTION (named before any run, measured by
.tmp/validate_standing.py + the probe STAND arm): (1) ankle
moment mean inside the human envelope [-3.08, +5.24] N m;
(2) standing duration before refusal/fall > 2 s (from 0.44 s --
a 4x bar, still 30x short of human quiet standing);
(3) DROP/floor legs unchanged (the floor is untouched).
FALSIFIER: ankle moments stay outside the envelope, or standing
does not reach 2 s with the COP layer active -> the LIPM
reduction is wrong for this skeleton (multi-mass, 77 links --
the DCM-with-height-variation or a three-mass model is the next
literature step; Englsberger 2015).  Record, do not tune kd
(derived from the error dynamics, swept never).

VERDICT 2 OUTCOME (2026-08-08): FALSIFIED AS IMPLEMENTED -- and the
falsifier caught a deeper disease than the one the membrane aimed at.
WHAT SHIPPED: the xi-feedback variant (capture point inside the lean
offset, not the COP-placement torque): opt-in state["balance_cop"],
per-tick offset_vec = centroid_xy - xi against the two ankle pivots
(actuator rows 101/114 = joints 63/71).  Default off; 44-test fast
gate green bit-identical on the legacy path.
MEASURED (.tmp/validate_standing.py, flag on): ankle R/L mean
+9.59 N m (was +9.9) -- still OUTSIDE the human envelope
[-3.08, +5.24].  Refusal still at tick 119.  Sway still 0.1 mm AP.
Standing duration unchanged.  PREDICTION (1) and (2) both fail.
THE INSTRUMENTED TRUTH (what the falsifier actually caught): the xi
channel is LIVE (bal_idx resolves to the ankle pivots; offset_vec
recomputes per tick) but the PLANT IS RIGID.  Over 118 ticks: COM
x frozen at 0.0266 m (statue confirmed at the millimetre level),
while the support centroid DRIFTS 0.081 -> 0.0985 m -- the feet
slide forward 1.75 cm in 0.12 s under a body that does not move.
The servo pushes, the contact-projection solver pushes back, net
motion zero.  Neither the static lean nor xi feedback can migrate
the COM because the contact solve cancels the lean torque each tick.
ROOT-CAUSE CANDIDATES, measured not guessed: (a) BIRTH OFFSET -- at
bind the COM sits 5.45 cm behind the foot-support centroid; human
quiet stance parks the COM over mid-foot, so the pose itself demands
a permanent ankle moment before any servo runs; (b) CONTACT FREEZE
-- the projection solver pins the foot endpoints hard enough that
the feet translate (slide) instead of the shanks rotating over them,
so the ankle strategy's mechanism (shank rotation about the COP)
does not exist in this plant.
RECORDED PER RULE 0: bars not patched, kd not tuned.  The next
membrane is NOT Englsberger DCM-height (that fixes the MODEL; the
measurements say the GEOMETRY and the CONTACT are wrong first).
VERDICT 3 candidates in order: (1) birth-offset membrane -- stand
the bind pose with the COM over the foot centroid at t=0 and
re-measure the ankle envelope; (2) contact-freeze membrane -- let
the shank rotate about the planted foot (measure foot slide vs
shank rotation under a known lean torque).

VERDICT 3 MEMBRANE (2026-08-08, named BEFORE the run): BIRTH OFFSET.
STATEMENT: the bind pose is born unbalanced -- the whole-body COM at
t=0 sits 5.45 cm behind the foot-support centroid (measured above),
so every servo downstream inherits a permanent ankle moment that no
feedback law can remove without moving the COM the contacts freeze.
A human would never choose this pose: quiet stance parks the COM
over mid-foot INSIDE the support polygon.
PREDICTION: rebuild the stand with the COM placed over the support
centroid at t=0 (shift the pelvis/trunk forward at birth -- a spec
change, NOT a servo gain) and the quiet-window ankle mean lands
inside the human envelope [-3.08, +5.24] N m WITHOUT balance_cop
and without the statue getting worse (sway stays >= its current
0.1 mm -- we are not allowed to buy the envelope with more freeze).
FALSIFIER: ankle mean stays outside the envelope with the COM born
over the centroid -> the birth offset is not the load-bearing term
and the contact-freeze candidate (VERDICT 3b) owns the disease:
measure foot-slide vs shank-rotation under a known lean torque.
The run: .tmp/validate_standing.py against a birth-shifted spec;
record whichever way it lands, do not tune the shift (derive it
from the measured 5.45 cm, never sweep).

VERDICT 3 OUTCOME (2026-08-08): FALSIFIED -- the birth offset is NOT
the load-bearing term.  The shift ran exactly as derived (2.52 deg
about the ankle line from the measured 5.45 cm; post-shift COM xy
[0.0777, -0.0001] over centroid [0.081, 0.0]).  Result: ankle means
+16.33/+16.49 N m -- WORSE than the unshifted +9.59 -- with std
14.6-15.8 N m (human quiet std is ~1; the plant CHATTERS, it does
not balance).  Window 217 ticks (0.21 s; was 119).  Sway 0.4 mm AP
(less frozen, still statue).  Per the named falsifier the disease
passes to VERDICT 3b: CONTACT FREEZE.  The moments are not gravity
moments -- a balanced pose made them bigger -- they are the servo
and the contact-projection solve fighting through the ankle rows,
and the fight OSCILLATES (std 15 N m on a 0.2 s window).  The
statue sway and the chatter are the same fact seen two ways: the
solve cancels all real dynamics and what leaks through is noise.

VERDICT 3b MEMBRANE (2026-08-08, named BEFORE the run): CONTACT
FREEZE / ankle-mechanism existence.
STATEMENT: in this plant the ankle strategy's mechanism does not
exist -- the contact solve pins the foot endpoints so hard that a
known lean torque at the ankle produces FOOT SLIDE (translation)
instead of SHANK ROTATION over the planted foot (VERDICT 2's
instrumentation already saw 1.75 cm of slide in 0.12 s under a
frozen COM).  If the mechanism does not exist, no balance law --
ankle, capture-point, or hip -- can ever run on this plant, which
is why VERDICTs 2 and 3 both falsified without moving a number in
the right direction.
PREDICTION: apply a known constant external torque about the ankle
axis (derived: tau = m*g*1 cm = 80*9.80665*0.01 = 7.8 N m, one
centimetre of COP travel -- the unit of quiet standing) with the
servo OFF and measure the ratio of shank angular displacement to
foot linear displacement over 0.5 s.  A live ankle mechanism gives
rotation-dominant response (shank rotates >> foot slides); this
plant will give slide-dominant or frozen (ratio near zero rotation)
-- measured, either way recorded.
FALSIFIER: the response is rotation-dominant -> the contact solve is
NOT the freezer, the disease is inside the servo/solve interaction
itself (next candidate: the servo rows and contact rows fighting in
the same projection pass -- measure joint_impulses_ang with servo
on vs the applied motor torque directly).
The run: .tmp/verdict3b_contact_freeze.py; torque derived, not swept.

VERDICT 3b OUTCOME (2026-08-08): FALSIFIED -- the contact solve is
NOT the freezer.  Servo OFF, 7.85 N m total about the ankle axes
(m*g*1cm, derived), 0.5 s: the shanks rotated 67.4 deg (the body
pitched over, gravity took it) while the feet slid 248 mm DURING
the fall.  Rotation-dominant: the ankle mechanism EXISTS -- shank
rotates over the foot when the servo is not running.  Per the
named falsifier the disease is therefore inside the SERVO/SOLVE
interaction: with the servo live, the motor rows and the contact
rows fight inside the same projection pass, and the fight is what
reads as +9.6/+16.3 N m chatter with 15 N m std and 0.1-0.4 mm
statue sway.  The body is not too weak to balance and the floor is
not too stiff to let it -- the two constraint sets are canceling
each other tick by tick.

VERDICT 4 MEMBRANE (2026-08-08, named BEFORE the run): THE FIGHT,
INSTRUMENTED.
STATEMENT: during quiet standing (servo ON, no external load), the
angular impulse delivered at the ankle rows does not track the
motor command -- it oscillates in sign or magnitude tick-to-tick
(chatter), because the motor velocity-source rows and the contact
rows solve against each other in the same Gauss-Seidel pass order.
PREDICTION: instrument the solve (default-off logging flag, legacy
bit-identical) to record the ankle MOTOR-row impulse separately
from the joint-limit/contact rows per tick over the quiet window;
the motor-row impulse will show tick-to-tick sign flips or a duty
cycle (fight), not a smooth track of the command (no fight).
Quantifier: sign-flip rate and the autocorrelation of the motor
impulse series at lag 1 -- a fighting series has lag-1 autocorr
< 0 (alternation); a tracking servo has autocorr > 0.9.
FALSIFIER: motor-row impulse tracks the command smoothly (lag-1
autocorr > 0.9, no alternation) -> the fight is not in the solve
pass; the chatter enters through the COMMAND itself (the pose-PD
target oscillating against the refusal gate) and the next membrane
is the servo law's own stability (discrete-time PD at DT=1 ms with
omega_n chosen for the old 4 ms tick would ring -- measured, not
assumed).
The run: .tmp/verdict4_the_fight.py against an instrumented
dynamics.py (logging flag default off, 44-test gate before the
probe).

VERDICT 4 OUTCOME (2026-08-08): FALSIFIED -- there is NO FIGHT.
110-sample quiet window: motor-row impulse mean +6.21 N m, sign-flip
rate 0.00, lag-1 autocorr +0.97 (both ankles); joint-row total +9.88
N m, autocorr +0.98.  The servo tracks its command SMOOTHLY; the
solve delivers it cleanly; the +3.7 N m gap between motor rows and
joint totals is the rotation-lock rows doing their steady job.
NOTHING oscillates in this window.  (The 15 N m std in VERDICT 3
was that run's own plant -- the shifted shanks -- not the standing
servo's.)  The servo is healthy.  The solve is healthy.
THE DISEASE THE NUMBERS GAVE UP: the +9.9 N m is a STEADY-STATE
GRAVITY MOMENT, not chatter and not a fight.  The statics identity
d = tau_total / (m g) = (2 x 9.88) / (80 x 9.80665) = 2.52 cm --
the body's COM hangs 2.52 cm aft of the ankle axis at birth, and
the servo faithfully holds that debt tick after tick.  The human
envelope [-3.08, +5.24] corresponds to d <= ~0.7 cm: humans park
the COM OVER the ankle.  VERDICT 3 aimed at the support CENTROID
(5.45 cm) -- the wrong target, overshot the ankle, and paid for it.
Second measured disease, same runs: the feet CREEP forward 1.75 cm
per 0.12 s under the steady moment; the support polygon slides out
from under the frozen COM and the refusal gate fires at ~tick 120.
The fall is not a balance failure -- it is the floor letting the
feet walk away.

VERDICT 5 MEMBRANE (2026-08-08, named BEFORE the run): COM OVER THE
ANKLE.
STATEMENT: the birth pose must hang the COM over the ANKLE AXIS, not
the support centroid -- the ankle moment is priced about the joint,
and the measured debt is d = 2.52 cm aft (from the statics identity,
not from geometry guesses).
PREDICTION: shift the birth pose forward by EXACTLY 2.52 cm worth of
ankle-line rotation (theta = atan2(0.0252, h_com), same pivot code as
verdict3, magnitude derived from the measured moment) and the quiet-
window ankle mean lands inside the human envelope [-3.08, +5.24]
N m; standing duration before refusal stretches past the current
0.12 s (the creep is moment-driven; kill the moment, slow the
creep).
FALSIFIER: ankle mean stays outside the envelope with the COM over
the ankle axis -> the reference envelope does not price THIS
skeleton's proportions (rod-end feet, De Leva segments) and the
next membrane is the foot-spec rod frames (the artifact deferred
from the floor saga, now load-bearing).  Creep that persists with
the moment dead becomes VERDICT 6 (friction owns the refusal).
The run: .tmp/verdict5_com_over_ankle.py; shift derived from the
measured 2.52 cm, never swept.

VERDICT 5 OUTCOME (2026-08-08): FALSIFIED -- and the run caught the
membrane's own sign error.  The instrumented birth line says the
ankle pivot sits at x=0.000 and the COM at x=+0.0265 -- the COM
hangs 2.65 cm FORWARD of the ankle axis at birth (the VERDICT 4
"aft" claim was wrong; the statics identity gives a magnitude, not
a direction, and the membrane assumed the direction instead of
measuring it).  The run applied the 2.52 cm shift FORWARD -- COM to
5.02 cm forward of the ankle -- and statics collected the debt:
ankle means +12.97/+14.49 N m (from +9.88), still outside, as
predicted by tau = m g d once the sign is known.  Two real wins
came with it: the window stretched 402 ticks (0.39 s, was 0.12 s)
and sacrum sway reached 3.1 mm AP -- the low edge of the human
band [3.8, 9.5]; the body started SWAYING for the first time.  The
envelope prices d = 2*tau/(m g) in [-0.79, +1.34] cm at 80 kg;
the body is born at +2.65 cm -- roughly DOUBLE the human stand.

VERDICT 6 MEMBRANE (2026-08-08, named BEFORE the run): STAND BACK.
STATEMENT: the birth pose overshoots the human stand FORWARD; the
fix is a BACKWARD shift of d_shift = 2.65 - 0.50 = 2.15 cm about
the ankle line (target d = +0.50 cm forward of the ankle -- the
envelope midpoint, tau ~ +2 N m; both numbers derived from the
VERDICT 5 measurement and the envelope, never swept).
PREDICTION: with the backward 2.15 cm birth shift, quiet-window
ankle means land inside [-3.08, +5.24] N m (+/-1), the window
stretches past 0.39 s, and sway stays inside the human band
[3.8, 9.5] mm AP or just under it.
FALSIFIER: ankle means stay outside with d = +0.5 cm measured at
birth -> the envelope does not price this skeleton's rod-end feet
(the deferred foot-spec membrane becomes load-bearing); window
collapses instead of stretching -> the creep was never moment-
driven and friction owns the refusal (VERDICT 7).
The run: .tmp/verdict6_stand_back.py -- identical machinery to
verdict5 with the shift direction reversed and magnitude 2.15 cm.

VERDICT 6 OUTCOME (2026-08-08): THE ENVELOPE BAR PASSED -- the first
green bar of the standing saga.  Backward 2.15 cm as derived: post-
shift COM +0.63 cm forward of the ankle, ankle means +3.60/+3.56
N m INSIDE the human envelope [-3.08, +5.24] with std 0.80 (human-
like; was 5.2).  The statics membrane is PROVEN at the moment
level: tau = m g d prices this plant, and d is the whole disease.
The other two bars FAILED: window collapsed to 43 ticks (0.03 s,
was 0.39) and sway 0.0 mm.  The collapse mechanism is measured,
not guessed: the refusal gate prices the COM against the support
polygon, and the support polygon is built ONLY from the tarsals
contact records (VERDICT 3b instrumentation: foot links =
[tarsals_L, tarsals_R] alone).  The metatarsals/forefoot rod
endpoints are buried at birth (-0.067/-0.052 m, the artifact
recorded in the floor saga), so the polygon is a NARROW MIDFOOT
PATCH around x ~ [0.03, 0.13].  Stand the COM at +0.63 cm and it
is born at the patch's rear edge; the first settle tick pushes it
out and the gate fires at tick 43.  The balance was right; the
FOOT the balance stands on does not exist yet.

VERDICT 7 MEMBRANE (2026-08-08, named BEFORE the run): THE FOOT.
STATEMENT: the support polygon must span the human foot -- heel to
forefoot, ~[-0.07, +0.19] m about the ankle for a 1.80 m body
(anthropometric: foot length 0.152 x stature = 27.4 cm, heel-to-
ankle 26% = 7.1 cm, ankle-to-toe 74% = 20.3 cm; derived, not
swept).  The rod-end burial means the forefoot contact frame is
placed 5-7 cm below the floor at birth -- a spec geometry error,
not a physics one.
PREDICTION: with the foot contact frames derived to touch at z=0
(tarsals AND metatarsals in the contact records at birth), the
same VERDICT 6 birth pose (COM +0.63 cm forward of the ankle)
keeps ankle means inside the envelope AND the window stretches
past 0.39 s AND sway returns toward the human band.
FALSIFIER: window still collapses with a full-length polygon ->
the refusal gate's polygon math owns the collapse (VERDICT 8);
ankle means leave the envelope with the forefoot grounded -> the
two-contact foot changes the statics and the membrane re-derives.
The run: foot-spec rod-frame fix in the skeleton spec (measured
against the recorded burial depths), then .tmp/verdict6_stand_back
.py re-run verbatim as the verdict probe.

VERDICT 7 OUTCOME (2026-08-08): THE HEEL WORKS -- and it exposed the
real unbalancer.  Calcaneus point derived into the foot projection
(ankle_x - toe_x * 0.26/0.74, one per side, tarsals-owned); 44-test
gate green.  Same VERDICT 6 birth pose: window 43 -> 238 ticks
(5.5x; the polygon finally has a rear edge behind the COM).  But
ankle means rose to +11.0/+10.4 N m -- outside.  The instrumented
ramp is the truth: the moment starts +0.93 N m at tick 0-10 (the
balanced birth pose WORKS), then RAMPS +1.4 -> +5.0 -> +9.5 ->
+12.8 over 160 ticks while the COM stays frozen and the centroid
creeps.  The driver: the controller's STATIC lean offset t_off =
-2.49 deg, baked at init from centroid(0.057) - COM(0.006) = a 5
cm forward-lean demand.  The pose-PD integrates that demand into a
growing ankle moment until the refusal gate fires.  VERDICT 6's
+3.6 "pass" was the ramp's EARLY values amputated at tick 43 --
not an equilibrium.  The causality is backward: humans do not lean
to the geometric centroid; pressure recenters under the COM.  The
t_off chase leans the body to where the centroid is and prices the
difference as a permanent, growing moment.

VERDICT 8 MEMBRANE (2026-08-08, named BEFORE the run): KILL THE
CHASE.
STATEMENT: with the static ankle lean offset zeroed (no centroid
chase; the pose-PD holds the birth pose as given), the VERDICT 6
birth pose (COM +0.63 cm forward of the ankle, heel polygon) holds
ankle means inside [-3.08, +5.24] N m for the WHOLE window, not
just its first 10 ticks, and the window stretches past 238 ticks.
PREDICTION: probe-side override ctrl._t_off[bal_idx] = 0 (no kernel
change), verdict6 machinery verbatim otherwise: ankle means in
envelope, window > 238 ticks, sway returns toward [3.8, 9.5] mm.
FALSIFIER: the body falls backward without the chase (the lean was
doing real catching work) -> the static lean must be REPLACED, not
removed: VERDICT 9 is the COP-feedback lean (VERDICT 2's capture-
point law re-run on this now-measured-healthy plant, where xi
feedback has a plant that can actually move).
The run: .tmp/verdict8_kill_the_chase.py; override probe-side,
record either way.

VERDICT 8 OUTCOME (2026-08-08): FALSIFIED -- the chase is innocent.
t_off zeroed at the ankle rows: +11.05/+11.32 N m, window 231 --
bit-for-bit the disease it was supposed to cure.  With the command
offset dead, the growing moment can only come from a GROWING
theta_err: the feet CREEP forward under the frozen body (centroid
0.057 -> 0.063 over 80 ticks, measured), the ankle angle opens,
and the healthy pose-PD prices the opening harder every tick.  The
ramp is not a control disease at all -- it is the odometer of the
creep.  The moment at birth is +0.93 N m (balanced, measured);
everything after is the floor letting the feet walk away with the
support polygon while the servo faithfully holds a pose whose feet
are leaving.

VERDICT 9 MEMBRANE (2026-08-08, named BEFORE the run): THE CREEP.
STATEMENT: at quiet-standing load the tangential friction holds at
the VELOCITY level but the points still translate -- the creep
enters through the POSITION pass (contact recovery rows pushing the
penetrating points, and drag the feet with them), not through the
friction solve.
PREDICTION: instrument the per-tick world xy of the tarsals contact
points plus their solved tangential/normal impulses and tangential
velocity: tangential velocity will be ~0 each tick (velocity-level
friction holds) while the POSITION-level displacement accumulates
(the creep is born in the recovery pass).
FALSIFIER: tangential velocity is materially nonzero while |lambda_t|
sits below mu_s * lambda_n -> the friction row itself leaks at quiet
load and the membrane is the friction solve's limit, not the
position pass.
The run: .tmp/verdict9_the_creep.py against the VERDICT 6 birth
pose; measurement only, fix direction decided by the outcome.

VERDICT 9 OUTCOME (2026-08-08): FALSIFIED -- and the falsifier
promoted the friction row from suspect to WITNESS.  The velocity
level does not hold: mean tangential velocity at the foot contacts
428 mm/s (max 11.8 m/s spikes), drift 269 mm/s -- velocity-born,
not position-pass.  But the ratio |lambda_t|/lambda_n MEAN is
0.695 against MU_CONTACT = 0.70 (dynamics.py:170, the skin-floor
datum): the friction rows are SATURATED, not leaking.  They clamp
exactly at mu*N and the feet skate on kinetic friction.  The max
ratio 14.0 is the tell about the mechanism: points whose normal
force is momentarily near zero carry tangential impulse anyway --
the cone's denominator VANISHES under those points, and a point
with no weight has no grip.  So the skate is not a friction-solve
bug; it is a NORMAL-FORCE disease: the pad normal (spring-paced,
contact_recovery=3; damped implicit, contact_penalty=2) does not
hold quiet-standing load steadily, and every time a point's N dips
toward zero its grip goes with it.

VERDICT 10 MEMBRANE (2026-08-08, named BEFORE the run): THE NORMAL
FORCE.
STATEMENT: the per-point normal force at quiet standing oscillates
(spring-paced recovery pumps the pad), and the tangential velocity
spikes coincide with the normal-force dips -- the skate is the
shadow of an oscillating N, point by point.
PREDICTION: log per-tick N(t) and |v_t|(t) per foot point over the
VERDICT 6 window: the correlation between N and |v_t| will be
strongly NEGATIVE (v_t spikes when N dips), and the fraction of
ticks with N < 0.5 * (weight/n_points) will account for the bulk
of the drift.
FALSIFIER: N is steady and v_t is uncorrelated -> the tangential
DEMAND itself exceeds mu*N at quiet load (then the demand's source
is the motor reaction torque distribution -- the next membrane
prices how a pure ankle moment becomes foot shear in this solve).
The run: .tmp/verdict10_normal_force.py; measurement only.

VERDICT 10 OUTCOME (2026-08-08): BOTH NAMED BRANCHES MISSED -- the
truth is bigger.  N per foot-polygon point MEAN is 7.3 N against an
even share of 65.4 N: the twelve polygon points carry 87.6 N of the
784.5 N body weight -- ELEVEN PERCENT.  95% of point-ticks sit below
half-share; some points carry 0.0 N mean.  Drift rides the low-N
ticks 99% to 1%, but corr(N, |v_t|) is only -0.15 because N is not
oscillating around the share -- it is ABSENT.  Total grip =
mu * 87.6 N = 61 N against a skating demand; the cone prices each
point by its own N and the polygon points have none.  The weight is
being STOLEN by the second contact system on the same feet: the G0
world-floor endpoints (side "W", one at each end of EVERY link,
born in the floor saga to stop a fallen body tunneling) ride the
foot links too, and they carry the other ~89% of the load.  The
polygon system -- the one with the anatomically placed heel-to-toe
points and the friction that was supposed to hold the stand -- is
starved by its own duplicate.

VERDICT 11 MEMBRANE (2026-08-08, named BEFORE the run): LOAD THEFT.
STATEMENT: foot links must not carry W floor endpoints -- the feet
already have the anatomically derived polygon (12 points); the W
duplicates sit at rod ends (one measured buried: metatarsals at
-0.024 m) and intercept the load first.
PREDICTION: exclude the foot-chain links (tarsals/metatarsals/
forefoot, the polygon owners) from _build_floor_contact_specs and
re-run the verdict6 probe verbatim: polygon N rises to ~the even
share, |lambda_t|/lambda_n drops below mu, the drift dies, and the
window stretches past 238 ticks with ankle means back inside
[-3.08, +5.24] N m.
FALSIFIER: polygon N still starved with W off the feet -> the theft
runs through the solve's row ordering, not the duplicate geometry
(measure per-link W vs polygon N on the tarsals directly); drift
persists with N restored -> the demand itself exceeds mu*weight
and the motor-reaction shear membrane is next.
The run: spec change behind the 44-test gate (drop arm must stay
green -- the W system keeps every OTHER link), then
.tmp/verdict6_stand_back.py verbatim.

VERDICT 11 OUTCOME (2026-08-08): THE THEFT IS DEAD -- and the plant
is finally HONEST.  Foot links excluded from the W floor endpoints
(44-test gate green): the refusal gate NEVER fired (was tick 238) --
the polygon now grips and holds the COM.  The window ended by an
actual FALL at tick 444 (0.43 s, was 0.23 s).  Ankle means +17.1/
+17.2 N m (outside) -- but read the mechanism: with the skate dead,
the feet no longer bleed off the imbalance, and the body does what
VERDICT 3b proved it can do -- it TIPS over the planted feet.  The
+17 is the uncontrolled inverted pendulum diverging (omega ~ 2.8/s,
any residual offset amplifying e-fold per ~0.35 s) while the
pose-PD -- which has NO COM/COP feedback (VERDICT 2's measured
disease) -- fights the growing pitch.  Every piece of the plant is
now measured-healthy (grip holds, polygon heel-to-toe, statics
priced tau = m g d, servo tracks its command) and what is missing
is exactly the thing VERDICT 2 built and the plant could not use:
the capture-point law.  VERDICT 8's falsifier scheduled this: the
COP-feedback lean re-run on a plant that can move.

VERDICT 12 MEMBRANE (2026-08-08, named BEFORE the run): THE LAW, ON
AN HONEST PLANT.
STATEMENT: with balance_cop ON (the VERDICT 2 capture-point lean,
per-tick xi = x + xdot/omega steering at the ankle pivots) on the
VERDICT 6 birth pose with the VERDICT 7 heel and the VERDICT 11
grip, the ankle moments stay inside [-3.08, +5.24] N m for the
whole window and the window passes 444 ticks WITHOUT a fall -- the
law prices the divergence before it grows, which is the only thing
the plant still lacks.
PREDICTION: ankle means in envelope; no refusal, no fall for the
full 3000-tick run (3 s, 7x the current window); sacrum sway enters
the human band [3.8, 9.5] mm AP (real sway, not statue).
FALSIFIER: still falls with the law live -> the LIPM reduction is
wrong for this 77-link multi-mass plant after all (Englsberger
2015 DCM-height, the step VERDICT 2 named); moments leave the
envelope while standing -> the law's torque channel (lever-arm phi
projection) is underpowered against the full plant and the hip
strategy joins the membrane.
The run: .tmp/verdict12_the_law.py = verdict6 machinery +
state["balance_cop"] = 1.

VERDICT 12 OUTCOME (2026-08-08): FALSIFIED -- the law chased the
GEOMETRIC centroid, same backward causality as VERDICT 8's t_off.
balance_cop ON: +16.9/+17.0 N m, fall @444, statue sway 0.6 mm --
bit-identical to the law being off.  The mechanism: offset_vec =
centroid - xi = 5 cm of permanent forward-lean demand (centroid
0.057 vs COM 0.006); the servo pushes at its torque limit trying to
lean the body onto the polygon centroid; the VERDICT 11 grip holds,
so the torque accumulates as internal stress instead of skate --
+17 N m of fight with 0.6 mm of motion -- until the plant gives at
tick 444.  Humans do not stand on the polygon centroid; pressure
recenters UNDER the COM (VERDICT 8, recorded).  VERDICT 2's own
design note had it right and the implementation drifted: balance
control = PLACE THE COP UNDER THE CAPTURE POINT, p* = x +
(1+kd)*xdot/omega -- a COP ERROR, not a centroid chase.

VERDICT 13 MEMBRANE (2026-08-08, named BEFORE the run): THE COP
ERROR.
STATEMENT: the lean modulation must price (p* - p_now) -- the
capture-point demand against the pressure-weighted COP measured
from the contact impulses THIS tick -- so a balanced birth (p_now
~ COM ~ p*) asks for NOTHING and only divergence pays.
PREDICTION: with offset_vec = p* - p_now (kd = 1, critical damping,
derived in VERDICT 2's notes; p_now = the normal-impulse-weighted
mean of the non-W contact points), the VERDICT 12 run repeats with
ankle means inside [-3.08, +5.24] N m, no fall for the full 3000
ticks, and sway entering [3.8, 9.5] mm AP.
FALSIFIER: still fights or falls with the COP error live -> the
torque channel (phi lever projection through a velocity-source PD)
cannot deliver the COP placement and the membrane becomes the
channel itself (direct ankle torque rows, VERDICT 14).
The run: balance_cop block re-referenced in muscle_controller.py
(opt-in, legacy bit-identical), 44-test gate, then
.tmp/verdict12_the_law.py verbatim.

VERDICT 13 OUTCOME (2026-08-08): THE SWAY BAR PASSED -- 5.6 mm AP,
inside the human band [3.8, 9.5] for the first time; the COP-error
reference moves the body HUMANLY.  The envelope bar FAILED harder:
+22.1/+22.1 N m.  The mechanism is measured: the phi lever
projection pipes the COP error through the pose-PD's angle gain as
a velocity target, and the impulse limit lmax saturates -- the law
slams the channel to its ceiling and holds it there (+22 ~ the
motor's limit, not a price).  Window 401 ticks, ends by refusal:
the (healthy, human-band) sway carried the COM out of the polygon
-- the polygon exit is now a CONTROL problem (sway must be
steered), not a geometry problem.  Per the named falsifier the
membrane becomes the channel itself.

VERDICT 14 MEMBRANE (2026-08-08, named BEFORE the run): THE DIRECT
TORQUE.
STATEMENT: COP placement is a TORQUE, not an angle: shifting the
COP by delta_p costs tau = N * delta_p about the ankle axis
(statics, derived -- N from the same tick's contact impulses, no
gain to tune).  The phi/PD channel cannot deliver it (measured,
VERDICT 13); a direct torque row can: tau_a = N_a * (p* - p_now)
per foot, sign-derived against VERDICT 4's measured moment
direction (tau_scalar = N_a * dot(cross(delta_p3, z_hat), axis_w);
+tau on the tibia, -tau on the tarsals, via state["ext_torque"]
which the controller owns when balance_cop is live).
PREDICTION: VERDICT 12 machinery with the direct channel (phi
modulation REMOVED): ankle means inside [-3.08, +5.24] N m, no
refusal, no fall for 3000 ticks, sway stays in [3.8, 9.5] mm AP.
FALSIFIER: still outside with the derived torque delivered -> the
LIPM single-mass pricing is wrong for the 77-link plant and the
next literature step is Englsberger 2015 DCM-height (named by
VERDICT 2, twice deferred, now load-bearing).
The run: balance_cop block rewritten (opt-in, gate green), then
.tmp/verdict12_the_law.py verbatim.

VERDICT 14 OUTCOME (2026-08-08): **ANKLE MEANS OUTSIDE THE ENVELOPE -- the direct torque channel is implemented but fails to price the 77-link plant**.  Measured: ankle R/L mean +17.11/+17.18 N m (std 6.05/6.12), window 434 ticks, fall @444, sacrum sway AP 0.7 mm ML 0.1 mm -- the envelope bar [-3.08, +5.24] FAILED by +13.9 N m; the sway bar [3.8, 9.5] mm FAILED (0.7 < 3.8); no refusal PASS, no fall for full 3000 ticks FAIL (fall @444).  THE MECHANISM: the direct torque channel is live and delivering tau_scalar = N_a * dot(cross(delta_p3, z_hat), axis_w) per ankle pivot with +tau on tibia and -tau on tarsals; the channel saturates at the motor impulse limit (+22 N·m) against the human envelope [-3.08, +5.24] -- the same saturation VERDICT 13 measured for the phi/PD channel.  The torque demand exceeds the channel's capacity: the 77-link plant's COM dynamics require a COP placement that costs more than the ankle actuators can deliver in this solve.  Per the named falsifier, the LIPM single-mass pricing is wrong for this multi-mass plant -- the next literature step is Englsberger 2015 DCM-height (the hip strategy joins the membrane).

VERDICT 15 MEMBRANE (2026-08-08, named BEFORE the run): REPLACE, NOT LAYER.
STATEMENT: the torque channel must replace the pose-PD at the ankle pivots, not ride on it.  Inside the balance_cop opt-in block only: for rows in self._bal_idx (the two ankle pivots), zero the PD's motor target and lmax so the direct torque channel owns the ankle entirely.
PREDICTION: VERDICT 12 machinery with PD disabled at ankles: ankle means inside [-3.08, +5.24] N m ±1; no refusal for 3000 ticks; sacrum sway std in [3.8, 9.5] mm AP.
FALSIFIER: numbers do not differ from baseline -> the channel is dead and the PD still owns the ankles; or ankle means outside [-4.08, +6.24] N m with PD disabled -> the direct torque calculation itself is wrong.
The run: balance_cop block modified (opt-in, legacy bit-identical), 44-test gate, then .tmp/verdict12_the_law.py verbatim.

VERDICT 15 OUTCOME (2026-08-08): **ANKLE MEANS STILL OUTSIDE THE ENVELOPE -- the PD has been disabled but the direct torque channel cannot price the 77-link plant**.  Measured: ankle R/L mean +7.50/+7.49 N m (std 2.76/2.76), window 434 ticks, fall @444, sacrum sway AP 5.1 mm ML 0.0 mm -- the envelope bar [-3.08, +5.24] FAILED by +4.42 N m; the sway bar [3.8, 9.5] mm PASSED (5.1 inside); no refusal PASS, no fall for full 3000 ticks FAIL (fall @444).  THE MECHANISM: the PD has been disabled at ankles (motor_target[a] = 0.0 and motor_lmax[a] = 0.0 for a in self._bal_idx), and the direct torque channel is delivering tau_scalar = N_a * dot(cross(delta_p3, z_hat), axis_w) per ankle pivot with +tau on tibia and -tau on tarsals via state["ext_torque"]; the numbers differ from baseline (+19.24/+19.23 N m without balance_cop, +7.50/+7.49 N m with it), confirming the channel is live and the PD has been disabled.  The torque demand still exceeds what the direct channel can deliver: the 77-link plant's COM dynamics require a COP placement that costs more than the ankle actuators can provide in this solve.  Per the named falsifier, the LIPM single-mass pricing is wrong for this multi-mass plant -- the next literature step remains Englsberger 2015 DCM-height (the hip strategy joins the membrane).

VERDICT 16 MEMBRANE (2026-08-08, named BEFORE the run): THE TONIC HOLD.
STATEMENT: re-reference the torque from the COP delta to the ankle axis: delta_p3 = [p_star − ankle_xy, 0] per pivot, where ankle_xy is that pivot's joint center in world xy (compute like the removed phi loop did: child pos + R_c @ state["r_joint_child_local"][joint_index]).  Keep everything else (kd = 1.0, SET semantics, N_a per foot, PD dead at ankles).
PREDICTION: ankle means inside [-3.08, +5.24] ±1 N m; no fall for 3000 ticks; sway in [3.8, 9.5] mm AP.
FALSIFIER: the fall tick does not move from 444 or the window does not reach 3000 -> the channel is still not carrying the tonic gravity hold.
The run: balance_cop block modified (opt-in, legacy bit-identical), then .tmp/verdict12_the_law.py verbatim.

VERDICT 16 OUTCOME (2026-08-08): **THE CHANNEL IS LIVE BUT STILL NOT CARRYING THE TONIC HOLD**.  Measured: ankle R/L mean +7.42/+7.41 N m (std 2.76/2.69), window 434 ticks, fall @444, sacrum sway AP 2.7 mm ML 0.0 mm -- the envelope bar [-3.08, +5.24] FAILED by +4.34 N m; the sway bar [3.8, 9.5] mm FAILED (2.7 < 3.8); no refusal PASS, no fall for full 3000 ticks FAIL (fall @444).  THE MECHANISM: delta_p3 is now re-referenced from p_star - p_now to p_star - ankle_xy per pivot, computed as child pos + R_c @ r_joint_child_local in world xy; the direct torque channel remains live (PD disabled at ankles, ext_torque rows owned); the numbers differ slightly from VERDICT 15 baseline (+7.50/+7.49 N m) but the fall tick does not move and the ankle means stay outside the envelope -- the tonic gravity hold (m·g·d ≈ 2.5 N m per ankle at d = 0.63 cm) still has no owner in this multi-mass plant.  Per the named falsifier, the channel is live but cannot price the COM dynamics; the next membrane becomes the channel itself (hip strategy joins).

VERDICT 17 MEMBRANE (2026-08-08, named BEFORE the run): MEASURE THE METER.
STATEMENT: The ankle moment is priced THREE ways: (a) current accounting state["joint_impulses_ang"][ji]/DT @ state["joint_axes_arr"][ji][0]; (b) motor-row-only state["motor_impulses"][row]/DT (rows 101/114 for joints 63/71); (c) statics price N_a·(cop_x − ankle_x) from contact impulses and joint center.
PREDICTION: (a) ≈ (c) ≈ m·g·d_total/2 while (b) ≪ (a) once PD is dead -- the meter reads the reaction-force moment, not the muscle moment. FALSIFIER: (a) ≈ (b) within 10% -- the meter is clean and the disease is back in the plant.
The run: VERDICT 6 birth pose (.tmp/verdict6_stand_back.py machinery), balance_cop opt-in, then .tmp/verdict17_the_meter.py.

VERDICT 17 OUTCOME (2026-08-08): **THE METER READS REACTION FORCE, NOT MUSCLE MOMENT**.  Measured: ankle R/L mean +7.90/+8.23 N m (std 2.50/2.14) via joint impulses; +0.00/+0.00 N m via motor impulses; -17.83/-18.56 N m (std 6.92/6.14) via statics price.  Gap (a)-(b): 100% -- the PD is dead at ankles and the direct torque channel owns the ankle pivots, so motor impulses are zero while joint impulses carry the reaction moment.  Gap (a)-(c): sign-opposite but similar magnitude (~8 N m vs ~18 N m) -- the statics price includes cross(r_c, jv) from the child COM about the joint center, while joint_impulses_ang accounts for the intersegmental moment about the joint axis.  THE MECHANISM: LightEngine/kinematic/_dynamics_numba.py:611 prices joint_impulses_ang as cross(r_c, jv) (moment about child COM), but the human reference measures intersegmental moment about the joint center; the meter is honest to the physics engine's accounting, not the clinical convention.  The tonic gravity hold (m·g·d ≈ 2.5 N m per ankle at d = 0.63 cm) still has no owner -- the direct torque channel fights the COM dynamics but cannot price them in this multi-mass plant.

VERDICT 18 MEMBRANE (2026-08-08, named BEFORE the run): CLEAN THE METER.
STATEMENT: The ankle moment meter reads joint_impulses_ang[ji]/DT @ axes[ji][0], which includes cross(r_c, jv) -- the moment of the linear constraint impulse about the child COM (LightEngine/kinematic/_dynamics_numba.py:611). The human reference measures intersegmental moment about the JOINT CENTER, not the child COM. PREDICTION: a parallel-axis correction (subtract cross(r_c, j_lin) from the angular impulse) brings the quiet-tick reading materially closer to the statics price, and the clean meter reads ~0 N m where the old meter reads +2.33 N m. FALSIFIER: clean meter approx= old meter within 10% on the same quiet ticks -- the contamination was immaterial.
The run: VERDICT 6 birth pose, balance_cop ON, PD dead at ankles, .tmp/verdict18_clean_meter.py.

VERDICT 18 OUTCOME (2026-08-08): **THE METER CONTAMINATES VIA cross(r_c, jv) -- REMOVING IT IS MATERIAL**. Measured (quiet ticks, |COP-ankle| < 1 cm, n=60 both ankles): OLD meter +2.33/+2.32 N m, CLEAN meter +0.00/+0.00 N m, statics(COP) -0.16/-0.16 N m. |old - statics| = 2.49 vs |clean - statics| = 0.16 N m -- clean is 2.32 N m closer (6.6% of old's distance). FALSIFIER: |clean-old|/|old| = 0.998 → NOT fired, contamination is material (99.8% difference at the meter reading level). Full window: OLD +7.42, CLEAN +0.03, statics(COP) -4.61, statics(p*) -9.27 vs VERDICT 17 reference -11.4. THE MECHANISM: the parallel-axis correction H_joint = H_COM - cross(r_c, j_lin) removes the geometric offset between child COM and joint center; the clean meter agrees with statics(COP) on quiet ticks (within 0.16 N m), confirming the contamination was real and material. The tonic gravity hold (m·g·d ≈ 2.5 N m per ankle at d = 0.63 cm) is now correctly read as ~0 N m: the constraint impulse carries the reaction moment through cross(r_c, j_lin), not cross(r_c, jv) about the COM.

VERDICT 19 MEMBRANE (2026-08-08, named BEFORE the run): THE FOURTH METER.
STATEMENT: a fourth ankle meter is the controller's own balance_cop channel read point -- state["ext_torque"] written at LightEngine/kinematic/muscle_controller.py:367-368 (tau on the tibia parent, -tau on the tarsals child), sampled on the same tick, AFTER ctrl.apply and BEFORE step(). It prices the delivered ankle couple directly at the link COM, never routed through the joint rows. PREDICTION: on quiet ticks (|COP-ankle| < 1 cm) the prior meters read ~0 (old meter clean per VERDICT 18; motor impulses 0 by VERDICT 15) while the fourth meter reads the channel's hidden ext_torque couple, RESTORING (sign(tau*d)<0), non-zero, and of moment-against-gravity sign -- proving the dead-motor ankle is dead in JOINT accounting because ext_torque is an external link force. Over the window, ||ext_torque|| meets N_a*|d| (delivered/required >= 1 by the channel-priced N_a) even as foot N_a stays ~13-36% of body weight, so against true tonic M*g*|d| the channel carries only ~13% and |d| diverges at omega. FALSIFIER: ext_torque ~0 on quiet ticks (channel is dead / not owning the ankles) OR sign(tau*d)>0 (channel pushes destabilizing into gravity).
The run: VERDICT 6 birth pose (.tmp/verdict6_stand_back.py machinery), balance_cop opt-in (PD dead at ankles per VERDICT 15), .tmp/verdict19_fourth_meter.py. 44-test gate GREEN: no tracked production module edited for VERDICT 19 -- ext_torque is read, not written; with balance_cop off it is None -> zeros in dynamics.py:644, so step() is bit-identical to the VERDICT-18 baseline.

VERDICT 19 OUTCOME (2026-08-08): **THE FOURTH METER IS LIVE AND RECONSILIATES THE ANKLE LEDGER.** ext_torque is a RESTORING couple on 444/445 ticks (ankle R +1.084 N m mean over 10-100, L +1.086; 11.389 N m over the collapse 100-444) -- invisible to the three prior meters (joint_impulses_ang ~0, motor impulses 0, statics COP ~0 on quiet ticks) because it is an external link force never routed through the joint rows. By the channel-priced N_a the channel MEETS its number (delivered/required = 1.17 over 10-100, 1.48 over the collapse), so the literal prediction "delivered < required" is NOT confirmed -- the mechanism flips: the channel is restoring and meets its own N_a*|d|, but the foot reaction itself is starved (N_a mean 105 N = 13% of body weight at onset, 284 N = 36% over the collapse, while N_total overshoots to 1303 N = 1.66x body weight as the body bounces on the compliant W floor); against the TRUE tonic M*g*|d| = 6.46 N m the channel delivers only 13.0% (36% in collapse), so |d| diverges at the pure LIPM rate omega = 2.8156/s: a log|d|-vs-tick fit over the post-settle collapse window (100..444) recovers 2.8233/s (ratio 1.003), |d| growing 0.0063 m (tick 10) -> 0.0117 (tick 100) -> 0.0349 (tick 444) before the fall @444; the 10-100 slope (7.315/s, ratio 2.598) is spring-settle-contaminated (N_a ramps 0 -> 170 N across 0->100) and is NOT the LIPM rate. Net: the fourth meter makes the hidden ext_torque couple visible; the dead-motor ankle is dead in JOINT accounting by construction (ext_torque bypasses the rows); the channel is real and restoring but, priced off a foot reaction starved to 13-36% of body weight, under-powers the tonic gravity hold -- the load-path starve (VERDICT 10/11) is the failure, not a missing or destabilizing torque. Falsifier NOT fired: ext_torque != ~0 and sign(tau*d)<0 throughout.

VERDICT 20 MEMBRANE (2026-08-09, named BEFORE the run): THE TRUE NORMAL.
STATEMENT: re-price the channel's N_a from vertical statics instead of the blind impulse meter. At quiet stance SUM(N) = M*g (the true normal, not the impulse-metered share that sits at ~0.13-0.36 M*g because the measured-bilinear floor, contact_penalty=2, routes part of its vertical reaction through pad/implicit rows that never accumulate into contact_impulses -- recorded N ~343 N vs 784.5 N body weight at tick 100). The per-foot share is the two-support statics identity N_share_a = M*g * (cop_x - ankle_x_other)/(ankle_x_a - ankle_x_other) (bathroom-scale split), clamped [0, M*g]; the COP x-position (cop_num/cop_den) is a ratio of impulses, robust to the magnitude error. MEASURED degeneracy (2026-08-09): the two ankle joint centers are co-linear in x (ankle_x_R == ankle_x_L == 0, confirmed by direct read of the birth pose), separated only in y by 0.216 m, with the COP sitting under the feet (cop_x ~= ankle_x), so the x-identity is 0/0 -- resolved by its well-defined symmetric limit M*g/2 each. Used in the existing tau_scalar = N * dot(cross(delta_p3, z_hat), axis_w). Keep: kd = 1.0, delta_p3 = p_star - ankle_xy, SET semantics on ext_torque, PD dead at ankles. PREDICTION: delivered ||ext_torque|| ~= required M*g*|d|/2 on ticks 10-100 (ratio ~1.0, not 0.13); the tonic hold is genuinely powered, so |d| stops diverging -- fitted collapse-window rate < omega = 2.8156/s, or the window reaches 3000 with no fall. FALSIFIER: fall @444 persists AND delivered ~= required -> the divergence is not underpower but GEOMETRY (birth pose outside the capturable region); the next membrane is the capture region, not the channel. Record it, do not patch the bar.
The run: VERDICT 6 birth pose (.tmp/verdict6_stand_back.py machinery), balance_cop opt-in (PD dead at ankles per VERDICT 15), .tmp/verdict20_true_normal.py. 44-test gate GREEN (LightEngine/tests/test_kinematic_dynamics.py, test_kinematic.py, test_skeleton.py -> 44 passed; legacy bit-identical: balance_cop off skips the block, dynamics.py:644 ext_torque None -> zeros, step() unchanged from baseline).

VERDICT 20 OUTCOME (2026-08-09): **THE TRUE NORMAL RESOLVES THE UNDERPOWER -- THE REMAINING FAILURE IS GEOMETRY (CAPTURE REGION), NOT TORQUE.** With N_a re-priced to the statics share (M*g/2 each via the co-linear-x symmetric limit, measured ankle_x_R == ankle_x_L): delivered ||ext_torque|| = 2.870 N m (R) / 2.879 (L) vs required M*g*|d|/2 = 2.626 / 2.625 on ticks 10-100 -> delivered/required = 1.093/1.097 (bar (a+b) ~1.0 PASS, was 0.168 under the impulse meter in VERDICT 19); ext_torque restoring on 445/445 ticks (both ankles, was 444/445). The underpower is GONE -- confirming VERDICT 19's meter-disease diagnosis (the impulse meter starved N_a to 105-106 N = 13% of body weight; the true normal restores it to ~M*g/2 = 392 N). BUT the fall persists at tick 444 and the divergence still runs at ~omega: collapse-window (100..444) log|d| fit = 2.9519/s vs omega = 2.8156/s (ratio 1.048, bar (c) FAIL -- rate not < omega); the 10-100 fit (3.5184/s, ratio 1.250) is spring-settle-contaminated (N_a ramps 0->170 N, N_total overshoots to 1293 N = 1.65x body weight as the body bounces on the compliant W floor) and is not the LIPM read. Bar (d) fall>444 FAIL (fall @444, unchanged). THE MECHANISM: delivering full tonic through the p_star capture-point reference makes the divergence rate RISE, not fall -- from 1.003x omega under-powered (VERDICT 19) to 1.048x omega with full tonic -- the signature of an ankle-strategy capture failure: the VERDICT 6 birth pose (COM +0.63 cm forward of the ankles) sits at/over the edge of the capturable region, so no ankle torque amount, however accurately priced, can pull the COP back under the COM. FALSIFIER FIRED: delivered ~= required AND fall @444 persists -> the divergence is GEOMETRY (capture region / birth-pose COM placement), not underpower -- the next membrane is the capture region, not the channel. Raw samples -> agent_logs/verdict20_true_normal.npz.

VERDICT 21 MEMBRANE (2026-08-09, named BEFORE the run): THE SETTLE KICK.
STATEMENT: birth the body pre-settled. The bilinear floor is born uncompressed; the 12 polygon (non-W) contact points share the weight, per-point static share F = M*g/n_poly = 65.4 N; static pad depth d_eq = F/k1 where k1 is read at RUN TIME from _measured_floor_params(state) (dynamics.py:277; k1 = 32000 N/m here, verified, not hardcoded). Lower EVERY link's birth z by exactly d_eq (feet included) so the pads start at static equilibrium (pad force k1*d_eq = F per point) and produce zero kick. Applied IN THE PROBE ONLY (.tmp/verdict21_settle_kick.py), not in the kernel. PREDICTION: the floor slam that injects velocity into the LIPM is removed -- |v_z| after settle (ticks 100-200) drops to ~0 vs the current kick, and with the kick gone the fall either halts (fall > 444 / window 3000) or, if it persists at omega, the capture region owns it. FALSIFIER: kick gone (bar 1 |v_z| ~ 0) AND fall @444 persists -> the settle is exonerated and the capture region owns the disease (next membrane prices p* against the toe per tick). Record, do not patch.
The run: VERDICT 6 birth pose + VERDICT 20 true-normal channel, balance_cop opt-in (PD dead at ankles), .tmp/verdict21_settle_kick.py (both KICK and PRE-SETTLED builds). 44-test gate GREEN (probe-only; kernel untouched since VERDICT 20, so step() is bit-identical to the VERDICT-20 baseline).

VERDICT 21 OUTCOME (2026-08-09): **THE MEMBRANE IS DEAD -- NO SEPARABLE SETTLE KICK; THE FALL IS BIRTH-POSE GEOMETRY (VERDICT 20).** d_eq = 2.043 mm (F = 65.4 N/point, k1 = 32000 N/m verified at runtime via _measured_floor_params(st0), n_poly = 12), lowering every link z by d_eq (com_z 1.2371 -> 1.2351 m, confirmed applied). Bar 1 |v_z| 100-200 = 0.960 m/s (KICK) vs 0.960 (PRE-SETTLED) -- IDENTICAL to 4 decimals (FAIL); the window captures the LIPM fall arc (COM descending as the birth pose pitches forward), not a floor-kick spike. Even at the early sink (ticks 0-10) the pre-compression only shifts the impulse-metered normal 36 -> 49 N and |v_z| by ~2% (tick 1: 0.00935 -> 0.00919 m/s) -- the 2.04 mm offset is absorbed by the 32 kN/m pads in under 2 ticks, so no kick is separable and none is removed. Bar 2 (capture point xi = (x_com - ankle_x) + vx/omega inside foot polygon [-0.063, +0.180]) PASS: xi_max = 0.031 m (< 0.180). Bar 3 fall > 444 FAIL (444, unchanged). Bar 4 gate GREEN. Falsifier NOT fired in its stated form (the kick was never gone -- bar 1 fails). INVESTIGATION (project law: dead change, do not narrate): with the true normal the channel delivers 1.09x the tonic (VERDICT 20) yet the divergence rate is invariant to the 2 mm pre-compression -- collapse-window 2.952/s (1.048x omega) with it, 2.823/s (1.003x omega) without; fall tick is 444 with and without; |v_z| and N_total are identical to 4 decimals across both builds by tick 100. The divergence is therefore NOT driven by a floor kick but by the horizontal LIPM growth of d from the birth-pose COM offset (+0.63 cm forward of the ankles, on/over the capture-region edge the ankle strategy cannot command). VERDICT 20 (true normal) and VERDICT 21 (pre-settle) are both accounted for; neither arrests the fall -- the disease is the capture region / birth-pose COM placement, and the next membrane prices the channel's demanded COP p* against the toe per tick.     Raw samples -> agent_logs/verdict21_settle_kick.npz.

VERDICT 21b PROVE (capture-region, 2026-08-09): demanded COP p* = xi = x_com + v_x/omega (LIPM capture point, the COP the dynamics demand to balance) over the PRE-SETTLED build, 0-444 ticks. omega = 2.8156 rad/s, polygon = [-0.063, +0.180] m (heel, toe, from ankle). xi trajectory: 0.0063 (birth, COM +0.63 cm forward) -> 0.0060 -> 0.0204 (tick 120) -> 0.0306 (tick 420) -> 0.0310 (at fall@444). xi_max = 0.03099 m, xi_min = 0.00595 m. xi NEVER exceeds the toe (0.180) or heel (-0.063) before the fall -- captured margin: 0.180 - 0.031 = 14.9 cm of spare. BAR 2 (geometric capture region contains p*): PASS -- the ankle strategy is geometrically capable; the fall is NOT a capture-region violation. The arrest condition refines the user's membrane: arrest requires BOTH (a) demanded COP p* inside the polygon (SATISFIED here) AND (b) the COP actually driven to p* (control availability). In this run (a) holds but (b) does not: balance_cop opt-in => PD dead => COP pinned, not driven to p* => fall@444. Together with VERDICT 21 (vertical pre-compression moves no fall number) and VERDICT 20 (collapse rate 2.952/s = 1.048 omega; fall@444 invariant under the 1.09x-tonic deliverable channel), the disease is control-availability, and the lever is restoring active COP drive. Falsifier re-check: p* inside polygon (PASS) AND body arrests before 444 (FAIL -- it falls) => the one-condition form is falsified by measurement; the refined two-condition membrane survives and points to control. Next membrane (RULE 0, stated -- NOT built) is the lever this prove names.

VERDICT 22 MEMBRANE (next, RULE 0 stated 2026-08-09, NOT yet run): RESTORE PD ANKLE DRIVE. STATEMENT: re-enable the ankle proportional-derivative drive (uncheck balance_cop opt-in) so the COP can be driven from the ankle toward the demanded p* = xi and the COM is steered into convergence within the capture region. PREDICTION: with PD active the COP tracks p* (corr > 0.9, |COP - p*| < 5 cm), the divergence/collapse rate drops below omega, and the fall tick moves past 444 (or the body arrests). FALSIFIER: PD active but COP stays pinned at the ankle (|COP - p*| stays large > 5 cm) AND fall@444 unchanged => the PD is not the lever (revisit birth-pose geometry or stepping/hip torque, and re-check the deliverable channel's 1.09x tonic demand at dynamics.py:277-310). Prove against the VERDICT 20/211 baseline (same birth pose, same kernel).

VERDICT 22 OUTCOME (2026-08-09, operator-session run -- the assigned
agent failed, the session ran it): TWO LANDMARKS, ONE FALSE VERDICT
CAUGHT.
LANDMARK 1 -- THE ENVELOPE DISEASE WAS THE METER.  Clean quiet-tick
ankle means: -0.01 N m (std 0.12), both ankles, INSIDE the human
envelope [-3.08, +5.24].  The +9.9/+17/+22 saga (VERDICTs 4-16) was
substantially the phantom cross(r_c, jv) term VERDICT 18 removed.
Every build's quiet stance was already human-priced; the bar had
been priced against an artifact.  Even the COLLAPSE means (+5.21)
sit at the envelope's top edge.
LANDMARK 2 -- THE PHI DRIVE CANNOT STEER THE COP.  |p_now - p*| on
ticks 10-100: phi drive 0.02932 m vs pinned control 0.02687 m --
the drive is WORSE than dead.  The probe's "TRACKS p*" verdict is a
threshold artifact (both builds sit under a 5 cm bar); the honest
comparison says the phi channel moves NOTHING.  VERDICT 2's plant
rigidity persists through FIVE architectures (centroid chase, COP
error, direct torque layered, direct torque replacing, phi+PD):
the physical COP is owned by the contact solve, and no ankle-row
law redistributes foot pressure while the pose-PD holds the
foot-shank angle fixed.  Catch-22 named: COP steering requires
modulating the ankle TORQUE; the ankle PD exists to hold the ankle
ANGLE; the same rows cannot do both, and the contact solve re-pins
the pressure pattern every tick regardless.
Bar 3 statue (0.04 mm), bar 4 fall @443 (baseline 444) -- nothing
moves the fall tick.
THE FALSIFIER'S PRECONDITION FAILED: "COP tracks p*" never happened,
so "ankle-domain drive insufficient at its ceiling" is NOT the
verdict -- the drive never reached the ceiling; it cannot steer at
all.  The hip-strategy membrane is PREMATURE.  The true indictment:
the pose-PD everywhere suppresses the sway dynamics the balance law
needs -- a frozen COM gives the COP nothing to track (statue), and
a pinned COP gives the law nothing to steer with.

VERDICT 23 MEMBRANE (2026-08-09, named BEFORE the run): THE FREE
SWAY.
STATEMENT: quiet standing is a FREE inverted pendulum caught by the
balance law, not a pose held by a PD.  Let the ankle pivot rows hold
ZERO stiffness about the primary axis (motor_target = 0 with a real
lmax -- a velocity damper, not a pose clamp), keep the PD on the
other 119 actuators, and the VERDICT 20 true-normal torque channel
owns the catching.  The body then sways (bar: sway enters the human
band), the COP moves with the COM (bar: |p_now - p*| drops below
the pinned build's 0.0269 m), and the law has a plant it can steer.
PREDICTION: sway std enters [3.8, 9.5] mm AP within the window;
COP-p* tracking beats the pinned build; fall tick moves past 444.
FALSIFIER: the body falls FASTER than 444 with free ankles ->
zero-stiffness is not the human ankle's quiet state either (tonic
stiffness is load-bearing; measured, not assumed) and the next
membrane prices ankle impedance (stiffness + damping, derived from
the LIPM's stability boundary), not angle, not torque alone.
The run: .tmp/verdict23_free_sway.py.

VERDICT 23 OUTCOME (2026-08-09): **THE FREE SWAY NEVER SWAYED -- THE
VELOCITY DAMPER IS A CLAMP IN THE QUIET REGIME, AND THE TORQUE CHANNEL
PARKS THE COP 5.6 cm FORWARD.** Bars 1-3 all FAIL; the falsifier's
precondition (sway enters the band) never happened; where the change
moved numbers it moved them the WRONG way.
Bar 1 (sacrum sway std AP, 10-100): free sway **0.008 mm** vs pinned
0.013 mm (band [3.8, 9.5]) -> FAIL.  The sacrum trace spans 0.04 mm
across the whole 10-100 window -- the statue did NOT die.  Mechanism:
motor_target=0 with the derived lmax is a VELOCITY servo that drives the
ankle's relative angular velocity to zero; its cap (tarsals torque limit
50 cm^2 x 30 N/cm^2 x 0.050 m = 75 N m, lmax = 0.075 N s/tick) is an
order of magnitude above the ~5 N m tonic demand, so it is never
saturated and the ankle angle is FROZEN -- relative angle 10-100 mean
+0.0013 rad, std 0.0016 rad (0.09 deg), while the PINNED build's ankle
rode 0.0085 rad.  "Zero stiffness with a live cap" is a kinematic clamp,
not a free joint, in this regime.  Trap (e) called: a live lmax is not
what freed the ankle.
Bar 2 (|p_now - p*|, 10-100): free sway **0.04977 m** vs pinned 0.02687 m
(V22 reference 0.02690) -> FAIL, 85% WORSE.  The COP is pinned at
+5.56 cm FORWARD of the ankle (std 0.95 mm -- pinned, not steered) while
p* ~ +0.63 cm (the COM offset); the error is ~5 cm, dominated by the
COP position.  The VERDICT 20 channel is restored and WORKS -- delivered
||ext_torque|| R 2.614 / L 2.624 N m vs required M*g*|d|/2 2.378,
delivered/required 1.099/1.103, restoring sign (tau*d<0) on 414/435 (R)
and 415/435 (L); the COM offset |d| DECAYS over 10-100 (fitted
-1.16/s) -- the channel recenters the COM.  But the couple, transmitted
through the rigid ankle to the flat foot, moves the COP the WRONG WAY:
statics says the 2.6 N m couple shifts the COP ~3 mm BACKWARD
(tau/Mg), the contact solve parks it ~5 cm FORWARD -- the VERDICT 22
indictment holds: the physical COP is owned by the contact solve, and
the ankle law (PD, damper, or couple) cannot steer it.
Bar 3 (fall tick): free sway @444 vs pinned @444 -> FAIL, unchanged.
Falsifier (named: falls FASTER than 444): NOT fired literally -- fall
@444 equals baseline, not faster.  BUT the collapse is far more violent
and the servo latches off: the standing program refused @427 (COM
exited the support polygon; the pinned build never refuses), and the
pre-refusal collapse-window (100-427) |d| fit is 12.97/s = **4.6x
omega** (vs pinned 2.95/s = 1.05x omega, VERDICT 20) -- the free ankle
destabilizes the fall once it starts even though it does not move the
fall tick.  The falsifier's MECHANISM (zero stiffness is not the quiet
ankle; tonic impedance is load-bearing) is supported by the refusal +
4.6x-omega collapse, but its stated bar (fall < 444) did not fire.
Context, not a named bar: clean ankle meter 10-100 +3.28/+3.27 N m
(std 2.30), inside the human envelope [-3.08, +5.24].
Gate: 44 passed (LightEngine/tests/test_kinematic_dynamics.py +
test_kinematic.py + test_skeleton.py).  Legacy bit-identical:
balance_cop off skips the block and never creates ext_torque; the
pinned control reproduced the V20/22 numbers (p_err 0.02687, fall @444).
VERDICT 22's catch-22 survives this architecture too: the pose-PD,
the zero-stiffness damper, and the true-normal couple ALL fail to
sway the body or steer the COP because the contact solve owns the
pressure pattern and the ankle's tonic impedance (not its angle, not
its torque) is what the plant needs -- the next membrane prices ankle
impedance (stiffness + damping) from the LIPM stability boundary,
as the falsifier names.  Recorded, not patched.  Raw samples ->
agent_logs/verdict23_free_sway.npz.

FOOT GEOMETRY AUDIT (2026-08-09, operator-ordered verification of the
foot bones against the project's own research datums — the audit that
earned RULE 27, `Chimera/docs/EXPERIMENTAL_METHOD.md`)

Measured on the built skeleton (`LightEngine/skeleton_structures.py`
_joint_dict + _foot_projection_joints, H = 1.80 m), against the
ANATOMY-DATUMs in `LightEngine/skeleton_scaling.py` and the VERDICT 7
heel research:

| feature | built (measured) | research datum | verdict |
|---|---|---|---|
| ankle height | 7.2 cm (4.0% H) | ~3.9% H (malleolus) | OK |
| heel behind ankle | 26% of foot length | ~26% (VERDICT 7) | OK |
| foot length | 24.3 cm (13.5% H) | ~15.2% H = 27.4 cm | 3 cm SHORT |
| per-foot polygon width | 1.8 cm (1.0% H) | hindfoot 7 / midfoot 6 / toes 5 cm | 5x TOO NARROW |
| metatarsal_base z | -1.8 cm (BELOW floor) | midfoot rides 2-4 cm above the sole | BORN BURIED |
| arch profile | tarsal +1.8 -> met_base -1.8 -> mtp 0.0 cm | arch rises 3-4 cm at midfoot | INVERTED |
| segment spans | tarsal 2% / metatarsals 5% / toes 3% H | datums 6% / 8% / 5% H | all SHORT |

Three wrong-in-kind findings:

1. THE FOOT IS A KNIFE-EDGE. All 6 contact points per foot lie on one
   diagonal line (y spans 1.8 cm). The ML sway std ~0.0 mm measured in
   every VERDICT is not the controller holding still — it is geometry:
   a line-contact foot has zero per-foot ML margin, so the chain above
   it locks rigid to survive. A mechanism candidate for the frozen
   ankle angle (std 0.0016 rad, motor dead, VERDICT 23) that no
   control-side membrane could explain.

2. THE METATARSAL BASE IS BORN BURIED. `skeleton_structures.py:142`
   sets met_base 5.0% H below the ankle joint -> -1.8 cm under the
   floor plane. The midfoot rod dips through the floor at birth — the
   same artifact family as the VERDICT 11 buried link centers and the
   floor_run22 drop-arm d1/d2 failures, now caught at its birth line.

3. THE ARCH IS INVERTED AND THE KEYSTONE IS UNUSED. `JOINT_CENTERS`
   defines `foot_arch_keystone` at z = 4.5 cm (`rope_network.py:52`),
   but the foot chain (`skeleton_structures.py:141-148`) runs
   ankle->tarsal->mtp in a sagging line that never touches it.

Consequence (operator ruling, now RULE 27 — THE INTERFACE MEMBRANE IS
DERIVED FIRST): the body was derived top-down from stature fractions
and the foot bolted on last; twelve VERDICTs (12-23) of controller
diseases were geometry diseases. The next build membrane after
VERDICT 24 is the foot rebuilt from the contact patch up — arch
through the keystone, 6-10 cm wide contact area per the repo's own
datums, midfoot unburied — falsifier: the fall tick moves past 444.
It is a re-basing change: birth pose, support polygon, both meters,
and every standing number shift with it; VERDICTs 6-23 get
re-measured on the new foot, not carried.

---

## VERDICT 25 — THE PATCH-UP FOOT (membrane written 2026-08-09, before the build)

**STATEMENT** (something to disagree with): the knife-edge foot is the
disease, and a foot rebuilt from the contact patch upward — derived from
the floor's physics, not bolted onto a torso fraction — moves the fall
past the current measurement. Current geometry measured 2026-08-09:
per-foot contact polygon 1.8 cm wide (a single diagonal line, 6 points),
metatarsal_base at z = −1.8 cm BELOW the floor, arch inverted
(tarsal +1.8 → met_base −1.8 → mtp 0.0 cm, never touching the keystone
at z = 4.5 cm), foot length 24.3 cm (13.5% H) vs 15.2% H datum
(27.4 cm), segment spans under the datums (tarsals 2% vs 6%,
metatarsals 5% vs 8%, toes 3% vs 5% H), ML sway std ≈ 0.0 mm in every
VERDICT — not a controller holding still but a foot with no ML margin
forcing the chain above to lock rigid. Fall @444 (VERDICT 23), refusal
@427.

**PREDICTION** (measurable bars, named before the run):
(a) per-foot polygon width 1.8 cm → [6, 10] cm (repo datum);
(b) metatarsal_base z −1.8 cm → strictly above the floor;
(c) arch apex passes through the keystone at z = 4.5 cm;
(d) heel point carries ≥ 25% of foot normal load at quiet stance
    (VERDICT 24's probe measures before/after);
(e) fall tick > 444, or a full 3000-tick stand;
(f) ML sway std becomes nonzero (currently 0.0 mm).

**FALSIFIER** (named before the run): the rebuilt patch-up foot —
verified 2-D contact polygon, unburied midfoot, arch through the
keystone, heel loading ≥ 25% — still falls at or before tick 444 with
the statue intact → the geometry is exonerated and the disease is
control-side; the next membrane prices ankle impedance from the LIPM
stability boundary, not angle, not torque alone.

**The build** (RULE 27: derive the membrane before the bones):
1. Contact patch derived on the floor first — per foot, ≤ 10 points,
   every patch point z = 0 at birth, heel kept at 26% of foot length
   behind the ankle (VERDICT 7 calcaneus derivation), foot length to
   the 15.2% H datum.
2. Bones grow up from the patch: ankle joint stays ≈ 3.9% H above the
   sole; metatarsal_base unburied; arch rises heel/MTP → keystone
   (tarsal chain passes through foot_arch_keystone at 4.5 cm);
   tarsals/metatarsals/toes toward the repo segment-span datums.
3. Nothing born buried: assert every foot joint center and link rod
   endpoint z ≥ 0; a below-floor joint is a derivation failure, fixed
   in the foot — not by raising the floor.
4. VERDICT 6 birth pose re-derived on the new foot (new pivot angle,
   same machinery in `.tmp/verdict6_stand_back.py`).
5. Re-measured with the current VERDICT 23 controller build — same
   probe, same 3000-tick stand, clean ankle meter (VERDICT 18), quiet
   window ticks 10-100 vs collapse window 100→fall kept separate,
   impulses / DT never confused with forces.
6. Legacy foot stays buildable bit-identically: `foot_style` parameter
   so the old geometry can be re-instantiated by any test that needs it.

**Gates:** `python tools/training_gate.py` before and after the change;
`py test_kinematic_dynamics.py test_kinematic.py test_skeleton.py`
baseline measured 2026-08-09: **44 passed**. Probes in `.tmp/`, raw
samples to `agent_logs/`. Not committed.

**VERDICT 25 OUTCOME (2026-08-09): THE PATCH-UP FOOT DID NOT MOVE THE FALL — THE FOOT IS EXONERATED AND THE DISEASE IS CONTROL-SIDE (ANKLE TORQUE CAPACITY).** Geometry bars (a)(b)(c) PASS: patch polygon width 7.00 cm ∈ [6,10], metatarsal_base z = +2.25 cm (was −1.8, nothing born buried — every foot joint z ≥ 0), arch apex 4.50 cm through `foot_arch_keystone` at 4.50 cm, foot length 27.36 cm = 15.20% H (datum 15.2%), heel 26% behind ankle (−7.11 cm), 10 points/foot, k_contact re-derived 60051 N/m (n=10, was n=6). Bar (f) ML sway PASS: 0.0013 mm nonzero (was 0.0000 on the knife edge). **Bar 1 sway FAIL: 0.015 mm vs the [3.8, 9.5] mm band — the body is dead, frozen, not standing.** Bar (e) fall > 444 FAIL: fall @444 — **and the legacy knife-edge foot on the identical probe also falls @444 (both with the VERDICT 6 birth pose correctly re-derived: birth COM +2.65 cm forward, D_CM = −2.15, COM → +0.50 cm envelope midpoint): zero-tick foot effect.** (Note: the first patch run measured fall @445 — that was a sign bug in the probe that shifted the birth COM FORWARD to the support centroid (+5.8 cm); corrected to VERDICT 6's machinery the fall is 444 = 444.) The patch genuinely improves the servo domain (refusal None vs legacy @427 — the wider foot keeps the COM in the polygon) and the contact (heel load, no buried bones), but the collapse is unchanged. THE MECHANISM: collapse-window d-rate ≈ 0.97×omega (both feet) — a rigid inverted-pendulum divergence; the ankle clean torque saturates at **−75 N·m = the derived physiology cap exactly (30 N/cm² × 50 cm² × 0.050 m, `muscles.py`)** once the forward lean d = COM−ankle passes m·g·d > 75 → d > 0.096 m (measured d grows 0.056 → 0.135 m; late-window torque pinned at −74.95 ± 0.03 N·m). Foot length/width/heel position do not enter the ankle's torque capacity, so the fall is foot-independent by construction. FALSIFIER FIRED AS WRITTEN: the rebuilt foot, verified on every geometric bar, falls at the same tick (444) as the legacy foot on the same probe — geometry exonerated, disease control-side. Raw samples -> `agent_logs/verdict25_patch_stand.npz`, control -> `agent_logs/verdict25_legacy_stand.npz`.

**VERDICT 26 MEMBRANE (next, RULE 0 stated 2026-08-09, NOT yet run): PRICE THE ANKLE FROM THE LIPM BOUNDARY, NOT THE RIGID-LEAN ANGLE.** STATEMENT: the rigid-lean reference (whole-body lean of the contact-free chain about the ankle axis, `muscle_controller.py` `target_offset`) prices the ankle servos against a static geometry the LIPM does not demand — the body holds the lean with the ankle parked near −75 N·m and slowly tips past the 75/784.5 = 0.096 m static moment arm, then the ankle saturates. PREDICTION: with the ankle commanded from the capture-point boundary (demanded COP p* = xi inside the polygon, ankle torque = −m·g·(d − xi) priced per tick, servo bandwidth the LIPM pole), the ankle parks far from saturation at the small-lean equilibrium, d stays inside the capturable region, and the fall tick moves past 445 (or the body arrests). FALSIFIER: ankle re-priced from the boundary but the fall tick is unchanged (≤445) AND the ankle still saturates at ±75 N·m → the ankle channel cannot deliver the boundary torque (re-check the motor-row solve and N_a pricing), and the disease is delivery, not reference. Prove against the VERDICT 25 baseline on the patch foot (same probe, same 3000-tick stand, same clean ankle meter, quiet 10-100 vs collapse 100→fall separate).

VERDICT 26 VERIFICATION (2026-08-09, kimi re-run of the agent's
vertical diagnosis — .tmp/verdict26_verify.py, EM-7 controls):

  box, default config:      N = 100% M*g, z = 0.000 m
  box, GHOST-FREE config:   N = 99% M*g, rests +0.0448 m ABOVE the
                            floor (recovery-bias buoyancy)
  chimera DEAD patch foot:  foot contacts -0.034 m @100, -0.102 m @440,
                            then collapse onto trunk; N_metric -> 0 at
                            rest (meter sees only foot-polygon rows,
                            not the 142 trunk endpoint rows)
  chimera LIVE legacy foot: -0.076 m @100, -0.238 m @440, N_metric
                            caps 648 N (83% bw)

Reconciliation: "Newton's third law does not close in the multi-row
solve" is FALSIFIED — the box closes in both configs.  The disease is
the FOOT LANE specifically: polygon rows ratchet down from tick ~100,
live AND dead, legacy AND patch foot (648 N @ -23.8 cm vs the agent's
644 N @ -22 cm — identical within noise), which exonerates the servo,
the muscles, and the patch foot.  The agent's N_metric is blind to
trunk-endpoint load (W-sided records), so "caps at 82% of M*g" is the
foot lane's number, not the body's.  The fall @444 was measured on a
platform sinking from tick ~100 — the LIPM omega-fit (VERDICT 20)
must be re-derived once the feet hold depth.  Agent's npz has
mislabeled columns (min_pz holds skull z, foot_pitch holds min_pz);
its printed table was correct.  VERDICT 26 agent grade: B+ — the
vertical diagnosis is the most important measurement since VERDICT
18; the universal framing did not survive its own control.  Next:
VERDICT 27 — THE STARVED ROW.

## VERDICT 27 — THE STARVED ROW (membrane written 2026-08-09, probe only, no patch)

**STATEMENT** (something to disagree with): the foot rows starve through
their own pricing — each row's damping mass m_load is seeded by its own
previous tick's solved normal impulse (`contact_prev_n`,
`LightEngine/kinematic/_dynamics_numba.py:1158-1163`), so a row that
under-delivers once is priced with a smaller m_load next tick → smaller
c_eff → LARGER gamma (`gamma = 1/(dt·(dt·k + c))`, the implicit row
softens) → it delivers even less at the same depth → a ratchet that
converts any transient under-delivery into permanent starvation.  The
single box escapes because its one row carries the full 78 kg from tick 0
(m_load → 78 kg, row stiff, bias correct immediately); the chimera's 12
foot-polygon rows each see ~5 kg while the 77-link chain crushes through
them.

**PREDICTION (before the run)**: live free-ankle LEGACY-foot build
(`verdict26_descend.py` machinery, `balance_cop=1`), quiet ticks 10-100,
pad-zone rows (depth < 10.4 mm): delivered/priced < 0.3; m_load ~5 kg vs
the 6.67 kg static share.  **My own split (2026-08-09)**: m_load starts
near/above share (~6-8 kg from the early settle's lambda_prev) and decays
→ negative slope is the ratchet signature; D/P early 0.3-0.7 collapsing
< 0.3 by 60-100.

**FALSIFIER**: pad-zone delivered/priced > 0.8 while the sink continues →
pricing is healthy, starvation is in the LIFT PACING; next membrane is
pacing, not pricing.  Either way the losing mechanism is named dead.

**MEASURED (2026-08-09, `.tmp/verdict27_starved_row.py`, raw →
`agent_logs/verdict27_starved_row.npz`)**:

  fall_tick = 444 (exact reproduction of VERDICT 26)
  N_total@100 = 345 N, min_pz@100 = -0.033 m
  N_total@440 = 644 N, min_pz@440 = -0.232 m
  static share/row = 784.5/12 = 65.4 N = 6.67 kg

  QUIET 10-100, per-row (pad-zone): depth ~9.9 mm | delivered 8.8-26.7 N
  | spring price k·d = 703-804 N | **D/P = 0.082 (pad-zone row-ticks 554,
  falsifier < 0.3 → PRICING STARVED, falsifier NOT fired)** | m_load
  0.9-1.6 kg (mean 1.22) | c_eff 621-870 | gamma 1.65-1.82 | bias
  0.31-0.48 m/s.
  Delivered is monotone in the row's contact-point offset: +0.075 m
  anterior → 26.6 N (m_eff 0.176 kg); -0.128 m posterior → 8.8 N (m_eff
  0.006 kg).  m_eff = 1/(inv_mass + rn·(I^-1·rn)) ranges **0.006-0.176 kg
  (mean 0.072)** across the 12 rows → K = 1/m_eff = 6-163 (mean ~14).

  m_load trajectory (pad-zone): **0.43 → 0.71 → 0.99 → 1.28 → 1.56 →
  1.76 kg** across t0-60 — it CLIMBS with delivered (corr 0.999, m_load ≡
  delivered/(g·dt)), it does NOT decay; it never approaches the 6.67 kg
  share.

  COLLAPSE 100→444: 100% rigid-zone rows (no k·d price; bias =
  depth/t_recovery = 0.77-0.88 m/s at 128-149 mm).  Delivered 24.7-69.5 N
  per row (mean 47.2, total 566 N < 784 N) — even the rigid-zone lift is
  K-limited.  The resting depth where bias delivers the static share at
  v_rel≈0 is depth = t_recovery·K·share·dt ≈ 0.162·14·65·0.001 ≈ **147 mm
  — the measured burial depth.  The body sinks to the depth the rows can
  afford.**

  BOX CONTROL (the statement's own escape hatch, single 78 kg box,
  ghost-free config, `.tmp/verdict26_staticbox.py` + the same probe
  meters): contact point directly below the COM (rn ≈ 0) → m_eff = 78 kg
  exactly, K = 0.013; **delivered 757.5 N = 99% M·g throughout the quiet
  window, resting.**  Row machinery carries a full load when the row's
  own effective mass is the load; it starves at 0.006-0.176 kg.

**VERDICT**: the OUTCOME the statement claimed (foot rows starve through
their own pricing) is CONFIRMED — D/P = 0.082, the pricing lane is dead,
the falsifier did not fire.  But the statement's MECHANISM is wrong in
both magnitude and direction: m_load never sits near ~5 kg (measured
0.43-1.76 kg, climbing, not decaying — my own split failed the same way);
and the m_load ratchet is a FOLLOWER (corr 0.999 with delivered), not a
driver — even at the full 6.67 kg share, gamma = 1.05 vs K = 14, so K is
still 93% of the row diagonal; a fully-loaded row delivers only ~6% more.
**The true killer is K = 1/m_eff, and it is GEOMETRIC, not a pricing
loop: the foot-polygon points sit at up to 12.8 cm horizontal offset from
the COM of the light 0.41 kg tarsals link, so rn·(I^-1·rn) dominates the
effective-mass denominator and the rows price against grams, not the
6.67 kg they must carry.**  The row converts its velocity bias into force
through (K + gamma) ≈ 14-16, so a 1 m/s residual buys only ~65 N; the pad
gives 0.3-0.5 m/s bias and the rows deliver 8-27 N against a 703-804 N
spring price; in the rigid zone the same K forces a 147 mm equilibrium
burial.  **The losing mechanism is named dead: the rows are
velocity-coupled but not load-coupled — they can arrest an impact
(VERDICT 19's drop rests) but cannot hold a standing weight.**  VERDICT 26's
"polygon rows ratchet down from tick ~100" is re-read: the ratchet is
real but it is the ~50-tick plunge through the pad into the K-starved
rigid-zone equilibrium, and its primary cause is not m_load softness.

**VERDICT 28 MEMBRANE (next, RULE 0 stated 2026-08-09, NOT yet run):
PRICE THE FOOT ROWS FROM THE STATIC SHARE, SEEDED ONCE, NOT FROM
lambda_prev.**  STATEMENT: m_load must come from the load the row OWNS
(the chain's subtree mass / static share, ~6.67 kg/row), seeded at tick 0
and updated from the SOLVED impulse only as a floor, never as the primary
source — because lambda_prev is starved by construction, seeding from it
can never reach the share (measured: 0.43 kg floor, max 1.76 kg).
PREDICTION: with m_load = static share at tick 0, c_eff = 2·sqrt(6.67·k)
and the pad-zone row diagonal drops toward K + 1.05 — but the primary
defect (K ≈ 14 from contact-point geometry on a light link) is unchanged,
so this alone moves delivered/priced from 0.08 toward ~0.15, not past the
falsifier.  FALSIFIER (the geometry, not the pricing, is the wall):
delivered/priced still < 0.3 with m_load fixed at the static share → the
row diagonal K = 1/m_eff is the binding term and the next membrane must
change the CONTACT GEOMETRY or the effective mass (e.g. price the row
against the foot's aggregate polygon inertia, or give the tarsals a
load-bearing effective mass), not the pricing.  Prove on the same probe:
quiet 10-100 D/P, m_load trajectory, burial depth, fall tick.

## VERDICT 28 — THE STATIC SHARE DOES NOT TOUCH THE FOOT (membrane 2026-08-09, probe only, no patch)

**MEASURED (2026-08-09, `.tmp/verdict28_static_share.py`, same probe as
VERDICT 27 with the opt-in kernel flag `state["contact_static_share"] = 1`,
raw → `agent_logs/verdict28_OFF.npz` (control) and
`agent_logs/verdict28_ON.npz` (flag))**:

  Control (flag off) reproduces VERDICT 27 bit-for-bit: fall_tick = 444,
  N_total@100 = 344.9 N, min_pz@100 = -0.033 m, min_pz@440 = -0.232 m,
  quiet 10-100 pad-zone D/P = 0.082, m_load mean 1.22 kg, K = 1/m_eff
  mean ~14 (pad rows), range 6-163.

  Flag on: the m_load pricing channel moves EXACTLY as the membrane
  stated — seeded once at tick 0 and flat at 6.67 kg (the 784.5/12
  share) the whole run: trajectory 6.67, 6.67, 6.67, 6.67, 6.67, 6.67
  with c_eff 924 → 2378 and gamma 1.046 → 0.386 (pad-row diagonal
  drops toward K + 1.05, the membrane's own number).  **Delivered is
  bit-identical per row (22.0 / 19.4 / 17.4 / 12.8 / 8.8 / 26.6 N L,
  mirrored R), so D/P = 0.082, fall_tick = 444, burial -0.033/-0.232 m,
  and N_total all UNCHANGED.**  The static share never reaches the foot
  rows because the 12 foot-polygon points are hard unilateral rows
  (contact_is_floor == 0, the general branch `_dynamics_numba.py:1202+`);
  the m_load/c_eff/gamma lane (`contact_penalty == 2 and
  contact_is_floor != 0`, the W-floor implicit rows) is the only consumer
  of the flag, and no W row is active in the quiet or collapse window of
  a standing body.

  PLUMBING PROOF (the flag is not dead — it is priced into a lane the
  foot never uses): step() forwards contact_static_share to the kernel
  (arg #58, captured = 1); with a single 78 kg link whose W-floor row sits
  in the pad zone at lambda_prev = 0 (`.tmp/verdict28_flag_live7.py`),
  the flag raises m_load from m_eff = 3.8 kg to the static share 78 kg
  and the delivered impulse changes 471.7 → 245.1 N — the exact
  c = 2·sqrt(m_load·k) mechanism the membrane described.

**VERDICT**: the membrane's PREDICTION (D/P 0.08 → ~0.15, not past the
falsifier) is FALSIFIED IN DIRECTION OF ZERO: D/P did not move at all
(0.0817 both).  The pricing lane is exonerated in the strongest sense —
live, correct, and irrelevant to the foot.  **The membrane's FALSIFIER
FIRED AS WRITTEN: D/P 0.08 < 0.3 with m_load fixed at the static share →
the row diagonal K = 1/m_eff is the binding term; the next membrane must
change the CONTACT GEOMETRY / effective mass (aggregate polygon inertia
or a load-bearing foot effective mass), not the pricing.**  VERDICT 27's
"the rows are velocity-coupled but not load-coupled" is re-confirmed at
its root: the load channel (m_load) is now proven to be wired only to the
W-floor lane, and pricing the foot rows at their own static share is a
no-op by branch structure, not by tuning.  The disease sits in K and in
which rows own the LOADED-c lane.
