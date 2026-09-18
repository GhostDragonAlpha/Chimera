"""Build the canonical authored creature-graph store.

Loads the authored seed files (data/authored/*.json), preserves each evidence
record's measurement capture, syncs dependency/evidence mirrors, runs
the integrity check, and saves data/creature_graph.json.

Deterministic and idempotent: same authored inputs -> identical store bytes
(same graph hash). Reference-data joins (tools/reference_data) are applied
with --with-reference and add ONLY reference-family objects + explicit
candidate mapping records; they never overwrite authored content.

Usage:
  python build_graph.py [--with-reference] [--check-only]
"""

import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from schema import SCHEMA_VERSION  # noqa: E402
from store import CreatureGraph, content_version  # noqa: E402

AUTHORED_DIR = os.path.join(HERE, "data", "authored")
AUTHORED_FILES = ["types.json", "instances.json", "mechanisms.json",
                  "requirements_tasks.json", "relations.json"]
EXTRACTED_DIR = os.path.join(HERE, "data", "extracted")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_record_shard(path: str):
    """Read/hash one independent authored shard without touching graph state."""
    with open(path, encoding="utf-8") as stream:
        shard = json.load(stream)
    return os.path.basename(path), _sha256_file(path), shard


def _worker_count(workers, jobs: int) -> int:
    if workers is None:
        workers = os.environ.get("CHIMERA_GRAPH_WORKERS", "1")
    workers = int(workers)
    if workers < 1:
        raise ValueError(f"graph workers must be >= 1, got {workers}")
    return min(workers, max(1, jobs))


def build(with_reference: bool = False, workers=None) -> CreatureGraph:
    g = CreatureGraph()
    input_hashes = {}
    # authored objects
    for fname in AUTHORED_FILES:
        path = os.path.join(AUTHORED_DIR, fname)
        input_hashes[f"authored/{fname}"] = _sha256_file(path)
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        if fname == "relations.json":
            for r in payload:
                g.relate(r["src"], r["rel"], r["dst"], r.get("note", ""))
        else:
            for obj in payload:
                g.add(obj)
    # Optional project program: versioned documentation, workflow and typed
    # scientific interfaces share the same authored graph, never a second board.
    program_path = os.path.join(AUTHORED_DIR, "project_program.json")
    deferred_edges = []
    if os.path.exists(program_path):
        input_hashes["authored/project_program.json"] = _sha256_file(program_path)
        with open(program_path, encoding="utf-8") as stream:
            program = json.load(stream)
        for obj in program["objects"]:
            g.add(obj)
        deferred_edges.extend(program.get("relations", []))
    # Authored record shards: bulk reference families admitted by batch lanes
    # (work.data.graph_store_split) -- the program file stays small and
    # hand-editable while the bulk rotates in sibling files.
    records_dir = os.path.join(AUTHORED_DIR, "records")
    if os.path.isdir(records_dir):
<<<<<<< HEAD
        for fname in sorted(os.listdir(records_dir)):
            if not (fname.startswith("records_") and fname.endswith(".json")):
                continue  # only the serial writer's rotation pattern
            shard_path = os.path.join(records_dir, fname)
            input_hashes[f"authored/records/{fname}"] = _sha256_file(shard_path)
            with open(shard_path, encoding="utf-8") as stream:
                shard = json.load(stream)
=======
        shard_paths = [os.path.join(records_dir, fname)
                       for fname in sorted(os.listdir(records_dir))
                       if fname.endswith(".json")]
        count = _worker_count(workers, len(shard_paths)) if shard_paths else 1
        if count == 1:
            loaded = [_load_record_shard(path) for path in shard_paths]
        else:
            # Disk/XML-sized shard reads overlap; graph mutation remains below,
            # deterministic and single-threaded in sorted filename order.
            with ThreadPoolExecutor(max_workers=count) as pool:
                loaded = list(pool.map(_load_record_shard, shard_paths))
        for fname, digest, shard in loaded:
            input_hashes[f"authored/records/{fname}"] = digest
>>>>>>> origin/lane/visual-proof-wave2-20260918
            for obj in shard.get("objects", []):
                g.add(obj)
            deferred_edges.extend(shard.get("relations", []))
    # relations last: program edges may reference sharded endpoints and vice versa
    for edge in deferred_edges:
        g.relate(edge["src"], edge["rel"], edge["dst"], edge.get("note", ""))
    # Captures are historical measurement inputs, never build products.
    g.sync_dependencies()
    g.meta["schema_version"] = SCHEMA_VERSION
    g.meta["built_from"] = input_hashes
    g.meta["built_utc"] = None  # determinism: stamped by save(), not by build
    # Class contracts: one RULE 0 membrane per (source x record class); records
    # reference a contract by id+version and are proven by its mechanical checks.
    contracts_path = os.path.join(AUTHORED_DIR, "class_contracts.json")
    if os.path.exists(contracts_path):
        input_hashes["authored/class_contracts.json"] = _sha256_file(contracts_path)
        with open(contracts_path, encoding="utf-8") as f:
            from schema import validate_class_contracts
            registry = validate_class_contracts(json.load(f))
        g.meta["class_contracts"] = {cid: {
            "version": c["version"],
            "sha256": hashlib.sha256(
                json.dumps(c, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        } for cid, c in sorted(registry.items())}
        for oid, obj in g.objects.items():
            cc = obj.get("class_contract")
            if cc is None:
                continue
            contract = registry.get(cc.get("class_id"))
            if contract is None:
                raise SystemExit(f"store check FAILED:\n  {oid}: unknown class_contract "
                                 f"{cc.get('class_id')!r}")
            if contract["version"] != cc.get("version"):
                raise SystemExit(f"store check FAILED:\n  {oid}: class_contract version "
                                 f"{cc.get('version')!r} != registry {contract['version']}")
            if obj.get("kind") not in contract["applies_to"]["kinds"]:
                raise SystemExit(f"store check FAILED:\n  {oid}: kind {obj.get('kind')!r} "
                                 f"outside contract {cc['class_id']} applies_to")
    if with_reference:
        join_reference(g)
    g.refresh_validation(stamp=False)
    errs = g.check()
    if errs:
        raise SystemExit("store check FAILED:\n  " + "\n  ".join(errs))
    # deterministic roadmap layout (SEPARATE from engine coordinates, enforced
    # by schema validation)
    from views import layout_roadmap
    g.layout = layout_roadmap(g)
    return g


def join_reference(g: CreatureGraph) -> None:
    """Add reference-data records + explicit CANDIDATE mappings to the store.

    Automatic joins happen ONLY on stable IDs or explicit mapping records; name
    similarity produces CANDIDATES that are NEVER equivalences and NEVER
    overwrite authored creature content."""
    ref_path = os.path.join(HERE, "..", "reference_data", "data",
                            "reference_store.json")
    if not os.path.exists(ref_path):
        print(f"[join] no reference store at {os.path.normpath(ref_path)} -- "
              f"run tools/reference_data/run_import.py first; skipping")
        return
    with open(ref_path, encoding="utf-8") as f:
        ref = json.load(f)
    added = 0
    for obj in ref["objects"]:
        if obj["id"] in g.objects:
            continue  # idempotent join: never duplicate, never overwrite
        g.add(obj)
        added += 1
    # candidate mappings computed deterministically on exact name tokens
    from reference_join import candidate_mappings  # local import
    n_map = 0
    for m in candidate_mappings(g, ref["objects"]):
        if m["id"] not in g.objects:
            g.add(m)
            for s, r, d, note in m.pop("_edges", []):
                g.relate(s, r, d, note)
            n_map += 1
    print(f"[join] reference objects added: {added}; candidate mappings: {n_map}")
    g.meta["reference_join"] = {"source": os.path.normpath(ref_path),
                                "sha256": _sha256_file(ref_path)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--with-reference", action="store_true",
                    help="join the reference-data store (explicit mappings only)")
    ap.add_argument("--workers", type=int, default=None,
                    help="parallel authored-shard readers; graph insertion stays serial")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    g = build(with_reference=args.with_reference, workers=args.workers)
    print(f"objects: {len(g.objects)}  relations: {len(g.relations)}")
    kinds = {}
    for o in g.objects.values():
        kinds[o["kind"]] = kinds.get(o["kind"], 0) + 1
    for k in sorted(kinds):
        print(f"  {k:20s} {kinds[k]}")
    if args.check_only:
        return
    path = g.save()
    print(f"saved {os.path.normpath(path)}  graph_hash={g.graph_hash()[:16]}")


if __name__ == "__main__":
    main()
