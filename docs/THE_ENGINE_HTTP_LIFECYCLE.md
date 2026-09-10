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
