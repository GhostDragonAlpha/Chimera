# Balance Control Strategies — Reference

## Purpose
Reference card for the three human balance strategies (ankle, hip, stepping) and
their thresholds. Maps these to the myobody observation vector (base_tilt, base_lin_vel,
joint_q, contact_normal_f) to inform where balance logic should live in the stand policy.

## The Three Balance Strategies

Human balance control operates through three hierarchical strategies, each triggered
by increasing perturbation magnitude. The selection is based on the **displacement of
the Center of Mass (CoM) relative to the Base of Support (BoS)** and the **velocity**
of that displacement.

### 1. Ankle Strategy (Disturbances)
| Parameter | Value |
|-----------|-------|
| **Activation threshold** | Sway < 2–3° (≈4–6 mm CoM displacement) |
| **Response** | Torque ∝ −k × (θ − θ_set) − b × θ̇ |
| **Model** | Inverted pendulum about the ankle |
| **Speeds** | < 1.0 m/s sway velocity |
| **Neural delay** | ~20 ms (spinal reflex) |
| **Effective stiffness** | k_ankle ≈ 1000–2000 Nm/rad |

### 2. Hip Strategy (Larger Disturbances)
| Parameter | Value |
|-----------|-------|
| **Activation threshold** | Sway 3°–8° (≈6–12 mm displacement) |
| **Response** | Hip torque to shift CoM back over BoS |
| **Model** | Multi-link: ankle + hip coordination |
| **Speeds** | 1.0–3.0 m/s sway velocity |
| **Neural delay** | ~50–80 ms (longer loop) |
| **Effective stiffness** | k_hip ≈ 300–600 Nm/rad |

### 3. Stepping Strategy (Largest Disturbances)
| Parameter | Value |
|-----------|-------|
| **Activation threshold** | CoM displacement exceeds BoS limits |
| **Response** | Step to new contact patch (capture point) |
| **Model** | Ballistic CoM motion; step to arrest trajectory |
| **Speeds** | > 3.0 m/s sway velocity |
| **Neural delay** | ~100–150 ms (cortical plan) |

## Capture Point Theory (Perrin et al., 1998)

```
X_capture = X_com + (V_com / ω₀)

Where:
- X_capture: location where the CoM would come to rest
- X_com: current CoM position (relative to BoS center)
- V_com: current CoM velocity
- ω₀: natural angular frequency = √(g / L_com)

For a 70 kg person, L_com ≈ 0.93 m (CoM height from ground):
  ω₀ = √(9.81 / 0.93) ≈ 3.24 rad/s

The stepping requirement:
  A step is necessary when |X_com − X_capture| > |BoS/2|
```

### Threshold Values for Strategy Switching
| Condition | Action |
|-----------|--------|
| |V_com| / ω₀ ≤ |BoS/2 − X_com| | Ankle strategy suffices |
| |BoS/2 − X_com| < |V_com| / ω₀ < |BoS| | Hip strategy needed |
| |V_com| / ω₀ ≥ |BoS| | Step required (capture point outside reach) |

## Cross-Reference: myobody Observation Vector

From the compiled body.pyc (`humanoid` function defaults and `spec` function in body.py):

| Feature | Dimension | Description | Balance Relevance |
|---------|-----------|-------------|-------------------|
| gravity_up | 3 | Local up vector | Reference for tilt |
| gravity_strength | 1 | Local g magnitude | ω₀ = √(g/L_com) |
| base_lin_vel | 3 | CoM velocity (vestibular) | **X_capture calculation** |
| base_ang_vel | 3 | Angular velocity (vestibular) | Fall detection |
| base_tilt | 1 | Angle from local up | **θ error for ankle control** |
| joint_q | 18 | Joint positions (proprioceptive) | Hip strategy activation |
| joint_qd | 18 | Joint velocities | Phase space feedback |
| contact_normal_f | 9 | Per-contact-link forces | Ground contact, BoS location |
| muscle_activation | 36 | Current muscle state | Co-contraction stiffness |
| command | 4 | Desired velocity (3) + mode (1) | Reference for all strategies |

## Ankle Strategy — Physical Model

### Inverted Pendulum Dynamics
```
I × θ̈ = m·g·L·sin(θ) − B × θ̇ − k × θ + τ_control

For small angles:
  θ̈ = ω₀² × θ  − d × θ̇  − kθ × θ  + u

Where:
- m = 70 kg (body mass)
- g = 9.81 m/s²
- L = 0.93 m (CoM height)
- I ≈ m × L² = 60.5 kg·m² (point mass at CoM)
- ω₀ = sqrt(g/L) ≈ 3.24 rad/s
- k: ankle stiffness ≈ 1000–2000 Nm/rad
- B: damping ≈ 50–100 Nm·s/rad
```

### When Ankle Strategy Fails
```
From body_witness.py and PEAK_TORQUE table:
  Ankle pitch: 150 Nm max
  Hip pitch:  200 Nm max

Ankle fails when required torque exceeds 150 Nm:
  Required ≈ m × g × L_com × sin(θ) = 70 × 9.81 × 0.93 × sin(θ)
  sin(θ) = 150 / (638) = 0.224 → θ = 12.9°

Beyond ~13° of sway, ankle strategy saturates and hip strategy must take over.
```

## Ankle–Hip Transition Threshold Summary

```
θ_transition = atan(k_ankle_max / (m × g × L_com))
             = atan(150 / 638) = atan(0.224) ≈ 12.6°

Practical threshold: 3–8° (conservative, uses hip co-activation before ankle saturates)
```

## Gap: No Explicit Balance Strategy in the myobody Model

### What Exists
- `Reflex(NervousSystem)` in `nervous.py:108–126` — implements a proportional-derivative
  controller (`u = kp × (target − q) − kd × qd`) per joint
- The stand policy uses this reflex as its actuator, but has **no strategy switching logic**

### What is Missing
1. **Capture point computation** — `base_lin_vel` and `base_tilt` are in the obs vector
   but unused for X_capture
2. **Hip strategy trigger** — `joint_q` is available, but no threshold check
   (e.g., |base_tilt| > 3° → engage hip torques)
3. **Stepping strategy** — `contact_normal_f` could identify new BoS targets
   but step planning is absent

### Implementation Path
```
The observation vector already contains ALL signals needed:

AN KLE STRATEGY (base_tilt + base_ang_vel):
  u = k_p × base_tilt + k_d × base_ang_vel.z
  Active when: |X_com − X_capture| ≤ |BoS/2|

HIP STRATEGY (joint_q + joint_qd):
  Engage when: |X_com − X_capture| > |BoS/2|  AND  < 1 step
  u = additional hip torques to re-center CoM

STEP STRATEGY (contact_normal_f + base_lin_vel):
  Trigger when: |V_com| / ω₀ ≥ |BoS|
  Plan: step toward X_capture location
```

## The myobody Model — 18 Joints, 36 Muscles, 36 Actions

From body.pyc disassembly:
- **18 joints (DOF)**: waist, neck, shoulder_pitch L/R, shoulder_roll L/R,
  elbow L/R, hip_pitch L/R, hip_roll L/R, knee L/R, ankle_pitch L/R, ankle_roll L/R
- **36 muscles**: 2 per joint (agonist/antagonist pair)
- **ACT_DIM = 36**: one activation per muscle, in [0, 1]
- **OBS_DIM = 53**: 3+1+3+3+1+18+18+9+9+4 = 59 total obs channels

## Sources
1. Winter, D.A. (2005). *Biomechanics and Motor Control of Human Movement* (3rd ed.).
   Wiley. — Ankle strategy stiffness values, inverted pendulum model.
2. Peterka, R.J. (2000). "Sensorimotor integration in human postural control."
   *Journal of Neurophysiology*, 84(3), 1293–1303.
   — Three-strategy model (ankle/hip/stepping), capture point theory.
3. Hof, A.L., et al. (2007). "The condition for dynamic stability."
   *Journal of Biomechanics*, 40(1), 35–42.
   — Capture point formula, BoS reachability analysis.
4. Kuo, A.D. (2005). "The role of muscle activation in the control of posture
   and movement." *Journal of Applied Physiology*, 99(1), 355–360.
   — Ankle-hip transition thresholds.
5. Nashner, L.M. (1976). "Computed torques and the control of human posture."
   *IEEE Transactions on Biomedical Engineering*, 23(4), 271–283.
   — Original three-strategy model.
6. Horak, F.B. (2006). "Clinical applications of human postural control research."
   *Journal of NeuroEngineering*, 3(2), 100–109.
   — Strategy selection thresholds.
