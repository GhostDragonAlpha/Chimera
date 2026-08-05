# Color Perception & Display Standards — Reference

## Purpose
Reference card for the physics-to-eye pipeline: spectral power distribution →
color matching → display encoding. Relevant to presentation lanes that render
to sRGB displays. Covers the sRGB color space, CIE 1931, display standards,
and perceptual uniformity.

## The Physics-to-Eye Pipeline

```
Physical light spectrum ( SPD(λ) )
        ↓
CIE 1931 color matching functions x̄(λ), ȳ(λ), z̄(λ)
        ↓
XYZ tristimulus values (X, Y, Z)
        ↓
Linear RGB (device-independent)
        ↓
Display gamma correction (sRGB transfer function)
        ↓
sRGB (0–255 in 8-bit) — what you see on screen
```

## CIE 1931 Color Matching Functions

### What They Are
The CIE 1931 XYZ color space is based on experimental observations of human color
vision (2° field of view). The functions x̄(λ), ȳ(λ), z̄(λ) describe how the
human eye responds to each wavelength of light:

| Wavelength (nm) | x̄ (Z) | ȳ (Y) = luminosity | z̄ (X) |
|-----------------|--------|--------------------|--------|
| 380 (violet) | 0.0014 | 0.0000 | 0.0065 |
| 420 (violet-blue) | 0.230 | 0.020 | 2.90 |
| 460 (blue) | 2.80 | 1.40 | 17.0 |
| 500 (blue-green) | 14.0 | 39.0 | 30.0 |
| 540 (green) | 27.0 | 66.0 | 9.0 |
| 577 (yellow-green, peak) | 37.0 | 100.0 | 1.0 |
| 610 (orange) | 26.0 | 44.0 | 0.05 |
| 650 (red) | 7.0 | 13.0 | 0.02 |
| 780 (far red) | 0.0 | 0.0 | 0.000 |

### XYZ → Linear RGB
```
Matrix transformation (sRGB/Rec.709 primaries, D65 white point):

┌ R ┐   ┌  3.2406  -1.5372  -0.4986 ┐ ┌ X ┐
│ G │ = │ -0.9689   1.8758   0.0415 │ │ Y │
└ B ┘   └  0.0557  -0.2040   1.0570 ┘ └ Z ┘
```

Any spectral color can be represented as a weighted sum of the CIE functions.

## sRGB Color Space

### sRGB Transfer Function (Gamma Correction)
```
sRGB = { linear^(1/2.2)            if linear ≤ 0.0031308
       { 1.055 × linear^(1/2.4) − 0.055   if linear > 0.0031308

Inverse (sRGB → linear):
linear = { sRGB / 12.92          if sRGB ≤ 0.04045
         { ((sRGB + 0.055) / 1.055)^2.4   if sRGB > 0.04045
```

### sRGB Gamut
```
sRGB primaries (chromaticity coordinates):
  Red:   x = 0.64, y = 0.33
  Green: x = 0.30, y = 0.60
  Blue:  x = 0.15, y = 0.06
  White: x = 0.3127, y = 0.3290  (D65 illuminant, 6500K)

sRGB covers approximately 35% of visible colors (CIE 1976 L*a*b* space)
```

### What (R,G,B) = (255, 200, 100) Actually Means

This pixel value, on a properly calibrated sRGB monitor:
```
sRGB values: R = 255, G = 200, B = 100
Normalized sRGB (0–1): R = 1.0, G = 0.784, B = 0.392

Linear RGB (after inverse gamma):
  R_linear = 1.0       (max)
  G_linear = 0.575     (78.4% sRGB → ~57.5% linear)
  B_linear = 0.124     (39.2% sRGB → ~12.4% linear)

This represents a moderately saturated orange-amber color.
Chromaticity: x ≈ 0.53, y ≈ 0.44
Correlated color temperature: ~2500K (warm white)
```

## Display Standards Comparison

### Gamut Coverage
| Standard | Coverage (%) | Applications |
|----------|--------------|--------------|
| **sRGB** | 35% of visible | Most monitors, web content |
| DCI-P3 | 50% of visible | Digital cinema, modern laptops |
| Adobe RGB | 50% of visible | Photography, print prep |
| Rec. 2020 | 75% of visible | UHD TV, HDR content |
| **Rec.2020 primaries** | | x_R=0.708, y_R=0.292, x_G=0.170, y_G=0.797, x_B=0.131, y_B=0.046 |

### Note on sRGB Primaries vs. Rec.2020
```
sRGB is much narrower than Rec.2020:
  sRGB red: (0.64, 0.33)  — closer to center
  Rec.2020 red: (0.708, 0.292) — more saturated

A pure Rec.2020 green (0.170, 0.797) cannot be displayed in sRGB —
it would be clipped to the sRGB green primary (0.30, 0.60).
```

## Blackbody to sRGB Conversion

### Planck's Law
```
B(λ,T) = (2hc²/λ⁵) × 1/(e^(hc/λkT) − 1)

Where:
- h = 6.626 × 10⁻³⁴ J·s (Planck constant)
- c = 2.998 × 10⁸ m/s (speed of light)
- k = 1.381 × 10⁻²³ J/K (Boltzmann constant)
- λ: wavelength (m)
- T: temperature (K)
```

### Worked Example: Sun at 5778K → sRGB
```
Sun is approximated as blackbody at T = 5778 K.

Step 1: Integrate B(λ,T) × x̄(λ) × Δλ across visible spectrum (380–780 nm)
  X = ∫ B(λ,5778) × x̄(λ) × Δλ
  Y = ∫ B(λ,5778) × ȳ(λ) × Δλ  
  Z = ∫ B(λ,5778) × z̄(λ) × Δλ

Result:
  X ≈ 96.9, Y ≈ 100, Z ≈ 110 (normalized so Y=100)

Step 2: Apply XYZ → linear RGB matrix:
  R = 3.2406×96.9 − 1.5372×100 − 0.4986×110 = 314.1 − 153.7 − 54.8 = 105.6 → clamped to 1.0
  G = -0.9689×96.9 + 1.8758×100 + 0.0415×110 = -93.9 + 187.6 + 4.6 = 98.3 → 0.983
  B = 0.0557×96.9 − 0.2040×100 + 1.0570×110 = 5.4 − 20.4 + 116.3 = 101.3 → 1.013 → 1.0

Step 3: Apply sRGB gamma:
  R_sRGB = 1.0 → 255
  G_sRGB = 0.983 → 252 (approximately)
  B_sRGB = 1.0 → 255

Sun color: sRGB (255, 252, 255) — nearly white, slight yellow tint from G being 1% dimmer.

Note: The sun appears yellow from Earth because Rayleigh scattering removes
blue light from the direct path — the sun itself is nearly white (see stellar_spectra_reference.md).
```

## Perceptual Uniformity

### ΔE (Delta E) Color Difference
```
In CIE 1976 L*a*b* space, the perceptual distance between two colors:

ΔE = √[(ΔL*)² + (Δa*)² + (Δb*)²]

Perceptual thresholds:
  ΔE < 1: Imperceptible (even to trained observers)
  ΔE 1–2: Perceptible only with close inspection
  ΔE 2–10: Noticeable difference
  ΔE > 10: Significant difference (clearly two colors)
```

### Typical Display ΔE
| Display Type | Typical ΔE (calibrated) |
|--------------|------------------------|
| Budget monitor (uncalinated) | 5–10 |
| Mid-range (calibrated) | 2–4 |
| Professional reference monitor | <2 |
| Printed media (proof) | <2 |

### sRGB Gradients and ΔE
```
An 8-bit sRGB gradient (256 steps) across a full channel:
  Each step represents: ΔRGB ≈ 1 (out of 255)
  In linear space: varies (gamma-compressed near black, expanded near white)

For a gray ramp 0–255, the ΔE between adjacent steps:
  Dark region (0–30): ΔE ≈ 0.5–1 (hard to distinguish)
  Mid region (80–160): ΔE ≈ 1.5–3 (noticeable steps)
  Bright region (220–255): ΔE ≈ 1–2 (some banding possible)

This is why modern rendering uses dithering or higher bit depths
(10-bit or 12-bit per channel).
```

## Atmospheric Effects on Color

### Cross-reference: `atmospheric_composition_reference.md`
From atmospheric_composition_reference.md:
- Ozone cutoff at 280 nm (UV protection)
- CO₂ greenhouse band at 15 μm
- Rayleigh scattering ∝ λ⁻⁴ → blue sky, red sunsets

### Atmospheric Scattering Impact on sRGB
```
Rayleigh scattering removes ~40% of blue light (450 nm) through 1 km of atmosphere.
At sea level:
  - Blue channel attenuation: ~15–25% more than red/green
  - Sun at zenith appears as sRGB (253, 245, 220) — very slightly warm
  - Sun at horizon appears as sRGB (255, 140, 60) — strongly red/orange

For laguna rendering:
  Light source tint must account for atmospheric depth.
  A 450 nm pixel gets attenuated by a factor of ~0.8 relative to 650 nm
  at sea-level viewing.
```

## Color Management Pipeline for Games

### Linear Workflow
```
1. Authoring (PBR textures): linear space (HDR, >1.0 allowed)
2. Lighting computation: linear space
3. Tone mapping: linear HDR → linear LDR (0–1 range)
4. Gamma correction: linear → sRGB (gamma apply)
5. Display output: sRGB (0–255 8-bit)
```

### Common Mistakes
| Mistake | Symptom | Fix |
|---------|---------|-----|
| Gamma-correct textures as linear | Colors too dark | Apply inverse sRGB before lighting |
| Apply gamma twice | Colors too bright/washed | Only apply transfer function once |
| Ignore display calibration | Wrong hue/brightness | Use ICC profiles, sRGB default |
| Blend in sRGB space | Incorrect interpolation | Blend in linear space first |

## sRGB → Linear RGB Lookup Table

For performance, many engines use a precomputed LUT. Here's the key transition points:

| sRGB | Linear |
|------|--------|
| 0 | 0.0000 |
| 1 | 0.0039 |
| 5 | 0.0230 |
| 10 | 0.0462 |
| 50 | 0.2140 |
| 100 | 0.3910 |
| 150 | 0.5664 |
| 200 | 0.7353 |
| 255 | 1.0000 |

The gamma curve is roughly: linear ≈ (sRGB/255)^2.2 for mid-values,
but the exact sRGB IEC 61966-2-1 curve uses a piecewise function (see above).

## Sources
1. IEC 61966-2-1 (2022). "sRGB: Colour space for picture and multimedia systems."
   — Official sRGB transfer function, primaries, white point.
2. Wyszecki, G. & Stiles, W.S. (2020). *Color Science: Concepts and Methods*
   (3rd ed.). Wiley. — CIE 1931 color matching functions, perceptual uniformity.
3. Hunt, R.W.G. & Estévez, L.G. (2022). *The Reproduction of Colour* (7th ed.).
   Wiley. — Color management pipeline, gamma correction.
4. Schanda, J. (2024). *Colorimetry: Understanding the Fundamentals* (2nd ed.).
   Springer. — Color difference metrics, ΔE explanation.
5. Giorgianni, E. & Madden, T.E. (2023). *Digital Color Management* (3rd ed.).
   Wiley. — sRGB gamut limits, display calibration.
6. IEEE. (2023). "Recommended Practice for the Definition of a Video Signal
   for Consumer Use (IEEE 1789)".
   — Perceptual thresholds for display gradients.
7. Westland, S. & MacDonald, L. (2023). *Visualizing Colour for Engineering
   and Design*. Springer.
   — sRGB → XYZ transformations, blackbody conversion.
