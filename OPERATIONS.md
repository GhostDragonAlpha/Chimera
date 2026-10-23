# Shared Blender construction operations

Use **N > Chimera > Shared Human / AI Operations** in Chimera Blender. Inspect,
choose an action, enter a purpose and parameters, preview, then apply. The visible
proposal is also the proposal used by a local AI caller. Target UUIDs survive names;
intervening source/native changes refuse the proposal before execution. Make a
new proposal after inspecting changed inputs. Retrying an already delivered ID
returns its outcome without repeating the edit.

## Local Python entry point

Run inside this Blender process on its main thread, for example from the Python
Console. This does not start a network endpoint or connect Z Code automatically.

```python
from chimera_studio import operations as matter
state = matter.inspect()
ids = [p['id'] for p in state['parts'] if p['id'].startswith('membrane:')]
proposal = matter.propose('build_films', ids,
                         purpose='Inspect the support response of this construction')
# The same proposal is visible in the sidebar before application.
result = matter.apply(proposal['id'])
result = matter.status(proposal['id'])
```

Use explicitly selected source IDs when a scene contains multiple assemblies.
Hidden computed sources must be returned to authoring before editing. Use the
`authoring` action or Return to Matter Authoring: it now retains the confirmed
checkpoint, reveals sources and releases its helper. Rebuild accepts a new result
only after native validation and preview success. Saving in authoring preserves
both the edits and the last physical checkpoint; they are separate states.

| Action | Parameters | Existing owner |
| --- | --- | --- |
| `create_films` | `{}` | Pinned mechanism-factory three-film starter |
| `assign_surface` | `{"gamma":1.25}` | Native current-area material, J/m2 |
| `mark_apex` | `{"vertex":0}` | Existing fan apex selection |
| `connect_apices`, `disconnect_apices` | `{}`; exactly two source IDs | Existing explicit apex connections |
| `build_films` | `{}`; 2â€“6 film IDs | Existing compiler and private native GPU session |
| `apply_load` | `{"load":0.8}` | Existing center load, N |
| `resume`, `release`, `authoring` | `{}` | Existing checkpoint/owned helper lifetime; authoring preserves edited sources and the accepted trial |
| `replay` | `{"checkpoint":0}` | Existing confirmed native history |
| `duplicate_layers` | `{"offset":[2,0,0]}`; closed libuipc selection | Installed construction copier and native seam metadata |

A mixed-surface-tension joined assembly still refuses. The wrapper does not add
new physics or silently repair unsupported geometry. Libuipc duplication requires
its materials profile and a new bake; its cached replay is not a native checkpoint.

## Outcomes and recovery

- `proposed` has made no edit. Discard it or apply it after review.
- `queued`/`running` means the native result is pending. FINISHED from a Blender
  operator confirms submission only. Poll `status(id)` or inspect the panel.
- `succeeded` means the native result/presentation completed, or the synchronous
  authoring action returned. Inspect `native_result.accepted_state_id` when present.
- `failed` supplies an error. Native connection failure preserves the confirmed
  checkpoint for explicit resume. A replacement failure retains the old result;
  a lost result after in-place mutation closes its uncertain owner. A context-recovery error may follow an applied
  edit; inspect the scene before creating a retry. Mutation failures are not
  automatically retried or claimed to be universally transactional.
- `interrupted` means the saved file lacks the live job or its owner closed. Inspect
  the retained checkpoint and explicitly choose a new command. Reopen never starts
  simulation or claims an unfinished operation succeeded.

Ordinary `.blend` saves store up to 64 records in `Chimera Operations.json`, with
purpose, targets, parameters, expected revisions and outcomes (512 KiB maximum).
This is bounded session history, not a second recipe/evidence database. Native
checkpoint serialization remains owned by `gpu_workspace` and its runtime lock.
Inspect returns `source_matches_native`, `needs_rebuild` and `source_note` for a
compiled assembly. It compares physical geometry/material/connections without
requiring labels to stay fixed; a new source edit does not rewind native state.
Blender Undo is not native Undo. Use explicit Replay/Resume for physical recovery.
Inspect also returns `connections`: one entry per apex weld, with `edge` (the two
part IDs), `names` (current film names), `authored` (edge in the scene connection
list), `accepted` (edge in the compiled assembly of the accepted native build)
and the derived flags `stale` (authored, not in the accepted build) and `missing`
(in the accepted build, no longer authored). The Membrane Assembly panel draws
one compact line per weld with the same state. This is bookkeeping for connection
repair: it names which weld differs and changes nothing about which connections a
build compiles, and it reports no reaction forces (the panel's attachment scope
note stays).

## Measured scope

`evidence/shared-operations/acceptance.json` links actual Blender/native checks,
installed libuipc authoring, fresh reopen and the real-window screenshot. They
cover Edit Mode/selection preservation, compiler parity, stale refusal, duplicate
delivery, source/rebuild correspondence, an actual owned-helper failure, exact
checkpoint recovery and pending-save interruption. Saved pending is exercised
with a deliberately held live Future, rather than claiming a naturally stalled
GPU. The first selection-restoration crash and repair are recorded separately.

The external local client below connects these commands to Z Code's terminal.
No arbitrary script executor, multiscene native-world support, all-mode adapter
or automatic native undo is implemented. Saved native comparison
is implemented in the scoped adapter below.
The full fifteen-technique sequence remains in GAME_PLAN_ACTION_RPG.md section
12.2. The unregistered `workshop_lab.py` draft is not tested product functionality.
Water stays deferred. No original user project or model service was changed.

Rebuild recovery now has separate evidence in `evidence/rebuild-recovery`: real
candidate upload and partial-preview failures, successful owner replacement, a
lost response after actual native mutation, authoring retention and pending-save
fresh reopening. Edited geometry/materials/deleted connections remain authored;
preview rollback does not silently undo them. Native physics and runtime identity
are unchanged. Broader import transactions and automatic native Undo are not
claimed by these checks.

## Saved native pair commands

`capture_trial` takes `{"slot":"A","label":"Baseline"}` (or B); `compare_trials`
takes `{}`. Both use no part targets. Their shared proposals retain the purpose
and pair revision; captions/purposes as well as physical IDs invalidate stale
proposals. `compare_trials` reports its actual separate job outcome through the
same `status()` call. Re-delivery returns the previous outcome, never another run.

```python
r = operations.propose('capture_trial', params={'slot':'A','label':'Baseline'},
                       purpose='Choose a supported response for the construction')
operations.apply(r['id'])
# Author, rebuild, load and capture B through the existing commands.
r = operations.propose('compare_trials', purpose='Inspect the measured alternative')
operations.apply(r['id'])
operations.status(r['id'])
```

The pair captures the confirmed native state even if source edits await rebuild.
It is bounded to two documents and a 20 MiB save budget, independent of the 64
command records. Native computation stays in the existing owner; captured images
are observations, not proof of a new law. The `select_pair` helper is deliberately
pinned from the existing recipe runner, with its source and slice hashes, without
copying that runner's B4 qualification scope. `trial_compare` is the local UI
adapter. Evidence and limits: `evidence/trial-comparison/acceptance.json`.

`cancel_comparison` takes `{}` with no targets. It requests interruption;
poll the original comparison to its terminal state. Both comparison and material
search cancellation proposals bind the exact active job ID. A stale cancellation
cannot affect its successor, and a cancellation for the other task kind refuses.
The human Cancel button is shown while its comparison is pending.

Native comparison now shares the search's external Python, owned-process lifetime,
140 s hard deadline and 3 s cancellation grace. Original native startup/request
limits, exact replay/capture, receiving validation and independent checks remain.
File replacement closes the owned job immediately. View A/B uses the active
viewport/Image Editor before falling back to another image area. Evidence:
`evidence/external-comparison/acceptance.json`. Live native-workspace computation
still needs its separate persistent-worker migration.

## Existing recipe references

`link_evidence` takes no part targets and parameters such as
`{"target":"A","recipe":"assembly.star-k2"}`. Targets are CURRENT/A/B;
records are assembly.star-k2 and piece.patch-equilibrium. Supply the construction
purpose as with other commands. The shared proposal binds native/pair/reference
revisions and rechecks the pinned owner dependencies before acceptance.

```python
from chimera_studio import operations, recipe_evidence
p = operations.propose('link_evidence',
    params={'target':'A','recipe':'assembly.star-k2'},
    purpose='Reuse the known load range while retaining native constraint checks')
operations.apply(p['id'])
report = recipe_evidence.inspect('A')
```

`linked_reference` means the reference is bound to this checkpoint; inspect the
owner record validation, each receipt's source freshness and applicability fields
separately. It never means native qualification. `target_changed` requires explicit
relinking; `unavailable` names a missing/changed dependency and retains the prior
reference. A failed replacement keeps the previous readable report. Check/Report
perform no native computation; opening a saved file rechecks references offline.

The 27-file pinned snapshot reuses the original piece_record/receipt_adapter
implementations and their citations. Relevant dependencies are hashed on each
request; unchanged inputs reuse validation. Changing unrelated scene objects or
an unrelated record's dependency does not invalidate the target reference.
Existing failed table/learned reductions stay visible. No new qualification rule,
solver-response cache, automatic snapshot refresh or separate database is added.
Scope and measured checks: evidence/recipe-evidence/acceptance.json.

## Existing libuipc layer trials

The GPU Materials profile adds four shared commands, all with no part targets:

| Action | Parameters | Outcome |
| --- | --- | --- |
| `capture_layers` | `{"slot":"A","label":"Attached"}` | Bind the verified current bake and purpose; no copy or new solve |
| `compare_layers` | `{"seconds":0.6,"focus":"physical-part-id"}` | Equal-time cache measurements and changed input groups |
| `show_layer_trials` | Same as compare_layers | Independent nonphysical A/B mesh copies, original construction untouched |
| `clear_layer_preview` | `{}` | Remove only comparison copies; references/results remain |

Use the object's `uipc_object_id` for focus. An empty focus uses the panel's
Measured Part object or the current active part. This human field is an ordinary
Blender object picker. Inspect/propose/apply/status use the same operators as the
panel, bind the pair revision and refuse stale delivery. Edit Mode capture uses
the existing selection-restoration mechanism; removing a selected comparison
copy now skips the deleted object when restoring incidental selection.

Saved trials reference existing request/input/result/cache bytes and decoder
identities. The original protocol validates their meaning. No extra receipt
admission policy or database is introduced. Stored samples use equal simulated
time; float32 UI representation error never authorizes interpolation. Changing
multiple input groups remains a comparison, not an isolated causal explanation.

The .blend retains references, purpose, measurements and any observational meshes.
References remain absolute across Save As; moved external cache folders can now
be relinked explicitly through `relocate_layer_cache` after exact identity checks. Reopening starts no solver. Compare checks
files again; the saved preview alone is not proof of current cache availability.
Scope, failures and timing: evidence/layer-trials/acceptance.json.

## Infer and instantiate a reusable assembly

`learn_assembly` takes `{"name":"Flexible support"}` and no targets. Its proposal
binds both A/B and stored-template revisions. `instantiate_assembly` takes
`{"gamma":1.5}` and no targets; it binds the stored template and authoring state.
Both require a construction purpose. They use the same operators as the human
Reusable Assembly panel and preserve mode/selection through the shared adapter.

```python
from chimera_studio import operations, reusable_assembly
p = operations.propose('learn_assembly', params={'name':'Flexible support'},
    purpose='Reuse these known films and connections for a material choice')
operations.apply(p['id'])
p = operations.propose('instantiate_assembly', params={'gamma':1.5},
    purpose='Create another editable support with the chosen surface tension')
result = operations.apply(p['id'])
# Inspect exposes new independent part IDs; build_films remains explicit.
operations.inspect()
```

The only inferred parameter is uniform surface tension under the existing fixed-rim,
Z-rail apex law. Creation calls the existing authoring importer and checks compiled
physical arrays before accepting; failure removes only newly created datablocks
and restores connections. No native state is replaced until an explicit build.
The one bounded data template is embedded as `Chimera Reusable Assembly.json`,
with provenance and compiler identity. It cannot execute arbitrary code and is not
a new qualification record. Changed compiler bytes or corrupted saves refuse;
missing historical A/B references are distinguished from invalid template data.

## Bounded native material search

All three actions take no part targets and use the same panel operators:

| Action | Parameters | Outcome |
| --- | --- | --- |
| `search_material` | `{"gammas":[0.75,1,1.5,2,3],"load":0.8,"target":0.05,"tolerance":0.01}` | Asynchronous native observations using the stored assembly |
| `cancel_material_search` | `{}` | Request interruption; poll the original search until terminal |
| `select_material_result` | `{"index":3}` | Explicitly replace A/B with this measured candidate's unloaded/loaded checkpoints |

```python
from chimera_studio import operations, material_search
p = operations.propose('search_material',
    params={'gammas':[0.75,1,1.5,2,3], 'load':0.8,
            'target':0.05, 'tolerance':0.01},
    purpose='Choose a compliant support with about five centimetres of travel')
operations.apply(p['id'])
operations.status(p['id'])  # Poll until succeeded/failed/interrupted.
material_search.report()   # Compact rows and checkpoint hashes, no full meshes.
```

A learned template is required; pending proposals bind its revision. Selection
binds the completed-result revision. Re-delivery returns the existing command
outcome. Failure retains previous completed evidence. A succeeded search can
still have no matching candidate: inspect `within_tolerance` and each row.
Failed candidates cannot be selected. Final measurements recheck native state,
render correspondence and the pinned independent reference before publication.

The search launches the existing pinned external Python under a Windows job;
its private native helper is reused across candidates and closed afterward.
Native startup/HTTP deadlines are unchanged. Search checks a 120 s budget between
native calls; the parent enforces a 140 s hard deadline and 3 s cancellation grace.
These are task limits, not changed solver tolerances. No automatic retry/install.
A saved pending job becomes interrupted on reopen. Full evidence is embedded in
`Chimera Material Search.json`; logs/outcomes stay in `.user/observations`.
The external local client below exposes this API to Z Code's terminal tool.

## Persistent native ownership and UI status

The existing build/load/replay/resume actions now submit typed commands to one
persistent private process. Main-thread timers accept its validated replies.
`operations.status(id)` may advance/accept work: call it from a timer or operator,
not `Panel.draw`. Panels use `operations.peek(id)`, which copies cached status
without touching Blender data. A registered timer updates pending command records.
The proposal schema, UUIDs, purpose, idempotency and stale-source rules are unchanged.

A build/resume candidate replaces the accepted owner only after presentation.
Lost replies, deadline expiry and process failure return terminal failure and keep
the last confirmed checkpoint for explicit resume. Release/file replacement close
only owned processes. The private `gpu_workspace._session` is now a proxy; direct
HTTP fault-injection tests belong to `gpu_native.GpuSession` in an external process,
not to that Blender proxy. Native physics/checkpoint schema and tolerances did not
change. Fixed-view and supported viewport rendering now have separate qualification
in `evidence/viewport-camera`; arbitrary camera objects/roll/native FOV remain open.

## Render through the shared workflow

`render_native` takes no part targets and exactly `{"view":"VIEWPORT"}` or
`{"view":"FIXED"}`. VIEWPORT reads the chosen 3D editor's perspective orbit on
Blender's main thread. Use a context override for a particular viewport. FIXED
also works in a background session; an explicit VIEWPORT request never silently
falls back. The same human Native Render operator and persistent owner execute it.

```python
p = operations.propose('render_native', params={'view':'VIEWPORT'},
                       purpose='Inspect the loaded support from the current construction view')
operations.apply(p['id'])
operations.status(p['id'])  # Wait for succeeded/failed/interrupted outside Panel.draw.
```

The proposal binds the converted camera request as well as source/native state;
moving the orbit invalidates it. Rendering retains mode/selection/unfinished
edits and modifies no physical state. The saved packed image's
`chimera_native_view` property records the camera, mapped probes, pixel/state/render
hashes and framing warnings. This is evidence metadata, not another physics owner.

## Mounted shell starter

`create_mounted_panel`, no targets, parameters `{"origin":[0,0,1]}`, uses the
same `chimera.add_mounted_panel` operator as the human button. Requires the
installed libuipc profile and Object Mode with meter units. Adds editable rods,
shell and sixteen native stitches; no bake starts. Existing shared revision,
purpose, duplicate-delivery and saved-history checks apply. Root supports are
fixed rod nodes. Evidence: `evidence/mounted-panel/acceptance.json`.

## Diverse geometry/material choices

`search_designs` takes `{"gammas":[0.75,3],"scales":[0.7,1],"load":0.8,"band_width":0.06,"bands":3,"budget":9,"seed":17}`.
It operates on the current reusable assembly, retaining the smallest XY footprint
in each movement band. `cancel_design_search` has no parameters and binds the
current job. `select_design` and `create_design` take `{"index":N}`, where N is a
measured elite's trial index returned by `design_search.report()`. Selection uses
existing native A/B; creation uses the existing transactional authoring importer.
Current geometry and physical checkpoints are retained; saved purposes/lineage
survive compression through the compact report and ordinary .blend persistence.
See `evidence/design-search/acceptance.json`; scope and physical limits remain explicit.

## External local client (implemented, October 19)

In the intended Blender window use **N > Chimera > Local Z Code Connection >
Enable Local Z Code Client**. The pinned Python CLI can then inspect and operate
that window from Z Code's existing terminal tool. There is no model/runtime
configuration change. As an explicit per-launch opt-in you can instead start
with `Start Chimera Studio.cmd -EnableClient`, which runs the same enable
automatically (the default stays opt-out — same trust as the click). Opening a
file stays offline; enable a fresh connection
for that file. Changing scenes/files, closing the window or disabling the addon
closes the old session. Disabling the client leaves any existing native job alone.

From `D:/Chimera-Maintenance/ChimeraStudio/integration`:

```powershell
& '../Libuipc/.venv/Scripts/python.exe' -B tools/studio_client.py sessions
& '../Libuipc/.venv/Scripts/python.exe' -B tools/studio_client.py request --session SESSION_ID --file request.json
& '../Libuipc/.venv/Scripts/python.exe' -B tools/studio_client.py wait --session SESSION_ID --operation OPERATION_ID
```

Choose the listed session whose project/scene matches the intended work. The
request file is ordinary UTF-8 JSON; use these messages in order:

```json
{"method":"inspect","args":{}}
```

```json
{"method":"propose","args":{"action":"apply_load","targets":[],"params":{"load":0.8},"purpose":"Check whether this support has useful travel under its intended load"}}
```

```json
{"method":"apply","args":{"operation":"ID_RETURNED_BY_PROPOSE"}}
```

Use the existing action table and explicit part IDs for assignments/connections;
`resume` needs no targets/parameters and starts only Studio's saved native owner.
`inspect.native_history` gives the confirmed cursor/count for an explicit `replay`.
The operation ID, purpose and terminal outcome are the same records the human
panel shows and ordinary Blender Save preserves. `report` accepts `kind` equal
to `history`, `materials`, `designs` or `adaptive`; it returns compact existing-owner results,
not another evidence catalog. A proposal is visible immediately; an authorized
agent may apply it itself without requiring another human approval.

The client uses atomic JSON files under `integration/.user/clients`, processed
by a Blender main-thread timer. It accepts only the typed shared methods, no
arbitrary Python, shell commands or paths to write a project. Use ordinary Save
in Blender. Filesystem access by the local OS account is the trust boundary;
this is not protection against a hostile process with the same account access.
No network listener is opened. One session addresses one window/scene; multiple
3D views refuse a VIEWPORT render instead of guessing. FIXED rendering remains
available. Native rendering may switch the area to Image Editor; Shift-F5 returns
to the 3D View and its connection panel.

**Completion and retry:** `apply` may return queued/running. Wait/poll its operation
ID until terminal. Exit 0 means a valid reply (inspect `status` after apply); exit 1
means refusal/failed/interrupted; exit 2 means transport/input failure; exit 3 from
`wait` means observation expired while the operation was still pending. This never
cancels or resubmits the job. A missing response returns its request ID and an
unknown-execution warning. Retrieve it using `response --session SESSION_ID --id
REQUEST_ID` within 60 seconds; after that inspect shared history before retry.
Requests not started within their deadline (at most 30 seconds) refuse. Replies
are retained for at least 60 seconds; duplicate request delivery retains the first
reply, and reapplying an existing operation ID does not repeat the edit. A stale
Blender heartbeat is a clear connection failure, not evidence of a solver result.

The live test used a separate pinned Python process and actual CLI commands.
It preserved human Edit Mode geometry/vertex selection, refused an intervening
edit, resumed/loaded/rendered/replayed real native matter to its exact prior
state, and reopened the construction offline with operation purposes intact.
Actual scene switches and file reloads closed the connection. The 28 sampled
request round trips had a 0.204 s median and 0.409 s maximum in this small test;
these include the polling interval and are not generation or solver throughput.
No model was invoked and this does not claim a Z Code agent evaluation. Evidence:
`evidence/local-client/acceptance.json`. Wider owner/mode adapters remain work.

## Adaptive target-directed material measurements

`search_adaptive` takes exactly
`{"gammas":[0.75,3],"load":0.8,"target":0.065,"tolerance":0.002,"budget":7,"schedule":"ADAPTIVE"}`.
`FIXED` selects the same-budget reference schedule; budgets are 3, 5, 7 or 9.
The current learned assembly is the source, bound by its revision. The solver
measures every selected candidate; the predictor only chooses experiments.
`cancel_adaptive_search` has no parameters and binds the exact current job.
`select_adaptive_result` and `create_adaptive_result` take `{"index":N}` for an
actual measured trial returned by `report` with `{"kind":"adaptive"}`. They bind
the completed result revision, then reuse native A/B and the existing editable
recipe importer. There is no selectable prediction or automatic source rebuild.

The human panel uses these same actions. Reports preserve purpose, settings,
trial measurements/refusals, acquisition decisions, cost and best observed
selection, omitting bulky checkpoint arrays. No-match is an honest successful
characterization outcome, not a promised design. The 120 s batch / 140 s hard
worker deadline, cancellation, exact native checks, prior-result retention and
explicit interrupted-save recovery match the existing trial workflow.

Typed `assign_surface` and `apply_load` now pass their exact JSON number to the
same native operator rather than round-tripping through a float32 UI property;
ordinary human slider input still uses Blender's normal precision. The checkpoint
wire codec repairs only the representation of a native float32 material decimal
and refuses mismatched bits. Saved source documents and physics remain unchanged.
See `evidence/active-search/acceptance.json` for native measurements, chosen-material
replay, fresh-process continuation, old-design rendering, UI and external report tests.

## Reuse successful construction procedures

`report` with `kind: procedure_candidates` returns compact mined patterns and
source operation references. `learn_procedure` takes `{"candidate":"PATTERN_ID",
"name":"Build and inspect support"}`; its successful operation ID identifies the
retained definition. `report` with `kind: procedures` returns ready/stale definitions,
role counts, typed steps, observed parameter values, purposes and recent run progress.

`run_procedure` takes `{"procedure":"LEARNED_OPERATION_ID","bindings":["membrane:ID0",
"membrane:ID1","membrane:ID2"],"values":{"step_1_gamma":1.8,"step_3_load":0.6}}` for
the tested four-step example. Read the actual definition: role and parameter names
come from its observed sequence. Preview expands the concrete steps; apply starts
them through normal operators, and status/wait tracks that parent operation ID.
`cancel_procedure` takes `{}` and binds the current run; it stops after the in-flight
bounded operation. `forget_procedure` takes `{"procedure":"ID"}` and also works on
stale definitions. These actions use the same purpose/revision/duplicate rules.

Every child operation has its own ID plus a procedure-parent reference. The saved
run identifies completed children, the current child and explicit errors. Retry is
never automatic and starts a new sequence; inspect partial effects/checkpoints first.
Definitions use the existing operation-history Text block, with no second database.
Eight retained procedures are protected from normal history trimming. Source/owner
changes make them stale rather than silently replacing their meaning. Native checks
still run for new part bindings/values. Evidence: `evidence/learned-procedures/acceptance.json`.

Procedure guards now use fresh construction revisions without hashing unrelated
search reports. Child proposals and full public inspection retain their previous
checks/schema. No cross-call cache is introduced. The bounded comparison and
current saved examples are in `evidence/procedure-performance/acceptance.json`;
older learned definitions remain honestly stale after source changes. Relearn
from current successful operations; pending saves never resume automatically.

## Shared layered-material authoring and recovery

Available in the GPU Materials profile, through the existing proposal/apply/status
API and human panel. Target IDs come from `inspect` or `report {"kind":"layers"}`.
Every proposal includes current geometry/FEM topology, materials, attachments,
units, timing, solver/contact/preset settings and active-cache identity.

| Action | Targets | Parameters |
| --- | --- | --- |
| `edit_layer_material` | 1–128 physical parts | `{"values":{"rod_bending":100000}}`; only fields belonging to each part's existing role |
| `apply_layer_preset` | 1–128 same-role parts | `{"preset":"Saved preset name"}` |
| `set_layer_attachment` | None | `{"attachment":0,"values":{"stiffness":1000}}`; also enabled, group_a/group_b, pairing, reverse_b, max_gap |
| `rebind_layer_attachment` | None | `{"attachment":0}` |
| `remember_layer_cache` | None | `{}`; retain exact active-cache identity in the existing saved trial text before moving files |
| `relocate_layer_cache` | None | `{"reference":"ACTIVE","directory":"D:/moved/cache","activate":false}`; reference ACTIVE/A/B, absolute or saved-blend-relative directory; activation also requires current physical inputs |
| `detach_layer_cache` / `activate_layer_cache` | None | `{}` |
| `bake_layers` | None | `{"timeout_seconds":120}`; finite deadline 0.01–3600 s, pinned external Python |
| `cancel_layer_bake` | None | `{}`; binds the active shared job owned by this scene |

Materials/presets reuse installed validation and RNA callbacks. Pins, role and
drive remain intact. Attachment indices come from the current report; the
underlying endpoint groups and existing native bind operation remain editable.
Preflight refuses unsupported fields/ranges. Shared baking supports the explicit
rigid controller target mapping below, using the same existing native drive owner.

`report {"kind":"layers"}` returns part materials, saved presets, endpoint/group
identities, invalid-binding reasons, cache state, changed fields and shared job
status. The human inspection panel shows the last explicit report. Rebind after
endpoint changes; bake after physics changes. Reverted inputs can reactivate a
checksum-verified cache. Detaching removes playback through its existing owner.

Baking returns immediately and completes through the existing main-thread status
poll. Use `status`, including after a lost client reply; duplicate Apply does not
repeat a completed operation. Deadline, cancel, worker failure and changed-input
refusal return terminal outcomes with the old cache retained. Even an immediate
worker failure carries its error. An existing addon timer consuming completion is
recognized without repeating or reattaching the job. A saved pending operation
reopens interrupted, never silently restarted; inspect before an intentional retry.

Evidence: `evidence/layer-editing/acceptance.json`. Tested actual human and local
CLI execution, GPU load transfer/material response, fixed supports, cache recovery,
worker failure/timeout/cancel, fresh completed/pending reopening and native-owner
regressions. Purpose/history are saved. This is cached mesh replay, not full
physical restart or a model-quality evaluation. Keep external cache files with
the saved project.

## Layered procedure bindings

The existing `learn_procedure`, `run_procedure`, `cancel_procedure`, reports and
saved history now support libuipc in addition to native membrane procedures.
`report {"kind":"procedure_candidates"}` identifies observed patterns; the
retained definition/report identifies its owner, steps, role numbers, learned
parameter names, observed values, purpose and runtime dependencies.
`run_procedure` still accepts exactly `procedure`, `bindings` and `values`.
Bindings are ordered `uipc:<part-id>` values for a layered procedure. Use the
steps' role references to assign the intended physical parts. Human **Use Active**
buttons set individual roles explicitly; the existing ID-order bulk binding
remains available. Material/attachment panels remain normal Blender controls.

Attachment operations now accept either the existing integer input or a selector:
`{"attachment":{"a":"uipc:PART_A","b":"uipc:PART_B","group_a":"Edge A","group_b":"Edge B"}}`.
A proposal canonicalizes integer input to that selector before hashing. Add
`values` for `set_layer_attachment`. An ambiguous selector refuses; it never
chooses the first of two matching seams. Reordering the list does not change
which physical endpoints a learned step addresses. Changed group names need
an explicit new binding/sequence.

The miner accepts homogeneous, contiguous successful sequences of 2â€“6 steps.
A layered sequence ends in one completed bake with a verified converged quality
report; numeric fields under material/attachment `values` can become parameters.
Endpoint part references become roles, group names remain literals. It does not
infer an entire machine, insert unobserved commands or mix solver ownership.
Final acceptance reuses the current native cache/archive validation and native
step/convergence report. The saved run records exact cache references and limits.

Native and layered procedures use owner-specific dependency sets. Changed owner
source/runtime makes a definition stale; no automatic requalification or
provenance rewrite. A running layered procedure also guards solver/contact/time
settings and cache identity between steps. Stop-after-current-step retains
partial work. Existing `cancel_layer_bake` can stop an owned in-flight bake;
failed/cancelled children propagate their terminal status to the parent.
Fresh pending saves reopen interrupted without execution. See
`evidence/layer-procedures/acceptance.json` for actual human/CLI, replay and
adjacent native-procedure regressions.

Cache relocation uses the existing trial archive validator and native playback
attachment transaction. `report` with `{"kind":"layers"}` includes
`saved_cache_references` (location, identity, label and purpose). Remember and save
before moving an active cache; A/B capture already stores identities. Missing
original folders do not prevent relinking a matching new folder. Apply rechecks
all bytes and the proposal's saved-reference revision. A/B measurements retain
their original identities; no cache copy, simulation or automatic retry occurs.
Older saved files remain readable. New menu entries append without renumbering
existing Blender operation enums. Evidence: `evidence/cache-relocation/acceptance.json`.


`set_component_representation` takes one `uipc:ID` and
`{"representation":"AFFINE","rigidity":100000000}` or representation `FEM`.
It changes authored rest geometry, not a live physical state. The original
mesh/groups stay in the blend; existing native seams receive an explicit boundary
index remap. `compare_component_trials` takes that same part and
`{"position_m":0.002,"force_relative":0.1}` after the existing A/B captures
(detailed A, affine B). It checks all saved frames, identical surrounding inputs,
converged native steps and matching runtime, retaining the result with the existing
trial references. `report layers` exposes `component_reductions` and
`component_comparison`. Source revisions include saved detailed meshes/metadata;
A/B changes invalidate a reviewed comparison. No new worker or response catalog.
Restore detail before duplication or topology edits. Current authoring cap:
20,000 nodes / 100,000 tetrahedra; synchronous comparison cap: 601 frames / two
million part-node samples plus the existing 256 MiB archive limit. Eight fresh
reopen samples, full native fingerprint restoration, human/CLI Edit Mode
preservation and a measured soft-material rejection are in
`evidence/component-reduction/acceptance.json`.

`learn_native_warm_start` takes no parameters and learns from the live owner's
existing balanced native membrane checkpoints. Supply the normal proposal purpose.
`set_native_warm_start` takes `{"enabled":true}` or false and explicitly replaces
only Studio's helper, preserving accepted state and live replay history. Existing
`apply_load` then uses GPU-checked guesses inside the trained range. `inspect`
reports `native_warm_start` and `warm_start_revision`. Model changes invalidate
pending load/mode proposals. The saved Text model and variant identity survive
normal .blend saving; reopening never launches a helper automatically. Human
panel buttons call these same operations. No layered/libuipc commands change.
See `evidence/native-warmstart/acceptance.json` for actual UI/CLI/reopen checks and
the small measured full-operation benefit. Default continuation remains available.


`bake_layers_checkpoint` takes `{"timeout_seconds":120}`. `continue_layers`
takes `{"end_frame":81,"timeout_seconds":120}`. Both are asynchronous shared
operations, with the ordinary status/deadline/cancel behavior. They use the same
pinned libuipc worker through a separate loop/checkpoint adapter; installed
addon and solver files remain unchanged. Every new native timestep executes.
`inspect.layer_checkpoint_revision` binds reviewed continuation to its saved
manifest, and `report layers` includes `physical_checkpoint`. Full validation
checks native binaries, adapter bytes, every checkpoint dependency and unchanged
physical inputs before reuse. Final native dump/recover buffers must agree exactly.

Save the blend and entire cache folder. Reopening a saved running continuation
marks it interrupted and restores the prior end frame only for the same scene,
checkpoint and unedited target end. A later human timeline edit is retained.
An explicit new proposal retries. Existing mesh-only bakes cannot continue physics.
Converged/fully iterated Custom profiles are supported; the default semi-implicit
profile and driven constructions refuse. End extension is bounded to 601 frames
and the checkpoint archive to 256 MiB. Representation changes require rebaking.

Future trajectories are tolerance-based: the ordinary Converged mounted-panel
case failed a 10 micrometer budget; explicit tighter Custom settings passed,
as did existing FEM and affine component cases. See BLENDER_WORKFLOW.md for all
settings, preserved failures and complete wall costs. Do not silently retune a
user's scene, advertise universal exact future motion, or equate saved mesh replay
with native state recovery. Evidence: `evidence/layer-continuation/acceptance.json`.


`refine_saved_component` takes one `uipc:ID` target and
`{"end_frame":23,"timeout_seconds":120}`. It requires the selected affine part's
unchanged saved detailed mesh, a full native checkpoint and a later end frame.
This asynchronous operation retains open authoring/playback until native
admission and completion. Use ordinary `status` and `cancel_layer_bake`.
Reviewed requests bind source, settings, cache and checkpoint revisions; inputs
are rechecked before commit. No installed addon/solver file is patched.

On success, the detailed mesh/groups and native seam indices are restored,
the new frame range starts at the previous end, and a new physical checkpoint
supports ordinary `continue_layers`. Its native step count restarts at zero;
physical time comes from the unchanged FPS/substeps and absolute frame range.
`report` with `{"kind":"layers"}` exposes `component_refinement`: the previous
cache/checkpoint, construction purpose and all transfer measurements. Save to a
new blend to retain both editable branches; cache files are never deleted.

Stale edits, failed admission, cancellation/deadline and attachment errors retain
the previous construction; later human edits are not rolled back. Pending saves
reopen interrupted with source authoring/checkpoint intact and no automatic retry.
Support is currently undriven BDF1 with no active contact candidates. Momentum,
kinetic/strain/port and total-potential budgets remain explicit. This implements
refinement, not automatic fidelity selection or general coarsening. Actual panel,
CLI, late rollback, pending reopen and native continuation evidence is in
`evidence/component-refinement/acceptance.json`.


`learn_port_response` takes `{"seed":2}` (integer 0..1000),
`measure_port_response` takes `{"heights":[0.21,-0.13]}` in metres,
and `show_port_response` / `cancel_port_response` take `{}`. All take empty
`targets` and the usual construction purpose. Learn/measure are asynchronous;
use ordinary status. Learning measures the existing AP02 GPU owner and admits
only a positive reduced response that passes independent unseen-state checks.
The UI has fixed scale and gamma=1 J/m2, with both rail heights within +/-0.34 m.

`inspect` adds `port_response_revision` and `port_response_job`; proposals bind
those identities and the scene. `report` with `{"kind":"ports"}` returns the
current response, observation, assembly, job and created view names. These accepted
records survive saving; a saved pending job reopens interrupted, without an
automatic retry. Deadlines and cancellation preserve prior accepted data. Actual
human panel and CLI preserve unfinished Edit Mode work. Use all four required
proposal fields (`action`, `targets`, `params`, `purpose`) in the external protocol.

Showing an observation creates a new full mesh and labels; it never overwrites
selected objects. Exact saved geometry/reactions are replayable offline. These
are prescribed-state measurements of a constant-current-area surface-energy membrane, not a
libuipc physical body, live time integration or general material certification.
See `evidence/port-cubature/acceptance.json` for native checks, composition,
end-to-end costs and saved-state recovery. No second database or solver.


`set_layer_region_weights` takes one `uipc:ID` target and
`{"group":"Supports","weights":[[0,0.49],[1,0.51]],"replace":false}`.
`replace:true` replaces the entire named group; false changes only listed vertices.
New groups use the requested name. Writes are finite [0,1], unique existing
indices, at most 20,000; locked groups and shared meshes refuse. A partial write
failure restores the original group. This does not silently bind a seam or bake.

`set_layer_pin_region` takes one target and
`{"group":"Supports","threshold":0.5}`. Empty group explicitly removes partial
pins. Unfixed cloth/FEM/rod roles support this mapping. Native membership uses
Blender's stored float threshold; preview includes requested and stored values.
Weights select fixed vertices or >=0.5 stitch endpoints, not graded stiffness.
Use the existing attachment group assignment/rebind commands for painted seams.

`report` with `{"kind":"regions"}` inspects the active physical object's groups,
counts, hashes and up to 32 sample endpoint IDs per group. It reads live BMesh
weights in Edit Mode without mutating IDs during panel drawing. Full geometry
and all weights are not sent in this compact report. Purpose and explicit edits
remain in the existing bounded operation history and saved .blend groups.

Weight Paint now supports these region operations, layer material/preset edits,
seam edits/rebinding, detach/activate cache, ordinary bake/cancel and layer A/B
capture/compare/show/clear. Sculpt/Pose additionally support evaluated physical
copies, these ordinary layer controls and saved-cache relinking; other actions
retain their declared mode requirements.
Context handoff preserves active object/group/mode and selection. Shared job
cache acceptance also handles the installed timer while the physical object is
being painted; unrelated native jobs are not intercepted. Stale or in-flight
paint changes refuse outdated results and keep the prior cache plus human edits.
See `evidence/painted-regions/acceptance.json` for native movement, real panel/CLI,
rollback, decimal threshold and offline replay checks. Physical continuation
and broader animated-actuation/material-field mappings remain separate capabilities.


`create_physical_copy` takes no existing physical targets and
`{"source":"Procedural canopy source","name":"New physical canopy",
"preset":"Workshop shell","attributes":{"left_edge":"Left seam"}}`.
`source` is a nonphysical mesh in the active view layer; `name` must be unused.
The reviewed evaluated content and object session identity bind the source
selection, frame, transform, groups and preset. New physical parts receive native
UUIDs and are reported by `report` with `{"kind":"geometry"}`. The command uses
the same visible **Create Physical Copy** workflow in Object/Edit/Sculpt/Pose,
preserving human selection and edits. Pose uses Blender 5 PoseBone selection,
including multiple rigs; active Dyntopo requires explicit completion first. Retry of the delivered operation is idempotent.

Attribute mappings are optional, distinct new group names, at most sixteen.
Existing evaluated vertex groups are copied. FLOAT/BOOLEAN point fields must
be finite [0,1]; their weights retain the existing pin/stitch membership meaning.
No full mesh is put into command history or the compact report. Inspect the new
part's source provenance and physical material through the existing owners.
Unrealized instances, non-mesh output, stale snapshots and unsupported physical
roles give actionable failures. Source changes never silently replace accepted
physical geometry, connections or replay. This snapshot bridge supports shell/
cloth and closed rigid surfaces; volumetric FEM and rods use their current tools.
See `evidence/evaluated-geometry/acceptance.json` for native load transfer, saved
replay, failure rollback and actual human/external CLI tests.


`explain_layer_trials` takes no targets and
`{"focus":"PHYSICAL_PART_ID","seconds":0.4,"metric":"max_drop_m","limit_m":0.35}`.
The focus is the existing native UUID without `uipc:`. Metrics are `max_drop_m`,
`mean_drop_m` and `max_motion_m`; each reports its maximum over stored frames from
the initial sample through the requested common time. Purpose states the useful
construction requirement. The reader reuses native cache/fingerprint/quality
checks, records limiting frame/vertex, and bounds work to two million vertex
samples per trial. It distinguishes single, joint, unchanged and confounded
comparisons and does not recommend correction merely because one option moves
less. `report` with `{"kind":"explanation"}` rechecks files and recomputes the
observation/attribution before returning it; a rehashed forged result fails.

`prepare_layer_alternative` takes no targets or parameters. It supports one
accepted material-field or seam-enabled/stiffness intervention, requires current
inputs equal the compared losing baseline, and verifies projected full native
inputs equal the accepted winner. Hidden disabled-seam bindings must also match.
Its result includes `prepared_operation`, an ordinary shared native-authoring
proposal. No physical edit is performed until that child is applied. The parent
is idempotent and never creates another correction on redelivery. The existing
shared controls review/apply/discard the child. **Review prepared correction**
restores its selection after viewing A/B. `relocate_layer_cache` can then use the
winner's existing reference/directory with `activate:true`, avoiding a new solve
when its full inputs match. Saved mesh replay remains distinct from continuation.

Requirement, purpose, explanation and prepared-operation reference use the
existing Layer Trials Text and operation history, not a new database. New trial
capture clears the old explanation/shortcut; stale commands and evidence refuse.
Both/neither-pass, already-applied, joint or confounded comparisons produce no
automatic correction. The human/lead can reject a recommendation based on other
construction goals. Actual native seam and density comparisons, raw-MDD peak
cross-check, human/CLI panels, failure handling and pending-save recovery are in
`evidence/layer-explanations/acceptance.json`.


`compose_port_responses` takes empty `targets` and
`{"pieces":["Lower membrane","Upper membrane"],"loads":[0.08,-0.03]}`.
Choose two to eight distinct saved response-card mesh names. The normal purpose,
proposal review, asynchronous status, cancellation and deadline owners apply.
Proposal/apply/acceptance bind the chosen cards' model, observed mesh and current
world translation. A late human edit retains both that edit and the prior assembly.
Use `show_port_assembly` with `{}` to create the accepted snapshot offline. Repeated
delivery of the same operation ID does not duplicate the snapshot. `report` with
`{"kind":"ports"}` includes the detailed/reduced decision, fallback reason,
accepted loads, per-piece reactions, native balance and retained evidence path.

Cards retain fixed shape, gamma=1 J/m2 and scale1. Rim translations are limited to
+/-0.1 m in Z and +/-20 m in X/Y; rotations, scaling, modifiers and edited display
geometry refuse. Common P/Q coordinates stay within +/-0.2 m, loads within +/-2 N;
not every load in that input range has an equilibrium in the declared box.
Current source selection/purpose and accepted assembly survive save/reopen.
Shared UI fields remain next-request inputs when an external client submits other
loads; accepted loads are displayed explicitly. This composes static ideal rails,
not physical joints or live libuipc bodies. See `evidence/port-assembly/acceptance.json`.


`set_layer_drive` takes one existing `uipc:<physical UUID>` target and
`{"enabled":true,"controller":"Lift controller","translation_strength":10000,
"rotation_strength":10000}`. Select an unfixed RIGID body, a separate nonphysical
controller in the current scene/view layer, and finite nonnegative native strength
ratios (at least one positive when enabled). Purpose explains the construction
motion. Inspect/preview/apply bind controller action contents/settings as well as
the physical inputs. A changed key refuses the stale proposal; failed admission
restores previous native drive fields and cache visibility.

The existing `bake_layers` owns asynchronous completion, cancel/deadline, native
sampling and cache attachment. Shared preflight samples every native substep and
refuses scale/shear or unsupported controller evaluation before launch. A human
edit during calculation prevents the obsolete result from replacing the accepted
cache. Native exported target arrays are hash-checked when comparing saved trials.
`report` uses existing native body/operation fields; no second motion database.
The human panel's next-request controls remain separate from applied values when
an external CLI assigns other settings.

This is the installed soft quasistatic transform target on the rigid link, with
native dynamic attached parts. It is not a torque-limited motor or bone-to-force
mapping. Explicit physical checkpoint commands now support the same driven scene
with unchanged actions and a validated native motion clock. Ordinary mesh caches
still contain no physical restart state. Blender 5 action
slots use a compatibility reader in Studio; installed solver files are unchanged.
See `evidence/controller-motion/acceptance.json` and BLENDER_WORKFLOW.md for scope.


`bake_layers_checkpoint` and `continue_layers` keep their existing parameters for
animated constructions. V2 checkpoint metadata stores each driven body's target
identity, sampled-trajectory hash, final-target hash and saved native step. The
worker verifies the entire old trajectory prefix before recovering native state
and starts the next target at `saved_step + 1`. The original worker's native
animator, material/contact laws and dump/recover remain authoritative. Changed
curves/materials/settings refuse, preserving prior cache/timeline/checkpoint.

Only the exact prior v1 checkpoint adapter and worker hashes receive compatibility
handling, with unchanged native/addon files and undriven inputs. Physical state is
validated, not synthesized from mesh playback. Optional-backend load ordering may
defer interrupted timeline restoration until GPU Materials activates; only that
record is retried and no simulation starts. `refine_saved_component` still requires
undriven inputs. See `evidence/motion-continuation/acceptance.json` for UI/CLI,
fresh-process continuation, full-range replay and retained failure evidence.

## Saved construction knowledge

The read-only local methods use the same implementation as the Blender panel:

```json
{"method":"search_memory","args":{"query":"rib seam support","limit":8}}
```

Pass a result's exact `ref` and `revision` to inspect it:

```json
{"method":"inspect_memory","args":{"ref":"layer:A","revision":"<revision returned by search>"}}
```

Use the normal `studio_client.py request --session ID --file REQUEST.json` transport.
Queries are at most 256 characters and limits are 1–20. Results cover only the
open project's retained procedures, native/layer A/B slots, reusable assembly and
two existing pinned mechanism-factory references. Matching is keyword coverage
then name/purpose relevance, not a learned suitability score. Search results are
`reference_unchecked`; only explicit inspection validates selected content.

`ready_for_binding` exposes a procedure's roles, typed steps and observed numeric
parameters. Bind new target IDs and use existing `run_procedure`; neither method
executes it. `verified_saved_checkpoint`, `verified_saved_playback`,
`ready_for_instantiation` and `verified_reference_only` retain their different
owner scopes. `unavailable` returns the owner's failure and retains the source;
a changed query reference fails before inspection. Check both protocol `ok` and
result `status`; an `ok` inspection can truthfully report unavailable evidence.
Read the explicit limits/receipt status before deciding whether work can be reused.
There is no search-triggered source refresh, new physics qualification or solver.
See `evidence/construction-memory/acceptance.json` for actual UI/client/reopen checks.

## Targeted layered material search

Use shared `propose` / `apply` / `status` with `search_layer_material`, exactly one
`uipc:<part-id>` target and these parameters (IDs come from inspect):

```json
{"field":"rod_bending","bounds":[100000,10000000],"focus":"MEASURED_PART_ID","seconds":0.6,"metric":"mean_drop_m","target_m":0.1425,"tolerance_m":0.0007,"budget":7,"schedule":"ADAPTIVE","timeout_seconds":60}
```

`FIXED` provides the equal-budget comparison. Choose a supported native stiffness
field, 3/5/7 trials, a converged undriven scene and an exact saved-frame horizon.
`report` with `{"kind":"layer_search"}` exposes measured rows and target outcome.
`cancel_layer_search` takes no targets/parameters and stops after the current
bounded native child. A failed/interrupted parent retains accepted changes and
measured progress; retry explicitly. Saving/reopening never resumes automatically.

`use_layer_search_result` takes no targets and
`{"operation":"COMPLETED_SEARCH_ID","index":3}`. The chosen actual measurement,
all trial dependencies and current physical inputs are checked; the existing
material edit/cache owner applies it without another solve. Repeated apply of
one operation returns its terminal record. Task-memory results use
`layer_search:<operation-id>` and inspect as `verified_native_search`; that status
means validated saved evidence, not material certification or universal suitability.
Search results remain in the existing bounded operation history. Preserve a saved
project and cache before that history rolls over. Source updates can make recorded
search/procedure definitions stale; do not change their recorded dependency hashes.
See `evidence/layer-search/acceptance.json` for actual UI/client/native/reopen tests.

For two controls, keep `search_layer_material` and supply each distinct physical
part ID once in `targets` (one or two IDs). Replace `field`/`bounds` with:

```json
{"controls":[{"target":"uipc:RIB_ID","field":"rod_bending","bounds":[100000,10000000]},{"target":"uipc:CLOTH_ID","field":"stretch","bounds":[1000,100000]}],"focus":"CLOTH_ID","seconds":0.6,"metric":"mean_drop_m","target_m":0.15,"tolerance_m":0.003,"budget":9,"schedule":"ADAPTIVE","timeout_seconds":60}
```

Use 5/9/13 complete native trials. Two different fields may share one part; repeating
the same part/field refuses. Rows retain ordered `candidate` and
`actual_material_values` vectors in the declared control order. Selection still
uses `use_layer_search_result`; both edits and the exact matching cache use the
existing owners. Task-memory inspection exposes `actual_material_values` for
paired searches; scalar results retain `actual_material_value`. Native results,
failed/partial progress and purpose survive saving. The 64-record history prefers
pruning copied completed search-child details before parent measurements.

Windows file access retries briefly during atomic updates; persistent reply-read
errors report the original request ID and unknown execution state. Inspect that
request/operation instead of reissuing an edit. No command is retried by this I/O
repair. See `evidence/layer-design/acceptance.json` for paired native, UI/client,
replay and exclusive-file-handle evidence.

## Measured component representation choice

`review_component_choice` takes one `uipc:<component-id>` target and
`{"position_m":0.002,"force_relative":0.1,"minimum_gain":0.1}`. Existing A/B must
contain the same complete undriven construction, with only its FEM/affine mapping
and ABD rigidity differing. Review remeasures boundary, all partner motion and
attachment-force errors; the declared gain uses recorded native-worker time,
excluding Blender/process startup. Insufficient accuracy or speed keeps FEM.

`report` with `{"kind":"component_choice"}` returns the saved decision, source
references, purpose, measured limits and `sha256`. Use the same part with
`apply_component_choice` and `{"decision":"<reviewed sha256>"}`. Current evidence
and physics are rechecked before applying the existing representation/cache.
The current accepted cache supplies rollback; this starts no simulation and does
not transfer a running state. Repeated apply returns the same terminal record.
A failed replacement retains the previous accepted geometry/bindings/playback.

Existing task search exposes `component_choice:current`; explicit inspection
returns `verified_component_choice` only after rechecking its original owners.
Saving retains the decision and external cache references. Reopening is offline;
a changed source, decision or native result refuses rather than silently choosing
another model. See `evidence/component-choice/acceptance.json` for actual human,
client, independent cache and failed-attachment checks.

## Construction assets through the shared interface

`export_layer_asset` takes 1-128 `uipc:` targets and
`{"path":"D:/Assets/new-construction.blend","name":"Supported panel"}`.
Selection must be closed under attachments. New files only; source physics and
playback are restored after export. `scan_layer_assets` takes
`{"path":"D:/Assets/new-construction.blend"}` and returns collection names plus
`sha256`. `import_layer_asset` takes no targets and
`{"path":"D:/Assets/new-construction.blend","collection":"Supported panel",
"sha256":"<scanned hash>","offset":[2,0,0]}`. File/geometry/material/native checks
precede acceptance; all parts receive new identities and need a scene bake.

Successful records have `construction_asset` with purpose/source identities.
Existing task memory exposes these as `asset:<operation-id>`; inspection returns
`verified_asset_reference` only for the matching current file. This is a file
reference check, not physics qualification. Object/Edit human and external-client
paths are tested. Ordinary Asset Browser drag is an inactive visual template;
the typed import activates native roles, groups and scene-owned connections.
See `evidence/layer-assets/acceptance.json` and the workflow for exact scope.


### Rigid construction placement

`import_layer_asset` additionally accepts **both** `rotation_xyz_rad` and `pivot`
with its original fields. Existing offset-only calls retain their old behavior.
`place_layer_construction` takes 1–128 existing `uipc:` targets and
`{"offset":[0,0,0],"rotation_xyz_rad":[0,0,1.5707963267948966],"pivot":[0,0,0]}`.
Each vector has three finite numbers; angles are within ±2π, coordinates ±1000
Blender units. The transform is `Rz * Ry * Rx * (point - pivot) + pivot + offset`.
Targets must form a closed undriven/unparented construction. Hinge axes transform;
stitch endpoint pairs/rest gaps, materials, supports and world gravity retain their
meaning. Result `construction_placement` records names/IDs, transform and
`requires_bake:true`. It does not move a solved native state or reuse its cache.

Explicitly placed cloth stores its authored material reference; native separate
rest/current geometry preserves its directions. This is included in ordinary
stale-proposal, cache/checkpoint and asset identities. Invalid references or changed
adapter owners refuse; a material-frame scale/shear/mirror is not a rigid placement.
Reexport/reimport and normal Blender saves preserve the reference. Old unplaced
objects keep their original native route. Shared rollback restores exact Blender
transform channels, reference properties, hinges and accepted cache visibility.
Evidence: `evidence/construction-placement/acceptance.json`.

## Native rigid hinges through the shared interface

`set_native_hinge` takes two `uipc:` targets and
`{"id":"","name":"Panel hinge","axis":[[0,-0.15,1],[0,0.15,1]],"strength":1000000,"enabled":true}`.
An empty id creates a joint; use the existing id to edit one. `inspect` returns
`native_hinges`. `remove_native_hinge` takes no targets and `{"id":"<joint id>"}`.
Axis coordinates use authored Blender world units. Endpoints must be distinct
native RIGID parts, including fixed supports. The strength is the native joint
ratio; there is no torque or hard angle-limit contract.

Human and client calls share revision-bound propose/apply, purpose/history,
transaction recovery and exact delivery handling. The same native adapter runs
under ordinary Bake and existing physical checkpoint/continue operations. Edits
invalidate the accepted cache without deleting it; ordinary offline replay is
separate from physical continuation. Complete joint closures are required for
copy/export. v3 assets preserve these definitions and v2 remains supported.
See `evidence/native-hinges/acceptance.json` for the actual inertial, attached-cloth,
external-client, stale-edit, rollback, native-continuation and offline checks.

## Static internal-port condensation through the shared interface

`learn_condensed_response` takes no targets and
`{"pieces":["Lower membrane","Upper membrane"],"boundary":"P"}`; choose `P` or
`Q` for the exposed coordinate. Pieces are existing saved AP02 response cards.
The current scene/card revision binds the proposal and running job. Native
characterization measures the existing quadratic response before acceptance.
`measure_condensed_response` takes no targets and `{"loads":[0.03,-0.01]}` in N.
`show_condensed_response` takes no targets or parameters and reconstructs the
accepted full geometry. Use the existing propose/apply/status/report operations;
`report` with `{"kind":"ports"}` contains `condensed_model` and
`condensed_measurement`, including domain, qualification and fallback reason.
`cancel_port_response` retains the last accepted result.

Existing task search exposes `condensation:current`; inspection returns
`verified_static_response` only after rechecking saved coefficients and measured
proof against the original owners. Search/inspection runs no GPU solver.
Completed responses survive saving; pending jobs reopen as interrupted and require
explicit retry. Keep referenced `.user/observations` evidence with the .blend.
This eliminates one of two shared Z coordinates in a static quadratic model;
no dynamic restart, general multibody reduction or libuipc coupling is implied.
See `evidence/port-condensation/acceptance.json` and BLENDER_WORKFLOW.md.

## Measured membrane libraries through shared operations

`export_response_asset` takes no targets and
`{"pieces":["Lower membrane","Upper membrane"],"path":"D:/Assets/new-membranes.blend","name":"Measured parts"}`.
Choose one to eight existing response-card meshes. Export binds the proposal to
their geometry, placement, models and packed evidence and writes only a new file.
`scan_response_assets` takes `{"path":"D:/Assets/new-membranes.blend"}` and uses
the same Blender library listing as `scan_layer_assets`. `import_response_asset`
takes no targets and `{"path":"D:/Assets/new-membranes.blend","collection":"Measured parts","sha256":"<listed hash>","offset":[2,0,0]}`.

Both actions use ordinary propose/apply/status and return `response_asset` in the
operation record. Import validates the actual appended cards and packed original
measurements, selects new independent card instances and preserves prior response
state. The `objects` result can feed `compose_port_responses` or
`learn_condensed_response`. No training or native job runs during import/export.
Current source-owner hashes must match; changed laws are not silently requalified.
`response_asset:<operation-id>` in existing task memory inspects as
`verified_response_asset_reference` after checking the library file; import owns
the deeper evidence/geometry check. Source provenance paths stay unchanged even
though the packed card no longer needs those original training directories.
Keep the .blend library and any external appearance textures. Static cards do not
carry a live integrated state, complete condensed assembly or libuipc material.

## Measured workflow outcomes

The same typed controls now expose `begin_workflow_trial` with
`{"case":"Support 0.8 N","variant":"Direct load","goal":{"gamma":1,"load":0.8}}`,
`finish_workflow_trial` with `{}`, and `cancel_workflow_trial` with `{}`. Start
from a settled native membrane assembly matching its authored parts. The finish
operation can succeed while its `workflow_trial.outcome.accepted` is false:
completion of measurement does not mean the construction met its declared goal.

`compare_workflow_trials` accepts `trials` (finish-operation IDs), `baseline`,
`candidate` and `minimum_gain` (0 <= gain < 1). It checks original evidence and
requires two matched cases with two independent, equally counted repeats each.
Its recommendation is scoped advice; Qwen/human retains adoption authority.
`report` with `{"kind":"workflow_outcomes"}` returns goals, recorded outcomes and
comparisons. Human controls use these same operations; names can select all
retained trials, including failures. A live trial survives normal history
pressure without dropping commands, but reopening marks its clock interrupted;
start a new measurement after inspecting the retained goal and construction.
Completed comparison evidence remains discoverable in existing task memory.
Keep the referenced `.user/workflow-trials` folders. See BLENDER_WORKFLOW.md and
`evidence/workflow-outcomes/acceptance.json` for measured cost and exact limits.

### Layered goal adapter

`begin_workflow_trial` also accepts `owner: "libuipc"`. Its goal is
`{"focus":"<part ID>","seconds":0.4,"metric":"max_drop_m","limit_m":0.35,
"editable_materials":{"<part ID>":["density"]},"editable_attachments":[]}`.
Use existing physical part/attachment IDs; the human panel resolves its selected
objects and active seam. Explicit material fields and selected seam enable/
stiffness may change. Geometry/supports/other settings remain fixed. Current
rest-input scene export defines the start; driven and continued-state comparisons
are not admitted. Finish uses the existing complete-cache/quality reader and
saved-frame observation owner. A completed measurement can report `accepted:false`.
Comparisons require one owner and use the same matched-case/repeat rules.
Goal, failure and native file references retain their existing save/retry behavior.
The older membrane schema and saved comparisons remain checked and readable after
the reviewed extraction of shared ranking; no historical physics test is skipped.


### Published elastic inputs and numeric references

`apply_published_material` takes one or more existing FEM target IDs and
`{"reference":"febio.elementary-beam"}`. Preview identifies source conditions;
apply reuses `edit_layer_material`, preserves other properties and saves its
source provenance. Standard proposal freshness and duplicate delivery apply.
`report` with `{"kind":"published_materials"}` returns compact source summaries
and current/changed/unavailable assignments. `search_memory` / `inspect_memory`
expose `published:febio.elementary-beam` and
`published:unitcelldb.bcc-example` using their returned revisions. The latter has
no isotropic assignment. These references do not qualify a complete material.
The pinned curves stay local in `data/published_materials.json`; no notebook or
spreadsheet formula is executed at runtime. See the workflow for exact scope.


### Part size and mixed size/material search

`resize_layer_part` takes one `uipc:` target and
`{"values":{"scale_x":1.02}}` (also `scale_y`, `scale_z`). It uses the existing
native stitch validator to retain endpoint pairs and update rest gaps, with
transactional rollback. Only axis-aligned positive, local undriven parts are
supported initially; see the workflow for deliberate limits and derived mass/
support changes. It never starts a bake implicitly.

Existing `search_layer_material` accepts those same field names in its scalar
`field`/`bounds` or two-entry `controls`. No new search service or state machine.
Existing `use_layer_search_result` explicitly applies measured size/material
values and reuses the matching native cache. For compatibility, saved
`actual_material_value(s)` fields carry ordered control values, including scales.
Every trial uses complete native advancement; the native cache remains authority.


### Generated procedure alternatives

`run_procedure` additionally accepts `strategy: "ORIGINAL" | "COALESCE" | "REUSE"`;
omission preserves ORIGINAL behavior. Existing `procedure`, `bindings`, `values`
and purpose remain required. The procedure report lists available strategies.
COALESCE combines compatible adjacent typed material assignments. REUSE is for
layered rest-input procedures and uses existing validated cache relocation, or
retains the full bake when no exact match exists. `native_result.optimization`,
`executed_steps`, `cache_attempts`, `completed` and `layer_trial` distinguish the
generated program, actual path and accepted evidence. Selection does not alter
solver policy; no parallel service or arbitrary Python execution is added.

To re-admit an immutable source pattern under the current wrapper, explicitly
call existing `learn_procedure` with `candidate: "saved:<learn-operation-id>"`
and a new name/purpose. The old definition remains; native-owner identity and
original successful source examples are checked. Use the returned new operation
ID and recheck the actual outcome. This is not automatic qualification after a
physics change. Saved history retains definitions/results/measurements and active
work; duplicate terminal procedure child receipts may be compacted to stay within
the existing budget, with their IDs recorded in `compacted_completed_children`.


### Native hinge torque and soft limits

Existing `set_native_hinge` accepts optional `actuation` alongside its existing
id/name/axis/strength/enabled fields, for example:
`{"torque_Nm":30,"limit":{"lower_rad":-0.1,"upper_rad":0.1,"strength":1000}}`.
`limit:null` means no angle penalty. Omitting both actuation and torque_profile resets the hinge to passive;
zero torque plus no limit canonicalizes to the original passive schema. The
human panel uses the same operation. Positive torque acts on the second target
around authored axis start-to-end by the right-hand rule. Values use N m and
radians; Blender displays angle properties in its normal unit convention.

Limit bounds must include zero, lie within +/-pi and span at least 0.0001 rad;
strength is the installed normalized cubic penalty's energy scale, not a hard
stop or rotational spring constant. Finite overshoot is expected. No driving
curve, speed servo or feedback controller is inferred. Existing bake/checkpoint,
asset and inspect calls carry these fields. Native request hashes include the
extended adapter only when actuation is used; old passive requests keep their
unchanged source owner. `hinges.json` records actual native laws, inputs and final
retrieved joint angle. See the workflow for independent accuracy/load-transfer
checks and explicit saved-mesh versus native-state scope.


### Diverse layered designs

The existing two-control `search_layer_material` accepts optional `diversity`:
`{"response_min_m":0.125,"band_width_m":0.005,"bands":6,"projection":"XY","seed":17}`.
Use `schedule:"DIVERSE"` for measured-archive mutation; `ADAPTIVE`/`FIXED` may carry
the same fields to retain comparable archives. No fields means original behavior.
The 2–8 bands cover [start,start+width*count), using the existing measured movement
metric and horizon. The lower measured rest bounding-box footprint wins each band;
equal footprints retain the earlier result. All rows remain saved. This is one
behavior descriptor and one footprint objective; no mass or physical-law estimate.

`report` with `{"kind":"layer_search"}` includes `archive`, rows and the separate
target-based `best_index`. Each archive entry links `evidence` to its measured row.
Use existing `use_layer_search_result` with that operation and row `index`, retaining
existing source/cache admission. Task-memory inspection also returns the archive.
Export the selected authored rest construction with existing `export_layer_asset`;
a new imported instance needs a destination-scene bake. Complete measurement,
partial-save and UI/CLI evidence is linked from the workflow.


### Keyed native hinge torque

`create_hinge_torque_controller` takes no physical targets and either
`{"name":"Panel torque","knots":[[5,30],[15,30],[15.5,-30],[25,-30],[25.5,0],[35,0]],"interpolation":"LINEAR"}`
or `{"name":"Editable copy","profile":PROFILE}`. Knots use Blender frame numbers
and N m; LINEAR or CONSTANT is accepted. The successful operation returns
`torque_controller` with the source object's name and captured `profile`.
`report` with `{"kind":"hinge_torque_curves"}` inspects the current editable curves,
their purpose and capture errors without starting physics.

Add `torque_profile:PROFILE` to existing `set_native_hinge`. PROFILE is
`{"schema":"chimera.studio.torque-profile.v1","fps":100,"substeps":2,"first_frame":5,"values_Nm":[30,30,-30,0]}`.
Use actual captured values, with 1-20,000 finite samples; each native step indexes
by scene start frame plus the saved native step count. First/last values hold
outside the captured range. FPS/substeps must match. Optional `actuation.limit`
may coexist; its constant torque must be zero. Omitting profile removes it.
Inspect reports the applied profile, distinct from the editable source action.

The human Apply button captures the selected source curve explicitly. Later curve
edits do not silently update the hinge. Profiles are part of cache/checkpoint input
identity and existing collection assets; recreating a curve from a profile preserves
its samples, not unsampled Bezier handles. A new destination instance is freshly
simulated. Native Animator, inertia, contacts and joints own evolution; this API
provides no speed/position servo or Python stepping approximation. Existing typed
operations, rollback, purpose/history and duplicate-delivery rules remain active.


### Measured construction requirements

`find_layer_designs` takes `{"query":{"focus":"<native part ID>",
"metric":"mean_drop_m","seconds":0.6,"minimum_m":0.139,"maximum_m":0.145,
"projection":"XY","maximum_footprint_m2":0.124},"limit":8}`. Supported metrics
are the existing `max_drop_m`, `mean_drop_m`, `max_motion_m`; projection is XY/XZ/YZ.
The interval is inclusive, time/area positive, all numbers finite and nonnegative;
limit is an integer 1–20. Part identity, response definition and recorded horizon
must match the source experiment. History remains the only index.

The response includes `results`, total status `counts`, `unavailable` and `excluded`
searches, `query`, `scope_revision` and measured query time. Each result records its
source `operation`, trial `index`, `revision`, status, actual controls, movement,
footprint, native content identity and purpose. One row is one trial, not necessarily
one unique design. Ranking favors compatible measured requirements, compactness
and interval-center distance; incidental GPU timing is not an optimization score.

`inspect_layer_design` takes the returned query, operation, index plus
`revision_id: result.revision` and `scope_id: response.scope_revision`. It rechecks
native evidence and current source identity. Only `ready_to_apply` passes the
same-scene reuse check. To apply explicitly, use existing propose/apply with
`action:"use_layer_search_result"`, empty targets and `params:{operation,index}`,
then poll its operation ID. The owner retains final admission authority.

`report` with `{"kind":"construction_requirements"}` returns the saved human
purpose, mode and numeric query, or its missing-target error. This is persistent
intent, not a fresh suitability verdict. Re-run find/inspect after resuming.
The human panel saves these fields in the .blend; transient result lists are cleared
on file changes. Modified human requirements refuse an old button payload. Actual
human and external-client tests preserve unfinished edits, use no native solve and
replay exact saved geometry; see `evidence/behavior-retrieval/acceptance.json`.


### Read existing attachment loads

`inspect_attachment_loads` accepts exactly `{"seconds":0.6,"review_N":1.0}`.
It validates the current native construction/cache, then returns all native
SoftVertexStitch seams ranked by peak individual force estimate through that exact
stored time. Each record identifies endpoints, peak time/frame, signed force on A,
extension, peak energy, net force and sum of magnitudes; maxima need not coincide.
The response includes cache identity, sample/step counts and explicit scope.
`review_N:0` disables the optional review flag. This is a read-only inspection;
no operation proposal, new solve or automatic correction follows. Negative,
nonfinite, inter-sample, excessive-range or invalid native evidence returns a
clear failed call. Force is derived from rounded positions and the native energy,
not a solver force output or strength test. The human panel uses the same function.
Use the existing A/B and explicit authoring operations if the observation warrants
an actual construction change.


### Native hinge angle target

Existing `set_native_hinge` accepts optional
`angle_drive:{"target_rad":0.25,"strength":100.0,"enabled":true,"ramp_seconds":0.15}`.
The target is the native absolute angle relative to authored zero; the native axis
sets its right-hand sign. Optional `ramp_seconds` defaults to zero (immediate);
positive time linearly advances the target from zero and holds after arrival.
Native Animator uses the saved physical step count, including after continuation.
`strength` is a finite native solver penalty in [1e-6,1e8], not a torque/power cap
or timestep-independent spring stiffness. Its effective resistance depends on
both body masses and timestep. Enabled must be an explicit boolean.

Do not combine angle_drive and torque_profile on the same hinge. Existing constant
`actuation.torque_Nm` and soft limits may coexist; they retain their own meaning.
Omit angle_drive to remove it; enabled:false retains the unpowered drive definition.
Inspect/history, current source identity, collection assets and native checkpoints
carry these fields. An edited target/ramp/powered flag requires a fresh bake.
`hinges.json` records each actual native target callback and final native angle.
The human UI and external client share existing validation/rollback/duplicate rules.
Tests and the small-construction scope are in the workflow; mixed drive types on
multiple joints and general multi-turn mechanisms are not newly qualified.


### Painted native cloth stiffness

`set_cloth_stiffness_region` targets one existing Cloth mesh and accepts exactly
`{"group":"Reinforcement","stretch_factor":8,"shear_factor":8,"bending_factor":8}`.
The named Blender vertex group must exist. Stretch/shear factors are finite
[0.001,1000], bending [0,1000]. They multiply the part's existing native coefficients
at weight one; missing weights are zero and intermediate weights blend linearly.
Triangle mean weights drive native stretch/shear, edge-endpoint means drive bending.
Density, thickness, Poisson inputs, strain law and contacts stay uniform per part.
`clear_cloth_stiffness_region` uses the same one target with empty params.

Use existing `set_layer_region_weights` or Blender Weight Paint to edit the mask;
shared Object/Edit/Weight Paint mode preservation applies. `report` kind `layers`
returns `cloth_stiffness_regions` with part ID and applied group/factors. Inspect
includes the raw definition and existing group weights in source revision. This
uses ordinary saved operation purpose/history and collection assets, not a second
material database. Bake/checkpoint/continue use the existing owners. Changed paint
invalidates physical continuation; rejected calls keep accepted caches. Native
`cloth-regions.json` records actual topology, weights and before/after coefficients
for inspection. Human colors show brush weights, not measured stress or strength.


Mass-aware layer search uses optional `params.diversity.mass` with explicit native
part IDs, `minimum_kg`, `band_width_kg` and `bands`. Existing
`find_layer_designs` / `inspect_layer_design` accept optional query `mass` with
`parts` and `maximum_kg`; saved intent includes these fields. Reports identify
per-part native rest mass and included parts. Use the unchanged
`use_layer_search_result` after current-scene inspection. No solver runs during
lookup or compatible reuse. See BLENDER_WORKFLOW.md and
`evidence/mass-diversity/acceptance.json` for real human/client and saved-replay
evidence; old queries without mass keep their prior meaning.


### Inspect existing membrane triangle response

`inspect_cloth_triangles` accepts exactly
`{"focus":"<native part ID>","seconds":0.6,"limit":8}`. Use an existing Cloth
part ID (without the operation target's `uipc:` prefix), an exact stored time and
1-32 results. The response includes cache/report IDs, principal length ratios,
area ratio, rest area/mass, vertices, peak frame/positions and paint factors.
Rows rank the maximum absolute departure of either length ratio from 1 across
stored frames. It reads existing evidence and does not advance physics.

`show_cloth_triangle` accepts `{"params":<the inspected params>,
"report_id":"<the returned report_id>","triangle":<returned triangle index>}`.
It remeasures before navigating the timeline and replacing the owned static display
highlight. The physical mesh and its edit buffers are preserved. Repeated display
requests leave one highlight; old/forged evidence produces a failed call. This is
a visible inspection action, not an operation that changes physical state.

`report` with `{"kind":"triangle_inspection"}` retrieves the saved human purpose
and parameters after reopening. This is saved intent; inspect again to validate
current evidence. The human panel uses the same core. Neither geometry ratios nor
paint factors establish stress, failure, bending energy or applicability to changed
topology. Native cache files must remain available for revalidation/replay.


### Reuse GPU-learned triangles across physical scales

Use the existing `propose` / `apply` / `status` operations. First
`learn_port_response` with `{"seed":2}` trains the existing AP02 response.
`qualify_scaled_response` with `{}` reuses that current model and checks 232
unseen scaled/material states against the full GPU teacher and independent Heron
energy/forces. Both are bounded asynchronous jobs; the existing
`cancel_port_response` cancels an owned request and retains the last accepted card.

`measure_scaled_response` accepts exactly
`{"scale":1.3,"gamma":1.5,"heights":[0.156,-0.117]}`; heights are physical metres.
Scale is 0.5–2, gamma 0–2 J/m2, and each height/scale must be within +/-0.34.
The asynchronous worker reuses the saved conservative response without a GPU call.
`show_scaled_response` with `{}` creates a new observation mesh with per-face
`chimera_cubature_weight` and `chimera_rest_area_m2` attributes. It retains all eight
faces, source model, qualified domain and current energy/reactions.

`use_scaled_response_card` with `{"object":"<saved card object name>"}` validates
and selects an existing/Blender-appended card. Its mesh and stored response must
still match; changes between proposal and application fail. `report` kind `ports`
returns `scaled_model` and `scaled_measurement` alongside previous response state.
Pending saves recover interrupted, completed observations replay offline, and
normal retries remain idempotent. Original AP02 cards/operations keep their meaning.
This is the constant-current-area membrane owner; a libuipc cloth inspection is
not a compatible training label. New laws require their own native labels and
independent qualification, not a type rename or a second solver.


### Cloth training labels

`build_cloth_training_labels` accepts `focus` (native part UUID), `seconds`,
`samples` (2-9), `scale_thickness` (boolean), and `purpose`. It starts the same
owned job as Blender's Cloth GPU Training Data panel. Poll `report` with
`{"kind":"cloth_labels"}` for status and a compact source-bound summary.
`cancel_cloth_training_labels` takes no arguments; accepted data is retained.
This operation reads a complete converged bake and evaluates existing native
constitutive functions, not another physical simulation. Full compressed records
stay in the saved blend Text `Chimera Cloth Training Labels.json` and worker
`labels.json`; use `cloth_label_core.unpack(packet)` in the pinned workflow to
obtain record/label arrays after source and integrity checks. Record slots are
kind(0 triangle/1 bending edge), four rest xyz positions, four current xyz positions,
lambda/mu/strain-rate (or kappa for bending), and four reserved zeros; triangle's
fourth corner is unused. Each output is E followed by four xyz force vectors.
`triangles`, `bending_stencils` and `cases` map local corners, source vertices,
frames, scales and fixed training/held-out groups. No constitutive model is fitted
or admitted by collection; ordinary native stepping remains authoritative.

### Cloth rail teaching and saved queries

- `learn_cloth_rail`: `{port: -1, purpose: "construction reason"}` uses the current
  saved cloth training dataset and the existing owned external worker. -1 selects
  the central interior vertex; humans can also pick a native cloth vertex in Edit
  Mode. Poll `report` with `{kind: "cloth_port"}`. No repeated automatic retries.
- `query_cloth_rail`: `{scale: 0.5|1|2, height: METRES}` returns compact energy and
  normal reaction from the saved qualified response, no GPU call. The domain is
  +/-0.01*scale metres. No arbitrary scale interpolation.
- `preview_cloth_rail`: the same arguments create a separate wireframe Blender
  asset containing the learned model and preview mesh. Original construction
  geometry/physics is unchanged. The card requires metre scene units.
- `cancel_cloth_rail`: `{}` interrupts only the owned teacher and retains its last
  completed response. Save/reopen keeps that response; pending work is interrupted.

This is a static fixed-rim cloth fixture, not a free cloth, contact surrogate or
live physical continuation. The shared human/client contract and all materials,
source identities and limits are in the saved card. Reuse first; train only when
needed by the construction. See BLENDER_WORKFLOW.md and cloth-port evidence.

### Requested cloth support loads

- `check_cloth_load`: `{scale: 0.5|1|2, load_N: NUMBER, purpose: "construction reason"}`
  inverts the currently selected saved cloth response, then starts a fresh owned
  native static check. Poll `report` with `{kind: "cloth_load"}`. The compact report
  gives displacement, measured reaction, check residuals, timing and explicit scope.
- `show_cloth_load`: `{}` creates a separate snapshot from accepted native positions.
- `cancel_cloth_load`: `{}` cancels only this owned request; accepted results survive.
- `search_memory` and `inspect_memory` now expose `cloth_response:current`,
  `cloth_card:OBJECT_NAME` and `cloth_load:current` through their unchanged contracts.
  Inspection is read-only, validates the original owner and does not load a model.

A request outside a taught scale/load interval refuses before GPU work. A native
mismatch reports the measured error and limit; its worker directory keeps
`refused-load-check.json`. Do not repeatedly retry an unchanged mismatch. Report
its relevance to the construction and choose a detailed scoped analysis or a
better qualified response. After context compression, re-read the saved accepted
result and its purpose through `report`; the Blender file retains both. This
change does not edit Z Code's saved goal or model settings. No full scene force
injection or dynamic restart.

### Shared cloth support loading

`check_cloth_assembly` takes `{names: [CARD_OBJECT_NAMES], load_N: NUMBER,
purpose: "construction reason"}` for two to four distinct qualified cloth cards.
It uses their saved scale/material, intersected displacement domains and the
existing conservative scalar equilibrium. Poll `report` with
`{kind: "cloth_assembly"}` for status, shared displacement and each native load
contribution. `show_cloth_assembly` and `cancel_cloth_assembly` take `{}`.
`search_memory`/`inspect_memory` expose `cloth_assembly:current` with the same
read-only contracts. Per-component checks and total balance are both required.

Cards must have matching normals and unchanged preview geometry. Repeated source
models represent independent instances, not shared state. No arbitrary transformed
port or live solver injection is admitted. A component refusal is retained in its
worker `support-N/refused-load-check.json`; inspect it instead of retrying the
unchanged request. Completed result/purpose stays in the Blender file and can be
re-read after agent compression; no model settings or saved-goal changes.


### Detailed native cloth attachment checks

When a saved vector card refuses compliant-stitch composition, use
`check_cloth_stitch` with `{scale: 0.5|1|2, stiffness_N_m: 1000, gap_m: 0.02,
displacement_m: [0, 0, 0.005], purpose: "construction reason"}`. Displacement is
the prescribed anchor movement in world metres; gap is measured along the card's
rest normal. It starts the existing bounded native worker and checks its actual
free-XYZ-port equilibrium. Poll `report` with `{kind: "cloth_stitch"}` for compact
forces, deflection, lateral movement, energy, residual, timing and scope.
`show_cloth_stitch` and `cancel_cloth_stitch` take `{}`. The same controls are in
Blender's **Native Compliant Attachment** panel below the vector card.

After context compression, read the saved result and purpose through `report`.
The blend retains full native observations in `Chimera Native Stitched Support.json`.
Failure/cancellation/deadline preserves the last accepted result. Pending saves
reopen interrupted; retry deliberately. This does not replace the source scene,
train a compliant surrogate or resume dynamic physics. New requests must pass
native static and independent checks; use the result to inform the construction.
