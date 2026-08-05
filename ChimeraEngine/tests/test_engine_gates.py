"""The engine must FORCE the workflow: prove() refuses until the term's PHYSICS interior
(frame/provenance/saturation/classify/why) AND the HUMAN DYAD agree. The dyad is a physics NUMBER and
a human TERM (a vision reading of the render), cross-referenced -- two DIFFERENT systems, never a
monad. A render the human rejects is refused. If any of these fail, the engine has rotted into a
rubber stamp.

Runs standalone: python ChimeraEngine/tests/test_engine_gates.py  (no LM Studio / GPU needed here --
the human side and the splat renderer are mocked; the real ones run through the MCP tools).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # ChimeraEngine/
import engine_state
import appearance
import human_messenger
import splat_appearance


def _engine(tmp_path):
    return engine_state.Engine(path=Path(tmp_path) / "state.json")


def _mock_dyad(term, frame, threshold=0.6, human_override=None):
    """Stand in for the LM-Studio vision human side in tests. PASS if the render is green (the mock
    'good' appearance), FAIL_RESTART if not (the 'lie' the human rejects). The engine judges the MOVIE
    ([begin, end]) -- the settled END frame is the state the dyad weighs."""
    from PIL import Image
    import numpy as np
    if isinstance(frame, (list, tuple)):
        frame = frame[-1]                                    # the movie's settled end
    a = np.asarray(Image.open(frame).convert("RGB"), dtype=float)
    r, g, b = a[..., 0].mean(), a[..., 1].mean(), a[..., 2].mean()
    ok = g > r + 5 and g > b + 5
    return {"pass": bool(ok), "verdict": "PASS" if ok else "FAIL_RESTART", "term": term,
            "detail": f"[mock] mean g={g:.0f} vs r={r:.0f},b={b:.0f}"}


human_messenger.dyad = _mock_dyad                          # no LM Studio in tests -- mock the human side
splat_appearance.project_movie = lambda term, out: None    # no GPU in tests -- fall back to the matplotlib mock


def _install_projector(term):
    """Give `term` a fast mock appearance (real splat renders are slow + need a GPU). The mock renders
    solid green; the mocked human dyad reads green as PASS."""
    def _proj(out):
        from PIL import Image
        p = Path(out); p.mkdir(parents=True, exist_ok=True)
        f = p / f"{term}_mock.png"
        Image.new("RGB", (8, 8), (0, 120, 0)).save(f)
        return str(f)
    appearance.PROJECTORS[term] = _proj


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


def test_prove_refuses_until_both_messengers_agree(tmp_path):
    E = _engine(tmp_path)
    term = E.next_term()
    assert term is not None
    assert "REFUSED" in E.prove(term)                         # S0 not framed
    E.frame(term, "the term stated as one atomic claim")
    assert "REFUSED" in E.prove(term)                         # physics: not saturated
    r = None
    for i, vs in enumerate(_SATURATING):
        r = E.question(term, f"q{i}", vs)
    assert r["saturated"] is True
    assert "REFUSED" in E.prove(term)                         # physics: not classified
    E.classify(term, {v: "PHYSICS" for v in E._vars(term)})
    assert "REFUSED" in E.prove(term)                         # appearance messenger missing
    assert "REFUSED" in E.render(term)                        # this term has no projector -> refused
    _install_projector(term)                                  # give it a light-view
    E.render(term)                                            # the engine PROJECTS the appearance
    out = E.prove(term)                                       # now both messengers agree
    assert "PROVEN" in out and "REFUSED" not in out
    assert term in E.state["codebook"]
    assert E.state["hierarchy"][term]["status"] == "proven"


def test_render_refuses_a_term_with_no_light_view(tmp_path):
    E = _engine(tmp_path)
    # theLaws has no projector in appearance.PROJECTORS -> no appearance messenger -> refused
    assert "REFUSED" in E.render("theLaws")


def test_dyad_refuses_a_render_the_human_rejects(tmp_path):
    """THE TEETH: a render the HUMAN reads as wrong cannot be proven. The projector paints the term
    BLUE; the (mocked) human dyad reads it as not-green and returns FAIL_RESTART, so prove() refuses at
    the appearance gate. This is 'the human is the arbiter' as a mechanism -- disagreement blocks the proof."""
    E = _engine(tmp_path)
    term = "theBlueLie"

    def _blue(out):
        from PIL import Image
        p = Path(out); p.mkdir(parents=True, exist_ok=True)
        f = p / f"{term}.png"
        Image.new("RGB", (64, 64), (40, 90, 255)).save(f)     # not green -> the human rejects it
        return str(f)
    appearance.PROJECTORS[term] = _blue

    E.frame(term, "a term whose render the human will reject")
    for i, vs in enumerate(_SATURATING):
        E.question(term, f"q{i}", vs)
    E.classify(term, {v: "PHYSICS" for v in E._vars(term)})
    assert "DYAD did not hold" in E.render(term)              # the human rejected the render
    out = E.prove(term)
    assert "REFUSED" in out and "APPEARANCE MESSENGER" in out # so prove refuses at the appearance gate
    assert E.state["hierarchy"].get(term, {}).get("status") != "proven"


def _prove_ss(E):
    _install_projector("theSolarSystem")
    E.frame("theSolarSystem", "the setting")
    for i, vs in enumerate(_SATURATING):
        E.question("theSolarSystem", f"q{i}", vs)
    E.classify("theSolarSystem", {v: "PHYSICS" for v in E._vars("theSolarSystem")})
    E.render("theSolarSystem")
    assert "PROVEN" in E.prove("theSolarSystem")


def test_prove_refuses_a_premature_saturation(tmp_path):
    E = _engine(tmp_path)
    E.frame("x", "a claim")
    E.question("x", "q", ["a", "b", "c"])
    report = E.prove("x")
    assert "REFUSED" in report and "SATURATION" in report


def test_frame_refuses_compound_claim(tmp_path):
    assert "REFUSED" in _engine(tmp_path).frame("x", "this and that")


def test_classify_refuses_illegal_terminal(tmp_path):
    E = _engine(tmp_path)
    E.frame("x", "c")
    E.question("x", "q", ["a"])
    assert "REFUSED" in E.classify("x", {"a": "MAYBE"})


def test_next_starts_at_the_seed_in_story_order(tmp_path):
    assert _engine(tmp_path).next_term() == "theSeed"


def test_next_descends_the_started_branch_first(tmp_path):
    E = _engine(tmp_path)
    _prove_ss(E)
    assert E.next_term() == "theStar"


def test_measured_compression_beats_declared_order(tmp_path):
    E = _engine(tmp_path)
    _prove_ss(E)
    for i, vs in enumerate(_SATURATING):
        E.question("theSpace", f"q{i}", vs)
    assert E.compression("theSpace") > 0 and E.compression("theStar") == 0
    assert E.next_term() == "theSpace"


def _run() -> int:
    import tempfile
    fns = [test_prove_refuses_until_both_messengers_agree, test_render_refuses_a_term_with_no_light_view,
           test_dyad_refuses_a_render_the_human_rejects,
           test_prove_refuses_a_premature_saturation, test_frame_refuses_compound_claim,
           test_classify_refuses_illegal_terminal, test_next_starts_at_the_seed_in_story_order,
           test_next_descends_the_started_branch_first, test_measured_compression_beats_declared_order]
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
