# ONT-A04 — hand assembly identity and palm orientation: report

Attempt `86b87bfe23b14059ac8ed516104340bf`, agent `arrival-32436e70ed1e4866a25a29940db1789c`,
card criteria `bf8583ae76c4930f726c4c71861ab9219cdac65eb3913cb29ab6131671505570`,
scope `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Preregistration frozen before the first probe run of this attempt
(`PREREGISTRATION.md`; it is the first evidence-bearing file of the attempt and
predates every artifact in `evidence/`).

**Capture correction (this head).** Worker review `8837d083c2544b2784178ea462bd9f87`
returned CHANGES_REQUIRED on PR #172 with three capture findings (collapsed
source placement, locator-rect convention, close-up subject overreach). The
correction was applied by attempt `d9e5561a0c7b4c0881faf8a213e475b2`
(`arrival-685b1adcb79c4f0f933db12466db1fc7`), CPU-only, card-scoped: the capture
builder, manifest, PNG, capture receipt and this report are refreshed; the
numerical leg (`evidence/numerical_receipt.json` `e3864b16…`,
`evidence/state_snapshot.json` `33d3219c…`) is byte-identical to the reviewed
`7df75f41` pins — a capture correction only. Details in item 6 below and in
`qualification_receipt.json` → `capture_correction`.

## DONE_WHEN (the only clause qualified)

"Source and target assembly correspondence is evidenced, including palm sign and
geometry coverage" — calculation contracts C01 (frames/units/source correspondence)
and C16 (identity leg only). Verification profile `anatomy` (kind `visible_static`,
numerical evidence required). Dependency ONT-P02: merged and lead-verified
(`review/ONT-P02`, merge commit `8c7ed8c2`).

## Reconcile: what EXISTED (reused, hashes asserted, nothing re-implemented)

- **ONT-P02 monkey lineage map** (merged): Chimanoid `SOURCE_OF` the
  forearm/paddle assets; forearm/paddle assets `KEPT_SEPARATE` from the
  runtime/training bodies; myo_sim vendor `KEPT_SEPARATE`. This card claims no
  runtime, training or production role for anything it measured.
- **HAND_SOURCE_EVIDENCE** (source identity + palm normal, `70c9ff41` on
  `forearm-package-20260924`; on-disk under `forearm_package/audits/`):
  receipts re-pinned byte-exact from the git blob into `reference/`
  (s1_inventory, s2_identity, s2b_cmc_diagnosis, s3_palm_normal,
  identity_table, commands, prereg).
- **HAND_TARGET_VIEWS** (`57beb8b2`): the ±T_R opposed-face labeling instrument
  (A/B) for the target band + `LABELING_CARD.md` + C2/B1 measure receipts.
- **I6 ANATOMICAL_DECISION_TABLE + architect addendum**: H-LEN/H-ASP unresolved,
  H-BODY rejected circular; hand scale blocked on same-assembly; production
  mapping not authorized.

## What was MISSING and is BUILT here (task-owned only)

1. **One unambiguous frame chain with independently checked transforms (C01)** —
   `a04_correspondence_probe.py` check C2: hand_r world origin re-derived from the
   pinned XML chain = `(-0.0731, 0.532647, 0.202699)` m (R2-A4 pin); all chain
   quats identity (0 non-identity in 100+ walked bodies); `x_world = R x_local + t`
   round-trips every anchor and site with max residual < 1e-12 m; det(R) = +1;
   assembled anchor record reproduces (155.285 mm vs authored 155.29; rays
   66.99/96.42/100.17/89.10/78.61 vs 67.0/96.4/100.2/89.1/78.6 mm).
2. **Independent palm-SIGN re-derivation** — frozen pisiform-signed palm-plate
   method re-implemented and re-run on pinned bytes: `n_palm =
   (+0.128427, -0.168691, -0.977266)` hand_r local (12.2404° from −ẑ; plate rms
   5.8819 mm; pisiform sign-rule dot −6.9659 mm) — exact reproduction of the s3
   receipt to 1e-9; compartment split 5/5 clean (FCR +5.2869, FCU +4.3611,
   ECRL −3.2637, ECRB −9.0956, ECU −2.6272 mm); XML z-mirror exact (max |Δ| = 0).
3. **Target geometry measures re-derived** — band 111.26/111.35 mm (r<25/40 mm),
   far end 47.07 × 18.04 mm, region one component at 8-mm occupancy (168 voxels;
   C2's [165] differs only by grid-origin convention — recorded), L/R anchor
   x-mirrors exact (max |Δ| = 0.0).
4. **Correspondence + coverage inventory (C16 identity leg)** — 27 source bone
   IDs + 5 port IDs + target band + 2 anchors, owner map per port; 13
   carpals/metacarpals region-covered (region homology ONLY, scale UNDECIDED);
   14 phalanges NOT covered as identified digit anatomy (no digit joints, no
   persistent grooves; distal lobation at 2-mm scale recorded per C2 and visible
   in the render — none of it resolves into per-digit correspondence); scale
   alternatives recorded UNRESOLVED (H-LEN s=0.716, H-ASP) and REJECTED-circular
   (H-BODY); "orientation alone does not set scale" enforced — no scale promoted.
5. **Anatomy-profile camera-pinned capture** — `capture_build.py`: six-panel
   contact sheet (`evidence/capture_a04.png`, 700×3628 px, byte-identical on
   rerun), 3 profile views × diagnostic/clean pairs, source and target inspected
   SEPARATELY in every view cell, all six diagnostic layers present, all 16
   camera fields per camera (primary + fully-declared secondary cameras),
   `chimera.visual_capture_manifest.v1` validated in-process with the campaign's
   `visual_capture.validate_manifest` against the exact card profile
   (`structurally_valid: true`, view toggles share one state hash).
6. **Capture-truth guards** (correction for review `8837d083` on PR #172) —
   every source bone is placed at `tris + hand_r origin + per-bone XML anchor`
   (the first commit had dropped the anchor term and superimposed all 27 bones
   at the hand_r origin); the build now ASSERTS that each declared camera
   targets the vertex mean of its framed subject, that the declared
   orthographic span equals the auto-frame span over the PLACED geometry
   (overview span 0.29511 m vs 0.20515 m over the collapsed set — guard), that
   the collapsed guard actually differs, and that every declared subject vertex
   projects inside its declared frame (A01-lesson bounds, per-camera margins
   recorded in `evidence/capture_receipt.json` → `capture_truth`). The
   `artifact_locator` rects follow the documented `[left, top, width, height]`
   upper-left convention, and the close-up view scopes its region subjects to
   what it frames (`src/assembly/27_bones/carpal_row`,
   `tgt/envelope/distal_band/proximal_segment`). `TestCaptureTruth` (5 tests)
   regresses all three findings failing-first against the pre-fix artifacts.

## Verification actually executed (exact commands)

```
python -B a04_correspondence_probe.py     # all_green=True, 2 recorded deviations
python -B capture_build.py                # structurally_valid=True, fired=0
python -B -m unittest test_ont_a04        # Ran 19 tests ... OK  (CPU-only)
# determinism: both builders re-run; numerical_receipt/state_snapshot byte-identical
# to the reviewed 7df75f41 pins (e3864b16/33d3219c); capture artifacts byte-identical rerun
```

## Recorded deviations (FIRED, preserved — never smoothed)

1. **C4 site-to-cited-bone metric**: s2's "surface" numbers reproduce under the
   nearest-VERTEX metric (FCU→pisiform exact to 1e-12; the other four within
   0.11 mm); exact point-to-surface puts the four anchor sites at 0.001–0.011 mm.
   Both metrics are inside the governing R2-A3 anchor class (3.5 mm); check ok.
2. **C5 far-end c1 extent**: measured 18.04 mm vs C2's printed 18.1 mm (Δ 0.061 mm
   > the 0.05 mm recording tolerance; within the 0.1 mm print precision; ONB
   construction float detail). Recorded, check ok at print precision.

## Honest boundaries / remaining gates (named, not claimed)

- **Target palm sign UNRESOLVED**: the A/B face instrument exists and is rendered
  (honest lettering: labels FACES, not anatomy), but the HUMAN labeling verdict is
  not recorded anywhere; no model or worker answer substitutes for it (card
  falsifier F-D).
- **Scale/assembly UNDECIDED**: H-LEN/H-ASP unresolved, H-BODY circular — same-assembly
  proportion mismatch (1.72 vs 0.49–0.51) recorded, never bridged.
- **No runtime/native claim**: static pinned-geometry inspection only; the
  runtime render body and training body are P02-kept-separate lineages.
- **C16 reach/ROM leg** is downstream grasp-skill scope; not claimed here.
- **Independent review** of this candidate is a remaining gate (receipt's
  `independent_review` entry is null by the U01 precedent; set at ACCEPTED).
- Left STL identity remains untestable on disk (vendor carries no `_l` files) —
  preserved limitation of the source receipt.

## Falsifier states (all frozen bars)

| falsifier | state |
|---|---|
| F-A identity (hashes/extents) | not fired (27/27 STL hashes, XML pin, extents reproduced) |
| F-B palm sign (re-derivation/split) | not fired (1e-9 agreement, 5/5 clean) |
| F-C frame chain (round-trip/handedness) | not fired (< 1e-12 m, det +1, quats identity) |
| F-D coverage honesty (digits/scale/verdict) | not fired (all named unresolved, none claimed) |
| F-E capture (manifest/clean/masks/determinism) | not fired (gate true, masks nonempty, byte-identical rerun) |

## Inputs (read-only; all writes inside this attempt workspace)

- git blob `forearm-package-20260924:forearm_package/baseline_snapshot/source_xml/chimanoid.xml`
  = `7caa32c6e31e319876ea21625b662c5c00e736038f542b38ce6b0cb81aadc8a5` (the drifted
  worktree's `.tmp/chimanoid.xml` `675e00d0…` was NOT used);
- `E:/PythonChimera/vendor/myo_sim/meshes/<bone>.stl` (27 files, per-bone sha256
  asserted against the s1 pins; vendor = MyoHub/myo_sim v0.1.0 @ `33f3ded9…`,
  Apache-2.0);
- `E:/PythonChimera/Saved/meshes/monkey_birth.bin` `550a5b3e…` and
  `monkey_joints.bin` `74b3ab04…` (both byte-equal to the branch-pinned blobs).
- CPU-only: no GPU/OpenGL/Vulkan/CUDA; matplotlib Agg before pyplot import.
