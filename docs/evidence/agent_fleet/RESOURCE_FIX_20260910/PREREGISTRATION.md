# Resource lifecycle repair — preregistration

Base: f2c4f7e850267f400ea3eb7441e7c67d7fdc4466 (production code unchanged from cf275281). Offline Linux only; no live registry migration, model unloading, engine control or GPU testing.

Statement: existing reservations cannot be overwritten; chained runtime reservations retain their GPU parent; memory summaries equal held allocations; resource field errors yield named refusals; requests that cannot grant immediately while retaining resources cannot create a pending hold-and-wait cycle.

Predictions before implementation: (1) GPU release/clear with retained engine_demo refuses, preserving state; (2) grouped grant on any already-held non-memory resource cannot replace its owner or class; (3) final memory release/clear updates admitted_mb; (4) missing/nonstring names produce JSON refusals with unchanged revision; (5) a contended grouped request from a holder terminates ungranted with release_required and keeps its resources, while a nonholder can queue and auto-promote after drain; (6) legacy chained acquisition checks its GPU parent; (7) existing compatible release/order and memory admission checks remain green.

No automatic preemption: client must drain/release then re-request the complete bundle. Persisted pre-repair hold-and-wait queues are marked terminal on next promotion, preserving held resources. This changes a formerly indefinite pending result into a named result; consumers must inspect served/granted/dropped_reason.

Falsifiers: any overwrite, leaked partial group, missing parent, stale memory total, transport disconnect on tested invalid types, retained contended pending request from a holder, or unrelated existing test regression. Positive control: nonholder queue auto-promotes after owner drains; holder can acquire immediately available chained resources.

Strict FIFO versus work-conserving scheduling is not changed in this patch: R4 remains an explicit policy follow-up. Unknown-memory admission is unchanged and not certified as physical memory availability. Linux process stop/restart remains a separately reported platform gap. Identity/publication screening-blocked cases are outside this patch.

## Linux lifecycle increment (registered before implementation)

Statement: the persistent controller can stop/restart its owned Linux service without Windows netstat/taskkill, preserving its DB and credentials and refusing unverifiable process identity.
Prediction: the existing two failing lifecycle tests pass on Linux; mismatched identity or a process not owning the listening socket is refused. A kernel pidfd binds stop signaling to the verified process; boot ID and proc start ticks distinguish stale pidfiles. No name-based process kill or blind PID fallback.
Falsifier: foreign process signaled, stale identity accepted, unsupported platform silently falls back to unsafe signaling, prior session/claim lost on restart, or Windows branch modified in execution behavior.
References: Python os.pidfd_open and signal.pidfd_send_signal documentation; Linux kernel proc filesystem documentation. This is a control-service backend, not a Linux engine/window port. Limits: Linux procfs and Python/kernel pidfd support required; Windows regression execution unavailable here.
