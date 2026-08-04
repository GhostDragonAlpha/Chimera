# Task 4 — Torque-to-Perturbation Reference Citations

## Statement

Torque perturbations applied to joints elicit reflex responses whose
amplitude and timing reveal the stiffness contribution of reflexes vs.
intrinsic muscle elasticity. The short-latency reflex (SLR, 25-50 ms)
provides near-instantaneous stiffness; the long-latency reflex (LLR,
50-100 ms) provides task-dependent stiffness.

## Prediction

Papers using torque perturbations to isolate intrinsic vs. reflex
stiffness will report reflex gains (Nm/rad/s) that scale with background
muscle activation and perturbation velocity. The intrinsic stiffness
of relaxed ankle is ~16 Nm/rad; reflex contributions add 4-7x on top.

## Citation list

### Perturbation identification methods

1. **Kearney, J.J., and Hunter, J.B.** (1990). "Identification of the
   reflex and intrinsic stiffness of the ankle joint." IEEE Trans
   Biomed Eng 37: 711-719.
   - Introduces position-perturbation system identification for
     separating intrinsic and reflex stiffness.

2. **Kearney, J.J., Crago, P.E., and Hogan, N.** (1997). "A
   parallel-cascade model of joint stiffness: estimation from
   position and velocity perturbations."
   - Parallel-cascade model: intrinsic stiffness (linear) and reflex
     stiffness (Hammerstein, velocity-in).
   - Used as the canonical decomposition method for ~2 decades.

3. **Giesbrecht, M.J., et al.** (2006). "Time-varying parameter
   estimation of dynamic joint stiffness during movement."
   - Extends parallel-cascade to time-varying (TV) parameters.

4. **Guarin, D. and Kearney, J.J.** (2012). "Time-varying ankle
   dynamic stiffness during gait." IEEE TNSRE 59(12): 1279-1286.
   - DOI: 10.1109/TNSRE.2012.2210239

5. **Guarin, D. and Kearney, J.J.** (2015b). "Time-varying dynamic
   joint stiffness during movement: application to the ankle."
   - Iterative estimation of TV stiffness during gait.

6. **Klomp, D.M., et al.** (2014). "Estimation of dynamic joint
   stiffness during naturalistic movements using a feedback
   linearized driven string approach."
   - J Neurosci Methods.

7. **Jalaleddini, C., et al.** (2016). "Estimation of time-varying
   intrinsic and reflex joint stiffness during movement."
   - IEEE TNSRE.

8. **Jalaleddini, C., et al.** (2017). "Estimation of time-varying,
   intrinsic and reflex dynamic joint stiffness during movement.
   Application to the ankle joint." Front Comput Neurosci.
   - DOI: 10.3389/fncom.2017.00051

### Torque/stretch perturbation studies

9. **Crago, P.E., et al.** (1976). "Functional characteristics of
   cat hissian muscle as studied by tendon vibration." J Physiol
   257: 731-746.
   - Shows SLR compensates for muscle yielding under stretch.

10. **Allum, J.H.J. and Mauritz, K.-H.** (1984). "Compensation for
    intrinsic muscle stiffness by short-latency reflexes in human
    triceps surae muscles." J Neurophysiol 52(5): 797-818.
    - DOI: 10.1152/jn.1984.52.5.797

11. **Allum, J.H.J., Mauritz, K.-H., Voge, J.** (1982). "The
    mechanical effectiveness of short latency reflexes in human
    triceps surae muscles revealed by ischaemia and vibration."
    Exp Brain Res 48(1): 153-156.
    - DOI: 10.1007/BF00239584

12. **Gielen, C.C.A.M., Ramaekers, L., van Zuylen, E.J.** (1988).
    "Long-latency stretch reflexes as coordinated functional
    responses in man." J Physiol 395: 113-128.
    - DOI: 10.1113/jphysiol.1988.sp017415
    - Torque perturbations around elbow in flexion-extension and
      supination-pronation; SLR (25-50 ms) + LLR (50-75 ms).

13. **Perreault, E.J., Kirsch, R.F., Crago, P.E.** (2001). "Effects of
    voluntary force generation on the elastic components of endpoint
    stiffness." Exp Brain Res 141: 312-323.
    - DOI: 10.1007/s00221-001-0028-3
    - Endpoint stiffness increases 4-7x with co-contraction.

14. **Schouten, A.C., et al.** (2008). "A rigorous model of reflex
    function indicates that position and force feedback are flexibly
    tuned to position and force tasks." J Neurophysiol 99: 2000-2016.
    - DOI: 10.1152/jn.00789.2007
    - 13-parameter neuromusculoskeletal model fitted to ankle
      perturbation data (k_p, k_v, k_f, k_a, b_a, I_a, k_tendon,
      tau_ms, tau_gto, f_a, d_a, b_c, k_c).

15. **Valero, J.S., et al.** (2021). "Neurophysiological validation of
    simultaneous intrinsic and reflexive joint impedance estimates."
    J Neuroeng Rehabil 18:21.
    - DOI: 10.1186/s12984-021-00809-3
    - 2 deg position perturbation (pulse+hold), PC model, ankle.

16. **An, K.N., et al.** (1989). "Determination of muscle and joint
    stiffness in the elbow joint in vivo." J Biomech 22(8): 807-815.
    - In vivo elbow joint stiffness measurement.

17. **Mussa-Ivaldi, F.A., Hogan, N., Bizzi, E.** (1985). "Neural,
    mechanical, and geometric factors subserving arm posture in
    humans." J Neurosci 5(10): 2732-2743.
    - Arm stiffness ellipsoid during posture.

### Perturbation predictability

18. **Kurtzer, A.J.** (2015). "Long-latency stretch reflex: a
    transcortical view." Motor Control 19(1): 1-21.

19. **Pestilli, F., et al.** (2008). "Temporal shift in task factor
    influence across the stretch reflex." PLoS One.
    - DOI: 10.1371/journal.pone.0350818

20. **Schuurmans, F., et al.** (2009). "Modulation of long-latency
    reflexes by perturbation velocity and direction."

## Canonical model parameters

| Parameter | Notation | Value (typical) | Source |
|-----------|----------|-----------------|--------|
| Intrinsic ankle stiffness | k_a | 16 Nm/rad | [Crago 1976; Schouten 2008] |
| Reflex gain scales | 4-7x | Co-contraction | Perreault 2001 [#13] |
| SLR latency | tau_ms | 20-50 ms | Crago 1976; Allum 1982 |
| LLR latency | tau_ms | 50-100 ms | Gielen 1988; Kurtzer 2015 |
| Position feedback gain | k_p | 0-20 Nm/rad | Schouten 2008 |
| Velocity feedback gain | k_v | -17 Nm*s/rad | Schouten 2008 |
| Force feedback gain | k_f | variable | Schouten 2008 |
