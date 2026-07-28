# THE MATHEMATICS OF WALKING — derive it, prove it, THEN train

> **The operator's correction (2026-07-28), and it is the method:** *"You have to know it works because
> it's proven mathematically first before you start training."* Every membrane — hip, knee, foot, hand —
> has a mathematical principle. Trace ALL the variables and show the equations close, or training is
> guess-and-check with a two-hour feedback loop. This is the project's own doctrine (`PROGRAM the rules,
> TRAIN the numbers`): I had been trying to *train the rules*.
>
> Every constant below is **measured from `myobody.xml` itself**, not assumed.

## 0. The measured body

| quantity | symbol | value |
|---|---|---|
| total mass | M | **82.04 kg** |
| CoM height, standing | H | **0.965 m** |
| leg length (hip→foot) | L | **0.845 m** |
| leg mass | m_leg | **13.65 kg** (17% of M) |
| hip→leg-CoM distance | d | **0.374 m** |
| leg inertia about hip | I | **2.879 kg·m²** |
| gravity | g | 9.81 m/s² |

*Validation:* leg mass at 17% of body mass matches the human 16–18%. The model is anthropometrically sane.

## 1. THE MEMBRANE HIERARCHY, and the principle inside each

Walking is not one equation; it is **one principle per membrane**, coupled.

### 1.1 Whole body — angular momentum
The body's total angular momentum about its CoM stays **near zero** through the gait cycle. Arm swing
is not decoration: it **cancels** the angular momentum the swinging legs generate.
> **H_total ≈ 0** — a constraint, and the mathematical reason arms counter-rotate with legs.

### 1.2 Stance leg — INVERTED pendulum
The body vaults up and over the planted foot.
> **ω₀ = √(g/H) = 3.188 rad/s** (time constant 1/ω₀ = **0.314 s**)
> **XcoM = com + v/ω₀** (capture point — where the foot must land)
Stability: the foot is placed such that the XcoM stays within the base of support.

### 1.3 Swing leg — COMPOUND pendulum (this sets the RHYTHM)
Released at toe-off, carried by gravity — ballistic walking (Mochon & McMahon; McGeer's passive walkers
walk down a slope with **no motors at all**).
> **T = 2π√(I/(m_leg · g · d)) = 1.506 s**  →  **step time T/2 = 0.753 s**  →  **cadence 80 steps/min**

*Honest check:* human cadence is 100–120/min, so we predict **slower** than a human. That is a **known
real result**: humans do not walk fully ballistically — the preferred cadence sits *above* the free
pendular frequency, i.e. the swing is partly driven. The pure-pendulum number is the **floor**, and it is
the natural frequency a CPG should be seeded with.

### 1.4 Foot / contact — the constraint membrane
> **friction cone:** |F_tangential| ≤ μ·F_normal (or the foot slips)
> **CoP inside the contact polygon** (else the foot rolls)
> **support ≥ 1 foot at all times** — a walk is *never* airborne (this is what our gait witness measured at 15% and convicted)

### 1.5 Joint — the gear ratio
> **τ = r(q) · F_muscle**, where r(q) is the measured moment arm (already in `body.py`, MEASURED for knee/ankle/hip/elbow)

### 1.6 Muscle — Hill, and the gap
> **F = a · F_max · f_L(L) · f_V(v)**
> **MISSING: muscle is a fluid.** Muscle is ~75% water and incompressible, so contraction **must** bulge it
> at constant volume, generating intramuscular pressure (hundreds of mmHg). That pressure stiffens the
> muscle **hydraulically** (a hydrostat, not a 1-D string), **shifts the muscle's path** so moment arms move
> dynamically with activation, and transmits force **laterally** through fascia. A Hill element has length,
> velocity and force — no volume, no pressure, no thickness. *(Operator's observation, 2026-07-28: "muscle
> creates fluid pressure, which is why it is dynamic." Real gap; a candidate for the typed-brick matter
> model. NOT the current bottleneck — our failure is control, not muscle fidelity.)*

## 2. THE UNIFYING LAW — the Froude number

The dimensionless group that makes gaits comparable **across gravity and body size**:
> **Fr = v² / (g · L)**

Two bodies at the same Fr walk **dynamically similar** gaits. Human preferred walk ≈ **Fr 0.25**;
**walk→run transition at Fr ≈ 0.5**.

**This is the mathematical bridge between membranes, and it answers the space game directly:**

| world | g | speed at Fr 0.25 (walk) | speed at Fr 0.5 (must run) | swing step time |
|---|---|---|---|---|
| Earth | 9.81 | **1.44 m/s** | 2.04 m/s | 0.75 s |
| Mars | 3.71 | 0.89 m/s | 1.25 m/s | 1.22 s |
| Moon | 1.62 | **0.59 m/s** | **0.83 m/s** | 1.85 s |

**Validation — this reproduces Apollo.** On the Moon the walk→run transition falls to **0.83 m/s**, a
slow jog on Earth. Astronauts exceeded it almost immediately, which is *why they bunny-hopped instead of
walking.* The mathematics predicts a famous observed fact it was never fitted to.

## 3. DOES IT CLOSE? — the derived gait, with no training

Given the body's own constants, the gait is **determined**, not free:
- cadence ← swing pendulum (**0.753 s/step**)
- speed ← chosen Froude number
- **step length = v × step_time** (not a free parameter once speed and cadence are fixed)
- foot placement ← capture point **XcoM = com + v/ω₀**
- contact schedule ← always ≥1 foot down, left/right in antiphase

At **Fr 0.25**: v = 1.44 m/s, step time 0.753 s → **step length 1.08 m** → hip sweep ±0.69 rad
(within the measured hip range −0.52…+2.09 ✓ — the geometry permits it).

*Our current `TARGET_SPEED = 0.8 m/s` corresponds to **Fr 0.077** — a deliberately slow walk. It is
close to the pure-ballistic prediction (0.77 m/s), so it is physically reasonable, but it is NOT the
human-like gait; that is Fr 0.25 ≈ 1.44 m/s.*

## 4. WHAT IS STILL OPEN — variables not yet traced (honest)

1. **Lateral / frontal plane.** Everything above is *sagittal* (forward). Balance sideways has its own
   membrane: step **width**, lateral capture point, and Hof's rule that the foot lands **outward** of the
   XcoM. Untouched.
2. **Angular momentum regulation** (§1.1) — the arm-swing law. Measured to be near zero in humans; we
   neither measure nor reward it.
3. **Double-support fraction** — the overlap where both feet are down (~20% of a human cycle). Sets duty
   factor ≈ 0.6, which our witness measures but nothing targets.
4. **Energetics** — pendular recovery ~65% at optimum (`docs/WALKING_MECHANICS.md`); cost of transport
   minimum defines the *preferred* speed.
5. **Knee/ankle roles** — knee flexion for ground clearance in swing; ankle push-off supplying most of the
   propulsive work. Not yet expressed as constraints.
6. **Muscle fluid pressure** (§1.6).
7. **The hand** and every distal membrane — not started (the operator's point: each decomposes further).

## 5. WHAT THIS CHANGES ABOUT TRAINING

Before this document, the rewards encoded *guesses* (a hand-picked target speed, an invented alive
threshold). Now the targets are **derived from the body's own measured constants**:

- target speed is a **Froude number**, not a m/s guess — and it scales to any gravity automatically
- the CPG's frequency is **1/0.753 s**, the measured swing pendulum — not a tuned knob
- the alive threshold follows from H = 0.965 m and the ~4 cm gait dip
- foot placement follows ω₀ = 3.188 rad/s

**Program these; train only what remains free** (the muscle coordination that satisfies them).

## Sources
Ballistic walking: Mochon & McMahon 1980 · Passive dynamic walking: McGeer 1990 ·
Capture point / XcoM: [Hof 2008](https://pubmed.ncbi.nlm.nih.gov/17935808/) ·
Pendular recovery: [Cavagna](https://pubmed.ncbi.nlm.nih.gov/1011078/) ·
Froude scaling & the walk-run transition: Alexander's dynamic similarity ·
Reduced-gravity walking: [J Appl Physiol 1999](https://journals.physiology.org/doi/full/10.1152/jappl.1999.86.1.383)
