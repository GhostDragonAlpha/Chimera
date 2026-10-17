# AP01: asymmetric rail-port membrane

Prediction: the existing constant-gamma current-area law gives a reproducible,
convex scalar port response for a convex planar rim and a centre constrained to
its normal rail. A table of that response can balance two connected pieces and
be reused inside two different three-piece assemblies within declared error.

Falsifiers: analytical/triangle reference disagreement; GPU force or energy
mismatch; hidden out-of-domain evaluation; unbalanced joined port; stale artifact
accepted; or held-out response/reuse error exceeding the frozen limits below.

Scope: metres, joules and newtons; gamma=1 J/m^2 for characterization, zero-gamma
control; scale 0.5, 1, 2 m; normalized port height [-0.4,0.4]. Quasistatic prescribed
boundary response. Supports and the rail are explicit external constraints. No
mass, dynamics, contact, damage, finite-area attachment or biological claims.

Numerical limits fixed before experiments (not material qualification limits):
CPU energy/force analytic agreement 2e-11 normalized; f32 Vulkan parity 3e-5
normalized; table energy and force error 5e-4 normalized; assembled displacement
error 2e-4 m; reduced-assembly error 5e-4 m; detailed scalar solve residual 1e-10 N.
Normalization uses gamma*scale^2 for energy and gamma*scale for force, with a
unit denominator for zero-gamma controls. GPU inputs are compared with their exact
float32-to-float64 promotion. CPU tolerances allow roundoff; GPU budget is based
on the existing small-fan probe's 2.5e-5 N complete-force budget with normalized
coordinate scaling. Approximation budgets are explicitly numerical prototype
requirements and do not establish gameplay or material validity.

65 training heights per geometry. Held-out off-grid heights from independent
fixed RNG seeds, plus unseen physical scales, verify interpolation and similarity.
No geometry-generalization claim: each geometry has its own table. 3 deterministic
geometry candidates. Table only in AP01; Noether training is not needed to prove
this composition seam and is not claimed. One frozen trial configuration, no
post-observation tolerance widening. Native/GPU memory bounded by 32768 vertices;
all candidate cases run under one existing managed GPU reservation. Final-check
implementation recomputes analytic responses and assembled energy independently.

The packet implements part of S0-S4 in an isolated research harness. A general
multiport kernel, runtime save/pick/inspector integration, controller attestation
and S5 remain open. No controller session is provisioned. Reference/implementation
source hashes and build identities must accompany evidence. Worker-authored PASS
is a local numerical result, not independent authority to release the engine.
