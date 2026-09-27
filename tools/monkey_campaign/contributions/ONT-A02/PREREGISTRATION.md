# PREREGISTRATION — ONT-A02 (attempt a6c4ddd216a648348d0810f05dd464d4)

Frozen 2026-09-26, BEFORE any measurement, render or receipt run of this attempt.
Arrival `arrival-db815a40e472418c810c538a333bbc5e`. Card ONT-A02, planning id A02.
Criteria sha256 `ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1`.
Scope sha256 `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Verification profile `anatomy` (`visible_static`), `numerical_evidence_required: true`,
`clean_view_required: true`.

## done_when (exact card clause)

> Radioulnar definition, independent evidence, B4 result and before/after radius
> mapping are presented

Kind `measurement`. The four clauses are PRESENTATION + VERIFICATION obligations:
each must be presented with source-bound identity and re-checked against the pinned
records from this campaign lane. This card does not choose a mapping, does not
authorize a radius supersession, and does not close A03.

## Reconciliation (read-only, completed before this freeze)

- ONT-A01 (dependency) is DONE/merged (PR #176, head `6f90c288`): ulna volar-side
  roll sign determined/ambiguity recorded by the O1 audit. Its contribution
  (`tools/monkey_campaign/contributions/ONT-A01`) is reused as the O1 receipt home.
- The U-STR record chain lives on the `forearm-package-20260924` branch of
  `E:/PythonChimera` (read-only `git show` extraction, byte-preserved under
  `reference/`): `USTR_DIAGNOSTIC_RECEIPT.md` (I7 consolidated receipt + ADDENDUM 1
  B4 run), `ANATOMICAL_DECISION_TABLE.md` (I6 U-STR definition),
  `audits/R1_radioulnar_evidence/` (definition of the 7.5 %, primary human evidence,
  refutation), `audits/C1_ulna_evidence/` (10/10 landmark set), `audits/I7_ustr_diagnostic/`
  (frozen candidate, T1–T6 gate receipts, before/after radius receipt 08, C1
  replacement receipt 09, coverage receipt 10), `audits/B4_correspondence_challenge/`
  (known-good radius landmarks), and the durable session-5 baseline snapshot
  (`baseline_snapshot/MANIFEST.json`, `source_xml/chimanoid.xml`,
  `runs/actual_monkey_fit.json`).
- Identity note (measured, recorded): the branch blobs are LF; the audit-time
  working-tree files carried Windows line endings, so the MANIFEST-recorded hashes
  differ from the raw blobs for line-ending-sensitive files. Reproduced exactly:
  `actual_monkey_fit.json` CRLF variant = MANIFEST `a4475550…`; `chimanoid.xml` with
  ONLY the final newline as CRLF = MANIFEST `675e00d0…`; all other extracted XML/JSON
  content is identical up to line endings. The re-measurement below therefore asserts
  BOTH the raw-blob identity and the MANIFEST-recorded identity where one exists.
- No prior ONT-A02 attempt produced artifacts (six prior attempt dirs are empty);
  this attempt is the first A02 evidence run.

## Statement (frozen)

Present, as one source-bound evidence package for this lane:

1. **Radioulnar definition.** The U-STR radioulnar relationship is defined by two
   kinematic anchors: the ulna edge P = `body_origin:ulna` ↔ `elbow_R` (anchor gap
   0.0), and the radius edge P = `body_origin:radius` ↔ the derived point at
   5.1158 mm from the elbow along the elbow→wrist axis. The source quantity the
   derived point scales is the authored ulna→radius body-origin offset
   `(0.0004, −0.011503, 0.019999)` m — decomposed 14.324 mm distal + 18.088 mm
   lateral + 0.301 mm posterior, oblique at 51.63° to the 305.7922 mm elbow→hand
   axis (7.5459 % of that axis). This offset is a KINEMATIC JOINT-FRAME offset
   (`radius` body origin in the `ulna` frame; rest pose, all arm quats identity),
   NOT a bone-landmark distance and NOT a radial-head position.
2. **Independent evidence.** The R1 audit's three applicable primary human sources
   (London 1981, 8 elbows; Brownhill et al. 2009, 12 specimens; Hollister et al.
   1994, fresh specimens) place the radial head center ON the elbow flexion axis
   and at the proximal terminus of the forearm rotation axis: ≈ 0 % ± ~1 % of
   forearm length distal to the humeroulnar hinge, outside the frozen 4–12 %
   plausibility band by ≥ 3.0 points. The applicable lane is HUMAN base anatomy
   because the source model is FreeMusco's fictional "Chimanoid" (a modified human
   model), so no species-specific osteometry can exist. This refutes the
   re-anchorings's ANATOMICAL reading; its only surviving basis is source-kinematic
   convention preservation. Additionally, O1's roll evidence and C1's independent
   10/10 ulna landmark set are presented as the in-model independent checks.
3. **B4 result.** The authorized isolated U-STR B4 diagnostic ran (I7 receipt,
   ADDENDUM 1): 12/12 side-test verdicts PASS + T6 process PASS on the existing
   protocol with tolerances unchanged; declared candidate = U-STR + the O1-resolved
   roll (source `site:TRIlat-P5` ↔ the shipped `_band_roll` extreme vertex; measured
   residual 0.1535°). The result is a SOURCE-KINEMATIC FIDELITY statement only.
4. **Before/after radius mapping.** The closed-form consequence map a future
   authorized revision would force (nothing executed): radius P moves from
   `elbow_R` to `ulna.P_d`, span 64.7449 mm → 59.6291 mm, uniform scale
   0.22170679566544982 → 0.204188680010 (−7.9015 %), det(full map) s³
   0.0108977544 → 0.0085132421, rigid part G unchanged (same edge line, same roll
   witness), and the 16+16 radius site globals recomputed with max displacement
   4.9510 mm (`BICshort-P6`) / 4.9484 mm (`BIClong_l-P9`); source locals untouched.
   The mechanism is first-child shared-joint closure (`compiler.py:399-423`,
   `JOINT_EPS = 1e-9`): ‖radius.P(packet) − ulna.P_d(candidate)‖ = 5.1158 mm ≫ 1e-9.

## Frozen predictions (probe N = re-measurement from pinned inputs)

Identity: every `reference/` file matches `reference/EXTRACTION.json` (raw sha256);
`monkey_birth.bin` sha256 = `550a5b3e…`, `monkey_joints.bin` sha256 = `74b3ab04…`,
`reference/meshes/ulna.stl` sha256 = `71026415…`, `reference/meshes/radius.stl`
sha256 = `1cfc0056…` (as recorded by this attempt's extraction).

N1 (definition, from the pinned XML alone): ulna→radius = 23.0746 mm ± 0.0001;
radius→hand = 292.0294 mm ± 0.0001; elbow→hand straight-line = 305.7922 mm ± 0.0001;
axial component +14.324 mm ± 0.001; lateral +18.088 mm ± 0.001; posterior
+0.301 mm ± 0.001; oblique angle 51.63° ± 0.01; authored fraction 7.5459 % ± 0.0001.
Anatomical basis reproduces C1's receipted basis (axial `[0.060172, −0.987281,
0.147155]`, lateral `[−0.008952, 0.146883, 0.989113]`, p = a×l) to ±1e-5.

N2 (before/after, from the pinned packet + I7 declaration + B4 known-good records):
before radius scale `0.22170679566544982`; span `0.06474489854186721` m; gap
`0.005115804490107064` m; after scale `0.20418868001006546`; after span
`0.05962909405176015` m; det after `0.008513242115903171`; `G` vs packet ≤ 1e-15;
scale change −7.901478889180636 %; max site displacement ≥ 4.950983466166482 mm
(`BICshort-P6`) within ±1e-9 m of the receipt's recorded value; source locals
byte-identical (no write). Fraction law: 7.5459 % × 1.0471281884537094 =
7.901478841651782 % (equality to ≤1e-9).

N3 (B4 presentation): the recorded verdict set in receipt 07/08 is reproduced as
the presented result, and receipts 09/10 are hash-pinned. This attempt does NOT
re-run the gate (no repeat of completed work); it verifies the receipt arithmetic
fold (N2) and reports both.

N4 (independent evidence): the recorded primary fraction ≈ 0–1 % lies outside the
frozen 4–12 % band; margin ≥ 3.0 points reproduced by arithmetic; O1's declared
residuals (ECU-P2 63.61°, ANC-P2 17.55°, TRIlat-P5 0.1535°) reproduce from the O1
receipt to ≤1e-9; the roll sign basis is recorded as O1's unanimous no-flip result.

## Falsifier (decidable either way, reported as it falls)

F1: any identity assertion above fails → the package must not present that clause as
    verified; record the mismatch.
F2: any N1/N2/N4 value outside its frozen tolerance → disagreement with the record;
    the attempt does NOT overrule the record — it presents BOTH readings and flags
    the disagreement to the reviewer.
F3: the profile falsifier (visual): "Wrong owner/frame, hidden outside placement,
    clipped/occluded subject or label ambiguity fails. View toggles must preserve
    the physical state hash." Every declared subject point of every view must project
    inside its panel with the frozen 8 % margin (bounds regression); diagnostic and
    clean rows of a pair share identical camera and state binding.
F4: any write outside the attempt workspace, any execution of a supersession, or any
    claim that the B4 PASS is anatomical evidence fails the attempt.

Outcome rule: all four clauses presented with N1–N4 verified and F3 passing →
done_when satisfied as "presented", with the honesty bounds below. Any F1/F2 hit →
the clause is presented with the exact discrepancy recorded and the reviewer decides.

## Probes frozen before execution

Numerical (CPU-only, deterministic, no GPU, no network): N1–N4 as above, run by
`ota02_radioulnar.py` with `python -B`; every input is read read-only from
`reference/` or the pinned `Saved/meshes/` inputs with hash assertions.

Visual (`anatomy` profile; three declared views, each diagnostic + clean pair):
- V1 `whole-creature overview` — target pack mesh (`monkey_birth.bin`) whole body in
  the target world frame (m), frame triad, boxed right forearm region, `elbow_R` /
  `wrist_R`, the elbow→wrist axis, and BOTH radius proximal anchors (before =
  `elbow_R`; after = `ulna.P_d`, +5.1158 mm toward the wrist); layer set includes
  outer envelope, selected bones/joints, attachment sites, frame axes, stable labels.
- V2 `local attachment close-up` — SOURCE rest frame (mm): vendor `ulna.stl`
  (authored scale 1, 1.2, 1 from the XML) and `radius.stl` placed at the authored
  ulna→radius offset, the ulna origin / radius origin markers, the offset's
  axial/lateral/posterior component arrows, and the 51.63° obliquity annotation;
  layers include selected bones/joints, attachment sites, frame axes, stable labels.
- V3 `orthogonal side and oblique views` — target forearm region (m): four-bookmark
  sampled trajectory (anterior, posterior, lateral-oblique, superior) showing the
  elbow→wrist axis, the before anchor, the after anchor, and the 5.1158 mm /
  59.6291 mm span change; layers include selected bones/joints, frame axes, labels.

Camera framing is never hand-picked: every camera is computed from the PROJECTED
BOUNDS of its declared subject point set with the single uniform margin
`FRAME_MARGIN = 0.08`, guarded by `assert_in_bounds` at generation time and by an
all-bookmark bounds regression in the test suite. Renderer honesty label (frozen):
deterministic CPU numpy z-buffer software raster + matplotlib Agg compose; NOT
native engine frames; subject is anatomy evidence records — component evidence is
the honest bar for this card (no native application run is claimed).
`tick_interval = [0, 0]` with one fixed bookmark per camera (single-sample static
evidence); diagnostic rows declare `occlusion_mode: "mixed"` (mesh depth-tested,
overlay markers/labels intentionally unoccluded = xray semantics), clean rows
`depth_tested` with no layers/labels/bindings.

## Honesty bounds (binding, carried into every receipt)

- The B4 PASS is a SOURCE-KINEMATIC FIDELITY statement ONLY. R1's refutation is
  RETAINED and not relabeled: primary anatomy places the radial head at ≈ 0 % ± 1 %
  of forearm length; the 7.9015 % target anchor preserves the source author's
  kinematic convention (7.5459 % → 7.9015 %, drift +0.356 points, mechanism
  identified) and carries NO primary-anatomical support.
- NOTHING is executed: no production radius supersession, no hand fit, no
  training-body change, no fit search, no moment-arm/utility computation. The old
  radius record and all failed alternatives (U-ANA rejected, H-BODY rejected, every
  fired falsifier) remain preserved. The section-4 AFTER column is a closed-form
  consequence map only.
- A diagnostic PASS does not close A03 or authorize mechanically qualified grasp.
- Writes are confined to this attempt's contribution directory. `E:/PythonChimera`
  is read-only for this attempt. No git write, no push, no network during probes.

## AMENDMENT A1 (recorded before any render run)

The camera `tick_interval` is `[0, 3]`, not `[0, 0]`: the canonical camera validator
requires a sampled trajectory's samples to cover its declared interval, and V3 is a
four-bookmark sampled trajectory (ticks 0..3). V1/V2 remain single fixed bookmarks
repeated at ticks 0 and 3 (identical values) — the static-evidence semantics are
unchanged. No measurement prediction, tolerance or falsifier is affected by this
filing-level correction; it was made before the visual probe executed.
