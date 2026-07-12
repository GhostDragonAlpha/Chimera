"""Standalone assert-script for core/fractal_spiral.py (repo non-pytest convention).
Run: python core/test_fractal_spiral.py

Layout math is tested against an injected tree (deterministic, no live graph);
one read-only integration check builds from the real graph.
"""
import math
import os
import sys
import tempfile
from pathlib import Path

os.environ["CHIMERA_SPIRAL_DIR"] = str(Path(tempfile.mkdtemp(prefix="chimera_spiral_test_")))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import fractal_spiral as fs  # noqa: E402

FIXTURE = {
    "id": "player", "kind": "trunk", "label": "The Player", "status": None,
    "children": [
        {"id": "loop-1", "kind": "loop", "label": "Loop 1", "status": None, "children": [
            {"id": "feat::A", "kind": "feature", "label": "A", "status": "verified",
             "children": [
                 {"id": "band::A::k", "kind": "band", "label": "k", "status": "done",
                  "children": [{"id": "cp::k.1", "kind": "checkpoint", "label": "k.1",
                                "status": "done", "children": []}]}]},
            {"id": "feat::B", "kind": "feature", "label": "B", "status": "needs_refinement",
             "children": []},
        ]},
    ],
}


def test_golden_angle_is_phyllotaxis():
    deg = math.degrees(fs.GOLDEN_ANGLE)
    assert abs(deg - 137.507) < 0.01, f"golden angle wrong: {deg}"


def test_trunk_at_origin_and_recursion_is_self_similar():
    placed, edges = fs.layout(_deepcopy(FIXTURE))
    by_id = {p["id"]: p for p in placed}
    assert (by_id["player"]["x"], by_id["player"]["y"]) == (0.0, 0.0), "trunk must be the origin"
    # player=0, loop=1, feature=2, band=3, checkpoint=4 — five self-similar scales
    assert by_id["player"]["depth"] == 0 and by_id["cp::k.1"]["depth"] == 4
    # self-similar: a checkpoint (depth 3) sits far nearer its band than a loop
    # sits to the player — child spirals shrink by CHILD_SCALE each level.
    d_loop = math.hypot(by_id["loop-1"]["x"], by_id["loop-1"]["y"])
    band = by_id["band::A::k"]
    feat = by_id["feat::A"]
    d_band = math.hypot(band["x"] - feat["x"], band["y"] - feat["y"])
    assert d_band < d_loop, "deeper spirals must be tighter (self-similar shrink)"


def test_edges_form_a_tree():
    placed, edges = fs.layout(_deepcopy(FIXTURE))
    assert len(edges) == len(placed) - 1, "a rooted tree has n-1 edges"
    kinds = {p["id"]: p["kind"] for p in placed}
    assert kinds["feat::B"] == "feature" and kinds["cp::k.1"] == "checkpoint"


def test_status_maps_to_strand_tier():
    placed, _ = fs.layout(_deepcopy(FIXTURE))
    by_id = {p["id"]: p for p in placed}
    assert by_id["feat::A"]["tier"] == "done"        # verified
    assert by_id["feat::B"]["tier"] == "scarred"     # needs_refinement


def test_neighborhood_walks_the_fractal():
    fs._load_structure = lambda: _deepcopy(FIXTURE)  # monkeypatch the live read
    payload = fs.build()
    nb = fs.neighborhood("feat::A", payload)
    assert nb["trunk"] == "loop-1"
    assert nb["branches"] == ["band::A::k"], "a feature's branch is its exam band"
    assert "feat::B" in nb["siblings"]
    deep = fs.neighborhood("band::A::k", payload)
    assert deep["branches"] == ["cp::k.1"], "recursion: bands branch into checkpoints"


def test_svg_is_self_contained():
    fs._load_structure = lambda: _deepcopy(FIXTURE)
    svg = fs.render_svg()
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "http" not in svg.replace("http://www.w3.org/2000/svg", ""), \
        "no external asset references allowed"
    assert "THE PLAYER" in svg


def test_live_graph_builds_without_error():
    # read-only integration: the real DNA graph must lay out cleanly
    import importlib
    importlib.reload(fs)
    payload = fs.build()
    assert payload["nodes"], "live spiral should not be empty"
    assert payload["nodes"][0]["id"] == "player", "the player is always the trunk"
    assert payload["golden_angle_deg"] == round(math.degrees(fs.GOLDEN_ANGLE), 4)


def _deepcopy(d):
    import json
    return json.loads(json.dumps(d))


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} fractal_spiral tests passed")
