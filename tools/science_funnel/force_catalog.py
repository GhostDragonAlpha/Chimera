"""Rebuild the force-origin source catalog offline, or reacquire its exact pins."""
import argparse
import copy
import json
from pathlib import Path
import urllib.request

from .common import canonical, loads, local_file, require, sha
from .pipeline import ingest, verify
from .graph import graph_from, propose

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).parent / "data" / "force_sources"
LOCK = DATA / "sources.lock.json"


def lock():
    data = loads(LOCK.read_bytes())
    require(data.get("schema") == "chimera.force_sources.v1", "force_source_schema")
    require(isinstance(data.get("sources"), list) and data["sources"], "force_sources_missing")
    names = set()
    for art in data["artifacts"]:
        path = art.get("path")
        require(isinstance(path, str) and Path(path).name == path and path not in names,
                "force_source_filename", path)
        names.add(path)
        require(isinstance(art.get("sha256"), str) and len(art["sha256"]) == 64,
                "artifact_pin_required")
    for source in data["sources"]:
        import re
        require(isinstance(source, dict) and
                re.fullmatch(r"[a-z0-9][a-z0-9._-]*", source.get("id", "")),
                "force_source_identity")
        require(source.get("data") in names and
                isinstance(source.get("attachments"), list) and
                all(a in names for a in source["attachments"]), "force_source_artifacts")
    return data


def acquire(destination):
    """Network is confined to explicit source acquisition; offline build never fetches."""
    target = Path(destination).resolve()
    target.mkdir(parents=True, exist_ok=True)
    receipt = []
    for art in lock()["artifacts"]:
        path = target / art["path"]
        if path.exists():
            require(path.is_file() and sha(path.read_bytes()) == art["sha256"],
                    "existing_acquisition_pin_mismatch", art["path"])
            receipt.append({"path": str(path), "status": "verified_existing"})
            continue
        url = art["url"]
        require(isinstance(url, str) and url.startswith("https://"), "source_https_required")
        request = urllib.request.Request(url, headers={"User-Agent": "Livechart/1.0 (Chimera scientific source acquisition)"})
        with urllib.request.urlopen(request, timeout=40) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
        require(len(raw) <= 16 * 1024 * 1024, "source_size_limit")
        require(sha(raw) == art["sha256"], "source_changed_requires_review", art["path"])
        # Exclusive create: another process cannot silently replace a checked result.
        with path.open("xb") as stream:
            stream.write(raw)
        receipt.append({"path": str(path), "status": "downloaded_exact_pin"})
    return receipt


def build(output, source_root=DATA, base_graph=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_root = Path(source_root).resolve()
    manifest_lock = lock()
    artifacts = {a["path"]: a for a in manifest_lock["artifacts"]}
    for name, art in artifacts.items():
        raw = local_file(source_root, name).read_bytes()
        require(len(raw) == art["bytes"] and sha(raw) == art["sha256"], "source_pin_drift", name)
    graph = copy.deepcopy(base_graph) if base_graph is not None else graph_from(
        ROOT / "tools/creature_graph/data/creature_graph.json")
    source_base_hash = graph.graph_hash()
    receipts, assertions = [], []
    for source in manifest_lock["sources"]:
        folder = output / "manifests" / source["id"]
        folder.mkdir(parents=True, exist_ok=True)
        selected = [source["data"]] + source["attachments"]
        for name in selected:
            (folder / name).write_bytes((source_root / name).read_bytes())
        manifest = {
            "schema_version": "1.0.0", "adapter": source["adapter"],
            "source": {k: source[k] for k in ("id", "release", "license", "url", "attribution", "scope")},
            "artifacts": [{"id": name, "path": name, "sha256": artifacts[name]["sha256"],
                           "role": "data" if name == source["data"] else "attachment"}
                          for name in selected],
        }
        manifest_file = folder / "manifest.json"
        manifest_file.write_bytes(canonical(manifest))
        bundle = ingest(manifest_file, output / "bundles")
        data = verify(bundle)
        require(not data["quarantine"], "force_source_quarantined",
                {"source": source["id"], "refusals": data["quarantine"]})
        patch = propose(bundle, graph)
        for obj in patch["payload"]["objects"]:
            graph.add(obj)
        for edge in patch["payload"]["relations"]:
            if not any(all(old.get(k) == v for k, v in edge.items()) for old in graph.relations):
                graph.relate(**edge)
        require(graph.graph_hash() == patch["metadata"]["candidate_graph_hash"], "force_admission_mismatch")
        receipts.append({"source_id": source["id"], "bundle_id": data["receipt"]["bundle_id"],
                         "accepted": len(data["records"]), "quarantined": 0})
        assertions.extend(data["records"])
    require(not graph.check(), "force_catalog_graph_invalid")
    from tools.creature_graph.views import layout_roadmap
    graph.layout = layout_roadmap(graph)
    graph.save(str(output / "force_graph.json"))
    (output / "assertions.json").write_bytes(canonical(assertions))
    result = {"schema": "chimera.force_catalog.v1", "base_graph_hash": source_base_hash,
              "graph_hash": graph.graph_hash(), "source_lock_sha256": sha(LOCK.read_bytes()),
              "sources": receipts, "assertions": len(assertions), "objects": len(graph.objects),
              "relations": len(graph.relations),
              "scope": "Imported assertions and model definitions only; no runtime qualification.",
              "graph_file": str(output / "force_graph.json")}
    (output / "catalog_receipt.json").write_bytes(canonical(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".tmp" / "force-catalog")
    parser.add_argument("--source-root", type=Path, default=DATA)
    parser.add_argument("--acquire", type=Path, help="Download the exact locked source bytes to this directory.")
    args = parser.parse_args(argv)
    result = acquire(args.acquire) if args.acquire else build(args.output, args.source_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
