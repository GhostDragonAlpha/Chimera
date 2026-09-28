# MAT2-M03 report — pressure on a closed triangulated membrane

Task MAT2-M03 / planning id M03, criteria sha256
f91d2bca94b7f72c2650eab4f14356eb0889e139facb6f07d66920b021bb8ded, attempt
61aa525f80da4b61a10b7e3c788d87fc, arrival
arrival-88bfdd2e0d2c4397b5a21b3a876f8882, base revision 986f270e (sealed line
origin/astra/gait-capture carrying merged M01 + M02 via PR #236), isolated
local branch-2 checkout.

## What was implemented

`pressure_membrane.py` — pressure traction F_i = (p_int - p_ext) * A_i * n_i
from a DECLARED source, divergence-theorem volume closure with named refusals
(`closure_open_edges`, `orientation_inconsistent`, `closure_negative_volume`),
exact zero net force/torque from uniform pressure on any closed mesh (before
and after equal-third vertex lumping), exact linear-field external loading
references (F = -q*V, torque about volume centroid), refinement families
(right tetra with midpoint subdivision, welded cube grids n=1/2/4, icospheres
L0/1/2), quasi-static P-V work with the declared midpoint-rule traction
account, `PressureSource` with authored limits and named refusals
(`pressure_source_undeclared`, `pressure_source_negative_absolute`,
`pressure_source_delta_p_limit_exceeded`, `pressure_source_flow_limit_exceeded`,
power = dp*dV/dt), and the XPBD-style inflate/deflate run (heritage pin
docs/THE_MASTER_LIST.md; fixed 300 Hz tick pin req.teddy_gpu_matter_kernel)
whose per-tick energy ledger reports damping dissipation and the MEASURED
constraint-projection residual — never hidden.

Upstream authority reused verbatim, unmodified: M01 `material_state.py`
(schema authority, sha256 recorded in the receipt and the state document) and
M02's compiled tetra mesh blob (byte-verified against its recorded sha256
51d8231e... before use, exact volume 1/6000 m^3 confirmed).

## Verification (frozen preregistration incl. corrections A1-A7)

- `qualification_receipt.json`: 41/41 checks PASS, 6/6 falsifier bites.
  Highlights: M02 tetra closure exact (V within 1e-18 of the compiled value);
  uniform dp=100 Pa net force/torque worst 1.641e-15 N / 6.36e-17 N m across
  the T4 family (nine refinement meshes + the M02 tetra); buoyancy identity
  |F - (-qV)|/|qV| <= 1e-12
  at every family member (cube grids exactly rho*g*V = 9806.65 N per m^3);
  icosphere volume error monotone 0.3945 -> 0.1265 -> 0.0338 (L2 within the
  A2-derived 6e-2 bound); quasi-static work closed form 8.275e-3 J exact,
  per-step traction-volume agreement 8.0e-16 J; power 0.03 W exact to 1 ulp;
  dynamic run COM drift 2.9e-17 m (uniform internal pressure does NOT propel
  the free body), peak volume ratio 1.2352, recoil 0.54 percent, max edge
  strain 0.46 percent, ledger residual within tick turnover at every tick and
  the account closes to 5.551e-17 J; byte-identical replay (T8); the experiment
  document validates under the UNMODIFIED M01 validator (T10).
- `test_pressure_membrane.py`: 15/15 tests OK (probes P1-P10 + falsifier
  bites F1-F6 as assertions).
- Falsifier proof (each bite demonstrated on a tampered copy, observed values
  in the receipt): F1 area-independent traction -> uniform-dp net force
  0.433 N (vs 1.92e-16 N correct) and buoyancy identity broken >= 1e-3 rel;
  F2 tampered free body drifts 7.5e-3 m (vs 2.6e-16 m correct); F3 undeclared
  / negative-absolute sources refused by name; F4 deleted triangle ->
  `closure_open_edges`, traction refused; F5 flipped winding ->
  `orientation_inconsistent`, volume drops, net force 1.732 N; F6 area factor
  omitted -> work account mismatch 5.54e-2 J (vs <= 1e-15 J per step correct).
- Determinism: no stochastic inputs anywhere; replay equality is checked
  (T8) by canonical digests; the render replay asserts per-tick volume
  equality with the committed trace at 1e-15.

## Visual capture (material/motion profile)

- 24 frames (2560x840), 1 tick = 1/300 s simulated replayed at 1 video second
  (slow motion x300, declared in every footer); top row diagnostic viewports
  [whole | side | front | close-up] carrying the packet's five diagnostic
  layers, middle row clean (same cameras, no overlays), bottom pressure /
  volume / cumulative-work traces.
- Video: capture/capture_mat2_m03_pressure_20260928.mkv (attempt workspace),
  sha256 30a15d87a38050c437e38e6e2ab18306e0461d05861150e6e121a8114322f815,
  24.0 s, h264 2560x840, mid-video decode spot-checked against the source
  frame.
- Manifest: chimera.visual_capture_manifest.v1, task_id "M03" (SHORT form),
  profile_id material, subject_sha256 = pressure_state.json, capture_sha256 =
  the mkv, state_binding = sha256 of pressure_trace.json;
  `visual_capture.validate_manifest` returned structurally_valid=True (6
  views, diagnostic+clean pairs, fixed_bookmark cameras with fully declared
  fields, required subject visibility declared).
- Pixels inspected (not inferred from filenames): frames 03/10/22 show the
  ball inflating (V 3.904e-3 -> 4.519e-3 -> 3.687e-3 m^3), radial force
  arrows growing with dp and vanishing at dp=0, close-up tetra arrows scaling
  with triangle area (slant A=0.0087 longer than leg A=0.0050) and with
  pressure, clean rows clean, COM drift line showing no propulsion.

## Corrections issued before the receipt (all pre-measurement, documented in
PREREGISTRATION.md with the triggering probe values)

A1 work-path step count + dynamic scenario scale; A2 icosphere L2 volume
bound re-derived from face geometry (guess 3.0e-2 replaced by derived 6e-2);
A3 telescoping bound below one ulp re-issued at 1e-14 J; A4 scaffold
compliance re-derived for visible inflation + ledger residual re-based on
tick turnover; A5 run length 24 ticks (aligned 1:1 with video), membrane
r0 = 0.10 m for visibility, recoil bound 1.0 percent; A6 first-receipt
failures (runner over-applied the L2 bound to L0/L1; T6 bound below one ulp,
re-issued 1e-16 W) — failed first receipt preserved as
first_receipt_t3_t6_failures.json; A7 torque about the volume centroid is an
h^2-convergent quadrature, not an exact identity (measured 1.926e-2 ->
4.816e-3 -> 1.204e-3 N m, exactly x4 per subdivision; refined members <=
1e-9 N m). The force identity F = -q*V is exact everywhere.

## Honest limits

- XPBD edge constraints are a demonstration scaffold, not a qualified
  constitutive model; no material stiffness is inferred from them.
- The source is an ideal declared actuator: no gas law, no compressibility,
  no fluid interior, no contact, no gravity-on-membrane scenario.
- The renderer is a CPU rasterizer with painter's-algorithm depth (declared
  occlusion_mode depth_tested); it displays solver state, it is not a GPU
  render.
- The constraint-projection work is reported as the measured per-tick
  residual, not modelled as dissipation.
- Visual acceptance of the capture remains with the independent reviewer;
  validate_manifest is camera-metadata structure only.

## Durable lessons

1. Freeze absolute bounds from derivations, never from guessed magnitudes:
   three of the six corrections (A2, A3, A6) were float-resolution or
   geometry guesses that a first probe falsified; deriving the ulp floor and
   the h^2 quadrature order beforehand would have saved the round trip.
2. An exact identity can live one derivative higher than intuition puts it:
   net force of a linear field is exact at centroid midpoints (linear
   integrand) but net torque is quadratic and only h^2-convergent (A7).
3. Visual-scene scale must be derived from camera pixel budgets before
   freezing scenario constants: an r0 = 0.04 m membrane is 13 px at the
   frozen whole-experiment camera — invisible motion cannot satisfy a motion
   profile (A5).
