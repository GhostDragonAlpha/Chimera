"""The engine must FORCE the workflow: prove() refuses until every gate passes, then records it.
If any of these fail, the engine has rotted into a rubber stamp -- the failure it exists to prevent.

Runs two ways:
  python ChimeraEngine/tests/test_engine_gates.py          (standalone; the reliable way)
  python -m pytest ... --import-mode=importlib              (pytest; --import-mode needed because the
                                                             sibling ChimeraEngine/__init__.py is a
                                                             corrupted 4.2 MB blob -- a pre-existing defect)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # ChimeraEngine/ (skip the pkg __init__)
import engine_state


def _engine(tmp_path):
    return engine_state.Engine(path=Path(tmp_path) / "state.json")


def _tiny_png(tmp_path):
    from PIL import Image
    p = Path(tmp_path) / "vis.png"
    Image.new("RGB", (8, 8), (0, 120, 0)).save(p)
    return str(p)


_SATURATING = [
    ["canopy", "understory", "forest_floor"],
    ["soil_loam", "water_table", "mycorrhiza"],
    ["streams", "rainfall", "humidity", "water_table"],
    ["light_dapple", "growing_season", "canopy"],
    ["fauna_mammal", "fauna_bird", "insects", "pollinators"],
    ["fruit", "flowers", "decomposers", "leaf_litter"],
    ["canopy", "understory", "leaf_litter", "pollinators"],
    ["streams", "humidity", "rainfall", "mycorrhiza", "fruit"],
    ["fauna_bird", "insects", "flowers", "soil_loam", "decomposers"],
    ["forest_floor", "growing_season", "light_dapple", "fauna_mammal"],
]


def test_prove_refuses_until_every_gate_passes(tmp_path):
    E = _engine(tmp_path)
    term = E.next_term()
    assert term is not None
    assert "REFUSED" in E.prove(term)                         # S0 not framed
    E.frame(term, "the term stated as one atomic claim")
    assert "REFUSED" in E.prove(term)                         # no variables / not saturated
    r = None
    for i, vs in enumerate(_SATURATING):
        r = E.question(term, f"q{i}", vs)
    assert r["saturated"] is True                             # over the hump
    assert "REFUSED" in E.prove(term)                         # S3 CLASSIFY not done
    E.classify(term, {v: "PHYSICS" for v in E._vars(term)})
    assert "REFUSED" in E.prove(term)                         # VISUAL missing
    assert "REFUSED" in E.render(term, str(Path(tmp_path) / "nope.png"))   # fake visual refused
    E.render(term, _tiny_png(tmp_path))                       # real one accepted
    out = E.prove(term)                                       # every gate passes
    assert "PROVEN" in out and "REFUSED" not in out
    assert term in E.state["codebook"]
    assert E.state["hierarchy"][term]["status"] == "proven"


def test_prove_refuses_a_premature_saturation(tmp_path):
    E = _engine(tmp_path)
    E.frame("x", "a claim")
    E.question("x", "q", ["a", "b", "c"])                      # one round, no dry tail
    report = E.prove("x")
    assert "REFUSED" in report and "SATURATION" in report


def test_frame_refuses_compound_claim(tmp_path):
    assert "REFUSED" in _engine(tmp_path).frame("x", "this and that")


def test_classify_refuses_illegal_terminal(tmp_path):
    E = _engine(tmp_path)
    E.frame("x", "c")
    E.question("x", "q", ["a"])
    assert "REFUSED" in E.classify("x", {"a": "MAYBE"})


def test_next_is_setting_first(tmp_path):
    # theStory is decided at the seed, so the first open term is its child
    assert _engine(tmp_path).next_term() == "theSolarSystem"


def _prove_ss(E, tmp_path):
    E.frame("theSolarSystem", "the setting")
    for i, vs in enumerate(_SATURATING):
        E.question("theSolarSystem", f"q{i}", vs)
    E.classify("theSolarSystem", {v: "PHYSICS" for v in E._vars("theSolarSystem")})
    E.render("theSolarSystem", _tiny_png(tmp_path))
    assert "PROVEN" in E.prove("theSolarSystem")


def test_next_offers_most_source_like_sibling_first_not_alphabetical(tmp_path):
    E = _engine(tmp_path)
    _prove_ss(E, tmp_path)
    # children are all fresh (no data); the source-weight puts theStar first -- NOT alphabetical theLoop
    assert E.next_term() == "theStar"


def test_measured_compression_beats_the_source_weight_prior(tmp_path):
    E = _engine(tmp_path)
    _prove_ss(E, tmp_path)
    # give theSpace (low source-weight) real data; its MEASURED compression must lift it above
    # theStar (high weight, no data) -- the most-compressed DATA wins, not the prior
    for i, vs in enumerate(_SATURATING):
        E.question("theSpace", f"q{i}", vs)
    assert E.compression("theSpace") > 0 and E.compression("theStar") == 0
    assert E.next_term() == "theSpace"


def _run() -> int:
    import tempfile
    fns = [test_prove_refuses_until_every_gate_passes, test_prove_refuses_a_premature_saturation,
           test_frame_refuses_compound_claim, test_classify_refuses_illegal_terminal,
           test_next_is_setting_first, test_next_offers_most_source_like_sibling_first_not_alphabetical,
           test_measured_compression_beats_the_source_weight_prior]
    ok = 0
    with tempfile.TemporaryDirectory() as base:
        for i, fn in enumerate(fns):
            d = Path(base) / f"t{i}"; d.mkdir()
            try:
                fn(d); print(f"  PASS  {fn.__name__}"); ok += 1
            except Exception as e:
                print(f"  FAIL  {fn.__name__}: {e}")
    print(f"\n  {ok}/{len(fns)} passed")
    return 0 if ok == len(fns) else 1


if __name__ == "__main__":
    raise SystemExit(_run())
