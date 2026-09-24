# A5_containment — receipts (exact commands + key output)

All commands run from `E:/PythonChimera/forearm_package/audits/A5_containment` with
`PYTHONDONTWRITEBYTECODE=1`, python 3.14 + NumPy. No writes outside this audit dir;
no git write commands; no network.

## 0. Brief copy
```
mkdir -p .../audits/A5_containment/{scripts,receipts,work}
# brief written verbatim to brief.md (Write tool)
```

## 1. Baseline integrity (criterion 6)
```
git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
# output: (empty)   EXIT:0
git -C /e/PythonChimera log --oneline -1 -- forearm_package/baseline_snapshot
# 0ad24b02 forearm-package: reopen campaign — durable session-5 baseline snapshot (44 files, ...)
sha256sum baseline_snapshot/inputs/monkey_birth.bin baseline_snapshot/inputs/monkey_joints.bin
# 550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c  monkey_birth.bin
# 74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662  monkey_joints.bin
# == recorded meta in admission_actual_monkey.json (target_mesh_sha256 / target_pack_sha256)
```

## 2. Module copies (verbatim, read-only use)
```
cp baseline_snapshot/code/target_envelope.py work/ ; cp baseline_snapshot/code/mesh_target.py work/ ; cp baseline_snapshot/code/compiler.py work/
sha256sum work/*.py   # receipts/work_copy_hashes.txt
# 1752c0fd6256117729ee0eacb7eae84bcafe8eeb9bdabe0fb6a4b47ce79f1307  work/target_envelope.py
```

## 3. Synthetic probes (criterion 2)
```
python scripts/synthetic_probes.py     # EXIT:0
# TOTAL: 49/49 probes match the law
# receipt: receipts/synthetic_probes.json
```
Note: two probe-design errors of the auditor were made and fixed during development
(plane placed exactly on a mesh vertex ring -> zero strict crossings -> unresolved, my
error; 1-ulp-fragile -1mm site, replaced by robust offsets; exact-boundary semantics
pinned by axis-aligned square probes where floats are exact). One expectation-tuple
miscount (gapped quad = 2 open chains, not 1) fixed; module behavior was correct
throughout. No baseline data used.

## 4. Reproduction (criterion 3)
```
python scripts/reproduce.py     # EXIT:0
# PATH A: recorded count tables per side: loop 6/1/7/2 ; hull 3/0/5/8  (known state CONFIRMED)
# all per-site recorded verdicts re-derived from recorded distances per the law: match
# fit-json vs attachment_candidates.json: 32 candidates crosschecked (verdict+dist+authority): match
# admission lists vs reproduced lists: match; residual flags consistent
# PATH B: MonkeyTarget(inputs/) sha match; frame rebuild dev 2.9e-10..4.7e-10 m
# recompute loop 6/1/7/2, hull 3/0/5/8 per side; all per-site verdicts match
# receipt: receipts/reproduction.json
```
Auditor trap documented: the baseline builds the roll witness with the UNNORMALIZED
axis (`_band_roll(mt, pk[0], P, P_d - P)`, actual_target_fit.py L523). My first rebuild
passed the normalized axis; the roll witness argmax changed, rotating the frame by a
large angle (loop distances invariant under frame rotation, hull distances not). Fixed
to verbatim baseline logic.

## 5. Candidate-C shortfall re-derivation (criterion 4)
```
python scripts/candidate41.py   # EXIT:0
# radius   : recorded objective 4.346890e-07 m^2; recomputed 4.346888e-07 (delta 2.19e-13)
#   = ridge 4.301800e-07 + ONE violation (67.15 um)^2 at ECRL-P3 t=0.35
# radius_l : identical (mirror), ECRL_l-P3
# receipt: receipts/candidate41.json
```
Hull/loop discretization stats:
```
# receipts/hull_discretization.json  (hull edge med 2.80-2.84 mm, sagitta 187-256 um)
# receipts/reproduction.json -> segment_stats, loop_geometry
```

## 6. Authority labeling (criterion 5)
```
grep -rn "authority" baseline_snapshot (py/json/md)
# every JSON authority field == "local_triangle_plane_loop"; hull never labeled authority
python: 32/32 candidates carry skin_containment.authority == local_triangle_plane_loop
        + a hull_sampling_diagnostic key; fit json containment_authority:
        "local_triangle_plane_loop (hull sampling retained as diagnostic)"
grep -n "loop_authority_ok" baseline_snapshot/code/*.py
# actual_target_fit.py:632: "loop_authority_ok": confirm_loop[side]["ok"]
# target_envelope.py:548:   "ok": bool(not outside and not unresolved and not tight and inside)
```
