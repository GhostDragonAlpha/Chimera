# Read-only units design repair report — 2026-09-10

Artifact root:
`E:/ChimeraWork/evidence/units_design_sol_20260910`

Inspected source: `E:/ChimeraWork/slot-03`, branch
`astra/tasks/elastic-units-contract-01`, HEAD
`accd15b61d7ac3805edfc36535ef99de121baf65`. The worker checkout's tracked
source was not changed. Its status before and after retained the same existing
untracked units candidate/evidence plus existing Saved/dyad logs.

## Outcome

The proposal supplies a sealed, versioned public physical record; separate 3-D
and surface admitters; typed synthetic/sourced provenance with no defaults; a
private duck-typed view for the unchanged kernel; a result retaining both the
admitted record and full `Evaluation`; unit-labelled outputs; coefficient and
output validation; an independent rational oracle; full scaling/equivalence
checks; and implementation-seam mutation controls.

The old candidate is retracted as sufficient evidence. Its two tests pass even
when all vertex forces and `w_vol` are replaced with zero. The retained
counterexample is
`E:/ChimeraWork/evidence/units_parent_zero_mutation_20260910.json`, SHA-256
`5dc302d14abe5092908a1684fee509608fe03cc87ce0083e78570ca49c61e44f`.

## Executed command

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:CHIMERA_UNITS_REPO='E:\ChimeraWork\slot-03'
$env:CHIMERA_UNITS_CANDIDATE='E:\ChimeraWork\evidence\units_design_sol_20260910\PROPOSED_units_contract.py'
python E:\ChimeraWork\evidence\units_design_sol_20260910\PROPOSED_test_units_contract.py -v
```

Result: **12 tests run, 12 passed, 0 failed, 0 errors** in 0.016 s. A separate
`py_compile` of both proposed Python files also completed successfully.

Measured fixed-oracle values:

| quantity | measured | absolute error from rational oracle | derived bound |
|---|---:|---:|---:|
| `U` [J] | `0.03134065934065933` | `1.3877787807814457e-17` | `gamma(64)*713/22750 = 4.4547e-16` |
| max full vertex-force component error [N] | — | `5.551115123125783e-17` | `gamma(64)*498/2275 = 3.1104e-15` |
| max `w_vol` component error [J/m3] | — | `1.4210854715202004e-14` | `gamma(64)*2852/91 = 4.4538e-13` |

`h -> 2h` measured energy ratio `2.0`, maximum full-force delta from `2F`
`0.0 N`, and maximum `w_vol` delta `0.0 J/m3`. The volumetric and explicit
surface representations produced bit-equal energy and a bit-equal full vertex
force array when given the same stored `E2`, `nu`, and `h`.

## Falsifier table

1. Rational full-output oracle -> **PASS** (errors above; all below preregistered `gamma(64)` bounds).
2. Representation equivalence and exact thickness accounting -> **PASS** (bit-equal representations; `2.0`, `0.0 N`, `0.0 J/m3` thickness measures).
3. Actual seam mutants -> **PASS** (omitted `h`, doubled `h`, wrong `w_vol`, dropped provenance, and retained zero-force/zero-`w_vol` mutant all killed).
4. Named refusal matrix -> **PASS** (numeric/bool, nonfinite, sign/range, surface overflow/underflow, Lamé overflow/underflow/subnormal/cancellation, direct construction, malformed/nonfinite/dimensionally inconsistent output).
5. Historical fixture immutability/numerics -> **PASS** (`trisingle` SHA-256 `2cb83077485447909e22e4322152bdfd8baa835f43dea973604a111024035ded`; `patch` SHA-256 `73aaad4a030e7a60b418b07f819a61abe6ac4344c97fee64e23aaa35e7533fd7`; both unchanged legacy energies and complete force arrays matched exactly).

## Files written

| file | bytes before this report | SHA-256 before this report |
|---|---:|---|
| `MEMBRANE.md` | 4213 | `7901b4260d0fa0c85f02e43d0284d5b0da7fcb24a80148f603f9324ac1704850` |
| `PROPOSED_units_contract.py` | 22776 | `51ab9d0d0567a62ded7979cd5ea0f8fee31ae60506beb23d6a1132db2c30c2f4` |
| `PROPOSED_test_units_contract.py` | 18611 | `3eed80aaa1353b0d8afe68c7bb6db89137baa6cd8cc4a2047a23364733240da1` |
| `PROPOSED_V1_CORRECTION.md` | 5810 | `d693f234aec2df7334ffcdbbcef354ec0ecc60be43705890b71335e8db000ca1` |
| `MIGRATION.md` | 3091 | `5b625d5f3bfbd4247618f86b4c62233fccf02abe921f27122ee659a21958ed15` |
| `PATCH_PLAN.md` | 1473 | `f7e7cbe7e0321973373b16ff4e0b9e2c0db1036d558d030ab908c12b8a777324` |
| `PROPOSED_DOMAIN_AUDIT_APPEND.md` | 969 | `b3ef69dc9cac6cae28e4b6a2cc2c3428426ed10f1694bc7feaf039b8bf118b2d` |

The hashes identify the tested state before adding this report. Recompute them
after review if any proposal file changes.

## Falsified/retracted

- The initial `2/2` scaling-only gate is retracted as sufficient because the
  retained zero-output mutation passes it.
- A public `SurfaceContract` directly constructible with mutually inconsistent
  `E3d`, `h`, and `E2` is rejected. The replacement record is factory-sealed.
- Creating `ElasticMaterial2D(E=E3d*h, ...)` and returning only its Evaluation
  is rejected because it labels N/m as Pa and discards provenance.
- Reinterpreting frozen fixture field `E` as a sourced 3-D modulus is rejected;
  those fixtures remain historical legacy numerical evidence.

## Open items

- Root/worker review and paste-back in the owned task worktree.
- After paste-back: normal package test, full elastic battery, and fixture
  verifier on a temporary copy. Those were not run against an unapplied
  private proposal.
- `PROPOSED_DOMAIN_AUDIT_APPEND.md` is a recommendation for a future lead-owned
  docs task. It is outside this worker's units-task write scope.
- GPU implementation, real-material certification, unrestricted finite-strain
  validity, bending, fracture, contact, and anisotropy remain unbuilt/unmeasured.

## Boundary hits

- The worker checkout was read-only for this assignment, so no patch was
  applied, committed, pushed, or submitted from slot 03.
- `docs/THE_ELASTIC_DOMAIN_AUDIT.md` is outside the task write scope; its
  proposed append remains private and unapplied.
- No GPU, engine, DYAD, material library mutation, or live control session was
  used.
