# Reset must report one coherent accepted state

Observed during scheduler verification: Reset restored iteration, accepted
positions and energy, but its reported center force still matched a preceding
step. Source inspection locates the status cache in `md_last_vf_centre_`:
the reset branch evaluates the GPU force buffer but does not refresh that cache.

STATEMENT: after Reset, reported positions, gamma, energy and center force all
describe the restored accepted state, rather than mixing different revisions.
PREDICTION: initialize the frozen B2 fixture, record its status, admit gamma 0,
then Reset. The reset position, initial gamma, energy and all force components
equal the corresponding initialization outputs. A step followed by Reset has
the same result. The fixed-order GPU evaluation receives identical uploaded
geometry/material/topology, so this metamorphic test predicts exact equality
of the serialized outputs; it does not introduce a new numerical tolerance.
FALSIFIER: any mismatch, failed response, nonfinite result, or reset status
reporting success after a failed evaluation. Run the old executable first and
retain that failure, then rebuild in the private build path and repeat.

The existing 20-PASS/1-INFO frozen runtime gate remains unchanged and must still
pass after the repair. This adds an accepted-state consistency test; it does
not replace the f64 reference oracle, certify performance, or infer physics
from a picture. No protected build files or operator process are touched.

## Gate negative controls

These controls are preregistered for the CPU-only fake-request regression test
at `test_reset_gate.py`; they do not contact or launch the engine.

STATEMENT: the metamorphic gate must demonstrate that each named control took
effect before judging whether Reset restored the initial state.
PREDICTION: a fake endpoint that returns the initialization status for every
control, a gamma-zero response with nonzero gamma/energy/force, a step response
whose iteration advances without changing the accepted ID or centre, and a
status with a non-three-component force vector each cause a nonzero exit and a
`passed: false` result. A valid fake sequence must retain two PASS checks.
FALSIFIER: any negative control exits zero or records `passed: true`, or the
valid sequence fails. The test uses finite B2-shaped values and writes only to
temporary output directories.

The strict-schema negative control also includes a boolean and a nonfinite
centre component; both must be rejected as non-JSON-number status values.
