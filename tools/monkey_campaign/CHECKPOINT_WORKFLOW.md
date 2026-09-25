# Continuous goal execution through verified checkpoints

This operationalizes the existing playable-monkey requirements. It changes no requirement,
physical threshold, approved scope hash, training rule or publication authority.
Read it through `docs/MONKEY_RUN.md`; the operator still supplies one entry file.

## The persistent goal

Complete every selected requirement and demonstrate the complete physically controlled
ground-to-tree-to-ground experience in the accepted game build. The goal stays incomplete
until its numerical, runtime, visual, integration and explicit player-acceptance gates hold.
Finishing an assignment, producing a report, or dispatching workers is not completion.

Enter this objective in the harness's persistent goal facility when it has one. The
coordinator owns the loop below. A child worker owns one bounded checkpoint assignment.
Do not rely on prose to resume an exited session: the harness must actually deliver child
completion events or provide a tested wait/resume path. Record the provisioned mechanism
and its observed result; never claim continuous execution from a plan alone.

## Checkpoints for each affected feature

The coordinator freezes the applicable gates in the task packet BEFORE work. The existing
controller owns task state; a receipt is attached evidence, not a competing task registry.

| Checkpoint | Evidence required to advance | If it does not pass |
|---|---|---|
| 0. Claim and freeze | Current claim/generation, prerequisites, owned files, expected behavior, existing acceptance criteria, candidate identity and resource budget | Reconcile or take another eligible task; never duplicate a live claim |
| 1. Implement | Scoped source diff, exact source identity and a reproducible candidate | Continue implementation; no placeholder treated as working behavior |
| 2. Verify numerically | Relevant preregistered checks, actual results, failure trail and independently meaningful oracle | Diagnose and repair the measured failure, then rerun affected checks under unchanged bars |
| 3. Exercise the runtime | The intended binary/shaders/assets/policy, actual input commands and synchronized state trace for the scenario | Correct invocation/behavior; missing GPU access queues this gate while other work continues |
| 4. Inspect visually | Actual capture from that run, actual independent inspection, criterion-by-criterion verdict and timestamps | Repair observed defects or gather sufficient evidence; inconclusive remains open |
| 5. Review and integrate | Independent code/evidence review, exact reviewed revision, publisher acknowledgement and affected integration revalidation | Resolve findings/conflicts; do not substitute a worker's PASS for integration |
| 6. Advance | Native checkpoint records the accepted evidence and next unmet requirement; finished worker/slot is reused | Refill other legal slots and wait for a real completion/resource event |

Pure offline work can have a predeclared nonvisual policy with a specific rationale, such
as input parsing with no changed player-visible behavior. It still requires appropriate
tests and review. A worker cannot invent N/A after failing or lacking visual access.
All player-visible behavior needs runtime and visual checks; motion needs motion evidence.
Source/component evidence can be preserved across unrelated commits. Revalidation must
cover affected integration behavior on the actual final candidate, not erase history or
require every old receipt to equal the latest repository HEAD.

## What visual verification means here

A reviewer must actually inspect the recorded output; writing a path or declaring PASS
does not constitute seeing it. Keep the viewer/tool invocation and response with the
capture's raw-file SHA-256. A different reviewer performs the acceptance inspection;
the implementer's own inspection is useful debugging, not independent acceptance.

For movement, retain the actual video and synchronized command/state trace. Give the
reviewer the relevant intervals and frozen neutral questions. Require criterion verdicts,
observations and timestamp/tick references; include occlusion and unobserved behavior as
limits. Never infer an entire motion sequence from a single screenshot. If the available
eye only accepts individual images, preserve the existing one-image-per-call protocol,
inspect an ordered set of frames, and state its coverage. Use the retained video and
full trace for transition verification; incomplete observation stays inconclusive.

Pin a candidate manifest covering the exact source/tree or preserved dirty patch, engine
executable, shader set, assets, scene, policy and configuration used in the test. Bind
capture, commands, telemetry and inspection to one scenario/run ID and declared tick range.
Wrong/stale candidate or mixed runs invalidate the evidence. A compile alone does not
prove which executable was served. The trusted launcher/runtime owner verifies the actual
process, endpoint and loaded identities through the existing mechanism.

Visual verification addresses observable behavior: movement, controls, camera, contact
appearance and continuity. It cannot prove mass provenance, grip forces, torque capacity,
solver correctness or absence of an invisible force by appearance alone. Those retain
their numerical and runtime checks. A good-looking animation cannot substitute for physics.

Reuse `docs/THE_DYAD_PROTOCOL.md` for actual inspection and neutral questions. Current
gaming/process rules override its older window-restoration, port-reload and runtime-swap
directions. Do not disturb the operator's windows, endpoint, processes or protected
training. Reserve capture and judge resources; release them only after verified drainage.
If the authorized capture path is unavailable during gaming, queue visual work and use
available capacity for eligible offline implementation/review. Do not mark the gate passed.

## The playable sequence to verify

These are coverage checkpoints within the approved list, not new features or numeric bars.
Use P06 and the relevant frozen runbook to define heights, surfaces, duration, performance,
tracking and failure thresholds before trials. An unspecified bound is a missing contract,
not a number to choose after observing a run.

| Playable checkpoint | What must be observed and corroborated |
|---|---|
| Scene and controls | Correct monkey/forest identity, usable camera and genuine player-command path |
| Ground movement | Start, all-fours walking, steering and stop on supported ground; compare actual response with commands and physical contacts |
| Tree approach | Reach the supported trunk without bypassing terrain/collision or snapping into a pose |
| Grip, climb and hold | Physical support, ascent and pause within the declared envelope; correlate visible contact with force/contact records |
| Descent and release | Return to the ground, remove grip support, transition back to walking without hidden reset or teleport |
| Whole experience | One continuous run covering the sequence and its required failure behavior on the integrated candidate; remaining selected UI/save/performance/package gates still apply |

Run the final sequence through the normal player interface. Diagnostic replay is supporting
evidence, not a replacement for the user's control path. Freeze relevant seeds/scenarios
and preserve failures; no repeated success-seeking retries or relaxed thresholds.

When all selected requirements have scoped accepted evidence, present the exact candidate,
controls, short capture and known limits for the operator to play. Record explicit operator
acceptance from the actual conversation/authorized acceptance channel, bound to that
candidate. A model verdict or agent-written `actor: human` field is not human acceptance.

## The coordinator never stops merely to announce progress

At startup recover existing workers, claim generations and checkpoints. Do not redispatch
the reported W1/W3/W4/W6 or any other assignment merely because a new session began.
Then, after EVERY completion, failure, review or integration event:

1. Reconcile actual active workers and controller claims; preserve owned work.
2. Process completed evidence and advance each task to its first unmet checkpoint.
3. Refill available legal slots with independent ready implementation or required review,
   within the existing campaign cap, actual harness capacity and machine limits.
4. Perform coordinator work that is ready, including review/integration and resource release.
5. If workers remain active, call the harness's completion/wait mechanism and resume this loop
   when it returns. A progress message is not a terminal result. Do not busy-poll or sleep
   through an actionable completion.
6. If a resource wait is temporary, record the exact wait/resume event and use the supported
   mechanism. If nothing executable remains and no worker can advance, checkpoint the named
   external blocker and resume action; leave the goal incomplete.

Explicit operator stops and actual quota/budget/platform limits remain binding. A context
handoff records active child IDs, native claims, first unmet checkpoints and the precise
resume action. A final message cannot be used as the scheduler. If the harness ends the
coordinator and offers no resumption, report `CONTINUATION_NOT_CONNECTED`; do not promise
that these files alone make it run unattended.

Verify continuity on REAL useful work: retain the dispatch event, completion event,
coordinator processing, and next dispatch/review action for successive task completions
without an operator “continue” message. Do not invent a filler campaign to demonstrate this.

## Executable receipt check

`campaign.py checkpoint` is a bounded, read-only evidence-structure/hash checker. It emits
the first unmet checkpoint and its next action, or `ready_for_controller_review`. It does
not judge pixels, authenticate people, publish code, dispatch models or mark a goal complete.

The coordinator pins a `chimera.checkpoint_context.v1` document through its existing claim
packet before work. Its raw-file SHA-256 is provided separately by the trusted coordinator;
never recompute a changed context and automatically approve the new hash. The document names:

- scope hash; planning/native task IDs; claim generation; run ID; implementer ID;
- subject manifest hash and preregistered criteria manifest hash;
- kind: `offline`, `visible_static`, `motion`, or `final_playthrough`;
- applicable ordered gates: implementation, numerical, runtime, visual, review, human;
- a specific predeclared nonvisual reason for offline work.

The receipt repeats those bindings, names existing subject/criteria files and evidence,
and records each gate as pending/pass/fail/inconclusive. Its evidence references are relative
to the explicitly supplied evidence root and carry raw-file SHA-256. Pass records need
actor/run/candidate identity plus these roles:

| Gate | Evidence roles |
|---|---|
| implementation | changes |
| numerical | results |
| runtime | commands, telemetry; actual tick interval |
| visual | capture, inspection; matching tick interval; video for motion |
| review | review, from an independent reviewer |
| human | acceptance, with source_kind=operator_message and the actual source reference |

Use `checkpoint_context.example.json` and `checkpoint_receipt.example.json` as incomplete
templates, not passes. Store completed records with native controller checkpoint evidence.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File 'E:/PythonChimera/tools/monkey_campaign/Invoke-MonkeyCampaign.ps1' -Action checkpoint -ApprovedSha256 '33a8fb7204e20bf71f563014c57d772dd111a198cd1d6b212fd053653858f863' -ContextPath '<pinned-context.json>' -ContextSha256 '<coordinator-pinned-raw-hash>' -ReceiptPath '<checkpoint-receipt.json>' -EvidenceRoot '<owned-evidence-directory>'
```

Exit 0 means the checker produced an assessment, NOT acceptance. Inspect `next_checkpoint`
and `ready_for_controller_review`. Exit 2 is a malformed/stale/mismatched evidence refusal.
The checker limits referenced file reads to 512 MiB per call; split oversized captures into
declared checkpoint intervals with complete coverage. It refuses missing/empty artifacts,
path escapes and links/reparse points. These are local integrity checks, not an OS security
boundary or proof that a recorded actor actually performed the claimed judgment.

`plan` now reports `implementation_integrated` separately and never claims `goal_complete`
from task-status strings. The actual coordinator may close the persistent goal only after
checking the selected requirements, final integration candidate, actual visual/numerical
judgments and explicit operator acceptance. A helper's JSON must never impersonate that act.
