# Embedded HTTP lifecycle guardrails

Task `engine-http-lifecycle-01` (generation 1), base `cde18631e43ee684bc2851d0e2bcdb09d12d99d6`.

## Scope

- Embedded C++ implementation: source-level HTTP transport files under ChimeraEngine/engine
- Evidence bundle: docs/evidence/engine_http_lifecycle

## Contract

The HTTP listener must stop safely when it owns no new external traffic and even when a single client is mid-read.

- Preserve IPv4 loopback bind and public API.
- Avoid deadlock in `stop()` under a quiet listener or partially-read client.
- Preserve startup failure behavior and avoid leaked listener/worker states.
- Keep changes limited to this task scope.

## Contract text (extracted from packet)

`HttpServer::stop()` must make a running Winsock listener and any accepted connection leave their blocking operations, then join the worker and release Winsock exactly once.

`start` and `stop` must handle repeated lifecycle calls without leaks or races.

The regression cases (quiet listener, partial request, repeated start/stop, startup port-occupied failure) must remain isolated to this task and be verified with a private CPU harness.

## Generation 2 correction (2026-09-10)

The first candidate still closed the listener and accepted client from `stop()` while the worker could be in `accept`, `recv`, or `send`. The corrected implementation gives the worker exclusive ownership of both listener and client handles. It sets them nonblocking, waits with `select()` while observing the atomic cancellation flag, and closes each local handle only after leaving its Winsock calls. `stop()` stores cancellation, joins, clears the member handle, and calls `WSACleanup()` once for the matching successful `WSAStartup()`.

`SO_EXCLUSIVEADDRUSE` protects the loopback endpoint from a second server instance, making an occupied-port startup failure deterministic. The public destructor calls `stop()` for scope teardown. A finite callback drain and a blocked response-send control are part of the CPU evidence. Whole-engine shutdown remains a separate lifecycle problem because an arbitrary callback, including boot restore code, may outlive the socket worker.
