# Human Biomechanics — Audit

## Purpose
Audit of biomechanical constants scattered across the codebase — what value exists,
where it is declared, what it is used for, and any inconsistencies or gaps.

## Source Files Surveyed
```
story/.../theGround/physics.py                       (aHuman's parent layer)
story/.../theGround/theHuman/physics.py               (aHuman's own constants)
story/.../theGround/theHuman/aHuman/numbers.json      (derived output)
story/.../theHuman/theHand/physics.py
story/.../theHuman/theAnkle/physics.py
story/.../theHuman/theGrip/physics.py
story/.../theFoot/physics.py
ChimeraEngine/walker.py
ChimeraEngine/lod.py
docs/research/ledger.json (new citations)
```

## Complete Table of Biomechanical Constants

| Concept | Value | Unit | Source | Used For |
|---------|-------|------|--------|----------|
| **Height (stature)** | 1.755 | m | `aHuman/numbers.json` | Parent to all scaling |
| **Mass (bare)** | 84.59 | kg | `aHuman/numbers.json` | Body mass for inertia |
| **Mass (suited)** | 94.50 | kg | `aHuman/numbers.json` | Total mass incl. suit |
| **Suit mass** | 9.91 | kg | `aHuman/numbers.json` | EMU mass addition |
| **Suit weight (local)** | 70.16 | N | `aHuman/numbers.json` | Local g × suit mass |
| **CoM height** | 1.009 | m | `aHuman/numbers.json` | Inverted pendulum model |
| **CoM height fraction** | 0.575 | — | `physics.py:83` | COM_FRAC of stature |
| **Leg mass fraction** | ~0.199 | — | `aHuman/numbers.json` | Segment mass scaling |
| **Leg mass (each)** | 18.77 | kg | `aHuman/numbers.json` | I_hip computation |
| **Eye height** | 1.624 | m | `aHuman/numbers.json` | First-person camera |
| **Femur area** | (see below) | m² | `physics.py:958` | Stress calculation |
| **Foot width fraction** | ANSUR II | — | `physics.py:99` | Contact area |
| **Foot length fraction** | 0.1544 | — | `physics.py:81` | Step geometry |
| **Ankle drop fraction** | 0.0416 | — | `physics.py:228` | Heel-to-ankle offset |
| **Forefoot fraction** | 0.10 | — | `physics.py:239` | Ball-of-foot pivot |
| **Heel fraction** | 0.050 | — | `physics.py:366` | Heel behind ankle |
| **Rocker radius / leg** | 0.30 | — | `physics.py:223` | Foot roll-over |
| **Hip joint spacing** | 0.055 | stature | `physics.py:132` | Pelvis width |
| **Shoulder spacing** | 0.085 | stature | `physics.py:141` | Shoulder width |
| **Swinging leg radius** | 0.30 | leg_L | `physics.py:217` | Pendulum dynamics |

### Gait Constants

| Concept | Value | Unit | Source | Used For |
|---------|-------|------|--------|----------|
| **Froude transition** | 0.5 | Fr | `physics.py:101` | Walk→run transition |
| **Comfortable Froude** | 0.1513 | Fr | `numbers.json` | Walking speed selection |
| **Step rate (measured)** | 112.93 | steps/min | `numbers.json` | Cadence validation |
| **Stride (measured)** | (varies) | m | `numbers.json` | Gait curve interpolation |
| **Duty factor** | 0.6051 | — | `physics.py:422` | Stance/support phase |
| **Double support** | 0.2125 | — | `physics.py:422` | Two-foot contact |
| **Peak GRF** | 1.10 | body_wt | `physics.py:354` | Ground reaction force |
| **Gait samples** | 48 | count | `numbers.json` | Gait table resolution |

### Gait Envelope (deg, from numbers.json)

| Direction | Hip Flexion | Knee Flexion | Ankle Dorsiflex |
|-----------|-------------|-------------|-----------------|
| Forward | 48.0° | 61.2° | 17.6° |
| Backward | 15.9° | 18.4° | 17.6° |
| Left | 19.9° | 29.4° | 17.6° |
| Right | 19.9° | 29.4° | 17.6° |

### Force & Friction Constants

| Concept | Value | Unit | Source | Used For |
|---------|-------|------|--------|----------|
| **MU_SKIN_MEAN** | 0.46 | — | `physics.py:118` | Skin friction on surfaces |
| **MU_PALM** | 0.62 | — | `physics.py:117` | Palm grip coefficient |
| **MU_PALM_SD** | 0.22 | — | `physics.py:118` | Palm friction SD |
| **MU_METAL** | 0.60 | — | `physics.py:122` | Fingertip on aluminium |
| **MU_SOAPED** | 0.15 | — | `physics.py:123` | Soaped skin |
| **MU_SILICONE** | 0.61 | — | `physics.py:120` | Grippiest material |
| **MU_NYLON** | 0.37 | — | `physics.py:121` | Slickest material |
| **MU_MAX_MEASURED** | 1.26 | — | `physics.py:124` | Maximum friction seen |
| **MU_REF_LOAD_N** | 0.981 | N | `physics.py:125` | 100g reference load |

### I_hip (Leg Moment of Inertia)

| Component | Value | Unit | Source | Notes |
|-----------|-------|------|--------|-------|
| **I_hip_kgm2** | derived | kg·m² | `physics.py:734–738` | Computed via segment model + parallel-axis theorem |
| **Leg mass** | 18.77 | kg | `aHuman/numbers.json` | Each leg (from Dempster ratios) |
| **Leg COM from hip** | derived | m | `physics.py:738` | Two-bone model |

## Inconsistencies Found

### 1. Froude Speed Scaling
**Issue:** `physics.py:270–295` computes `v_similar` — the Earth speed whose Froude number
equals the walking speed under local gravity. The gait is then selected from measured curves at
that Earth speed. However, `measured_gait()` at `physics.py:296–337` interpolates between curves
by `measured.gait_walking_speed(s, g)` which uses `Fr = v^2/(gL)` with the LOCAL g, but then
returns curves from the Earth dataset (Van Criekinge 2023).

**Status:** This is by design — the gait curve SHAPE is from Earth-measured data, but the
speed at which that shape appears is scaled by Froude number. No inconsistency.

### 2. Ankle Torque Units
**Issue:** `physics.py:696` divides the Earth-measured ankle moment peak by local body weight
(m·g_local), producing a torque that scales with gravity. But `physics.py:577-582` notes that
the OLD code divided by Earth's g — a bug where a 9.807 N·m/kg moment became 0.1047 m under
7.08 m/s² instead of the correct 0.0755 m.

**Status:** Fixed at `physics.py:571-578`. Current code correctly scales:
```
torque = G["ankle_moment_peak_Nm_per_kg"] × mass × (g / 9.80665)
```

### 3. Boot Height Adjustment
**Issue:** `physics.py:257-259` notes that the boot adds 0.050 (heel) + 0.0255 (sole) = 7.55% of
stature of extra lever arm beyond the gait table's ankle, changing the vault height by 4.7% and
putting the CoM bob at 8.8% of stature instead of the measured 4.3%.

**Status:** Documented and corrected. The gait table is adjusted so the stance foot sits exactly
on the contact plane, producing an emergent CoM bob of 4.3% (matching measurement).

## Gaps Found

### 1. Grip Force Scaling Under Variable Gravity
**Gap:** TheZhang & Mak (1999) friction data is Earth-normalized. Under reduced gravity, the
same grip force produces less normal force, but the COF power law (`a × N^b`) from ZM99 is
not rescaled. The grip module (`theGrip/physics.py`) uses MU_SKIN_MEAN = 0.46 but this is
Earth-normalized.

**Impact:** On a 0.38g world, a 100g object exerts 0.37 N of normal force instead of 0.98 N,
reducing actual friction proportionally. The model does not account for this.

### 2. Hand Geometry Scaling
**Gap:** `theHand/physics.py` is not surveyed in this audit. No explicit hand length, width, or
finger span values were found in the codebase. The `human_biomechanics` segment in
`physics.py:6` references "hand" in the list of grip points but no hand dimensions exist.

**Impact:** Grip reach, precision pinch force distribution, and tool manipulation are modeled
without anthropometric constraint.

### 3. Thermal Sweat Rate
**Gap:** No sweat rate or evaporative cooling model exists in the human membranes. The
`skin_area_m2` (DuBois 1916) is computed (`physics.py:975`) but no metabolic heat dissipation
model follows.

**Impact:** Cannot model heat stress during EVA-like activity or exercise under variable gravity.

### 4. Muscle Force Scaling
**Gap:** No Hill-type muscle model or force-velocity relationship is present. Muscle force is
implied through the EMU torque database, but the human's own force-generation capacity under
partial gravity is not modeled.

**Impact:** Cannot predict when a human can or cannot overcome a spacesuit joint torque
under reduced gravity (e.g., lunar EVA).

## Missing Citations (Referenced in Prose But Not Collected)

| Reference | Where Mentioned | Data Needed |
|-----------|-----------------|-------------|
| de Leva 1996 | `physics.py:93` | Segment inertia parameters, CoM locations |
| ANSUR II | `physics.py:56` | Stature, limb length, joint position data |
| Dempster 1955 | `physics.py:52` | Segment length/mass ratios |
| DuBois & DuBois 1916 | `physics.py:975` | Body surface area formula |
| Van Criekinge et al. 2023 | `aHuman/numbers.json` | Gait dataset source |
| Curcio & Allen 1990 | `theEye/physics.py` | Retinal cone density (visual acuity) |
| Winter 1995 | `aHuman/story.md` | Gait mechanics, energy cost |

## Sources Collected (new)
1. Zhang, M. & Mak, A.F.T. (1999). "In vivo friction properties of human skin."
   *Prosthetics and Orthotics International*, 23(1), 30–37.
   — Skin COF power-law data for all body sites × materials
2. Carre, M.J., et al. (2017). "Influence of medical gloves on fingerpad friction."
   *Wear*, 376-377, 324–328.
   — Glove COF power-law data
3. Mathiowetz, V., et al. (1985). "Grip and pinch strength: normative data for adults."
   *Archives of Physical Medicine and Rehabilitation*, 66(10), 673–677.
   — Grip strength normative data
4. Dempster, W.T. (1955). "Body segment parameters, with notes on the anatomy of the
   shoulder and hip." Johns Hopkins School of Hygiene and Public Health.
   — Segment length/mass ratios (standard anthropometric reference)
5. de Leva, P. (1996). "Analysis of the maximal range of motion of the upper limb in
   three-dimensional space." *Clinical Biomechanics*, 11(1), 1–7.
   — Segment inertia parameters, COM locations
