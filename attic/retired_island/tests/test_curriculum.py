"""Standalone assert-script for core/curriculum.py (repo non-pytest convention).
Run: python core/test_curriculum.py

Progression tests run against a TINY fixture curriculum (env-redirected); the
real docs/curriculum/curriculum.json gets a structural lint pass. Feature
transcripts, gauntlet creds, and the board all redirect to a temp dir.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="chimera_curriculum_test_"))
_fixture = _tmp / "curriculum.json"
os.environ["CHIMERA_CURRICULUM_PATH"] = str(_fixture)
os.environ["CHIMERA_GAUNTLET_DIR"] = str(_tmp / "gauntlet")
os.environ["CHIMERA_GAUNTLET_LOCK"] = str(_tmp / "gauntlet.lock")
os.environ["CHIMERA_TASK_BOARD_STATE"] = str(_tmp / "board.json")
os.environ["CHIMERA_TASK_BOARD_LOCK"] = str(_tmp / "board.lock")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import curriculum as cu  # noqa: E402
from core import gauntlet as gl    # noqa: E402
from core import task_board as tb  # noqa: E402

FEATURE = "Dust_Kickup"

FIXTURE = {"bands": [
    {"band": "kindergarten", "min_role": None, "courses": [
        {"discipline": "joy", "title": "Joy", "checkpoints": [
            {"id": "k.a", "prompt": "fun of <feature>?", "artifact": "k_a.md",
             "verify": [{"type": "artifact", "min_chars": 30, "must_match": ["fun"]}]},
            {"id": "k.b", "prompt": "again?", "artifact": "k_b.md",
             "verify": [{"type": "artifact", "min_chars": 20, "min_bullets": 2}]},
        ]}]},
    {"band": "bachelor", "min_role": "initiate", "courses": [
        {"discipline": "eng", "title": "Eng", "checkpoints": [
            {"id": "ba.a", "prompt": "numbers for <feature>", "artifact": "ba_a.md",
             "verify": [{"type": "artifact", "require_numeric": 1},
                        {"type": "prior_artifact", "n": 1}]},
        ]}]},
]}


def _reset():
    import shutil
    _fixture.write_text(json.dumps(FIXTURE), encoding="utf-8")
    if cu.GAUNTLET_DIR.exists():
        shutil.rmtree(cu.GAUNTLET_DIR)
    for f in (tb.STATE_PATH, tb.STATE_PATH.with_suffix(".json.bak")):
        if f.exists():
            f.unlink()
    cu._graph_nodes = lambda: []


def _write(name, text):
    d = cu._feature_dir(FEATURE)
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(text, encoding="utf-8")


def test_real_curriculum_lints():
    real = json.loads((cu.ROOT / "docs" / "curriculum" / "curriculum.json")
                      .read_text(encoding="utf-8"))
    ids, total = set(), 0
    for band in real["bands"]:
        assert band.get("min_role") in (None, "initiate", "journeyman")
        for course in band["courses"]:
            for cp in course["checkpoints"]:
                assert cp["id"] not in ids, f"duplicate id {cp['id']}"
                ids.add(cp["id"])
                total += 1
                assert "<feature>" in cp["prompt"] or "feature" in cp["prompt"].lower()
                assert cp.get("artifact"), f"{cp['id']} has no artifact checkpoint"
                for spec in cp["verify"]:
                    assert spec["type"] in cu.VERIFIERS, \
                        f"{cp['id']} uses unknown verifier {spec['type']!r}"
    assert total >= 50, f"the founding curriculum should be substantial, got {total}"
    print(f"    (real curriculum: {len(real['bands'])} bands, {total} checkpoints)")


def test_enroll_submit_bounce_pass_and_agent_credit():
    _reset()
    cu.enroll(FEATURE, agent="porter-1")
    try:
        cu.submit(FEATURE, "k.a", "porter-1")   # no artifact yet
        assert False, "must bounce without the artifact"
    except SystemExit:
        raise
    except Exception:
        pass  # submit returns, doesn't raise, on bounce — check below
    tr, checks, passed, grad = cu.submit(FEATURE, "k.a", "porter-1")
    assert not passed and tr["attempts"], "bounce must be recorded"
    _write("k_a.md", f"The fun of {FEATURE} is kicking dust and watching it settle.")
    tr, checks, passed, grad = cu.submit(FEATURE, "k.a", "porter-1")
    assert passed and grad is None
    assert tr["passed"]["k.a"]["agent"] == "porter-1", "the carrier gets credited"


def test_band_graduation_unlocks_and_locks():
    _reset()
    cu.enroll(FEATURE)
    try:
        cu.submit(FEATURE, "ba.a", "porter-1")
        assert False, "a later band's checkpoint must be locked"
    except ValueError as e:
        assert "locked" in str(e)
    _write("k_a.md", f"The fun of {FEATURE} is kicking regolith and watching it drift.")
    tr, checks, passed, grad = cu.submit(FEATURE, "k.a", "porter-1")
    assert passed, f"k.a failed: {[d for d, ok in checks if not ok]}"
    _write("k_b.md", f"{FEATURE} again because:\n- itch one\n- itch two")
    tr, checks, passed, grad = cu.submit(FEATURE, "k.b", "porter-2")
    assert passed and grad == "kindergarten", f"band must graduate, got {grad}"
    assert tr["band_index"] == 1
    carriers = {v["agent"] for v in tr["passed"].values()}
    assert carriers == {"porter-1", "porter-2"}, "different agents carry different checkpoints"


def test_role_gate_and_prior_artifact_coherence():
    _reset()
    cu.enroll(FEATURE)
    _write("k_a.md", f"The fun of {FEATURE} is the dust plume that follows every kick.")
    cu.submit(FEATURE, "k.a", "porter-1")
    _write("k_b.md", f"{FEATURE} again because:\n- the plume\n- the settle")
    cu.submit(FEATURE, "k.b", "porter-1")
    # bachelor band requires the porter to hold 'initiate'
    try:
        cu.submit(FEATURE, "ba.a", "porter-1")
        assert False, "unqualified porter must be refused"
    except PermissionError as e:
        assert "initiate" in str(e)
    gl._grant("porter-1", ["initiate"], note="test fiat")
    _write("ba_a.md", f"{FEATURE} runs at 60 fps; builds on k_a.md's spark.")
    tr, checks, passed, grad = cu.submit(FEATURE, "ba.a", "porter-1")
    assert passed, f"failed: {[d for d, ok in checks if not ok]}"
    assert grad == "bachelor" and tr["band_index"] == 2, "final band confers the degree"


def test_verifier_units():
    _reset()
    ctx = {"nodes": [], "tasks": [], "h_rules": {"H-21"}, "transcript": {"passed": {}}}
    ok = dict(cu._v_h_rule({}, FEATURE, "H-21 applies here", ctx))
    assert all(ok.values())
    bad = cu._v_h_rule({}, FEATURE, "H-999 applies", ctx)
    assert not bad[0][1], "citing a nonexistent H-rule must fail"
    # url_cache: URL + a real repo file under docs/research/
    text = ("Source: https://example.com/gdc-talk cached at "
            "docs/research/engine-symbols.cache.json")
    assert all(ok for _, ok in cu._v_url_cache({}, FEATURE, text, ctx))
    assert not all(ok for _, ok in cu._v_url_cache(
        {}, FEATURE, "https://example.com only, no cache", ctx))
    # board_done cross-checks the live (temp) board
    tb.add_task(title="impl", recipe="r", feature=FEATURE)
    t = tb.claim_task("porter-1")
    tb.complete_task("porter-1", t["id"], result="read-back verified, 5/5 beats reached")
    ctx["tasks"] = tb.get_state()["tasks"]
    assert all(ok for _, ok in cu._v_board_done({}, FEATURE, "", ctx))
    # sim_evidence
    ctx["nodes"] = [{"type": "SimPlaytest",
                     "outcomes": [{"features": [FEATURE], "outcome": "reached"}]}]
    assert all(ok for _, ok in cu._v_sim_evidence({}, FEATURE, "outcome: reached", ctx))
    # graph_cite with allow_no_prior escape
    assert cu._v_graph_cite({"allow_no_prior": True}, FEATURE, "no prior exists", ctx)[0][1]
    assert not cu._v_graph_cite({}, FEATURE, "cites nothing real", ctx)[0][1]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} curriculum tests passed")
