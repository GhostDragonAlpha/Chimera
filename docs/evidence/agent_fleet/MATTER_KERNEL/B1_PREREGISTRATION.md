# B1 PREREGISTRATION — the scratch reference model

Rule 0: statement, prediction, falsifier — BEFORE implementation. No
measured actuals appear here; every number below is a PREDICTION derived
from cited constants.

## STATEMENT

A scratch is contact pressure pinned at the softer material's hardness:
the softer surface yields until the load-bearing area is just large enough
that pressure = H(soft); the harder body never yields because that pinned
pressure is below its own hardness. Groove depth follows from the tip
geometry alone once pressure is pinned.

## DERIVATION (from cited constants only)

- Hardness conversion: H (Pa) = HV x 9.80665e6 (1 kgf/mm^2 = 9.80665 MPa).
  Oak HV 4 -> 39.2 MPa. Hardened steel HV 640 -> 6.28 GPa. (constants.py)
- Spherical tip, radius R, pressed to depth d (d << R): projected
  load-bearing area A ~ pi * 2Rd.
- Load balance at pinned pressure: F = H_soft * pi * 2Rd
  => **d = F / (2 * pi * R * H_soft)** — depth linear in F, set by the
  SOFTER material's hardness and tip radius only.
- Tip groove: occurs only if pinned pressure (= H_soft) >= H_tip, i.e.
  only if the tip is not harder. For a hardened-steel tip (6.28 GPa) on
  oak (39.2 MPa): tip pressure is 160x below its hardness -> tip intact.
- Refusals (ordering law): a cut requires H_tip > H_plate. Rubber tip
  (0.5 HV) on oak (4 HV): refused, zero groove, reason recorded.
  Steel on hardened steel (equal): refused — no groove in either.

## PREDICTIONS (test bars, all with R = 1 mm round tip)

P1. Oak plate, F = 10 N: groove depth ~0.0406 mm (linear formula).
P2. Linearity: F = 20 N gives exactly 2x the 10 N depth.
P3. Monotonic: depth strictly increases across F = 1..100 N sweep.
P4. Tip intact: steel-on-oak leaves zero tip deformation, any F in range.
P5. Refusals: rubber-on-oak = zero groove + named refusal; equal-hardness
    steel pair = zero groove + named refusal.
P6. Force must be known: the API requires force in newtons; omitted force
    is a refusal, never a default.

## FALSIFIER

Any bar fails, OR the model ever cuts the harder member, OR depth is
non-monotonic or non-linear in force, OR a measured value contradicts the
cited hardness ordering. A failure here names the successor hypothesis
(per-tip-geometry calibration of the projected-area constant).
