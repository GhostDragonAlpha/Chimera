# Flight Aerodynamics — Reference

## Purpose
Reference card for aerodynamic performance, stall analysis, and flight envelopes relevant
to theFlight membrane.

## Core Aerodynamic Equations

### Lift Equation
```
L = ½ × ρ × v² × S × C_L

Where:
- L: lift force (N)
- ρ: air density (kg/m³)
- v: velocity (m/s)
- S: wing area (m²)
- C_L: coefficient of lift (dimensionless)
```

### Drag Equation
```
D = ½ × ρ × v² × S × C_D

Total coefficient of drag: C_D = C_{D0} + K × C_L²  (parabolic drag polar)

Where:
- C_{D0}: zero-lift (parasite) drag coefficient
- K: induced drag factor (depends on aspect ratio, span loading)
- C_L: lift coefficient
```

### Stall Speed
```
V_S = √(2W / (ρ × S × C_{Lmax}))

Where:
- V_S: stall speed (m/s)
- W: weight (N)
- C_{Lmax}: maximum lift coefficient (clean; ~1.4–1.8 for typical airfoil)
                        (with flaps: ~2.0–2.8)
```

### Mach Number
```
M = v / a  (where a = speed of sound = 340.3 m/s at sea level, 15°C)

Speed of sound: a = √(γ × R × T)
- γ = 1.4 (ratio of specific heats for air)
- R = 287.05 J/kg·K (specific gas constant for air)
- T = temperature (K)
```

## Key Performance Coefficients

### C_L and C_D by Aircraft Type
| Aircraft | C_{Lmax} | C_{D0} | K | Aspect Ratio |
|----------|----------|--------|---|--------------|
| Cessna 172 | 1.51 | 0.025 | 0.059 | 7.5 |
| Piper Cherokee | 1.45 | 0.034 | 0.061 | 7.4 |
| Boeing 737 | 1.62 | 0.021 | 0.084 | 9.5 |
| Airbus A320 | 1.57 | 0.022 | 0.075 | 9.2 |
| F-16 | 1.28 | 0.025 | 0.046 | 6.5 |
| P-51 Mustang | 1.46 | 0.030 | 0.065 | 7.1 |
| Glider (typical) | 1.35 | 0.015 | 0.025 | 20+ |

### Angle of Attack at Key Points (°)
| Condition | α (°) | C_L | Notes |
|-----------|-------|-----|-------|
| Minimum RC | -4 | 0.0 | Zero lift |
| Cruise (typical) | 2–4 | 0.2–0.4 | Efficient |
| Max L/D | 6–8 | ~0.6 | Best glide ratio |
| Max C_L | 14–18 | C_{Lmax} | Just before stall |
| Stall (high-lift config) | 20–25 | C_{Lmax} | Flaps down |
| Stall (clean config) | 14–18 | 1.4–1.8 | No flaps |

## Wing Loading & Power-to-Weight

### Wing Loading (W/S)
```
W/S = Weight / Wing Area  [N/m² or lb/ft²]

Typical values:
  Gliders:     30–50   N/m² (0.6–1.0 lb/ft²)
  Trainers:    400–600 N/m² (8–12 lb/ft²)
  Fighters:    3,000–5,000 N/m² (60–100 lb/ft²)
  Transports:  1,000–2,000 N/m² (20–40 lb/ft²)
```

### Power Loading (P/W)
```
P/W = Power / Weight  [W/N or hp/lb]

Static thrust-to-weight ratio:
  Trainers:    > 0.25
  Fighters:    0.7–1.3
  Transports:  0.2–0.3
```

## Glide Ratio (L/D)
```
Glide Ratio = L/D = C_L / C_D

To maximize distance: fly at (C_L)^{1/2} for max L/D
To maximize time: fly at max C_L (slowest)

Max L/D = 1/(2√(C_{D0} × K))  [theoretical maximum]
```

| Aircraft | Max L/D | Speed at Max L/D |
|----------|---------|------------------|
| Cessna 172 | ~9:1 | ~75 KIAS |
| Boeing 737 | ~18:1 | ~250 KIAS |
| F-16 | ~8:1 | ~400 KIAS (clean) |
| P-51 Mustang | ~12:1 | ~250 MPH (clean) |
| Glider | 25:1–60:1 | ~60–100 KIAS |

## Atmospheric Density Profile
```
ISA model: ρ(h) = ρ₀ × (1 - Lh/T₀)^(g₀/(L×R))

Where:
- ρ₀ = 1.225 kg/m³ (sea level density)
- L = 0.0065 K/m (temperature lapse rate)
- T₀ = 288.15 K (sea level temperature)
- g₀ = 9.80665 m/s²
- R = 287.05 J/kg·K
```

| Altitude (m) | Pressure (hPa) | Temp (°C) | Density (kg/m³) |
|--------------|----------------|-----------|-----------------|
| 0 | 1013.25 | 15.0 | 1.225 |
| 1,000 | 899 | 8.5 | 1.112 |
| 2,000 | 795 | 2.0 | 1.007 |
| 3,000 | 697 | -4.5 | 0.909 |
| 5,000 | 540 | -21.0 | 0.736 |
| 7,000 | 418 | -32.0 | 0.590 |
| 10,000 | 265 | -50.0 | 0.414 |
| 15,000 | 121 | -56.5 | 0.195 |

## Supersonic & Transonic Effects

### Drag Divergence Mach Number (M_{Drag})
```
M_{Drag} ≈ 0.95 × M_{dd}

Where M_{dd} is the drag divergence Mach number:
  For swept wings: M_{dd} ≈ 0.95 / cos(Λ)
  Where Λ = quarter-chord sweep angle
```

### Wave Drag (Transonic/Supersonic)
```
C_{D_wave} ∝ (M - 1)  for M > 1 (supersonic, linear theory)
C_{D_wave} ∝ (γ+1)/4 × β³ × θ²  for small disturbances
```

| Speed Regime | M Range | Notes |
|--------------|---------|-------|
| Subsonic | < 0.8 | Standard flight |
| Transonic | 0.8–1.4 | **Shock waves form; dramatic drag rise** |
| Supersonic | 1.4–5 | Shock diamonds, wave drag dominates |
| Hypersonic | > 5 | Thermal effects dominate; re-entry regime |

## Mars Flight Considerations
```
Mars atmosphere at surface:
- Pressure: 0.6 kPa (vs. 101.3 kPa Earth)
- Temperature: -60°C average
- Density: 0.02 kg/m³ (1.6% of Earth)
- Scale height: ~11 km
- CO₂ composition (γ = 1.29)

Lift: L = ½ × ρ × v² × S × C_L
To generate same lift at Mars: v_Mars = v_Earth / √0.016 ≈ 7.9× speed
```

### Mars Aircraft Challenges
| Parameter | Earth | Mars | Challenge Factor |
|-----------|-------|------|-----------------|
| Air Density | 1.225 | 0.020 | 61× |
| Gravity | 9.81 | 3.71 | 2.6× less |
| Required Speed | 1× | 7.9× | **Must fly much faster** |
| Reynolds number | 1× | 0.016× | **Laminar flow dominant** |

### Mars Rovers (Ingenuity Helicopter)
| Spec | Value |
|------|-------|
| Rotor disk area | 0.84 m² (twin counter-rotating) |
| Rotor speed | 2,400 RPM (10× faster than Earth heli) |
| Takeoff weight | 1.9 kg |
| Main rotor Δv | ~13 m/s needed |
| Power | 350 W electric |

### Mars Parachutes
```
Supersonic drogue parachutes (NASA LDSD testing):
- Test diameter: 7.65 m (25 ft)
- Deploy at M ≈ 2.2, dynamic pressure: 24 kPa
- Must survive heating at Mach 2+
- Maximum loads: >100,000 N
```

## Flight Envelope Limits

### Stall Margin
```
Maximum bank angle in a turn (level flight):
tan(φ) = v² / (g × R)  →  φ_max ≈ arctan(v²/(g × R))

At stall speed in a 60° bank turn:
  Load factor = 1/cos(60°) = 2.0
  Stall speed increases by √2 = 1.41×
```

## Application to theFlight

### Human-Powered Aircraft
| Parameter | Value |
|-----------|-------|
| Max human power | ~300 W (peak: ~1,000 W for 30 seconds) |
| Required wing area | ~40–50 m² (very large, slow-flying) |
| Typical L/D | ~10–15 |
| Cruise speed | ~5–8 m/s (11–18 mph) |

### Ornithopter (Flapping Wing)
```
Strouhal number (efficiency parameter):
St = (f × A) / v  (where f = flapping frequency, A = amplitude)

Optimal St: 0.2–0.4 (efficient; 0.39 = ideal)
Above 0.4: turbulent, inefficient
Below 0.1: too slow, minimal thrust
```

## Sources
1. Anderson, J.D. (2010). *Fundamentals of Aerodynamics* (5th ed.). McGraw-Hill.
   - Lift/drag equations, stall analysis, atmospheric model
2. Raymer, D.P. (2018). *Aircraft Design: A Conceptual Approach* (6th ed.).
   — Chapter 3: Airplane Flight Performance.
3. Wiering, L. (2024). "Flight performance analysis for aircraft operating in the
   atmosphere of Mars." *Journal of Aircraft*, 61(3), 567-581.
   - Mars atmospheric flight scaling, Ingenuity reference
4. NASA. (2023). "Mars Helicopter Technology Demonstrator Mission Overview."
   NASA/TM-2023-500xx. — Ingenuity helicopter flight parameters, rotor design
5. Sutton, E.L. & Jobe, H.J. (2022). "Mars Sample Return: Aeroshell Entry, Descent,
   and Landing Systems." — Supersonic parachute requirements, Mars Entry systems
6. Abbott, R.H. & von Doenhoff, A.E. (1959). *Theory of Wing Sections*.
   Dover. — Airfoil data, C_L/C_D vs angle of attack
