# THE_FLEET_MAILBOX.md — the cross-agent coordination mailbox

**Operator direction (2026-09-11):** a cross-agent mailbox so fleet agents coordinate
without the lead as relay. Built live in fleet space by the lead
(`E:/ChimeraWork/tools/fleet_mailbox.py` — the fleet-space copy is the LIVE v0, in
production NOW: a promoted holodeck team lead coordinates through it). This document is
its contract; the repo copy (`tools/agent_fleet/fleet_mailbox.py`, promoted by
fleet-mailbox-hardening-01) is the durable, tested, behavior-identical promotion of
that v0. A repo copy changing behavior without a contract change here is a defect.

## THE CONTRACT (coordination-ONLY)

1. **Instance root — the live tree is fleet space, not the repo.** The authoritative
   instance is `E:\ChimeraWork\mailbox` (`inbox\<agent>\` + `served\<agent>\`, one JSON
   file per message). Tests and alternate instances MUST pass an explicit root (the
   `root=` seam or `FLEET_MAILBOX_ROOT`); the suite carries a guard that the live tree
   never sees a test artifact. Nothing in the repo writes to the live tree.
2. **Coordination-ONLY.** Evidence, verdicts, gates, and acceptance NEVER ride the
   mailbox — they live in the controller registry and the repo as always. A message
   that matters is a pointer ("look at X"), never the record itself. The mailbox has
   no verdict authority; nothing posted is evidence of anything.
3. **Sender is self-declared.** `--from` is whatever the caller typed; the audit trail
   is the file itself — who wrote into whose inbox is visible to anyone reading the
   tree (audit-by-visibility). Treat senders as claims, not identity, until the
   controller-plane successor lands (below).
4. **Atomic posting.** A post writes a temp file (`.tmp-<id>.json`) in the recipient's
   inbox and `os.replace()`s it into place — atomic on the same volume, so a concurrent
   reader never sees a partial message and concurrent posters never lose messages
   (measured: 100 posts / 4 processes / zero lost — see
   `docs/evidence/agent_fleet/FLEET_MAILBOX/`).
5. **Take is append-only.** `read --take` prints the inbox then MOVES each message to
   `served\<agent>\` — history is never deleted. Taking is the consumer's durable-handling
   marker; re-reading after take is a clean no-op (idempotent), and unreadable files are
   reported and moved too (never silently dropped).
6. **Name safety.** Agent names are controller session names. `_safe_name` refuses
   empty names, path separators/traversal, leading dots, and reserved characters —
   and a refused post writes nothing.
7. **Polling pattern.** Delivery is poll-based; there is no push and no delivery
   guarantee — an agent that never polls never receives. The discipline: poll
   (`read --agent <me>`) at natural idle points; `--take` ONLY once you have durably
   handled the message (acted on it or recorded it); never take on behalf of another
   agent; treat un-taken old mail as possibly-stale, not as unread obligations.

## Usage

```bash
python tools/agent_fleet/fleet_mailbox.py post --from <me> --to <agent> \
    --subject "<one line>" --body "<what you need>" [--correlation <task-id>]
python tools/agent_fleet/fleet_mailbox.py read --agent <me>            # poll
python tools/agent_fleet/fleet_mailbox.py read --agent <me> --take     # consume
```

`FLEET_MAILBOX_ROOT` (or the `root=` parameter) selects an alternate instance for
tests — never set it in production shells.

## DESIGN: the controller-plane successor

The filesystem mailbox is the v0: safe for coordination under single-host, single-user
assumptions, with its limits declared (self-declared senders, poll delivery, no
central audit beyond tree visibility). The successor moves the SAME two operations
into the controller's single-writer store:

- **`mailbox_post`** — arguments `from`, `to`, `subject`, `body`, `correlation`; the
  controller writes the message into the store and appends the event to the log.
- **`mailbox_take`** — arguments `agent`, message ids; marks served in the store
  (append-only served table, same discipline), records the take event.

**Why the successor is better:**

- **Instance-fenced senders.** The controller verifies the caller's enrolled instance
  header (the `X-Chimera-Instance` fencing from fleet-client-instance-01) and stamps
  the message with the ATTESTED session identity — `from` becomes evidence-grade
  identity instead of self-declaration. Spoofing a sender becomes a fencing violation,
  not a typo.
- **Durable and single-writer.** Messages live in the store the controller already
  persists with its own atomicity discipline — no second concurrency domain, no
  dependency on a fleet-space directory surviving cleanups.
- **Auditable.** Every post/take lands in the controller event log next to
  claims/checkpoints/reviews — the mailbox joins the system's existing audit plane
  instead of being visible only by reading a directory.
- **Cross-host ready.** Store-backed messages work for agents on any host that talks
  to the controller; the filesystem inbox only ever worked on the one host.

**Deployment-transition note — the wrapper-shadowing lesson (PR #80).** The new ops
must reach the controller's dispatch un-intercepted. The PR #80 lesson: a dispatch
wrapper (`ReviewHandoffControl._dispatch` in the review-handoff adapter) intercepted
the `claim` operation unconditionally and silently dropped semantics the direct path
had (auto-spawn, instance binding) — the wrapper SHADOWED the primary path and the
regression was only found by a live smoke lane. Rule for this transition: no
intermediary layer (review-handoff adapter, launch wrappers, client-side shims) may
intercept `mailbox_post` / `mailbox_take`; if an existing wrapper's pattern would
capture them, the wrapper must delegate VERBATIM or fail VISIBLY (refuse by name),
never silently substitute its own behavior. The fleet-space filesystem instance
retires only after the store-backed ops are live, verified, and un-shadowed; until
then the fleet-space root stays authoritative.

## Status

- Live v0: `E:/ChimeraWork/tools/fleet_mailbox.py` + `E:\ChimeraWork\mailbox`
  (production, coordination-only).
- Repo promotion: `tools/agent_fleet/fleet_mailbox.py` (behavior-identical; root seam)
  with `tools/agent_fleet/test_fleet_mailbox.py` (temp-root suite; atomicity probe
  100/4/0-lost; take idempotent; served append-only; name-safety; live-tree guard).
- Controller-plane successor: DESIGNED here, not built — a future lane delivers the
  store ops under the wrapper rule above.
