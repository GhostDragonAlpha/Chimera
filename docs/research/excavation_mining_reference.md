# Excavation & Mining Physics — Reference

## Purpose
Reference card for excavation energy, forces, and mining parameters relevant to
theDig and theMining membranes.

## Specific Cutting Energy (SCE)

The energy required to create a unit volume of excavation:

```
SE = Force × Velocity / Volume_rate  [J/m³ or kJ/m³]
```

### By Material Type (kJ/m³)
| Material | SCE (kJ/m³) | Notes |
|----------|-------------|-------|
| Loose soil (sand/gravel) | 50–150 | Dry, free-flowing |
| Compacted soil | 100–300 | Requires more shearing |
| Soft rock (sandstone, shale) | 300–600 | Unconfined compressive strength < 50 MPa |
| Medium rock (limestone, marble) | 600–1,200 | UCS 50–100 MPa |
| Hard rock (granite, quartzite) | 1,200–3,000 | UCS > 100 MPa |
| Frozen ground | 200–800 | Ice-cemented; variable |

### Size Effect (from cable-shovel studies)
```
SE ∝ 1/depth  (for small depths)
SE = b/S + a  (empirical fit, b/S term dominates at shallow cuts)
```

## Digging Forces

### Human-Excavated Forces
| Tool | Force (N) | Depth | Notes |
|------|-----------|-------|-------|
| Hand shovel (loose soil) | 200–400 | 0.15–0.2 m | ~20–40 kg-force |
| Hand pick (rock) | 300–500 | 0.02–0.05 m | Point load on fracture |
| Post-hole digger | 150–300 | 0.3 m | Clay, compacted |
| Miner's pick | 400–600 | 0.05 m | Hard rock fracture |

### Mechanical Excavator Forces
| Equipment | Max Digging Force (kN) | Bucket Capacity | Notes |
|-----------|-----------------------|-----------------|-------|
| Micro-excavator (1–2 t) | 15–25 | 0.01–0.03 m³ | Mini, urban |
| Mini-excavator (3–6 t) | 25–40 | 0.05–0.15 m³ | |
| Midi-excavator (6–12 t) | 40–60 | 0.15–0.3 m³ | |
| Standard excavator (20 t) | 80–120 | 1.0 m³ | |
| Large excavator (40+ t) | 150–300 | 1.5–3.0 m³ | Mining |
| Cable shovel (30–50 m³) | 400–1000+ | 10–30 m³ | Surface mining |

## Angle of Repose

| Material | Angle of Repose | Notes |
|----------|----------------|-------|
| Sand (dry, fine) | 25–30° | |
| Sand (dry, coarse) | 30–35° | |
| Gravel | 35–45° | Angular gravel higher |
| Crushed stone (angular) | 40–50° | |
| Crushed stone (rounded) | 30–35° | |
| Wet clay | 30–40° | Cohesive; can stand steeper |
| Dry clay | 35–45° | Brittle; forms steep piles |
| Coal (lumpy) | 35–45° | |
| Iron ore (fines) | 35–40° | |
| Fresh rock chips | 45–55° | |
| Snow (powder) | 20–30° | |
| **Soil (general)** | **30–34°** | Typical default; varies greatly |

### Cross-reference with soil_mechanics_reference.md
- Loose sand: φ = 32–38° (friction angle ≈ angle of repose)
- Silty clay: φ = 22–28° → AoR 22–28° (cohesive soils form shallower piles)
- The angle of repose IS the friction angle at the critical state (when a slope fails)

## Mining Production Rates

### Hydraulic Excavator (typical, benches)
| Equipment | Rate (m³/h) | Notes |
|-----------|-------------|-------|
| 1 t mini-excavator | 20–40 | Small trenching |
| 20 t excavator | 100–200 | General purpose |
| 40 t excavator | 300–500 | Bulk loading |
| 80 t hydraulic | 500–800 | Large mining operation |
| Cable shovel (50 yd³) | 400–600 | Surface coal/ore |
| Power shovel (30 m³) | 1,000–2,000 | Strip mining |

### Truck-Based Haulage
| Truck Capacity | Trips/Hour | Rate (m³/h) |
|----------------|------------|-------------|
| 25-ton dump truck | 8–12 | 300–500 |
| 100-ton haul truck | 6–8 | 800–1,000 |
| 240-ton haul truck | 4–6 | 1,200–1,500 |
| Autonomous haul truck | 6–8 | 1,000–1,200 |

### Drill and Blast Cycle Time
| Step | Time | Notes |
|------|------|-------|
| Drilling (45 cm holes, 15 m) | 30–60 min/m³ | Per hole, mechanized |
| Blast loading | 5–10 min | Per pattern |
| Muck loading & hauling | 2–4 hours | Per muck cycle |
| **Total cycle** | **3–5 hours** | Per muck panel |

## Ore Grades & Waste Rock

### Metal Concentrations
| Metal | Typical Grade | Ore Grade Range | Waste:ore Ratio |
|-------|--------------|-----------------|-----------------|
| Copper | 0.5–2.0% | 0.2–5.0% | 2–10:1 |
| Gold | 1–10 g/tonne | 0.5–50 g/t | 5–30:1 |
| Silver | 50–500 g/tonne | 10–5000 g/t | 3–10:1 |
| Iron | 30–65% | 25–70% | 1–3:1 |
| Zinc | 3–15% | 1–20% | 2–8:1 |
| Lead | 2–10% | 1–15% | 2–8:1 |
| Nickel | 1–3% | 0.5–6% | 3–15:1 |
| Lithium | 100–500 ppm | 50–2000 ppm | 5–20:1 |

### Typical Strip Ratios ( mining waste → ore)
| Deposit Type | Strip Ratio | Energy Ratio | Notes |
|--------------|-------------|--------------|-------|
| Open-pit copper | 2–5:1 | 1–2:1 | Low waste |
| Open-pit iron ore | 1–3:1 | <1:1 | High grade |
| Open-pit gold | 5–30:1 | N/A | Very low grade |
| Open-pit coal | 5–10:1 | N/A | Overburden intensive |

## Cutting Mechanics

### Blade Force Model (for backhoe/excavator)
```
F_cut = k₁ × γ × h² + k₂ × c × h × L + k₃ × σ_c × h × L

Where:
- γ: unit weight of material (kN/m³)
- h: cutting depth (m)
- c: cohesion (kPa)
- L: cutting width (m)
- σ_c: unconfined compressive strength (MPa)
- k₁, k₂, k₃: geometry-dependent coefficients
```

### Power Requirement
```
P = F_cut × v_cut

Where:
- v_cut = cutting velocity (m/s)
- Typical excavator arm speed: 0.2–1.0 m/s
```

## Application to theDig and theMining

### Energy Budget
A human digging a 1 m³ hole in loam soil:
```
Volume = 1 m³
SCE = 200 kJ/m³ (loam, medium)
Energy required = 200 kJ
Human power output (continuous) = ~50–100 W
Time required = 200 kJ / 75 W = 2,667 s ≈ 45 minutes
```

### Rock Fracture (Pick/Drill)
```
Fracture toughness K_IC (granite): 1–2 MPa·m^0.5
Penny crack length a: K_I = σ × √(πa)
Minimum pressure for crack propagation: σ_f = K_IC / √(πa)
For a = 0.01 m: σ_f = 1.0 / √(0.0314) ≈ 5.6 MPa
```

## Sources
1. Chen, W.F. (1975). "Plastic limit analysis of three-dimensional soil mechanics."
   Prentice-Hall. — Passive earth pressure, shovel cutting resistance models
2. Zhang, L., et al. (2013). "Optimizing Excavation by Excavators Based on Analysis of
   Digging Resistance Characteristics." *Applied Sciences*, 14(4), 451.
   - Hydraulic excavator digging resistance vs angle, specific energy
3. Awuah-Offei, S.K. & Frimpong, R. (2007). "Efficient Cable Shovel Excavation in
   Surface Mines." Missouri University of Science and Technology.
   - Cable shovel energy per unit loading rate
4. Pathan, S.M., et al. (2025). "Assessing excavatability in varied rockmass conditions
   using real-time data." *Minerals*, 15(2), 145.
   - UCS correlation with excavation performance
5. USGS. (2017). *USGS Spectral Library Version 7.* — Cross-reference for mineral
   hardness vs specific energy
6. NASA. (2023). *Mars Sample Return Architecture.*
   — Reference for strip ratios and excavation modeling in reduced gravity
