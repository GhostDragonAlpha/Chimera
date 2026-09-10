# HTTP lifecycle gen2 preregistration

## Statement
`HttpServer::stop()` can cancel a quiet listener, a partial header/body receive, or a blocked response send by publishing cancellation and joining one worker that owns every Winsock handle. Repeated start/stop, occupied-port startup failure, and destructor shutdown therefore complete without another thread calling `closesocket` on a handle in use.

## Prediction
The exact pre-fix source at `7616771cdc15ccfb2dd0297b6961bc0bedfea400` will remain hung in the warm quiet, partial-header, and partial-body controls until an external watchdog kills each process. The current source will return from each of those controls promptly and will pass local GET/POST, blocked-send, finite-callback drain, repeated cycles, occupied-port failure/restart, and destructor controls.

## Falsifiers
This theory fails if any baseline control returns without the watchdog witness, if any fixed control exceeds the process watchdog, if a fixed blocked send cannot join after cancellation, if a finite callback is detached or skipped before release, if a second server binds the occupied endpoint, or if a restart after the failed bind cannot start.

## Derived design
The worker sets listener and accepted sockets nonblocking and uses `select()` with a 50 ms cancellation poll. `stop()` only stores `false`, joins the worker, and then releases Winsock. The worker closes its local listener/client handles after it leaves Winsock calls. The finite callback control is deliberately bounded; arbitrary engine callback cancellation and whole-engine teardown remain outside this socket contract.

## Run boundary
Preregistered for generation 2 before fresh runs. Baseline files are reconstructed privately from the exact 7616771c tree and are never copied over historical evidence. Fixed files use the current dirty source at test time. All builds and processes are CPU-only private harnesses.
The receive loops retry only `WSAEWOULDBLOCK` and `WSAEINTR` after readiness; connection reset/other errors terminate that request. The 50 ms `select()` interval is a cancellation polling policy and is not a claim about physical-time or engine-performance guarantees.
