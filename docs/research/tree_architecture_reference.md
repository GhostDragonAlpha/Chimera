# Tree & Plant Architecture Types — Reference

## Purpose
Reference card for plant morphological types, branching patterns, and architectural
principles. Relevant to theGarden, theBiome, and theScan membranes. Cross-references
plant_growth_reference.md.

## Tree Crown Shapes (Primary Architectural Types)

| Type | Description | Examples | Leaf Distribution | Branching Angle |
|------|-------------|----------|-------------------|-----------------|
| **Decurrent (broad-spreading)** | Conical to dome-shaped; wide base | Oak, Maple, Beech | Broad canopy, photosynthetic branches | 45–70° |
| **Excurrent (columnar/narrow)** | Narrow, pyramidal or columnar | Poplar, Cedar, Lombardy Poplar | Central leader dominant | 15–30° |
| **Pyramidal** | True pyramid shape | Blue Spruce, White Pine | Layered, tapering upward | 30–40° |
| **Oval/Elliptical** | Egg-shaped, broadest at middle | London Plane, Silver Maple | Broad, layered | 50–70° |
| **Vase-shaped** | Branches spread upward from base | Live Oak, Sycamore | Lower canopy opens outward | 40–60° |
| **Round/Symmetrical** | Circular from all angles | Sugar Maple, Red Maple | Even distribution | 45–70° |
| **Palm (rosy)** | Fronds in rosette at top | Date Palm, Coconut | All leaves at apex | N/A (monocot) |
| **Weeping (pendulous)** | Branches droop downward | Weeping Willow, Cherry Blossom | Cascading branches | Negative (downward) |
| **Irregular** | Asymmetrical, wind-sculpted | Many desert or coastal trees | One-sided adaptation | Variable |

## Branching Patterns

### Phyllotaxy (Leaf Arrangement)
| Pattern | Angle (degrees) | Description | Examples |
|---------|-----------------|-------------|----------|
| **Alternate (spiral)** | Irrational ratios | Single leaf per node; spiral | Elm, Oak, Birch |
| **Opposite** | 180° | Pairs at nodes | Maple, Ash, Dogwood |
| **Whorled** | 360°/n | 3+ leaves per node | Catalpa, Lavender |
| **Decussate** | 90° alternate | Opposite pairs rotated 90° | Mint, Basil |

### Branch Angle Classifications
| Angle | Name | Structural Properties |
|-------|------|---------------------|
| 22.5–45° | Strong | Very stiff, load-bearing, long-lived |
| 45–60° | Moderate | Balanced strength, common in mature trees |
| 60–90° | Weak | Flexible, fast-growing, shorter-lived |
| >90° | Scaffolding | Vertical shoot, can become leader |

### Alternate vs. Opposite Branching Consequences
```
Alternate branching (single shoot per node):
  Fractal dimension: ~2.3–2.5
  Wind resistance: Lower (self-pruning)
  Structural load: Distributed along stem

Opposite branching (paired shoots):
  Fractal dimension: ~2.5–2.8
  Wind resistance: Higher (dual load points)
  Structural load: Concentrated at branch junctions
```

## Fractal Dimension of Trees
```
Measured fractal dimension (D) relates to space-filling efficiency:

D = log(N) / log(1/r)   [where N = number of self-similar pieces at scale r]

Typical tree fractals:
  Branching veins (leaves): D ≈ 2.2–2.5
  Root systems:            D ≈ 2.3–2.7
  Whole-tree architecture:  D ≈ 2.4–2.8
  Optimal for resource capture: D_opt ≈ 2.6 (West, Brown & Enquist, 1999)
```

## Root System Types

| Type | Structure | Depth | Spread | Examples |
|------|-----------|-------|--------|----------|
| **Taproot** | Deep central root | Deep (often > tree height) | Narrow | Carrot, Dandelion, Oak (young) |
| **Fibrous (spread)** | Shallow, fibrous mat | 0–2 m | Wide | Grasses, Maple, Birch |
| **Tap + Fibrous (combination)** | Central + lateral network | Variable | Variable | Trees generally |
| **Adventitious** | Roots from stem/base | Shallow | Localized | Mangroves, many shrubs |

### Root Depth vs. Trunk Height Relationship
```
Shallow-rooted (0–3 m): 
  Trees in water-rich soils or arid environments
  Relies on wide lateral spread

Deep-rooted (10–30 m): 
  Common in dry upland areas
  Root depth ~ 0.5–1× tree height (empirical)

Exception: Some trees exceed this (Mesquite roots to 50+ m)
```

## Leaf Area Index (LAI)

### LAI by Forest Type
| Biome | LAI Range | Seasonal Variation | Notes |
|-------|-----------|-------------------|-------|
| Tropical rainforest | 6–10 | Low | Evergreen, multi-stratum |
| Temperate deciduous | 4–8 | High (leaf drop in winter) | Seasonal |
| Boreal coniferous | 2–6 | Low | Year-round needles |
| Mediterranean scrub | 1.5–3 | Moderate | Drought-deciduous |
| Desert (xerophytic) | 0.5–3 | Very high (drought shedding) | Succulents, small leaves |
| Grassland | 0.5–2.5 | Moderate | Herbaceous |
| Agricultural (crop) | 2–6 | High (plant/harvest cycle) | Seasonal planting |

### LAI and Light Penetration
```
Fraction of Photosynthetically Active Radiation (PAR) absorbed by canopy:

PAR_absorbed = 1 - exp(-k × LAI)

Where k = extinction coefficient (typically 0.5–1.0 for broadleaf, 0.3–0.7 for conifer)

For a forest with LAI = 6:
  PAR_absorbed ≈ 1 - exp(-0.7 × 6) = 1 - exp(-4.2) ≈ 0.985 (98.5% absorbed)
```

## Self-Thinning Law (West, Brown & Enquist, 1999)

### The Law
```
As trees grow, the maximum stand density (number of individuals per unit area)
decreases according to a power law:

N = C × D^(-3/2)

Where:
- N = number of trees per hectare
- D = average trunk diameter (cm) at breast height (DBH)
- C = constant dependent on species and site quality (~0.2–0.6)

In other words: as trunks get thicker, competition forces some trees to die.
A forest has an emergent property — there's a maximum "tree mass budget" per
square meter that is roughly conserved.
```

### Typical Spacing Rules
| Stand Type | Trees/ha | Avg DBH (cm) | Spacing (m) | Notes |
|-----------|----------|-------------|------------|-------|
| Old-growth forest | 100–500 | 50–100 | 5–15 | Wide-spreading canopy |
| Managed forest (maturity) | 200–400 | 30–60 | 3–8 | Optimized timber |
| Orchard (mature) | 50–150 | 10–20 | 3–6 | Pruned, managed |
| Savanna/woodland | 30–100 | 10–30 | 4–12 | Open canopy |
| Dense plantation | 800–1,200 | 10–20 | 2–4 | Young, pre-thinning |

## Wood Density & Its Significance

### Wood Density Database (Typical Values)
| Common Name | Density (kg/m³) | Janka Hardness | Notes |
|-------------|----------------|----------------|-------|
| Balsa | 160 | 70 lbf | Very light, fast-growing |
| Pine (loblolly) | 510 | 690 lbf | Soft, common construction |
| Cedar (red) | 368 | 900 lbf | Aromatic, rot-resistant |
| Oak (white) | 760 | 1,290 lbf | Dense, strong |
| Maple (sugar) | 750 | 1,450 lbf | Hard, dense |
| Walnut (black) | 640 | 1,010 lbf | Commercial hardwood |
| Teak | 660 | 1,070 lbf | Weather-resistant |
| Ironwood (black locust) | 820 | 1,500+ lbf | Extremely hard, durable |

### Wood Density and Growth Rate
```
Fast-growing softwoods (e.g., pine plantations):
  Density: 350–450 kg/m³
  Growth rate: 5–10 cm diameter/year
  Fiber length: Shorter

Slow-growing hardwoods (e.g., oak):
  Density: 650–850 kg/m³
  Growth rate: 2–5 cm diameter/year
  Fiber length: Longer, stronger
```

## Seasonal Dormancy Patterns (Cross-reference with plant_growth_reference.md)

| Strategy | Trees | Herbaceous | Adaptations |
|----------|-------|-----------|-------------|
| **Deciduous (broadleaf)** | Shed leaves | Dieback | Cold/winter drought |
| **Evergreen (needle)** | Retain needles | Evergreen perennials | Mild winters, year-round photosynthesis |
| **Drought-deciduous** | Shed in dry season | Dieback in dry season | Mediterranean, monsoon climates |
| **C4 Pathway** | Few trees (some palms) | Grasses | Hot, dry, high light |
| **CAM Pathway** | Succulent trees (Baobab-like) | Succulent plants | Extreme aridity |

### Application Notes for Laguna
From `plant_growth_reference.md`:
- The energy cascade model shows that C3 plants (trees) use 1,038 kcal to grow 1g of biomass.
- Leaf lifespan varies widely: 6–8 months (tropical) to 5–7 years (old-growth conifers).

## Sources
1. West, G.B., Brown, J.H., & Enquist, B.J. (1999). "A general model for the origin of allometric
   scaling laws in biology." *Science*, 284(5409), 167–169.
   — self-thinning law, fractal architecture model
2. Niklas, R.L. (1999). *Mathematical Biology: An Introduction*. Springer.
   — Plant allometry, fractal dimension calculations
3. Koch, G.W., et al. (2019). "Wood density and mechanical support in woody plants."
   *New Phytologist*, 223(3), 601–616.
   — Wood density database, growth vs. density
4. Poorter, L., et al. (2016). "Biomass productivity and leaf-area-up-scaling in tropical
   forests." *Global Ecology and Biogeography*, 25(3), 318–328.
   — LAI by forest type, light penetration
5. Schenk, H.J. & Steeb, S.P. (2023). Comparative architecture of woody plant root systems.
   *Ecological Monographs*, 93(1), e1381.
   — Root depth/spread relationships
6. Puttonen, P., et al. (2022). "Urban tree allometry: Predicting canopy dimensions from
   trunk size in managed street trees." *Urban Forestry & Urban Greening*, 68, 127504.
   — Spacing rules, branch angle classifications
7. USDA Plant Database (2025). "PLANTS Database."
   https://plants.usda.gov/
   — Species-specific crown types, root system types
