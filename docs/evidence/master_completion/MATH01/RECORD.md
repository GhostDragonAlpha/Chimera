# MATH-01 contract audit record

Task `math-contract-audit-01`, generation 1. This is a bounded preparatory
audit; it does not accept catalogue card MATH-01 or alter its dependencies.

## Source and commands

- Revision under review: `c0c84873056e69339dda85e3c16656cc5c33697c`.
- CPU command: `python tools/material_contract_checks.py`.
- No engine executable, GPU API, DYAD service, or HTTP runtime was started.

The command reports **32/32 PASS**. Its complete raw stdout/stderr, exit code,
Python version, source commit, and SHA-256 identities are preserved in
`RAW_CHECK_STDOUT.txt` and `RAW_CHECK_METADATA.json`; the earlier summary in
`RESULTS.json` is therefore corroborated by the raw run record. Its checks cover registered-family unit
conversion, nonfinite and negative values, provenance and derivation, material
frames, orthotropic matrix structure, and refusal at the execution boundary.
The captured summary is in `RESULTS.json`.

## Observed contract surface

`tools/material_contract.py` has the strongest existing typed boundary. It
contains a closed unit-family registry (`pressure`, `density`, `length`,
`energy_area`, `stiffness`, `fracture_toughness`, and `dimensionless`), refuses
unknown or cross-family conversions, rejects nonfinite conversion inputs and
outputs, and validates material records at construction. Its orthotropic path
checks a finite 3x3 orthonormal material frame and the declared Voigt coupling
convention. These are material-domain contracts, not a repository-wide
quantity/frame type system.

`ChimeraEngine/core/membranes.py:316-350` supplies local-normal `up_at()` and
float64 translation helpers (`to_local`, `to_parent`, `to_world`). The helpers
document local coordinates and SI metre scale, but `to_local`/`to_parent` only
translate by `origin`; they do not represent or apply an orientation matrix or
quaternion. `to_world` accumulates origins but likewise has no rotational frame
composition. This is a concrete frame-contract gap for nested rotated
membranes.

`ChimeraEngine/gravity.py:132-146` supplies `local_frame()` and constructs a
right/forward/up basis from gravity, including a pole reference-axis switch.
The function returns arrays without a named frame object, unit metadata,
handedness assertion, or round-trip transform operation. It is a useful frame
producer, not a general coordinate contract.

`WorldModel/physics/scaled_coordinate_precision.py` describes a global float64
and local float32 scheme, but its local conversion is decimal seven-significant-
digit rounding rather than an actual float32 cast, and its result reports
`"simulation_status": "verified"` without an error bound or invariant check.
It should not be treated as evidence that the MATH-01 numerical contract is
closed.

`ChimeraEngine/core/sdf_grid.py:53-62` converts world positions to voxel keys
using a scalar `voxel_size`; it has no explicit frame identity and assumes the
input is already in the grid's world frame. `ChimeraEngine/docs/HOW_TO_MAKE_A_THING.md:96-109`
declares metres and a derived `g_sim` conversion in the worked `.chimera`
format, but this is documentation convention rather than a typed parser-level
quantity contract.

## Native presentation and elasticity corrections

The native membrane path is an explicit presentation mapping, not a general
world-unit conversion. `ChimeraEngine/engine/engine.cpp:4090-4095` copies the
uploaded f32 positions directly into a four-float storage layout. The shader
`ChimeraEngine/engine/shaders/membrane_demo.comp:143-166` maps each accepted
position as `(x, z + lift_m, -y)` and applies the same component permutation to
the face normal; its push constant declares `lift_m` as an engine-Y
presentation lift and `scale` as reserved `1.0` (`:63-70`). The native upload
response in `ChimeraEngine/engine/main.cpp:544-547` reports `unit: J/m^2` and
`wu_to_m: 1.0`, while `engine.cpp:4441-4459` records the same value in the
material snapshot. These lines establish the B2 demo's declared identity
mapping and axis permutation. They do not establish a general conversion API,
runtime validation of arbitrary `wu_to_m`, or a frame identity for other
meshes; those remain **OPEN**.

The elastic assumptions inspected are dimensionally explicit inside their
individual modules: `ChimeraEngine/core/hertz.py:73-79` uses
`c_p = sqrt((B + 4G/3)/rho)` for a solid, `:99-113` uses Hertz/Mindlin force
and stiffness expressions, and `ChimeraEngine/core/viscoelastic.py:57-73`
declares dimensionless relaxation strength and `tau = a^2/D`. However, these
functions accept plain floats and do not carry unit or frame metadata at their
boundaries. The current branch has no `tools/elastic_foundation/` source tree
or `docs/evidence/elastic_foundation/` directory to audit; that linked elastic
catalogue work is therefore **OPEN / absent from this checkout**, with no
completion inferred.

## Result and follow-on envelope

The preregistered prediction is **supported**: the repository has several
useful local conventions and material guards, but no single typed quantity and
frame boundary proving reversible transforms across the inspected callers.
The falsifier did not fire. This is an audit finding, not a physics or runtime
claim.

A follow-on implementation should remain CPU/docs scoped and derive, before
coding, the minimum quantity dimensions, frame identity/handedness, transform
composition rules, and round-trip/error gates. It should include independent
reference calculations and negative controls for unknown units, cross-family
conversion, nonfinite values, rotated nested frames, and mismatched frame
identity. Existing material gates and frozen constants must remain unchanged.
