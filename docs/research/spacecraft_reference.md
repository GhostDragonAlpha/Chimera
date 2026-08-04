# Spacecraft Design Parameters — Reference

## Purpose
Reference card for spacecraft structural mass fractions, specific impulse, and delta-v
budgets relevant to theShip, theShipCombat, and theFlight membranes.

## Structural Mass Fraction

The **mass fraction** = inert mass / propellant mass. The **structural mass fraction**
(dry/wet) is distinct and mission-dependent.

### Stage-Level Structural Mass Fractions

| Propulsion Type | Inert Mass Fraction* | Notes |
|-----------------|---------------------|-------|
| LOX/LH2 (cryogenic) | 9–11% | Best Isp; tanks heavy due to insulation |
| LOX/RP-1 (kerosene) | 8–10% | Denser; simpler; cheaper |
| LOX/CH4 (methane) | 10–12% | ISRU-friendly; moderate Isp |
| LOX/N₂O₄ (storable) | 12–15% | Throttleable; long-term storage |
| Solid rocket | 15–20% | Simple; cannot throttle; high thrust |
| Nuclear thermal (NTR) | 10–15% | Isp ~900 s; reactor mass penalty |
| Ion thruster (Xenon) | 30–40% | Power processing dominates; high Isp |

*Inert = tanks + engines + structure (no propellant, no payload)

### Whole-Vehicle Dry/Oxidizer-Fuel Ratios

| Vehicle | Dry/Wet | Payload/Wet | Notes |
|---------|---------|-------------|-------|
| Falcon 9 Block 5 | 22% | 4–5% | Reusable; 25% margin for landing |
| Atlas V 401 (SL) | 20% | ~3% | |
| SLS Block 1 | ~19% | ~4% | 8.8 MSLE to LEO |
| Starship | ~10% | ~10% | Fully reusable; 100–150 t payload |
| Apollo CSM | ~22% | ~5% | 4–5 t dry, 25 t total |

## Specific Impulse (I_sp) Values

| Engine Type | Propellants | I_sp (s) | Isp (vacuum) | Notes |
|-------------|------------|----------|--------------|-------|
| RL-10 | LOX/LH2 | — | 451–462 | Upper stage |
| SSME / RS-25 | LOX/LH2 | 366 (sl) | 452 (vac) | Shuttle main engine |
| Merlin 1D | LOX/RP-1 | 282 (sl) | 311 (vac) | Falcon 9 1st stage |
| Merlin Vacuum | LOX/RP-1 | — | 348 (vac) | Falcon 9 2nd stage |
| F-1 | LOX/RP-1 | 263 (sl) | 304 (vac) | Saturn V 1st stage |
| R-25 | NTO/MMH | — | 462 | Space Shuttle OMS (storable) |
| NERVA (historical) | H₂/H₂ | — | 850–1000 | Nuclear thermal |
| NEXT (ion) | Xe/Xe | — | 4190 | NSTAR follow-on |
| NSTAR (ion) | Xe/Xe | — | 3160 | Dawn spacecraft |
| Hall thruster | Xe/Xe | — | 1500–3500 | Typical: 2000–3000 s |
| **LOX/LH2 typical** | — | ~350–450 | 450 | Most efficient chemical |
| **LOX/RP-1 typical** | — | ~300–340 | 330 | Most common launch |
| **Solid typical** | — | ~250–300 | 280 | Simple, high thrust |
| **NTR (projected)** | H₂/H₂ | — | 900 | Mars missions |

## Rocket Equation (Tsiolkovsky)
```
Δv = I_sp × g₀ × ln(m₀ / m_f)

Where:
- I_sp = specific impulse (seconds)
- g₀ = 9.80665 m/s² (standard gravity)
- m₀ = initial "wet" mass (with propellant)
- m_f = final "dry" mass (without propellant)
- ln = natural logarithm

Mass ratio: m₀/m_f = e^(Δv / (I_sp × g₀))
```

### Worked Example: LEO → Moon
```
Stage: LOX/LH2 upper stage, I_sp = 450 s
Required Δv from LEO: ~4.1 km/s (to achieve lunar transfer + capture)

m₀/m_f = e^(4100 / (450 × 9.807)) = e^(0.933) = 2.54

So 61% of the stage mass is propellant for this single maneuver.
```

### Worked Example: LEO → Mars
```
LEO → Earth escape: Δv ≈ 3.2 km/s
Earth escape → Mars capture: Δv ≈ 2.9 km/s
Mars capture → Mars surface: Δv ≈ 1.5–3.0 km/s (aerobraking reduces this)
Total ideal Δv: ~7.6–8.6 km/s

For LOX/LH2 (I_sp=450s): m₀/m_f = e^(8000/(450×9.807)) = e^(1.814) = 6.13
Requires 6.13× mass ratio — very challenging for single stage.
```

## Delta-v Budgets

| Maneuver | Δv (km/s) | Notes |
|----------|-----------|-------|
| Earth surface → LEO | 9.3–10.0 | Including gravity + drag losses |
| LEO → GEO (Hohmann) | 3.9 | Two-burn maneuver |
| LEO → LEO (inclination change) | ~3.1 × sin(Δi/2) | For Δi = 28°: ~1.4 km/s |
| LEO → Earth-Moon L1 | 4.0 | Direct transfer |
| **LEO → Moon surface** | **~6.0** | Orbit insertion + descent |
| **LEO → Mars transfer** | **~3.9** | Hohmann transfer |
| **Mars transfer → Mars capture** | **~2.9** | Braking into Mars orbit |
| **Mars capture → Mars surface** | **~1.5–3.0** | Aerocapture reduces Δv greatly |
| **Mars surface → Mars orbit** | **~4.1** | Ascent (Mars DRA 5.0) |
| **Earth-Moon L1 → Earth** | **~0.9** | Return (low energy) |

## Life Support Requirements

| Parameter | Value | Per Crew | Notes |
|-----------|-------|----------|-------|
| O₂ consumption | 0.84 kg/day | 0.84 kg/day | 550 L/day at STP |
| CO₂ production | 0.96 kg/day | 0.96 kg/day | 1.0 kg ≈ 530 L at STP |
| H₂O consumption | 2.5–3.5 kg/day | 2.5–3.5 kg/day | Drinking + hygiene |
| H₂O recovery rate | 85–95% | — | ISS level |
| Food mass | 1.2–1.5 kg/day | 1.2–1.5 kg/day | Packaged; 500 kcal/kg |
| Waste management | 1.0 kg/day | 1.0 kg/day | Solid waste |
| **Total consumables** | **~6.0 kg/person/day** | For 30-day mission: ~180 kg/person |

### Power Requirements for Life Support
| System | Power | Per Crew | Notes |
|--------|-------|----------|-------|
| O₂ generation (electrolysis) | 3–4 kW | 3–4 kW | Splits H₂O → O₂ + H₂ |
| CO₂ scrub (Sabatier/ESD) | 0.5–1 kW | 0.5–1 kW | LiOH or Sabatier reactor |
| Water reclamation | 1–2 kW | 1–2 kW | Filtration + distillation |
| Thermal control | 2–5 kW | 2–5 kW | Radiators + pumps |
| **Total life support** | **7–13 kW** | For a 4-person crew: ~40–50 kW |

## Key Spacecraft Design Guidelines

### Tsiolkovsky's Dictum (Δv scales exponentially)
```
m₀/m_f = e^(Δv/(I_sp·g₀))

Δv = 3 km/s, I_sp=300s → m₀/m_f = 2.7  (manageable)
Δv = 9 km/s, I_sp=300s → m₀/m_f = 22   (impossible in one stage)
```

### Multi-Stage Advantage
```
Two stages, each with I_sp=300s, 2 stages with Δv=4.5 km/s each:

Stage 2: m₀/m_f = e^(4500/(300×9.807)) = e^(1.53) = 4.62
Stage 1: m₀/m_f = e^(4500/(300×9.807)) = e^(1.53) = 4.62

Total: m₀/m_f = 4.62 × 4.62 = 21.4

Single stage would need m₀/m_f = 21.4 for the same Δv.
```

### Payload Fraction
```
Payload fraction = m_payload / m₀

For a 2-stage vehicle:
m_payload/m₀ = (m_f1 - m₀2) / m₀ = m₀2/m₀1 × m_f2/m₀2 × ... 
```

## Mars DRA 5.0 Reference Architecture (2009)
```
IMLEO = Initial Mass in Low Earth Orbit (total mission mass)
Δv total: ~15 km/s for Earth-Mars roundtrip
ISRU: In-Situ Resource Utilization for Mars ascent propellant
```

## Sources
1. NASA. (2009). *Mars Design Reference Architecture 5.0.* NASA/TM-2009-215322.
   - Δv budgets, ISRU, life support power requirements
2. NASA. (2019). "Small Launch Vehicle Sizing Analysis with Solid Rocket Examples."
   NASA/TM-2019-220244.
   - Structural mass fractions, inert mass fractions
3. Tsiolkovsky rocket equation. Wikipedia.
   https://en.wikipedia.org/wiki/Tsiolkovsky_rocket_equation
   - Rocket equation derivation
4. NASA. (2025). *Space Transportation Systems.*
   — Specific impulse values for chemical, nuclear, and electric propulsion
