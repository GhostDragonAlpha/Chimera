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
