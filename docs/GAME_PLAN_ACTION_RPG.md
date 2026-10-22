# SEALED — a game built from simulated matter

**Active delivery plan · operator direction consolidated 2026-10-22.** Keep this
file named `GAME_PLAN_ACTION_RPG.md`. The saved Z Code goal follows this file;
retain its identity, progress, budgets, decisions and child conversations.

## 0. Mandatory delivery path and reading order

**Build and deliver Chimera through Blender. This applies to Qwen and every
subagent. Blender is the mandatory authoring, inspection and product-validation
interface, not an optional viewer attached after engine development.** The current
deliverable is the Chimera Studio add-on/application template and useful `.blend`
constructions. The existing native engines remain its physical and rendering
backends. Qwen may optimize the process and choose peers; changing this product
platform requires an explicit new direction from the user.

Every implementation task identifies the **Blender project/user action**, existing
operator or integration owner, required result, and recovery/acceptance check.
Engine code, CLI tools, CPU references and headless tests are allowed when they
support that named Blender action. Headless Blender must exercise the installed
add-on/native boundary and a real saved construction. A standalone engine window,
browser game shell, endpoint response or numerical experiment alone does not
complete a Blender feature. If Blender or its connection is unavailable, state the
specific blocker and advance useful offline dependencies; do not silently switch
the deliverable to the old interface.

Read **this section → §3 (existing capability) → §12.2 (Blender workflow) → §13.1
(current work selection)**, then §11.22 for delegation. Load other sections only
for the selected task. Do not load the full historical reference into every agent.

This explicit operator direction supersedes older engine-first assignments,
“first/next” sequences, expired scheduled-work deadlines and historical graph
handoffs as sources of task selection. Scientific contracts and qualified domains
still apply to the physics being used. This document does not rewrite a live
controller graph, promote a failed check, or claim deployment admission.

The previous complete plan is preserved in the
[design and evidence reference](GAME_PLAN_ACTION_RPG_REFERENCE_20261022.md).
Its original body, designs, citations, gates and measured results are retained;
its old scheduling and imperative paragraphs are **reference, not another work
queue**. Section numbers 5.1, 11.22, 12.2 and 13.1 remain here for existing goals
and handoffs. Detailed former subsections are found under the same numbers in
the reference.

## 1. The game we are making

Create a compelling game **that uses simulated matter**. Exploration,
construction, combat, companionship and meaningful choices are the experience.
Physics supplies understandable consequences and useful invention. SEALED is a
working title, not a requirement to discard other strong settings or genres.

Players assemble and revise functional pieces as they would LEGO constructions
or multi-material 3D prints. A shape, its assigned material, its internal layers,
its connections and its history jointly determine what it does. The same design
can become a vehicle, shelter, tool, machine or creature component when the
required laws and connections exist. Appearance and a material name alone do not
make an imported object functional. Fictional materials are explicit game laws
with declared parameters, not claims of measured real-world properties.

The immediate product is a professional Blender interface for making and using
those constructions. The workshop is an early playable milestone, not the entire
game. Preserve the wider design in the reference; implement the next useful
interaction instead of expanding all genres or simulating all matter first.

## 2. What the new concepts unlock

Reusable physical mechanisms (“artificial proteins”) combine geometry, material
state, ports, constraints, scale rules and measured response. Triangulated
membranes, shells, solids, rods and rigid bodies contribute different capabilities.
Layered assemblies can carry loads, permit motion, store/release energy and fail
in ways players can diagnose and repair. A tested assembly can itself become a
reusable part without erasing the limits of its internal mechanisms.

Three continuing design targets are a recoverable load-bearing construction, a
machine with readable motion and attachments, and a rescue situation whose
solutions depend on what the player builds. These guide choices; they are not
three simultaneous implementation assignments. Detailed encounter and genre
designs remain in reference §§2, 6–10.

## 3. Starting point: evidence and limits

**Read current source and scoped receipts before dispatch.** This table records
existing work inspected during consolidation; it is not a new GPU test or a claim
that every old receipt matches today's source. Preserve completed work and use
the existing owners. A filename or an old PASS never establishes broader physics.

| Capability already available | Owner / evidence | Boundary that still matters |
| --- | --- | --- |
| Membrane authoring, supported material assignment, apex connections, native solve/render, save/reopen/replay | [Blender workflow](../../ChimeraStudio/integration/BLENDER_WORKFLOW.md); [membrane workflow checks](../../ChimeraStudio/integration/evidence/membrane-workshop-workflow-checks.json): 9/9 recorded checks | Fixed-rim triangle fans, shared rail apex, uniform constant-current-area tension. Not general elastic cloth; membrane apex-weld reaction inspection is still absent. |
| Layered construction with different materials, interacting parts and stitches | [installed libuipc workflow](../../ChimeraStudio/integration/optional/libuipc/INSTALLED_WORKFLOW.md); [layered workflow checks](../../ChimeraStudio/integration/evidence/layered-workshop-workflow-checks.json): 9/9 recorded checks | SoftVertexStitch force estimates use saved positions and the native energy with independent raw-cache decoding. They are not recorded solver forces or membrane-weld forces. |
| Human and external AI operate the same Blender scene | [operations contract](../../ChimeraStudio/integration/OPERATIONS.md), `integration/tools/studio_client.py`; [local-client evidence](../../ChimeraStudio/integration/evidence/local-client/acceptance.json) | Explicit session/scene, shared operators, stale-edit checks and terminal job results. No hidden second scene or arbitrary-script remote executor. |
| Saved comparisons, construction assets, measured search, procedure reuse, inspection, modes, hinges and supported physical continuation | Current [workflow sections](../../ChimeraStudio/integration/BLENDER_WORKFLOW.md), [libuipc work log](../../ChimeraStudio/Libuipc/WORK_LOG.md), and their linked acceptance receipts | Reuse the applicable implementation; each has its own material, boundary, state-transfer and persistence envelope. |
| Triangle inspection and reusable responses at taught scales | [AP02 scale-response evidence](../../ChimeraStudio/integration/evidence/scale-response/acceptance.json); [cloth-port evidence](../../ChimeraStudio/integration/evidence/cloth-port/acceptance.json) | Constant-tension AP02 and elastic-cloth responses are different laws. Taught static domains are not arbitrary dynamic or between-scale predictions. |
| Detailed compliant cloth-attachment checks in Blender | [native stitched-support evidence](../../ChimeraStudio/integration/evidence/cloth-stitch-control/acceptance.json) | A usable detailed native fallback exists. The normal-only learned vector card remains insufficient for general lateral/compliant coupling; do not promote the refused pilot. |
| Native construction, recipes, comparisons and independent references | PythonChimera `tools/construction_packet`, `tools/recipe_experiments`, `tools/artificial_proteins`, `tools/mechanism_factory`, `ChimeraEngine/engine` | Supporting owners and scientific evidence, not an alternative user-facing delivery route. Studio consumes deliberately pinned versions. |

The native membrane renderer and libuipc simulation remain distinct owners.
They are not yet a generally force/state-coupled CA/membrane/solid system. Render
and material bindings must identify the owner actually producing their result.
Water remains deferred, including the already implemented flow-specific CA work.

## 4. Design rules that let the systems combine

- One explicit physical owner per state variable; no double-counted mass, forces,
  energy, contacts or material volume when pieces overlap or nest.
- Geometry, physical material, attachment law, units, rest/history state and
  display styling are separate. Colored regions select explicit material IDs;
  paint color is not a constitutive law.
- Source edits and the last accepted physical result remain distinguishable.
  Refusal, cancellation or interrupted work preserves recoverable accepted state.
- Reuse Blender's modeler, selection, modes, Properties, Outliner, Geometry Nodes,
  animation and image viewers. Use the existing native compiler/solver rather
  than a parallel Python solver or automatic substitution of Blender physics.
- Claim only the represented behavior. A screenshot is not force evidence;
  accurate forces alone do not establish a usable editor or an enjoyable game.

## 5. The playable vocabulary and control contract

The core verbs are inspect, select, assemble, assign material, connect, load/use,
compare, repair, save and reuse. Each should produce a readable consequence and
a recovery path. CAD/3D-printing imports supply geometry; supported mappings add
material regions, layer thickness, local directions, ports and connections.
Unsupported inputs receive an actionable explanation instead of invented physics.

### 5.1 Matter workshop: the next playable increment

Use a small existing construction in Blender. A person should be able to change
one part/material/connection, predict a useful difference, run the admitted
physics, understand the outcome and save/reopen/reuse the invention. Layered
Materials Workshop is the existing multi-material/stitch path; Membrane Workshop
is the existing constant-tension/native-render path. Choose the one that already
supports the task instead of conflating their laws or rebuilding their controls.

The recorded nine-check loops in §3 are completed foundation, not a request to
repeat those milestones. Select a missing or demonstrably confusing action from
current source/evidence. A task is complete when that specific action works through
the installed Blender path, relevant persistence/physics checks pass, and its
limits are reported. Human comprehension/enjoyment remains unobserved until a
person actually tries it. Player-directed rescue/adventure work follows useful
construction interactions; an engine-only playable demo does not satisfy this lane.

## 6. The first vertical slice: “Bring Them Home”

Retain the rescue-adventure design: investigate a damaged environment, construct
or adapt a way through, protect/recover a companion, and return with consequences
and reusable knowledge. Physical choices should permit alternative solutions and
readable failure/recovery. Reference §6 preserves its sequence and original gate.
This is a subsequent product milestone; it does not authorize switching the
current Blender integration task into a standalone game loop.

## 7. Combat, companionship and progression

Combat can contest support, reach, access and material limits. Companionship gains
meaning through useful shared history, care and recoverable mistakes. Progression
should open construction tradeoffs rather than replace every part with a single
strictly stronger version. Keep those design directions, while selecting only
capabilities supported by a concrete current interaction. See reference §7.

## 8. The lair, economy and world memory

Reusable inventions, persistent repairs and competing uses for limited parts can
connect home building with exploration. Resource and world-memory systems should
recognize meaningful physical outcomes. They remain later design work until a
selected playable milestone needs them; the detailed designs remain in reference §8.

## 9. What the rest of gaming can teach this game

Keep the genre library as a source of interaction ideas: movement, threat,
inference, logistics, building, care, tactical tradeoffs, story and expression.
Choose a useful player decision and the smallest supported mechanism that creates
it. Genre coverage is neither a completion checklist nor permission for scope
expansion. Reference §9 retains every prior genre/application proposal.

## 10. Turn the library into encounters and a campaign

An encounter proposal identifies player intent, reused parts/verbs, alternate
solutions, meaningful failure/recovery and the one uncertainty it will answer.
Promote it when the prerequisite construction interaction is usable and its
physical claims are supported. Reference §10 preserves encounter grammar,
constructions, chapter pacing, rewards and world teaching; those are not the
active implementation queue.

## 11. The reusable matter system and its renderer

This is the architecture to serve Blender and the eventual game. Detailed
derivations, examples, source links and historical evidence are in reference §11;
consult the relevant mechanism, not the entire chapter.

### 11.1 Reusable functionality is the unit of construction

A reusable part declares geometry, material law, units, state, ports, admissible
scale/load/history domain and evidence. Its displayed material label must agree
with the native law. Reusing a qualified part requires matching its conditions,
not automatically rerunning its entire original qualification.

### 11.2 How asymmetric polygon layers become physical matter

Triangles describe a discretization, with material fields, thickness/directions,
rest geometry and state appropriate to the chosen law. Shells, volumes and rods
need their own admitted representations. A triangle does not by itself encode
all of matter. Import, triangulation and subdivision must preserve intended
ownership and material quantity. CAD and additive-manufacturing mappings retain
explicit region/layer assignments and supported connection semantics.

### 11.3 How pieces stack, join and separate

Use existing native contact, stitch, joint and finite-area attachment laws within
their envelopes. Contact is not automatically a bond; coincident surfaces are not
automatically welded; a scalar point support does not prove moment transfer.
Record both sides' exchanges, rest geometry and failure/refusal conditions.

### 11.4 CA rules advance the material; they do not merely decorate it

CA state updates require a declared physical state, clock, exchanges and mapping
to geometry/rendering. Keep current CA/native owners; a trained material-response
query is not automatically a CA evolution law. Bind a new coupling only for an
identified Blender capability with independent checks. The flow-specific water
continuation implementation does not supply a general cloth/solid interface.

### 11.5 Construction is a conservative topology transaction

Reuse existing compile/admit/commit/refuse paths. Validate stable identities,
topology, quantities and connections before accepting edits. Preserve the last
confirmed state when an edit or native request fails. Do not infer physical undo
from ordinary Blender geometry undo.

### 11.6 Render the same accepted matter that the player touches

The visible result, selection and inspector identify the same accepted physical
sample and owner. Reuse the native render capture and Blender presentation path.
Camera and projection limits stay visible; preview/source geometry must not be
passed off as computed matter. There is no second physics implementation behind
the display. Continuous viewport streaming and generalized cross-owner rendering
remain scoped work, not consequences of having one native screenshot.

### 11.7 A worked layered assembly: the asymmetric rescue cradle

Retain the cradle as a historical recipe and scoped comparison/control. Reference
§11.7 contains the construction. Use the existing Blender layered/stitch examples
for present authoring work; do not rebuild a separate cradle editor.

### 11.8 Matter capabilities behind the genre library

Select mechanisms because they enable a useful interaction: support, shielding,
articulation, compliance, sensing or controlled failure. Catalog growth alone is
not product progress. Keep broader applications in the reference until selected.

### 11.9 A shape grammar that preserves what the material remembers

Preserve rest state, forming/damage history and named interfaces when the law
actually represents them. A duplicated instance gets its own identity/state;
shared immutable recipes and response data remain reusable.

### 11.10 Contact discovers connections; history makes them meaningful

Distinguish proximity, contact, permitted attachment and persistent bond history.
Only create or remove connections through supported native/authoring contracts;
retain clear failures and recovery rather than silently attaching to another face.

### 11.11 Mechanisms are patterns of permitted motion

Reuse the implemented native hinge, rod, shell and attachment paths. Distinguish
prescribed animation targets from finite powered actuation, and visual pose from
native physical state. More degrees of freedom need measured authority, not labels.

### 11.12 Fabrication sequence is part of the design

Assembly order, supports and temporary fixtures can change behavior. Keep these
as explicit recipe/procedure inputs. A supported process must reveal which support
is carrying load and what happens when it is removed.

### 11.13 A reusable part promises a range of behavior

Preserve input identities, validity domains, response/error measures and runtime
cost. Use existing recipe comparisons and evidence adapters. Mark results stale
when relevant inputs change; retain old outcomes and check the changed mapping.
Transient comparisons need synchronized native advancement and observation;
equal wall-time sleeps or discarded simulation steps are not equivalent tests.

### 11.14 From a player gesture to one accepted physical result

Use the shared Blender inspect/propose/apply/status boundary. Resolve actual
selection, mode, UUIDs and source/native revision. Submission is not completion;
poll the same operation to its terminal result. An uncertain delivery is inspected
or recovered by identity rather than blindly replayed.

### 11.15 A small numerical design example

The historical numerical example remains in reference §11.15. Example constants
and tolerances do not become universal acceptance budgets for other materials.

### 11.16 The multiscale physical-mechanism library

Separate immutable mechanism, qualified representation and stateful instance.
Physical scale transfer needs units, geometry/thickness rules, boundary inputs
and an applicable similarity argument. Remeshing is a different change. Compose
through supported ports and preserve exchanges; geometric resemblance alone is
not proof of transferable response.

### 11.17 Learn reusable membrane responses from qualified experiments

Triangles and their neighborhoods contribute native energy, strain, force,
curvature/state labels appropriate to the law; bending/attachments may span
elements. Use the existing AP02/cloth adapters and GPU characterization paths.
Keep detailed physics authoritative outside the trained domain. Optional learned
fits must beat an adequate analytic/table/native path on useful total cost and
error. DFT/Materials Project data may inform applicable source properties; they
do not directly supply universal per-triangle gameplay dynamics.

### 11.18 Procedure-driven mechanism factory: the worker follows evidence

Reuse current factory, recipe and receipt owners. Define the physical question,
freeze relevant independent checks, generate only needed cases, retain failures,
fit/select a representation and admit it only within its measured domain. Batch
GPU work using existing reservations. This qualification procedure is conditional
on changed physical behavior; it is not a research prerequisite for ordinary UI
wiring, documentation or reuse of already qualified responses.

### 11.19 Recursive research: creative discovery with independent physics checks

Agents may discover better structures, procedures and implementations. Tie each
bounded exploration to a current Blender capability, a concrete player benefit
or an explicitly chosen high-value uncertainty. Qwen may choose another method,
stop an unproductive line and retain useful surprises as proposals. Improve the
process without weakening the independent judge or relabeling failed evidence.

### 11.20 Artificial proteins: from physical alphabet to playable matter

“Artificial protein” means a generated reusable physical mechanism, not a claim
of molecular/protein fidelity. Build from existing geometric/material primitives,
qualify response and compose through declared ports. Detailed and reduced models
can coexist under explicit validity and state-transfer rules.

#### 11.20.12 Workshop integration audit

AP01/AP02, construction packets and scripted native loops are foundations with
retained evidence, including failures and later corrections. Current Blender
capability is summarized in §3 and its linked receipts. Old next-step paragraphs
must not restart completed experiments or dispatch another standalone workbench.

#### 11.20.13 Functional construction kit, layers and preparation cost

Start with the supported cloth/shell, deformable solid, rigid part, rod and native
attachment set already exposed by Studio/libuipc. Imported geometry and region
materials become useful parts only after their mapping is admitted. Keep expensive
characterization/import preparation offline and reuse immutable results; measure
interactive assembly, solving, transfer, rendering and recovery together.

### 11.21 Database-grounded matter: structure snapshots become reusable responses

Use source conditions, units, licensing, corrections, specimen/material identity
and uncertainty. A database geometry, material parameter set, published measurement
and learned response are different kinds of evidence. Reuse existing data owners
and provenance/evidence indices instead of adding another catalog.

#### 11.21.3 Priority sources and useful subsets

Prioritize **UnitcellDB** for applicable architected-cell geometry/effective
response and **FEBio** for appropriate continuum constitutive/contact references
and examples. Match the exact material, loading, boundary conditions and scale;
neither supplies universal ready-to-use dynamic game parts. The original primary
links, usable subsets and source corrections remain in reference §11.21.3.
Materials Project and other databases are supporting candidates when the selected
law needs their actual data scope. No large download or solver installation is
required merely to continue the present Blender workshop.

#### 11.21.8 Reuse established results; check the new translation and behavior

Do not rederive every established published number. Preserve its conditions and
check our units, coordinate/material mapping, boundaries and changed behavior.
Use focused independent controls at the integration boundary. Source authority
does not certify our implementation; repeating unchanged original experiments
does not improve a Blender feature.

### 11.22 Peer-agent development: deliver the game, preserve the science

**Qwen leads:** first gather enough current source, paths and evidence to frame a
useful assignment. Choose the next Blender outcome, research or implement directly
when useful, select suitable peers and optimize task size, review and process.
Stop gathering once the task and uncertainty are clear; avoid another full audit.

**Maya usually implements:** use existing owners, deliver the scoped change and
checks, then return a report. **Step is read-only:** inspect supplied files and
evidence, analyze consequential issues and return findings; no code execution,
file edits or implementation. A researcher or flexible worker can be chosen when
appropriate. Actual runtime profiles, not this document, select model versions.

Every brief includes: game goal; specific Blender action and why it matters now;
known facts/unknowns; project/session and absolute source/test/evidence paths;
owned scope; deliverable/decision and stopping condition. Every agent returns a
report, including PARTIAL/BLOCKED work: outcome, actual evidence and limits,
recommendation and next action. The lead reads the terminal report, not merely
the tool's delivery acknowledgement, and gives the user an integrated report.

Qwen may accept, defer or reject Step criticism with reasons based on evidence,
user value, risk and cost. Only accepted scoped fixes go to implementation.
No mandatory Step round or agreement veto is added. Actual failed physical checks
remain failed for that capability. Use focused checks for consequential changes
and broader regression when the change or a failure justifies it.

Preserve goal/progress, the mandatory Blender path, current project and owner,
task purpose, pending/completed reports, decisions, failures and next action
through compression and resume. Retrieve artifacts and resume the same child
where possible. Keep one foreground model task at a time on this host and use
existing GPU resource coordination; this plan adds no context/output limit,
model change, scheduler or requirement to interrupt working agents.

### 11.23 Structure as nested membranes and repeating physical arrangements

Use geometric repetition and nested layers as a generative vocabulary. Explicit
material ownership, thickness, interfaces and boundary exchanges turn geometry
into mechanics. A shape analogy or one equation does not prove a universal law.
Compare supported arrangements through the existing native/training pipeline and
inspect their accepted geometry and response in Blender.

### 11.24 Production principle: more physical capability for less runtime work

Measure accepted useful behavior against full elapsed time, memory, transfer,
synchronization and rendering costs. Reuse qualified responses and choose fidelity
within measured domains. Preserve the simulated time and relevant exchanges;
batching is not skipping timesteps. A smaller residual or faster isolated kernel
is valuable only when it improves a required capability or protects its correctness.

### 11.25 Research that produces a playable matter workshop

Research starts from the next decision in §13.1. Check existing source/evidence,
then primary external sources if needed. End with a usable answer, applicable
conditions, owner to reuse and a concrete decision; stop when that is resolved.
Store detailed sources and trials in their existing records and update the
relevant plan paragraph. Do not append another research diary or restart a
scheduled research cycle. Current Blender delivery continues with supported
native methods while a new reduction/material remains unqualified.

## 12. Graphics and readability

Make source versus accepted physical state, selected parts, material regions,
connections, loading, domain limits and failures understandable. Use Blender's
viewport, Image Editor, Properties and existing inspectors. Visual polish must
not conceal an unsupported physical claim. Include useful contrast, readable
status text and recoverable controls; measure human usability separately.

### 12.1 The same production principle applied to the playable game

Choose work by the useful interaction delivered, development/review cost and
remaining risk. Include editor latency, native solve, model reload, failed attempts
and recovery in real workflow cost. Keep one primary milestone. A technically
correct experiment that answers no current design question is not the deliverable.

### 12.2 Chimera Studio: Blender as the current Chimera interface

**Entry and ownership.** Use **Chimera Blender** on the desktop or
`D:/Chimera-Maintenance/ChimeraStudio/Start Chimera Studio.cmd`.
The Membrane Workshop project is
`D:/Chimera-Maintenance/ChimeraStudio/Projects/Membrane Workshop/Chimera Membrane Workshop.blend`;
the layered project is
`D:/Chimera-Maintenance/ChimeraStudio/Projects/Layered Materials Workshop/Chimera Layered Materials.blend`.
Preserve original user projects; tests save owned copies. The integration source
root is `D:/Chimera-Maintenance/ChimeraStudio/integration`, with registration at
`python/chimera_studio/__init__.py`. `D:/Chimera-Maintenance` is only the container.

Read Studio's `AGENTS.md`, `integration/AGENTS.md`, `integration/README.md`, source
locks and the relevant [BLENDER_WORKFLOW.md](../../ChimeraStudio/integration/BLENDER_WORKFLOW.md)
section. Detailed operator contracts live in [OPERATIONS.md](../../ChimeraStudio/integration/OPERATIONS.md).
Those documents own commands and scoped evidence; this plan owns product direction
and priority. Older unimplemented/next-step sentences in their chronological
history require comparison with newer source and receipts before assigning work.

**Human and AI use one path.** Enable **N > Chimera > Local Z Code Connection**
for external control. The existing `integration/tools/studio_client.py` lists
`sessions`; select the actual intended project/scene, inspect, propose, apply and
poll the same operation. Use the protocol's IDs and recovery semantics. A live
request must not target a guessed session or another construction. Missing/stale
connections are reported, not bypassed by mutating the engine behind Blender.
CPU/unit work and owned headless Blender tests remain available when the window
is closed. Keep UI evidence explicit when the visible path has not been exercised.

**Working loop.** Open → inspect current source/accepted state → edit one supported
part/material/connection → build or bake with its existing owner → inspect native
consequences and limits → compare if useful → save a project copy → reopen offline
→ replay or explicitly continue with the supported checkpoint path. Use existing
Object/Edit/paint/Sculpt/Pose/animation adapters only within their tested mappings;
changing a workspace or seeing a modifier does not qualify new physical behavior.

**Persistence meanings.** A mesh-animation cache replays recorded samples. A
validated native checkpoint supports its declared physical continuation. A static
learned card answers within its domain. These are distinct. Save/open must retain
identities, purpose, sources and accepted results; pending commands reopen as
interrupted, not successful. Do not promise arbitrary-time continuation, automatic
physical Undo or unqualified cross-owner state exchange.

**Known gaps to assess against the selected task.** Membrane apex-weld reaction
inspection; general learned lateral/compliant response; broad CA/libuipc/native
coupling; additional camera/streaming coverage; arbitrary imports and large-scene
budgets. Existing detailed native fallback, taught static responses and current
workshop loops remain usable. No blanket repair/research prerequisite is imposed.

**Advanced techniques remain available, not a second queue.** The original
fifteen-technique table, method links, detailed status and measured examples are
preserved in reference §12.2. Reuse current implementations before extending them:

| Techniques | Existing direction / selection rule |
| --- | --- |
| 1. Small reliable construction language; 2. Library learning | Shared operations and learned/reused construction procedures. Extend one missing operation or useful reusable sequence. |
| 3. Quality-diversity / MAP-Elites; 4. Inverse design | Existing measured alternatives and bounded material/size searches. Keep useful tradeoffs; evaluate the declared native response. |
| 5. Learned solver warm starts; 6. Static condensation / component reduction | Use existing warm-start/reduction experiments where applicable; native residuals, port behavior and full cost decide acceptance. |
| 7. Hyper-reduction / optimized cubature; 8. Port-Hamiltonian learned components | Research options requiring their own domain/conservation evidence; do not claim general implementation from AP02 or a scalar card. |
| 9. Active learning; 10. Adaptive fidelity | Reuse targeted sampling and measured representation choices; broader dynamic transitions require qualified state transfer. |
| 11. Dependency-aware physical reuse; 12. Counterfactual failure explanations | Reuse existing identity-aware results and requirement comparisons; explanations must follow actual measurements. |
| 13. Bounded evolutionary code/workflow optimization; 14. Outcome-driven agent procedure optimization | Improve a measured bottleneck with reversible candidates, existing checks and an accepted user outcome. No arbitrary code execution from an untrusted recipe. |
| 15. Retrievable procedural memory | Use current knowledge/procedure/assets and evidence adapters; search a relevant usable result before creating another registry or experiment. |

## 13. Roadmap and release gates

One active delivery path: useful Blender construction → coherent human/AI editing
and recovery → selected additional material/connection capabilities → measured
performance and reusable assemblies → a player-facing game slice when the user
chooses it. Preserve the construction release and B/S/AP evidence at their original
scope. A named release freezes explicit interfaces, save compatibility and evidence;
it does not certify every future material or open a separate game repository by itself.

### 13.1 Worker handoff: deliver usable matter through Blender

1. **Resume, do not restart.** Read this plan's active sections, current task and
   reports. Keep completed work, live ownership and existing goal state. If an
   in-progress engine task lacks a Blender destination, preserve its safe
   checkpoint and reframe the remaining increment around the user action it serves.
   Do not kill another agent or discard its work to enforce this instruction.
2. **Choose one concrete gap.** Prefer a missing/confusing operation in an existing
   construction: discovering the correct controls/session, editing/material binding,
   connection inspection, intelligible failure, recovery, save/reuse or an actual
   blocking physical defect. Inspect the current implementation first; the two
   nine-check workshop loops are already recorded as passing.
3. **Gather and brief.** Qwen names the `.blend`/owned copy, UI or shared operation,
   native owner, exact source/evidence and desired user outcome. Delegate a bounded
   gap or work directly. For backend work, identify its Blender caller and the
   integration evidence needed to close the parent task.
4. **Implement through existing owners.** Keep Studio pins and scientific contracts.
   Native dependency changes have their own owned source/build and focused checks;
   deliberately review/repin the integration before claiming the Blender feature
   works. Do not copy a changing live engine binary or replace the interface with
   `tools/game_shell`, a browser workbench or an engine-only demo.
5. **Accept proportionately.** Check the changed behavior, applicable independent
   physics/state correspondence, and affected save/reopen/replay path in Blender.
   Reuse unchanged evidence. Documentation-only work needs coherence/link/hook
   checks, not GPU experiments. If a required check cannot run, report it as pending
   with the actual blocker; no fabricated completion.
6. **Integrate reports and improve the next step.** Qwen reads each report, triages
   Step findings and sends only accepted fixes to an implementer. Record the
   outcome, evidence, limits and next decision in the existing work record. Update
   this plan's current status in place when the direction/capability changes.

If no narrower task is active, the next assignment is to identify and close the
smallest remaining friction in the **existing Blender construction loop**, using
the current shared client and operators. Deliver an observable improvement, not
another inventory, a replacement client or a new demo. The broad game, research
catalog and optional numerical techniques do not override this selection rule.

**Stable goal meaning:** implement this file through the mandatory Blender path,
continue existing progress, choose the highest-value useful construction outcome,
give each agent purpose and exact evidence, preserve that through compression,
and improve the process while retaining independent physics checks. The saved
goal text and database do not need to be recreated for this consolidation.

## 14. Risk controls that preserve the game

| Risk | Required response |
| --- | --- |
| Drift back to the standalone engine | Require the Blender project/action/caller in the brief and user-facing acceptance. Preserve backend work as a dependency. |
| Research or review takes over delivery | Qwen chooses the decision and stop condition; retain optional discoveries without turning every criticism into work. |
| Correct-looking display hides unsupported physics | Name the native owner, law/domain and independent evidence. Keep unqualified behaviors explicit. |
| Lost edits, uncertain calls or invalidated state | Preserve accepted state and IDs, inspect terminal outcome, recover explicitly and test affected persistence. |
| Useful detail exhausts hardware | Measure full workflow cost and use qualified reuse/reduction. Respect GPU leases and active services. |
| Plan grows into conflicting queues again | Keep current decisions here, commands/evidence with their owners and historical designs in the reference. Replace obsolete status instead of appending another overriding paragraph. |

## 15. Change and publication discipline

This is the active navigation and decision file. Keep one current handoff (§13.1),
one capability summary (§3), one Blender execution contract (§12.2), and one role
contract (§11.22). Technical detail and daily results belong in their existing
source documentation, receipts and work logs. Add only a compact linked status
change here. Historical reference text does not automatically create tasks.

Preserve concurrent edits, source ownership, original projects, existing evidence
and the live Git HEAD/index. Publish completed owned changes under the existing
project authorization without bundling unrelated work; verify the intended remote
ref and report actual publication status. No public Blender repository, runtime
restart, model retuning or controller gate advancement follows from a plan edit.

The [consolidation audit](GAME_PLAN_COHESION_20261022.md) records the preserved
source identity, conflicts resolved, instruction surfaces updated and validation.
The full prior plan remains retrievable from the reference; reducing this active
file does not delete the product vision or reset any implementation milestone.
