# Vegetation Spectral Reflectance — Reference

## Purpose
Reference card for vegetation spectral properties relevant to laguna rendering and physics.

## Vegetation Reflectance Spectrum (400–1000 nm)

Vegetation reflectance can be subdivided into three regions:

| Region | Wavelength | Dominant Process | Reflectance |
|--------|------------|------------------|-------------|
| Visible (VIS) | 400–700 nm | Pigment absorption (chlorophyll) | 2–10% (low) |
| Red Edge | 680–750 nm | Transition zone | 10–40% (rapid rise) |
| Near-Infrared (NIR) | 750–1000 nm | Leaf internal structure (spongy mesophyll) | 40–60% (high) |

## Pigment Absorption Features

| Pigment | Peak Absorption (nm) | Visible Region | Notes |
|---------|---------------------|----------------|-------|
| Chlorophyll-a | 430, 662 | Blue, Red | Primary photosynthetic driver |
| Chlorophyll-b | 453, 642 | Blue, Red | Accessory pigment, broader spectrum |
| Carotenoids | 400–500 (β-carotene), 400–550 (xanthophyll) | Blue/Green | Photoprotection, fall leaf colors |
| Anthocyanins | 500–600 | Green/Red | Stress response, UV protection |

## Key Spectral Landmarks

| Wavelength (nm) | Feature | Reflectance |
|----------------|---------|-------------|
| 550 | Green peak (minimum absorption) | ~10–15% (appears green to eye) |
| 660–680 | Red absorption minimum | ~2–5% (chlorophyll-a) |
| 700 | Red Edge start (shoulder) | ~5–10% rising |
| 720 | Red Edge midpoint | ~15–25% |
| 800–900 | NIR plateau (internal structure) | ~40–60% |
| 1200 | Water absorption onset | ↓ (water content) |

## Red Edge Characteristics
- Location: 680–740 nm (varies with chlorophyll content)
- Position: Higher chlorophyll → red edge shifts to longer wavelengths (700–730 nm)
- Slope: Steeper slope indicates healthier vegetation
- Amplitude: Larger VIS-NIR contrast = denser canopy

## Vegetation Indices (from NDVI onward)

| Index | Formula | Bands (nm) | Range | Interpretation |
|-------|---------|------------|-------|----------------|
| NDVI | (NIR − Red)/(NIR + Red) | 800, 660 | −1 to +1 | >0.8 = dense vegetation; <0.1 = bare soil/water |
| EVI | 2.5×(NIR−Red)/(NIR+6×Red−7.5×Blue+1) | 800, 660, 470 | 0–1 | Forest canopy optimized, reduced atmospheric noise |
| MCARI | (Red_Edge − Red) − 0.5×(Red_Edge − Red_Blue) | 700, 660, 470 | varies | Chlorophyll content, less soil-sensitive |
| REPI | 700 + (REP_fit) | 680–740 | 700–730 nm | Red Edge Position (nm), chlorophyll proxy |

## Chlorophyll Content Ranges

| Plant Status | Chlorophyll Content (μg/cm²) | NDVI | Appearance |
|-------------|------------------------------|------|-------------|
| Healthy | 40–80 | 0.6–0.9 | Deep green |
| Moderate stress | 20–40 | 0.3–0.6 | Yellow-green |
| Stressed/Senescence | <20 | <0.3 | Yellow → brown |
| Bare soil | ~0 | ~0.1–0.2 | Non-vegetated |

## Leaf Optical Model (PROSPECT-5)
Key absorption coefficients (Feret et al., 2008):
- Chlorophyll-a+b: peak at 680 nm (red), 430 nm (blue)
- Carotenoids: peak 470–500 nm (blue-green)
- Water: 1450, 1950 nm (shortwave IR)
- Dry matter: 2100 nm (SWIR)

## Application to Laguna Rendering
- **Green wavelengths (500–580 nm):** Vegetation reflectance minimum — drives "green" appearance.
- **Red edge (700–750 nm):** Critical transition — indicates plant health in NIR.
- **NIR (750–1000 nm):** Strong scattering off leaf mesophyll — appears bright to sensors.

## Sources
1. Gitelson, A. A., & Merzlyak, M. N. (1997). "Remote estimation of chlorophyll content on leaf and canopy scales." *International Journal of Remote Sensing*, 18(18), 3697–3708.
   - NDVI, PRI, and chlorophyll estimation methods
2. Feret, J.-B., et al. (2008). "PROSPECT-4 and -5 improvement." *Remote Sensing of Environment*, 112(11), 3030–3043.
   - PROSPECT-5 leaf optical model, chlorophyll/carotenoid absorption coefficients
3. Baranoski, G. V. G., & Rokne, J. G. (2005). "A practical approach for estimating the red edge position of plant leaf reflectance." Unpublished.
   - Red Edge Position methods and 680–750 nm range
4. Zhang, H., et al. (2022). "A novel red‐edge spectral index for retrieving leaf chlorophyll content." *Journal of Vegetation Science*, 33(10), e13099.
   - Red edge chlorophyll inversion, CSI index formulation
