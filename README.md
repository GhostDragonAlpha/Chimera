# Chimera

A physics-teaching engine and creature game built from a versioned scientific graph.

**Start here. This is the only onboarding file an operator needs to give an agent.**
The selected graph revision holds project requirements, concepts, work, dependencies,
sources, and evidence. This README is its bootstrap and command reference.

## Fresh-session continuation

In the verified current checkout, read the maintained onboarding assignment from
its graph before dispatching work:

```powershell
python -B -m tools.creature_graph.project_spec --check
python -B -m tools.creature_graph.project_spec --show doc.handoff.zcode
```

On this Windows host, the examples were checked with
`E:\PythonChimera\.venv-hy3d\Scripts\python.exe`. Use that executable in place
of `python` if the default interpreter lacks the project's dependencies.
PowerShell launchers also accept `-Python` with this path. The coupled reference
runs offline from the pinned data already in the repository.

The last development worktree was
`E:\ChimeraWork\codex-graph-workflow-20260916`; verify it using the checks below.
The project home's separate dirty checkout may be older than GitHub master.
Do not switch or reset that checkout to obtain the latest work.
The graph handoff covers Z Code/GLM, resumable subagents, serial integration,
publication, worked examples and exact remaining tasks.

## 1. Confirm the checkout

The project home is `E:\PythonChimera`. Work may run in an assigned isolated
worktree under `E:\ChimeraWork`. `E:\Chimera` is an older, different project.

Run these commands in your assigned checkout before editing:

```powershell
git rev-parse --show-toplevel
git rev-parse --git-common-dir
git branch --show-current
git rev-parse HEAD
git status --short
```

Confirm the common repository is the PythonChimera repository. Preserve existing
dirty work. Use the assigned worktree, branch, scope, and build directory; never
reset or clean another lane. Record the checkout and revision in your work result.

## 2. Read the graph

From the checkout root, with Python 3.11 or later:

```powershell
python -B -m tools.creature_graph.project_spec
python -B -m tools.creature_graph.project_spec --check
python -B -m tools.creature_graph.project_spec --show req.documentation_admission
python -B -m tools.creature_graph.project_spec --show req.agent_operation
python -B -m tools.creature_graph.project_spec --show req.publication_workflow
python -B -m tools.creature_graph.project_spec --show req.engine_game_release
python -B -m tools.creature_graph.project_spec --show req.current_product_focus
python -B -m tools.creature_graph.project_spec --show req.creature_assembly
python -B -m tools.creature_graph.project_spec --show req.macaque_rebuild
python -B -m tools.creature_graph.project_spec --show doc.handoff.zcode
python -B -m tools.creature_graph.project_spec --show doc.workflow.shared_body_example
python -B -m tools.creature_graph.project_spec --show doc.workflow.macaque_assembly
python -B -m tools.creature_graph.project_spec --show req.earth_environment
python -B -m tools.creature_graph.project_spec --show doc.workflow.earth_patch
python -B -m tools.creature_graph.project_spec --show doc.workflow.force_arm
python -B -m tools.creature_graph.project_spec --show doc.workflow.coupled_arm
python -B -m tools.creature_graph.project_spec --show doc.workflow.coupled_native
python -B -m tools.creature_graph.project_spec --show req.layered_anatomy
python -B -m tools.creature_graph.project_spec --show req.embodied_senses
python -B -m tools.creature_graph.project_spec --show doc.creature_binding_observation
python -B -m tools.creature_graph.project_spec --show req.encapsulation_inventory
```

These read-only commands print the selected store and graph hash. The default
repository snapshot is `tools/creature_graph/data/creature_graph.json`.
Use `--store PATH` to inspect another snapshot and `--json` for machine output.

Find the concept or work you need:

```powershell
python -B -m tools.creature_graph.project_spec --concepts
python -B -m tools.creature_graph.project_spec --next
python -B -m tools.creature_graph.project_spec --search energy
python -B -m tools.creature_graph.project_spec --show concept.energy
python -B -m tools.creature_graph.project_spec --show req.material_catalog
python -B -m tools.creature_graph.project_spec --show concept.reduced_cell_state
python -B -m tools.creature_graph.project_spec --show req.matter_variables_lod
python -B -m tools.creature_graph.project_spec --show req.element_identity_spine
python -B -m tools.creature_graph.project_spec --show req.fundamental_force_scope
python -B -m tools.creature_graph.project_spec --show work.science.force_data_runtime
python -B -m tools.creature_graph.project_spec --show doc.force_source_catalog
python -B -m tools.creature_graph.project_spec --show doc.force_model_library
python -B -m tools.creature_graph.project_spec --show doc.space_mechanism_catalog
python -B -m tools.creature_graph.project_spec --show work.encapsulation.demo_game_loop
```

`--show` returns the full contract, dependencies, falsifier, and evidence freshness.
`--next` is a planning view: missing checklists are explicitly nondispatchable.
A structurally valid checklist still requires the controller's current ownership,
admission, and resource checks.

### Which graph is authoritative?

For a provisioned fleet, the controller's transactional `project_graph` is the
authority. Retrieve it using your own assigned session:

```powershell
python tools/agent_fleet/client.py --session OWN_SESSION.json graph_snapshot
```

The repository JSON is a versioned bootstrap or proposal for that service; edits
do not hot-update its database. Graphify is a checked projection of the selected
authority. It is not an independently editable source of project policy.

If no controller session is provisioned, report that fact. Explicitly authorized,
isolated repository work may proceed as repository work; do not claim a live
workflow admission, invent credentials, reuse another agent's session, or restart
a shared service to manufacture ownership.

## 3. Follow the graph workflow

Read `req.agent_operation` for the full operation map and responsibilities.

1. Select the assigned graph work item; read its dependencies and scoped contract.
2. Confirm ownership and resource reservations. Preregister a prediction and a
   falsifier before the implementation or measurement.
3. Implement one coherent change in the assigned scope. Keep declarations,
   definitions, and callers compatible together. Parallel workers use isolated
   scopes and builds; shared integration and graph changes have one serial writer.
4. Commit the candidate, then run the approved checks against that exact revision.
   Capture failures as well as passes, with inputs and artifact identities.
5. Submit scoped evidence and the candidate through the assigned review and
   integration path. Only the authorized verifier/integrator advances its gates.

Commit messages include an `Agent: NAME` trailer. The operator has authorized prompt
publication of completed commits to the existing project remote; read
`req.publication_workflow`, push to the intended branch, and verify the remote ref.
Master integration follows its assigned authorization. No shared engine restarts,
worktree resets, or changes to another lane's state.

A task without an approved executable checklist needs its checklist prepared and
reviewed before controller dispatch. Do not substitute a prose assurance for it.
Worker self-reports cannot authorize their own verification. The control plane
enforces workflow within its interfaces; it is not an operating-system sandbox.

### Batch database intake

Whole databases integrate and prove in one run:
`python -B -m tools.creature_graph.batch_qualify --reprove all --admit
smithsonian_voyager,copernicus_glo30,bodyparts3d --apply --train exercise --out
tools/science_funnel/validation/batch_20260917/receipt.json`.
Each connector pins its artifacts by sha256; every record class carries an
admitted Rule-0 contract (`data/authored/class_contracts.json`) whose mechanical
falsifiers run over every record; existing admissions re-prove byte-identically
under their recorded producers; the count identity closes with zero silent
drops (conflicting records quarantine, never merge). One receipt records the
whole batch. Admitted records stay `extracted` — batch admission is proven
intake, never verification. Per-domain connector modules
(`tools/science_funnel/batch/connectors_*.py`) auto-merge their connector
declarations into the batch registry — `connectors_life.py` (PanTHERIA 1.0 +
NCBI taxdmp Macaca subtree applied, Rhea proven-but-not-applied; receipts
under `validation/batch_life_20260917/`) is the first — so parallel intake
lanes never edit the shared registry.

## 4. Documentation and proof

The graph separates **admission**, **implementation**, **measurement**, **freshness**,
and **deployment**. An active specification is an adopted requirement; it is not
a claim that the engine implements it or that a test passed.

New prose begins as experimental material. Preserve its original bytes and source,
extract typed proposals, validate them, and admit them through the authority for
the current lane. A source import alone never turns arbitrary text into policy.
Historical evidence retains its original inputs, failures, and limited scope.

Authoring inputs live in `tools/creature_graph/data/authored/`; the active
encapsulation program is `project_program.json`. Inspect a rebuild without
overwriting the selected store:

```powershell
python -B tools/creature_graph/build_graph.py --with-reference --check-only
```

Existing Markdown files are historical or reference material unless an active
graph contract explicitly adopts their content. Prior versions of the root
onboarding files and core graph contracts are preserved losslessly as graph
source records; find them with `--search` and retrieve with `--show`.
Root `AGENTS.md` and `CLAUDE.md` only redirect here.

## 5. Run the current scientific workbench

Windows with CMake, a native C++ compiler, Vulkan support, and Python is required.

```powershell
powershell -File tools/science_funnel/run_surface.ps1
```

Open [the local scientific workbench](http://127.0.0.1:8107/science).
The launcher builds and runs the native surface experiment. Its measured scope
is a quasistatic constant-tension surface using pinned scientific inputs.
It does not yet qualify a dynamic two-body interaction or a complete creature
game loop. Read `doc.science_surface_native` in the graph for the recipe and evidence.

Relevant checks, run from the checkout root:

```powershell
python -B -m unittest tools.creature_graph.tests.test_project_spec -v
python -B tools/creature_graph/tests/test_contracts.py
python -B -m unittest discover -s tools/science_funnel/tests -p "test_*.py"
```

### Rebuild the force-origin scientific catalog

The pinned source files cover constants, gravitational parameters, gas species,
solid property curves and nuclide metadata. Read `doc.force_source_catalog` in
the graph for source limitations and the admission recipe.

```powershell
python -m pip install -r tools/science_funnel/requirements.txt
python -B -m tools.science_funnel.force_catalog --output .tmp/force-catalog
```

The build is offline. It creates a checked graph snapshot and preserves source
qualifiers; importing a model definition does not qualify its runtime behavior.

### Play the native thermal-salvage demo

Hold the heater to lift a load, release inside the target window, and recover it
before spending the finite charge. Gas energy, pressure, motion and beam reaction
are calculated by the native engine.

```powershell
powershell -File tools/science_funnel/run_thermal.ps1
python -B -m tools.creature_graph.project_spec --show doc.thermal_salvage
python -B -m tools.creature_graph.project_spec --show doc.native_readback_diagnosis
```

Open [thermal salvage](http://127.0.0.1:8108/thermal). The launcher uses its own
build and refuses occupied ports. The graph holds source mappings, derivations,
reference-test commands, evidence identities and the model's limits.

## 6. Release sequence

The active contract is `req.engine_game_release`:

**Functioning demo game loop -> qualify and lock the open-source engine ->
create the separate game repository -> focus on the game.**

The loop must include a concrete objective, player action, physical consequence,
feedback, success/failure, and recovery. The graph names its prerequisites and
falsifiers. Later concepts do not block engine release unless the selected demo
requires them. The separate game will depend on a versioned engine interface.
Creating that repository is a later gated task, not part of onboarding.

The engine's existing license is in [LICENSE](LICENSE). The future game's
visibility and license have not been selected.
### Explore the data-derived macaque arm

```powershell
powershell -File tools/science_funnel/run_creature.ps1 -Anatomy -EnginePort 8124 -GamePort 8224
```

Choose free private ports. Read `doc.workflow.macaque_assembly` for source pins,
units, geometry processing, native checks and the remaining anatomical work.
This is a jointed anatomical reference; muscle forces and whole-body tissue layers
remain unimplemented.

### Explore the creature–Earth boundary

```powershell
powershell -File tools/science_funnel/run_earth.ps1 -Port 8125
```

Open `http://127.0.0.1:8125/earth`. The source-derived arm releases a reference
object into native gravity, air, ground contact and heat exchange. Read
`doc.workflow.earth_patch` for data provenance, assumptions, energy/momentum
accounts and continuation tasks. Choose a free private port; other worlds remain
independent.

### Load-bearing anatomy reference

```powershell
powershell -File tools/science_funnel/run_earth.ps1 -ForceArm -Port 8126
```

Open `http://127.0.0.1:8126/earth`. Cut drive power, change the target, apply a
downward load or reduce torque. Native dynamics owns the elbow angle; the
source arm can fall or stall against its support. Read `doc.workflow.force_arm`
for inertia derivation, finite-energy accounting, qualification and limitations.

### Derive coupled joint dynamics

```powershell
python -B -m tools.science_funnel.coupled_arm
python -B -m unittest tools.science_funnel.tests.test_coupled_arm -v
```

This produces `.tmp/coupled-arm/reference.json`: named coordinate slots, the
source-derived inertia matrix, gravity and velocity-dependent joint loads.
Read `doc.workflow.coupled_arm` for the derivation and independent checks, and
`work.creature.coupled_arm_native` for integration. This command produces the offline reference. The two-coordinate native scene below consumes the same source laws.

### Move the coupled shoulder and elbow

```powershell
powershell -File tools/science_funnel/run_earth.ps1 -CoupledArm -Port 8127
```

Open `http://127.0.0.1:8127/earth`. Each drive applies capped torque to a source-derived
coupled mass matrix. Cut either drive, change a target, add hand load, or cut global
power. The native state determines both bones and the hand marker. A finite 2 J
mechanical store, passive losses and source joint stops account for energy.
Enable **Hand contact plane** and drive the elbow target toward 20°: the hand presses
an authored rigid surface, a measurable normal reaction appears, and the
elbow stalls short of its target instead of passing through. The toggle resets the
trial; with it off, the qualified free dynamics run unchanged. With contact on, the
**friction coefficient μ** slider (0–1) applies live, without a reset: μ = 0 is the
qualified frictionless world bit-exactly, low μ lets the hand slip while dissipating
friction heat into the energy ledger, and high μ makes it stick (readouts show the
tangential force, slip speed and stick/slide mode). A preregistered one-time
catch-event balance allowance of 5e-5 J at first landing is documented in the
receipt.
Read `doc.workflow.coupled_native`, `work.creature.coupled_arm_contact` and
`work.creature.coupled_arm_friction` for
equations, checks, scope and next work. This reference has a fixed mount and two
moving coordinates; grasping, whole-body balance, muscles and GPU
integration remain unfinished.
