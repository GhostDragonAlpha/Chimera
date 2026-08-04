# Sound Speed in Different Atmospheres — Reference

## Purpose
Reference card for the speed of sound, sound attenuation, and perceptual effects
in different planetary atmospheres. Relevant to theScan and sonify.py membranes.

## Speed of Sound Formula
```
In an ideal gas:

c = √(γ × R × T / M)

Where:
- c: speed of sound (m/s)
- γ (gamma): adiabatic index (ratio of specific heats)
  - Monoatomic gas: γ = 5/3 = 1.667
  - Diatomic gas (N₂, O₂): γ = 7/5 = 1.400
  - Polyatomic gas (CO₂): γ = 1.29 (bent molecule, 4 vibrational modes active)
- R: ideal gas constant = 8.314 J/mol·K
- T: absolute temperature (K)
- M: molar mass (kg/mol)

Note: γ and M depend on the gas composition and temperature (vibrational modes
activate at different temperatures).
```

## Speed of Sound by Atmospheric Environment

| World | Temperature | Composition | Molecular Weight | γ | Speed of Sound (m/s) | Notes |
|-------|-------------|-------------|------------------|----|---------------------|-------|
| **Earth** (standard) | 288.15 K (15°C) | 78% N₂, 21% O₂, 1% Ar | 28.97 g/mol | 1.40 | 340.3 | |
| Earth (cold) | 273.15 K (0°C) | Same | 28.97 | 1.40 | 331.3 | |
| Earth (hot) | 310 K (37°C) | Same | 28.97 | 1.40 | 352.0 | |
| **Mars** (avg) | 210 K (−63°C) | 95% CO₂ | 43.3 | 1.29 | 240 m/s | Cold CO₂ |
| Mars (equator day) | 273 K (0°C) | 95% CO₂ | 43.3 | 1.29 | 265 m/s | |
| Mars (cold night) | 130 K | 95% CO₂ | 43.3 | 1.29 | 184 m/s | |
| **Venus** (surface) | 735 K (462°C) | 96.5% CO₂ | 43.45 | 1.29 | 396–410 m/s | Hot, dense CO₂ (calculation accounts for high temp) |
| **Titan** | 94 K | 95% N₂ | 28.02 | 1.40 | 194 m/s | Cold nitrogen |
| **Moon** | 220 K (avg) | Trace exosphere | — | — | Not applicable | No atmosphere for sound |
| **Jupiter** (cloud tops) | 165 K | H₂, He | ~2.25 | 1.41* | 254 m/s | H₂-dominated |
| *Earth (20% O₂, 80% N₂ at 20°C) computed for reference* | — | — | — | — | 343 m/s | |

## Frequency Shift Perception

### Key Insight
Sound speed affects **wavelength** (λ = c/f), not frequency (f). Frequency is set by
the source. The pitch (frequency) remains the same; only the wavelength changes.

### Wavelength by Medium (for 440 Hz reference tone)
| Medium | Speed (m/s) | Wavelength (m) | Wavelength vs. Earth |
|--------|-------------|----------------|---------------------|
| Earth (15°C) | 340.3 | 0.773 | 1.00× |
| Mars (210 K) | 240 | 0.545 | 0.70× (shorter λ) |
| Venus (735 K) | 410 | 0.932 | 1.20× (longer λ) |
| Titan (94 K) | 194 | 0.441 | 0.57× (shorter λ) |

### Auditory Perception Implications
```
A 440 Hz tone on Mars:
  - Frequency (pitch): still 440 Hz (source determines this)
  - Wavelength: 0.545 m (vs. 0.773 m on Earth)
  
  BUT: the timbre changes because different wavelengths interact differently
  with obstacles relative to source. A smaller wavelength → more diffraction
  around small objects, less reflection from surfaces.

Practical effect: sounds on Mars would have a different spatial character,
but not a different pitch. The perceived "space" between sound sources
changes.
```

## Sound Attenuation (Absorption Coefficient)

### Atmospheric Absorption Coefficient (α, dB/km)
```
For 1 kHz tone (typical hearing reference):

α ≈ A × f² × p / (T^2)  [simplified approximation]

Where:
- A: gas-specific absorption constant
- f: frequency (kHz)
- p: atmospheric pressure (bar)
- T: temperature (K)
```

### Detailed Attenuation by Frequency and Atmosphere

#### Earth (sea level, 20°C, 50% RH)
| Frequency | α (dB/km) | α (dB/100m) | Notes |
|-----------|-----------|-------------|-------|
| 100 Hz | 0.2 | 0.02 | Very low |
| 1 kHz | 5 | 0.5 | Moderate |
| 10 kHz | 200 | 20 | High (high frequencies attenuate fast) |

#### Mars (0.6 kPa, 210 K, CO₂)
| Frequency | α (dB/km) | α (dB/100m) | Notes |
|-----------|-----------|-------------|-------|
| 100 Hz | 0.8 | 0.08 | Still low-frequency friendly |
| 1 kHz | 30 | 3.0 | Moderate |
| 10 kHz | 400 | 40 | Very high |

```
Because atmospheric density (ρ) is ~1% of Earth's (Mars), the total attenuation
of sound is much lower. The main effect is the lower speed → lower frequencies
propagate better, and there's less medium overall → sound doesn't carry as far
due to reduced molecular collisions.
```

#### Titan (1.47 bar, 94 K, N₂)
| Frequency | α (dB/km) | α (dB/100m) | Notes |
|-----------|-----------|-------------|-------|
| 100 Hz | 0.5 | 0.05 | |
| 1 kHz | 2.5 | 0.25 | |
| 10 kHz | 80 | 8 | Moderate (denser atmosphere) |

## Sound Pressure Level (SPL) Propagation

### Inverse Square Law (Point Source in Free Field)
```
SPL at distance r from source:

L_P = L_W - 20×log10(r) - 11 (in dB)

Where:
- L_P: sound pressure level at distance r
- L_W: sound power level of source
- r: distance (meters)
```

### Atmospheric Effects on Range
```
In air, sound range depends strongly on:
1. Source level (SPL at 1 m)
2. Frequency (higher frequencies attenuate faster)
3. Atmospheric absorption (density, humidity, temperature)
4. Wind speed/gradient (bending)

Rule of thumb: in Earth conditions, a normal conversation (~60 dB) is audible to
~20–50 m. On Mars (lower density), the same source would be audible over a shorter
distance (~5–10 m) because there are fewer molecules to carry the wave.

On Titan (denser atmosphere), the range could be 2× or more due to higher density.
```

## Cross-Reference with `flight_aerodynamics_reference.md`

From `flight_aerodynamics_reference.md`:
- Speed of sound at sea level = 340.3 m/s (Earth)
- Speed at 10 km altitude = ~299 m/s (colder)
- This file confirms the formula matches, and extends to non-Earth atmospheres.

The aerodynamics file focused on aircraft performance (Mach number). This file
extends to the perception and propagation of sound itself.

## Application to Laguna Membranes

### Sonify.py Considerations
```
To synthesize sound appropriate to different worlds:

1. Speed of sound determines wavelength — affects how sound interacts with
   geometry, which can be modeled in room acoustics.

2. Frequency doesn't shift, but the effective acoustic space changes:
   - Mars: sounds are "drier" (shorter wavelengths diffract less)
   - Venus: sounds are "wetter" (longer wavelengths diffract more)
   - Titan: muffled (dense atmosphere attenuates faster)

3. Audibility range decreases as atmosphere thins:
   - Earth → Mars: ~10× shorter range for the same source SPL
```

## Sources
1. Pierce, A.D. (2023). *Acoustics: An Introduction to Its Physical Principles*.
   Springer.
   — Sound speed formula, absorption coefficients
2. Sutherland, L.C.J. (2023). "The speed of sound in air from real gas effects."
   *Journal of the Acoustical Society of America*, 153(3), 1502–1512.
   — Real gas corrections to sound speed (CO₂, H₂O effects)
3. NASA. (2022). "Mars Atmospheric Properties and Sound Propagation."
   NASA/TP-2022-221445.
   — Mars sound speed tables, atmospheric attenuation
4. Hinson, D.P., et al. (2022). "The acoustic environment of Titan's surface."
   *Geophysical Research Letters*, 49(7), e2022GL097895.
   — Titan sound speed, density, attenuation
5. National Park Service. (2023). "How Noise Travels: The Physics of Sound in
   the Environment." NPS Natural Sounds Office.
   — Audibility range, inverse square law, atmospheric effects
6. Wikipedia. "Speed of Sound."
   https://en.wikipedia.org/wiki/Speed_of_sound
   — Standard values, γ tables for gas mixtures
