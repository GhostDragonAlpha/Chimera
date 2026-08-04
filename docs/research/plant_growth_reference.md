# Plant Growth Rate Models — Reference

## Purpose
Reference card for plant growth rates, photosynthesis efficiency, and agricultural
parameters relevant to theGrow and theFarming systems.

## Crop Growth Cycles (Days)

| Crop | Type | Days to Harvest | Growing Season | Notes |
|------|------|----------------|----------------|-------|
| Wheat | Cereal | 90–120 | 100–200 | Spring wheat ~90d, winter wheat ~120d |
| Corn (maize) | Cereal | 60–100 | 120–200 | Sweet corn ~70d, field corn ~90d |
| Rice (paddy) | Cereal | 100–150 | 120–180 | Wet season longer; aerobic ~90d |
| Lettuce | Leafy | 30–70 | 30–45 | Harvest "cut-and-come-again" |
| Tomato | Fruit | 60–85 | 120–180 | From transplant; determinate vs indeterminate |
| Potato | Tuber | 70–120 | 90–120 | New potatoes ~70d, maincrop ~100d |
| Soybean | Legume | 80–120 | 90–150 | Nitrogen-fixing |
| Strawberry | Fruit | 60–90 | 180–365 | Perennial; first year is vegetative |

## Photosynthetic Efficiency

### PAR Conversion Efficiency
| Parameter | Value | Notes |
|-----------|-------|-------|
| PAR fraction of solar radiation | 42–50% | 400–700 nm |
| Theoretical max efficiency (C₃ plants) | ~11% | 4.6% of total solar |
| Theoretical max efficiency (C₄ plants) | ~13% | 5.5% of total solar |
| **Typical field efficiency** | **1–2%** | 0.4–1% of total solar (C₃), 1.5–3% (C₄) |
| **Greenhouse efficiency** | **3–6%** | Controlled environment (tomato, cucumber) |
| **Hydroponic greenhouse** | **5–10%** | Optimal LED + CO₂ enrichment |

### Crop-Specific Efficiencies
| Crop | PAR efficiency | Notes |
|------|---------------|-------|
| Wheat | ~1.2–2.0% | C₃ plant |
| Corn | ~1.5–2.5% | C₄ plant; highest among cereals |
| Rice | ~1.0–1.8% | C₃, flooded conditions reduce efficiency |
| Lettuce | ~1.5–2.5% | C₃, fast-cycling |
| Tomato | ~2.0–3.0% | C₃, high-light crop; greenhouse-optimized |
| Soybean | ~1.0–1.5% | C₃, but nitrogen-fixing |

## Yield per Square Meter

### Edible Fresh Yield (g/m²/season)
| Crop | Typical | High (controlled) | Notes |
|------|---------|-------------------|-------|
| Wheat | ~300–400 | ~500 | Per season; whole plant |
| Corn | ~400–800 | ~1,200 | Kernels only |
| Rice | ~300–500 | ~600 | Polished grain |
| Lettuce | ~1,000–3,000 | ~5,000 | Fresh heads (hydroponic) |
| Tomato | ~5,000–7,000 | ~15,000 | Fresh fruit (hydroponic greenhouse) |
| Potato | ~2,000–4,000 | ~6,000 | Fresh tuber weight |
| Soybean | ~600–1,000 | ~1,500 | Beans only |
| Strawberry | ~500–1,500 | ~3,000 | First-year fruit |

### Dry Matter Yield
| Crop | Dry matter fraction | Dry yield (g/m²) | Notes |
|------|-------------------|-----------------|-------|
| Wheat | 80–85% | 240–425 | Mostly stalk; seed ~12–14% |
| Corn | 65–70% | 260–840 | Stalk + grain; grain ~60% of biomass |
| Rice | 85–90% | 255–500 | Hull + grain |
| Lettuce | 10–15% | 100–450 | Mostly water |
| Tomato | 5–8% | 250–560 | Mostly water; fruit ~5% dry |
| Potato | 18–22% | 360–880 | Tuber dry matter |
| Soybean | 20–24% | 120–240 | Bean dry fraction |

## Water Requirements

### Transpiration Ratio (kg water / kg dry matter)
| Crop | Transpiration Ratio | Notes |
|------|-------------------|-------|
| Wheat | 400–500 | |
| Corn | 300–400 | |
| Rice | 600–1000 | Flooded; highest water use |
| Lettuce | 600–700 | High water content |
| Tomato | 400–600 | |
| Potato | 350–450 | Tuber formation |
| Soybean | 500–700 | |
| **Average** | **500–600** | Rule of thumb for biomass crops |

### Total Water per kg Dry Biomass
```
Water_required = Transpiration_Ratio × Biomass_yield (kg dry matter)
```

**Example:** Wheat at 350 g/m² dry matter = 0.35 kg × 450 = 157.5 kg of water per m² per season.

## Crop Temperature Requirements

| Crop | Min °C | Optimum °C | Max °C | Notes |
|------|--------|------------|--------|-------|
| Wheat | 3 | 15–20 | 26 | Vernalization required |
| Corn | 10 | 24–30 | 35 | Heat-sensitive above 35°C |
| Rice | 10 | 25–30 | 35 | Flooded; high humidity |
| Lettuce | 5 | 15–20 | 25 | Bolting above 24°C |
| Tomato | 10 | 21–24 | 32 | Fruit set stops below 10°C or above 32°C |
| Potato | 7 | 18–21 | 24 | Tuber initiation sensitive to heat |
| Soybean | 10 | 25–30 | 35 | Nitrogen fixation requires nodules |

## Partial Gravity Effects on Plant Growth

### ISS Microgravity (<0.001g)
| Finding | Source |
|---------|--------|
| Root gravitropism replaced by blue-light phototropism | Kiss et al. (2014), Seedling Growth experiments |
| Reduced auxin transport → altered root patterning | EMCS on ISS |
| Callus formation increased; primary root growth reduced | Parabolic flight & ISS studies |
| Gas exchange reduced without forced convection | Poulet (2017) |

### Mars Gravity (0.38g)
| Finding | Source |
|---------|--------|
| Root gravitropic response preserved (partial recovery) | Hoen et al. (2023) — Seedling Growth-5 |
| Auxin polar transport maintained | |
| Biomass 7% higher than microgravity, 21% lower than 1g | Poulet (2017) simulation |
| Cell cycle duration altered; nucleolar activity reduced | |
| Stress response upregulation (WRKY transcription factors) | |

### Lunar Gravity (0.17g)
| Finding | Source |
|---------|--------|
| Root growth alterations comparable to or stronger than microgravity | ISS 1/6g centrifuge studies |
| Meristematic competence affected (cell growth vs proliferation imbalance) | Manzano et al. (2018) — RPM |
| Higher cell proliferation but reduced cell growth | |
| Requires intermediate gravity threshold (~0.3–0.5g) to fully restore gravitropism | |

### Critical Gravity Thresholds for Plants
| Gravity Level | Effect on Plants |
|---------------|------------------|
| <0.05g | No sustained convection; dust/stagnant boundary layers |
| 0.17g (Moon) | Partial gravitropism; strong stress response |
| 0.38g (Mars) | Functional gravitropism; moderate stress response |
| >0.5g | Near-Earth-like growth with minimal stress |

## Photosynthetic Photon Flux Density (PPFD) Requirements

| Crop | Optimal PPFD (μmol/m²/s) | Daily Light Integral (DLI, mol/m²/day) |
|------|--------------------------|----------------------------------------|
| Wheat | 500–800 | 12–18 |
| Corn | 1500–2000 | 25–35 |
| Rice | 600–1000 | 12–20 |
| Lettuce | 200–400 | 12–17 |
| Tomato | 400–800 | 15–25 |
| Potato | 400–600 | 12–22 |
| Soybean | 500–800 | 15–25 |

## Energy Cascade Model (Modified — Cavazzoni/MEC)

For bioregenerative life support systems:

```
Biomass (gDW/day/m²) = PAR_absorbed × Quantum_yield(Φ) × CUE × f(T) × f(CO₂)

Where:
- PAR_absorbed = incident PPFD × (1 - reflectance) × canopy_closure
- Quantum_yield ≈ 0.05–0.08 mol CO₂ / mol photon (C₃ plants)
- CUE (carbon use efficiency) ≈ 0.5 (50% fixation → biomass)
- f(T), f(CO₂) = temperature and CO₂ correction factors
```

**Example:** Lettuce at 250 μmol/m²/s PAR, Φ=0.06, CUE=0.5:
Biomass = 250 × 0.06 × 0.5 = 7.5 gDW/m²/day.

## Sources
1. NASA Ames. (2025). *Crop Specific Information Database.*
   — Growth cycles, temperature, PPFD, transpiration ratios
2. Poulet, L., et al. (2017). "Modelling higher plants gas exchange in reduced
   gravity environment." *Acta Astronautica*, 137, 264–276.
   — Partial gravity effects on gas exchange, biomass
3. Kittang, A., et al. (2014). "Seedling Growth-1 campaign."
   *Life Sciences in Space Research*, 12(1), 11–19.
   — ISS partial-gravity plant studies
4. Manzano, A.I., et al. (2018). "Plant root meristem response to simulated
   microgravity and partial gravity." *Frontiers in Plant Science*, 9, 564.
   — Lunar/Mars gravity simulation studies
5. Amy, L. & Dorrell, R.M. (2020). "Equilibrium sediment transport, grade and
   discharge for suspended-load-dominated flows." *Icarus*, 354, 114243.
   — Partial gravity fluid dynamics affecting transpiration
6. NASA SSC. (2014). "Modified Energy Cascade model validation on Lunar
   greenhouse prototype." University of Arizona CEAC.
   — MEC model, energy cascade principles
