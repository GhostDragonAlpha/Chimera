# CPU listener harness results — generation 1

## Identity

- Tested source checkout: `513724db295a893f3f57e2b10d3972c34be1f114` on `astra/tasks/engine-local-control-01` at harness setup.
- The source diff under test changes `addr.sin_addr.s_addr` from `INADDR_ANY` to `htonl(INADDR_LOOPBACK)` in `ChimeraEngine/engine/http_server.cpp`; the header comment records loopback-only intent. See `source_diff.txt` and `source_binary_hashes.json`.
- The harness was built from the actual repository `http_server.cpp` and `http_server.hpp` with no Vulkan or engine sources. Build output is in `configure_mingw_fresh.txt` and `build_mingw_fresh.txt`.

## Result

- **Local GET:** PASS. `GET /health` returned `HTTP/1.1 200 OK` and the handler observed `GET` and `/health`.
- **Local POST:** PASS. `POST /control` with body `{"probe":true}` returned `HTTP/1.1 200 OK` and the handler observed `POST` and `/control` with the body.
- **Listener address:** PASS. `Get-NetTCPConnection` reported `127.0.0.1:49173`, state `Listen`, owned by the verified harness PID 31672.
- **Non-loopback probes:** the two local interface addresses `192.168.3.169` and `172.23.64.1` did not connect, but both returned a 0.8 second socket `TIMEOUT`, not `ConnectionRefusedError`. Therefore the strict “connection refused” predicate is **not passed** in this Windows environment. The result is compatible with a host firewall dropping the packet; no firewall setting or rule was inspected or changed.
- **Process/window observation:** the fresh harness process path was verified as `.tmp/engine_local_control_gen1/build_mingw/engine_local_control_harness.exe`, with no main window title. No `PickerHost` process or window was observed in the recorded launch snapshot. This is an observation only and makes no universal no-popup claim.
- **Cleanup:** after all probes, PID 31672 was path-verified and terminated with `Stop-Process -Force`; a follow-up lookup confirmed it was gone. The harness never called `HttpServer::stop()`.

The local-only listener and local GET/POST behavior are reproduced. The requested non-loopback *refusal* could not be established because both probes timed out; retain that limitation in the gate record rather than calling the full prediction green.

The durable evidence directory also contains the exact harness source, probe source, and private CMake file (`harness.cpp`, `probe.py`, `CMakeLists.txt`) plus `evidence_hashes.json`; `.tmp` is only the build/run workspace.
