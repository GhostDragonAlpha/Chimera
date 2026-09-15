# BRIDGE_REPORT — F3 graphify-consumer (2026-09-15)

Branch `glm53/graph-consumer` (off a12bfbcc). Agent: F3-graphify-consumer.

## VERDICT

**The consumer bridge EXISTS, RUNS, and is HONEST.** One command:

```
python tools/creature_graph/graphify_consumer.py
```

round-trips the creature graph's projection through the REAL Graphify
machinery (`Chimera/core/graphify_interface.py` + `dna_sqlite_backend.py`)
and answers **HONEST — the consumer round-trips the projection** on every
check. Before this landed, nothing had ever shown a Graphify surface
consuming the projection; the integration claim is now demonstrated
end-to-end: export → schema gate → sanitizer pre-check → ingest through
`save_dna_graph` → queries back through `load_dna_graph` /
`graphify_query("health")` / `because_of` / FTS search — with per-object and
per-relation identity verified against the native store.

Measured on the final run: 1,486 objects / 141 relations exported, gated,
ingested (+1,486/+141 into a scratch Graphify store), and verified 1486/1486
node identities, 141/141 edge identities with direction and notes intact,
2-hop traversal parity, health total exact, re-run idempotent.

## 1. DISCOVERY MAP — the ACTUAL installed Graphify (all read and measured)

"Graphify" in this repo is **not an external library**. It is the in-repo
machinery under `Chimera/core/` (worktree copy verified byte-identical to
E:\PythonChimera's at a12bfbcc, sha256 aba3840e1c8b interface / ad8dd63867b9
record):

| Surface | Entry point | What it accepts/exposes |
|---|---|---|
| Unified query dispatcher | `graphify_interface.graphify_query(type, id, ctx)` | pattern, file, mutation, community, chain, config, campus, health, feature, pathway, gpa — all DNA-graph-native |
| Unified mutation dispatcher | `graphify_interface.graphify_mutate(type, result, details)` | ~30 typed mutations (compilation, feature_complete, pathway_attempt, …) |
| Typed recorders | `graphify_record.py` CLI + `record_*` helpers | append typed nodes; refusals returned as `rejected_*` strings |
| Why-edges | `because_edge` / `record_because` / `because_of` | edge dict DUAL-KEYED: `src/dst/rel` + `source/target/type`; `proves` restricted to `BECAUSE_PROVES = (EXISTENCE, RECORDED, DISPATCH, MEASURED, HUMAN)`; `record_because` validates BOTH endpoints exist |
| Store seam | `load_dna_graph` / `save_dna_graph` | `{"nodes":[...], "edges":[...]}` dicts; node = `{id, type, timestamp, ...arbitrary}`; SQLite backend default (`CHIMERA_DNA_DB`, `CHIMERA_DNA_SNAPSHOT` env-overridable), JSON fallback; save = provenance stamp + atomic replace-all + snapshot |
| ID mint | `hash_node_id(type, id)` | `sha256("type:id")[:16]` |
| Search | `dna_sqlite_backend.search` (FTS5, world_store substrate) | indexes keys `name, feature_name, fix_description, context, reality, type, status, grade, phase, target_action` — **`label` is NOT indexed** |
| Derived artifact | `Chimera/core/graphify-out/graph.json` | the OLD knowledge graph (AST + feature updates, `directed:false, multigraph:false`) — **not** this integration (matches the BASELINE note) |

Ruled out: no `graphify` pip package is installed or imported anywhere; the
incidental dist `graphifyy 0.9.5` (an AI-assistant skill) is never imported
by the repo and is unrelated.

**The gap the brief predicted is real**: `graphify_interface` has NO
ingestion path for a node-link projection — every write path assumes
hand-built DNA dicts. The bridge supplies exactly that missing step,
mechanically.

## 2. THE BRIDGE (`tools/creature_graph/graphify_consumer.py`)

### IMPLEMENTED (and exercised)
- **Schema gate (falsifier a)** — `load_projection()`: refuses BEFORE load on
  `directed`/`multigraph` not true, `schema_version != "2.0.0"` (legacy
  `1.0.0-unversioned` named and refused), missing/mismatched `id_map`,
  duplicate node ids, nodes missing label/kind/status/`_authored_id`, edges
  with missing endpoints or the reserved `because` rel. Collects ALL
  violations per load.
- **Sanitizer pre-check (falsifier c)** — `id_collision_report()` inverts
  `id_map`; any sanitized id claimed by 2+ native ids REFUSES ingestion
  (identity would collapse). Collision-safe alternative is not improvised
  here — routed to the packet (below).
- **Ingestion through the real write path** — `projection_to_dna()` +
  `ingest()`: nodes keep every projection field verbatim + `type:
  "CreatureObject"` + `name` (FTS alias) + `timestamp` (projection's
  `generated_utc`) + `origin` marker; edges are dual-keyed exactly like
  `because_edge` builds them, WITHOUT because-semantics; write goes through
  `save_dna_graph` (provenance stamp, atomic sqlite replace-all, snapshot).
  Idempotent: prior projection rows are replaced, never stacked.
- **Round-trip verification (falsifier b)** — `verify()` queries everything
  back through the consumer store: ALL objects reversible via `_authored_id`
  with label/kind/status equal; ALL relations as a multiset over native ids
  (direction + note); per-(src,rel,dst) multiplicity totals; 2-hop BFS
  traversal parity from the max-degree node; `graphify_query("health")`
  total exact (and creature nodes pollute no DNA family:
  mutations/pathways/features stay 0 on the scratch store); `because_of`
  honestly `[]`; FTS search finds an ingested node by name.
- **Scratch-store guard** — pins `CHIMERA_DNA_BACKEND=sqlite` +
  `CHIMERA_DNA_DB`/`CHIMERA_DNA_SNAPSHOT` under
  `data/graphify_demo/` BEFORE core import; asserts the pin took effect.
  Operator may set `CHIMERA_DNA_DB` to aim elsewhere. Nothing outside
  `data/graphify_demo/` is written (verified by git status: no Chimera/ or
  canonical-store changes from this agent).

### MEASURED (numbers, this session)
- Committed projection artifact (branch base): 1,482 nodes / 130 edges,
  schema 2.0.0, sanitizer collisions **0**.
- Current store (a concurrent lane modified authored inputs mid-session):
  1,486 objects / 141 relations; fresh export + full round-trip **HONEST**;
  re-run idempotent (store stays 1,486/141, `nodes_replaced: 1486`).
- Adversarial: tampered projection (wrong version, `directed:false`,
  duplicate node, `because` edge, dangling endpoint) → REFUSED with 5 named
  violations; synthetic collision map → 1 collision found; missing file →
  refused.
- **Drift detection** (bonus, measured): ingesting the STALE committed
  1482/130 projection and verifying against the current 1486/141 native
  store correctly FAILS edge identity + multiplicity (the concurrent lane's
  11 new `verified_by` relations missing) — a stale projection cannot pass
  as current. The bridge is honest in both directions.

### INFERRED (not separately demonstrated)
- That the interface's stamping treats a node without `timestamp` as
  `legacy_pre_provenance` (read from `_stamp_provenance`; the bridge sets
  `timestamp` so ingested nodes get real `recorded_by` provenance instead).
- That `graphifyy 0.9.5` is unrelated (dist metadata inspected; never
  imported by the repo).

### NOT_TESTED
- The other 10 `graphify_query` types against ingested nodes (only
  `health` exercised; feature/pathway/mutation scans match by node type,
  which creature nodes deliberately do not claim).
- The JSON DNA backend (bridge refuses it — its path is the worktree's real
  tracked snapshot).
- Ingestion into the PRODUCTION DNA store (read-only canonical root; also a
  policy decision, see packet).
- The `record_*` mutation helpers (untouched by design — creature edges must
  not fake why-provenance), MCP/engine surfaces, networkx-based layouts.

## 3. CODEX-PACKET ADDITIONS (semantic repairs — not landed here)

1. **Exporter sanitizer is not injective (D3 #5, LATENT).**
   `graphify_projection.py:36 _sanitize()` lowercases and maps all
   non-`[a-z0-9_]` to `_`; distinct native ids can collapse
   (`membrane.A` vs `membrane_a`). Measured today: 0 collisions on both the
   1482-object committed projection and the 1486-object current store — the
   defect is live in code, dormant in data. The bridge's pre-check refuses
   to ingest on collision; the exporter itself should mint collision-safe
   ids (deterministic disambiguator) and keep the reversible map. NOT fixed
   here: the exporter is under active reproduction by F2, whose harness is
   green-on-defective-base and turns RED the moment a repair lands.
2. **Projection edges carry the sort-index `key`, not the native `rid`.**
   Cross-boundary identity is multiset-level, not rid-level. Mechanical
   exporter repair: include `rid` in each exported edge (backward
   compatible).
3. **No ingestion API in `graphify_interface`.** If the projection
   integration is meant to be first-class, a schema-gated
   `graphify_ingest_projection()` belongs in the interface; this bridge's
   `projection_to_dna()`/`ingest()` (~60 lines) is the reference
   implementation to lift.
4. **`_searchable_text` does not index `label`**, so Graphify FTS cannot
   find nodes by their display name unless consumers alias `name=label`
   (the bridge does). Either add `label` to the indexed key list or document
   the alias — a decision on the shared index, not this bridge's to make.
5. **Policy: production-store ingestion.** Pointing the bridge at the
   shared DNA store (vs scratch) is a storage/semantics decision — the
   bridge defaults to scratch and honors `CHIMERA_DNA_DB`.

## 4. WRITER-CONFLICT NOTE (preserved, isolated)

Two concurrent writers were active in this worktree during this task and are
UNTouched by this commit: (a) F2's untracked `tools/creature_graph/tests/`
(fixtures + harness, created 15:05–15:06 mid-session); (b) the lead's
creature-graph data lane — observed here as uncommitted modifications that
drifted the store 1482/130 → 1486/141 between this agent's first and second
builds (measured, and turned into the drift-detection demonstration above),
then landed by glm53-lead-02 as commit `1f3c062c` ON this branch while this
agent's files were staged ("Attach codex limb-runtime evidence to creature
graph (scoped)": 4 evidence records + 11 `verified_by` edges — exactly the
delta the drift demo caught). This commit adds ONLY:
`graphify_consumer.py`, `BRIDGE_REPORT.md`,
`data/graphify_demo/consumer_demo_report.json`. The scratch store db,
snapshot, and demo projection copy under `data/graphify_demo/` are
machine-local, untracked, and regenerable by the one command.
