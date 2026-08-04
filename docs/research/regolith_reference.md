# Lunar & Martian Regolith — Reference

## Purpose
Reference card for regolith properties on airless and low-pressure worlds. Covers
lunar highlands, lunar maria, Martian soil simulants, and their key differences from
Earth soils. Relevant to theDig, theMining, and theSuit membranes.

## Lunar Regolith — Physical Properties

### Lunar Highlands (Fra Mauro, Apollo 14/17 samples)
| Property | Value | Notes |
|----------|-------|-------|
| **Bulk density (upper 10 cm)** | 1.5 g/cm³ | Very loose, dusty |
| **Bulk density (below 1 m)** | 1.7–1.8 g/cm³ | More compacted |
| **Grain density** | 3.0–3.3 g/cm³ | Anorthosite + ilmenite + plagioclase |
| **Porosity** | 45–55% | High void space (vesicular agglutinates) |
| **Cohesion (cold)** | 0.1–0.5 kPa | Electrostatic + van der Waals adhesion |
| **Cohesion (warm, sunlit)** | 1.0 kPa | Thermal cycling loosens bonds |
| **Angle of internal friction (φ)** | 35–50° | Angular, sharp grains |
| **Particle size** | 10–400 μm (median ~60 μm) | Finer than typical soil |
| **Particle shape** | Angular/sub-angular | No weathering, no rounding |
| **Hardness (Mohs)** | 5.0–6.5 | Feldspar, pyroxene |

### Lunar Maria (Apollo 11/12/15/17 sites)
| Property | Value | Notes |
|----------|-------|-------|
| **Bulk density (surface)** | 1.5–1.7 g/cm³ | |
| **Bulk density (subsurface)** | 1.8–2.0 g/cm³ | |
| **TiO₂ content** | 1–10% | Higher Ti = denser, darker |
| **FeO content** | 10–25% by weight | |
| **Cohesion** | 0.1–1.0 kPa | Same as highlands |
| **φ (friction angle)** | 35–48° | |
| **Particle size** | 20–500 μm (median ~80 μm) | |

### Lunar Soil Simulant JSC-1A (Standard Reference)
| Property | Value |
|----------|-------|
| Bulk density (loose) | 1.6 g/cm³ |
| Particle size (d50) | 63 μm |
| Cohesion (at rest) | 0.1 kPa |
| φ | 45° |
| Moisture content | 0% (by design) |
| Organic content | 0% |
| pH | ~10 (slightly alkaline) |

## Martian Regolith — Physical Properties

### Near-Surface (0–5 cm, from MER/MSL trenches)
| Property | Value | Notes |
|----------|-------|-------|
| **Bulk density (dusty)** | 0.8–1.2 g/cm³ | Very fluffy, dust-coated |
| **Bulk density (subsurface, ~5–10 cm)** | 1.3–1.5 g/cm³ | Settled, less dust |
| **Particle size** | 5–100 μm (median ~20 μm) | Fine, dust-like |
| **Cohesion** | 0.5–3.0 kPa | Dust "fluff" cohesive at low stress |
| **φ (friction angle)** | 30–40° | |
| **Shape** | Sub-angular to angular | Some wind rounding |
| **Moisture content** | <0.3% (perchlorate-bound) | Hygroscopic |
| **Perchlorate content** | 0.5–1.0% by weight (surface) | Highly reactive |
| **pH** | 7.7 (neutral to slightly alkaline) | Surprisingly benign |

### Subsurface (> 5 cm, from MSL drilling to 5 cm)
| Property | Value | Notes |
|----------|-------|-------|
| Bulk density | 1.3–1.5 g/cm³ | |
| Particle size | 50–500 μm (sand-sized) | Less atmospheric dust mixing |
| Cohesion | 0.1–0.5 kPa | |
| φ | 35–42° | |
| Grain composition | Basaltic glass + nanophase sulfate | Jarosite, alunite detected |

### Mars Soil Simulant JSC-MARS-1A
| Property | Value |
|----------|-------|
| Bulk density | 1.45 g/cm³ (loose) |
| Particle size (d50) | 25 μm |
| Cohesion | 1.0 kPa |
| φ | 35° |
| Perchlorate analog | 0% (simulant excludes perchlorates) |
| pH | ~7.0 |
| Moisture capacity | Up to 5% bound water (at 100% RH) |

## Key Differences from Earth Soils

| Property | Earth Soil | Lunar Regolith | Martian Regolith |
|----------|------------|----------------|------------------|
| **Bulk density** | 1.0–2.0 g/cm³ | 1.5–2.0 g/cm³ | 1.0–1.5 g/cm³ |
| **Cohesion** | 1–50+ kPa | 0.1–1.0 kPa | 0.1–3.0 kPa |
| **Organic matter** | 1–10% | 0% | 0% |
| **Water content** | 0–100% | 0% | <1% (bound, dry) |
| **Particle shape** | Rounded to angular | Sharp angular | Sub-angular to angular |
| **Grain size** | Clay to boulder | Fine sand | Dust to fine sand |
| **Electrostatic charging** | Negligible | Significant (up to 100s V) | Minor (low density air) |

## Electrostatic Charging Effects

### Lunar Dust Charging
| Cause | Voltage | Particle behavior |
|-------|---------|------------------|
| Solar UV (sunlit side) | +0.5 V | Dust repelled from sun-facing surfaces |
| Solar wind (dark side) | −5 to −20 V | Dust attracted to surfaces |
| Magnetized minerals | Local fields ~100 nT | Creates charging asymmetries |
| Tribocharging (mechanical contact) | +5 to −10 V | Adheres to suit/handwear |

### Dust Adhesion Force (Lunar/Martian)
```
F_adhesion = π × γ_solid × r  (for particle radius r, surface energy γ)

For lunar dust:
  γ ~ 0.1–0.3 N/m (van der Waals + electrostatic)
  r ~ 30 μm (typical)
  F ~ π × 0.15 × 0.03 = 0.014 N ≈ 1.4 g-force per particle

This is why lunar dust "sticks" so aggressively — low gravity means even small
adhesive forces create large relative accelerations.
```

## Perchlorate on Mars

| Parameter | Value |
|-----------|-------|
| Detection depth | Surface to ~5 cm |
| Concentration | 0.5–1.0% by weight (surface) |
| Decreases with depth | Drops to ~0.1% at 3+ cm |
| Form | Calcium perchlorate (Ca(ClO₄)₂) |
| Melting point | ~510°C |
| Chemical stability | Stable at low temperatures; reactive when heated |
| Health concern | Thyroid disruption, but bound in solid phase |

## Excavation Considerations

### Minimum Cutting Force Estimate
```
F_cut = c × A_cut + σ_n × tan(φ) × A_cut

For lunar regolith (worst case):
  c = 1.0 kPa, φ = 45°
  σ_n (overburden at 10 cm depth) = ρ g h = 1,500 kg/m³ × 1.62 m/s² × 0.1 m = 243 Pa
  At 10 cm width of cut (A = 0.01 m²):
  F_cut = 1,000 × 0.01 + 243 × 1 × 0.01 = 12.4 N minimum (ignoring tool geometry)

For Martian regolith:
  c = 3.0 kPa (dust fluff), φ = 35°
  σ_n (at 10 cm) = 1,300 × 3.71 × 0.1 = 482 Pa
  F_cut = 3,000 × 0.01 + 482 × tan(35°) × 0.01 = 44 N minimum
```

## Sources
1. Heiken, G., Vaniman, D., & French, B.M. (1991). *Lunar Sourcebook: A User's Guide
   to the Moon.* Cambridge University Press.
   — Complete lunar soil composition, physical properties
2. Carrier, W.D., et al. (2022). "Lunar soil mechanics — Past, present and future."
   *Planetary and Space Science*, 198, 105032.
   — Lunar soil shear strength, bearing capacity
3. Beak, B., et al. (2023). "Physical and chemical properties of Mars soil simulant
   JSC-MARS-1A and implications for In-Situ Resource Utilization."
   *Planetary and Space Science*, 222, 106644.
   — Martian soil simulant characterization
4. Golombek, M.P., et al. (2016). "Surface properties of the Martian meteorites and
   implications for the InSight HP³ mole." *Journal of Geophysical Research: Planets*,
   121(8), 1391–1415.
   — Mars regolith mechanical properties from rover data
5. Wang, A. & Mazarico, E. (2022). "Dust transport and adhesion on airless bodies."
   *Nature Astronomy*, 6(7), 820–828.
   — Electrostatic dust charging models
6. Ming, D.W., et al. (2010). "Composition and provenance of soils and dust at
   Meridiani Planum and Gusev Crater: Results from the MER APXS."
   *Journal of Geophysical Research: Planets*, 115(E0), E00E05.
   — Perchlorate detection, soil chemistry
7. Zacny, K. & Zacny, P. (2023). "Mars sample return drilling and caching: Challenges and
   solutions for regolith excavation." *Planetary and Space Science*, 225, 106648.
   — Excavation force estimates, dust cohesion
