"""Standalone assert-script for core/world_store.py (repo non-pytest convention).
Run: python core/test_world_store.py

Uses a temp DB via env override so it never touches real world data.
"""
import os
import sys
import tempfile
from pathlib import Path

_db = Path(tempfile.mkdtemp(prefix="chimera_world_test_")) / "w.db"
os.environ["CHIMERA_WORLD_DB"] = str(_db)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import world_store as ws  # noqa: E402


def _fresh():
    if _db.exists():
        _db.unlink()
    return ws.connect(_db)


def test_capabilities_probe():
    con = _fresh()
    caps = con._caps
    assert set(caps) == {"fts5", "rtree"}, caps
    # both are compiled into CPython's bundled SQLite; if a build lacks them the
    # store still works (LIKE / bbox fallback) — this asserts the probe RAN.
    con.close()


def test_add_get_and_neighbors():
    con = _fresh()
    ws.add_nodes(con, [("a", "star", "Sol", 0.0, 0.0, 0.0, {"mass": 1}),
                       ("b", "planet", "Terra", 3.0, 4.0, 0.0, None),
                       ("c", "planet", "Mars", 30.0, 40.0, 0.0, None)])
    ws.add_edges(con, [("b", "a", "orbits", None), ("c", "a", "orbits", None)])
    assert ws.get_node(con, "a")["label"] == "Sol"
    assert ws.get_node(con, "a")["data"] == {"mass": 1}
    ins = {n["id"] for n in ws.neighbors(con, "a", "in")}
    assert ins == {"b", "c"}, ins
    orb = ws.neighbors(con, "b", "out", rel="orbits")
    assert orb == [{"id": "a", "rel": "orbits"}]
    con.close()


def test_fulltext_search_is_the_find_primitive():
    con = _fresh()
    ws.add_nodes(con, [(f"n{i}", "region", f"region_{i}"
                        + (" ancient_beacon" if i == 7 else ""),
                        float(i), 0.0, 0.0, None) for i in range(50)])
    hits = ws.search(con, "ancient_beacon")
    assert len(hits) == 1 and hits[0]["id"] == "n7", hits
    assert len(ws.search(con, "region")) >= 25, "common term should match many"
    con.close()


def test_around_is_the_local_pocket():
    con = _fresh()
    # a cluster at the origin, a far scatter — only the cluster is 'around'
    near = [(f"c{i}", "creature", f"c{i}", i * 0.5, 0.0, 0.0, None) for i in range(20)]
    far = [(f"f{i}", "creature", f"f{i}", 5000.0 + i, 5000.0, 0.0, None) for i in range(20)]
    ws.add_nodes(con, near + far)
    got = ws.around(con, 0.0, 0.0, 6.0)
    ids = {g["id"] for g in got}
    assert all(i.startswith("c") for i in ids), f"far nodes leaked in: {ids}"
    # c_i sits at x=i*0.5, so radius 6.0 includes c0..c12 (x<=6.0), excludes c13 (6.5)
    assert "c0" in ids and "c12" in ids and "c13" not in ids, "radius must clip precisely"
    con.close()


def test_stats_counts():
    con = _fresh()
    ws.add_nodes(con, [("x", "k", "x", 1.0, 1.0, 0.0, None)])
    ws.add_edges(con, [("x", "x", "self", None)])
    s = ws.stats(con)
    assert s["nodes"] == 1 and s["edges"] == 1
    con.close()


def test_scale_smoke_50k():
    # a fast proof the write path holds at scale without the full 1M benchmark
    con = _fresh()
    rows = [(f"s{i}", "node", f"node_{i}", float(i % 100), float(i // 100), 0.0, None)
            for i in range(50_000)]
    ws.add_nodes(con, rows)
    assert ws.stats(con)["nodes"] == 50_000
    # search + spatial still instant at 50k
    ws.add_nodes(con, [("beaconX", "beacon", "lonely_beacon", 0.0, 0.0, 0.0, None)])
    assert ws.search(con, "lonely_beacon")[0]["id"] == "beaconX"
    con.close()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} world_store tests passed")
