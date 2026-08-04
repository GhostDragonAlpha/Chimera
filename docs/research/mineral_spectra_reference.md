# Mineral Spectral Reflectance — Reference

## Purpose
Reference card for common laguna mineral spectral properties relevant to rendering and physics.

## Data Source
**USGS Spectral Library Version 7** — covers 0.2–200 μm, includes pure minerals, rocks, soils,
and mixtures. Samples measured with Beckman 5270, ASD field spectrometers (0.35–2.5 μm),
FTIR (1.12–216 μm), and AVIRIS (0.37–2.5 μm).

## Diagnostic Absorption Bands (0.4–2.5 μm)

### Silicate Minerals

| Mineral | Type | Key Absorption Bands (nm) | Reflectance Range | Notes |
|---------|------|--------------------------|-------------------|-------|
| Olivine | Nesosilicate (Mg,Fe)₂SiO₄ | 1000, 1250, 1700, 2000 | 35–60% | Broad absorptions; blue-green tint |
| Pyroxene (augite) | Inosilicate | 1000, 1300, 1800, 2200 | 25–45% | Doublet at ~1000, 1200; diagnostic |
| Pyroxene (hypersthene) | Inosilicate | 1000, 2000 | 30–50% | Broad feature near 2000 nm |
| Amphibole | Inosilicate | 850, 1200, 2300 | 30–50% | Sharp hydroxyl bands at 1200, 1400 nm |
| Muscovite | Phyllosilicate | 1400, 1900, 2200 | 30–50% | Aluminous mica, OH absorption |
| Chlorite | Phyllosilicate | 1400, 1900, 2300 | 25–45% | Fe-Mg mica, broad absorptions |
| Kaolinite | Phyllosilicate | 1400, 1900, 2150, 2300 | 20–40% | Aluminum clay, sharp doublet at 2150/2300 |
| Montmorillonite | Phyllosilicate | 1400, 1900, 2200 | 25–45% | Expandable clay, ~2200 nm shift |

### Oxide Minerals

| Mineral | Type | Key Absorption Bands (nm) | Reflectance Range | Notes |
|---------|------|--------------------------|-------------------|-------|
| Hematite | Iron oxide | 860, 1300, 2200 | 20–40% | Red, broad; ~860 nm diagnostic |
| Goethite | Iron oxyhydroxide | 900, 1300, 2300, 2400 | 25–45% | Yellow/brown, ~900 nm feature |
| Magnetite | Iron oxide | Broad: 500–1000 | 10–30% | Black, low reflectance overall |
| Ilmenite | Oxide | 700, 1000, 1200 | 30–50% | Metallic luster, dark |
| Rutile | Oxide | 300–450 (UV) | 40–60% | High NIR reflectance, TiO₂ |

### Carbonate Minerals

| Mineral | Type | Key Absorption Bands (nm) | Reflectance Range | Notes |
|---------|------|--------------------------|-------------------|-------|
| Calcite | Carbonate | 1400, 1900, 2300, 2500 | 40–70% | High reflectance, ~2300 nm diagnostic |
| Dolomite | Carbonate | 1400, 1900, 2300, 2600 | 35–65% | Distinct shift from calcite |

### Quartz and Feldspar

| Mineral | Type | Key Absorption Bands (nm) | Reflectance Range | Notes |
|---------|------|--------------------------|-------------------|-------|
| Quartz (pure) | Tectosilicate | Nearly featureless | 60–80% | Very high visible/NIR reflectance |
| Quartz (weathered) | Tectosilicate | 1400, 1900, 2900, 3400 | 40–70% | OH from alteration |
| Albite (feldspar) | Tectosilicate | 1400, 1900, 2200, 2700 | 45–70% | Weak features, high reflectance |
| Orthoclase (feldspar) | Tectosilicate | 1400, 1900, 2200, 2700 | 40–65% | Similar to albite |
| Microcline | Tectosilicate | 1400, 1900, 2200, 2700 | 40–60% | Low-temp K-feldspar |

## Spectral Purity Notes (USGS)

Samples are rated for spectral purity:
- **a:** Pure — primary features unobscured
- **b:** Minor contamination — features slightly modified
- **c:** Significant contamination — features overlap but recognizable
- **u:** Unclassifiable — insufficient data

**Key finding:** Almost all samples show absorption near 3 μm due to water adsorption.
Mineral OH/H₂O features at 1.4, 1.9, 2.2 μm are common and not intrinsic to the mineral
but indicate surface weathering or alteration.

## High-Resolution Features
At resolving powers ~1000–2240 (λ/Δλ):
- OH-bearing minerals show sharp absorptions near 1400, 1900 nm
- Amphiboles and talcs show four OH bands (Mg₃, Mg₂Fe, MgFe₂, Fe₃ sites)
- These fine structures enable elemental composition determination

## Application to Laguna Rendering

| Mineral Type | Visual Appearance | Key Rendering Parameters |
|-------------|-------------------|--------------------------|
| Olivine-rich | Green-black, metallic | High NIR (~55%), absorption at 1000/1250 nm |
| Iron oxides | Red/yellow/brown | Sharp drop at 860 nm (hematite), low overall reflectance (20–40%) |
| Quartz sand | White/gray, high reflectance | Very high VIS/NIR (60–80%), featureless |
| Clay-rich | Dull red/brown | ~1400/1900 nm OH features, moderate reflectance (25–45%) |
| Calcite | White/gray, bright | High reflectance (40–70%), diagnostic ~2300 nm |

## Sources
1. Kokaly, R. F., et al. (2017). "USGS Spectral Library Version 7." *U.S. Geological Survey Data Series* 1035.
   - https://pubs.usgs.gov/ds/1035/ds1035.pdf
   - Complete mineral spectral library, 0.2–200 μm range
2. Sutley, S. J. (2007). "USGS Digital Spectral Library splib06a." *U.S. Geological Survey Data Series* 231.
   - Early release, foundational purity coding system
3. King, T. V. V., et al. (1990). "High spectral resolution reflectance spectroscopy of minerals."
   *Journal of Geophysical Research*, 95(B8), 12653–12672.
   - Fine structure in OH-bearing minerals, resolving power effects
