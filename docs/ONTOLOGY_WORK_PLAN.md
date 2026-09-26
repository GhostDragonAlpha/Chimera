# Work is organized by membranes and their ports

Operator-authorized amendment, 2026-09-24. The existing 83 task IDs remain the
work inventory; each task now names its primary membrane, related membranes,
connection membranes, verification profile and integration checkpoints. The
machine-readable completion map owns those mappings and dependencies. Browser
and worker views are derived from it; this document does not create a second
task board. Existing accepted evidence must be reconciled, never erased.

Containment determines the subject and integration boundary. Port contracts
determine which providers a consuming integration must have qualified first.
Explicit task dependencies define that order. A preorder traversal of the tree
is not a schedule: independent child membranes can progress in parallel, and a
large parent is accepted only after its required children/connections are ready.
Dependency layers are logical readiness groups, not elapsed-time estimates.

Checkpoint task IDs are contributors to an integration milestone. They do not
make those tasks depend on their own checkpoint. Checkpoint `requires` orders
integrated acceptance, not independent implementation. S05 accepts the feature
set; completing the selected list also requires its downstream S06 deliverable.

Every task retains its original done_when and calculation contracts. The
ontology adds the subject, interface dependencies and evidence requirements;
it does not turn an old report into current acceptance. The seven material/
assembly modernization tasks remain conditional unless a runtime adopts that
path. Their presence in the ontology is not authorization to activate them.

## Visual verification is an explicit work product

Every visual profile names the subject, scenario, diagnostic layers, required
views, clean-view requirement and falsifier. Each run must freeze a capture
manifest BEFORE judging its result. That manifest records:

- Candidate/build/model/ontology/task IDs and raw input identities.
- Simulation state or tick interval and the actual command trace.
- Camera frame ID and units; position; orientation convention and value; target;
  target distance; projection; vertical FOV or orthographic span; near/far planes;
  aspect ratio; viewport/capture resolution; camera motion/bookmark sequence.
- Overview, detail and alternate/oblique views as required by the profile;
  required objects/ports and their screen visibility in each view. Record the
  actual numeric settings, not merely 'front', 'close' or 'looks clear'.
- Visibility masks, selected IDs, clipping/section planes, x-ray/occlusion mode,
  overlay scale, labels and legend; stable membrane/port IDs behind display names.
- The inspected images/video, numerical trace and the independent verdict.

Derive framing from the subject bounds and the declared feature under inspection,
or reuse an approved camera bookmark. Do not invent a universally sufficient
angle/distance, crop away failures, or mutate the operator's live orbit to make
an instrument pass. Motion needs a recorded interval, not one favorable frame.
Paired diagnostic/clean views use the same state or reproducible command trace;
camera/overlay toggles must not change physical state, contacts, forces or RNG.

Hidden implementation elements are intentionally visible in diagnostic mode:
bones, joints, tendon paths, attachment patches, frame axes, collision surfaces,
contact normals and forces. Their absence in final gameplay is not a missing
feature. An x-ray label is an instrument, not proof that two solids intersect.
The normal-depth view and numerical ownership/contact evidence remain required.

Profiles are applied to the exact task acceptance clause, not every later
behavior in that skill family. G02 uses controlled attachment-fixture loads;
G03 uses a tendon pose sweep; F04 records impact/crossing trajectories to catch
tunnelling; W03 records its frozen parity replays. Early anatomy work inventories
missing layers explicitly instead of requiring downstream anatomy to exist.
These profile distinctions preserve useful parallel work.

Instrument qualification includes dense labels, leader-line target identity,
near/far views, resized viewports, clipped and behind-camera objects, and the
occluded side of a trunk. Each required subject must be visibly inspectable in
at least one declared view. Record occlusion and x-ray status honestly; numeric
camera settings alone do not prove that the geometry was visible.

## Existing engine machinery to reuse

`ChimeraEngine/engine/engine.cpp::Engine::push_joint_tags()` projects joint
positions through the frame's view-projection transform. It already implements
label de-crowding and viewport/panel exclusion. `ui.hpp::StudioUI::JointTag`
and `ui.cpp` render the tags. They intentionally do not depth-test labels.
`main.cpp` exposes GET/POST `/inspect` using the same inspector state as the UI.
These are source-inspection findings, not fresh runtime qualification.

The P02 lineage/inspection work must bind tag IDs to actual membrane/source IDs
and capture named diagnostic presets. X06 extends the existing inspection path
to live physics values. Reuse these paths for other elements; do not create a
second label renderer or infer anatomical identity from display text. Native
changes still require a scoped PR and runtime/resource ownership.

## Preregistered plan checks

Q1: any of the 83 tasks has no valid primary membrane/profile -> refuse.
Q2: a task references a nonexistent membrane, port connection or checkpoint -> refuse.
Q3: port integration consumes an unlisted prerequisite, or DAG cycles -> refuse.
Q4: a visual checkpoint lacks camera/diagnostic/clean-view requirements -> refuse.
Q5: task acceptance/calculation clauses disappear during migration -> fail.
Q6: a conditional task becomes selected merely because its membrane is visible -> fail.
Q7: worker packets/browser task lists differ from the same amended catalog -> fail.
Q8: a capture receipt lacks actual camera values or claims visual acceptance from
    hashes alone -> refuse structurally / withhold substantive acceptance.

The inspector displays planned checkpoints, not earned visual passes. The
existing lead/independent/human acceptance gates remain responsible for verdicts.
