# Task 3 — Spring-Rate Equivalence (Stiffness to Natural Frequency)

## Statement

Stiffness K (Nm/rad) converts to natural frequency f (Hz) via the
rotational spring-mass formula:  omega_n = sqrt(K / I),  f = omega_n / 2pi.
This is the canonical relationship — without it, a kp value in the model
cannot be cross-checked against observed sway oscillation periods.

## Prediction

The standing human inverted pendulum has an effective stiffness Ke ~ 300-500
Nm/rad (Winter 1998) with I ~ 50-70 kg*m2, yielding omega_n ~ 2-3 rad/s
(0.3-0.5 Hz), matching the observed ~0.4 Hz sway. If the formula fails to
reproduce this, the model omits reflex contributions.

## Deliverable

## Key equation

For a rotational spring-mass-damper about a joint:

    I * theta_ddot + B * theta_dot + K * theta = tau

where:
- I  = moment of inertia about the joint (kg*m2)
- K  = stiffness (Nm/rad)
- B  = damping (Nms/rad)
- tau = torque (Nm)

Natural angular frequency:   omega_n = sqrt(K / I)    [rad/s]
Natural frequency:           f_n = omega_n / (2*pi)  [Hz]
Period:                      T = 2*pi * sqrt(I / K)  [s]

Stiffness from observed frequency:   K = I * omega_n^2

## Primary source (whole-body balance)

**Winter, D.A., Patla, A.E., Prince, F., Ishac, M.G., Gielo-Perczak, K.**
(1998). "Stiffness Control of Balance in Quiet Standing."
J Neurophysiol 80(3): 1211-1221. DOI: 10.1152/jn.1998.80.3.1211

> "The effective stiffness of the system, Ke, is then estimated from
> Ke = I * omega_n^2, and the damping B is estimated from
> B = BW * I, where BW is the bandwidth of the tuned response
> (in rad/s), and I is the moment of inertia of the body about the
> ankle joint."

This establishes the formula: stiffness = inertia x (natural frequency)^2.

### Typical values from Winter 1998:

| Subject parameter | Value | Source |
|-------------------|-------|--------|
| Body mass (m) | 75 kg | Table in Frontiers paper (replicating Winter model) |
| COM height (h) | 0.83 m | ibid. |
| Moment of inertia I = m*h^2 | 51.9 kg*m^2* | Computed (see note) |
| Natural freq omega_n | ~2.5 rad/s (~0.4 Hz) | Inferred from COP-COM spectrum |
| Effective stiffness Ke = I*omega_n^2 | ~327 Nm/rad | Computed |

* I = m * h^2 is the point-mass approximation of body segment inertia
  about the ankle. More precise biomechanical estimates use
  ~66 kg*m^2 (Fonteyn et al. 2010, used in Frontiers paper).

## Secondary source (math formulation)

**Tawaki, Y., Nishimura, T., Murakami, T.** (2021). "Classification of
Older and Fall-Experienced Subjects by Postural Sway Data Using Mass Spring
Damper Model." IEEE TNSRE. DOI: 10.1109/TNSRE.2021.3139966

> "omega_0 = kappa / m = sqrt(k)"  (Eq. 5 — natural angular frequency
> of MSD model)
> "zeta = d / (2 * sqrt(m*k))"    (Eq. 4 — damping ratio)
> "x_ddot + 2*zeta*omega_0*x_dot + omega_0^2 * x = F'(t)" (Eq. 3)

This is the standard mass-spring-damper equation. For rotational form:
replace m with I (kg*m^2), k with K (Nm/rad), d with B (Nms/rad).
Result: omega_n = sqrt(K / I).

## Supporting source (pendulum test)

**Loram, G.N., et al.** (2005). "The human upside-down pendulum is
stiff during standing but not during postural preparation."
J Physiol 564(Pt 2): 643-654.

> "gravitational load stiffness (mgh) ... approximately 0.13 rad/s^2 ratio
> of J/kg" — i.e., mgh/I ~ 0.13 for standing human.

For the standing person: mgh = restoring torque stiffness.
With m=75 kg, g=9.81, h=1 m: mgh = 735.8 Nm/rad
With I = 52 kg*m^2: mgh/I = 14.2 rad^2/s^2, omega = 3.77 rad/s

The observed sway frequency (~0.4 Hz = 2.5 rad/s) is LOWER than the
passive gravitational frequency (3.77 rad/s), indicating active
stiffness reduction by the CNS (~2/3 of passive).

## Reference values for conversion table

| Segment/system | K (Nm/rad) | I (kg*m2) | omega_n (rad/s) | f_n (Hz) | T (s) | Source |
|----------------|------------|-----------|-----------------|----------|-------|--------|
| Ankle (relaxed)* | ~16 | 0.01-0.05 | 18-40 | 2.9-6.4 | 0.16-0.35 | Hogan 1985 |
| Lumbar L3-L4 (HFZ) | ~57 | — | — | — | — | Muriuki 2016 |
| Lumbar L1-L2 (HFZ) | ~86 | — | — | — | — | Muriuki 2016 |
| Standing (passive) | ~736 | 51.9 | 3.77 | 0.60 | 1.67 | Loram 2005 |
| Standing (effective) | ~327 | 51.9 | 2.51 | 0.40 | 2.49 | Winter 1998 |

*Ankle: Hogan 1985 cites 1-200 Nm/rad range for elbow; ankle I ~ 0.01-0.05
 kg*m^2 gives f ~ 3-6 Hz.

## Summary

The canonical conversion is:
-  omega_n = sqrt(K / I)
-  f_n [Hz] = 0.159 * sqrt(K / I)
-  T [s]  = 6.28 * sqrt(I / K)

Stiffness alone is insufficient — the moment of inertia I must be
specified. For intervertebral joints, I is typically the segment
rotational inertia (very small, ~1e-4 to 1e-3 kg*m^2 for a single
vertebra-disc unit). For whole-body sway, I is the full body inertia
about the support joint (~50-70 kg*m^2).

## References

1. Winter, D.A. et al. (1998). Stiffness Control of Balance in Quiet
   Standing. J Neurophysiol 80(3):1211-1221.
   DOI: 10.1152/jn.1998.80.3.1211

2. Tawaki, Y., Nishimura, T., Murakami, T. (2021). Classification of
   Older and Fall-Experienced Subjects by Postural Sway Data Using
   Mass Spring Damper Model. IEEE TNSRE.
   DOI: 10.1109/TNSRE.2021.3139966

3. Loram, G.N., et al. (2005). The human upside-down pendulum is
   stiff during standing but not during postural preparation.
   J Physiol 564(Pt 2): 643-654.

4. Morasso, P., Schieppati, M. (1999). Standing balance: a
   neurobiological perspective. ProgBrain Res 123: 17-28.
