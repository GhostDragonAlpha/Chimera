# AP02: two independent ports and finite-area coupling

Prediction: the existing constant-gamma current-area law supports a piece with
two independent rail ports whose reactions are cross-coupled through the shared
surface (moving one port changes the force measured at the other). A qualified
finite-area attachment between two rigid carriers transfers both force and
moment between ports, with exact equal-and-opposite wrench balance, and the
assembly equilibrium agrees with independent references within frozen limits.

Falsifiers: Heron/triangle energy or reaction disagreement; vanishing or
asymmetric cross stiffness; reduced quadratic response outside its declared
domain budget; equilibrium disagreeing with the independent conjugate-gradient
minimizer; joint wrench disagreeing with the energy gradient; broken wrench
balance across the joint; a collinear or collapsed patch accepted as a full
bond; hidden out-of-domain evaluation; stale artifact accepted.

Scope: metres, joules, newtons; gamma=1 J/m^2 for characterization; scale 0.5,
1, 2 m; enforced port gate is the recipe domain |h/scale| <= 0.4, and every
shipped case lies within |h/scale| <= 0.34. Quasistatic prescribed-boundary
response. Rims and the far carrier fixture are explicit external constraints.
No mass, dynamics, contact, damage, GPU batch, render binding or biological
claims. The finite-area joint uses the existing qualified CPU reference
(tools/finite_area_attachment) unchanged; carriers are rigid, joints between
carrier and fan port node are exact welds.

Patch admission is the reference module's own gates: assert_constrains_all_six
(numerical rank) and assert_min_couple_stiffness with the authored requirement
k_couple_min = 1e-3 N*m/rad (a design requirement for this fixture, not a
measured material value). Joint stiffness provenance: Kbar = kappa_areal *
A_patch with declared synthetic kappa_areal = 1e8 N/m^3 and the patch's
nominal area, checked by the module's provenance gate.

Numerical limits fixed before experiments (not material qualification limits):
detailed energy vs Heron reference 2e-11 normalized (gamma*scale^2); detailed
reaction vs Heron central-difference 1e-8 normalized (gamma*scale); cross
stiffness C_pq detailed-FD vs Heron second-difference 1e-6 normalized by gamma;
Hessian symmetry |C_pq - C_qp| <= 1e-6*gamma; coupling existence |C_pq| >=
0.05*min(K_pp,K_qq) at every sampled state (ports on one shared surface must
not behave as independent pieces); quadratic reduced response inside its
declared domain |h| <= 0.15*scale: normalized reaction and energy error <= 5e-3;
two-port equilibrium vs independent conjugate-gradient minimizer 2e-4 m;
detailed equilibrium residual 1e-10 N; joint wrench vs energy central-difference
1e-6 relative to the larger of the largest generalized-force term and
Kbar*max(delta, patch_radius*|phi|) (generalized forces vanish physically for
some prescribed poses, and zero must not divide FD noise); loaded-port equilibrium
residual 1e-9 N and 1e-9 N*m checked per unit (the Newton solve uses the
reference module's analytic wrenches, so no finite-difference noise floor
applies); cross-joint wrench balance (equal and opposite) and carrier balance
1e-12 relative to the largest force/torque term involved (float64 summation of
kilonewton-scale terms cannot support an absolute 1e-12). Transfer existence
gates (authored, fixed before measurement): a prescribed port displacement
delta must produce |F_b| >= 0.25*Kbar*delta, and a prescribed port rotation
phi must produce |tau_b| >= 0.25*lambda_min_couple*|phi| — a patch that
transfers neither is not a coupling.
Normalization uses gamma*scale^2 for energy, gamma*scale for force, gamma for
stiffness. Approximation budgets are explicitly numerical prototype
requirements and do not establish gameplay or material validity.

Representation decision fixed in advance: the two-port response keeps the
detailed solve as authoritative. A measured quadratic (linear-stiffness)
reduced model is admitted only inside its declared domain and only if its
measured error stays under the frozen budget; a rejected fit leaves the
detailed path available. Domain selection is characterization, not tolerance
widening: the 5e-3 budget was frozen first, and the declared domain is the
largest radius on the frozen 11x11 grid meeting it for every shipped recipe
(0.02 normalized; the initially proposed 0.15 radius measured 8.2e-2 worst
reaction error and 0.03 measured 5.9e-3 on recipe ap02_1 — both recorded as
rejected reductions). No 2-D table and no Noether fit is claimed here.

Three deterministic two-port recipes (seeds 0..2) and one deterministic
carrier/patch family. One frozen trial configuration, no post-observation
tolerance widening. The final check recomputes Heron energies, cross
stiffnesses, equilibria and joint wrenches independently of the runner.
Worker-authored PASS is a local numerical result, not independent authority
to release the engine. General multiport kernels, runtime save/pick/inspector
integration, render-state repair, controller attestation and S5 remain open.
