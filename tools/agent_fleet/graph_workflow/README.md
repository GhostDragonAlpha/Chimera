# Graph-executed project: bounded prototype

STATEMENT: On the graph-required controller, a worker cannot submit a task for review without a graph-defined checklist, acknowledged read inputs, and trusted-runner checks tied to the submitted source candidate. Parallel submissions cannot silently overwrite the same graph revision.

PREDICTION: missing/failed/foreign/stale proof is refused, a genuine successful runner result reaches REVIEW, and exactly one of two simultaneous updates from the same graph revision succeeds.

FALSIFIERS (preregistered before test execution): any missing or failed check admits review; a worker supplies its own accepted attestation; changed source or graph contract reuses old proof; competing writes both accept a stale revision; document import or projection loses original bytes.

## Authority
The graph-required service imports an existing CreatureGraph once into the existing controller SQLite transaction store. That graph is then authoritative for this service. The input JSON is a bootstrap snapshot, not a second writable authority. `graph_snapshot` exports a complete snapshot. `graph_apply` uses an expected graph hash and the controller's existing lead authorization; SQLite BEGIN IMMEDIATE serializes writes. No second ownership registry is introduced. Parallel workers retain existing scope/claim/generation/resource checks.

This is an isolated prototype, NOT activated against the running product or Kilo. No existing documents are removed. Full project migration, Gaussian rendering, and DSL-to-native generation are not claimed complete.

## Operations
- `graph_snapshot`: authoritative graph plus revision/hash.
- `graph_apply`: lead supplies epoch, expected_hash, objects. Stale revisions, evidence rewriting, and direct verified promotions refuse. Dependency removal requires a future reviewed migration operation; this API only adds dependency mirrors.
- `create_task`: existing envelope plus graph_work. That native work node must have execution_workflow containing statement, prediction, read_first graph document IDs, verifier_inputs mapping approved verifier paths to SHA256, and nonempty checks: {id, falsifier, argv, timeout_s}.
- `workflow_context`: generates the pinned task envelope and assigned worktree.
- `workflow_prepare`: claimed worker supplies task, generation, input_hash, read_hashes. Byte acknowledgement is not proof of comprehension.
- `workflow_attest`: trusted runner only; records passed AND failed checks. Never give its session to workers.
- `workflow_view`: joined graph work IDs, controller claims and checklist/results.
- `submit_review` and integration gates: require matching complete passing proof; review also rechecks the clean candidate. Existing independent publication authorization remains required.

## Run
Use the provisioned controller credentials and an isolated DB/root/port. Do not invent a session or restart an existing controller.

    python tools/agent_fleet/graph_workflow_service.py --root <slots> --db <db> --graph <initial-graph.json> --port <owned-port>

The trusted broker runs graph_workflow_runner.py with its private --session, --task, and a new --out directory outside tracked source. Commands are preregistered graph argv and run without a shell. Candidate source must be committed and clean. Check artifacts are hashed. Ignored assets, toolchains, executable identity, GPU/resource leasing and runtime ownership must be verified by the approved check program; they are not inferred from a Git hash.

## Project memory and space
project_documents.absorb imports immutable, hash-addressed document versions with exact original bytes and searchable text. Imports remain untrusted knowledge, never automatically executable policy. They attach to existing graph IDs; they do not invent physical coordinates. The Graphify projection now preserves complete records and spatial fields.

Physical anchors must reference versioned engine/world frames. Gaussian mean/covariance and render assets are a representation of those anchors; graph identity must survive movement and resplatting. The precise placement of nonphysical project-wide concepts remains an explicit design decision. No synthetic force-layout coordinates are labeled engine measurements.

## Hard boundary
Controller enforcement cannot prevent raw filesystem edits, Git pushes, a new rogue controller, test manipulation, or direct engine access by an agent with those permissions. Protected integration and separate OS identities/credentials are required for adversarial containment. This runner is a trusted broker tool, not a sandbox for hostile commands. It does not kill descendants on timeout or automatically schedule model turns. Runtime harnesses must own and clean up their processes. No scientific claim is proven by an exit code alone.

## Serial authority / parallel execution
Workers read revisions and propose bounded changes. One transaction accepts each graph mutation. On conflict, reread and rebase the proposal; do not overwrite. Work execution remains parallel in isolated checkouts. The graph stores the program/specification and evidence; the existing controller interprets ownership and execution. A complete graph compiler and promotion of verified physical claims require further measured integration.

Verifier files are pinned by the approved graph contract. The runner refuses altered verifier bytes even if a worker commits them. All transitive verifier dependencies must be included; no hash can prove that a weak or malicious approved test is scientifically adequate.

Required reading resolves to losslessly imported document nodes, not competing Markdown authorities. workflow_context includes their hashes; graph_snapshot carries their full content. Historical document versions cannot be rewritten through graph_apply.

## Current architecture decisions (operator, 2026-09-16)
The project graph is the executable specification: documentation, initial membrane state, physics laws, roadmap, work instructions and evidence. README is the eventual external entry point; document deletion waits for complete migration and consumer verification. Existing files are retained during this prototype.

Use one public project graph plus an unadvertised auxiliary verification graph. The latter is loaded into controller memory from an operator-supplied file with an opaque filename, omitted from worker discovery and normal context. `--auxiliary` configures it; only the trusted runner can obtain its instructions. The graph contains objects with pinned verifier_inputs and checks, linked to public work IDs by `verifies` edges. A private failure prevents acceptance even when public tests pass. Restart refuses a changed or removed auxiliary fingerprint. The lead knows it is audited but cannot modify governed acceptance contracts through its ordinary session. Policy changes require independent supervisor authority.

The operator explicitly rejected a third/offline/security repository layer. Existing online Git commit and review records provide human inspection. No additional archive or repository is created here. No remote push has been performed.

Scientific databases supply source assertions into typed object interfaces: identity/anatomy, geometry, material properties, law/model, actuation, transport, sensing, observations. Assertions retain units, applicability conditions, uncertainty, provenance and version. An adapter maps each source to these interfaces; an unknown remains an explicit gap. Ontology relations plus implementation dependencies plus player-facing acceptance determine build order. An ontology alone does not supply forces or prove a feature.

Physics uses local state/update rules on a mixed domain: surface triangles, volumes, bonds/edges, joints and signal paths. Mechanics exchanges momentum, fluids exchange mass, thermal rules exchange energy, signals propagate state. Different quantities are not merged into one scalar force. Geometry, material data, constitutive law and numerical solver are all required. Database records do not by themselves generate stable motion. Gaussian splats provide spatial presentation anchored to persistent graph IDs; their placement and covariance are not substitutes for topology or material behavior.

Near-product fidelity is tested at player interactions: pressing, delayed response, obstruction, falling, cutting, fluid loss. Add resolution where these observations require it. Do not equate more graph nodes or splats with greater physical accuracy.

## Kilo adoption: new-session entry
Project home is E:/PythonChimera. This prototype is isolated in E:/ChimeraWork/codex-graph-workflow-20260916 on codex/graph-workflow-gate, based on 32382a95. Kilo's active native work remains in E:/ChimeraWork/codex-graph-contracts-20260915 and was not edited. Verify actual revisions and ownership; never reset the active worktree to these historical values.

Read the graph program in tools/creature_graph/data/authored/project_program.json and this README. Use up to ten genuinely independent subagents for adapter review, migration inventory, Gaussian frame binding, DSL planning, numerical-interface review, fixture tests, integration review and evidence checks. One owner per writable file and one writer for graph transactions. Keep native hydraulic work independent. Complicated native solver changes require a focused Codex packet with a reproduction.

Next bounded milestone: qualify one real engine task end to end through the graph-required controller on a provisioned isolated endpoint. Register its independently approved checklist and immutable graph reading, claim it, run its pinned checks, prove failed and stale candidates are rejected, submit the passing candidate for review, export the graph to the real consumer, and record exact source and executable identity. Do not treat these controller fixture tests as engine or product qualification. Full documentation migration, live Graphify adoption, Gaussian rendering, native code generation and resource-aware automatic model dispatch remain open graph tasks.
