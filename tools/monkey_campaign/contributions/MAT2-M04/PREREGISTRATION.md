# MAT2-M04 PREREGISTRATION — frozen before implementation and before any measurement

Frozen: 2026-09-28Z, before authoring passive_law.py, passive_response.py,
test_passive_response.py or run_experiments.py, before any experiment run, and
before any capture code exists. Task: MAT2-M04 / planning id M04 — "Verify
passive resistance and directional material response" (criteria sha256
e9faa5bcb3926b2cdcd68f110c2c9480bb7b7d18e40a2623beb5ff5ce978a665, attempt
262e9d2a30ae4c4b82d84de7de9661a1, arrival
arrival-9c8ab01ecb754d6792806d29ae3fc332).

done_when (verbatim): "Implement/reconcile only the rigid, compliant and
fiber-reinforced responses needed by the monkey. Declare constitutive equations,
parameters, source or synthetic status, rest state, damping and valid strain
range. Independent load-extension, relaxation and rotated-fiber experiments meet
preregistered limits."

Card falsifier (verbatim): "Density substitutes for stiffness, a rotated fiber
has no intended effect, or passive material creates unexplained energy."

Verification-profile falsifier (verbatim): "Unbound media, clipped load path,
hidden constraint/support, area-independent triangle forces, overlay-driven
motion, or unaccounted energy prevents acceptance."

Port contract (verbatim): "Rest/current geometry + material history -> stress/
force + updated history + stored/dissipated energy."

## Base and reconciliation (read-only, done before this freeze)

- Canonical startup assigned slot branch-3, prepared checkout head
  c525b82c7c3ce0128565424764293a3c85811ab3. The sealed line (registry MAT2-M02
  winner merge_commit_sha 986f270ef24cda0008c52bd40d4b6d08565c0692, PR #236,
  merged 2026-09-28T22:04:20Z) contains the merged MAT2-M01 schema and MAT2-M02
  compiler and is a descendant of c525b82c. Per the dispatch ("depend only on
  what is already merged"), the local attempt branch is advanced to 986f270e
  (fast-forward descendant of the prepared head; local-only, never pushed).
- Dependency input pins verified in the checkout before this freeze:
  - MAT2-M02/monkey_arm_regions.json canonical sha256
    51767d1fd33c4002041a31764158dbd75ded27b4bec4c1ecb63453d87cfb316a
    (object monkey-arm-regions, revision 1, 7 regions, 6 bonds, 7.006 kg).
  - MAT2-M02/independent_shape_regions.json canonical sha256
    23995548570aaaac41fccfe9fb0e6cdbee1f7a3f25b151989ce4289be463ceed
    (object independent-shape-regions, revision 1, tetra + plate, 0.14 kg).
  - MAT2-M02/monkey_arm_independent_meshes.json file sha256
    51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834
    (blob: tetra 4 triangles / 4 vertices, plate 2 triangles / 4 vertices).
  These hashes are frozen inputs; a mismatch at run time refuses
  `input_pin_drift` (no silent rebase onto different inputs).
- Reconciled gaps this card fills (M02 inventoried absences): the compiled
  documents declare ZERO material directions and ZERO laws, and no material
  solver existed at revision 1 (rest == current by declaration). M04 adds the
  passive response laws + directions on declared specimens and the first
  passive response evaluator. M01's `laws` rows are closed at kind
  'pressure_deformation' (reserved by M03, in parallel); passive response laws
  therefore live in a new M04-owned versioned document
  `chimera.passive_law.v1`, and the schema gap is inventoried here rather than
  silently widening M01's vocabulary.

## Frozen statement

M04 implements ONLY passive response (no active control, no pressure law, no
fracture, no thermal coupling):

1. `passive_law.py` — strict validator + builders for `chimera.passive_law.v1`:
   pins source documents by canonical sha256; declares gauges, profile
   assignments, fiber directions and parameters with named refusals
   (M01 validation style; canonical round-trip required). Zero-length or
   non-unit fiber axes refuse `invalid_fiber_axis`.
2. `passive_response.py` — the passive evaluator honoring the port contract:
   state (extension history, force, stored, dissipated, tick) stepped per tick;
   exact exponential Maxwell integrator (no ad-hoc Euler drift); energy ledger
   check refusing `unexplained_energy`; area-scaled per-triangle force
   distribution `F_i = F_total * A_i / sum(A)` refusing zero/negative areas;
   strain gate refusing `outside_valid_strain_range` BEFORE evaluation; named
   profiles 'rigid', 'compliant_maxwell', 'fiber_reinforced' only.
3. `author_laws.py` — emits the M04 declaration documents from the pinned M02
   documents (never mutating them):
   - `arm_rigid_laws.json`: all seven arm regions assigned 'rigid' (bone
     surface segments; the compiled arm has no soft-tissue volumes — M02's
     absent-anatomy inventory is preserved, no tissue invented).
   - `independent_shape_laws.json`: tetra assigned 'compliant_maxwell' with
     gauge G-TETRA; tetra also carries the fiber-reinforced variants for the
     directional experiment; plate assigned 'fiber_reinforced' (two-triangle
     area-scaled interface); fiber directions declared as M01-compatible
     direction rows in a companion `independent_shape_directions.json` copy
     that validates through the UNMODIFIED M01 validator.
4. `run_experiments.py` — E1/E2/E3 below; emits `experiment_trace.json`
   (per-tick solver states + canonical state hashes) and
   `experiment_receipt.json` (frozen-limit verdicts + hashes). No wall-clock,
   no RNG in any emitted artifact (determinism is probe-checked by a double run
   comparing bytes).

### Specimen and gauge (all geometric numbers are pinned from M02's compiled rest geometry, not invented)

Specimen: the M02 independent tetra (closed right tetrahedron, world vertices
v0=[0.3237059520399438,-0.14045346996593683,-0.05670000000000001],
v1=v0+[0.1,0,0], v2=v0+[0,0.1,0], v3=v0+[0,0,0.1] m; volume
1.6666666666666667e-04 m^3 (compiled 1.66666666666666682e-04), authored mass
0.120 kg). Gauge G-TETRA: uniaxial along +X, rest length L0 = 0.100 m
(X-leg), declared load-bearing area A = 5.0e-3 m^2 (exact area of the
tetrahedron face perpendicular to X), support = the x-min face (pinned,
rendered, never hidden), load applied at the gauge end (x-max vertex),
compressive. Rest state: zero applied load -> extension exactly 0, force 0,
stored 0, dissipated 0 (rest == rest geometry).

### Constitutive declaration (the "declare" clause; all parameters authored here, status synthetic unless stated)

| profile | constitutive equation | parameters | source/synthetic status | damping | valid strain range |
|---|---|---|---|---|---|
| rigid | x = 0 for any load in range; transmits F_out = F_in exactly; U = Q = 0 | none (kinematic idealization) | synthetic_authored (modeling choice: bone segments treated as rigid for the monkey) | none (no history) | n/a (no strain state exists; any nonzero extension claim is a refusal) |
| compliant_maxwell | elastic: x_el = F/k, k = E*A/L0; series dashpot: tau = c/k; force ramp: F(t) = c*v*(1 - e^(-t/tau)); hold: F(t) = F_ramp*e^(-(t-t_ramp)/tau); creep under force ramp F=rt: x(t) = r*t/k + (r*t^2)/(2c) | E = 5.0e5 Pa, k = 2.5e4 N/m, c = 6250 N*s/m, tau = 0.25 s | synthetic_authored (no source modulus is admitted for any monkey tissue yet; authored for the experiment, declared as such) | linear viscous dashpot c (Maxwell series), tau = 0.25 s | -0.30 <= eps = x/L0 <= +0.30 |
| fiber_reinforced | E(theta) = E_trans + (E_fiber - E_trans)*cos^2(theta), theta = angle between gauge axis and fiber axis; elastic x = F*L0/(A*E(theta)); k(theta) = E(theta)*A/L0 | E_fiber = 2.0e6 Pa (along fiber), E_trans = 5.0e5 Pa (transverse, = matrix E) | synthetic_authored (fiber ratios authored; no source tendon modulus admitted; geometry-derived quantities pinned) | none declared (elastic anisotropy; damping remains a compliant-only declaration) | -0.30 <= eps <= +0.30 |

Density: matter masses/densities are M02's pinned data; they are NEVER inputs
to stiffness, force, extension or energy (probe P8 enforces bitwise invariance
under a 100x density change; falsifier bite F1 proves a density-coupled tamper
is caught).

## Frozen experiments and preregistered limits (exact closed forms; the discrete per-tick trace must match them within 1e-9 relative, ledger residual below 1e-9 relative of W)

E1 load-extension (force-controlled, quasi-static elastic law; F in
{25, 50, 100, 250} N on G-TETRA):

| profile | k (N/m) | x(25 N) | x(50 N) | x(100 N) | x(250 N) |
|---|---|---|---|---|---|
| rigid | n/a | 0.0 m exactly | 0.0 exactly | 0.0 exactly | 0.0 exactly; F_out == F_in bitwise |
| compliant_maxwell | 2.5e4 | 0.001 m | 0.002 m | 0.004 m | 0.01 m |
| fiber theta=0 | 1.0e5 | 0.00025 m | 0.0005 m | 0.001 m | 0.0025 m |
| fiber theta=45 | 6.25e4 | 0.0004 m | 0.0008 m | 0.0016 m | 0.004 m |
| fiber theta=90 | 2.5e4 | 0.001 m | 0.002 m | 0.004 m | 0.01 m |

Limits: linearity x(2F) = 2*x(F) bitwise for each elastic profile; max test
strain eps = 0.10 inside the declared band; F = 1.0e4 N on the compliant
profile (x = 0.4 m, eps = 4.0) must be REFUSED `outside_valid_strain_range`
before any state update; same-load comparison on the SAME tetra shows
x_rigid(0) < x_fiber0 < x_fiber45 < x_fiber90 = x_compliant at every load.

E2 relaxation (position-controlled: ramp at v = 0.01 m/s to x_target = 0.002 m
(t_ramp = 0.2 s), then hold 1.0 s to t = 1.2 s; compliant_maxwell):

- F(t_ramp) = c*v*(1 - e^(-0.8)) = 34.416939742673655 N (frozen).
- F(t = 1.2 s) = F_ramp * e^(-4) = 0.6303682399821345 N (frozen); ratio to
  F_ramp = e^(-4) = 0.01831563888873418.
- Monotone strict decrease of F through the hold; zero load rate never raises F.
- Ledger (exact closed forms): W_in = c*v^2*(t_ramp - tau*(1 - e^(-0.8)))
  = 0.038957650643315876 J; U(ramp end) = F_ramp^2/(2k)
  = 0.023690514825016586 J; U(hold end) = F_end^2/(2k)
  = 7.947282359563479e-06 J; dissipated Q = W_in - U_end
  = 0.038949703360956316 J; independent closed-form integrals
  Q_ramp + Q_hold must equal Q to within 1e-9 relative of W_in
  (Q_ramp = 0.015267135818299296 J, Q_hold = 0.02368256754265702 J).
  Residual |W - U - Q| > 1e-9*W refuses `unexplained_energy`.

E3 rotated fiber (same tetra, same F = 50 N, fiber axis rotated about world Z;
theta in {0, 45, 90} degrees):

- x(theta=0) = 0.0005 m; x(45) = 0.0008 m; x(90) = 0.002 m (frozen).
- Limits: strict ordering x(0) < x(45) < x(90); x(90)/x(0) = 4.0 exactly
  (= E_fiber/E_trans); E(45) = 1.25e6 Pa exactly; symmetry x(+theta) =
  x(-theta) bitwise; rotating the LOAD by theta with fixed fiber equals
  rotating the fiber by theta with fixed load (bitwise).
- The rotated-fiber EFFECT is required: any implementation where rotation
  leaves the response unchanged fails P5 (this is the card falsifier's second
  arm, inverted into a positive requirement).

Area-scaled interface forces (part of E1's oracle, profile
fiber_reinforced on the plate, declared interface = the two plate triangles,
pinned areas exactly 0.01 m^2 each, total 0.02 m^2): F_i = 50 N * A_i / 0.02
-> 25 N + 25 N exactly; an analytic twin with one triangle's area doubled
gives 100/3 N + 50/3 N; the sum stays 50 N bitwise. Zero-area triangle input
refuses `zero_area_interface`.

Visual motion protocol V (frozen before any capture code; drives the capture;
separate from E1-E3): force ramp F(t) = 100 N/s on G-TETRA, ticks 0..12 at
dt = 0.1 s (t = 1.2 s final), five columns rigid / compliant_maxwell /
fiber0 / fiber45 / fiber90, per-tick extensions from the solver only:

| t (s) | rigid | compliant | fiber0 | fiber45 | fiber90 |
|---|---|---|---|---|---|
| 0.0 | 0 | 0.0 m | 0.0 | 0.0 | 0.0 |
| 0.1 | 0 | 0.00048 m | 0.0001 | 0.00016 | 0.0004 |
| 0.2 | 0 | 0.00112 m | 0.0002 | 0.00032 | 0.0008 |
| 0.6 | 0 | 0.00528 m | 0.0006 | 0.00096 | 0.0024 |
| 1.2 | 0 | 0.01632 m | 0.0012 | 0.00192 | 0.0048 |

Final compliant strain 0.1632 inside the declared band; rigid column is the
visible negative control (zero motion under identical load); the three fiber
columns visibly differ (directional response).

## Frozen positive probes (must PASS on the exact candidate revision)

P1 schema/round-trip: all three M04 documents validate under
passive_law.validate (strict, named refusals) and round-trip byte-identically;
`independent_shape_directions.json` validates through the UNMODIFIED M01
`validate_material_state` with direction_count = 3 (fiber axes 0/45/90 deg for
the tetra) and law_count = 0 (M01 law vocabulary untouched).
P2 input pins: the pinned M02 canonical/blob hashes above are re-verified at
run time; mismatch refuses `input_pin_drift`.
P3 elastic closed forms: every E1 cell matches the table within 1e-9 relative
(or bitwise where stated); k values exact.
P4 relaxation: E2 F(t) trace matches the closed forms above within 1e-9
relative; strict monotone decay in the hold.
P5 directional: E3 ordering/ratios/symmetries as frozen; per-tick E(45) exact.
P6 energy: E2 ledger closes (residual < 1e-9 relative of W_in); U and Q
nonnegative; stored energy at ramp end equals F_ramp^2/(2k).
P7 area scaling: plate interface shares 25/25 N; doubled-area twin
100/3 + 50/3; sum bitwise invariant at 50 N.
P8 density independence: scaling every matter mass_kg by 100 in a copy of the
inputs changes NO response number (bitwise) in E1/E2/E3.
P9 strain gate + rest state: over-band load refused with
`outside_valid_strain_range` and NO state produced; zero-load step returns the
rest state exactly (x = 0, F = 0, U = 0, Q = 0, history unchanged).
P10 determinism: run_experiments.py run twice produces byte-identical
trace+receipt files (no wall-clock, no RNG).
P11 rigid transmission: rigid profile returns F_out == F_in bitwise for all
E1 loads and refuses any nonzero extension request `rigid_has_no_strain`.
P12 regression: M01's and M02's frozen test suites pass unmodified in this
checkout at the candidate revision.

## Frozen falsifier bites (each must FAIL LOUDLY on a TAMPERED COPY, named, then the copy discarded; the real module must stay green)

F1 density substitutes for stiffness: copy passive_response.py to the attempt
scratch, tamper k = rho*A/L0 (density-coupled), rerun P3+P8 against the copy:
both must FAIL (closed-form mismatch; density variance). The unmodified module
passes both. Recorded with the tamper diff and the captured failures.
F2 rotated fiber has no effect: tampered copy ignores the fiber axis
(E(theta) = E_fiber for all theta): P5 must FAIL on the copy (strict ordering
x(0) < x(45) < x(90) broken; ratio != 4.0). Input-side: a zero fiber axis in a
law document refuses `invalid_fiber_axis`; an axis of wrong norm refuses the
same code.
F3 passive material creates unexplained energy: tampered copy flips the
dissipation sign (energy creation); P6 must FAIL on the copy. The real module
must additionally refuse a synthetic trace with negative dissipation or
residual above tolerance with `unexplained_energy`.

## Frozen capture plan (before any frame exists; task_id SHORT form "M04")

Profile (read-only from registry card MAT2-M04): id material, kind motion,
views ["whole experiment at fixed distance", "orthogonal side and front",
"oblique close-up of the loaded interface"], clean_view_required true, five
diagnostic layers, 16+ camera fields per camera.

- Renderer: real 3D orthographic projection of the ACTUAL tetra mesh vertices
  displaced ONLY by the solver trace of protocol V (per-tick world vertices
  recomputed from the per-tick extension; painter's algorithm, depth-sorted,
  occlusion_mode depth_tested; quaternion wxyz camera-to-frame, forward -Z,
  up +Y, right-handed, coordinate_unit m). Motion is solver-driven: camera
  bookmarks are fixed; the geometry moves because the trace says so; no
  overlay-driven motion (no tweens, no authored interpolation).
- Views: (1) whole experiment at fixed distance — all five columns, full rig
  (supports + load arrows) inside the viewport with numeric margin proof;
  (2) orthogonal side and front — two declared viewports, same tick state;
  (3) oblique close-up of the loaded interface — 25 deg about world X onto the
  compliant column's loaded end: load arrow, gauge label, support visible,
  labeled vertex/triangle ids from ONE function (target and labels from the
  same selection), numeric force/extension captions from the trace.
- Diagnostic layers (all five, genuinely drawn): stable region/triangle/
  vertex ids; load force vector + per-triangle area-scaled shares on the
  loaded interface; rest wireframe vs current geometry + fiber axis arrows;
  support/contact state (pinned face, state "loaded" during ramp); per-tick
  ledger panel (tick, F, x, U, Q, W, ledger residual) and frame stamp.
- Clean rows: same camera, same tick, same state binding, zero diagnostics.
- Manifest: task_id "M04" (SHORT form), profile_id "material",
  tick_interval [0, 12], state binding kind "trace" (sha256 of
  evidence/experiment_trace.json as rendered), video locator per view,
  fixed_bookmark cameras with samples at both interval ends; validate with
  visual_capture.validate_manifest and the registry profile read read-only;
  load-path margin check (projected rig AABB inside viewport margins) recorded
  as numerical evidence for the "clipped load path" falsifier arm.
- Capture lives in the attempt workspace (capture-evidence-20260928/), not in
  the contribution; the contribution carries the display/trace artifacts the
  capture binds to.

## done_when clause map

| clause | execution |
|---|---|
| only the rigid, compliant and fiber-reinforced responses needed by the monkey | exactly three named profiles; arm bones -> rigid; tetra -> compliant (and fiber variants for the directional gate); plate -> fiber; no active/pressure/thermal response implemented; no tissue invented on the arm |
| declare constitutive equations, parameters, source or synthetic status | declaration table above, embedded in the law documents with per-parameter provenance strings |
| rest state | zero-load rest returns rest geometry, zero force/energy (P9); documents declare the rest state explicitly |
| damping | linear dashpot c = 6250 N*s/m, tau = 0.25 s, declared only on compliant_maxwell (Maxwell series); absent (null) elsewhere, never silently zero |
| valid strain range | [-0.30, +0.30] strain band, gate refuses outside before evaluation (P9); test loads stay inside (max 0.10 in E1, 0.1632 in protocol V) |
| independent load-extension, relaxation and rotated-fiber experiments meet preregistered limits | E1 (P3, P7), E2 (P4, P6), E3 (P5) — three separate runs, separate oracles, frozen numbers above |

## Honest boundary

Offline CPU-only material experiment executable over pinned M02 documents;
not the native engine, no GPU, no training, no runtime integration. The
Maxwell/Hooke/cos^2 laws are declared synthetic models (no source modulus for
monkey tissue is admitted in the graph); only geometry, masses and mesh data
are pinned heritage. Uniaxial gauge kinematics (affine stretch, pinned face)
is a declared experiment rig, not a general 3D constitutive solver. M01's law
vocabulary remains closed at pressure_deformation; passive laws therefore live
in the M04-owned document and the mapping into material_state.v1 laws rows is
recorded as future serial-integration work. Visual acceptance belongs to the
independent reviewer; validate_manifest is metadata structure only.

## Heritage citations (real pins, read and hashed before this freeze)

- B1 scratch law lineage (force-required law, d = F/(2*pi*R*H_soft)):
  docs/evidence/agent_fleet/MATTER_KERNEL/B1_PREREGISTRATION.md, sha256
  643e1cd8ec59ab7d4be91e5d1ca7c1de9e616d3fa567b664d0b5335fe333cc73 (pinned
  pressure = hardness; force must be known, never defaulted — reused here as
  "loads are declared, never inferred").
- B2 bonds-are-materials (capacity = strength x area):
  .../MATTER_KERNEL/B2_PREREGISTRATION.md, sha256
  4a4d4b7e1c495313f8c665b98025943b17642dc2f6322dd624fa9116371c600a (area-scaled
  capacity law; P7's area scaling is the same family).
- B3 tensile web/chain (same force in every link, minimum capacity fails):
  .../MATTER_KERNEL/B3_PREREGISTRATION.md, sha256
  36e112918cc40a8ebd67cc2e091bd32491980ed4e4a71fdec37609cce0a23cf1.
- B4 tension-only drape: .../MATTER_KERNEL/B4_PREREGISTRATION.md, sha256
  df306b31363ca97b376f4fffeefb82bf39e114eee4c466859aefb2c57c3f7053.
- Graph: concept.elasticity ("Select membrane/shell/bulk energy with thickness
  and material directions"), req.material_catalog (tendon = fiber_solid,
  bone = composite_solid), type.B15 (distributed tensile web).
- Schema/compiler lineage: MAT2-M01 material_state.py (unmodified validator,
  reused), MAT2-M02 compiled documents + mesh blob (hashes frozen above).
