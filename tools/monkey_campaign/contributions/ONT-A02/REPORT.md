# ONT-A02 REPORT — Validate U-STR and proposed radius consequence (attempt a6c4ddd2)

Card **ONT-A02** (planning id A02), attempt `a6c4ddd216a648348d0810f05dd464d4`,
arrival `arrival-db815a40e472418c810c538a333bbc5e`.
Criteria sha256 `ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1`.
Scope sha256 `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Base revision (checkout `branch-5`) `c525b82c7c3ce0128565424764293a3c85811ab3`.
Verification profile `anatomy` (`visible_static`), `numerical_evidence_required: true`,
`clean_view_required: true`.

**done_when**

> Radioulnar definition, independent evidence, B4 result and before/after radius
> mapping are presented

**Outcome: all four clauses PRESENTED and re-verified from the pinned inputs.**
Re-measurement: **57/57 checks PASS** (`evidence/numerical_receipt.json`,
`outcome = PRESENTED_AND_VERIFIED`). Regression suite: **106/106 CPU tests PASS**.
Visual capture: canonical manifest validator + `visual_gate.verify` both
`structurally_valid: true`, 6 rows (3 views × diagnostic/clean).

Nothing was executed against any store: no production radius supersession, no hand
fit, no training-body change, no fit search, no moment-arm/utility computation. The
old radius record and every failed alternative remain preserved.

---

## 1. RADIOULNAR DEFINITION (clause 1) — re-derived from the pinned XML alone

The U-STR relationship is defined by two kinematic anchors: P = `body_origin:ulna` ↔
`elbow_R` (anchor gap 0.0), and P_d = `body_origin:radius` ↔ the derived point
`elbow_R + 5.1158 mm` along `unit(elbow→wrist)`. The quantity the derived point scales
is the authored `radius` body-origin offset in the `ulna` body frame,
`(0.0004, −0.011503, 0.019999)` m, read verbatim from `chimanoid.xml` (all four arm
quats identity → offsets compose additively).

Recomputed by this attempt (`ota02_radioulnar.py`, checks `N1.*`):

| quantity | recorded (C1 / R1) | re-measured | verdict |
|---|---|---|---|
| \|ulna→radius\| | 23.0746 mm | 23.074639975522924 mm | PASS |
| \|radius→hand_r\| | 292.0294 mm | 292.0293820833787 mm | PASS |
| \|elbow→hand_r\| straight-line | 305.7922 mm | 305.792236… mm | PASS |
| axial component | +14.324 mm | +14.323729 mm | PASS |
| lateral component | +18.088 mm | +18.087… mm | PASS |
| posterior component | +0.301 mm | +0.301… mm | PASS |
| obliquity to the forearm axis | 51.63° | 51.630…° | PASS |
| authored fraction (straight-line) | 7.5459 % | 7.545855… % | PASS |
| C1's anatomical basis `a, l, p` | `[0.060172,−0.987281,0.147155]` etc. | reproduced ≤1e-6 | PASS |

**What this measures (binding):** a KINEMATIC JOINT-FRAME offset — where the source
author placed the radius BODY ORIGIN relative to the ulna frame in the authored rest
pose. It is **not** a bone-landmark distance and **not** the radial-head position
(C1's kinematic-fragment verdict; R1's outside-the-model confirmation).

Source: `reference/baseline_snapshot/source_xml/chimanoid.xml`,
`reference/receipts/C1_c1_geometry.txt`, `reference/receipts/R1_arithmetic.txt`.

### Identity note (measured, not assumed)

The branch blobs are LF; the audit-time working tree carried Windows line endings, so
the MANIFEST-recorded hashes of content inputs differ from the raw blobs. Both are
asserted here and the equivalence is reproduced exactly:

- `chimanoid.xml`: LF blob `7caa32c6…` (154 834 B); with **only the final newline**
  as CRLF → `675e00d0…` (154 835 B) = the MANIFEST record.
- `runs/actual_monkey_fit.json`: LF blob `7b5d6345…` (1 294 000 B); full CRLF →
  `a4475550…` (1 346 469 B) = the MANIFEST record.

So the extracted inputs are the same XML/JSON the R1/I7 audits read, up to line
endings; XML/JSON semantics are identical, which is why every re-measured number
below lands on the recorded value.

---

## 2. INDEPENDENT EVIDENCE (clause 2)

### 2.1 Primary anatomy (R1) — the applicable lane

The source model is FreeMusco's fictional **"Chimanoid"** (a human model with arms ×1.2,
legs ×0.7), so no species-specific osteometry can exist; the applicable primary lane is
**human base anatomy**. R1 located three applicable primary sources
(`reference/receipts/R1_citations.md`; hash pinned in the state snapshot):

- **S1 London 1981** (JBJS Am 63:529–535; 8 elbows) — flexion about a single axis
  through the trochlear sulcus and the capitellar periphery; the radius center is AT
  the elbow joint.
- **S2 Brownhill et al. 2009** (J Biomech Eng 131:021005; 12 cadaveric specimens) — the
  radial head is a defining landmark OF the ulnohumeral flexion axis.
- **S3 Hollister et al. 1994** (Clin Orthop 298:272–276; fresh specimens) — the forearm
  rotation axis runs radial-head center → distal ulna center; the radial head is the
  proximal terminus, with **no positive distal fraction**.

Convergent result: radial head center ≈ **0 % ± ~1 %** of forearm length distal to the
humeroulnar hinge, **outside the frozen 4–12 % band by ≥ 3.0 points** (margin
recomputed, check `N4.band_margin`). The re-anchoring's ANATOMICAL reading is refuted;
its surviving basis is source-kinematic convention preservation (R1 §6).
`Macaca` morphometry exists but measures other quantities — recorded INAPPLICABLE,
never forced.

### 2.2 In-model independent checks

- **O1 roll evidence**: unanimous NO-FLIP over the declared candidate set
  (ECU-P2 63.61229795664599°, ANC-P2 17.552772577400333°, TRIlat-P5 0.15353092426937565°),
  each reproduced from `o1_combine_sign.json` to 1e-9 (`N4.o1_*`, `N4.o1_unanimous`).
  The residual selects the witness pair and is explicitly **not** validation (the roll
  reference site is circular for its own DOF); the sign rests on the independent
  split + olecranon chain.
- **C1's 10/10 ulna landmark set** reproduced under the declared frame (worst delta
  0.004 points; max transverse 15.378 mm) — `I7_09_c1_replacement.json`, `ok: true`.

---

## 3. B4 RESULT (clause 3)

The architect-authorized isolated U-STR B4 diagnostic ran on the frozen candidate
(U-STR + the O1-resolved roll: source `site:TRIlat-P5` ↔ the shipped `_band_roll`
extreme vertex; measured residual 0.1535°). Presented from the hash-pinned receipts
(`I7_07_gate_table.json`, `I7_08_radius_before_after.json`,
`I7_10_coverage_topology.json`):

| item | result |
|---|---|
| T1 source-provenance | PASS on both sides (parent `humerus(_l)`, site set 10/10 == XML) |
| T2 landmark-sufficiency | PASS (0.023074640 m / 0.005116 m; roll witnesses ≫ ROLL_EPS 1e-9) |
| T3 laterality | PASS (right→right, left→left, det(Q)=+1, handedness preserve) |
| T4 transform-explainability | PASS (orthonormality 4.1e-16, det(L)=s³, anchor gap 0.0, edge on the elbow→wrist line, C1 10/10 reproduced) |
| T5 uniqueness | PASS (resolution-consistency count = 1: supporters `['ulna']` / `['ulna_l']`) |
| T6 utility-ban (whole run) | PASS, 0 banned-evidence occurrences |
| receipt 08 internal flag | `ok: true` |
| coverage receipt 10 | `ok: true`; ulna-only scenario newly defines PT/PT_l and repairs BRD/BRD_l elbow arms |

Receipt 07 stores T1–T5 **per side** (10 verdict cells, all PASS) plus T6 once; the
I7 report's own headline counts T6 per side ("12/12 side-test verdicts + T6 process
PASS"). Both wordings are carried in the state snapshot; nothing is inflated.

**Bounds (binding).** The PASS is a **SOURCE-KINEMATIC FIDELITY** statement only. R1's
refutation is retained and not relabeled; no production radius supersession, hand fit
or training-body change is authorized or executed; a diagnostic PASS does **not** close
A03 or authorize mechanically qualified grasp. This attempt did not re-run the gate
(no repeat of completed work) — it verified the receipt arithmetic fold (clause 4) and
bound the receipts by hash.

---

## 4. BEFORE/AFTER RADIUS MAPPING (clause 4) — closed form only

Recomputed from the session-5 packet + the frozen declaration + the B4 known-good
records; every value cross-checked against receipt 08 (`N2.*`):

| record | BEFORE (frozen packet) | AFTER (forced closure, closed form) |
|---|---|---|
| radius P | `elbow_R` = (−0.11548098385334016, 0.3191090774536133, −0.0060765563324093825) | `ulna.P_d` = (−0.11781299127866669, 0.3145557153217149, −0.006067056594766505) |
| radius P_d | `wrist_R` | unchanged |
| span | 64.74489854186721 mm | **59.62909405176015 mm** |
| scale s (uniform) | 0.22170679566544982 | **0.20418868001006546** (−7.901478889 %) |
| det(full map) = s³ | 0.010897754382730345 | **0.008513242115903161** |
| rigid part G | packet rotation | **unchanged**, max abs diff 2.220446049250313e−16 |
| translation t | packet | recomputed (−0.5743881501002028, −0.36085729483653595, −0.23549874330359868) for `radius` |
| 16+16 site globals | A4-verified | recomputed: max displacement **4.950983466166482 mm** (`BICshort-P6`) / **4.948423135921825 mm** (`BIClong_l-P9`); all 16 deltas per side reproduced to ≤1e-9 m |
| source locals | verbatim | **untouched** (BEFORE map reproduces packet fitted globals to ≤1e-9 m) |

**Mechanism (why the re-anchor is forced, not chosen):** first-child shared-joint
closure — `compiler.py:399-423`, `JOINT_EPS = 1e-9` (`:47`), refusal
`shared_joint_separation` (`:422-423`), skipped only while the parent is unresolved.
Measured on the frozen record: ‖radius.P(packet) − ulna.P_d(candidate)‖ =
**5.115804490107064 mm ≫ 1e-9**.

**Fraction law (exact-float form):** 7.545855… % × 1.047128… = **7.901478889** % =
the target fraction, equality to ≤1e-9 (`N2.fraction_law`); derived point =
23.074640 × 0.22170679566544982 = **5.115804490107078 mm** (`N2.derived_mm`). The
receipts' rounded-input variant (7.5459 % × 1.0471281884537094 = 7.901478841651782 %)
is reproduced within 1e-5 pt (`N4.arith_source_pct`) and the drift factor within 1e-6.

**Definition property checks:** `P_d` after is 5.1158 mm from `elbow_R`, lies ON the
`elbow→wrist` line (perpendicular component ≤1e-12 m), and its distance to `wrist_R`
is the reduced span.

---

## 5. VISUAL EVIDENCE (anatomy profile)

`evidence/capture_sheet.png` (1920×1080, sha256 `a728b16a…`), three declared views,
each with a diagnostic + clean pair sharing camera and state binding:

- **V1 whole-creature overview** (target frame, m): target pack mesh (18 459 verts /
  36 630 tris), frame triad, boxed right forearm region, `elbow_R`/`wrist_R`, dotted
  elbow→wrist axis, and both radius proximal anchors — before (`elbow_R`) and after
  (`ulna.P_d`, +5.1158 mm) — with leader lines and labels.
- **V2 local attachment close-up** (source rest frame, mm): vendor `ulna.stl` at the
  ulna body origin and `radius.stl` at the authored offset (XML scale 1, 1.2, 1), the
  23.0746 mm kinematic offset with its axial/lateral/posterior component arrows
  (14.324 / 18.088 / 0.301 mm; 51.63°), the two body origins, the frame triad, recorded
  tendon-path waypoints (ECU-P2..P4 on the ulna, BIClong-P9/P11 on the radius) and the
  PT-P2/BRA-P3/BRA-P4 attachment sites. The distal shafts are the declared backdrop of
  the close-up (same semantics as the reviewed ONT-A01 V2).
- **V3 orthogonal side and oblique views** (target frame, m): the forearm region
  sub-mesh (all vertices within a declared 60 mm of the elbow→wrist segment) across four
  bookmarks (anterior, posterior, lateral oblique, superior) with the axis, both anchors
  and the span change annotation.

Framing is deterministic: every camera comes from the PROJECTED BOUNDS of the view's
declared subject point set with the single uniform 8 % margin; `assert_in_bounds` runs
at generation time and the all-bookmark bounds regression (`test_all_bookmark_bounds`)
re-checks every declared subject point of every view/bookmark in the committed
manifest. Diagnostic rows declare `occlusion_mode: "mixed"` (mesh depth-tested,
overlay markers/labels/paths unoccluded = xray semantics); clean rows `depth_tested`
with no layers/labels/bindings.

**Honesty label (frozen, carried in the manifest):** rasterization is a deterministic
CPU numpy z-buffer software raster + matplotlib Agg compose — **NOT native engine
frames**; no GPU, no engine start. The claim subject is anatomy evidence records, for
which component evidence is the honest bar; no native application run is claimed.

---

## 6. Reconcile-first: what existed and was reused

| record | where | reuse |
|---|---|---|
| U-STR consolidated receipt + B4 ADDENDUM 1 | `forearm_package/USTR_DIAGNOSTIC_RECEIPT.md` | read as the parent outcome record |
| U-STR / U-ANA definition table | `forearm_package/ANATOMICAL_DECISION_TABLE.md` | definition wording and candidate identity |
| R1 radioulnar evidence (definition, primary sources, refutation) | `audits/R1_radioulnar_evidence/` | clauses 1–2 |
| C1 ulna evidence (10/10 region table, anatomical basis) | `audits/C1_ulna_evidence/` | basis reproduction + landmark validation |
| I7 frozen candidate, gate table, before/after receipt, coverage | `audits/I7_ustr_diagnostic/` | clause 3–4 record of record |
| B4 known-good radius landmarks (recorded roll source) | `audits/B4_correspondence_challenge/receipts/01_known_good_records.json` | BEFORE-map reconstruction |
| O1 combine-sign receipt | `audits/O1_ulna_orientation/receipts/o1_combine_sign.json` | roll evidence cross-check |
| ONT-A01 (dependency, merged PR #176) | `tools/monkey_campaign/contributions/ONT-A01` | review-approved renderer/camera method reused and adapted |

All of the above were extracted **byte-preserved, read-only** into `reference/` with
their origin (branch/path/blob sha1 or working-tree path) and raw sha256 recorded in
`reference/EXTRACTION.json` (`_make_extraction.py`). No source repository was
modified; no git write, push or network call occurred during any probe.

Six prior ONT-A02 attempt directories exist and are empty; this attempt is the first
A02 artifact run.

---

## 7. Commands and observed results

```
cd <attempt checkout>/tools/monkey_campaign/contributions/ONT-A02

PYTHONDONTWRITEBYTECODE=1 python -B _make_extraction.py
  -> wrote 20 entries to reference/EXTRACTION.json                       [exit 0]

PYTHONDONTWRITEBYTECODE=1 python -B ota02_radioulnar.py
  -> checks 57/57 PASS  outcome=PRESENTED_AND_VERIFIED                   [exit 0]

PYTHONDONTWRITEBYTECODE=1 python -B ota02_render_views.py
  -> structurally_valid: True views: 6                                   [exit 0, ~4 s]

PYTHONDONTWRITEBYTECODE=1 python -B make_qualification_receipt.py
  -> checks {'fail': 0, 'pass': 57, 'total': 57}
     visual_gate.verify: structurally_valid true, view_count 6           [exit 0]

PYTHONDONTWRITEBYTECODE=1 python -B test_ota02_radioulnar.py
  -> 106/106 tests PASS                                                  [exit 0]
```

Falsifier bookkeeping (PREREGISTRATION §Falsifier): **F1** (identities) no mismatch —
reference integrity 20/20, MANIFEST equivalence reproduced; **F2** (values) 0 of 57
checks outside tolerance; **F3** (visual) manifest structurally valid, all-bookmark
bounds regression passes, pairs share camera/state, clean rows carry no diagnostics;
**F4** (execution) nothing executed, source locals reproduce the frozen packet exactly,
no write outside this contribution directory, B4 PASS not relabeled as anatomy.

---

## 8. Evidence index (sha256)

| artifact | sha256 |
|---|---|
| `PREREGISTRATION.md` | `c624401d…` |
| `reference/EXTRACTION.json` | `60241502…` |
| `evidence/state_snapshot.json` | `9e770ea5…` |
| `evidence/numerical_receipt.json` | `2aa382a1…` |
| `evidence/capture_sheet.png` | `a728b16a…` |
| `evidence/capture_manifest.json` | `6a7957d3…` |
| `evidence/capture_context.json` | in the qualification receipt |
| `evidence/visual_provenance.json` | in the qualification receipt |
| `evidence/qualification_receipt.json` | full digests for every entry |

Key source identities: `chimanoid.xml` `7caa32c6…` (MANIFEST-equivalent `675e00d0…`),
`actual_monkey_fit.json` `7b5d6345…` (`a4475550…`), `monkey_birth.bin` `550a5b3e…`,
`monkey_joints.bin` `74b3ab04…`, `ulna.stl` `71026415…`, `radius.stl` `1cfc0056…`.

---

## 9. What remains for the reviewer (and what this card does not claim)

1. **Independent review of the exact published head** — reproduce the re-measurement,
   inspect `evidence/capture_sheet.png` pixels against the declared subjects, and
   **fill `evidence.qualification_review`**: the `independent_review` entry in
   `qualification_receipt.json` is explicitly `pending` with a zero placeholder (the
   same shape the accepted ONT-A01 receipt carried); the reviewer must supply the real
   receipt path + raw sha256 and pin `head_sha` to the reviewed head.
2. This card presents and validates; it does **not** choose a mapping, does not
   authorize the radius supersession, and does not close A03. The anatomical-justification
   decision (kinematic fidelity vs new evidence vs declining the distal declaration)
   remains exactly where I7's DR-B left it.
3. No native runtime or human acceptance is claimed: the subject is anatomy evidence
   records, captured with component evidence, honestly labeled as such.
