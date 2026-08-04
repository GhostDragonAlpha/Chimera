# Task 2 — Control-Theory Stiffness References

## Statement

Stiffness (K, in Nm/rad) is the static component of mechanical impedance —
the ratio of force/torque to displacement/angle. The nervous system modulates
joint stiffness via antagonist coactivation and reflex gain, treated the CNS
as controlling impedance rather than just position.

## Prediction

References that treat stiffness as an independently controllable parameter
(rather than a fixed tissue property) will report stiffness scaling by muscle
coactivation over a range of at least 3x, consistent with the
"co-contraction increases apparent joint stiffness by a factor 4 to 7"
finding [Perreault 2001].

## Citation list

### Foundational: Impedance Control (robotics)

1. **Hogan, N.** (1985). Impedance Control: An Approach to Manipulation.
   Parts I, II, and III. J Dyn Syst Meas Control 107:1-24.
   - DOI: 10.1115/1.3140708 (Part I), 10.1115/1.3140713 (Part II),
         10.1115/1.3140714 (Part III)
   - Part I: defines impedance as a network of physical elements; lowest-order
     term is stiffness (force/displacement).
   - Part II: feedback algorithm for Cartesian impedance; eliminates inverse
     kinematics; notes "stiffness about the human elbow can vary from about
     1 Nm/rad to more than 200 Nm/rad."
   - Part III: optimization-based selection of impedance for task performance.

2. **Salisbury, J.K.** (1980). Active stiffness control of a manipulator in
   Cartesian coordinates. Proc 19th IEEE Conf Decision and Control,
   New York, 95-100.
   - DOI: 10.1109/CDC.1980.272026
   - Introduces stiffness control as a subset of impedance control.

3. **Hogan, N.** (1984). Adaptive control of mechanical impedance by
   coactivation of antagonist muscles. IEEE Trans Autom Control 29(8):681-690.
   - DOI: 10.1109/TAC.1984.1103644
   - KEY EQUATION: "the torques due to the opposing muscles subtract from
     one another, but the impedances due to the opposing muscles add.
     The net torque about a joint is determined by the difference between
     the activities of the agonist and antagonist groups, while the net
     angular stiffness is determined by the sum." (p. 682)
   - Predicts antagonist coactivation as a mechanism for stiffness modulation.

4. **Hogan, N.** (1980). Mechanical impedance control in assistive devices
   and manipulators. Proc Joint Automatic Controls Conference 1:361-371.

5. **Hogan, N.** (1982). Programmable impedance control of industrial
   manipulators. Proc CAD/CAM Mechanical Engineering Conf, MIT.

### Equilibrium-Point / Lambda Model

6. **Bizzi, E., Hogan, N., Mussa-Ivaldi, F.A., Giszter, S.F.** (1992).
   Does the nervous system use equilibrium-point control to guide single
   and multiple joint movements? Behav Brain Sci 15(4):575-582.
   - DOI: 10.1017/S0140525X00072538
   - "Posture may be controlled through the choice of muscle
     length-tension curve that set agonist-antagonist torque-angle curves
     determining an equilibrium position for the limb and the stiffness
     about the joints."

7. **Feldman, A.G.** (1986). Once more on the equilibrium-point hypothesis
   (lambda model) for motor control. J Motor Behavior 18(1):17-54.
   - DOI: 10.1080/00222895.1986.10735369
   - Defines equilibrium point via gamma-static threshold (lambda) and
     length-force invariant characteristic of muscle.

8. **Mussa-Ivaldi, F.A., Hogan, N., Bizzi, E.** (1985). Neural, mechanical,
   and geometric factors subserving arm posture in humans. J Neurosci
   5(10):2732-2743.
   - DOI: 10.1523/jneurosci.05-10-02732.1985
   - Shows arm stiffness ellipsoid rotates with target direction.

9. **Flash, T., Hogan, N.** (1985). The coordination of arm movements:
   an experimentally confirmed mathematical model. J Neurosci 5(7):1688-1703.
   - DOI: 10.1523/jneurosci.05-07-01688.1985

10. **Hogan, N.** (1984). An organizing principle for a class of voluntary
    movements. J Neurosci 4(11):2745-2754.
    - DOI: 10.1523/jneurosci.04-11-02745.1984

### Joint Stiffness Quantification

11. **Perreault, E.J., Kirsch, R.F., Crago, P.E.** (2001). Effects of voluntary
    force generation on the elastic components of endpoint stiffness.
    Exp Brain Res 141:312-323.
    - DOI: 10.1007/s00221-001-0028-3
    - Co-contraction increases endpoint stiffness by factor 4-7.

12. **Humphrey, D.R., Reed, D.J.** (1983). Separate cortical systems for
    control of joint movement and joint stiffness: reciprocal activation and
    coactivation of antagonist muscles.

13. **Crago, P.E., Hansen, N.L., Abbas, J.J.** (1979). Models for control of
    the myoelectric activation of shoulder and elbow muscles. IEEE Trans
    Biomed Eng 26:264-272.
    - Introduces 3-component model: K (stiffness), B (viscosity), M (mass).
    - Conventionally used: elbow K ~ 16 Nm/rad, B ~ 2.4 Nms/rad.

### Limb Impedance Modulation (behavioral)

14. **Damm, L., McIntyre, J.** (2008). Physiological basis of limb-impedance
    modulation during free and constrained movements. J Neurophysiol
    100:1105-1115.
    - DOI: 10.1152/jn.90471.2008
    - "Stiffness can be regulated by two mechanisms: coactivation of
      antagonistic muscles and modulation of reflex gains."

15. **Krutky, M.A., Trumbower, R.D., Perreault, E.J.** (2013). Influence of
    environmental stability on the regulation of end-point impedance
    during the maintenance of arm posture. J Neurophysiol 109:1045-1054.
    - DOI: 10.1152/jn.01094.2007

16. **Lee, H., Ho, P., Rastgaar, M.A.J., Krebs, H.I., Hogan, N.** (2011).
    Multivariable static ankle mechanical impedance with relaxed muscles.
    J Biomech 44(10):1901-1908.
    - DOI: 10.1016/j.jbiomech.2011.04.028
    - Characterizes ankle stiffness in 2 DOFs (dorsiflexion/plantarflexion,
      inversion/eversion).

17. **Lee, H., Ho, P., Rastgaar, M.A.J., Krebs, H.I., Hogan, N.** (2013).
    Multivariable static ankle mechanical impedance with active muscles.
    IEEE TNSRE.
    - DOI: 10.1109/TNSRE.2013.2262689
    - Shows ankle stiffness increases with muscle activation, more in
      sagittal than frontal plane.

### Ankle Impedance (dynamic)

18. **Valero, J.S., et al.** (2015). Mechanical impedance and its relations to
    motor control, limb dynamics, and motion biomechanics.
    J Med Biol Eng 35:78-90.
    - DOI: 10.1007/s40846-015-0016-9
    - Review: stiffness is the ratio of force change to displacement change;
      strong relatedness to muscle activation.

19. **Hogan, N.** (1990). Mechanical impedance of single- and
    multi-articular systems. In: Multiple Muscle Systems, pp. 149-164.
    - DOI: 10.1007/978-1-4613-9030-5_9

### Passive Dynamics / Spring-Based Control

20. **Pratt, G.W.** (1995). Low-resolution compliance control for robot
    manipulators. IEEE Trans Robotics Automation 11(2):215-229.
    - DOI: 10.1109/70.347249
    - Shows compliance/stiffness can reduce control complexity.

### Key numerical reference values

| Parameter | Value | Source |
|-----------|-------|--------|
| Elbow joint stiffness (conventional) | K ~ 16 Nm/rad | Crago et al. 1979 [#13] |
| Elbow viscosity (conventional) | B ~ 2.4 Nms/rad | Crago et al. 1979 [#13] |
| Elbow stiffness range (Hogan) | 1-200 Nm/rad | Hogan 1985 Part II [#1] |
| Stiffness increase from co-contraction | 4-7x | Perreault 2001 [#11] |
| Lumbar spine stiffness (L1-L5, flexion) | 51.6 Nm/rad (pooled) | Schultz 1979 (see Task 1) |
| Lumbar spine stiffness (lateral bending) | 63.0 Nm/rad (pooled) | Schultz 1979 (see Task 1) |

## Canonical equation

The linearized joint-space impedance model used across these references:

    tau = K * (theta_ref - theta) + B * (theta_dot_ref - theta_dot)

Where:
- K = stiffness (Nm/rad) — the parameter of interest
- B = viscosity (Nms/rad) — damping
- tau = torque (Nm)
- theta = joint angle (rad)
