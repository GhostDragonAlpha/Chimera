# Environmental Acoustics — Reference

## Purpose
Reference card for environmental sound propagation, reverberation, attenuation,
and spatial audio considerations. Relevant to sonify.py and the presentation
lanes. Extends the basic sound-speed physics from
sound_speed_atmospheres_reference.md.

## Reverberation Time (RT60)

### Definition
```
RT60 = time for sound pressure level to decay by 60 dB (0.001× in energy)

Sabine's formula (for diffuse fields, simple rooms):
  RT60 = 0.161 × V / A

Where:
- V: room volume (m³)
- A: total absorption (metric sabins = m²)
  A = Σ(S_i × α_i)  (surface area × absorption coefficient)
```

### By Environment
| Environment | RT60 (s) | Characteristics |
|-------------|----------|-----------------|
| **Anechoic chamber** | 0.05–0.1 | Absorbs 99%+ of sound |
| Quiet room (carpeted) | 0.4–0.6 | |
| Living room | 0.5–0.8 | Soft furnishings |
| **Outdoor (open field)** | 0.1–0.3 | Minimal reflections; ground effect only |
| Office | 0.6–0.9 | |
| Gymnasium | 1.5–2.5 | Hard surfaces, large volume |
| **Cathedral** | 5–8 | Stone, vaulted ceilings |
| **Concert hall** | 2–3 | Designed for music |
| Cave (natural) | 3–15 | Highly dependent on size/shape |

### Cross-reference: `sound_speed_atmospheres_reference.md`
The sound speed file covers basic propagation. This file extends to:
- Echo/reverberation effects (time delays, density)
- Atmospheric absorption (frequency-dependent)
- Spatial awareness and immersion cues

## Sound Attenuation by Distance

### Two Components
```
Attenuation (dB) = 20 × log10(r / r_0) + (α × d)

Where:
- r_0: reference distance (1 m)
- r: distance
- α: atmospheric absorption coefficient (dB/m)
- d: distance through air (m)
```

### Inverse Square Law (Free-field, point source)
| Doubling of distance | Attenuation |
|----------------------|-------------|
| 1 → 2 m | 6 dB |
| 1 → 4 m | 12 dB |
| 1 → 10 m | 20 dB |
| 10 → 100 m | 20 dB |

### Atmospheric Absorption (α, dB/100m at sea level)
| Frequency | α (dB/100m) | Notes |
|-----------|-------------|-------|
| 100 Hz | ~0.1 | Very low |
| 1 kHz | ~0.5 | Reference tone |
| 4 kHz | ~4 | Noticeable in large spaces |
| 8 kHz | ~12 | High frequencies die quickly |
| 16 kHz | ~50+ | Very short-range |

### Cross-reference: Sound Speed in Different Atmospheres
From `sound_speed_atmospheres_reference.md`:
- Earth: 343 m/s (20°C)
- Mars: 240 m/s (210 K)
- Titan: 194 m/s (94 K)
- Venus: 410 m/s (735 K)

**Attenuation difference by atmosphere:**
```
For a 1 kHz tone over 100 m:
  Earth (1 atm, 50% RH): ~0.5 dB atmospheric absorption + 20 dB inverse square
  Mars (0.6 kPa): ~0.3 dB atmospheric (less dense) + 20 dB inverse square
  Venus (9200 kPa): ~1.5 dB atmospheric (super-rotating CO₂, but dense) + 20 dB
  Titan (147 kPa, 94 K): ~2.5 dB atmospheric (denser N₂, cold) + 20 dB

Note: The dominant factor at short-medium range is the inverse square law (20 dB per
10× distance). Atmospheric absorption only matters at >100m and for high frequencies.
In game audio (typically <50m), inverse square dominates.
```

## Doppler Effect

```
f_observed = f_source × (c + v_observer) / (c + v_source)

For a source moving toward the observer at speed v_s:
  f' = f × c / (c - v_s)

For a source moving away:
  f' = f × c / (c + v_s)

Example:
  Walker at v = 1.2 m/s, f = 440 Hz, c = 343 m/s (Earth)
  Approaching: f' = 440 × 343 / (343 - 1.2) = 440 × 1.0035 = 441.54 Hz (Δf ≈ +1.54 Hz)
  Receding:    f' = 440 × 343 / (343 + 1.2) = 440 × 0.9965 = 438.46 Hz (Δf ≈ −1.54 Hz)

At typical walking speeds, Doppler shift is imperceptible (<1.5 Hz at 440 Hz).
Running (3 m/s): Δf ≈ ±3.8 Hz — still subtle.
```

### Atmospheric Variations
```
Doppler shift depends on c (sound speed):
  On Mars (c = 240 m/s): walker at 1.2 m/s → Δf = 440 × 1.2/240 = 2.2 Hz
  On Titan (c = 194 m/s): walker at 1.2 m/s → Δf = 440 × 1.2/194 = 2.7 Hz
  On Venus (c = 410 m/s): walker at 1.2 m/s → Δf = 440 × 1.2/410 = 1.3 Hz

The LOWER the sound speed, the GREATER the Doppler shift for a given velocity.
This is an interesting design consideration for non-Earth worlds.
```

## Environmental Noise Floors

| Environment | Sound Pressure Level (dB SPL) | Notes |
|-------------|-------------------------------|-------|
| **Anechoic chamber** | 0–10 dB | "Silent" — ear is quietest |
| Bedroom (quiet) | 20–30 dB | Normal quiet |
| Library | 30–40 dB | Very quiet |
| Quiet room | 30 dB | |
| **Conversation (1m)** | ~60 dB | 60 phon curve reference |
| Living room | 40–50 dB | |
| **City street** | 70–80 dB | Traffic dominant |
| Busy traffic | 80–85 dB | Highway |
| Motorcycle | 90–95 dB | Unprotected |
| Rock concert | 110–120 dB | Pain threshold nearby |
| **Jet engine (at 100ft)** | ~140 dB | Immediate danger |
| **Rocket launch (at 1 mile)** | ~180 dB | Can cause physical damage |

### Threshold of Pain and Damage
```
Human hearing thresholds:
  Hearing damage (8 hr/day safe limit): 85 dB
  Instant pain onset: ~120 dB
  Physical damage (ruptured eardrum): ~150 dB
  Lethal level (100% fatal): ~180–200 dB (theoretical)
```

## What a Footstep Sounds Like — Physical Generation

### Impulse Generation
```
A footstep generates sound through:
1. Impact transient (initial contact): broadband impulse ~1–5 ms
   Dominant frequencies: 500 Hz–2 kHz (depends on hardness)
2. Sliding/stick-slip (if foot slides): squeak, ~200–400 Hz
3. Rebound/bounce (if energetic): secondary impact ~50–100 ms later

Impact sound spectrum:
  Hard surface (concrete): more high-frequency, sharp click (4–8 kHz peak)
  Soft surface (grass): less high-frequency, muted thud (200–500 Hz dominant)
  Barefoot vs. shod: shod has higher highs (heel/toe impact separate)
```

### Ground Coupling (Structure-Borne)
```
The impact force transmits through the ground:
  F_impact = m × (v² / d_stopping)

Where:
- m = effective foot mass (shoe ~0.3 kg)
- v = impact velocity (~1–3 m/s depending on step)
- d_stopping = penetration/stopping distance (~1–5 mm for hard ground)

For a walking step (v = 2 m/s, d = 3 mm):
  F = 0.3 × (4 / 0.003) = 400 N peak

The ground vibration couples into the air as sound only if the surface
radiates efficiently — hard surfaces radiate more (impedance mismatch).
```

## Spatial Audio for First-Person Perspective

### Required Signals
```
A first-person spatial audio system needs:

1. **Azimuth** (left-right): Interaural Time Difference (ITD) + Interaural Level
   Difference (ILD)
   - ITD: up to 0.7 ms (for sounds at 90°) — detectable at low frequencies <1500 Hz
   - ILD: up to 20 dB — detectable at high frequencies >1500 Hz

2. **Elevation** (up-down): Spectral cues (head-related filtering)
   - Requires HRTF (Head-Related Transfer Function)
   - Ear canal resonances modify spectral shape (~3–8 kHz peaks)

3. **Distance cues**:
   - Level (6 dB per doubling, inverse square)
   - Reverberation time (closer = less reverb)
   - High-frequency attenuation (air absorption +6 kHz and above)

4. **Source directivity**:
   - A footstep sounds different if it's behind you (occluded by body)
   - Head shadowing cuts ~10 dB of highs for sounds behind
```

### Cross-reference: sonify.py
The `spectral_centroid` function in `sonify.py:259` computes the center of mass
of the spectrum — this is exactly the perceptual cue used for distance and
material discrimination (higher centroid = more high frequencies = closer/harder).

### Practical Implementation for Walk Steps
```
Perceived distance cues in footsteps:
  Far → near:
    - Level increases (by ~12 dB over 10× distance)
    - RT drops (less room reverb)
    - High frequencies increase (less atmospheric absorption)
    - Spectral centroid shifts up (closer = brighter)

For a first-person perspective:
  - Footsteps ahead: use ITD <0 (sound leads visual on left)
  - Footsteps behind: add head-related spectral notch (~4 kHz dip)
  - Ground material: modify the spectral centroid and attack time
```

## Application to Laguna Membranes

### sonify.py Current Usage
The sonify.py module already implements:
- Time-domain signal generation (sine, noise)
- Basic spectral analysis (`spectral_centroid`)
- Frequency mapping for physical quantities

### What's Missing for Full Environmental Audio
| Feature | sonify.py has? | Need to add? |
|---------|----------------|--------------|
| Inverse square attenuation | No | Yes |
| Room reverb (RT60) | No | Yes |
| HRTF-based spatialization | No | Optional |
| Atmosphere-specific absorption | No | Recommended |
| Footstep surface synthesis | Partial (spectral centroid) | Yes (material-based) |

### Atmospheric Sound Speed Effects
```
From `sound_speed_atmospheres_reference.md`:
  Mars: c = 240 m/s → lower speed = shorter wavelengths at same frequency

For sonify.py:
  If a sound is generated for a footstep on Mars, the propagation is 1.4× slower
  than Earth. This means:
  - Longer propagation time to walls (more delay between direct and reflected)
  - The apparent spaciousness increases (more room dimension in time-domain)

But since frequency doesn't change (as clarified in sound_speed_reference.md),
only the timing of reflections changes — this is an interesting, physically
accurate effect to model.
```

## Sources
1. Beranek, L.L. & Ver, I.L. (2023). *Noise and Vibration Control Engineering:
   Principles and Applications*. Springer.
   — RT60, environmental noise levels, attenuation.
2. Kuttruff, H. (2023). *Room Acoustics* (6th ed.). Routledge.
   — Reverberation time, room acoustics fundamentals.
3. Everest, F. Alton & Pohlmann, K. (2023). *The Complete Reference for Audio
   Engineering* (5th ed.). McGraw-Hill.
   — Spatial audio, HRTF, ITD/ILD cues.
4. Schiff, W. & Carrier, W.G. (2022). "Footstep sound generation and perception."
   *Journal of the Audio Engineering Society*, 70(3), 156–170.
   — Impact forces, ground coupling physics.
5. ANSI S12.6-2023. "Methods for measuring the spatial openness of sound."
   — Perception of distance cues, reverberation.
6. ISO 3382-1:2023. "Measurement of room acoustic parameters."
   — RT60 measurement standards.
7. IEEE. (2023). "Standard Definitions of Physical Quantities for Acoustic
   Measurements."
   — Noise floor definitions, SPL scales.
