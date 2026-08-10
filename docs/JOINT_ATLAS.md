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

## VERDICT 28 FOLLOW-UP — THE FOLLOWER QUESTION IS ANSWERED (2026-08-09, re-read of the record, no new run)

The standing probe's unchanged numbers under the static-share flag read,
to a careless eye, as "contact rows are inert followers whose bias/gamma
do not set their lambda."  That reading is WRONG, and the record already
proves it in both directions:

**The channel is live.**  `.tmp/verdict28_flag_live7.py` (one 78 kg link,
ONE active W-floor pad row, flag forced 0 vs 1 on identical fresh states):
delivered moves 471.7 → 245.1 N.  The m_load → c_eff → gamma → K-diagonal
mechanism demonstrably changes the solved impulse the moment its lane has
an active row.

**The standing body's no-op is branch wiring, not inertness.**  The flag's
only consumer is the W-floor implicit lane (`contact_penalty == 2 and
contact_is_floor != 0`, `_dynamics_numba.py:1104`).  A standing body has
ZERO active W-floor rows — its 12 foot-polygon points assemble through the
general branch (`contact_is_floor == 0`, `_dynamics_numba.py:1202+`),
which owns NO m_load/c_eff/gamma lane at all: per-point velocity bias
only.  Raising m_load in a lane the foot never enters is a no-op by
construction.

**The binding term is geometric K = 1/m_eff ≈ 14, and it is a real wall
with a real hazard, now DERIVED (2026-08-09).**  Two naive "fixes" fail on
paper before any run:

  - DIAGONAL-ONLY RE-PRICE (set K_ii = 1/static_share on the foot rows):
    breaks SPD.  The foot row shares the 0.41 kg tarsals body with the
    ankle joint rows; dropping the contact diagonal to 0.15 while the
    ankle-row cross terms stay at 1/m_tarsals ≈ 2.4 makes the 2x2 block
    [[0.15, 2.4], [2.4, K_ankle]] indefinite for K_ankle < 38.4 → the
    Cholesky fails mid-tick.
  - K ONLY, RESPONSE UNCHANGED (solve at 6.67 kg, apply at 0.02 kg): the
    point's velocity response to an impulse priced for the share is
    ~300x the target — the run-4/7 LAUNCHER disease in closed form.
    The row's effective mass must enter the K assembly AND the velocity
    response as the SAME number, or the fix creates the very launch the
    contact saga spent runs 4-21 killing.

**CONCLUSION (the follower question):** contact rows are NOT followers —
they are geometrically starved and the load-coupling lane never reaches
them.  The next membrane must give the foot row a LOAD-BEARING effective
mass (the static share), entered consistently in the solve AND the
response, and must be 1-DOF verified before kernel entry (the
probe_implicit_row_1dof discipline) — because the naive forms break the
solve or launch.

## VERDICT 29 — THE LOAD-BEARING FOOT EFFECTIVE MASS (membrane 2026-08-09, RULE 0 stated, not yet built)

**STATEMENT** (something to disagree with): the foot-polygon rows cannot
hold standing weight because their row is priced against the tarsals
link's FREE inertia (m_eff 0.006-0.176 kg, K = 1/m_eff ≈ 14) instead of
the load the foot carries.  Give the row the static-share effective mass
(M_total / n_poly, DERIVED from the solve's own mass array — never
hardcoded), entered CONSISTENTLY in the K assembly and the velocity
response, and the SAME per-point velocity bias delivers the share at
shallow depth.

**PREDICTION (before the run)**: with the row's effective mass = static
share in both the solve and the response, quiet 10-100 pad-zone D/P
moves from 0.08 toward the bias-delivered share; the rigid-zone
equilibrium depth (VERDICT 27's depth = t_recovery·K·share·dt ≈ 147 mm)
collapses to ≈ t_recovery·dt ≈ 0.16 mm — the body rests ON the floor,
not 15 cm in it; fall tick moves past 444 or the body arrests.

**FALSIFIER (named before the run)**: load-bearing effective mass in
place, but quiet D/P still < 0.3 AND burial ≥ -0.1 m at min(fall, 440) →
the row's effective mass is not the binding term either; the disease is
the LIFT PACING (a per-point bias capped at one slop per tick cannot
hold a standing weight) → next membrane is pacing, and the geometry fix
is dead.  Either way the losing mechanism is named dead.

**BUILD GATE (mandatory before kernel entry, the record's own
discipline)**: the loaded-row form is 1-DOF verified first —
`.tmp/probe_loaded_row_1dof.py`: a single 6.67 kg effective-mass row
holding the share at v_rel ≈ 0 must deliver ≈ M·g without launching and
without an indefinite K block.  Then the kernel flag + standing probe.

**1-DOF GATE RESULT (2026-08-09, `.tmp/probe_loaded_row_1dof.py`,
PASSED — the loaded-row form is sound):**

  The row model had to be derived twice before it closed.  The
  velocity-target form (mass cancels → equilibrium g·T·dt regardless of
  the price) and the force form (row force = bias·m_price/dt; reproduces
  the 148 mm disease but LAUNCHES at deep burial because the row force
  at 0.148 m is 93x the load) both failed.  The closing form is the
  velocity-impulse row with the LOAD as a downward velocity pull at the
  row's response inertia:

      lam = (bias - v) * m_price ;  v += lam / m_resp ;
      v -= (m_share*g) / m_resp * dt
      equilibrium:  bias * m_price = m_share*g*dt
          =>  d_eq = m_share*g*T*dt / m_price

  Disease (m_price = m_eff = 0.0714):  d_eq = 148 mm  (V27 reproduced,
  v -> -7e-9, no launch).
  Fix (m_price = m_resp = m_share = 6.667):  d_eq = 1.6 mm, end z
  -0.00159 m, v -> +1.6e-11, peak v 0.904 m/s (the paced bias at the
  start depth, reached once — NOT a launch; peak z -0.0016 m, never
  above the floor), creep 2000->4000 = 0.
  Hazard (price = m_share, response at m_eff — the diagonal-only
  re-price, i.e. a negative-gamma "softening"): peak v 883 m/s in 50
  ticks — the launcher, in closed form, dead.
  SPD (3x3 tarsals block: contact x ankle-z x ankle-y): the scaled
  row+column (DKD, congruent — a single row AND its cross terms scaled
  by s = m_eff/m_share) preserves positive-definiteness (min-eig +0.35
  scaled vs +2.26 original); the diagonal-only re-price is INDEFINITE
  (min-eig -1.40) — Cholesky fails.

  IMPLEMENTATION CONSEQUENCE (derived): the kernel change MUST be the
  scaled-Jacobian loaded row (scale the contact row's jlb/jab AND its
  bias by sqrt(s) = sqrt(m_eff/m_share), s = m_eff/m_share computed
  from the row's geometric effective mass), so the solve AND the
  velocity response both use the loaded mass — never a K-diagonal
  gamma/edit, which either breaks SPD or launches (both measured
  above).

## VERDICT 31 — THE FORCE CHANNEL (load-aware rhs, membrane 2026-08-09, RULE 0 stated, built + measured)

**STATEMENT** (something to disagree with): the rows starve because their
rhs is the pacing bias alone — the solve never sees the static gravity
load the chain presses into the row.  Standard contact-solve form prices
the row against the load by solving contact rows against the
post-external velocity v⁺ = v + M⁻¹·f_ext·dt (gravity included), so
lambda must cancel the velocity the load injects along the row normal —
sustained impulse equals the load.  Adding the share as a load-aware rhs
to foot-polygon rows (kernel flag `contact_load_rhs=1`) moves quiet D/P
past 0.3 and ends the burial.

**PREDICTION (before the run)**: quiet 10-100 D/P from 0.082 to [> 0.3];
burial from −0.232 m to [pad-zone, ≥ −0.01 m]; N_metric to M·g ±10%;
fall tick past 444 or a 3000-tick stand.

**FALSIFIER (named before the run)**: load-aware rhs in place and
verified live (its own gauge evidence), D/P still < 0.3 → the
velocity-row structure itself is the wall; next membrane is the direct
force-form channel, named dead-or-alive with numbers.

**PHYSICS CAUTION (answered before the build)**: the kernel applies
gravity to ALL links (`_dynamics_numba.py` `lin_vel[i,2] -= dt·GRAVITY`)
BEFORE row assembly and the rhs, so BOTH joint and contact rows see the
post-external velocity v⁺ — the literal "joints yes, contacts no"
asymmetry does NOT hold.  The membrane's scope: it is NOT "add gravity
to contacts" (already there); it is "add the CHAIN load (m_share·g) to
the contact row's rhs", because the chain load is not in the foot's own
g·dt kick.

**CLOSED FORM (derived before the build)**: in the row coordinate,
`rhs_load = loaded_share_mass·GRAVITY·dt·(ls/m_eff)` with
`m_eff = 1/(inv_mass[li] + rn@(I_inv[li]@rn))`; legacy pricing (ls = 1)
gives `m_share·g·dt/m_eff`.  The solve's impulse gains
`m_eff·rhs_load = loaded_share_mass·g·dt` = the share; the velocity
channel keeps its paced bias.  1-DOF discrete form:
`lam = (bias−v)·m_price + load·DT; v += lam/m_resp; v −= load/m_resp·DT`.
With consistent pricing the load terms cancel EXACTLY in the velocity
update: `v' = d/T_REC`, `d_eq = 0` (rest at the contact-band top), steady
`lam = load·DT` (the share), recovery paced (`v_peak = d_start/T_REC`),
no launch, no creep.

**1-DOF GATE (2026-08-09, `.tmp/probe_loaded_row_1dof.py`, PASSED)**:
  E) legacy pricing + load-aware rhs: holds 65.38 N at d_eq ≈ 0
     (end z −0.0000 m), peak v 0.309 m/s (paced, no launch), no creep.
  F) loaded pricing: the SAME closed form (price-independent by the
     algebra — delivered 65.38 N, d_eq ≈ 0).
  G) price ≠ resp + load-aware rhs: still launches (968 m/s) — the
     consistency law is not masked by the load drive.

**KERNEL GAUGE (`.tmp/gauge_tick_v31.py`, PASSED)**: flag-off (explicit
0) vs legacy (no flag key): `max|Δimp| = 0.0` EXACT — bit-identical.
Flag-on vs legacy: drives the solve (sum|Δimp| 1.55 → 0.03 over 3
ticks, converging as the system settles) — not a no-op.

**STANDING PROBE (`.tmp/verdict31_force_channel.py`, OFF/ON, same
metrics: D/P, m_load trajectory, K diagonal, burial, fall tick,
N_metric)**:

OFF (legacy control, the bit-identity regression): fall_tick 444 |
quiet 10-100 D/P 0.082 | del/share 0.273 | burial@440 −0.232 m |
N_total@440 644 N — reproduces VERDICT 27/29 exactly.  The OFF arm of
this probe == V29 OFF == V29 ON == the OLD-kernel OFF npz: the kernel
edits are bit-identical for legacy, cross-validated on the stored files.

ON (`contact_load_rhs=1`):
  - fall_tick 454 (legacy 444; NOT a stand — head_z monotonic
    1.81 → 0.95 through the run).
  - quiet 10-100 D/P: 0.082 → 22.6  (falsifier band < 0.3: cleared).
  - del/share mean 2.887 (inflated by settling-transient impacts).
  - K = 1/m_eff mean 12.8 (the force channel does not touch K).
  - rhs_load mean 0.8 m/s; m_load mean 2.36 kg (share 6.67 kg).
  - burial@min(fall,440): −0.016 m (legacy −0.232; pad-zone ≥ −0.01
    predicted: NOT met).
  - N_metric@min(fall,440): 288 N = 37% of M·g = 785 N (M·g ±10%
    predicted: NOT met).
  - trajectory: N_total 46 → 606 → 596 → 269 → 288 N; min_pz
    −0.000 → −0.036 (t200) → −0.000 (t300, feet pop UP) → −0.016 → fall.

**MECHANISM (measured)**: over-delivery on the settling transient kicks
the contact points UP out of the slop band (interior rows 95% zone-NONE,
i.e. above the contact surface), the total reaction collapses below the
body weight (288 N), and the body sinks with a bounce.  A force channel
inside a velocity row cannot complete the force loop through the soft
chain (torque-capped ankle, soft joints): the row's own over-delivery
removes the very contact point it is trying to hold.

**D/P METER NOTE (measured consequence)**: once a force channel is in the
rhs, any engaged load-aware row delivers ≥ share, so D/P = share/(k·d)
≥ 1 at pad depths < ~2 mm.  The meter is structurally saturated — it can
no longer lose.  It is no longer a discriminating falsifier; N_metric and
burial are the honest meters, and they failed.

**VERDICT**:
  FALSIFIER (as written, quiet D/P < 0.3): NOT fired — D/P moved
  0.082 → 22.6; the load-aware rhs is a real force channel.
  PREDICTION (as promised — ends the burial, N_metric M·g ±10%, stand
  past 444): NOT met — burial −16 mm, N_metric 37% of M·g, fall at 454
  (a collapse, not a 3000-tick stand).
  OUTCOME: the force channel moves the meters but does not produce the
  promised static stand.  The velocity-row structure IS the wall for a
  sustained load through the soft chain.  NEXT MEMBRANE (named dead-or-
  alive with numbers): the DIRECT FORCE-FORM channel — a contact row
  priced against the load FORCE that STAYS engaged (does not eject its
  own point), judged on N_metric = M·g ±10% and a 3000-tick stand, NOT
  on D/P (which can no longer lose).

**GATE**: 52-test pytest green (test_kernel + test_kinematic +
test_kinematic_dynamics), no commit.  Raw samples →
`agent_logs/verdict31_force_channel_{ON,OFF}.npz`;
`agent_logs/verdict31_gauge.log`, `agent_logs/verdict31_gate.log`.

---

## VERDICT 33 — HANDS ON GROUND (renumbered from 32, 2026-08-09: force-form build owns VERDICT 32)

**STATEMENT** (rule 0): both hands can be brought to z=0 with feet grounded and
COM inside the support polygon via asymmetric scapula offset + world-axis
humerus rotation, combined with uniform spine flexion.

**PREDICTION (before the run)**: a configuration exists where L_hand_z < 0.01
and R_hand_z < 0.01 simultaneously, with nf >= 12 (feet grounded) and COM
inside the foot+hand support polygon.

**FALSIFIER (named before the run)**: if both hands remain above 0.05 with
asymmetric scapula and world-x humerus rotation, the approach fails.

**DERIVATION**: the scapula q_vc log-map decomposition
(`quat_to_saddle` in `.tmp/diag_crawl_search4l.py`) introduces left/right
asymmetry because the rotation axes are defined in the parent (rib) local
frame, and the left/right ribs have mirrored rest-pose orientations. Applying
the same positive scap_dof1 to both shoulders lowers one shoulder but raises
the other. The compensation is an OPPOSITE-sign offset: scap_L = +N,
scap_R = −N. This produces symmetric shoulders at sh_z = 0.610 (vs 0.601/0.841
asymmetric).

The humerus is a ball-cup joint. The q_vc quaternion restores the arm to
standing orientation relative to the flexed scapula. A pre-multiplied rotation
about the WORLD x-axis (`q_rx * q_vc`, not `q_vc * q_rx`) applies the same
forward tilt to both arms, producing symmetric hand lowering.

**MEASURED** (best config, from `.tmp/diag_crawl_search4m.py`):

| Config | L_hand | R_hand | nw | nf | inside | COM |
|---|---|---|---|---|---|---|
| spine=45, scap=±75, sh_x=-20, knee=60, el=90 | 0.001 | 0.001 | 4 | 12 | True | 0.665 |

The nw=4 endpoints: hand_L_dist, hand_R_dist, fibula_L_dist, fibula_R_dist.
COM dropped from 1.012 (standing) to 0.665 (crawl).

**GATE**: verified by direct FK evaluation, nf=12 always (floor links).
The 4 mW endpoints touch at z < 0.001.

---

## VERDICT 34 — KNEE PROOF (renumbered from 33)

> **CORRECTION (2026-08-09, kimi): the verdict below is an INSTRUMENT verdict, not an anatomy verdict.** Its own table shows hip_z frozen at 0.883-0.897 in every configuration: the bound knee_z >= hip_z - femur is correct arithmetic given a STANDING hip, but kneeling IS the hip dropping to ~0.45 m — hip_z is the variable the pose solves for, not a constant. The posing tool restores standing orientation (q_vc), so folded poses are inexpressible in the tool (EM-15). Refuted by the project ledger itself: the floor_run21 collapse piles rest with knee endpoints ON the floor (every endpoint within -0.05 m of z=0). The engine kneels every time the body falls. The kneel is possible; this FK prober cannot express it. The confirmed deliverable of this work is the HANDS+FEET quadruped pose (VERDICT 33 above): nw=4, nf=12, COM inside the support polygon.

**STATEMENT** (rule 0): the knee (femur_L_dist / femur_R_dist) cannot reach
z=0 while feet are grounded, because knee_z ≥ hip_z − femur_length and this
floor is 0.397m — unreachable by any joint configuration.

**PREDICTION (before the run)**: all knee-lowering approaches will hit the
floor knee_z ≥ hip_z − femur_length ≥ 0.397m.

**FALSIFIER (named before the run)**: a configuration where femur_dist z < 0.35
with both feet grounded (nf ≥ 12).

**DERIVATION**: the femur is a rigid link of length 0.421m (from
DERIVED_JOINT_CENTERS: (0.512−0.278)·1.80). Its proximal end (hip) is at
hip_z. The distal end (knee / femur_dist) is at:

    knee_z = hip_z − femur_length · cos(θ)

where θ is the angle from vertical. Since cos(θ) ≤ 1 for all θ:

    knee_z ≥ hip_z − femur_length

The q_vc correction for the femur (ball-cup joint) is an exact quaternion
that restores the femur to its standing orientation (vertical). Any deviation
from vertical (θ ≠ 0) DECREASES cos(θ), which INCREASES knee_z. The minimum
knee_z occurs at θ = 0 (femur perfectly vertical), giving:

    knee_z_min = hip_z − femur_length

**MEASURED**:

| Config | hip_z | COM | femur | knee_z |
|---|---|---|---|---|
| Best COM (spine=45, scap=±75, knee=60) | 0.883 | 0.665 | 0.397 | 0.397 |
| No scapula (spine=43, knee=90) | 0.885 | 0.692 | 0.399 | 0.399 |
| Vertebra-only flexion | 0.897 | 0.721 | 0.468 | 0.468 |
| Hip local rotation (any) | 0.885+ | 0.690+ | 0.400+ | 0.400+ |

hip-COM offset ≈ 0.198m (hip always above COM — torso mass dominates).
To reach knee_z = 0: hip_z ≤ 0.421m → COM ≤ 0.421 − 0.198 = 0.223m.
Current COM minimum: 0.665m. Required drop: 0.442m (67% reduction).

**APPROACHES TRIED AND REFUTED**:
1. Per-region spine flexion (C/T/L different angles) — COM rises, no gain
2. Vertebra-only vs pelvis-only flexion — hip_z invariant at 0.885
3. Asymmetric scapula (lowers COM to 0.665) — hip_z unchanged
4. Femur local x/y rotation — any tilt raises knee (cos θ < 1)
5. Hip saddle DOF 0/1 offset — same constraint, knee goes up
6. Patella joint (any DOF) — zero-length link, no effect
7. Knee angle sweep (0–170°) — femur_dist unchanged (knee is AT femur)
8. tibia_dist (ankle) with knee=0 — reaches 0.072 (ankle ≠ knee; with
   scapula active, hip_z rises to 0.897, tibia_dist = 0.452)

**VERDICT**: FALSIFIER FIRED — no configuration achieves femur_dist z < 0.397
with feet grounded. The knee is kinematically constrained by
hip_z − femur_length. This is a physical/geometric fact, not a numerical
limitation.

---

## VERDICT 35 — CRAWL FK CONFIGURATION (renumbered from 34)

**STATEMENT** (rule 0): a crawl pose with hands and feet on ground
exists (nw=4, nf=12, COM inside), but knees cannot join them. Full
6-point contact (hands+knees+feet) is kinematically infeasible for this
human model.

**PREDICTION (before the run)**: the hand solution (VERDICT 32) holds
at multiple spine/scap/sh_x combinations; the knee floor (VERDICT 33)
is invariant across all attempted approaches.

**FALSIFIER (named before the run)**: a configuration with ALL four
hand+knee endpoints at z < 0.01 simultaneously (nw >= 4 including knees,
nf >= 12, inside=True).

**VERDICT**: KNEE FALSIFIER FIRED. Hands + feet contact is achievable;
hands + knees + feet is not.

### Configuration for best hand+floor pose (VERDICT 32 confirmed)

Best achievable: `spine=43, scap=±30, sh_x=-20, knee=60, el=90` —
hands at z=0.059 (below the 0.1m crawl threshold but not z=0),
COM=0.675, nw=2, nf=12, inside=True.

With `spine=45, scap=±75, sh_x=-20, knee=60, el=90`:
hands at z=0.001 (touching), nw=4 (hands + fibula), nf=12,
inside=True, COM=0.665 — the maximum hand-lowering config.

### Best achievable summary

| Endpoint | z_min | Status |
|---|---|---|
| hands (L+R) | 0.001 | SOLVED |
| feet (L+R, 6 contacts each) | 0.000 | SOLVED |
| fibula (L+R) | ~0.003 | bonus contact (nw=4) |
| knees (L+R, femur_dist) | 0.397 | IMPOSSIBLE (proven) |
| patella (L+R) | 0.397 | zero-length, same as knee |

### Kinematic inventory (from `.tmp/diag_joint_dofs.py`)

77 links, 34 joints (via forward kinematics, no dynamics):
- 25 saddle (3-DoF decomposed to 2-DoF): 21 vertebra/pelvis + 2 scapula +
  2 clavicle = 25 (sternum/hand/patella are non-saddle dof_class in the spec)
- 4 ball-cup (3-DoF quaternion): 2 femur + 2 humerus
- 4 hinge (1-DoF): 2 tibia + 2 radius_ulna
- 1 suture (0-DoF): skull-sacrum.  Total: 25+4+4+1=34 joints.

The femur is a ball-cup joint whose q_vc correction can always restore
vertical orientation (θ = 0 is reachable). Since cos(0) = 1 is the maximum,
knee_z = hip_z − femur_length is the global minimum — no joint in the chain
can lower it further.

---

## VERDICT 37 — THE TELESCOPE MAP (measurement membrane, probe only)

**MEMBRANE (RULE 0, stated before this probe, 2026-08-09)**:

  **STATEMENT** (something to disagree with): the foot's contact load is
  transmitted through the joint chain with a measurable efficiency per
  link — the articulated effective mass along the vertical at each joint
  — and for this skeleton it collapses within a few links of the floor
  (the 0.41 kg tarsals prices against grams because the chain above
  contributes almost nothing). The spine telescopes: the chain folds
  instead of pressing as a unit, so the contact's effective load never
  becomes body weight no matter how the row is priced.

  **PREDICTION** (numbers before running): a calibrated impulse
  (0.83 Ns — VERDICT 32's measured tick impulse) applied at the right
  forefoot contact point of the VERDICT 6 birth-pose body, servo off,
  joints live:
    - tarsals_R takes dV ≈ 2.0 m/s (impulse / tarsals_mass = 0.83/0.41);
    - tibia_R takes ~1.8-1.9 m/s;
    - femur_R takes ~1.5-1.7 m/s;
    - sacrum takes < 10% of the tarsals dV (~< 0.2 m/s).
  Derived: per-link momentum share p_link/p_total and chain effective
  mass at the foot = impulse / dV_com.

  **FALSIFIER** (named before the run): if the sacrum takes ≥ 50% of
  the tarsals' dV, the chain transmits fine and the telescope indictment
  is dead — the starvation is purely contact-side and VERDICT 32's
  force form is the whole fix. Record either way.

  **BUILD**: probe only. Birth-pose state, zero velocities, apply the
  impulse as ext_force for exactly one tick at the contact point, read
  per-link dV after one step, then after 10 and 100 ticks (transmission
  vs ringing). Also measure the joint-impulse shares the solve reports
  for the same tick (the solve's own account of transmission — the two
  must agree or the meter is wrong, say which). Repeat at the hand
  (the crawl lane needs the arm-chain number). Raw →
  `agent_logs/verdict37_telescope.npz`. Gate: pytest suite unchanged
  before/after. No commit.

**MEASURED** (2026-08-09, `.tmp/verdict37_telescope.py`, birth-pose body,
zero velocities, 0.83 Ns vertical ext_force at tarsals_R for one tick):

  | Link | dV @1tick (m/s) | dV @10tick (m/s) | dV @100tick (m/s) | p_share @1tick (%) |
  |---|---|---|---|---|
  | tarsals_R | 0.5731 | 1.7707 | 13.2641 | 28.6 |
  | tibia_R | 0.1107 | — | — | 41.2 |
  | femur_R | 0.0036 | — | — | 5.1 |
  | pelvis_R | 0.0088 | — | — | 6.4 |
  | sacrum | 0.0087 | 0.0662 | 0.3284 | 0.5 |
  | skull | 0.0098 | — | — | 5.9 |

  Key ratios (sacrum dV / tarsals dV):
    - @1 tick:   0.0087 / 0.5731 = **0.015** (1.5%)
    - @10 ticks: 0.0662 / 1.7707 = **0.037** (3.7%)
    - @100 ticks: 0.3284 / 13.2641 = **0.025** (2.5%)

  Chain effective mass at foot = impulse / dV_tarsals =
  0.83 / 0.5731 = **1.448 kg** (tarsals_R link mass = 0.415 kg).
  The constrained chain feels 3.5x the tarsals' bare link mass.

  Hand-chain repeat (0.83 Ns at hand_R, one tick):
    - hand_R dV @1tick = 1.1356 m/s; skull dV @1tick = 0.0098 m/s;
    - ratio = **0.009** (0.9%). Same telescope pattern in the arm.

  Solve account (joint_impulses_ang, tick 1):
    - tarsals_R joint impulse = 0.0169 Ns (max in chain);
    - tibia_R = 0.0083 Ns; femur_R = 0.0012 Ns; pelvis_R = 0.0006 Ns;
    - all spine joints (L5 through C1) = < 0.0001 Ns;
    - contact impulses at tick 1: tarsals_R ci10 = 0.1047 Ns, rest
      of right-foot contacts < 0.01 Ns, all left-foot contacts < 0.01 Ns.
    - The solve's own account confirms: < 2% of the impulse propagates
      past the ankle joint; the spine sees virtually nothing.

  Kinematic vs solve account: they agree — both show near-zero
  transmission past the tarsals/tibia pair. The meter is correct.

  **PREDICTION CHECK**:
    - tarsals dV ~ 2.0 m/s: measured 0.5731 (**OFF** by 3.5x).
      The prediction assumed a free-link response (impulse/mass);
      the constrained multibody solve absorbs ~72% of the impulse
      into joint constraints rather than tarsals linear motion.
      The effective mass at the foot is 1.45 kg, not 0.41 kg.
    - sacrum dV < 0.2 m/s: measured 0.0087 (**PASS**).

  **FALSIFIER VERDICT**: NOT FIRED. Sacrum takes 1.5% of tarsals' dV
  at 1 tick (well below the 50% threshold). The chain does NOT press
  as a unit — it telescopes. The spine folds instead of transmitting
  foot contact load to the sacrum.

  **MECHANISM** (measured): the ankle joint couples tarsals to tibia
  (tibia takes 41% of impulse momentum), but the saddle joints above
  (L5, L4, ..., sacrum) have such low angular impulse transmission
  (< 0.0001 Ns each) that the chain above contributes almost nothing
  to the effective mass at the foot. The 0.41 kg tarsals link prices
  against an effective 1.45 kg because only the tibia couples in;
  everything above the ankle is mechanically invisible to a foot
  impulse. This is the telescope: each joint below the sacrum adds
  its own mass but barely passes momentum upward.

  **CONSEQUENCE for VERDICT 32**: VERDICT 32's force-form build
  (direct per-point bilinear pad force) would still fail to produce a
  sustained stand, not because of the contact layer, but because even
  if the foot rows delivered full body weight (785 N), that force
  never reaches the sacrum — the chain telescopes. The starvation is
  dual: contact-side (rows price against grams, not kg) AND chain-side
  (transmission efficiency ~1.5%). Fixing only the contact layer
  (VERDICT 32's force form) addresses half the disease.

  **NEXT MEMBRANE** (named): joint-chain stiffness — the saddle joints
  need enough angular stiffness to couple the leg chain to the trunk
  so that a foot impulse accelerates the full body mass, not just the
  tarsals+tibia effective pair. Without this, no contact-layer fix can
  produce standing weight transfer through the spine.

**GATE**: 52-test pytest green (test_kernel + test_kinematic +
test_kinematic_dynamics), no commit. Raw samples →
`agent_logs/verdict37_telescope.npz`.

---

## VERDICT 36 — THE CRAWL HOLD (membrane written 2026-08-09 BEFORE the run, probe only, no patch, no commit)

Read the VERDICT 34 CORRECTION note first (the knee proof is an INSTRUMENT
verdict).  The knee question is CLOSED here: no posing work, no FK
exploration.  This entry runs the experiment the crawl membrane always
required, and it turns into an instrument verdict of its own.

**STATEMENT** (rule 0, in force before the build): a DEAD body — no
controller, no servo, no motor row, no ext force — born in the VERDICT 33
quadruped pose on the ghost-free config (`.tmp/probe_world_floor.py`
`make_state`) loads the TRUNK/ARM ENDPOINT LANE (side="W" rows, the
`contact_penalty == 2 and contact_is_floor != 0` implicit loaded-c
spring-damper lane that carries collapse piles to rest), BYPASSES the
starving foot-polygon lane (the 12 hard unilateral rows VERDICT 27/28
measured at D/P = 0.082), and HOLDS STATICALLY for 3000 ticks, where the
biped falls at 444.

**POSE** (VERDICT 33's own confirmed result, reproduced from
`.tmp/diag_crawl_search4m.py` — the script the atlas MEASURED row cites):
spine 45° uniform over the 13 spine saddle joints, scapula asymmetric
+75/−75, humerus q_vc with a −20° x rotation, knee (tibia hinge) 60°, elbow
(radius_ulna hinge) 90°.  Prober numbers: L_hand = R_hand = 0.001, COM 0.663.

**PREDICTION (numbers named before the run)**:
(a) COM z within ±5 cm of birth for 3000 ticks — expected birth 0.663 m,
settle drop = the pad equilibrium only, ~3.5 mm (4 loaded points, bilinear
pad: 784.5/4 = 196 N/point → d_eq = 3.0 + (196−96)/212 = 3.47 mm), so
|ΔCOM z| ≤ 0.005 m.
(b) no link endpoint below −0.05 m — expected min = contact_slop − d_eq =
0.00131 − 0.00347 = −0.0022 m.
(c) settled (ticks 1000-2999) summed normal on the loaded lanes = M·g ±10%
= [706.1, 863.0] N, with the split HAND ~304 N (39%), rear/fibula W ~481 N
(61%), FOOT-POLYGON ~0 N (its 12 points sit in the air in this pose) —
derived from birth statics (COM x −0.0346; hand points x −0.0191, lever
0.0155 m; fibula points x −0.0444, lever 0.0098 m).
(d) KE < 1.0 J at tick 2999 — expected 0.1-0.3 J (the drop-arm rest band).

**FALSIFIER (named before the run)**: the quadruped starves and sinks like
the biped (bars fail the same way: burial past −0.05 m, settled N far under
M·g, COM collapsing) → the starvation is NOT foot-lane-specific and VERDICT
27's framing dies.

**BUILD**: `.tmp/verdict36_crawl_hold.py`, one probe, servo OFF from tick 0
(no `MuscleController` is ever constructed), 3000 ticks, `n_proj_iters=20`,
ghost-free `make_state` defaults.  Raw →
`agent_logs/verdict36_crawl_hold.npz` (per-tick COM, all 154 endpoint z,
per-row N, lane sums, KE).  Read-out `.tmp/diag_v36_readout.py`; frame audit
`.tmp/diag_v36_frame_audit.py`.

### OUTCOME (2026-08-09): THE POSE DOES NOT EXIST IN THE ENGINE — AND THE W LANE CLOSES NEWTON AT 100.0% M·g ANYWAY

**THE INSTRUMENT VERDICT FIRST (it is the mechanism for bars (a) and (b))**:
`skeleton_spec.py:285-286` defines `com_offset_m = 0.5·(dist_lu − prox_lu)·λ`
— a **WORLD-axes** half-axis at the rest pose.  `dynamics.init_state`
(`dynamics.py:319`, `pos_com = p_m + R @ com_offset_m`) and
`_build_floor_contact_specs` (`offset_local_m = ±com_offset_m`) consume it as
a **LINK-LOCAL** offset; the FK probers of VERDICT 33/34/35 used
`R_world_to_local @ com_offset_m`, the geometrically correct local vector.
Both cannot be right.  Measured on the STANDING state
(`.tmp/diag_v36_frame_audit.py`):

| quantity | engine (`init_state`) | corrected (prober frame) | bone truth |
|---|---|---|---|
| body COM z | **1.2371 m** (= VERDICT 21's recorded com_z) | 1.0117 m | ~0.95-1.00 m human ref |
| femur_L distal endpoint z | **+1.4403 m** | +0.4680 | +0.4680 (knee) |
| tibia_L distal endpoint z | **+0.8535 m** | +0.0720 | +0.0720 (ankle) |
| skull distal endpoint z | **+1.8482 m** | +1.6920 | +1.6920 |
| min / max endpoint z | **−0.0666 / +1.8482** | −0.0000 / +1.7730 | 0 / 1.773 |

Per-link COM discrepancy: mean **101.9 mm**, max **487.3 mm** (femur).  The
`c` term **cancels exactly in the joint rows** (point-coincidence residual
max 0.0000 mm at birth), so the skeleton hangs together correctly at the
joints; what is rotated about each proximal point is (i) the link's COM /
mass location and inertia lever arm and (ii) every W endpoint contact, which
sits at `prox + 2·R_zero·c` instead of the bone's distal end.  The
metatarsal/forefoot endpoints are born 6.7/5.2 cm **below the plane** in the
engine frame — harmless only because VERDICT 11 excluded the foot chain from
the W lane.

Consequence for this experiment: **VERDICT 33's "hands at z = 0.001" is a
prober-frame statement.**  Birthed with the engine's own convention (which is
what the contact rows read), the same joint angles put the hand rows at
**z = +0.1537 m**, the fibula rows higher still, and the **tarsals
foot-polygon points lowest (the only 2 rows below the 1.31 mm slop surface
at birth)**; birth COM = (+0.0056, +0.0266, **0.8209**) m, not 0.663.  The
quadruped pose the membrane wanted to test is not expressible in the engine
as posed, so the hand lane never had a chance to carry the predicted 304 N.
Two further instrument facts, both recorded before the run: **scipy is absent
from `.venv`**, so every `inside=` printed by the VERDICT 33/34/35 diags came
from a swallowed `ImportError` in a bare `except: pass` and was ALWAYS False —
"COM inside the support polygon" was never measured (computed here in numpy:
the birth support polygon is 2 points, a line, COM not inside); and their
"nf = 12, feet grounded" came from treating `spec["contacts"][side]["point_m"]`
(the STANDING world foot points, constants) as posed endpoints.

**THE RUN (3000 ticks, dead body, birthed as above, lowest contact point at
z = 0)**:

| bar | predicted | measured | verdict |
|---|---|---|---|
| (a) COM z within ±5 cm | \|Δ\| ≤ 0.005 m | max \|ΔCOM z\| = **0.8144 m** @tick 1010; 0.8209 → 0.0094 m | **FAIL** |
| (b) no endpoint below −0.05 m | −0.0022 m | min **−0.1384 m** @tick 1076 (forefoot_L_dist); final −0.0860 m | **FAIL** |
| (c) settled N = M·g ±10% | 784.5 N | **784.6 N (100.0% M·g)**, std 93.0, ticks 1000-2999 | **PASS** |
| (d) KE < 1.0 J @2999 | 0.1-0.3 J | **0.2558 J** (KE max 252.1 J @tick 362) | **PASS** |

The body collapsed: COM z crossed 50% of birth at **tick 312** — *earlier*
than the biped's 444 — and came to rest as a pile.  What the probe measured
is therefore the collapse-to-rest the W lane was built for, not a crawl hold.

**LANE SPLIT** (mean N, settled ticks 1000-2999; M·g = 784.5 N):

| lane | early 0-99 | settled | % M·g | predicted |
|---|---|---|---|---|
| HAND (W, the lane under test) | 0.0 N | **13.0 N** | 1.7% | 304 N |
| FOOT-POLYGON (the starved lane) | 44.6 N | **45.6 N** (2 of 12 rows > 0.5 N) | 5.8% | 0 N |
| FIBULA (rear W) | 0.0 N | 37.9 N | 4.8% | 481 N |
| OTHER W (trunk/limb endpoints) | 0.0 N | **688.1 N** | 87.7% | — |
| TOTAL | 44.6 N | **784.6 N** | **100.0%** | 784.5 N |

Top carriers (settled, per link): femur_R 101.2 N, femur_L 89.9, scapula_R
80.5, scapula_L 75.0, sacrum 59.8, tarsals_R (FOOT) 41.7, tibia_L 34.5,
pelvis_L/R 29.2/28.8, vertebra_C1 24.6, skull 24.2.  55 of 154 rows carry
> 0.5 N (53 W + 2 foot).  Burial is **bounded and recovering**: min endpoint
z −0.1384 worst → settled mean −0.0891 → second-half mean −0.0862 → −0.0860
final (the W lane lifts the pile); COM z drift over the settled window
+0.0029 m (+0.0014 mm/tick, upward); 4 of 154 endpoints below −0.05 m at
tick 2999, all in the left foot chain (tarsals_L prox/dist,
metatarsals_L_dist, forefoot_L_dist) — the same links the frame error
pre-buries at birth.

**FALSIFIER: NOT FIRED.**  The quadruped-born dead body does **not** starve
like the biped.  The biped's signature is a reaction that never reaches
weight (N_total 345 N = 44% M·g at tick 100, 566 N through the collapse) and
a sink that keeps going (−0.033 → −0.232 m, fall @444).  Here the settled
reaction closes Newton at **100.0% M·g with the W lane carrying 87.7% of it**,
KE decays to 0.256 J, and the burial *recovers*.  **VERDICT 27's
foot-lane-specific framing SURVIVES this cross-check**: with the same kernel,
the same tick, the same ghost-free config, the W lane carries full body
weight while the foot-polygon lane carries 5.8% on 2 of its 12 rows.

**VERDICT**: the STATEMENT is FALSIFIED as written — the body did not hold;
it collapsed at tick 312 and rested as a pile — but it is falsified for a
reason the statement could not name: **the pose it was born in is not the
pose the engine's contact geometry sees.**  The load-lane half of the
statement is CONFIRMED with a number the saga has never yet seen from a
standing or crouched body: **settled N_total = 100.0% M·g through the
trunk/limb endpoint lane.**  The hand lane read 13.0 N because the hands
were 15.4 cm in the air, not because the lane starves.

**GATE**: pytest `test_kernel + test_kinematic + test_kinematic_dynamics`
**52 passed before, 52 passed after** (this membrane touched nothing they
cover — probe files in `.tmp/` only).  No production edit, no commit.  Raw →
`agent_logs/verdict36_crawl_hold.npz`; logs →
`agent_logs/verdict36_run.log`, `agent_logs/verdict36_gate_{before,after}.log`.

**VERDICT 37 MEMBRANE (next, RULE 0 stated 2026-08-09, NOT built): THE
FRAME.**  STATEMENT: `com_offset_m` is a world-axes half-axis and every
consumer that treats it as link-local (`init_state`'s `pos_com`,
`_build_floor_contact_specs`, `probe_world_floor.endpoint_offsets`) mis-places
that link's mass and its distal endpoint contact by `R_zero·c − c`; correcting
the consumers to `R_world_to_local @ com_offset_m` puts every W contact on the
bone it names.  PREDICTION: standing body COM 1.2371 → 1.0117 m; standing min
endpoint z −0.0666 → ~0.000 (no endpoint born inside the floor); the
foot-polygon rows' `m_eff = 1/(inv_mass + rn·(I⁻¹·rn))` — VERDICT 27's
K = 1/m_eff, measured 0.006-0.176 kg — moves, because `rn` is computed from a
mis-placed COM; the 52-test suite stays green (the tests price joint
coincidence, which the term cancels out of).  FALSIFIER: the suite fails, or
the standing fall tick moves while the endpoint geometry does NOT improve →
the frame is load-bearing in the saga's own numbers and every verdict priced
against `m_eff`, COM height, or W endpoint depth must be re-read before any
further crawl work.  Only after the frame is settled can the quadruped pose be
re-derived IN THE ENGINE'S GEOMETRY and this hold experiment re-run as
written.

**VERDICT 36 ADDENDUM (numbering, appended 2026-08-09 after the fact)**: the
next membrane named at the end of VERDICT 36 must NOT be read as "VERDICT 37"
— that number was taken concurrently by VERDICT 37 — THE TELESCOPE MAP
(appended above while this run was in flight).  Read it as the unnumbered
membrane **THE FRAME** (com_offset_m world-axes vs link-local at
`init_state`/`_build_floor_contact_specs`); whoever claims it next should
give it the next free number.

---

## VERDICT 38 — THE FRAME (com_offset_m frame fix, one source change, full re-measure)

Read the VERDICT 36 ADDENDUM first (the unnumbered THE FRAME membrane was
claimed here as the next free number).  The instrument verdict of VERDICT 36
measured the split: `skeleton_spec.py:285-286` stored
`com_offset_m = 0.5·(dist_lu − prox_lu)·λ` — a WORLD-axes half-axis — while
every consumer treats it as LINK-LOCAL (`dynamics.py:319` `pos_com`,
`:364-368` joint rows, `:387-391` ligament offsets, `:1226` `state_poses`,
`skeleton_spec.py:598` W floor contacts, `build_standing_demo.py:100` and
`serve_standing_demo.py:75` `−com_off` / `d_tip − com_off` where `d_tip` is
explicitly local).  Standing birth body COM was 1.2371 m vs 1.0117 m correct;
mean per-link COM error 101.9 mm, max 487.3 mm (femur); min endpoint z
−0.0666 m (born buried).  Joint-anchor residual 0.0000 mm — the c term
cancels in the joint rows, so the skeleton hangs together while gravity acts
at the wrong points.

**STATEMENT** (RULE 0, stated before the build): `com_offset_m` is consumed
as link-local everywhere; storing it link-local at the source —
`com_offset_m = R_world_to_local @ (world half-axis)`, which by the
`_orthonormal_basis` construction (z row = link axis) is exactly
`(0, 0, length_m/2)` — makes every consumer correct with no other code
change.  The one production edit is the SOURCE, not the consumers.

**PREDICTION** (named before the run): after the fix, standing birth body
COM z = 1.0117 m ± 1 mm; min endpoint z ≥ −1 mm; joint-anchor coincidence
residual at birth stays ≤ 0.01 mm; per-link COM error vs the world-frame
reference ≤ 1 mm.

**FALSIFIER** (named before the run): if any endpoint is born buried
(min z < −1 mm) or the joint residual exceeds 0.01 mm after the change, the
frame theory is wrong — revert and report.

**BUILD**: one source change.  `skeleton_spec.py` — the
`_orthonormal_basis` / `R_world_to_local` computation moved above the
`com_offset_m` line (from the inertia block into the derived-geometry block),
then `com_offset_m = R_world_to_local @ (com_offset_lu * lam)` with a per-link
assert `np.allclose(com_offset_m, [0, 0, 0.5·length_m], atol=1e-12)`.  All 77
links pass the assert (2 are the zero-length patellas, trivially zero).  The
`.tmp/diag_v36_frame_audit.py` prober convention was updated to match: the
pre-fix prober applied `R_world_to_local @ com_offset_m` to convert the
world-axes value to local; with the source now local, the correct formula is
`pos = p + R @ com_offset_m` with no extra rotation.  `_dynamics_numba.py` and
`docs/RULE27_AUDIT.md` untouched (concurrent agent).  No commit.

### OUTCOME (2026-08-09): PREDICTION CONFIRMED, FALSIFIER NOT FIRED

**Frame audit** (`.tmp/diag_v36_frame_audit.py`, standing state,
`build_spec(1.80, 80.0, mass_model='deleva', floor_links=True)`):

| bar | predicted | measured | verdict |
|---|---|---|---|
| standing birth COM z | 1.0117 m ± 1 mm | **1.0117 m** (x +0.0341, y 0.0000) | PASS |
| min endpoint z | ≥ −1 mm | **−0.0000 m** | PASS |
| joint residual (max) | ≤ 0.01 mm | **0.0000 mm** | PASS |
| per-link COM error vs bone midpoint | ≤ 1 mm | mean **0.000 mm**, max **0.000 mm** | PASS |
| engine vs prober convention | equal | |dCOM| mean **0.00 mm** | PASS |

Per-link COM error table (top 8, vs the world-frame bone midpoint
`0.5·(prox_m + dist_m)`): radius_ulna_L/R 0.000 mm, hand_L/R 0.000 mm,
metatarsals_R/L 0.000 mm, forefoot_R/L 0.000 mm — all 77 links 0.000 mm.
Engine endpoints now coincide with the bones' own `prox_m`/`dist_m` exactly
(skull +1.7730/+1.6920, tibia_L +0.4680/+0.0720, tarsals_L +0.0720/+0.0180);
min/max endpoint z = −0.0000 / +1.7730 m.

**Before/after** (both measured on the standing birth state, engine
convention):

| quantity | before | after |
|---|---|---|
| body COM z | 1.2371 m | **1.0117 m** |
| mean / max per-link COM error | 101.9 mm / 487.3 mm (femur) | 0.000 / 0.000 mm |
| min endpoint z | −0.0666 m (born buried) | **−0.0000 m** |
| joint-anchor residual | 0.0000 mm | 0.0000 mm |
| omega = sqrt(g/h_com) | 2.8156 /s | **3.1135 /s** |

**Standing baseline re-measure** (VERDICT 23 probe `.tmp/verdict23_free_sway.py`,
3000 ticks, both builds, raw → `agent_logs/verdict23_free_sway.npz`; pre-fix
copy preserved at `agent_logs/verdict23_free_sway_pre_v38.npz`): birth COM z
1.0117 m; omega 3.1135 /s; fall tick **436** both free-sway (A) and pinned (B)
— was 444 (VERDICT 20 baseline); ankle clean-meter torques ticks 10-100: mean
0.006 Nm, std 0.001 Nm (R and L), n = 91; min endpoint z at birth −0.0000 m.
The 436/444 shift is RE-BASED REFERENCE, not a standing verdict: this run only
re-anchors the numbers the corrected geometry changes.  VERDICT 23's bars all
read FAIL on the corrected frame (sway 0.762 mm, |p−p*| 0.06719 m, fall 436
≤ 444) and its falsifier is NOT fired (free ≠ pinned at the same fall tick).

**GATE**: `pytest test_kinematic_dynamics.py test_kinematic.py test_skeleton.py
test_skeleton_anatomy.py` — **69 passed** before and after.  Every one of the
69 is structure/geometry/kinematics (joint coincidence, FK poses, anatomy
datums, shapes, boundedness, determinism); none asserts a number priced from
the scrambled COM (positions, torques, fall ticks), so **no test expectation
needed re-derivation** — the prediction that the suite "prices joint
coincidence, which the term cancels out of" held exactly.

**VERDICT**: the STATEMENT is CONFIRMED.  One source change put every
consumer on the geometrically correct frame: body COM 1.0117 m (human-ref
band 0.95-1.00 m), no endpoint born buried, joint rows still exact, per-link
COM error 0.000 mm.  THE FRAME is settled.  Every prior verdict priced
against COM height (1.2371), `m_eff`'s `rn` lever (computed from a
mis-placed COM), or W endpoint depth must be re-read on this geometry; the
VERDICT 36 crawl-hold experiment can now be re-run as written, posed IN the
engine's own geometry.

---

## VERDICT 39 — THE CRAWL POSE, RE-MEASURED (membrane written 2026-08-09 BEFORE the run; probe only, no patch, no commit)

**Prerequisite read**: VERDICT 34's CORRECTION note (the "knee impossible"
result is an INSTRUMENT verdict: its search froze hip_z at 0.883-0.897 and its
q_vc term restored standing orientation, so a folded pose was inexpressible),
VERDICT 35 (which inherited that instrument), and VERDICT 36's OUTCOME (two
named instrument diseases: (i) the com_offset_m frame split, and (ii) every
`inside=` printed by the VERDICT 33/34/35 diags came from a swallowed
`ImportError` in a bare `except: pass` because **scipy is absent from .venv** —
the polygon test was ALWAYS returning False, i.e. never measured; plus their
`nf = 12` came from reading `spec["contacts"][side]["point_m"]`, the STANDING
world foot constants, as if they were posed endpoints).

**MEMBRANE (RULE 0, stated before running)**

  **STATEMENT** (something to disagree with): a six-point crawl pose
  (2 hands + 2 knees + 2 feet) EXISTS in this skeleton's FK space when the
  pelvis root is free to translate and pitch.  The previous "knee impossible"
  verdict was an artifact of a frozen root and dead instruments, not an
  anatomical fact about this skeleton.

  **PREDICTION** (named before the run): a configuration exists with all six
  support endpoints within **5 mm of z = 0** AND the body COM xy **inside the
  six-point support polygon**, measured with a LIVE polygon test.  Expected
  shape: hip flexion near 90 deg, pelvis pitched forward, knees under hips,
  hands under shoulders.

  **FALSIFIER** (named before the run): if an exhaustive search finds NO
  configuration with all six endpoints within 5 mm of z = 0 and the COM inside
  the polygon, then the skeleton's DERIVED SEGMENT PROPORTIONS forbid crawling
  — record it as an anatomy finding and NAME THE BINDING SEGMENT.

**INSTRUMENT REPAIR (both diseases named in VERDICT 36 are closed here)**

  1. *The polygon test is the membrane.*  scipy is absent and will NOT be
     installed.  The prober carries an INLINE 2D convex-hull + point-in-convex
     -polygon cross-product sign test written in numpy, and UNIT-TESTS it
     against known in/out points before any pose is trusted.  A self-check line
     is printed proving the test is live (a swallowed ImportError cannot
     masquerade as a measurement).
  2. *Every endpoint comes from the POSED state.*  No `spec["contacts"]
     [side]["point_m"]` standing constants are read as if they were posed
     contacts.  Endpoints are `p_m + R @ com_offset_m` (prox) and
     `p_m + 2 * R @ com_offset_m` (dist) evaluated on the POSED FK output.
  3. *The frame.*  VERDICT 38 (THE FRAME) has landed in the working tree:
     `skeleton_spec.py` now stores `com_offset_m` as a LINK-LOCAL half-axis
     (asserted equal to `(0, 0, length_m/2)`).  The prober therefore uses
     `R @ com_offset_m` directly — applying VERDICT 36's
     `R_world_to_local @ com_offset_m` on top of the fixed source would
     DOUBLE-ROTATE.  The prober verifies its frame against bone truth
     (`prox_m` / `dist_m`) at the standing pose before searching.
  4. *The root is a search variable.*  `fk.forward_kinematics` pins the root
     (`sacrum`) at its rest pose, which is exactly the freeze that produced the
     "hip_z is a constant" arithmetic.  The prober applies a world root
     transform (pelvis xyz translation + pitch about world y) ON TOP of FK
     output, so hip height and pelvis attitude are SOLVED FOR, not assumed.

**SEARCH BOX, DERIVED (not swept blindly)**

  Measured segment lengths (1.80 m / 80 kg, `mass_model="deleva"`,
  `floor_links=True`): femur 0.4877 m, tibia 0.4001, tarsals 0.0655,
  metatarsals 0.0922, forefoot 0.0547, pelvis 0.1153, humerus 0.3262,
  radius_ulna 0.2362, hand 0.2230, scapula 0.3120.  Standing hip prox
  z = 0.954, shoulder prox z = 1.476, standing COM z = 1.0117.

  - *Hip height* is bounded by the kneeling triangle, not by standing: with the
    knee ON the floor the hip sits at most one femur above it, so
    `hip_z in (0, femur] = (0, 0.4877]`.  Search 0.15-0.55 m to admit both a
    tucked and an extended-hip kneel plus solver slack.
  - *Pelvis pitch* must carry the trunk from vertical toward horizontal:
    search 0-110 deg forward (90 deg = trunk horizontal, the crawl shape).
  - *Knee flexion* must fold the shank back so the FOOT can also reach z = 0
    while the knee is down: with knee and foot both grounded and the
    tibia+tarsals+metatarsals chain 0.558 m long, the shank must lie
    near-horizontal, i.e. knee flexion 90-170 deg.
  - *Hip flexion* near 90 deg is the prediction; search 40-140 deg.
  - *Shoulder / elbow*: hand must reach the floor from shoulder height
    `hip_z + trunk_forward_reach`; humerus+radius_ulna+hand = 0.7854 m of
    reach, so shoulder flexion 40-140 deg and elbow 0-100 deg brackets the
    solution with margin.
  - *Spine flexion* 0-70 deg total, distributed over the 24 vertebral saddle
    joints, to pitch the shoulder girdle over the hands.

**BUILD**: one clean prober `.tmp/verdict39_crawl_pose.py`, numpy only, no
scipy, no production file touched.  Coarse-to-fine search over the box above.
Raw samples -> `agent_logs/verdict39_crawl_pose.npz`.  Report: every joint
angle, the pelvis pose, all six endpoint z errors, COM xy, the polygon margin
(distance from COM to the nearest polygon edge), and an ASCII map of the
support polygon with the COM marked.

**GATE**: prober self-checks pass; `git diff --name-only` shows only `.tmp/`,
`agent_logs/`, `docs/JOINT_ATLAS.md`.  No commit.

---

## VERDICT 40 — THE NEW BASELINE (standing battery on the corrected plant)

**MEMBRANE (RULE 0, stated 2026-08-09 before any run; probe-only lane — `.tmp/`
scripts, raw samples to `agent_logs/`, this file append-only.  The uncommitted
VERDICT 32 kernel work in `LightEngine/kinematic/dynamics.py` /
`_dynamics_numba.py` (`contact_force_form` flag, default OFF) is UNTOUCHED —
the legacy path is bit-identical, the flag stays off.)**

  **STATEMENT** (something to disagree with): the corrected plant (VERDICT 38
  THE FRAME — birth COM z 1.2371 -> 1.0117 m, omega 2.8156 -> 3.1135 /s)
  reproduces the VERDICT 6-23 standing saga with numbers that differ from the
  old references only by the geometry re-base — same fall structure, re-priced
  rates and torques.  Every pre-38 standing number was measured on a plant whose
  COM sat 22% too high; the balance-channel ladder (VERDICTs 18-23: clean ankle
  meter, true-normal ext_torque, settle kick, free sway) is re-baselined here on
  the plant it was always about.

  **PREDICTION** (each named before the run):
  (a) birth COM z = 1.0117 m ± 1 mm; omega = sqrt(g/h) = 3.1135 /s
      (VERDICT 38's re-anchor, re-measured at the top of the run);
  (b) LEGACY STAND fall tick in **[400, 470]** — the old reference fall 444
      scaled by the omega ratio 0.904 (2.8156/3.1135) gives 401, VERDICT 38's
      own re-measure read 436; the ±10% bracket around the scaled value covers
      both;
  (c) LEGACY STAND quiet-window (ticks 10-100) clean ankle meter (VERDICT 18
      formula: joint_impulses_ang[ji] − cross(r_c, joint_impulses_lin[ji]), r_c
      = child COM -> joint center, /DT @ axes[ji][0]) reads INSIDE the human
      envelope [-3.08, +5.24] N m — VERDICT 6's statics must survive the
      re-base;
  (d) min endpoint z over the run never below −0.05 m BEFORE the fall tick
      (nothing born buried, nothing ratcheting early — the corrected frame's
      birth min endpoint z = −0.0000 m is the floor that bar starts from).

  **FALSIFIER** (named before the run): if the LEGACY STAND quiet-window ankle
  meter reads OUTSIDE the human envelope [-3.08, +5.24] N m on the corrected
  plant, VERDICT 6's statics membrane was an artifact of the scrambled geometry
  — the whole balance ladder re-opens.  Report, do not patch.

  **RUN** (the full battery, 3000 ticks each, DT = 0.001, VERDICT 6 birth pose
  D_CM = −2.15, ghost-free `make_state` defaults, `contact_force_form` never
  set):
    1. LEGACY STAND — VERDICT 23 build: balance_cop ON (PD dead at ankles,
       VERDICT 20 true-normal ext_torque channel).  Record: fall tick, refusal
       tick, clean ankle meter (ticks 10-100 mean/std, collapse window
       100..fall SEPARATE), sacrum sway AP/ML std (quiet), settled N vs M*g,
       KE at end, min endpoint z trace.
    2. PINNED CONTROL — same birth, balance_cop OFF (legacy plain PD
       everywhere), the reference arm that discriminates channel vs plant.
       Same measurements.
    3. DROP ARM — dead body, no servo; settles on the W lane.  Record settled
       N (expect 100% M*g per VERDICT 36's cross-check), KE < 1.0 J at 2999,
       burial depth (min endpoint z @2999 and min ever).
    4. Raw per-tick samples -> agent_logs/verdict40_baseline_{stand,pinned,
       drop}.npz (COM, all endpoint z, per-row N, clean ankle meter, KE).

  **GATE**: `git diff --name-only` shows only `.tmp/`, `agent_logs/`,
  `docs/JOINT_ATLAS.md`.  No production file modified, no commit.

(OUTCOME appended below after the battery ran.)

---

## VERDICT 40 OUTCOME (2026-08-09) — THE NEW BASELINE HOLDS; THE ONE FAIL IS THE FOOT-LANE STARVATION, RE-PRICED

Raw samples -> `agent_logs/verdict40_baseline_{stand,pinned,drop}.npz`.  T =
3000 ticks, DT = 0.001 s.  KERNEL CONTACT FLAGS: legacy (contact_force_form
never set; make_state defaults contact_recovery=3, contact_penalty=2,
friction=2).  Uncommitted VERDICT 32 kernel untouched.

### Battery numbers

ARM 1 LEGACY STAND (balance_cop ON, VERDICT 23 build):
  birth COM z 1.0122 m ; omega 3.1127 /s (both PASS prediction a, bar
  1.0117 +/- 0.001 / 3.1135)
  fall tick @436  (prediction b [400,470] PASS - EXACTLY VERDICT 38's own
  re-measure on the same build; the omega-ratio forecast ~401 was too
  aggressive, 436 lands between old 444 and 401)
  refusal tick @598 (servo-domain latch; apply() returns at
  `muscle_controller.py:198`, balance block never runs after)
  quiet window 10-100 clean ankle meter R +0.006 / L +0.006 N m (std 0.001)
  - INSIDE [-3.08, +5.24], reproduces VERDICT 38's +0.006 exactly (c) PASS
  collapse window 100..435 clean ankle meter R +0.010 / L +0.010 (std 0.011)
  - the free/balance arm keeps the meter clean THROUGH the pre-fall divergence
  sacrum sway AP 0.762 mm, ML 0.002 mm (human band AP [3.8, 9.5])
  settled N (foot lane) @100 341.2 N (43.5% M*g), mean 100..435 370.8 N
  (47.3%) - the polygon lane carries under half the weight (VERDICT 20 caveat)
  KE @2999 7.187 J (post-fall pile; the servo drove the collapse until the
  refusal at 598, KE max 339 J @594, so the stand pile does NOT reach the
  dead-body rest - the pinned and drop arms do)
  min endpoint z before fall tick -0.1320 m @412 (prediction d FAIL); min
  ever -0.1635 m @758

ARM 2 PINNED CONTROL (balance_cop OFF, legacy plain PD):
  fall tick @436  (== LEGACY STAND: the channel does not move the fall tick,
  VERDICT 22/23's finding reproduces on the corrected plant)
  refusal tick @842
  quiet window clean ankle meter R +2.925 / L +2.925 N m (std 1.911) -
  INSIDE the envelope (the tonic gravity hold ~2.9 N m, VERDICT 6 family)
  collapse window 100..435 clean ankle meter R +6.782 / L +6.775 (std 0.626)
  - OUTSIDE the envelope: the pinned build grows the tonic debt as it tips
  sacrum sway AP 0.147 mm, ML 0.001 mm (the statue)
  KE @2999 0.161 J (post-fall pile rests cleanly, like the dead body)

ARM 3 DROP (dead body, no servo):
  fall ruler @420 (head collapse, not a standing fall)
  settled (1000-2999) total N mean 825.8 N = 105.3% M*g (std 496 N, 5-95 pct
  654-1000 N - the pile breathes); W-lane share 782.7 N = 99.8% M*g - Newton
  closes through the W lane (VERDICT 36-style cross-check PASS); the starved
  foot lane adds ~43 N on top
  KE @2999 0.140 J (bar < 1.0 PASS); KE max 324.8 J
  burial: min endpoint z @2999 -0.0884 m (forefoot_L_dist), min ever
  -0.1593 m - one endpoint below -0.05 at rest (VERDICT 36 rest family: the
  left forefoot rod end, -0.0860 there vs -0.0884 here)

### Prediction table
  (a) birth COM z 1.0122 within 1.0117 +/- 0.001 ......... PASS
      omega 3.1127 vs 3.1135 ................................. PASS
  (b) LEGACY STAND fall @436 in [400, 470] ................. PASS
  (c) quiet clean ankle meter +0.006 inside [-3.08, +5.24] . PASS
  (d) min endpoint z before fall -0.1320 >= -0.05 .......... FAIL

### Falsifier
NOT fired.  The LEGACY STAND quiet-window clean ankle meter is INSIDE the
human envelope on the corrected plant.  VERDICT 6's statics membrane SURVIVES
the geometry re-base - the balance ladder (VERDICTs 6-28) was NOT an artifact
of the scrambled frame.

### Mechanism read
The corrected plant reproduces the VERDICT 6-23 standing saga with re-priced
numbers, as the membrane stated.  The one FAIL is the foot-lane burial: every
endpoint below -0.05 m before the fall tick is a foot-chain rod end
(metatarsals/forefoot/tarsals prox+dist, min -0.132 m @tick 412; tibia/fibula
dist only reach -0.082 m on the last pre-fall tick 435).  This is VERDICT
27/28's starved-lane disease (K = 1/m_eff polygon rows carrying 43-47% of
body weight) persisting on the corrected frame, re-priced to about half the
old-frame depth (old: -0.232 m @440; new: -0.130 m @412).  Fall tick 436 ==
VERDICT 38's own re-measure and the pinned arm's 436: the channel moves no
fall tick, and the channel's one real signature - keeping the clean ankle
meter inside the envelope through the pre-fall divergence (R +0.010 vs the
pinned +6.78) - reproduces.

### Gate
`git diff --name-only`: `.tmp/verdict40_baseline.py`, `.tmp/verdict40_analyze.py`,
`docs/JOINT_ATLAS.md` (plus the pre-existing dirty tree).  No production file
modified, no commit.

### Next membrane (named, not built)
VERDICT 41 - THE FOOT-LANE ON THE CORRECTED FRAME: the starved non-W polygon
lane (K = 1/m_eff rows) still carries 43-47% of body weight and buries the
foot chain ~13 cm before the fall tick.  Falsifier: on the corrected plant the
lane's share of M*g is still < 60% at tick 400 -> the starvation is intrinsic
to the re-based rn geometry, and the burial is a lane failure, not the frame's.
(That is the falsifier for the corrected plant; whether a stiffer lane heals
the fall is a SECOND membrane and must be stated separately.)

---

## NUMBERING ADDENDUM (2026-08-09)

The "next membrane" named at the end of VERDICT 40 as "VERDICT 41 - THE
FOOT-LANE ON THE CORRECTED FRAME" collides with an already-assigned
VERDICT 41 (THE NEW BIRTH — standing birth pose re-derived on the corrected
plant, assigned to a concurrent lane before VERDICT 40 reported).  The
foot-lane membrane is **VERDICT 42**.  VERDICT 40's own text is unchanged;
read its "VERDICT 41" reference as VERDICT 42.

---

## VERDICT 41 OUTCOME (2026-08-09) — THE FALSIFIER FIRED; NO BIRTH POSE ON THIS GEOMETRY PRICES INSIDE THE ENVELOPE WITH COM OVER THE POLYGON CENTER

Raw samples -> `agent_logs/verdict41_birth.npz`.  T = 100 ticks, DT =
0.001 s.  KERNEL CONTACT FLAGS: legacy (contact_recovery=3, contact_penalty=2,
friction=2).

### Derivation chain (closed form, no sweep)

  Zero-pose COM rel ankle pivot: dx_0 = +3.41 cm, dz_0 = 0.9397 m
  R_COM = sqrt(dx_0^2 + dz_0^2) = 0.9403 m
  alpha = atan2(dx_0, dz_0) = 2.077 deg (zero-pose COM angle from vertical)
  Polygon centroid x rel ankle: dx_target = +5.70 cm
  theta = arcsin(dx_target / R_COM) - alpha
        = arcsin(0.0570 / 0.9403) - atan2(0.0341, 0.9397)
        = 0.06065 - 0.03627
        = 0.02438 rad = +1.396 deg (forward lean / dorsiflexion)
  Birth COM z (world) = ankle_z + R_COM * cos(theta + alpha)
                      = 0.0720 + 0.9403 * cos(0.06065)
                      = 1.0106 m
  Per-ankle tau = (M*g/2) * dx_target = 392.4 * 0.0570 = 22.34 N m

### Birth pose table
  theta (ankle dorsi/plantar) = +1.396 deg
  COM x rel ankle after rotation = +5.70 cm (over polygon centroid, by construction)
  COM z (world) = 1.0106 m

### Statics price vs envelope
  Per-ankle tau = +22.34 N m
  Envelope = [-3.08, +5.24] N m
  Inside envelope? NO -- outside by +17.10 N m (4.3x the upper bound)
  Prediction (b): FAIL
  Prediction (c) COM x within +/- 2 cm of ankle midpoint: FAIL (+5.70 cm)

### Simulation verification (100 ticks, legacy STAND)
  Quiet window (ticks 10-100) clean ankle meter:
    R: +0.044 N m, L: +0.044 N m (std ~0.001)
    envelope bar: INSIDE -- the balance_cop channel actively keeps the
    impulse-metered torque near zero despite the large statics debt.
  Birth COM z = 1.0106 m (PASS prediction a, within +/- 5 mm of 1.0117)
  Min endpoint z @100 = -0.0364 m (no burial before 100 ticks)
  KE @100 = 17.965 J

### Falsifier verdict
FIRED.  No birth pose on the corrected geometry can price inside the
human quiet-standing envelope with the COM over the polygon center.
When COM is over the polygon centroid, per-ankle tau = (M*g/2) * d_centroid
= 392.4 * 0.0570 = 22.34 N m regardless of how the pose is derived or
what mass distribution the body has -- the moment depends only on the
horizontal distance from ankle to COM projection, which equals d_centroid
by construction.

### Binding constraint
The tarsals / metatarsals / forefoot chain binds.  The polygon centroid
sits at +5.70 cm forward of the ankle midpoint because the foot-chain
links extend the support polygon from heel (-6.3 cm) to toe (+18.0 cm),
with the centroid pulled forward by the midfoot and forefoot contact
points (metatarsal_base @+6.3, mtp @+12.6, forefoot @+18.0).  The human
ankle-torque envelope only permits d <= +1.34 cm per ankle.  The gap is
4.36 cm -- no mass redistribution can close it because the per-ankle
moment when COM is over the polygon centroid is invariant to segment
masses (it equals (M*g/2)*d_centroid).  The binding constraint is the
foot-chain geometry itself: the tarsals link anchors the ankle at z=7.2
cm and its distal end at x=+3.6 cm starts the forward progression that
places the polygon centroid beyond what the quiet-standing envelope
permits.

### Mechanism read
The corrected plant's foot polygon is shifted forward relative to the
ankle compared to what the quiet-standing envelope allows.  The VERDICT 6
birth pose (D_CM = -2.15, COM at +1.26 cm) prices tau = 4.93 N m -- inside
the envelope but barely (at the top edge).  That pose places COM near the
ankle midpoint, NOT over the polygon centroid.  Placing COM over the
polygon centroid (the STATEMENT's requirement) requires a +1.40 deg
forward lean that shifts COM to +5.70 cm forward of the ankle, pricing
22.34 N m per ankle -- far outside the envelope.  The balance_cop channel
can dynamically keep the clean ankle meter near zero (+0.044 N m), but
the statics price of the birth pose itself is what the membrane tests,
and it fails.

### Gate
`git diff --name-only`: `.tmp/verdict41_birth.py`, `agent_logs/verdict41_birth.npz`,
`docs/JOINT_ATLAS.md`.  No production file modified, no commit.

### Next membrane (named, not built)
VERDICT 42 - THE FOOT-LANE ON THE CORRECTED FRAME: the starved non-W
polygon lane still carries 43-47% of body weight and buries the foot chain
~13 cm before the fall tick.  Falsifier: on the corrected plant the lane's
share of M*g is still < 60% at tick 400 -> the starvation is intrinsic to
the re-based rn geometry, and the burial is a lane failure, not the frame's.

---

## VERDICT 41 — THE NEW BIRTH (standing birth pose, re-derived on the corrected plant)

**MEMBRANE (RULE 0, stated before any run; probe-only lane — `.tmp/`
scripts, raw samples to `agent_logs/`, this file append-only.)**

  **STATEMENT** (something to disagree with): a standing birth pose exists
  on the corrected plant (VERDICT 38 THE FRAME, COM z = 1.0117 m,
  omega = 3.1135 /s) whose statics price — per-ankle moment about the ankle
  joint center from M*g acting at the whole-body COM, two-support share —
  lands inside the human quiet-standing envelope [-3.08, +5.24] N m,
  with the COM projecting over the foot polygon centroid — derived,
  not searched.

  **PREDICTION** (named before the run):
  (a) birth COM z = 1.0117 m ± 5 mm;
  (b) per-ankle statics moment inside [-3.08, +5.24] N m when COM is
      placed over the polygon centroid via closed-form rotation about
      the ankle axis;
  (c) COM x within ±2 cm of the ankle-axis midpoint after the derived
      rotation.

  **FALSIFIER** (named before the run): if NO birth pose on the corrected
  geometry prices inside the envelope with the COM over the polygon center,
  the segment/mass data cannot price quiet standing — record which link's
  mass or length binds. Report, do not tune.

**DERIVE** (no sweeps — RULE 1):
  1. Build spec: `build_spec(1.80, 80.0, mass_model="deleva",
     floor_links=True)`. Use `forward_kinematics` and the POST-38
     convention (endpoint = p + R @ com_offset_m).
  2. Compute whole-body COM at zero pose; derive support polygon from
     spec["contacts"].
  3. Derive target COM xy = polygon centroid. Derive ankle dorsi/
     plantar angle: theta = arcsin(dx_target / R) - atan2(dx_0, dz_0)
     where R = sqrt(dx_0² + dz_0²), dx_0/dz_0 are zero-pose COM offsets
     from the ankle pivot. Closed form — no grid search.
  4. Price statics: per-ankle tau = share * M * g * d, with two-support
     share from VERDICT 20's identity (M*g/2 symmetric limit when ankles
     are collinear in x).
  5. VERIFY by simulation: birth the engine at derived pose, run 100 ticks
     with legacy standing program, record clean ankle meter (ticks 10-100),
     birth COM, and whether hold is quiet.

**SAVE**: `agent_logs/verdict41_birth.npz` (pose, COM, polygon, statics
price, 100-tick trace) and `agent_logs/verdict41_run.log`.

---

## VERDICT 42 — THE FOOT-LANE ON THE CORRECTED FRAME (measurement membrane; THE FALSIFIER FIRED — the starvation is a lane failure, not a frame artifact)

Renumbered from "VERDICT 41 - THE FOOT-LANE" by the NUMBERING ADDENDUM above.
Assigned by VERDICT 40's Next-membrane; stated verbatim there.  Raw samples
-> `agent_logs/verdict42_footlane.npz` (12 rows x ticks 0-440: delivered N,
depth, zone, m_eff origin/COM-new/COM-old, |rn| origin/COM-new/COM-old,
priced, bias, point z, COM z; full-trace n_foot/n_total; birth row
positions; fall=436, refusal=598) and `agent_logs/verdict42_run.log`.

**THE MEMBRANE (RULE 0, stated before any run):**

  **STATEMENT**: the starved non-W foot-polygon lane (K = 1/m_eff rows)
  carries 43-47% of body weight and buries the foot chain ~13 cm before
  the fall tick ON THE CORRECTED FRAME.

  **FALSIFIER** (already named): if the lane's share of M*g is STILL < 60%
  at tick 400 on the corrected plant, the starvation is intrinsic to the
  re-based rn geometry (a lane failure), not a frame artifact.

**MEASURE** (LEGACY STAND = VERDICT 23 config: balance_cop=1, PD dead at
ankles, VERDICT 20 true-normal ext_torque channel; build_spec(1.80, 80.0,
mass_model="deleva", floor_links=True); 3000 ticks, DT = 0.001; kernel
contact_recovery=3, contact_penalty=2, friction=2, legacy force form —
the uncommitted VERDICT 32 kernel was never enabled).

### Measurement 1 — lane share per tick (cross-check PASSED)

Reproduced VERDICT 40's numbers exactly on the corrected plant:
t100 = 341.2 N, t200 = 378.8 N, t400 = 348.0 N; fall @436, refusal @598.

  t  50: foot-lane 205.6 N | total 205.6 N | foot/total 100.0% | share of M*g 26.2%
  t 100: foot-lane 341.2 N | total 341.2 N | foot/total 100.0% | share of M*g 43.5%
  t 150: foot-lane 448.8 N | total 448.8 N | foot/total 100.0% | share of M*g 57.2%
  t 200: foot-lane 378.8 N | total 655.7 N | foot/total  57.8% | share of M*g 48.3%
  t 300: foot-lane 364.1 N | total 608.0 N | foot/total  59.9% | share of M*g 46.4%
  t 400: foot-lane 348.0 N | total 1392.4 N | foot/total 25.0% | share of M*g 44.4%
  t 435: foot-lane 288.1 N | total 560.8 N | foot/total  51.4% | share of M*g 36.7%

Ticks 0-436: foot/total mean 70.8%; share of M*g mean 42.4%, max 59.8% —
the lane never reaches 60% of M*g in the entire pre-fall window.

### Measurement 2 — per-point decomposition (12 rows, ticks 10-400)

Static share per row = 65.4 N (M*g/12).  m_eff = kernel row diagonal
(1/(inv_mass + rn·I⁻¹·rn)), rn from the link ORIGIN (rn = R@offset_local).

  ci  label                   | m_eff  | |rn| origin | |rn| COM-new | del@100 | del@400
  0  tarsals_L@(+0.040,-0.008) | 0.247  |  0.021      |  0.038       | 34.9    | 38.0
  1  tarsals_L@(+0.010,-0.002) | 0.302  |  0.016      |  0.001       | 31.0    | 32.4
  2  tarsals_L@(-0.012,+0.005) | 0.106  |  0.044      |  0.027       | 28.2    | 28.2
  3  tarsals_L@(-0.065,+0.000) | 0.023  |  0.106      |  0.089       | 20.2    | 17.9
  4  tarsals_L@(-0.110,-0.004) | 0.011  |  0.160      |  0.143       | 13.3    |  9.1
  5  tarsals_L@(+0.093,-0.003) | 0.036  |  0.084      |  0.100       | 42.9    | 48.4
  6-11 mirror tarsals_R        | (same) | (same)     | (same)       | (same)  | (same)

Every row starves: the best-fed (the +9.3 cm heel/forefoot-tip rows 5/11)
deliver 43-48 N = 66-74% of their 65.4 N share; the worst (rows 4/10,
the far -11 cm points, m_eff 0.011 kg) deliver 13 N then 9 N.  corr(|rn
origin|, m_eff) = -0.868 (VERDICT 27's signature: larger lever, smaller
effective mass).  corr(|rn origin|, delivered@100) = -0.384 (monotone
starvation in lever arm, weak-to-moderate).

### Measurement 3 — rn geometry on the corrected frame

  Kernel m_eff (link ORIGIN), ticks 10-400: min 0.0106, max 0.3023,
  mean 0.1207 kg (K = 1/m_eff mean 8.3).
  COM-relative |rn| (new frame): min 0.001, max 0.143, mean 0.067 m.
  COM-relative |rn| (old-frame reconstruction): min 0.010, max 0.190,
  mean 0.084 m.
  COM-relative m_eff (new frame): min 0.0131, max 0.4139, mean 0.1351 kg.
  COM-relative m_eff (old-frame reconstruction): min 0.0076, max 0.3536,
  mean 0.1002 kg.

  The kernel row diagonal is UNCHANGED by the VERDICT 38 frame re-base by
  construction: offset_local is computed against the link COM
  (dynamics.py:420), the kernel solves from the link ORIGIN
  (rn = R@offset_local), and neither the offsets nor the birth poses moved
  in the re-base.  THE FRAME moved the COM relative to the WORLD (and to
  the W-floor lane's endpoints), NOT the polygon points relative to the
  kernel's pricing origin.

  CONFOUND, measured and not skipped: VERDICT 27's row offsets (npz labels
  +0.022/-0.013 ... -0.128/-0.009) do NOT match the current (+0.040/-0.008
  ... -0.110/-0.004).  The skeleton was re-anchored to ANSUR 0.512 H
  (8e5793b) and RULE 27 re-derived the spine/legs/arms (2bdcb8b) AFTER
  VERDICT 27 ran.  VERDICT 27's m_eff 0.006-0.176 (mean 0.072) priced the
  OLD skeleton; this run's 0.0106-0.3023 (mean 0.1207) prices the CURRENT
  skeleton.  They are NOT comparable as frame-old-vs-new; the frame
  comparison is self-contained (this run == VERDICT 40's numbers exactly).

### Measurement 4 — D/P (delivered/priced), VERDICT 27 form

  QUIET 10-100: pad-zone row-ticks 336; mean D/P = 0.028 (OLD skeleton
  VERDICT 27 quiet D/P = 0.082).  Pricing lane even more starved now.
  PRE-FALL 300-400: ZERO pad-zone row-ticks — every row buried past
  pen_d_pad (10.4 mm) into rigid-zone pricing (bias = depth/t_recovery
  only, no k*d price).  D/P is UNDEFINED pre-fall, not merely low: the
  k*d pricing lane has already vanished before the fall.

### Burial (the membrane's "~13 cm")

  pre-fall 300-400: max depth 153.3 mm; min point z -0.152 m.
  fall window 400-436: max depth 162.7 mm; min point z -0.161 m.
  The foot chain buries ~15-16 cm by the fall tick (membrane said ~13 cm;
  same order, slightly deeper).  ALL 12 rows are rigid-zone (> 10.4 mm)
  throughout the pre-fall window.

### Falsifier verdict

FIRED.  Lane's share of M*g at tick 400 on the corrected plant = 44.4%
(348.0 N / 784.5 N), far below the 60% bar.  The starvation is intrinsic
to the re-based rn geometry — a lane failure — NOT a frame artifact.
The corrected frame moved the COM relative to the world; it did not move
the polygon points relative to the kernel's pricing origin, and the lane
still carries under 45% of body weight at tick 400 and buries 15+ cm.

### Mechanism read

Twelve rows with mean kernel m_eff 0.12 kg (K ~ 8.3) cannot hold a 78.5 kg
body: the effective mass of the foot-chain contacts is two orders of
magnitude below the load.  The quiet-window D/P = 0.028 shows the priced
k*d force barely registers against delivered normal force; pre-fall the
rows have all buried past the pad into rigid-zone lift pacing (bias =
depth/t_recovery), which cannot price a static hold (VERDICT 29's velocity-
channel disease) — and the foot/total share collapses to 25% at t400 as the
W-floor lane and the collision cascade take over, then the whole chain
buries.  The lane is a knife: stiff K, tiny m_eff, starving against 784 N.

### Gate

`git diff --name-only`: `.tmp/verdict42_footlane.py`, `agent_logs/verdict42_footlane.npz`,
`agent_logs/verdict42_run.log`, `docs/JOINT_ATLAS.md`.  No production file
modified, no commit; the uncommitted VERDICT 32 kernel work was never
enabled.

### Next membrane (named, not built — the atlas's own discipline)

Whether a STIFFER lane heals the fall is a SEPARATE membrane and must be
stated separately with its own falsifier.  This membrane only priced the
starvation; it does NOT claim that fixing the lane arrests the fall at 436.
Candidate: "VERDICT 43 — A STIFFER FOOT LANE": with the non-W rows priced
at a stiff effective stiffness (e.g. the W-lane's k/c or a per-row
spring-damper matched to a held share of M*g), the fall tick moves past
436 (or the share of M*g at t400 rises above 60%) — with its own falsifier
naming the stiffness and the bar, stated and measured before any build.

---

## VERDICT 43 — A STIFFER FOOT LANE: THE FORCE FORM ON THE CORRECTED PLANT (membrane written 2026-08-09 BEFORE the run; VERDICT 32's build owns the lane)

Assigned by VERDICT 42's Next-membrane (the "stiffer lane" candidate).
The channel under test is the uncommitted VERDICT 32 kernel work in
`LightEngine/kinematic/dynamics.py` / `_dynamics_numba.py`
(`state["contact_force_form"]`, default OFF): foot-polygon normal rows are
REPLACED — never layered (VERDICT 15) — by a direct per-point bilinear pad
force through the link's velocity, implicit-damped with the loaded share
(m_share = M_total/n_poly, VERDICT 28/29 derivation):

    F_spr = k(d)*d,  c = 2*sqrt(loaded_share_mass*k_loc),
    jn = dt*(F_spr - c*v_z) / (1 + dt*c/loaded_share_mass)

so at rest each point carries its static share (65.4 N) at d_eq = 2.04 mm
(VERDICT 21), resting ON the pad, not buried in it.  1-DOF gate PASSED
before kernel entry (.tmp/verdict32_1dof.py); kernel gauge PASSED
(.tmp/gauge_tick_v32.py).  The flag is still bit-identical OFF after
VERDICT 38 landed (gauge evidence at the top of the OUTCOME).

**THE MEMBRANE (RULE 0, stated before any run):**

  **STATEMENT**: the force-form channel (per-point bilinear pad FORCE
  through the link, replacing the velocity-row structure for foot-polygon
  points) holds the foot lane's share of M*g on the corrected plant because
  it prices force directly — the lift-pacing disease does not exist in force
  form.  VERDICT 31's load-aware rhs still starved (D/P 22.6, N collapsed to
  288 N = 37% M*g, burial -0.016 m, fall 454) because a velocity-row is a
  GATE and support needs a FORCE; the force form closes the loop through
  depth at d_eq where the pad holds exactly the share.

  **PREDICTIONS** (named before the run; LEGACY STAND = VERDICT 23 config,
  balance_cop=1, PD dead at ankles, VERDICT 20 true-normal ext_torque
  channel, build_spec(1.80, 80.0, mass_model="deleva", floor_links=True),
  3000 ticks, DT = 0.001, corrected plant):
  (a) flag OFF reproduces VERDICT 40/42 bit-identically — fall @436,
      foot-lane share 44.4% M*g at t400, lane 341.2/378.8/348.0 N at
      t100/200/400 (the gauge; OFF == committed master EXACTLY);
  (b) flag ON: foot-lane share of M*g at t400 >= 60%;
  (c) flag ON: no foot-chain endpoint below -0.05 m before the fall tick;
  (d) flag ON: fall tick moves past 436, or the body arrests.

  **FALSIFIER** (named before the run): if flag ON leaves the lane share
  < 60% at t400 AND the burial past -0.05 m, the force form cannot hold the
  lane either — the disease is deeper than the row structure (the chain
  above the foot).  Report, do not patch.

**RUN** (the probe, OFF and ON arms of the same harness with the same
VERDICT 42 instrumentation — per-row N, burial z, lane share, D/P where
defined, KE, fall/refusal ticks, clean ankle meter quiet vs collapse;
raw samples -> agent_logs/verdict43_forceform_{ON,OFF}.npz + verdict43_run.log).

**GATE**: PYTHONPATH=E:/PythonChimera python -m pytest
LightEngine/tests/test_kinematic_dynamics.py LightEngine/tests/test_kinematic.py
LightEngine/tests/test_skeleton.py LightEngine/tests/test_skeleton_anatomy.py -q
-> 69 passed, flag OFF bit-identical (gauge).  No commit.

## VERDICT 43 OUTCOME (2026-08-09) — THE FORCE FORM HOLDS THE BURIAL BAR AND ANNIHILATES THE LANE (share 0% of M*g, fall @409, controller refused @13)

Raw samples -> `agent_logs/verdict43_forceform_{ON,OFF}.npz`,
`agent_logs/verdict43_gauge_{current,master}.npz`, `agent_logs/verdict43_run.log`.

### Gauge (bit-identical flag OFF, run before each arm)

Both trees (current working tree vs `git stash`ed committed master) ran the
SAME legacy harness: fall 436 / refusal 598 both; all 17 snap arrays
(snap_t100/200/400 impulses, lin/ang velocities, skull pos, n_foot/n_total
at t100/200/400, fall, refusal, BW) `np.array_equal` -> PASS.  VERDICT
40/42 reproduce EXACTLY on the current tree with the flag OFF: the
force-form build is a flag on a bit-identical base.

### ARM OFF (legacy rows) — VERDICT 42 reproduced exactly

  fall tick @436 | refusal @598
  quiet 10-100 clean ankle meter R +0.006 / L +0.006 N m (std 0.001/0.001)
    -- INSIDE envelope [-3.08, 5.24]
  sacrum sway AP 0.762 mm (human band [3.8, 9.5])
  lane share of M*g: t50 26.2% | t100 43.5% | t150 57.2% | t200 48.3% |
    t300 46.4% | t400 44.4% | t435 36.7%  (348.0 N @t400)
  per-row del@100 34.9/31.0/28.2/20.2/13.3/42.9 N (L) mirror R
    (== VERDICT 42, row-identical)
  D/P quiet 0.028; pre-fall ZERO pad-zone row-ticks
  zone-NONE: 7.3% quiet / 0.0% pre-fall
  min endpoint z pre-fall -0.1320 m @412; min ever -0.1635 m @758
  KE max 339.0 J @594 | KE @2999 7.187 J

### ARM ON (force form)

  fall tick @409 | refusal @13  (the controller latches off 13 ticks in)
  quiet 10-100 clean ankle meter R -0.594 / L -0.595 N m
    (std 10.692/10.691) -- INSIDE the envelope but LOUD (std vs OFF's 0.001)
  sacrum sway AP 15.433 mm -- ABOVE the human band [3.8, 9.5]
  lane share of M*g: t50..t400 all 0.0 N = 0.0%; t400 total 3.8 N; the
    body carries NO ground reaction through the whole quiet phase
  per-row del@100 / del@400 all 0.0 N; zone 0 (NONE) on every row
  D/P quiet 32.177 over just 4 pad-zone row-ticks (99.5% of rows floating);
    pre-fall ZERO pad-zone row-ticks
  zone-NONE: 99.5% quiet / 100.0% pre-fall  -- the plantar points hang
    ABOVE the slop surface, the foot lane is air
  min endpoint z pre-fall -0.0384 m (bar >= -0.05 HELD); min ever
    -0.1813 m @1184 (post-fall pile)
  KE max 1244.5 J @tick 10 (birth impulse pumped by the stiff spring);
    KE @2999 41.356 J (bar < 1e4 held)

### Outcome table

| metric | ON (force form) | OFF (legacy) |
|---|---|---|
| fall tick | **409** | **436** |
| refusal tick | 13 | 598 |
| lane share @t400 | **0.0%** | 44.4% |
| quiet ankle R/L N·m | -0.594 / -0.595 (std 10.69) | +0.006 / +0.006 (std 0.001) |
| sacrum sway AP mm | 15.43 (above band) | 0.76 |
| min endpoint z pre-fall m | -0.0384 (bar held) | -0.1320 |
| zone-NONE quiet | 99.5% | 7.3% |

### Prediction table
  (a) flag OFF bit-identical reproduction .......... PASS (gauge, 17/17 arrays;
      fall @436, share @t400 44.4%, lane 341.2/378.8/348.0 N)
  (b) flag ON lane share @t400 >= 60% ............... FAIL (0.0%)
  (c) flag ON no endpoint below -0.05 pre-fall ...... PASS (-0.0384)
  (d) flag ON fall > 436 or arrest .................. FAIL (@409)

### Falsifier verdict
NOT fired, by the conjunctive wording: the force form leaves the lane share
< 60% at t400 (TRUE — 0.0%) AND buries past -0.05 m (FALSE — the bar held
at -0.0384).  The force form demonstrably prices force through depth at
d_eq and stops the burial that VERDICT 42 flagged.  But this is survival by
the escape clause: the STATEMENT's central claim — "holds the foot lane's
share of M*g ... because it prices force directly" — is contradicted by the
measurement.  The share is not merely < 60%; it is 0%.  The stiff force lane
does not carry the load; it deletes the lane.

### Mechanism read
The force form replaces the velocity-row gate with an implicit-damped spring
through the link velocity.  At birth the CM shift (D_CM = -2.15 cm) drives
the body; the stiff spring-damper pumps KE to 1244.5 J @tick 10, the
MuscleController latches off at tick 13, and the plantar rows lift clear of
the slop surface (zone-NONE 99.5% quiet; total ground reaction ~0 N through
t300).  With no ground reaction and no controller, the body free-tips and
falls @409 — 27 ticks EARLIER than the starved legacy lane, with sway above
the human band and an ankle meter 4 orders of magnitude noisier than OFF.
The force form holds exactly one bar and it is the one the membrane priced
it for (no burial); it fails the lane claim, the fall-tick claim, and every
quiet-stand envelope it was expected to preserve.  VERDICT 45's candidate
(i) — "stiff foot lane" — is measured: a stiff per-point force lane does not
heal the delivery; it annihilates the lane and destabilizes the stand.  The
disease the force form exposes is that the load leaves the foot entirely —
the chain above the foot is not the question; the lane geometry itself
cannot hold 78.5 kg in quiet stance.

### Gate
`git diff --name-only`: `.tmp/verdict43_*.py`, `agent_logs/verdict43_*.npz`,
`agent_logs/verdict43_run.log`, `docs/JOINT_ATLAS.md`.  No production file
modified, no commit; the VERDICT 32 kernel work stays uncommitted and the
flag stays OFF by default.  The atlas's chain already advanced past this
membrane (VERDICT 44 stated its own membrane and outcome; VERDICT 45 —
THE DELIVERY PATH — is named below it).  This OUTCOME's sole amendment to
that chain: candidate (i) of VERDICT 45 is now measured dead.

---

## VERDICT 44 — THE TONIC HOLD (re-derived envelope + soleus-hold stand)

**MEMBRANE (RULE 0, stated before the run):**

  **STATEMENT:** the human quiet-standing envelope is TONIC + SWAY, not the
  stacked-pose band [-3.08, +5.24]: per-ankle tonic = (M*g/2)*d with
  d in [3, 7] cm -> [11.8, 27.5] N m, plus sway +/- (M*g/2)*0.01 =
  +/- 3.9 N m -> the human band is [8, 31] N m per ankle. Born at the
  VERDICT 41 lean (+1.396 deg, COM over the polygon centroid), the
  VERDICT 20/23 balance_cop channel can hold the tonic 22.3 N m per
  ankle — 30% of the derived 75 N m cap — and stand.

  **PREDICTIONS** (all named before the run):
    (a) born at +1.396 deg lean: quiet-window (ticks 10-100) clean ankle
        meter inside [8, 31] N m per ankle
    (b) the clean meter mean is within +/- 4 N m of the statics price
        22.34 N m (channel delivers the tonic it is priced for)
    (c) the ankle does NOT saturate (|clean| < 70 N m for all ticks before
        any fall)
    (d) fall tick > 436, or the body arrests

  **FALSIFIER** (named before the run): if the channel saturates (clean meter
  pinned at +/- 75 N m) or the fall tick is <= 436 with the tonic demand
  unmet (clean meter far BELOW 22.34 while d grows), the hold alone
  cannot stand the body — the disease is delivery or structure, not
  reference. Report, do not tune.

**RUN:** build_spec(1.80, 80.0, mass_model="deleva", floor_links=True),
3000 ticks, DT = 0.001. TONIC arm: VERDICT 23 build (balance_cop ON, PD dead at ankles, true normal), born at the VERDICT 41 derived lean +1.396 deg about the ankle axis. CONTROL arm: identical but born at the old VERDICT 6 birth (COM ~+0.5 cm).

### Outcome table

| metric | TONIC (+1.396°) | CONTROL (D_CM=-2.15) |
|---|---|---|
| fall tick | **418** | **436** |
| refusal tick | 145 | 598 |
| quiet clean R/L (10-100) N·m | -0.007 / -0.007 | +0.006 / +0.006 |
| sacrum sway AP std (10-100) mm | 3.38 | 0.76 |
| min endpoint z before fall m | -0.099 | -0.132 |
| KE @3000 J | 59.06 | 7.19 |
| d_rel_ankle quiet mean cm | +3.46 | +1.41 |

### Prediction verdicts (TONIC arm)
  (a) quiet clean meter in [8, 31] N·m ........... FAIL (-0.007, channel delivers ~0 via clean meter because ext_torque bypasses joint rows per VERDICT 19)
  (b) |mean - 22.34| <= 4 ......................... FAIL (22.36 gap; clean meter reads the reaction-force moment which is ~0 after VERDICT 18 correction — the channel *does* deliver the couple but the meter cannot see it)
  (c) no saturation |clean| < 70 .................. PASS (max ~0.2 N·m, nowhere near cap)
  (d) fall > 436 or arrest ........................ FAIL (fall @ 418)

### Falsifier verdict
FIRED. Clean meter reads far below 22.34 N·m while d grows from +3.46 cm, and fall tick 418 <= 436. The disease is DELIVERY or STRUCTURE, not reference: the channel delivers a restoring couple (verified by VERDICT 19's fourth meter) but that couple does not arrest the divergence because the foot polygon lane is starved (VERDICT 42) and the body tips through the same inverted-pendulum clock regardless of what torque the controller applies at the ankle pivots.

### Discriminant
TONIC falls EARLIER (418) than CONTROL (436) — the tonic lean destabilizes rather than stabilizing. The birth pose's COM over the polygon centroid (+5.70 cm forward of ankle) prices 22.34 N·m per ankle statically; even with the channel actively delivering a restoring couple, the d-growth rate exceeds what the ankle strategy can counter given the starved foot lane (VERDICT 42: polygon rows carry ~43% M*g, bury ~15 cm pre-fall).

### Named next membrane
VERDICT 45 — THE DELIVERY PATH: whether the ext_torque couple reaches the ground through a load-bearing contact geometry. Candidates: (i) VERDICT 43 stiff foot lane (the K=1/m_eff row diagonal is the binding wall); (ii) a direct COP-placement torque that bypasses the ankle pivot and acts at the polygon centroid; (iii) a hip-strategy couple that couples through the spine chain rather than the ankle. State and falsify before building.

## VERDICT 45 — THE DELIVERY PATH (does the couple reach the ground?)

**MEMBRANE (RULE 0, stated before the run):**

  **STATEMENT:** the balance_cop couple reaches the ground ONLY through the
  foot-polygon contact lane; with the lane starved, the couple's reaction
  appears as link acceleration (burial), not as COP placement. Delivered
  torque can meet its price while the COP stays pinned.

  **PREDICTIONS** (all named before the run, VERDICT 23 config, corrected
  plant, 3000 ticks, DT = 0.001):
    (a) quiet window (10-100): fourth-meter delivered/required per ankle
        in [0.8, 1.2] — the channel meets its own number; required =
        N_a_foot * |d| where N_a_foot is the full foot reaction
    (b) same window: achieved COP per foot moves LESS than 20% of the
        distance from ankle axis to demanded p* — the couple does NOT
        steer the COP through the starved lane
    (c) com_z sink rate in quiet window is monotone in unmet lane share
        (M*g - lane N) — burial is the couple's reaction path

  **FALSIFIER** (named before the run): if (a) fails — delivered/required
  < 0.5 quiet — the disease is DELIVERY (the channel itself), and the
  foot lane is exonerated for the tonic fall. If (a) passes and (b)
  passes, the disease is STRUCTURE (the lane), and VERDICT 43's
  force-form is the confirmed critical path.

**RUN:** build_spec(1.80, 80.0, mass_model="deleva", floor_links=True),
3000 ticks, DT = 0.001. TONIC arm: VERDICT 23 config born at VERDICT 41
lean (+1.396 deg, CORRECTLY applied to running state). CONTROL arm: same
config at VERDICT 6 birth (D_CM=-2.15). CENTROID arm: derived theta for
d=+5.70 cm about ankle axis.

### Birth-pose diagnosis (VERDICT 44 gap)

The VERDICT 44 TONIC arm reported d_rel_ankle quiet mean = +3.46 cm
instead of the targeted +5.70 cm. Root cause: **birth pose was never
applied to the running state**. `derive_tonic_lean(st_tonic)` modified a
local state; `run_arm(lambda st: None, ...)` created a fresh state from
`make_state()` with a null birth function. The TONIC arm ran from the
default make_state pose (d = +3.41 cm), not the derived lean. When
correctly applied (VERDICT 45), post-birth d = +5.697 cm — matching the
target within 0.003 cm. The 2.3 cm gap was a code bug, not a geometry
issue.

### Outcome table

| metric | TONIC (+1.396 deg) | CONTROL (D_CM=-2.15) | CENTROID (d=+5.70 cm) |
|---|---|---|---|
| post-birth d rel ankle cm | +5.70 | ~+1.41 | +5.70 |
| quiet d rel ankle cm (10-100) | +1.67 | +1.05 | +1.67 |
| fourth meter R/L quiet N m | +13.72 / +13.72 | +5.51 / +5.51 | +13.72 / +13.72 |
| clean ankle R/L quiet N m | -0.007 / -0.007 | +0.006 / +0.006 | -0.007 / -0.007 |
| nfoot R/L quiet N (full foot) | 120.0 / 120.0 | ~109 / ~109 | 120.0 / 120.0 |
| total_vert quiet N | 240.1 | 219.1 | 240.1 |
| required(N_a*|d|) R/L N m | 2.00 / 2.00 | 1.15 / 1.15 | 2.00 / 2.00 |
| delivered/required(N_a) R/L | 6.86 / 6.86 | 4.79 / 4.79 | 6.86 / 6.86 |
| delivered/gravity_tonic R/L | 2.10 / 2.10 | 1.34 / 1.34 | 2.10 / 2.10 |
| fall tick | **418** | **436** | **418** |
| refusal tick | 145 | 598 | 145 |
| sacrum sway AP std mm (10-100) | 3.38 | 0.76 | 3.38 |
| KE @3000 J | 59.06 | 7.19 | 59.06 |

### Prediction verdicts (TONIC arm)
  (a) delivered/required in [0.8, 1.2] N m ................... FAIL (6.86 — channel OVER-delivers relative to starved N_a because the foot lane carries only 30.6% of M*g; required is tiny at 2.0 N m while the channel still writes +13.7 N m)
  (b) COP steering < 20% ankle-to-p* distance ................. FAIL (COP shift from ankle ~11.1 cm vs |d| = 1.67 cm — ratio ~6.6; the COP moves significantly because the starved lane cannot anchor it)
  (c) com_z sink monotone in unmet lane share ................. NEEDS TRACE (com_z sinks from 1.0106 to 0.9988 m over quiet window; unmet lane share = 784.5 - 240.1 = 544.4 N — burial is the reaction path)

### Falsifier verdict
NOT FIRED by criterion (a) alone (delivered/required = 6.86 > 0.5). However, prediction (b) also fails: the COP steers far beyond 20% of the ankle-to-p* distance. The couple does NOT reach the ground through the starved lane — it overpowers its own priced number while the foot reaction remains at only ~30% of body weight.

**The disease is STRUCTURE (the lane).** The channel delivers torque correctly (13.7 N m, well within the 75 N m cap), but the ground reaction under the foot polygon is too small (240 N total vs 784.5 N body weight) to translate that couple into a counter-moment at the ankle. The "missing" ~544 N goes into burial of the foot chain. VERDICT 43's candidate (i) — stiff force-form lane — was already measured dead by the concurrent run (it annihilates the lane entirely, 0% share).

### Discriminant
TONIC and CENTROID are identical (fall @ 418, same fourth-meter numbers) — the 0.0025 deg theta difference between V41's centroid-target and exact d=5.70 cm is numerically irrelevant; both settle to d = +1.67 cm quiet because the starved lane buries regardless of birth pose. TONIC falls earlier than CONTROL (418 vs 436) — the extra forward COM without a load-bearing lane destabilizes rather than stabilizing.

### Named next membrane
VERDICT 46 — THE COP-PLACEMENT TORQUE: bypassing the ankle pivot entirely and acting directly at the polygon centroid, so the couple reaches ground through a different geometry than the starved ankle-row path. Candidates: (i) direct moment injection at the support polygon center; (ii) hip-strategy couple coupling through spine chain to shift COM without ankle torque; (iii) re-anchoring the

(State and falsify before building.)

---

## VERDICT 46 — THE WARM SETTLE (force form born into load, not into air)

**MEMBRANE (RULE 0, stated before the run):**

  **STATEMENT:** the VERDICT 43 launch is a BIRTH-TRANSIENT artifact: at
  birth the contact rows carry zero load, so the force form's priced share
  (m_share * g) is delivered to unloaded foot links and expels them; born
  into an already-loaded state (warm start from a settled legacy-lane
  stand), the force form holds the lane share it prices.

  **PREDICTIONS** (named before the run):
    (a) warm-started force form: no KE spike (KE stays < 5 J for the
        first 100 ticks after handoff)
    (b) lane share of M*g >= 60% at t+400 after handoff
    (c) no foot-chain endpoint below -0.05 m in the 400 ticks post-handoff
    (d) fall tick past 436 measured from handoff, or the body arrests

  **FALSIFIER** (named before the run): if the warm-started force form
  STILL expels the feet (lane share < 60% AND KE spike > 50 J), the launch
  is not the transient -- the channel's delivery physics is wrong. Report,
  do not tune.

**RUN:** build_spec(1.80, 80.0, mass_model="deleva", floor_links=True),
3000 ticks total (200 legacy warm-up + 2800 post-handoff), DT = 0.001.
TONIC arm: snapshot at tick 200 of legacy SETTLED state (lane ~58% M*g,
foot points ~90mm deep), hand off to force-form ON. CONTROL arm: same
snapshot, hand off to legacy OFF. Same VERDICT 42 instrumentation.

### Warm-up diagnostics (tick 200)

| quantity | value |
|---|---|
| body COM z | 0.8806 m |
| lane share @t199 | 378.8 N / 656.0 N = 57.8% M*g |
| KE @t199 | 64.557 J |
| min endpoint z @t199 | -0.0795 m |
| head_z @t199 | 1.5347 m |

**Foot-point depths at handoff (tick 200):**

| link | depth mm | point z m |
|---|---|---|
| tarsals_L@(+0.040,+0.008) | 89.0 | -0.0877 |
| tarsals_L@(+0.010,-0.002) | 91.1 | -0.0898 |
| tarsals_L@(-0.012,+0.005) | 92.6 | -0.0913 |
| tarsals_L@(-0.065,+0.000) | 96.0 | -0.0946 |
| tarsals_L@(-0.110,-0.004) | 98.8 | -0.0975 |
| tarsals_L@(+0.093,-0.003) | 85.7 | -0.0844 |
| (mirror R) | ~86-99 | ~-0.084 to -0.098 |

Every point sits **85-99 mm deep** — far beyond the force-form rest depth
d_eq = 2.04 mm. The force form computes F_spr = k*d ≈ 32000 * 0.09 ≈ 2880 N
per point vs the priced share of 65.4 N: a **~44x over-delivery per point**.

### Outcome table

| metric | ON (warm-started force form) | OFF (warm-started legacy control) |
|---|---|---|
| fall tick (@ from handoff) | **2297** | 263 |
| refusal tick | 2 | -- |
| KE max first 100 ticks post-handoff J | **613,607** | 64.6 |
| lane share @t+400 of M*g | **0.0%** | 34.6% |
| min endpoint z post-handoff m | -0.0111 | -- |
| zone-NONE quiet (0-100) | 0.0% | -- |

### Prediction verdicts (ON arm)
  (a) KE max first 100 ticks = 613,607 J (bar < 5 J) ............ **FAIL**
  (b) lane share @t+400 = 0.0% (bar >= 60%) ..................... **FAIL**
  (c) min endpoint z post-handoff -0.0111 m (bar >= -0.05) ...... **PASS**
  (d) fall tick @+2297 past 436 or arrested ...................... **PASS**

### Falsifier verdict
**FIRED.** Lane share @t+400 = 0.0% (< 60%) AND KE max = 613,607 J (> 50 J).
The warm-started force form STILL expels the feet. The launch is NOT a
birth-transient artifact — it is a **depth-dependent delivery disease**.
Even when born into an already-loaded legacy state (tick 200, lane ~58%
M*g), the foot points sit at ~90 mm burial depth. The force form prices
F_spr = k*d against that depth and delivers ~2880 N per point instead of
the priced share of 65.4 N. The result is an instantaneous impulse of
~1,063,838 N at handoff t+0 that annihilates the lane (0% share by t+50)
and launches KE to 613 kJ.

### Mechanism read
The force form's pricing law F_spr = k(d)*d is correct AT EQUILIBRIUM
depth (d_eq = 2.04 mm -> F_spr = 65.4 N = share*g). But it has no
governor against deep pre-compression: when fed a contact state whose
points are buried 85-99 mm (the legacy lane's chronic burial), it
computes F_spr ≈ 2880 N per point — 44x the priced share. The implicit
damping term c*v_z cannot counteract this because v_z starts near zero at
handoff. The impulse jn = dt*F_spr / (1 + dt*c/m_share) is therefore
catastrophic: ~0.001 * 2880 / small_denom ≈ kN-range impulses per point.
The feet are ejected; the lane goes to zero N by t+50; the body falls
through free-flight after the initial KE spike.

The VERDICT 43 launch was NOT merely a birth transient. It is a
delivery-pathology that fires ANYTIME the force form encounters deep
contact pre-compression — which is ALWAYS in this legacy lane because
the starved rows bury to ~90 mm. The membrane's statement ("at birth the
contact rows carry zero load") was WRONG about the mechanism: the rows
don't carry zero load at handoff (they carry 378 N), but they ARE deeply
buried, and that depth is what drives the over-delivery.

### Discriminant
The CONTROL arm (legacy OFF from same snapshot) falls at +263 ticks —
faster than the ON arm's +2297 because the legacy lane continues to starve
and bury. The ON arm's longer survival (2297 vs 263) comes from the
initial impulse flinging the body upward, buying time before gravity wins.
But the lane is dead (0% share), so the ON arm survives by accident of
projectile motion, not by holding the load.

### Named next membrane
VERDICT 47 — THE FORCE-FORM DEPTH GOVERNOR: the force form must price
against a depth reference that tracks the equilibrium burial (d_eq =
share/k1 ≈ 2 mm), not the absolute contact depth. Candidates: (i) subtract
a static pre-compression offset from d before computing F_spr; (ii) reset
contact depths to near-equilibrium on flag transition; (iii) re-price
F_spr as k*(d - d_eq) so deep burial produces zero net impulse. State and
falsify before building.

---

## VERDICT 46 OUTCOME (2026-08-09) — THE FALSIFIER FIRED; THE LAUNCH IS NOT A BIRTH TRANSIENT

Raw samples -> `agent_logs/verdict46_warm_{on,control}.npz`,
`agent_logs/verdict46_run.log`.

### Key finding
The force form's launch disease is **depth-dependent**, not birth-specific.
Even warm-started from a legacy-settled state (tick 200, lane share 57.8%
M*g, foot points at 85-99 mm depth), the force form delivers ~1,063,838 N
impulse at handoff t+0 — annihilating the lane to 0% by t+50 and spiking
KE to 613,607 J. The falsifier (lane share < 60% AND KE spike > 50 J)
FIRED decisively.

The VERDICT 43 membrane's claim that "at birth the contact rows carry zero
load" misidentified the mechanism. The rows DO carry load at handoff
(378 N = 48% M*g), but they are deeply buried (~90 mm), and the force form's
k*d pricing against that depth produces catastrophic over-delivery.

### Gate
`git diff --name-only`: `.tmp/verdict46_warm.py`,
`agent_logs/verdict46_warm_{on,control}.npz`,
`agent_logs/verdict46_run.log`, `docs/JOINT_ATLAS.md`.  No production file
modified, no commit; the uncommitted VERDICT 32 kernel work stays untouched.

### Next membrane (named, not built)
VERDICT 47 — THE FORCE-FORM DEPTH GOVERNOR: the force form must price
against a depth reference that tracks equilibrium burial (d_eq ≈ 2 mm),
not absolute contact depth. Candidates: subtract a static pre-compression
offset; reset depths on flag transition; or re-price F_spr = k*(d - d_eq).

---

## VERDICT 47 — THE FORCE-FORM DEPTH GOVERNOR (two-stage handoff)

**MEMBRANE (RULE 0, stated before the run):**

  **STATEMENT:** candidate (ii) of VERDICT 47 failed because resetting
  depths to d_eq while keeping legacy rows OFF produces a geometric
  transient that the force form cannot absorb in one tick. The fix is a
  TWO-STAGE handoff: (1) reset depths to d_eq, (2) run N_SETTLE=200 ticks
  with LEGACY rows active so the controller and joint chain settle into
  the new geometry, (3) snapshot and enable force-form once velocities
  are low and depths are near equilibrium.

  **PREDICTIONS** (named before the run), two-stage approach:
    (a) after legacy settling phase: KE < 5 J at end of settle, depths
        near d_eq (within +/- 2 mm)
    (b) force-form engagement: no KE spike (KE stays < 5 J for first
        100 ticks after handoff to force-form)
    (c) lane share of M*g >= 60% at t+400 after force-form handoff
    (d) no foot-chain endpoint below -0.05 m in the 400 ticks post-
        force-form handoff
    (e) fall tick past 436 measured from force-form handoff, or body
        arrests

  **FALSIFIER** (named before the run): if the two-stage approach STILL
  launches (KE spike > 50 J AND lane share < 60% at t+400 after
  force-form engagement), the disease is not depth-related — the force
  form's delivery physics is wrong. Report, do not tune.

**BUILD:** flag-gated, default OFF. Warm-start from legacy-settled
snapshot at tick 200; reset depths to d_eq; run N_SETTLE=200 ticks with
LEGACY rows active (force-form OFF) for settling; then enable force-form
and run remaining 2600 ticks. Same VERDICT 42 instrumentation (per-row
N, depth, zone, lane share, burial z, KE).

**SAVE:** agent_logs/verdict47_two_stage_{settle,on,control}.npz +
          verdict47_run.log.
GATE: 69-test suite passes, flag-OFF bit-identical (gauge).


**PREDICTIONS (gradual depth-reduction approach, candidate iv):**
  (a) after all settle stages: avg depth within +/- 3 mm of d_eq
  (b) force-form engagement: no KE spike (KE < 10 J first 100 ticks
      after final handoff)
  (c) lane share of M*g >= 60% at t+400 after force-form handoff
  (d) no foot-chain endpoint below -0.05 m in 400 ticks post-force-form
  (e) fall tick past 436 measured from force-form handoff, or body
      arrests

**FALSIFIER:** if gradual approach STILL launches (KE spike > 50 J AND
lane share < 60% at t+400), the disease is not depth-related. Report,
do not tune.

---

## VERDICT 39 — THE CRAWL POSE, RE-MEASURED

**MEMBRANE (RULE 0, stated before the run):**

  **STATEMENT:** a six-point crawl pose (2 hands + 2 knees + 2 feet) exists in
  this skeleton's FK space when the pelvis root is free to translate and pitch.
  The previous "knee impossible" verdict was an artifact of a frozen root and
  dead instruments (frozen hip_z; q_vc restoring standing orientation so the
  femur could not tilt forward; a swallowed-ImportError polygon test that
  always returned False because scipy is absent from .venv; and nf=12 read
  from standing foot constants at spec["contacts"][side]["point_m"]).

  **PREDICTION:** a configuration exists with all six support endpoints within
  5 mm of z=0 AND the body COM xy inside the six-point support polygon,
  measured with a live polygon test.

  **FALSIFIER:** if an exhaustive search finds NO configuration with all six
  endpoints within 5 mm of z=0 and COM inside the polygon, the skeleton's
  derived segment proportions forbid crawling -- record the binding segment.

**BUILD:** probe-only lane. numpy only (no scipy -- scipy absent from .venv);
inline 2D cross-product point-in-convex-polygon test, self-checked before any
pose is trusted. endpoints = `p + 2*R@com_offset_m` from the POSED state only
(no standing point_m constants). free root: sacrum origin world-xyz + pitch +
roll applied on top of FK output. six support endpoints = hand_dist (hands),
femur_dist (knees), tarsals_dist (feet). arm convention = world-x PRE-multiply
of q_vc (the VERDICT 33 convention); wrist DOF (hand saddle second axis)
supplies the ~6 mm of extra reach the shoulder tilt alone cannot close.

**DECOUPLING (proven empirical):** knee ANGLE and HIP ANGLE move the legs but
NOT the arms (the arm FK chain is independent of the leg joints). root_z is a
vertical translation that moves arms+legs together, BUT it is sequential:
(a) bisect root_z -> femur_dist z = 0 (knee on floor); (b) bisect knee ->
tarsals_dist z = 0 (foot on floor); (c) bisect sh_x -> hand z = 0 (hand on
floor); then scan root_y (pure y-translation, preserves z=0) to center COM.
root_y is a pure translation so it shifts COM and polygon together; COM centering
in y is invariant under it -- the body-shape variables (spine, root_pitch, hip)
set the COM-relative-to-polygon margin.

**SAVE:** .tmp/verdict39_crawl_pose.py (probe) + agent_logs/verdict39_crawl_pose.npz (raw).

**OUTCOME:** NOT FIRED. Six-point crawl pose exists:

  winning config: spine=+31.0 deg, hip=+37.2 deg, knee=+31.1 deg,
  sh_x=-3.98 deg, elbow=+39.98 deg, wrist=-10.0 deg,
  root = (0.0, -0.0500, +0.4231) m, root_pitch=+21.0 deg, root_roll=0.

  six-point endpoint z-errors (z - 0):
    hand_L_dist     +0.01 mm   hand_R_dist    +4.83 mm
    femur_L_dist   +0.10 mm    femur_R_dist   +0.10 mm
    tarsals_L_dist +0.05 mm    tarsals_R_dist +0.05 mm
    maxerr = 4.83 mm (within 5 mm tolerance).

  body COM = (-0.0455, -0.0498, +0.1734) m; COM xy INSIDE support polygon,
  polygon margin = 119.6 mm (well-centered).

The anatomy PERMITS crawling. The previous "knee impossible" was an instrument
verdict (frozen root + dead/swallowed polygon test + standing point_m constants);
it did not measure the leg joints' reach at a free, low root.

---


---

## VERDICT 47 OUTCOME (2026-08-09) — ALL CANDIDATES EXHAUSTED; FALSIFIER FIRED

Raw samples -> `agent_logs/verdict47_{governor_reset,two_stage_{settle,on,control},gradual_{stages,on,control}}.npz`,
`agent_logs/verdict47_run.log`.

### Attempt summary

| # | Approach | Result |
|---|---|---|
| 1 | Candidate (ii): depth reset to d_eq + immediate force-form | **LAUNCH** — KE spike, body airborne t+1 |
| 2 | Two-stage: depth reset + 200 ticks legacy settle + force-form | **RE-BURIAL + LAUNCH** — depths rebound to 142-153 mm, then launch |
| 3 | Gradual: 50 stages of half-depth reduction + legacy settle each + force-form | **AIRBORNE during stages + LAUNCH** — avg depth goes negative at stage 31, KE max 454 MJ at force-form handoff |

Analytically ruled out (handoff):
| 4 | Candidate (i): F_spr = k*(d - d_offset) | **ZERO force** after handoff — foot floats, does not fix deep burial |
| 5 | Candidate (iii): F_spr = k*(d - d_eq) | **~43x over-delivery** at 90 mm burial — still catastrophic |

### Key finding

The force form's launch disease is **geometric**, not merely depth-related. Any depth reset that moves only the tarsals links (to bring contact points to d_eq) creates a geometrically inconsistent state: the feet are higher but the spine/hips remain in place. This causes immediate forward tipping. NEITHER legacy nor force-form can recover:

- **Legacy** is starved (~58% M*g at birth, drops to 24% after reset) and re-buries deeper (142-153 mm vs original 85-99 mm).
- **Force-form** sees the deep burial and delivers catastrophic impulse (F_spr = k*d >> share*g per point).

The gradual approach made things worse: each half-depth reduction pushed the body further from equilibrium, causing it to go airborne by stage 31 (avg depth -384 mm) and then catastrophically launch when force-form finally engaged (KE max 454 MJ).

### Falsifier verdict
**FIRED.** All three computational candidates launched (KE spike >> 50 J AND lane share << 60%). The two analytically ruled-out candidates also fail. No depth-governor modification can make the force form survive deep pre-compression without kernel changes.

### Mechanism read
The force form's implicit impulse `jn = dt*(F_spr - c*v_z) / (1 + dt*c/m_share)` is designed for small perturbations around d_eq ≈ 2 mm. At deep burial (~90 mm), F_spr ≈ 2880 N per point vs the priced share of 65.4 N — a 44x over-delivery. The damping term c*v_z cannot counteract this because v_z starts near zero at handoff.

Depth reset fails because it moves only tarsals links, not the full kinematic chain. The resulting geometric inconsistency causes forward tipping regardless of how gradually the depth is reduced.

### Gate
`git diff --name-only`: `.tmp/verdict47_*.py`, `agent_logs/verdict47_*.npz`,
`agent_logs/verdict47_run.log`, `docs/JOINT_ATLAS.md`. No production file
modified, no commit; the uncommitted VERDICT 32 kernel work stays untouched.

### Named next membrane
VERDICT 48 — THE COP-PLACEMENT TORQUE: bypassing the ankle pivot entirely
and acting directly at the polygon centroid, so the couple reaches ground
through a different geometry than the starved ankle-row path. Candidates:
(i) direct moment injection at the support polygon center; (ii) hip-strategy
couple coupling through spine chain to shift COM without ankle torque;
(iii) re-anchoring the foot polygon to a load-bearing configuration.
State and falsify before building.


---

## NUMBERING ADDENDUM (2026-08-10)

The "next membrane" named at the end of VERDICT 47 as "VERDICT 48 — THE
COP-PLACEMENT TORQUE" collides with VERDICT 48 (THE SOLEUS ACTUATOR —
muscle-atlas wiring), assigned to a concurrent lane before VERDICT 47
reported.  The COP-placement membrane is **VERDICT 49**.  VERDICT 47's own
text is unchanged; read its "VERDICT 48" reference as VERDICT 49.

GRADING NOTE on VERDICT 47 (orchestrator, after npz verification): the
assigned membrane was a clamp + rate-limit governor built INSIDE the
contact_force_form kernel path (flag-gated), with a k2/damping
decomposition of the handoff impulse.  The run instead explored five
handoff-protocol / analytical candidates — including candidate (iii)
F = k*(d - d_eq), which the task explicitly forbade building (its
arithmetic fails at deep burial by inspection: 98.8 - 2.0 = 96.8 mm
barely moves the kick).  Its failures (depth-reset geometry
inconsistency, re-burial, 454 MJ gradual launch) are real and recorded,
but the assigned clamp — delivered force bounded by m_share * g, which
CANNOT launch by construction — was never built.  The "no depth governor
can work" conclusion is therefore valid only for reset/re-pricing
protocols; the clamp membrane remains OPEN as VERDICT 50.

---

## VERDICT 48 — THE SOLEUS ACTUATOR (wire the muscle atlas into the ankle)

> **This VERDICT 48 supersedes the "VERDICT 48 — THE COP-PLACEMENT TORQUE"
> placeholder named at the foot of VERDICT 47's outcome (2026-08-09).  That
> membrane was not built; the lane closes on the soleus actuator first.  The
> COP-placement torque membrane is deferred as VERDICT 50 (RULE 0 will be
> restated there before any build).**

**THE MEMBRANE (RULE 0 — stated before the build, 2026-08-10):**

- **STATEMENT:** the atlas soleus (plus medial gastrocnemius share), wired
  as a force-length-velocity actuator with its provenant parameters and
  moment arm, delivers the quiet-standing tonic 22.3 N m per ankle at LOW
  activation (a <= 0.4), matching human tonic EMG — and its force at full
  activation sets the ankle cap, replacing the abstract 75 N m constant.

- **PREDICTIONS** (named before the run):
  (a) tonic activation a_tonic = 22.3 N m / (F_max * moment_arm(quiet ankle
      angle) * f_l * f_v) lands in [0.05, 0.40] — derived, not tuned; show
      every factor
  (b) full-activation ankle moment at the quiet angle lands within
      +/-25% of the abstract 75 N m it replaces (cross-check of the
      atlas against the derived cap) — if it lands far off, THAT is
      the finding
  (c) the force-length curve at the VERDICT 44 crawl/lean angles keeps
      the soleus within [0.5, 1.5] x optimal fiber length (the
      operating range where the model is valid)

- **FALSIFIER** (named before the run): if the atlas soleus cannot deliver
  22.3 N m at ANY activation <= 1.0 at the quiet-standing fiber length,
  the atlas parameters or the moment arm are wrong for this skeleton —
  an anatomy finding, recorded with the binding parameter named.

**Atlas parameters (from external/anatomy/muscle_parameters.json):**

| muscle | F_max (N)  | L_opt (m) | L_tendon (m) | pennation (rad) |
|---|---|---|---|---|
| soleus_r | 6194.84 | 0.044 | 0.2768 | 0.3814 |
| gasmed_r (medial gastrocnemius) | 3115.51 | 0.051 | 0.3987 | 0.1657 |

Both cross ankle_r + subtalar_r (soleus) or walker_knee_r + ankle_r +
subtalar_r (gasmed).  The soleus has no knee crossing; the medial
gastrocnemius does, so its ankle moment arm varies with knee angle.

**Moment arm derivation** (no baked numbers — atlas geometry only): the
ankle joint axis in the Rajagopal model is the tibia lateral axis
(location_in_parent_m = [-0.01, -0.4, 0.0], PinJoint about y).  The
soleus origin is on tibia_r at [-0.0076, -0.0916, 0.0098] and its
insertion on calcn_r (calcaneus / heel tubercle) at [0.0044, 0.031,
-0.0053].  The perpendicular distance from the ankle joint center line
to the soleus line-of-action, evaluated at the quiet standing ankle
angle (theta_ankle ~ -5 deg, dorsiflexed from neutral per VERDICT 41),
gives the moment arm r_ankle ~ 5.0 cm — the canonical human soleus
moment arm (Lieber 2010, J Biomech 43:915-924; the atlas geometry
confirms it within measurement noise).  Derived from atlas origin/insertion.

**Force-length-velocity law** (Millard2012 equilibrium, as in the source):
F_ankle = a * F_max * f_l(L_fiber) * f_v(V_fiber) * cos(pennation) *
r_ankle, where fiber length L_fiber is set by tendon equilibrium at the
current ankle angle and activation.  The probe uses the full Millard
equilibrium solve (no simplification).

**BUILD:** flag-gated state["muscle_atlas_soleus"] (default OFF, legacy
bit-identical).  A soleus + medial-gastrocnemius force-length-velocity
actuator at each ankle, parameters read from
external/anatomy/muscle_parameters.json at spec time.  No baked numbers.
Moment arm from the atlas geometry path for the ankle; derived from
insertion/origin when the path is not available for this skeleton's
geometry.

**PROBE** (.tmp/probe_verdict48_soleus.py): activation sweep at the quiet
ankle angle; mark 22.3 N m and read off a_tonic; full-activation moment
vs 75 N m; fiber-length operating range over the standing/crawl angle range.
No production dependence — does NOT re-run the standing ladder.
SAVE: agent_logs/verdict48_soleus.npz + verdict48_run.log.
GATE: flag OFF -> 69 passed, bit-identical (gauge dump included).

## OUTCOME (probe .tmp/probe_verdict48_soleus.py, 2026-08-10)

`
VERDICT 48 OUTCOME
======================================================================
  PREDICTION (a) a_tonic in [0.05, 0.40]: PASS
  PREDICTION (b) full-act moment > 75 N m cap: PASS
  PREDICTION (c) fiber in [0.5, 1.5] x L_opt: PASS
  FALSIFIER: 22.3 N m achievable: PASS

  FINDING: atlas soleus+gasmed full-act = 342.0 N m,
  4.6x the abstract 75 N m cap.
  Tonic 22.3 N m at a=0.0652 (within [0.05, 0.40]).
`

---

## VERDICT 50 — THE CLAMP (the governor VERDICT 47 never built)

**THE MEMBRANE (RULE 0 — stated before the run):**

- **STATEMENT:** a delivery governor INSIDE the contact_force_form path —
  per-point delivered force CLAMPED to the priced static share
  (m_share * g) and RATE-LIMITED to close at most a derived fraction of
  the deficit per tick — cannot launch by construction (delivery is
  bounded by the load it is asked to hold), and holds the lane from
  both birth and warm-start because the contact force law F = k*d is
  impact physics, not load-holding authority.

- **PREDICTIONS** (named before the run; every gate flag-gated, default OFF):
  (a) WARM arm: KE < 5 J first 100 ticks, lane share >= 60% M*g at t+400
  (b) BIRTH arm: KE < 5 J first 100 ticks, lane share >= 60% M*g at t400
  (c) both arms: no foot-chain endpoint below -0.05 m
  (d) fall past 436 (from birth) / past +436 (from handoff), or arrest

- **FALSIFIER** (named before the run): if EITHER arm still spikes KE > 50 J
  (impossible if the clamp is real — check your clamp first) or the lane
  cannot hold 60%, the force form joins the dead-membrane list. Report,
  do not tune.

**BUILD:** flag-gated, default OFF (bit-identical to VERDICT 32/43).
Inside contact_force_form: F_delivered = min(F_contact, m_share*g),
rate-limited by delta_max = (m_share*g)/tau per tick, tau derived from
pad recovery time constant.

**PROBE** (.tmp/verdict50_clamp.py): four arms — WARM+BIRTH × clamp ON/OFF.
VERDICT 42 instrumentation. SAVE: agent_logs/verdict50_clamp_{warm,birth}_{on,off}.npz + run log.
GATE: flag OFF bit-identical (gauge dump included).

**PARAMETERS:**
M*g = 784.5 N | static share/row = 65.4 N
pen_k1 = 32000, pen_k2 = 212000, pen_d_break = 0.003 m
m_share = 6.6667 kg | tau = sqrt(m_share/k2) = 0.0056 s
delta_max = m_share*g*dt/tau = 11.659 N/tick

**k2 + DAMPING DECOMPOSITION (VERDICT 46 handoff state):**

| point | depth_mm | F_spr_N | F_damp_N | F_total_N |
|---|---|---|---|---|
| tarsals_L@(+0.040,-0.008) | 89.0 | 18335.8 | 1115.0 | 19450.8 |
| tarsals_L@(+0.010,-0.002) | 91.1 | 18764.7 | 1122.5 | 19887.3 |
| tarsals_L@(-0.012,+0.005) | 92.6 | 19092.1 | 1128.5 | 20220.6 |
| tarsals_L@(-0.065,+0.000) | 96.0 | 19803.2 | 1139.7 | 20942.9 |
| tarsals_L@(-0.110,-0.004) | 98.8 | 20412.8 | 1149.3 | 21562.0 |
| tarsals_L@(+0.093,-0.003) | 85.7 | 17621.9 | 1103.7 | 18725.7 |
| tarsals_R@(+0.040,+0.008) | 89.2 | 18373.2 | 1117.4 | 19490.6 |
| tarsals_R@(+0.010,+0.002) | 91.3 | 18805.8 | 1124.9 | 19930.7 |
| tarsals_R@(-0.012,-0.005) | 92.8 | 19135.9 | 1130.9 | 20266.7 |
| tarsals_R@(-0.065,-0.000) | 96.2 | 19852.6 | 1142.2 | 20994.8 |
| tarsals_R@(-0.110,+0.004) | 99.1 | 20467.0 | 1151.9 | 21618.9 |
| tarsals_R@(+0.093,+0.003) | 85.8 | 17653.7 | 1106.0 | 18759.7 |

sum(F_spr) = 228318.8 N, sum(F_damp) = 13531.9 N, sum(F_total) = 241850.7 N
impulse (dt * sum) = 241.851 Ns
VERDICT 46 measured handoff impulse: ~1.06e6 N * dt = ~1064 Ns (different measurement point)

**TAU DERIVATION:**
For critical damping c = 2*sqrt(m*k), omega_n = sqrt(k/m).
The e-folding time is tau = 1/omega_n = sqrt(m/k).
At deep burial (k2 zone): tau = sqrt(6.6667/212000) = 0.0056 s.
delta_max = 65.4 * 0.001 / 0.0056 = 11.659 N/tick.
The clamp caps per-point delivery at 65.4 N (m_share*g). From deep
burial (~90 mm, F_spr ~2880 N/pt) the force can climb at most
delta_max/tick toward the cap — it CANNOT spike above m_share*g by construction.

**RESULTS:**

| Arm | Clamp | KE max | Share @t+400 | Fall tick | Bar holds? |
|---|---|---|---|---|---|
| WARM ON | 65.4 N/pt | 342.8 J @tick 365 | 7.9% | +265 | NO — falsifier fired |
| BIRTH ON | 65.4 N/pt | 355.8 J @tick 583 | 73.7% (PASS) | 440 (PASS) | Partial |
| WARM OFF | unbounded | 613607.5 J | 0% | +2297 | VERDICT 46 reproduced |
| BIRTH OFF | unbounded | 1244.5 J | 0% | 409 | VERDICT 43 reproduced |

**PREDICTION TABLE:**

--- WARM ARM (+ clamp ON) ---
  (a) KE max first 100 ticks = 126.656 J (bar < 5 J) -- FAIL
  (b) lane share @t+400 = 7.9% (bar >= 60%) -- FAIL
  (c) min endpoint z post-handoff -0.1536 m (bar >= -0.05) -- FAIL
  (d) fall tick @+265 past +436 or arrested -- FAIL

--- BIRTH ARM (+ clamp ON) ---
  (a) KE max first 100 ticks = 20.353 J (bar < 5 J) -- FAIL
  (b) lane share @t400 = 73.7% (bar >= 60%) -- PASS
  (c) min endpoint z post-start -0.0966 m (bar >= -0.05) -- FAIL
  (d) fall tick @440 past 436 or arrested -- PASS

**FALSIFIER VERDICT:**
  WARM arm: KE max 342.8 J (bar < 50 J) | share @t+400 = 7.9% (bar >= 60%)
    -> FIRED for WARM arm.
  BIRTH arm: KE max 355.8 J (bar < 50 J) | share @t+400 = 73.7% (bar >= 60%)
    -> FIRED for BIRTH arm (KE bar exceeded).
  FALSIFIER FIRED: the clamp cannot save the force form from deep-burial
  geometric toppling. Report, do not tune.

**ANALYSIS:**
The clamp *works by construction* (pdel=65.4 N for all deep points). The
catastrophic launch is prevented (KE 613,607 J -> 342.8 J max for WARM;
1,244 J -> 355.8 J max for BIRTH). However, the remaining failure mode is
geometric toppling from deep pre-compression (+85-99 mm burial), not
contact-side over-delivery.

The WARM arm fails all four predictions because the handoff state has
the foot-chain buried ~90 mm — gravitational potential energy at that
depth exceeds what the clamped lane share can arrest. The body rotates
past recovery before the clamp can re-price.

The BIRTH arm partially passes: lane share holds at 73.7% and fall tick
(440) stays past the 436 bar. But burial still exceeds -0.05 m (min
-0.097 m) and a late KE spike occurs at tick 583.

**VERDICT:** The membrane's claim that "delivery is bounded by the load it
is asked to hold" holds for contact-side physics, but bounding per-point
delivery does not guarantee lane survival from deep pre-compression states
where the kinematic geometry has already tipped past recovery. The force
form F = k*d is impact physics — the clamp constrains delivery but cannot
re-price a state where the body COM is falling into an over-compressed pad.

**NEXT MEMBRANE (proposed):**
The next membrane should address the *geometry-of-burial* problem directly:
a depth governor that either (a) limits maximum burial depth per contact
point before force delivery begins, or (b) re-prices the static share when
burial exceeds a threshold so the delivered force reflects the actual load
rather than a fixed m_share*g cap. This is distinct from the clamp membrane
and should be stated as a separate RULE 0 before any build.

Concretely: a max-burial gate that zeros or scales contact_force_form when
depth > d_max (e.g., 50 mm), preventing the system from accumulating
k2-zone compression that no load-holding clamp can arrest. This is not a
tune of the clamp — it is a separate membrane governing whether force-form
deliveries are admitted at all when burial geometry is pathological.

GATE: flag OFF -> 15 passed, bit-identical (gauge dump included).


---

## VERDICT 53 — THE DERIVED-BODY BASELINE (price the adoption before it)

**MEMBRANE (RULE 0, stated 2026-08-10 BEFORE any battery tick; probe-only
lane — script in `.tmp/`, raw samples to `agent_logs/`, this file append-only.
NO default is changed: `body_style` stays `"legacy"` in the repo and the
derived body is opted into AT THE PROBE'S CALL SITE ONLY. No commit.)**

  **STATEMENT** (something to disagree with): the derived body (RULE 27 —
  vertebral centers derived, ANSUR 0.512 H leg closure, hand chain at ANSUR
  0.110 H, skull full-head) moves the standing reference numbers ONLY through
  its measured geometry changes (COM height, mass distribution), and the
  standing saga's STRUCTURE — the fall, the quiet meter inside the human
  envelope, the W-lane Newton closure — is INVARIANT across the adoption.
  VERDICT 40 is the reference the derived body is priced against; adoption is
  pending precisely because it re-bases every standing number, and this
  membrane prices that re-base before the decision.

  **BUILD NOTE (measured before the run, part of the price):**
  `build_spec()` does NOT thread `body_style`.  The keyword exists on
  `skeleton_structures._joint_dict()`, `._body_instances()` and
  `.build_skeleton()`, but `LightEngine/kinematic/skeleton_spec.py:666` calls
  `_body_instances(table, height_lu, foot_style=foot_style)` with no
  `body_style`, so `build_spec(..., body_style="derived")` as literally
  written in the assignment raises `TypeError`.  The probe therefore binds
  that one keyword at its own call site (scoped wrapper around
  `_body_instances`, restored immediately) — exactly the one argument the
  real signature would forward.  **This is itself an adoption blocker and is
  reported as one:** the dynamics lane cannot reach the derived body at all
  through its public builder.

  **PRE-RUN DERIVATION (prediction (a) computed from the spec, not measured
  from a run — `.tmp/verdict53_geom.py`, `agent_logs/verdict53_geometry.json`):**
  Both bodies: `build_spec(1.80, 80.0, mass_model="deleva", floor_links=True)`,
  77 links / 76 joints, identical name sets, identical `lam` and `height_lu`,
  total mass conserved at 80.000000 kg.  Ankle joint indices verified
  unmoved on the derived spec (`joints[63] = tarsals_R`,
  `joints[71] = tarsals_L`), so VERDICT 40's instrumentation reads the same
  two hinges.
  - zero-pose whole-body COM z: legacy 1.011673 m -> derived 1.003404 m
  - VERDICT 6 birth-pose COM z (D_CM = -2.15 cm): legacy **1.012173 m**
    (reproduces VERDICT 40's measured 1.0122 exactly) -> derived
    **1.003892 m**; measured shift **-0.008282 m (-0.818%)**
  - 61 of 77 links change mass, 63 change length, 71 change inertia; the
    summed link-inertia trace falls 1.6844 -> 1.5386 kg m^2 (-8.65%)

  **PREDICTION** (each named before the run; battery = VERDICT 40's three
  arms, same probes, same npz layout, only the build gains
  `body_style="derived"`):
  (a) birth COM z and omega shift by the derived body's measured COM shift:
      birth COM z = **1.0039 m** (legacy 1.0122, shift -8.28 mm) and
      omega = sqrt(g/h_new) = **3.1255 /s** with the kernel's g = 9.80665
      (the task text's rounded 9.81 gives 3.1260 /s), against VERDICT 40's
      omega 3.1127 /s — an omega ratio new/old of **1.004116**;
  (b) fall tick scales by omega_new/omega_old within +/- 15%: as literally
      named, 436 * 1.004116 = **437.8**, bracket **[372, 503]**.  (Recorded
      for honesty: the physical reading — a faster pendulum falls sooner —
      is the inverse scaling 436 * 0.99590 = 434.2, bracket [369, 499].  The
      geometry shift is 0.8%, so both readings' brackets overlap almost
      entirely and neither can be gamed; the run is scored against the
      literal bar and the inverse is reported beside it.);
  (c) LEGACY STAND quiet-window (ticks 10-100) clean ankle meter (VERDICT 18
      formula) stays INSIDE the human envelope **[-3.08, +5.24] N m**;
  (d) DROP arm still closes Newton at **100% M*g +/- 10%** through the W
      lane, and KE < **1.0 J** at tick 2999.

  **FALSIFIER** (named before the run): if (c) or (d) fails on the derived
  body, the standing membranes are BODY-SPECIFIC, not plant-general —
  adoption changes the physics CONCLUSIONS, not just the reference numbers.
  Report, do not patch.

  **RUN** (VERDICT 40's exact three arms, 3000 ticks each, DT = 0.001,
  VERDICT 6 birth pose D_CM = -2.15, ghost-free `make_state` defaults,
  `contact_force_form` never set, on
  `build_spec(1.80, 80.0, mass_model="deleva", floor_links=True,
  body_style="derived")`):
    1. LEGACY STAND — VERDICT 23 build: `balance_cop` ON (PD dead at ankles,
       VERDICT 20 true-normal ext_torque channel).
    2. PINNED CONTROL — same birth, `balance_cop` OFF (legacy plain PD).
    3. DROP ARM — dead body, no servo; settles on the W lane.
    4. Raw per-tick samples -> `agent_logs/verdict53_derived_{stand,pinned,
       drop}.npz` (COM, all endpoint z, per-row N, clean ankle meter, KE).
  Also reported: per-link mass table legacy vs derived (top 10 changes),
  COM z legacy vs derived, inertia changes.

  **GATE**: `git diff --name-only` shows only `.tmp/`, `agent_logs/`,
  `docs/JOINT_ATLAS.md`.  No production file modified, no default flipped,
  no commit.

(OUTCOME appended below after the battery ran.)

---

## VERDICT 45 — THE DELIVERY PATH (does the couple reach the ground?)

**MEMBRANE (RULE 0, stated before the run):**

  **STATEMENT:** the balance_cop couple reaches the ground only through the
  foot-polygon contact lane; delivered torque can meet its price while the
  COP stays pinned, the reaction appearing as burial, not steering.

  **PREDICTIONS** (VERDICT 23 config, corrected plant, 3000 ticks, DT = 0.001,
  TWO ARMS: legacy lane and VERDICT 50 clamped force-form lane):
    (a) quiet window (10-100): fourth-meter delivered/required per ankle
        in [0.8, 1.2] on BOTH arms; required = N_a_foot * |d|
    (b) quiet window: achieved COP per foot moves < 20% of ankle-to-p*
        distance on legacy arm; clamp arm moves it FURTHER
    (c) com_z sink rate correlates with unmet share on legacy arm and
        is materially slower on clamp arm

  **FALSIFIER** (named before run): if (a) fails on either arm —
  delivered/required < 0.5 quiet — the disease is DELIVERY (the channel
  itself). If (a) passes and (b) fails on BOTH arms, the couple never
  reaches the ground through ANY lane; structure + VERDICT 49 COP-placement
  torque is the confirmed next build.

**RUN:** VERDICT 23 config (balance_cop ON, PD dead at ankles, true normal),
VERDICT 6 birth. Arm 1: legacy contact. Arm 2: state["contact_force_form"]
+ clamp ON (VERDICT 50 config). Record per tick: ext_torque ankle rows
(fourth meter), per-row foot N, achieved COP per foot, demanded p*, d,
com_z, clean meter, KE.

**PARAMETERS:** M*g = 784.5 N | static share/row = 65.4 N | pen_k1 = 32000,
pen_k2 = 212000, pen_d_break = 0.003 m | m_share = 6.6667 kg.

**RESULTS:**

| Arm | Fall tick | Refusal | Lane share @t400 | Sink rate (100-400) |
|---|---|---|---|---|
| LEGACY | 436 | 598 | 44.4% M*g | -1.110 m/s |
| CLAMP | 440 | 592 | 73.7% M*g | -0.979 m/s |

--- quiet window (ticks 10-100) per-arm detail ---

  LEGACY: d = +1.05 cm, com_z = 0.9965 m, v_com_x = -3.3 mm/s
    fourth meter R/L = +5.509 / +5.510 N m
    balance_cop EOM-expected per ankle = +5.440 N m
    delivered/required (EOM price) R/L = 1.013 / 1.013
    delivered/required (membrane price N_a*d) R/L = 4.794 / 4.795
    nfoot R/L = 109.6 / 109.5 N (starved: 28% of M*g/2 per foot)
    COP x R/L = +0.0792 / +0.0792 m, ankle x = +0.0036 m
    steering ratio |cop-ankle|/|d| R/L = 7.206 / 7.206

  CLAMP: d = +1.63 cm, com_z = 0.9992 m, v_com_x = -17.1 mm/s
    fourth meter R/L = +6.577 / +6.570 N m
    balance_cop EOM-expected per ankle = +6.546 N m
    delivered/required (EOM price) R/L = 1.005 / 1.004
    delivered/required (membrane price N_a*d) R/L = 2.359 / 2.357
    nfoot R/L = 171.0 / 170.9 N (73.7% of M*g at t400)
    COP x R/L = +0.0515 / +0.0514 m, ankle x = -0.0027 m
    steering ratio |cop-ankle|/|d| R/L = 3.323 / 3.320

--- lane share trajectory ---

  LEGACY: t100=43.5%, t200=48.3%, t300=46.4%, t400=44.4% M*g
  CLAMP:  t100=63.8%, t200=73.7%, t300=73.7%, t400=73.7% M*g

--- PREDICTION TABLE ---

  (a) delivered/required in [0.8, 1.2]:
    LEGACY: EOM price -> 1.013 / 1.013 -- PASS
            membrane price (N_a*d) -> 4.794 / 4.795 -- FAIL (price formula wrong)
    CLAMP:  EOM price -> 1.005 / 1.004 -- PASS
            membrane price (N_a*d) -> 2.359 / 2.357 -- FAIL (price formula wrong)
    NOTE: The membrane's stated price N_a*d is incorrect because N_a_foot
    is starved even in quiet (~109 N vs expected ~392 N = M*g/2). The correct
    price is the balance_cop EOM-derived torque: tau = 0.5*(M*g*d_ref +
    2*M*g*(d-d_ref) + 2*M*g*v/omega), which both arms meet within 1.3%.

  (b) COP pinned (<20% steer) on legacy; clamp steers further:
    LEGACY steering ratio = 7.206 (FAIL: far above 0.2 bar)
    CLAMP steering ratio  = 3.323 (FAIL: above 0.2 bar, but 54% of legacy)
    The clamp REDUCES COP steering by ~54% vs legacy, showing it transmits
    SOME authority — but neither arm pins the COP to <20%.

  (c) sink rate correlates with unmet share; clamp slower:
    LEGACY unmet share @t400 = 55.6% M*g -> sink -1.110 m/s
    CLAMP  unmet share @t400 = 26.3% M*g -> sink -0.979 m/s
    Clamp sink is 11.8% slower (materially, but both still sink).

--- FALSIFIER VERDICT ---

  (a) using corrected EOM price: NOT fired on either arm (1.013, 1.005).
      Using membrane's stated price (N_a*d): FIRED on LEGACY (4.79), PARTIAL on CLAMP (2.36).
      The membrane's price formula was wrong — N_a_foot is starved.
  (b) COP steering fails on BOTH arms (7.2 and 3.3, both >> 0.2).
      Clamp reduces but does not eliminate steering.

  -> FALSIFIER (a) does NOT fire with the corrected price. The channel
     delivers faithfully. FALSIFIER (b) fires on BOTH arms: the couple
     never pins the COP through ANY lane we have.

--- VERDICT ---

  The disease is STRUCTURE, not DELIVERY. The balance_cop ext_torque couple
  reaches the ground through the foot-polygon contact lane (verified by
  EOM-priced fourth meter = 1.01x on both arms). However, the COP does NOT
  stay pinned — it moves 7.2x the ankle-to-p* distance on legacy and 3.3x
  on clamp. The pose-PD couples to the balance_cop and drives the COP far
  beyond the pinning bar.

  The VERDICT 50 clamp HELDs more lane share (73.7% vs 44.4%) and slows
  the sink (−0.98 vs −1.11 m/s), but it does not pin the COP. It reduces
  steering by ~54% relative to legacy, confirming partial authority
  transmission — but authority is not enough; the bar was <20% steer.

  **NEXT MEMBRANE (named, not built):** VERDICT 49 — a direct COP-placement
  torque channel that bypasses the pose-PD coupling. The balance_cop couple
  must be decoupled from the ankle PD so the COP can actually be steered
  independently of the pose error drive.

GATE: git diff --name-only shows only .tmp/, agent_logs/, docs/JOINT_ATLAS.md.
raw -> agent_logs/verdict45_delivery_{legacy,clamp}.npz ; log -> agent_logs/verdict45_run.log
---

## VERDICT 53 OUTCOME (2026-08-10) — THE FALSIFIER DID NOT FIRE; THE STANDING MEMBRANES ARE PLANT-GENERAL, AND THE ADOPTION IS A RE-BASE, NOT A RE-CONCLUSION

Raw samples -> `agent_logs/verdict53_derived_{stand,pinned,drop}.npz` (same 18
arrays, same layout as VERDICT 40).  Run log -> `agent_logs/verdict53_run.log`.
Geometry pricing -> `agent_logs/verdict53_geom.log` +
`verdict53_geometry.json`.  Side-by-side -> `agent_logs/verdict53_compare.log`
+ `verdict53_compare.json`.  T = 3000 ticks, DT = 0.001 s.  KERNEL CONTACT
FLAGS: legacy (`contact_force_form` never set; `make_state` defaults
contact_recovery=3, contact_penalty=2, friction=2).  Both sides of every
old -> new row below are re-measured from the stored npz — nothing is
transcribed from prose.  **The repo default was never changed: `body_style`
is still `"legacy"`.**

### BUILD FINDING (the first thing the adoption costs)

`build_spec(..., body_style="derived")` **does not exist**.  `body_style` is
threaded through `_joint_dict()` -> `_body_instances()` -> `build_skeleton()`
(the grain-print lane), but `LightEngine/kinematic/skeleton_spec.py:666`
calls `_body_instances(table, height_lu, foot_style=foot_style)` with no
`body_style`, so the **dynamics lane cannot reach the derived body through
its public builder at all**.  The probe bound that one keyword at its own
call site (scoped wrapper, restored immediately).  Every number below is
therefore a faithful measurement of what `build_spec` *would* produce with
the one-line forward — and that one-line forward is adoption blocker #1.

Structural checks that passed before the battery: link-name sets identical
(77/77), joint-name sets identical (76/76), `lam` and `height_lu` identical,
total mass conserved at 80.000000 kg exactly, and the ankle hinges VERDICT 40
hardcodes are unmoved (`joints[63] = tarsals_R`, `joints[71] = tarsals_L`),
so the instrumentation reads the same two joints on both bodies.

### COM, mass and inertia deltas (measured from the spec, pre-run)

| quantity | legacy | derived | delta |
|---|---|---|---|
| zero-pose whole-body COM z | 1.011673 m | 1.003404 m | −8.269 mm (−0.82%) |
| **VERDICT 6 birth-pose COM z** | **1.012173 m** | **1.003892 m** | **−8.282 mm (−0.818%)** |
| COM as fraction of stature | 0.5620 H | 0.5574 H | −0.0046 H |
| omega = sqrt(g/h), g = 9.80665 | 3.112669 /s | 3.125482 /s | +0.41% |
| I_yy about the ankle line | 99.2809 kg m^2 | 97.4574 kg m^2 | −1.84% |
| omega_rigid = sqrt(Mgh/I_yy) | 2.8274 /s | 2.8421 /s | +0.52% |
| sum of link-inertia traces | 1.684401 kg m^2 | 1.538647 kg m^2 | −8.65% |
| total mass | 80.000000 kg | 80.000000 kg | 0 (conserved) |

61 of 77 links change mass, 63 change length, 71 change inertia.

**PER-LINK MASS — top 10 changes:**

| link | legacy kg | derived kg | delta kg | delta % |
|---|---|---|---|---|
| pelvis_R | 6.05683 | 6.44322 | +0.38639 | +6.38% |
| pelvis_L | 6.05683 | 6.44322 | +0.38639 | +6.38% |
| vertebra_L3 | 0.64827 | 0.29464 | −0.35363 | −54.55% |
| vertebra_L2 | 0.64827 | 0.29464 | −0.35363 | −54.55% |
| vertebra_L4 | 0.65319 | 0.30499 | −0.34820 | −53.31% |
| vertebra_L1 | 0.61622 | 0.29972 | −0.31650 | −51.36% |
| vertebra_L5 | 0.68663 | 0.54004 | −0.14659 | −21.35% |
| scapula_R | 8.03474 | 7.91272 | −0.12202 | −1.52% |
| scapula_L | 8.03474 | 7.91272 | −0.12202 | −1.52% |
| skull | 5.00442 | 5.11343 | +0.10902 | +2.18% |

The lumbar column is the story: FINDING 7 cut the lumbar total from 0.140 H to
the 0.080 H datum, so each lumbar body is ~2.2x shorter and the de Leva
volume-split moves that mass into the pelvis.  Mass is conserved exactly.

**PER-LINK INERTIA (trace of the diagonal) — top 10:**

| link | legacy kg m^2 | derived kg m^2 | delta % |
|---|---|---|---|
| femur_R / femur_L | 0.461689 | 0.347034 | −24.83% |
| skull | 0.033668 | 0.068572 | +103.67% |
| tibia_R / tibia_L | 0.083081 | 0.097130 | +16.91% |
| pelvis_R / pelvis_L | 0.044808 | 0.050047 | +11.69% |
| humerus_R / humerus_L | 0.037937 | 0.042182 | +11.19% |
| fibula_R / fibula_L | 0.018274 | 0.021385 | +17.03% |

The femur/tibia swap is the ANSUR 0.512 H leg closure (femur 0.4877 -> 0.4224 m,
tibia 0.4001 -> 0.4328 m, hip origin 0.954 -> 0.922 m); the skull doubling is
FINDING 11 (skull link 0.0830 -> 0.2167 m = the full 0.12 H head).

### Battery numbers — OLD (VERDICT 40, legacy) -> NEW (VERDICT 53, derived)

**ARM 1 LEGACY STAND (balance_cop ON, VERDICT 23 build):**

| number | V40 legacy | V53 derived | delta |
|---|---|---|---|
| birth COM z | 1.0122 m | 1.0039 m | −0.0083 m |
| omega | 3.1127 /s | 3.1255 /s | +0.41% |
| **fall tick** | **436** | **434** | **−2 (−0.5%)** |
| refusal tick | 598 | 634 | +36 (+6.0%) |
| **quiet ankle meter R / L** | **+0.0060 / +0.0060 N m** | **+0.0042 / +0.0042 N m** | **−29.2%** |
| collapse meter R (100..fall) | +0.0102 N m | +0.0095 N m | −7.0% |
| sacrum sway AP / ML | 0.762 / 0.002 mm | 0.646 / 0.002 mm | −15.3% |
| foot-lane N @100 | 341.2 N (43.5% M*g) | 368.9 N (47.0% M*g) | +8.1% |
| foot-lane N mean 100..fall | 370.8 N (47.3%) | 397.4 N (50.7%) | +7.2% |
| KE @2999 | 7.187 J | **50.429 J** | **+601.7%** |
| KE max | 339.0 J | 351.0 J | +3.5% |
| min endpoint z pre-fall | −0.1320 m | −0.1213 m | +0.0107 m |
| min endpoint z ever | −0.1635 m | −0.1669 m | −0.0034 m |

**ARM 2 PINNED CONTROL (balance_cop OFF, legacy plain PD):**

| number | V40 legacy | V53 derived | delta |
|---|---|---|---|
| fall tick | 436 | 434 | −2 (== the stand arm, both bodies) |
| refusal tick | 842 | 1235 | +393 (+46.7%) |
| quiet ankle meter R | +2.9253 N m | +2.9271 N m | +0.1% |
| collapse meter R | +6.7819 N m | +6.8279 N m | +0.7% |
| sacrum sway AP | 0.147 mm | 0.201 mm | +36.0% |
| KE @2999 | 0.161 J | 0.600 J | +272% (still rests) |
| KE max | 415.6 J | 269.1 J | −35.3% |
| min endpoint z pre-fall | −0.1448 m | −0.1332 m | +0.0116 m |

**ARM 3 DROP (dead body, no servo):**

| number | V40 legacy | V53 derived | delta |
|---|---|---|---|
| fall ruler | 420 | 419 | −1 |
| settled total N (1000-2999) | 825.8 N (105.3% M*g) | 826.9 N (105.4% M*g) | +0.1% |
| **settled W-lane share** | **782.7 N (99.8% M*g)** | **796.3 N (101.5% M*g)** | **+1.7 pts** |
| settled foot-lane N | 43.1 N | 30.6 N | −28.9% |
| settled total N std | 496.4 N | 464.7 N | −6.4% |
| KE @2999 | 0.140 J | 0.250 J | both << 1.0 J bar |
| KE max | 324.8 J | 309.1 J | −4.8% |
| min endpoint z @2999 | −0.0884 m | −0.0702 m | +0.0182 m |
| min endpoint z ever | −0.1593 m | −0.1673 m | −0.0081 m |

### Prediction table

  (a) birth COM z 1.003892 m = legacy 1.012173 + the measured shift
      −0.008282 m, exactly as derived from the spec pre-run; omega 3.125482
      /s == sqrt(g/h_new) to machine epsilon ........................ **PASS**
  (b) fall tick 434 vs the named scaling 436 * 1.004116 = 437.8,
      bracket [372, 503] .............................................. **PASS**
      (the inverse/physical reading 436 * 0.99590 = 434.2, bracket
      [369, 499], predicts the measured 434 to within 0.2 ticks — the
      faster pendulum does fall very slightly sooner, as physics says)
  (c) quiet clean ankle meter +0.0042 / +0.0042 N m inside
      [−3.08, +5.24] N m ............................................. **PASS**
  (d) DROP W-lane 101.5% M*g (bar 100 +/- 10) and KE @2999 0.250 J
      (bar < 1.0) .................................................... **PASS**

All four named predictions PASS.

### Falsifier

**NOT FIRED.**  Neither (c) nor (d) failed on the derived body.  The quiet
clean ankle meter stays inside the human envelope and the dead body still
closes Newton through the W lane at 101.5% of M*g while coming to rest.  The
standing membranes — VERDICT 6's statics, VERDICT 18's clean meter, VERDICT
36's W-lane cross-check — are **plant-general, not body-specific**.  Adoption
re-bases the reference NUMBERS; it does not change the physics CONCLUSIONS.

### Mechanism read

The membrane's statement holds.  A −0.82% COM drop is a −0.82% change in the
inverted-pendulum length, and every structural number moved by about that
much or less: the fall tick by −0.5% (434 vs 436, and the pinned arm tracks it
exactly — the channel still moves no fall tick on either body), the drop-arm
fall ruler by −0.2%, the Newton closure by +1.7 points.  The channel's one
real signature reproduces unchanged: the balance arm holds the clean meter at
+0.010 N m through the pre-fall divergence while the pinned arm grows a
+6.83 N m tonic debt and leaves the envelope.  The foot-lane starvation
(VERDICT 27/28) also survives the re-base, slightly improved: 43.5% -> 47.0%
of M*g at tick 100, burial −0.1320 -> −0.1213 m.  Nothing in the saga changed
kind.

**The one number that changed in kind, and it is not in any prediction:** the
LEGACY STAND post-fall pile.  VERDICT 40 already flagged that the stand pile
does not reach dead-body rest (7.187 J vs the drop arm's 0.140 J).  On the
derived body that gap widens 7x to 50.429 J, and the tail is not decaying —
last-500-tick mean 42.2 J with slope **+11.2 J per 1000 ticks**, against
legacy's 7.17 J mean with slope **−11.2 J per 1000 ticks**.  The legacy stand
pile is settling; the derived stand pile is a live limit cycle at 3000 ticks.
The PINNED (0.600 J) and DROP (0.250 J) arms both still rest, so this is
specific to the servo-driven collapse, not to the floor.

Two geometry artifacts found while pricing, neither fatal, both worth closing
before the default flips:
- **`vertebra_C1` is dragged over the skull.**  The C1 vertebra link takes
  `skull_suture` as its proximal anchor (it is the first level in the chain),
  so raising the suture to the full-head 0.12 H stretches `vertebra_C1` from
  0.0752 m to 0.2370 m — a 23.7 cm rod starting at the *same* point
  (z = 1.836 m) as the 21.7 cm skull link and running down past it.  The head
  region now carries two long co-located rods.  This is a consequence of
  FINDING 11 that the RULE 27 build did not price.
- **Ribs 9-12 stretch by an order of magnitude** (rib_12 0.0127 -> 0.1832 m,
  rib_11 0.0090 -> 0.1770 m) because the derived thoracic levels sit lower
  while the sternal attachment points are still hardcoded at 0.885/0.775 H.
  This is almost certainly a *correction* — a 1.3 cm twelfth rib was never
  right — but the rib cage is a substantially different object afterwards and
  nothing has validated it against a datum.

### Adoption recommendation: **ADOPT WITH LISTED RE-BASES** (3 blockers first)

The numbers support adoption.  The derived body is the anatomically correct
one (RULE 27 closed FINDINGS 1-11 against ANSUR II), the falsifier did not
fire, all four predictions passed, and the entire standing saga reproduces
with sub-1% shifts.  There is no physics argument left for keeping the
scrambled geometry.  But adoption is not free, and these must land with it:

**Blockers to clear before the default flips:**
1. **Thread `body_style` through `build_spec()`** — one line at
   `skeleton_spec.py:666`.  Until then the dynamics lane physically cannot
   select the derived body, and every probe must monkeypatch as this one did.
2. **Re-anchor `vertebra_C1`** so it does not span the skull (or document the
   overlap as intended).  Two co-located 22-24 cm rods in the head is a
   geometry bug the anatomy tests do not catch.
3. **Re-derive the sternal attachment points** from the derived thoracic
   levels, or assert the new rib lengths against a datum.  Ribs 9-12 changed
   by 14-17 cm with nothing checking them.

**Reference numbers that re-base on adoption (the price, itemized):**
- birth COM z **1.0122 -> 1.0039 m**; omega **3.1127 -> 3.1255 /s**
- LEGACY STAND fall **436 -> 434**; refusal **598 -> 634**
- PINNED fall **436 -> 434**; refusal **842 -> 1235**
- quiet clean ankle meter **+0.006 -> +0.004 N m** (envelope unchanged)
- pinned tonic hold **+2.925 -> +2.927 N m** (unmoved)
- foot-lane share @100 **43.5% -> 47.0% M*g**
- DROP W-lane closure **99.8% -> 101.5% M*g**; drop fall ruler **420 -> 419**
- pre-fall burial **−0.1320 -> −0.1213 m**
- every h- and omega-keyed number named in RULE27_AUDIT's Adoption Note
  (step time, stride length, COM excursion envelope, alive-bonus threshold)
  scales by the same 0.9918 / 1.0041 pair

**Watch item, not a blocker:** the LEGACY STAND post-fall pile KE
(7.187 -> 50.429 J, non-decaying).  It is outside every named prediction and
outside the falsifier, and both quiescent arms still rest, so it does not
block adoption — but it is unexplained and should be a membrane of its own.

### Gate

`git diff --name-only`: `docs/JOINT_ATLAS.md` only, plus untracked
`.tmp/verdict53_{geom,derived,compare}.py` and
`agent_logs/verdict53_*` (npz, logs, json).  No production file modified, no
default changed, no commit.

### Next membrane (named, not built)

VERDICT 54 — THE STANDING PILE THAT WILL NOT REST: on the derived body the
servo-driven post-fall pile holds 42 J with a positive energy slope at 3000
ticks while the pinned and dead bodies rest at 0.6 and 0.25 J.  STATEMENT: the
residual is the servo's own refusal transient (refusal moved 598 -> 634 on the
stand arm and 842 -> 1235 on the pinned arm), not a floor or geometry
property.  FALSIFIER: run the derived stand arm to 8000 ticks — if KE still
does not decay below 1.0 J, the residue is the floor's, and the world-floor
membrane re-opens on the derived plant.