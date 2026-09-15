# HANDOFF — G2-creature-graph (2026-09-15)

## Changed files (all inside this lane's owned paths)

```
tools/creature_graph/
  schema.py                    EXTENDED  kinds+relations (bounds_region, contains,
                                         uses_material, uses_model, derived_from),
                                         schema v2.0.0, layout-in-spatial guard,
                                         content projection
  store.py                     EXTENDED  relation ids+multiplicity, schema stamping,
                                         validation lifecycle (stale), graph_hash,
                                         enables-field sync
  queries.py                   kept      (original first-proof query, unchanged)
  views.py                     kept      (works off the renamed REL_BOUNDS constant)
  engine_live.py               EXTENDED  band-geometry cell join, inspection records,
                                         GET latency measurement; still GET-only
  gaps.py                      NEW       the six gap-query shapes
  graphify_projection.py       NEW       Graphify-compatible projection exporter
  reference_join.py            NEW       creature-side CANDIDATE mappings
  build_graph.py               NEW       seeds -> canonical store CLI
  seed/build_seed.py           NEW       deterministic authoring of the seed files
  data/authored/*.json         NEW       5 authored seed files (110 objects + 67 relations)
  data/creature_graph.json     NEW       the canonical store (1482 objects, 130 relations)
  data/graphify_projection/    NEW       the exported projection (node-link multigraph)
  data/.gitignore              NEW       live_snapshots/ + __pycache__ not tracked

tools/reference_data/
  sources.py                   NEW       pinned source registry (releases, licenses)
  fetch_cache.py               NEW       pin-verified caching, concurrent fetch
  parsers.py                   NEW       deterministic OBO / RO-OWL / QUDT-TTL / OSIM-XML
  import_reference.py          NEW       the 7 record families, idempotent merge
  run_import.py                NEW       CLI
  data/pins.json               NEW       first-fetch sha256 pins
  data/reference_store.json    NEW       1348 reference records
  data/import_provenance.json  NEW       provenance table of record
  data/.gitignore              NEW       cache/ (raw downloads) not tracked

docs/THE_MEMBRANE_INVENTORY.md AMENDED  provenance banner: continuation note
docs/evidence/agent_fleet/SHIP/CREATURE_GRAPH/
  DESIGN.md                    NEW  design note (substrate shape, the six distinctions)
  IMPORT_PROVENANCE.md         NEW  exact sources/releases/checksums/licenses/gaps
  SIX_QUERIES.md               NEW  the six query outputs on the seeded graph
  acceptance_results.json      NEW  28/28 machine checks (items 6-8, graph side 9-10)
  inspection_record_example.json NEW consistent-ID/timestamp live join example
  HANDOFF.md                   NEW  this file
```

## How to launch the inspection / reproduce

```bash
cd E:\ChimeraWork\slot-01

# 1. rebuild everything from scratch (deterministic, idempotent):
python tools/reference_data/run_import.py          # pinned fetch+verify, 2nd run = no-op
python tools/creature_graph/seed/build_seed.py     # rewrite authored seeds (byte-identical)
python tools/creature_graph/build_graph.py --with-reference
python tools/creature_graph/acceptance.py          # 28 checks -> evidence JSON

# 2. inspect (engine optional; live engine on 8107 is read via GET only):
python - <<'EOF'
import sys; sys.path.insert(0, r"tools\creature_graph")
from store import CreatureGraph
import views, gaps
g = CreatureGraph.load()
print(views.select(g, "inst.comp.thigh_l"))        # select in all three views
print(gaps.run_all_six(g)["q6_next_ready_task"])   # the gap queries
EOF
```

Interventions themselves live in the ENGINE lane (POST routes on a scratch
engine; this lane stays GET-only). The graph side that the demonstration must
keep honest: `pathway.pressure_to_intent` (disconnectable, negative control),
`ev.reflex_controls_fail` (the failing control that must stay visible), and
the acceptance tests on `inst.comp.*` / `memb.septum.*` objects — attach new
evidence to those SAME stable IDs.

## The next five graph-backed tasks (with the evidence each adds)

1. **work.partition_leg_l** (ready, authored priority 1) — AN2's volumetric
   partition of the left leg from the measured pins. Evidence added: per-bone
   V0i + closure/coverage/conservation numbers; `inst.comp.*` flip
   specified -> geometry_built; Q1's "boundary pending build" verdicts become
   measurable.
2. **work.septa_leg_l** (ready, priority 2) — the two shared oblique septa as
   load-bearing walls (one wall, two owners). Evidence added: puncture-a-neighbor
   isolation test results attached to `memb.septum.thigh_l_shin_l` /
   `memb.septum.shin_l_foot_l`; Q1's per-bone verdicts go "physically bounded".
3. **work.causal_demo_leg_l** (ready, priority 3) — the honest intervention
   (obstruct actuator / disconnect `pathway.pressure_to_intent`) on existing
   machinery. Evidence added: pressure-trace + intent-log pairs keyed by the
   same stable IDs + engine ticks (acceptance 4/5), flipping
   `ev.reflex_controls_fail` toward passing or keeping it honestly failing.
4. **work.reference_adaptation_osim** (ready, priority 4) — confirm/reject the
   30 CANDIDATE mappings (human decision), then select at most a handful of
   OpenSim parameters with applicability + validation plans. Evidence added:
   mapping records become equivalence/analogue decisions; Q3's gap list
   shrinks only where real validation landed.
5. **work.inspect_consistent_ids** (ready, priority 5) — one inspection UI
   surface joining structure + pressure + intervention records (the graph
   already emits the join format: `inspection_record_example.json`). Evidence
   added: measured end-to-end latency + sampling disclosure against
   acceptance 9's presentation bar.

Standing note for the next agent: `python tools/creature_graph/acceptance.py`
must stay 28/28 green; anything that turns a check red either broke a
contract above or found a real defect — both are findings, not noise.

(Agent: G2-creature-graph)
