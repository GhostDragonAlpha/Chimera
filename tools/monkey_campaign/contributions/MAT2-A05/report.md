# REPORT — MAT2-A05 "First Mutation" implementation (Captain Decision 2)

Sergeant-implementer record. Attempt b4ad70883ac2480a928dcc828f33c65f,
arrival-b22e42ce0ecf4204acb2f99d0aecff97, 2026-09-28. Resume of a predecessor
attempt whose workspace never materialized (host restart); this workspace was
prepared by this instance per checkout_identity.json. No pushes, no PRs; the
lead publishes. Registry handoff (--request-pr) not attempted per brief.

## Identity

- Card MAT2-A05, slot 2, branch-2, base c525b82c7c3ce0128565424764293a3c85811ab3.
- Criteria sha256 34411771f7bd5dea2ec2cc4775d44b33df422e5454d283eae40676d1e3346544;
  done_when "The modeled grasp has sufficient explicit bodies, joints and geometry;
  sources and adaptations approved". Profile anatomy (visible_static).
- Governing ruling: CAPTAIN_DECISION_2_MUTATION.json
  sha256 3c34168ef28b00b1dc60c2362cc9d2d6ffb273a8c28a1663d9bff729596dd1d7
  (decision_id A05-DIGIT-MUTATION-20260928, verbatim + decision recorded in
  MUTATION_MANIFEST.md section (d)).

## What was delivered

1. PREREGISTRATION.md — written BEFORE any mutation artifact or capture frame:
   mutation plan (human elements taken / macaque constraints applied), the stated
   formula with arithmetic, 8 falsifiable predictions, honest-gap declarations.
2. The mutation (builder build_mutation.py -> macaque_hand_mutation.xml +
   mutation_structure.json + derivation_output.txt):
   - 19 explicit digit bodies (5 metacarpals + 14 phalanges; thumb 2-segment),
     20 explicit digit joints, wrist-anchored at the macaque hand body origin
     carrying the macaque wrist dof (ranges/axes from the osim wrist custom joint).
   - Every length = s x human source offset, s = MACAQUE_HAND_LENGTH /
     HUMAN_HAND_LENGTH = 0.08360625 / 0.155285 = 0.538404813 (recomputable from
     pins; identity mutant length == macaque hand length, diff 0.0).
   - Mass priors = 0.049 kg x human fraction (0.1589 kg base); anchor = macaque
     hand body values verbatim (allocation views declared non-additive).
   - Geometry = 19 vendor STLs (all sha256-pinned) at recorded uniform scale s +
     explicit scaled segment vectors; no fabricated mesh.
   - Muscle anchors ext_digitorum-P3/P2, flex_digit_profundus-P4 recorded in the
     macaque hand frame with nearest-mutant-body mapping at rest pose.
3. MUTATION_MANIFEST.md + mutation_manifest.json — itemized (a) human-derived
   base w/ vendor pins, (b) macaque constraints w/ osim/graph pins, (c) 8 declared
   deviations incl. the species-mixing disclosure, (d) Captain decision reference.
   This is the "adaptations approved" leg for review.
4. validate_mutation.py + validation_receipt.json — independent validator
   (re-derives from pins, does not import the builder): 37/37 checks PASS,
   exit 0.
5. Visible_static capture (capture_evidence.py -> capture/ + evidence/):
   6 rows (3 profile views x diagnostic/clean) on one hashed PNG sheet; pure-PIL
   orthographic projection of the mutant skeleton over the macaque hand.vtp
   envelope point cloud; 16-field cameras with computed unit quaternions and
   exact distances; validate_manifest structurally_valid=True (profile 'anatomy',
   kind visible_static, capture_kind image, view_count 6), profile read read-only
   from E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3.

## Commands executed and observed results

All with /c/Python314/python -B from the contribution directory:

1. `build_mutation.py` — exit 0. Pin verification OK for all 5 inputs (sha256
   echoed in derivation_output.txt). Emits XML (well-formed, ET-verified) +
   JSON (sha256 8d51b55180965d413ce6bd461dd98daa37f455c3e2af3353c78a403fc3c8eb83).
2. `validate_mutation.py` — final run: 37/37 PASS, exit 0 (validation_receipt.json).
   - FIRST RUN: 35/37 with 2 FAILs — both validator-side defects, preserved here
     honestly: (i) V1-phalanx-count observed 12 — the name filter `'ph' in b`
     misses proximal_thumb/distal_thumb; (ii) V1-chain-connectivity observed 19
     bodies "unconnected" — the walk did not treat macaque_hand_anchor as
     terminal. Structure values were unaffected; validator fixed, re-run 37/37.
3. `make_manifest_json.py` — exit 0; mutation_manifest.json
   sha256 eb5c3ebeee7bf13f1ca2966eb8353cb597f3d24242ab99c59225b56417876a44.
4. `capture_evidence.py` — final run: structurally_valid=True, capture
   sha256 d8bb22f9ada9b5c5e20dbd5f6f316f6fd45f5f2bdeb5f264370cfd4619c86514.
   - INTERMEDIATE DEFECTS (caught and fixed before finalizing; preserved here):
     (a) validate_manifest fired visibility_required_subject_ids_invalid (clean
     rows had empty required ids — fixed to M01-style aggregate ids);
     (b) fired capture_pair_camera_mismatch (secondary_cameras present only on
     the diagnostic camera — added to the clean pair);
     (c) a quaternion implementation bug (conjugate negating the scalar part,
     plus operand order) collapsed the rendered skeleton to a line — fixed to
     v' = q v q* with vector-only conjugation, and a camera self-test assertion
     added so a broken orientation cannot render silently;
     (d) close-up camera framing put the anchor above its viewport and rows were
     not clipped, bleeding content across rows — fixed by reframing (span 0.06,
     target y -0.026) and rendering each row on its own canvas before pasting;
     (e) anchor label drawn at x-coordinate instead of y — fixed.
   - After fixes every row was visually inspected (diagnostic rows: labels,
     layers, axes, panels present and legible; clean rows: identical geometry,
     no diagnostics; state hash strip 8d51b55180965d41 on every row matches
     mutation_structure.json).

## Per-digit derived structure (summary; full table in MUTATION_MANIFEST.md)

| digit | bodies (chain) | chain length m | joints |
|---|---|---|---|
| thumb | firstmc -> proximal_thumb -> distal_thumb | 0.055887 | cmc_abduction, cmc_flexion, mp_flexion, ip_flexion |
| 2 | secondmc -> proxph2 -> midph2 -> distph2 | 0.081837 | mcp2_flexion+abduction, pm2_flexion, md2_flexion |
| 3 | thirdmc -> proxph3 -> midph3 -> distph3 | 0.083606 | mcp3_flexion+abduction, pm3_flexion, md3_flexion |
| 4 | fourthmc -> proxph4 -> midph4 -> distph4 | 0.078262 | mcp4_flexion+abduction, pm4_flexion, md4_flexion |
| 5 | fifthmc -> proxph5 -> midph5 -> distph5 | 0.070343 | mcp5_flexion+abduction, pm5_flexion, md5_flexion |

Metacarpals 2-5 welded to the palm anchor (human base topology, myohand lines
286/409/509/607); thumb CMC joints carried on firstmc. Fingertip Y positions all
inside the hand.vtp Y span (preregistered falsifier PASS); radial X/Z overshoot
(thumb +0.0307 X vs envelope max 0.0207, d2/d3 +0.0105 Z vs 0.0046, d5 -0.0149 X
vs -0.0124) recorded as declared deviation, visible in the capture.

## Artifact hashes (final)

| artifact | sha256 |
|---|---|
| PREREGISTRATION.md | e79b4a7853916629d54a22904d4b1dcb92984556f37122b44211ee15b19ae5f9 |
| build_mutation.py | 80bbf6b99083e6a6456f42e14fe4f428960351199e82dc60efe41df92ffeb3db |
| macaque_hand_mutation.xml | 9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf |
| mutation_structure.json | 8d51b55180965d413ce6bd461dd98daa37f455c3e2af3353c78a403fc3c8eb83 |
| derivation_output.txt | e10ad1c055fc5bee9206862213cf0559b1c97ca730a9845e642b06a9194839d8 |
| validate_mutation.py | 333fbb60dbfbd8baf99146efbb91fc630b82851ec2f41f5eca927c156bc798bf |
| validation_receipt.json | 1781aa6bfe7069183c225d54be21f8788c460b24b9abeca1aaac25ff0fa6c3ff |
| make_manifest_json.py | 65c5b010f25da244ecb5b975f519834a88a42dd038c826b4a4a349e0268cbab8 |
| mutation_manifest.json | eb5c3ebeee7bf13f1ca2966eb8353cb597f3d24242ab99c59225b56417876a44 |
| MUTATION_MANIFEST.md | eaf0fe535ffcfbfb81e38567c28d2594d092dc96f0d74379cfe86d9b8e53f92b |
| capture/capture_mat2_a05_mutation_20260928.png | d8bb22f9ada9b5c5e20dbd5f6f316f6fd45f5f2bdeb5f264370cfd4619c86514 |
| evidence/cameras.json | 0a22e3ab98c65d12f84d0ff49a694d4331ecfa2798dccc44c47077301a6b467b |
| evidence/capture_manifest.json | 5bb60c3518eb4dedb5327c9d8836bfed1f6ad7b829d2da48e9ddaea1b3c20ee5 |
| evidence/capture_context.json | 287781a61bc3383349a92fd7621cfc7024819316eed6f4e2b44729c4264d66e6 |
| evidence/validation_receipt.json | 9780bd65a69b71c6ef013925ff30d6d9017d874a1165e9b5833851a09dbd20ad |

## Honest limitations

- Species mixing is inherent to the Captain's ruling: human base topology/shapes,
  macaque frame numbers. This is a training-oriented hybrid, not species-true
  anatomy; every node carries the hybrid species label.
- No macaque per-phalanx proportions, per-digit ROM or per-phalanx masses exist
  in-repo; uniform scale, human digit ranges and proportional mass priors are the
  declared substitutes (manifest deviations 2, 5, 7).
- Radial envelope mismatch (deviation 4): a uniform scale cannot match the
  macaque hand envelope in X/Z while matching Y; per-axis correction needs
  macaque per-digit data (Captain-level acquisition).
- The capture is a 2D orthographic skeleton/envelope view (no 3D renderer, no
  mesh surfaces, no GPU); validate_manifest is structural only — independent
  pixel/visual review remains mandatory and is not claimed here.
- No dynamic simulation, no MuJoCo load test (MuJoCo not exercised in this
  environment); the MJCF is a well-formed structure record whose numbers are
  validator-checked against the pins, not a runtime-verified simulation.
- The vendor clone is unpinned upstream MyoHub/myo_sim; rev 33f3ded9... +
  per-file sha256 recorded at use time (E:/PythonChimera is read-only for this
  worker; re-pinning the vendor is outside attempt scope).
