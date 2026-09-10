# Embedded HTTP lifecycle — generation 1

Commit under test before implementation: `7616771cdc15ccfb2dd0297b6961bc0bedfea400` (`astra/tasks/engine-http-lifecycle-01`).

## Theory

**STATEMENT:** `HttpServer::stop()` must make a running Winsock listener and any accepted connection leave their blocking operations, then join the worker and release Winsock exactly once; repeated start/stop and startup failure paths must not leak a listener or leave a worker behind.

**PREDICTION:** The pre-fix actual-source CPU harness will hang in `stop()` with a quiet listener and with a client blocked in partial-header/body receive. After the smallest ownership/cancellation repair, the same harness will complete quiet stop, partial-request stop, local GET/POST, repeated cycles, and occupied-port startup failure within bounded watchdog times.

**FALSIFIER:** Any post-fix stop that exceeds the watchdog, any accepted connection that keeps the worker from joining, any second start that steals or corrupts the first listener, any startup failure that leaves a bound port or unbalanced Winsock state, or any failed local GET/POST falsifies the statement. The pre-fix hangs are retained as failures and are not converted into passes.

## Derived cancellation contract

The listener socket is the worker's owned blocking resource. `stop()` first publishes cancellation, then performs `shutdown(SD_BOTH)` and `closesocket()` on that listener handle to wake `accept()`, and joins the worker before releasing the lifecycle state. The worker keeps a local copy of the accepted listening handle so it never races the `sock_` field. Each accepted client is also closed on every exit path, and cancellation is checked before invoking the request handler.

A lifecycle mutex serializes `start()` and `stop()`; a second `start()` while active fails. Startup failure paths close any created socket and call `WSACleanup()` after a successful `WSAStartup()`. The existing IPv4 loopback bind remains unchanged.

## Test scope

The harness compiles only the actual `http_server.cpp/.hpp` plus a small test driver, with no Vulkan or engine sources. It runs in a fresh `.tmp` executable path. Baseline watchdog kills only the verified harness PID when the known pre-fix stop hangs. No engine, GPU, firewall, or unrelated process is touched.
