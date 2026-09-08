# GLM-FREEZE RUN HISTORY — frozen GPU-comparison fixtures

Run by GLM (deputy, physics implementation agent), 2026-09-07. ASTRA-authorized
continuation of GLM-RECOVER. Big Pickle unavailable; nothing committed or
pushed — publication is ASTRA's decision.

## Source identity

- Isolated checkout: `E:\Chimera_GLM_freeze` (fresh `git clone --no-hardlinks`
  of https://github.com/GhostDragonAlpha/Chimera; the recovered checkout
  `E:\Chimera_G01` was not touched: no switch/reset/clean/stash/overwrite).
- Branch `astra/gait-capture`, remote head = **cf2a0ae2c7bd68f1c64db630c4db5de32785580a**
  ("Publish BP-A1: G01 nine-finding hardening pass + 25 named regression checks (62/62)").
  The branch head IS the BP-A1 commit (`git merge-base --is-ancestor` → true).
- Published `tools/surface_energy_reference.py` SHA-256
  `ee9effcfbddad8d02e03f71d414b27da177f0656de535eaab0d76ae39796f0b7`.
  Recovered pre-crash copy hashed `ca0a4500a11c19eedd50e0fafb1cf6c34b6df6d03082427dbe8f8588a31ab844`
  (which matched the R3 snapshot of record). **The two are NOT equivalent by
  hash**; diff shows the published file is the BP-A1 hardening rewrite (named
  refusals, A1-8 finite gates, NONFINITE_RESULT, CSR reduceat gather with the
  F8 fix). All frozen references in this task were evaluated with the
  PUBLISHED file at the commit above. The recovered membrane files are not
  present in the published tree; verbatim copies + original hashes live in
  `tools/gpu_fixtures_recovered/`.
- `docs/THE_MASTER_LIST.md` read for context; not modified (ASTRA maintains it).

## Commands and exit codes (actual)

```
git clone --no-hardlinks https://github.com/GhostDragonAlpha/Chimera E:/Chimera_GLM_freeze   # ok
git -C E:/Chimera_GLM_freeze checkout --detach origin/astra/gait-capture                     # HEAD = cf2a0ae2
python tools/gpu_fixtures_generate.py        # EXIT_GEN=0     (21:0xZ, after 2 preregistration fixes)
python tools/gpu_fixtures_verify.py          # EXIT_VERIFY=1  (21:12Z — FAILED, preserved)
python tools/gpu_fixtures_verify.py          # EXIT_VERIFY=0  (21:19Z — all PASS, control DETECTED)
```

## Preregistered allowances / budget law (see manifests for full derivation)

- `u = 2^-24`; coordinates conservative bound `sqrt(3)*u` per corner; area
  allowance `sum_f 3*0.5*maxedge_f*sqrt(3)*u` (gamma-INDEPENDENT — areas do
  not scale with gamma); force_z allowances PROVISIONAL: B2 1.0e-6 N
  (preserved from recovered B2 C2), fan12 2.0e-6 N (scaled by face count
  12/6); force_xy symmetry 1.0e-6 N.
- Budget law per vertex/component: `B_vj = eta_(d_v-1) * sum_incident |f32
  corner force component|`, corners rounded to binary32 BEFORE summing;
  `eta_n = n*u/(1-n*u)`. Degree-six bounds were NOT reused for the fan;
  every budget derives from actual degree (centre 6 → eta_5 = 2.9802331269482156e-07;
  centre 12 → eta_11 = 6.556515e-07; rims d=2 → eta_1 = 5.960465e-08).
- Adopted B2 GPU budgets (corner 4.0e-6 N, assembly-only 1.0e-6 N, complete
  2.5e-5 N, energy 1.1e-5 J) are RECORDED in the manifests, preserved, and
  remain the gates for FACE arithmetic; these fixtures do NOT verify face
  arithmetic — they freeze the assembly-isolation reference (`asmref`) and
  the per-vertex assembly bounds.

## Results (verify_results_20260907T211952.096833Z.json)

All 11 checks PASS for both fixtures at gamma = 0, 1, 2:

| check | b2 | fan12 |
|---|---|---|
| V1 artifact hashes/shapes/dtypes | PASS | PASS |
| V1b numpy version matches generation | PASS | PASS |
| V2 CSR coverage + fixed order | PASS | PASS |
| V2b manifest analytic bitwise reproducible | PASS | PASS |
| V3 bitwise reload reproducibility | PASS | PASS |
| V4 independent scatter within eps64 bound | PASS | PASS |
| V5 asmref bitwise + f32 rounding bound | PASS | PASS |
| V6 zero-gamma numerically zero | PASS | PASS |
| V7 gamma2 bitwise double of gamma1 | PASS | PASS |
| V8 analytic within preregistered allowances | PASS | PASS |
| V9 budgets bitwise recompute + eta5 contract | PASS | PASS |

Key frozen values (gamma = 1 J/m^2):
- b2: A = 2.62499995337 m^2 (analytic 2.625), F_c = (0, 0, -0.428571428493) N
  (analytic -3/7 = -0.428571428571; dev 7.8e-11 N ≪ 1e-6 allowance).
- fan12: A = 3.02501588342 m^2 (analytic 3.02501593727), F_c =
  (0, -8.3e-17, -0.398600004352) N (analytic -0.398600004411; dev 5.9e-11 N).
- Assembly budgets (gamma 1): b2 centre (deg 6) [5.109e-07, 5.899e-07,
  1.277e-07] N, max rim (deg 2) [5.162e-08, 4.471e-08, 4.258e-09] N;
  fan12 centre (deg 12) [1.3005e-06, 1.3005e-06, 2.6134e-07] N, max rim
  [5.212e-08, 5.212e-08, 1.980e-09] N. (gamma 2 budgets are exactly 2x.)
- Corner-order corruption control: corner slots 0<->1 of face 0 swapped in a
  temp copy with the copied manifest hash updated (hash check evaded) —
  verification FAILED as required, detected by V3, V4, V5, V7, V9.

## FAILED RUN PRESERVED + two verifier corrections (both pre-acceptance, cause named)

`verify_results_20260907T211214.440162Z.json` records the honest first run:
V5/V9 FAIL on uncorrupted fixtures, caused by two bugs in the VERIFIER (no
fixture, budget, allowance, or implementation was changed):
1. V5 used the wrong rounding model: binary32 relative error is bounded by
   the unit roundoff u = 2^-24, not u/2. Observed worst ratio 1.239 against
   the erroneous 0.5*u bound = 0.62 against the corrected u bound.
2. V9 demanded bitwise equality of eta_5 to the 16-digit contract literal;
   the float64 value is 2.9802331269482156e-07. Corrected to <1e-15 relative
   agreement (the structural identity eta_5 == 5u/(1-5u) remains bitwise).
Earlier, BEFORE any artifact existed, two preregistration errors were caught
in review and fixed at generation time: a dead allowance line, and an
incorrect gamma-scaled area allowance (areas are gamma-independent).

## Scope boundaries honored

- No optimizer, dynamics, gravity, contact, or time claim; force-evaluation
  fixtures only. CPU numerical class only — the engine window is not
  exercised and no visual claim exists.
- The recovered 25-vertex/36-face disk demo remains its own fixture; the new
  fan12 (13 vertices / 12 triangles) is a separate construction. B2's frozen
  upload was asserted byte-equal to the recovered `b2_mesh()` upload.
- Nothing committed or pushed. Workspace git state: published tree unmodified;
  all deliverables are NEW untracked files (list below).
