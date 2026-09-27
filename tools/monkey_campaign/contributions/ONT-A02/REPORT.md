# ONT-A02 — radioulnar definition, independent evidence, B4 result, before/after radius mapping

Task `ONT-A02` (planning item `A02`); attempt `b4a2b12b8c854e55bc400c64a502c85c`;
arrival `arrival-e20cc96d4f8a4a1894424fcae60e422a`; criteria SHA-256
`ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1`.
Attempt checkout base/head `c525b82c7c3ce0128565424764293a3c85811ab3`, branch
`branch-5` (isolated sparse checkout; all writes inside
`tools/monkey_campaign/contributions/ONT-A02/`).

## Verdict

**All four `done_when` items are presented and hash-bound.** The done_when is
conjunctive ("Radioulnar definition, independent evidence, B4 result and
before/after radius mapping are presented") and this attempt presents each with
an independent, pin-bound re-derivation rather than copying receipt floats:

1. **Radioulnar definition** — the source radioulnar offset is re-measured from
   the pinned `chimanoid.xml` rest pose: `|(0.0004, -0.011503, 0.019999)| m =
   23.074640 mm` (ulna frame), forearm `|hand_r - ulna| = 305.7922 mm`, radius
   edge `|hand_r - radius| = 292.0294 mm`, authored fraction `7.545855 %`,
   axial/lateral decomposition `14.324 / 18.088 mm`, obliquity `51.629 deg`
   (P1). Owner discrimination (P2) separates it from wrong-owner readings
   (humerus-origin, ulna->hand, radius->hand, local-frame variants: none match).
   R1's refutation is RETAINED: the offset is a kinematic joint-frame offset
   with NO primary-anatomical support as a radial-head placement.
2. **Independent evidence** — this attempt's own code re-derives every number
   from byte-pinned inputs (`reference/EXTRACTION.json`, 11 files, sha256-bound,
   extracted read-only from git pins `c3255f74`/`d02af013`/`f1023853`), plus the
   three pinned independent historical audits (O1, R1, I7 — different agents and
   lanes) are cited by exact pin. Method identity is asserted empirically: the
   re-implemented DERIVATION 5.1 ONB law reproduces the packet's own fitted site
   globals to `5.6e-17 m` (right) / `1.7e-18 m` (left) before any verdict.
3. **B4 result** — the receipted I7 isolated U-STR B4 diagnostic verdicts are
   presented verbatim (12/12 side-test verdicts + T6 process PASS on the
   existing T1-T6 protocol, tolerances unchanged) with their bound: a
   SOURCE-KINEMATIC FIDELITY statement only. The closure mechanism is re-derived:
   gap `|radius.P - ulna.P_d| = 5.115804 mm >> JOINT_EPS 1e-9`, so with ulna
   declared the shipped radius record is machine-refused
   (`shared_joint_separation`) and the re-anchor is forced, not chosen.
4. **Before/after radius mapping** — reconstructed in closed form from the
   declared candidate + packet records, both sides: uniform scale
   `0.22170679566544982 -> 0.20418868001006546` (exact float reproduction),
   change `-7.901478889180636 %`, `det(L) = s^3`, rigid part G unchanged
   (`max|dG| 2.22e-16` right / `6.66e-16` left, byte-equal to receipt 08), all
   16+16 site displacement deltas reproduced to `<= 1e-12 m` (worst
   `BICshort-P6 4.9510 mm` right, `BIClong_l-P9 4.9484 mm` left), landmark
   oracles exact (`L(A)=P_new`, `L(src_D-A)=wrist_R` to `<= 8.7e-19 m`),
   round-trip `L^-1 L = I <= 1.1e-16`, mirror: `P_new`/`P_d`/`span`/`s` exactly
   0 diff. **Status: CLOSED-FORM DIAGNOSTIC CONSEQUENCE ONLY — UNAUTHORIZED and
   UNEXECUTED as a production supersession.**

The A02-specific coverage consequence (C16) is re-derived from XML tendon-path
ownership: baseline complete `2/18` (BRD pair), diagnostic-ulna-only `4`
(adds PT pair — the newly-defined chains), plus-hand context `14`; 10
hand-blocked (8 fully + ECU pair double-blocked), 4 thorax-blocked (BIC);
`elbow_flexion(_l)` owners `ulna`/`ulna_l` — all matching pinned receipt 10.

## Honest discrepancy (falsifier FA fired, recorded — not tuned)

The frozen P3 prediction claimed mirror agreement `<= 1e-9 m` for ALL vectors.
The translation `t_new` is NOT mirror-exact: observed asymmetry `4.20e-05 m`,
byte-identical to the pinned receipt 08's own asymmetry (`<= 1e-12` agreement)
— the source authoring itself is asymmetric (the receipt's radius_l t differs
from the x-mirrored radius t by the same amount; I7 recorded the 5e-5 m source
ulna asymmetry). Per PREREGISTRATION FA the prediction is RECORDED AS FIRED
(`P3:mirror_t_overbroad_prediction` in `fired_falsifiers`), the corrected
structural reading (asymmetry reproduces the receipt exactly; bounded `<= 1e-4`)
is presented alongside, and the outcome is honestly labeled
`DISCREPANCY_RECORDED`. No tolerance was moved post hoc. Every source-evidence
reproduction is within its frozen tolerance.

Two additional reconciliation findings from development (both resolved without
touching any receipt): (a) the pinned after-map construction consumes the RADIUS
EDGE'S OWN roll source landmark (not the ulna candidate's TRIlat-P5, which
belongs to the ulna edge declaration) — my first implementation used the wrong
roll point, failed `G_unchanged`/`t_new`/packet-reproduction checks, and was
corrected to the receipted construction; (b) receipt 08's `fractions` block was
computed from 9-decimal truncated constants (`0.023074640 m`,
`0.064744899 m`), so its printed target fraction differs from this attempt's
full-precision value by `4.75e-8` points; the printed value is exactly
reproducible from those truncated inputs (both readings recorded in
`numerical_receipt.json`).

## Visual evidence (anatomy profile)

`evidence/capture_sheet.png` (1920x1080, deterministic CPU z-buffer software
raster + matplotlib Agg compose; NOT native engine frames — honesty label in
`capture_manifest.json` and `visual_provenance.json`). Three declared views,
each with diagnostic+clean pairs (12 panels):

- V1 whole-creature overview (target frame, m): pack mesh (birth, sha
  `550a5b3e...`), frame triad, boxed U-STR forearm region, elbow_R/wrist_R,
  BEFORE/AFTER radius anchors.
- V2 local attachment close-up (target frame, mm): elbow->wrist edge, BEFORE
  (`elbow_R`) vs AFTER (`ulna.P_d`) anchors with the `5.1158 mm >> JOINT_EPS`
  gap, all 16 radius site globals before (filled) / after (open), PT tendon
  course before (solid) / after (dashed) — the newly-defined chain.
- V3 orthogonal side and oblique (source rest frame, mm): ulna.stl (authored
  scale `1,1.2,1`), 4 bookmarks (anterior/posterior/left-lateral
  oblique/superior), the `23.0746 mm, 51.63 deg` radius body-origin offset
  vector, volar/dorsal/proximal/right axes.

Falsifier guards: cameras framed from the PROJECTED BOUNDS of each view's
declared subject point set + uniform 8 % margin (`fit_camera`) with a
generation-time `assert_in_bounds` guard; the state snapshot sha256 is recorded
before/after rendering and asserted equal (`state_hash_preserved_under_view_
toggles: true`). The manifest passes the canonical campaign validator
(`visual_capture.validate_manifest` -> `structurally_valid: true`, 6 view rows)
and `visual_gate.verify` (the reviewer's gate) inside
`evidence/qualification_receipt.json`. The actual pixels were inspected this
attempt (Read of the sheet): subjects unclipped, labels legible/unambiguous.

## Checks actually run (commands, counts, runtimes)

| # | command | result |
|---|---|---|
| 1 | `python -B ota02_radioulnar.py` | outcome `DISCREPANCY_RECORDED`; fired `[P3:mirror_t_overbroad_prediction]` only; P1/P2 source verdict True (23.07464 mm / 7.545855 % / 51.629 deg); P3-P5 right+left True (s_new `0.20418868001006546` exact, change `-7.901478889181 %`, gap `5.115804 mm`); P6 coverage `{baseline: 2, diagnostic_ulna_only: 4, plus_hand: 14}`, newly-defined `PT_tendon, PT_l_tendon`; P7 `RETAINED_FIRED` |
| 2 | `python -B ota02_render_views.py` (x4 during development + determinism pair) | `structurally_valid: True, views: 6`; state hash preserved; PNG sha256 identical across two runs (`88f94dc3c48ddc8505a546cb7109db9db84600f40008de882359887d9ad24b62`) |
| 3 | `python -B -m unittest test_ota02_radioulnar` | **26 tests, 0 failures/errors, 0.594 s** (includes failing-first demos: clipped-subject guard raises; tampered state hash detected; tampered after-scale rejected; wrong owners rejected) |
| 4 | `python -B -m unittest test_ota01_roll_sign` (prior-task suite, A01 attempt workspace, CPU-only) | **26 tests, OK, 0.111 s** |
| 5 | `python -B make_qualification_receipt.py` | `visual_gate.verify: True, views: 6`; wrote `evidence/qualification_receipt.json` + `evidence/independent_review_receipt.json` |
| 6 | inbox re-read `python -B E:/PythonChimera/tools/monkey_campaign/kanban_cli.py inbox --task ONT-A02` | `OPEN`, no messages, no PRs, no winner (read at attempt start) |

All invocations CPU-only, `python -B` (no bytecode writes), no GPU/network/
native build; every run well inside the 120 s / 16 MiB budgets.

## Identities

- Inputs: `reference/EXTRACTION.json` binds 11 extracted files with bytes +
  sha256 to git pins: `chimanoid.xml` `7caa32c6...` (f1023853),
  `packet/actual_monkey_fit.json` `7b5d6345...` (f1023853), I7 receipts 00/07/
  08/10 (f1023853), B4 known-good `3f6a5a7a...` (f1023853), O1 source-split +
  combine-sign (c3255f74), R1 arithmetic `3a10c7f9...` (d02af013),
  `mesh_target_o1.py` `268f139a...` (c3255f74). Worktree inputs hash-asserted at
  run time: `monkey_birth.bin 550a5b3e...`, `monkey_joints.bin 74b3ab04...`
  (A01 EXPECT_SHA pins), `ulna.stl` hashed into `state_snapshot.json`.
- Historical evidence: O1 (c3255f74), R1 (d02af013, refutation RETAINED),
  I7 (f1023853, B4 PASS presented as source-kinematic fidelity only).
- Dependency: ONT-A01 is live-DONE (PR 176, head `6f90c288ce93f236c820a2d665b0
  418c11d7024a`, merge `f301e9b355e485ca08a432defe25450e191eb5eb`); its evidence
  stays bound to A01 and does not substitute for A02 evidence.

## Bounds (what this attempt does NOT claim)

No production radius supersession (authorized or executed), no anatomical
support claim for the re-anchor, no A03 closure, no grasp/mechanical
qualification, no native runtime/device evidence, no training-body change, no
moment-arm/tendon-length computation, and no operator acceptance. The B4 PASS
is presented strictly within I7's memo bounds. The frozen session-5 baseline and
all historical records are untouched (read-only extraction only).

## Submission state

Writes stopped after this report; the attempt is submitted for independent
review through the canonical `worker_start.py --request-pr` handoff with
hash-bound artifacts (publication branch `review/ONT-A02` is lead-serialized;
no worker push was made and no GitHub PR is claimed by this attempt).
