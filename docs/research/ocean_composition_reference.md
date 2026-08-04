# Ocean Composition — Reference

## Purpose
Reference card for standard ocean/water composition parameters for laguna modeling.

## TEOS-10 Standard (Thermodynamic Equation of Seawater, 2010)

### Practical Salinity (SP, dimensionless)
- Standard deep ocean: 35.0 PSU (Practical Salinity Units)
- Range: 0 (fresh) to ~42 (hypersaline, e.g., Red Sea ~41, Dead Sea ~34–44)

### Absolute Salinity (SA, g/kg)
```
SA = SP × 0.00001 × (35 / 1.80655) = SP × 0.000548
```
- Standard ocean SA ≈ 35.165 g/kg for SP=35

### Conservative Temperature (Θ, °C)
Derived from in-situ temperature via TEOS-10 Gibbs function. Near-surface ocean: 0–30°C.

## Seawater Density (ρ, kg/m³)
```
ρ = ρ(T, S, P)  — function of temperature, salinity, pressure
```
For laguna conditions (surface, P ≈ 1 atm):
- Freshwater (S=0, 25°C): 997.05 kg/m³
- Standard seawater (S=35, 25°C): ~1023.6 kg/m³
- Hypersaline lagoon (S=50, 25°C): ~1038.5 kg/m³

## Trace Ion Composition (by mass in standard seawater)

| Ion | Concentration (g/kg) in S=35 seawater | % |
|-----|---------------------------------------|---|
| Cl⁻ | 19.35 | 55.04% |
| Na⁺ | 10.76 | 30.72% |
| SO₄²⁻ | 2.71 | 7.72% |
| Mg²⁺ | 1.38 | 3.94% |
| Ca²⁺ | 0.41 | 1.18% |
| K⁺ | 0.39 | 1.12% |
| HCO₃⁻ | 0.14 | 0.40% |

**Note:** Cl⁻ + Na⁺ account for ~85.7% of total dissolved ions.

## Solar Composition (Photosphere)

| Element | Mass Fraction | Notes |
|---------|--------------|-------|
| Hydrogen | 0.7340 (73.40%) | Primary component |
| Helium | 0.2485 (24.85%) | Second most abundant |
| Carbon | 0.0029 (0.29%) | Organic trace |
| Nitrogen | 0.0007 (0.07%) | Trace |
| Oxygen | 0.0077 (0.77%) | Major trace |
| Iron | 0.0016 (0.16%) | Most abundant metal |

**Source:** Caffau, H., et al. (2011). "The chemical composition of the Sun." *Astronomy & Astrophysics*, 532, A141.

## Application to Laguna Physics
- **Density range:** A laguna's density depends on S (salinity) and T (temperature). Hypersaline lagoons (S > 45) can have ρ > 1040 kg/m³.
- **Light absorption:** Water absorption spectrum peaks at 420nm (~3.0 m⁻¹) and 740nm (~0.3 m⁻¹ for pure water, higher with dissolved ions).
- **Refractive index:** Seawater n ≈ 1.3345 at 589nm (slightly higher than fresh water's 1.333).

## Sources
1. IOC, SCOR, and UNESCO. (2010). "The International Thermodynamic Equation of Seawater — 2010: Calculation and Use of Thermophysical Properties." *InterpolatedoceanographicToolkit 36*, 195–205.
2. UNESCO. (1983). *Seawater State Properties — IAPWS-83*. UNESCO Technical Papers in Marine Science.
   - Standard seawater composition tables
3. Caffau, H., et al. (2011). "The chemical composition of the Sun." *Astronomy & Astrophysics*, 532, A141.
   - Solar photosphere elemental abundances
