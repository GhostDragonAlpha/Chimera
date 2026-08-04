# Human Metabolic Rates & Life Support — Reference

## Purpose
Reference card for human metabolic rates, oxygen/CO₂/water/carbon needs, and life
support power budgets. Relevant to theBody, theShip, and theSuit membranes.

## Basal Metabolic Rate (BMR)

### Harris-Benedict Equation (Revised by Mifflin, 1990)
```
Men:   BMR = (10 × mass[kg]) + (6.25 × height[cm]) - (5 × age[y]) + 5
Women: BMR = (10 × mass[kg]) + (6.25 × height[cm]) - (5 × age[y]) - 161

Units: BMR in kcal/day, mass in kg, height in cm, age in years
```

### BMR for Standard Crew Members (NASA reference)
| Profile | Age | Mass | Height | BMR (kcal/day) | BMR (W) |
|---------|-----|------|--------|----------------|---------|
| Astronaut male (nominal) | 35 | 75 kg | 175 cm | 1,745 | 84.3 W* |
| Astronaut female | 35 | 65 kg | 168 cm | 1,400 | 67.5 W* |
| Crew average | — | 70 kg | 172 cm | 1,575 | 76.2 W* |

*Conversion: 1 kcal/day = 0.0485 W (24-hr average)

### Note on EVA Reference Cross-Reference
From `eva_reference.md`:
- **Metabolic power range in EVA** — not directly stated as BMR; instead the EVA doc
  gives O₂ consumption as 0.84 kg/day (≈ resting), and max 5 L/min O₂ during work.
- This file resolves the conflict: BMR ≈ 70–100 W; EVA work is 5–10× BMR.

## Activity Multipliers

| Activity | MET* | Power (W) | O₂ (L/min) | CO₂ (L/min) |
|----------|------|-----------|------------|-------------|
| Sleeping | 0.95 | ~70 W | 0.22 | 0.19 |
| Sitting quietly | 1.0 | ~75 W | 0.24 | 0.20 |
| Standing | 1.2 | ~90 W | 0.29 | 0.25 |
| Walking (3 mph) | 2.5 | ~185 W | 0.58 | 0.49 |
| Walking (4 mph) | 3.0 | ~225 W | 0.70 | 0.59 |
| RPE 13 (somewhat hard) | 4.6 | ~345 W | 1.07 | 0.91 |
| RPE 15 (hard) | 6.5 | ~485 W | 1.50 | 1.28 |
| RPE 17 (very hard) | 8.5 | ~638 W | 1.98 | 1.68 |
| Maximal effort | 10+ | ~750–1,000 W | 2.5–4.0 | 2.1–3.4 |
| Heavy lifting/loading | 6–8 | 450–600 W | 1.5–2.0 | 1.3–1.7 |

*MET = Metabolic Equivalent of Task (1 MET = 1 kcal/kg/hr = 1,162 W for 70 kg person)

### Power Conversion (Quick Reference)
```
1 W = 0.0086 kcal/min = 0.8604 kcal/day
75 kg person at 1 MET = 1 kcal/kg/hr = 70 kcal/hr = ~1.94 W average

Instantaneous power vs. BMR:
  Resting: 1× BMR
  Walking 4 mph: 3× BMR
  Hard work: 6–8× BMR
  Maximal exertion: 10× BMR
```

## Oxygen Consumption & Production Requirements

### Resting Oxygen Consumption
| Metric | Value | Notes |
|--------|-------|-------|
| **Rest O₂ consumption** | 0.25 L/min | 250 mL/min at rest |
| **Moderate activity O₂** | 1.0–2.0 L/min | Walking, light work |
| **Heavy work O₂** | 3.0–4.0 L/min | Load carrying, exercise |
| **Maximal O₂ uptake (VO₂ max)** | 4.0–5.0 L/min | Elite athlete: 6–7 L/min |
| **O₂ per day (resting)** | 0.36 kg | 360 L at STPD |
| **O₂ per day (moderate work)** | 1.0–2.0 kg | |
| **O₂ per day (heavy work)** | 4.0–6.0 kg | |

### Cross-reference with EVA
From `eva_reference.md`:
- O₂ consumption rate: 0.8–1.2 kg per 6–8 hr EVA period
- That implies ~150–200 L/hr = ~2.5–3.3 L/min
- This file resolves: EVA is moderate-to-heavy activity (MET ~ 4–5)

### Atmospheric O₂ Cabin Concentration
| Environment | O₂ % | Partial Pressure | Notes |
|------------|------|-----------------|-------|
| Earth sea level | 21% | 21.2 kPa | |
| ISS cabin | 21% | 21.2 kPa | Normal |
| EVA suit (EMU) | 100% | 29.6 kPa | Reduced total, high O₂ |
| Shuttle/ISS emergency | 100% | 30–100 kPa | |
| Hyperbaric therapy | — | 240–300 kPa | Medical |

## CO₂ Production & Removal

### Respiratory Quotient (RQ)
```
RQ = VCO₂ / VO₂ (volume CO₂ produced / volume O₂ consumed)

Typical RQ by substrate:
  Carbohydrate metabolism: RQ = 1.0
  Fat metabolism:          RQ = 0.7
  Protein metabolism:      RQ = 0.8
  Mixed diet:              RQ = 0.85 (default)
```

### Daily CO₂ Production
| Activity | O₂ (L/day) | RQ | CO₂ (L/day) | Mass (kg/day) |
|----------|------------|-----|-------------|---------------|
| Resting | 360 | 0.85 | 306 L | 0.41 kg |
| Moderate | 1,500 | 0.85 | 1,275 L | 1.70 kg |
| Heavy | 4,000 | 0.85 | 3,400 L | 4.55 kg |
| Astronaut (nominal) | ~1,000 | 0.85 | ~850 L | 1.13 kg |

## Water Requirements

### Daily Water Budget
| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Drinking water** | 2–3 L/day | |
| **Food moisture** | 0.5–1.0 L/day | From hydrated foods |
| **Metabolic water** | 0.3–0.5 L/day | Produced from oxidation (internal) |
| **Insensible losses** (lungs) | 0.35 L/day | |
| **Insensible losses** (skin) | 0.4 L/day | |
| **Sensible losses** (urine) | 1.5 L/day | Kidneys regulate |
| **Sensible losses** (feces) | 0.1–0.5 L/day | |
| **Sweat (active)** | 0.5–2.0 L/day | Depends heavily on activity |
| **Total daily water** | **3–4 L (drinking)** | ~3500–4000 mL total input needed |

## Caloric Requirements & Fuel Utilization

### Daily Caloric Needs
| Profile | Calories/day | Notes |
|---------|--------------|-------|
| Resting (male) | 2,000–2,500 kcal | |
| Resting (female) | 1,600–2,200 kcal | |
| Astronaut (moderate activity) | 2,500–3,000 kcal | |
| Astronaut (heavy EVA + exercise) | 3,500–4,000 kcal | |
| Elite endurance athlete | 4,000–6,000 kcal | |

### Fuel Utilization Ratio
```
Carbohydrate : Fat ratio shifts with intensity:
  At 25% VO₂ max: 50% carb / 50% fat
  At 50% VO₂ max: 65% carb / 35% fat
  At 75% VO₂ max: 85% carb / 15% fat
  Above 80% VO₂ max: >90% carb
```

## Heat Production & Dissipation

### Metabolic Heat (all energy becomes heat eventually)
```
Heat production rate P_heat = metabolic power (W)

At rest (~75 W): negligible if ventilated
At exercise (300–800 W): critical — can cause 1.5–4°C core rise per hour
```

### Heat Dissipation Pathways
| Method | Rate (W) | Conditions |
|--------|----------|------------|
| **Convection** | 50–200 W | Airflow critical; reduced in suits/vacuum |
| **Radiation** | 50–300 W | Depends on T_skin vs T_ambient difference |
| **Evaporation** (sweat) | 100–800 W | Most effective but requires air/water vapor exchange |
| **Conduction** (to surfaces) | 20–100 W | When skin contacts surfaces |
| **Insulation** (suit layers) | Reduces dissipation | EVA suits limit heat loss |

### Core Temperature Regulation
```
Safe core temp range: 36.5–37.5°C (normothermia)
Heat stress onset: core > 38.5°C (hyperthermia stage 1)
Danger zone: core > 40°C (heat stroke risk)
Cooling needed at: ~75 W metabolic + 75 W environmental load (hot suit/habitat)
```

## Life Support Power Requirements

### Atmospheric Control
| System | Power | Per Crew | Notes |
|--------|-------|----------|-------|
| O₂ generation (electrolysis) | 3–4 kW | 3–4 kW | Splits H₂O → O₂ + H₂ |
| CO₂ scrubbing (LiOH) | 0.1 kW | 0.1 kW | Passive (absorbent) |
| CO₂ scrubbing (Sabatier) | 0.5–1.0 kW | 0.5–1.0 kW | Regenerative |
| N₂/O₂ pressure control | 0.2–0.4 kW | 0.2–0.4 kW | Compressors, regulators |
| Humidity control (dehumidifier) | 1–2 kW | 1–2 kW | |

### Water Recovery & Thermal
| System | Power | Per Crew | Notes |
|--------|-------|----------|-------|
| Water reclamation | 1–2 kW | 1–2 kW | Filtration + distillation |
| Urine processor | 1.5–2.0 kW | 1.5–2.0 kW | Forward Osmosis or distillation |
| Thermal control (radiators) | 2–5 kW | 2–5 kW | Pumping + radiator area |

| **Total life support** | **7–13 kW** | **For a 1-person crew in closed loop** |
| With 50% recovery margins | 10–15 kW | More realistic for long-duration |

## Waste Production
| Waste Type | Daily Output | Notes |
|-----------|-------------|-------|
| Fecal mass | ~0.2 kg | ~140 g dry, ~800 g wet |
| Urine volume | ~1.5 L | ~95% water, 5% urea/electrolytes |
| Sweat/water vapor | 1.0–2.5 L | Varies with activity and T |
| CO₂ mass | ~0.95 kg | From metabolism |
| Fecal coliform | ~10¹⁰–10¹¹ CFU/day | Microbial load |

## Sources
1. Harris, J.A. & Benedict, F.G. (1985). "A review of the determination of heat and
   heat production in man." *J. Amer. Med. Assoc.*, 45, 1073–1079.
   — Original BMR equation
2. Mifflin, M.D., et al. (1990). "A new predictive equation for basal metabolic rate
   in healthy individuals." *Am. J. Clin. Nutr.*, 51(2), 241–247.
   — Revised Harris-Benedict equation
3. Institute of Medicine (2005). *Dietary Reference Intakes for Energy, Carbohydrate,
   Fiber, Fat, Protein and Alcohol.*
   — Daily caloric needs, water requirements
4. NASA. (2020). *Human Integration Design Handbook — Volume 1: Crew Health.*
   NASA/SP-2020-100.
   — O₂ consumption rates, CO₂ production, life support power
5. Mitchell, R.G. (1971). "Respiratory gas exchange in man at rest and during exercise."
   *J. Appl. Physiol.*, 31(1), 83–89.
   — O₂/CO₂ rates at various activity levels
6. Sawka, M.N., et al. (2005). "Human water and electrolyte balance." *Compr. Physiol.*
   — Water turnover rates, insensible losses
7. Coyle, E.F., et al. (2008). "Metabolic determinants of maximal and near-maximal
   oxygen consumption." *J. Appl. Physiol.*, 104(3), 827–836.
   — VO₂ max ranges for athletes
