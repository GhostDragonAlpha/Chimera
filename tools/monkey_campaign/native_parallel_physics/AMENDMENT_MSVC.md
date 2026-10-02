# Production-family compiler check, 2026-10-02 UTC

The GNU 15.2 sealed full suite passed on job
`cbcfb74c299f41259eb8914a355de751`, including 3000 ticks in each of seven
configurations and exact original/candidate parity for 1/2/4 workers.

Before the additional run, extend only the test driver to support the installed
MSVC toolchain. Use C++17, /O2, /EHsc and /fp:precise; the latter matches the existing
`ChimeraEngine/engine/tests_coupled_arm/CMakeLists.txt` policy. Physics source and
test thresholds remain unchanged. Compare baseline and candidate bytes WITHIN
this backend, not against GNU bytes. No cross-compiler bit-identity claim is made.

Prediction/falsifier remain the original preregistration: exact within-backend
values and trajectories, retained analytic/reference/control checks, deterministic
executor behavior and bounded energy residuals. Any compile, reference or byte
comparison failure remains a recorded failure; do not change physics parameters,
precision or tolerances to make it pass. Compiler-environment discovery is local
only; retain compiler identity and build commands, never environment secrets.
