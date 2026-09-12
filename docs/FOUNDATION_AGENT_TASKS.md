# Foundation worker assignments, revision 1

Coordinator: ASTRA. Operator: Alan. First available worker: GLM 5.3 Flash on the
platform Alan supplies. This document does not launch an agent or assume platform tools.

## Dispatch order

| Packet | Worker | State | Dependency |
|---|---|---|---|
| G01: material contracts + force-reference foundation | GLM 5.3 Flash | Ready for Alan to paste | This architecture package |
| V01: engine-window and DYAD seam | Next local window-capable agent | Reserved; specification below | Can audit independently; only one camera owner |
| I01: GPU integration + first live membrane | Unassigned | Not authorized by these packets | ASTRA review of G01 and V01 |

G01 combines the previously proposed A/material and B/force-reference tracks in one
sequential assignment for the first available worker. V01 is the previous C track.

## G01 — complete assignment for GLM 5.3 Flash

ROLE: foundation implementation and derivation worker. ASTRA retains architecture review;
Alan owns product judgment. Work in the Chimera repository available to your platform.
Alan's Windows working copy is E:\PythonChimera, but do not assume that drive is mounted
on a remote platform. Discover your actual cwd and tools before claiming local access.

OBJECTIVE: implement a sourced, capability-aware material contract and one conservative
triangle surface-energy reference, with falsifiers and an actionable GPU handoff. Do not
build an independent simulator or claim the entire foundation validated.

### Isolation

Read all relevant repository instructions. Current user restrictions override older
master-commit instructions. No master push, no force-push, no writes anywhere under
ChimeraEngine/engine/build/, no process kills/restarts, no engine POSTs, no runtime or
gait changes. Do not alter other agents' files. Do not install tools or download large
assets merely to expand this packet. If tools are unavailable, finish the derivation and
accessible implementation work and report exactly which measurements remain unavailable.

For this packet do not commit, push, or change branches. Return the exact patch/file set
to the coordinator. Work only in a checkout already containing this packet; do not pull
over another worker's changes. If the checkout has unrelated changes in your owned files,
report the collision and continue unaffected tasks without overwriting them.

Owned deliverables (NEW files; paths are assignments, not claims they already exist):

- tools/material_contract.py
- tools/material_contract_checks.py
- tools/surface_energy_reference.py
- tools/surface_energy_checks.py
- docs/FOUNDATION_G01_REPORT.md
- docs/FOUNDATION_G01_GPU_HANDOFF.md
- Optional raw evidence: agent_logs/glm_foundation_g01/ (gitignored; include in returned
  artifacts and summarize immutable measurements in the tracked report).

Scratch only under .tmp/glm_foundation_g01/. No deliverable may exist only in scratch.
Do not edit the governing architecture, context ledger, master list, source material
tables, or surface preregistration. Proposed corrections belong in your report.

### Read first

1. docs/FOUNDATION_CONTEXT.md
2. docs/THE_MATERIAL_FOUNDATION.md
3. docs/THE_SURFACE_ENERGY_TRANSLATION.md
4. docs/THE_WOLFRAM_FRAME.md and docs/THE_TRIANGLE_GUIDE.md
5. tools/matter_data.py, tools/port_registry.py, tools/port_tests_matter.py
6. tools/ca_triangle.py and LightEngine/modifier.py
7. Engine water/volume shaders only to understand the handoff; do not repair them.

### Ordered work list

1. Report base SHA, branch, platform capabilities, Python/numpy availability, and owned
   path collisions. Read existing source, including tests, rather than relying on comments.
2. Start FOUNDATION_G01_REPORT.md with STATEMENT / PREDICTION / FALSIFIER before code or
   tests. Reuse the surface port's registered predictions. For material schema validation,
   predict explicit accept/reject results for each fixture before executing it.
3. Inventory which existing material sources supply density, elastic response, strength,
   failure, viscosity, interfacial response, and conditions. Use primary sources if extra
   research is necessary. Keep source URLs, table/equation locators, units, and domains.
4. Implement immutable material/property records, material identity/revision, response
   model ID, provenance/dependency references, units, uncertainty meaning, applicable
   conditions, and material frame. Do not make one mandatory giant record containing every
   possible property: requirements belong to declared model capabilities.
5. Implement a narrow adapter reading tools/matter_data.py's existing data/functions.
   Never silently duplicate or default its values. Preserve its missing-source refusals.
   Existing white_oak and douglas_fir entries are starting evidence, not presumed complete
   orthotropic materials. Missing uncertainty is explicitly unknown, not zero.
6. Implement capability evaluation returning available, missing_input, out_of_domain, or
   unsupported_model with exact missing requirements. An available property set is not
   a runtime certification. Do not infer yield from elastic modulus or convert specific
   gravity to density without a declared reference-density/conditioning basis.
7. Implement dimensional validation for the supported property set. Distinguish Pa, N/m,
   N/m², J/m², Pa*s, and kg/m³; equivalent units may be normalized explicitly. Reject
   unknown units rather than inventing conversions. Reject nonfinite values and physically
   invalid domains (e.g. negative density); zero surface tension is a legal control.
8. Validate only declared elasticity models. For full 3D isotropic linear elasticity,
   E>0 and -1<nu<1/2 yield positive bulk and shear response. For a supplied orthotropic
   stiffness/compliance matrix, declare Voigt/shear convention, verify symmetry and
   positive definiteness, and validate the material frame. Do not manufacture absent
   components. A uniaxial-only capability can remain available independently.
9. Create independent material-contract controls: correct and wrong units; missing
   property/source; domain violation; nonfinite inputs; invalid matrix; nonorthogonal
   frame; material reuse on two geometries; changed source value propagating through the
   adapter. Use synthetic values explicitly labeled as fixtures. Require each invalid
   fixture to produce the expected reason, not just any exception.
10. Implement surface_energy_reference.py with numpy + stdlib only. Public functions:
    evaluate_surface(positions, faces, gamma), build_vertex_corner_adjacency(faces,
    vertex_count), and triangle_metric(rest_positions, positions, faces). Document shapes,
    units, accepted dtypes, and empty/invalid input behavior. Return energy, per-face
    areas, face-corner forces, vertex forces, and validity diagnostics as appropriate.
11. Follow THE_SURFACE_ENERGY_TRANSLATION exactly: CURRENT unsigned area, current normal,
    constant nonnegative scalar or per-face gamma, conservative force -grad U. Refuse
    degenerate faces explicitly. No rest-area spring, frozen reference normal, damping,
    arbitrary collapse cure, timestep, or dynamics is introduced into this reference.
12. Build fixed vertex-to-corner adjacency suitable for deterministic GPU gather. Validate
    each face corner appears exactly once and no vertex index is out of range. Compare
    the gather result with a separate CPU scatter on a mesh with shared vertices.
13. Implement triangle_metric as rest-frame F^T F, with a declared tangent basis and
    consistent transformation. Demonstrate the equal-area diag(2,1/2) counterexample.
    This returns geometric information, not a complete constitutive solid law.
14. Implement EVERY registered surface falsifier in surface_energy_checks.py, including
    independent energy finite differences, force/torque balance, rigid motions, scaling,
    zero gamma, rejected invalid geometry, negative controls, sphere refinement, and the
    prescribed 121-sample moving-geometry test. Do not call that trajectory an integrated
    simulation or use its samples as substitute engine footage.
15. Reuse the existing port registry where compatible; otherwise justify the seam. Assert
    the expected check count. Emit machine-readable results and nonzero exit on failure.
    No silently skipped test may count as PASS. Print tolerances and their derivation.
16. Verify the independent instrument detects wrong-force sign, zero force, frozen normals,
    and unbalanced force. Controls that merely compare two copies of your implementation
    are insufficient. Preserve raw failed runs and diagnosis; never widen the gate after
    seeing results. If a preregistered assumption is false, report it and propose a new
    membrane rather than pretending the old one passed.
17. Draft FOUNDATION_G01_GPU_HANDOFF.md: explicit buffer layouts/units, scalar versus vector
    semantics, face-force pass, CSR vertex gather pass, validity mask, barriers, ownership,
    deterministic tier, units conversion, and force-accumulation seam. Map each force mode
    to the radial modifier where possible; show where a scalar multiplier is insufficient.
    Propose any extension explicitly; do not implement it or another physics engine.
18. Explain how the reference material state binds to a membrane and how a shared material
    can be shaped into different objects. Separate material stiffness, failure strength,
    geometry-dependent load capacity, and interface adhesion. Include wood, a named alloy
    as an unsupported example if data is missing, liquid surface, and knee composition.
19. Propose an engine-window experiment for the later integrator: actual state identifiers,
    expected behavior, controls, camera-only motion, ordered captures, and questions for
    the local DYAD. Do not manufacture captures or record visual/human PASS in this packet.
20. Run only relevant checks. Review the patch against owned paths and provide complete
    commands, outputs, numerical maxima/RMS where relevant, failure history, sources,
    open assumptions, and integration dependencies. Stop at this handoff; do not take I01.

### Required return to Alan and ASTRA

1. Falsifier table: name -> PASS/FAIL/NOT RUN, measurement, limit, reason.
2. Files written and exact base SHA; patch or commits from the platform if independently
   created by its workflow, but no worker push under this packet.
3. Falsified/retracted claims and preserved failed-attempt evidence.
4. Open numerical/runtime/visual/human items, separately.
5. Boundary hits and missing capabilities.
6. New ideas: idea, why it helps, cheapest falsifier, and whether it changes the architecture.

The objective is a reusable foundation, not a cleanup campaign or a polished fake demo.
Perform the authorized work autonomously within these paths. Do not stop merely to ask
whether you should continue. A real missing input blocks only the capability it affects.

## V01 — reserved next local assignment

Not yet dispatched. Objective: identify and demonstrate the real engine-window / local
DYAD evidence seam without changing physics. Reads: THE_MATERIAL_FOUNDATION, current
engine/main.cpp routes, engine/engine.cpp, senses.py, cpp_bridge.py, current local viewer
launch/config, and actual running process identity. Source wins over stale launch prose.

Owned deliverable: docs/FOUNDATION_V01_REPORT.md and captures under
agent_logs/foundation_v01/. No runtime edits, process restart, protected-build writes,
or physics POSTs. Camera changes require the sole active camera lease for that session;
Alan's interaction takes precedence. When assigned, use the existing running engine and
configured local eye, not a replacement viewer/model selected by the worker.

Read-only audit can run alongside G01. Actual observations must identify build, scene,
tick/time if exposed, camera, capture order, and uncertainty when metadata is missing.
Demonstrate (a) fixed camera with existing motion, (b) camera-only change on a paused or
otherwise independently characterized scene, and (c) human input remains responsive.
Use a few ordered frames first; escalate temporal sampling if the claim is unresolved.
The local eye receives observation questions without predicted numeric outcomes.

Return the exact existing invocation commands, original captures, eye observations,
human judgment if Alan supplied one, and the minimal missing metadata/API contract.
Unavailable engine/eye is NOT RUN, not a reason to fabricate or launch a rival process.
No foundation acceptance follows from observing an unrelated existing gait.

## I01 — integration admission, not yet an assignment

ASTRA first reviews G01 and V01, reconciles expressivity/parameter gaps, and names a
single material membrane plus a current engine seam. Only then issue writable engine
paths, an isolated build output outside the protected directory, replay/input protocol,
numerical comparison gates, and a real-window DYAD experiment. Alan's material and
visual judgment remains the product checkpoint.
