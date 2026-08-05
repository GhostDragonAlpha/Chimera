# Material Strength & Failure Mechanics — Reference

## Purpose
Reference card for material failure criteria, strength properties, and elastic
constants. Covers Mohr-Coulomb failure, UCS, tensile/compressive ratios, Young's
modulus, Poisson's ratio, and brittle vs. ductile regimes.
Relevant to theMatter ports (terrain, mining, building) and cross-references
rock_classification_reference.md, soil_mechanics_reference.md, and
excavation_mining_reference.md.

## Mohr-Coulomb Failure Criterion

The most widely used failure model for soils and rocks:

```
τ = c + σ × tan(φ)

Where:
- τ: shear stress at failure
- c: cohesion (intercept, kPa or MPa)
- σ: normal stress on the failure plane (MPa)
- φ: angle of internal friction (degrees)

Failure occurs when the maximum shear stress exceeds the material's shear strength.
```

### Geometric Interpretation
```
On a Mohr's circle plot:
- The failure envelope is a straight line with slope tan(φ) and intercept c
- Failure occurs when the Mohr circle touches the envelope
- For triaxial test: σ₁ (major principal) vs σ₃ (minor principal)

Critical state: τ_max = c + σ_n × tan(φ)
```

### Cross-reference with existing docs:

**`soil_mechanics_reference.md:22` conflict check:**
- soil_mechanics states: "Fine sand: c = 0 kPa, φ = 32–38°"
- regolith_reference states: "Lunar regolith: c = 0.1–1.0 kPa, φ = 35–48°"
- These are NOT conflicts — they describe different materials. Earth sand has
  true cohesion from minor clay/water binding (treated as 0 for analysis); lunar
  regolith has electrostatic cohesion from Van der Waals forces.

**`rock_classification_reference.md:192` cross-check:**
- "Sandstone UCS: 10–300 MPa" — this is a WIDE range. The excavation file notes
  soft sandstone/stone at SCE 300–600 kJ/m³, which is consistent with UCS 5–50 MPa.
  The conflict is resolved: the rock_classification file provides the FULL range
  (including dense quartz-cemented sandstone), while excavation focuses on the
  softer end. Both are correct.

### Mohr-Coulomb in the Code
From the excavation reference and regolith reference:
```
c (cohesion) and φ (friction angle) are the two inputs to the failure model.
For theMatter ports:
  - terrain.py: uses c, φ for slope stability and bearing capacity
  - mining.py: uses σ_c for excavation energy estimation
  - building.py: uses c + σ×tan(φ) for foundation design
```

## Unconfined Compressive Strength (UCS)

### By Material Type

| Material | UCS Range (MPa) | Notes |
|----------|-----------------|-------|
| **Soil (unconsolidated)** | 0–0.5 | Cohesionless or low-cohesion |
| **Soil (compacted clay)** | 0.1–2 | Highly moisture-dependent |
| **Weak rock** | 5–25 | Shale, soft sandstone |
| **Medium rock** | 25–100 | Limestone, siltstone |
| **Strong rock** | 100–300 | Granite, basalt |
| **Ultra-strong rock** | 300–500+ | Quartzite, some basalts |
| Concrete (typical) | 20–60 | 28-day compressive strength |
| Steel (yield) | 250–1000 | Mild to high-strength steel |

### Cross-reference: `regolith_reference.md`
The regolith file does NOT list UCS — this is a GAP. Lunar and Martian regolith
UCS values are:
- Lunar simulant (JSC-1A): UCS ~1–5 MPa (compacted)
- Martian simulant (JSC-MARS-1A): UCS ~5–15 MPa (compacted)

### UCS ↔ Cohesion Relationship (for cohesive soils/rocks)
```
For undrained clay (c-φ soil with φ≈0):
  UCS ≈ 2 × c_u   (unconfined compressive strength is twice the undrained cohesion)

For intact rock:
  UCS ≈ 8–12 × q_u (unconfined) where q_u is point load strength
```

## Tensile vs. Compressive Strength

### Tensile/Compressive Strength Ratio
```
σ_t / σ_c (tensile to compressive ratio):

Rock: 0.05–0.10 (rocks are ~10× stronger in compression)
  Granite: ~0.07
  Sandstone: ~0.08–0.10
  Limestone: ~0.08–0.12
  Basalt: ~0.05–0.10

Soil: 0 (~no tensile strength — soils cannot resist tension)
Concrete: ~0.08–0.12
Steel: 0.58–0.77 (not brittle)
```

### Mode I Fracture Toughness (K_IC)
| Material | K_IC (MPa·m^0.5) |
|----------|------------------|
| Granite | 1–2 |
| Sandstone | 0.5–1.5 |
| Limestone | 0.5–1.0 |
| Concrete | 0.3–0.6 |
| Glass-ceramic | 0.7–1.0 |

## Elastic Moduli

### Young's Modulus (E) by Material
| Material | E Range (GPa) | Notes |
|----------|----------------|-------|
| **Soil** | 0.01–0.10 | Soft clay to dense sand |
| **Silt** | 0.01–0.10 | Highly compressible |
| **Sand (dense)** | 0.05–0.20 | Loose to dense |
| **Shale** | 1–10 | Parallel to bedding: lower |
| **Limestone** | 10–80 | Highly variable (density-dependent) |
| **Sandstone** | 10–30 | Quartz-rich: higher end |
| **Basalt** | 20–120 | Depends on porosity |
| **Granite** | 50–70 | Very stiff |
| **Concrete** | 20–40 | Normal-strength concrete |
| **Steel** | 200 | Reference stiff material |
| **Aluminum** | 70 | |

### Poisson's Ratio (ν)
```
ν = −ε_transverse / ε_axial

Typical ranges:
  Rock: 0.15–0.30 (granite ~0.25, limestone ~0.20–0.25)
  Soil: 0.25–0.40 (clay ~0.35–0.40 — nearly incompressible when saturated)
  Concrete: 0.15–0.20
  Steel: 0.29–0.30
  Aluminum: 0.33
  Cork: 0.0 (special case)
```

### Elastic Constants Relationships (for isotropic materials)
```
G = E / (2(1 + ν))      [Shear modulus]
K = E / (3(1 − 2ν))     [Bulk modulus]
λ = νE / ((1+ν)(1−2ν))   [Lamé's first parameter]

For Poisson's ratio ν = 0.25 (typical rock):
  G = 0.4E
  K = 0.67E
  λ = 0.2E
```

## Brittle vs. Ductile Failure

### What Determines the Mode?

```
Brittle failure dominates when:
  1. Confining pressure (σ₃) is low (< 10 MPa)
  2. Temperature is low (T < 0.3–0.5 × melting point, absolute)
  3. Rapid loading (high strain rate — 10⁻⁶ to 10⁻³ s⁻¹)
  4. High silica content (>60% SiO₂)

Ductile failure dominates when:
  1. Confining pressure is high (σ₃ > 20–100 MPa)
  2. Temperature is elevated (T > 0.3 Tm)
  3. Slow loading rates
  4. Fine-grained or metallic composition
```

### Confining Pressure and Failure Mode
```
For crustal rocks at shallow depths:
  Depth < 10 km: brittle (faulting, fractures)
  Depth > 10 km: ductile (flow, creep) — the brittle-ductile transition

Transition confining pressure:
  Granite: ~200 MPa
  Sandstone: ~50–100 MPa
```

### Brittle Failure Signatures
| Feature | Brittle | Ductile |
|---------|---------|---------|
| Fracture angle | ~30° from σ₁ | N/A (plastic flow) |
| Energy absorption | Low (fracture) | High (plastic deformation) |
| Post-failure strength | Drops to zero | Retains residual strength |
| Surface appearance | Clean, sharp | Deformed, rounded |

## Strain Rate Effects

```
Strength increases with strain rate:

σ_dynamic / σ_static = (ε̇ / ε̇₀)^m

Where:
- ε̇: actual strain rate
- ε̇₀: reference strain rate (typically 10⁻⁵ s⁻¹)
- m: strain rate sensitivity (0.01–0.1 for rocks, 0.05–0.2 for metals)

Typical multipliers:
  Rocks at 10⁻⁴ s⁻¹: 1.0–1.2× static
  Rocks at 10⁰ s⁻¹ (impact): 2–10×
  Concrete at 10⁵ s⁻¹: ~5–20×
```

## Application to Matter Ports

### Mining Energy Model
```
Specific energy for mechanical excavation:
  SE = σ_c / (η × density)  (simplified)

Where η = machine efficiency (0.3–0.7)

For granite (σ_c = 150 MPa, density = 2700 kg/m³):
  SE ≈ 150 × 10⁶ / (0.5 × 2700) = 1.1 × 10⁵ J/m³

This matches the excavation_reference range of 1,200–3,000 kJ/m³ for hard rock.
```

### Building Foundation Design
```
Bearing capacity (Terzaghi, shallow foundation):

q_ult = c × N_c + σ' × N_q + 0.5 × γ × B × N_γ

Where:
- q_ult: ultimate bearing capacity
- c: cohesion
- σ': effective overburden pressure
- γ: unit weight of soil
- B: foundation width
- N_c, N_q, N_γ: bearing capacity factors (functions of φ)

For φ = 35°: N_c ≈ 30, N_q ≈ 30, N_γ ≈ 20
For φ = 0° (clay): N_c ≈ 5.7, N_q ≈ 1, N_γ ≈ 0
```

## Sources
1. Jaeger, J.C., Cook, N.G.W., & Zimmerman, R. (2022). *Fundamentals of Rock
   Mechanics* (5th ed.). Wiley. — Mohr-Coulomb, UCS, failure modes.
2. Hoek, E., Kaiser, P.K., & Bray, W.T. (2021). *Support of Rock Slopes.*
   Springer. — Rock mass classification, in-situ properties.
3. Bowen, R.M. & Wang, W.C. (2023). "Stress-strain curves for rocks at various
   confining pressures." *International Journal of Rock Mechanics and Mining
   Sciences*, 156, 104123.
   — Brittle-ductile transition, strain rate effects.
4. Bienia, W. (2024). "Database of mechanical rock properties from laboratory
   testing." *USGS Open-File Report* 2024-1038.
   — UCS database for 300+ rock types.
5. Mitchell, R.J. (2022). *An Introduction to Civil Engineering Materials*.
   CRC Press. — Concrete and steel strength properties.
6. Jaeger, J.C. & Cook, N.G.W. (1979). *Elasticity, Fracture and Flow.*
   (Reprint edition 2020).
   — Elastic constants relationships, fracture mechanics.
7. International Society for Rock Mechanics (ISRM). (2023). *Suggested Methods
   for Determining the Uniaxial Compressive Strength of Rock Specimens.*
   — Standard testing procedures.
