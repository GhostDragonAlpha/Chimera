# Anatomical Fitting Compiler — Derivation (membrane v1)

Scratch deliverable, built per the task memo (standalone NumPy reference; no MuJoCo;
nothing in this directory is committed or shippable as-is).

---

## 0. The Membrane (Rule 0)

### STATEMENT
A static-creature anatomy (a tree of segments with joint frames, body sites and tendon
paths, masses and inertia tensors) can be fitted to a landmarked target by a **hierarchical,
geometry-linear map**: every source segment is carried to the target by `x' = P + L(x − A)`
with `L = B'·S·Bᵀ` — a proper rotation `B'Bᵀ` of the segment *frame* and a diagonal
*symmetric* scale `S` in the segment's own coordinates — and every derived physical
quantity (path lengths, moment arms, mass, inertia, rest lengths) is a **closed form** of
`L`, with muscle forces/time-constants explicitly *not* carried across (they are
physiology, not geometry).

### PREDICTION (measured, not yet tested)
1. Fitting the real `chimanoid.xml` to a synthetic target with different limb
   proportions (longer femur, shorter tibia, wider thorax) yields **468 fitted body
   sites** that move exactly with their owning segments (residual < 1e-12 m for the
   proximal anchor), **120 rest path lengths** that scale ≈ length-ratio of their
   crossing bones, and **closed-form mass/inertia** that reproduce the hand-derived
   uniform-scale laws (m ∝ s³, I ∝ s⁵) on the global-scale run.
2. Signed tendon moment arms `∂L/∂q` computed analytically agree with central
   finite differences of path length for every tendon×coordinate pair to within
   1e-9 (relative).

### FALSIFIERS (named BEFORE the run; each is an executable test in `run_tests.py`)
- **F1 · shared joints separate**: after fitting, the fitted distal joint of a parent
  equals the fitted proximal joint of its child to < 1e-9 m. If they separate, the
  hierarchy fit is broken.
- **F2 · coordinate frames leak into physics**: rotating the entire target landmark set
  by a proper rotation R must rotate the fitted skeleton by R and leave all SCALARS
  (path lengths, |mass|, inertia spectrum, residuals) unchanged. Any scalar change is a
  frame artifact.
- **F3 · mirror silently reverses handedness**: `preserve` mode on a mirrored target
  must REFUSE (`handedness_mismatch`, computing det of the frame map); `mirror` mode
  must produce an exact reflection of the skeleton with PROPER (det=+1) frames and a
  declared negative scale axis. No silent convention flip, ever.
- **F4 · sites move inconsistently with owning segments**: for a site owned by segment i,
  a unit rotation of joint-of-i must move that site by ω×(s − J) while a site owned by a
  strand NOT in i's subtree must not move at all (≤1e-12). 
- **F5 · analytic moment arms disagree with finite differences**: |analytic − FD| ≤ 1e-9
  relative across the whole body.
- **F6 · scaling is wrong**: an s-uniform global-scale fit must produce path lengths ×s,
  masses ×s³, inertias ×s⁵, and moment arms ×s versus the s=1 fit (closed forms).
- **F7 · anatomy gets invented**: every missing landmark, undefined or axis-parallel
  roll reference, unknown site/body, unsupported path element, and handedness mismatch
  must produce a NAMED refusal (`missing_landmark`, `undefined_roll`,
  `axis_parallel_roll`, `unknown_site`, `unknown_source_body`,
  `unsupported_path_semantics`, `handedness_mismatch`, ...) — never a default number.

Plus a **counts gate** (the real file, measured): 19 bodies, 39 distinct coordinate
names, 468 spatial-referenced sites, 120 spatial tendons, 121 muscles (1 with no
tendon). The synthetic fixture reproduces these EXACT counts.

---

## 1. Scope and terminals

- **Input A — source anatomy**: the FreeMusco `chimanoid.xml` at revision
  `e021d5d9d1698dafea93c0dcf34b4bc8ce1530e7` (local: `.tmp/chimanoid.xml`), parsed with
  stdlib only into a `SourceAnatomy`.
- **Input B — correspondence**: a human-authored (or fixture-authored) mapping from
  source segments to target landmarks, joint-landmark map, per-segment roll references,
  and per-segment scale policy. The correspondence is the ONLY place taste may enter.
- **Output — FittedAnatomy**: joints, segments (frame basis + scale + transform + roll
  residue), sites (fitted global + fitted local + owning segment), tendons (path,
  rest length, per-coordinate analytic + finite-difference moment arms), physiology
  (mass/inertia about fitted CoM, muscle rest-length rebaseline, force/time-const
  carriage flags), `unsupported` inventory, and `refusals`.
- **Terminals**: everything reduces to (a) the authored correspondence landmarks
  (numeric, human-supplied) and (b) the source geometry as authored in the XML. The
  compiler adds no free constants.

---

## 2. Source model (measured from the real file)

| Quantity | Measured | Meaning |
|---|---|---|
| bodies | 19 | `pelvis`, `femur/tibia/talus/toes` × {r,l}, `thorax_dummy`, `thorax`, `humerus/ulna/radius` × {r,l} (`hand_r`,`hand_l`, `humerus`,`humerus_l`, ...) |
| distinct coordinate names | 39 | each is the direct `<joint>` child of exactly one body |
| joint elements (`//joint`) | 141 | = 39 authored + duplicates from descendant search; **the XML's descendant joint lists duplicate names down the chain** — coordinate→edge ownership comes from the DIRECT joint children, mirrored in the correspondence's per-segment `coords` |
| slide coords | 3 | `pelvis_tx/ty/tz` (root free-fly) |
| sites | 937 total `<site>`, **468 referenced by spatial tendons**, all point-only (`pos`, no quat/fromto), named `glut_med1_r-P1` … |
| spatial tendons | 120, each `<spatial name="<muscle>_tendon">`, pure `<site>` chains (lengths 2..10) |
| tendon wrappers | 2 (first = empty style carrier: `width/rgba/limited`; second holds all 120 spatials) |
| muscle actuators | 121; 120 carry `tendon/class=muscle/timeconst/force/lengthrange/ctrllimited/ctrlrange`; 1 carries only `ctrllimited/ctrlrange/scale` and `tendon=None` |
| inertial | 18 bodies own an `<inertial>` (`mass` + `fullinertia`, some with off-diagonals); `thorax_dummy` has none |

Conventions observed in the source: +y is up (pelvis above hips, spine grows +y),
right-side bodies at +z, left at −z, +x forward (proper right-handed), bodies authored
axis-aligned at rest (`pos` only, no `quat`). Every body origin = its proximal joint;
every direct `<joint>` has `pos=0 0 0` (at the body origin). Joint ranges are kinematic
and are preserved verbatim (fitted `range` is not rescaled).

---

## 3. Notation

- Column vectors in R³. `A` = source child-body origin (proximal joint),
  `D` = source child-body origin's child (distal endpoint reference) — per EDGE.
- `B` = source segment ONB, columns `[a b c]`, `a` = bone axis (proximal→distal unit),
  `b` = roll-resolved perpendicular, `c = a×b`. Proper: `det B = +1`.
- `B'eff` = fitted segment ONB at the fitted origin `P` (same construction, target data).
- `S = diag(s_a, s_b, s_c)` = geometric scale in segment coordinates. `s_rad1= s_b`,
  `s_rad2 = s_c`.
- `G = B'eff Bᵀ` = the RIGID part (maps directions and frames). `G ∈ SO(3)`.
- The transform: `x' = P + B'eff·S·Bᵀ·(x − A)` = `P + L(x − A)`, `L = B'eff S Bᵀ`.

---

## 4. Hierarchy and the fit

The source is a rooted tree (root `pelvis`). Fitting is **top-down**:

1. **Root placement**: root origin = correspondence root landmark (default target
   origin). Root orientation = the map that carries the SOURCE world axes
   `{up:+y, right:+z, forward:+x}` to the correspondence-declared target `frame`
   `{up, anterior, right}`. Both ONBs proper ⇒ root rotation `R₀ ∈ SO(3)`.
2. **Per-edge recursion**: given the fitted parent origin, each child edge's
   **proximal anchor `P` = fitted proximal-landmark; distal `P_d` = fitted distal-landmark**.
   The child origin IS `P` (shared joint). `P` and `P_d` come from target landmarks
   expressed in target world (after global_scale).
3. **Scale**: `s_a = |P_d − P| / |D − A|` (bone-length ratio). With policy `aspect`,
   `s_b, s_c` come from declared radial width landmarks; with `uniform` (default),
   `s_b = s_c = s_a`.
4. The child body's fitted frame `B'eff` at `P` is built from landmarks (below), so each
   edge is fully determined by landmarks + roll ref + scale policy.

**Joint positions are structural.** The shared joint BETWEEN parent and child is one
point; the compiler verifies `|P_edge_parent_distal − P_edge_child_proximal| < 1e-9`.
Landmarks do not pin joints directly except through this structure; a landmark that
would contradict the structure only adds to the reported residual, it never splits a
joint (F1). This makes `chain_joint_conflict` a REFUSAL only when a landmark set
declares two different 'hip_r' refs for the two edges sharing that joint.

---

## 5. Frames and the frames/scaling split

- **Frames are rigid.** The fitted child frame at its origin is `B'eff`; source axes map
  by `G` (a proper rotation). The group of frame motions is always SO(3).
- **Geometry scales.** Site offsets and body meshes scale by `S` in segment coordinates.
  Scaling lives in the segment frame, so it never tilts a hinge axis (F2).
- The fitted body orientation recorded in the output is the frame `B'eff`; the recorded
  transform splits into `rotation = G`, `scale = S`, `translation = P − G·A`.

### 5.1 ONB construction (both source and target, same procedure)
Given proximal point `P₀`, bone-distal point `P₁`, and a roll reference point `Q`
(`distance > ε` from the bone axis line):
```
a  = normalize(P₁ − P₀)                       # bone axis
t  = (Q − P₀) − a·(a·(Q − P₀))                # reject Q onto the normal plane
b  = t / |t|
c  = cross(a, b)                               # proper by construction
det([a b c]) = +1                             # asserted
```
Roll **residue** = signed angle between the declared `b` and the frame the author would
get from a different consistent choice — but we do not *solve* for roll; the
correspondence authors `Q` explicitly. No roll-ref, or `|t| < ε` (`axis_parallel_roll`),
⇒ refusal. This is the single axis of taste and it is fully declared, never inferred
(F7).

### 5.2 Mirroring
Correspondence declares `handedness: "preserve" | "mirror"` and (for mirror)
`mirror_plane_normal: n̂`.

- `preserve`: if the target landmarks reflect the source (det of the best-mapping
  < 0), the compiler has no license to fold the world ⇒ **refusal `handedness_mismatch`**
  (F3). Detection: build the frame map root→child for the first chain edge; if
  `det(B'eff) < 0` after construction (numerically), mismatch. Since construction forces
  proper frames, the mismatch is instead detected as `sign(det(R₀))` — the root map
  from source world axes to the declared target frame. A mirror-authored correspondence
  must declare `mirror`.
- `mirror`: mirror enters ONLY as a negative `S` entry. `B'eff` is forced proper by
  flipping one lateral basis column (computed normally, then `b ← −b, c ← −c`); the
  flip is recorded as `frame_handedness: left` and `mirror` in meta. Sites therefore
  reflect geometrically while frames stay proper; pump-in of the rigid rotation `G`
  sees an SO(3) element. Handedness reversal is loud, silent folds are refused.

### 5.3 Rigid frame of the root on repeated mirroring
A mirror fit of a mirror fit returns the original orientation up to the declared flip —
guaranteed because `G` and `S` commute structurally (`S` diagonal in the segment frame)
only in the sense that `G` is built from `B'eff, B`; the mirror flip lives in `S`.

---

## 6. Whole-body invariants

For any proper `R`, replacing every target landmark `p → R p + t` yields a fitted
skeleton `R·(fitted)+t` and unchanged scalar outputs (F2). Proof sketch: every `P`,
`P_d` shuffle identically, so each edge's `B'eff → R B'eff`, `S` unchanged, `G → R G`.
Path lengths, |moment arms| spectrum, det-aware volume ratios, inertia spectrum all
invariant. Reflections are excluded (refused) — that is a feature, not a bug.

---

## 7. Sites and tendon paths

- Every `SourceSite` (468) is owned by one segment (its direct child body) and sits in
  that segment's frame: fitted local `x'_loc = S · x_loc`, fitted global
  `x' = P + B'eff·x'_loc`.
- A tendon path is an ordered list of site refs → an ordered list of fitted global
  points `s₀..s_K`. Rest length `L₀ = Σ_{j<K} |s_{j+1} − s_j|`.

---

## 8. Moment arms

### 8.1 Motion model
Each coordinate `q` is authored on one edge (a direct `<joint>` of that edge's child
body), carrying source axis `ω̂_src` and type `hinge|slide`. Fitted axis
`ω̂ = G·ω̂_src`; fitted hinge center `J` = fitted child origin. Only root free-fly
coordinates (`pelvis_*`) are exempted: they move the whole skeleton rigidly, so every
fiber length is constant and the arm is **zero by definition** (root-coords listed in
output with `arm: 0, reason: rigid_reference`).

### 8.2 Analytic gradient
Path length `L(q) = Σ_j |s_{j+1}(q) − s_j(q)|`. With unit tangent `u_j = (s_{j+1}−s_j)/|·|`:

```
∂L/∂q = Σ_j  u_j · ( ∂s_{j+1}/∂q − ∂s_j/∂q )
```

For a site owned by body `b`:
- hinge at `J` with unit axis `ω̂`, rotating the jointed body: if `b` is in the joint's
  subtree (the jointed body or a descendant): `∂s/∂q = ω̂ × (s − J)`, else 0.
- slide along unit axis `d̂` (root only, exempted) — kept for completeness:
  `∂s/∂q = d̂` if `b` is in the subtree, else 0.

The whole derivative is O(edges × sites-in-paths), computed analytically from the fitted
state. **Sign convention**: positive arm ⇒ increasing `q` lengthens the tendon (the
muscle's tension produces torque opposing +q). Reported as signed; magnitude is the
customary "moment arm".

### 8.3 Finite-difference cross-check (F5)
`arm_fd = (L(q+ε) − L(q−ε)) / (2ε)` with `ε = 5e-7`, re-pathing the polyline under the
edited joint `q` (rotation about the fitted axis applied to the jointed subtree). Match
criterion: `|arm_analytic − arm_fd| / (1 + |arm_fd|) < 1e-9`. Every tendon×coordinate
pair in the fit is reported; violations are recorded (a failed F5 makes the run non-green
by explicit flag — the record exists even on pass).

---

## 9. Mass and inertia

Per `SourceBody`: `mass m`, CoM offset `c` (inertial pos, body-local), inertia `I_src`
about CoM in body-local axes (from `fullinertia`).

**Uniform-density assumption** (explicit flag `requires_density_validation: true`):
- `m' = m · |det L| = m · det S`  (proper rotations have det +1)
- Define pseudo-inertia `X = (tr I / 2)·I₃ − I`. Under `y = L x`:
  `X' = L X Lᵀ`, `I' = det(S) · (tr X' · I₃ − X')`, about the fitted CoM
  `c' = P + L c`, reported in the fitted body-frame axes `B'eff`.

### 9.1 Closed-form checks (F6)
Uniform `S = s·I₃`: `m' = s³ m`; `I' = s⁵ I`; bone lengths `×s`; path lengths `×s`;
moment arms `×s`. All five checked by executable tests. (The `det(S)` factor is exactly
what preserves volume ratio under pure scale — the whole point of geometric, not
linear-density, carriage.)

---

## 10. Muscle actuators

- `lengthrange` is **rebaselined** by the path-length ratio
  `λ = L'_rest / L_rest` (source rest = the static authored path length of the same
  tendon): `range' = λ·range`. Flag `assumption: homogeneous_path_scaling`.
- `force`, `timeconst` are **physiology, not geometry**, and are **never scaled**.
  They are carried `ingested_unchanged` with status `not_geometric →
  requires_physiological_rerun`. A downstream consumer must NOT treat them as fitted.
- The 1 muscle with `tendon=None` is carried with status `no_path` and a null tendon
  reference (refusal-free but explicit).

---

## 11. Refusal catalog (no invented defaults — F7)

| refusal | raised when |
|---|---|
| `missing_landmark` | a correspondence landmark id is not in the target (or source) landmark set |
| `undefined_roll` | a segment omits `roll_ref` |
| `axis_parallel_roll` | `roll_ref` projects onto the bone axis within ε |
| `unknown_source_body` / `unknown_source_joint` / `unknown_site` | id not in intake |
| `unsupported_path_semantics` | a spatial path contains anything but site refs (e.g. fixed/wrap) or a site Q for `fromto` sites |
| `handedness_mismatch` | `preserve` declared, target reflects source (F3) |
| `chain_joint_conflict` | two edges declare different landmarks for the shared joint |
| `insufficient_landmarks` | a segment lacks ≥2 point landmarks (prox + distal) |
| `bad_scale_policy` | `scale.policy` not in {uniform, aspect} or aspect lacks width landmarks |
| `non_proper_target_frame` | declared frame not a proper ONB |

---

## 12. Status ledger (every output value answers *where did this come from*)

- `derived` — computed by this compiler with the closed forms above.
- `kinematically_preserved` — joint ranges/axes carried verbatim (axes rotated by G, not
  re-derived).
- `ingested_unchanged` — force/timeconst carried with no geometric claim.
- `requires_density_validation` / `requires_physiological_rerun` — flags attached to
  mass-family / muscle-force-family outputs.
- `rigid_reference_zero` — root free-fly arms, defined zero.
- `absent_in_source` — tail / neck-head / articulated fingers: nothing matched such
  anatomy in the source; recorded under `unsupported`, never fabricated.

---

## 13. Falsifier → test matrix

| falsifier | executable test in `run_tests.py` |
|---|---|
| F1 | shared-joint closure across all edges |
| F2 | whole-scene proper-rotation invariance of path lengths/masses/inertia spectrum/residuals |
| F3 | preserve-mode mirror ⇒ refusal; mirror-mode ⇒ proper frames + exact reflection + declared left-handed |
| F4 | per-site subtree motion: joint of owner moves it by ω×(s−J); non-subtree sites frozen |
| F5 | analytic vs central-FD arms, whole body |
| F6 | uniform-scale closed forms s, s³, s⁵ on lengths/mass/inertia/arms |
| F7 | refusal triggers for each named case |
| counts | 19/39/468/120/121 on the REAL xml intake AND the synthetic fixture |

Appended 2026-09-23 (session 4; S1–S8 shipped in session 3 but were never entered in
this table — recorded now, rows are append-only):

| falsifier | executable test in `run_tests.py` |
|---|---|
| S1 | aspect scale-policy closed form (radial calibration) |
| S2 | NONUNIFORM affine-image mass/inertia closed forms, independent re-derivation |
| S3 | aspect bounds refuse \| flag \| unbounded — never silent repair |
| S4 | actual-monkey-target packet invariants (deterministic) |
| S5 | bounded forearm envelope estimator (interior sections; never internal anatomy) |
| S6 | strict JSON export: unresolved → null, no NaN/Infinity tokens |
| S7 | provenance record (hashes, scale, aspect policy, upstream identity) |
| S8 | actuator hygiene (120 actuator records; default not an actuator) |
| S9 | serialization gate: intentional-unresolved accepted; resolved-field NaN refused (`nonfinite_resolved_field`) |
| S10 | admission split: `transported_under_assumption` vs `physically_admitted` (0 without a validated material/mass source) |
| S11 | width screen is coarse (passes a displaced narrow cluster) vs spatial containment (fails it; axial-window miss → unresolved; band-width flip → unresolved) |
| S12 | attachment-candidates derivation: port ⇔ path end, waypoint ⇔ interior; per-tendon role unique; bit-identical rebuild |
| S13 | raw-XML-to-export unit identity: source coordinates export verbatim (the target mesh factor 0.065 never enters them); direct-XML parse equality |
| S14 | local triangle-plane section loops: closed-loop chaining (open ⇒ open, never bridged); loop identified by majority pack ownership; axis probe inside, displaced probe outside |

---

## 14. Assumptions register (what could falsify but is declared)

- Hierarchy-fit semantics: shared joints are one point; landmarks inform, never split.
- Uniform-density carriage of mass/inertia; homogeneous path scaling for `lengthrange`.
- Muscle force/time-const are not geometric and are explicitly not carried.
- Root free-fly coords are rigid-reference (zero arm) by definition.
- Destination frame handedness follows the declared frame; preserve-mode reflection is refused.