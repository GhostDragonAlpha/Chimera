# CREATURE GRAPH — design note (G2-creature-graph, 2026-09-15)

Fleet lane: GRAPH + REFERENCE DATA. No engine edits, no tools/game_shell/.
Workspace: E:\ChimeraWork\slot-01, branch `astra/tasks/matter-kernel-format-01`,
HEAD 37444cee at start.

## What existed before this run (preserved, per dispatch)

The prior (externally cancelled) dispatch had already written five modules in
`tools/creature_graph/` (schema/store/queries/views/engine_live) and the
verbatim transcription banner in `docs/THE_MEMBRANE_INVENTORY.md` — but NO seed
data (no `data/` directory), no reference-data lane, no projection, no
evidence. This run PRESERVED all five modules, extended them (schema v2.0.0),
and built the missing 90%.

## The substrate

ONE object store, three coordinated views (spatial / physical / roadmap)
projected from it; selecting an object selects the same object in all three.
Modules:

| module | role |
|---|---|
| `tools/creature_graph/schema.py` | kinds, relation types, status ladders, validation, content projection (v2.0.0) |
| `tools/creature_graph/store.py` | the store: objects, typed directed relations (LIST: multiplicity preserved), layout (separate), validation lifecycle + staleness, versioned save/load |
| `tools/creature_graph/queries.py` | the original first-proof query (next work, blockers, proof chain) |
| `tools/creature_graph/gaps.py` | the six gap-query shapes |
| `tools/creature_graph/views.py` | the three projections + select() |
| `tools/creature_graph/engine_live.py` | GET-only live-state client (127.0.0.1:8107/tick_state), band-geometry cell join, inspection records, latency |
| `tools/creature_graph/build_graph.py` | authored seeds -> canonical store (+ optional reference join) |
| `tools/creature_graph/reference_join.py` | creature-side CANDIDATE mappings (explicit join table) |
| `tools/creature_graph/graphify_projection.py` | Graphify-compatible projection export |
| `tools/creature_graph/seed/build_seed.py` | deterministic authoring of the seed files |
| `tools/reference_data/*` | pinned deterministic importers (no LLM rows) |

## The six preserved distinctions (where each lives)

1. **type vs instance** — `type.A1` (definition) vs `inst.band.feet` /
   `inst.comp.thigh_l` (creatures' parts); instances cite
   `classification: "type.A1"`.
2. **intended structure vs observed implementation** — authored seeds vs
   extracted records live in separate files joined by stable IDs; the
   implementation ladder is `specified -> extracted -> geometry_built ->
   simulated -> verified`.
3. **physical connection vs implementation prerequisite** — physical relations
   (inside/bounds_region/attached_to/contains/transmits_force_to/
   carries_signal_to/uses_material/uses_model) MAY cycle (reflex loops,
   action/reaction pairs are real); readiness is computed ONLY on the
   `requires_implementation` subgraph (a DAG, checked); `derived_from` is also
   DAG-checked. No centrality anywhere.
4. **reference assertion vs selected parameter** — reference records (1264
   entities, 63 property assertions, 9 relation types, 30 mapping candidates)
   are status `extracted` and can never satisfy a creature requirement;
   creature parameters are separate `parameter` objects whose selection is an
   explicit adaptation decision with units/source/applicability/validation.
5. **known geometry vs provisional placement vs unknown dimensions** —
   `geometry.is_placeholder` + explicit `unknowns` lists (V0i, boundary
   geometry, cross-sections); `work` items carry NO fabricated extent.
6. **reference pose vs live state vs graph layout** — `spatial` (engine
   coordinates, rest/reference), `data/live_snapshots/` + inspection records
   (live, engine-owned, timestamps only), `store.layout` (drawing coords).
   Schema validation REJECTS layout keys inside `spatial`; the engine is read
   with one light GET per call (no /frame, no LLM in any tick path).

## Membranes, sides, enclosure

Every surface (wall) carries `region_a`/`region_b` (the environment may be one
side: `region.environment`); every compartment volume carries `region_a`. The
shared septa carry TWO bounds_region edges (one per side) while remaining ONE
physical wall. `is this compartment actually enclosed?` is query Q1.

## Validation lifecycle (independent of implementation state)

Evidence records carry `validation: untested|passing|failing|stale` +
`last_result` + `deps` + `captured` (per-dep content versions, sha256 of the
physics-relevant projection). `refresh_validation()` conservatively stales any
evidence whose captured version no longer matches — the previous result stays
visible in `last_result`; a failing CURRENT test stays `failing`. Source
availability never flips anything to passing: `extracted` ranks below
`geometry_built` and never satisfies verification.

## IDs, units, provenance

Stable authored IDs (`type.*`, `inst.*`, `req.*`, `work.*`, `src.*`,
`ref.uberon.UBERON_0000981`, ...) are separate from external dataset IDs
(stored in `external_ids`); every reference record cites its `src.*` via
`derived_from`; schema versions stamped (`2.0.0`); joins happen ONLY on stable
IDs or explicit `mapping` records — name similarity yields `candidate`
mappings (30 of them), never equivalences.

## The central falsifier — what this substrate makes true

"If the graph says a structure exists and works, we must be able to select it,
inspect its physical connections, intervene on it, and observe the predicted
change." This delivery makes SELECT (views.select + stable IDs), INSPECT
(Q1-Q6 + physical view + live join), and EVIDENCE-ATTACH (validation lifecycle
on stable IDs) true and auditable. INTERVENE is the engine lane's half: the
graph points at the existing disconnectable machinery
(`pathway.pressure_to_intent` via the pressure_coupling flag,
`actuator.joint_servos`, force caps) and at AN2's limb partition
(`work.partition_leg_l`, watch git log for "(Agent: AN2-one-honest-limb)") —
linked by stable IDs, not names.

## Numbers on this run

- Store: 1482 objects / 130 relations; authored 110 (42 types, 29 instances,
  20 mechanisms, 18 requirements/tasks/experiences/capabilities) + 67 authored
  relations; reference join adds 1372 records + 23 creature-side candidate
  mappings.
- Acceptance: 28/28 checks pass (items 6-8 fully, graph side of 9-10).
- Live engine (GET-only): 4 cells, sealed, conserve -0.000117%, all four bands
  matched by geometry at v0 to 1e-4; GET latency ~20 ms (NOT the tick path);
  outer tick 300 Hz.
