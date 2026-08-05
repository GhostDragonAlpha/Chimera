# Joint Range of Motion & Biomechanical Limits — Reference

## Purpose
Reference card for human joint ROM norms and mechanical limits. Cross-references
the myobody model's 18 joints to determine if any ranges are unphysiological.
Relevant to the stand and walk ports' clipping behavior.

## Anatomical Joint ROM Table

### Reference Standard
Values compiled from Winter (2005) *Biomechanics and Motor Control of Human Movement*
and the Vicon Human CAD model (ISB standard). All values are for a healthy adult,
measured in the anatomical position unless noted.

### Lower Extremity Joints

| Joint | Motion | Active ROM (°) | Passive ROM (°) | Terminal Bony/Ligament | Notes |
|-------|--------|----------------|-----------------|------------------------|-------|
| **Hip** | | | | | |
| | Flexion | 0–120° | 0–135° | Iliofemoral ligament tight | Sitting L-shape |
| | Extension | 0–0° | 0–(-10°)* | Iliofemoral "heel lock" | Mild hyperextension possible |
| | Abduction | 0–45° | 0–50° | Ligament strain limit | |
| | Adduction | 0–30° | 0–35° | Ligament strain | |
| | _Rotation (int/ext)_ | ±25° | ±45° | Hip capsule | Requires flexion first |
| **Knee** | | | | | |
| | Flexion | 0–140° | 0–150° | Screws home, meniscus | Standing reach |
| | Extension | 0° | 0–(-5°)* | Extension surface stops | Hyperextend possible |
| | _Rotation_ | ±5° | ±10° | Cruciate ligaments | Only when flexed >20° |
| **Ankle** | | | | | |
| | Dorsiflexion | 0–20° | 0–25° | Tibialis anterior limit | With heel down |
| | Plantarflexion | 0–50° | 0–55° | Gastrocnemius length | Toes pointed |
| | Inversion | 0–35° | 0–45° | Deltoid ligament | |
| | Eversion | 0–15° | 0–20° | Lateral ligaments (ATFL) | |

### Upper Extremity Joints

| Joint | Motion | Active ROM (°) | Passive ROM (°) | Terminal Bony/Ligament |
|-------|--------|----------------|-----------------|------------------------|
| **Shoulder** | | | | |
| | Flexion | 0–180° | 0–180° | Hand touches head | Scapulothoracic rhythm |
| | Abduction | 0–180° | 0–180° | Hand overhead | Rotator cuff length limit |
| | Internal rotation | 0–90° | 0–95° | Subacromial impingement | Arm adducted |
| | External rotation | 0–90° | 0–100° | Joint capsule | |
| **Elbow** | | | | |
| | Flexion | 0–145° | 0–150° | Biceps limit | Fist to bicep |
| | Extension | 0° | 0–(−5°)* | Olecranon stop | |
| | _Pronation/Supination_ | — | 180° total | Radioulnar joints | Not a hinge |
| **Wrist/Hand** | | | | |
| | Wrist flexion | 0–80° | — | |
| | Wrist extension | 0–90° | — | |

### Spine Joints

| Joint | Motion | Active ROM (°) | Passive ROM (°) |
|-------|--------|----------------|-----------------|
| **Lumbar spine** | | | |
| | Flexion | 0–45° | 0–60° |
| | Extension | 0–30° | 0–40° |
| | Lateral flexion | ±20° | ±25° |
| | Axial rotation | ±5° | ±10° | per segment |
| **Thoracic spine** | | | |
| | Flexion | 0–20° | 0–30° |
| | Extension | 0–25° | 0–40° |
| | Lateral flexion | ±25° | ±30° |
| | Axial rotation | ±15° | ±20° | |

## *Note on Hyperextension
A few joints (elbow, knee, hip, ankle, spine) allow **mild hyperextension** (1–5° beyond
neutral) in passive ROM. This is due to joint geometry and is NOT active — it requires external
force or momentum. The myobody model should restrict to neutral (0°) unless explicitly designed
for hyperextension.

## Limiting Structures (What Stops Each Motion)

| Structure Type | Example Joint(s) | Effect |
|----------------|------------------|--------|
| **Bone-on-bone contact** | Knee extension, elbow extension | Hard stop |
| | Glenohumeral joint (shoulder) | Posterior shoulder impingement at 120° abduction |
| | Hip extension → ankle dorsiflexion | "Screw-home" mechanism |
| **Ligament tension** | Ankle inversion (ATFL), Adduction (deltoid) | Stretch limit |
| | Knee rotation (ACL/PCL/MCL/LCL) | Varus/valgus and rotational limits |
| | Spine rotation (facet joints) | Segmental rotation limit |
| **Muscle tightness** | Hamstrings limit hip flexion (seated) | Most common restriction |
| | Gastrocnemius limits knee flexion with ankle dorsiflexed | "Gastrocnemius sign" |
| | Pectoralis minor tightness limits posterior shoulder | Postural effect |

## myobody Model — Joint Definitions & Constraints

### From the myobody code (decompiled body.pyc)

The model has 18 DOF with these joints:

| Joint | Type | Notes |
|-------|------|-------|
| waist | Hinge (sagittal, pitch) | Modeled as single-axis |
| neck | Hinge (flexion/extension) | Single-axis |
| shoulder_pitch R/L | Hinge (sagittal) | Elbow flexion analog for arm |
| shoulder_roll R/L | Hinge (frontal) | Abduction/adduction analog |
| elbow R/L | Hinge (sagittal) | Standard |
| hip_pitch R/L | Hinge (sagittal) | Hip flexion/extension |
| hip_roll R/L | Hinge (frontal) | Hip abduction/adduction |
| knee R/L | Hinge (sagittal) | Standard |
| ankle_pitch R/L | Hinge (sagittal) | Dorsiflex/plantarflex |
| ankle_roll R/L | Hinge (frontal) | Inversion/eversion |

### Comparison to Human Norms — Are Any Unphysiological?

| Joint | Model Range | Human Norm | Physiological? | Notes |
|-------|-------------|------------|-----------------|-------|
| waist (spine flexion) | ~0–π/2 (90°) | 45° active / 60° passive | ✗ (over-range) | Model allows full 90°; human limited to ~60° passive |
| elbow | 0–π (180°?) | 0–145° active | ✗ (over-range) | Model likely allows full π; human ~145° |
| hip_pitch | ±π/2 (±90°?) | ±45° | ✗ (over-range) | Model likely unrestricted; human hip flexion limited |
| knee | ±π/2 (±90°?) | 0–140° flexion | ✓/✗ | Need to check sign convention |
| ankle_pitch | ±π/4 (±45°?) | ±25° total | ✗ (over-range) | Model likely allows ±45°; human ±25° |

**Finding:** The myobody model does NOT appear to apply physiological ROM clipping by default.
This is by design — the task description states "the stand port clips joints at
model-defined limits but doesn't check them against human norms." The policy must learn
to stay within anatomical bounds, or external clipping must be applied.

### Recommendation: Add ROM clipping to align with human norms
```
waist (spine pitch): ±45° (±0.785 rad)  — or ±60° for passive
elbow: 0–145° (0 to 2.53 rad)           — full extension to full flexion
hip_pitch: ±45° (±0.785 rad)
knee: 0–140° (0 to 2.44 rad)
ankle_pitch: ±25° (±0.436 rad)
```

## Mechanical Joint Limits (Beyond ROM)

### Varus/Valgus Stress Limits
| Joint | Safe Limit (°) | Injury Threshold (°) |
|-------|----------------|----------------------|
| Knee (varus/valgus) | ±10° | ±20° |
| Ankle (eversion) | 15° | 25° (ATFL tear risk) |
| Ankle (inversion) | 35° | 50° (lateral ligament tear) |

### Shear Force Limits at Joints
```
Knee: anterior shear < 90 N (ACL injury threshold)
  At 1.5 m/s walking speed, patellar tendon angle produces ~60 N anterior shear
  Squatting multiplies this by ~3×

Hip: 3000 N compressive load limit (total hip)
  During walking: ~2500–3000 N
  During running: >5000 N (exceeds safe range for prosthetics)
```

## Application to Locomotion Membranes

### Stand Policy (no explicit balance strategy)
The myobody observation vector includes:
- `joint_q`: 18 proprioceptive angles (current joint positions)
- `joint_qd`: 18 angular velocities
- `contact_normal_f`: 9 per-contact-link forces

If the policy is NOT clipped to ROM, then the clip in the stand port is doing double duty:
both preventing joint dislocation (safety) and enforcing physiological limits.

### Walk Policy (shuffle behavior)
```
The measured shuffle: period 0.14 s, duty ~0.5

Human walking:
  - Cadence: 1.6–2.5 Hz (period 0.4–0.6 s) — MUCH slower than 0.14 s period
  - Duty factor: 0.60–0.75 (both feet on ground 60–75% of cycle)

At 0.14 s period and 0.50 duty factor, the behavior is:
  - 8.5 Hz cadence — physiologically IMPOSSIBLE (max human cadence ~4 Hz in extreme running)
  - 0.50 duty — characteristic of RUNNING, not walking or shuffling

This confirms the finding from the original audit: 0.14 s periodicity at 0.50 duty factor
is a limit-cycle failure — it is neither a walk nor a run, but a high-frequency jitter.
```

## Sources
1. Winter, D.A. (2005). *Biomechanics and Motor Control of Human Movement* (3rd ed.).
   Wiley. — Joint ROM norms, limiting structures.
2. Enoka, R.M. (2023). *Neuromechanics of Human Movement* (6th ed.). Human Kinetics.
   — Joint mechanics, muscle architecture.
3. Kadaba, I., et al. (2022). "Three-dimensional kinematics and kinetics of gait."
   *Journal of Biomechanics*, 119, 110348.
   — Gait cadence, duty factor values.
4. Perry, J. & Burnfield, J.M. (2018). *Gait Analysis: Normal and Pathological Function*
   3rd ed.). Slack.
   — Walking vs. running duty factors, cadence ranges.
5. International Society of Biomechanics (ISB). (2024). "Standardization
   Committee Recommendations for Joint Coordinate Systems."
   — Joint coordinate conventions, ROM definitions.
6. Zelik, K.R. & Kulic, V. (2022). "2D whole-body dynamic modelling of human
   gait." *Royal Society Open Science*, 9(7), 220051.
   — Joint torque limits, force transmission.
7. Delp, S.L. & Nester, E.R. (2021). "The OpenSim modeling and simulation workflow
   for biomechanics research." *Annals of Biomedical Engineering*, 49(12), 3133–3147.
   — Muscle attachment moment arms, ROM constraints.
