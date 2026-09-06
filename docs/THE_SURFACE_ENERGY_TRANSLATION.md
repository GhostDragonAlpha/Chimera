# The surface-energy translation

2026-09-06, ASTRA. Specification for the first executable reference stage of Alan's
approved cup-and-water proposal. Implementation is delegated to G01. No reference code
or numerical tests have been run by ASTRA in this architecture session.
This specifies an offline derivation bench, not a Python runtime or a certified cup simulation.

## Statement

For nondegenerate triangles with constant, nonnegative interfacial energy density gamma,
the current-area energy U = sum_t gamma_t A_t has conservative vertex forces obtained
from its exact geometric derivative. These forces are objective under rigid motion,
balance internal force and torque, and reproduce the spherical capillary pressure
under mesh refinement. The same geometry supplies rendering; no second pose is authored.

## Derivation and distinction from existing code

For a triangle (a,b,c), let n = ((b-a) cross (c-a))/|(b-a) cross (c-a)|.
Then grad_a A = (b-c) cross n / 2, with cyclic permutations for b and c.
Face-corner force is -gamma grad A; sum incident corners into each vertex.
The normal is recomputed from CURRENT geometry on every evaluation. A frozen import
normal is a different projected-area law. The reference does not silently redefine
`tools/ca_triangle.py`'s rest-area/strain experiments.

For a sphere U=4*pi*gamma*R² and V=4*pi*R³/3, so dU/dV=2*gamma/R.
For a discrete closed surface under uniform scaling, the generalized pressure is
`-sum_i(F_i dot x_i)/(3V)`. This scalar radial-work test is not proof of local pressure
balance, dynamics, or a solved drop.

Area is insufficient for solids: diag(2,1/2) preserves area but changes the in-plane
metric from I to diag(4,1/4). Expose the rest-to-current metric in the reference so
the missing shear information is explicit; do not invent a solid modulus.

Literature: [Young–Laplace](https://farside.ph.utexas.edu/teaching/336L/Fluidhtml/node41.html)
and [Discrete Shells](https://multires-1.cms.caltech.edu/pubs/ds.pdf). The latter motivates
separate membrane and bending responses, neither implemented in this first port.

## Predictions and falsifiers, registered before implementation and execution

Fixtures use dimensionless unit gamma and radius; these are analytic controls, not
water or cup material calibration. Double-precision epsilon is e. For well-conditioned
O(1) fixtures, central differences use h=e^(1/3), balancing O(h²) truncation and O(e/h)
cancellation. Error limit is 256*e^(2/3), a preregistered numerical allowance (not a
rigorous bound for arbitrary geometry). Algebraic invariance limit is 512*e.

1. Force versus independent Heron-area finite differences: normalized max error <=
   256*e^(2/3). Any breach falsifies derivative implementation on the fixture.
2. Rigid rotation/translation, force/torque balance, zero-gamma identity and gamma
   scaling: normalized errors <=512*e. A breach falsifies the relevant invariance.
3. Negative controls: force sign reversal, zero forces, a spurious force on one vertex,
   and a frozen-normal derivative after a 90-degree rotation must each fail the check
   they attack. A surviving mutation falsifies the instrument.
4. Refined unit octahedra at levels 0 through 4: generalized pressure error versus
   2*gamma/R strictly decreases and is <=1% at level 4. The 1% target is a proposed
   discretization gate inherited from the triangle carrier's numerical regime, not
   a material constant or an engine-wide certification. No fitting to select a level.
5. Equal-area distortion: area ratio exactly 1 within 512*e; metric diag(4,1/4)
   within that allowance. Failure invalidates the translation counterexample implementation.
6. A prescribed two-second, 60-sample/s moving surface (121 endpoints): force/energy
   agreement holds at every sample under the same derivative limit. This is a moving
   input control, not an integrated simulation or a live-render claim.
7. Reject malformed indices, nonfinite data, negative/nonfinite gamma, empty faces,
   repeated-vertex and collapsed triangles. Near-degenerate cross-product magnitude
   <=64*e*max_squared_edge is refused as outside the numerical domain. The reference
   never silently drops a face or creates zero force to hide invalid geometry.

## Integration contract

CPU setup supplies validated topology, vertex-to-corner CSR adjacency, material gamma,
units, and the model scope. GPU stage A reads current positions and writes one force
per face corner plus face energy and a validity flag. GPU stage B gathers each vertex's
incident corners in fixed CSR order, avoiding racing floating-point scatter atomics.
The existing force accumulation/integrator consumes that contribution exactly once.
Use compute-write/read barriers between stages. Rendering reads the resulting accepted
state after the appropriate compute/vertex-input barrier. Invalid geometry closes the
step gate: retain the last valid state and report the cause; do not draw a repaired pose.

Constant gamma here is held fixed during the derivative. Spatial/material evolution of
gamma, wetting, contact and bulk pressure require explicit additional laws. Open-patch
boundary forces are real boundary traction and must couple to the other phase/support.
Do not apply a free-surface energy to every interior solid triangle by default.

This port supplies conservative forces, not damping, a timestep, remeshing, collision
handling, or a guarantee of equilibrium. GPU port and runtime integration follow an
independent float64 reference and require measured GPU agreement and a live movie.

## Audit findings and ideas to pursue

Inspected base: `2b440b29bbd885dd14a4a287a3cf14b6cedf4eba`, local branch
`astra/gait-capture`. User branch/protected-build restrictions outrank the older manual's
master-commit convention. No protected build files or live processes are touched.

- `engine.cpp` records `steps_per_frame` water macro steps each rendered frame. Holding
  this and dt fixed makes simulation speed proportional to render FPS. Proposal: an
  explicit simulation-time accumulator and deterministic tick-indexed input events.
  Slow-motion/movie playback should be an explicit time mapping, not incidental GPU load.
- `water_color.comp` uses max(1,floor(dt_macro/dt_ij)) substeps of dt_ij. Their total
  can undershoot or overshoot dt_macro. For positive admissible bound b and interval T,
  n=ceil(T/b), h=T/n closes time exactly with h<=b (up to rounding). This alone does not
  prove the hydrodynamic CFL bound; that must be re-derived for changing depths.
- The cited `.tmp/tri_water.py` CPU reference is absent in this checkout. Reconstructing
  it from a shader would supply a mirror, not an independent physics reference.
- `water_occ.comp` clears occupied volume; any new occupancy over water needs transfer
  or an explicit sink ledger. Never equate a visible sealed surface with conserved water.
- Water display offsets each substrate face along its own normal. Arbitrary 3D cups,
  moving walls, and free droplets need a bulk/free-surface representation decision.
- New idea: a common conservation ledger per simulation tick (mass, momentum, energy,
  input work, dissipated heat) can make the movie inspectable and replayable. Checkpoint
  plus seed/input log is a candidate, not a demonstrated cross-device replay guarantee.
- New idea: choose spatial/temporal detail from BOTH physical error and visibility.
  Off-camera or subpixel interactions still need resolution when they affect observable
  loads or motion. Perceptual limits cannot alone decide which physics is discarded.

Measured results will be appended after the run. No live integration is claimed here.
