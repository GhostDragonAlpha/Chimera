# ONT-A05 report — acquired/authorable hand-digit structure: decision candidate

Card `ONT-A05` (A05, kind decision+implementation, profile `anatomy`,
kind visible_static), attempt `1a7c477561f647a29f4e4775bb933547`, agent
`arrival-b249a6084f3c4525afde7644b08ead4f`, criteria
`a19ba471bfde65e094f63ef8f3e6d1edc4d55390f5901e1e82f3d6883d18823d`.

## 1. The decision, on evidence

done_when: "The modeled grasp has sufficient explicit bodies, joints and
geometry; sources and adaptations approved". A04 (merged, PR #177) proved the
source hand has 27 identity-pinned bones but ONE rigid body with a 3-DOF
wrist, and the target runtime has ZERO digital articulation — the modeled
grasp cannot map digits.

**The acquisition candidate is identified and identity-proven**: the vendored
MyoSuite `myo_sim` v0.1.0 hand (Apache-2.0) IS the pinned source-hand asset —
all 27 unprefixed vendor STLs (`E:/PythonChimera/vendor/myo_sim/meshes/
<bone>.stl`) hash-match A04's per-bone identity pins 27/27 (check C2) — and
its pinned `myohand_body.xml` carries exactly the missing structure: **19
explicit digit bodies and 20 explicit range-carrying digit joints** (C3).
A complete name-level correspondence covers **all 14 phalanges** A04 recorded
as NOT covered (C4). The exact adaptation delta — graft the vendor digit tree
under the pinned chimanoid hand_r's existing 3-DOF wrist, per-joint
type/pos/axis/range values VERBATIM from the pinned XML — is recorded as a
PROPOSAL manifest in `evidence/state_snapshot.json.adaptation_delta` (C5),
with scale, target-runtime binding, origin promotion and palm-sign claims
explicitly EXCLUDED. The approval conjunct of done_when ("adaptations
approved") is the lead/operator gate and is recorded UNAPPROVED (C6); this
candidate cannot grant it.

## 2. Reconciliation (records reused; nothing re-implemented)

- A04 winner head `020c0a5c216a4182d0bed9c4ade59cb0beb585ad` (PR #177 merged,
  merge `f301e9b3`): identity table, chimanoid XML blob `7caa32c6…`,
  s1/s2/s3 receipts, target measures, A04's numerical receipt — recovered
  read-only into `reference/a04_winner/`.
- Vendor structure files: `hand/myohand.xml`, `hand/assets/myohand_body.xml`,
  LICENSE, VERSION — byte-copied read-only into `reference/vendor_myo_sim/`;
  vendor STLs hashed IN PLACE (never modified, never copied).
- `reference/EXTRACTION.json` records all 19 recovered files + hashes; the
  probe re-asserts every hash at import (PIN DRIFT guard).
- P02 separation preserved: myo_sim stays KEPT_SEPARATE from the
  runtime/training bodies; this candidate claims NO runtime, training or
  production role for anything it measured.

## 3. What ran (exact commands, bounded)

```
python -B tools/monkey_campaign/contributions/ONT-A05/extract_reference.py
python -B tools/monkey_campaign/contributions/ONT-A05/a05_hand_structure_probe.py
python -B tools/monkey_campaign/contributions/ONT-A05/capture_build.py
python -B -m unittest test_ont_a05 -v
```

CPU-only (numpy + Pillow + the A04 winner's pinned z-buffer rasterizer);
no GPU, no engine, no network; vendor files read-only; all writes inside
this attempt checkout; each invocation bounded (<120 s probe/tests,
<200 s capture).

## 4. Results

### Probe — 6/6 checks PASS (byte-identical on rerun)

- `C1_source_hand_structure` — chimanoid hand_r: 1 body, 3 hinges
  (`wrist_dev_r`, `wrist_flex_r`, `wrist_3_r`), 27 mesh geoms == the 27
  pinned bones, 5 frozen sites.
- `C2_vendor_mesh_identity_27_27` — 27/27 unprefixed vendor STLs hash-match
  A04's identity pins; zero missing, zero mismatched. THE IDENTITY RESULT.
- `C3_vendor_digit_structure` — 19 digit bodies, 20 digit joints
  (cmc/mp/ip + mcp/pm/md per finger), every range explicit; Apache-2.0
  license + copyright header verified.
- `C4_correspondence_map` — 19 name-level entries; all 14 A04-uncovered
  phalanges covered; explicitly NOT a scale or runtime binding.
- `C5_adaptation_delta_recorded` — 19 bodies + 20 joints verbatim under the
  carried wrist; exclusions recorded; delta manifest hashed.
- `C6_approval_status_honest` — adaptation UNAPPROVED (the named remaining
  gate); target palm sign UNRESOLVED (inherited); scale UNDECIDED
  (inherited); runtime binding NONE.

### Capture — GATE-VALID

- `evidence/capture_a05.png` = `64529f881c428e81…` (106,569 bytes;
  3 views x diagnostic+clean pairs; BITEXACT on rerun, verified with cmp).
- Rasterizer = the MERGED A04 winner's pinned z-buffer orthographic code
  (`reference/a04_winner/a04_capture_build.py`), imported read-only; the
  A04 capture-truth guard re-asserted at build time (assembled placement,
  NOT origin-collapsed: span asserted > 0.05 m; anchor extent in the A04
  band).
- `evidence/capture_manifest.json` = chimera.visual_capture_manifest.v1,
  profile `anatomy`, 6 rows, state-bound to `state_snapshot.json`
  (`7944df30…`); `visual_capture.validate_manifest` AND
  `visual_gate.verify` (including the receipt's camera/visual entries)
  both `structurally_valid: true` (visual_acceptance false by law).
- Diagnostic layers (task-owned subset): frame axes (L5) at the A04 origin
  pin, selected-bone centroids (L2), the 5 tendon sites (L4) with course
  lines to their cited bones (L3), stable IDs (L6). Clean panels carry
  pure geometry only.

### Tests — 10/10 OK in 0.056 s

Pinned hashes, A04 winner binding, source-hand structure, 27/27 vendor
identity, 19/20 vendor digit structure, correspondence coverage, delta
exclusions + honest approval status, all-six-checks green, manifest
structure + clean-view refusal.

## 5. Honest deviations (recorded, never smoothed)

1. `C5` (FIRED, prereg REVISION A): the vendor digit body count was frozen
   as 15; the actual pinned count is 19 (5 rays: 16 finger segments +
   firstmc/proximal_thumb/distal_thumb). The prereg's own body LIST already
   named all 19; only the arithmetic was wrong. The deviation is preserved
   in `numerical_receipt.prediction_deviations`; the expectation was
   corrected per the prereg's revision trail before the candidate commit.

## 6. Artifact identities

| artifact | sha256 (16) |
|---|---|
| evidence/state_snapshot.json | `7944df30c79e54e2` |
| evidence/capture_a05.png | `64529f881c428e81` |
| evidence/numerical_receipt.json | `4c3a018bf6bd25b2` |
| evidence/runtime_receipt.json | `edc2401399b4c4be` |
| evidence/capture_manifest.json | `15539eb3e2ecd36c` |
| evidence/capture_receipt.json | (hashed in the publication request) |
| reference/EXTRACTION.json | `ad3e4bdd9cdf4039` |
| qualification_receipt.json | (hashed in the publication request) |

## 7. Remaining gates (not claimed by this candidate)

- **"sources and adaptations approved"** — the lead/operator must approve
  the C5 adaptation delta proposal (or choose an alternative); this is the
  explicit remaining conjunct of done_when and this candidate cannot grant
  it.
- Independent worker review of this exact head; lead ACCEPTED pinning
  `head_sha`; GitHub merge via `review/ONT-A05` + `accept-merge`.
- Any subsequent implementation that fits the adapted digit structure into
  the target runtime is downstream work with its own gates (A06 depends on
  this card).

## 8. Failures encountered and fixed during development

(provenance; all resolved, final state green)
- `cam_record` returns `(dict, basis)` — unpacked; `raster` returns
  `(img, zbuf, mask)` — unpacked; `load_stl` lives in the A04 probe module,
  not the capture module — imported as `A04P`.
- Site anchors come from A04's frozen `SITES` table (probe module), not the
  s2 JSON (which stores course-class records, not anchors).
- The probe's pin assertion needed the extraction manifest's
  `<origin>:<repo path>` key mapping resolved to the on-disk
  `reference/<origin>/<basename>` layout (vendor files keep their relative
  path under `vendor_myo_sim/`).
- The qualification receipt must exist under `evidence/` before the capture
  builder's `visual_gate.verify` runs (the gate checks the receipt's
  camera/visual entries in-process).
