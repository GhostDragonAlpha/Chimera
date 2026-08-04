# Biome Climate Classification (Köppen-Geiger) — Reference

## Purpose
Reference card for Köppen climate classification, mapped to visual biome appearance parameters.

## Classification System
Five main groups (A–E), determined by temperature and precipitation thresholds.

### Group A: Tropical (T_avg_month > 18°C year-round)
| Subtype | Precipitation | Dry Season | Visual |
|---------|--------------|------------|--------|
| Af | All months > 60mm | None | Evergreen rainforest, dense canopy |
| Am | ~2000mm/yr, winter drier | Short dry | Broadleaf evergreen, bamboo understory |
| Aw | Wet/dry seasonality | Winter dry | Deciduous patches, grasslands |

### Group B: Dry (potential evapotranspiration > precipitation)
| Subtype | Precipitation (Pg) | Visual |
|---------|-------------------|--------|
| BWh | < 10×PET, hot | Hyper-arid desert, bare rock/scatter |
| BWk | < 10×PET, cold | Cold desert, sparse shrubs |
| BSh | 10–20×PET, hot | Semi-arid steppe, grasses + scattered |
| BSk | 10–20×PET, cold | Cold steppe, drought-tolerant grass/shrub |

**Formula:** `Pg = P_threshold × (PET / P_actual)` where P_threshold = 10 (hyper-arid) to 20 (semi-arid)

### Group C: Temperate (warmest < 22°C but > 10°C, coldest > −3°C to −3 to 18°C)
| Subtype | Pattern | Visual |
|---------|---------|--------|
| Cfa | Humid subtropical | Deciduous forest, broadleaf summer |
| Cfb | Oceanic | Mixed forest, green year-round |
| Cfc | Subpolar oceanic | Boreal-like, low-growing |
| Csa/Csb | Mediterranean (dry summer) | Scrub, sclerophyll, dry summers |

### Group D: Continental (coldest < −3°C, warmest > 10°C)
| Subtype | Visual |
|---------|--------|
| Dfa/Dwa | Hot summer, possible dry winter | Deciduous/conifer mix, seasonal |
| Dfb/Dwb | Warm summer | Mixed boreal/deciduous, cold winters |
| Dfc/Dwc | Subarctic | Conifer-dominated, brief summer |
| Dfd/Dwd | Severe subarctic | Sparse conifer, very cold |

### Group E: Polar (warmest < 10°C)
| Subtype | Visual |
|---------|--------|
| ET | Tundra | Low shrubs, moss, permafrost |
| EF | Ice cap | Permanent ice/snow, bare |

## Parameter Summary

| Parameter | Tropical | Desert | Temperate | Continental | Polar |
|-----------|----------|--------|-----------|-------------|-------|
| Temp range (°C) | — | 20–45 daily range | 3–22 | −30 to 25 | −20 to 10 |
| Precip (mm/yr) | 2000+ | 0–250 | 300–1200 | 300–800 | 0–500 |
| Vegetation height | 15–40m | 0.1–2m (sparse) | 5–25m | 5–20m seasonal | 0.1–5m |
| Growing season | 12mo | 1–4mo | 6–9mo | 3–6mo | 0–3mo |

## Application to Laguna Biomes
- **A-type:** Dense rainforest canopy → high moisture, low albedo (0.08–0.15)
- **B-type:** Sparse vegetation, exposed substrate → high albedo (0.25–0.40)
- **C/D-type:** Seasonal forest → moderate albedo (0.15–0.25), seasonal color shifts
- **E-type:** Ice/tundra → high albedo (0.40–0.80), minimal biomass

## Sources
1. Peel, M. C., Finlayson, B. L., & McMahon, T. A. (2007). "Updated Köppen-Geiger land environments of the world." *Hydrology and Earth System Sciences*, 11(5), 1639–1641.
2. Kottek, M., et al. (2006). "World map of Köppen-Geiger climate classification." *Meteorologische Zeitschrift*, 15(3), 257–260.
3. Trewartha, G. T., & Horn, L. E. (1980). *An Introduction to Climate*. 2nd ed. McGraw-Hill.
   - Temperature thresholds for Köppen groups
