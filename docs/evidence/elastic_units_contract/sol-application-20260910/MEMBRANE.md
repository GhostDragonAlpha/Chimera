# Elastic physical CPU units v1 — preregistration

Recorded before the candidate implementation and before its tests were run on
2026-09-10. The existing `units_contract.py`, its two tests, and its evidence
were inspected first; those are historical attempts, not evidence for this
prediction.

## Statement

A versioned CPU boundary can admit either a three-dimensional Young modulus
`E3d` in Pa plus thickness `h` in m, or an already reduced surface Young
modulus `E2` in N/m plus the same physical thickness, and feed the unchanged
STVK kernel exactly one surface reduction. Both representations describe the
same material when `E2 = E3d*h`. The admitted public record retains its input
representation, units, physical thickness, and typed synthetic or sourced
coefficient provenance; the private compatibility view alone exposes the old
kernel field name `E` with the documented N/m meaning.

## Derivation and prediction

For dimensionless Green strain,

```
E2 = E3d h                                      [Pa m = N/m]
lambda2 = E2 nu/(1-nu^2)                       [N/m]
mu2 = E2/(2(1+nu))                             [N/m]
Wbar = 1/2 lambda2 tr(epsilon)^2
       + mu2 tr(epsilon^2)                     [N/m = J/m^2]
U = sum_f A0_f Wbar_f                          [m^2 J/m^2 = J]
force = -dU/dx                                 [J/m = N]
w_vol = Wbar/h                                 [J/m^3]
```

Thus `h` occurs exactly once in the 3-D-to-surface admission and once as a
division used only to recover the volume diagnostic. An explicit surface input
does not multiply by `h` on admission.

For the right reference triangle `(0,0),(1,0),(0,1)`, current diagonal map
`diag(6/5,4/5)`, `E3d=1000 Pa`, `h=1/500 m`, and `nu=3/10`, the independent
rational oracle predicts:

```
U = 713/22750 J
w_vol = 2852/91 J/m^3
vertex forces = [[ 498/2275, -228/2275, 0],
                 [-498/2275,          0, 0],
                 [         0,  228/2275, 0]] N
```

The float64 comparison budget is `gamma(64) = 64*eps/(1-64*eps)` times a
declared component scale. Sixty-four rounded operations exceed the longest
single-triangle coefficient/strain/stress/force path (under 32 elementary
operations, including the two 2x2 products); the factor of two covers the
independently rounded rational-to-float oracle. Zero expected components use
the largest nonzero oracle component as their absolute scale. No NumPy default
tolerance participates.

Two admitted representations constructed with the *same stored surface value*,
Poisson ratio, and thickness predict bit-identical complete kernel evaluations.
At fixed `E3d`, replacing `h` by `2h` predicts `2U`, twice every corner and
vertex force component, twice `Wbar`, and unchanged `w_vol`, within the same
derived `gamma(64)` budget.

## Falsifiers named before the run

1. Any rational-oracle energy, full vertex-force array, or `w_vol` component
   exceeds `gamma(64)` at the non-unit thickness above.
2. The equivalent 3-D-plus-thickness and explicit-2-D admissions differ in any
   complete evaluation field, or `h -> 2h` violates the stated full-array laws.
3. Any actual seam mutant that omits `h`, applies `h` twice, returns the wrong
   `w_vol`, or drops admitted provenance survives the tests.
4. Nonnumeric/bool, nonfinite, nonpositive, out-of-range Poisson ratio,
   surface-product overflow/underflow, Lamé overflow/underflow or catastrophic
   Lamé cancellation, malformed/nonfinite output, or dimensional-output
   mismatch lacks its preregistered machine-readable refusal.
5. The two frozen v1 fixture byte hashes change, or the unchanged legacy API no
   longer reproduces the frozen energy and full force arrays exactly.

## Scope and honest limits

This is a dimensional CPU boundary for the already implemented isotropic STVK
membrane. It does not certify a real material, finite-strain suitability,
bending, fracture, contact, anisotropy, a GPU port, or the historical fixtures
as physically dimensioned. The sourced constructor requires explicit source
references for modulus, Poisson ratio, and thickness; it does not fabricate
missing sources or make `material_from_library()` succeed when the repository
still lacks a measured Poisson ratio.
