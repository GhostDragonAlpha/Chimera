# Consumer migration map

The patch is additive at the kernel boundary: replace the paused candidate
`tools/elastic_foundation/units_contract.py` with `PROPOSED_units_contract.py`
and replace its test with `PROPOSED_test_units_contract.py`. Do not edit
`materials.py`, `law.py`, `geometry.py`, raw fixtures, manifests, or old result
JSON.

| Consumer | Current meaning | Migration |
|---|---|---|
| `tools/elastic_foundation/law.py` | Historical numerical surface kernel; duck-types `E/nu/h`, reads `lambda_bar/mu_bar/h` | No code change. New v1 adapter is its only physical-units caller. |
| `tools/elastic_foundation/materials.py` | Historical `ElasticMaterial2D`; comments label `E` Pa although kernel numerics omit `h` | Preserve behavior for fixtures. Record the correction append-only; do not pass this record out of the new physical API. |
| `battery.py`, `demo_sheet.py` | Synthetic dimensionless/legacy acceptance and demo | Keep numerical inputs and outputs unchanged. Label as historical synthetic surface-law paths when docs are next amended. |
| `make_fixtures.py`, `verify_fixtures.py`, `test_verify_fixtures.py` | Produce/verify frozen v1 legacy byte streams | Never route v1 fixtures through the physical adapter. Keep fixture hashes and exact outputs frozen. A future physical fixture needs a new fixture version. |
| `domain_audit.py` and `docs/THE_ELASTIC_DOMAIN_AUDIT.md` | Correctly exposes the old unit conflict | Keep historical result. The supplied append is only a future lead-owned recommendation because this file is outside the units task write scope. |
| `docs/evidence/elastic_foundation/DERIVATION.md` §12 and `GPU_HANDOFF.md` | Historical implicit-thickness contract and frozen GPU handoff | Preserve. Add a future append-only cross-reference saying these govern legacy v1 fixtures, while physical CPU calls use `elastic-physical-cpu/v1`. Do not change GPU fixture interpretation in this task. |
| `material_from_library()` | Refuses because repository material entries lack measured `nu` | Preserve refusal. Do not provide a default `nu` or fake a source. |
| paused `units_contract.py::compare_fixture()` | Reinterprets frozen fixture `E` as Pa and then calls a synthetic record whose `E` actually means N/m | Remove from the physical API. Frozen fixture verification remains with `verify_fixtures.py`; a physical comparison must receive separately declared E3d/nu/h sources. |
| all new CPU physical consumers | No safe path today | Construct typed provenance; call `admit_volumetric_v1()` or `admit_surface_v1()`; retain the returned `AdmittedMaterialV1`; then call `evaluate_physical_v1(rest, admitted, positions)` and consume unit-labelled result properties. |

No current source consumer outside the paused units candidate imports
`evaluate_physical`, `SurfaceContract`, or `contract`, so replacing that
unreviewed candidate does not require a compatibility alias. If a hidden or
downstream consumer appears during application review, map it explicitly to an
admitter rather than preserving raw-parameter evaluation that can lose the
admitted record.
