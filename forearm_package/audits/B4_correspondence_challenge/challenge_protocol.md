# B4 — Correspondence Challenge Protocol (preregistered)

**Status:** FROZEN 2026-09-24, before any candidate ulna/ulna_l/hand_r/hand_l mapping exists.
**Author:** adversarial audit agent B4. **Scope:** read-only + diagnostics + isolated
reports under `forearm_package/audits/B4_correspondence_challenge/`. No fitting
searches; no ownership decisions; B4 proposes NO mapping — B4 builds and validates the
gate. Baseline is `forearm_package/baseline_snapshot/` (READ-ONLY; git-checked at end).

This protocol is the gate ANY proposed body correspondence must pass before its
evaluation may begin. Bilateral similarity alone cannot establish identity.

---

## 0. Architect's wave-2 laws (binding; quoted verbatim from the wave-2 authorization)

> "Preregister before any candidate mapping is evaluated: the claimed correspondence,
> supporting landmarks, numerical tolerances, uniqueness criteria, and falsifier. A
> mapping fails if it contradicts source evidence, requires an unexplained transform,
> or leaves multiple equally supported owners. Never choose ownership because it
> produces useful moment arms."

Each architect fail-condition and each prerequisite below maps to exactly one test:

| test | architect clause / prerequisite |
|---|---|
| T1 SOURCE-PROVENANCE | "fails if it contradicts source evidence" |
| T2 LANDMARK-SUFFICIENCY | prerequisite: the inputs the fit consumes exist and are usable |
| T3 LATERALITY | DERIVATION §5.2 handedness law (F3); left↔left, right↔right |
| T4 TRANSFORM-EXPLAINABILITY | "requires an unexplained transform" |
| T5 UNIQUENESS | "leaves multiple equally supported owners" |
| T6 UTILITY-BAN | "Never choose ownership because it produces useful moment arms" (process law) |

A candidate correspondence passes the gate **only if T1–T6 all PASS**. A single FAIL
refuses the candidate; the refusal is recorded with the fired falsifier and numbers.

---

## 1. Candidate submission format (what a challenger must declare)

A candidate is a record with, per claimed segment:
- `source_body` (the claimed owner) and `parent` (as claimed);
- target landmarks: proximal `P`, distal `P_d`, roll reference `Q` (ids + coordinates);
  width landmarks if the scale policy is `aspect`;
- source landmark resolutions (`body_origin:<name>` | `joint:<name>` | `site:<name>`)
  for every source-side id used;
- handedness policy (`preserve` | `mirror`) and, for mirror, `mirror_plane_normal`;
- scale policy (`uniform` | `aspect`) and any authored axis values with provenance;
- the coordinates (`coords`) claimed for the segment.

The known-good used for gate validation is the artifact's own accepted case:
**radius + radius_l** in `runs/actual_monkey_fit.json` (fit packet) with its authored
correspondence (`code/actual_target_fit.py::build_correspondence_envelope`), whose
canonical digest is recorded in the packet provenance
(`meta.provenance.input_files[3].sha256 = 52c92fe0d207a59971d9765d…`).

## 2. Constants and tolerances (derived from the artifacts, preregistered)

| symbol | value | source law |
|---|---|---|
| `ROLL_EPS` (roll-ref projection floor ε) | **1e-9** | `code/compiler.py:48` — `axis_parallel_roll` refusal floor (DERIVATION §5.1/§11). Amendment A1: the brief pointed at `correspondence.py`; the constant lives in `compiler.py` (`correspondence.py` carries the frame checks below). |
| `JOINT_EPS` (shared-joint closure, F1) | **1e-9 m** | `code/compiler.py:47`; DERIVATION §4: `\|P_parent_distal − P_child_proximal\| < 1e-9` |
| reconstruction bound (step-A bound) | **1e-6 m** | brief preregistration; A4 measured 4.54e-10 m packet-vs-fit agreement (export rounding floor 1e-9), so 1e-6 m has ≥3 decades headroom while still catching any undeclared transform |
| orthonormality, CONSTRUCTED frames | **1e-12** (‖MᵀM−I‖max) | DERIVATION §5.1 (frames are proper ONBs by construction; fresh float construction holds ~1e-16) |
| orthonormality, PACKET-RECORDED frames | **1e-9** (‖MᵀM−I‖max) | A4 measured 2.64e-12 on packet `rotation`/`frame_basis` (JSON export rounding floor 1e-9). Amendment A2: two-tier tolerance — a single 1e-12 tier would have failed the known-good on export rounding, i.e. a protocol defect, fixed BEFORE candidate evaluation. |
| chirality (det of frame maps, Q = R/s) | **+1 within 1e-12** | A4: det(Q) = +1.0 both radii; packet `chirality_det` = 0.9999999999999998; DERIVATION §5.2/F3 |
| target authoring frame | orthogonality ≤ **1e-6**, \|det\|−1 ≤ **1e-9** | `code/correspondence.py:53-61` (`non_proper_target_frame`) |
| scale plausibility band | **factor 2** about the ipsilateral proximal neighbor's axial evidence scale, i.e. s ∈ [s_nbr/2, 2·s_nbr] | T4 preregistration (below); outer envelope = the packet's own aspect policy `min_magnitude 0.2 / max_magnitude 5.0 / max_aspect 6.0` (`meta.aspect_bounds`) |
| T5 uniqueness margin | **factor 2 in log scale** (no competing owner with s within [s_declared/2, 2·s_declared] on the same declared target edge) | T5 preregistration (below) |
| degenerate-bone floor | **1e-12 m** | `code/compiler.py:155` (`degenerate_bone`) |

All tolerances are applied to numbers computed from the DECLARED landmarks and the
baseline artifacts only.

---

## 3. The tests

### T1 — SOURCE-PROVENANCE
**Purpose:** a body can only own what the source gives it; ownership may not be
re-assigned to convenient bodies (architect clause "contradicts source evidence").

**Procedure:**
1. Parse `source_xml/chimanoid.xml` (stdlib ElementTree, live elements only — commented
   elements are not source) into the body tree and the direct site→body ownership map
   (a `<site>` is owned by the body element it is a direct child of; `code/intake.py`
   law).
2. Check `parent`: the candidate's declared parent must equal the XML parent of
   `source_body` (the `chain_conflict` guard of `code/correspondence.py:113-117`).
3. Check site ownership: the candidate's claimed site set — for the known-good, the fit
   packet's exported `sites[*]` with `segment == source_body` — must EQUAL the XML
   direct-site set of that body. Any site in the claim not owned by the body in the XML,
   or any XML site of the body missing from the claim, fires the falsifier.
4. Check source landmark resolutions: proximal must resolve `body_origin:<source_body>`;
   distal must resolve `body_origin:<chain_child>` (chain child per XML parentage) or,
   for a leaf, a `site:` owned by the body itself (the leaf law of
   `code/actual_target_fit.py:171-177`); every `site:` resolution used as roll or width
   evidence must be owned by the XML body set {`source_body`, parent, chain_child}
   (the `_pick_roll_site` candidate law, `code/synthetic_fixtures.py:46-67`).

**Tolerance:** identity relations (exact string/set equality); no float tolerance
applies.
**Falsifier:** any candidate whose claimed site set differs from the XML's; a declared
parent that differs from the XML parent; a source resolution that names a body/site the
XML does not place there.

### T2 — LANDMARK-SUFFICIENCY
**Purpose:** the edge must be constructible at all: per DERIVATION §4–§5.1 the segment
needs proximal P, distal P_d, roll ref Q with \|t\| > ε; an `aspect` policy needs width
landmarks (DERIVATION §11 `insufficient_landmarks`, `axis_parallel_roll`,
`bad_scale_policy`).

**Procedure:**
1. From the declared landmarks: A_src = ‖src_D − src_A‖ > 1e-12 (degenerate-bone floor);
   target pair distinct: ‖P_d − P‖ > 1e-12 m.
2. Roll witness: t = (Q − P) − a·(a·(Q − P)) with a = (P_d − P)/‖P_d − P‖;
   require ‖t‖ > ROLL_EPS = 1e-9 (m). Record the measured ‖t‖ (m).
3. Scale policy: `uniform` ⇒ no width landmarks required; `aspect` ⇒ width landmarks
   declared, present, and each resolving (their declared source pairs likewise).
4. Every declared landmark id must resolve to a finite 3-vector in the declared set.

**Tolerance:** floors exactly as in §2 (`ROLL_EPS` 1e-9; degenerate floors 1e-12).
**Falsifier:** missing/unusable landmarks — a missing id, a non-finite coordinate,
‖t‖ ≤ 1e-9 (`axis_parallel_roll`), or an aspect policy without usable width landmarks.

### T3 — LATERALITY
**Purpose:** left candidates map to left targets, right to right; the handedness policy
is honored — a cross-side or handedness-flipping candidate is REFUSED (DERIVATION §5.2,
falsifier F3: "preserve mode on a mirrored target must REFUSE (`handedness_mismatch`)",
"no silent convention flip, ever").

**Procedure:**
1. Source side from the XML/DERIVATION §2 convention: right bodies authored at +z, left
   at −z (source world z-coordinate of `body_origin`; also the name suffix law
   `_r`/`_l` for limbs, unmarked = right).
2. Target side from the declared proximal joint's own side token (`_R`/`_L`) and the
   authored target frame law: source right (+z) maps onto monkey right (−x) under the
   declared frame (right × anterior = … verified by `build_target_frame` proper-ness).
3. Require side(source_body) == side(target landmark). Cross-side → FAIL.
4. Handedness: `preserve` requires every constructed frame map proper, det(R) = s³ and
   det(Q) = det(R)/s³ = +1 within 1e-12, no negative scale entry (a negative entry is
   mirror semantics, §5.2 — under `preserve` it is a silent flip → FAIL);
   `mirror` requires a declared `mirror_plane_normal` (unit, ‖n‖−1 ≤ 1e-9,
   `code/correspondence.py:88-93`) and the flip recorded (`frame_handedness: left`).
5. The packet/declaration chirality must agree: `chirality_det` ≥ 0 under `preserve`
   (the fit refuses det < 0 itself, `code/compiler.py:364-369`).

**Tolerance:** det +1 within 1e-12 (constructed); chirality_det ≥ 0 within 1e-12 of the
recorded value (packet); side tokens exact.
**Falsifier:** det/branch violations (det(Q) ≠ +1 beyond 1e-12; negative scale under
preserve; undeclared mirror), cross-side claims (left source body claimed onto a right
target landmark or vice versa).

### T4 — TRANSFORM-EXPLAINABILITY
**Purpose:** the implied body map must be reconstructible from the DECLARED landmarks
alone, with the SAME construction the fit uses (architect clause "requires an
unexplained transform"). No extra rotation/translation may be needed.

**Procedure:**
1. Rebuild the source ONB B = [a b c] from (src_A, src_D, src_Q) and the target ONB
   B' from (P, P_d, Q) with the exact §5.1 construction (`onb_from_points`:
   a = unit(P_d − P); t = rejection of Q − P; b = unit(t); c = a×b; det = +1 asserted).
2. Rebuild the scale from the declared policy: axial s_a = ‖P_d − P‖/‖src_D − src_A‖;
   authored axes as declared (with provenance); `uniform` legacy blanket permitted only
   when DECLARED (the packet's own law: uniform b/c inheritance is recorded as
   assumption, never evidence).
3. Rebuild L = B'·diag(s_a, s_b, s_c)·Bᵀ, the rigid part Q = B'·Bᵀ and det(Q).
4. Compare against the candidate's recorded transform (known-good: packet segments'
   `frame_basis`, `scale`, `rotation`): ‖Δscale‖ ≤ 1e-9; ‖ΔB'‖max ≤ 1e-9 (packet
   re-read tier); landmark reconstruction x' = P + L(x − A) of the segment's own source
   landmarks vs the recorded fitted positions within the 1e-6 m step-A bound.
5. Orthonormality of the REBUILT frames ≤ 1e-12 (constructed tier).
6. Scale plausibility vs neighbors: s_a within the factor-2 band about the ipsilateral
   proximal neighbor's axial evidence scale (for a forearm candidate the neighbor is
   humerus/humerus_l), and inside the packet aspect-policy envelope [0.2, 5.0]
   (magnitude) — a scale needing a special exception is an unexplained transform.

**Tolerance:** §2 table (1e-9 packet tier; 1e-12 constructed; 1e-6 m reconstruction;
factor-2 plausibility band).
**Falsifier:** any residual needing an unexplained transform — a rebuilt L that misses
the recorded map beyond tolerance, det(Q) ≠ +1 beyond 1e-12 after construction, a
plausible-band violation, or reconstruction error > 1e-6 m.

### T5 — UNIQUENESS
**Purpose:** "leaves multiple equally supported owners" must be excluded by a declared
margin, using declared landmarks only.

**Procedure:**
1. Comparison metric (preregistered): the **implied axial scale** s(B) = ‖P_d − P‖ /
   ‖src_D(B) − src_A(B)‖, evaluated for EVERY source body B under its own XML-consistent
   landmark resolution (prox = body_origin:B; dist = body_origin:chain_child(B), or the
   leaf law for a leaf) against the SAME declared target edge (P, P_d). This is a
   diagnostic on declared landmarks + XML facts, not a fitting search: no candidate is
   optimized; each B is evaluated exactly once at its own resolution.
2. A body B ≠ declared is a **competing owner** iff s(B) lands inside the factor-2 band
   about s(declared): s(B) ∈ [s(declared)/2, 2·s(declared)].
3. Record the full table (all bodies evaluated, their s, in-band y/n) and the separation
   ratio to the nearest alternative.

**Tolerance/margin:** uniqueness margin = factor 2 in log scale (§2). Zero competing
owners required.
**Falsifier:** one or more competing owners (a tie) → FAIL with the tie reported by
name and numbers. (The metric is deliberately the same quantity T4 already blesses as
plausible — an alternative that T4 would have accepted as plausible is exactly what
makes ownership non-unique.)

> **Amended by A5 (see Amendments):** gate-validation iteration 2 proved the bare
> factor-2 scale-band metric non-discriminating (the known-good itself fails it under
> bilateral symmetry). The GOVERNING metric is now the resolution-consistency count
> (primary; count must be exactly 1) with the factor-2 implied-scale band retained as
> the fallback that fires on under-declared candidates. The scale table is context,
> never the gate.

### T6 — UTILITY-BAN (process law)
**Purpose:** "Never choose ownership because it produces useful moment arms." Moment
arms, path lengths, tendon lengths, or any mechanical-utility number may NOT be
computed as evidence during a challenge run.

**Procedure:**
1. The challenge scripts compute no moment arms and no path/tendon lengths: no call to
   `_analytic_arm`, `_fd_arm`, `_pl`, no invocation of `compiler.fit`, no tendon export
   is read as evidence. (Audited mechanically: token scan over `scripts/` + `work/` for
   the banned call symbols; import graph check.)
2. The challenge report cites no utility number. Any moment arm, path length, or
   mechanical-advantage-like quantity appearing in `report.md`/`receipts/` as evidence
   invalidates the run.

**Tolerance:** zero occurrences (exact token scan).
**Falsifier:** any utility number cited in a challenge report or computed in a
challenge script as evidence. (Mesh/joint distances that ARE declared landmarks or
axial evidence — e.g. ‖P_d − P‖ — are landmarks, not utility; the ban covers
muscle-path/moment quantities.)

---

## 4. Gate verdict rule

- Per candidate, per side: PASS requires T1 ∧ T2 ∧ T3 ∧ T4 ∧ T5 ∧ T6.
- Any FAIL ⇒ the candidate correspondence is REFUSED for evaluation; the refusal record
  must name the fired falsifier and the numbers.
- UNCERTAIN is a verdict when a test cannot be evaluated for lack of declared inputs;
  it blocks evaluation until resolved (it is not a pass).

## 5. Gate validation against the known-good (this audit, step 2)

The gate itself is validated by running T1–T6 on the artifact's own accepted case
(radius + radius_l). EXPECT: all PASS. **Any test the known-good fails means the TEST
is wrong — fix the test, not the case, and record the iteration** (§7 amendments).
Iterations are logged in `receipts/validation_log.md`.

## 6. Preregistration (frozen, from the brief)

- **PREDICTION:** the radius/radius_l resolution passes T1–T6 cleanly (it is the
  artifact's own accepted case); the pack tri-ownership data provides genuine
  EVIDENCE-grade laterality-consistent anchors for hand-region geometry.
- **FALSIFIER:** any T-test the known-good fails (protocol defect — fix protocol,
  re-validate, record), or tri-ownership near hands turning out absent/inconsistent-
  lateral (downgrades the evidence inventory).

## 7. Amendments (append-only; all made BEFORE any candidate exists)

See §Amendments at the bottom of this file. A1–A5 were entered during gate
validation, before any candidate mapping existed; none weakens a falsifier. The
iteration-by-iteration log lives in `receipts/validation_log.md`.

---

## Amendments (append-only log)

**A1 (2026-09-24, before any candidate exists).** The brief located the roll-ref floor ε
"from correspondence.py"; measured, the constant is `ROLL_EPS = 1e-9` at
`code/compiler.py:48` (used by `onb_from_points` → `axis_parallel_roll`),
`correspondence.py` carrying the authoring-frame checks instead (orthogonality 1e-6,
det 1e-9). The protocol cites the measured location; value unchanged.

**A2 (2026-09-24, before any candidate exists).** Orthonormality is a TWO-TIER
tolerance: 1e-12 for frames constructed fresh in a validation run; 1e-9 for frames
re-read from the fit packet (JSON export rounding; A4 measured 2.64e-12, floor 1e-9).
A single 1e-12 tier would fail the known-good on export rounding — a protocol defect,
fixed here before candidate evaluation. No falsifier weakened.

**A3 (2026-09-24, before any candidate exists).** T5's competing-owner band is defined
about the DECLARED owner's implied axial scale (factor 2), identical in form to T4's
neighbor-plausibility band; the brief's example "residual ratio" metric was rejected
during derivation because a segment map absorbs any length mismatch into its scale
(residual is identically zero by construction — degenerate, non-discriminating) — the
implied-scale metric is the non-degenerate relative. No falsifier weakened.

**A4 (2026-09-24, gate-validation iteration 1 — before any candidate exists).** The
fit packet records the segment transform SPLIT per DERIVATION §5: `rotation = G =
B'·Bᵀ` (the RIGID part), `scale = S`, `translation = P − G·A`. T4's procedure step 4
was ambiguous about which recorded field the rebuilt full map `L = B'·diag(S)·Bᵀ`
compares against; the first implementation compared L to `rotation` and failed the
known-good at 6.56e-01 — a TEST defect (comparator mismatch), not a case defect.
Fixed: T4 now compares rebuilt G vs packet `rotation`, rebuilt S vs packet `scale`,
and — the decisive explainability check — landmark reconstruction
`x' = P + L(x − A)` vs the packet's recorded fitted site positions (1e-6 m bound).
The known-good then reconstructs at 5.6e-17 m (radius) / 1.7e-18 m (radius_l).
No falsifier weakened; the reconstruction bound was already preregistered.

**A5 (2026-09-24, gate-validation iteration 2 — before any candidate exists).** T5's
first metric (competing owner = implied axial scale within a factor-2 band of the
declared owner's, on the same target edge) is NON-DISCRIMINATING and was FAILED BY
THE KNOWN-GOOD ITSELF: bilateral source symmetry makes the contralateral bone's
implied scale essentially identical (s(radius_l) = s(radius) to 12 digits), and 9 of
17 bodies (femur_r/l, tibia_r/l, humerus_r/l, radius_l, thorax, thorax_dummy) land
inside the band. A metric the known-good fails is a defective metric. T5 is
re-specified: PRIMARY = resolution-consistency count — the number of source bodies
whose own XML-consistent landmark resolution (prox = body_origin:B', dist =
chain-child or leaf law, roll site owned by {B', parent, child}) coincides with the
DECLARED source resolutions; unique ownership requires count == 1. FALLBACK for an
under-declared candidate (target landmarks only, no source resolutions): the
factor-2 implied-scale band applies, and any body in band is an equally supported
owner → FAIL with the tie reported. The scale-band table is retained as recorded
context, never as the gate. No falsifier weakened: the fallback is strictly
stricter than the old single metric (it fires on every body the old metric would
have flagged), and the primary catches under-declaration the old metric missed.
