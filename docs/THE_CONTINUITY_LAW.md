# The continuity law — ASTRA

Base: `f6ff0dbfb7064eafcc774bc34730dd6f43c264f1` (merged PR #6).
Calibration is inherited unchanged: H=5.615640 wu, L=3.091285 wu,
omega=1.321480348/s. The same blobs, weights, axes, ROM and FK are used.
Pre-run statements and successive falsified candidates are recorded in the
appended continuity membranes in `THE_CAPTURE_LAW.md`. This document gives
the resulting law; `THE_CAPTURE_INTEGRATION.md` specifies coordinator handoff.

**Verdict:** a sufficient continuous, periodic, low-lift inverse section passes
the proposed geometric 60 Hz bound. This is a change of swing trajectory as
well as branch selection. The old pendulum swing height is NOT preserved.
Physical walking remains unverified: neither the tiny proxy lift nor the
required force/acceleration is an established contact/actuator capability.

## K1 — diagnose the discontinuity, not just its maximum

**STATEMENT:** demanding numerical exactness before comparing distance to the
previous pose can discard a continuous, gate-valid solution and reseed across
an inverse branch. Elbow signs alone do not distinguish that event from a
continuous passage through a virtual two-link singularity.

**PREDICTION:** the remote seed event will have a rejected nearby solution,
whereas conditioning-driven large local increments will retain seed zero.

**FALSIFIER:** the logged selected seed, local residual, ROM contact and
one-sided elbow labels fail to explain the claimed event.

Reproduced distribution: all six commanded joints, 220 intervals of T/110
seconds, including zero ankle increments where applicable. No dilution with
the 22 uncommanded joints. Quantiles describe the result; none sets a gate.

| rad per sample | PR #6 baseline | persistent section, same grid |
|---|---:|---:|
| maximum | 2.381311797 | 0.095153674 |
| RMS | 0.087412009 | 0.024127469 |
| median | 0.008044037 | 0.012754038 |
| p90 | 0.024889573 | 0.041771070 |
| p99 | 0.077820886 | 0.089323692 |

The ordinary increments grow slightly; the discontinuous tail is removed.
Baseline L max/RMS: 0.077846373/0.017214419 rad. R:
2.381311797/0.122414797 rad. There is ONE remote seed selection and THREE
virtual-knee elbow-sign changes, not three remote flips.

* At global time 2.115085751 s, R local stance phase 0.154545455:
  q changes from `(0.0714353,0.6168234,-2.7738752)` to
  `(0.2525607,-1.3369364,-0.3925634)` rad. The signed virtual-knee sine
  changes +0.686264 to -0.931101. The previous-seed refinement reaches ankle
  ROM, moves only 0.019562361 rad, and misses the target by 0.010230781 wu.
  That is below 0.028078200, but above the old 1e-10 selection tolerance.
  Seed 2 is selected instead. This is a **ROM-triggered remote branch flip**,
  not a continuous clamp bounce.
* At R stance phase 0.472727273, the 0.213476181 rad increment keeps seed 0,
  does not touch ROM, and crosses virtual-knee sine -0.178414 to +0.008256.
  The adjacent 0.157013250 rad increment also keeps seed 0. These are large
  local inverse motions near conditioning loss, not remote reseeds. The
  probe reports this evidence rather than equating every sign change with a
  topological discontinuity.

The diagnostic sine is `sin(k+arg(H-K)-arg(K-A))`, with **physical +X k**.
It labels the free-frame seed's virtual elbow, not an anatomical ROM sign.
The negative-zero-identical L/R axes and spatial ROM equivalence stand.

## K2 — persist in a certified inverse section

**STATEMENT:** keep the one ROM-admissible representative of a single inverse
chart. Where the chart has a strict annulus margin and the continued angles
stay in ROM, it is continuous and the actual LBS tracking error has a uniform
bound. Loss of these conditions rejects the trajectory; it never licenses a
remote reseed.

**PREDICTION:** both sides admit that chart for the derived stance, active
swing and finite-force startup; the same chart returns to the same angles.

**FALSIFIER:** empty/multiple ROM representatives, annulus loss, a nonzero
cyclic winding within these sub-2pi ROM intervals, or actual centroid error
above the proved bound.

Use YZ vectors and physical +X angles h,k,b; convert to stored theta by
componentwise division by the measured axis X component. Define

    B0=P-H, B1=H-K, B2=K-A; lj=|Bj|
    b=-arg(B2), Kstar=A+R(b)B2=A+(l2,0)   [YZ only]
    U=Q-Kstar, r=|U|
    Q=Kstar+R(b+k)[B1+R(h)B0].

This is the SAME root-first/own-last fixed-pivot FK, with the redundant ankle
orientation held constant. It is not a conventional moving-pivot rig. The
inverse is

    delta=acos((r^2-l0^2-l1^2)/(2*l0*l1))
    h=sigma*delta-arg(B0)+arg(B1)
    k=arg(U)-arg(B1+R(h)B0)-b.

At the rest marker, select sigma and a ROM representative minimizing |theta|.
Keep sigma forever. Enumerate theta+2pi*n in the actual ROM; require exactly
one representative. The measured choice is sigma=+1 on both sides, physical
b=0.05310943 rad, approximately
`theta_rest_section=(-0.03641322,0.07150640,-0.05310943)`.

This fixes the elbow of the **new inverse chart** (the virtual B0/B1 elbow).
It does not forbid every zero of the old free-frame chart's knee sine.
Topological persistence means a continuous lift of the target path, not
blindly freezing a coordinate-dependent sign at all singularities.

Reach requires `|l0-l1|<r<l0+l1`. Let

    gap=l2-(P-A)_y-(l0-l1), c=gap/2.

The midpoint maximizes the smaller of positive lift and retained inner
radial margin. The common L/R lift is **c=0.001928210330 wu**; it is not a
terrain or whole-sole clearance measurement. Across the resulting target
rectangle, r_min>l0-l1 and r_max<l0+l1. Thus sin(delta) stays nonzero.

For the two moving joints the inverse Jacobian determinant magnitude is
`l0*l1*|sin(delta)|`. If target speed is at most Vq, then

    |h_dot| <= r_max*Vq/D_min,
    |k_dot| <= l0*Vq/D_min.

The probe uses these analytic bounds to subdivide time intervals until the
midpoint's ROM margin exceeds the maximum possible angle excursion on each
half-interval. **878 intervals** certify continuous ROM, rather than only
sampling it. This is proof subdivision, not additional rendered frames.
The smallest sampled ROM margin is 0.058289562 rad.

Why gate-level accuracy is preserved: the analytic inverse exactly tracks the
full-frame marker. The actual sampled ankle vertices have knee second owners.
Their difference is `(1-w)(F_knee(P_i)-F_ankle(P_i))`. Hence, uniformly in h,k,

    e_LBS <= 2*|sin(b/2)| mean[(1-w_i)
             (|P_i-H|_YZ + l1+l2)] = 0.000250545733 wu.

Weights/owners are checked; no LBS weights are edited. This is below the
0.028078200 gate. Consequently the continued branch never increases actual
tracked error beyond the gate while the stated premises hold. No universal
persistence theorem is claimed for arbitrary targets: the feasible component
can end at ROM or a singularity. Reject those requests before motion.

## K3 — active swing and velocity-matched exchange

**STATEMENT:** a C1 target followed by this nonsingular chart gives a C1 joint
path; nominal support exchange needs no foot or joint velocity jump.

**PREDICTION:** swing/stance one-sided velocities agree to 1e-9 wu/s, and the
startup target and pose join the periodic orbit at the same instant.

**FALSIFIER:** mismatched endpoint data, insufficient time for the endpoint
turns, branch/ROM failure, or an unbudgeted impulse called physical closure.

A passive swing has relative endpoint speed zero; stance requires -vb.
Cubic interpolation of the endpoints alone overshoots the branch's knee ROM.
Derive the overshoot budget instead. For each height (0,c), enumerate the
circles produced by each hip/knee ROM endpoint and by both annulus boundaries;
intersect with that horizontal target line. These events partition all
sagittal intervals. Take the connected valid interval containing zero.
For L at height zero it is [-2.320877796,4.371247948] wu; R agrees to rounding.
The smaller common fore/aft reserve beyond +/-a is split to maximize
`min(used_reserve,remaining_reserve)`:

    d=(min(-z_min,z_max)-a)/2 = 0.081709942273 wu.

The two endpoint height lines choose a conservative candidate reserve;
the subsequent continuous annulus/ROM certificate covers the entire actual
profile, including interior heights. Endpoint checks alone are not a proof.

For swing duration D, z0->z1, and relative endpoint speeds v0<=0, v1<0:

    d0=d if v0<0 else 0
    tau0=-2*d0/v0 if v0<0 else 0; tau1=-2*d/v1
    M=D-tau0-tau1 > 0; distance=z1-z0+d0+d

1. First turn (if tau0>0): z=z0+v0*t-v0*t^2/(2*tau0).
2. Middle, u=(t-tau0)/M: z=z0-d0+distance*(3u^2-2u^3).
3. Last turn, s=t-(D-tau1): z=z1+d+v1*s^2/(2*tau1).
4. Vertical offset over the entire swing: y=16*c*(t/D)^2*(1-t/D)^2.

Values and first derivatives match at all joins. Acceleration can jump;
this is a C1 law, not a C2 or torque-rate certificate. The periodic parameters
are (D,z0,z1,v0,v1)=(T,-a,+a,-vb,-vb). The specific Cartesian acceleration
bound is **71.030061 wu/s^2**, dominated by the endpoint turns. It is required
kinematics, not demonstrated actuator authority.

At nominal exchange, COM v is continuous and support displacement is 2a.
Before: (a,vb); after: (-a,vb). Energy
`E=0.5*v^2-0.5*omega^2*x^2` is unchanged. Body-relative foot velocity -vb
cancels root velocity in the ideal full-frame marker. The actual LBS velocity
is continuous too, although its world velocity need not be identically zero:
a small position bound does not by itself certify zero foot slip. The
measured actual-LBS world speed at the join is 0.000138885 wu/s.

For the earlier perturbed hybrid controller, `d=x_minus+a`, `j=vb-v_minus`
still resets the state, with its previously derived energy ledger. A nonzero
j changes body velocity instantaneously. That case requires an explicit
impact/joint-impulse law or a newly solved finite-force transition. The
nominal C1 certificate must not be reused as a certification of that impulse.

## K3b — finite-force first step, starting at rest

**STATEMENT:** finite constant forcing can enter the orbit from rest at the
full-period exchange. **PREDICTION:** state, energy and first-swing boundaries
close simultaneously. **FALSIFIER:** RK4/state disagreement over 1e-8, a work
ledger mismatch, or nonzero initial target speed.

Instead of applying an instantaneous midpoint impulse and giving the swing
only T/2, apply constant horizontal force per unit COM mass u for a full T:

    x''=omega^2*x+u, x(0)=v(0)=0
    x(t)=u/omega^2*(cosh(omega*t)-1)
    v(t)=u/omega*sinh(omega*t)
    u=omega^2*a/(cosh(omega*T)-1)=E/a.

Then (x(T),v(T))=(a,vb) exactly. The first left stance follows -x(t); the first
right swing uses (T,0,a,0,-vb). At T it joins the periodic state with L at
local phase T and R at phase zero. The phase is not reset to the old midpoint
entry schedule. This removes the **scheduling deficit**, not an unknown
physical actuator limitation.

| Required quantity | Result |
|---|---:|
| horizontal force per COM mass u | 0.806343648 wu/s^2 |
| force duration T | 1.831964036 s |
| integrated force per COM mass u*T | 1.477192564 wu/s |
| injected work per COM mass u*a=E | 1.739652480 wu^2/s^2 |
| independent forced-LIPM RK4 boundary error | 1.359e-13 |
| startup state closure | 4.441e-16 |
| first-swing time deficit | 0 s |

Gravity contributes to the changing COM velocity; u*T is not v(T). During
entry E'=u*v, so E rises from zero to the desired orbital energy, rather than
being falsely described as conserved from rest. Afterwards the usual
unforced stance conserves E. Actual force is m*u; neither m nor the available
horizontal actuation is in this pack. If realized entirely by contact under
constant height, the startup friction requirement includes u as well as the
LIPM acceleration: `mu >= (omega^2*a+u)/g`, before other loads are considered.

Prepare the section while COM remains at rest, using a smoothstep of theta
from zero to theta_rest_section. One 60 Hz interval suffices for the proposed
three-moving-joint preparation bound (0.079066594 rad). Preparation adds
0.016666667 s before force onset; it is not hidden in the zero time-deficit
claim. Both entry target velocities start at zero. The preparation's
continuous foot-error certificate is 0.023010970 wu, below the same gate.

## K4 — proposed engine bound and what it proves

**STATEMENT:** bound the geometric deviation between FK of interpolated
angles and the chord of the endpoint geometry. Reuse the task's 0.005H
allowance; do not derive a tolerance from the measured jump distribution.

**PREDICTION:** the new trajectory passes at actual 60 Hz, through startup,
off-grid exchanges and a second stride, without hidden temporal subdivision.

**FALSIFIER:** any commanded inter-frame increment exceeds the bound, or the
FK/target chord certificate exceeds 0.005H. Calling this a measured visual
threshold before coordinator ratification also violates the claim's scope.

Expanding fixed-pivot FK gives rotated rest/pivot-difference vectors. Along
an angular chord with infinity increment Delta, a term of length r carrying
m changing angles has second derivative norm at most r*m^2*Delta^2.
Convex LBS preserves the sum bound. Maximizing over ALL mesh vertices gives
C=14.980247749 wu for the two moving hinges per leg; ankles are constant.
Preparation moves all three and uses C_prepare=35.610701037 wu instead.

The interpolation remainder bound is C*Delta^2/8. If target acceleration is
bounded by Amax, its Cartesian chord remainder is Amax*dt^2/8. Thus

    error <= e_LBS + Amax/(8*60^2) + C*Delta^2/8
    Delta_limit=sqrt(8*(0.005H-e_LBS-Amax/(8*60^2))/C)
               = 0.116378172 rad/frame (6.982690311 rad/s at 60 Hz).

Measured actual-60-Hz maximum: **0.095247312 rad**, RMS **0.024130364 rad**
(two strides). The first-entry-plus-stride stream also passes. The worst
resulting interpolation certificate is **0.019704563 wu**. The same full
mirror is run on a nonzero chord control (0.020237887 wu deviation, within
its predicted bound). An unreachable annulus target and the old 2.38 rad
jump serve as negative controls.

This certificate concerns deviation from endpoint geometry, not maximum
vertex travel in one frame, not triangle strain, and not a perceptual claim.
Analytic section evaluation is C1. Piecewise-linear table playback has
piecewise-constant joint velocity and does **not** inherit the analytic C1
claim; the chord certificate only bounds its position error. Prefer the
analytic engine law. Another interpolation mode needs its own validation.
Dropped frames need the actual dt and increment checked, not a 60 Hz label.

## Results, limits, and reproducibility

`OPENBLAS_NUM_THREADS=1 python tools/gait_capture.py --require-ready` prints
the preserved baseline distribution followed by the new law. Exit 2 is
intentional: continuity/tracking passes; full integration remains closed.
`--baseline-only` runs the old pointwise ablation; `--seed-law flat` retains
the older stance-closure ablation. `--self-test` checks analytic capture-state
controls; the continuity/ROM/LBS controls require the real pack.

One-stride foot max/RMS is **9.542360332e-5 / 5.643409958e-5 wu** versus
0.028078200. Pose return is 8.882e-16 rad; nominal actual-LBS velocity jump
6.875e-15 wu/s; joint velocity jump 3.775e-15 rad/s. Startup pose and velocity
joins are 8.882e-16 rad and 7.550e-15 wu/s. No ROM, axis, band, root-height,
canonical blob, mirror, engine or referee file is changed.

Honesty ledger:

* **Most fragile prediction:** the 0.001928 wu lift is usable. It is only an
  extra height of the inherited tracked centroid. Terrain, sole tilt, skin,
  and actual contact may reject it. The tracked band's minimum vertex height
  is 0.206304 wu above the mesh's global ground proxy in this probe; it is
  plainly not proof of a loaded, planted sole.
* This is a sufficient low-lift section, not the unique or globally optimal
  inverse. A higher-clearance continuous solution with the same rig may exist;
  the failed searches below do not prove it impossible.
* T remains the inherited conditional 1.831964036 s comparison period. Active
  swing replaces the passive pendulum equation. Its time boundary problem
  closes, but it cannot provide a unique physical clock without actuator,
  inertia and contact data. The old passive clock residual is diagnostic.
* Required force and approximately 71 wu/s^2 foot acceleration are unverified.
  The mass proxy, signed perturbation impulse, lateral support, friction,
  whole-sole orientation, triangle strain and visual tearing remain open.
* Failed, recorded attempts: fixed hip had cyclic/ROM jumps up to 2.321578 rad;
  local nullspace continuation missed 0.122035 wu and jumped 0.446597 rad;
  a transverse-ankle swing lost 29 annulus samples; constant ROM-end ankle
  lost 34. Cyclic variational fitting from the old seed stalled at 0.067774 wu
  with 1.988749 rad jumps; from rest it reached 7.47e-12 wu but still jumped
  2.496258 rad. These are local numerical failures, not impossibility proofs.
* A low-lift cubic endpoint interpolation still jumped 3.408222 rad at ROM;
  the derived overshoot-turn budget fixed that failure. The successful
  T/2 driven startup comparison required J/m=vc=1.865290 at onset; it is
  superseded by finite forcing to remove that initial velocity discontinuity.
* The initial coefficient implementation included zero-angle ancestor lever
  arms. Removing those identities reduced a conservative overestimate
  (15.017624 to 14.980248); the candidate passed both bounds. The formula,
  error allowance and clock were not fitted to the observed maximum.

External background only: [MathWorks' inverse-kinematics overview](https://www.mathworks.com/discovery/inverse-kinematics.html)
notes the multiple-solution issue. All section, bound and entry equations
above are derived from this repository's actual reverse FK and LIPM law;
no textbook articulated-chain inverse is substituted.
