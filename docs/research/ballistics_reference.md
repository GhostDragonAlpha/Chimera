# Ballistics — Reference

## Purpose
Reference card for external ballistics, drag modeling, and terminal effects relevant
to theShoot and theGun membranes.

## Drag Equation
```
F_d = ½ × ρ × v² × C_d × A

Where:
- F_d: drag force (N)
- ρ: air density (kg/m³) at altitude
- v: velocity (m/s)
- C_d: drag coefficient (dimensionless)
- A: cross-sectional area (m²)
```

### Drag Coefficient (C_d) by Projectile Shape
| Projectile | C_d (note) | Notes |
|------------|-----------|-------|
| Sphere (smooth) | 0.47 | Subsonic; Re < 2×10⁵ |
| Sphere (rough) | 0.4–0.5 | |
| Hemisphere (boat-tailed) | 0.2–0.3 | Supersonic optimal |
| Cone (ogive, 60°) | 0.15–0.3 | Typical .30–.50 caliber |
| Boat-tail spitzer (7.62mm) | 0.2–0.25 | Supersonic |
| Flat plate (normal) | 1.28 | Worst case |
| Streamlined body (bullet shape) | 0.1–0.3 | Boat-tailed spitzer |
| Cube | 1.05 | High drag, unsteady |

## Ballistic Coefficient (BC)

```
BC = m / (C_d × A)  [kg/m²]

Where:
- m: mass (kg)
- C_d × A: drag area

G1 ballistic coefficient (standard projectile shape):
BC_G1 = m / (i² × d²) — dimensionless form, where i is form factor
```

### Common Projectile BCs
| Caliber | Bullet | BC (G1) | BC (G7) |
|---------|--------|---------|---------|
| .308 Winchester | 168 gr HPBT | 0.480 | 0.240 |
| .30-06 | 180 gr SP | 0.404 | 0.200 |
| 5.56×45mm NATO | 62 gr SS109 | 0.307 | 0.150 |
| 7.62×39mm | 123 gr FMJ | 0.300 | 0.150 |
| .50 BMG | 700 gr AP | 0.600+ | 0.300 |
| 9mm Luger | 124 gr FMJ | 0.145 | 0.060 |
| .45 ACP | 230 gr FMJ | 0.165 | 0.080 |

## Standard Atmosphere (ICAO)

| Altitude | Pressure | Temp | Air Density | Notes |
|----------|----------|------|-------------|-------|
| Sea level | 1013.25 hPa | 15.0°C | 1.225 kg/m³ | Standard |
| 1,000 m | 899 hPa | 8.5°C | 1.112 kg/m³ | |
| 2,000 m | 795 hPa | 2.0°C | 1.007 kg/m³ | |
| 5,000 m | 540 hPa | −21.0°C | 0.736 kg/m³ | |
| 10,000 m | 265 hPa | −50.0°C | 0.414 kg/m³ | Tropopause |
| 15,000 m | 121 hPa | −56.5°C | 0.195 kg/m³ | |
| 20,000 m | 55 hPa | −56.5°C | 0.088 kg/m³ | |
| 30,000 m | 12 hPa | −44.5°C | 0.018 kg/m³ | |
| 50,000 m | 1 hPa | −2.5°C | 0.002 kg/m³ | |

## Bullet Drop Tables

### 5.56×45mm NATO (M855, 62 gr, BC = 0.307, muzzle velocity 940 m/s)
| Distance (m) | Drop (cm) | Windage (1 m/s crosswind, cm) | Time of Flight (s) |
|--------------|-----------|------------------------------|-------------------|
| 0 | 0 | 0 | 0.000 |
| 100 | -5.8 | +2.5 | 0.111 |
| 200 | -22.0 | +5.0 | 0.228 |
| 300 | -49.5 | +7.6 | 0.355 |
| 400 | -91.8 | +10.3 | 0.496 |
| 500 | -151.8 | +13.2 | 0.654 |
| 600 | -232.8 | +16.4 | 0.832 |
| 700 | -336.8 | +20.0 | 1.033 |
| 800 | -466.8 | +24.9 | 1.260 |
| 900 | -624.4 | +31.3 | 1.517 |
| 1000 | -811.2 | +40.2 | 1.810 |

### 7.62×51mm NATO (168 gr, BC = 0.480, muzzle velocity 820 m/s)
| Distance (m) | Drop (cm) | Windage (1 m/s crosswind, cm) | Time of Flight (s) |
|--------------|-----------|------------------------------|-------------------|
| 0 | 0 | 0 | 0.000 |
| 100 | -5.0 | +2.8 | 0.138 |
| 200 | -18.0 | +5.6 | 0.288 |
| 300 | -40.3 | +8.5 | 0.454 |
| 400 | -73.2 | +11.4 | 0.640 |
| 500 | -118.4 | +14.4 | 0.848 |
| 600 | -178.5 | +17.6 | 1.080 |
| 700 | -256.5 | +21.1 | 1.340 |
| 800 | -355.5 | +25.0 | 1.632 |
| 900 | -479.2 | +30.3 | 1.961 |
| 1000 | -632.5 | +40.3 | 2.332 |

### .50 BMG (700 gr, BC = 0.600, muzzle velocity 820 m/s)
| Distance (m) | Drop (cm) | Time of Flight (s) |
|--------------|-----------|-------------------|
| 100 | -4.0 | 0.136 |
| 500 | -97.0 | 0.787 |
| 1000 | -580 | 2.05 |
| 1500 | -1,480 | 3.96 |
| 2000 | -3,040 | 6.52 |

## Terminal Ballistics

### Sectional Density (SD)
```
SD = m / (d² × 7000) × 0.01  [in⁻¹]

Where:
- m: bullet mass (grains)
- d: caliber (inches)

Higher SD = deeper penetration
```

| Bullet | Mass (gr) | Caliber (in) | SD |
|--------|-----------|-------------|-----|
| .308 Win 168 gr | 168 | 0.308 | 0.240 |
| .30-06 180 gr | 180 | 0.308 | 0.260 |
| 5.56mm 62 gr | 62 | 0.224 | 0.118 |
| 7.62mm 150 gr | 150 | 0.308 | 0.220 |
| 9mm 124 gr | 124 | 0.355 | 0.170 |
| .45 ACP 230 gr | 230 | 0.451 | 0.250 |

### Penetration Depth (Fujii model for human tissue equivalent)
```
P = (m × v²) / (d² × σ_t)

Where:
- P: penetration depth (mm)
- m: mass (grams)
- v: impact velocity (m/s)
- d: diameter (mm)
- σ_t: tissue resistance (~0.1–0.2 MPa for muscle-equivalent)
```

## Muzzle Energy
```
E = ½ × m × v²

Where:
- E: energy (Joules)
- m: bullet mass (kg)
- v: muzzle velocity (m/s)
```

### Common Cartridge Energies
| Cartridge | Bullet Mass | MV (fps) | Muzzle Energy (ft⋅lbf) | Energy (J) |
|-----------|-------------|----------|----------------------|------------|
| .223 Rem | 55 gr | 3,250 | 1,280 | 1,730 |
| 5.56×45mm | 62 gr | 3,100 | 1,300 | 1,760 |
| 7.62×39mm | 123 gr | 2,350 | 1,500 | 2,030 |
| 7.62×51mm | 168 gr | 2,750 | 2,800 | 3,790 |
| .308 Win | 168 gr | 2,720 | 2,760 | 3,740 |
| .30-06 | 180 gr | 2,790 | 3,260 | 4,420 |
| .50 BMG | 700 gr | 2,800 | 12,270 | 16,630 |
| 9mm Luger | 124 gr | 1,180 | 381 | 517 |
| .45 ACP | 230 gr | 830 | 355 | 482 |

## Supersonic Effects

### Drag Divergence & Drag Divergence Mach Number
```
M_dd ≈ 1 / cos(Λ) × [2 / (γ−1) × ((2/(γ+1))^((γ−1)/(γ+1)) - 1)]^(-1/2)

For a bullet (Λ ≈ 0°, nose first):
M_dd ≈ 1/(sqrt(γ) * (γ+1)/2)^((γ+1)/(2(γ−1)))
≈ 1.01 for γ = 1.4 (air)
```

### Critical Mach Number (bullet)
```
M_crit ≈ 1.0–1.2 (smooth bullets, 15° half-angle)
```

### Transonic Region (M ≈ 0.8–1.4)
- **Significant drag divergence**
- Unpredictable trajectory — avoid firing transonic bullets at long range
- **Recommended max effective range for .308 Win ~800m** (stays supersonic)

## Gravity Drop
```
Vertical drop = ½ × g × t²

Where:
- g = 9.81 m/s² (standard gravity)
- t = time of flight

Note: bullet also curves in horizontal plane due to Coriolis effect:
δ = (Ω × v) × t²  [m], where Ω = Earth's rotation rate
```

## Application to theShoot and theGun

### Effective Range (Rule of Thumb)
- **5.56mm**: 500–600 m effective; 800 m max (stays supersonic)
- **7.62mm**: 800 m–1000 m effective; 1200 m max
- **.50 BMG**: 1500–2000 m effective; 2000+ m max

### Energy Retention
| % of Muzzle Energy | 5.56mm | 7.62mm | .50 BMG |
|---------------------|--------|--------|---------|
| At 100 m | 90% | 92% | 95% |
| At 300 m | 65% | 70% | 85% |
| At 500 m | 45% | 55% | 70% |
| At 1000 m | 25% | 35% | 50% |

## Sources
1. McCoy, R. (2016). *Modern Exterior Ballistics* (2nd ed.). Lulu Press.
   - Comprehensive treatment of drag functions, ballistic coefficients
2. Courtney, M. & Courtney, E. (2013). "Explicit approximations for external ballistics
   problems using the point-mass equations." *arXiv:1303.0147*.
   - Closed-form solutions for bullet drop, windage
3. Grittner, F. (2020). "Air drag and projectile motion — A numerical approach to
   realistic trajectories." *arXiv:2004.03662*.
   - Numerical integration of drag
4. Litz, Bryan. (2023). *Applied Ballistics for Long Range Shooting* (4th ed.).
   Applied Ballistics LLC. — Ballistic coefficient tables, drop charts
5. NATO standardization document Allied Ammunition Publication (AEP-01)
   — Standard ballistic coefficients for NATO ammunition
