# Variable Gravity Physics — Reference

## Purpose
Reference card for key dimensionless numbers and physics governing sediment transport,
fluid dynamics, and atmospheric scale height under variable gravity conditions.

## Core Dimensionless Numbers

### Shields Number (Threshold for Sediment Motion)
```
Θ = τ_b / [(ρ_s - ρ_f) g d]
```
Where:
- `τ_b` = bed shear stress (Pa)
- `ρ_s` = sediment density (~2650 kg/m³ for quartz)
- `ρ_f` = fluid density (~1000 kg/m³ for water, ~1.2 kg/m³ for air)
- `g` = gravitational acceleration (m/s²) — **scales directly with planetary gravity**
- `d` = particle diameter (m)

**Critical threshold:** Θ_c ≈ 0.03–0.06 for quartz in water, Θ_c ≈ 0.12–0.37 for sand in air
**Note:** At low gravity, the submerged specific gravity `(ρ_s − ρ_f)/ρ_f` is unchanged,
but the driving force `τ_b / (ρ_f g d)` changes — lower g means the same shear stress
produces proportionally more particle motion.

### Shear Reynolds Number
```
Re* = u* × d / ν
```
Where:
- `u* = √(τ_b / ρ_f)` = shear velocity
- `ν` = kinematic viscosity of fluid

**Critical threshold:** Re* ≈ 1–10 (laminar), Re* > 70 (fully rough/turbulent)

### Galileo Number (Grain Reynolds)
```
G = √[ρ_f (ρ_s - ρ_f) g d³] / η
```
Where:
- `η` = dynamic viscosity

**Interpretation:** Ratio of gravity-to-viscosity forces on a grain. Scales as √g.

### Density Ratio
```
s = ρ_p / ρ_f
```
- Water: s ≈ 2.65 (quartz)
- Air: s ≈ 2650 (quartz), but s ≈ 10⁶–10⁷ for small particles (Brownian regime)

## Atmospheric Scale Height
```
H = k_B × T / (m × g)
```
Where:
- `k_B` = Boltzmann constant (1.38×10⁻²³ J/K)
- `T` = temperature (K)
- `m` = mean molecular mass of air (~4.8×10⁻²⁶ kg for N₂)
- `g` = gravitational acceleration

**Examples:**
- Earth (g=9.81, T=288K): H ≈ 8.4 km
- Mars (g=3.71, T=210K): H ≈ 11.1 km
- Moon (g=1.62, T=250K): H ≈ 32 km
- Titan (g=1.35, T=94K): H ≈ 40 km

## Rayleigh Number (Natural Convection)
```
Ra = (g × β × ΔT × L³) / (ν × α)
```
Where:
- `β` = thermal expansion coefficient (1/T for ideal gas)
- `ΔT` = temperature difference
- `L` = characteristic length
- `ν` = kinematic viscosity
- `α` = thermal diffusivity

**Critical threshold:** Ra > 1708 (onset of convection). Scales linearly with g.
- Earth: convection in 10–100 m layers
- Mars (0.38g): convection requires 2.6× larger ΔT or 2.6× deeper layer

## Sediment Transport Regimes by Gravity

### Water-Driven Transport (Subaqueous)
| Gravity | Critical Shields | Typical d (mm) | Transport Mode |
|---------|-----------------|----------------|----------------|
| Earth (1g) | 0.03–0.05 | 0.1–2.0 | Bedload, suspended load |
| Mars (0.38g) | 0.08–0.12 | 0.05–1.5 | More suspended load favored |
| Titan (0.14g) | 0.25–0.40 | 0.01–0.5 | Dominantly suspended |

### Wind-Driven Transport (Aeolian)
| Gravity | Critical Shields | d_threshold (μm) | Saltation Energy |
|---------|-----------------|------------------|------------------|
| Earth (1g) | 0.1–0.3 | 100–500 | Standard aeolian processes |
| Mars (0.38g) | 0.3–0.8 | 100–500 | Similar transport despite lower density |
| Titan (0.14g) | 0.8–2.0 | 100–500 | Very limited saltation (CO₂ atmosphere) |

## Reduced-Gravity Effects

### Key Scaling Relationships
1. **Scale height:** H ∝ 1/g → atmospheres expand vertically at low gravity
2. **Convective vigor:** Ra ∝ g → convection weaker at low gravity
3. **Sediment threshold:** Θ_c ∝ 1/g → easier to move particles at low gravity (given same τ_b)
4. **Settling velocity:** v_settling ∝ g → particles settle slower at low gravity

### Critical Gravity Thresholds
- **g < 0.14g_Earth (Titan-like):** Convection becomes sluggish; dust stays suspended for weeks
- **g < 0.05g_Earth (asteroid):** No sustained convection; atmosphere collapses quickly
- **g > 0.38g_Earth (Mars-like):** Fluidized sediment transport possible; "rain" can erode

## Application to Laguna Physics

### Gravity Scaling for Splat Transport Thresholds
When modeling laguna particle splats under variable gravity:
1. **Shields threshold scales:** Use `Θ_c(g) = Θ_c(Earth) × (g_Earth / g)`
2. **Scale height scales:** `H(g) = H_Earth × (g_Earth / g)`
3. **Rayleigh threshold:** `Ra = 1708 × (g / g_Earth)` for onset of convection

### Example: Mars-Sized Laguna (g = 3.71 m/s²)
- Scale height H ≈ 11 km (vs Earth's 8.4 km)
- Sediment threshold Θ_c ≈ 2× higher → need ~2× higher shear stress to move grains
- Rayleigh number threshold Ra_c = 1708 × 0.38 ≈ 650
- Convecting layer must be ~2.6× deeper than Earth for same ΔT

## Sources
1. Pähtz, T., Clark, A.H., Valyrakis, M., & Durán, O. (2020).
   "The physics of sediment transport initiation, cessation, and entrainment across aeolian
   and fluvial environments." *Reviews of Geophysics*, 58(1), e2019RG000679.
   - Shields criterion, threshold numbers, density ratio effects
2. Martin, R.L. & Kok, J.F. (2017).
   "Wind-invariant saltation heights imply linear scaling of aeolian saltation flux with shear
   stress." *Science Advances*, 3(6), e1602569.
   - Scale height, aeolian transport scaling with gravity
3. Amy, L. & Dorrell, R.M. (2020).
   "Equilibrium sediment transport, grade and discharge for suspended-load-dominated flows
   on Earth, Mars and Titan." *Icarus*, 354, 114243.
   - Reduced-gravity sediment transport, Shields criterion across planets
4. Bagnold, R.A. (1941).
   "The physics of blown sand and raised surfaces."
   *Proceedings of the Royal Society A*, 179, 314–335.
   - Foundational aeolian physics, critical shear stress
5. Shields, G. (1936).
   "An improved method for the mathematical specification of soil movement."
   *Proceedings of the 2nd Hydraulics Conference*, ASCE, 131–155.
   - Original Shields diagram and criterion
