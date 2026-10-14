# Lead instruction revision reader

2026-09-24, before implementation/tests. Operator appointed Astra/Codex lead and
asked that only the designated lead maintain overall instructions; workers consume them.

Statement: an explicit revision and read-only bundle fingerprint can distinguish
published instructions from a coordinator's acknowledged version without modifying
the sealed requirements or starting another progress registry.

Prediction: initial/missing acknowledgement requires a read; matching acknowledgement
is current; higher revision requires rereading; lower revision and changed content
at the same revision refuse. Every listed policy file participates in the fingerprint.
Traversal/absolute paths, unknown lead/schema, malformed/duplicate metadata and overlarge
files refuse. The reader never writes an acknowledgement, authenticates a human,
launches a worker or changes ACLs. Tests exercise those claims with synthetic files.

This is cooperative integrity and revision tracking, not cryptographic authorship.
The current file ACL grants broad Modify access. Model names are not Windows security
principals. OS isolation or an inaccessible signing key would be a separate deployment.
Actual GLM pickup remains unverified until its real acknowledgement arrives.

Operator additions before slot-timeout implementation: ten slots are short-term
assignment memory and the common entry funnel. Use the top of every hour, not a
rolling 60-minute timeout. Each registration expires at the next hour boundary;
a mid-hour join gets the remainder of that hour. Reports never renew the deadline.
Expiry preserves checkpoint memory, blocks further normal reports under the old
registration, and reserves the slot until confirmed worker cessation/preservation.
Prediction: boundary-time expiry is exact, stale generations cannot update a reused
slot, no expiry silently releases a writer, and memory survives release. Registry
operations evaluate the clock; no background scheduler or OS process stop is claimed.
# Suggestion box and universal onboarding amendment

Operator steering: workers need one reusable onboarding prompt, can receive small
scoped tasks directly, and must route architecture questions to the designated lead.
The latest instruction supersedes the earlier hourly lead-review request: Astra checks
the mailbox only when the operator talks to Astra. No scheduled review or self-wakeup.
Worker/coordinator hour-boundary checkpoints remain in effect.

Statement: a shared transactional mailbox can preserve concurrent questions and
versioned lead answers without granting workers authority to change the instructions.
Prediction: simultaneous submissions remain distinct, exact retries are idempotent,
stale answer attempts cannot overwrite newer answers, and neither submission nor
checkpointing invokes a model or installs a timer.
Falsifiers before implementation: lost concurrent submissions; duplicate exact retry;
question mutation or answer overwrite; accepted stale answer sequence; unbounded
accepted payload; an implicit scheduler/model/process invocation. Test in temporary
directories; preserve real workers and the sealed feature map.
