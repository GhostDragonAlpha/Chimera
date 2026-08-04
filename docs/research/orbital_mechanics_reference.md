# Keplerian Orbital Mechanics — Reference

## Purpose
Reference card for orbital mechanics constants and Hohmann transfer calculations
relevant to theNavigate and orbital mechanics in the laguna system.

## Standard Gravitational Parameters (μ = G×M, km³/s²)

| Body | μ (km³/s²) | Radius (km) | Notes |
|------|------------|-------------|-------|
| **Earth** | **398.600** | 6,371 (mean) | 3.986004418×10⁵ m³/s² |
| **Moon** | 4.904 | 1,737 (mean) | 4.9028×10³ m³/s² |
| **Mars** | 42.832 | 3,390 (mean) | 4.2828×10⁴ m³/s² |
| **Sun** | 132,712,440 | 695,700 | 1.32715×10¹¹ m³/s² |
| **Jupiter** | 126,686 | 69,911 | |
| **Saturn** | 37,931 | 58,232 | |

## Orbital Velocity Formulas

### Circular orbit velocity
```
v = √(μ/r)
```
where `r` = orbital radius (planet center to spacecraft) = R_planet + altitude

### Escape velocity
```
v_esc = √(2μ/r)
```

## Key Orbital Velocities

### Low Earth Orbit (LEO, 400 km altitude)
- `r = 6,371 + 400 = 6,771 km`
- `v_LEO = √(398,600 / 6,771) = 7.67 km/s`
- Orbital period: `T = 2π√(r³/μ) = 5,542 s ≈ 92.4 min`

### Geostationary Earth Orbit (GEO, 35,786 km altitude)
- `r = 6,371 + 35,786 = 42,157 km`
- `v_GEO = √(398,600 / 42,157) = 3.07 km/s`
- Orbital period: 24 hours (synchronous)

### Moon's orbit (around Earth, 384,400 km)
- `v_Moon = √(398,600 / 384,400) = 1.02 km/s`

### Mars circular orbit (4,000 km altitude)
- `r = 3,390 + 4,000 = 7,390 km`
- `v_Mars = √(42,832 / 7,390) = 2.40 km/s`

### Earth's orbit around Sun
- `r = 1 AU = 149,597,870 km`
- `v_Earth = √(132,712,440 / 149,597,870) = 29.78 km/s`

### Mars' orbit around Sun
- `r = 1.524 AU = 227,939,200 km`
- `v_Mars_sun = √(132,712,440 / 227,939,200) = 24.13 km/s`

## Escape Velocities

| Body | Surface | LEO | Notes |
|------|---------|-----|-------|
| Earth | 11.18 km/s | ~10.3 km/s (from 400 km) | Including gravity & drag losses |
| Moon | 2.38 km/s | ~2.3 km/s | |
| Mars | 5.03 km/s | ~4.7 km/s (from 400 km) | |

## Sphere of Influence (SOI) Radii
```
r_SOI ≈ a × (m/M)^(2/5)
```
where `a` = semi-major axis of planet's orbit around Sun, `m` = planet mass, `M` = Sun mass.

| Body | SOI Radius (km) | Notes |
|------|-----------------|-------|
| **Earth** | **929,000** | Region where Earth gravity dominates |
| **Moon** | **66,200** | From Earth; Moon orbits within Earth's SOI |
| **Mars** | **579,000** | |

## Hohmann Transfer

### Formula
For transfer between two circular orbits with radii `r₁` (inner) and `r₂` (outer):

```
Transfer semi-major axis: a = (r₁ + r₂) / 2

Velocity on transfer ellipse at periapsis:
  v_t1 = √(μ × (2/r₁ - 1/a))

Velocity on transfer ellipse at apoapsis:
  v_t2 = √(μ × (2/r₂ - 1/a))

Circular velocity at start: v_1 = √(μ/r₁)
Circular velocity at end:   v_2 = √(μ/r₂)

First burn Δv₁ = |v_t1 - v_1|   (raise apoapsis)
Second burn Δv₂ = |v_2 - v_t2|   (circularize)
Total Δv = Δv₁ + Δv₂

Transfer time: t = π × √(a³/μ)  (half the orbital period of the transfer ellipse)
```

### Worked Example: LEO → GEO

```
r₁ = 6,771 km (LEO, 400 km altitude)
r₂ = 42,157 km (GEO)

a = (6,771 + 42,157) / 2 = 24,464 km

v_1 = √(398,600 / 6,771) = 7.674 km/s
v_2 = √(398,600 / 42,157) = 3.075 km/s

v_t1 = √(398,600 × (2/6771 - 1/24464)) = √(398,600 × 0.0001649) = 10.156 km/s
v_t2 = √(398,600 × (2/42157 - 1/24464)) = √(398,600 × 0.00001329) = 1.622 km/s

Δv₁ = 10.156 - 7.674 = 2.482 km/s
Δv₂ = 3.075 - 1.622 = 1.453 km/s
Total Δv = 3.935 km/s

Transfer time: t = π × √(24464³/398600) = 5.83 hours
```

### Worked Example: Earth → Mars (interplanetary Hohmann)

```
Earth orbit: r₁ = 1 AU = 149,597,870 km
Mars orbit:  r₂ = 1.524 AU = 227,939,200 km

Using heliocentric frame (μ_sun = 132,712,440 km³/s²):
a = (149,597,870 + 227,939,200) / 2 = 188,768,535 km

v_Earth = √(μ_sun/r₁) = 29.78 km/s
v_Mars  = √(μ_sun/r₂) = 24.13 km/s

v_t1 (departure)  = √(μ_sun × (2/r₁ - 1/a)) = 32.73 km/s
v_t2 (arrival)    = √(μ_sun × (2/r₂ - 1/a)) = 21.53 km/s

Δv_escape = v_t1 - v_Earth = 32.73 - 29.78 = 2.95 km/s (C3 = 8.7 km²/s²)
Δv_capture = v_Mars - v_t2 = 24.13 - 21.53 = 2.60 km/s

Total interplanetary Δv (ideal): ~5.55 km/s
PLUS: Earth escape (~3.2 km/s from LEO) and Mars capture (~2.6 km/s)
Total mission Δv: ~11.3 km/s (ideal, no margins)
```

## Earth-Moon Lagrange Points

| Point | Distance from Moon | Notes |
|-------|-------------------|-------|
| **L1** | 58,000 km from Moon | Between Earth-Moon; unstable equilibrium |
| **L2** | 64,500 km from Moon | Behind Moon; unstable equilibrium |
| **L3** | 381,000 km from Moon (far side) | Behind Earth; very unstable |
| **L4** | 381,000 km from Moon | 60° ahead in Moon's orbit; stable |
| **L5** | 381,000 km from Moon | 60° behind; stable |

## Δv Budget Summary

| Maneuver | Δv (km/s) | Notes |
|----------|-----------|-------|
| Earth surface → LEO | 9.3–10.0 | Including gravity & drag losses |
| LEO → GEO (Hohmann) | 3.94 | Pure Keplerian; no plane change |
| LEO → Earth-Moon L1 | ~4.0 | Direct transfer |
| LEO → Moon surface | ~6.0 | Lunar orbit insertion + descent |
| LEO → Mars transfer | 3.9 | Hohmann + escape |
| LEO → Mars surface | ~6.5 | Transfer + capture + descent |

## Sources
1. NASA. (2025). *Basics of Space Flight — Orbital Mechanics.*
   https://www.braeunig.us/space/orbmech.htm
2. Curtis, H. (2021). *Orbital Mechanics for Engineering Students.* 4th ed. Oxford.
   — Hohmann transfer derivation, Lagrange point calculations
3. NASA. (2009). *Mars Design Reference Architecture 5.0.* NASA/TM-2009-215322.
   — Δv budget tables, Mars transfer calculations
4. JPL. (2024). *Planetary Physical Parameters.*
   https://ssd.jpl.nasa.gov/planets/phys_par.html
5. Tsiolkovsky rocket equation. Wikipedia.
   https://en.wikipedia.org/wiki/Tsiolkovsky_rocket_equation
