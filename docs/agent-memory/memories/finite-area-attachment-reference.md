---
name: finite-area-attachment-reference
description: Standalone conservative finite-area membrane-to-bone attachment
  reference (tools/finite_area_attachment) — derivation + Python reference +
  elastic coupon + native C++ coupon evolved through seven lead-audited rounds;
  now a data-driven coupon-input/v3 contract system incl. a powered two-body
  membrane assembly (tension-only actuator, synthetic not muscle) AND a
  ground-interaction fixture with provisional penalty contact (no engine
  parity); 48 Python tests + 534 preregistered native comparison checks
  (102+102+132+198) pass; failure ledger FR-1..FR-23 unedited in DERIVATION.md
metadata:
  node_type: memory
  type: project
  originSessionId: sess_2241cedd-5b94-4475-a9be-a8a37f344578
---

`tools/finite_area_attachment/` — the attachment-model reference, evolved over seven
rounds (all 2026-09-23/24), no production engine files touched. Model: objective
area-weld Π = ½ Σ w eᵀWe, e = x − c − Rā, W = RK̄Rᵀ (K̄ bone-local). Round 2 audit:
production rest-length spring = weld only at L₀=0 + single point (rank 1 at rest,
3 taut, transverse k(r−L₀)/r negative slack); autodiff CAN give the exact tangent
(fixed-chart energy differentiation); sweeps: virtual-work probe cancellation-
dominated (B/ε). Round 3 (LEAD-found): admission gate replaced by
assert_min_couple_stiffness = weakest-direction eigenvalue of actual M = Σw[ã̃]ᵀK̄[ã̃]
(fixed==relaxed: origin-invariant Schur), explicit κ̄·A provenance, authored-
requirement label, NO length cutoffs (FR-7: 40×2 µm sliver with consistent
provenance admitted before). Round 4: NaN/negative×negative input holes closed
individually + zero refused as policy (FR-9); FR-8 CORRECTED — units_contract.py
EXISTS at the chimera-balance checkout
(C:/Users/allen/Documents/Codex/2026-09-21/files-pasted-by-the-user-we/work/chimera-balance/tools/
elastic_foundation/units_contract.py), absent from E: checkout only; coupon now
admits via admit_volumetric_v1 (thickness exactly once, E2=E3D·h) +
evaluate_physical_v1 from ONE pinned root (dependency_pin.json, sha256 verified at
import). Coupon fixture of record: 60mm 2×2 STVK grid, E3D=25000 Pa, ρ=5000,
k_weld=100 N/m, ω_max·dt=0.685; scenarios off-center/asymmetric-3-corner/mixed:
p exact ≤1e-16, L drift + energy envelope ∝dt, no secular drift, orders mem 1.9-2.1
/ translation 1.9-2.4 / rotation ~1.0; off-center 25% envelope at 300 Hz = measured
LIMITATION, bounded 2 s runs ≠ general nonlinear stability certificate. Oscillator
modified-energy exactness scoped to the linear oscillator. NATIVE C++ coupon
(native/native_coupon.cpp, C++17 stdlib-only): one command bash native/run_native.sh
→ 102/102 preregistered cross-language checks pass (energies 1.9e-16, forces/wrench/
one-step ≤1e-12, metrics ≤1e-9, worst budget 42%); benchmark 2.64e6 steps/s
(0.38 µs/step) scoped to the 9-vertex coupon ONLY. Native gotcha FR-11: corner
forces need u_j = P @ ROW j of B (columns of P·Bᵀ) — energy matched while forces
were wrong; the static comparison caught it. Round 5 (data-driven, same day):
native coupon reads coupon-input/v1 JSON contracts (mesh/B/areas, EXPLICIT nodal
masses, material, body, weld, per-scenario ICs, dt) with strict refusals on both
sides (unknown/missing fields, partial overrides refused); authored ONCE by
make_coupon_input.py from the pinned dependency — no runtime inference; two
fixtures: input_default.json (102/102 regression preserved) + input_second.json
(irregular pentagon, 5 verts/3 faces, asymmetric weld, 102/102 first run, worst
25% of budget). Benchmark accounting fixed per LEAD finding (FR-14): completed
steps + termination reason + FNV-1a final-state checksum; incomplete runs report
NO throughput; deliberate early-stop probe (bench_dt 0.25 → 5/200000, step_failed).
Round 6 (powered two-body, same day): three LEAD-found admission holes fixed in
BOTH runtimes (doubled areas0 → native now recomputes areas+B from rest geometry
within 1e-9; improper rotation det=−1 refused everywhere; inertia [1,1,3] triangle
inequality refused, equality admitted) — exact mutations are regression probes.
coupon-input/v2: bodies list + optional tension-only actuator (authored knot
profile, dynamics none, F_max declared — synthetic, not muscle). input_twobody:
strip with two L-shaped welds + mast actuator; F_a+F_b=0, tau_a+tau_b=0 exactly;
zero activation = passive BITWISE; p exact; L + work-energy residual halve with
dt; 132/132 Python/native checks. FR-17: actuator sign was inverted (strut not
tension) — caught by the preregistered torque-sign falsifier. Viz:
native/twobody_trajectory.png. 43 Python tests + 336 native comparison checks
pass; one command bash native/run_native.sh. Round 7 (ground interaction, same day): dup-JSON-key refusal in both runtimes
(FR-19, lead-found; Python kept last, native picked first); general common-origin
wrench-moment falsifier replaces fixture-specific tau-pair claim (FR-20). Bounded
contact-law discovery found NONE in repo → PROVISIONAL frictionless penalty-dissipative
normal contact 'provisional-penalty-v1' (k=200 N/m, c=1.0 per site, membrane vertices,
fixed plane, gravity 9.81) — no engine parity claim. input_ground.json (coupon-input/v3):
A freeflight (COM ballistic EXACT to 4e-16), B passive drop (pen 11.7mm ≤ 15mm bound,
t_c 0.0633), C powered-supported (residual refines only 1.06×: FR-22 refuted prediction,
reported), NC near-contact (py/native first-contact times agree exactly). External-impulse
momentum balance replaces free-space conservation. 198/198 ground checks; 534 total across
4 fixtures; 48 Python tests; GIF animation fixed axes. FR-21: L_drift relative tolerance
ill-posed for rounding-scale residuals → absolute (failed run retained as evidence).
Failure ledger FR-1..FR-23 in DERIVATION.md §9. No walking claims, no production edits.
Follows the tools/elastic_foundation precedent ([[fleet-state-2026-09-20]]).
