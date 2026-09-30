---
name: fleet-mailbox-and-team-leads
description: The operator-directed cross-agent mailbox (fleet-space v0 live) and
  the holodeck team-lead structure — who leads, what authority sub-leads hold
metadata:
  node_type: memory
  type: project
  originSessionId: sess_8207b32c-37a6-443b-91a8-b9f8901a74d5
---

Operator-directed 2026-09-11: "set up cross agent communication from sub agent to sub agent — use a mailbox if nothing exists" + "agent becomes a team leader".

**Mailbox v0 (LIVE, fleet space):** `E:\ChimeraWork\tools\fleet_mailbox.py` — post/read/--take; inboxes under `E:\ChimeraWork\mailbox\inbox\<agent>\`; atomic os.replace posting; served/ is append-only history. Contract: coordination ONLY — evidence, verdicts, gates never ride the mailbox (registry + repo only); senders self-declared. Repo-integration + controller-plane successor design = task fleet-mailbox-hardening-01 (PR pipeline).

**Team-lead structure:** subagent-worker-10 = HOLODECK TEAM LEAD (GOV/MATH/MAT), appointed rev 902, rank 50, while keeping its lane. Authority: member-to-task assignment, pre-check of team preregs against the PR #77 pattern BEFORE submit_review, inter-member blocker relay via mailbox, single consolidated voice to the lead. NOT granted: merge, provision, review verdicts, packet creation outside domain — ALL GATES UNCHANGED. Team: w09, w03, w07, w04, w11 (holodeck lanes). Pattern generalizes to other domains (engine, dyad) as benches grow.

**Why:** removes the lead as relay bottleneck; scales coordination with fleet size.
**How to apply:** new holodeck dispatches route member assignment through w10; member claims/provisions still report to the lead; watch for sub-lead coordination drift in reviews. See [[alan-fleet-operating-style]].

**Astra channel directive (2026-09-26):** the operator ordered the Execution Sergeant (and henceforth this fleet) to communicate with Astra via this mailbox — inbox `astra-codex` (created by the first post; any agent may post to any inbox). First use: the stale-OPERATIONAL_LEAD release request (msg id `fd1b02f9`, correlated to campaign suggestion-box Q-eac524d1). This mailbox is now the standing Astra channel, replacing operator-relay/suggestion-box-only routing.

**Status update (2026-09-11 late night)**: mailbox v1 promoted into the repo as durable infrastructure (PR #90 integrated — behavior-identical copy at tools/agent_fleet/fleet_mailbox.py, temp-root atomicity tests 100-posts/4-processes zero-lost, docs/THE_FLEET_MAILBOX.md contract + controller-plane successor design with instance-fenced senders and the PR #80 no-wrapper-shadowing rule). Team lead w10 is ACTIVE end-to-end: bootstrapped all five members through the mailbox (channel confirmed both ways), and received the first real division of assignment authority — MAT-02..05 member assignment delegated entirely via a mailbox message (the lead no longer dispatches holodeck members individually).

**First full assignment cycle completed (2026-09-11 post-compaction)**: after the conversation window killed every host, w10 itself was resurrected as a FRESH host under the standing controller identity (the disposable-host pattern), consumed the stalled delegation from its inbox, and delivered the mapping with stated fitness reasoning: w12→mat-02 (mat-01 author, seam continuity), w09→mat-03 (import/validation record), w11→mat-04 (math-01 units backbone), w05→mat-05 (authorship/provenance record), w07 reserve (excluded correctly on its own initiative when the lead took a conflicting dispatch). All four claims landed and RUN. The division of authority proven live: **w10 decides and posts via mailbox; the LEAD executes host spawns** (children of a completing session are not guaranteed to persist — team leads do not spawn hosts); prereg pre-check before submit_review stays the team lead's.
