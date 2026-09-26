# Workflow index and glossary

For the playable-monkey campaign, execute [MONKEY_RUN.md](MONKEY_RUN.md).
This index is navigation, not an alternative startup prompt or authority grant.
Read installed instruction revisions and actual command results; an implementation
branch or proposed document does not prove deployment. Historical receipts remain
evidence of their recorded revision, not instructions for the current queue.

## Find the procedure

| Keyword or question | Canonical starting point |
| --- | --- |
| STARTUP, autonomous entry, next assignment | [MONKEY_RUN.md](MONKEY_RUN.md) |
| WORKFLOW, overall sequence | [Fleet workflow](FLEET_WORKFLOW.md) |
| DISASTER RECOVERY, new PC, backup, install, dependencies | [Replacement-PC checklist](DISASTER_RECOVERY.md) |
| CAPTAIN, LIEUTENANT, architectural lead | [Lieutenant onboarding](../tools/monkey_campaign/LIEUTENANT_ONBOARDING.md) |
| SERGEANT, OPERATIONAL_LEAD, coordinator claim | [Sergeant onboarding](../tools/monkey_campaign/EXECUTION_SERGEANT.md), [operational coordination](../tools/monkey_campaign/OPERATIONAL_LEAD.md) |
| CONTINUE, next task, handoff | [Continuous cycle](../tools/monkey_campaign/CONTINUOUS_CYCLE.md) |
| DEVELOPMENT, REVIEW, CORRECTION, branch-N | [Review lane](../tools/monkey_campaign/REVIEW_LANE.md) |
| PR, ACCEPTED, merge, missing GitHub credentials | [Merge service](../tools/monkey_campaign/MERGE_SERVICE.md) |
| ARRIVAL, ATTEMPT, restart, lost context | [Startup recovery](../tools/monkey_campaign/STARTUP_RECOVERY.md) |
| MAILBOX, architecture question, suggestion | [Suggestion box](../tools/monkey_campaign/SUGGESTION_BOX.md) |
| MEMBRANE, containment, PORT | [Membrane ontology](MEMBRANE_ONTOLOGY.md) |
| DEPENDENCY, backlog, qualification | [Ontology work plan](ONTOLOGY_WORK_PLAN.md), [ontology queue](../tools/monkey_campaign/ONTOLOGY_QUEUE.md) |
| VISUAL, CAMERA, labels, debug geometry | Card's verification profile and [capture contract implementation](../tools/monkey_campaign/visual_capture.py) |

## Identities are different things

| Term | Meaning |
| --- | --- |
| arrival_id | Worker identity recovered from its own startup receipt; used with --arrival-id. |
| task_id | Durable unit of approved work, criteria, inbox and submission history. |
| attempt_id | A particular attempt at a task; never substitute it for arrival_id. |
| Development slot | One of ten active task positions; not an agent identity or GPU reservation. |
| branch-N | Assigned Development branch; do not switch the shared checkout to it. |
| review/<task-id> | Separate publication branch for the card, as returned by current policy. |
| criteria_sha256 | Identity of the acceptance criteria; workers must not rewrite it to pass. |
| head_sha | Exact Git revision under review; changed heads need renewed verification. |
| artifact SHA-256 | Hash of declared artifact bytes; proves identity, not correctness. |
| role token | Issued coordination capability; not a GitHub credential or instruction checksum. |

## State and evidence vocabulary

- **Publication request:** durable candidate handoff; no claim that GitHub has a PR.
- **Review queue:** submitted work outside the ten Development slots.
- **PASS:** reviewer's evidence-based recommendation for the exact candidate.
- **ACCEPTED:** authorized acceptance; still not a verified GitHub merge.
- **CHANGES_REQUIRED / CHANGES_REQUESTED:** review finding / correction state;
  follow the returned transition and existing task inbox, retaining failed evidence.
- **CORRECTION_QUEUED:** correction awaiting Development capacity; not a new task.
- **DONE:** recorded completion through the applicable acceptance and merge gates.
  A diagnostic's completion does not automatically qualify its parent feature.
- **Component versus feature:** useful code and records may still lack required
  runtime or visual behavior. Do not infer feature qualification from code presence.
  Use only integration transitions actually supported by the installed workflow.
- **AWAITING_LEAD_ACTION:** routing result requiring an exact blocker report after
  checking eligible implementation, correction, publication and independent review.
  Empty Development does not imply an empty Review queue or a completed campaign.
- **Visual evidence:** proof suited to the card's claim. Static asset inspection
  and actual player-motion verification are different requirements. Record element
  identity, debug visibility, camera position/orientation/distance and framing.
- **Preregistration:** statement, prediction and falsifier recorded before the run.
  A retrospective test description must not be relabeled preregistration.

## Reporting and recovery

At each handoff record task, arrival, attempt, workspace, instruction revision,
criteria hash, tested source revision, commands/results, artifact hashes, actual
publication state and next action. Never include role tokens or API credentials.
Use the returned handoff templates; preserve failures and earlier receipts.

For a blocker, send its task ID, exact failing command or gate, expected versus
observed behavior, evidence location and proposed next action to the appropriate
task inbox or mailbox. Report missing evidence explicitly. A WORKING label or file
timestamp alone does not establish liveness, and a prose mismatch alone does not
prove an allocator defect. Continue unrelated eligible work.

## Documentation maintenance

Keep operational facts in their canonical contract and link to them here. Change
contradictory current instructions together; preserve historical receipts as history.
Separate proposed, tested, installed and published changes in deployment reports.
Instruction pin changes require the authorized update process, not a worker editing
a checksum to make verification pass. This index creates no new role permissions.
