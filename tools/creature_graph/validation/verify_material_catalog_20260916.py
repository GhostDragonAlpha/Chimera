"""Recheck the material/LOD graph addition without changing graph or engine state."""
import argparse
import copy
import hashlib
import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
from tools.creature_graph import project_spec as spec
from tools.creature_graph.build_graph import build
from tools.creature_graph.store import CreatureGraph
from tools.creature_graph import graphify_consumer as consumer
from tools.creature_graph import graphify_projection as projection

BASE = "7621ad33224ead6094856b96877ada9873ac5074"
STORE = "tools/creature_graph/data/creature_graph.json"
PROGRAM = "tools/creature_graph/data/authored/project_program.json"
REPORT = "tools/creature_graph/validation/material_catalog_20260916.json"
PUBCHEM = "tools/science_funnel/data/pubchem/periodic_table.json"
RECEIPT = "tools/science_funnel/data/pubchem/download_receipt.json"
SELF = "tools/creature_graph/validation/verify_material_catalog_20260916.py"
FILES = [".gitattributes", "README.md", STORE, PROGRAM, PUBCHEM, RECEIPT, SELF]
IDS = ["req.material_catalog", "concept.reduced_cell_state",
       "req.matter_variables_lod", "req.element_identity_spine",
       "req.fundamental_force_scope"]


def git(*args):
    return subprocess.check_output(
        ["git", "-c", "safe.directory=" + ROOT.as_posix(), *args], cwd=ROOT)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(phase):
    checks = []
    def require(name, passed, detail):
        checks.append({"check": name, "pass": bool(passed), "detail": detail})
        if not passed:
            raise AssertionError(json.dumps(checks[-1]))

    before_files = {f: sha((ROOT / f).read_bytes()) for f in FILES}
    g = CreatureGraph.load(str(ROOT / STORE))
    base = json.loads(git("show", BASE + ":" + STORE))
    require("schema_and_admission", not spec.check(g), spec.check(g))
    changed = [oid for oid, obj in base["objects"].items() if g.objects.get(oid) != obj]
    require("all_prior_objects_preserved", not changed,
            {"prior_count": len(base["objects"]), "changed": changed})
    current_edges = {r["rid"]: r for r in g.relations}
    require("all_prior_relations_preserved",
            all(current_edges.get(r["rid"]) == r for r in base["relations"]),
            {"prior_count": len(base["relations"])})
    evidence = [o for o in base["objects"].values() if o["kind"] == "evidence"]
    require("historical_evidence_unchanged", all(g.get(o["id"]) == o for o in evidence),
            {"count": len(evidence), "scope": "No old captures, statuses or results rewritten."})
    added = [o for oid, o in g.objects.items() if oid not in base["objects"]]
    admitted = [o for o in added if spec.active(o)]
    require("new_specs_are_requirements_not_proof",
            len(admitted) == 7 and all(o["status"] == "specified" and
            o["falsifier"]["status"] == "untested" for o in admitted),
            [o["id"] for o in admitted])
    mats = [o for o in added if o["id"].startswith("material.catalog.")]
    require("23_candidate_material_profiles", len(mats) == 23 and
            all(o["status"] == "specified" for o in mats), [o["id"] for o in mats])
    raw = (ROOT / PUBCHEM).read_bytes()
    receipt = json.loads((ROOT / RECEIPT).read_text(encoding="utf-8"))
    table = json.loads(raw)["Table"]
    columns = table["Columns"]["Column"]
    rows = table["Row"]
    require("pinned_upstream_bytes",
            sha(raw) == receipt["sha256"] and len(raw) == receipt["bytes"],
            {"sha256": sha(raw), "bytes": len(raw)})
    require("periodic_table_shape", len(columns) == len(set(columns)) and
            len(rows) == 118 and all(len(r["Cell"]) == len(columns) for r in rows),
            {"columns": len(columns), "rows": len(rows)})
    records = [dict(zip(columns, r["Cell"])) for r in rows]
    require("118_unique_element_identities",
            sorted(int(r["AtomicNumber"]) for r in records) == list(range(1, 119)) and
            len({r["Symbol"] for r in records}) == 118, {"elements": 118})
    for row in records:
        oid = "ref.element.atomic_number." + row["AtomicNumber"]
        obj = g.get(oid)
        assert obj["reference_payload"]["raw_source_cells"] == row
        assert obj["reference_payload"]["runtime_ready"] is False
        assert obj["provenance"]["artifact_sha256"] == receipt["sha256"]
        assert obj["external_ids"]["symbol"] == row["Symbol"]
    require("element_provenance_and_unqualified_numeric_boundary", True, {"elements": 118})
    for mid, counts in [("water", {"H": 2, "O": 1}),
                        ("ethanol", {"C": 2, "H": 6, "O": 1})]:
        assert g.get("material.catalog." + mid)["physical"]["composition"]["atom_counts"] == counts
    require("pure_compound_composition", True, ["H2O", "C2H6O"])
    with redirect_stdout(io.StringIO()):
        rebuilt = build(with_reference=True)
        repeated = build(with_reference=True)
    require("deterministic_rebuild", rebuilt.graph_hash() == repeated.graph_hash(),
            {"hash": rebuilt.graph_hash()})
    effective = copy.deepcopy(g)
    effective.refresh_validation(stamp=False)
    require("rebuild_retains_all_records_and_edges",
            rebuilt.objects == effective.objects and
            sorted(rebuilt.relations, key=lambda r: r["rid"]) ==
            sorted(effective.relations, key=lambda r: r["rid"]),
            {"objects": len(rebuilt.objects), "relations": len(rebuilt.relations),
             "note": "Compare effective freshness; stored historical captures stay unchanged."})
    reader_args = [["--check"], ["--next"]] + [["--show", oid] for oid in IDS]
    for args in reader_args:
        with redirect_stdout(io.StringIO()):
            assert spec.main(["--store", str(ROOT / STORE), *args]) == 0
    require("readme_reader_commands", True, reader_args)
    for oid in ("work.encapsulation.material_profiles", "work.encapsulation.cell_response_reduction"):
        assert spec.checklist(g, oid)["dispatchable"] is False
    require("no_invented_workflow_readiness", True, "New work remains nondispatchable without its checklist.")
    suite = unittest.defaultTestLoader.loadTestsFromName(
        "tools.creature_graph.tests.test_project_spec")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    require("reader_contract_tests", result.wasSuccessful(),
            {"run": result.testsRun, "output": stream.getvalue()})
    private = ROOT / ".tmp" / ("material-catalog-consumer-" +
                               datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
    consumer.DEMO_DIR = str(private)
    consumer.DEMO_DB = str(private / "graph.db")
    consumer.DEMO_SNAPSHOT = str(private / "snapshot.json")
    projected = copy.deepcopy(g)
    proj = projection.make_projection(projected)
    consumer.validate_projection(proj, projected)
    gi, dna = consumer.load_graphify()
    ingest = consumer.ingest_projection(gi, proj, projected)
    round_trip, ok = consumer.verify(projected, proj, gi, dna, ingest)
    require("real_graphify_round_trip", ok, round_trip)
    require("checks_did_not_modify_inputs",
            before_files == {f: sha((ROOT / f).read_bytes()) for f in FILES}, before_files)
    head = git("rev-parse", "HEAD").decode().strip()
    report = {
        "schema": "chimera.material_catalog_validation.v1",
        "scope": "Repository specification/data identity checks; no new runtime physics qualification.",
        "phase": phase, "checked_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": BASE, "candidate_commit": head if phase == "committed_candidate" else None,
        "graph_hash": g.graph_hash(), "effective_graph_hash": effective.graph_hash(),
        "objects": len(g.objects), "relations": len(g.relations),
        "active_specifications": sum(spec.active(o) for o in g.objects.values()),
        "candidate_materials": len(mats), "element_identities": len(records),
        "file_sha256": before_files, "checks": checks, "all_pass": True,
        "consumer_store": str(private / "graph.db"),
        "deployment": "Local repository only; no controller admission, engine restart or push.",
        "earlier_attempt": "The initial material builder rejected a missing hypothesis priority before writing graph files; the corrected builder passed admission."
    }
    if phase == "committed_candidate":
        dirty = git("diff", "--name-only", "HEAD", "--", *FILES).decode().strip()
        assert not dirty, dirty
        report["candidate_tree"] = git("rev-parse", "HEAD^{tree}").decode().strip()
        report["git_blob_ids"] = {f: git("rev-parse", "HEAD:" + f).decode().strip() for f in FILES}
    (ROOT / REPORT).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8", newline="\n")
    print(json.dumps({"all_pass": True, "checks": len(checks), "objects": len(g.objects),
                      "relations": len(g.relations), "graph_hash": g.graph_hash(),
                      "phase": phase, "report": REPORT}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["preflight", "committed_candidate"], default="preflight")
    run(parser.parse_args().phase)
