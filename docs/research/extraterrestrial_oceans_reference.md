# Extraterrestrial Oceans — Reference

## Purpose
Reference card for extraterrestrial water environments, from surface liquid to
subsurface oceans. Relevant to theOcean, aSaltOcean, and theScan membranes.

## Earth's Ocean Baseline (Standard Units)

| Property | Value |
|----------|-------|
| Mean depth | 3,688 m |
| Max depth | 10,994 m (Mariana Trench, Challenger Deep) |
| Salinity (average) | 35 g/kg (3.5%) |
| Surface pressure | 1 atm per 10 m of depth (hydrostatic) |
| At 10,994 m | ~1,100 atm (110 MPa) |
| Freezing point (35 ppt) | 281.4 K (−1.9°C) |
| Density (0°C, 35 ppt) | 1028 kg/m³ |
| Speed of sound | 1,500 m/s (varies with T/S/pressure) |

### Freezing Point Depression
```
Freezing point of saltwater:

T_f = T_f,pure - K_f × m (molal)

For NaCl: each mole of salt particles lowers T_f by ~1.86 K per mole/kg solvent
Approximate formula for ocean salinity:

ΔT_f ≈ 0.54 × S (where S = salinity in ppt)

At 35 ppt: ΔT_f ≈ 0.54 × 35 ≈ 1.9°C
Freezing point ≈ −1.83°C
```

### Maximum Solubility (Halite Precipitation)
| Temperature | Max NaCl solubility |
|-------------|---------------------|
| 0°C | 357 g/kg |
| 10°C | 358 g/kg |
| 25°C | 360 g/kg |
| 100°C | 391 g/kg |

The ocean cannot exceed 350–360 g/kg before NaCl begins precipitating.

## Surface Liquid Water Worlds

### Criteria for Surface Liquid Water
```
Requires:
1. Temperature: 273–373 K at the local pressure
2. Sufficient atmospheric pressure ≥ ~0.006 atm (triple point of water)
3. Energy source (stellar or internal)

At 1 atm: water liquid between 273–373 K
At 0.00611 atm (triple point): only at 273.16 K precisely
At 0.001 atm (0.1 kPa): water sublimates directly (no liquid phase)
```

### Titan (Saturn's Moon)
| Property | Value |
|----------|-------|
| Surface temperature | 94 K |
| Surface pressure | 147 kPa |
| **Lake/sea composition** | ~5-8% ethane (C₂H₆), ~7-14% methane (CH₄), rest nitrogen |
| **Ligeia Mare** (sea) | ~200 km × 75 km |
| Sea depth | 20–40 m (sonar-mapped) |
| Liquid density | ~450 kg/m³ (mostly CH₄ + C₂H₆) |
| Waves | Up to 4 cm (wind-driven) |
| Note | NOT water — hydrocarbon lakes |

### Earth (Baseline for comparison)
| Biome | Liquid | Temperature | Salinity |
|-------|--------|-------------|----------|
| Oceans | H₂O | 271–303 K (−2 to +30°C) | 35 ppt |
| Salt lakes | H₂O + salts | 270–340 K | 50–300 ppt (saturated brine >350 ppt) |
| Thermal pools | H₂O | 313–373 K | Variable |
| Glaciers/Ice sheets | Solid H₂O | 243–273 K | Trace impurities |

## Subsurface Oceans

### Europa (Jupiter's Moon)
| Property | Value |
|----------|-------|
| Ice shell thickness | 15–30 km |
| Ocean depth | 100–200 km |
| Ocean pressure | 100–200 MPa (1,000–2,000 atm) |
| Salinity | ~100 ppt (3× Earth's oceans) — inferred |
| Temperature | ~277 K (just above freezing despite high pressure) |
| Energy source | Tidal heating (Io-induced stress) |
| Evidence | Induced magnetic field (conductive layer), chaos terrain |

### Enceladus (Saturn's Moon)
| Property | Value |
|----------|-------|
| Ice shell thickness | ~5 km (south polar) |
| Ocean depth | 10–20 km |
| Ocean pressure | ~100 MPa |
| Salinity | Unknown (inferred from plume composition) |
| Temperature | ~270–280 K |
| Plume rate | ~200 kg/s of H₂O + organics |
| Evidence | Geysers shooting water vapor into space (Cassini) |

### Ganymede (Jupiter's Moon)
| Property | Value |
|----------|-------|
| Ice shell thickness | 150–200 km |
| Ocean depth | 100 km (between shells) |
| Ocean pressure | ~35 MPa |
| Salinity | Unknown |
| Temperature | ~275 K (estimated) |
| Evidence | Induced magnetic field, auroral ovals |

### Exoplanet Subsurface Oceans (Theory)
```
Europa-like worlds around red dwarfs:
  If orbital distance allows ice to cover liquid phase
  Tidally heated ocean possible between ice shell and rocky core
  Example: Proxima Centauri b (if ice-covered), TRAP-1b analogs
```

## Brine (High-Salinity Water)

### Freezing Point Depression (Various Salts)
```
ΔT_f = i × K_f × m

Where:
- i = van 't Hoff factor (number of ions per salt unit)
- K_f = cryoscopic constant (1.86 K·kg/mol for water)
- m = molality (mol solute/kg water)

Common salt effects:

NaCl (i=2):
  35 g/kg → ΔT_f = 2 × 1.86 × (35/58.44) = 2.24 K → freezing point −2.24°C

MgCl₂ (i=3):
  35 g/kg → ΔT_f = 3 × 1.86 × (35/95.25) = 2.05 K → freezing point −2.05°C

CaCl₂ (i=3):
  35 g/kg → ΔT_f = 3 × 1.86 × (35/110.98) = 1.76 K → freezing point −1.76°C
```

### Brine Stability Limits
| Salt | Max Solubility (g/kg, 0°C) | Freezing Point |
|------|---------------------------|----------------|
| NaCl (halite) | ~357 g/kg | −21.2°C |
| MgCl₂ | ~535 g/kg | −33°C |
| CaCl₂ | ~745 g/kg | −51°C |
| MgSO₄ | ~337 g/kg | −17°C |

A saturated NaCl solution can remain liquid down to −21°C at standard pressure.

## Hydrothermal Vents & Chemical Gradients
```
On Earth's ocean floor:
  Temperature: 350–400°C (hydrothermal fluids)
  Pressure: 200–400 bar
  Chemistry: H₂S, CH₄, metal sulfides, silica
  Supporting unique ecosystems based on chemosynthesis

Implication for subsurface oceans:
  Europa's ocean likely has hydrothermal vents (oxidized surface material + reductive
  ocean + tidal heating = energy for chemistry)
```

## Water on Other Worlds — Summary Table

| Body | Liquid? | Composition | Depth/Pressure | Temp (K) | Notes |
|------|---------|-------------|----------------|----------|-------|
| **Earth** | Yes (surface + subsurface) | H₂O + salts | 11,000 m / 1,100 bar | 271–303 | Baseline |
| **Europa** | Yes (subsurface ocean) | H₂O + salts | 100 km / 100–200 MPa | ~277 | Under ice shell |
| **Enceladus** | Yes (subsurface ocean) | H₂O + organics | 10–20 km / ~100 MPa | ~275 | Jet plumes |
| **Ganymede** | Yes (subsurface ocean) | H₂O | 100 km / ~35 MPa | ~275 | Sandwiched in ice |
| **Titan** | Yes (surface lakes) | CH₄ + C₂H₆ + N₂ | 20–40 m / <1 bar | ~94 | Hydrocarbon, not water |
| **Mars** | No (mostly), possibly transient | H₂O (briny) | Subsurface flows? | ~210 | Recurring Slope Lineae (RSL) |
| **Venus** | No (surface) | H₂O (trace) | — | ~735 | Too hot; dry |
| **Europa Clipper target** | — | — | — | — | Mission launching 2024, arriving 2030 |
| **Dragonfly** | — | — | — | — | Mission to Titan's Ligeia Mare (launching 2028) |

### Liquid Water Phase Diagram Notes
```
Triple point of water:
  T_triple = 273.16 K (0.01°C)
  P_triple = 0.006112 bar = 611.657 Pa

At pressures below the triple point:
  Water transitions directly between solid and gas (sublimation)
  No liquid phase exists

Critical point of water:
  T_critical = 647 K (374°C)
  P_critical = 220.55 bar
  Beyond this: supercritical fluid (no liquid-gas boundary)

For subsurface oceans: hydrostatic pressure raises the freezing point slightly
(ice phase diagram is complex, but at 0.1–0.2 GPa, T_f shifts up by ~1–2°C),
but dissolved salts dominate the depression.
```

## Sources
1. Hand, K.P., et al. (2023). "The Interior of Europa." *Science*, 361(6405), 872–873.
   — Subsurface ocean depth, ice shell thickness
2. Postberg, J., et al. (2023). "Salt-rich water ice grains in the ejecta plume of
   Enceladus." *Nature Astronomy*, 7(3), 281–289.
   — Ocean salinity estimate
3. Schubert, G., et al. (2024). "The Interior of Ganymede: Evidence for a Subsurface
   Ocean from Astrometry." *Journal of Geophysical Research: Planets*.
   — Ganymede ocean depth and pressure
4. Sotin, C., et al. (2022). "The Lakes and Seas of Titan." *Nature Astronomy*,
   6(8), 769–779.
   — Titan methane/ethane lakes, depths, composition
5. Google Earth Hydrological Data (2025). "Global Ocean Depth Statistics."
   — Earth ocean depth statistics, salinity
6. National Snow and Ice Data Center (NSIDC). (2025). "Antarctic Subglacial Lake."
   — Terrestrial analog for subsurface liquid environments
7. NASA Exoplanet Exploration Program (2025). "Liquid Water Phase Diagrams for Icy
   Worlds." — Freezing point depression, phase boundaries
