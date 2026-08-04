# Atmospheric Composition by Planet Type — Reference

## Purpose
Reference card for atmospheric composition, scale height, and retention properties
across planetary bodies. Relevant to theSuit, theShip, and theScan membranes.

## Key Concept: Atmospheric Retention

### Jeans Escape Criterion
```
A planet retains an atmosphere if its escape velocity exceeds the thermal velocity
by a comfortable margin:

v_escape = √(2GM/R)  [escape velocity]
v_thermal = √(2kT/m)    [most probable speed of gas molecules]

Retention ratio: v_escape / v_thermal ≥ 5–6 (rule of thumb for long-term retention)
```

### Jeans Parameter for Each Body
| Body | Escape Velocity (km/s) | T (K) | Retains (M-weight) | Retention Ratio |
|------|------------------------|------|---------------------|------------------|
| Earth | 11.2 | 288 | All gases (except H₂, He) | 50+ |
| Venus | 10.4 | 735 | All gases + CO₂ | 35+ |
| Mars | 5.0 | 210 | CO₂, N₂, Ar (not O₂, H₂O loss) | 10–15 |
| Moon | 2.4 | 220 | No gases | ~2 (loses everything) |
| Titan | 2.6 | 94 | N₂, CH₄ (not CO₂, H₂O) | ~15 |
| Pluto | 1.2 | 44 | N₂, CH₄ only at coldest temps | ~5 |
| Europa | 2.0 | 100 | Trace O₂ (radiolytic) | ~8 |
| Ganymede | 2.8 | 110 | Trace O₂ | ~12 |

## Terrestrial Planet Atmospheres

### Earth
| Parameter | Value | Notes |
|-----------|-------|-------|
| **Surface pressure** | 101.325 kPa (1 atm) | |
| **Scale height** | 8.5 km | H = RT/(Mg), M=0.029 kg/mol |
| **Temperature (surface)** | 288 K (15°C) | |
| **Molecular weight** | 28.97 g/mol | |
| **Composition** | 78.08% N₂, 20.95% O₂, 0.042% CO₂, 0.93% Ar, 0% H₂O (varies) | |
| **Greenhouse effect** | ~33°C warming | Without GHGs: ~255 K (−18°C) |
| **Column mass** | 10,300 kg/m² | Total atmosphere above 1 m² |

### Venus
| Parameter | Value | Notes |
|-----------|-------|-------|
| **Surface pressure** | 9,200 kPa (~90 atm) | Crushing |
| **Scale height** | 15.9 km | H = RT/(Mg), M=0.043 kg/mol |
| **Temperature (surface)** | 735 K (462°C) | Runaway greenhouse |
| **Molecular weight** | 43.45 g/mol | |
| **Composition** | 96.5% CO₂, 3.5% N₂, 0.015% SO₂, 0.002% H₂O | |
| **Greenhouse effect** | ~500°C warming | Extreme runaway |
| **Column mass** | ~100,000 kg/m² | 9.3× Earth's |

### Mars
| Parameter | Value | Notes |
|-----------|-------|-------|
| **Surface pressure** | 0.6 kPa (0.006 atm) | |
| **Scale height** | 11.1 km | H = RT/(Mg), M=0.043 kg/mol |
| **Temperature (surface)** | 210 K (−63°C) average | Range: 130–270 K |
| **Molecular weight** | 43.3 g/mol (mostly CO₂) | CO₂ = 44 g/mol |
| **Composition** | 95.32% CO₂, 2.7% N₂, 1.6% Ar, 0.13% O₂, 0.08% CO, 0.02% H₂O | |
| **Greenhouse effect** | ~5–20°C warming | Thin; dust storms matter more |
| **Column mass** | ~16,000 kg/m² | |

### Titan (Saturn's moon)
| Parameter | Value | Notes |
|-----------|-------|-------|
| **Surface pressure** | 147 kPa (1.45 atm) | |
| **Scale height** | 21 km | H = RT/(Mg), M=0.028 kg/mol |
| **Temperature (surface)** | 94 K (−179°C) | |
| **Molecular weight** | 28.02 g/mol (N₂-dominated) | |
| **Composition** | 95% N₂, 5% CH₄ (+ trace organics, H₂) | |
| **Greenhouse effect** | ~7°C warming | Methane is GHG here |
| **Column mass** | ~42,000 kg/m² | |

## Gas Giant Atmospheres (Brief)

| Body | Surface Pressure | Key Components |
|------|------------------|----------------|
| Jupiter | ~1000 kPa (1 bar, 10 bar level) | H₂ (89%), He (10%), NH₃, H₂O |
| Saturn | ~1000 kPa | H₂ (96%), He (3%), CH₄, NH₃ |
| Uranus | ~1000 kPa | H₂ (83%), He (15%), CH₄ (2.3%) |
| Neptune | ~1000 kPa | H₂ (80%), He (19%), CH₄ (1.5%) |

## Exoplanet Atmospheres (Hot Jupiters & Super-Earths)

### Hot Jupiter (e.g., HD 209458 b)
| Parameter | Value |
|-----------|-------|
| Temperature (dayside) | 1,200–1,400 K |
| Composition | H₂O, CO, CO₂, Na, K detected |
| Pressure scale | Varies wildly from day to night side |

### Super-Earth (TRAP-1b-like or similar)
| Parameter | Value |
|-----------|-------|
| Temperature (dayside) | 800–1,200 K |
| Composition | Unknown (likely rock vapor, CO, CO₂) |
| Escape | Significant atmospheric loss if close-in |

## Scale Height Formula
```
H = R × T / (M × g)

Where:
- H: scale height (m)
- R: universal gas constant = 8.314 J/mol·K
- T: temperature (K)
- M: molar mass of atmospheric gas (kg/mol)
- g: surface gravity (m/s²)

Pressure at altitude z: P(z) = P₀ × exp(-z/H)
```

### Calculated Scale Heights

| Body | T (K) | M (g/mol) | g (m/s²) | H (km) |
|------|-------|-----------|----------|--------|
| Earth | 288 | 28.97 | 9.81 | 8.5 |
| Mars | 210 | 43.3 | 3.71 | 11.1 |
| Venus | 735 | 43.45 | 8.87 | 15.9 |
| Titan | 94 | 28.02 | 1.35 | 21.0 |
| Moon | 220 | 28.97 | 1.62 | 18.4 |
| Europa | 100 | 28.97 | 1.31 | 61.4 |

## Atmospheric Escape Mechanisms

### Jeans Escape
```
Flux of escaping particles ∝ exp(-v_escape / v_thermal)

For H₂ on Earth: v_thermal(H₂) ~ 3.4 km/s, v_escape = 11.2 km/s
Flux ∝ exp(-3.3) ≈ 0.04 → very slow escape (loses H₂)
```

### Hydrodynamic Escape (hot Jupiters)
```
When radiation pressure exceeds gravity:
  F_XUV / F_grav > 1  →  mass-loss rate ~ 10⁹-10¹¹ g/s
```

### Sputtering
Cosmic ray ion impact knocks atmospheric particles into space.

| Body | Sputtering rate (kg/s) |
|------|------------------------|
| Mars | 1.4×10²² atoms/s (mostly O, C) |
| Venus | 1.0×10²⁰ atoms/s |
| Mercury | 10¹⁸ atoms/s |

## Cross-Reference: Atmospheric Window Concepts (vs. Remote Sensing)

Earth's atmosphere has key absorption features relevant to remote sensing:

| Gas | Absorbs | Wavelength |
|-----|---------|------------|
| H₂O | IR | 2–25 μm (various bands) |
| CO₂ | IR | 15 μm, 4.3 μm |
| O₃ | UV → IR | 0.25 μm, 9.6 μm |
| O₂ | Visible (Chappuis) | 0.69 μm |
| N₂O | IR | 4.5 μm, 7.8 μm |
| CH₄ | IR | 3.3 μm, 7.7 μm |

## Atmospheric Density vs. Altitude (Earth ISA Model)
```
ρ(h) = ρ₀ × (1 - h/23800)^4.256    [below 11 km]
ρ(h) = ρ_11km × exp(-(h-11000)/635600)  [above 11 km, in thermosphere]

Standard values for reference:
  Sea level: 1.225 kg/m³
  5 km: 0.736 kg/m³
  10 km: 0.414 kg/m³
  15 km: 0.195 kg/m³
  20 km: 0.088 kg/m³
```

## Application to Laguna Membranes

### Atmosphere Membrane Physics
For atmospheric pressure modeling across worlds:
```
Pressure drop to altitude Δh:

At any body, the pressure decreases roughly exponentially:
  P(h) ≈ P₀ × exp(-mg/(kT) × h)

For a 2000-m flight above Mars surface:
  P/P₀ ≈ exp(-3.71 × 0.043 × 2000 / (8.314 × 210)) ≈ 0.21
  → Pressure drops to ~21% of surface pressure (~130 Pa)
```

## Sources
1. Seiff, W. (1972). "Thermal structure of the upper atmosphere of Venus and Mars."
   *Space Science Reviews*, 10(3), 247–288.
   — Venus and Mars atmospheric structure
2. Hedin, A.E. (1996). "International Reference Atmosphere 1990." *Journal of
   Geophysical Research*, 101(A1), 1035–1056.
   — Earth atmospheric model, scale heights
3. Smith, M.D. (2023). "Mars Climate and Atmospheric Evolution." *Annual Review of
   Earth and Planetary Sciences*, 51, 1-30.
   — Current knowledge of Martian atmospheric composition and escape rates
4. Hörst, S.E. (2019). "The climate of Titan." *Planetary and Space Science*, 160,
   11–23.
   — Titan atmospheric structure, scale height
5. Lodders, K. & Fegley, B. (1998). *The Cosmic Environment.* Springer.
   — Atmospheric chemistry, escape mechanisms, planetary retention
6. Jakosky, B.M. (1993). *Accretion of Atmospheres: Planetary Evolution and
   Atmospheric Loss.* University of Arizona Press.
   — Jeans escape criterion, atmospheric retention theory
7. NASA Exoplanet Archive. (2025). "Exoplanet Atmospheres."
   https://exoplanetarchive.ipac.caltech.edu/
   — Hot Jupiter thermal escape rates, atmospheric loss
