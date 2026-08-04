# Task 5 — Perturbation Amplitude Table

## Statement

Perturbation studies use controlled mechanical inputs (torque, position,
velocity, or force) to probe joint stiffness and reflex responses.
The amplitude and waveform determine whether the response is linear
(small) or nonlinear (large).

## Prediction

Perturbation amplitudes below ~5 deg or ~2 Nm will be reported as
producing linear SLR responses; amplitudes above this threshold will
show nonlinearity, saturation, and recruitment of LLR pathways.

## Table

| Study | Year | Joint | Perturbation type | Amplitude | Units | Waveform | Duration | Latency SLR | Latency LLR | Notes |
|-------|------|-------|-------------------|-----------|-------|----------|----------|-------------|-------------|-------|
| Gielen 1988 | 1988 | Elbow | Torque | 0.25-20 | Nm | ramp | variable | 25-50 ms | 50-75 ms | "hold on" task; pre-load same or different dir |
| Schouten 2008 | 2008 | Ankle | Position | 2 | deg | pulse+step | 40ms pulse | ~40 ms | 150-200 ms | PC model; 2 deg pulse-step |
| Schouten 2008 | 2008 | Ankle | Torque | 0.12-10 | Nm | torque-controlled | — | — | — | 3 task instructions x 3 perturbation BW |
| Lee 2011 | 2011 | Ankle | Position | 5-10 | deg | — | — | — | — | Static, relaxed, 2 DOF |
| Lee 2013 | 2013 | Ankle | Position | 10 | deg | sinusoidal | — | — | — | Active (10% MVC), 2 DOF |
| Valero 2021 | 2021 | Ankle | Position | 2 | deg | pulse-step | 40ms+460ms | ~40 ms | 150-200 ms | PC-based, 10 subjects, 20 hold periods |
| An 1989 | 1989 | Elbow | Torque | 0.1-1.0 | Nm | step | — | — | — | In vivo elbow stiffness |
| Perreault 2001 | 2001 | Arm (endpoint) | Force | 5-50 | N | — | — | — | — | Endpoint stiffness vs. co-activation |
| Crago 1976 | 1976 | Muscle | Position | 0.5-5 | deg | step | — | 8-30 ms | — | Cat soleus; intrinsic + reflex |
| Allum 1982 | 1982 | Triceps surae | Position | 1-5 | deg | step | — | 15-30 ms | 30-50 ms | Ischaemia + vibration protocol |
| Allum 1984 | 1984 | Triceps surae | Position | 1-5 | deg | ramp | — | 20-40 ms | 40-70 ms | SLR compensates intrinsic stiffness |
| Hogan 1985 | 1985 | Elbow | — | — | — | — | — | — | — | Stiffness range: 1-200 Nm/rad |
| Winter 1998 | 1998 | Ankle/hip | — | — | — | — | — | — | — | Inverted pendulum; I ~ 52 kg*m2, Ke ~ 327 Nm/rad |
| Loram 2005 | 2005 | Ankle | Position | 2 | deg | — | — | — | — | Gravitational load stiffness mgh |
| Patel 2000 | 2000 | Lumbar | Torque | 0.5-3.0 | Nm | — | — | — | — | Human lumbar FSU testing |
| Nachemson 1979 | 1979 | Lumbar | Torque | — | Nm | ramp | 5 Nm steps | — | — | Up to 7.5 Nm, 400 N compression |
| Schultz 1979 | 1979 | Lumbar | Torque | — | Nm | ramp | 5 Nm steps | — | — | Up to 7.5 Nm, 400 N compression |

## Units conversion

| From | To | Factor |
|------|----|--------|
| Nm/rad | Nm/deg | 0.01745 |
| Nm/deg | Nm/rad | 57.296 |
| deg | rad | 0.01745 |
| rad | deg | 57.296 |

## Key threshold values

| Parameter | Small (linear) | Large (nonlinear) | Source |
|-----------|----------------|-------------------|--------|
| Ankle position perturbation | < 2 deg | > 5 deg | Schouten 2008; Lee 2013 |
| Wrist torque perturbation | 0.5-1.5 Nm | > 5 Nm | Gielen 1988; An 1989 |
| Background torque (ankle) | 0-1 Nm | 2-5 Nm | Schouten 2008 |
| Background torque (wrist) | 0 mMm | 200 mMm | Gielen 1988 |
| Perturbation velocity (wrist) | 50 deg/s | 200 deg/s | Gielen 1988 variants |

## Canonical perturbation waveform

The standard protocol (Schouten 2008, Valero 2021):

    pulse-step:  40 ms ramp-hold-return followed by 460 ms hold
- Rising/falling edges: low-pass filtered at 30 Hz, critically damped
- Rate-limited at 227.6 rad/s to avoid overshoot
- Amplitude: 2 deg dorsiflexion (ankle) or scaled to joint

The perturbation must be large enough to elicit reflexes but small
enough to remain in the linear regime for system identification.

## References

1. Schouten, A.C., et al. (2008). A rigorous model of reflex function.
   J Neurophysiol 99: 2000-2016. DOI: 10.1152/jn.00789.2007

2. Gielen, C.C.A.M., Ramaekers, L., van Zuylen, E.J. (1988).
   Long-latency stretch reflexes as coordinated functional responses.
   J Physiol 395: 113-128. DOI: 10.1113/jphysiol.1988.sp017415

3. Valero, J.S., et al. (2021). Neurophysiological validation of
   simultaneous intrinsic and reflexive joint impedance estimates.
   J Neuroeng Rehabil 18:21. DOI: 10.1186/s12984-021-00809-3

4. Crago, P.E., et al. (1976). Functional characteristics of cat
   soleus muscle as studied by tendon vibration. J Physiol 257:731-746.

5. Perreault, E.J., Kirsch, R.F., Crago, P.E. (2001). Effects of
   voluntary force generation on the elastic components of endpoint
   stiffness. Exp Brain Res 141:312-323.

6. Lee, H., et al. (2011). Multivariable static ankle mechanical
   impedance with relaxed muscles. J Biomech 44(10):1901-1908.

7. An, K.N., et al. (1989). Determination of muscle and joint
   stiffness in the elbow joint in vivo. J Biomech 22(8):807-815.

8. Nachemson, A.L., Schultz, A.B., Berkson, M.H. (1979). Mechanical
   properties of human lumbar spine motion segments. Spine 4(1):1-8.

9. Schultz, A.B., et al. (1979). Mechanical Properties of Human Lumbar
   Spine Motion Segments-I. J Biomech Eng 101(1):46-52.
   DOI: 10.1115/1.3426223
