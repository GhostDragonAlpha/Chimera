# elastic-units-contract-01 result

`python -m tools.elastic_foundation.units_contract --fixture <frozen-trisingle>`
evaluates the complete frozen geometry/current pose through the physical
equivalent evaluator and records full energy/force arrays in
`evaluator-final.json`. Physical `h` to `2h` scaling is tested separately;
legacy mode remains explicitly labelled. Overflow and nonnumeric inputs refuse
as `surface_modulus_overflow` and `numeric_material_required`. Source hash:
`09fcca05b1a8da186be9959ba4706fb9cd6fc09b` (initial adapter).

The versioned physical evaluator now preserves `h` in the law call, compares
full force arrays componentwise at `h` and `2h`, keeps `w_vol` equal, and
requires structured synthetic/sourced provenance. Overflow and nonnumeric
inputs refuse by name. Unit tests pass 2/2; raw evaluator output is retained
in `evaluator-v2.json`.
