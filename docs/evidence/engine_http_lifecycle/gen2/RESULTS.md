# HTTP lifecycle gen2 results

HEAD before source work: `153f7a8863747a3d8429da158443076896c9be0c` (expected candidate; source was then edited in this worktree).
Baseline source: `7616771cdc15ccfb2dd0297b6961bc0bedfea400`, copied with `git show` into `.tmp/engine_http_lifecycle_gen2/baseline_source/`.

## Baseline negative controls

The private MinGW harness was built from the exact baseline source and run with a 3 second watchdog. Every process printed its scheduling witness (`BEFORE_STOP ...`) and then had to be killed by the verified executable path because `stop()` did not return:

- `quiet`: `WATCHDOG_KILLED`; stdout retained in `baseline/quiet.stdout.txt`.
- `partial_header`: `WATCHDOG_KILLED`; stdout retained in `baseline/partial_header.stdout.txt`.
- `partial_body`: `WATCHDOG_KILLED`; stdout retained in `baseline/partial_body.stdout.txt`.

The watchdog used `Get-CimInstance Win32_Process` to compare the PID executable path before `Stop-Process -Force`. No unrelated process was touched.

## Fixed controls

Built with CMake MinGW Makefiles from the current `ChimeraEngine/engine/http_server.cpp` and `.hpp`. The same harness returned exit code 0 for every mode:

- `quiet`: `STOP_RETURN quiet ms=15`.
- `partial_header`: `STOP_RETURN partial_header ms=16`.
- `partial_body`: `STOP_RETURN partial_body ms=16`.
- `local`: `LOCAL_GET PASS`, `LOCAL_POST PASS`.
- `blocked_send`: `entered=yes stop_ms=31` after a 64 MiB response and a 1 KiB client receive buffer.
- `finite_callback`: `entered=yes released=yes joined=yes before_release_joinable=yes`.
- `cycles`: five `CYCLE n PASS` results.
- `start_failure`: `OCCUPIED_SECOND_START EXPECTED_FAILURE`, `RESTART_AFTER_FAILURE PASS`.
- `destructor`: `DESTRUCTOR_RETURN PASS`.

Raw fixed output and build metadata are retained in this directory. The controls establish socket-worker lifecycle behavior only. They do not establish orderly whole-engine shutdown: `main.cpp` still owns callback/boot-restore ordering, and an arbitrary callback may not be cancelled by this class.

After the readiness retry correction, the complete fixed matrix was rebuilt and rerun; the second raw capture is under `fixed_v2/`. All nine modes again returned exit code 0. This is the source state represented by `source_hashes.txt`.
