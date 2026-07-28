# theGround — the planet's surface settles into a walkable floor

**Claim:** Regolith under gravity settles to its own angle of repose and stops. That
settled surface is the negative space the body stands on, and its repose angle is
exactly the friction the foot will grip.

## Math that closes
- **Repose = friction:** a granular pile is stable up to the angle φ where
  `tan(φ) = μ_s`. The pile's emergent repose angle IS the surface friction coefficient
  it hands to contact: `μ_s = tan(φ) ≈ tan(40°) ≈ 0.84`.
- **Halting:** cost ∝ change, not world size — a settled pile is a computation that
  has stopped. Stochastic sandpile, quenched per-site thresholds, cohesion freezing.

## Why (terminal → PHYSICS, measured)
Emergent repose 40.03° ± 1.55, inside the researched lunar-regolith band
(Carrier / Lunar Sourcebook); unsettled_worst = 0 (it halts). Receipt:
`Chimera/core/trainables/granular.py` (+ `core/matter_gpu.py`, the GPU shaker),
`docs/objectives/granular*.json`.

## Outputs (handed DOWN) → outputs.json
The surface normal (local up), the friction coefficient `μ_s = tan(repose)`, slope,
and "solid contact exists here."

## Children
- `aBody/` — a body stands on this floor
