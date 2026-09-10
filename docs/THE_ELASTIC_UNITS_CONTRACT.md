# Elastic units contract

**STATEMENT:** A 3-D Young modulus `E` in Pa and thickness `h` in metres
produce the 2-D surface modulus `E₂ = E·h` in N/m; the historical law remains
available only as `legacy_implicit_unit_thickness`.

**PREDICTION:** Doubling thickness doubles the physical surface modulus and
energy at fixed strain, while legacy mode remains unchanged and is visibly
labelled.

**FALSIFIER:** A physical conversion fails dimensional scaling, accepts
nonfinite/invalid material values, or silently treats legacy mode as physical.

`tools/elastic_foundation/units_contract.py` is an adapter and diagnostic. It
does not rewrite historical fixtures or the existing law. The physical mode
must be used before any 3-D material or GPU claim; legacy fixture verification
retains its recorded implicit-thickness semantics.

The versioned evaluator retains physical `h` when constructing the equivalent
2-D material, so `w_vol` remains a volume diagnostic. It requires structured
`{"kind": "synthetic"|"sourced", "source": ...}` provenance and rejects
overflow, nonnumeric, and missing provenance inputs.
