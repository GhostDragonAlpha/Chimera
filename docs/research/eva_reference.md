# EVA & Spacesuit Physics — Reference

## Purpose
Reference card for spacesuit constraints relevant to EVA physics in the laguna environment.

## EMU (Extravehicular Mobility Unit) — NASA Standard

### Operating Conditions
| Parameter | Value | Notes |
|-----------|-------|-------|
| Operating pressure | 29.6 kPa (4.3 psi) | Pure O₂ |
| Cabin pressure (ISS) | 101.3 kPa | 79% N₂, 21% O₂ — prebreath protocol needed |
| Max EVA duration | 7 hours | 8 hours with worst-case solar exposure |
| Prebreathe time | 40 min (10.2 psia cabin) to 4 hr (14.7 psia cabin) | Denitrogenation protocol |

### Mass Properties
| Component | Mass (lbs) | Mass (kg) | Notes |
|-----------|------------|-----------|-------|
| Hard Upper Torso (HUT, wet) | 29.6 | 13.4 | Fiberglass shell |
| Arm Assembly (both) | 22.2 | 10.1 | Pressurized joint bearings |
| Lower Torso Assembly | 59.7 | 27.1 | |
| PLSS (Primary Life Support, wet w/O₂) | 101.4 | 46.0 | Includes O₂ |
| DCM (Contingency Water) | 14.3 | 6.5 | |
| AAP (Auxiliary Applicator Pack) | 20.5 | 9.3 | |
| Liquid Cooling Vent Garment (wet) | 8.57 | 3.9 | |
| Helmet Assembly | 3.5 | 1.6 | |
| EMU Total (wet) | ~240 | ~109 | + suit wearer mass |

**Note:** "Mass ≠ weight" — on the Moon (0.17g) the suit weighs ~18 kg; on Mars (0.38g) ~41 kg.
On Earth, a suited astronaut weighs ~240 kg (including wearer).

### Metabolic Rates
| Activity | BTU/hr | Watts | Notes |
|----------|--------|-------|-------|
| Resting EVA | 350 | 103 | Minimum after work |
| Normal work | 850–1000 | 249–293 | Average |
| Peak work | 2000 | 588 | 15 min max |
| Apollo EVA (avg) | 1000 | 293 | Peak 2200 BTU/hr |
| ISS EVA (min) | 575 | 169 | (2025 NASA data) |
| ISS EVA (max) | 2232 | 654 | (2025 NASA data) |

### Oxygen Consumption
| Parameter | Value | Notes |
|-----------|-------|-------|
| O₂ consumption rate | ~0.8–1.2 kg/6–8 hr EVA | Varies with metabolic rate |
| O₂ delivered | Regulated pressure | 29.6 kPa (4.3 psia) suit pressure |
| Secondary O₂ Pack | 30 min backup | Emergency supply |

### Joint Torque & Range of Motion

#### EMU Joint Torques (from instrumented robot studies, Schmidt et al.)
| Joint | Max Torque (Nm) | Pressure | Notes |
|-------|----------------|----------|-------|
| Elbow flexion | ~20–40 Nm | 30 kPa (4.3 psi) | Hysteresis model |
| Shoulder flexion | ~30–50 Nm | 30 kPa | Depends on arm position |
| Knee flexion | ~25 Nm | 30 kPa | Measured at max flexion (100°) |
| Hip abduction | ~100–200 Nm | 30 kPa | Highest torque requirement |

#### Range of Motion (ROM)
| Joint | EMU ROM | Unsuited ROM | Reduction |
|-------|---------|--------------|-----------|
| Shoulder (flexion+abduction+rotation) | ~120° | ~180° | ~33% |
| Elbow flexion | ~100° | ~140° | ~29% |
| Hip flexion | ~90° | ~120° | ~25% |
| Knee flexion | ~100° | ~140° | ~29% |
| Waist rotation | ~90° | ~180° | ~50% |

### Thermal Extremes
| Environment | Temperature Range | Notes |
|-------------|-------------------|-------|
| LEO sunlight | -150°C to +120°C | Peak solar ~120°C |
| LEO shadow | ~-150°C | Radiative cooling |
| Lunar equator (day) | ~+120°C | |
| Lunar equator (night) | ~-150°C | |
| Lunar poles | ~-230°C to -50°C | Permanent shadow regions |

### Thermal Control Limits
| Parameter | Value |
|-----------|-------|
| Skin temp increase limit | 1.4°C (performance impairment begins) |
| Core temp increase limit | 0.6°C |
| Heat storage limit | 3.0 kJ/kg (upper) to -1.9 kJ/kg (lower) |
| Cooling method | Sublimator (water → ice → sublimate to vacuum) |

### Tether Safety
| Parameter | Value | Notes |
|-----------|-------|-------|
| Tether load rating | 4,000–10,000 N | Depends on tether type |
| Tether diameter | 12–16 mm | Polyethylene (Dyneema/Spectra) |
| Anchor point load | 2× body weight + safety factor | For restraint |
| Safety factor | 4–6× | Breaking strength over working load |

## Application to Laguna EVA
- **Pressure:** At 29.6 kPa pure O₂, prebreath protocols must be followed for any transition
  from a higher-pressure habitat. The decompression sickness risk is modeled by nitrogen
  bubble formation kinetics (Haldane model).
- **Mobility:** Joint torques create a "work envelope" — a 3D volume where a suited operator
  can comfortably reach. This limits the interaction distance with laguna surfaces.
- **Thermal:** Laguna temperature extremes depend on stellar irradiance. At 0.4g, convective
  heat transfer is reduced; thermal control relies more on conduction and sublimation.
- **Tether:** In reduced gravity, tether forces are lower, but dynamic loads from waves or
  atmospheric disturbance can still exceed tether ratings unpredictably.

## Sources
1. NASA Johnson Space Center. (2025). *Spacesuit: A User's Guide.* NASA Technical Standard.
   - EMU mass properties, operating pressure, metabolic rates
2. Schmidt, P.B., Newman, D.J., & Hodgson, E.W. (2000). "Modeling Space Suit Mobility."
   *AIAA* (ICES 01-2162).
   — EMU joint torque-angle database, hysteresis modeling
3. NASA. (2013). *Extravehicular Activity (EVA) Operations.* Chapter 5.4.
   — Thermal extremes, metabolic rates, tether requirements
