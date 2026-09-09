# CHIMERA — THE LIVING HOLODECK BLUEPRINT

**Edition 1 · 2026-09-08 · ASTRA architectural proposal for Alan**  
**Inspected repository snapshot:** `bf0a62162008c8415b88091c671ac180dbb50193` on `astra/gait-capture`.  
**Publication status:** review proposal; adoption and deployment are not implied by publication. Existing agent work continues.

**Operating amendment:** [THE_AGENT_FLEET.md](THE_AGENT_FLEET.md) and [AGENT_START.md](AGENT_START.md) define the proposed five-slot successor operating system. Historical role assignments below remain active until reconciled migration; after activation, the controller owns live claims and leadership. The catalogue is planning input, not authority to claim work.

## Read this first

The ambition is a world in which people can create, inhabit, inspect and change richly interacting objects, environments, creatures and stories. Chimera's particular foundation is a triangle substrate whose accepted physical state also supplies visible geometry. The job is to make increasingly broad classes of phenomena work together, with declared limits, rather than to produce a collection of convincing but mutually inconsistent demonstrations.

This book is a finite, extensible first map. It does **not** enumerate everything that will ever be discovered, promise the most advanced engine by an objective universal ranking, or claim to encode an entire person or universe. No finite software system or dataset specifies every real-world state. A holodeck-like experience can nevertheless be an engineering objective if the experience, represented phenomena, devices, spatial/time scales and error budgets are stated.

This edition contains **240 capability task cards across 40 domains**, an integration ladder, mathematical contracts, an agent operating protocol and a machine-readable catalogue. Cards specify deliverables and falsifiers; a card is not an already validated derivation. Research tasks start by identifying a tractable question and independent benchmark. A missing derivation is work to perform, never a license to invent a physical constant or silently weaken a gate.

Read the current-control section first, then the dependency front relevant to your task. The JSON catalogue is the canonical definition of the new cards; the card appendix is generated from it. After adoption, `docs/THE_MASTER_LIST.md` is the operational front door and owns active assignments, decisions and evidence pointers. This book is its design annex, not a competing live status board.

## 1. Current control and continuity

The inspected Master list opens with an old amendment naming Luna sole owner, although its later history records GLM work. Alan's later instructions in this conversation supersede that roster. Do not erase the old entry: mark it historical and place a current-control amendment above it.

| Actor | Current assignment reported by Alan / assigned in this conversation | Ownership boundary |
|---|---|---|
| Alan | Product direction, authorization and actual human acceptance | Does not have to relay every routine implementation decision |
| ASTRA | Architecture, prioritization, physics guidance and cross-stream review | No parallel production edits or publication race |
| GLM 5.3 | Autonomous GPU material milestone, including runtime integration and mandatory DYAD | Sole production implementer and publisher on `astra/gait-capture` |
| Big Pickle | BP-ELASTIC-FOUNDATION | Experimental CPU elasticity and its owned reference/evidence paths |
| Muse Spark 1.3 | MUSE-ROBUSTNESS-01 | Generated adversarial material/geometry/numerical boundary tests |
| DeepSeek V4 Flash | DS-STATE-INTEGRITY-01 | Offline state/synchronization/capture provenance verifier |
| Step 3.7 Flash | STEP-SCALE-01 | Isolated scaling/benchmark/optimization lab; GLM has GPU priority |
| Local DYAD eye | Served by the documented local vision endpoint | GLM initializes it and sends images plus physical/programming context; no separate worker task |
| Luna | Inactive for current implementation ownership | Do not restart or duplicate GLM's work automatically |

These are **active assignment claims**, not declarations that results are finished or accepted. Agent speed, self-report and model branding do not establish reliability. The previously reported local eye changed from `tiel-coder-35b-a3b-mtp` to `qwen3.8-27b-nvfp4-mtp`; record the model actually served per request instead of pinning a historical identity in the ledger.

Known progress at the inspected snapshot: published records report the constant-gamma CPU and Vulkan gates, WSL llvmpipe execution, mutation detection with reconstructed source inputs, a CPU-reference window demonstration and executed DYAD rounds, and standalone GPU relaxation. These are pointers to existing evidence, not new reruns by this book. GPU-resident engine integration is the current assignment, not a completed feature inferred from the standalone probe. Prior successful fixtures are reused; only concrete contradictions or affected paths trigger reruns.

### Nonnegotiable working boundaries

- Never push `master`, force-push, or write under `ChimeraEngine/engine/build/`.
- Use isolated checkouts. On Alan's machine every Git invocation uses `git -C <explicit checkout>` because `E:\` itself is a repository.
- GLM serializes publication. Other actors prepare owned experimental files and reviewable handoffs; they do not race remote updates.
- Never overwrite another worker's dirty files, evidence or task claim. A stale heartbeat is a reason to reconcile, not permission to steal a task.
- Control only an explicitly owned isolated demo process. Preserve Alan's running engine and resident vision service.
- No archive/manual transfer workflow is required. Publication uses GitHub. Nothing in this book grants new installations, device control, main-branch merges or external messaging rights.
- Python remains a derivation, setup, verification and evidence tool, not the per-frame physical runtime. GPU/CA runtime math stays in the appropriate native/kernel path.
- Every visually consequential implementation task explicitly includes GLM-operated DYAD. Mathematical/source-only tasks record DYAD as not applicable with a reason, not as passed.

## 2. The architecture to preserve, and the missing distinctions

### One accepted physical world

A triangle carries identity, topology, geometry and material/field bindings. A solver uses the state relevant to its declared model. A renderer consumes the accepted geometry and derives presentation data from it. A collision hierarchy, render normal, Gaussian surface moment or compressed appearance representation is a **derived view**, with its own version and approximation contract; it must not silently become an independent physical world.

A render-only rigid rotation or translation is legitimate if its mapping is recorded and physical measurements use the physical frame. A deformation added only to make a prediction visible is not evidence that the physical computation produced it. Trial positions remain separate until accepted. GPU execution, CPU orchestration, CPU acceptance checks, host readbacks and staging must each be stated honestly.

Triangles remain the primary material/interface and visible representation. They do not automatically determine arbitrary interior density, stress, pressure, temperature or chemistry. Bulk support fields may eventually require volumetric cells, particles, tetrahedra or boundary-integral information beneath the triangle surface. That is an explicit architecture decision to evaluate against the established substrate, not a stealth replacement with another engine. The roadmap offers candidate methods, not simultaneous mandatory implementations.

A cellular automaton is a representation and local-update scheme. Its neighborhood, state variables, schedule, fluxes and constitutive rules determine the physics. Gravity is one interaction; its hierarchy can accelerate some other interactions, but a gravity equation does not contain shear elasticity, viscosity, light transport or human behavior. Gaussian moment matching is useful mathematics, but does not prove equality of collision geometry, optical response and all physical laws.

### The useful layers of reality

| Layer | What must be explicit | Example limitation |
|---|---|---|
| Representation | State, topology, frames, support fields and resolution | A triangle shell does not uniquely encode the interior |
| Constitutive law | Relation between deformation/fields and energy, stress or flux | A material name supplies no missing modulus or viscosity |
| Evolution | Time integration, optimization, transport or stochastic sampling | An optimizer iteration is not a second of motion |
| Coupling | Exchange of mass, momentum, heat, species and work | Two correct solvers may still exchange energy incorrectly |
| Observation | Camera/sensor model, rendering, capture and uncertainty | A screenshot cannot prove a pressure or force value |
| Semantics | Object identity, affordances, stories and knowledge | Words cannot bypass physical admission |
| Experience | Interaction, accessibility, audiovisual/haptic feedback | Software cannot supply uninstalled physical hardware |

## 3. The mathematical contract every physical law must ship

### State and dimensions

Declare the reference configuration, current configuration, degrees of freedom, mass/inertia, velocity when time is modeled, internal variables, boundary conditions and material parameters. Distinguish intensive values from extensive quantities and reference measures from current measures. Surface density is not bulk density; reference-area energy is not current-area energy.

Use the dimension table before code:

| Quantity | Symbol | SI dimension |
|---|---|---|
| Position/displacement | x, u | m |
| Physical time / optimizer step | t / alpha | s / dimensionless |
| Velocity / acceleration | v / a | m/s / m/s² |
| Force / traction | f / traction | N / N/m² |
| Stress and modulus | sigma, E | Pa = J/m³ |
| Surface energy density | gamma | J/m² = N/m |
| Total energy | U | J |
| Area / volume / thickness | A / V / h | m² / m³ / m |
| Descent preconditioner for area energy | P = 1/gamma | m²/J |
| Descent direction | p = P f | m |
| Actual mobility in an overdamped time law | M in dx/dt = M f | m²/(J·s) |

For constant gamma the current reference is `U = sum_f gamma_f A_f(x)` with `f_i = -partial U/partial x_i`. At zero gamma, do not divide by gamma. The existing `P = 1/gamma` optimization step defines a length direction; it is not a time-calibrated mobility. Finite CPU input is not sufficient for a float32 upload: inspect the converted value and quantify representation error. World-unit mapping belongs to the physical configuration, not an undocumented display convention.

### From continuum to triangles

A law card must state whether it is a continuum approximation, a discrete model in its own right, a phenomenological closure, a learned approximation, or a purely authored rule. If discretized, state quadrature, trial/test spaces, interpolation order, mass assignment, boundary enforcement and topology assumptions. Derive force/flux from the stated law; do not tune per-vertex forces to obtain an attractive scene.

For elasticity distinguish the deformation gradient from force despite the conventional shared letter F. Objectivity means a superposed rigid rotation should not change strain energy in a frame-indifferent material law. Positive definiteness of a particular small-strain tensor is not a universal finite-strain stability proof. Near incompressibility can require special mixed formulations; an enormous penalty coefficient is not automatically a sound solution.

For a conservative system, mass, momentum and energy balances include **boundary fluxes, external work and supports**. Pins exert reactions. Contact and actuators exchange impulse/work. For a dissipative or thermal system, total mechanical energy need not remain constant; the correct heat/dissipation ledger must close. A solver must never demand universal energy nonincrease in a driven inertial system simply because an earlier optimizer used Armijo.

### Error contracts

Separate modeling error, spatial discretization, time error, nonlinear/linear solver error, floating-point error, quantization, sensor error and perceptual uncertainty. Add only compatible measures, with a justified combination rule; independent stochastic errors and worst-case correlated bounds do not combine the same way.

For a simple sequential floating-point sum in the usual model, use `eta_n = n*u/(1-n*u)` only under its assumptions (`n*u < 1`, appropriate finite arithmetic, no unmodeled under/overflow). Assembly error can be bounded using the sum of absolute components, avoiding division by a nearly cancelled result. Face arithmetic, tree reductions and temporal accumulation require their own derivations. An empirically passing envelope is not automatically a proven worst-case bound.

Numeric constants have categories: physical measurement, mathematical derivation, algorithm choice, user preference, measured device constraint, or provisional product target. Algorithm constants are allowed, but labeled and preregistered. Never invent a universal target FPS, contact penetration or perceptual threshold just to fill a table. Existing frozen bounds remain frozen. New tasks first derive or ratify their fixture-specific values, then execute the implementation gate.

### Operator library required over time

This blueprint includes linear algebra, tensor calculus, differential geometry, weak forms, graph algorithms, topology, numerical PDEs, compatible discrete operators, sparse and matrix-free solvers, nonlinear optimization, automatic differentiation, adjoints, statistical inference, robust control, hybrid systems, sampling theory, information/uncertainty reasoning, distributed consistency and formal verification. They are tools selected by the physical question. Learning all terminology or implementing every solver family is not a deliverable.

## 4. Dependency order: many branches, a small integration spine

The full dependency graph is not one giant serial list. Physics branches can develop in isolated reference laboratories while the engine core is integrated. Each has to enter the common world through tested state, unit and exchange contracts.

| Milestone | Required capability evidence | Concrete demonstration | Stop condition |
|---|---|---|---|
| M00 — recoverable project | Current owners, exact source identity, protected scopes, preserved evidence | Restart any agent without losing ownership or using stale results | State recovered; no new simulation feature required |
| M01 — accepted GPU material state | Current surface/gamma gates, state ownership, runtime buffer path | GPU membrane reset/step/run/pause and state-linked rendering | Numerical, runtime and DYAD fields separately recorded |
| M02 — shape-memory material | Isotropic/orthotropic baseline, rest state, reference forces, GPU transcription | Stretch/shear a material sheet and release it | Declared load-response benchmarks and error domain pass |
| M03 — physical time and contact | Mass/inertia, time integrator, normal/frictional contact and energy ledger | Drop, support and manipulate an object | Contact, work and temporal convergence certified in scope |
| M04 — rigid cup with water | Closed volume semantics, incompressible transport, gravity, pressure, wall boundary | Fill a rigid cup, settle, move gently, tip and spill | Water mass and hydrostatic/traction tests pass separately from appearance |
| M05 — deformable cup | Elastic/bulk or shell choice, two-way pressure traction, contact | Compare declared compliant and stiff containers | Wall/fluid work exchange and deformation converge |
| M06 — embodied creature | Existing rig/gait knowledge, physical actuation, constraints and contact | Stand, enter motion, stop and recover from bounded perturbations | Stable controller and actuator/contact budgets, not just FK paths |
| M07 — multiphysics workshop | Heat/species/field ports and selected coupled laws | Warm a cup, bend a sheet, drive a simple mechanism | Each law and coupled exchange has independent evidence |
| M08 — persistent authored world | Objects/editor, save/reload, physical LOD and bounded content generation | Build a small world and revisit its consequences | State/resource conservation survives streaming and persistence |
| M09 — shared embodied world | Authority/replication, latency policy, XR/device capability, accessibility | Multiple users/agents inhabit a bounded scene | Shared-state and experience targets pass on declared hardware |
| M10 — autonomous creator | Grounded tools, memory, transactions, independent verification | Fresh agent creates a new small playable physical scenario | Reproducible build/test/runtime/DYAD with actual human review |
| M11 — expanding holodeck portfolio | Tested domain bridges, uncertainty, new devices and limited research questions | Add new classes of interaction without breaking earlier ones | Each expansion declares where realism and experience stop |

M04 does not wait for advanced fracture, chemistry or a fully deformable wood model. A rigid cup can establish fluid containment first. Surface tension matters at interfaces, especially small scales, but hydrostatic pressure, incompressibility, gravity, impermeable walls and reactions also matter. M06 can proceed in parallel with fluids once dynamics/contact are available. Advanced appearance, sound and authoring can advance independently while consuming the accepted state. Future domains do not all block a playable game.

### Candidate domain dependencies need refinement, not blind execution

The catalogue encodes a valid coarse DAG. A listed dependency is a minimum conceptual/contract dependency; it is not proof that the entire parent domain must be completed or that a single parent card is sufficient for all implementations. Some cards deliberately carry additional prerequisite review (for example cloth self-contact requires CON collision/contact work, and coupled multiphysics requires the relevant port contract). The planner emits proposals only. GLM must decompose cards, add actual implementation dependencies, recognize existing evidence and reserve scopes before execution.

No future card is marked certified merely to make the scheduler convenient. Reconcile already landed capabilities once at the relevant scope and device; attach references instead of re-deriving them. Active assignments above remain intact even if their roadmap parents are not yet formally reconciled.

## 5. How agents actually feed from the ledger

### Operational task record

Each active task must carry: stable ID; parent capability; title; inspected/base commit; phase and supported domain; owner; reviewer when assigned; exact read/write scopes; hard dependencies plus required evidence class; hardware/resource reservation; assumptions; statement/prediction/falsifier; frozen threshold source; deliverables; reproduction command; checkpoint; blockers; evidence references; publication head; limitations; and next useful action.

Execution states: `PROPOSED`, `READY`, `CLAIMED`, `RUNNING`, `BLOCKED`, `REVIEW`, `ACCEPTED`, `SUPERSEDED`, `RETIRED`. A long-running task is not blocked just because it is slow. Evidence classes are independent fields: source review, CPU numerical, software Vulkan, hardware Vulkan by device, integration/runtime, window, DYAD, human. Use `PASS`, `FAIL`, `NOT_TESTED`, `INCONCLUSIVE`, `CONDITIONAL`, or `NOT_APPLICABLE` with a reason. Do not collapse them to one misleading green label.

Only the coordinating publisher changes canonical ownership. Workers report checkpoints and write inside reserved paths. Read-only review at a pinned commit is parallel-safe; large hardware workloads still compete with rendering and the local eye. Reserve the RTX explicitly; use CPU/software paths for independent work until the slot is available. Do not infer GPU availability from low apparent utilization or an idle-looking window.

### Selection algorithm

1. Read the current Master control section and own active assignment. Continue it if useful work remains.
2. Verify exact checkout identity, recent publication and uncommitted work. Never assume a report's local path exists here.
3. If idle, consider only tasks whose actual required prerequisites are evidenced, whose write scopes do not overlap and whose necessary resources are available.
4. Prefer work that unlocks a current milestone, closes a known failure, produces an independent oracle, or resolves a high-consequence architectural uncertainty. Favor those over additional reports on already understood artifacts.
5. Estimate cost with uncertainty after a pilot. Do not allocate work by impressive model names or advertised token speed.
6. Reserve task and scopes through the coordinator; then execute the full loop without returning for every routine decision.
7. If one part blocks, finish independent authorized portions. If all useful paths block, report the exact blocker and next decision in a few sentences.
8. Submit a concrete reviewed handoff. GLM integrates in coherent commits and records actual evidence classes.

### The reusable autonomous packet

A generated packet must include the capability card plus this operating contract:

> Own this bounded milestone end to end. Inspect existing source/evidence before inventing replacements. Derive the selected law and numerical contracts; preregister falsifiers and algorithm choices; implement only your owned files; build, test, diagnose, fix and rerun affected gates. Keep independent numerical oracles. Do not substitute mocks for real execution. Preserve failures. For visible runtime changes, the runtime owner initializes DYAD and sends actual images with a physical briefing and technical questions, recording served identity and uncertainty. Publish through the sole coordinator. Stop only at the completed milestone or a concrete blocker after independent work is exhausted. Return code/evidence/commands/limits, not a list of unexecuted intentions.

Use the actual environment, capabilities and existing prompt scope. A generated packet is a reviewable proposal; it cannot authorize new installations, external actions, user-data use or physical devices. The included query tool never claims tasks or changes status.

### Bounded self-improvement of the book

Every substantive discovery produces one of: a test-backed correction; an additional dependency; a split task; a calibrated model; a narrowed claim; a new research proposal; or retirement of a redundant approach. Link the old and new records. Never erase a failed prediction or retune its historical threshold. New cards need an observable, a purpose, an owner category and a first useful experiment. A title such as 'quantum realism' is not actionable until decomposed.

Review milestones at integration boundaries, not after every minor file edit. The book should grow when knowledge grows and shrink its active frontier when repeated tasks stop adding evidence. Historical records stay available; the front page stays short enough for agents to recover context.

## 6. Three reusable verification ladders

### A physical-law ladder

1. Define domain, units, reference/current measures and supported parameters.
2. Derive independent analytic or manufactured controls.
3. Implement reference and derivative checks with step-size/error analysis.
4. Execute negative controls: wrong sign, ownership, unit, stale state and invalid input as relevant.
5. Freeze representative quantized inputs and independent expected values.
6. Transcribe per-kernel stages and isolate accumulation from local arithmetic.
7. Execute on each claimed device/backend; retain source, shader and artifact identity.
8. Integrate accepted state; test rejected trials, reset and terminal behavior.
9. Execute runtime/window/DYAD if visible; record uncertainty and human review separately.
10. Only then expand resolution, deformation domain, coupling or performance claims.

### A learned-model ladder

State whether the model predicts appearance, forces, parameters, motion, semantics or authored content. Build train/validation/test splits resistant to leakage, including held-out interventions. Separate aleatoric/model uncertainty, numerical error and hallucination. Check invariance, conservation or passivity where applicable. Record fallback and out-of-domain behavior. A learned view interpolator does not inherit the oracle's correctness or novel-light generality. A language model is not a physical measurement instrument simply because it can explain an equation.

### A human-experience ladder

Declare the actual device and audience, supported input/ability modes, target tasks, latency/framerate measurement method and visible/audible/haptic outcomes. Use runtime recordings and calibrated measures where possible. DYAD supplies observations, not Alan's taste or approval. Require real human review for product acceptance. Negative results may be a perception/viewpoint limitation rather than a failed physical computation; keep the causal hypothesis explicit.

## 7. Depth criteria: when a concept is actually included

A topic is covered at one of six depths: `INDEXED`, `DERIVED`, `REFERENCE_TESTED`, `DEVICE_TESTED`, `INTEGRATED`, `EXPERIENCE_REVIEWED`. This book initially indexes future concepts with specific tasks; it does not pretend every indexed concept is already mathematically solved. Store scope and evidence beside depth. 'Fluids integrated' is too broad; 'single-phase incompressible free surface in the tested density/viscosity range, on one device' is assessable.

An advanced capability counts when it has an implementable state/law, independent prediction, failure detection, coupling contract and a consumer that actually uses it. Architecture diagrams and fluent reports help organize work, but never replace those artifacts.

## 8. Scope and limits of 'human everything'

The scope includes natural phenomena, engineered objects, perception, languages, culture, institutions, work, play, environments and world-building tools. Human behavior models are abstractions with uncertain mechanisms; they cannot be certified the same way as a triangle gradient. Historical worlds distinguish evidence from invention. Digital twins require measured boundary conditions and domain-specific validation. Real people, voice and likeness require explicit provenance and appropriate permission in a shared creator product.

Smell, taste, force feedback and thermal sensation can be represented as world fields or metadata; delivering them to a person requires corresponding calibrated hardware and separate physical-device constraints. Software cannot manufacture unbounded force, matter or sensory bandwidth. Relativistic/quantum scenes and subjective consciousness belong to explicitly restricted research or fiction unless a specific observable can be tested. There is no present general law that reconstructs every nuance of human experience from triangle state.

Fidelity is allocated by physical consequence and user task, not only visibility. Coarse unseen water must still conserve the volume that later pours into view. A distant structure must retain forces/resources relevant to future interaction. Level-of-detail transitions are models with conservation/error contracts, not just triangle-count reduction. GPU arithmetic is one resource among bandwidth, memory, solver convergence, synchronization, CPU orchestration, device latency, authoring time and available calibration data.

## 9. Primary-source entry points

These are technical starting points consulted for this blueprint, not a claim that every task has already received a full literature review. Each implementation packet must cite the exact equations, API revision and assumptions it actually uses.

- [Khronos Vulkan specification and documentation](https://docs.vulkan.org/spec/latest/index.html): API/memory and feature contracts; use the actual device's supported revision.
- [MFEM finite-element concepts](https://mfem.org/fem/): weak forms, spaces, operators and boundary-condition terminology for the numerical continuum tasks.
- [Physically Based Rendering, fourth edition](https://pbr-book.org/4ed/contents): reference light transport, sampling, radiometry and imaging vocabulary. Existing Chimera appearance architecture remains the target; this is an oracle/research source, not a mandate to replace the renderer.
- [OpenMM theory documentation](https://docs.openmm.org/latest/userguide/theory.html): atomistic-model and integration entry points for the offline molecular bridge, not an in-engine atomistic promise.
- [Khronos OpenXR registry](https://registry.khronos.org/OpenXR/): actual XR API, spaces and conformance references when an XR task is activated.
- [OpenUSD introduction](https://openusd.org/release/intro.html): scene interchange/composition research; scene description does not by itself specify Chimera physical semantics.
- [FMI 3.0.2 specification](https://fmi-standard.org/docs/3.0.2/): co-simulation boundary vocabulary for future external solver integration, not authorization for a per-frame Python runtime.

Repository sources of record remain the inspected Master list, current law documents, tests, shader/host sources, frozen fixtures and their run evidence. Conflicts are resolved by concrete source and executed falsifiers, with the claim's date and scope preserved.

## 10. Capability catalogue

The following cards are generated from `docs/roadmap/holodeck_tasks.json`. All are **roadmap candidates**, not replacement assignments. The current active owner table remains authoritative until GLM reconciles these cards into the Master list.

Every card inherits: preserve branch/protected-path rules; inspect existing evidence before building; reserve owned paths before execution; derive/reregister fixture-specific numerical gates before code; no tolerance widening; retain failures; separate source/CPU/device/runtime/DYAD/human claims; and expose actual limits. The per-card prediction and falsifier add the phenomenon-specific obligation.

### GOV — Agent orchestration and scientific claims

Domain class: **engineering**. Candidate prerequisites: none; project-control entry point.

#### GOV-01 · Authoritative ledger and ownership

**Mathematics/concepts:** dependency DAG; transactions; compare-and-swap.

**Depends on:** none. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Canonical task IDs, claims, owners and publication queue.

**PREDICTION:** Conflicting claims are rejected and active assignments survive restart.

**FALSIFIER:** Two agents own the same write scope or stale state replaces a newer claim.

#### GOV-02 · Capability and evidence registry

**Mathematics/concepts:** typed states; proof obligations; epistemic uncertainty.

**Depends on:** GOV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Per-device and per-law support records with independent evidence classes.

**PREDICTION:** Missing runtime or DYAD evidence remains unknown regardless of unit-test success.

**FALSIFIER:** Any inferred capability is advertised as executed.

#### GOV-03 · Law and decision records

**Mathematics/concepts:** dimensional analysis; contracts; versioned assumptions.

**Depends on:** GOV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Energy, force, flux, boundary, domain and parameter records.

**PREDICTION:** Each admitted law names its domain, independent oracle and limitations.

**FALSIFIER:** A physical claim lacks a falsifier or a constant lacks an origin.

#### GOV-04 · Agent packet generation

**Mathematics/concepts:** topological scheduling; critical paths; resource constraints.

**Depends on:** GOV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Self-contained assignments from ready tasks and preserved active scopes.

**PREDICTION:** Packets include dependencies, actual evidence, write scope and finish criteria.

**FALSIFIER:** A blocked or already claimed task is silently reassigned.

#### GOV-05 · Crash recovery and publication

**Mathematics/concepts:** event sourcing; content addressing; idempotence.

**Depends on:** GOV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Recovery journal and serialized integration procedure.

**PREDICTION:** Replay reconstructs accepted task state without overwriting unpublished work.

**FALSIFIER:** Duplicate publication or orphaned ownership changes task truth.

#### GOV-06 · Discovery and roadmap evolution

**Mathematics/concepts:** requirements traceability; Bayesian decision reasoning.

**Depends on:** GOV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Append-only proposal, contradiction and supersession workflow.

**PREDICTION:** New concepts have parent requirements and explicit integration dependencies.

**FALSIFIER:** A speculative idea is promoted directly into a certified production claim.

### MATH — Mathematical language

Domain class: **engineering**. Candidate prerequisites: GOV-01.

#### MATH-01 · Units and coordinate algebra

**Mathematics/concepts:** SI dimensions; nondimensionalization; Buckingham Pi.

**Depends on:** GOV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Typed quantity/frame contract and reversible coordinate transforms.

**PREDICTION:** Unit and frame changes preserve dimensionless predictions.

**FALSIFIER:** A metre-newton comparison or undeclared world-unit conversion is admitted.

#### MATH-02 · Linear and tensor algebra

**Mathematics/concepts:** eigensystems; SVD; polar decomposition; Voigt conventions.

**Depends on:** GOV-01, MATH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Robust small-matrix primitives with conditioning diagnostics.

**PREDICTION:** Reconstruction and symmetry identities hold over the declared domain.

**FALSIFIER:** Silent singular inversion or inconsistent shear convention.

#### MATH-03 · Geometry of rotation

**Mathematics/concepts:** SO(3); SE(3); quaternions; Lie algebra.

**Depends on:** GOV-01, MATH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Rigid transform, tangent update and interpolation primitives.

**PREDICTION:** Group composition and finite-rotation invariants survive round trips.

**FALSIFIER:** Quaternion sign ambiguity creates physical jumps or transforms distort lengths.

#### MATH-04 · Variational calculus

**Mathematics/concepts:** weak forms; integration by parts; Euler-Lagrange equations.

**Depends on:** GOV-01, MATH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Derivation templates from energy or flux to discrete operators.

**PREDICTION:** Analytic forces agree with independent energy differentiation.

**FALSIFIER:** Boundary terms disappear without a physical boundary assumption.

#### MATH-05 · Discrete geometry and topology

**Mathematics/concepts:** manifolds; differential forms; exterior calculus; cohomology.

**Depends on:** GOV-01, MATH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Orientation, boundary and compatible differential-operator contracts.

**PREDICTION:** Discrete boundary-of-boundary is zero on valid complexes.

**FALSIFIER:** Topology or operator composition invents a source on a closed complex.

#### MATH-06 · Probability and inference

**Mathematics/concepts:** random variables; covariance; Bayesian inference; identifiability.

**Depends on:** GOV-01, MATH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Uncertainty, stochastic seed and calibration conventions.

**PREDICTION:** Intervals and coverage are evaluated on held-out known cases.

**FALSIFIER:** A fitted parameter is treated as identifiable without evidence.

### NUM — Numerical foundations

Domain class: **engineering**. Candidate prerequisites: MATH-01.

#### NUM-01 · Floating-point error contracts

**Mathematics/concepts:** unit roundoff; condition numbers; backward error; cancellation.

**Depends on:** MATH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Precision budgets by operation, degree, scale and reduction order.

**PREDICTION:** Independent error envelopes predict measured numerical behavior.

**FALSIFIER:** A small-mesh tolerance is reused at arbitrary degree or scale.

#### NUM-02 · Sparse linear solvers

**Mathematics/concepts:** CG; MINRES; GMRES; preconditioning; multigrid.

**Depends on:** MATH-01, NUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Solver selection by operator class with residual and work records.

**PREDICTION:** Manufactured solutions meet residual and solution-error criteria.

**FALSIFIER:** A small residual is used to hide an ill-conditioned wrong solution.

#### NUM-03 · Nonlinear and constrained solvers

**Mathematics/concepts:** Newton; line search; trust regions; KKT; complementarity.

**Depends on:** MATH-01, NUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Energy/constraint solvers with explicit unsuccessful termination.

**PREDICTION:** Accepted steps obey the declared decrease or constraint criteria.

**FALSIFIER:** Stalling or exhausted work is labeled equilibrium.

#### NUM-04 · Differentiation and adjoints

**Mathematics/concepts:** automatic differentiation; finite differences; reverse mode.

**Depends on:** MATH-01, NUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Gradient and Jacobian-vector verification bench.

**PREDICTION:** Independent directional checks survive scale and step-size sweeps.

**FALSIFIER:** A reference and implementation share the same derivative bug unnoticed.

#### NUM-05 · Time integration

**Mathematics/concepts:** symplectic methods; implicit methods; BDF; IMEX; splitting.

**Depends on:** MATH-01, NUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Integrator contracts for conservative, damped and stiff systems.

**PREDICTION:** Order studies and energy behavior match each method's stated properties.

**FALSIFIER:** Optimization steps are relabeled physical time or instability hidden by damping.

#### NUM-06 · Adaptive error control

**Mathematics/concepts:** a posteriori estimates; Richardson studies; multirate stepping.

**Depends on:** MATH-01, NUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Space/time refinement policy with observable-specific budgets.

**PREDICTION:** Refinement reduces estimated and measured error on representative problems.

**FALSIFIER:** A timestep or mesh adaptation creates unaccounted mass or energy.

### GEO — Triangle substrate and geometry

Domain class: **engineering**. Candidate prerequisites: MATH-01, NUM-01.

#### GEO-01 · Oriented triangle complex

**Mathematics/concepts:** half-edge topology; adjacency; boundary orientation.

**Depends on:** MATH-01, NUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Persistent triangle/vertex IDs and valid manifold/boundary classification.

**PREDICTION:** Permutations preserve geometry and intentional openings remain open.

**FALSIFIER:** Repair closes a real opening or loses connectivity ownership.

#### GEO-02 · Spatial acceleration

**Mathematics/concepts:** BVH; Morton ordering; sparse grids; neighborhood search.

**Depends on:** MATH-01, NUM-01, GEO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Query structures tied to actual state epochs.

**PREDICTION:** Exact small-scene queries agree with brute force.

**FALSIFIER:** A stale acceleration structure misses an interaction.

#### GEO-03 · Volume and interior meaning

**Mathematics/concepts:** winding numbers; tetrahedralization; signed distance; boundary integrals.

**Depends on:** MATH-01, NUM-01, GEO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Explicit inside/outside and support-field proposal beneath triangle interfaces.

**PREDICTION:** Closed-volume estimates converge and open surfaces are distinguished.

**FALSIFIER:** Area alone is used to infer arbitrary mass or interior pressure.

#### GEO-04 · Remeshing and conservative transfer

**Mathematics/concepts:** edge split/collapse; quadrature; conservative projection.

**Depends on:** MATH-01, NUM-01, GEO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Adaptive mesh edits preserving material/history fields.

**PREDICTION:** Transfer preserves declared mass, momentum and material orientation budgets.

**FALSIFIER:** Refinement creates matter or resets accumulated strain silently.

#### GEO-05 · Triangle/Gaussian interpretation

**Mathematics/concepts:** surface covariance; moments; reconstruction; occlusion.

**Depends on:** MATH-01, NUM-01, GEO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Audited geometric moment map and appearance-only surrogate limits.

**PREDICTION:** Moment predictions match independent integration in the tested domain.

**FALSIFIER:** Moment matching is mistaken for exact collision or light equivalence.

#### GEO-06 · Precision across world scales

**Mathematics/concepts:** local frames; origin rebasing; quantized coordinates.

**Depends on:** MATH-01, NUM-01, GEO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Large-world/local-detail coordinate bridge.

**PREDICTION:** Relative contacts and constraints survive rebasing within budget.

**FALSIFIER:** Rebasing changes local momentum, contact or visible position unexpectedly.

### MAT — Material admission and calibration

Domain class: **engineering**. Candidate prerequisites: MATH-01, GOV-03.

#### MAT-01 · Typed material properties

**Mathematics/concepts:** dimensions; reference conditions; immutable snapshots.

**Depends on:** MATH-01, GOV-03. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Admitted parameter records distinct from raw data.

**PREDICTION:** Invalid units, nonfinite values and missing basis refuse at the real caller.

**FALSIFIER:** A legacy bypass reaches a calculation advertised as validated.

#### MAT-02 · Constitutive capability matrix

**Mathematics/concepts:** isotropy; orthotropy; state variables; model domains.

**Depends on:** MATH-01, GOV-03, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Explicit supported model and required-parameter registry.

**PREDICTION:** Missing inputs prevent unsupported capability claims.

**FALSIFIER:** Density and one modulus are assumed sufficient for every response.

#### MAT-03 · Measured-data import

**Mathematics/concepts:** uncertainty propagation; citations; interpolation.

**Depends on:** MATH-01, GOV-03, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Versioned datasets with temperature, moisture and strain-rate conditions.

**PREDICTION:** Imports retain source identity and reject missing physical context.

**FALSIFIER:** Provenance membership is represented as proof of authentic measurement.

#### MAT-04 · Parameter identification

**Mathematics/concepts:** inverse problems; sensitivity; experimental design.

**Depends on:** MATH-01, GOV-03, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Calibration tools with confidence and parameter-correlation outputs.

**PREDICTION:** Held-out experiments agree within declared predictive uncertainty.

**FALSIFIER:** Training-fit success is called predictive material validation.

#### MAT-05 · Synthetic materials and authorship

**Mathematics/concepts:** admissible domains; nondimensional controls.

**Depends on:** MATH-01, GOV-03, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Synthetic presets clearly separated from calibrated materials.

**PREDICTION:** Authoring remains in supported domains or gives explicit refusals.

**FALSIFIER:** A fictional preset is presented as measured wood, metal or water.

#### MAT-06 · CPU-to-GPU representation

**Mathematics/concepts:** quantization; overflow; underflow; packing.

**Depends on:** MATH-01, GOV-03, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Validated upload conversion and immutable parameter epoch.

**PREDICTION:** Converted values and units meet the actual device representation contract.

**FALSIFIER:** Finite float64 silently becomes infinity or zero at upload.

### GPU — GPU execution foundation

Domain class: **engineering**. Candidate prerequisites: NUM-01, GEO-01.

#### GPU-01 · Accepted state ownership

**Mathematics/concepts:** double buffering; state epochs; immutable publication.

**Depends on:** NUM-01, GEO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Compute/render ownership contract with accepted/trial separation.

**PREDICTION:** Rendered buffers contain only the recorded accepted state.

**FALSIFIER:** Rejected, partial or stale trial data reaches a frame.

#### GPU-02 · Synchronization and lifetime

**Mathematics/concepts:** Vulkan memory model; stages; access masks; fences.

**Depends on:** NUM-01, GEO-01, GPU-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Minimal barriers and lifetime proofs for actual consumers.

**PREDICTION:** Validation and adversarial traces detect missing visibility or early reuse.

**FALSIFIER:** A submission is treated as completion or memory is reused while referenced.

#### GPU-03 · Deterministic assembly and reductions

**Mathematics/concepts:** CSR gather; tree reductions; floating-point ordering.

**Depends on:** NUM-01, GEO-01, GPU-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Versioned reduction plans with degree-specific bounds.

**PREDICTION:** Independent references validate each stage at matching input bytes.

**FALSIFIER:** A changed sum order silently inherits a serial-order error budget.

#### GPU-04 · Device portability

**Mathematics/concepts:** feature negotiation; SPIR-V; alignment; workgroup limits.

**Depends on:** NUM-01, GEO-01, GPU-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Capability-driven compiled kernels and explicit refusal/fallback paths.

**PREDICTION:** Every supported device path executes its own numerical gate.

**FALSIFIER:** CUDA presence is mistaken for Vulkan support or fallback is mislabeled hardware.

#### GPU-05 · Persistent runtime execution

**Mathematics/concepts:** dispatch graphs; buffer pools; GPU compaction.

**Depends on:** NUM-01, GEO-01, GPU-01, GPU-02, GPU-03. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded runtime loop without Python per-frame simulation.

**PREDICTION:** Repeated updates preserve ownership while avoiding repeated setup.

**FALSIFIER:** Hidden host simulation or HTTP mesh animation substitutes for the runtime.

#### GPU-06 · Failure containment

**Mathematics/concepts:** device loss; allocation failure; invalid-state quarantine.

**Depends on:** NUM-01, GEO-01, GPU-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Recoverable run-state and last-accepted-state policy.

**PREDICTION:** Fault injection preserves evidence and prevents invalid publication.

**FALSIFIER:** Device failure produces a success verdict or corrupted restored state.

### SUR — Surface and interface energy

Domain class: **engineering**. Candidate prerequisites: MAT-01, GEO-01, NUM-01.

#### SUR-01 · Constant-gamma interface law

**Mathematics/concepts:** area gradients; virtual work; pinned boundaries.

**Depends on:** MAT-01, GEO-01, NUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Reuse and extend current CPU/GPU law with exact input identity.

**PREDICTION:** Analytic, finite-difference and compiled results meet existing budgets.

**FALSIFIER:** Wrong sign, corner ownership or gamma controls escape detection.

#### SUR-02 · Variable interface energy

**Mathematics/concepts:** surface gradients; Marangoni traction; material advection.

**Depends on:** MAT-01, GEO-01, NUM-01, SUR-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Derived spatial/material gamma law with clear independent fields.

**PREDICTION:** Uniform gamma recovers the certified baseline and gradient controls agree.

**FALSIFIER:** Per-face scalar variation is claimed to model all tangential interface physics.

#### SUR-03 · Curvature and capillarity

**Mathematics/concepts:** mean curvature; Laplace pressure; variational shape forces.

**Depends on:** MAT-01, GEO-01, NUM-01, SUR-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Pressure/interface equilibrium benchmark.

**PREDICTION:** Sphere/drop equilibria converge under the declared curvature convention.

**FALSIFIER:** Curvature sign or factor errors remain after refinement.

#### SUR-04 · Wetting and contact lines

**Mathematics/concepts:** Young balance; adhesion; hysteresis; boundary energy.

**Depends on:** MAT-01, GEO-01, NUM-01, SUR-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Contact-angle law with declared substrate and resolution effects.

**PREDICTION:** Equilibrium contact angle approaches the independent prediction.

**FALSIFIER:** Apparent pixel angle alone certifies microscopic wetting physics.

#### SUR-05 · Interface transport

**Mathematics/concepts:** surface diffusion; surfactant conservation; adsorption.

**Depends on:** MAT-01, GEO-01, NUM-01, SUR-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Conservative interface species/energy transport.

**PREDICTION:** Closed-system species accounting closes across moving triangles.

**FALSIFIER:** Remeshing or motion creates interface concentration.

#### SUR-06 · Topology-changing interfaces

**Mathematics/concepts:** coalescence; breakup; minimum feature scales.

**Depends on:** MAT-01, GEO-01, NUM-01, SUR-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Restricted interface event model with mass/energy accounting.

**PREDICTION:** Declared split/merge events conserve the specified quantities.

**FALSIFIER:** Topology surgery silently changes volume or available surface energy.

### ELA — Elastic surface foundation

Domain class: **engineering**. Candidate prerequisites: SUR-01, MAT-01.

#### ELA-01 · Rest metric and deformation

**Mathematics/concepts:** deformation gradient; reference area; objectivity.

**Depends on:** SUR-01, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Rest/current geometry and material-frame reference.

**PREDICTION:** Rigid transforms preserve energy and force expectations.

**FALSIFIER:** Finite rotation creates artificial strain.

#### ELA-02 · Isotropic stretching and shear

**Mathematics/concepts:** plane stress; hyperelastic energy; stable domains.

**Depends on:** SUR-01, MAT-01, ELA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One selected elastic sheet law and analytic forces.

**PREDICTION:** Extension, shear and independent gradient tests agree.

**FALSIFIER:** Area minimization is used as a substitute for shear resistance.

#### ELA-03 · Orthotropic elasticity

**Mathematics/concepts:** material axes; reciprocal compliance; positive definiteness.

**Depends on:** SUR-01, MAT-01, ELA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Direction-dependent sheet response with stated shear convention.

**PREDICTION:** Axis rotations and isotropic limit reproduce analytic controls.

**FALSIFIER:** An arbitrary SPD matrix is mislabeled orthotropic.

#### ELA-04 · Thickness and prestress

**Mathematics/concepts:** reference-volume energy; membrane resultants; residual stress.

**Depends on:** SUR-01, MAT-01, ELA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Explicit thickness/prestress treatment and surface-energy combination.

**PREDICTION:** Parameter scaling follows the chosen constitutive derivation.

**FALSIFIER:** Thickness is counted twice or surface tension double-counts prestress.

#### ELA-05 · Elastic patch verification

**Mathematics/concepts:** affine patch tests; mesh convergence; force/torque balance.

**Depends on:** SUR-01, MAT-01, ELA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Frozen mixed-triangulation connected patches.

**PREDICTION:** Independent patch/reference predictions meet derived bounds.

**FALSIFIER:** Only a single-element self-consistency check supports acceptance.

#### ELA-06 · GPU elastic transcription

**Mathematics/concepts:** matrix kernels; tangent conditioning; reference storage.

**Depends on:** SUR-01, MAT-01, ELA-01, GPU-03, ELA-05. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** GPU law and fixtures at exactly quantized inputs.

**PREDICTION:** Stage-wise forces/energies pass before runtime or visual claims.

**FALSIFIER:** A visually plausible deformation masks failed constitutive gates.

### SHE — Shells cloth and bending

Domain class: **engineering**. Candidate prerequisites: ELA-01.

#### SHE-01 · Discrete bending

**Mathematics/concepts:** dihedral energies; rest curvature; Kirchhoff-Love shells.

**Depends on:** ELA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One justified bending law with boundary conditions.

**PREDICTION:** Bending patches approach an independent small-deformation reference.

**FALSIFIER:** Triangle subdivision changes stiffness without a documented limit.

#### SHE-02 · Thin-shell locking

**Mathematics/concepts:** membrane/shear locking; mixed interpolation.

**Depends on:** ELA-01, SHE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Thickness/refinement conditioning study.

**PREDICTION:** Thin limits remain controlled within the selected discretization domain.

**FALSIFIER:** Artificial stiffness is hidden by material retuning.

#### SHE-03 · Cloth contact and self-contact

**Mathematics/concepts:** shell thickness; CCD; friction.

**Depends on:** ELA-01, SHE-01, CON-02, CON-03, CON-04. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Wrinkle/fold bench coupled to validated contact.

**PREDICTION:** Nonpenetration and energy ledger hold under folds.

**FALSIFIER:** Visual overlap substitutes for collision detection.

#### SHE-04 · Layered and composite shells

**Mathematics/concepts:** laminate tensors; neutral axis; bending-extension coupling.

**Depends on:** ELA-01, SHE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Layered material and orientation contract.

**PREDICTION:** Independent laminate controls reproduce coupling direction and scale.

**FALSIFIER:** Layer ordering or tensor transport reverses mechanical response.

#### SHE-05 · Buckling and instability

**Mathematics/concepts:** eigenmodes; bifurcation; imperfections.

**Depends on:** ELA-01, SHE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Load-path and imperfection-sensitive shell benchmark.

**PREDICTION:** Critical-load trends agree with controlled references.

**FALSIFIER:** A single solver branch is advertised as the unique physical result.

#### SHE-06 · Tearing and seam mechanics

**Mathematics/concepts:** cohesive energy; topology edits; fracture budget.

**Depends on:** ELA-01, SHE-01, GEO-04, SOL-05. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Declared seam/tear model with conservative transfer.

**PREDICTION:** Failure thresholds and energy expenditure are accounted.

**FALSIFIER:** Edges disappear without a crack law or material history.

### SOL — Bulk solids and irreversible matter

Domain class: **engineering**. Candidate prerequisites: ELA-01, GEO-03.

#### SOL-01 · Interior discretization decision

**Mathematics/concepts:** FEM; finite volume; MPM; meshfree coupling.

**Depends on:** ELA-01, GEO-03. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Compare support representations beneath triangle boundaries.

**PREDICTION:** Selected representation passes volumetric and interface benchmarks.

**FALSIFIER:** A surface-only metric is claimed to resolve arbitrary bulk stress.

#### SOL-02 · Finite-strain solids

**Mathematics/concepts:** hyperelasticity; Jacobian determinant; volumetric modes.

**Depends on:** ELA-01, GEO-03, SOL-01, MAT-02, NUM-03. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Compressible bulk baseline with inversion domain.

**PREDICTION:** Hydrostatic and deviatoric controls separate correctly.

**FALSIFIER:** Pressure and shear are coupled by an accidental parameter shortcut.

#### SOL-03 · Near incompressibility

**Mathematics/concepts:** mixed displacement-pressure; inf-sup; locking.

**Depends on:** ELA-01, GEO-03, SOL-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Stable constrained-volume solver.

**PREDICTION:** Volume and pressure converge without artificial locking.

**FALSIFIER:** Increasing bulk modulus merely freezes the simulation.

#### SOL-04 · Plasticity and viscoelasticity

**Mathematics/concepts:** yield surfaces; return mapping; internal variables.

**Depends on:** ELA-01, GEO-03, SOL-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One bounded irreversible law with dissipation ledger.

**PREDICTION:** Loading-unloading and rate controls reproduce stated hysteresis.

**FALSIFIER:** Negative dissipation or erased history is accepted.

#### SOL-05 · Fracture fatigue and damage

**Mathematics/concepts:** cohesive zones; phase fields; cycle accumulation.

**Depends on:** ELA-01, GEO-03, SOL-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Restricted damage model with mesh-objectivity study.

**PREDICTION:** Energy and crack response converge within declared regularization.

**FALSIFIER:** Element size determines strength without disclosure.

#### SOL-06 · Granular and porous solids

**Mathematics/concepts:** contact networks; frictional yield; Darcy/Biot coupling.

**Depends on:** ELA-01, GEO-03, SOL-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Sand/soil/porous benchmark with state-dependent closures.

**PREDICTION:** Packing and drainage experiments meet independent balances.

**FALSIFIER:** Granular flow is approximated as a universal elastic sheet.

### DYN — Time mass mechanics and gravity

Domain class: **engineering**. Candidate prerequisites: NUM-05, MAT-01.

#### DYN-01 · Mass momentum and inertia

**Mathematics/concepts:** quadrature; density; surface/bulk mass; inertia tensors.

**Depends on:** NUM-05, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Mass assignment contract for each supported representation.

**PREDICTION:** Total mass and rigid-body inertia match independent integration.

**FALSIFIER:** Triangle area implies undeclared volume or mass.

#### DYN-02 · Rigid and articulated dynamics

**Mathematics/concepts:** Newton-Euler; Lagrangian mechanics; spatial algebra.

**Depends on:** NUM-05, MAT-01, DYN-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bodies/joints with declared constraints and inertial parameters.

**PREDICTION:** Free fall, pendulum and torque-response controls converge.

**FALSIFIER:** FK motion is mislabeled force-driven dynamics.

#### DYN-03 · Conservative time evolution

**Mathematics/concepts:** Hamiltonian structure; symplectic methods.

**Depends on:** NUM-05, MAT-01, DYN-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Time-stepping bench with external work ledger.

**PREDICTION:** Conservative test energy error behaves as the method predicts.

**FALSIFIER:** Unbounded energy creation is hidden by visual smoothness.

#### DYN-04 · Damping and dissipation

**Mathematics/concepts:** Rayleigh damping; constitutive viscosity; dissipation potentials.

**Depends on:** NUM-05, MAT-01, DYN-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Separate physical damping from solver stabilization.

**PREDICTION:** Damped oscillator and work balances distinguish each contribution.

**FALSIFIER:** Numerical damping is reported as measured material loss.

#### DYN-05 · Gravity and long-range fields

**Mathematics/concepts:** uniform gravity; Poisson; Barnes-Hut; multipole expansions.

**Depends on:** NUM-05, MAT-01, DYN-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Gravity kernel with opening/error and unit contracts.

**PREDICTION:** Small-system direct sums bound approximation errors.

**FALSIFIER:** A gravity acceleration kernel is treated as a universal constitutive law.

#### DYN-06 · Events and multirate stepping

**Mathematics/concepts:** event localization; impulse matching; asynchronous time.

**Depends on:** NUM-05, MAT-01, DYN-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Coupled fast/slow dynamics and event timing protocol.

**PREDICTION:** Impacts and exchanges preserve the declared impulse/work balance.

**FALSIFIER:** Substep boundaries create or lose unaccounted momentum.

### CON — Collision friction and contact

Domain class: **engineering**. Candidate prerequisites: GEO-02, DYN-01.

#### CON-01 · Collision geometry

**Mathematics/concepts:** broadphase; narrowphase; robust predicates.

**Depends on:** GEO-02, DYN-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Triangle/rigid interaction primitives with state identity.

**PREDICTION:** Brute-force controls expose missed and false contacts.

**FALSIFIER:** Acceleration culling misses a valid contact.

#### CON-02 · Continuous collision detection

**Mathematics/concepts:** time of impact; conservative advancement.

**Depends on:** GEO-02, DYN-01, CON-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** High-speed thin-feature tests.

**PREDICTION:** Swept trajectories do not tunnel within declared bounds.

**FALSIFIER:** Endpoint overlap tests certify all continuous motion.

#### CON-03 · Normal contact

**Mathematics/concepts:** complementarity; barrier methods; penalty conditioning.

**Depends on:** GEO-02, DYN-01, CON-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One justified normal-contact solver.

**PREDICTION:** Nonpenetration and load balance hold in declared tolerances.

**FALSIFIER:** Arbitrary penalty stiffness is called exact contact.

#### CON-04 · Friction and adhesion

**Mathematics/concepts:** Coulomb cones; stick-slip; rolling resistance.

**Depends on:** GEO-02, DYN-01, CON-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Tangential law with energy and frame contracts.

**PREDICTION:** Incline/slide controls reproduce stick-slip and dissipation.

**FALSIFIER:** Friction adds net energy or depends on world-axis orientation.

#### CON-05 · Rigid deformable coupling

**Mathematics/concepts:** action-reaction; impulse transfer; constraint work.

**Depends on:** GEO-02, DYN-01, CON-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Two-way solid/shell interaction.

**PREDICTION:** Momentum and work agree across the representation interface.

**FALSIFIER:** Only the visually smaller object receives the reaction.

#### CON-06 · Resting contact stacks

**Mathematics/concepts:** stabilization; warm starts; contact persistence.

**Depends on:** GEO-02, DYN-01, CON-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Long-duration stacks and resting mechanisms.

**PREDICTION:** Drift and energy remain inside preregistered budgets.

**FALSIFIER:** A short still image certifies long-term support stability.

### FLU — Liquids gases and volume transport

Domain class: **engineering**. Candidate prerequisites: DYN-01, GEO-03.

#### FLU-01 · Fluid representation choice

**Mathematics/concepts:** finite volume; grid-particle; SPH; MPM; free surfaces.

**Depends on:** DYN-01, GEO-03. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Comparative small benchmarks and triangle-interface contract.

**PREDICTION:** Chosen domain supports its claimed flow and topology cases.

**FALSIFIER:** A height column is claimed to model overturning water or enclosed cavities.

#### FLU-02 · Incompressible flow

**Mathematics/concepts:** Navier-Stokes; pressure projection; inf-sup; viscosity.

**Depends on:** DYN-01, GEO-03, FLU-01, NUM-02, NUM-05. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Conservative momentum/pressure baseline.

**PREDICTION:** Manufactured flow and volume balances converge.

**FALSIFIER:** Low divergence alone hides incorrect velocity or pressure.

#### FLU-03 · Free-surface transport

**Mathematics/concepts:** VOF; level sets; particle transfers; reconstruction.

**Depends on:** DYN-01, GEO-03, FLU-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Mass-controlled moving interface tied to visible triangles.

**PREDICTION:** Advection and deformation preserve declared volume budgets.

**FALSIFIER:** Reconstructed surface volume drifts without accounting.

#### FLU-04 · Surface-force coupling

**Mathematics/concepts:** capillary stress; balanced-force schemes; parasitic currents.

**Depends on:** DYN-01, GEO-03, FLU-01, SUR-03, FLU-02, FLU-03. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Couple certified interface law to pressure.

**PREDICTION:** Static drop pressure/shape balances converge with small spurious currents.

**FALSIFIER:** Surface force and pressure generate unexplained motion at equilibrium.

#### FLU-05 · Fluid-solid interaction

**Mathematics/concepts:** moving boundaries; pressure traction; displaced volume.

**Depends on:** DYN-01, GEO-03, FLU-01, FLU-02, FLU-03, CON-03, MULTI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Two-way cup/water coupling.

**PREDICTION:** Pressure load and wall reaction obey independent balances.

**FALSIFIER:** Watertight appearance is mistaken for impermeability.

#### FLU-06 · Compressible and multiphase flow

**Mathematics/concepts:** equations of state; Riemann fluxes; Mach regimes.

**Depends on:** DYN-01, GEO-03, FLU-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded gas/bubble model and interface exchanges.

**PREDICTION:** Acoustic/shock or bubble references match within declared domain.

**FALSIFIER:** One incompressible closure is silently used across all regimes.

### THM — Heat phase change and thermodynamics

Domain class: **engineering**. Candidate prerequisites: MAT-01, NUM-02.

#### THM-01 · Thermal state and heat capacity

**Mathematics/concepts:** internal energy; temperature; reference enthalpy.

**Depends on:** MAT-01, NUM-02. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Material thermal-state contract.

**PREDICTION:** Heating/cooling matches independent energy accounting.

**FALSIFIER:** Temperature is changed without a heat source or energy exchange.

#### THM-02 · Heat conduction

**Mathematics/concepts:** Fourier flux; anisotropic diffusion; boundary flux.

**Depends on:** MAT-01, NUM-02, THM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Surface/bulk compatible heat operator.

**PREDICTION:** Manufactured diffusion and insulated-domain energy tests converge.

**FALSIFIER:** Mesh orientation changes isotropic conductivity.

#### THM-03 · Thermomechanical coupling

**Mathematics/concepts:** thermal expansion; thermoelastic energy; work heat split.

**Depends on:** MAT-01, NUM-02, THM-01, ELA-02, MULTI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Coupled temperature/strain model.

**PREDICTION:** Constrained/free expansion and energy balance agree.

**FALSIFIER:** Heat expansion creates mechanical work without energy accounting.

#### THM-04 · Phase change

**Mathematics/concepts:** latent heat; enthalpy methods; moving fronts.

**Depends on:** MAT-01, NUM-02, THM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One melting/freezing benchmark with phase fractions.

**PREDICTION:** Latent-heat and front-position balances close.

**FALSIFIER:** Material identity flips without latent energy.

#### THM-05 · Convection and radiation

**Mathematics/concepts:** advection diffusion; emissivity; radiative exchange.

**Depends on:** MAT-01, NUM-02, THM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Thermal boundary and transport coupling.

**PREDICTION:** Canonical heat-transfer controls match declared approximations.

**FALSIFIER:** Visible brightness is confused with absolute thermal power.

#### THM-06 · Entropy and constitutive admissibility

**Mathematics/concepts:** Clausius-Duhem; dissipation inequalities.

**Depends on:** MAT-01, NUM-02, THM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Sign and domain audit for coupled laws.

**PREDICTION:** Closed irreversible processes respect declared entropy production.

**FALSIFIER:** Thermal/mechanical coupling allows unmodeled perpetual energy gain.

### CHM — Chemistry and material transformation

Domain class: **research**. Candidate prerequisites: THM-01, MAT-01.

#### CHM-01 · Species and reactions

**Mathematics/concepts:** stoichiometric matrices; elemental balances; kinetics.

**Depends on:** THM-01, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Restricted species/reaction network with units.

**PREDICTION:** Element inventory and nonnegative concentrations are preserved.

**FALSIFIER:** A reaction creates elements or negative species without refusal.

#### CHM-02 · Transport and mixing

**Mathematics/concepts:** advection diffusion; chemical potentials; diffusion tensors.

**Depends on:** THM-01, MAT-01, CHM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Conservative concentration fields on support meshes.

**PREDICTION:** Diffusion/advection controls converge and species budgets close.

**FALSIFIER:** Visual color blending is claimed as molecular diffusion.

#### CHM-03 · Reaction thermodynamics

**Mathematics/concepts:** Gibbs energy; equilibria; detailed balance.

**Depends on:** THM-01, MAT-01, CHM-01, THM-06. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Consistent thermal/chemical parameter and equilibrium contract.

**PREDICTION:** Closed-box equilibria and energy match stated references.

**FALSIFIER:** Arbitrary forward/reverse rates imply contradictory equilibria.

#### CHM-04 · Reactive materials

**Mathematics/concepts:** oxidation; corrosion; curing; phase-dependent properties.

**Depends on:** THM-01, MAT-01, CHM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One narrow material-transformation demonstrator.

**PREDICTION:** Measured/synthetic rate assumptions predict held-out controls.

**FALSIFIER:** A generic decay timer is presented as validated chemistry.

#### CHM-05 · Atmospheric combustion abstraction

**Mathematics/concepts:** reaction progress; heat release; transport.

**Depends on:** THM-01, MAT-01, CHM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Clearly bounded visual/engineering combustion model.

**PREDICTION:** Energy/species balances hold in its declared regime.

**FALSIFIER:** A visually credible flame is called full predictive combustion.

#### CHM-06 · Molecular and quantum bridge

**Mathematics/concepts:** molecular potentials; statistical mechanics; coarse graining.

**Depends on:** THM-01, MAT-01, CHM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Offline parameter derivation/uncertainty research interface.

**PREDICTION:** Derived macroscopic parameters predict a separate calibration set.

**FALSIFIER:** An atomistic calculation is advertised as universal real-time chemistry.

### EM — Electric magnetic and field systems

Domain class: **research**. Candidate prerequisites: NUM-02, MAT-01.

#### EM-01 · Circuits and networks

**Mathematics/concepts:** Kirchhoff laws; modified nodal analysis; DAEs.

**Depends on:** NUM-02, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Lumped circuit components with energy accounting.

**PREDICTION:** RC/RLC and source/load controls match analytic results.

**FALSIFIER:** A circuit component produces unaccounted power.

#### EM-02 · Electrostatics and magnetostatics

**Mathematics/concepts:** Poisson; gauge; boundary conditions.

**Depends on:** NUM-02, MAT-01, EM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One field solver with material domains.

**PREDICTION:** Canonical field and force solutions converge.

**FALSIFIER:** Field boundary conditions or gauge freedoms are silently mishandled.

#### EM-03 · Electromechanical coupling

**Mathematics/concepts:** Maxwell stress; magnetic energy; virtual work.

**Depends on:** NUM-02, MAT-01, EM-01, MULTI-01, DYN-02. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Restricted actuator/sensor coupling.

**PREDICTION:** Mechanical work and electrical energy balance.

**FALSIFIER:** Field force lacks a reciprocal energy effect.

#### EM-04 · Wave electromagnetics

**Mathematics/concepts:** Maxwell equations; compatible curl operators; CFL.

**Depends on:** NUM-02, MAT-01, EM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Research FDTD/FEM benchmark and feasible runtime domain.

**PREDICTION:** Wave propagation and boundary reflection meet references.

**FALSIFIER:** Geometric optics is claimed to resolve arbitrary wave interference.

#### EM-05 · Conductive and thermal coupling

**Mathematics/concepts:** Ohmic loss; Joule heating; temperature coefficients.

**Depends on:** NUM-02, MAT-01, EM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Circuit/heat transfer coupling.

**PREDICTION:** Electrical loss equals deposited heat within balance budget.

**FALSIFIER:** The same power is both retained and dissipated.

#### EM-06 · Sensors and communication fields

**Mathematics/concepts:** signal propagation; noise; bandwidth; transducers.

**Depends on:** NUM-02, MAT-01, EM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Declared sensor/channel abstractions linked to world state.

**PREDICTION:** Known signals recover stated gain, delay and uncertainty.

**FALSIFIER:** A virtual sensor sees hidden perfect state while claiming realism.

### LGT — Light appearance and imaging

Domain class: **engineering**. Candidate prerequisites: GEO-01, MAT-01.

#### LGT-01 · Radiometry and color

**Mathematics/concepts:** spectra; radiance; irradiance; linear color; tone mapping.

**Depends on:** GEO-01, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Calibrated light/material/camera unit path.

**PREDICTION:** Radiometric controls survive unit and exposure changes.

**FALSIFIER:** Display RGB is used as conserved physical energy.

#### LGT-02 · Reference light transport

**Mathematics/concepts:** rendering equation; Monte Carlo; MIS; BSDFs.

**Depends on:** GEO-01, MAT-01, LGT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Offline reference oracle for surface appearance.

**PREDICTION:** Energy/reciprocity controls and convergence studies pass.

**FALSIFIER:** An attractive image substitutes for transport validation.

#### LGT-03 · Triangle-surface light representation

**Mathematics/concepts:** 2D surfels; Gaussian moments; view/light conditioning.

**Depends on:** GEO-01, MAT-01, LGT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Existing triangle-bound appearance representation with uncertainty.

**PREDICTION:** Held-out lighting and geometry edits expose generalization limits.

**FALSIFIER:** Novel view success alone certifies relighting.

#### LGT-04 · Occlusion and reflection consistency

**Mathematics/concepts:** visibility; normals; BRDF transport; mirror geometry.

**Depends on:** GEO-01, MAT-01, LGT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Coherent silhouettes/shadows/reflections from accepted geometry.

**PREDICTION:** Geometry perturbations update all relevant visibility paths.

**FALSIFIER:** Rendering uses an untracked second physical shape.

#### LGT-05 · Volume and spectral appearance

**Mathematics/concepts:** participating media; scattering; refraction; absorption.

**Depends on:** GEO-01, MAT-01, LGT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Declared fog/water/skin optical approximations.

**PREDICTION:** Reference paths bound bias over the supported regime.

**FALSIFIER:** Transparent appearance is treated as a fluid or bulk physical model.

#### LGT-06 · Temporal and perceptual rendering

**Mathematics/concepts:** sampling; anti-aliasing; temporal reconstruction; uncertainty.

**Depends on:** GEO-01, MAT-01, LGT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Artifact tests across motion, disocclusion and material change.

**PREDICTION:** Reconstruction respects silhouette and temporal evidence budgets.

**FALSIFIER:** History reuse hides incorrect current geometry or lighting.

### SND — Sound vibration and acoustics

Domain class: **engineering**. Candidate prerequisites: DYN-01, GEO-01.

#### SND-01 · Structural sound sources

**Mathematics/concepts:** modal analysis; impulse response; radiation coupling.

**Depends on:** DYN-01, GEO-01, ELA-02. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Vibration-to-audio reference pathway.

**PREDICTION:** Mode frequencies and damping match independent structural tests.

**FALSIFIER:** An arbitrary sound clip is claimed as material vibration.

#### SND-02 · Acoustic propagation

**Mathematics/concepts:** wave equation; geometric acoustics; diffraction limits.

**Depends on:** DYN-01, GEO-01, SND-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Hybrid acoustic representation by wavelength/regime.

**PREDICTION:** Arrival time and attenuation match reference rooms.

**FALSIFIER:** Ray acoustics is advertised as exact at all wavelengths.

#### SND-03 · Materials and boundaries

**Mathematics/concepts:** impedance; absorption; transmission.

**Depends on:** DYN-01, GEO-01, SND-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Frequency-dependent acoustic material contract.

**PREDICTION:** Energy accounting across reflection/transmission/absorption closes.

**FALSIFIER:** Absorption coefficients outside physical bounds are accepted.

#### SND-04 · Spatial hearing

**Mathematics/concepts:** HRTF; binaural cues; listener pose.

**Depends on:** DYN-01, GEO-01, SND-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Head-tracked audio with declared model uncertainty.

**PREDICTION:** Known-source direction and delay tests match rendered cues.

**FALSIFIER:** Audio responds to a different world/pose epoch without disclosure.

#### SND-05 · Procedural interaction audio

**Mathematics/concepts:** contact impulses; friction excitation; resonators.

**Depends on:** DYN-01, GEO-01, SND-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** State-driven scraping/impact sound synthesis.

**PREDICTION:** Controlled material/contact changes produce predicted spectral trends.

**FALSIFIER:** Sound invents a contact absent from the physical state.

#### SND-06 · Speech and audiovisual timing

**Mathematics/concepts:** speech synthesis; phonemes; synchronization.

**Depends on:** DYN-01, GEO-01, SND-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Character voice and lip/audio timing bridge.

**PREDICTION:** Recorded event latency and articulation remain within agreed budgets.

**FALSIFIER:** Audio and visible action contradict their shared event identity.

### BIO — Living physical systems

Domain class: **research**. Candidate prerequisites: ELA-01, DYN-01.

#### BIO-01 · Tissue mechanics

**Mathematics/concepts:** anisotropy; incompressibility; viscoelasticity.

**Depends on:** ELA-01, DYN-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded fictional/biological tissue models with measured domains.

**PREDICTION:** Mechanical tests reproduce declared tissue response.

**FALSIFIER:** A game tissue model is promoted to clinical prediction.

#### BIO-02 · Muscles tendons and actuation

**Mathematics/concepts:** force-length-velocity; activation; tendon compliance.

**Depends on:** ELA-01, DYN-01, BIO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Energy-budgeted actuator models.

**PREDICTION:** Isolated actuator work and force controls match the chosen model.

**FALSIFIER:** Animation commands inject unaccounted physical energy.

#### BIO-03 · Circulation and transport

**Mathematics/concepts:** network flow; lumped compliance; exchange.

**Depends on:** ELA-01, DYN-01, BIO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Simplified physiology model with conservation contracts.

**PREDICTION:** Closed transport loops balance mass and specified substances.

**FALSIFIER:** A coarse model claims detailed physiological fidelity.

#### BIO-04 · Growth and morphogenesis

**Mathematics/concepts:** reaction diffusion; mechanics-coupled growth; remodeling.

**Depends on:** ELA-01, DYN-01, BIO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded growth and pattern formation systems.

**PREDICTION:** Growth changes rest state with declared source/material accounting.

**FALSIFIER:** New tissue appears without mass or growth assumptions.

#### BIO-05 · Plants and soft organisms

**Mathematics/concepts:** rod mechanics; tropisms; hydraulic coupling.

**Depends on:** ELA-01, DYN-01, BIO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One plant/soft-organism demonstrator.

**PREDICTION:** Controlled loads/environment changes produce repeatable responses.

**FALSIFIER:** A procedural shape generator is mislabeled predictive biology.

#### BIO-06 · Ecosystem interactions

**Mathematics/concepts:** population dynamics; resource flows; stochastic processes.

**Depends on:** ELA-01, DYN-01, BIO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Resource-linked ecosystem abstraction.

**PREDICTION:** Population/resource accounting and sensitivity tests are explicit.

**FALSIFIER:** An emergent-looking animation is treated as ecological validation.

### HUM — Human behavior and experience

Domain class: **research**. Candidate prerequisites: BIO-01, GOV-01.

#### HUM-01 · Embodied person model

**Mathematics/concepts:** perception-action loops; affordances; bounded rationality.

**Depends on:** BIO-01, GOV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Explicit observation/action capabilities and state separation.

**PREDICTION:** Agents act only on information their sensors/history provide.

**FALSIFIER:** Characters exploit inaccessible simulator truth.

#### HUM-02 · Attention memory and emotion

**Mathematics/concepts:** cognitive architectures; appraisal; memory decay.

**Depends on:** BIO-01, GOV-01, HUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Adjustable behavioral models with clear fictional status.

**PREDICTION:** Scenario tests distinguish modeled mechanisms and reproducibility.

**FALSIFIER:** Behavioral similarity is called a complete model of a person.

#### HUM-03 · Social interaction and culture

**Mathematics/concepts:** multi-agent systems; norms; communication; institutions.

**Depends on:** BIO-01, GOV-01, HUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Inspectable social rules with uncertainty and author control.

**PREDICTION:** Scenario changes have traceable rule/observation consequences.

**FALSIFIER:** One culture or heuristic is presented as a universal human law.

#### HUM-04 · Individual variation and accessibility

**Mathematics/concepts:** motor/sensory variability; interface adaptation.

**Depends on:** BIO-01, GOV-01, HUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Configurable abilities and accessible interaction profiles.

**PREDICTION:** Tasks remain usable across declared access modes.

**FALSIFIER:** A single perceptual/motor profile is assumed for all users.

#### HUM-05 · Consent and personal representation

**Mathematics/concepts:** identity provenance; privacy; revocation.

**Depends on:** BIO-01, GOV-01, HUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Controls for likeness, voice, memories and shared-world personal data.

**PREDICTION:** Revocation and scope limits propagate to derived artifacts.

**FALSIFIER:** A fictional inference is attributed as a real person's fact or consent.

#### HUM-06 · Consciousness and subjectivity limits

**Mathematics/concepts:** philosophy of mind; measurement limits; falsifiability.

**Depends on:** BIO-01, GOV-01, HUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Research boundary document and claim taxonomy.

**PREDICTION:** Observable behavior is kept distinct from untestable inner experience.

**FALSIFIER:** A simulated persona is claimed to reconstruct human consciousness.

### CTRL — Creatures robotics and control

Domain class: **engineering**. Candidate prerequisites: DYN-02, CON-01.

#### CTRL-01 · Rig-to-dynamics mapping

**Mathematics/concepts:** FK; IK; Jacobians; inertial identification.

**Depends on:** DYN-02, CON-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Map authored axes/ROM/weights to physical actuation.

**PREDICTION:** Reference FK and dynamic constraints agree on coordinates and ranges.

**FALSIFIER:** Rig conventions are guessed from channel names or negative zero.

#### CTRL-02 · Continuous locomotion

**Mathematics/concepts:** hybrid systems; capture point; orbital stability; branch persistence.

**Depends on:** DYN-02, CON-01, CTRL-01, CON-03, DYN-03, BIO-02. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Resume existing gait law with contact and actuator budgets.

**PREDICTION:** Perturbation, start/stop and path-continuity tests pass independently.

**FALSIFIER:** Foot-position closure alone certifies walking.

#### CTRL-03 · Whole-body control

**Mathematics/concepts:** inverse dynamics; QP; support constraints; momentum.

**Depends on:** DYN-02, CON-01, CTRL-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One bounded standing/reaching controller.

**PREDICTION:** Targets respect torque, contact and stability constraints.

**FALSIFIER:** Unreachable targets silently teleport limbs.

#### CTRL-04 · Planning and manipulation

**Mathematics/concepts:** configuration spaces; trajectory optimization; grasp mechanics.

**Depends on:** DYN-02, CON-01, CTRL-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Pick/place/tool use with collision and force feasibility.

**PREDICTION:** Held-out tasks meet geometric and physical constraints.

**FALSIFIER:** A collision-free visual path is treated as a feasible physical grasp.

#### CTRL-05 · System identification and feedback

**Mathematics/concepts:** observability; Kalman methods; robust control; MPC.

**Depends on:** DYN-02, CON-01, CTRL-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Noisy sensor/state-estimation control bench.

**PREDICTION:** Perturbation and parameter shifts remain within stability margins.

**FALSIFIER:** Controller success depends on hidden exact parameters.

#### CTRL-06 · Learning-assisted control

**Mathematics/concepts:** imitation; reinforcement learning; residual policies.

**Depends on:** DYN-02, CON-01, CTRL-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded learned policy with fallback and OOD detection.

**PREDICTION:** New conditions expose uncertainty before unsafe commands are accepted.

**FALSIFIER:** Reward score substitutes for verified contact or energy behavior.

### AI — World understanding and agent tooling

Domain class: **research**. Candidate prerequisites: GOV-01, MATH-06.

#### AI-01 · World ontology and scene semantics

**Mathematics/concepts:** graphs; types; spatial relations; affordances.

**Depends on:** GOV-01, MATH-06. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Queryable world descriptions grounded in actual state.

**PREDICTION:** Symbolic queries map to identifiable geometry/material/state.

**FALSIFIER:** Language labels silently create unsupported physical capabilities.

#### AI-02 · Tool planning and transactions

**Mathematics/concepts:** planning; preconditions; effects; rollback.

**Depends on:** GOV-01, MATH-06, AI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Agent action API with state acknowledgements.

**PREDICTION:** Plans respect permissions and observe applied effects.

**FALSIFIER:** A successful request is mistaken for successful world mutation.

#### AI-03 · Memory and retrieval

**Mathematics/concepts:** provenance graphs; versioned retrieval; compression.

**Depends on:** GOV-01, MATH-06, AI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Persistent project/world memory with contradiction handling.

**PREDICTION:** Restart retrieves current ownership and superseded claims correctly.

**FALSIFIER:** Old summaries override newer measured evidence.

#### AI-04 · Multimodal grounding

**Mathematics/concepts:** vision-language alignment; uncertainty; scene correspondence.

**Depends on:** GOV-01, MATH-06, AI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Images/text/state linking with explicit observation boundaries.

**PREDICTION:** Known mismatches are detected without leading prompts.

**FALSIFIER:** A fluent description is accepted as measurement.

#### AI-05 · Learned world models

**Mathematics/concepts:** latent dynamics; predictive coding; OOD uncertainty.

**Depends on:** GOV-01, MATH-06, AI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Research surrogate of specified phenomena with oracle comparison.

**PREDICTION:** Held-out interventions reveal calibrated prediction error.

**FALSIFIER:** A plausible generated future replaces accepted simulator state.

#### AI-06 · Autonomous creator evaluation

**Mathematics/concepts:** task planning; tool use; benchmark contamination.

**Depends on:** GOV-01, MATH-06, AI-01, AUTH-03, VERIFY-04. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** End-to-end build/test/repair episodes on unseen small projects.

**PREDICTION:** Agent-built artifacts reproduce and meet independent acceptance.

**FALSIFIER:** Self-written tests or memorized examples alone certify capability.

### ENV — Land sky water and planetary worlds

Domain class: **research**. Candidate prerequisites: FLU-01, THM-01, GEO-01.

#### ENV-01 · Terrain and geology

**Mathematics/concepts:** heightfields; volumetric strata; erosion; sediment.

**Depends on:** FLU-01, THM-01, GEO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Triangle terrain with material layers and declared support fields.

**PREDICTION:** Erosion/deposition closes sediment budgets.

**FALSIFIER:** Procedural terrain noise is labeled predictive geological history.

#### ENV-02 · Weather and atmosphere

**Mathematics/concepts:** advection; buoyancy; moisture; radiation.

**Depends on:** FLU-01, THM-01, GEO-01, ENV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Regional atmosphere approximation with stated scale.

**PREDICTION:** Mass/energy and canonical transport controls converge.

**FALSIFIER:** Local weather visuals imply unrestricted climate predictability.

#### ENV-03 · Water cycle and hydrology

**Mathematics/concepts:** watersheds; infiltration; shallow water; groundwater.

**Depends on:** FLU-01, THM-01, GEO-01, ENV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Connected river/rain/soil transport abstraction.

**PREDICTION:** Catchment water accounting closes across reservoirs.

**FALSIFIER:** Water disappears between terrain and atmosphere representations.

#### ENV-04 · Ocean and waves

**Mathematics/concepts:** dispersion; shallow/deep regimes; wave spectra.

**Depends on:** FLU-01, THM-01, GEO-01, ENV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One declared wave regime coupled to local interaction.

**PREDICTION:** Dispersion and boundary controls agree with references.

**FALSIFIER:** Height-surface waves claim overturning or all underwater flow.

#### ENV-05 · Orbital and astronomical scenes

**Mathematics/concepts:** celestial mechanics; reference frames; scales.

**Depends on:** FLU-01, THM-01, GEO-01, ENV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Large-scale ephemeris/lighting interface.

**PREDICTION:** Two-body and frame-transform tests agree within domain.

**FALSIFIER:** Astronomical coordinates degrade nearby contact precision.

#### ENV-06 · Coupled environmental fidelity

**Mathematics/concepts:** nested grids; boundary exchange; uncertainty budgets.

**Depends on:** FLU-01, THM-01, GEO-01, ENV-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Regional-to-local world coupling policy.

**PREDICTION:** Boundary fluxes and observable errors stay accounted across scales.

**FALSIFIER:** Local refinement silently changes upstream weather/resource balances.

### PROC — Procedural objects and world construction

Domain class: **engineering**. Candidate prerequisites: GEO-01, MAT-01.

#### PROC-01 · Object recipes and assemblies

**Mathematics/concepts:** parametric geometry; constraints; material assignment.

**Depends on:** GEO-01, MAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Versioned object definitions grounded in components and laws.

**PREDICTION:** Rebuilding a recipe reproduces geometry/material identity.

**FALSIFIER:** Appearance-only labels promise structural functionality.

#### PROC-02 · Geometry acquisition

**Mathematics/concepts:** photogrammetry; point clouds; reconstruction; calibration.

**Depends on:** GEO-01, MAT-01, PROC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Import route with scale and uncertainty records.

**PREDICTION:** Held-out scans expose holes, bias and resolution limits.

**FALSIFIER:** A photograph determines hidden material properties without evidence.

#### PROC-03 · Shape editing and manufacturing

**Mathematics/concepts:** CSG; robust booleans; offsets; tolerances.

**Depends on:** GEO-01, MAT-01, PROC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Editable geometry preserving intentional openings and provenance.

**PREDICTION:** Operations maintain declared topology and dimensions.

**FALSIFIER:** Boolean repair seals a cup opening or loses material identity.

#### PROC-04 · Construction systems

**Mathematics/concepts:** assemblies; joints; load paths; constraint graphs.

**Depends on:** GEO-01, MAT-01, PROC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Buildable structures with explicit connectors.

**PREDICTION:** Load/path tests expose unsupported assemblies.

**FALSIFIER:** Visual adjacency is interpreted as a welded physical connection.

#### PROC-05 · Procedural diversity

**Mathematics/concepts:** grammars; constraint satisfaction; seeded generation.

**Depends on:** GEO-01, MAT-01, PROC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Deterministic diverse objects with validity filtering.

**PREDICTION:** Generated examples obey geometric/material constraints.

**FALSIFIER:** High content volume hides invalid or duplicate assets.

#### PROC-06 · Interchange and round trip

**Mathematics/concepts:** scene graphs; units; instancing; material bindings.

**Depends on:** GEO-01, MAT-01, PROC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Versioned import/export with capability-loss reports.

**PREDICTION:** Round trips preserve supported quantities and identify losses.

**FALSIFIER:** An interchange silently discards physical state or units.

### AUTH — Editor game creation and product authoring

Domain class: **engineering**. Candidate prerequisites: GOV-01, GEO-01.

#### AUTH-01 · World inspection and debugging

**Mathematics/concepts:** state queries; picking; provenance; overlays.

**Depends on:** GOV-01, GEO-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Editor inspectors tied to accepted state.

**PREDICTION:** Selected object/frame data matches the actual rendered state.

**FALSIFIER:** The inspector displays pending or stale data as applied.

#### AUTH-02 · Transactional editing

**Mathematics/concepts:** command patterns; undo/redo; snapshots.

**Depends on:** GOV-01, GEO-01, AUTH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Safe reversible authoring commands.

**PREDICTION:** Undo restores physical and authored state or declares nonreversible effects.

**FALSIFIER:** Undo only restores appearance while leaving hidden state changed.

#### AUTH-03 · Physical experiment authoring

**Mathematics/concepts:** boundary conditions; fixtures; parameter sweeps.

**Depends on:** GOV-01, GEO-01, AUTH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** No-code experiment setup with versioned law inputs.

**PREDICTION:** Saved experiments reproduce independent validation cases.

**FALSIFIER:** UI defaults silently select missing physical parameters.

#### AUTH-04 · Gameplay and interaction systems

**Mathematics/concepts:** state machines; events; inventories; objectives.

**Depends on:** GOV-01, GEO-01, AUTH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Playable interaction layer grounded in world actions.

**PREDICTION:** Player actions trigger consistent physical and game consequences.

**FALSIFIER:** Scripted gameplay bypasses resource/contact rules without declared mode.

#### AUTH-05 · Narrative cinematics and direction

**Mathematics/concepts:** timelines; cameras; constraints; authored events.

**Depends on:** GOV-01, GEO-01, AUTH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Story/camera tooling with explicit physical overrides.

**PREDICTION:** Scripted overrides are labeled and reproducible.

**FALSIFIER:** A keyframed override is presented as emergent physical behavior.

#### AUTH-06 · Creator usability and accessibility

**Mathematics/concepts:** task analysis; localization; input modes.

**Depends on:** GOV-01, GEO-01, AUTH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Usability benchmarks for human and agent creators.

**PREDICTION:** New users complete defined creation/debugging tasks.

**FALSIFIER:** Feature count substitutes for demonstrable usable workflows.

### SYS — Engine architecture and operating systems

Domain class: **engineering**. Candidate prerequisites: GOV-01, GPU-01.

#### SYS-01 · Subsystem boundaries and ABI

**Mathematics/concepts:** ownership; interfaces; data-oriented design.

**Depends on:** GOV-01, GPU-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Current dependency map and stable core contracts.

**PREDICTION:** Components can be tested without unrelated platform state.

**FALSIFIER:** A nominal seam still imports hidden global platform dependencies.

#### SYS-02 · Memory and job scheduling

**Mathematics/concepts:** arenas; lifetime; lock-free queues; work stealing.

**Depends on:** GOV-01, GPU-01, SYS-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded CPU/GPU jobs and memory policy.

**PREDICTION:** Stress runs meet lifetime and bounded-memory invariants.

**FALSIFIER:** Unbounded queues or allocator churn masquerade as GPU limits.

#### SYS-03 · Assets and resource lifecycle

**Mathematics/concepts:** content hashes; hot reload; dependency graphs.

**Depends on:** GOV-01, GPU-01, SYS-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Incremental asset pipeline and safe resource replacement.

**PREDICTION:** Reload invalidates correct dependents and preserves in-flight safety.

**FALSIFIER:** Stale compiled assets are used under new source identities.

#### SYS-04 · Runtime observability

**Mathematics/concepts:** structured traces; profiler; state epochs.

**Depends on:** GOV-01, GPU-01, SYS-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Inspectable timing/resource/claim evidence.

**PREDICTION:** A failure can be traced to its input/state/source.

**FALSIFIER:** Logs say PASS without retaining the relevant numerical verdict.

#### SYS-05 · Persistence and replay

**Mathematics/concepts:** event logs; snapshots; schema migration.

**Depends on:** GOV-01, GPU-01, SYS-01, GOV-05. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Crash-consistent save/load/replay.

**PREDICTION:** Restart preserves accepted physical state and ownership.

**FALSIFIER:** Partial writes or version changes silently corrupt a world.

#### SYS-06 · Language and extension boundary

**Mathematics/concepts:** C++ modules; scripting; sandboxed commands.

**Depends on:** GOV-01, GPU-01, SYS-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Authoring extensions outside the GPU physical update law.

**PREDICTION:** Plugins request valid actions and cannot silently replace runtime state.

**FALSIFIER:** Python per-frame simulation is introduced as an unnoticed dependency.

### PLAT — Windows Linux and device portability

Domain class: **engineering**. Candidate prerequisites: SYS-01, GPU-04.

#### PLAT-01 · Window and input seam

**Mathematics/concepts:** event ordering; focus; capture; native lifetime.

**Depends on:** SYS-01, GPU-04. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Behavior-preserving Windows seam and offline intent replay.

**PREDICTION:** Existing camera/input conventions survive extraction.

**FALSIFIER:** A second platform introduces new camera semantics silently.

#### PLAT-02 · Vulkan surface and presentation

**Mathematics/concepts:** WSI; swapchain; framebuffer sizes; minimization.

**Depends on:** SYS-01, GPU-04, PLAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Window lifecycle/presentation contract per platform.

**PREDICTION:** Resize/minimize/recreate works under explicit resource lifetime.

**FALSIFIER:** A compute-only pass is claimed as window portability.

#### PLAT-03 · Linux native runtime

**Mathematics/concepts:** build dependencies; display servers; device discovery.

**Depends on:** SYS-01, GPU-04, PLAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Separate Linux build/compute/presentation gates.

**PREDICTION:** Each claimed stage runs with exact device evidence.

**FALSIFIER:** llvmpipe success is labeled RTX hardware execution.

#### PLAT-04 · Cross-vendor support

**Mathematics/concepts:** feature tiers; shader compilers; alignment.

**Depends on:** SYS-01, GPU-04, PLAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** AMD/Intel/NVIDIA capability and evidence matrix.

**PREDICTION:** Supported tiers execute matching-law tests.

**FALSIFIER:** Vendor-specific numerical behavior is hidden by relaxed budgets.

#### PLAT-05 · Packaging and reproducible builds

**Mathematics/concepts:** toolchain pinning; shader hashes; dependency manifests.

**Depends on:** SYS-01, GPU-04, PLAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Clean-machine build/launch procedure.

**PREDICTION:** Artifacts trace to source and necessary dependencies.

**FALSIFIER:** An untracked local binary is required for a released feature.

#### PLAT-06 · Platform failure recovery

**Mathematics/concepts:** device loss; display loss; suspend/resume.

**Depends on:** SYS-01, GPU-04, PLAT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Explicit recoverable/unrecoverable session outcomes.

**PREDICTION:** Recovery preserves last accepted state or reports its loss.

**FALSIFIER:** A recovered window shows invalid physical memory.

### SCALE — Performance and multiscale simulation

Domain class: **engineering**. Candidate prerequisites: GPU-03, GEO-02, NUM-01.

#### SCALE-01 · Cost and memory model

**Mathematics/concepts:** asymptotics; roofline; bandwidth; latency.

**Depends on:** GPU-03, GEO-02, NUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Measured per-stage scaling by topology and workload.

**PREDICTION:** Model predicts held-out sizes within stated uncertainty.

**FALSIFIER:** Tiny-fixture timings are extrapolated to arbitrary worlds.

#### SCALE-02 · GPU optimization experiments

**Mathematics/concepts:** occupancy; reductions; batching; fusion.

**Depends on:** GPU-03, GEO-02, NUM-01, SCALE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** At most justified candidates with independent correctness.

**PREDICTION:** Matched workloads improve without physical-budget breaches.

**FALSIFIER:** Speedup comes from skipped work or altered tolerance.

#### SCALE-03 · Physical LOD and coarse graining

**Mathematics/concepts:** homogenization; conservative restriction/prolongation.

**Depends on:** GPU-03, GEO-02, NUM-01, SCALE-01, GEO-04, MULTI-04. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Scale transitions preserving chosen invariants.

**PREDICTION:** Coarse/fine exchange meets mass/momentum/error contracts.

**FALSIFIER:** Visual LOD alone is claimed as equivalent mechanics.

#### SCALE-04 · Model order reduction

**Mathematics/concepts:** modal bases; POD; reduced coordinates; hyper-reduction.

**Depends on:** GPU-03, GEO-02, NUM-01, SCALE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded surrogate with out-of-domain fallback.

**PREDICTION:** Held-out deformations expose error and trigger fallback.

**FALSIFIER:** Surrogate is trusted beyond its trained/derived domain.

#### SCALE-05 · Adaptive allocation and perceptual budgets

**Mathematics/concepts:** error indicators; visibility; interaction importance.

**Depends on:** GPU-03, GEO-02, NUM-01, SCALE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Resource prioritization combining physical and perceptual needs.

**PREDICTION:** Unseen objects retain consequences needed by future interaction.

**FALSIFIER:** Offscreen culling erases physical causes or changes world conservation.

#### SCALE-06 · Multi-device execution

**Mathematics/concepts:** domain decomposition; halo exchange; load balancing.

**Depends on:** GPU-03, GEO-02, NUM-01, SCALE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Research path to multiple GPUs with explicit communication costs.

**PREDICTION:** Cross-partition balances and timings match declared models.

**FALSIFIER:** Distributed speedup ignores transfer, synchronization or reproducibility.

### NET — Persistent shared worlds and networking

Domain class: **engineering**. Candidate prerequisites: SYS-05.

#### NET-01 · Authority and replication

**Mathematics/concepts:** distributed state; consistency; snapshots.

**Depends on:** SYS-05. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Authoritative world/region ownership model.

**PREDICTION:** Clients distinguish predicted from accepted replicated state.

**FALSIFIER:** Different nodes claim conflicting authoritative physics.

#### NET-02 · Prediction rollback and reconciliation

**Mathematics/concepts:** time-stamped inputs; deterministic subsets; error correction.

**Depends on:** SYS-05, NET-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded latency compensation model.

**PREDICTION:** Corrections preserve accepted event history and expose prediction error.

**FALSIFIER:** Client prediction is recorded as final physical truth.

#### NET-03 · Interest and region streaming

**Mathematics/concepts:** spatial partitions; causal relevance; cache invalidation.

**Depends on:** SYS-05, NET-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Streaming retaining persistent effects across unloaded regions.

**PREDICTION:** Reload reproduces world changes and resource accounting.

**FALSIFIER:** Unobserved regions reset inventory or stored energy.

#### NET-04 · Distributed persistence

**Mathematics/concepts:** transactions; crash recovery; event ordering.

**Depends on:** SYS-05, NET-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Durable world transitions with idempotent retries.

**PREDICTION:** Failure/retry tests avoid duplicate creation or lost edits.

**FALSIFIER:** One action is applied twice after reconnect.

#### NET-05 · Trust and abuse resistance

**Mathematics/concepts:** input validation; authority checks; quotas.

**Depends on:** SYS-05, NET-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Server-side action validation and resource limits.

**PREDICTION:** Unauthorized/invalid requests do not mutate authoritative state.

**FALSIFIER:** Client-supplied physical verdicts are accepted without validation.

#### NET-06 · Collaborative authoring

**Mathematics/concepts:** conflict resolution; version graphs; shared ownership.

**Depends on:** SYS-05, NET-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Multi-user edits with explicit physical-state conflict policy.

**PREDICTION:** Concurrent edits either merge validly or surface conflicts.

**FALSIFIER:** Geometry/material conflicts are silently overwritten.

### XR — Immersion embodiment and haptics

Domain class: **engineering**. Candidate prerequisites: PLAT-02, LGT-01.

#### XR-01 · Tracked viewing and spaces

**Mathematics/concepts:** OpenXR; rigid frames; pose prediction.

**Depends on:** PLAT-02, LGT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Head/controller/world-space contract.

**PREDICTION:** Pose and scale calibration survive reference-space changes.

**FALSIFIER:** Stereo views use mismatched state or incorrect physical scale.

#### XR-02 · Latency and stereo correctness

**Mathematics/concepts:** motion-to-photon; frame pacing; reprojection.

**Depends on:** PLAT-02, LGT-01, XR-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Measured frame/pose timing budget.

**PREDICTION:** Latency and dropped-frame distributions meet agreed target hardware goals.

**FALSIFIER:** A nominal frame rate hides long latency tails.

#### XR-03 · Hands and full-body interaction

**Mathematics/concepts:** inverse kinematics; contact proxies; tracking uncertainty.

**Depends on:** PLAT-02, LGT-01, XR-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Tracked interaction with explicit reach/contact limits.

**PREDICTION:** Known tracking loss/occlusion fails visibly and recoverably.

**FALSIFIER:** Tracking noise injects unlimited physical energy.

#### XR-04 · Haptic feedback

**Mathematics/concepts:** impedance; passivity; force saturation; device bandwidth.

**Depends on:** PLAT-02, LGT-01, XR-01, CTRL-05, TRUST-04. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Virtual contact-to-device contract with device-specific limits.

**PREDICTION:** Bench tests remain stable under delay and saturation.

**FALSIFIER:** A visual contact model is assumed safe for physical force hardware.

#### XR-05 · Locomotion and access modes

**Mathematics/concepts:** comfort; seated/standing modes; remapping.

**Depends on:** PLAT-02, LGT-01, XR-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Configurable embodied interaction without physics claims.

**PREDICTION:** Defined user tasks work in selected access modes.

**FALSIFIER:** One locomotion scheme is treated as universally comfortable.

#### XR-06 · Mixed-reality alignment

**Mathematics/concepts:** spatial anchors; depth; occlusion; registration uncertainty.

**Depends on:** PLAT-02, LGT-01, XR-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Real/virtual alignment with measured confidence.

**PREDICTION:** Calibration targets bound drift and occlusion error.

**FALSIFIER:** Uncertain geometry is treated as guaranteed physical clearance.

### SENSE — World sensing reconstruction and digital twins

Domain class: **research**. Candidate prerequisites: GEO-01, MATH-06.

#### SENSE-01 · Sensor models and calibration

**Mathematics/concepts:** camera models; lidar; IMU; noise; timestamps.

**Depends on:** GEO-01, MATH-06. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Ground-truthed virtual sensors and real calibration interfaces.

**PREDICTION:** Known scenes recover modeled bias/noise/latency.

**FALSIFIER:** Perfect simulator measurements masquerade as real sensors.

#### SENSE-02 · State estimation and SLAM

**Mathematics/concepts:** bundle adjustment; filtering; observability.

**Depends on:** GEO-01, MATH-06, SENSE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Pose/map estimation with explicit ambiguity.

**PREDICTION:** Controlled trajectories expose scale/drift uncertainty.

**FALSIFIER:** An unobservable quantity is returned with false certainty.

#### SENSE-03 · Data assimilation

**Mathematics/concepts:** inverse problems; filtering; uncertainty propagation.

**Depends on:** GEO-01, MATH-06, SENSE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Fuse measured observations into versioned world estimates.

**PREDICTION:** Held-out sensors validate predicted state uncertainty.

**FALSIFIER:** Observation fitting silently violates conserved quantities.

#### SENSE-04 · Digital twin scope

**Mathematics/concepts:** identifiability; model discrepancy; calibration validity.

**Depends on:** GEO-01, MATH-06, SENSE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Narrow twin with declared measurement and use boundaries.

**PREDICTION:** Predictions hold on independent experiments in its scope.

**FALSIFIER:** An attractive replica is advertised as a complete physical twin.

#### SENSE-05 · Sim-to-real and domain shift

**Mathematics/concepts:** domain randomization; sensitivity; robust transfer.

**Depends on:** GEO-01, MATH-06, SENSE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Transfer studies with measured mismatch.

**PREDICTION:** New environments expose and quantify failed generalization.

**FALSIFIER:** Synthetic success alone certifies real-world performance.

#### SENSE-06 · Acquisition to material inference

**Mathematics/concepts:** multimodal measurements; priors; inverse rendering.

**Depends on:** GEO-01, MATH-06, SENSE-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Separate appearance inference from constitutive identification.

**PREDICTION:** Unmeasured material parameters remain unknown or explicitly prior-driven.

**FALSIFIER:** Images alone determine hidden strength, density or chemistry.

### TRUST — Boundaries permissions and human control

Domain class: **engineering**. Candidate prerequisites: GOV-01, SYS-01.

#### TRUST-01 · Agent and plugin permissions

**Mathematics/concepts:** least authority; capability tokens; audit trails.

**Depends on:** GOV-01, SYS-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Scoped authoring/runtime tool access.

**PREDICTION:** Untrusted content cannot escalate tool authority.

**FALSIFIER:** Asset text or a generated plan becomes executable authorization.

#### TRUST-02 · Untrusted assets and parsers

**Mathematics/concepts:** fuzzing; resource limits; memory safety.

**Depends on:** GOV-01, SYS-01, TRUST-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Import boundary tests and quarantine.

**PREDICTION:** Malformed files fail without corrupting accepted worlds.

**FALSIFIER:** A content parser crash causes unchecked world mutation.

#### TRUST-03 · Privacy and consent lifecycle

**Mathematics/concepts:** data minimization; provenance; revocation.

**Depends on:** GOV-01, SYS-01, TRUST-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Controls for captured people, voices and persistent memories.

**PREDICTION:** Removal/revocation reaches dependent stored representations.

**FALSIFIER:** Deleted personal inputs remain exposed through cached derivatives.

#### TRUST-04 · Physical device boundary

**Mathematics/concepts:** interlocks; output saturation; emergency stop.

**Depends on:** GOV-01, SYS-01, TRUST-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Explicit separation of simulated actions from hardware actuation.

**PREDICTION:** Disconnect/stop behavior is tested before any device control.

**FALSIFIER:** An in-world command actuates real hardware without scoped authorization.

#### TRUST-05 · Licensing and distribution records

**Mathematics/concepts:** dependency licenses; dataset terms; attribution.

**Depends on:** GOV-01, SYS-01, TRUST-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Versioned asset/model/dependency provenance inventory.

**PREDICTION:** A release can explain redistribution rights of its shipped content.

**FALSIFIER:** Unknown rights are silently treated as open permission.

#### TRUST-06 · Human acceptance and governance

**Mathematics/concepts:** decision records; access controls; reversible changes.

**Depends on:** GOV-01, SYS-01, TRUST-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Human review that records actual approval and unresolved limits.

**PREDICTION:** No autonomous tool manufactures Alan's aesthetic/product acceptance.

**FALSIFIER:** A model verdict is stored as the human's decision.

### VERIFY — Independent numerical runtime and DYAD verification

Domain class: **engineering**. Candidate prerequisites: GOV-02, NUM-01.

#### VERIFY-01 · Reference and manufactured solutions

**Mathematics/concepts:** analytic controls; independent formulations; convergence.

**Depends on:** GOV-02, NUM-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Reusable law-level verification ladder.

**PREDICTION:** Reference errors and implementation errors are separable.

**FALSIFIER:** Implementation-mirroring tests create circular correctness claims.

#### VERIFY-02 · Metamorphic and mutation tests

**Mathematics/concepts:** symmetries; adversarial inputs; fault injection.

**Depends on:** GOV-02, NUM-01, VERIFY-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Mutation corpus with meaningful failure attribution.

**PREDICTION:** Corruptions fail intended semantic gates after successful execution.

**FALSIFIER:** Compile failures count as numerical mutation detection.

#### VERIFY-03 · State trace verification

**Mathematics/concepts:** causal graphs; epochs; lifetimes; insufficient evidence.

**Depends on:** GOV-02, NUM-01, VERIFY-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Offline accepted/trial/frame verifier.

**PREDICTION:** Incomplete traces remain insufficient and invalid traces fail.

**FALSIFIER:** Labels alone pass stale-state or buffer-reuse controls.

#### VERIFY-04 · DYAD protocol operation

**Mathematics/concepts:** physical context; image grounding; non-leading questions.

**Depends on:** GOV-02, NUM-01, VERIFY-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** GLM-operated image/question loop with served model identity.

**PREDICTION:** Observations, predictions and uncertainty remain distinct.

**FALSIFIER:** An expected feature is reported despite invisibility.

#### VERIFY-05 · Visual measurement instruments

**Mathematics/concepts:** RGB pixel predicates; calibration; projection.

**Depends on:** GOV-02, NUM-01, VERIFY-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Independent screenshot metrics with explicit measurement scope.

**PREDICTION:** Known synthetic/published controls expose calculation errors.

**FALSIFIER:** Histogram bins or hash changes are mistaken for physical motion.

#### VERIFY-06 · Evidence retention and reproduction

**Mathematics/concepts:** content addressing; build identity; unique runs.

**Depends on:** GOV-02, NUM-01, VERIFY-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Source/input/SPIR-V/executable linkage and preserved failures.

**PREDICTION:** A third party reconstructs tested inputs and distinguishes absent artifacts.

**FALSIFIER:** Historical provenance is rewritten to pretend a later commit was executed.

### SHIP — Delivery maintainability and performance targets

Domain class: **engineering**. Candidate prerequisites: PLAT-05, VERIFY-01.

#### SHIP-01 · Continuous integration ladder

**Mathematics/concepts:** unit; numerical; integration; hardware; runtime gates.

**Depends on:** PLAT-05, VERIFY-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Tiered CI with device-specific results.

**PREDICTION:** Missing hardware tests remain not tested and failures block their claims.

**FALSIFIER:** Skipped tests are included in a global PASS.

#### SHIP-02 · Regression and compatibility

**Mathematics/concepts:** goldens; schema migration; behavior contracts.

**Depends on:** PLAT-05, VERIFY-01, SHIP-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Baseline preservation and intentional-change records.

**PREDICTION:** Old projects open with declared migration behavior.

**FALSIFIER:** A new physical feature silently changes unrelated authoring semantics.

#### SHIP-03 · Performance service objectives

**Mathematics/concepts:** percentiles; budgets; workloads; memory limits.

**Depends on:** PLAT-05, VERIFY-01, SHIP-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Ratified target scenes/devices and performance acceptance.

**PREDICTION:** Measured distributions meet scene-specific goals.

**FALSIFIER:** An average FPS number certifies worst-case interactive behavior.

#### SHIP-04 · Diagnostics and supportability

**Mathematics/concepts:** crash dumps; minimal reproducers; trace capture.

**Depends on:** PLAT-05, VERIFY-01, SHIP-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** User-collectable debugging records with sensitive-data limits.

**PREDICTION:** A clean machine can reproduce declared scenarios.

**FALSIFIER:** Only the developer's dirty checkout can run the demo.

#### SHIP-05 · Documentation and agent onboarding

**Mathematics/concepts:** examples; API schemas; task packets.

**Depends on:** PLAT-05, VERIFY-01, SHIP-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Executable onboarding and creator tutorials.

**PREDICTION:** Fresh agents/users complete representative tasks without private history.

**FALSIFIER:** Documentation assumes missing files or obsolete active owners.

#### SHIP-06 · Release and rollback

**Mathematics/concepts:** versioning; staged artifacts; migration backups.

**Depends on:** PLAT-05, VERIFY-01, SHIP-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Reviewable releases with known limits and recovery procedures.

**PREDICTION:** Rollback restores a compatible project state.

**FALSIFIER:** A release claims holodeck completeness or untested platform support.

### FRONT — Frontier mathematics and research portfolio

Domain class: **research**. Candidate prerequisites: NUM-01, VERIFY-01.

#### FRONT-01 · Differentiable multiphysics

**Mathematics/concepts:** adjoints; nonsmooth contact; implicit differentiation.

**Depends on:** NUM-01, VERIFY-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Research derivative model with valid-domain boundaries.

**PREDICTION:** Gradient-based predictions survive independent perturbation tests.

**FALSIFIER:** Nondifferentiable events are hidden under unreported smoothing.

#### FRONT-02 · Certified numerics

**Mathematics/concepts:** interval arithmetic; formal proofs; reachability bounds.

**Depends on:** NUM-01, VERIFY-01, FRONT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Restricted certified kernels where tractable.

**PREDICTION:** Proof assumptions match executed types and domains.

**FALSIFIER:** A local proof is promoted to whole-engine correctness.

#### FRONT-03 · Learned constitutive surrogates

**Mathematics/concepts:** neural operators; invariance; passivity; OOD.

**Depends on:** NUM-01, VERIFY-01, FRONT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Physics-constrained approximation with reference fallback.

**PREDICTION:** Held-out loads and rotations expose calibrated error.

**FALSIFIER:** A neural model violates conservation while claiming law equivalence.

#### FRONT-04 · Multiscale statistical mechanics

**Mathematics/concepts:** homogenization; fluctuation-dissipation; coarse potentials.

**Depends on:** NUM-01, VERIFY-01, FRONT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Offline bridges from microstructure to macro parameters.

**PREDICTION:** Independent macro observables validate inferred closures.

**FALSIFIER:** Coarse-grained parameters are treated as universal across regimes.

#### FRONT-05 · Relativistic and quantum scenes

**Mathematics/concepts:** Lorentz transforms; wavefunctions; quantum measurement.

**Depends on:** NUM-01, VERIFY-01, FRONT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Optional educational/research modules with declared simplifications.

**PREDICTION:** Canonical restricted experiments match their own models.

**FALSIFIER:** Quantum or relativistic effects are claimed to emerge from gravity alone.

#### FRONT-06 · Holodeck feasibility and unknowns

**Mathematics/concepts:** information limits; sensing; embodiment; model uncertainty.

**Depends on:** NUM-01, VERIFY-01, FRONT-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Living limits register and experiments on missing capabilities.

**PREDICTION:** Each frontier claim has a measurable restricted question or stays speculative.

**FALSIFIER:** Software imagery is advertised as unrestricted physical matter or complete human consciousness.

### INT — Integrated world milestones

Domain class: **integration**. Candidate prerequisites: GPU-01, VERIFY-01.

#### INT-01 · Material observatory

**Mathematics/concepts:** accepted-state rendering; control fixtures; DYAD.

**Depends on:** GPU-01, VERIFY-01, SUR-01, GPU-05, MAT-06, VERIFY-03, VERIFY-04. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** GPU membrane experiment with full state-linked evidence.

**PREDICTION:** Numerics, runtime controls and visible accepted geometry independently pass.

**FALSIFIER:** Numerical success is substituted for executed runtime/DYAD.

#### INT-02 · Elastic object workshop

**Mathematics/concepts:** rest shape; shear; bending; material admission.

**Depends on:** GPU-01, VERIFY-01, INT-01, ELA-06, AUTH-03, MAT-05. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Build and manipulate a calibrated or labeled-synthetic elastic object.

**PREDICTION:** Independent load tests and physical state survive authoring and reset.

**FALSIFIER:** A material label supplies unsupported strength or deformation.

#### INT-03 · Cup holding water

**Mathematics/concepts:** volume transport; pressure; wall stiffness; contact.

**Depends on:** GPU-01, VERIFY-01, INT-01, FLU-05, FLU-04, DYN-05, GEO-03. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Watertight rigid cup first, then a declared deformable cup.

**PREDICTION:** Mass, hydrostatics, traction and visual state pass separate gates.

**FALSIFIER:** Water containment is attributed only to surface tension.

#### INT-04 · Embodied creature laboratory

**Mathematics/concepts:** actuation; contacts; perception; gait stability.

**Depends on:** GPU-01, VERIFY-01, INT-01, CTRL-02, CTRL-03, CON-06. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Fictional creature standing, starting, stepping and interacting.

**PREDICTION:** Perturbations, actuator limits, continuity and runtime evidence pass.

**FALSIFIER:** A keyframed stream is called force-driven stable locomotion.

#### INT-05 · Persistent interactive world

**Mathematics/concepts:** LOD; networking; authoring; resources; agents.

**Depends on:** GPU-01, VERIFY-01, INT-01, SYS-05, NET-01, AUTH-04, SCALE-03. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Small shared world retaining physical and authored consequences.

**PREDICTION:** Save/reload, clients and model transitions preserve declared invariants.

**FALSIFIER:** A vast empty scene is called a complete interacting world.

#### INT-06 · Immersive creator environment

**Mathematics/concepts:** XR; multimodal interaction; agents; human acceptance.

**Depends on:** GPU-01, VERIFY-01, INT-01, XR-01, AI-06, INT-05, TRUST-06. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** A bounded holodeck-like creation and exploration experience.

**PREDICTION:** New users create and inhabit tested physical scenarios within limits.

**FALSIFIER:** A convincing demo is represented as simulation of all reality.

### CA — Triangle cellular substrate and field evolution

Domain class: **research**. Candidate prerequisites: GEO-01, MATH-05.

#### CA-01 · Triangle cell definition

**Mathematics/concepts:** primal/dual meshes; state variables; adjacency.

**Depends on:** GEO-01, MATH-05. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Define exactly what one cell stores and which interactions cross its boundary.

**PREDICTION:** Each geometric/physical quantity has units, ownership and explicit update law.

**FALSIFIER:** A triangle database row is assumed to supply unspecified physics by itself.

#### CA-02 · Conservative neighborhood exchange

**Mathematics/concepts:** finite-volume flux; antisymmetric pair transfers.

**Depends on:** GEO-01, MATH-05, CA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Mass/momentum/energy exchange operators on irregular neighborhoods.

**PREDICTION:** Closed exchanges cancel pairwise within declared numerical budget.

**FALSIFIER:** An update creates a source when only transport was intended.

#### CA-03 · Cell clock and stochastic updates

**Mathematics/concepts:** synchronous/asynchronous CA; scheduling bias; random streams.

**Depends on:** GEO-01, MATH-05, CA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Versioned update order and reproducible stochastic process.

**PREDICTION:** Schedule-sensitive outcomes are measured and labeled.

**FALSIFIER:** Parallel scheduling changes the modeled law without disclosure.

#### CA-04 · Energy-based cell transitions

**Mathematics/concepts:** detailed balance; Metropolis rates; free energy.

**Depends on:** GEO-01, MATH-05, CA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Optional equilibrium sampling distinct from dynamics.

**PREDICTION:** Known equilibrium distributions reproduce under the stated sampler.

**FALSIFIER:** Monte Carlo sweeps are relabeled physical time without calibrated rates.

#### CA-05 · Hybrid constraints and field coupling

**Mathematics/concepts:** constraint projection; interface work; conservative maps.

**Depends on:** GEO-01, MATH-05, CA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Connect cell fields to forces and accepted geometry.

**PREDICTION:** Two-way exchanges close their work and conservation ledgers.

**FALSIFIER:** The same energy is counted in both CA and mechanical updates.

#### CA-06 · Emergence and resolution tests

**Mathematics/concepts:** renormalization ideas; universality; finite-size effects.

**Depends on:** GEO-01, MATH-05, CA-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Demonstrate one emergent phenomenon across mesh sizes and schedules.

**PREDICTION:** Its dimensionless observables converge over a declared regime.

**FALSIFIER:** Interesting patterns alone certify universal material behavior.

### MULTI — Multiphysics composition and solver compatibility

Domain class: **engineering**. Candidate prerequisites: NUM-05, MAT-02.

#### MULTI-01 · Port and exchange contract

**Mathematics/concepts:** effort-flow variables; power conjugacy; flux orientation.

**Depends on:** NUM-05, MAT-02. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Typed exchange boundaries for forces, heat, species and fields.

**PREDICTION:** Each closed exchange has equal-and-opposite accounted transfer.

**FALSIFIER:** One solver records gained energy that no other solver loses.

#### MULTI-02 · Energy and entropy ownership

**Mathematics/concepts:** free energy; stored energy; work; dissipation.

**Depends on:** NUM-05, MAT-02, MULTI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Global ledger assigning every term once.

**PREDICTION:** Coupled subsystem balances close without double-counted terms.

**FALSIFIER:** Surface, bulk or actuator energies overlap invisibly.

#### MULTI-03 · Time and coupling strategies

**Mathematics/concepts:** operator splitting; strong/weak coupling; subcycling.

**Depends on:** NUM-05, MAT-02, MULTI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Choose partitioned/monolithic coupling per stability evidence.

**PREDICTION:** Coupled benchmark order/stability matches declared scheme.

**FALSIFIER:** Individually stable solvers are assumed stable in composition.

#### MULTI-04 · Interface discretization transfer

**Mathematics/concepts:** mortar methods; conservative interpolation; adjoint maps.

**Depends on:** NUM-05, MAT-02, MULTI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Work-preserving transfers between unlike grids/representations.

**PREDICTION:** Loads/displacements and fluxes retain reciprocity across transfers.

**FALSIFIER:** Interpolation conserves values but loses total work or mass.

#### MULTI-05 · Multiphysics manufactured problems

**Mathematics/concepts:** manufactured solutions; exchange closure; feedback.

**Depends on:** NUM-05, MAT-02, MULTI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Independent small coupled tests before showcase integration.

**PREDICTION:** Known coupled responses reproduce with refinement.

**FALSIFIER:** Single-subsystem PASS is promoted directly to coupled-system PASS.

#### MULTI-06 · Co-simulation boundaries

**Mathematics/concepts:** FMI concepts; rollback; time negotiation; uncertainty.

**Depends on:** NUM-05, MAT-02, MULTI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Optional external solver adapter with explicit authority.

**PREDICTION:** External participants exchange consistent time/state under failure.

**FALSIFIER:** External simulator updates bypass accepted-state ownership.

### SOC — Societies institutions and human-created worlds

Domain class: **research**. Candidate prerequisites: HUM-03, AUTH-04.

#### SOC-01 · Resource and production systems

**Mathematics/concepts:** stock-flow consistency; inventories; process graphs.

**Depends on:** HUM-03, AUTH-04. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Inspectable fictional production/trade rules tied to physical resources.

**PREDICTION:** Production and consumption balance stated inputs and outputs.

**FALSIFIER:** An economic label permits unaccounted material creation.

#### SOC-02 · Institutions and governance models

**Mathematics/concepts:** agent rules; incentives; game theory; rule changes.

**Depends on:** HUM-03, AUTH-04, SOC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Configurable fictional institutions with traceable assumptions.

**PREDICTION:** Policy experiments expose sensitivities and alternate hypotheses.

**FALSIFIER:** One agent society is claimed to predict real political outcomes.

#### SOC-03 · Language and knowledge systems

**Mathematics/concepts:** grounding; knowledge graphs; uncertainty; dialogue.

**Depends on:** HUM-03, AUTH-04, SOC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** World-grounded multilingual knowledge and communication.

**PREDICTION:** Characters distinguish knowledge, inference and inaccessible facts.

**FALSIFIER:** Dialogue invents historical/world facts as accepted state.

#### SOC-04 · History and cultural reconstruction

**Mathematics/concepts:** source criticism; provenance; uncertainty layers.

**Depends on:** HUM-03, AUTH-04, SOC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Optional historically inspired worlds separating records and invention.

**PREDICTION:** Each reconstructed detail is sourced or labeled conjectural.

**FALSIFIER:** An immersive reconstruction claims unwarranted historical certainty.

#### SOC-05 · Human skills and training worlds

**Mathematics/concepts:** task decomposition; motor learning; assessment validity.

**Depends on:** HUM-03, AUTH-04, SOC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded training scenarios with explicit transfer limitations.

**PREDICTION:** Held-out task performance measures claimed skill gains.

**FALSIFIER:** Simulation achievement is treated as a real qualification without validation.

#### SOC-06 · Collective behavior limits

**Mathematics/concepts:** multi-agent dynamics; sensitivity; counterfactuals.

**Depends on:** HUM-03, AUTH-04, SOC-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Ensemble scenarios and model-disagreement reports.

**PREDICTION:** Different plausible assumptions produce visible uncertainty ranges.

**FALSIFIER:** A single simulated future is presented as inevitable human behavior.

### MECH — Machines infrastructure and engineered artifacts

Domain class: **engineering**. Candidate prerequisites: DYN-02, CON-03, MULTI-01.

#### MECH-01 · Mechanisms and transmissions

**Mathematics/concepts:** constraint graphs; gears; bearings; backlash.

**Depends on:** DYN-02, CON-03, MULTI-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Reusable joints/transmissions with work and loss accounting.

**PREDICTION:** Input/output motion and power meet independent mechanism controls.

**FALSIFIER:** Kinematic ratios create unaccounted torque or energy.

#### MECH-02 · Motors pumps and actuators

**Mathematics/concepts:** efficiency maps; operating envelopes; energy conversion.

**Depends on:** DYN-02, CON-03, MULTI-01, MECH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Restricted machines linking electrical/fluid/thermal/mechanical ports.

**PREDICTION:** Power balances and saturation hold over declared domains.

**FALSIFIER:** Idealized machines are advertised as unrestricted real hardware.

#### MECH-03 · Structures and infrastructure

**Mathematics/concepts:** load paths; beams; modal response; foundations.

**Depends on:** DYN-02, CON-03, MULTI-01, MECH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bridges/buildings/pipes as law-backed assemblies.

**PREDICTION:** Canonical load and vibration controls expose structural weaknesses.

**FALSIFIER:** A rendered building is treated as structurally validated.

#### MECH-04 · Tools and fabrication processes

**Mathematics/concepts:** contact cutting; joining; material removal; tolerances.

**Depends on:** DYN-02, CON-03, MULTI-01, MECH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Bounded construction/manufacturing operations.

**PREDICTION:** Material and energy budgets account for joins and removed stock.

**FALSIFIER:** Topology edits silently supply impossible fabrication or strength.

#### MECH-05 · Vehicles and mobility

**Mathematics/concepts:** tire/ground interaction; drag; propulsion; suspension.

**Depends on:** DYN-02, CON-03, MULTI-01, MECH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** One vehicle regime with measured/synthetic parameter records.

**PREDICTION:** Braking, turning and energy controls match the chosen model.

**FALSIFIER:** A controller's desired speed overrides traction and power limits.

#### MECH-06 · Engineering validation boundary

**Mathematics/concepts:** model verification; calibration; uncertainty; intended use.

**Depends on:** DYN-02, CON-03, MULTI-01, MECH-01. **State:** proposed; not a reassignment.

**STATEMENT / deliverable:** Explicit distinction between game mechanisms and engineering tools.

**PREDICTION:** A claimed predictive use has independent domain-specific evidence.

**FALSIFIER:** A game simulation is treated as certification of real-world safety.

## 11. Adoption and first execution

1. GLM preserves the active assignments and their latest checkpoints. This book is an amendment, not a request to restart their work.
2. Reconcile the small current frontier against published evidence: accepted GPU state into engine rendering, the elastic CPU reference, boundary robustness, trace verification and scaling. Do not mass-mark a future domain accepted.
3. Append the current-control section and annex link to the Master list. Preserve its history, corrections and unrelated edits. The prepared diff is against the inspected snapshot; if the branch moved, transplant only this insertion after review.
4. Install the JSON catalogue and read-only query tool. Validate unique IDs, dependency references and acyclicity. Instantiate implementation tasks with actual source, numerical gates and owned scopes only when selected.
5. Use domain search and packet generation to propose a complete milestone for an idle worker. Do not paste the whole book into every agent's context. Include the local dependency frontier, core invariants and relevant evidence.
6. GLM serializes task claims and publication. This edition deliberately has no autonomous write/claim tool. Implementing transactional claims later is GOV-01/GOV-04 work, not a hidden capability of the query script.
7. Build M01 first while the four independent laboratories continue. Integrate their outputs only after source/evidence review. Then choose the next thin integrated slice, usually elastic objects or physical time/contact according to actual readiness.

### Included read-only commands after adoption

```bash
python tools/roadmap_query.py validate
python tools/roadmap_query.py summary
python tools/roadmap_query.py search capillary
python tools/roadmap_query.py show FLU-05
python tools/roadmap_query.py packet ELA-02
python tools/roadmap_query.py ready --state docs/roadmap/task_state.local.json
```

The state file is optional and not shipped as fabricated progress. Its format is described in the tool help and README. `ready` reports eligible planning candidates from the reconciled state; it never authorizes work or claims resources. Existing active assignments continue independently of this draft catalogue.

### The book's own falsifiers

This edition fails as a useful blueprint if it duplicates existing ownership, cannot recover current state, contains cyclic/broken dependencies, lets untested claims become accepted automatically, generates permission beyond the user's instructions, or offers names without actionable deliverables. The included validator checks structural properties only. Physical correctness, architecture decisions and usefulness require the ongoing human/agent review and concrete experiments described above.
