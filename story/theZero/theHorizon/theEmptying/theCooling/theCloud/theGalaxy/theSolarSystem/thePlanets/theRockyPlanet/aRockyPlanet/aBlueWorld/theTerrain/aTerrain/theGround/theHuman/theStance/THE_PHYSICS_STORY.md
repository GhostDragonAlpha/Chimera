# THE PHYSICS STORY OF THE HUMAN MEMBRANE — the chain, and where it stops

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. If you are choosing a number, you broke the chain and substituted taste for a law.
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../../docs/THE_LAW.md)**
<!-- CHIMERA-LAW -->

**In plain words —** A body stands because a load finds an unbroken path from the mass to the
ground. This is that path, joint by joint, with what each one is known to carry — and an honest
mark where the body we have stops existing.

---

## THE INSTRUCTION, AND WHY IT CANNOT BE FOLLOWED AS WRITTEN

> *"The foot connects to the ankle… the pelvis connects to the spine, the spine to the ribs, the
> ribs to the shoulders, the shoulders to the arms, the arms to the hands, the hands to the world.
> Write them all. Derive every variable. Calculate every torque, every moment arm, every
> activation."*

The chain is right, and **two of its eleven links are missing — not six.**

> **CORRECTION, same day.** The first version of this file said *"There is no spine. No ribs. No
> shoulders. No arms. No hands."* **That was false, and it was false because of how I looked.**
> I walked the kinematic tree DOWNWARD FROM THE PELVIS and reported what I found. The sacrum is a
> **SIBLING** of the pelvis — both hang off `Full Body` — so the entire upper body was structurally
> invisible to that traversal. It reported "NONE" where the honest answer was "I did not look there."
>
> The mass said so and I did not listen: the chain I printed summed to ~35 kg of an 82 kg body.
> **A 47 kg discrepancy is not a rounding error; it is a missing half.**

**WHAT THE BODY ACTUALLY HAS**, all 26 bodies, read with their parents rather than walked from one:

    Full Body (massless root)
      ├─ sacrum 7.486
      │    └─ lumbar5 1.824 → lumbar4 1.799 → lumbar3 1.670 → lumbar2 1.689 → lumbar1 1.677
      │         └─ torso 18.619  →  neck 1.403  →  head 7.555
      │         └─ Abdomen 0.010
      └─ pelvis 10.960
           ├─ femur_r 8.400 → tibia_r 3.800 → talus_r 0.021 → calcn_r 1.140 → toes_r 0.285
           └─ femur_l 8.400 → tibia_l 3.800 → talus_l 0.021 → calcn_l 1.140 → toes_l 0.285
                                                              (+ patella_r/l 0.028 each)

**There IS a spine — five lumbar segments. There IS a torso, a neck and a head.** 47 kg of upper
body that the first version of this file declared absent.

**WHAT IS GENUINELY MISSING: ARMS AND HANDS.** No humerus, radius, ulna or hand anywhere in the
26. That is the real boundary, and it is five links narrower than the one I claimed.

**AND ONE STRUCTURAL FACT THAT NEEDS CHECKING BEFORE ANY LOAD PATH IS DRAWN THROUGH IT:** in this
tree the sacrum and the pelvis are SIBLINGS, not parent and child. Physically the spine's weight
must reach the legs through the sacroiliac joint; in the model's parent tree it does not descend
that way. Whether that is a weld, a constraint, or a genuine break is **not yet measured**, and
the load path from torso to ground cannot be drawn until it is.

---

## THE CHAIN THAT EXISTS

    GROUND → FOOT → ANKLE → KNEE → HIP → PELVIS ⟂ (the body ends)

| link | port | actuators | status |
|---|---|---|---|
| GROUND → FOOT | contact | — (the ground is not actuated) | **PROVEN at rest, +0.7%.** Two mechanisms — contact solver and integrator — agreeing to 7 parts in 1000. Carrying a heap, not an upright body |
| FOOT → ANKLE | the distal port | **22 muscles**, by moment arm | OPEN. 0.66 s of 5 |
| ANKLE → KNEE | *(same 22 muscles)* | — | **NOT A SEPARATE PORT.** Every muscle crossing the ankle also crosses subtalar and MTP: one tendon, three joint rows |
| KNEE → HIP | the knee port | **26 muscles** | OPEN. 1.20 s of 5 at parity |
| HIP → PELVIS | the hip port | **50 muscles** | OPEN. **1.60 s of 5 = 32%**, worst-of-4 |

**Three ports, not five, and not eleven.** The count came from the model's own `actuator_moment`,
never from a list of joint names — which is how the ankle/foot identity surfaced at all.

---

## WHAT EACH PORT IS KNOWN TO REQUIRE

Every number below is read or derived, and the ones that are neither say so.

| quantity | value | where from |
|---|---|---|
| gravity | 7.076122 m/s² | `theHuman`, down an unbroken chain from `aBlueWorld`'s mass |
| simulated body mass | 82.041 kg | summed from the model's own body tree |
| weight | 580.5 N | mass × g |
| pelvis target height | 0.920147 m | `hip_to_ankle + ankle_height`, **and it closes on `leg_length_m` to +0.0000%** |
| base of support | ±0.102 lat × ±0.1355 fore | `theStance`, feet-together |
| CoM at start | 4.8 mm fore, 40.4 mm lateral **inside** the base | measured |
| time to fall | 0.4066 s | `theStance`, the deadline every requirement is measured against |
| muscle response | 0.1257 s | `2π√(τ_act·τ_deact)` from the model's `actuator_dynprm` — **3.2× faster than the fall** |
| control interval | 20 ms | 20.3 corrections before the body is down |
| hold band | **2.3°** | measured human quiet-stance sway, 0.025–0.041 rad. *Was 8.6°, a round number in radians, never checked — 3.7–6× too loose* |
| hold duration bar | 5 s | **ASSERTED, NOT DERIVED.** The one number here with no source |

---

## THE THEORY THIS CHAIN IS A TEST OF

    R1  A BASE          CoM inside the polygon of support          MET
    R2  A LOAD PATH     every joint carries without buckling       OPEN — 32%
    R3  A FAST LOOP     the controller commands faster than 0.4066 s   MET
    R4  A FAST PLANT    the muscle responds faster than 0.4066 s   MET
    R4b THE PORT LOOP   the port is commanded with FEEDBACK        MET
    R5  ???                                                        UNKNOWN

**R5 cannot be named until R2 closes.** A row invented before its precondition is a guess wearing
a requirement's clothes — and the one named under exactly that pressure (R4, *"the plant is too
slow"*) was wrong, and was reversed two commits later by reading a number already in the model.

---

## AND THE SCOPE BOUNDARY IS A REAL RESULT, NOT AN EXCUSE

The chain above the pelvis matters for standing — arms counter-rotate, the trunk carries most of
the mass, the head stabilises the gaze. **None of it is in this body**, so:

- Any R5 that turns out to be *"standing needs the trunk"* is **unreachable with myoBody as
  loaded**. It would need a different model, and that is a decision, not a training run.
- Conversely: if these three leg ports ever close R2 and the body still falls, **the missing trunk
  is the first suspect**, and it will have been predicted here rather than discovered by surprise.

That is what a scope boundary written down in advance buys. The alternative is an agent spending a
week training a shoulder port on a body with no shoulder.
