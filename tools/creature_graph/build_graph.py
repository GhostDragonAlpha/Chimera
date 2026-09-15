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


def build(with_reference: bool = False) -> CreatureGraph:
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
    # Captures are historical measurement inputs, never build products.
    g.sync_dependencies()
    g.meta["schema_version"] = SCHEMA_VERSION
    g.meta["built_from"] = input_hashes
    g.meta["built_utc"] = None  # determinism: stamped by save(), not by build
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
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    g = build(with_reference=args.with_reference)
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
