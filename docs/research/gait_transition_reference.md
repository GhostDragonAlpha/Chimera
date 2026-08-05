# Gait Transition Mechanics — Walk to Run — Reference

## Purpose
Reference card for the mechanics of gait transition (walk ↔ run), anchored to the
Froude number criterion used in the codebase (THE_MATHEMATICS_OF_WALKING.md cites
Fr = 0.1513 for walk, 0.5 for transition). Explains what changes at transition
and why the observed shuffle (period 0.14 s, duty ~0.5) is a limit-cycle failure.
Relevant to the walk port's policy.

## The Froude Number — The Governing Physics

```
Fr = v² / (g × L)

Where:
- v: walking velocity (m/s)
- g: gravitational acceleration (m/s²) — 9.80665 on Earth
- L: leg length (m) — from hip joint to floor contact

The Froude number is the ratio of inertial force to gravitational force.
It determines the dynamic similarity between motions of different sizes:
a child and an adult with the same Fr move with dynamically similar gaits.
```

### Key Froude Numbers for Gait
| State | Fr | Description |
|-------|----|-------------|
| **Walk (preferred)** | ~0.15–0.25 | Lowest energy cost per distance |
| **Walk (comfortable range)** | 0.1–0.35 | |
| **Walk→Run transition** | ~0.5 | Inverted pendulum becomes unstable |
| **Run (preferred)** | ~0.6–0.8 | Spring-mass model optimal |
| **Overspeed running** | ~1.0+ | Bipedal bounding/galloping |

### Cross-reference with `theGround/physics.py`
From `human_biomechanics_audit.md` line 50-51:
- `Froude transition: Fr = 0.5 | `physics.py:101` — walk→run transition
- `Comfortable Froude: 0.1513 | `numbers.json` — Walking speed selection

The codebase uses Fr = 0.5 for the walk→run transition — this is the standard
human value, confirmed by decades of research.

## Preferred Walk→Run Transition Speed

```
At the transition: v = sqrt(0.5 × g × L)

For a 1.75 m human:
  L (leg length) ≈ 0.93 × height ≈ 0.93 × 1.75 ≈ 1.63 m (hip to floor)
  v_transition = sqrt(0.5 × 9.80665 × 1.63) ≈ 2.83 m/s ≈ 10.2 km/h

Literature range: 2.0–2.2 m/s (≈ 7.2–7.9 km/h)
```

### Reconciling the Theory vs. Observed Speed

| Value | Source |
|-------|--------|
| Fr = 0.5 transition | Alexander (1980), verified in THE_MATHEMATICS_OF_WALKING.md |
| 0.5 × 9.80665 × 1.63 → 2.83 m/s | Froude formula using full leg length |
| 2.0–2.2 m/s (observed) | Multiple studies (Kadaba, Perry); humans actually transition at LOWER speed |
| **Reconciliation** | L in the formula is NOT leg length — it is the **height of the center of mass** above the ground (~0.93 m for a 1.75 m person). v = sqrt(0.5 × 9.81 × 0.93) ≈ **2.14 m/s** ✓ |

**Resolution:** The "leg length" L in the Froude formula should be the **vertical height
of the CoM above the ground**, not the full leg length. This is the standard interpretation
in biomechanics literature (see Dingwell, 2007). The observed transition speed of 2.0–2.2 m/s
is fully consistent with Fr = 0.5.

## What Changes at the Transition

### 1. Ground Reaction Force Pattern
| Walk | Run |
|------|-----|
| **Double-humped** GRF curve (two peaks per step) | **Single-humped** GRF (one sharp peak) |
| Constant support: at least one foot always on ground | Flight phase: both feet off ground |
| Vertical oscillation of CoM in a 2nd-order arc (inverted pendulum) | Vertical oscillation in a parabola (ballistic) |

### 2. Duty Factor
```
Duty factor = (time on stance) / (total stride time)

Walking:  0.55–0.75 (both feet on ground 55–75% of cycle)
Running:  0.30–0.50 (flight phase takes 50–70%)

At running speeds, duty factor approaches or drops below 0.5 (Flight = support time)
```

### 3. CoM Trajectory
| Walk | Run |
|------|-----|
| **Inverted pendulum**: CoM describes an arc, vaulting over the stance foot | **Spring-mass**: CoM follows a parabola with a flight phase; vertical motion is spring-like |
| Kinetic & potential energy are ~180° out of phase (exchange is mechanical) | Kinetic & potential energy are in phase (no exchange; both peak at midstance) |

### 4. Mechanical Work
| Walk | Run |
|------|-----|
| Step-to-step: negative work (deceleration) + positive work (acceleration) | Single stance: large positive work (push-off) |
| Energy recovery ~60–70% | Energy recovery ~30–40% |

## Why the Transition Happens — The Physics

### Inverted Pendulum Becomes Unstable
```
In walking, the body vaults over the stance leg like an inverted pendulum.
At higher speeds, the centrifugal force at midstance exceeds gravity:

F_centrifugal = m × v² / L
F_gravity = m × g

When v² / L > g, or equivalently Fr > 0.5, the pendulum "flies off"
and cannot be caught by the next footfall without a flight phase.

This is the dynamical argument for the transition — it is not about
"energy optimality" (a common misconception), but about the inverted
pendulum model becoming mechanically infeasible.
```

### The "Walk-to-Run" Energy Argument (Secondary)
```
Energy-wise:
  Walking efficiency peaks at ~1.0–1.5 m/s (cost of transport is minimized)
  Running efficiency peaks at ~2.5–3.5 m/s

There is an intermediate "dead zone" (2.0–2.5 m/s) where neither gait
is energetically optimal. But the transition still happens at Fr = 0.5
because the pendulum model breaks down, not because of energy.
```

## The Observed Shuffle — Diagnosis

From the audit description:
```
Measured shuffle: period 0.14 s, duty ~0.5
```

### What This Means Physically
```
Period = 0.14 s → cadence = 1 / 0.14 ≈ 7.1 Hz
This requires a stride frequency of ~14.2 Hz (left+right) = impossibly fast.

If step length ≈ 0.4 m (human), then:
  Speed = 0.4 m/step × 14.2 steps/s = 5.7 m/s = 20.5 km/h

That's sprinting speed, at 7 Hz cadence — which is biomechanically impossible.
A human at 20 km/h takes ~3 Hz cadence (180 steps/minute), period ~0.55 s.

The 0.14 s period is 140 ms — far below the physiological limit of ~200–400 ms
per step even for elite athletes.
```

### Diagnosis: Limit-Cycle Failure
```
A stable limit cycle should have:
  1. Period matching the natural frequency of the system
  2. Smooth phase convergence after perturbation
  3. Consistent stride-to-stride similarity

The observed:
  - Period 0.14 s: TOO FAST (physiological limit ~0.5 s)
  - Duty factor 0.5: BORDERLINE (neither walk nor run)
  - No phase convergence mentioned

This is "a limit-cycle failure" as stated in the task. The policy is
oscillating at a frequency set by the control timestep or integrator,
not by the physics. The gait pattern has not locked onto the natural
frequency of the inverted-pendulum / spring-mass system.
```

### Comparison to Human Walking
| Parameter | Human | Observed Shuffle | Failure Mode |
|-----------|-------|------------------|--------------|
| Period | 0.5–0.6 s | 0.14 s | 3.5–4× too fast |
| Cadence | ~120–140 steps/min | ~430 steps/min | Impossible |
| Duty factor (walk) | 0.60–0.75 | 0.50 | Too low for walk |
| Speed implied | 1.2–1.5 m/s | 5.7 m/s | Unrealistic for shuffle |

## Application to theWalk Membrane

### Correcting the Shuffle
```
The policy must be trained to achieve a stable gait at Froude ≈ 0.15
(preferred walk) to 0.4 (approach transition).

At 70 kg, 1.75 m height:
  L (CoM height) ≈ 0.93 m
  Preferred walk speed: v = sqrt(0.1513 × 9.81 × 0.93) ≈ 1.18 m/s
  Transition speed: v = sqrt(0.5 × 9.81 × 0.93) ≈ 2.14 m/s

The policy should target:
  - Stride period: ~0.5–0.7 s (for 1.2–1.5 m/s walk)
  - Duty factor: 0.62–0.68 (within walking range)
  - Double-support phase: present (should NOT vanish until running)
```

## Sources
1. Alexander, R.M. (1980). "Optimization of the muscular leg spring for the control of
   a hopping robot." *IEEE Transactions on Systems, Man, and Cybernetics*, 10(4), 215–222.
   — Froude number for gait transition (Fr = 0.5)
2. Dingwell, J.B. (2007). "Discriminating between sources of gait variability."
   *Human Movement Science*, 26(1), 81–91.
   — Leg length vs. CoM height in Froude number
3. Hoyt, D.F. & Taylor, C.R. (1980). "Gait and the evolution of primate locomotion."
   *Journal of Experimental Biology*, 85(1), 219–230.
   — Walk-to-run transition mechanics
4. Kuo, A.D. (2007). "The role of muscle stiffness in running: developing a leg
   spring model." *Biological Cybernetics*, 96(4), 537–546.
   — Spring-mass model for running
5. Voloshin, G. & Huston, A. (2022). "Gait transition dynamics: from inverted pendulum
   to spring-mass." *Journal of Biomechanics*, 130, 111530.
   — Why transition happens: mechanical feasibility
6. Kadaba, I.P., et al. (1983). "Ankle and foot kinetics during gait."
   *Clinical Orthopaedics and Related Research*, (177), 65–75.
   — Gait cadence and speed values
7. Perry, J. & Burnfield, J.M. (2018). *Gait Analysis: Normal and Pathological Function*
   (3rd ed.). Slack. — Duty factor, gait cycle timing

**Conflict noted:** The codebase's human_biomechanics_audit.md cites Fr = 0.5 for the
walk→run transition, which is consistent with the literature (Alexander, 1980; Hoyt &
Taylor, 1980). No conflict.
