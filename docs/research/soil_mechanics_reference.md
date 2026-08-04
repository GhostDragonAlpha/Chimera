# Soil Mechanics — Reference

## Purpose
Reference card for soil mechanics parameters relevant to laguna membrane physics.
Surface-based (not deep geological) — applicable to laguna floor sedimentation and crust formation.

## Core Principle
**Terzaghi Effective Stress Principle:**
```
σ' = σ - u
```
- `σ'` = effective stress (what the soil skeleton carries)
- `σ` = total stress (overburden weight + external loads)
- `u` = pore water pressure

This governs whether a laguna sediment layer stays cohesive or liquefies under wave loading.

## Key Parameters

| Parameter | Symbol | Range | Notes |
|-----------|--------|-------|-------|
| Cohesion | c | 0–100 kPa | Fine-grained soils (clay) hold together; sand has ~0 |
| Internal friction angle | φ | 25°–45° | Sand ~35°, clay ~20–30° |
| Unit weight (dry) | γ_dry | 14–18 kN/m³ | Sand ~16, clay ~15 |
| Unit weight (saturated) | γ_sat | 18–22 kN/m³ | Sand ~19, clay ~20 |
| Relative density | D_r | 0–100% | Loose <35%, dense >65% |

## Critical Threshold: Liquefaction
A laguna sediment layer liquefies when cyclic stress exceeds the soil's cyclic resistance:

```
CSR = τ_cyc / σ'_v0
CRR = f(D_r, σ'_v0, fines_content, ... )
```
- `CSR`: Cyclic Stress Ratio (demand)
- `CRR`: Cyclic Resistance Ratio (capacity)
- Failure when `CSR ≥ CRR`

For laguna crust modeling: if the sediment is fine-grained (clay/silt) with low cohesion (<10 kPa), wave-induced cyclic loading can trigger liquefaction at shallow depths, forming a fluidized layer.

## Standard Values for Laguna Sediment Types

### Fine Sand (laguna floor)
- Source: Iowa DOT (2023)
- c = 0 kPa
- φ = 32–38°
- γ_sat = 19 kN/m³
- D_r = 30–50% (loose)

### Silty Clay (delta deposits)
- Source: Washington State DOT (2019)
- c = 15–30 kPa
- φ = 22–28°
- γ_sat = 18–19 kN/m³

### Organic Layer (laguna bed)
- c = 5–15 kPa (weak, organic)
- φ = 18–25°
- γ_sat = 16–17 kN/m³

## Application to Laguna Membrane Physics
- **Crust formation:** A cohesive layer (c > 20 kPa) can support wave loads and form a stable crust.
- **Fluidization:** If pore pressure rises (e.g., gas exsolution or groundwater seepage), effective stress drops and the sediment liquefies.
- **Wave interaction:** Wave period (T) and sediment grain size (d) control the boundary layer. For laguna waves (T ~ 5–10 s, d ~ 0.1–0.3 mm), the Shields parameter determines whether grains move:
  ```
  τ* = τ_b / [(ρ_s - ρ) g d]
  ```
  where τ_b is bed shear stress, ρ_s sediment density (~2650 kg/m³ for quartz), ρ water density (1000 kg/m³).

## Sources
1. Iowa Department of Transportation. (2023). *Soil Mechanics Handbook*. Ames, IA.
   - Standard sand parameters: φ = 35°, γ_sat = 19 kN/m³
2. Washington State Department of Transportation. (2019). *Geotechnical Manual — Soil Properties*. Olympia, WA.
   - Cohesive soil ranges: c = 15–30 kPa, φ = 22–28°
3. Terzaghi, K. (1943). *Theoretical Soil Mechanics*. Wiley.
   - Effective stress principle: σ' = σ - u
