# Capture integration contract — coordinator only

**Current continuity amendment:** see [THE_CONTINUITY_LAW.md](THE_CONTINUITY_LAW.md) and the appended integration update. A low-lift persistent section passes the proposed 60 Hz geometric bound; finite-force startup closes from rest. Full physical integration remains CLOSED. Earlier results below are preserved history.

**Prior stance amendment:** sampled stance/foot position now passes with the
free-frame inverse. Use the appended "Stance-closure amendment" for current
seed selection, ROM parity and clamp/referee propagation. The earlier
candidate specification is retained as history; full gait readiness is CLOSED.

Companion derivation and Rule-0 ledger: `THE_CAPTURE_LAW.md`.
**Current result: CLOSED. Do not enable a walk from this PR.** This is an
offline controller/probe and a C++ integration specification, not an engine
patch. The measured FK error, pose return and passive contact closure fail;
signed impulse limits, lateral support and full swing dynamics are unmeasured.

## STATEMENT / PREDICTION / FALSIFIER

**STATEMENT:** a capture gate must evaluate physical feasibility before issuing
poses or changing support; analytic CP convergence alone is insufficient.

**PREDICTION:** this calibration produces a closed gate with the supplied
candidate. A +10% velocity perturbation can yield one-step full-state recovery
only if the independent placement and signed-impulse requirements are both
admitted and the actual contact/rig trajectory meets the tolerance.

**FALSIFIER:** enabling the candidate despite a missing budget, out-of-ROM or
unreachable target, pose-loop/contact error over tolerance, unvalidated lateral
support, or a clipped command subsequently described as deadbeat.

## Units, ownership and interfaces

* Scalar forward x below corresponds to mesh Z; mesh Y is up. The local ground
  frame must be supplied explicitly if heading or ground normal changes.
* Angles in the pack's ROM are **degrees**; math and shader theta are radians.
  `main.cpp` POST `/joint` accepts `{joint:name_or_index,theta:degrees}` for the
  editor. POST `/joints` accepts `{on:bool}` and is not an array-of-angles API.
  GET `/joints` reports state. Inspect the current handlers when implementing;
  the requested dedicated HTTP schema was not found under `docs/` at this SHA.
* Existing `Engine::gait_theta(double&,double&)` serves the older two-knee CPG.
  It is NOT the 28-element JNT3 gait function below. Do not silently overwrite
  its meaning. A separate coordinator change must establish ownership and
  populate the six named hip/knee/ankle entries of the joint state buffer.
* Python is the offline derivation bench only. All runtime state, control and
  FK evaluation belong to the engine (C++/GPU); no HTTP-per-frame Python loop.
* Preserve the shader's fixed-rest-pivot root-first/own-last product and JNT3
  second-owner blend. Do not accumulate rotations into last frame's vertices.

## Exact tested candidate `gait_theta(k,t)`

The mathematical profile is defined by targets plus a constrained inverse,
not six invented sinusoidal amplitudes. Let k be the integer support-step
number, t in [0,T) the time since that step began, and absolute phase time
u=k*T+t. T here is the conditional surrogate fixed point from the derivation;
it may only be used by the offline falsifier until the full clock is certified.

```text
gait_theta(k, t, previous_theta):
    theta[0..27] = 0
    for side in {L, R}:
        phase = modulo(k*T + t + (side==R ? T : 0), 2*T)
        P = calibrated_rest_sole_centroid[side]
        if phase < T:
            target = P - forward * lipm_x(phase; -a, vb, omega)
        else:
            phi = pendulum_solution(phase-T; phi0=-asin(a/L), phidot0=0)
            target = P + forward * L*sin(phi)
                       + up * L*(cos(phi)-cos(asin(a/L)))
        seeds = {previous_theta[side], both_reverse_FK_planar_IK_branches(target)}
        candidates = constrained_DLS(actual_JNT3_sole_centroid, target, seeds, ROM)
        q = candidate_with_smallest_position_residual
        theta[hip_side, knee_side, ankle_side] = q
    evaluate BOTH legs simultaneously with actual_JNT3_pose_points(theta)
    return theta, measured_residuals, validity
```

This is exactly `gait_target` + `Rig.solve` + simultaneous evaluation in
`gait_capture.py`. Numerical solver history is part of the state: the measured
nonzero pose return means **there is currently no certified periodic
theta(k,t) depending only on phase**. Do not concatenate this failed first
stride indefinitely, force its endpoint equal to its start, or conceal the
joint jump in a blend. The coordinator must solve/verify a periodic inverse
branch before an offline table can be accepted.

Mirror rule: M=diag(-1,1,1), pivot_R=M*pivot_L, axis_R=det(M)*M*axis_L.
For this pack hip/knee axes are +X and ankle axes -X on both sides. Therefore
theta_R(phase)=theta_L(phase+T) for ideal mirrored geometry: **no extra angle
negation**. Use side-specific LBS weights/vertices for the final test.

## Controlled support transitions

Keep measured state `(p,X,v,contact_side,t,previous_theta)` in the engine.
Never replace measured X,v with reference values to manufacture convergence.
The ideal integrator and support transition are:

```text
predict at intended touchdown:
    x = X-p
    (xm,vm) = A(remaining_time) * (x,v)

capture-only mode:
    d = xm + vm/omega - xi_ref
    j = 0

one-step full-state mode:
    d = xm + a
    j = vb - vm                 # signed J/m, including braking

    next_foot = p+d
    planned_x_plus = xm-d
    planned_v_plus = vm+j
```

At a full step start these equations use remaining_time=T. During an ongoing
swing, changing the planned landing foot changes the swing boundary-value
problem. Do not extrapolate a changing target while retaining a stale
reachability/actuation certificate. At a confirmed contact event, apply the
certified physical impulse/impact law and update the support label. A variable
called `j` is not an implementation of push-off. Record the actual impulse,
the actual foot location and the resulting state; compare with the prediction.

The nominal target recipe above only covers `d=2a`. For corrected d, use the
**absolute intended foot** and actual predicted root trajectory to form the
stance target `Q_body=foot_world-root_translation`. A swing must join its
current world position/velocity to that foot with **zero world foot velocity
at touchdown** (unless an explicit impact law accepts a nonzero value).

One completely specified **driven** candidate, for the coordinator to test
after deriving actuator budgets, is a quintic Hermite trajectory in world
coordinates with measured initial position/velocity/acceleration and desired
touchdown position/velocity/acceleration. For duration T and normalized u:

    Q(u)=c0+c1*u+c2*u²+c3*u³+c4*u⁴+c5*u⁵
    c0=Q0; c1=T*V0; c2=T²*A0/2
    D=Q1-c0-c1-c2; V=T*V1-c1-2*c2; A=T²*A1-2*c2
    c3=10*D-4*V+A/2; c4=-15*D+7*V-A; c5=6*D-3*V+A/2

Specify Q1 on the ground and V1=A1=0 for a planted foot. These six boundary
conditions uniquely fix the polynomial; terrain clearance is an additional
constraint and must be checked, not assumed. This driven candidate is **not
the tested passive trajectory** and supplies no clock by itself. Its duration
must be determined from swing dynamics/effort limits together with stance,
capture and contact constraints. No polynomial frequency is a derived gait.

## Capture gate (all conditions, fail closed)

```text
capture_gate(state, candidate, certificate):
    require finite(state, candidate), canonical_pack_and_axes_match
    require certificate.full_coupled_clock_loop_closed
    require certificate.periodic_inverse_branch_closed
    require certificate.continuous_foot_error <= 0.005*H
    require certificate.ground_clearance_and_touchdown_contact
    require certificate.lateral_balance_and_support_polygon
    require certificate.signed_impulse_bounds_are_measured
    require certificate.j_min <= candidate.j <= certificate.j_max
    require candidate.foot in certified_reachable_foot_set(remaining_time, state)
    require candidate.theta within ROM without clipping
    require abs((xm-d)+(vm+j)/omega-xi_ref) <= declared_state_tolerance
    if exact_full_state_mode:
        require abs(xm-d+a), abs((vm+j-vb)/omega) <= declared_state_tolerance
    require predicted_contact_forces inside measured friction cone
    require no unsupported interval; verify actual contact before switching support
    require energy/reset ledger agrees with stated impulse and impact model
    return ADMITTED

if not ADMITTED while preparing to start:
    keep the independently certified standing controller in charge
    publish the actual failing conditions
if not ADMITTED during motion:
    invoke an independently certified recovery/stop policy
    # Freezing theta or zeroing velocity is NOT a fall-prevention policy.
```

No recovery policy is supplied or certified by this PR. A stopping step needs
its own delayed capture point in the true reachable set, rather than simply
using the next nominal walking foot. With no such policy, walking cannot be
enabled under a "without falling" claim.

## Startup and handoff gates

The smallest ideal stable-manifold kickoff at x=0 is
`J/m=omega*xi_ref=0.555972770` followed by periodic supports. A controlled lean
`x=xi_ref,v=0` is another manifold point. Both need a physical preparation and
first-swing certificate. Exact midpoint kickoff `J/m=vc=1.865289511` needs
touchdown after T/2 and cannot inherit a full-duration passive swing.

Before the coordinator enables anything: identify a swing/impact/actuator law
and measure its budgets; derive a coupled period within its capture/reach
domain; close the inverse branch with contact and foot orientation; verify
continuous error and lateral balance; certify in the live engine. These are
unclosed dependencies, not permission requests or claims about work performed.

Exact Rodrigues uses one evaluation per pose. Do not port the mirror's
hypothetical small-angle substep count. For the tested profile, even infinitely
fine temporal sampling leaves the measured bad poses and contact discontinuity.

## Stance-closure amendment — 42c6f5db / S1–S4

This section supersedes the **inverse selection and foot-position verdict**
above. It does not supersede the full capture/contact gate. See the appended
STANCE CLOSURE LAW in `THE_CAPTURE_LAW.md` for the derivation and Rule-0 tests.

**Recommended fix:** port the free-frame seed plus stable bounded refinement;
retain the current axes, ROM, weights, pivots and root height. The real-blob
probe now passes the sampled foot gate: max/RMS 9.873789293e-11 /
2.182060552e-11 wu. Do not apply an unconditional right-side ROM reversal.

### Exact inverse update

The stance/swing target formulas and capture clock are unchanged. Replace the
`seeds` and candidate-selection lines in `gait_theta` as follows:

```text
U=target-A; B0=P-H; B1=H-K; B2=K-A     # all in the Y,Z plane
l0=length(B0); l1=length(B1); l2=length(B2); r=length(U)
rho_lo=max(abs(l1-l2),abs(l0-r))
rho_hi=min(l1+l2,l0+r)
if rho_lo>rho_hi: reject geometric seed (never move the target into range)
rho_squared=(rho_lo^2+rho_hi^2)/2
delta=acos((rho_squared-l1^2-l2^2)/(2*l1*l2))

for both solutions phi of
    cos(arg(U)-arg(B0)-phi)=(r^2+l0^2-rho_squared)/(2*r*l0):
    D=U-R(phi)*B0
    for both two-link inverse branches D=R(phi1)*B1+R(phi2)*B2:
        signed_plane_angles=(phi-phi1, phi1-phi2, phi2)
        theta_j=signed_plane_angles_j / axis_j.x
        enumerate theta_j+2*pi*n within the actual ROM
        retain admissible triples; verify their rigid full-frame FK

seeds={previous_theta[side], old_flat_seeds, new_free_frame_seeds}
for each seed:
    solve actual_JNT3_sole_centroid(theta)=target within ROM
    use augmented least squares [J;sqrt(lambda)I], not normal equations
    stop when residual<=1e-10 wu
    use an inward finite difference at an upper ROM boundary
if any refined candidates have residual<=1e-10:
    select the one closest to previous_theta[side]
else:
    select the least residual and report the failed target if above 0.005 H
```

Use bounded acos arguments only to absorb floating-point roundoff, not to
admit geometry outside the interval. r=0 is orientation-degenerate: the probe
tries phi=0 and expressly makes no exhaustive ROM claim for that case. The
new code is `free_frame_seeds`, `rom_representatives`, and `bounded_refine` in
`tools/gait_capture.py`. It still calls the mirror for actual FK/LBS.

Delta is a derived virtual-link extension margin, not a knee-angle bias or
root drop. Its continuous geometric lower bound for these targets is
0.141938983 rad; its sampled minimum is 0.173619618 rad. No delta is added to
engine joint commands. Propagate actual derived angles, not a blanket crouch.

### Correct ROM parity and clamp propagation

For each pair, compute a_expected=det(M)*M*a_L. If a_R=s*a_expected, then
theta_R=s*theta_L. For s=-1 the interval must become [-hi_L,-lo_L]; for s=+1
it stays [lo_L,hi_L]. Do not infer s by the suffix `_R`, or confuse ordinary
vector reflection M with axial reflection det(M)*M. Here s=+1 for all six leg
joints' pairs, so the shipped paired table remains correct.

If a future pack genuinely negates an axis, its scalar interval, stored pose,
velocity, torque sign, caches and command producers must change representation
consistently. Specifically,

    clamp(s*theta, mirrored_interval) = s*clamp(theta, original_interval).

The probe applies the derived table to a COPY in memory. An engine change
must instead establish a single canonical table and use it in all readers:
`j_rom_`, the single-joint editor, show sweep, UI limit labels, bulk-pose input,
GPU state and any gait authoring path. Swapping the numbers only in the CPU
probe would leave the engine executing a different feasible set.

At the audited engine SHA, the single-joint editor clamps degree input using
`j_rom_`, then writes radians. The bulk `pose_pending_` render-thread path
copies radians directly into joint state, without a clamp in that block.
The coordinator must validate that whole path before integration; no live
clamp change is made in this PR. Do not silently clip a gait command and then
report deadbeat recovery against the unclipped state.

### Referee propagation

`tools/rom_referee_r2.py` currently tests a_R=-M*a_L and compares mirrored
L(+theta) with R(+theta), which matches this pack. For a general parity s,
its spatial test must compare mirrored L(theta) with R(s*theta). Test BOTH
transformed interval endpoints, not just shared positive sample angles.
Flexion/extension labels must refer to spatial movement: a negative scalar
endpoint may be the right-side flexion extreme when s=-1. Convert the measured
right stops into the common spatial convention before comparing L/R budgets,
and only then convert the recommended interval back into each stored axis.
The referee's current practice of publishing paired common bounds is valid
only after that convention is established. This is a specification for the
coordinator, not a claim that the referee has been modified or run here.

### What still prohibits a live walk

The corrected local selection reports maximum sampled joint jump
2.381311797 rad and pose-return discrepancy 0.297065513 wu. It solves sampled
foot positions but does not produce a certified continuous periodic joint
path. Keep the old pose-history, contact, effort, lateral and physical-clock
conditions in the gate; none becomes satisfied by a small centroid residual.
The net full-frame angle statistic is not a contamination test or a substitute
for measuring the actual LBS contact patch and sole orientation.

The coordinator can now evaluate continuous inverse-branch tracking and
contact dynamics without the old false flat-seed reach restriction. No new
ankle DOF or band surgery is supported by this position test alone.

## Continuity amendment — supersedes pointwise inverse playback

Companion: `THE_CONTINUITY_LAW.md` (K1–K4, complete derivation and falsifiers).
The default probe now prints the old pointwise inverse as `baseline_*` and
then the continuous section as `continuity_result`. The baseline's 2.38 rad
jump is not part of the new command stream.

**STATEMENT:** evaluate the certified branch and C1 boundary law in the engine;
never use an exact-residual competition to replace its branch mid-motion.

**PREDICTION:** nominal contact velocities and joint angles close; actual 60 Hz
increments stay below the proposed 0.116378172 rad bound (ankles constant).

**FALSIFIER:** branch/ROM loss, foot gate failure, wrong phase at first contact,
an unchecked perturbation impulse, or a frame-bound violation. This is not
permission to integrate before force, contact and visual gates are ratified.

### Exact state/phase and angle law

Compile side-specific H,K,A,P, axis signs and ROM from the SAME pack. Derive
b, Kstar, sigma, c and d exactly as `ContinuitySection` and `continuity_probe`.
For this pack sigma=+1 on both sides, b=0.05310943 physical +X radians,
c=0.001928210330 wu, d=0.081709942273 wu. These are a low-lift section, not the
old pendulum target and not a requested ROM/band revision.

```text
section_inverse(side, Q):
    require Q.X == P[side].X within numerical tolerance
    U = (Q-Kstar)[YZ]; r = norm(U)
    require abs(l0-l1) < r < l0+l1
    delta = acos((r*r-l0*l0-l1*l1)/(2*l0*l1))
    h = sigma*delta - arg(B0) + arg(B1)
    knee = arg(U) - arg(B1 + R(h)*B0) - b
    candidates = ROM_representatives([h,knee,b] / axis_X)
    require exactly one candidate on the certified section
    return candidate                      # never clamp, flip, or reseed

prepare(s):                              # COM stationary, 0 <= s <= 1
    theta = (3*s*s-2*s*s*s) * theta_section_at_rest
    duration = prepare_frames / 60        # measured 1 frame, separately gated

start_from_rest(t):                       # 0 <= t <= T after preparation
    u = omega^2*a / (cosh(omega*T)-1)
    X = u/omega^2 * (cosh(omega*t)-1)
    v = u/omega * sinh(omega*t)
    Q_L = P_L - forward*X
    Q_R = P_R + driven_swing(t,T,0,a,0,-vb,d,c)
    theta[leg_L] = section_inverse(L,Q_L)
    theta[leg_R] = section_inverse(R,Q_R)
    at t=T: verify measured (X,v) == (a,vb); confirm contact
            stop the extra force; switch support by 2a
            enter periodic phase T, not phase zero

gait_theta(k, t):                         # absolute phase tau=k*T+t
    tau = k*T+t                          # first periodic k is 1
    theta[0..27] = 0
    for side in {L,R}:
        phase = modulo(tau + (side==R ? T : 0),2*T)
        if phase < T:
            Q = P_side - forward*lipm_x(phase)
        else:
            Q = P_side + driven_swing(phase-T,T,-a,a,-vb,-vb,d,c)
        theta[leg_side] = section_inverse(side,Q)
    return theta
```

`driven_swing` is the three-piece sagittal law and quartic lift in K3 and the
Python function of that name. Its return offsets are Y,Z (not X,Y). Start
speed zero removes the initial turning piece; never divide by zero there.
Its joins are C1 and acceleration is allowed to jump. The initial preparation
also starts/stops at zero joint velocity. Keep the calibrated standing
support/COM coordinate offsets when converting body-relative Z to world X.

The L/R rule is unchanged: M=diag(-1,1,1), a_R=s*det(M)*M*a_L, theta_R=s*theta_L
at corresponding local phases, with a T phase offset in periodic motion.
Here s=+1. Recompute the small geometric side differences rather than assuming
bitwise-identical vertices. ROM sign-swap is conditional on s=-1; no new clamp
or referee convention is requested. Bulk pose paths must still validate ROM.

### Gate before scheduling; preserve analytic continuity

1. Verify the section's whole planned target interval, continuous ROM margin,
   LBS bound and required timing/overshoot reserve. The probe's proof
   subdivisions (878 intervals) do not become extra rendered frames.
2. Ratify the proposed per-frame geometric bound. At 60 Hz and fixed ankles:
   `Delta <= sqrt(8*(eps-e_LBS-Amax*dt^2/8)/C)`, with eps=0.005H,
   e_LBS=0.000250545733, Amax=71.030061, C=14.980247749. Preparation moves
   three hinges, uses C=35.610701037, and has its own 0.079066594 bound.
3. Verify the actual clock dt and angle increment, including the first and
   repeated stride seams. Do not divide a 60 Hz jump into hidden offline
   substeps and report the smaller increments as engine compliance.
4. Prefer evaluating the analytic C1 section in C++/GPU. Linear interpolation
   of an angle table retains the proved position-chord bound, but is only C0
   in velocity. It does not inherit the C1 claim. Another interpolation law
   needs another ROM/position certificate. Never accumulate FK into vertices.
5. For finite startup, the required horizontal force is m*0.806343648 for
   T=1.831964036 s; its integral is m*1.477192564 and work is m*1.739652480.
   Confirm an actual contact/actuator law supplies it. It is not an assignment
   to measured X,v. Stop extra forcing at exchange; the resulting E is the
   existing orbit's E. No instantaneous startup impulse is needed by this law.
6. At nominal exchanges, d=2a and j=0. A perturbed hybrid reset with j!=0
   requires a separately certified impact/joint impulse or finite-force
   boundary problem; do not claim this nominal C1 path covers it.
7. Keep the integration gate CLOSED for missing actuator budget, whole-sole
   contact/slip, lateral balance, physical clock, terrain/clearance or visual
   ratification. Plan/reject before scheduling. A sudden runtime freeze of the
   legs with a moving COM is not a derived safe fallback.

The engine's exact Rodrigues FK has no special angular stability limit at
60 Hz. The proposed limit bounds geometric interpolation deviation; it does
not prove absent triangle tearing or perceived smoothness. The coordinator
must judge the live movie and ratify or reject the proposal.
