# Engine local-control listener evidence — generation 1

Commit under test: `513724db295a893f3f57e2b10d3972c34be1f114`
Branch: `astra/tasks/engine-local-control-01`
Source under test: `ChimeraEngine/engine/http_server.cpp` and `http_server.hpp`.

## Preregistration

**STATEMENT:** The embedded engine HTTP control server must accept local IPv4 requests while binding only to IPv4 loopback, so it does not expose the engine control API on LAN interfaces.

**PREDICTION:** A fresh no-Vulkan executable built against the actual `http_server.cpp` will answer positive GET and POST requests through `127.0.0.1`, its listener will report `127.0.0.1:<port>`, and a connection to the host's non-loopback IPv4 address on the same port will be refused.

**FALSIFIER:** Any positive non-loopback connection, any listener address other than `127.0.0.1`, or failure of either local GET or POST request falsifies the statement. A timeout instead of refusal on the non-loopback probe is recorded as an environment-dependent failure and does not count as a refusal.

## Scope and controls

The harness uses the repository's actual `ChimeraEngine/engine/http_server.cpp` and `http_server.hpp`, with a fresh executable path in `.tmp/engine_local_control_gen1`. It does not include Vulkan or engine sources. The harness never calls `HttpServer::stop()` because the existing join-before-close path is outside this task; the verified harness PID is terminated after probes.

No firewall rules/settings or Security UI are changed. Any observed new `PickerHost` process/window is recorded if present; this evidence makes no claim that an OS firewall prompt can never appear.
