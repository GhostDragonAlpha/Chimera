# aPlanet — one (m, a, e) triple becomes a world with gravity and a climate

**Claim:** A single planet triple handed down from aSolarSystem becomes a world with
a surface gravity, an atmosphere it can or cannot keep, oceans or ice, and a
temperature gradient from core to surface — and the habitable band is not placed, it
EMERGES from where the numbers land.

## Math that closes
- **Gravity (Newton):** `g = G·M / R²`, with R from a mass–radius relation. g is the
  first thing this membrane owns, and the first thing it hands down.
- **Climate (researched effective laws):** equilibrium temperature `T_eq` from
  (a, luminosity, albedo); atmosphere retention by the Jeans escape criterion (depends
  on g); greenhouse + moist-greenhouse limit; condensation → oceans; interior heat →
  core-to-surface gradient; ice-albedo feedback damped to a fixed point.

## Why (terminal → PHYSICS, measured)
Every catalog system independently resolved hot_rock → ocean → frozen; the habitable
zone EMERGED, unplaced. Learned constants landed on the literature: moist-limit
352.8 K (Kasting ~340–350), Jeans 5.5 (lit ~6), g-exponent 0.585 (Venus–Earth
bracket). Receipt: `Chimera/core/trainables/planet.py`, `docs/objectives/planet*.json`.
g itself is elementary Newtonian mechanics — true in an empty universe.

## Outputs (handed DOWN) → outputs.json
`g_surface` (the number walking's Froude law inherits), R, T_surface, atmosphere,
water state.

## Children
- `theGround/` — the planet's surface settles into walkable regolith
