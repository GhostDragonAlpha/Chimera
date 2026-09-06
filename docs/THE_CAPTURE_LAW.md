# The capture law — ASTRA derivation bench

Base: `04d7bd7a8eb10167cbab05e4da469cb222a1c53a`. Scope: offline theory,
CPU falsification, and an integration contract; not live-engine certification.
The coordinator's clock retraction in `THE_MATHEMATICS_OF_WALKING.md` binds.
COM `[-0.0002198713, 5.5961329890, 0.4057449222]`, ground `-0.019507`,
H = `5.615640`, hip-to-ankle leg L = `3.091285` are calibration, not fitted
parameters. The mirror's diagnostic boundary residual is about `1.11e-16`.
Neither the retracted clock nor the diagnostic `1/omega` clock governs this work.

## Pre-run membranes (declared before implementation)

| Law | STATEMENT | PREDICTION | FALSIFIER |
|---|---|---|---|
| C1 capture | Constant-height LIPM separates into growing xi and decaying eta. | Analytic flow and independently integrated flow agree within 1e-8 world units, using velocity/omega for dimensional comparison. | Larger residual; zero-input standstill moves. |
| C2 reset | Capture-only feedback cancels xi error in one step, not the full state; placement plus a signed velocity impulse can reset both. | A 10% initial velocity perturbation has one-step xi convergence; the two-input map has one-step full-state convergence at 1e-9 scaled-state tolerance. | Wrong convergence count, or unchanged-foot ablation also converges. |
| C3 energy | Nominal symmetric transfers conserve orbital energy; correcting a perturbed orbit needs an explicit energy change. | Stance and nominal reset errors below 1e-9 in specific-energy units; the correction ledger closes to the same tolerance. | Claiming the perturbed energy is preserved while resetting to a different target energy. |
| C4 clock | A finite-amplitude point-pendulum surrogate can close T=P(T), but capture and equal phase durations alone do not identify a physical clock. | Starting from the derived small-amplitude half-period, the candidate loop converges in at most 64 iterations with residual below 1e-10 s; independent pendulum integration returns within 1e-7 s. | Nonconvergence, invalid arcsine, failed independent return, or calling this a certified gait despite failed rig/contact/budget gates. |
| C5 rig | Reverse-order planar IK must be checked through the actual JNT3 LBS, not textbook articulated FK. | Sole max error below 0.005 H is the integration requirement, NOT an assumed pass. Exact subset evaluation agrees with the full mirror within 1e-10 wu. | Error exceeds 0.005 H, ROM/lateral violation, or full/subset disagreement. |
| C6 closure | Passing the surrogate clock is necessary but insufficient for a realizable stride. | Pose/target endpoints close; all contact, reach, budget and moving-pivot conditions must also close before enabling gait. | Any missing budget, failed reach/contact, or nonzero unmodelled swing forcing keeps the gate CLOSED. |

Numerical tolerances above are declared verification tolerances, not biological
constants. The 0.005 H geometric threshold is the task's acceptance bound.
Measured outcomes and the full derivation are appended after the runs.

## 1. Scope, coordinates and the missing inputs

Sagittal x in the equations below means the mesh's **Z** direction; mesh Y is
up, mesh X lateral. Let X be absolute COM position, p the current support,
x=X-p, v=dX/dt. Distances are world units (wu), time seconds, energies are
specific energies (wu²/s²), impulses are **J/m** (wu/s). The mirror uses
g=9.80665 in these units. It computes COM as an unweighted vertex mean, not a
mass-weighted mechanical COM. This calibrated proxy is inherited, not upgraded
by calling it COM. No body mass, leg inertia, impact law, friction coefficient,
actuator limits or impulse budget is supplied by the JNT3 pack.

The inherited Fr=0.183 gives mean speed V=sqrt(Fr*g*L)=2.355350 wu/s. Fr is
a reference choice in the mirror, not a uniquely derived preference of this
creature. Holding V fixed does not make cadence an input.

The math uses an ideal torque-free point support, constant COM height,
instantaneous support change and continuous v unless an explicit impulse is
included. Physical contact is a separate gate. In particular, repositioning p
is not the same thing as an engine implementing contact forces.

## 2. Capture point and region (C1)

The programmed stance equation is x''=omega²*x, omega=sqrt(g/H)=1.321480348/s.
Define xi=x+v/omega and eta=x-v/omega. Then

    xi'=omega*xi, eta'=-omega*eta
    [x(t);v(t)] = A(t)[x(0);v(0)]
    A(t) = [[cosh(omega*t), sinh(omega*t)/omega],
            [omega*sinh(omega*t), cosh(omega*t)]]

The absolute capture point is p+xi. After a remaining swing time r with the
old support fixed, a no-impulse stopping step must land at

    p_stop = p + exp(omega*r)*xi.

For an available foot-displacement interval [d_min,d_max], the delayed capture
region is xi in exp(-omega*r)*[d_min,d_max]. Its signed landing margin is
min(exp(omega*r)*xi-d_min, d_max-exp(omega*r)*xi). This is a **stopping** region;
a continuing walk need not put its foot at its stopping capture point.

For a symmetric orbit, a=VT/2 and

    x*(0)=-a, x*(T)=a
    vb = omega*a*coth(omega*T/2), v*(0)=v*(T)=vb
    vc = omega*a/csch(omega*T/2)  # midstance velocity
    xi_ref = -a+vb/omega = VT/(exp(omega*T)-1)
    d_nominal = 2a = VT.

The next stopping foot is exp(omega*T)*xi_ref = VT+xi_ref. Thus an interval
[0,VT] NEVER includes that stopping point for any finite positive T. Its
margin is -xi_ref. This does not falsify continuing periodic walking: putting
the foot at VT resets xi to xi_ref, rather than to zero.

We also report [-2L,2L] as an **optimistic geometric surrogate**, not a measured
capture region of the pack. Hip-to-ankle separation L is not a foot-workspace
radius; floor height, ROM, sole offset and the unusual FK order all matter.
Consequently a positive surrogate margin is only permission to test the rig.
At the candidate clock, the periodic stopping margin is -0.420719666 for
[0,VT] and +1.446933875 for [-2L,2L], at every sampled stance phase and every
nominal step (analytically phase invariant because exp(omega*r)*xi is constant).
The actual physical capture region remains uncertified.

In particular, 2L has NOT been proven to be an outer bound for this reverse
FK/LBS foot workspace (L ends at the ankle, not the sole). A rejection under
that assumed interval rejects that reach model; it is not a global
impossibility proof for the creature's real capture region.

Source correlation: [Englsberger & Ott, 2012, §II-A, equations 1–4](https://elib.dlr.de/79926/1/JohannesEnglsberger_HumanoidsPaper_2012.pdf)
gives the LIP/CP split and constant-support exponential solution. The
stopping/continuation distinction is also explicit there. The interval and
hybrid maps here are derived above and below, not borrowed controller gains.

## 3. From standstill (C2, C3)

There are two distinct meanings of "enter the orbit".

**Enter its hybrid stable manifold at the start of a full stance.** With the
periodic supports d=2a, the perturbation map is e_next=A(T)e. The stable
eigenvector satisfies delta_v=-omega*delta_x. Starting at x=0 rather than -a,
the required velocity is

    J_start/m = vb-omega*a = omega*xi_ref = 0.555972770 wu/s.

The initial error is (a,-omega*a), so every step reduces it by
exp(-omega*T), with xi exactly on reference. This asymptotically joins the
orbit; it is not exact full-state entry on the first step. A controlled initial
lean x=xi_ref=0.420719666 with v=0 is another point on this stable manifold.
Its geometric lean angle atan(x/H)=0.074779572 rad is not an anatomical command.
Getting there while stationary requires a controlled preparation, and the
available support polygon must permit it. It cannot happen spontaneously from
(0,0). This option affords a full nominal T for the first swing but does not
prove that the real swing can launch from the standing pose.

**Enter the positive-energy orbit exactly at midstance.** An instantaneous
horizontal impulse J/m=vc=1.865289511 at (0,0) sets E=vc²/2 exactly. Flow for
T/2=0.915982018 reaches (a,vb); a foot at p+2a then gives (-a,vb). This is
closed-form exact in the ideal model. A passive full swing takes T, however,
so this startup needs prepositioning or a separately actuated half-time swing.
The report prints that time deficit rather than assuming it away.

**A passive lean at v=0 cannot enter the positive-energy stance orbit exactly**:
E=-omega²*x²/2 <= 0 while E*=vc²/2 > 0. That statement is about one fixed
support's energy; it does not contradict asymptotic hybrid-manifold entry
through subsequent support changes. Total impulses in N·s require mass, which
is absent. No budget is inferred from joint ROM.

## 4. Step transition and what "deadbeat" can mean (C2)

All states below are immediately after support exchange. Predict
(x_minus,v_minus)=A(T)(x_k,v_k). Let d_k=p_(k+1)-p_k. The reset is

    (x_(k+1),v_(k+1)) = (x_minus-d_k, v_minus+j_k), j_k=J_k/m.

**Minimal capture-only feedback (one scalar actuator):**

    d_k = exp(omega*T)*(x_k+v_k/omega)-xi_ref, j_k=0
    p_(k+1) = p_k+d_k.

Its feedback row on errors is K_cp=exp(omega*T)[1,1/omega]. It cancels xi
error in one step. The closed-loop eigenvalues are (0,exp(-omega*T)); the
stable component generally survives. With +10% vb, full-state error after one
step is 2.068224169 wu in the Euclidean (x,v/omega) norm, despite near-zero xi
error. This is a measured counterexample to "one-step full-state deadbeat".
Its first d=7.216921640 exceeds the optimistic 2L allowance by 1.034352283.
The simulated later convergence is **unconstrained algebra**, not a successful
physical recovery. We never clip that command and call it deadbeat.

**Full-state placement-only deadbeat needs two steps.** Let C=cosh(omega*T),
S=sinh(omega*T), e=(x+a,v-vb). Set

    d=2a+[2C, (2C²-1)/(omega*S)] e.

For B=(1,0)^T the matrix A-BK has trace=det=0 and its square is zero. Both
errors disappear after two steps. This first command is even larger here,
7.240190927 wu, so the same reach rejection applies. No claim of one-step
full-state control with only d survives the rank-one input map.

**Exact one-step full-state reset requires a second input:**

    d=x_minus+a, j=vb-v_minus.
    delta_d=[C,S/omega]e; delta_j=-[omega*S,C]e.

The resulting state is (-a,vb) exactly. For +10% vb: d=5.754466305,
j=-1.932605984 wu/s. The negative sign means **braking**, not positive push-off.
The d margin under 2L is +0.428103052; the actual foot workspace and signed
impulse capability still have to admit it. A positive-only push-off model
cannot execute this example. This is the minimal two-input ideal reset, not
evidence that the current engine has either physical actuator.

## 5. Orbital energy ledger (C3)

    E(x,v)=v²/2-omega²*x²/2; dE/dt = v*(v'-omega²*x)=0.

Nominal exchange x_minus=a -> x_plus=-a, v unchanged preserves E exactly.
For a general support shift and signed impulse,

    E_after-E_before = v_minus*j+j²/2
                       +omega²*(x_minus*d-d²/2).

The second term is the change of the support-relative orbital quantity;
it is NOT literal mechanical work at a joint. The first is the impulse's
kinetic-energy change. At +10% vb, E_before=2.958463493 and hybrid
E_after=E*=1.739652480. Resetting to E* while also preserving a different
perturbed E is impossible. The code checks the full ledger and nominal
conservation instead of hiding this incompatibility. No impact losses are
included; their inclusion changes the required j.

## 6. Clock derivation, loop and rejection (C4, C6)

Capture plus T_stance=T_swing does **not** identify a unique clock without a
swing dynamical law and actuator/contact constraints. A driven swing can be
time-scaled for any T in a feasible interval, and the LIPM formulas above
remain a family. No absent mass distribution or torque limit may be chosen
to make the family collapse to one number.

To test the coordinator's specific reference, assume a point-mass swing leg
of length L about a fixed hip. Its equation is phi''=-(g/L)sin(phi), released
from rest at -alpha. A displacement +/-a gives alpha(T)=asin(VT/(2L)). Its
half-period, derived from pendulum energy and a change of integration variable,
is

    P(T)=2 sqrt(L/g) K(sin(alpha(T)/2))
    K(k)=integral_0^(pi/2) [1-k² sin²(u)]^(-1/2) du.
    T_next=P(T), T_initial=pi sqrt(L/g).

This supplies an actual amplitude feedback loop, rather than defining the
swing duration to equal an arbitrary T and reporting zero residual. AGM
evaluates K, and a separate RK4 integration measures the turning-point return.
The code also evaluates the mirror's original LIPM orbit functions at the
candidate clock to ensure their stance segment closes.

Measured: T_initial=1.763839384 s, fixed point T=1.831964036 s, ten iterations,
loop residual 4.403e-12 s, independent return residual 4.409e-12 s. The
candidate step is 4.314915816 wu, cadence 0.545862244 steps/s (stride 2T).
These are **conditional surrogate results**, not the governing gait clock.

For the specified +10% velocity perturbation, capture-only feedback demands

    d(T)=VT+0.1 exp(omega*T)*vb(T)/omega <= 2L.

This function increases strictly for T>0: VT increases and T*coth(omega*T/2)
increases. Bisection of the unique equality yields T <= 1.673330718 s.
But every passive half-swing satisfies P(T) >= pi sqrt(L/g)=1.763839384 s.
The feasible intersection is EMPTY, even before the real FK restrictions.
At the capture boundary P(T)=1.817999952 s, a 0.144669233 s mismatch. Thus
shortening the passive clock cannot repair this controller under that reach
assumption. A faster **driven** swing or the signed-impulse controller changes
the model; a torque/impulse budget is required to derive its feasible clock.

There is a second, independent failure of applying the fixed-pivot surrogate
to the creature. The hip translates. A horizontal hip acceleration adds
-(X_hip''/L)cos(phi) to the swing equation (and vertical acceleration also
changes its gravity term). Assuming the hip follows the LIPM translation gives
an omitted term of magnitude 0.872863923 rad/s² at toe-off. Also the passive
swing has zero relative endpoint velocity; a planted foot needs relative
velocity -vb. The mismatch is 3.407010996 wu/s at each exchange. It requires
an explicit swing impulse/impact/drive. A numerical period match does not erase
these failures. The **full coupled clock loop remains unclosed**, which the
script prints as UNDEFINED alongside the finite surrogate residual.

## 7. Rig inverse: use the product that actually executes (C5)

The brief's "small-angle composition" contradicts `joints.comp` and
`gait_mirror.frames`: both use exact Rodrigues about fixed rest pivots,
accumulated ROOT FIRST, OWN LAST by left multiplication. Engine comments
elsewhere saying "own first" do not override the executable loop.

For hip H, knee K, ankle A, foot marker rest point P, positive-X planar
rotation R and signed plane angles h,k,b, the full ankle-frame point is

    Q=A+R(b)(K-A)+R(b+k)(H-K)+R(b+k+h)(P-H).

This is not ordinary proximal-to-distal articulated IK. For a flat full
ankle frame, h+k+b=0. Put D=Q-A-(P-H), B1=H-K, B2=K-A in the (Y,Z) plane.
Then D=R(phi1)B1+R(phi2)B2, phi1=b+k, phi2=b. With l_i=|B_i| and r=|D|,

    phi1 = arg(D)-arg(B1) +/- acos((r²+l1²-l2²)/(2*r*l1))
    phi2 = arg(D-R(phi1)B1)-arg(B2)
    (h,k,b)=(-phi1, phi1-phi2, phi2).

Reachability requires unchanged lateral X, |l1-l2|<=r<=l1+l2, and at least
one branch satisfying all ROMs after conversion to stored-axis theta.
Singular r=0 needs a separate branch; the numerical fallback handles it.
The calibrated axes are hip +X, knee +X, ankle -X on BOTH sides; hence
(theta_hip,theta_knee,theta_ankle)=(h,k,-b). The code considers both branches.

JNT3 blends full first/second-owner frames per vertex. A sole centroid is
not generally the transformed centroid of a single rigid ankle frame. Reuse
the mirror's lowest-tenth ankle-band sole proxy and refine the seeds using
its ROM-constrained damped least squares against the SAME `pose_points` law.
The previous solution is the continuity seed. This position-only refinement
releases the flat-frame constraint: it cannot claim a level rigid sole.
Its max full-ankle-frame tilt is printed, not hidden. A local solver's failure
is a failed profile, not a proof that all joint configurations are infeasible.

Candidate body-relative target at time t with local leg phase lambda in [0,2T):

    lambda_L=t mod 2T; lambda_R=(t+T) mod 2T
    stance, lambda<T: Q=P - forward*x*(lambda)
    swing: Q=P + forward*L*sin(phi(lambda-T))
               + up*L*(cos(phi(lambda-T))-cos(alpha)).

This is the tested passive candidate; it replaces the mirror's arbitrary
minimum-jerk clock with a specified swing equation. It still inherits the
sole-proxy rest height, not a newly certified ground plane. Targets close
in position, but their velocity mismatch is the contact failure above.

Mirror symmetry uses M=diag(-1,1,1) on positions and det(M)*M on axial
vectors. Here det(M)*M fixes +/-X, so right angles have the SAME signs as left
angles with a T phase offset, not a blind sign flip. Each side still uses its
own measured vertices and second-owner weights; mesh asymmetry is not erased.

## 8. Substeps and measured falsifiers

Exact rest-to-pose FK requires **one evaluation per requested pose**. Its
algebraic small-angle accumulation drift is zero; finite floating-point error,
temporal sampling, target error, foot tilt and contact slip are different
quantities. The mirror's printed Euler substep estimate is for a hypothetical
approximation, not the actual shader. It must not be used to certify a stride.

For an incremental first-order rotation of a bounded-radius point, one hinge
increment delta has error <=rho*delta²/2. N equal subincrements reduce its
accumulated leading error as 1/N, not 1/N²; multiple hinges/frames need the
sum of their bounds and amplification accounting. This is why a per-frame
square-root rule is not a whole-stride certificate. We do not introduce such
an integrator or claim an unmeasured rho bound for LBS.

The recorded exact-pose profile already exceeds 0.005 H at sampled times.
No number of temporal substeps can make those same erroneous poses pass.
The report therefore prints `UNATTAINABLE_FOR_RECORDED_PROFILE` for the total
error requirement, while printing one for exact Rodrigues evaluation. Even a
passing sampled profile would need a continuous-time/contact certificate.

| Falsifier | Measured result | Verdict |
|---|---|---|
| C1 analytic vs independent RK4 | 9.193e-14 wu | PASS |
| C1 unchanged-input standstill | exactly (0,0) | PASS control |
| C2 capture-only xi convergence | one step, ~4.4e-16 error | PASS algebra; first step exceeds assumed reach |
| C2 placement-only full state | two steps, ~4e-15 scaled error | PASS algebra; first step exceeds assumed reach |
| C2 placement+signed impulse | one step, ~4.4e-16 scaled error | PASS algebra; physical budget UNKNOWN |
| C3 nominal/impulse energy ledger | assertions within 1e-9 | PASS; perturbed energy is NOT conserved |
| C4 surrogate fixed point | 4.403e-12 s | PASS conditional model |
| C4 independent pendulum return | 4.409e-12 s | PASS conditional model |
| C5 full mirror vs exact subset | 0.0 wu | PASS, five full-mesh checks with both legs active |
| C5 foot max / RMS | 0.122037881 / 0.024728394 wu | FAIL max > 0.028078200 |
| C5 flat full-frame inverse | 414 of 442 target calls outside annulus | Rejected seeds; LBS refinement not a flat-foot proof |
| C5 max full-frame tilt | 3.560502067 rad (unwrapped sum) | No level-foot certification |
| C6 pose return | 0.296449956 wu max coordinate error; theta return 1.975743440 rad | FAIL; branch history has not closed |
| C6 contact velocity closure | 3.407010996 wu/s jump | FAIL passive profile |
| C6 full clock / budget / lateral contact | not supplied or not closed | CLOSED integration gate |

221 time samples include both exchange boundaries and stride endpoint. Foot
errors use both legs active in one pose. The subset optimization only removes
unused vertices from evaluation; it does not change axes, parents, weights,
ROM or the FK law. Absolute maxima take precedence over RMS.

## 9. Honesty ledger and coordinator handoff

* **Approximated:** calibrated vertex-mean COM; fixed-height point support;
  constant reference Fr; point mass at distance L for swing; fixed hip in the
  surrogate; instantaneous signed impulses; optimistic 2L reach; sole centroid
  proxy; numerical IK; sampled rather than continuous contact checks.
* **What breaks it:** moving hip, real swing inertia and knee folding, finite
  actuator authority, impact loss, slip, support polygon edges, changing COM
  height, JNT3 sole distortion, branch switches, lateral instability.
* **Most fragile prediction:** promoting the conditional pendulum period to
  the live stride period. Its own coupling and contact falsifiers already fire.
* **Contradictions retained:** 24-byte mesh header in the committed mirror
  versus the original brief's implied 8-byte payload offset; exact Rodrigues
  versus small-angle composition; two-input requirement for one-step full-state
  deadbeat; changed orbital energy during correction; absent physical budgets.
  The committed index payload also contains **36,630 triangles**, not the
  original brief's 36,424 (109,890 indices, max index 18,458). A strict
  brief-count assertion fired during verification; it was replaced with
  actual topology-validity checks because the coordinator binds COM/H/L,
  not the stale triangle count. No blob or triangle was altered.
* **No fabricated feasible clock:** the no-impulse passive candidate fails
  the stated perturbation test under the optimistic reach model. A two-input
  candidate needs measured signed impulse limits and a driven swing/contact
  model; no principled unique period can be selected before those exist.
* **No live-engine claim:** no engine process was contacted or altered. All
  protected build files were only read. No master or force push is authorized.

Run `python tools/gait_capture.py` from repo root (numpy + stdlib only).
`--self-test` runs synthetic analytic controls; `--require-ready` returns 2
when gait is uncertified. Normal exit 0 means the falsification report ran,
not that a walk passed. Full output: `agent_logs/astra/gait_capture.txt`.
The executable coordinator contract is `THE_CAPTURE_INTEGRATION.md`.

## COORDINATOR'S RIG AUDIT (2026-09-05, post-merge 73f40bf3)

Phase-1 "hip band repair" is RETRACTED before surgery — the weights are innocent:

- hip_L/R own 300 verts each; only 47 sit above the anchor, all at crease-blend
  0.5, ZERO above 0.6. (The coordinator's earlier "863 contaminated" was a
  1.5-ball neighborhood count that included other joints' verts — misread.)
- `max_full_frame_tilt` is |q| summed over the leg's three hinge angles:
  legs bending IS the walk. Not a defect.

THE SURGICAL DECOMPOSITION (coordinator re-run, per-sample, one full stride):

  swing-phase errors          max = 0.0000
  reachable-stance errors     max = 0.0000
  flat-seed-miss errors (414) max = 0.1220  <- THE ENTIRE DEFECT
  worst window: phase 0.45..0.63 of T=1.832 (mid-stance), all on the R leg

Mid-stance is where the foot passes under the hip: the demanded hip->ankle
span equals full leg extension. Geometry: rest hip_L->ankle_L = 3.089 vs
leg = 3.0913 — the frame was fitted essentially straight-legged, so mid-stance
sits exactly on the singularity. Two open questions for the theorist:

  Q1 the ROM PARADOX: shipped knee_L ext = -147.89 deg (hyperextension allowed),
     so a straight knee is INSIDE the shipped ROM — yet the flat seed reports
     unreachable. Suspect the seed law / the ROM sign convention inside the
     solver, not the skeleton.
  Q2 the L/R ASYMMETRY: every top-12 error is the R leg. The chains are
     mirror-identical (measured). Why does only R fail? (solver warm-start
     order: L is solved first each frame and R inherits `previous`.)

  Also retracted: the coordinator's delta-sweep (Orbit(h,...) never flowed into
  gait_target — stance targets displace the rest marker horizontally only;
  identical outputs for every h proved the poke void before it misled anyone).

The ask: derive the STANCE CLOSURE LAW — how the stance leg must carry flexion
margin at mid-stance (root drop vs knee bias vs seed reformulation), with the
reachability proof and the corrected probe. The 0.0281 gate is unchanged.
