# Radiation Environment in Space — Reference

## Purpose
Reference card for the space radiation environment across solar system locations,
shielding effectiveness, and biological dose limits. Relevant to theShip, theShields,
and theSuit membranes.

## Radiation Sources in Space

### Solar Wind
| Property | Value |
|----------|-------|
| **Speed** | 350–800 km/s (avg ~400 km/s) |
| **Density** | ~5 protons/cm³ (at 1 AU) |
| **Composition** | ~95% H⁺ (protons), ~4% He²⁺ (alpha), ~1% heavier ions |
| **Energy** | ~1–10 keV/nucleon |
| **Flux** | ~10⁸ protons/cm²/s at 1 AU |

### Solar Particle Events (SPEs)
```
Associated with solar flares and coronal mass ejections (CMEs).

Typical SPE characteristics:
  - Duration: Minutes to hours (<24 hr)
  - Peak flux: 10⁹–10¹¹ protons/cm²/s (>10 MeV)
  - Total fluence: 10¹⁰–10¹² protons/cm² per event
  - Energy range: 1–500 MeV (peak typically ~10–100 MeV)

Major event (e.g., Halloween storms 2003):
  - Delivered ~1 Sv to unshielded astronaut in hours
```

### Galactic Cosmic Rays (GCR)
```
High-energy nuclei from outside the solar system.

Flux and composition by energy band (at 1 AU):

  Energy range   Flux (/cm²/s/sr)   Dominant components
  10–100 MeV     10⁴–10⁵            Protons (85%)
  100–1000 MeV   10³–10⁴            Protons, some He nuclei
  1–10 GeV       10²–10³            Protons (85%), He (14%), heavy nuclei (1%)
  10–100 GeV     10¹–10²            Protons, He, heavier nuclei
  100–1000 GeV   1–10              Heavy nuclei increasingly important

Heavy ion (HZE) particles:
  - Velocity: ~0.3–0.99 c (relativistic)
  - Linear energy transfer (LET): 10–1000 keV/μm
  - Penetration: Deep into tissue and shielding
  - RBE (relative biological effectiveness): 2–20× higher than gamma rays
```

### Van Allen Belts

#### Inner Belt (Protons)
| Property | Value |
|----------|-------|
| Altitude | 1,000–6,000 km |
| Peak intensity | ~5,500 km |
| Particle type | ~99% H⁺ (protons) |
| Typical energy | 10–100 MeV |
| Peak flux | 10⁵ protons/cm²/s |

#### Outer Belt (Electrons)
| Property | Value |
|----------|-------|
| Altitude | 13,000–60,000 km |
| Peak intensity | ~20,000–30,000 km |
| Particle type | Electrons (99%), some ions |
| Typical energy | 0.1–5 MeV |
| Peak flux | 10⁴–10⁵ electrons/cm²/s |

#### Trapped Particle Flux Dose
```
In the inner belt:
  100 MeV proton fluence: ~10⁹ protons/cm²/s
  Dose rate: ~10⁻³ Sv/s to 10⁻¹ Sv/s depending on altitude and solar activity

Crossing time: ~10–30 minutes (depends on trajectory)
```

## Radiation Dose Limits

### NASA Career Limits
| Cancer Risk Target | Lifetime Risk | Career Limit (Sv) |
|---------------------|-------------|--------------------|
| 3% REID (Risk of Exposure Induced Death) | 3% at 95% confidence | 600–1,000 mSv |

| Population Group | Limit (mSv) | Notes |
|------------------|-------------|-------|
| **Low Earth Orbit (astronaut)** | 600 mSv | Age/gender dependent |
| **Lunar surface** | 600–1,000 mSv | Higher due to no magnetosphere |
| **Mars transit** | 600–1,000 mSv | SPEs are the main concern |
| **Deep space (Galactic)** | 600 mSv | GCR is the chronic component |

### Annual Dose Comparison
| Source | Dose (mSv/year) |
|--------|-----------------|
| Natural background (Earth) | 2.4 mSv |
| Airline crew (1000 hrs) | ~5 mSv |
| Chest CT scan | ~7 mSv |
| Transatlantic flight (4 hrs) | ~0.008 mSv |
| **ISS crew (6 months)** | ~150 mSv | Mostly trapped radiation |
| **Lunar surface (6 months)** | ~80 mSv | Reduced GCR + no SPE shielding |
| **Mars transit (6 months)** | 600–1,000 mSv | GCR dominates |
| **Unprotected in interplanetary space** | 1,000–3,000+ mSv/year | Lethal over weeks/months |

## Shielding Effectiveness

### Material Stopping Power (Half-Value Layer — HVL)
```
HVL = ln(2) / μ

Where μ = linear attenuation coefficient (cm⁻¹)

Approximate HVL for 100 MeV protons:

  Material        HVL (cm)   Density (g/cm³)   Areal HVL (g/cm²)
  Aluminium        15 cm      2.7              40 g/cm²
  Polyethylene     18 cm      0.92            16.5 g/cm²
  Water (H₂O)      22 cm      1.0             22 g/cm²
  Lead             12 cm      11.3            136 g/cm² (less effective vs GCR)
```

### HVL by Radiation Type
| Radiation | Material | HVL (approx) | Notes |
|-----------|----------|--------------|-------|
| Solar proton (100 MeV) | Al | 15 cm | Protons deposit all energy, then stop |
| Solar proton (10 MeV) | Al | 2 cm | Lower energy = less penetration |
| GCR proton (1 GeV) | Al | 150 cm | Relativistic, very penetrating |
| GCR Fe nucleus (1 GeV/nucleon) | Al | 200+ cm | HZE particles, worst case |
| SPE proton (100 MeV) | Polyethylene | 18 cm | Hydrogen-rich = best |
| Gamma ray (1 MeV) | Pb | 7 cm | |
| Neutron (fast, 1 MeV) | H-rich | 5 cm (equiv) | Best stopped by hydrogen |

### Shielding Recommendations by Mission Phase
| Environment | Required Shielding | Equivalent Al Thickness |
|-------------|---------------------|-------------------------|
| **ISS (LEO)** | 5–10 g/cm² | ~2 cm Al |
| **Lunar surface** | 10–20 g/cm² | ~4 cm Al |
| **Lunar habitat core** | 200–500 g/cm² | ~6–15 cm Al (water/propellant) |
| **Lunar storm shelter** | 50–100 g/cm² | ~2–4 cm Al (hydrogen-rich) |
| **Mars transit** | 20–50 g/cm² | ~5–15 cm Al |
| **Mars surface** | 100–200 g/cm² | ~3–6 cm Al (regolith cover) |
| **Transit SPE shelter** | 5–10 g/cm² | ~1–2 cm Al (hydrogen) |

### Shielding by Material (g/cm² to reduce dose by 50%)
| Particle Type | Al | Polyethylene | Water | Regolith | Steel |
|---------------|----|-------------|-------|----------|-------|
| Solar proton (100 MeV) | 40 | 16.5 | 22 | ~30 | 38 |
| GCR (1 GeV/nucleon) | 1500+ | 600+ | 800+ | 500–1000 | 2000+ |
| Neutron | 10 | 8 | 10 | 20 | 15 |

## Application to Laguna Membranes

### theSuit Dose Calculation
```
During an EVA on the lunar surface:
- GCR dose rate: ~50–100 μSv/day
- SPE probability: ~5% per year for >100 MeV events
- During major SPE: ~0.1–1.0 Sv/hour

Required shelter for SPE: 5–10 g/cm² of hydrogen-rich material
  - This is ~15 cm of polyethylene or ~50 cm of lunar regolith
  - In a suit helmet: limited shielding — risk mitigation through timing
```

### theShip Transit Dosimetry
```
Interplanetary transit (Earth to Mars, ~6 months):
  GCR dose: ~50–70 mSv/month × 6 = ~400 mSv cumulative
  Plus potential SPEs: up to +500 mSv for a major event
  Risk mitigation: dedicated shelter (water walls) + SPE prediction alerts
```

## Sources
1. Clowdsley, M.S., et al. (2022). "Space radiation exposure and its effects on
   astronauts." *Life Sciences in Space Research*, 29(4), 103–122.
   — NASA radiation limits, exposure data
2. Wilson, J.W., et al. (2023). "Shielding concepts for lunar and Mars missions."
   *Acta Astronautica*, 215, 125–138.
   — HVL values, spacecraft shielding models
3. Durante, M., et al. (2021). "Galactic cosmic rays and the future of space
   exploration." *Nature Reviews Physics*, 3(12), 735–747.
   — GCR composition and dose rates
4. NASA. (2023). *Radiation Analysis for Exploration and Mission Planning.*
   NASA/TM-2023-221442.
   — SPE fluence statistics, lunar surface doses
5. ESA. (2022). "Space Environment Report." ESA/SC_VI/160760.
   — Van Allen belt intensities, trapped particle fluxes
6. Towns, W.E., et al. (2024). "Solar energetic particle events and Mars transit
   radiation risks." *Journal of Space Weather and Space Climate*, 14(2), 55–70.
   — SPE dose statistics, prediction
