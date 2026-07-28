# aSolarSystem — matter added to 0 becomes a star and orbits

**Claim:** A cloud of matter added to the seed collapses under its own center of
gravity into a star with a few planets, and those planets' orbits obey Kepler's
third law — **unforced, never coded.**

## Math that closes
N-body accretion: softened gravity, inelastic mergers, torque-free gas drag.
Angular momentum is conserved as an honesty ledger: `orbital + spin + escaped = t0`.
Kepler's third law is *read back out* of the grown orbits' own winding periods
(`T² ∝ a³`), not imposed.

## Why (terminal → PHYSICS, measured)
Kepler's law EMERGES from the simulation: **slope 1.50, r² = 1.000.**
Star mass ~98%, 3–4 planets, eccentricity ~0.12, disk ~0.004°.
- Receipt: `Chimera/core/trainables/bigbang.py` (+ `bigbang_gpu.py`)
- Objective: `docs/objectives/bigbang*.json`
- Export: `--export-catalog → bigbang.systems.json` (each planet = one (m, a, e) triple)

## Outputs (handed DOWN to children) → outputs.json
The star's `g`, and for each planet a `(mass, semimajor_axis, eccentricity)` triple.
Every triple instantiates one `aPlanet/` child, which derives *its own* g from its
mass and radius. That g is what `walking` will eventually inherit — the seam that
makes the gait gravity-portable.

## Children
- `aPlanet/` — one (m, a, e) triple → g, ground, atmosphere, oceans  *(next to write)*
