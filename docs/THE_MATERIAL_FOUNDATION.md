# Chimera material foundation: architecture contract v0.1

Owner: ASTRA, architecture coordinator. Operator: Alan. Written 2026-09-06.
Status: implementation specification, not a measured runtime certificate.
Session context and dispatch state: [FOUNDATION_CONTEXT.md](FOUNDATION_CONTEXT.md).
Executable worker assignments: [FOUNDATION_AGENT_TASKS.md](FOUNDATION_AGENT_TASKS.md).

## Purpose and authority

Alan has assigned ASTRA the architecture, derivation, context, integration review, and
task-dispatch role. Local/open-source agents implement and test assigned pieces. Alan
dispatches them through chat, judges the engine window, and can stop the work. The local
DYAD vision agent examines ordered captures of that same window. No agent's confident
description replaces evidence.

This contract implements the operator's current instructions. It retains the triangle
carrier, gravity-translation architecture, GPU runtime, membrane composition, timeline,
and DYAD in `THE_WOLFRAM_FRAME.md`. It does not certify old implementations by inheritance.
The present project is broad; assignments are bounded so their results can be attributed.
New ideas remain in the context ledger instead of becoming silent changes to a running test.

## The six contracts

| Contract | Owns | Must not own |
|---|---|---|
| Material | Versioned constitutive responses, measured parameters, applicable conditions, uncertainty | A second copy of object geometry or prescribed motion |
| Geometry | Triangle topology, rest metric, thickness/volume allocation, material directions | Unsourced stiffness or strength inferred from appearance |
| Membrane | Material/geometry membership, internal state, children, typed interfaces and initial conditions | Duplicate mass or independent clocks for the same physical element |
| Translation | Derivation from material response to the shared force/constraint calculation | Unproved claim that an arbitrary force equals a scalar radial modifier |
| Timeline/runtime | Accepted GPU state, tick ordering, input work, integration and synchronization | Per-frame Python-authored positions or a competing visual pose |
| Evidence/DYAD | Equation checks tied to a build and state; actual window captures and judgments | A blanket `verified=true` disconnected from conditions or footage |

These are logical contracts. They do not require six new subsystems or replacement
implementations. Reuse the existing ledger, engine buffers, API, and visual tooling where
the data and behavior meet the contract. Multiple typed buffers may hold one authoritative
state; scratch buffers and diagnostic snapshots are not competing simulation authorities.

## Material contract

An object is shaped geometry using a particular material under particular conditions.
"Wood", "metal", or "water" alone is an incomplete parameterization. Material identity
must include enough information to distinguish the response being claimed.

Every parameter record must carry: property name; value or referenced function; units;
provenance category and source locator; uncertainty meaning (or explicitly unknown);
temperature/moisture/strain-rate domain where relevant; direction/frame; revision; and
dependencies for derived values. Read existing values through `tools/matter_data.py` and
the referenced material library; do not create a second unsynchronized table.

| Response family | Required information for a supported claim |
|---|---|
| Mass | Density with reference conditions; shell thickness or volume allocation |
| Isotropic elasticity | Two independent elastic constants, compatible domain, strain measure and stress law |
| Orthotropic wood elasticity | Longitudinal/radial/tangential frame and the stiffness/compliance components needed by the chosen model; symmetry and positive-definiteness checks |
| Strength/failure | Distinct yield/ultimate/fracture measures as applicable; tension/compression/shear direction and rate conditions; failure criterion |
| Fluid response | Density/compressibility or incompressible constraint, momentum representation, viscosity and its domain |
| Surface/interface | Pair of phases/materials, interfacial energy or response law, temperature and environmental scope |
| Thermal/history | Heat capacity/transport and state evolution only when that capability is actually implemented |
| Optical | Appearance properties and their material/phase linkage; no reverse inference of strength from color |

Stiffness and failure strength are different. A material can resist deformation strongly
yet fail at a small strain. Material strength is also different from object load capacity:
shape, thickness, supports, and defects determine the latter. Wood direction and moisture
matter; clear-wood tables are not automatically structural lumber design values.
[USDA Wood Handbook, mechanical properties](https://research.fs.usda.gov/treesearch/62244).
Water surface tension is condition-dependent; the IAPWS release concerns water in
equilibrium with pure water vapor, which is not an automatic calibration for contaminated
water in air. [IAPWS release](https://iapws.org/technical-guidance/release/Surf-H2O).

Capability is explicit: `available`, `missing_input`, `out_of_domain`, or
`unsupported_model`, with a reason and the input/model that resolves it. Missing shear
constants need not prevent an independently supported uniaxial demonstration; they must
prevent a claim of fully parameterized 3D wood. Unknown never becomes zero or a default.

## Geometry and membrane contract

An area scalar does not identify solid strain. A triangle's rest-to-current in-plane
metric captures stretch and shear; adjacent-face geometry captures bending. The physical
mass lives once, with references from overlapping anatomical or conceptual groupings.
Triangle area times density is not a mass unless density is areal or thickness is supplied.

A membrane contains a declared physical domain, stable element IDs, material references,
initial state, capability declarations, boundary ports, law revision, validity domain, and
evidence references. A conceptual membrane may group children without adding new mass.
For a knee, the children can be bone, cartilage, ligament, tendon, and actuator membranes;
the knee declares their geometric attachments, contact and allowed motion. A ROM clamp
alone is not a tissue model. Actuation supplies accounted work; it does not teleport a pose.

Ports declare participants, orientation/frame, units, exchanged quantities, and ownership:
mechanical traction/velocity, contact, fluid flux, heat flux, or control work as applicable.
Each internal exchange is applied once with the appropriate equal-and-opposite transfer.
The same pair cannot acquire both a bond stiffness and a separate shell stiffness for the
same mode without deriving their combined response. Interface composition checks units,
orientation, capability, conservation, and compatible time domains before activation.

## Translation and GPU contract

The desired sequence is material law -> discrete energy/constraint/dissipation -> shared
force accumulation -> accepted state -> engine picture. Constant liquid surface tension
is the first isolated port: [THE_SURFACE_ENERGY_TRANSLATION.md](THE_SURFACE_ENERGY_TRANSLATION.md).

The gravity walk provides the common hierarchy and interaction mechanism. For a nonzero
radial draw D, a desired radial interaction f can be represented algebraically by M=f/D.
Stable evaluation must avoid artificial division by near-zero D. Tangential and multivertex
responses require a derived representation. If the scalar modifier cannot encode one,
report that expressivity limit and propose a local vector/constraint extension for
architecture review. Do not bolt on an independent simulator or disguise the extra law.

CPU initialization validates and uploads parameters/topology. CPU runtime requests are
tick-addressed levers/events, camera, and inspection. GPU passes evaluate accepted laws
and integrate state. Each buffer has one writer per stage, declared readers, barriers,
and a validity policy. Gather or proven coloring avoids uncontrolled scatter races.
An invalid trial step cannot silently become a corrected render-only state.

Budget reports separate resident memory, bandwidth, dispatch/dependency cost, numerical
substeps, render cost, and vision-model contention. Parallel slot count alone is not the
capacity metric. Fixed triangle count alone does not prove fixed computational cost.

## Fourth-dimensional contract

Every observation identifies scene revision, law/material revisions, simulation tick,
simulation time, input sequence, camera pose, and engine build. Render time and simulation
time are separate. Slow motion or playback rate is explicit. Changing display FPS must not
silently change the law's elapsed physical time. Mixed-rate membranes exchange flux/impulse
over matching intervals with conservation checks; mixed-rate coupling is not yet certified.

Checkpoint plus ordered inputs is a replay candidate. Same-machine reproducibility and
cross-device reproducibility are separate capabilities. GPU float32, float64, and integer
state can coexist where their numerical/conservation requirements demand it.

Ordered screenshots can reveal motion but can miss between-frame events. A camera-only
control distinguishes camera motion from object motion; timestamps prevent stale frames
from masquerading as progression. Record a movie when sparse captures cannot resolve the
claimed behavior. Do not infer continuity or stability from one still frame.

## Engine window and DYAD acceptance

All product behavior is demonstrated in the real engine window. Offline numerical tests
are supporting instruments, never substitute viewers or acceptance of an object.

Acceptance record has independent fields:

- `numeric`: claim, reference, measured result, tolerance provenance, controls, pass/fail.
- `runtime`: actual engine build/path, state ownership evidence, timing/buffer checks.
- `visual`: ordered actual-window frames/movie, camera and tick metadata, observer identity,
  observed defects and uncertainty. A compile or a synthetic plot cannot fill this field.
- `human`: Alan's judgment in his words, including requested changes; never fabricated.
- `scope`: demonstrated conditions and explicit untested conditions.

Stages: specified -> numeric_checked -> engine_observed -> dyad_reviewed ->
operator_accepted, with failed, pending, and out-of-scope fields retained. These stages
are proposed report states, not changes to the existing verdict registry.

The local eye receives the subject and observation question without the numerical
prediction it is supposed to independently assess. Compare its observations with the
numerical record afterwards. Alan can independently inspect and judge the window.
If the eye is unavailable, record that state; a coding model cannot silently impersonate it.
When Alan identifies a visual discrepancy, preserve the evidence and investigate; never
adjust physical constants solely to make an unrelated image score pass.

## Architecture predictions and falsifiers

| Statement | Prediction before implementation | Falsifier |
|---|---|---|
| Material identity is reusable | One material revision binds to two geometries without copying parameter values | Hidden per-object constants change the claimed material response |
| Geometry determines object response | One declared beam law predicts the geometry-dependent compliance of both objects within its domain | Response stays fixed despite changed geometry, or exceeds preregistered error |
| Unsupported responses are explicit | Removing a required property yields its exact capability refusal | A silent fallback produces a supposedly physical object |
| Composition conserves exchanges | Joined ports have a closed mass/momentum/work ledger | An internal interface creates or loses an unaccounted quantity |
| Timeline belongs to the simulation | Replay at different presentation rates matches at equal simulation ticks under the declared determinism tier | Display FPS changes the physical trajectory |
| Rendering reveals the accepted state | Captures and numerical diagnostics refer to the same state identifier | Different state or pose drives the picture |
| Weaker agents can build through contracts | A task worker produces an auditable result without choosing hidden material constants or changing core laws | Completion depends on guessing those values or bypassing the contract |

Numeric tolerances must be preregistered by each task from its reference and scope. A
universal visual score or a single universal material-error percentage is not specified.

## First delivery and expansion

Wave 1 establishes contracts, one force reference, and the actual window/evidence seam.
Wave 2 connects an accepted reference to GPU state and a single material demonstration.
Wave 3 composes cup and liquid only after bulk/contact/interface capabilities are established.
Wood, aluminum alloys, liquids, knees, and further mechanisms remain in the same roadmap;
they receive separate capability certificates as their distinct responses become supported.

The local agents' current assignments and writable paths are exact in the task document.
ASTRA reviews their output before issuing the next integration assignment. No worker may
declare all matter, complete walking, or the foundation itself proven from one passing port.
