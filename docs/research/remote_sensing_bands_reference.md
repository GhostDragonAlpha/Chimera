# Electromagnetic Spectrum & Remote Sensing — Reference

## Purpose
Reference card for the electromagnetic spectrum and multispectral remote sensing
bands. Relevant to theScan membrane. Cross-references atmospheric_composition_reference.md
for atmospheric absorption.

## The Electromagnetic Spectrum

```
Wavelength order (short → long):
γ-ray → X-ray → UV → Visible → IR → Microwave → Radio

Frequency (Hz) = c / λ  (where c = 2.998 × 10⁸ m/s, λ = wavelength in meters)

Energy of photon: E = h × ν  (where h = Planck's constant = 6.626 × 10⁻³⁴ J·s)
```

| Region | Wavelength | Frequency | Energy | Sources/Applications |
|--------|-----------|-----------|--------|----------------------|
| **Gamma-ray** | 0.001–1 nm | 300–300,000 GHz | >124 keV | Nuclear decay, GRBs |
| **X-ray** | 0.01–10 nm | 30–30,000 GHz | 0.124 keV – 124 keV | Medical, astronomical objects |
| **Ultraviolet** | 10–400 nm | 750–30,000 GHz | 3–124 eV | Sun, chemical bonds |
| **Visible** (400–700 nm) | --- | --- | --- | --- |
| &nbsp;&nbsp;• Violet | 380–450 nm | 666–790 THz | 2.75–3.26 eV | |
| &nbsp;&nbsp;• Blue | 450–495 nm | 606–666 THz | 2.51–2.75 eV | |
| &nbsp;&nbsp;• Green | 495–570 nm | 526–606 THz | 2.18–2.51 eV | Peak solar at Earth |
| &nbsp;&nbsp;• Yellow | 570–590 nm | 508–526 THz | 2.10–2.18 eV | |
| &nbsp;&nbsp;• Orange | 590–620 nm | 484–508 THz | 2.00–2.10 eV | |
| &nbsp;&nbsp;• Red | 620–750 nm | 400–484 THz | 1.65–2.00 eV | |
| **Near IR** | 750–1400 nm | 214–400 THz | 0.89–1.65 eV | Vegetation, heat |
| **Shortwave IR** | 1400–3000 nm | 100–214 THz | 0.41–0.89 eV | Mineral mapping |
| **Longwave IR (LWIR)** | 8–14 μm | 21–37 THz | 0.087–0.15 eV | Thermal |
| **Microwave** | 1–300 mm | 1–300 GHz | 4 μeV–1.2 meV | Radar, CMB |
| **Radio** | >300 mm | <1 GHz | <4 μeV | Communication, cosmic |

## Atmospheric Windows
From `atmospheric_composition_reference.md` — Earth atmosphere selectively transmits
certain wavelengths. Key windows:

### Transmitting Windows (Earth)
```
Spectral regions where atmosphere is transparent (≥70% transmission):

1. Visible (390–680 nm)      — Surface imaging
2. Near-IR (760–1300 nm)     — Vegetation health, some water vapor absorption
3. Shortwave IR (1550–1800 nm)— Mineral identification
4. Thermal IR (8–12 μm)      — Thermal imaging, "atmospheric window"
5. Radio/microwave (cm wavelengths) — Radio telescopes
```

### Absorbing Bands (Earth)
| Gas | Wavelength(s) (μm) | Absorption Strength |
|-----|---------------------|---------------------|
| H₂O (water vapor) | 1.4, 1.9, 2.7, 6.3, 12–18, 25–30 | Very strong |
| CO₂ (carbon dioxide) | 2.7, 4.3, 15 | Very strong (15 μm is major GHG band) |
| O₃ (ozone) | 0.25–0.30 (UV) | Absorbs all <0.28 μm |
| O₂ (oxygen) | 0.69, 0.76, 1.27, 1.58, 2.06 | Moderate |
| CH₄ (methane) | 1.7, 2.3, 3.3, 7.7, 13 | Moderate to strong |
| N₂O | 4.5, 7.8 | Moderate |

Note from `atmospheric_composition_reference.md`:
- Ozone cutoff at ~300 nm (UV protected)
- CO₂ greenhouse band at 15 μm (infrared back-radiation)
- H₂O bands are dominant absorbers in the infrared

## Multispectral Remote Sensing Bands

### Landsat 8/9 OLI (Operational Land Imager)
| Band | Wavelength (μm) | Name | Resolution | Common Uses |
|------|-----------------|------|------------|-------------|
| Band 1 | 0.43–0.45 | Coastal/Aerosol | 30 m | Coastal water, aerosol |
| Band 2 | 0.45–0.51 | Blue | 30 m | Water penetration, bathymetry |
| Band 3 | 0.53–0.59 | Green | 30 m | Peak vegetation reflectance, true color |
| Band 4 | 0.64–0.67 | Red | 30 m | Chlorophyll absorption, vegetation |
| Band 5 | 0.85–0.88 | NIR | 30 m | Vegetation health, NDVI |
| Band 6 | 1.36–1.38 | SWIR-1 | 30 m | Moisture content, burn scars |
| Band 7 | 2.11–2.29 | SWIR-2 | 30 m | Mineral mapping, soil moisture |
| Band 8 | 0.50–0.67 | Panchromatic | 15 m | Panchromatic sharpening |
| Band 9 | 1.36–1.38 | Cirrus | 30 m | Cloud cover detection |
| Band 10 | 10.60–11.19 | Thermal TIRS | 100 m | Land surface temperature |
| Band 11 | 11.50–12.51 | Thermal TIRS | 100 m | Land surface temperature |

### Sentinel-2 MSI
| Band | Wavelength (μm) | Resolution | Common Uses |
|------|-----------------|------------|-------------|
| B1 | 0.43–0.45 | 60 m | Coastal/aerosol |
| B2 | 0.44–0.53 | 10 m | Blue |
| B3 | 0.53–0.59 | 10 m | Green |
| B4 | 0.64–0.67 | 10 m | Red |
| B5 | 0.69–0.72 | 10 m | Red edge |
| B6 | 0.73–0.74 | 10 m | Red edge |
| B7 | 0.76–0.79 | 10 m | Red edge |
| B8 | 0.77–0.96 | 10 m | NIR |
| B8A | 0.86–0.89 | 20 m | Narrow NIR |
| B11 | 1.63–1.66 | 20 m | SWIR |
| B12 | 2.10–2.14 | 20 m | SWIR |

## What Each Band Detects

### Vegetation Health (Spectral Indicators)
```
NDVI = (NIR - Red) / (NIR + Red)

  Healthy vegetation: NDVI > 0.6
  Moderate vegetation: NDVI 0.3–0.6
  Bare soil / urban: NDVI < 0.2
  Water: NDVI < 0 (NIR absorbed by water)

EVI (Enhanced Vegetation Index):
  EVI = G × [(NIR - Red) / (1 + C₁×Red - C₂×Blue + C₃×L)]

  Accounts for atmospheric and soil background effects
```

### Mineral Identification (SWIR Absorption Features)
```
Minerals have diagnostic absorption features in Short-Wave Infrared (1.4–2.5 μm):

  Feature Wavelength  Material Detected
  0.9 μm             Oxyiron minerals (goethite, hematite)
  1.0 μm             Carbonates (calcite, dolomite)
  1.4 μm             Water/OH-bearing minerals (clays, micas)
  1.9 μm             Water/OH-bearing minerals
  2.2 μm             Clay minerals (alunite, illite, kaolinite)
  2.3 μm             Carbonates (calcite, dolomite)
  2.4 μm             Sulfates (gypsum, kieserite)

Spectral angle mapper (SAM):
  Compare unknown spectrum to library of known materials
  Angle threshold < 0.1 radians = confident match
```

### Water Detection
```
Water absorption features:
  0.97 μm  — Liquid water (surface)
  1.20 μm  — Water vapor
  1.40 μm  — Water vapor (strong)
  1.90 μm  — Water vapor (very strong)
  2.70 μm  — Water vapor
  6.30 μm  — Water vapor (thermal IR)

Pure water:
  - Absorbs strongly at 1.4, 1.9, 2.7, 6.3 μm
  - Reflects/transmits at 0.9–1.3 μm (visible + shortwave IR)

Clouds and water bodies:
  - Low 0.4–0.7 μm reflectance (dark in visible)
  - High 3–10 μm reflectance/emit (bright in thermal IR during day, cold)
```

### Urban/Built-up Areas
```
Built-up areas:
  - High 0.4–0.7 μm reflectance (concrete/asphalt)
  - Low NIR (0.7–0.9 μm) compared to vegetation
  - Distinct SWIR signatures (0.9–1.3 μm) based on material

NDBI (Normalized Difference Built-up Index):
  NDBI = (SWIR - NIR) / (SWIR + NIR)
  Higher values = more built-up
```

## Spatial Resolution vs. Spectral Resolution Tradeoff

| Mission | Spectral Bands | Spatial Resolution | Coverage (km²) | Revisit (days) |
|---------|---------------|-------------------|----------------|----------------|
| Landsat 8 | 11 bands | 30 m (multispectral), 15 m pan | 185 × 185 km | 16 (8 with pair) |
| Sentinel-2 | 13 bands | 10–60 m | 290 × 290 km | 5 |
| MODIS | 36 bands | 250–1000 m | 2,030 × 2,030 km | 1–2 |
| ASTER | 14 bands | 15–100 m | 60 × 60 km | 16 |
| Hyperspectral (AVIRIS) | 224 bands | 4 m | 12 km swath | Campaign only |
| WorldView-3 | 8 bands | 0.31–2.0 m | ~13 × 13 km | On demand |

### Resolution Trade-offs Applied
```
For planetary science:
  Hyperspectral → high spectral, low spatial
  Multispectral → balanced (good compromise)
  Panchromatic → high spatial, low spectral

Example: Detecting a 1 m² patch of vegetation
  Landsat (30 m): pixel contains 900 m² — 1 m² invisible
  WorldView (0.31 m): pixel contains 0.1 m² — 1 m² easily detected
```

## Applications for Laguna Scanning

### Mineral Mapping
```
Target minerals for laguna worlds:
  1. Iron oxides (hematite, goethite) — red coloration (0.86 μm band)
  2. Clay minerals (kaolinite, montmorillonite) — OH absorption (1.4, 1.9 μm)
  3. Sulfates (gypsum, kieserite) — 1.45, 1.95, 2.25 μm features
  4. Carbonates (calcite, dolomite) — 1.0, 2.3 μm features
  5. Ice (H₂O, CO₂) — 1.0, 1.5, 2.0, 3.0 μm for H₂O; 4.3 μm for CO₂ ice
```

### Vegetation Health Monitoring
```
From theGarden/theBiome:
  NDVI thresholds:
    Healthy growth: > 0.6
    Stressed plants: 0.3–0.6 (N-limited)
    Dying/underground: < 0.3

  EVI more robust in high biomass (forest) or sparse vegetation:
    EVI > 0.4 = healthy
```

## Sources
1. Sabins, W.F. (2023). *Remote Sensing: Principles and Interpretation* (5th ed.).
   Waveland Press.
   — Spectral signatures, atmospheric windows
2. Lillesand, T., Kiefer, R.W., & Chipman, J. (2024). *Remote Sensing and Image
   Interpretation* (8th ed.). Pearson.
   — Landsat/Sentinel band specifications, vegetation indices
3. NASA. (2025). "Landsat 8 Data Users Handbook."
   https://landsat.gsfc.nasa.gov/
   — Official band characteristics, calibration
4. ESA. (2025). "Sentinel-2 MSI Instrument Documentation."
   https://sentinel.esa.int/
   — Band specifications, resolution details
5. Goetz, A.F.H. (2021). "Hyperspectral image generation and analysis."
   *American Society for Photogrammetry and Remote Sensing*.
   — Spectral feature identification principles
6. NASA Earth Observing System. (2025). "MODIS Spectral Response Functions."
   — Broadband and narrowband spectral ranges
7. USGS. (2025). "Mineral Spectral Library."
   https://speclab.cr.usgs.gov/
   — Diagnostic absorption features by mineral
