# Independent parent verification

Task `engine-http-lifecycle-01`, generation 2. Current source was independently
reviewed after the generation-1 candidate was rejected. The earlier candidate,
failed build attempts, baseline watchdog failures and original weak finite
callback check remain preserved; they are not acceptance evidence for this head.

Build commands (fresh private build directory):

```powershell
cmake -S E:\ChimeraWork\slot-03\docs\evidence\engine_http_lifecycle\gen2_review -B E:\ChimeraWork\slot-03\.tmp\engine_http_lifecycle_parent_review -G "MinGW Makefiles" -DCMAKE_CXX_COMPILER=C:/ProgramData/mingw64/mingw64/bin/c++.exe -DCMAKE_MAKE_PROGRAM=C:/ProgramData/mingw64/mingw64/bin/mingw32-make.exe
cmake --build E:\ChimeraWork\slot-03\.tmp\engine_http_lifecycle_parent_review -j2
```

GNU C++ 15.2.0 configured and compiled the actual server and committed harness.
Each mode in `results.json` ran in its own process with a 3000 ms watchdog,
stdout/stderr redirected to the adjacent mode files. All ten processes exited
0 before the watchdog; no termination was necessary. The port was checked free
before launch. `hashes.json` binds source, header and fresh executable bytes.

The corrected finite-callback gate observes callback exit and stop return
directly. A deliberately early-returning test double is rejected by that gate;
joinability alone is no longer used as completion evidence. Existing gen2
results using the weaker gate remain historical, superseded by `gen2_review`.

Independent source review found worker-owned sockets, serialized start/stop,
balanced Winsock cleanup and preserved IPv4 loopback binding. Cancellation
polling uses a declared transport policy, not simulated time or a performance
certificate. The caller must supply a finite, nonthrowing handler; arbitrary
handler cancellation is not provided. Whole-engine teardown order, callback
admission and detached boot restore remain `engine-shutdown-order-01`.

No engine window, GPU, DYAD, firewall policy or unrelated process was used.
