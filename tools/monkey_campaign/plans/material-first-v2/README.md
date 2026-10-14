# Material-first monkey plan — revision 2

Operator-requested 2026-09-27. **95 tasks: all 83 prior IDs retained, plus 12 explicit material foundation gates.** These are requirements to reconcile, not 95 claims of missing implementation.

The architecture is reusable matter at selected fidelity. The first visible product is a controllable monkey walking through woods; climbing and full release follow. Additional materials remain extensions of the same interfaces, not prerequisites to the first product.

## Current adoption boundary

This is the prepared replacement plan, not a hot update to active worker criteria. The old canonical catalog, scope pin, claims, DONE records and receipts are untouched. No new physical qualification is asserted. The new list is machine-readable in [monkey_completion_map.json](monkey_completion_map.json); every old task has a [crosswalk](crosswalk.json). The [validation receipt](validation.json) checks structure, not physics.

## Physical interpretation

- **material_unit:** Bounded region or declared shell with stable identity, rest/current geometry, mass/inertia, material orientation/history, selected pressure/deformation laws and explicit interfaces.
- **triangles:** Surface elements carry area, orientation and interface ownership. Subdivision alone does not identify anatomy, assign bulk mass, or create new material.
- **pressure:** For a uniform pressure difference, F_i=(p_inside-p_outside)*A_i*n_i. Uniform compartment pressure is a selected equilibrated approximation; resolve spatial pressure when required by the observable and time scale. Define closure, exterior pressure, work and volume ownership.
- **topology:** Containment, spatial neighborhood, material adjacency, contact and bond are distinct relations. No containment edge silently produces a bond.
- **bones:** Separate physical objects. Tissue/capsule/contact can constrain them; any reduced constraint must identify the represented material, validity envelope and removal behavior. No unaccounted skeleton hinge survives tissue removal.
- **activation:** Pressure-controlled active membrane with explicit volume/work source and directional reinforcement is an engineering material model. Compare its measured response with intended muscle behavior; do not call it biological equivalence by definition.
- **gpu:** Reuse existing resident state and hierarchy infrastructure. Field, pressure/reduction, local constitutive, contact/constraint and integration passes have explicit ordering and single state ownership; CPU handles bounded intent/configuration/telemetry.
- **barnes_hut:** Only law-specific aggregatable far-field interactions use Barnes-Hut approximation with measured error. Local contact, shear history, bonds and pressure closure use appropriate local/topological operations; do not reinterpret every quantity as gravity.
- **graph:** Graph stores material types, geometry/region identity, parameter provenance and uncertainty, model versions, interfaces, dependencies, evidence and validity envelopes. Graphify is a search/visualization projection, not a solver or a source of missing physical laws.
- **extensibility:** Additional materials and phenomena can add parameterized response laws and state to the shared interfaces. No claim that density alone represents all reality or that a universal physical simulator is already implemented.
- **fidelity:** Render mesh resolution, mechanical discretization and control rate are independent. Changes preserve declared mass/inertia, boundary response, attachments and state within tested error; use only the detail required by the observable.
- **reuse:** Inventory current code/receipts first. Existing components close a gate only through scoped reproducible evidence; do not rebuild passed capabilities or substitute cosmetic animation.

## Visible progression

1. Reproduce the exact prototype the operator has seen (P02), retaining a runnable baseline.
2. Show a pressure-loaded membrane and passive/directional material response (M03/M04).
3. Show independent bones constrained by visible/removable material, with active pressure driving the assembly (M09/M10).
4. Reuse the laws in another shape and in the actual monkey limb (M11/M12).
5. Control the same physical monkey in the clearing, then walk between trees on the declared terrain (W10/F06).
6. Add grasp, climb, hold, descend and release to that build (K08).

Each applicable gate includes numerical/reference evidence plus source-bound video or a recorded frame sequence with tagged surfaces, pressure/force/contact overlays, orthogonal and oblique views, camera angle, target, distance, projection, clipping, viewport and exact simulation interval. A matched clean view uses the same physical state. Still images cannot prove motion. Tolerances and the applicable views are frozen before running; no invented universal precision threshold.

## Immediate work order

First locate the existing implementations and reproduce the prototype; do not rebuild existing material kernels from scratch. Then dispatch distinct owned work for M01/M02, the pressure and passive-material experiments, and the contact/interface path as dependencies permit. GPU work follows bounded resource admission. Review once per exact candidate unless a concrete finding warrants more. One integrator maintains the runnable prototype throughout. Independent workers can proceed in parallel; a visual checkpoint is not a dependency on itself.

The initial deliverable is a runnable baseline and the first missing material interaction identified by an executable failing probe, followed by a visible correction. It is not a new scheduler, material encyclopedia or another collection of successful prose audits.

## Every task and its revised acceptance

Dependencies below are acceptance prerequisites. Existing reference fixtures may be used earlier, explicitly labeled; fixtures do not qualify the real monkey.

| ID | Work | Dependencies |
|---|---|---|
| P01 | Freeze the playable-monkey completion contract | — |
| F01 | Author the finite clearing and its spatial units | P01 |
| P02 | Pin the active monkey and scene lineage | P01 |
| P03 | Reconcile current work and receipts into existing ledger | P01 |
| P06 | Choose release acceptance limits | P01 |
| X01 | Define the small game's repeatable objective | P01 |
| X02 | Implement start, pause and session restart flow | P01 |
| A01 | Resolve ulna volar-side orientation evidence | P02 |
| A04 | Determine hand assembly identity and palm orientation | P02 |
| B01 | Close independent exporter review and multi-cell coupon | P03 |
| M01 | Define reusable material state and distinct relation types | P02, P03 |
| P04 | Apply fleet resource and gaming contract | P03 |
| P05 | Retain milestone recovery and artifact identity | P03 |
| S01 | Audit distribution provenance and dependencies | P02 |
| U01 | Map gameplay input to the existing command seam | P01, P03 |
| U02 | Deliver a usable follow camera | P01, P03 |
| W01 | Close tick-3 discrete forelimb parity defect | P02, P03 |
| W02 | Close transcendental parity defects | P02, P03 |
| A02 | Validate U-STR and proposed radius consequence | A01 |
| A05 | Acquire or author evidenced hand/digit structure | A04 |
| B02 | Complete supported static exporter coverage | B01 |
| B04 | Author the real assembly frame forest explicitly | P02, M01 |
| M02 | Compile imported triangles into explicit material regions | M01 |
| U03 | Handle focus loss and input release | U01 |
| U04 | Expose supported input settings | U01 |
| U05 | Define and implement climb intent seam | U01 |
| W03 | Integrate frozen parity and walk anchors | W01, W02 |
| A03 | Approve and implement supported ulna correspondence | A02 |
| B03 | Produce real validated material-volume input | P02, M02 |
| M03 | Verify pressure on a closed triangulated membrane | M02 |
| M04 | Verify passive resistance and directional material response | M02 |
| M05 | Make contact, bond and release explicit physical interfaces | M03, M04 |
| M06 | Verify local triangle contact and finite sliding | M02, M04 |
| A06 | Resolve attachment and waypoint ownership | A03, A05, M05 |
| B05 | Provide real mechanical port requirements | B04, M05 |
| F02 | Build matching terrain rendering and collision | F01, M06 |
| F03 | Implement one rigid climbable trunk asset | F01, M06 |
| M07 | Couple pressure, material and contact through one physical step | M03, M04, M05, M06 |
| A07 | Resolve failed/outside attachment placements lawfully | A06 |
| B06 | Re-run real assembly readiness without substitutions | B03, B04, B05, B02 |
| F04 | Verify ground and trunk contact geometry | F02, F03, P02, P06 |
| M08 | Run the coupled material passes on resident GPU state | M07, P04 |
| F07 | Place forest obstacles and scene boundaries | F04 |
| M09 | Demonstrate loose bones assembled by physical connective matter | M05, M06, M08 |
| M10 | Demonstrate active pressurized material with directional reinforcement | M03, M04, M05, M08 |
| A08 | Define evidenced muscle/tendon parameter envelope | A06, M10 |
| F08 | Verify repeatable forest loading | F07 |
| M11 | Reuse the same material rules in a loaded monkey limb | M09, M10, B03, B04, B05 |
| A09 | Issue the grasp anatomy input package | A07, A08, M09 |
| B07 | Decide and qualify adoption by walking/climbing runtime | B06, M11 |
| M12 | Qualify mechanical detail and render detail independently | M11 |
| G02 | Qualify finite-area anatomical attachments | A09, M05 |
| G03 | Evaluate tendon lengths and moment arms | A09 |
| W04 | Bind training manifest and compatibility certificate | W03, M11, B07 |
| G01 | Derive support and grip feasibility | A09, F03, W04 |
| W05 | Execute the walking run qualified for the selected material dynamics | W04, P04 |
| G04 | Implement and verify physical grip contact | G01, G02, G03, F04, M06, M11 |
| W06 | Evaluate trained walking outcomes | W05 |
| F05 | Specify the terrain range for walking | F02, W06 |
| G05 | Implement contact/support observations | G04 |
| G07 | Measure unsupported release and falls | G04 |
| W07 | Load accepted walking policy in native runtime | W06, M08 |
| G06 | Prove a supported limb-transfer sequence | G04, G05 |
| W08 | Verify commanded start, stop, speed, and heading | W07, U01, P06 |
| W09 | Implement explicit out-of-envelope behavior | W07 |
| G08 | Qualify climbing dynamics and numerical budget | G06, G07 |
| W10 | Accept walking in the actual game scene | W08, W09, F04, U02, M12, U03, X02 |
| F06 | Implement and qualify terrain-aware walking | F05, W07, F04, W10 |
| K01 | Freeze the climbing skill specification | G08, U05 |
| U07 | Measure controls during actual play | W10, U03, U04, P06 |
| X04 | Render readable animal and environment state | W10, F08, M12 |
| X05 | Add grounded interaction audio | G04, W10 |
| K02 | Build reproducible climbing reset scenarios | K01 |
| K03 | Train climbing under approved reservations | K02, P04, W07 |
| K04 | Evaluate climb, hold and descend separately | K03 |
| K05 | Integrate the accepted climbing policy | K04 |
| K06 | Implement walk/climb skill arbitration | K05, W07, U05 |
| K07 | Verify boundary and failure behavior | K06 |
| R01 | Extend save/restore to the complete playable state | K06 |
| U06 | Add readable control and state feedback | U05, G05, K06 |
| K08 | Accept the complete ground-tree-ground loop | K07, F06, U07 |
| R02 | Implement player settings and save lifecycle | R01, U04, X02 |
| X03 | Implement the chosen fall/recovery experience | W09, X02, K07 |
| R03 | Profile representative ground/climb scenes | K08, P06, P05, M08, M12 |
| X06 | Wire physics teaching/inspection to live values | X01, K08 |
| R04 | Fix measured runtime bottlenecks | R03 |
| X07 | Run the stranger playthrough and human acceptance | K08, X01, X02, X03, X04, U06, X05, X06 |
| R05 | Verify long sessions and resource teardown | R04, X02 |
| R06 | Exercise input/device/failure recovery | R02, R05 |
| R07 | Bind full release compatibility evidence | R06, X04, X05, X06 |
| S02 | Build a self-contained Windows package | R07, S01, X02 |
| S03 | Verify install, launch, save and clean exit | S02 |
| S04 | Complete player help and failure diagnostics | S02, X07 |
| S05 | Accept playable-monkey feature completion | S03, S04, X05, X06, R07 |
| S06 | Prepare public/demo release assets | S05 |

### P01 — Freeze the playable-monkey completion contract

One monkey, ground movement, one climbable trunk, return to ground, explicit success/failure behavior; broader features excluded. Material-first addition: Reusable matter is the architecture; walking through woods is the first product milestone, followed by the existing climb/return goal. Additional materials remain extensible, not universal-physics prerequisites.

### P02 — Pin the active monkey and scene lineage

CT monkey, source musculoskeletal model, older forearm/paddle assets, training body, and runtime body are related explicitly or kept separate. Material-first addition: Recover and reproduce the operator-observed prototype before replacing any subsystem; pin executable/build recipe/source/body/scene/policy and capture actual behavior. A missing source or behavior is an explicit unresolved gap.

### P03 — Reconcile current work and receipts into existing ledger

Every active task has one owner, source revision, scoped verdict, and receipt; prior completed work is reused. Material-first addition: Crosswalk old receipts to revised requirements without promoting old DONE to new acceptance. Search the existing material graph and code before adding work.

### P04 — Apply fleet resource and gaming contract

Every launched job uses existing ownership/broker rules; admitted training may interrupt gaming and local inference through a verified supervisor handoff, while already-running protected training retains ownership until confirmed release

### P05 — Retain milestone recovery and artifact identity

Recoverable commits, run manifests, training checkpoints, raw/blob/canonical hash labels, and retry rules exist

### P06 — Choose release acceptance limits

Supported hardware, controls, terrain/trunk envelope, session duration, latency, frame-time and stability limits are frozen before acceptance trials. Material-first addition: Freeze numerical/convergence/energy/contact/performance limits and camera-visible player outcomes before experiments. Report first walking-through-woods acceptance separately from later full climbing completion.

### W01 — Close tick-3 discrete forelimb parity defect

Frozen entry-state and event traces satisfy the existing CPU/GPU acceptance bar

### W02 — Close transcendental parity defects

Reference-math equivalence is demonstrated at the frozen sites without tolerance relaxation

### W03 — Integrate frozen parity and walk anchors

Freefall/stand/C1/C2 and scene f6844ee, stdout 8c537cdb, 302 ticks, 30.970714 J reproduce on the training revision. Material-first addition: Old gait/anchor evidence is baseline evidence only until it is rerun against the selected physical representation; no identity substitution.

### W04 — Bind training manifest and compatibility certificate

Exact dynamics, observations/actions, model revision, seeds and runbook identity are frozen and checked. Material-first addition: Bind the accepted material assembly, active law, observation/action schema and physics tick to both training and runtime. An old policy is reusable only if this contract still matches.

### W05 — Execute the walking run qualified for the selected material dynamics

All three prescribed seeds execute under the frozen approximately 1M-decision runbook with failures retained. Material-first addition: The old runbook is unchanged only when W04 demonstrates unchanged dynamics and interfaces. Otherwise create and freeze a revised run with retained baseline, bounded resources and explicit controller changes; no incompatible run by inertia.

### W06 — Evaluate trained walking outcomes

Frozen walking success/failure metrics reported per seed without cherry-picking or additional tuned runs

### W07 — Load accepted walking policy in native runtime

Runtime consumes the certified observation/action contract and drives physical actuators. Material-first addition: The controller supplies bounded activation/pressure/effort to the accepted material system; native solved matter is the only physical pose authority.

### W08 — Verify commanded start, stop, speed, and heading

Frozen command sequence satisfies tracking and physical-stability limits

### W09 — Implement explicit out-of-envelope behavior

Unsupported states and falls have a declared controller response; no concealed resets or forces

### W10 — Accept walking in the actual game scene

Player can walk, turn and stop in the scene on a supported surface; numerical and visual receipts match. Material-first addition: Show the existing monkey asset walking under player commands in one pinned forest clearing build, with clean and diagnostic views; no cosmetic skin over an unrelated qualified body.

### U01 — Map gameplay input to the existing command seam

Input emits bounded speed/heading commands at the existing 20 Hz boundary, without state teleportation

### U02 — Deliver a usable follow camera

Player can see motion on ground and at trunk; camera avoids tested obstruction cases and never moves the animal

### U03 — Handle focus loss and input release

Alt-tab, disconnect and key release clear or age commands under a declared policy; no stuck movement

### U04 — Expose supported input settings

Sensitivity, inversion and bindings needed for the selected controls work and persist

### U05 — Define and implement climb intent seam

One explicit climb/let-go intent reaches the skill selector with versioned semantics; frozen walk contract remains unchanged

### U06 — Add readable control and state feedback

Prompts distinguish available climb, unavailable support, holding, falling and recovery without claiming nonexistent capabilities

### U07 — Measure controls during actual play

End-to-end input response and camera behavior meet P06 limits under repeatable scenes

### F01 — Author the finite clearing and its spatial units

Deterministic terrain/tree recipe, explicit extent and coordinate convention, safe spawn and visible boundary

### F02 — Build matching terrain rendering and collision

Rendered ground and physical query surfaces agree within frozen geometric tolerance. Material-first addition: Terrain contact uses the shared material/contact path; surface shape, material identity and collision geometry stay tied to the rendered asset.

### F03 — Implement one rigid climbable trunk asset

Trunk geometry, surface IDs, material provenance and collision representation are explicit. Material-first addition: The rigid trunk is an explicitly reduced material object using the same contact interfaces. Full wood growth/fracture or all tree rings are not prerequisites.

### F04 — Verify ground and trunk contact geometry

No unacceptable tunnelling, ghost support, interpenetration or visual/collision disagreement in frozen cases

### F05 — Specify the terrain range for walking

Slope, obstacle size and surface-friction envelope is declared from evidence

### F06 — Implement and qualify terrain-aware walking

Player walks the declared uneven-ground cases with certified runtime/training agreement. Material-first addition: Qualify player-controlled walking between trees and on the declared uneven-ground envelope in the same build as W10, with actual contacts.

### F07 — Place forest obstacles and scene boundaries

The clearing offers traversable routes; no invisible walls masquerade as physical obstacles

### F08 — Verify repeatable forest loading

Scene seed/configuration reproduces assets, collision and initial state with clear failures for missing assets

### A01 — Resolve ulna volar-side orientation evidence

Independent anatomical evidence determines roll sign or records ambiguity

### A02 — Validate U-STR and proposed radius consequence

Radioulnar definition, independent evidence, B4 result and before/after radius mapping are presented

### A03 — Approve and implement supported ulna correspondence

Architect approves mapping/supersession, historical radius preserved, new transforms and regressions qualified

### A04 — Determine hand assembly identity and palm orientation

Source and target assembly correspondence is evidenced, including palm sign and geometry coverage

### A05 — Acquire or author evidenced hand/digit structure

The modeled grasp has sufficient explicit bodies, joints and geometry; sources and adaptations approved

### A06 — Resolve attachment and waypoint ownership

Every grasp-relevant endpoint and waypoint has an explicit approved body and role. Material-first addition: Represent tissue-to-bone attachments explicitly; ontology containment and conventional rig parentage never silently create a mechanical bond.

### A07 — Resolve failed/outside attachment placements lawfully

Attachment validity is supported or explicitly unresolved; any new fitting experiment is separately authorized

### A08 — Define evidenced muscle/tendon parameter envelope

Strength, force-length/velocity, compliance, limits and applicability are defined for the selected animal. Material-first addition: Separate source-backed biological parameters from chosen engineering active-pressure material parameters. No inferred density/stiffness/activation law from geometry alone.

### A09 — Issue the grasp anatomy input package

One versioned package carries supported mappings, parameters, provenance and explicit gaps. Material-first addition: Package the skeletal/tissue/interface graph and each explicit reduction; removal of represented tissue must remove its mechanical connection.

### G01 — Derive support and grip feasibility

Required force/moment support lies within reachable contacts and actuator bounds for the declared trunk

### G02 — Qualify finite-area anatomical attachments

Actual patch geometry, stiffness and rotational resistance meet declared physical requirements. Material-first addition: Finite-area attachment forces and moments enter both connected material states; physical bond/removal semantics match the limb experiment.

### G03 — Evaluate tendon lengths and moment arms

Relevant pose-range outputs are finite and independently checked; unresolved bodies cannot appear as zero arms

### G04 — Implement and verify physical grip contact

Attachment, friction, reaction loads and release operate through the physical solver without invisible anchors. Material-first addition: Use the same local contact and material interface implementation as ground locomotion; grasp cannot add a hidden sticky constraint.

### G05 — Implement contact/support observations

Controller receives only declared measurable contact/pose signals with explicit timing

### G06 — Prove a supported limb-transfer sequence

At least one reachable transfer retains admissible support throughout its tested envelope

### G07 — Measure unsupported release and falls

Loss/release of support removes its forces and yields accounted motion and energy

### G08 — Qualify climbing dynamics and numerical budget

Accepted mechanics pass CPU/GPU and runtime identity gates relevant to climbing

### K01 — Freeze the climbing skill specification

Observations, actions, reward, termination, success metrics, seeds, envelope and falsifiers approved before training

### K02 — Build reproducible climbing reset scenarios

Initial states are valid and attributable; setup/reset never becomes a hidden in-episode assist

### K03 — Train climbing under approved reservations

Approved runs finish or fail with checkpoints and unchanged acceptance criteria. Material-first addition: Reuse admitted walking/material dynamics and train only the distinct climbing behavior; all body, material, contact and control identities must match.

### K04 — Evaluate climb, hold and descend separately

Each claimed behavior meets frozen metrics; failures and unsupported cases are visible

### K05 — Integrate the accepted climbing policy

Native policy consumes certified dynamics and commands only available actuators

### K06 — Implement walk/climb skill arbitration

Transition preconditions, cancellation, ownership and command handling are explicit

### K07 — Verify boundary and failure behavior

Out-of-reach, rejected grip, excessive load and lost contact terminate/transition according to the specification

### K08 — Accept the complete ground-tree-ground loop

Player approaches, attaches, ascends, holds, descends, releases and resumes all-fours walking in one session

### X01 — Define the small game's repeatable objective

A finite purpose/lesson/free-play completion definition is selected without inventing a campaign

### X02 — Implement start, pause and session restart flow

Player reaches play and can pause/restart/exit without developer commands; reset is an explicit user action

### X03 — Implement the chosen fall/recovery experience

The player can continue after failure by the approved recovery action or visible restart

### X04 — Render readable animal and environment state

Connected animal, contact and climbing states are readable in actual captures with no second locomotion pose. Material-first addition: Deform/render from the actual material state and verified mapping. Debug layers can be invisible in play but cannot be missing from verification.

### X05 — Add grounded interaction audio

Contact/release/impact cues follow actual events, have volume controls and honest material scope

### X06 — Wire physics teaching/inspection to live values

Selected lesson or inspector uses runtime quantities with units and explains declared limitations. Material-first addition: Inspection exposes live membrane pressure, material directions, load paths and contacts with selectable IDs and camera bookmarks; the graph view links to runtime identity rather than substituting for it.

### X07 — Run the stranger playthrough and human acceptance

A player can discover controls, complete the loop and understand failure without operator coaching

### R01 — Extend save/restore to the complete playable state

Pose, velocity, policy/actuator/contact state, scene, RNG and clocks resume under the existing continuation contract. Material-first addition: Include required pressure/volume state, constitutive history, bond topology, activation/energy and solver continuity in the save contract; restoring visible pose alone is insufficient.

### R02 — Implement player settings and save lifecycle

Save selection/version refusal and interrupted-write behavior are explicit; settings persist

### R03 — Profile representative ground/climb scenes

Frame-time distribution, simulation-step time, memory, VRAM and stalls measured in reserved windows. Material-first addition: Measure the coupled GPU passes, contact density, active material count, mechanical/render resolution and memory footprint; GPU residency is not proof of real-time performance.

### R04 — Fix measured runtime bottlenecks

Target acceptance budgets met with unchanged physical/behavioral gates

### R05 — Verify long sessions and resource teardown

Repeated scene/restart/save cycles stay inside limits and all owned children/resources close

### R06 — Exercise input/device/failure recovery

Focus changes and claimed device-loss/suspend behaviors fail or recover clearly without corrupting saves

### R07 — Bind full release compatibility evidence

Code/data/policy/configuration identity matches the accepted complete game and independent receipts

### S01 — Audit distribution provenance and dependencies

Every shipped asset/model/library has a recorded source and applicable distribution terms

### S02 — Build a self-contained Windows package

Clean machine/user can launch without repo paths, development Python or operator-installed tools beyond declared dependencies

### S03 — Verify install, launch, save and clean exit

Package passes the declared supported Windows/hardware smoke and lifecycle cases

### S04 — Complete player help and failure diagnostics

Controls, supported limits, crash/report path and recoverable errors are understandable

### S05 — Accept playable-monkey feature completion

All selected core/product behaviors pass; remaining issues are triaged explicitly; operator accepts actual play

### S06 — Prepare public/demo release assets

Approved build, concise controls, captures and release notes are packaged; publication follows operator authorization

### B01 — Close independent exporter review and multi-cell coupon

Actual independent review targets 1af0bbde; U1 has frozen analytic evidence; hash claims remain distinct

### B02 — Complete supported static exporter coverage

Authorized scale/transform/status/numerical tests and static diagnostics ship with distinct evidence classes

### B03 — Produce real validated material-volume input

Actual geometry, material ownership and density source support a complete input for the selected body. Material-first addition: Author only the matter required at selected fidelity, with mass/volume ownership and density provenance; static meshes do not implicitly provide interiors.

### B04 — Author the real assembly frame forest explicitly

pelvis/thorax/ulna roots and transforms are authored with evidence; no guessed alignment. Material-first addition: Containment/frame hierarchy is separate from mechanical connection topology; disconnected bone bodies remain explicit.

### B05 — Provide real mechanical port requirements

Actual port patch/stiffness/couple/weight/frame inputs qualify or remain blocked. Material-first addition: Use material-law/interface definitions with declared stiffness, pressure limits and attachment area at chosen detail; distinguish engineering assumptions from measured anatomy.

### B06 — Re-run real assembly readiness without substitutions

All mass/ownership/frame/port requirements evaluated, with remaining gaps explicit

### B07 — Decide and qualify adoption by walking/climbing runtime

Architect names why this assembly replaces the current body, then requalifies affected dynamics/policies before use. Material-first addition: Adopt the material assembly only after actual limb load transmission and a compatible runtime/training contract are evidenced; static export is not runtime qualification.

### M01 — Define reusable material state and distinct relation types

One versioned schema distinguishes regions/shells, rest/current geometry, mass, material direction/history, pressure/deformation law, contact and bond. A known object displays its actual regions and graph relations with stable IDs; no mass double-counting or containment-as-bond.

**Fails if:** Changing containment creates a force, or an undefined parameter is silently inferred from a material name.

**Visible result:** Select a region and see geometry, state owner and actual connections.

### M02 — Compile imported triangles into explicit material regions

Import the pinned monkey mesh and a simple independent shape; check units, orientation, closure for volume regions, shell thickness where used, intersections and region ownership. Separate surface subdivision from semantic material assignment; report absent internal anatomy. Preserve visual mesh and physical mesh mapping.

**Fails if:** An open surface is treated as sealed, overlapping matter is counted twice, or subdivision invents tissue.

**Visible result:** Toggle imported surface, internal regions and mechanical mesh without changing physical state.

### M03 — Verify pressure on a closed triangulated membrane

Demonstrate pressure difference times area times outward normal, volume closure and pressure-volume work in a closed membrane. Check zero net force/torque from uniform internal pressure, external loading, and refinement consistency against independently derived references. Expose pressure-source power and limits.

**Fails if:** Retriangulation changes net loading, internal uniform pressure propels the free body, or inward loading appears without a declared pressure/tension source.

**Visible result:** Inflate/deflate a membrane with area-scaled force arrows and pressure/volume/work traces.

### M04 — Verify passive resistance and directional material response

Implement/reconcile only the rigid, compliant and fiber-reinforced responses needed by the monkey. Declare constitutive equations, parameters, source or synthetic status, rest state, damping and valid strain range. Independent load-extension, relaxation and rotated-fiber experiments meet preregistered limits.

**Fails if:** Density substitutes for stiffness, a rotated fiber has no intended effect, or passive material creates unexplained energy.

**Visible result:** Same shape with different material profiles compresses, stretches or resists directionally.

### M05 — Make contact, bond and release explicit physical interfaces

Two bodies exchange pressure/contact and bonded tension/shear through identified interfaces. Bond removal removes its restoring forces and permits separation except for remaining contact. Shared faces and mass are counted once; transfer includes equal/opposite loads and moments.

**Fails if:** A hidden hinge remains after all connecting material is removed, or a spatial neighbor is automatically bonded.

**Visible result:** Show two objects held by a visible material connection, then visibly separate them after release.

### M06 — Verify local triangle contact and finite sliding

Candidate search feeds actual local surface contact, friction and declared thin-feature/high-speed treatment. Native tests cover resting load, oblique contact, sliding and crossing trajectories; compare against exhaustive contact candidates on small fixtures.

**Fails if:** Hierarchy pruning misses contact, render-only triangles support weight, or two-sided loads violate the declared balance.

**Visible result:** Tagged surfaces collide and slide with matching contact points and rendered geometry.

### M07 — Couple pressure, material and contact through one physical step

One state owner integrates simultaneous pressure/material/contact loads with declared ordering, time step and iterative/substep convergence. Record external work, passive energy and boundary reactions; test timestep refinement and disconnected-component independence.

**Fails if:** Separate passes overwrite motion, expose mixed-tick state, or report stability only at one unexamined timestep.

**Visible result:** A membrane pressing on a loose object moves both through the same solved interaction.

### M08 — Run the coupled material passes on resident GPU state

Reconcile the existing GPU/DSL/hierarchy path. GPU state stays resident during steady-state stepping; CPU supplies bounded commands and asynchronous diagnostics. Validate GPU/direct-reference agreement and work/impulse budgets; profile actual step/frame/VRAM costs. Any Barnes-Hut pass has its own eligible law, error criterion and near-field reference test.

**Fails if:** A local bond/contact is replaced by an unchecked distant aggregate, or claimed GPU dynamics require a full CPU state roundtrip each tick.

**Visible result:** Render the GPU-solved material experiment with timing and residency evidence.

### M09 — Demonstrate loose bones assembled by physical connective matter

Two independent bone shapes fall separately, are constrained by authored ligament/capsule/contact material, and become independent again when all connecting material is removed. Any reduced constraints derive from those connections and vanish with them; no free hidden anatomical hinge.

**Fails if:** Removing tissue leaves an unexplained skeletal constraint or joint-axis pose writer.

**Visible result:** An assembled limb segment visibly becomes a pile of independent pieces when connections are removed.

### M10 — Demonstrate active pressurized material with directional reinforcement

A pressure-controlled membrane with authored directional resistance performs bounded work through actual attachments. Measure force-displacement/work against independent expectations, blocked-load reaction, pressure limits and power-off behavior. Classify it as an engineering actuator unless biological equivalence is independently evidenced.

**Fails if:** Activation writes body poses, contraction is claimed from isotropic inflation alone, or work has no source.

**Visible result:** One pressure-driven material bends or shortens as designed and lifts a measured load through its surface attachments.

### M11 — Reuse the same material rules in a loaded monkey limb

Demonstrate the same law implementation on two distinct shapes without shape-specific motion code, then on the selected monkey limb. Reconcile real mass/frames/attachments; show tissue-to-bone-to-foot-to-ground load transmission, activation-off and connection-removal controls.

**Fails if:** A new shape needs prescribed animation or limb motion is disconnected from ground reaction.

**Visible result:** The actual monkey limb supports load and pushes against the ground; a second shape reuses the same laws.

### M12 — Qualify mechanical detail and render detail independently

Compare at least two mechanical resolutions while preserving declared mass/inertia, interfaces, force response and control meaning within frozen tolerances; render mapping stays attached under large motion. Select the least costly qualified detail for the monkey and record frame-time/VRAM limits.

**Fails if:** Triangle refinement changes material strength/mass without declaration or leaves visible vertices behind.

**Visible result:** Switch diagnostic mesh detail while preserving the visible object and measured physical behavior.

## Queue migration procedure

The Captain authorized the architectural revision; this procedure supplies the remaining implementation steps for safe live adoption. It is not a request to re-approve that decision.

1. Snapshot and preserve the current catalog, externally pinned scope, instruction bundle and registry. Inventory each existing card, candidate and receipt against the crosswalk.
2. Introduce versioned qualification identities. Preserve old cards/PRs at their old criteria. Changed tasks receive a successor qualification with the new scope/criteria; unchanged work can carry forward only after source and dependency freshness review. Do not silently clear old DONE or make a new task pass by ID reuse.
3. Update ontology queue/catalog consumers, cached dependency closures and instruction pins together. Include acknowledgment compatibility for old sessions. Verify from a copied registry before deployment.
4. Require migration tests: old-DONE cannot unlock a strengthened task; changed material dynamics invalidate stale policy compatibility; a worker with the old bundle checkpoints; unchanged qualified evidence can be explicitly carried forward; rollback restores old routing and retains new artifacts.
5. Admit the reviewed revision through the existing serial authority, update the installed lead instructions last, and notify the Sergeant through the mailbox with the exact new digest. Start with prototype recovery and uncovered foundation tests.
6. For a provisioned creature-graph controller, apply through its legitimate versioned admission path; do not mistake the repository proposal or Graphify view for a database update. No controller session was provisioned to this task.

Until those steps execute, this list is available for planning and scoped proposal work; the existing live queue remains on its original sealed catalog. This change does not authorize workers to bypass claims or reinterpret active card criteria.

## Source and verification limits

The existing local graph already specifies material state, layered anatomy and GPU field/local passes. Relevant exact records are preserved in [inspected_graph_contracts.json](inspected_graph_contracts.json), with the inspected source-file hash; their status is specification, not experimental qualification. The graph is not present in this master checkout, so the extract prevents a broken remote reference. No graph/controller authority is imported merely by copying these records.

Structural verification uses the existing campaign catalog and ontology projector. The original 83-task catalog and ontology definition are unchanged. The proposed digest is in [fingerprints.json](fingerprints.json); it is change detection, not a secret authorization token.
