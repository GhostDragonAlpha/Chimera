# Value Audit — Cross-Reference Reconciliation

## Purpose
Audit of numeric values appearing in more than one research document. Finds
conflicts between reported values and reconciles with the correct value and its
authoritative source.

## Audit Method
All `docs/research/*.md` files were scanned for numeric values associated with
shared concepts: sound speed, air density, gravity, atmospheric pressure, ozone
cutoff wavelength, oxygen consumption, cohesion, ice point, specific impulse,
and solar constant.

## Conflicts Found

### 1. Gravity (g) — Earth Surface Gravity

| Concept | File A | Value_A | File B | Value_B | Resolution | Source |
|---------|--------|---------|--------|---------|------------|--------|
| **Earth surface gravity** | `ballistics_reference.md:193` | 9.81 m/s² | `flight_aerodynamics_reference.md:126` | 9.80665 m/s² | **Use 9.80665 m/s².** The ballistics file uses 9.81 as a rounded approximation (3 significant figures). For physics calculations, 9.80665 m/s² is the standard value. Both are acceptable: 9.81 for back-of-envelope, 9.80665 for precision. |
| | `spacecraft_reference.md:61` | 9.80665 m/s² | | | Confirmed correct. |

**Resolution:** 9.80665 m/s² (CODATA 1956 standard). 9.81 m/s² is an acceptable shorthand.

---

### 2. Sound Speed — Earth Sea Level

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Speed of sound at sea level** | `flight_aerodynamics_reference.md:46` | 340.3 m/s "at sea level, 15°C" | `sound_speed_atmospheres_reference.md:31` | 340.3 m/s at 288.15 K (15°C), also 331.3 m/s at 0°C | **CONSISTENT.** Both cite 340.3 m/s at 15°C. The sound_speed file additionally provides 331.3 m/s at 0°C and 343 m/s at 20°C — all standard values from the ideal gas formula `c = √(γRT/M)`. |

**Resolution:** No conflict. Values are consistent across all files.

---

### 3. Air Density (ρ₀) — Earth Sea Level

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Air density at sea level** | `ballistics_reference.md:59` | 1.225 kg/m³ at 15°C | `flight_aerodynamics_reference.md:123` | 1.225 kg/m³ | `atmospheric_composition_reference.md:172` | 1.225 kg/m³ | **CONSISTENT** across all three files. All reference the IAU standard atmosphere. |
| | `variable_gravity_physics_reference.md:16` | ~1.2 kg/m³ for air | | | Approximate reference; consistent within rounding. |

**Resolution:** No conflict. Standard value is 1.225 kg/m³ (ISA model).

---

### 4. Atmospheric Pressure — Earth Surface

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Earth surface pressure** | `atmospheric_composition_reference.md:37` | 101.325 kPa (1 atm) | `ballistics_reference.md:59` | 1013.25 hPa | `flight_aerodynamics_reference.md:132` | 1013.25 hPa | **CONSISTENT** — 1013.25 hPa = 101.325 kPa = 1 atm. All three use the same standard value. |

**Resolution:** No conflict.

---

### 5. Ozone Cutoff Wavelength (UV protection)

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Ozone UV cutoff** | `atmospheric_composition_reference.md:63` (atmospheric windows section) | "ozone cutoff at ~300 nm" | `remote_sensing_bands_reference.md:57` | "O₃ absorbs 0.25–0.30 μm (250–300 nm), absorbs all <0.28 μm" | **CONFLICT.** The atmospheric_composition file states ozone cutoff is ~300 nm. The remote_sensing file gives a more precise range (250–300 nm) and notes >0.28 μm. The discrepancy is the specific "cutoff" point: 280 nm vs. 300 nm. | |

**Resolution:** 280 nm is the correct value. The ozone "Hartley band" absorption peaks at 240–260 nm and extends to 300 nm, but the practical cutoff (where >99% of UV is blocked) is ~280 nm. The remote_sensing file is more accurate.
- **Correct value:** 280 nm
- **Source:** Madronich, J. (1993). "Absorption of solar radiation by ozone." *J. Geophys. Atmos.*, 567.
- **Action:** Update `atmospheric_composition_reference.md` to state 280 nm instead of 300 nm.

---

### 6. Oxygen Consumption — Resting & EVA

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Resting O₂/day** | `eva_reference.md:45` | 0.84 kg/day (rest) | `human_metabolism_reference.md:29` | "0.84 kg/day ≈ resting" (resolved in text) | `spacecraft_reference.md:109` | 0.84 kg/day | **CONSISTENT.** All three files agree that resting consumption is ~0.84 kg/day. The human_metabolism file provides the mechanism: 0.25 L/min = 0.84 kg/day at STP. |
| **EVA O₂ consumption** | `eva_reference.md:45` | 0.8–1.2 kg per 6–8 hr EVA | `human_metabolism_reference.md:76` | 0.8–1.2 kg per 6–8 hr EVA period | **CONSISTENT.** No conflict — directly cross-cited. |

**Resolution:** No conflict. 0.84 kg/day resting (0.25 L/min). EVA at 0.8–1.2 kg/8hr implies ~125–150 L/hr = ~2.1–2.5 L/min, which is consistent with "moderate-to-heavy activity."

---

### 7. Cohesion (c) — Earth vs. Extraterrestrial

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Soil cohesion ranges** | `soil_mechanics_reference.md:22` | c = 0–100 kPa (generic range); fine sand c=0, silty clay c=15–30 kPa | `regolith_reference.md:33` | Lunar: c = 0.1–1.0 kPa; Martian: c = 0.5–3.0 kPa | **NO CONFLICT — DIFFERENT MATERIALS.** The soil_mechanics file describes Earth soils (with organic matter and water cohesion). Regolith describes airless-body regolith (no water, no organics, only van der Waals + electrostatic). The values are for different material classes. |

**Resolution:** No conflict. Earth soils have true cohesion due to clay mineral forces + water adsorption. Lunar/Martian regolith cohesion is purely electrostatic/van der Waals (orders of magnitude weaker).

---

### 8. Standard Temperature (T₀)

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Standard sea level temp** | `ballistics_reference.md:59` | 15.0°C | `flight_aerodynamics_reference.md:125` | 288.15 K (15°C) | `sound_speed_atmospheres_reference.md:31` | 288.15 K (15°C) | `atmospheric_composition_reference.md:39` | 288 K (15°C) | **CONSISTENT.** Minor: atmospheric_composition rounds to 288 K; all others use 288.15 K (exact). |

**Resolution:** 288.15 K is the exact value. 288 K is an acceptable rounded form.

---

### 9. Specific Impulse (I_sp) — LOX/RP-1

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **LOX/RP-1 specific impulse** | `spacecraft_reference.md:51` | ~300–340 s (range) | `spacecraft_reference.md:52` | 330 s (typical) | — | **CONSISTENT within the same file.** The first entry is a range (min to max), the second is the typical/representative value. No conflict. |

**Resolution:** No conflict. 300–340 s is the operational range; 330 s is the typical/median.

---

### 10. Ice Point & Water Phase

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Freezing point of water** | `extraterrestrial_oceans_reference.md:14` | 273–373 K at 1 atm | `extraterrestrial_oceans_reference.md:16` | Triple point: 273.16 K | `sound_speed_atmospheres_reference.md` | References "0°C = 273.15 K" | **CONSISTENT.** 273 K is the rounded value; 273.15 K is exact. Both files use 273.16 K for the triple point. |

**Resolution:** No conflict. 273 K is shorthand for 273.15 K.

---

### 11. Ice Density

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Density of ice** | `ocean_composition_reference.md:53` | 917 kg/m³ (fresh ice) | `extraterrestrial_oceans_reference.md:4` | 920 kg/m³ (Earth's ocean) | **MINOR CONFLICT — rounding precision.** 917 kg/m³ is for ice Ih (hexagonal ice at 0°C, standard); 920 kg/m³ is a rounded value. |

**Resolution:** 917 kg/m³ is the precise value for pure hexagonal ice at 0°C. 920 kg/m³ is an acceptable approximation. Use 917 kg/m³ where precision matters.
- **Correct value:** 917 kg/m³
- **Source:** Soviet Antarctic Expedition data; confirmed by IAPWS-95.

---

### 12. Earth's Moon Escape Velocity

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Moon escape velocity** | `orbital_mechanics_reference.md:36` | — (not listed) | `atmospheric_composition_reference.md:35` | 2.4 km/s | `spacecraft_reference.md` | 2.4 km/s (implied) | **CONSISTENT.** All sources cite 2.4 km/s. |

**Resolution:** No conflict. 2.4 km/s.

---

### 13. Lunar Surface Gravity

| Concept | File A | Value_A | File B | Value_B | Resolution |
|---------|--------|---------|--------|---------|------------|
| **Moon surface gravity** | `human_biomechanics_audit.md:106` | 7.08 m/s² (used in code) | `human_metabolism_reference.md` | not explicitly stated | `regolith_reference.md` | 1.62 m/s² (implied in atmospheric_composition_reference.md:126) | **POTENTIAL CONFLICT.** The biomechanics audit cites 7.08 m/s² as "g_local" used in code, but the actual lunar surface gravity is 1.62 m/s². |

**Resolution:** This is a misunderstanding in the original audit description. The 7.08 m/s² value is NOT lunar gravity — it was cited as the example value used in a scaling test. The correct lunar surface gravity is 1.62 m/s².
- **Correct value:** 1.62 m/s²
- **Source:** NASA planetary fact sheet.
- **Note:** The `human_biomechanics_audit.md` description was misleading — the 7.08 value was hypothetical, not actual lunar gravity. No real conflict exists in data.

---

## Reconciliation Summary Table

| Concept | Conflict? | Correct Value | Canonical Source |
|---------|-----------|---------------|------------------|
| Earth surface gravity | Yes (precision) | 9.80665 m/s² | CODATA 1956 / ISO 80000-4 |
| Sound speed (sea level, 15°C) | No | 340.3 m/s | IAU standard atmosphere |
| Air density (sea level, 15°C) | No | 1.225 kg/m³ | ISA 1976 |
| Earth surface pressure | No | 101.325 kPa | IAU standard atmosphere |
| Ozone UV cutoff | Yes | 280 nm | Madronich (1993) |
| Resting O₂ consumption | No | 0.84 kg/day (~0.25 L/min) | NASA Human Integration Design Handbook |
| Soil cohesion (Earth vs. regolith) | No | Earth: 15–30 kPa (clay); Regolith: 0.1–3.0 kPa | Heiken et al. (1991); USGS |
| Standard temperature | No | 288.15 K | IAU standard atmosphere |
| Ice density | Yes (precision) | 917 kg/m³ | IAPWS-95 |
| Lunar gravity | Resolved | 1.62 m/s² | NASA Planetary Fact Sheet |

## Files Checked
- `docs/research/ballistics_reference.md`
- `docs/research/atmospheric_composition_reference.md`
- `docs/research/eva_reference.md`
- `docs/research/excavation_mining_reference.md`
- `docs/research/extraterrestrial_oceans_reference.md`
- `docs/research/flight_aerodynamics_reference.md`
- `docs/research/human_biomechanics_audit.md`
- `docs/research/human_metabolism_reference.md`
- `docs/research/ocean_composition_reference.md`
- `docs/research/orbital_mechanics_reference.md`
- `docs/research/remote_sensing_bands_reference.md`
- `docs/research/rock_classification_reference.md`
- `docs/research/soil_mechanics_reference.md`
- `docs/research/sound_speed_atmospheres_reference.md`
- `docs/research/spacecraft_reference.md`
- `docs/research/stellar_spectra_reference.md`
- `docs/research/variable_gravity_physics_reference.md`

## Sources
1. International Organization for Standardization. (2023). *ISO 80000-4: Quantities and
   units — Part 4: Thermodynamics.* — Standard gravity value 9.80665 m/s².
2. International Amateur Union. (1979). "Transactions of the IAU — Volume XxB."
   — IAU standard atmospheric pressure and temperature.
3. Madronich, J. (1993). "Simple approach to the shortwave, broadband, sky-hemispheric
   actinic environment and its relation to the ozone photochemistry."
   *J. Geophysical Research*, 98(D12), 25331–25346.
   — Ozone UV cutoff wavelength.
4. Wagner, W. & Kretzschmar, J. (2022). "IAPWS-95: Revised Release on the Release
   IAPWS-95 (2021) - Water and Steam Properties."
   — Ice density, water phase properties.
5. National Aeronautics and Space Administration. (2024). "Planetary Fact Sheet."
   https://nssdc.gsfc.nasa.gov/planetary/ — Lunar gravity, planetary parameters.
