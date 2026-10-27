# SEALED — a game built from simulated matter

**Active delivery plan · operator direction consolidated 2026-10-22.** Keep this
file named `GAME_PLAN_ACTION_RPG.md`. The saved Z Code goal follows this file;
retain its identity, progress, budgets, decisions and child conversations.

## 0. Mandatory delivery path and reading order

**Operator goal update, 2026-10-26:** build and validate the executable Z Code
workflow that enables the agents themselves to create games, mechanisms,
environments and other constructions from simulated matter. Connect the existing
ontology/databases, DFT evidence and scale reduction, machine learning/local CA
rules, native physics and Blender. Require spatial understanding before
implementation, independent physical/Blender tests, recovery from missing
evidence, retained recipes/tools/tests and demonstrated reuse for a different
construction. Qwen coordinates; Step 3.7 performs both spatial preparation and
post-implementation review through actual subagent handoffs. Instructions alone
do not complete this goal. Preserve sessions and ownership, use one local
inference agent at a time with the existing GPU handoff, and keep water deferred.
The [executable workflow record](../tools/zcode/MATTER_WORKFLOW.md) separates
implemented dispatch/checkpoint checks from the pending real-agent alloy,
energy-accounting, CA and reuse demonstrations. The original saved Z Code goal
has not been reset or resumed by this workflow development.

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
| Two database-to-asset matter fields: NIST 6061-T6 aluminum and 304 stainless, with native contact and reusable paired assets | Existing `tools/science_funnel/matter_cards.py`, ontology recipes and `model.matter_interaction.contact.v1`; [paired Blender workflow](../../ChimeraStudio/integration/BLENDER_WORKFLOW.md#two-matter-fields-and-ophysics-coverage-october-23); [acceptance](../../ChimeraStudio/integration/evidence/matter-pair/acceptance.json) | NIST E at 293 K; authored density/Poisson ratio and interaction friction. The original contact/continuation receipts are historical and currently stale. The newer solid-alloy fixture exercises both parent recipes within its own scope. Heat, yield/fracture, adaptive detail and real-time performance remain unqualified. |
| First source-to-Blender alloy equilibrium recipe implemented | `model.matter_mixture.al6061_ss304_equilibrium.v1`, existing scientific intake, MatCalc Al 2.032 and offline pycalphad; [alloy workflow](../../ChimeraStudio/integration/BLENDER_WORKFLOW.md#first-alloy-recipe-october-23), §11.21.13 | Nominal 95 mass% 6061 + 5 mass% 304; five equilibrium temperatures at 101325 Pa. Ten numerical reference checks remain current; thirteen earlier Blender checks are historical with changed dependencies. This phase display does not perform spatial mixing; the separate solid recipe below supplies mechanical response. |
| Solid alloy deformation and interaction with the original two fields | `model.matter_mixture.al6061_ss304_solid.v1`, §11.21.15; [acceptance](../../ChimeraStudio/integration/evidence/alloy-mechanics/acceptance.json) | Nine solid reference and nineteen Blender construction/reopen checks remain current. 300 K provisional elasticity/contact; finest axial error 0.8361%. Two explicit phase proxies cover 12.0444 mass%; measured-alloy validation and mesh-converged bending remain open. |
| Game matter roster and interaction matrix | `req.game_matter_catalog.v1`; [readable catalog](GAME_MATTER_CATALOG.md), [canonical data](../tools/science_funnel/data/game_matter_catalog.json), §11.21.14 | 34 entries, 29 interaction scenarios and 29 existing source routes; all 23 earlier material candidates and 16 broad recipe groups accounted for. Five initial material roles, one optional existing alloy, 21 later and seven optional/reference entries. Planning coverage is not runtime qualification. |
| Accumulating matter-feature benchmark catalog and evidence inspection | `model.matter_benchmark.v1`; [catalog](../tools/science_funnel/data/matter_benchmarks.json), `tools/science_funnel/matter_benchmarks.py`, §§11.21.12–15 | October 23 read-only audit: four current recorded passes, six specified families, three stale historical groups, zero recorded failures. Changed dependency pins mark old results stale instead of silently renewing them. Alloy source/test inspection is available inside Blender. |
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

**CA and machine-learning connection, October 26:** develop local rules that
materialize structure, useful mechanical behavior and energy exchanges through
the existing ontology recipes and native owners. The first implemented component
is the [learned matter rule lab](../../ChimeraStudio/integration/MATTER_RULE_LEARNING.md):
a source-bound local elastic-energy fit, physical tetrahedral neighborhoods and
Blender inspection of the saved alloy construction. Its native energy/force and
save/reopen checks are scoped to this offline component. Function-conditioned
structure learning, temporal CA updates and the complete native port-work ledger
remain required; a fitted constitutive response does not close those steps. The
linked implementation sequence preserves the active haul assignment and current
agent work. Its additive ontology object is a checked proposal, not a rewrite of
the graph used by the running agents.

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
error. The DFT-to-alloy route in §11.21.11 connects electronic structure evidence
to assessed thermodynamics and reduced constitutive response at game scale.

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

#### 11.21.9 Matter cards: the reusable source-to-construction path

The October 23 implementation uses the existing ontology and intake: pinned NIST
6061-T6 HTML → existing `nist_al6061` adapter/assertion → ontology recipe
`model.matter_card.al6061_elastic.v1` → compiled entry in Studio's existing
`published_materials.json` → `create_matter_card` → native libuipc FEM → existing
construction asset and memory. The saved part carries the recipe, exact source
identity, hashes, assumptions and purpose. Human and AI construction use the same
operation. The second route uses a pinned NIST 304-stainless source bundle through
the same intake, compiler, catalog, construction and persistence owners. The first
card's packet and earlier assets remain valid. Arbitrary database routing is future
work through these owners, not an additional catalog or solver.

The baseline is a declared reference state: undeformed dimensions, 293 K and initial
zero velocity. Aluminum uses authored density 2700 kg/m³ and Poisson ratio 0.33;
stainless uses authored 8000 kg/m³ and 0.29. NIST's polynomials give E = 70.358592
and 199.533627 GPa respectively. The native law owns stored elastic
energy; time advances through native positions, velocities and checkpoint history.
An empty scene has no instantiated matter. A new asset instance starts a new state;
reopening a checkpoint retains an existing state's history. This makes the temporal
part explicit without inventing an independent energy account.

Each additional route should reuse source adapters, conditions/units, recipe
reduction, named attachment regions, construction memory and asset persistence.
The increasing library then reduces repeated authoring work. The pilot fixes its
detail at 30 nodes/48 tetrahedra; hardware-dependent refinement remains a separate
extension of the existing representation machinery. Test our new translation and
state behavior. The operator explicitly waived redundant Blender mouse/interface
testing on October 23.

**Interaction is now part of the recipe path.** `concept.matter_field` names the
three-dimensional material region and its state through time; these two cards use
tetrahedral FEM interpolation. `set_matter_interaction` applies the ontology's
`model.matter_interaction.contact.v1` through the existing native material-pair
table. Both regions participate in the same native solve. The aluminum rests on
the steel with contact enabled; disabling just that pair removes support, changing
the final aluminum height by 31.1 mm in the recorded control. Contact groups are
material-wide and distinct from welded attachments. Saved native state continues
the coupled construction; a construction asset instantiates a new history.

#### 11.21.10 oPhysics coverage and the next interaction channels

The [oPhysics index](https://ophysics.com/index.html) is a useful concept and
example reference. It does not supply measured material-property recipes. The
[captured-topic audit](../tools/science_funnel/data/ophysics_coverage.json) accounts
for all 136 unique topic pages linked by that index: 18 map directly to existing
named concepts, 107 map through 18 new explicit refinements of existing families,
and 11 are drawing, geometry/art, music-export or perception utilities rather than
additional matter laws. All additions are linked into the existing ontology.

| Family | What the audit establishes | Current Blender matter-field scope |
| --- | --- | --- |
| Motion, vectors, inertia and equilibrium | Existing dynamics; explicit kinematics, center-of-mass and angular-momentum concepts added | Native motion/contact and existing hinges; each construction retains its own scope. |
| Contact, friction, momentum and energy exchange | Existing concepts reused, new sourced-material contact recipe | Two-solid contact/support comparison, reusable assets and physical continuation are exercised. Ideal collision restitution and heat production are not newly implemented. |
| Oscillation and waves | Explicit harmonic limits, phase/superposition, boundary modes and Doppler regimes added | Existing wave family; frequency, acoustic propagation and shock fidelity are not established by the two-solid example. |
| Light and optics | Explicit spectral mixing, polarization, diffraction, dispersion and image formation added | Appearance rendering remains separate from a coupled physical optical-field solver. |
| Electric and magnetic interactions | Existing circuits/magnetic families; explicit Coulomb potential, Lorentz force and EM propagation added | These are ontology specifications, not active exchange channels between these two solid cards. |
| Fluids and modern physics | Explicit hydrostatics/buoyancy, Bernoulli/Torricelli assumptions and hydrogen-level transitions added | Fluid coupling remains deferred under the existing water decision; no general atomic solver is claimed. |

Choose subsequent channels by a concrete construction need. Reuse one shared
interface owner for paired influence and its energy/state convention; specify
required database properties, regime and observable before binding a new channel.
Adding a concept to the ontology does not automatically activate a solver.

#### 11.21.11 DFT-informed continuous composition and alloy recipes

**Operator direction, October 23:** combine the two matter fields through an
energy-based material recipe, using density functional theory (DFT) as a
foundation and databases to make reusable game assets. The existing ontology
already has `source.shortcut.jarvis`, species transport, phase change, energy
accounts and compact cell state. Reuse these. The new
`model.matter_mixture.dft_calphad.v1` connects them to explicit electron-density,
composition-simplex, alloy free-energy and phase-field concepts.

DFT expresses ground-state electronic energy through a three-dimensional
electron density, with the nuclear/external-potential context and electron count
specified. Practical calculations select an approximate functional. This gives
the offline foundation for material energy/response evidence; finite-temperature
processing and time evolution need their corresponding closures. Electron number
density, bulk mass density and electronic density of states have different
meanings. [Hohenberg and Kohn](https://journals.aps.org/pr/abstract/10.1103/PhysRev.136.B864)

The continuous mixture coordinate is a **composition simplex**: nonnegative
constituent fractions sum to one. For two feedstocks with elemental mass fractions
`q_Ai`, `q_Bi`, their mixture has `w_i = a*q_Ai + (1-a)*q_Bi`, where `a` is the
fraction of feedstock A by mass. Convert to mole fractions explicitly before a
model expecting that basis. At zero inventory, retain an empty state rather than
undefined normalized fractions. Composition varies continuously; phase transitions
can change the material response. A grade label or bulk density alone cannot
identify the elemental mixture.

The source-to-asset path is:

1. Resolve elemental inventories and preparation/state from the parent recipes.
2. Reuse **JARVIS** for applicable DFT structure/energy/property evidence, with
   **Materials Project** as another route. MP documents elastic tensors and an
   alloy-candidate endpoint; a candidate is not a completed engineering recipe.
   [JARVIS-DFT](https://www.nist.gov/programs-projects/jarvis-dft),
   [MP API](https://docs.materialsproject.org/downloading-data/using-the-api/getting-started)
3. Select a compatible **CALPHAD assessment** for phases and free energies versus
   composition, temperature and pressure. Use **NIST Alloy Data** observations as
   experimental constraints. Pin exact records, conditions, units and source
   identities through the existing intake. pycalphad is a candidate offline
   evaluator; no dependency was installed in this design increment.
   [CALPHAD](https://www.nist.gov/programs-projects/calphad-data-informatics),
   [alloy measurements](https://www.nist.gov/mml/acmd/trc/nist-alloy-data)
4. Evaluate phases, then obtain the effective response for the selected
   preparation/microstructure. Compile bounded tables or a constitutive energy
   model through existing reductions, the published-material catalog, shared
   Blender operations and native asset/checkpoint owners. Elastic data have an
   established DFT-to-continuum route through strain/stress calculations.
   [MP elasticity](https://docs.materialsproject.org/methodology/materials-methodology/elasticity)
5. Add spatial mixing when required: stirring advects material, chemical-potential
   gradients drive diffusion, and phase fields describe evolving microstructure.
   Thermal processing adds heat/enthalpy and latent energy. These channels need
   an integrated native owner. [Phase-field equations](https://mooseframework.inl.gov/moose/modules/phase_field/Phase_Field_Equations.html)

**First Blender slice:** a homogeneous composition/temperature sweep for a pinned
assessment, exposed through the existing Matter workshop as a future **Compose
Matter** action. The current 6061 and 304 cards supply elastic baselines but no
exact elemental analyses or complete alloy free-energy model. Resolve those
inputs for the actual feedstocks. A separately named binary Al–Fe benchmark can
exercise the evaluator if multicomponent coverage is unavailable; it must retain
its own identity. An averaged stiffness is not the predicted alloy result.

**Compounding improvement:** store qualified response over a region of composition,
temperature, phase and strain/history, rather than only a single named grade.
New cards within that region reuse the same database evidence and compiled model.
Refine where a selected observable needs more accuracy; retain phase boundaries,
source/model identity, conservation, scope and error. Where applicable, derive
related responses from one fitted energy potential. Transport and irreversible
history still need their own laws. DFT computation stays offline.

The original increment records the [queryable design](../tools/science_funnel/data/matter_mixing_design.json)
and checked ontology additions. Its first bounded implementation is now recorded
in §11.21.13; the original design and two contact-enabled assets are preserved.

**Connected to learned local rules, October 26:** the Blender matter-rule lab
now replays the existing solid-alloy source route and retains phase-level DFT
lineage. Six routes use DFT-derived elastic tensors, including JARVIS JVASP-1075
and JVASP-8222; one uses measured nanoindentation data. Proxies and authored
baselines retain their labels. The implemented path is DFT-derived properties
through phase reduction, alloy/native response and learned cell energy. Raw
electron-density grids, new DFT jobs, temperature-dependent atomistic response
and learned growth/time evolution are still separate required capabilities.
The [DFT connection and calculation-bundle contract](../../ChimeraStudio/integration/MATTER_RULE_LEARNING.md#dft-supplies-the-microscopic-material-evidence)
states the inputs, source identities, density meanings and energy references.

#### 11.21.12 Accumulating standardized tests for matter features

**Operator direction:** build a growing library of reference experiments, like
checking a thermometer against boiling water under known environmental conditions.
Every feature claims a tested range of behavior. Cases attach to ontology
capabilities and are reused by relevant recipes; a new grade does not require
inventing its test protocol again. Different composition, preparation or physical
regime may require different reference data and additional cases.

Each versioned case records specimen/composition, geometry, temperature, pressure,
boundaries, physical time, source/model revisions, an independent reference,
observable/units, uncertainty and acceptance budget, numerical resolution and
cost. Set tolerances before the run. Calibration/fitting cases and independent
validation cases are identified separately. Keep immutable results, including
failures; a recipe/source change marks affected evidence for review or rerun.

For the thermometer example, use the saturation temperature at the known absolute
pressure and water composition. Altitude plus an atmospheric model can estimate
pressure; weather changes it. A later thermal test also checks latent energy for
the amount vaporized. This is a reference-test definition, not a change to the
existing water implementation priority.
[NIST thermometer checks](https://www.nist.gov/pml/sensor-science/thermodynamic-metrology/mercury-thermometer-alternatives/mercury-thermometer-7),
[IAPWS water formulation](https://iapws.org/technical-guidance/release/IAPWS-95)

The [starter catalog](../tools/science_funnel/data/matter_benchmarks.json) has three
recorded groups: NIST source-curve conversion, native pair-contact support with its
disabled-contact control, and saved-state continuation. Six additional families
are specified: elemental inventory, small-strain deformation, alloy phase
equilibrium, diffusion, thermal phase change, and resolution transfer. Source
conversion, physical response and persistence are different claims; no aggregate
PASS implies all properties of a material are correct.

`python -m tools.science_funnel.matter_benchmarks` inspects the catalog and pinned
historical receipts without running native physics. `--feature <ontology-id>`
selects relevant cases. Results distinguish recorded pass, recorded failure,
stale/missing evidence and an unrun specification. The tool checks named dependencies;
full runtime environment applicability remains with the original evidence owner.
Existing test runners remain authoritative for new runs. The alloy panel now
exposes its source assumptions, exact states and ten reference checks; the catalog
remains a read-only evidence auditor rather than an automatic test dispatcher.

#### 11.21.13 First alloy recipe implemented in Blender

**Open `ChimeraStudio/Start Alloy Workshop.cmd`, then N > Matter > Alloy Recipe.**
The two existing matter cards bind to an explicit nominal 1 kg feedstock recipe:
950 g 6061 and 50 g 304. Existing `science_funnel` intake pins supplier composition
bounds, the authored selections, the unmodified MatCalc Al 2.032 assessment and
NIST's unary aluminum fusion reference. The additive ontology recipe selects its
sources, phase exclusions, elemental mass basis, pressure and five temperatures.
An isolated offline pycalphad 0.11.1 environment computes the packet; Blender
reuses it through the same human/AI operation path, including state changes,
asset export/import, stale-proposal checks and fresh-process reopening.

The model predicts liquid **mass fractions** of 0%, 0%, 19.2%, 97.1% and 100% at
300, 700, 900, 1000 and 1200 K respectively, at 101325 Pa. Its colored three-dimensional
partitions are a mass-fraction diagram, not predicted grain shapes or phase volumes.
Both mass and mole fractions, phase compositions, Gibbs energy, enthalpy, source
identities and assumptions remain in the saved asset. The parent elastic moduli
are preserved, not averaged into a new mechanical law.

**Measured evidence:** ten preregistered reference checks passed. Pure Al's calculated
fusion point is 933.470833 K versus NIST 933.45 K (assigned uncertainty 0.2 K;
preregistered model budget 0.5 K). Maximum elemental inventory residual is
8.4233e-9 in mole fraction; increasing sampling from 500 to 2000 changes phase
fractions by at most 1.4482e-9. Enthalpy identity, constrained-liquid free energy,
pure endpoints and empty/negative inventory cases also pass. Nine Blender
construction/reuse checks and four fresh-process checks pass. Eighteen existing
source/catalog tests pass. Receipts, source/solver pins, failures and replay
commands are linked from the [workflow](../../ChimeraStudio/integration/BLENDER_WORKFLOW.md#first-alloy-recipe-october-23).

**Limits and next decision:** the feedstock compositions are authored values
within grade limits, not measured lots. The database is optimized for Al-rich
compositions; Ni is included but this multicomponent case is exploratory. The
unary reference may have informed database calibration and is not a withheld
experiment on this alloy. Next obtain a composition/preparation-specific alloy
holdout and phase elastic/volume data, then bind a justified effective mechanical
energy law through the existing native owner. Add kinetics/transport only for a
chosen preparation experiment. No new DFT calculation, spatial stirring, heat
transfer, deformation or real-time qualification is claimed by this slice.

#### 11.21.14 Working interactions, then the game's matter catalog

**Operator sequence (October 23):** first deliver complete, representative examples
of matter fields interacting correctly in Blender. Then produce the list of all
matter types required by the game's agreed environments, constructions, equipment,
characters and gameplay. Keep that list in the existing ontology and recipe/data
catalog so each entry can become a sourced, tested, reusable asset.

An interaction example is complete for its declared behavior when the real data,
recipes, native physical response, independent reference checks and saved/reusable
Blender construction form a working path. Record the participating fields, initial
conditions, exchanges of mass/energy or force, supported range and measured error.
Use the existing contact example and alloy work as starting points. The solid
alloy now has a bounded native elastic/contact example (§11.21.15), including
source routing, physical references, controls and reusable Blender assets.
Preparation-specific transport remains separate. Qualify bounded examples needed
by gameplay; completing every possible physical interaction is not a prerequisite
for making the catalog.

After those examples, inventory the matter actually needed for the planned game.
Candidate families to check include metals/alloys, minerals/soil/stone, glass and
ceramics, wood and fibers, polymers/elastomers, liquids, gases and biological
materials. These are coverage prompts, not a finalized roster or new gameplay
commitments. Derive the final entries from concrete objects and actions, and mark
initial-playable requirements versus later additions. Distinguish a substance or
mixture recipe from its phase, preparation and state; share underlying recipes
where game objects need the same material behavior.

Each catalog entry must link its game uses, ontology identity, composition/parent
recipes, source databases and missing data, relevant states/conditions, required
behavior, reference tests, Blender asset and permitted detail/performance budget.
Accompany the catalog with an **interaction matrix**: which material pairs must
contact, transfer heat, mix, bond, dissolve, react or otherwise affect one another
for a named game action. Record required, demonstrated and unsupported behaviors
separately. This turns the inventory into the next implementation order while
allowing every completed recipe and reference experiment to serve more objects.

**Delivered October 23:** the [game matter catalog and interaction matrix](GAME_MATTER_CATALOG.md)
now resolve that inventory through the existing ontology and scientific intake.
The [canonical data](../tools/science_funnel/data/game_matter_catalog.json) contain
34 material/recipe entries, 29 interaction scenarios, 29 existing source routes
and 14 shared reference-test families. All 23 existing `material.catalog.*`
identities and 16 `material.space_recipe.*` groups are accounted for. Three
previously missing planning families—circulating biological fluids, biological
resource matter and electrode/electrolyte mixtures—are added as **specified**
nodes; no coefficients or physical qualifications are invented. Existing element
identities, recipes, source nodes and evidence remain unchanged.

| Game scope | Materials / roles | Current position |
| --- | --- | --- |
| First rescue kit: five required roles | 6061-T6 aluminum, 304 stainless, ground/stone, fiber cloth/rope and compliant silicone/elastomer pad | Two sourced metal cards exist. Ground, cloth/rod and pad mechanisms exist, but the selected real material and pairs need data/tests. Explicitly authored physical surrogates may serve the initial scene. |
| Optional current extension | Existing 95:5 aluminum/stainless solid mixture | Bounded source-to-Blender elastic/contact example is available; qualification limits remain in §11.21.15. |
| Later game: 21 entries | Other steel, wood, glass, polymers, ceramics, fiber composites, conductors, water, air, sand, clay, adhesive, oil, six tissue families, circulating biological fluids and biomass | Concrete construction, terrain, infrastructure, companion and resource uses are mapped. No generic mechanism is presented as a measured material. |
| Retained optional/reference scope: seven entries | Ethanol, surfactant solution, wet foam, wax, selected fuel/coolant mixtures, isotope-bearing material and electrochemical mixtures | Preserved broader ontology coverage; none is a new prerequisite for the rescue slice. |

Water/ice/vapor are states of one conserved inventory. Rope, woven sheets,
laminates, porous pads and creature bodies are preparation/assembly recipes;
their constituents and interfaces remain explicit. A mechanical companion
surrogate can use admitted parts without claiming biological tissue fidelity.
Its powered pull/stall/work supply still needs a usable integrated example.
Light, sound, electricity and fire are channels or processes, not extra bulk
substances. Empty space has zero matter inventory and undefined composition;
field and boundary energy remain explicitly owned.

The matrix separates current scoped demonstrations, historical evidence, generic
mechanisms, missing implementations and deferred channels. The read-only
[audit](evidence/game-matter-catalog-20261023/audit.json) found four current
benchmark passes, six specified families and three stale historical groups;
no physics was rerun for this catalog. Unlisted material/channel combinations
are unqualified. Every entry records its source/data gaps, states, required laws,
test families, actual asset links and unresolved performance limits.

**Next useful construction:** close the rescue load path with a sourced or
explicitly authored strap/rope, compliant pad, ground contact and a recoverable
attachment/repair comparison. Reuse native cloth/rod/FEM/contact/stitch owners
and saved assets. Qualify the alloy's bending/density details as an optional
brace improvement. Biological, fluid, thermal and electrical extensions follow
named game needs; the existing water deferral is retained. This is a prioritized
catalog, not authorization to build all 34 entries simultaneously.

#### 11.21.15 Solid alloy deformation and contact in Blender

**Delivered October 23:** `Start Alloy Workshop.cmd` now opens the solid alloy
workshop. A 300 × 40 × 2 mm mixed field bends under the original stainless recipe
and transfers load into two instances of the original aluminum recipe. The
shared `create_alloy_field` operation and **N > Matter > Solid Alloy Field** panel
create native tetrahedral volumes from both parent cards. Existing material-pair
contact, construction export/import, playback and native checkpoints own the
remaining path. The earlier thermodynamic workshop is preserved unchanged.

**Ontology/data path:** immutable recipe
`model.matter_mixture.al6061_ss304_solid.v1` derives from the existing 95/5
CALPHAD inventory and a scientific-funnel assertion routing all seven 300 K phases
to published elastic data. NIST JARVIS supplies Mg2Si and theta-Al2Cu tensors and
densities; pinned papers supply Al, Al18Mg3Cr2, Al3Ni and an alpha-phase proxy.
Mass fractions become volume fractions using explicit phase densities. Random
orientation Voigt–Reuss–Hill averaging supplies effective bulk/shear energy,
then E = 91.290190 GPa, nu = 0.320590 and density = 2798.5201 kg/m3. The existing
native StableNeoHookean implementation receives those values; parent E values
are not averaged and no replacement dynamics or artificial softening is added.

**Evidence:** nine solid-reference checks pass, including source-table modulus
checks and native axial extension against rho*a*L^2/(2E). The fine mesh differs
from the analytic reference by 0.8361%; 20→40 axial cells change extension by
0.6486%, halving the time step leaves the settled result unchanged, and the
held-out double load differs from a 2× response by 0.0139%. Ten existing
thermodynamic reference checks and eighteen source/catalog tests pass again.
Fifteen Blender checks and four fresh-process checks pass. Each contact/control
scene executes 50 converged native steps; continuation reaches step 60 with an
identical earlier cache prefix. Loaded alloy sag is 0.33154 mm, compared with
0.00601 mm when steel/alloy contact is disabled. Disabling aluminum/alloy contact
removes support. `Solid Alloy Field.blend` and `Three Matter Fields.blend` retain
their recipes and import as independent constructions. Evidence and replay are
in the [workflow](../../ChimeraStudio/integration/BLENDER_WORKFLOW.md#solid-alloy-fields-october-23).

**Scope:** this is an explicitly provisional, isotropic, fully dense elastic
solid at 300 K. The alpha-AlFeMnSi and Cr-rich phase substitutions cover 12.0444%
of mass; density/Poisson baselines and ground-state tensors frozen at 300 K remain
declared approximations. Conditional Voigt/Reuss bounds and a ±25% proxy-modulus
sensitivity are retained, not presented as experimental uncertainty intervals.
The native bar reference qualifies the elastic mapping; the contact scene proves
load transfer and deformation, not mesh-converged bending compliance. It does
not establish this alloy's measured strength, yielding, fracture, molten flow or
real-time performance. Native bakes take 25.1 s loaded, 28.5 s without steel
contact and 184.6 s without aluminum contact for the 0.5 s fixtures on this host.
Next replace the provisional phase/density inputs with composition/preparation
specific measurements, qualify bending resolution for a chosen gameplay error
budget, and derive the matter catalog/interaction matrix from §11.21.14.

### 11.22 Peer-agent development: deliver the game, preserve the science

**Executable matter workflow (2026-10-26, in progress).** The opt-in controller
`tools/zcode/matter_workflow.py` and `matter_hook.py` binds a request to a native
lead session, enforces ready dependencies/profiles, records terminal child
reports, routes missing evidence to research or bounded experiments, dispatches frozen tests and requires
Step before implementation and afterward. Native Agent/SendMessage preserves
distinct Qwen and Step models. Installed-CLI mock-endpoint wiring and CPU fault
tests pass; these are not real model or Blender qualification. Remaining work and
evidence are in [MATTER_WORKFLOW.md](../tools/zcode/MATTER_WORKFLOW.md).
For a new physical capability, a separate implementation-profile task authors
tests after spatial/source understanding; Step approves the exact proposal before
construction implementation. The original acceptance remains fixed. The private
real-run entry point is `tools/zcode/matter_setup.py`; the first alloy request is
running in `Runtime/zcode-matter-workflow-20261026/alloy-real-01` under the workspace
root. Its checkpoint records actual progress; no completed physical or reuse
demonstration is claimed. Production agent definitions and sessions are unchanged.

New requests can enter through `matter_setup.py prepare-intent` with literal user
text and an operating envelope. Actual native Step roles supply conceptual 3D
design and separate specification review before the controller freezes a request.
Empirical gaps become dependencies; measurements needing the future construction
become explicit acceptance tests. Immutable clarification and bounded report
repair retain the same child and prior evidence. Installed-CLI intake wiring
passed with mock responses; real science and successful reuse remain open.
The real alloy experiment returned measurements, but report references and a
missed terminal-result retrieval required recovery. The same child is resumed
with a structural report checker; no measurements or physics were rerun by Codex.
The report was subsequently accepted structurally and returned to the original
Step child. Step's first resumed response repeated its earlier missing-evidence
report without recorded reads of the new measurements and had invalid trailing
JSON. Its next correction failed similarly. The controller stopped that task;
tested future dispatches now distinguish accepted dependencies from failed history
and require Step's cited assessment of the new evidence. One explicit transport
repair per task preserves the legacy experiment allowance as consumed and refuses
scientific/test failures. The same Step child has been resumed with this revised
handoff; scientific acceptance remains open.
The resumed Step read the accepted experiment report and dependency manifest,
corrected its own JSON using the report checker, and returned a valid
`NEEDS_EVIDENCE` report. Qwen dispatched its new question about native contact
gradient scaling and friction export to the read-only researcher. This verifies
an actual evidence/recovery handoff; it does not qualify the alloy. Automatic
format retries now count consecutive invalid reports since a validated terminal
report, preserving historical failures and consumed explicit repair allowances.
The research handoff also exposes native fetched-source artifacts and warns when
the local web tool returns excerpts rather than a complete source. Missing lines
remain unknown and can trigger bounded source acquisition; source retrieval is
not physical qualification.
The research report has now returned a narrower friction question; Qwen dispatched
analysis of saved measurement arrays before any conditional native rerun. Native
web observations are archived separately from report claims on future terminal
handoffs. This improves evidence retention without qualifying the construction.
That analysis found transient nonzero friction in the saved arrays without a GPU
rerun. The researcher inspected it and returned READY; Qwen has now resumed the
original Step child with all three accepted evidence reports. Step's assessment,
independent test plan and full physical qualification remain pending.
Its first resumed draft nevertheless repeated the old questions without reading
the new brief. Native records confirm delivery; the report checker refused the
missing dependency assessments. Future private attempts now require actual native
Read access to the current brief/manifest and accepted reports before acting and
at terminal acceptance. Identical previously read reports can be reused. Expired
repair instructions are excluded from future briefs while historical records and
allowances remain intact. The current run is preserved; 105 affected CPU tests
pass, and actual future-agent use of this new access gate remains to be observed.
Dependency errors also identify the current pinned assignment and missing report
paths explicitly; their replay preserves the draft and workflow state. The agent
still has to inspect and assess those results itself.
The same child subsequently used the diagnostic and read the missing experiment
and research reports. Its fifth dispatch returned an accepted `NEEDS_EVIDENCE`
report reconciling all three dependencies; Qwen then dispatched
`research-49bf442359` to investigate per-substep slip/velocity export for numerical
friction-work closure. This is verified evidence routing, not a physical pass.
The installed native wait matcher now also includes
`chimera-spatial`, with 15 CPU compatibility checks and a preserved rollback.
This removes an omitted-role cause of coordinator wakeups for future CLI processes;
the current process was not restarted, and live future-process timing is unverified.
Passive activity accounting now separates coordinator/child response receipts,
pending counters and deduplicated compaction spans. The live replay covers six
bound sessions and three compactions; 27 combined activity/observation tests pass.
Response spans include waiting and tools. Full-task/reuse costs remain unqualified
until delivery; missing compaction inference usage is explicitly unknown.
Final Step review can now route an implementation correction or additive
qualification correction after tests pass: preserved evidence -> spatial diagnosis
-> independently approved extra tests where needed -> implementation -> fresh
tests -> the same final reviewer. Original acceptance, existing tests and attempt
limits remain fixed. Recovery after interrupted state saving is covered; actual
agent use of this correction path is pending. The combined workflow, recovery,
archival and accounting suite has 145 passes and one host-dependent symlink skip.
The latest research report was corrected by the same child and returned to Step
spatial attempt6, which now carries the assignment-access policy. It proposes a
calculation from saved positions; numerical friction-work closure is still open.
Future retries also retain native web observations after a rejected structured
report, using recorded raw-response hashes and explicit rejected-report labeling.
Historical reports and the current assignment remain unchanged.

The accumulating ontology must preserve each run's exact scientific inputs while
allowing unrelated new records. The workflow now seals historical graph bytes,
checks relevant directional dependencies for current reuse, and searches completed
result descriptors through the existing ontology. Explicit protected inputs and
independent tests retain their byte checks. Publication of a qualified result and
a new request finding and using it remain separate acceptance gates; a private
admission database or a proposed descriptor alone does not establish cumulative
reuse. See the executable workflow record for the checked APIs and limitations.
The bound `matter_setup.py publish BUNDLE` command and native completion guidance
now connect qualified delivery to the existing authored/native graph authority.
They preserve the sealed run and resume one transaction, refusing changed targets
or unqualified sources. CPU fixtures pass; actual qualified publication and a
different construction discovered through it are still required.
The prepared second demonstration request is
`Runtime/zcode-matter-workflow-20261026/reuse-pressure-plate-intent.txt` under the
workspace root: a game pressure plate whose load/release trigger derives from
native deformation. Step must establish its design and operating domain. It is
not started; launch depends on qualified publication of the first result. Reuse
must be demonstrated through actual retained identities and independent Blender
tests, with measured reductions in repeated work.
Its prepared `reuse-pressure-plate-acceptance.json` fixes explicit local-rule,
energy and successful-reuse obligations; `reuse-pressure-plate-entry.json` records
the unexecuted private Z Code CLI entry. No app-session opt-in is implied by it.
The existing matter/DFT records also now survive the authored rebuild: 57 current
objects and 166 relations were preserved exactly in `project_program.json` after
an isolated owner-build check. The live graph and active agent inputs were left
byte-identical; this preservation adds no new scientific qualification.

**Implementation routing update (2026-10-26).** The `chimera-maya` role keeps its
dispatch name and implementation permissions but now uses Qwen IQ4_XS, matching
the lead's provider, with reasoning enabled. Lead and implementer retain separate
conversations. Step's spatial preparation and subsequent independent review stay
in place. `chimera-glm` is an optional read-only second opinion on a concrete
uncertainty; DeepSeek remains optional. Preserve current child/model identities
and work. Z Code caches profiles at worker startup, so reload after current work
finishes to apply the new routing. This change does not restart assignments, reset
or pause the active saved goal, change provider defaults or introduce warm-ups.
Continue sequentially through the existing handoff. Runtime definitions and the
verification record are in `.zcode/agents/` and
`Runtime/local-ai/qwen-implementer-20261026/` under D:/Chimera-Maintenance.

**Spatial understanding before mathematical implementation (2026-10-25).**
`chimera-spatial` is a separate agent using the Step model. For interacting 3D
objects and matter fields, Qwen first supplies it an owned scene/evidence copy,
existing ontology paths, task purpose and unchanged acceptance criteria. It
reconstructs coordinate frames, shapes, connections, boundaries, motion and
deformation; traces actual graph identities/relations; distinguishes observed,
intended and unknown behavior; and returns a grounded account or precise missing
evidence. `NEEDS_EVIDENCE` is a successful reasoning outcome when justified, not
permission to guess or start another speculative implementation. Qwen obtains
that information and returns it before dependent work. Maya then formulates and
implements; the existing `chimera-step37` reviews the actual Blender results,
including whether the earlier spatial interpretation was wrong. Qwen preserves
the reports, predictions, evidence requests and decisions in the existing cycle
record and chooses the next action. One agent at a time; no separate warm-up.
The new agent may write diagnostic scripts/reports in its assigned evidence
area; it does not repair geometry or change production science/graph records.
The existing reviewer and all current assignments remain unchanged. This profile
does not supply missing scene-instance ontology bindings, prove agent reasoning
quality or resume the paused development goal. Its instructions are
`D:/Chimera-Maintenance/.zcode/agents/chimera-spatial.md`.

Only the lead may delegate. Every subagent, including Explore, general-purpose, Maya, Step and researchers, works directly and returns a report; it cannot spawn or resume another agent or launch a workflow that delegates. If more expertise is needed, report the question and evidence to Qwen. Use RespondToCoordinator or a final response for reports. Preserve this rule through compression and resume; do not bypass it through a shell/CLI. Qwen alone chooses the next peer.

**Qwen leads:** first gather enough current source, paths and evidence to frame a
useful assignment. Choose the next Blender outcome, research or implement directly
when useful, select suitable peers and optimize task size, review and process.
Stop gathering once the task and uncertainty are clear; avoid another full audit.

**Maya (Qwen-powered role) usually implements:** use existing owners, deliver the scoped change and
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
For the bound matter workflow, Step's spatial and final review rounds are required.
Other scoped tasks retain proportionate review. Actual failed physical checks
remain failed for that capability. Use focused checks for consequential changes
and broader regression when the change or a failure justifies it.

Preserve goal/progress, the mandatory Blender path, current project and owner,
task purpose, pending/completed reports, decisions, failures and next action
through compression and resume. Retrieve artifacts and resume the same child
where possible. Keep one foreground model task at a time on this host and use
existing GPU resource coordination; this plan adds no context/output limit,
model change, scheduler or requirement to interrupt working agents.

The integrated local-model handoff loads through the actual Agent/SendMessage
request and reuses resident models; do not add separate warm-up commands.
Updated workers distinguish startup from ordinary stream inactivity and retain
native progress watchdogs. Resume the same saved child after an explicit failure.
Client changes take effect for newly started Z Code workers. Runtime fixes and
sequential installed-program test results are recorded in
`D:/Chimera-Maintenance/Runtime/local-ai/integrated-handoff-20261024/RESULTS.md`.
The 2026-10-24 desktop restart and foreground Qwen/Maya/Qwen check passed with
one child, no overlapping inference and all original sessions/goals preserved.
Restored chats now reconcile goal controls with saved status; the development
goal remains paused and displays "Resume goal". App evidence is in
`D:/Chimera-Maintenance/Runtime/local-ai/integrated-handoff-20261024/app-verification-20261024/RESULTS.md`.

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

**First matter-card entry.** Open
`ChimeraStudio/integration/evidence/matter-card/run-02/Al6061 Matter Workshop.blend`
with the existing GPU Materials launcher (`-ProjectFile`; see the linked workflow).
Use **N > Matter > Matter Card - Source to Asset** to create a part, inspect its
source, bake through the native owner, or export it. The adjacent
`Al6061 Matter Asset.blend` imports through **Reusable Construction Assets** with
new instance IDs and six named face groups. Keep the workshop's cache folder for
recorded replay and physical continuation. Original user projects are preserved.

**Two-field entry.** `ChimeraStudio/Start Matter Fields Workshop.cmd` opens the
aluminum/stainless workshop. **N > Matter** now selects either recipe and binds
material-pair contact. The saved **Contact On** and **Contact Off** scenes expose
the native comparison. Reusable steel and paired assets live alongside that project
in `integration/evidence/matter-pair/run-01`.

**Human and AI use one path.** Enable **N > Chimera > Local Z Code Connection**
for external control. The existing `integration/tools/studio_client.py` lists
`sessions`; select the actual intended project/scene, inspect, propose, apply and
poll the same operation. Use the protocol's IDs and recovery semantics. A live
request must not target a guessed session or another construction. Missing/stale
connections are reported, not bypassed by mutating the engine behind Blender.
CPU/unit work and owned headless Blender tests remain available when the window
is closed. Keep UI evidence explicit when the visible path has not been exercised.

**Spatial evidence before geometry tuning.** The existing Blender/native cache
export now provides ontology references, measured mesh/attachment/motion data and
labeled views. Use [SCENE_EVIDENCE.md](../../ChimeraStudio/integration/SCENE_EVIDENCE.md)
for complex contact/deformation debugging, preserving the current assignment and
unchanged acceptance tests. This is an inspection capability, not a new physical
law or a completed haul milestone.

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

**Legacy lane, operator direction 2026-10-23:** the old engine lane
(ChimeraEngine, PythonChimera engine tools, GPU jobs, model services) is a legacy
reference. Do not modify, test or gate it. Every required item below is delivered
through the Blender lane (`ChimeraStudio/integration`) against deliberately pinned
native owners.

### 13.0 Release checklist (finite; maintained by the lead)

Required release work only. An item is DONE solely with linked Blender-path
evidence at current dependencies; stale receipts stay labeled. Optional research
and later expansion never gate the finish line. Update status in place.

**R1. Blender construction loop dependable — IN PROGRESS**
- Two nine-check workshop loops: DONE (§3 receipts).
- Shared human/AI one-path operations incl. transport size refusals: DONE
  (`integration/evidence/local-client/`, `integration/evidence/size-refusals/`).
- Save/reopen a native trial through the shared operations path
  (`save_trial`/`open_trial`): DONE October 24 (`integration` 1d327d5 + fix
  c30b1ae, `integration/evidence/trial-persistence/`) — headless 21/21 plus a
  live-client save→reopen round-trip restoring the workshop's accepted state
  id; panel LABELS/DEFAULTS entries and a draw guard remain owed by
  `operations_ui.py`'s owner (recorded in the receipt).
- Apex-weld reaction display: backend DONE physics-verified
  (`integration` b2da149, `integration/evidence/membrane-forces/`);
  Blender-visible half OPEN behind a user-consented repin plus foreign-lane
  wiring of `gpu_native.py`/`blocks_ui.py`/`operations_ui.py`.

**R2. Rescue cradle / haul load path reusable in Blender — MILESTONE 1 DONE
October 24** (`integration` 143f781, `integration/evidence/cradle-haul/`;
independent stitch-load check 0.0 N residual, counterfactual drops
0.2812/1.0557/0.3475 m, seam asymmetry 41.37 N, offline reopen 0.0 m;
independent review ACCEPT). Authoring-level release/repair only; force-triggered
slip (I09) deferred pending a native-law decision; rope/pad/ground are labeled
surrogates (I06/I07/I08). Remaining R2 later-half: measured silicone, sourced
rope, calibrated terrain pair, demonstrated metal/cloth contact — each needs
data or a native-law decision, none gates R3.

**R3. “Bring Them Home” playable slice — OPEN (§6 gate preserved)**
Investigate a damaged environment → construct/adapt a way through →
protect/recover a companion → return with consequences and reusable knowledge;
readable failure/recovery and at least two viable physical solutions, delivered
through Blender's existing paths.

**R4. Release gates — OPEN (measured at slice completion)**
Installation/startup from a clean state; playable objectives completable;
understandable feedback; save/reload retains identities, sources and accepted
results; interrupted work recovers explicitly; physical references pass for every
claimed behavior; performance measured on target hardware.

**Explicitly optional / later (never gates release):** measured-alloy validation
and mesh-converged bending; powered mechanical companion; preparation transport;
biological fidelity; the water/thermal lane; general learned lateral/compliant
response; broad CA/libuipc/native coupling; arbitrary CAD imports and large-scene
budgets; catalog growth alone; §12.2 techniques 3–14 research options.

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

**Current workflow increment (October 27):** run the executable agent-led matter
workflow through the reusable Z Code dynamic workflow
`.zcode/workflows/matter-construction.dwf.ts`. One run advances one stage
(`spatial → research → implement → test → review → deliver`) of a
`chimera.matter-workflow.v1` bundle; Qwen coordinates and selects the stage model
(Step 3.7 for spatial and independent review, Qwen for the rest), reports are the
persistent checkpoints, `NEEDS_EVIDENCE` escalates to research, the script re-runs
the bundle verifier as an independent gate, and delivery is gated on a PASSED
review. Validation runs on the existing aluminum/stainless/alloy construction in
`Runtime/zcode-matter-workflow-20261027/alloy-zcode-01` (deformation, contact
interaction, complete energy accounting, save/reopen, editable construction);
`alloy-real-01` and all earlier sessions remain preserved and untouched. Actual
Qwen/Step reports, native/Blender tests, complete energy accounting and retained
cross-request reuse must establish completion. The earlier game increments below
retain their evidence and are not a competing assignment for these workflow agents.

**Completed increment (October 23): game matter catalog.** The
[34-entry roster and 29-scenario interaction matrix](GAME_MATTER_CATALOG.md)
are linked to the existing ontology, 29 source routes, reusable Blender assets
and accumulating benchmark registry (§11.21.14). Five initial material roles,
one optional existing alloy, 21 later-game entries and seven optional/reference
entries account for all earlier catalog identities and recipe groups. The audit
checks coverage, graph/source/asset links and evidence freshness; it adds no new
physical qualification. The alloy example remains completed within §11.21.15's
300 K provisional elastic/contact scope. Historical evidence is preserved and
stale receipts stay labeled.

**Following deliverable:** make the rescue cradle/haul load path reusable in
Blender: selected or explicitly authored strap/rope, pad and terrain response,
supported material-pair contact, attachment slip/release, a repair comparison and
saved condition. Use catalog matrix rows I05–I09 and the current native owners.
Select a bounded construction and its physical/error/runtime targets before
expanding the material list. Alloy data/bending improvements and a powered
mechanical companion are subsequent bounded increments; preparation transport,
biological fidelity and the broader water/thermal lane remain separate.

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
