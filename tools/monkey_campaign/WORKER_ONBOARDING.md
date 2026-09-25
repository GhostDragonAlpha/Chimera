# Worker procedure — internal reference, not another onboarding prompt

The sole user-facing entry is `E:/PythonChimera/docs/MONKEY_RUN.md`.
Its first action runs `worker_start.py`: instruction verification, real orientation,
shared-status inspection, and automatic arrival submission to the existing mailbox.
No hand-authored arrival JSON or separate goal prompt is needed.

Retain the returned arrival ID and use it on retries. Check for an existing native
claim before taking another. Arrival IDs are explicitly unauthenticated intake IDs;
they do not grant filesystem ownership or certify harness capacity.

The existing coordinator reads pending UNASSIGNED:BOOTSTRAP requests at its normal
coordination events. It recovers actual assignments, arranges trusted enrollment,
issues claims, adopts real workers into report slots, and acknowledges the lead revision.
If its provisioning adapter is absent, it files COORDINATOR_BOOTSTRAP_REQUIRED with
actual inventory and task-brief references. It does not invent credentials or enrollments.

Workers continue their owned tasks through preregistration, derivation, implementation,
appropriate numerical/runtime/visual verification, independent review and integration.
Then acquire the next eligible unit. A small direct operator task takes priority after
ownership is reconciled. Architecture questions go to the suggestion box.

Use COORDINATION.md for slot/report contracts, hourly Central deadlines, GPU rules and
recovery. Use SUGGESTION_BOX.md for questions and answers. Astra checks only when the
operator messages Astra; there is no automatic lead wakeup. Preserve protected training
across reporting-lease expiry. Do not reuse a slot until the previous worker has stopped.

The coordinator uses useful available subagents up to the shared ten-worker limit and
the lower real harness/controller/resource limits. Do not duplicate work to fill capacity.
Never mark the game complete without its required evidence and operator acceptance.

Startup now also reads EXECUTION_QUEUE and atomically claims a bounded diagnostic task
and free slot. Execute the returned brief immediately; no second goal prompt or HTTP
prototype enrollment is required for that explicitly scoped work. Recover an existing
owned task instead of double-claiming. Native/source/hardware assignments outside these
briefs still follow the current coordinator. An arrival alone is not a claim; the
returned ASSIGNED record is the bounded claim. Worker execution is never inferred from
a claim record. Read DOC_AUDIT.md for the live plan and acceptance corrections.
