# theGround — the planet's surface settles into a walkable floor

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **[docs/THE_LAW.md](../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

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
