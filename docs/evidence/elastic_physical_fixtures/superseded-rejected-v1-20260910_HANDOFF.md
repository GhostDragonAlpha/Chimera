# Elastic physical fixture handoff

Status: CPU reference prerequisite complete; no GPU claim.

`tools.elastic_foundation.physical_fixtures` reads the immutable v1 `.npz` records from
`docs/evidence/elastic_foundation/fixtures/v1/run_20260908T231140Z`. `load_fixture()` validates
shapes, finite numeric fields, material scalars, CSR dtypes, and records the source SHA-256.
`evaluate_fixture()` admits the explicit synthetic E [Pa], h [m], and nu through
`units_contract`, then evaluates the frozen float32 position stream in float64. The result
contains the complete per-face corner force tensor, gathered vertex force array, energy, and
volume density. `write_reference()` refuses an existing output path.

The packet preserves the historical fixture's implicit-unit legacy answers as expected arrays;
those bytes are not rewritten. Physical h scaling is checked independently: h and 2h double
energy, every force component, and surface stress while leaving w_vol and deformation tensors
unchanged. The two representations and provenance remain governed by
`THE_ELASTIC_UNITS_CONTRACT.md`.

The packet is a CPU reference for a future consumer. Binary32 inputs and binary64 references
are labelled separately. No f32 tolerance is invented here; GPU acceptance remains open and
must satisfy `GPU_HANDOFF.md` Stage C against both fixtures, including flags and CSR gather.

Actual mutation controls in `test_physical_fixtures.py` alter one force component, energy, and
finite status; each fails the full-array gate. Historical fixture hashes are checked before
comparison. Future readers must preserve the source hash and reject nonfinite/malformed data.
