# Stellar Spectra — Reference

## Purpose
Reference card for stellar spectral classification and solar composition relevant to rendering and physics.

## Stellar Spectral Classification (Harvard System)

| Class | Temp Range (K) | Color | Peak λ (nm) | Key Spectral Features |
|-------|----------------|-------|-------------|----------------------|
| O | 30,000–50,000 | Blue | ~120 | Ionized He, strong UV, weak H lines |
| B | 10,000–30,000 | Blue-white | ~230 | Neutral He, strong H lines |
| A | 7,500–10,000 | White | ~365 | Strongest H lines, ionized metals |
| F | 6,000–7,500 | Yellow-white | ~460 | Weak H, ionized Ca, metals |
| G | 5,200–6,000 | Yellow | ~580 | Neutral metals, Ca II H&K, CH bands |
| K | 3,700–5,200 | Orange | ~700 | Strong Ca II, neutral metals, CO bands |
| M | 2,400–3,700 | Red | ~1,050 | TiO bands, strong molecular lines |

**Sun:** G2V, T_eff = 5,778 K

## Solar Photospheric Composition

| Element | Mass Fraction | Number Fraction | Color/Region Notes |
|---------|--------------|-----------------|--------------------|
| Hydrogen | 0.7340 (73.4%) | 0.917 | Peak emission at 589 nm (yellow) |
| Helium | 0.2485 (24.85%) | 0.085 | No color contribution (UV lines) |
| Oxygen | 0.0077 (0.77%) | 0.00057 | [O I] lines at 630 nm (red) |
| Carbon | 0.0029 (0.29%) | 0.00024 | CH/C₂ bands (blue-green) |
| Neon | 0.0013 (0.13%) | 0.000087 | [Ne I] (UV, no visible) |
| Iron | 0.0016 (0.16%) | 0.000073 | Fe I/Fe II forest (broad continuum) |
| Nitrogen | 0.0007 (0.07%) | 0.000065 | N I lines (red, 661, 665, 666 nm) |
| Silicon | 0.0007 (0.07%) | 0.000058 | Si I (red, 614, 615, 634, 636 nm) |
| Sulfur | 0.0003 (0.03%) | 0.000045 | S I (red, 604, 605, 606, 608 nm) |
| Magnesium | 0.0007 (0.07%) | 0.000043 | Mg I (bright, 517, 518 nm — green) |

## Solar Spectrum (V-band normalized)

Key features for rendering:
- **589 nm (yellow):** Na I D lines (deep absorption) — defines sun's yellow hue
- **393 nm (near UV):** Ca II K line (strong absorption)
- **486 nm (blue):** Hβ Balmer line (strong absorption)
- **656 nm (red):** Hα Balmer line (moderate absorption)

## Blackbody Approximation
Solar spectrum approximated as blackbody at T = 5778 K:
```
B(λ,T) = (2hc²/λ⁵) × 1/(e^(hc/λkT) - 1)
```
Peak wavelength via Wien's law: λ_max = 2.898 × 10⁻³ / 5778 = 501.6 nm (green-blue)

**Note:** Sun appears yellow from Earth due to atmospheric Rayleigh scattering removing blue light, not because the sun itself is yellow.

## Application to Laguna Rendering
- **Sun color:** G2V spectrum, peak green (500nm) but appears yellow due to atmosphere.
- **Stellar variation:** O/B stars emit 10–100× more UV → affects photochemistry, laguna surface chemistry.
- **Atmospheric effects:** Rayleigh scattering proportional to λ⁻⁴ → blue sky, red sunsets.

## Sources
1. Cox, A. N. (ed.). (2000). *Allen's Astrophysical Quantities*. 4th ed. Springer.
   - Solar parameters, stellar classification tables
3. Gray, R. O., & Corbally, C. J. (2009). *Stellar Spectral Classification and Diagnostics*. Cambridge University Press.
   - Spectral line features, classification criteria
4. Caffau, H., et al. (2011). "The chemical composition of the Sun." *Astronomy & Astrophysics*, 532, A141.
   - Solar photosphere abundances
