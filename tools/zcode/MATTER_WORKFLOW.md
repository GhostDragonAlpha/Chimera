# Executable simulated-matter workflow

Operator goal, October 26: enable the agents to carry a requested game, mechanism,
environment or other construction from physical understanding to tested editable
Blender delivery, then reuse what they learned. Ontology, databases, DFT evidence,
machine learning, local cellular automata, native physics and Blender belong to
that process. A working handoff does not prove the complete physical workflow.

## Implemented foundation and evidence

`matter_workflow.py` owns durable dependencies, checkpoints and deterministic test
gates. `matter_hook.py` connects them to actual Z Code Agent, SendMessage and
TaskOutput events. It supplies neither a new inference service nor a physical law.
Binding is opt-in through `CHIMERA_MATTER_RUN`; unbound sessions are unchanged.
Production profiles, model settings and the original saved goal are unchanged.

## Z Code dynamic-workflow layer (October 27)

The October 27 goal adds a reusable executable Z Code dynamic workflow,
`.zcode/workflows/matter-construction.dwf.ts`, that drives the same stage
sequence through real Z Code subagent dispatch. One run advances exactly one
stage (`spatial`, `research`, `implement`, `test`, `review`, `deliver`) of a
bundle directory holding `flow/request.json` (immutable request, acceptance
items, toolchain, protected hashes) and `flow/reports/<stage>-<n>.json`
checkpoints. The installed facade has one model per run, so the coordinator
selects it per stage (October 27 operator grant: the coordinator chooses the
best model per stage): `spatial` and `review` use Step 3.7
(`chimera-step37/step-3.7-flash-iq4_xs`); `research` uses GLM-5.3-Flash
(`chimera-strata-maya/glm-5.3-flash`) for source reading and routing;
`implement` uses GLM-5.3-Flash, with DeepSeek Maya-XS
(`chimera-deepseek-maya-xs/deepseek-v4.1-flash-1017-maya-xs`) for a bounded
second attempt on difficult geometry/contact/recipe blockers; `test` uses
Chimera Code Dirk Qwen 27B (`chimera-code-provider/dirk-qwen3.8-27b`) for
command-driven harness execution; `deliver` uses the session Qwen. This
preserves real role profiles instead of renaming a Qwen actor. Dependencies are enforced by the script (each stage refuses to start
without its predecessor's accepted status), `NEEDS_EVIDENCE` returns a research
escalation to the coordinator, the `test` stage re-runs the bundle's
`flow/verify.bat` through the harness as an independent gate that can only
downgrade a claim, and `deliver` is gated on a `PASSED` review covering every
acceptance id. GPU work stays behind `run_gpu_job.py`; actors are instructed to
work only inside their bundle and preserve failures.

Validation runs on the existing aluminum/stainless/alloy construction in
`Runtime/zcode-matter-workflow-20261027/alloy-zcode-01` (acceptance:
deformation, contact interaction, complete energy accounting, save/reopen,
editable construction; protected inputs byte-identical to `alloy-real-01`,
which is untouched). The workflow is saved and typechecked and its first
spatial stage is executing; no physical qualification or reuse is claimed from
the workflow's existence alone.

The request front door is now `matter_setup.py prepare-intent BUNDLE --intent
UTF8_TEXT_FILE --mode new` (or `--mode existing --scene ORIGINAL_BLEND`). Optional
`--evidence`, `--protect`, `--ontology`, `--hardware` and `--acceptance-floor`
provide actual inputs and constraints. This prepares only a fresh private bundle;
`start BUNDLE` launches its existing native profiles after ownership checks.
The literal request is immutable. Step proposes the conceptual 3D design and
ontology-backed specification; a separate Step reviewer accepts its exact hash
before the controller creates `request.json` once. New geometry is an authored
design task; it is not labeled a measurement. Empirical source gaps become real
dependencies with pinned resolutions and independent plan review. Measurements
that require the new construction belong to explicit qualification acceptance.
Human clarification is appended immutably through `answer-intake`, retaining the
original wording, constraints and same child. This is new-bundle behavior; the
current alloy request and production sessions are not migrated into intake.

This entry runs the installed **Z Code CLI in a private home**. It does not bind
an already-running app conversation, and no matter opt-in command is registered
in the production app configs. Setting an environment variable inside an app's
Bash child cannot rebind its parent. Preparation starts no inference. `start`
requires the preserved production goal paused, no recent competing production
goal, an idle gateway and the existing GPU availability/owned-resume checks. It
never stops user work. A real new-request intake and qualified delivery still need
demonstration; app-native session binding would need separate implementation and
evidence, rather than being inferred from these CLI checks.

The second demonstration now has a prepared acceptance floor and explicit entry
arguments in `Runtime/zcode-matter-workflow-20261026/reuse-pressure-plate-acceptance.json`
and `reuse-pressure-plate-entry.json`. These retain local-rule evolution, complete
energy accounting and measured successful reuse as explicit checks. No second
bundle exists or has been launched. Its first source must qualify, be published,
and be discovered before Step authors the new pressure-plate specification.

The latest installed-CLI intake fixture passed in
`Runtime/zcode-matter-workflow-20261026/native-wiring-1793068527844484800/result.json`:
48 mock requests, 24.532 seconds, separate spatial/specification-review models,
same-child research/resume, freeze and subsequent tested controller stages,
including dependency reconciliation in spatial, specification review, test-plan
review and final review.
It contains synthetic graph records and fake Blender artifacts and proves no
physical behavior. It ran after the real CLI exited, using a private loopback
endpoint and unchanged production profiles/providers. Earlier fixture timings
are different wiring workloads, not performance comparisons.

Thirty-five controller CPU fault tests, thirteen process-lifetime tests, four
production-ownership checks, ten observation checks, fourteen retention checks and
eleven reuse checks passed.
The installed CLI fixture passed in
`D:/Chimera-Maintenance/Runtime/zcode-matter-workflow-20261026/native-wiring-1793058323420202800/result.json`:
30 requests, 29.90 seconds, a research detour, the same Step child resumed,
deferred test authoring, separate Step plan approval, implementation, actual CPU
test dispatch, independent Step review and delivery.
This used a **deterministic mock endpoint**, not the real models or Blender.
Its graph admission uses the existing authority with synthetic records. Its
Blender lookup receipts and `.blend` are explicitly fake; they are never physical
evidence. Runtime differs from older fixtures and is not a tuning comparison.

## Executable sequence

1. Resolve requested material/source IDs through the existing
   `tools.science_funnel.graph.graph_from`. Record intended function, spatial
   arrangement, interactions, conditions, fidelity, hardware, owned scope,
   protected inputs, acceptance and test dependencies. Do not create another
   ontology or treat semantic-embedding coordinates as physical positions.
2. Qwen dispatches the controller's exact next brief. The hook checks parent
   session ownership, ready dependencies, required profile and foreground mode.
   The hook now gives Qwen a short dispatch string pointing to the full preserved,
   hashed assignment file. No requirement is discarded to shorten the handoff.
   This avoids repeatedly generating the full specification and overflowing
   SendMessage's 20,000-character limit. The real run's first paraphrased task
   identifier was refused; Qwen corrected it and dispatched the actual Step child.
   A child may also return a short pointer to its full, fresh owned JSON report.
   The controller validates and pins those bytes, preserving the original content
   without asking the model to emit it twice.
3. `chimera-spatial`, using Step 3.7, supplies frames, units, geometry, topology,
   connections, load paths, motion, boundaries and predictions before mathematics.
   The research stage routes source evidence and scale reductions through existing
   adapters. DFT properties, phase proxies and authored baselines retain their
   labels; electron density is distinct from continuum mass density.
4. Record native terminal reports, child IDs, evidence hashes and available usage.
   SendMessage's acknowledgement cannot advance the task: retrieve TaskOutput for
   the same child. The concrete hook guidance uses the installed maximum blocking
   timeout, 600,000 ms, to reduce coordinator polling and model switches. Timeout
   is not completion; retain the same child. Native SendMessage resumes in the
   background, so this guidance is not a guarantee of zero queued coordinator
   requests. The gateway still serializes inference. `NEEDS_EVIDENCE` creates a research dependency with the question,
   unresolved assumption, measurement and decision. Repeated identical gaps stop
   blind retries. A measurement request creates a bounded experiment task for the
   existing implementation profile, restricted to fresh owned diagnostic outputs.
   It returns to the same blocked child with method, commands and measurements.
   The real alloy run has exercised this dispatch and returned native
   measurements. Its first experiment report was rejected for listing directories
   where pinned evidence files are required; Qwen resumed the same native child
   to correct the report. Scientific acceptance by Step remains pending.
   Future spatial and independent-review dispatches now pin an immutable manifest
   of accepted research/experiment ancestors, separate from failed report history.
   `matter_dependency_review.py` requires the exact issued brief and a
   `details.dependency_review` assessment citing each accepted report and relevant
   pinned result evidence for READY and NEEDS_EVIDENCE alike. Current attempts
   without that policy retain their original contract. Repeated identical needs
   still halt; citations establish declared provenance, not comprehension or
   scientific validity. New follow-ups retain their original structured question
   independently of repair instructions. Legacy overwritten questions are unknown.
   When tests are initially unknown, a separate Qwen task authors qualification
   tests after spatial/source understanding. Step reviews the exact hashed test
   proposal and every original acceptance item before those tests are frozen.
   Test revisions return through that approval; acceptance cannot be dropped.
5. `chimera-maya`, the existing Qwen-powered implementation role, works through
   native owners in the owned copy. Learned/CA rules require explicit physical
   state, neighborhood, time, matter/energy exchanges, domain and qualification.
   The lead dispatches frozen tests after the implementation child returns.
   GPU tests name the existing `gpu_batch.py` or `run_gpu_job.py` handoff.
   New GPU test plans also require an earlier CPU preflight in `depends_on`.
   The controller records skipped dependent tests when prerequisites fail and
   never launches their GPU command. The real experiment exposed a missing
   Python import only after an unload; this gate addresses that avoidable
   transition for subsequent qualification plans. It does not retrofit or
   interrupt an already-running experiment.
6. Require actual process success and assertions on fresh result files. Verify
   test dependencies, implementation bytes and accepted evidence. Changed bytes
   cannot inherit PASS. Failed tests retain receipts and return through spatial
   diagnosis before another implementation.
   Fresh assertion outputs are archived by content hash even when an assertion
   fails; later retries cannot erase those observations by overwriting their
   normal output paths. Stale pre-existing outputs are labeled and never treated
   as fresh evidence. Archival failure prevents qualification.
7. `chimera-step37` reviews every original acceptance item against actual receipts.
   Delivery must identify the same tested `.blend`, retained records and reuse
   instructions. Admission through existing ontology/asset owners remains required;
   a report or graph proposal is not applied admission.
   `matter_retention.py` corroborates actual graph-controller storage, a graph_apply
   event and receipt, stable identities, and tested asset/procedure lookup outputs.
   All retained artifacts must be among passed-test pins. The independent Blender
   tests must execute those lookups and check saved persistence. This does not
   promote physical verification or prove suitability for a new construction.

The installed Z Code dynamic-workflow facade has one model selection for all its
actors and no per-actor profile parameter. Native Agent/SendMessage preserves the
actual Step and Qwen profiles; do not substitute a Qwen actor merely named Step.

The source reviewer profile advertises write tools despite read-only instructions;
initial foreground children do not execute the existing role hook. The isolated
fixture and real setup therefore restrict the copied `chimera-step37` tool list
and disallow write, shell and delegation tools in the profile itself. The spatial
profile retains diagnostic permissions. Production children are unchanged.

`matter_setup.py prepare BUNDLE --request REQUEST` creates a fresh private home,
provider/profile copies, session database and owned workspace. `start BUNDLE`
checks the original production goal is still paused, the gateway is idle and the
GPU is free before starting the installed CLI through the existing providers.
There is no warm-up request. New dispatches also recheck production ownership;
resumed user work prevents subsequent dispatch. Existing owned CLI processes
must be inspected, never duplicated. `status BUNDLE` reports their identities.
`MATTER_TOOLCHAIN.json` records existing pinned runtime/launcher paths and the
GPU handoff reference, avoiding repeated PATH/interpreter guesses. It does not
claim qualification or invoke those executables.
An existing owned session may resume with idle Qwen already resident after a
read-only router/backend/engine ancestry and memory check. This avoids an
unnecessary unload/reload. Fresh bundles still require the normal free-GPU check.
Unknown ownership, busy/queued work, implausible memory counters or substantial
unattributed device memory refuse this exception. These are point-in-time checks.

For a later construction, `prepare BUNDLE --request REQUEST --reuse-from SOURCE_FLOW
--reuse-selection SELECTION_JSON` validates the completed source and selected
ontology IDs, `asset:` references and `procedure:` references through the existing
owners. It preserves source request/state and tested bytes as protected inputs.
The new request must include `successful_reuse` acceptance and a separate owned
scope. It still runs Step, independent tests and actual Blender qualification.
The source request is referenced by path/hash, not recursively copied into each
successive request. `compare BUNDLE` reports recorded costs only after both flows
complete; different task durations alone do not prove a speedup or reduced work.
No real cross-request reuse has yet passed.

Ontology inputs now have exact immutable snapshots and a versioned directional
dependency capture (`matter_ontology.py`). A later unrelated consumer or record
does not invalidate the earlier experiment. Changed upstream material/model
content, contracts, explicit artifact bytes or physical coupling makes current
reuse stale. Historical evidence remains tied to its original bytes. Explicit
protected files and frozen test inputs retain their live byte checks. Legacy
flows seal only at an idle task boundary, without rewriting requests or reports;
tests that still read the live graph require a normal reviewed test revision.
Twenty-one scope tests and seven workflow integration tests pass. These are CPU
consistency checks, not physical validation.

`matter_discovery.py search --authority GRAPH --query TEXT` uses the existing
ontology search to find immutable completed-result descriptors. Its ten CPU
tests cover source/scope changes, tampering and additive graph growth. A verified
published descriptor can feed `matter_setup.py prepare ... --reuse-authority GRAPH
--reuse-id ID --reuse-selection SELECTION_JSON`; it resolves the original flow
and checked asset/procedure references itself. New actions recheck current
eligibility while historical checks retain the sealed evidence. The proposal
API does not publish: actual repository/controller publication and a fresh
request demonstrating discovery and reuse are still required. Descriptors store
qualified-result references with `extracted` status; they do not promote physics
to `verified` merely by being stored.

The repository publication adapter is `matter_publication.py`:
`prepare SOURCE_FLOW GRAPH TRANSACTION_DIR`, then `apply TRANSACTION_DIR` or
`inspect TRANSACTION_DIR`. It appends the same immutable descriptor to the
existing authored program and native graph, retaining before/after bytes and a
recoverable process-owned transaction. Eighteen CPU tests pass, including an
isolated rebuild with the existing graph builder. It refuses changed targets,
unqualified sources, controller snapshot envelopes and provenance endpoints that
the authored build cannot restore. This is local graph publication, not Git push
or a live controller update. Cooperating writers must honor its lock; two files
are recoverable rather than one atomic commit.

The bound completion entry is now `matter_setup.py prepare-publication BUNDLE`,
`publish BUNDLE`, or read-only `publication-status BUNDLE`, implemented through
`matter_publish_step.py`. It derives source and graph authority from the original
launch/request, checks the completed source and production pause, and resumes one
owned publication transaction. The native completion hook supplies the publish
command only when inspection says the source/transaction is ready. Publication
receipts live outside the sealed flow; writing them into its state would change
the source identity. Changed targets, ambiguous preparation and unqualified or
stale sources refuse publication. Sixteen CPU tests cover this adapter; seven
entry/hook checks cover routing and preservation. These use synthetic qualified
fixtures. The real alloy result is still unqualified and has not been published.
Preparation and apply preflight both refuse a mutable target pinned by any
nonsuperseded evidence in accepted task attempts. This also prevents an unsafe
transaction prepared by an earlier adapter from invalidating its own source.
Only the existing exact historical ontology alias can resolve such a pin to a
sealed snapshot; ordinary source and test pins remain live requirements.

The real input audit found five requested matter/DFT roots absent from authored
inputs, despite their presence in the generated graph. The reviewed preservation
append is now applied: 57 existing connected objects and 166 exact relations in
the existing authored `project_program.json`. Old objects, statuses, evidence,
metadata and serialization are preserved. The isolated owner rebuild preserves
the entire 470-object request scope; the live graph remains byte-identical.
Receipt: `Runtime/zcode-matter-workflow-20261026/ontology-authored-preservation/proposal-01/APPLIED.json`.
Do not replace the live graph with that test rebuild: it also exposes nine
unrelated history records and eight links missing from the previous authored
baseline and recomputes layout. No real completed-result descriptor is published.

The first real run is
`D:/Chimera-Maintenance/Runtime/zcode-matter-workflow-20261026/alloy-real-01`.
Its original request and source pins are immutable; its live checkpoint and
terminal reports, not this document, establish current progress. No completed
real-agent physical qualification or successful reuse is claimed yet.
Step 3.7 completed the first spatial analysis (904.252 native-reported seconds),
returned `NEEDS_EVIDENCE` for contact/support-reaction measurements, and the
controller created `experiment-70adc7af1b`. Qwen dispatched that task to the
Qwen-powered implementation profile using a 558-character handoff referencing
the full preserved brief. Step's first accepted dispatch prompt was 10,670
characters. Different tasks and loading states prevent a speedup claim. The
measurement, resumed Step analysis, physical qualification and reuse remain open.
The experiment has since performed native CUDA diagnostic probes through the
existing GPU batch handoff. Failed API probes and native assertions are retained.
One later diagnostic command exits successfully but still records a contact API
error, so command PASS is not a passed contact-force or physical reference test.
Actual Step acceptance of the measurements remains pending. The first experiment
also found its instrumentation changes the trajectory; its claimed force
calibration and physical time mapping require review. A converged measured run
does not automatically establish evidence for the original trajectory.
The original real CLI ended after 7,377.322 seconds without retrieving the second
native terminal report. Its child had written a report-generation script but
never created the claimed report file. Recovery preserved both invalid terminal
reports. The controller now gives an exact TaskOutput command for an active
recorded child, and `matter_report_check.py FLOW FULL_REPORT_JSON` provides a
nonmutating structural check before submission. Report corrections may reuse
measurements created during the original same task, but not pre-task data. One
explicit bounded format-repair allowance was used after these fixes; it resumes
the same child and cannot reopen scientific failures or qualify missing results.
That resumed private CLI, `cli-job-1793065400197500700`, later exited normally
after 2,728.698 seconds with the workflow incomplete.
That correction subsequently created a real report and passed the structural
checker. Qwen retrieved it through native TaskOutput, and the controller resumed
the original Step spatial child with the measurements. This demonstrates the
actual recovery handoff; Step's scientific acceptance remains pending.

The first resumed Step response repeated its initial report and appended a second
JSON object. Its own native assistant message contains that text; TaskOutput did
not combine earlier outputs. The strict parser rejected it, and Qwen resumed the
same child for correction. The recorded reads in that response did not include
the experiment report. This is an unresolved evidence-consumption failure, not
proof that the measurements were scientifically accepted or rejected. Its next
correction wrote an actual JSON report but repeated the same unassessed evidence
request and appended another status object. The controller halted the task.

Explicit transport recovery is now bounded per stable task identity, rather than
one allowance shared by all tasks. The legacy experiment authorization remains
unchanged and consumed. A separate spatial authorization was recorded only after
the dependency handoff and exact-response checker changes passed tests. The helper
reproduces the saved native transport error; schema, scientific, test and retention
validation failures cannot use this path. It preserves old attempts, reports,
fingerprints and native child identity. Neither task may receive another explicit
repair. `matter_report_check.py` also checks report freshness and returns the exact
single terminal response, with no appended status footer. Twenty checker/recovery
tests pass; future dependency/intake/controller tests also pass.

The current real CLI is `cli-job-1793068718862103800`, resuming the same private
parent and Step child through the existing gateway. Inspect that owned process;
never start another copy while it is running or unknown. No physical qualification
or successful reuse is claimed from these repairs.
Step attempt4 read the pinned manifest and accepted experiment report3, wrote
its own report, corrected an invalid leading plus sign, and ran the report
checker. Its exact single terminal envelope was accepted as `NEEDS_EVIDENCE` at
1793070451.1747358. Qwen read that report and dispatched `research-942eb2b59d`
through the actual `chimera-researcher` profile. The new question concerns native
contact-gradient scaling and friction-force export. Evidence:
`alloy-real-01/spatial-accepted-1793070647963348500.json`. This is an actual
accepted-evidence and recovery handoff, not physical qualification. Source facts,
instrumentation effects and complete energy accounting remain unresolved.

Automatic invalid-report correction now counts the uninterrupted error streak
since a controller-validated terminal report. Native failures, empty attempts,
claimed statuses and an explicit reopen do not reset it. A subsequent valid
evidence cycle can receive one ordinary correction; two consecutive invalid
reports still stop the task. Historical reports, repeated-need fingerprints and
both consumed explicit repair allowances remain unchanged. Five focused tests
and 99 affected controller/dependency/intake/recovery/checker tests passed in
13.815 seconds. These are CPU workflow checks, not local-model or physics tests.

The real research run exposed a retrieval limitation: local Strata WebFetch uses
keyword-selected excerpts, even when asked for an entire function. The installed
tool has no full-text override; it saves some large extracted-text responses as
native artifacts but omits their paths from model-visible text. The narrowly bound
`matter_research_guidance.py` PostToolUse hook now explains this to the executing
research/evidence child and exposes only supplied, existing artifact paths inside
that child's native artifact directory. Read/Grep can inspect those files. Missing
lines must remain unknown; bounded raw-source acquisition can be requested through
the existing experiment worker without changing native physics. Six focused and
37 affected hook/controller tests pass. This changes neither installed Z Code nor
agent profiles and does not interrupt the current child. Actual use of the new
guidance still needs observation; code-path and CPU checks alone do not prove it.

`matter_web_evidence.py` now archives bounded native WebFetch/WebSearch receipts,
their displayed excerpts and any owned extracted-text artifacts at a terminal
research handoff. Parent call, child/profile, prompt hash and attempt timing are
checked against native records. The immutable manifest remains separate from the
agent's claims. Missing or oversized observations stay explicit; no fetch or model
call is added. Bindings and bookkeeping are protected but cannot satisfy a review's
source-body citation. Archive/database failures preserve active ownership and do
not consume a malformed-report correction. Focused archive tests passed 12 of 13;
the real symlink fixture was unavailable, while simulated Windows reparse rejection
passed. The affected integrated suite passed 77 checks with that one skip.

The real research attempt completed at 1793072234.689238, just before terminal
archiving was installed, so its first report has no retroactive archive field.
It returned `NEEDS_EVIDENCE` with source-based scaling findings and a narrower
friction question. Qwen dispatched `experiment-ee8ac5cfb7` to analyze already-owned
arrays first, with a conditional native diagnostic only if still necessary. Its
claims and new measurements remain subject to Step and independent qualification.
Original reports are not rewritten to make them appear archived or qualified.

That worker returned a structurally accepted report at 1793072932.0950646. It
found nonzero transient friction gradients in the saved arrays and did not trigger
the conditional GPU rerun. Its force/work interpretation still requires review;
the report explicitly leaves complete friction work unresolved. Qwen resumed the
same researcher at 1793073001.5923445, and native Read receipts show it opened both
the new experiment report and its earlier findings.
The researcher then inspected the actual result file and returned READY at
1793073847.2035956. Qwen resumed the original Step child for spatial attempt5 at
1793073875.0981052 with a pinned manifest of both experiments and the research.
Step remains the reviewer of these claims; no physical acceptance is inferred
from research READY. The actual gateway subsequently showed Step 3.7 IQ4_XS
running with one queued request; the native profile retains high reasoning.

Future research resumes now preserve available historical web observations before
native metadata is overwritten. `capture_prior` verifies the old terminal and
archives separately; the new brief/attempt pins those references while old attempts
stay unchanged. Missing historical binding is an explicit unknown, and changed
already-archived bytes refuse. This particular resume began before that integration
and has no retroactively inserted prior-source policy. A read-only metadata snapshot
was preserved separately for audit. Historical and current source bodies can inform
review; bookkeeping alone cannot satisfy the result-citation gate.

The final affected CPU suite ran 112 tests: 111 passed and the real symlink fixture
was skipped. After a native-ordering correction, 24 of 25 archive/handoff checks
passed with the same skip. A parent SendMessage receipt may still be running during
PostToolUse; completed child metadata and exact native identities remain required.
Logs: `Runtime/zcode-matter-workflow-20261026/web-handoff-cpu-final.txt` and
`web-handoff-terminal-order-check.txt` under the workspace root. No second installed
CLI mock or model run was started alongside the live workflow.

`alloy-real-01/handoff-cost-1793066425469003400.json` records actual router
model-switch events and waits of 248.975 and 200.612 seconds during resumed
handoffs. The host log cannot attribute each event to a particular agent request;
model selection can precede lazy loading. These are neither full task latency nor
launch-to-first-token measurements. No model settings or installed CLI code were
changed to address them.

`matter_activity.py BUNDLE` reads only the bound parent and children matched to
controller dispatch/profile identities in the private native session database.
It reports tool timings, explicit failure receipts and repeated identical
tool/input hashes without exporting prompts, commands or output bodies. Eight
CPU tests check ownership, read-only access, timing overlap, missing data and
redaction. The first real snapshot recorded 165 experiment tool calls and 13
explicit failure receipts; this is more detailed than the controller's one
research detour. Repetition is not automatically waste, and a completed tool is
not proof of either command or physical success. Parent/child intervals overlap;
do not add them as elapsed task time. Resource sampling remains separate and
incomplete between observations.

## Checkpoints and commands

The resumed Step attempt5 received the exact new brief pointer in its persisted
user message, then wrote a draft without a new Read. Its draft cited only the
older experiment; the existing checker rejected the missing two dependency
assessments. This is an observed evidence-use failure, not a SendMessage delivery
failure or a physics result. The same child remains owned; no restart was used.

`matter_assignment_access.py` now opts future private attempts with pinned
dependencies into an access check. Before Write/Edit/Bash/report tools and again
at report acceptance, it requires the current brief and manifest to have actually
been returned by native Read during that attempt. Every accepted report must also
have been returned; an older read of identical pinned report bytes can be reused.
It checks numbered output coverage, current hashes and native dispatch identity.
Cached reminders, partial reads, Write metadata and serialization-truncated output
cannot masquerade as complete access. Read tools remain available. Database/binding
failures retain ownership without consuming report-format retries. Current
attempt5 and historical attempts were not given a new acceptance contract.
These checks establish access, not comprehension, correctness or an OS sandbox.
Future brief rendering also stops replaying an expired repair's old file target;
the original purpose, attempts and consumed allowance remain in the checkpoint.

CPU validation: `assignment-access-cpu-final.txt` records 105 passing affected tests
in 13.530s. A read-only replay identified the four missing files in the real Step
session and reused its previously accessed original experiment report. This is
not evidence that a live future attempt has passed the new gate. The native mock
fixture now reads the issued brief, but was not rerun beside the real CLI.
The dependency-review error now returns the exact current brief/manifest pins and
missing accepted report paths, rather than forcing the agent to inspect validator
source to locate its inputs. A read-only replay on the attempt5 draft identifies
the new friction experiment and research report, preserving draft and state bytes:
`alloy-real-01/dependency-diagnostic-replay-1793076273861087100.json`.
The 62 affected dependency/checker/controller tests pass (9.862s). This improves
error recovery guidance without accepting the draft or supplying an assessment.
The live Step checker subsequently returned this diagnostic, and native receipts
show the same child opened the current manifest, new experiment and research
report. See `dependency-diagnostic-live-1793076605828710000.json`.
The subsequent terminal report was accepted as `NEEDS_EVIDENCE` at
1793077364.432346, with all three dependency assessments. Qwen dispatched
`research-49bf442359` at 1793077637.892159 to investigate per-substep slip/velocity
export for friction-work closure. The receipt is
`alloy-real-01/spatial-accepted-next-research-1793077663574482500.json`.
This demonstrates real research escalation; it does not qualify the source
scaling claim, pairwise Coulomb behavior, full energy ledger or construction.

The installed Z Code wait helper also omitted `chimera-spatial` from its existing
Chimera-role matcher. Its resumed spatial child therefore used ordinary background
delivery and ten-minute TaskOutput deadlines, waking Qwen while Step was working.
The matcher now includes that role, preserving all other bytes and roles. The
18-byte correction passed 15 extracted-native-function CPU cases and a complete
syntax check. Hash-guarded installation used normal Windows elevation, retained
a rollback preimage, and restarted nothing. Receipt:
`spatial-wait-coverage/installed-1793076901252073500.json`.
It affects future CLI processes; the already-running Node process keeps its old
loaded code. A live handoff through a newly started process still needs verification;
do not claim a measured speedup or restart the current child to demonstrate it.

Final Step review now has an executable correction path when a passed suite
missed a construction defect or needs an additional independent test. New final
review attempts pin a correction contract. A `NEEDS_EVIDENCE`/`FAILED` report can
use `needs.kind=review_correction`, with `needs.correction.target` set to
`implementation` or `qualification` and `acceptance_ids` naming the affected
original requirements, plus the usual question, assumption, measurement and
decision. `matter_review_recovery.py` preserves the review, tested artifact bytes
and test receipt, then schedules spatial diagnosis, optional additive test
authoring and independent Step approval, implementation, fresh tests and the same
final reviewer. Delivery remains dependent on that reviewer. Existing tests,
input bytes and thresholds stay unchanged; this path does not authorize relaxed
criteria or a changed request. Existing test-attempt limits and repeated-question
detection apply. Historical claims can resolve to exact archived baseline bytes;
current protected inputs and latest tested files still receive direct checks.

The latest correction regression checks include actual `recover_native` recovery
after an interrupted state save with a smaller native response envelope. The first
native response is preserved and its usage is counted once; changed findings or
file-report bytes refuse before rewrite. Fifteen focused and 51 affected CPU tests
pass. These are controller tests, not a real-model final-review or Blender pass.
No existing attempt was retrofitted with the correction contract.

The live research49 draft was rejected because `evidence_paths` contained a URL;
Qwen resumed the same child and accepted its corrected report, then resumed Step
spatial attempt6. The new report proposes computation from saved substep positions;
the computation and full energy closure are still unqualified. See
`alloy-real-01/research-accepted-spatial-six-1793079377515978200.json`. Attempt6 has
the new assignment-access policy, and its first recorded Read opens the current
brief. A complete access-gate pass is still pending.

That report rejection exposed a source-retention gap. New terminal responses now
receive a raw-envelope hash even if structured validation rejects them. A future
retry can archive the bound child's web observations from that rejected response,
explicitly labeled `report_validation=rejected`; this never accepts its claims.
Native child, call, prompt, completion and time bounds still must match. Altered
envelopes and old rejected reports without the recorded hash remain unavailable.
Validated-report descriptors keep their existing format. The already-issued
research49 attempt2 was unchanged; attempt1's prior archive remains unavailable.
The final combined controller/recovery/archival/accounting run completed 146 CPU
tests in 17.320 seconds: 145 passed and one host-dependent symlink case skipped.
See `Runtime/zcode-matter-workflow-20261026/review-web-activity-cpu-final.txt` under
the workspace root. No additional native CLI, inference or GPU run was started.

Run `C:/Python314/python.exe -B` followed by
`D:/Chimera-Maintenance/PythonChimera/tools/zcode/matter_workflow.py` and:

```
create ABSOLUTE_NEW_RUN_DIRECTORY --request ABSOLUTE_REQUEST_JSON
status ABSOLUTE_RUN_DIRECTORY
next ABSOLUTE_RUN_DIRECTORY
tests ABSOLUTE_RUN_DIRECTORY
recover ABSOLUTE_RUN_DIRECTORY
seal-ontology ABSOLUTE_RUN_DIRECTORY
answer-intake ABSOLUTE_RUN_DIRECTORY --answer UTF8_ANSWER_FILE --needs-sha256 QUESTION_HASH
reopen-report ABSOLUTE_RUN_DIRECTORY --task-id ID --reason CONCRETE_REASON --remediation NEW_REMEDIATION
```

`recover` reads private native metadata/session records for the exact pending
parent tool-call ID. It recovers a completed report or records a terminal native
failure; running/unknown children retain ownership. Time alone cannot authorize
another child. Test jobs retain launch intent, PID plus process-creation identity,
logs and terminal receipts. Recovery inspects the same job and reuses completed
test results. A transaction lock is reclaimed only for a verified dead identity.

The outer CLI helper uses a detached owner. Inside Z Code's Windows Bash job,
test helpers explicitly inherit that job's lifetime: the controller observes them
through completion. Z Code denies breakaway there; a failed attempt and the fix
are retained in `native-wiring-1793056907213223000`. If the parent is interrupted
and no terminal receipt survives, the test remains **unknown**, not PASS or an
automatic retry. The timeout is an overdue signal, not proof the process stopped.
Daemonized descendants are unsupported by this helper; GPU jobs keep their
existing reservation/process-tree owner.

Recorded metrics currently include elapsed workflow time, dispatch-to-report time,
native-reported child duration/tokens, test time and rework. Missing native usage
is counted explicitly; aggregate totals cover known terminal child reports only,
excluding coordinator work and requests without those receipts. Installed native
code computes these values from each executeTurn invocation, including resumed
invocations; a cumulative-across-resume defect was not established. Child wall
duration includes tool execution and waiting and is not inference generation time.
`matter_observe.py sample ABSOLUTE_BUNDLE` appends read-only observations of exact
CLI process identities, CPU/memory/I/O counters, host GPU telemetry, gateway state
and the paused production goal. `report ABSOLUTE_BUNDLE` summarizes those samples.
The first real run has actual observations. CLI counters exclude the external
inference server; GPU/gateway samples describe the host, and between-sample peaks
can be missed. Reload/prefill breakdown and cross-request reuse costs remain
unmeasured. Do not present sampled CPU time or native RAM loading as full latency.

`matter_activity.py ABSOLUTE_BUNDLE` now reads actual per-message usage metadata
for the bound coordinator and children. It separates completed responses from
pending counters, retains cache counters separately, and deduplicates compaction
receipts by native operation ID. It never reads response bodies. Seventeen CPU
tests pass. Actual replay is recorded in
`alloy-real-01/native-activity-usage-1793078067034766400-summary.json`: six bound
sessions and three compactions, with recorded spans of 261.839, 172.462 and
595.296 seconds. These spans are not model generation time; compaction inference
usage remains unknown. Workflow elapsed time, response/tool spans, host samples
and terminal-child receipt sums are distinct measurements and must not be added
together. A complete task/reuse comparison still requires finished constructions.

Known recovery/preservation boundaries: native Z Code can leave child metadata
marked running after some early startup failures. A parent tool error does not
prove that child stopped, so this controller retains ownership pending exact
native terminal evidence. Also, write-capable children are constrained by their
assigned scope and hash checks, not by a separately established OS filesystem
sandbox. No claim is made that the hook intercepts arbitrary child shell writes.
Actual originals and production configuration must remain byte-identical.

`test_matter_workflow.py` exercises CPU failure cases. `test_matter_native.py`
creates private sessions/providers and a loopback endpoint; it never contacts the
real gateway. Passing either is not real-agent or scientific proof.

## Required remaining work

- Demonstrate real-agent planning, experiment escalation and interruption
  recovery; the implemented controller and CPU fixtures alone do not prove them.
- Have actual Qwen and Step 3.7 execute the aluminum/stainless/alloy workflow.
  Existing `ChimeraStudio/integration/MATTER_RULE_LEARNING.md` and source adapters
  provide a bounded offline elastic-energy fit and DFT lineage. Complete
  inter-material work/energy accounting and temporal CA evolution remain absent.
- Run actual native/physical references, held-out checks and Blender deformation,
  interaction, editable construction, save/reopen/replay tests. Preserve failures.
- Admit qualified recipes, rules, sources, experiments and procedures through
  existing ontology/asset owners; demonstrate a different construction with less
  repeated work and measured full-task/resource costs.

The overall goal remains active. Keep water deferred and preserve prior work.
