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
