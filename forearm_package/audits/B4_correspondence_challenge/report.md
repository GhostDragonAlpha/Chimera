# B4 — Correspondence Challenge: gate built, validated, evidence inventoried

Adversarial audit agent B4 · 2026-09-24 · scope honored: read-only + diagnostics +
isolated reports; **no fitting searches, no ownership decisions, and NO hand/ulna
mapping is proposed here** — this audit builds and validates the GATE that any
proposed correspondence must pass before evaluation.

Baseline: `E:/PythonChimera/forearm_package/baseline_snapshot/` (read-only throughout).
All B4 output lives in `E:/PythonChimera/forearm_package/audits/B4_correspondence_challenge/`.
Run order: `scripts/00…09` (each writes its receipt into `receipts/`); per-test logs in
`receipts/log_*.txt`; iteration log `receipts/validation_log.md`; frozen gate
`challenge_protocol.md`.

---

## 1. Acceptance criteria — verdicts

| # | criterion | verdict | receipt |
|---|---|---|---|
| 1 | Protocol document: six tests, each with procedure + numerical tolerance + falsifier, architect's laws quoted | **PASS** | `challenge_protocol.md` (laws quoted verbatim in §0; tolerances table §2; falsifiers per test) |
| 2 | Known-good validation table (radius + radius_l x T1–T6) all PASS with receipts | **PASS** | `receipts/09_validation_table.json`, `receipts/log_09_gate_table.txt` |
| 3 | Implicit-evidence inventory classified EVIDENCE/NOISE with numbers | **PASS** | §4 below; raw numbers `receipts/08_inventory.json` |
| 4 | Protocol amendments recorded BEFORE any candidate exists | **PASS** | `challenge_protocol.md` §Amendments (A1–A5, all pre-candidate); `receipts/validation_log.md` |
| 5 | Baseline integrity | **PASS** | `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` → **empty** (re-checked at end; also asserted inside 09) |

## 2. Preregistration (frozen in the brief) — outcome

- **PREDICTION 1** — "the radius/radius_l resolution passes T1–T6 cleanly": **CONFIRMED**
  in the final state. The preregistration also declared its own falsifier: "any T-test
  the known-good fails (protocol defect — fix protocol, re-validate, record)". That
  falsifier **FIRED TWICE** during gate validation (T4 iteration 1, T5 iteration 2 —
  both times the TEST was wrong, never the case), was handled exactly per the frozen
  rule, and is recorded as amendments A4/A5 with before/after numbers
  (`receipts/validation_log.md`). The gate that exists now is the post-fix gate.
- **PREDICTION 2** — "pack tri-ownership provides genuine EVIDENCE-grade
  laterality-consistent anchors for hand-region geometry": **CONFIRMED**. Falsifier
  ("tri-ownership near hands absent / inconsistent-lateral") **NOT fired**: the
  hand-region cluster exists on both sides and laterality is consistent in
  1154/1154 arm-chain triangles per side (§4, item E4).

## 3. Known-good gate validation (criterion 2)

Extract first: the declared correspondence of the fit packet was **rebuilt
independently** from the snapshot inputs via the baseline's own builder
(`actual_target_fit.py::build_correspondence_envelope`) and its canonical digest
**matched the packet provenance exactly**
(`52c92fe0d207a59971d9765d…` == `meta.provenance.input_files[3].sha256`) — every test
below runs against the correspondence the artifact itself declares.

```
test                                       radius       radius_l  key numbers
T1 source-provenance                         PASS           PASS  parent=ulna(_l); site set == XML set (18/18 bodies); roll site XML owner=ulna(_l) ∈ legal {body, parent, child}
T2 landmark-sufficiency                      PASS           PASS  |src bone|=0.292029 m; |P_d−P|=0.064745 m; |t_roll|=0.0310 m >> eps 1e-9; policy=uniform
T3 laterality                                PASS           PASS  source z=±0.1777 (right/left) -> elbow_R/elbow_L; det(Q constructed)=+1.00000000000000; handedness=preserve; packet chirality_det=+0.9999999999999998; no negative scale
T4 transform-explainability                  PASS           PASS  frame/scale/G vs packet: 0.00e+00; orthonormality 5.2e-16 (<=1e-12); recon 5.6e-17 m / 1.7e-18 m (<=1e-6 m); s=0.221706795665 in neighbor band [0.1145,0.4581] and aspect policy [0.2,5.0]
T5 uniqueness                                PASS           PASS  resolution-consistent supporters = ['radius'] / ['radius_l'], count=1
T6 utility-ban (process)                                      PASS  0 banned-evidence occurrences in scripts/; no packet tendon/moment data read
correspondence digest match: True
baseline snapshot git status: '' (empty)
GATE VALIDATION: ALL PASS
```

Supporting numbers: `det(R) = s³ = 0.0108977544` reconstructed and consistent with the
packet (A4's measurement reproduced); shared-joint closure in the packet is exactly
`0.0` (<= JOINT_EPS 1e-9); T1's site-ownership equality holds for **all 18** source
bodies, not just the two under test.

**Validation iterations (protocol defects found by the known-good, fixed, recorded):**

| iter | test | symptom | defect | fix |
|---|---|---|---|---|
| 1 | T4 | rebuilt full map vs packet `rotation` missed by 6.56e-01 | packet records the DERIVATION §5 split (`rotation` = rigid G = B'Bᵀ; scale separate) — the test compared L to G | compare G vs `rotation`, S vs `scale`, and decisive landmark reconstruction vs fitted sites (A4) |
| 2 | T5 | preregistered factor-2 scale-band metric flagged 9 "competitors" incl. radius_l — the known-good failed its own gate | bilateral source symmetry makes the contralateral bone's implied scale identical to 12 digits; scale similarity is not evidence support | T5 re-specified (A5): primary = resolution-consistency count (must be exactly 1); band retained only as fallback that fires on under-declared candidates; scale table = context, never gate |
| 3 | T6 | scanner self-matched its own token literals; one dead line crashed the run | tooling only, no gate substance | tokens assembled from fragments; dead line removed; scan clean |

## 4. Implicit-evidence inventory (criterion 3)

Conventions measured, then used (not assumed): raw mesh RIGHT = −x (elbow_R x=−0.1155,
elbow_L x=+0.1155); source XML RIGHT = +z. Mesh: 18,459 vertices, 36,630 triangles,
extents x [−0.1993, 0.1993], y [−0.0013, 0.6481], z [−0.2787, 0.1204] m.

**EVIDENCE (usable in a future preregistration):**

- **E1 · Source parentage (XML, live elements).** `hand_r → radius → ulna → humerus →
  thorax → thorax_dummy → pelvis` (mirror for `_l`). The hand's XML parent is the
  **radius**; the radius's parent is the **ulna**. Any future correspondence must
  declare these parents or fail T1's chain check. (Fact about the source tree; not a
  mapping proposal.)
- **E2 · Source site ownership counts (XML == fit packet, 18/18 bodies).** humerus 50 /
  ulna 10 / radius 16 / hand_r 5 sites per side. The packet's exported
  `sites[*].segment` assignment equals the XML direct-site sets exactly. A future hand
  segment owns exactly 5 named sites per side (extensor/flexor insertions ECRL-P4,
  ECBR-P4, ECU-P6, FCR-P3, FCU-P4).
- **E3 · Bilateral mirror structure, measured.** 7/8 paired limb bodies have exactly
  z-mirrored body positions; 7/8 have exactly z-mirrored site sets. The ONLY arm
  asymmetries, with numbers: (a) ulna|ulna_l body position off by **5.0e-05 m** in y
  (−0.34845 vs −0.3485; inherited by radius globally: 0.823047 vs 0.822997);
  (b) radius|radius_l site pairs **BICshort-P6 off 2.732 mm** and **FCU-P2 off
  1.030 mm**. These recover wave-1's "2 source-authored pairs" and bound any future
  mirror-based tolerance argument: exact mirror equality is FALSE at exactly these
  places and true elsewhere (site level, 1e-12 m).
- **E4 · Pack tri-ownership of hand-region geometry.** Majority-owner attribution over
  36,630 triangles: elbow_R/L own 634 triangles each, wrist_R/L 520 each
  (26 triangles have no majority). Hand region = centroid distal of the wrist along
  the elbow→wrist axis AND within 1.0×|EW| (=6.47 cm) perpendicular distance:
  **445 triangles per side** (elbow-owned 428 + wrist-owned 17), a contiguous cluster
  extending **4.29 cm** distal of the wrist (median perp 1.9 cm), laterality-consistent
  in **1154/1154** arm-chain triangles per side (0 inconsistent, both sides). This is
  genuine EVIDENCE that hand-region geometry exists, is anchored to the arm chain, and
  is laterality-clean.
- **E5 · Pack joint ledger.** 31 pack joints; FK chain shoulder→elbow→wrist per side;
  band sizes elbow 318 / wrist 263 vertices; **no hand/digit joints exist in the pack**
  (confirms wave-1 A2). Consequence: the pack alone cannot supply a hand distal
  landmark — any hand correspondence must declare where its distal evidence comes from.
- **E6 · Fit-packet anchors for ulna/hand (partial records).** Joints owned by
  unresolved bodies carry MEASURED origins: elbow_flexion (ulna) at elbow_R/elbow_L;
  wrist_dev/flex/3_r (hand_r) at wrist_R; wrist_dev/flex/3_l (hand_l) at wrist_L —
  gap to pack joint position **0.0 m exactly** for all 8, status `unresolved_body`.
  The packet therefore already records, without claiming any length or scale, where
  ulna's and hand's shared joints sit in the target.
- **E7 · Ordered-but-unplaced anatomy.** 168 sites exported unplaced, of which the
  hand/ulna family is ulna 10, ulna_l 10, hand_r 5, hand_l 5 — owned, ordered, and
  unclaimed (no fabricated positions).
- **E8 · Measured edge/spans (context table, `receipts/06_t5_uniqueness.json`).**
  Target forearm edge |elbow→wrist| = 0.064745 m both sides; source spans radius
  0.292029 m vs ulna 0.023 m — the measured context any future scale discussion starts
  from (recorded as measurement, not as ownership).

**NOISE (measured, and deliberately NOT treated as correspondence evidence):**

- **N1 · Owner attribution of the hand-region triangles.** elbow_R/L own 428 of the 445
  distal-cluster triangles vs wrist's 17 — this is the pack's skin-blend law
  (A2's forensics: ridge vertices carry 0.5 elbow_R / 0.5 wrist_R), i.e. rig attachment,
  not anatomy. "Elbow owns the paw" would be noise; the laterality-clean cluster (E4)
  is the evidence.
- **N2 · The rig's own `hand_tip` measurement** (0.1351 m wrist→tip, identical both
  sides, tip at y=0.374 near elbow height): a geometry-only capture law (30 farthest
  vertices beyond the wrist, pdd < 1.2×arm) with no declared anatomical referent —
  rig diagnostic until someone declares what it measures.
- **N3 · Stale session-4 artifacts** (`grounded_chimanoid.json`, `mirror_read.json`,
  `synthetic_twin.json`): history only, never policy records (per brief). No B4 script
  reads them (verified by scan).
- **N4 · Projection artifacts in the capped beyond-wrist region**: spine_lower 1282 +
  tail_base 758 triangles per side fall inside the axis-line cap but belong to trunk or
  tail — excluded by per-owner attribution (they appear in no E-item).

## 5. Negative findings / protocol amendments (all BEFORE any candidate exists)

- **A1** — the brief's pointer for the roll floor ε resolved to `code/compiler.py:48`
  (`ROLL_EPS = 1e-9`), not `correspondence.py` (which holds the authoring-frame checks:
  orthogonality 1e-6, |det|−1 1e-9). Value unchanged.
- **A2** — orthonormality is two-tier: 1e-12 for frames constructed fresh in a
  validation run, 1e-9 for packet-recorded frames (JSON export rounding; A4 measured
  2.64e-12). A single 1e-12 tier would have failed the known-good on export rounding.
- **A3** — the brief's example T5 "residual ratio" metric is degenerate (a segment map
  absorbs any length mismatch into its scale; residual is identically 0) — rejected
  during derivation, before any run.
- **A4** — T4 comparator fixed to the packet's DERIVATION §5 transform split
  (iteration 1, §3).
- **A5** — T5 metric re-specified to resolution-consistency count with band fallback
  after the known-good failed the bare scale-band metric (iteration 2, §3). The
  fallback is strictly stricter than the original; no falsifier was weakened in any
  amendment.

## 6. Scope compliance

Read-only over the baseline (git clean; hashes verified against `MANIFEST.json` first —
44/44 files byte-identical). Module copies live in `work/modules/` (baseline files,
unmodified copies; the known-good rebuild points them at the snapshot inputs). No
fitting search was run; each T5 candidate is evaluated exactly once at its own
resolution; no ownership decision is made; no moment arm, path length, or
mechanical-utility number was computed (T6 receipt: 0 occurrences). No hand/ulna
mapping is proposed. No network, no GPU, no git writes.

## 7. Verdict

**The gate exists, is preregistered, and passes on the artifact's own accepted case
(radius + radius_l, 12/12 test-verdicts PASS + T6 process PASS).** Any ulna / ulna_l /
hand_r / hand_l correspondence may now be *submitted to* the gate — submission format
in `challenge_protocol.md` §1 — and nothing may be *evaluated* before it passes.
