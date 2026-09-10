# Elastic physical CPU contract v1 — corrective record

This is proposed as a **new append-only evidence file** at
`V1_CORRECTION.md`. It does not replace or
rewrite the earlier preregistration, results, raw JSON, fixture manifests, or
fixture bytes.

## Historical state retained

At `2026-09-10T19:23:52.3259860Z`, the paused slot-03 candidate was captured as:

| path | bytes | SHA-256 |
|---|---:|---|
| `tools/elastic_foundation/units_contract.py` | 4538 | `4c18db0451aa59bdc379bfb0ce652608036e582609656107c8060d7f8cc6d759` |
| `tools/elastic_foundation/test_units_contract.py` | 1314 | `4fa879868ce4accddb8eed1d0708a3ce039d4e251868e05f9b291663660f63fa` |
| `docs/THE_ELASTIC_UNITS_CONTRACT.md` | 1112 | `574989739db6094d03a01b7d4d992663cee86ae703bcf8b97ee682b231b0f78f` |
| `docs/evidence/elastic_units_contract/PREREGISTRATION.md` | 662 | `8ccf6ff44b918a729495d1d5c847b574bcf541e9968a7d33d46ea1c2f0bcb4f5` |
| `docs/evidence/elastic_units_contract/RESULT.md` | 870 | `644a7d9693a43f2f60856de15a71d283905637be190a5a759e61a6f23970d1bc` |

Those files record the initial attempt. They are not retroactively described as
this correction's preregistration. The original two tests passed, but the
retained zero-force/zero-`w_vol` implementation mutation also passed them.
That counterexample is preserved at
`E:/ChimeraWork/evidence/units_parent_zero_mutation_20260910.json`, SHA-256
`5dc302d14abe5092908a1684fee509608fe03cc87ce0083e78570ca49c61e44f`.

## Corrected dimensional boundary

The unchanged historical kernel is a numerical surface-law implementation.
Its compatibility protocol happens to call the modulus field `E`, but for a
dimensionally physical evaluation the value at that private boundary is
`E2 = E3d*h` in N/m. The new public record never labels that value Pa.

```
E3d [Pa] * h [m] = E2 [N/m]
lambda2 = E2*nu/(1-nu^2) [N/m]
mu2 = E2/(2(1+nu)) [N/m]
Wbar [J/m2]
U = sum(A0*Wbar) [J]
force = -dU/dx [N]
w_vol = Wbar/h [J/m3]
```

`admit_volumetric_v1()` performs the multiplication once.
`admit_surface_v1()` accepts the already reduced value and performs no
thickness multiplication. Both retain physical `h` because the unchanged
kernel uses it solely for `w_vol`. `evaluate_physical_v1()` returns a
`PhysicalEvaluationV1` that retains both the admitted material and the complete
kernel `Evaluation` while exposing unit-labelled accessors.

The public admitted record has two sealed construction routes. Direct
construction is refused because it could make its stored representation and
derived coefficients inconsistent. A private `_KernelMaterialView` is the only
object where the historical `E` name carries an N/m value.

## Provenance boundary

`SyntheticCoefficientProvenance(declaration_id, purpose)` explicitly says that
the values exist for a synthetic test. It has no fabricated `source` field.

`SourcedCoefficientProvenance` requires three `SourceReference(uri, locator)`
records: one each for modulus, Poisson ratio, and thickness. This establishes
that the caller declared structured provenance and keeps it attached to the
admitted result. The adapter does **not** independently verify that a citation
is accurate, that measurements apply to the represented specimen, or that a
real material is certified.

`material_from_library()` remains a named refusal because the current library
does not provide Poisson ratio. The v1 interface supplies no default Poisson
ratio and does not turn a modulus-only library entry into an admitted material.

## External coefficient/thickness foundation

A.F. Bower's *Applied Mechanics of Solids* gives the isotropic plane-stress
matrix as `E/(1-nu^2)` times the usual `[1, nu; nu, 1]` normal block and
`(1-nu)/2` engineering-shear entry:
https://solidmechanics.org/Text/Chapter7_2/Chapter7_2.php (section 7.2.4).

The shell chapter writes volume integration as a mid-plane integral plus an
integral through `[-h/2,h/2]`, and its membrane strain-energy term carries a
leading factor `h`:
https://solidmechanics.org/Text/Chapter10_5/Chapter10_5.php (sections 10.5.8 and
10.5.10). These sources support the plane-stress coefficient and thickness
reduction only. They are not evidence that this STVK law is accurate at
unrestricted finite strain.

## Corrected gate and measured result

The preregistration for this correction is the contemporaneous `MEMBRANE.md`
in the private review artifact. Its independent rational oracle uses a
non-unit `h=1/500 m` and predicts nonzero full outputs:

```
U = 713/22750 J
w_vol = 2852/91 J/m3
forces = [[ 498/2275, -228/2275, 0],
          [-498/2275,          0, 0],
          [         0,  228/2275, 0]] N
```

Acceptance of the fixed normal-arithmetic oracle uses
`gamma(64)=64*eps/(1-64*eps)`, derived before execution from a conservative
operation count. Admitted Lamé coefficients that are zero from underflow or
subnormal are refused by name (with the exact `nu=0` value of `lambda2=0`
remaining valid); this proposal does not claim a normal-relative-error bound
over arbitrary finite inputs or subnormal output regimes. The test also checks all complete thickness
scaling fields, exact representation equivalence, named refusals, and frozen
legacy bytes/numerics. It kills implementation mutations that omit thickness,
apply it twice, return wrong `w_vol`, discard provenance, or return zero forces
and zero `w_vol`.

The private candidate run result and hashes belong in its `REPORT.md`; they are
not a project acceptance verdict until reviewed and applied in the owned task
worktree.

## Honest limit

This proposal certifies only the dimensional CPU adapter against its stated
normal-arithmetic synthetic oracle and consistency gates. It does not add a GPU implementation,
modify the legacy law, migrate frozen fixtures, or certify a real material.
