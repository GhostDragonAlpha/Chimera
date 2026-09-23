# THE TICK-41 REGRESSION FIXTURE (permanent; Astra launch-sequence step 1)

THE SIGNATURE: the GPU build refuses at tick 41, rc=5 (gait_row_budget,
class 5), refused=1, adv=2, ticks=40; the host replay walks on (no refusal);
the states are BIT-IDENTICAL through tick 40 on the walk config
(reflex_level=1, block=32, E=1).

THE COMPLETE PRE-STEP STATE: state_t40_host.txt (host replay FULL t=40) ==
state_t40_gpu.txt (GPU DLL FULL t=40) byte-identical; the C++ reference's
aligned state is state_t39_cpp.txt (FULL t=39 == host t=40; the C++ FULL
index is offset by one). Scene: scene_sha256.txt.

THE ATTRIBUTION (frozen, closeout-8): the refusal fires inside the FIRST
BISECTION ADVANCE (ADV n=207, depth=2, h=5.2083256182402707e-05) of the
khit=0 hind-left pad crossing (hit=6.9340587375064531e-05). The device's
ADV n=0..205 lines are bit-identical to the host's. At n=207 the IMPE gaps
are bit-identical (g0=-6.9388939039072284e-18 -- the near-zero contact
residual knife; g2=2.0861058498689022e-07; g3=2.4677093701797048e-11) and
the IMPF rows r=0/2/3 are bit-identical (mode/ln/lt/caught). The host's
project_rows enumeration SUCCEEDS with R=3 (m0=0.00066410384680204437,
m2=1.0687132770298861e-05); the device's enumeration exhausts the row
budget. host_drill_t41.out (cl host replay, 82 ADV lines) and
device_drill_t41.out (30 ADV lines before the refusal) are the evidence.

REPRODUCE: `python diag_dll_walk.py 45` (GPU) vs `HL_FULL=1 ./host_loop.exe`
(host) on the scene at scene_sha256.txt; diff_trace.py cp hl 1.
Trailer: Agent: GLM 5.3
