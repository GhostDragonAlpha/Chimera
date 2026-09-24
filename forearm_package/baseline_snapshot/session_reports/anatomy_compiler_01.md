# ANATOMY COMPILER 01 — WHOLE-BODY FIT MEMBRANE EXECUTED

**Agent:** bigpickle | **Date:** 2026-09-23 | **Scope:** `.tmp/anatomy_compiler/` (build only; no production edits, no commit, no MuJoCo, no training/attachment-force/display-mesh work)
**Membrane:** `.tmp/anatomy_compiler/DERIVATION.md` (F1–F7 + closed forms + refusal catalog + status ledger)
**Source of truth:** verified real source XML, revision `e021d5d9d1698dafea93c0dcf34b4bc8ce1530e7`

**Verdict: F1–F7 + G0 + S1 all pass (`python run_tests.py` → exit 0); example pipeline runs end-to-end (exit 0).**

---

## 1. Source facts (measured, XML, not assumed)

| Quantity | Measured |
|---|---|
| bodies | 19 (root = pelvis) |
| coordinate names | 39 distinct |
| sites | 937 total `<site>`; **468 referenced by spatial tendons**; all point-only (`pos`, no quat/fromto) |
| spatial tendons | 120, each `<spatial name="<muscle>_tendon">`, pure site chains (length 2..10) |
| muscle actuators | 121; 120 carry `tendon/class=muscle/timeconst/force/lengthrange/ctrllimited/ctrlrange`; **1 carries only `ctrllimited/ctrlrange/scale`, `tendon=None`, and has NO name attribute** |
| rest pose | bodies axis-aligned; body origin = proximal joint; +y up, +x forward, +z right; root pelvis at (0, 0.73, 0) |

The synthetic fixture `synth_chimanoid()` reproduces EXACT counts (19/39/468/120/121) and the same coordinate-tree adjacency, so one correspondence object runs against BOTH the real intake and the twin — that is how the closed forms are checked synthetically and the same object grounds the real XML.

## 2. Membrane promises and their executables

| ID | Promise (DERIVATION §) | Executable | Result |
|---|---|---|---|
| G0 | counts gate | `run_tests.py` G0 (synth + real asserts) | PASS |
| F1 | shared-joint closure: parent `dist` ≡ first child `prox` (kinematic trunk; root children exempt; non-first children are independent branches) | closure residual ≤ JOINT_EPS 1e-9 | PASS (max 0.00e+00 m, 18 segments, synth + grounded) |
| F2 | output is covariant under a proper rotation of the *entire authoring* | all scalars invariant; sites co-rotate; roll twist invariant mod 180° | PASS (twist is a coord-axes branch, arctan2 ±90°, compare mod 180°) |
| F3a | preserve mode REFUSES reflected authoring | `Refusal.handedness_mismatch` (mirror plane n=(0,1,0)) | PASS |
| F3b | mirror mode is an EXACT reflection: frames proper, `chirality_det` negated, `frame_handedness=left`, scalar physics passed through | F3b asserts | PASS (chirality −1.000, left) |
| F4 | site-subtree coupling: a poke at one branch moves no foreign sites | F4 | PASS |
| F5 | analytic tendon moment arms ≡ central-difference (fd_eps = 1e-5) | whole body, 120 tendons, every tendon×coord | PASS (all matched; worst rel dev 2.78e-11) |
| F6 | uniform scale s=2.5 closed forms | rest×s, mass×s³, inertia×s⁵, arms×s, segment scale×s | PASS |
| F7 | every refusal NAMED; nothing silently defaulted | full catalog via `expect_code` / `expect_refusal` | PASS |
| S1 | `aspect` scale policy closed form (radial = w_fit/w_src) | femur_r aspect segment ⇒ diagonal (s_a, radial, radial), mass = m_src·detS | PASS |

**Numerical honesty notes (why these tolerances):** chirality_det comes out ±1 to fp (1.0 vs 0.999999999999999) → compare with `<1e-9`. Roll twist is a circular angle → circular compare mod 360, and because the lateral reference plane is only defined up to a 180° flip about the bone axis, twist is measured mod 180° (a ±90 flip is the SAME reference plane, not a geometry change — verified: `Bp1 == R·Bp0` exactly). Inertia spectra compared as signed eigenvalues (`eigvalsh` trick), not spectra. Moment arms compared absolute (`<1e-9`) because some arms are ≈0 (relative would divide by ~0).

## 3. Whole-body example output (measured)

`python example_whole_body.py` — 3 fits, one correspondence:

- **grounded** (real chimanoid.xml): 39 joints, 468 sites, 120 tendons, 55 landmarks / 18 segments, joint closure 0.0, unmatched arms 0, 120/120 analytic arms matched (worst rel dev 2.8e-11). Rest lengths 0.1117–1.0828 m. Total fitted mass **533.8 kg** vs source-scaled mass sum 68.5 kg (aggregate detS inflates distal bodies by up to 344× — see §5 flag).
- **synthetic twin**: 39/468/120, closure 0.0, chirality 1.0, 0 unmatched arms, rest 0.0895–1.1975 m, mass 614.5 kg.
- **mirror** read of the same anatomy: preserve→refused `handedness_mismatch`; mirror→accepted with `chirality_det=-1.000`, `frame_handedness=left`.

Per-segment output (grounded example, informative — scale is FITTED, not biology):
axial scale 0.844 (thorax_dummy) … 7.155 (hand_r/hand_l); roll twist ±90° on every segment (reference-plane branch, §2 F2/F3 notes).

## 4. Fitted structures (JSON, `runs/`)

- `grounded_chimanoid.json`, `synthetic_twin.json`, `mirror_read.json` — via `schema.write_json`.
- Per segment: `scale`, `frame_basis` (proper), `origin`, `bone_axis`, `roll_ref`, `roll_residual_deg`, `dist/prox` landmarks, `frame_handedness`.
- Per body site: fitted global + fitted local + owning segment.
- Per tendon: path (ordered fitted sites), `rest_length`, per-coord `moment_arms` (analytic + FD + matched flag + fd_eps).
- Physiology per body: `mass`, `mass_src`, `com_fitted`, `inertia_fitted` (about fitted CoM), `inertia_src`, `det_scale`, `status`. Status family: `requires_density_validation` etc.
- Per muscle: `rest_length` (fitted), `lengthrange` scaled, `force/timeconst/ctrl` ingested unchanged, DIY status. The 1 tendon-less muscle: status `no_path`, no name (truthful ledger).

## 5. Non-claims and open items (deliberately NOT done)

- Fitted geometry is a **homogeneous-scaling fit**, never asserted to be biology. Mass/inertia are `source × detS`; a real physiology pass is downstream, flagged `requires_physiological_rerun`.
- **Flag for reviewers — hand segment inflation:** axial scale 7.155 for `hand_r/hand_l` ⇒ detS ≈ 344.8 ⇒ fitted mass 157.7 kg each (source is a short bone). This is the honest output of the *synthetic generation* (source bone ~0.04 m vs target 0.30 m), not an authoring error; the aspect policy (S1) exists precisely to constrain radial axes off width landmarks. Do not present these masses as biology.
- Muscle/mass-families authoritative references and `<site quat/fromto>` handling: not exercised (source has none).
- No training, no attachment-force, no display-mesh, no MuJoCo run: out of scope by contract.

## 6. Latent machinery found & fixed along the way

- `intake.py`: the 1 muscle with `tendon=None` also has NO name attribute in the XML (verified: repr `''`); carried honestly, never invented.
- `synthetic_fixtures.py`: tibia distal landmark was on-axis (would have forced `axis_parallel_roll`) → added an `ankle_site` off the bone axis; `generate_target_landmarks` roll-reference used the bone midpoint instead of the picked roll site → `axis_parallel_roll` → fixed to use the actual roll site; `place()` seeded only the first child → KeyError `'humerus_l'` → seeds all direct children.
- `compiler.py`: chirality loop had a latent `assert seg is not None` that would mask `unresolved_segments` → now skips bodies without segments and pairs src/tgt arrays consistently. Mirror mode implemented as un-reflect → preserve fit → reflect geometry (frames `R·Bp·diag(1,1,-1)`, scale negated axis, `chirality_det` negated) so it is an *exact* reflection, not a covariant refit.
- `correspondence.py`: `detect_chirality_map` corrected — chirality det is `det(U@Vt)` directly (SVD congruence sign), not a derived `sign(det(UVᵀ))` with a stacked D.