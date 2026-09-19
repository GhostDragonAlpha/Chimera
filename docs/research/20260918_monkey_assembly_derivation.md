# WHOLE-BODY MACAQUE ASSEMBLY — DERIVATION FROM ADMITTED GRAPH DATA

Lane: `lane/monkey-assembly-20260918` (agent: GLM 5.3). Authored 2026-09-18 against
base commit `c43d3363` (origin/master tip). **This document authors a contract; it
implements nothing** (no engine code, no scene compiler change). Rule-0 admission:
`work.creature.macaque_assembly`, banked by
`tools/creature_graph/validation/admit_macaque_assembly_20260918.py` (idempotent,
revision-aware), rebuilt into the store by `tools/creature_graph/build_graph.py`.

**RULE 0 — STATEMENT:** Every number below is either (a) read from an admitted graph
record (cited by id), (b) computed from those records by the stated equation with no
free parameter, or (c) declared as an explicit assumption with bounds. Where the three
sources disagree in kind (species, stance, convention), the disagreement is carried,
never averaged away.

**PREDICTION (untested, falsifiable in the simulator):** the assembled 32-DOF body at
the Cayo plane stands with the fore paws carrying ~69% of body weight, runs its triceps
surae at 22–29% activation, and under zero activation folds elbow-first within 0.2 s,
dissipating ~20.5 J to prone. A simulator that stands passively, stands with the
fore/hind split inverted, or collapses tip-first has falsified this assembly.

**FALSIFIER (named before any run):** if the static solve below is replayed in the
qualified dynamics and (i) the fore/hind paw-load split differs from 69/31 ±10, (ii) the
zero-activation collapse is not elbow→knee→hip within the stated bounds, (iii) the COM
leaves the support polygon at the derived stance, or (iv) the energy ledger does not
close at 1e-5 J over the collapse — **the assembly contract is FALSE** and the next lane
supersedes this record with the measured revision, never a silent edit.

---

## 0. INPUTS (all admitted, all pinned)

| Record | What it supplies | Provenance |
|---|---|---|
| `model.anatomy.macaque_arm` | 11 bodies, 7 coordinates, 39 muscles, masses/inertias, wrap geometry | limblab monkeyArmModel @ `4fb7ddee` (MIT); M. mulatta |
| `work.creature.macaque_whole_body_sources` → observation | Oku 2021 Table 1: HAT/thigh/shank/foot/phalanges m, L, COM%, I | Oku, Ide & Ogihara 2021, Commun Biol 4:1831 (CC BY 4.0); M. fuscata, one ~10 kg male |
| `guimaraes2026.hindlimb_architecture` (batch `guimaraes_arch`, 1908 admitted / 49 quarantined) | PCSA, fascicle length, pennation, muscle mass — 30 Macaca mulatta hindlimb muscles | Guimarães, Vereecke & Wiseman 2026, PMC13425262 S1 (CC BY 4.0); specimen 127, KU Leuven, right limb |
| `oku2021.bipedal_series` (batch `oku_bipedal`, 40 series) | hip/knee/ankle/MP angles+torques, GRF h/v, 10 muscle forces, 101 samples over the cycle, before/after alteration | Oku 2021 Suppl. Data 1 (CC BY 4.0); forward-dynamics SIMULATION of a planar nine-link model — a derived reference, not a measurement |
| `janisch.wildprimate_kinematics` (batch `janisch_wildprimate_kin`, 387 strides) | quadrupedal joint angles (TD/MID/LO), excursions, 14 species; 145 cercopithecoid strides are the macaque analog | Janisch et al. 2024, figshare 23231366 (CC BY 4.0); angle conventions defined by unpinned source R code — recorded unknown |
| `work.environment.terrain` → wiring_20260918 | Cayo Santiago patch plane: `h_ellipsoidal_m = −42.82679794555668` | Copernicus GLO-30 N18W066 + EGM2008; the 5x5 window resolves to open ocean — this IS the recorded real-ground height at dataset resolution |
| Smithsonian USNM 15259 (bundle `smithsonian.usnm15259`) | cranium + mandible decoded geometry (head geometry candidate; welded, non-articulated in the locomotion ladder) | CC0 with conflicting Smithsonian copyright string — carried per the intake record |
| `docs/research/muscle_physiology_reference.md` | specific tension 25–32 N/cm² (vertebrate skeletal average band, the myobody value) | in-repo reference card |
| `docs/packets/seven_coordinate_lift_v1.md`, `docs/packets/free_root_balance_v1.md` | the coordinate machinery, frozen bit-exact controls, ledger identities this ladder must reuse | authored packets, admissions `work.dynamics.*` |

Species discipline (from `req.macaque_rebuild` + the whole-body-sources report): the
inertial hindlimb+HAT table is **M. fuscata**; the arm chain and the muscle
architecture are **M. mulatta**; the head is **M. sinica**. Every cross-species
substitution below is a DECLARED mapping with its scale statement, never a merge.

---

## 1. THE ASSEMBLY MAP

### 1.1 Which records become which segments

| Body segment | Source record | Mass used | Status |
|---|---|---|---|
| HAT (trunk+neck+head, floating base) | Oku Table 1 "HAT" minus the two arm chains (carve-out, §2) | 7.371998 kg | measured minus declared carve-out |
| Forelimb L/R (sternum-weld→clavicle→scapula welds + humerus, ulna, radius, hand) | `model.anatomy.macaque_arm` bodies `humerus/ulna/radius/hand` (+ `radius_jcc` 1e-6 kg) | 0.406001 kg/side | measured (effective segments) |
| Hindlimb L/R: thigh, shank, tarsometatarsus, phalanges | Oku Table 1 rows | 0.557/0.269/0.080/0.021 kg/side | measured (cadaver-derived) |
| Cranium + mandible | USNM 15259 geometry candidates | inside HAT | geometry only; head mass already inside Oku HAT — **no re-attribution** |
| Tail | — | 0 | `req.macaque_rebuild`: no tail DOF without species/mechanical justification; M. fuscata tail is short, non-prehensile |

The seven bone meshes and 39 musculotendon records ride with the forelimb chains
unchanged; the 30 Macaca hindlimb architecture records attach to the hindlimb chains
(§3.3). The arm's 30 wrap surfaces and 1 conditional path point stay `force_runtime_ready:
false` — they are geometry provenance, not actuator authority.

### 1.2 The joint vector

Three coordinate families, in the packets' exact conventions (ordered anatomical
transforms, rotation axes then translation axes, chain-depth order):

- **Floating base (6):** `base_rot_x/y/z`, `base_trans_x/y/z` — a 6-axis CustomJoint on
  the HAT, exactly `free_root_balance_v1.md` §D1 (no stop rows, ranges ±π/±1 m scaffold).
- **Forelimb ×2 (7 each, 14):** `shoulder_flexion, elbow_flexion, radial_pronation,
  wrist_flexion, wrist_abduction, shoulder_adduction, shoulder_rotation` — the
  seven-coordinate lift packet's pinned order; the second arm is the first mirrored
  through the sagittal plane (a declared transform mirror, no new joint types).
- **Hindlimb ×2 (6 each, 12):** hip ball (abduction, internal/external rotation,
  flexion) + knee flexion + ankle dorsiflexion + MTP dorsiflexion. The sagittal four
  are Oku's nine-link model's own joints (its angles/torques/forces are defined in
  exactly these coordinates); the two out-of-sagittal hip DOF exist because a
  quadruped carries weight through abducted hips — **derived from function, locked at
  0 until the balance stage** (declared, not measured; Ogihara's 3-D joint axes are
  ON_REQUEST).

**Total: 6 + 14 + 12 = 32 DOF.** Locked sets per stage in §6. Head stays welded into
HAT (Oku treats head+trunk+forelimbs as one link); the mandible is 1 locked DOF for a
future feeding lane, outside the locomotion contract.

### 1.3 Mass-matrix block structure (n = 32)

Exactly the free-root packet's §D2 generalized (its equations are n-generic):

```
M(q) = [ M_bb   M_bj ]   6+6+6 (base) | 14 (fore) | 12 (hind)
       [ M_bjᵀ  M_jj ]   M_bb: 6x6 rigid-body inertia of the whole animal about the base
                         M_bj: 6x26 base-joint coupling (the falling-and-flailing term)
                         M_jj: 26x26, banded along the four limb chains
g_gen = Σ_b m_b·jv_bᵀ·g ;  c = bias ;  U = −Σ_b m_b·g·p_b   (code conventions unchanged)
τ_b ≡ 0 (no root actuator); D nonzero on joint rows only.
```

## 2. THE MASS DISTRIBUTION

Oku's Table 1 sums two ways, and the assembly must say which it uses:

- **Unilateral sum** (each row once): 8.184 + 0.557 + 0.269 + 0.080 + 0.021 =
  **9.111 kg** — this is the task's named figure; it is the HAT-plus-one-leg sum.
- **Oku's own nine-link total** (limb rows doubled, as his model is bilaterally
  symmetric): 8.184 + 2×0.927 = **10.038 kg**; W = 10.038 × 9.80665 = **98.44 N**.
  The whole-body-sources observation's "implied whole body ≈ 10.0 kg" reads the same
  table the same way. **The assembly mass is 10.038 kg.**

**The forelimbs-in-HAT gap (declared):** Oku's HAT row *contains* the animal's
forelimbs (Table 1 gives no arm rows). The assembly replaces them with the measured
rhesus arm chain, so the carve-out is stated as an equation, not hidden:

```
HAT_eff = 8.184 kg − 2 × 0.406001 kg = 7.371998 kg
assembly total = HAT_eff + 2×0.406001 + 2×0.927 = 10.038000 kg (preserved exactly)
```

The substitution assumes the fuscata forelimb mass within HAT equals the mulatta arm
model's effective segment mass (0.812 kg the pair). HAT's COM fraction (52%) and pitch
inertia (2.07e-2 kg·m²) are retained on the carved-out body; the true fuscata
forelimb split — and therefore the HAT residual's true COM — is an **explicit
unknown** (Ogihara 2009 whole-body model, ON_REQUEST). This is the one place the
assembly touches a measured number with a declared mapping; everything else is
single-source.

Measured vs derived, one line: **measured** — hindlimb+HAT inertias (Oku, cadaver
lineage), arm masses/inertias (arm model), hindlimb muscle architecture (Guimarães
dissection); **derived** — HAT_eff (carve-out above), the stance geometry (§3), the
girdle load split (§3.2), the moment arms (§3.3); **unknown** — fuscata forelimb split,
Ogihara 3-D joint axes, Janisch angle-convention signs.

## 3. THE STANDING CONFIGURATION (Cayo plane, y = −42.82679794555668 m)

### 3.1 The pose comes from measurements, not taste

Hindlimb angles = Oku stance-phase means (samples with GRF v > 1 N, `before_alteration`),
whose sign convention the paper pins: hip **+0.3287 rad** (18.83°), knee **−0.8661**
(flexion κ = 49.63°), ankle **+1.3082**, MP **+0.8198**. Chain closure with NO free
parameter:

```
φ_thigh = hip flexion                                   = +18.83° from vertical
φ_shank = φ_thigh − κ                                   = −30.79° (shank slants back)
foot_pitch = ankle_angle − 90° − φ_shank                = +15.75°
```

The 15.75° residual is **the macaque's pitched, toe-grasping foot line** — the flat-foot
closure does NOT hold and the data says so; the animal stands and walks on a pitched
sole line, consistent with the 47° stance-mean MP dorsiflexion. (A −15.75° reading —
heel-down instead of toe-down — is the Janisch-convention unknown; the ladder's
falsifier F3 disambiguates it in simulation, §6.)

Derived vertical chain: ankle height = 0.074·sin(15.75°) = **0.0201 m**; hip height =
0.163·cos(18.83°) + 0.182·cos(30.79°) + 0.0201 = **0.3307 m**. Forelimb (Janisch
cercopithecoid ensemble, n=145): elbow internal 113.26° → flexion 66.74°; shoulder
height = 0.125 + 0.132·cos(66.74°) + hand contact ≈ **0.1976 m**. Trunk closure pins
the trunk pitch: dy = 0.3307 − 0.1976 = 0.1331 m over the hip→shoulder span
s (explicit unknown, Ogihara axes ON_REQUEST; bounded [0.28, 0.482] m, reference value
**s = 0.30 m** — a declared assumption): dx = 0.2689 m, **trunk pitch 26.33° from
horizontal** — a crouched quadrupedal trunk, anatomically plausible and falsifiable.

### 3.2 Whole-body COM and the girdle load split

Sagittal COM of all 13 bodies (2×5 hindlimb segments, 2×4 arm bodies, HAT_eff at 52% of
0.482 along the trunk axis): **x = +0.1917 m ahead of the hind paw line, y = 0.3581 m
above the plane; mass 10.038000 kg (exact closure)**. Support polygon (hind paw
[−0.0556, +0.0740], fore paw [+0.3602, +0.4502]): COM margins **+0.2473 m behind,
+0.2585 m ahead — inside, with ~2.5× margin either way.**

The paws do NOT share the weight equally: the trunk is a beam on two girdles with its
COM 0.2246 m along the 0.2689 m hip→shoulder span, i.e. 83.5% toward the shoulders:

```
hind girdle = W_hat × (dx − x_com_trunk)/dx = 11.90 N (16.5%)
fore girdle = 60.39 N (83.5%)
per hind paw = 5.95 + own leg 9.09  = 15.04 N  (15.3% BW)
per fore paw = 30.20 + own arm 3.98 = 34.18 N  (34.7% BW)   [sums to 98.44 N exactly]
```

**The assembled animal is forelimb-dominant (69/31), as real macaques are.** This is
a measured-geometry consequence, not an assumption, and it is the first thing a wrong
assembly gets wrong (falsifier F2).

### 3.3 Static equilibrium and the minimum muscle forces

Ground is friction-competent (Coulomb cone per the free-root packet §D5; the required
tangential/normal ratio at the derived stance is <0.1). Joint demands, hindlimb
(j = Σ r×F about each joint, +extension convention):

| Joint | External demand | Resisted by | Capacity (σ = 25–32 N/cm²) | Minimum activation |
|---|---|---|---|---|
| Ankle | 0.610 N·m dorsiflexion (paw COP lever 0.0442 m) | SOL + GAS (LG+MG) plantarflexors | 2.13–2.73 N·m | **22.3–28.6%** |
| Knee | 0.594 N·m extension (reaction) − 0.145 flexion (distal weight) → flexors hold 0.594 | BIFl + GAS knee flexors | 10.7–13.7 N·m | **4.3–5.6%** |
| Hip | ≈0 static (pin carries 5.95 N); gravity fold torque 0.172 N·m | GMED/BIFl extenders (swing) | ≫ demand | ~0 |
| MTP | ≈0.02 N·m | FDL, PLANT | ≫ demand | ~0 |
| Elbow | 5.15 N·m at the walking pose's 0.1507 m paw offset | triceps (417.3 N × 0.009 m wrap) = 3.76 N·m | **INSUFFICIENT at that pose** | — |

Capacities from Guimarães Macaca mulatta PCSA (SOL 1.241, LG 2.415, MG 2.003, VAS-sum
12.426, BFL 10.077 cm²; σ band from the pinned reference) with **effective moment arms
derived from the graph's own Oku series** by least squares, τ_j(t) = Σ_i r_ij·F_i(t)
over all 101 cycle samples (10 muscles × 4 joints; R² = 0.991 hip, 0.995 knee, 0.9997
ankle, 1.000 MP): r_SOL,ankle = −0.01744 m, r_GAS,ankle = −0.01444 m,
r_BIFl,knee = −0.03527 m, r_GAS,knee = −0.01615 m, r_VAS,knee = +0.02429 m,
r_TA,ankle = +0.02164 m, r_EDL,MP = +0.02057 m, r_FDL,MP = −0.00345 m — physiologically
ordered, signs correct per muscle. **Known gap:** rectus femoris has no Macaca row in
the Guimarães sheet (recorded), so knee-extensor capacity quotes VAS only — a
conservative lower bound.

**Derived tenability condition (the standing falsifier):** the Janisch walking-pose
forelimb cannot stand still — its paw lands 0.1507 m ahead of the shoulder, demanding
5.15 N·m of elbow extension against 3.76 N·m of triceps capacity. The stance exists but
only with the fore paw within **ℓ ≤ 3.76/34.18 = 0.110 m** of the shoulder. The
simulator's standing solution must converge inside this window, or the pose is refuted.

Terrain wiring: with the free base defined at the HAT/hip frame (per the packets'
sternum-base machinery, re-anchored), standing sets `base_trans_y = −42.82679794555668 +
0.3307 = −42.496100 m`; whole-body COM at absolute y = −42.468697 m. The opt-in
`contact_plane_height_source='terrain_cayo_20260917'` machinery (already qualified on
`work.environment.terrain`) supplies the plane; nothing in the terrain lane is edited.

## 4. THE FALL SEQUENCE (zero activation)

Gravity-only fold torques (no contact reaction credited) and distal inertias
(Oku I about segment COM + parallel axis):

| Joint | I_distal (kg·m²) | τ_g (N·m) | τ/I (rad/s²) | t to 5° fold |
|---|---|---|---|---|
| Elbow (arm) | 1.417e-3 | 0.0723 | 51.0 | **58 ms** |
| Knee (hind) | 7.971e-3 | 0.145 | 18.2 | **98 ms** |
| Hip (hind) | 3.613e-2 | 0.172 | 4.8 | **191 ms** |

**The buckling cascade is elbow → knee → hip** — the lightest-inertia, first-loaded
joint goes first, the heavy hip last — completing inside 0.2 s. The COM then drops
0.358 → ~0.15 m (prone crouch; collapsed height is a declared bound): **ΔU = m·g·Δh =
20.49 J to dissipate** through the packet's impact/friction ledgers, with a pure
free-fall time bound of 0.206 s. The rigid-body alternative — tipping about the front
paw edge from a 1° lean — runs on a ~0.15 s scale only for that first degree and then
accelerates far more slowly than the joint folds; **the body FOLDS, it does not tip.**
A simulation in which the animal tips rigidly, folds hip-first, or settles without the
~20.5 J appearing in the ledger, refutes the assembly (and the ledger bar is the
packets' own 1e-5 J).

## 5. THE GAIT REFERENCE

**Bipedal hindlimb cycle (Oku series, simulation-derived — the in-graph reference):**

- Joint-angle space: hip [−8.9°, +51.0°] (ROM 59.9°), knee [−69.5°, −26.9°] (42.5°),
  ankle [+48.5°, +86.3°] (37.8°), MP [−8.4°, +77.1°] (85.5°). Stance-phase means
  (§3.1) are the cycle's working point.
- GRF: vertical peak **106.5 N = 1.082 BW**, trough 0; horizontal
  [−0.243, +0.175] BW (braking/propulsion). **Duty factor 0.663** (67/101 samples
  loaded). Bilateral closure: 2× per-leg mean = 96.2 N vs W = 98.44 N (**−2.3%**) —
  the series closes as one leg of a symmetric bipedal walk. Cycle period is NOT in the
  data (x is % of cycle) — explicit unknown.
- Muscle-force envelopes over the cycle (N, before alteration): IL 79–668,
  GMED 1–330, VAS 10–277, SOL 1–215, GAS 0–126, BIFl 0–142, FDL 14–205, RF 0–106,
  TA 0–64, EDL 0–24.

**Quadrupedal envelope (Janisch, 145 cercopithecoid strides — Papio 29, Chlorocebus 43,
Cercopithecus 15, Lophocebus 58):** ensemble excursions hip 43.0°, forelimb 55.8°,
hindlimb 55.1°, shoulder 59.0°; touchdown means hip 33.3°, knee 120.4° (internal),
shoulder 91.0°, elbow 127.4°, wrist 153.3°; limb segments near vertical
(meanHLAng 92.0°, meanFLAng 93.3° from horizontal); TD→MID→LO progressions per joint
are in the store records. No macaque species is in the sample (recorded gap): the
cercopithecoids are the analog; the Higurashi/Dryad macaque gait set is deferred
(bearer-token), the Japanese-macaque Dryad set likewise.

**Assembly reading:** the walking gait reference is the INTERSECTION — hindlimb joint
space from Oku (same animal class, same coordinates, simulation), excursion envelopes
and duty from Janisch (wild quadrupedal kinematics), GRF scale from Oku's 1.08 BW peak
(bipedal) which upper-bounds the quadrupedal per-paw 0.35 BW stance loads. The walking
controller's reference trajectory in joint space starts at the §3 stance and traverses
the Oku ROMs at the Janisch duty.

## 6. THE IMPLEMENTATION LADDER (2-coordinate mounted arm → free-standing walker)

Each stage reuses the packets' machinery; each lands its own commit with falsifiers
run first; the qualified 2-coordinate scene stays byte-frozen at every stage (the
packets' D10/S7 dispatch law).

| Stage | DOF | Unlocked / locked | Gate (falsifier, named in advance) |
|---|---|---|---|
| A (done) | 2 | shoulder_flexion, elbow_flexion mounted | qualified; frozen control for everything above |
| B | 7 | + pronation, wrist ×2, shoulder adduction/rotation | seven-coordinate lift packet F1–F9 (oracle 1e-12) |
| C | 8 | 6 base + 2 arm; hindlimb chains absent | free-root packet F1–F9: falls at g, stands only through cone-valid contact, ledger 1e-5 |
| D | 20 | + second arm (7); head welded | F5-mirror: mirrored arm's M matches the single-arm oracle under the mirror transform at 1e-12; fall on plane contact; no new physics |
| E | 32 | + hindlimbs 6×2, sagittal 4 unlocked per leg, hip abd/rot locked at 0; mandible locked | **F1 (this contract):** replay §3 statics — paw split 69/31 ±10, COM in polygon, ankle activation 22–29% band; **F2:** zero-activation cascade elbow→knee→hip, 0.358→~0.15 m COM drop, ~20.5 J in the ledger; **F3:** pitched-sole disambiguation — only one foot-pitch sign stands with COP inside the paw |
| F | 32 | hip abd/rot unlocked (balance stage); walking targets from §5 | **F4:** walk closure — per-leg impulse/duty consistency (Oku's −2.3% bilateral closure as the template), fore-paw tenability ℓ ≤ 0.110 m enforced, ledger 1e-5 J on every query |

Stage E is the first stage this contract's falsifiers can kill: every number it needs
(§3–§4) is replayable from the store without new code. A stage that fails stops the
ladder; the next stage may not start (the lift packet's own law).

## 7. HONEST SCOPE / NON-CLAIMS

No engine code, no scene compiler change, no walking controller. The Oku series is a
simulation artifact and is never cited as a biological measurement. The Janisch angle
conventions are unpinned (their R code is not in the graph) — the ladder disambiguates
the one sign that matters (foot pitch) dynamically rather than by assumption. The
fuscata/mulatta/sinica species split is carried, not merged; the HAT carve-out is the
single declared cross-species mapping. The Cayo plane is open-ocean-resolved geoid
height — the recorded real-ground height at dataset resolution, per the terrain
receipt's own note. All derivation numbers in this document were computed by
`numpy` least squares / closed-form statics from the pinned xlsx/csv artifacts with the
pinned interpreter; no value was hand-tuned.

— lane/monkey-assembly-20260918, 2026-09-18
