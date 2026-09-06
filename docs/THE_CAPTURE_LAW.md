# The capture law — ASTRA derivation bench

**Current continuity amendment:** see [THE_CONTINUITY_LAW.md](THE_CONTINUITY_LAW.md) and the appended integration update. A low-lift persistent section passes the proposed 60 Hz geometric bound; finite-force startup closes from rest. Full physical integration remains CLOSED. Earlier results below are preserved history.

**Latest stance-position verdict (42c6f5db): PASS with the free-frame inverse;
no ROM, axis or skeleton change.** See the appended STANCE CLOSURE LAW and
S1–S4 results. Earlier PR #5 results below remain historical. Full physical
gait readiness remains CLOSED.

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

## ASTRA stance-closure membranes — before the corrective run

Base `42c6f5db33541da8e50e2713752e42f6fc06dcbd`; calibration and protected
blobs unchanged. The following tests concern offline position reachability,
not live contact/clock certification. Earlier results remain historical.

| ID | STATEMENT | PREDICTION | FALSIFIER |
|---|---|---|---|
| S1 | The old seed imposes zero full-frame orientation; its annulus is not the full three-hinge workspace. | A derived free-orientation seed produces FK-valid solutions for targets the old flat seed rejects, to 1e-10 wu in the rigid full-frame model. | Any seed fails imported FK, or no new admissible seeds exist. |
| S2 | Mirror ROMs transform with the sign relating the actual right axis to det(M) M times the left axis. | Identical stored +/-X axes here need no ROM change; deliberately negating a right axis AND mapping [lo,hi] to [-hi,-lo] preserves the spatial workspace. | Pack shows opposite axial parity, or the paired transformation changes FK/ROM membership beyond 1e-10. |
| S3 | Solving the redundant inverse before bounded LBS refinement can remove the position defect without editing the skeleton or lowering the root. | Full-stride max error <=0.005 H; phase/side decomposition and pose-return error are printed separately. | Any sample exceeds the unchanged threshold; a root-height modification is needed but not propagated into both targets and dynamics. |
| S4 | Side asymmetry can arise from different phase histories even when the chains are spatially mirrored. | Equal-phase, equal-seed L/R solves agree in sagittal position to 1e-6 wu; warm-start order cannot be called cross-leg inheritance because the dictionaries are separate. | Paired pack data or synchronized solves disagree beyond that bound. |

Numerical tolerances are predeclared verification bounds; 0.005 H is the
existing task gate. A failed local solve is not a global non-reachability
proof. No axis, ROM, weight or pivot in a protected blob will be changed.

## STANCE CLOSURE LAW — derivation and verdict on 42c6f5db

### 1. What the committed pack actually says (S2)

The recommended table for **this pack** is the shipped table, unchanged:

| Pair | L axis | R axis | L ROM, degrees | Recommended R ROM, degrees |
|---|---|---|---|---|
| hip | +X | +X | [-159,119] | [-159,119] |
| knee | +X | +X | [-131,147] | [-131,147] |
| ankle | -X | -X | [-159.2100067,131.4400024] | [-159.2100067,131.4400024] |

Thus the latest message's negated-right-axis premise does not hold in the
canonical blob at this SHA. The preceding audit's knee extension -147.89
also does not match this blob's -131. These may describe an uncommitted
instrument or another pack; they cannot justify altering the canonical data.

For reflection M=diag(-1,1,1), angular axes are pseudovectors, so the expected
mirrored axis is a_expected=det(M)*M*a_L. Define s=+1 or -1 from the actual
relation a_R=s*a_expected. Then

    theta_R=s*theta_L
    [lo_R,hi_R] = [lo_L,hi_L]       if s=+1
                 [-hi_L,-lo_L]     if s=-1.

This follows from Rodrigues conjugacy, M R(a,theta) M^-1 =
R(det(M) M a,theta), and R(-a,-theta)=R(a,theta). An axis not parallel to
either expected sign cannot be repaired by scalar ROM swapping.

`mirrored_rom()` implements this law in a copied, in-memory table. No
canonical blob is rewritten. For a hypothetically negated right knee, its
correct table would be [-147,131]; leaving [-131,147] loses one spatial
endpoint by 16 degrees. A deliberately negated-axis control plus the corrected
interval reproduces the full original mesh pose **exactly (0.0 wu error)**.
The unchanged-ROM ablation rejects that endpoint. This confirms the general
sign-swap law while rejecting its proposed application to the present pack.

### 2. The apparent straight-knee paradox (S1)

The old seed's necessary precondition was NOT "knee angle is in ROM". It
imposed h+k+b=0 (zero full-ankle-frame orientation) before it considered ROM.
With the reverse fixed-pivot product from §7,

    Q-A = R(b)(K-A)+R(b+k)(H-K)+R(b+k+h)(P-H),

that precondition reduces the problem to a virtual two-link vector
D=Q-A-(P-H). Write B1=H-K, B2=K-A and l1=|B1|, l2=|B2| in Y,Z.
The old seed accepts only |l1-l2|<=|D|<=l1+l2; it then proposes angles.
`flat_seed_unreachable` historically counted failure of this **restricted
geometric seed**, before any angle interval test, not full-chain reachability.

For the left calibrated sole marker, the planar lengths are

    |P-H| = 3.077611891
    l1 = 1.517644855, l2 = 1.567741580
    |H-A| = 3.077884422, l1+l2 = 3.085386435.

At exact midstance Q=P, the flat annulus has **positive** radial margin
0.007502013 wu and virtual-link bend 7.993686832 degrees. It is near straight,
but not on the extension singularity, and it is not rejected by the flat law.
The vector-straight knee parameter is k_straight=arg(B2)-arg(B1), about
-7.993686832 degrees for the +X knee; it lies inside [-131,147]. A stored
knee angle of zero means the rest geometry, not necessarily collinear links.

At a stance sagittal offset s, Q=P+(0,0,s), the flat restriction tests

    (H_y-A_y)^2+(H_z-A_z+s)^2 <= (l1+l2)^2.

It only accepts s in [-0.268014393,0.172516620] wu, whereas the requested
stance traverses +/-2.157457908 wu. That is the source of its many misses;
hyperextension permission cannot enlarge a radius fixed by this extra
orientation constraint. Most of those misses already solved through LBS
refinement. The largest original error occurs at right local stance phase
0.290909091, with ankle at its lower ROM bound -2.778738819 rad (-159.21 deg).
This differs from the brief's phase window; the log defines phase explicitly
as time since that leg's touchdown divided by T.

### 3. Free-frame inverse and closed-form flexion margin (S1, S3)

Keep all three hinges. Let phi=h+k+b be the full-frame orientation, U=Q-A,
B0=P-H, l0=|B0|, r=|U|. Instead of forcing phi=0, solve

    D=U-R(phi)B0 = R(phi1)B1+R(phi2)B2
    phi1=b+k, phi2=b.

The possible length rho=|D| must lie in the intersection

    rho_lo=max(|l1-l2|, |l0-r|)
    rho_hi=min(l1+l2, l0+r).

This interval is the complete planar three-vector geometric reach test
before ROM: nonempty iff max(0,2*max(l0,l1,l2)-(l0+l1+l2)) <= r <=
l0+l1+l2. Here the inner radius is zero. Positive interval width allows an
interior seed. Rather than choosing a knee bias, solve the explicit objective
of maximizing minimum **squared-radius slack** to both interval boundaries:

    rho^2 = (rho_lo^2+rho_hi^2)/2
    delta(Q) = acos((rho^2-l1^2-l2^2)/(2*l1*l2)).

The midpoint follows by equating the two slacks; it is not a fitted angle or
parameter sweep. Delta is the virtual-link flexion margin away from collinear
extension, not a new ROM parameter. The stored +X knee candidates are
k=k_straight +/- delta, with orientation/ROM decided by the full inverse.

For r>0, the two full-frame orientations are

    phi=arg(U)-arg(B0) +/- acos((r^2+l0^2-rho^2)/(2*r*l0)).

For each phi, solve the two branches of the earlier planar inverse using
the virtual rest point H+R(phi)(P-H). Recover

    h=phi-phi1, k=phi1-phi2, b=phi2.

Convert these signed +X angles to the stored axes, enumerate equivalent
theta+2*pi*n within each actual ROM, and reject inadmissible branches. There
are at most four geometric branches before equivalent-angle enumeration.
At r=0 the orientation is underdetermined; the implementation tries phi=0
and does NOT claim exhaustive ROM reachability there. The tested trajectory
does not require that degenerate branch.

**Continuous geometric margin:** throughout this candidate trajectory
r<=|P-A|+a < l0-|l1-l2|. (The pendulum arc displacement magnitude is at most
a for alpha<pi/2, as is the stance offset.) Put R=l1+l2. In this domain the
largest selected rho^2 occurs at r=R-l0 and equals l0^2+(R-l0)^2. Therefore

    delta >= acos((l0^2+(R-l0)^2-l1^2-l2^2)/(2*l1*l2))
          = 0.141938983 rad = 8.132504654 degrees.

At exact midstance the selected delta is 0.388681290 rad (22.269797521 deg).
Across the sampled stride its minimum is 0.173619618 rad. No skeleton bend
or root drop is required: **recommended skeleton delta = 0, root drop = 0**.
This bound is for the full-frame geometric seeds; it does not certify a
periodic joint path, an oriented LBS sole, continuous ROM admissibility, or
load-bearing dynamics after numerical refinement.

For comparison, a root drop d>0 would add +d to body-relative foot Y. Under
the OLD flat inverse it changes D_y to H_y-A_y+d, making its extension
inequality worse. If a flat virtual-link bend beta were externally required,
its condition would be

    (H_y-A_y+d)^2+(H_z-A_z+s)^2 <= l1^2+l2^2+2*l1*l2*cos(beta).

Thus an allowed d must obey the corresponding square-root bound; it is not
an arbitrary positive crouch amount. Applying conventional-chain crouch
intuition to this reverse product would change the wrong geometric quantity.
No such target or height modification is used by the recommended fix.

### 4. Numerical refinement and the asymmetric history (S3, S4)

Each geometric seed is checked through imported `gait_mirror.frames`;
the worst rigid seed residual is 4.866020254e-15 wu. At least two
ROM-admissible free-frame seeds exist at every sampled target on each side.
Then the actual JNT3 sole-centroid law, with the same weights and second-owner
frames, is solved by bounded Gauss-Newton. This retains the real LBS model,
not a substituted two-link endpoint.

An additional equal-phase control exposed the inherited normal-equation
solver throwing `LinAlgError: Singular matrix` after damping shrank toward
roundoff at a nearly solved redundant pose. The correction in this probe
(the original mirror is unchanged) stops at residual <=1e-10 wu and solves
the augmented least-squares system [J;sqrt(lambda)I], without forming J^T J.
Finite differences point inward at an upper ROM boundary. Iteration count,
initial damping and finite-difference increment retain the mirror's values.
The 1e-10 numerical threshold is many orders tighter than the 0.005 H gate.

Once several candidates meet numerical tolerance, choose the pose closest
to that side's previous pose, rather than preferring a meaningless 1e-15
residual improvement that jumps branches. This is a local continuity rule,
not a global periodic path solver. An initial minimum-residual-only trial
gave max error 9.288e-14 and zero pose-return residual; that attractive return
was not accepted as proof of continuous motion. The final continuity-aware
implementation reports its remaining joint/pose discontinuities explicitly.

The old probe had separate `previous['L']` and `previous['R']` states. R did
not inherit L's solution: it started half a stride away, so its optimization
history was different. With synchronized local phases and equal initial
warm starts, the baseline mirrored-position difference is 1.869e-8 wu and
angle difference 7.356e-9 rad. The corrected equivalents are 1.869e-8 wu and
7.349e-9 rad. This refutes a material spatial flexion-budget asymmetry in the
committed pack; history-dependent local minima explain the original result
without changing the body.

Also, `max_full_frame_tilt` computes max |h+k+b| = max |theta_hip+
theta_knee-theta_ankle| here, **not** sum |q_i|. It is an unwrapped net
full-frame angle, not a hip-contamination measurement or an independently
defined rigid-sole tilt test. No weight defect follows from that statistic.

### 5. Measured verdict and remaining boundary

| Check | Original flat-seed ablation | Recommended free-frame seed |
|---|---:|---:|
| Foot max, wu | 0.122037880750 | 9.873789293e-11 |
| Foot RMS, wu | 0.024728394083 | 2.182060552e-11 |
| Foot gate, 0.028078200 wu | FAIL | PASS |
| Full/subset FK discrepancy | 0 | 0 |
| Worst sampled joint change, rad | 2.686601588 | 2.381311797 |
| Pose-return discrepancy, wu | 0.296449956 | 0.297065513 |
| Clock scalar residual, s | 4.403e-12 | unchanged |
| Signed-axis/ROM gauge control, wu | 0 | 0 |

All six phase/side cohorts now meet the foot-position gate; the logs contain
their counts, max/RMS, worst phases and angles. Floating-point boundary
classification can put exact-endpoint samples in adjacent phase cohorts;
the endpoint positions are identical and all samples remain counted.

**The stance POSITION defect is closed on this sample grid. The walk is not
certified.** The local inverse still has joint jumps and nonperiodic pose
history; sole orientation/contact, driven swing, signed impulse limits,
lateral balance and full physical clock closure are still unproved. The
readiness command deliberately exits 2. No live-engine or referee process
was executed and no protected file was written.

Reproduce from repo root:

```bash
python tools/gait_capture.py --seed-law flat
python tools/gait_capture.py --require-ready
```

The first is the preserved ablation; the second uses the recommended law by
default. Logs: `agent_logs/astra/stance_closure_baseline.txt` and
`agent_logs/astra/stance_closure.txt`. The amended integration note specifies
engine-side clamp and referee propagation. No recommended ROM/axis changes
are needed for the committed pack; the general sign-swap rule is guarded by
measured axial parity instead of being applied by side name.
PRE-RUN CONTINUITY MEMBRANES (ASTRA)
D1 STATEMENT: the prior exact-residual filter can reject a continuous gate-valid local solution and jump to a remote seed; elbow changes, ROM contacts and seed changes must be counted separately.
PREDICTION: jumps correlate with inverse candidate replacement, not evidence of changed ROM.
FALSIFIER: log every large transition with old/new angles, virtual elbow sign, endpoint error, distance to ROM, and local-only refinement residual; unrelated jumps refute the classification.
D2 STATEMENT: fixing a redundant hip chart to its standing value reduces the actual reverse FK to U=R(b)[B2+R(k)(P-K)], a two-link inverse. Where its strict annulus and ROM hold, one unwrapped elbow branch gives continuous q and exact marker tracking. This is a testable candidate, NOT a promised global solution.
PREDICTION: a standing-connected chart may remove remote free-frame reseeding.
FALSIFIER: any annulus/ROM miss, branch sign loss, foot error >0.005H, or periodic winding incompatible with ROM refutes this chart on the requested path.
D3 STATEMENT: a cubic Hermite sagittal swing joining (-a,-vb) to (+a,-vb), with nonnegative quartic lift having zero endpoint slopes, removes the contact velocity mismatch. It needs active swing, not an unforced pendulum.
PREDICTION: analytic relative endpoint velocities agree with stance within 1e-9 wu/s.
FALSIFIER: endpoint position/velocity mismatch, negative clearance or actual inverse foot error above gate.
D4 STATEMENT: a first swing of duration T/2 with its own boundary data can close at the midpoint-impulse orbit's first exchange; the old deficit is a reuse-of-full-swing-duration defect, not a proof of insufficient impulse.
PREDICTION: time closure exactly zero under specified active swing, COM J/m=vc unchanged.
FALSIFIER: first contact state differs from (a,vb), active swing misses boundary, or estimated impulse is called an actuator-budget certification without mass/force data.
D5 STATEMENT: proposed visual interpolation bound follows a Cartesian error allowance and a bound on FK second derivatives; it is not a measured perceptual limit. At 60 Hz the actual frame intervals and cyclic seam must satisfy it. Coordinator ratification is still required.
PREDICTION: a smooth branch may meet this finite bound without increasing cadence or inserting hidden frames.
FALSIFIER: any real 60 Hz frame exceeds the derived bound, or proof assumes that merely subdividing offline steps changes render-time jumps.

### Continuity refinement, declared before the production probe

**STATEMENT:** choose the ankle's physical angle b=-arg(K-A) in the YZ plane,
so its virtual link is vertical upward. The remaining inverse is
`Q-Kstar=R(b+k)[B1+R(h)B0]`, with Kstar=A+(0,l2,0),
B1=H-K and B0=P-H. Keep the elbow sign selected nearest the standing pose.
Set `c=(l2-(P-A)_y-(l0-l1))/2`: equal retained inner-annulus margin and lift.
This is a NEW, very low-clearance active swing; the old pendulum clearance is
not preserved. Do not claim it certifies sole contact or practical walking.

**PREDICTION:** the fixed-ankle section admits the stance and an active swing
with bounded endpoint overshoot; both sides share one periodic branch. The
full JNT3 centroid differs slightly from the full-frame analytic marker, but
an explicit weighted Rodrigues bound keeps this difference below 0.005H.

**FALSIFIER:** any missing branch representative, out-of-ROM sample, tracked
foot error above 0.005H, cyclic joint mismatch, contact velocity mismatch above
1e-9 wu/s, or 60 Hz jump above the geometric frame bound rejects the candidate.
The frame bound uses only the TWO moving joints during this section; initial
preparation uses the three-joint bound. It is proposed for coordinator
ratification, not a perceptual fact. It must not be widened after the run.

**STATEMENT:** solve the ROM boundary circles to obtain connected sagittal
reach. Half the minimum overshoot reserve beyond +/-a is d. Each swing has
constant-acceleration endpoint turns of duration 2d/|v_endpoint|, joined by the
unique cubic zero-end-speed translation of the remaining distance. A quartic
vertical lift has zero endpoint velocity. The first swing uses duration T/2
and initial relative velocity -vc, not the periodic swing's T and -vb.

**PREDICTION:** analytic and actual-FK one-sided contact velocities coincide,
startup reaches (a,vb) with J/m=vc after T/2, and time deficit is zero.

**FALSIFIER:** nonpositive remaining swing duration, ROM/foot/frame rejection,
startup boundary disagreement, or calling the required acceleration/impulse
an available actuator budget. The inherited T remains a conditional timing
reference; replacing passive swing with active swing does not derive a unique
physical clock.

### K3 refinement: finite-force startup (pre-run)

**STATEMENT:** under `x''=omega^2*x+u`, starting at (0,0), the unique constant
specific force that reaches the periodic exchange in one full T is
`u=omega^2*a/(cosh(omega*T)-1)=E/a`. Then
`x=u/omega^2*(cosh(omega*t)-1)`, `v=u/omega*sinh(omega*t)`.
The first swing uses T, relative start speed 0 and terminal speed -vb.
The earlier half-period driven candidate remains a comparison, not the
recommended startup: finite forcing also closes the joint velocity at rest.

**PREDICTION:** (x(T),v(T))=(a,vb); integrated specific impulse is u*T,
energy injected is u*a=E, the first swing ends simultaneously, and its
initial joint velocity is zero after preparation. No instantaneous COM or
joint-velocity jump is needed by this entry model.

**FALSIFIER:** independent RK4 of the forced equation misses the boundary by
more than 1e-8, the energy/impulse ledger fails, initial or terminal target
velocity disagrees, or the required u is presented as available authority.
The engine must supply a horizontal actuator/contact law admitting u; the
pack contains no such budget. Normal force/friction and torque remain gates.

### Continuity verdict and law of record

The full derived continuation and finite-force startup are in
[`THE_CONTINUITY_LAW.md`](THE_CONTINUITY_LAW.md). Measured actual-60-Hz jump
max/RMS = 0.095247312/0.024130364 rad, proposed bound 0.116378172 rad.
One-stride foot max/RMS = 9.542360332e-5/5.643409958e-5 wu. Nominal velocity
jump = 6.875e-15 wu/s; startup state closure = 4.441e-16; timing deficit = 0.
Finite startup requires u=0.806343648 wu/s^2 for T, not an instantaneous
midpoint impulse. Its work injects E; subsequent nominal exchanges conserve E.

This success uses a newly derived **0.001928210330 wu proxy lift** and active
endpoint turns; it does not certify the old pendulum swing height or available
actuation. Full integration remains CLOSED. The detailed document preserves
the unsuccessful attempts and the distinction between a geometric frame
bound and perceptual ratification. The old pointwise/free-frame results above
remain valid history and reproducible ablations.
