# GPU handoff extension: preregistration, 2026-09-24

Operator explicitly answered: "Training may interrupt gaming too." This supersedes
gaming priority for an admitted training request. The request is for a mechanism,
not an instruction to close today's game or unload today's model immediately.

STATEMENT: one supervisor outside local-model inference can transfer the 4090 from
local agents/games to training without double admission, lost agent checkpoints,
automatic model reload during training, or releasing a still-running training job.

PREDICTION: concurrent requests serialize through the existing resource authority;
new inference stays gated throughout drain/training; preserved local-agent sessions
resume only after observed training cessation and release. Hourly worker expiry does
not revoke a protected training job. The supervisor needs no scheduled Astra wakeup.

FALSIFIERS BEFORE IMPLEMENTATION: double grant; generation-stale launch; Bionic/direct
LM request bypasses gate; model reload during training; release based on timer rather
than observed cessation; wrong application interrupted; lost worker checkpoint;
controller depends on the model it unloads; failed unload/quit treated as success;
recovery blindly reloads or relaunches; busy trainer preempted by another requester.

This change publishes implementation requirements in COORDINATION.md under the existing
resource-control scope. No live game interruption, model unload/reload, training launch,
new service, native controller migration or physical handoff is tested or claimed here.
