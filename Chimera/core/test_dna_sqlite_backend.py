"""Standalone assert-script for core/dna_sqlite_backend.py (repo convention).
Run: python core/test_dna_sqlite_backend.py

DB + JSON snapshot are redirected to a temp dir before import.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="chimera_dna_backend_test_"))
os.environ["CHIMERA_DNA_DB"] = str(_tmp / "dna.db")
os.environ["CHIMERA_DNA_SNAPSHOT"] = str(_tmp / "snapshot.json")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import dna_sqlite_backend as be  # noqa: E402

GRAPH = {
    "nodes": [
        {"id": "f1", "type": "FeatureUpdate", "feature_name": "Ground_Sand_Sound",
         "status": "verified", "note": "footsteps land on time"},
        {"id": "g1", "type": "ProfessorGrade", "grade": "B", "feature": "Ground_Sand"},
        {"id": "s1", "type": "SurpriseMoment", "source": "agent",
         "context": "unique_marker_zebra in the telemetry path"},
    ],
    "edges": [
        {"source": "g1", "target": "f1", "type": "grades"},
        {"type": "orphan_edge_no_endpoints"},   # must survive even w/o src/dst
    ],
}


def _reset():
    for p in (be.DNA_DB_PATH, be.DNA_DB_PATH.with_suffix(".db-wal"),
              be.DNA_DB_PATH.with_suffix(".db-shm"), be.JSON_SNAPSHOT):
        if Path(p).exists():
            Path(p).unlink()


def test_roundtrip_is_lossless():
    _reset()
    be.save_graph(GRAPH, write_snapshot=False)
    back = be.load_graph()
    assert len(back["nodes"]) == 3 and len(back["edges"]) == 2, back
    byid = {n["id"]: n for n in back["nodes"]}
    assert byid["f1"] == GRAPH["nodes"][0], "node content must be byte-identical"
    # the endpoint-less edge is preserved
    assert any(e.get("type") == "orphan_edge_no_endpoints" for e in back["edges"])


def test_fts_finds_by_content():
    _reset()
    be.save_graph(GRAPH, write_snapshot=False)
    hits = be.search("unique_marker_zebra")
    assert len(hits) == 1 and hits[0]["id"] == "s1", hits
    # a hyphenated / multi-word term must not throw (FTS operator sanitation)
    assert isinstance(be.search("ground-sand footsteps"), list)


def test_snapshot_written_and_ensure_seeded():
    _reset()
    be.save_graph(GRAPH)                       # writes JSON snapshot too
    assert be.JSON_SNAPSHOT.exists(), "durability snapshot must be written"
    # simulate a fresh clone: db gone, snapshot present -> ensure_seeded rebuilds
    be.DNA_DB_PATH.unlink()
    for suf in (".db-wal", ".db-shm"):
        p = be.DNA_DB_PATH.with_suffix(".db" + suf.replace(".db", ""))
    seeded = be.ensure_seeded()
    assert seeded == 3, f"fresh clone must reseed from snapshot, got {seeded}"
    assert len(be.load_graph()["nodes"]) == 3


def test_real_graph_roundtrip_verify():
    # the module's own fidelity check against the REAL committed graph
    if not be.JSON_SNAPSHOT.exists():
        # in the temp env there's no real snapshot; point at the repo's
        snap = Path(__file__).resolve().parent.parent / "docs" / "chimera_dna_graph.json"
        if not snap.exists():
            print("    (skip: no real snapshot present)")
            return
        r = be._verify_roundtrip(json_path=snap)
    else:
        r = be._verify_roundtrip()
    assert r["lossless"], r


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        _reset()
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} dna_sqlite_backend tests passed")
