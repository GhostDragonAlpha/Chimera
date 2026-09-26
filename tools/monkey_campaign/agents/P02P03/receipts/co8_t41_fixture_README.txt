[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] # THE TICK-41 REGRESSION FIXTURE (permanent; Astra launch-sequence step 1)
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] 
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] THE SIGNATURE: the GPU build refuses at tick 41, rc=5 (gait_row_budget,
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] class 5), refused=1, adv=2, ticks=40; the host replay walks on (no refusal);
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] the states are BIT-IDENTICAL through tick 40 on the walk config
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] (reflex_level=1, block=32, E=1).
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] 
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] THE COMPLETE PRE-STEP STATE: state_t40_host.txt (host replay FULL t=40) ==
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] state_t40_gpu.txt (GPU DLL FULL t=40) byte-identical; the C++ reference's
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] aligned state is state_t39_cpp.txt (FULL t=39 == host t=40; the C++ FULL
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] index is offset by one). Scene: scene_sha256.txt.
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] 
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] THE ATTRIBUTION (frozen, closeout-8): the refusal fires inside the FIRST
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] BISECTION ADVANCE (ADV n=207, depth=2, h=5.2083256182402707e-05) of the
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] khit=0 hind-left pad crossing (hit=6.9340587375064531e-05). The device's
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] ADV n=0..205 lines are bit-identical to the host's. At n=207 the IMPE gaps
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] are bit-identical (g0=-6.9388939039072284e-18 -- the near-zero contact
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] residual knife; g2=2.0861058498689022e-07; g3=2.4677093701797048e-11) and
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] the IMPF rows r=0/2/3 are bit-identical (mode/ln/lt/caught). The host's
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] project_rows enumeration SUCCEEDS with R=3 (m0=0.00066410384680204437,
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] m2=1.0687132770298861e-05); the device's enumeration exhausts the row
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] budget. host_drill_t41.out (cl host replay, 82 ADV lines) and
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] device_drill_t41.out (30 ADV lines before the refusal) are the evidence.
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] 
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] REPRODUCE: `python diag_dll_walk.py 45` (GPU) vs `HL_FULL=1 ./host_loop.exe`
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] (host) on the scene at scene_sha256.txt; diff_trace.py cp hl 1.
[co8_t41_fixture/README.md @ typeb-gpu-finish a62b286e] Trailer: Agent: GLM 5.3
