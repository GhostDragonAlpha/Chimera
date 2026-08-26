"""Standalone assert-script for core/task_board.py (matches this repo's non-pytest
convention, e.g. test_backlog_burn.py). Run: python core/test_task_board.py

State is redirected to a temp dir via env vars BEFORE import so the tests can
never touch the live board (fork invariant).
"""
import os
import sys
import tempfile
import time
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="chimera_task_board_test_"))
os.environ["CHIMERA_TASK_BOARD_STATE"] = str(_tmp / "state.json")
os.environ["CHIMERA_TASK_BOARD_LOCK"] = str(_tmp / "board.lock")
os.environ["CHIMERA_TASK_CLAIM_TTL"] = "7200"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import task_board as tb  # noqa: E402


def _reset():
    if tb.STATE_PATH.exists():
        tb.STATE_PATH.unlink()
    bak = tb.STATE_PATH.with_suffix(".json.bak")
    if bak.exists():
        bak.unlink()


def test_glob_overlap():
    assert tb._globs_overlap("Source/Chimera/ProceduralGenerated/**",
                             "Source/Chimera/ProceduralGenerated/Sound/**")
    assert tb._globs_overlap("Source/Chimera/ProceduralGenerated/Sound/**",
                             "Source/Chimera/ProceduralGenerated/**")
    assert not tb._globs_overlap("Source/Chimera/ProceduralGenerated/Sound/**",
                                 "Source/Chimera/ProceduralGenerated/Materials/**")
    assert tb._globs_overlap("docs/research/x.md", "docs/research/**")
    assert not tb._globs_overlap("docs/research/**", "docs/beats/**")
    # same-directory patterns over-detect on purpose (conservative)
    assert tb._globs_overlap("Sound/*.h", "Sound/*.cpp")


def test_disjoint_tasks_run_in_parallel():
    _reset()
    a = tb.add_task(title="sound work", recipe="r1",
                    files=["Source/Chimera/ProceduralGenerated/Sound/**"],
                    editor="open", exclusive=["pie"])
    b = tb.add_task(title="research", recipe="r2",
                    files=["docs/research/**"], editor="none")
    frontier = tb.parallel_frontier()
    assert len(frontier) == 2, f"expected 2-wide frontier, got {len(frontier)}"
    got_a = tb.claim_task("agent-1")
    got_b = tb.claim_task("agent-2")
    assert got_a["id"] == a["id"] and got_b["id"] == b["id"]
    assert tb.claim_task("agent-3") is None  # board drained


def test_file_scope_conflict_blocks_second_claim():
    _reset()
    tb.add_task(title="materials A", recipe="r",
                files=["Source/Chimera/ProceduralGenerated/Materials/**"])
    tb.add_task(title="materials B", recipe="r",
                files=["Source/Chimera/ProceduralGenerated/Materials/Dust*.cpp"])
    assert tb.claim_task("agent-1") is not None
    assert tb.claim_task("agent-2") is None, "overlapping file scopes must not co-claim"


def test_editor_mode_and_exclusive_conflicts():
    _reset()
    tb.add_task(title="build fix", recipe="r", files=["a/**"], editor="closed", priority=2)
    tb.add_task(title="pie verify", recipe="r", files=["b/**"], editor="open",
                exclusive=["pie"], priority=1.5)
    tb.add_task(title="pie soak", recipe="r", files=["c/**"], editor="open",
                exclusive=["pie"], priority=1.0)
    tb.add_task(title="pure research", recipe="r", files=["docs/research/**"],
                editor="none", priority=0.5)
    got = tb.claim_task("agent-1")
    assert got["title"] == "build fix"
    # closed conflicts with open, and research (editor:none) is the only survivor
    nxt = tb.claim_task("agent-2")
    assert nxt is not None and nxt["title"] == "pure research", f"got {nxt}"
    assert tb.claim_task("agent-3") is None
    # finish the build; now ONE pie task is claimable, the second waits on 'pie'
    tb.complete_task("agent-1", got["id"], result="UBT pass")
    p1 = tb.claim_task("agent-4")
    assert p1["title"] == "pie verify"
    assert tb.claim_task("agent-5") is None, "'pie' exclusive must serialize PIE tasks"


def test_same_feature_conflicts_and_explicit_claim_reason():
    _reset()
    tb.add_task(title="fix accessors", recipe="r", feature="audio_visual_sync",
                files=["x/**"], priority=2)
    t2 = tb.add_task(title="verify accessors", recipe="r", feature="audio_visual_sync",
                     files=["y/**"])
    tb.claim_task("agent-1")
    try:
        tb.claim_task("agent-2", task_id=t2["id"])
        assert False, "explicit claim of feature-conflicting task must refuse"
    except ValueError as e:
        assert "same feature" in str(e)


def test_dependencies_gate_claims():
    _reset()
    a = tb.add_task(title="step 1", recipe="r", files=["a/**"])
    b = tb.add_task(title="step 2", recipe="r", files=["b/**"],
                    depends_on=[a["id"]], priority=9)
    got = tb.claim_task("agent-1")
    assert got["id"] == a["id"], "dependent task must not be claimable before its dep"
    tb.complete_task("agent-1", a["id"], result="done evidence")
    got2 = tb.claim_task("agent-1")
    assert got2["id"] == b["id"]


def test_done_and_block_require_evidence():
    _reset()
    t = tb.add_task(title="t", recipe="r")
    tb.claim_task("agent-1")
    for fn, kw in ((tb.complete_task, "result"), (tb.block_task, "reason")):
        try:
            fn("agent-1", t["id"], **{kw: "   "})
            assert False, f"{fn.__name__} must demand a non-empty {kw}"
        except ValueError:
            pass
    blocked = tb.block_task("agent-1", t["id"], reason="Content/Audio empty; needs CC0 pack")
    assert blocked["status"] == "blocked"
    reopened = tb.reopen_task("agent-2", t["id"], note="pack imported")
    assert reopened["status"] == "open"


def test_release_and_stale_reap():
    _reset()
    t = tb.add_task(title="t", recipe="r")
    tb.claim_task("agent-1")
    assert tb.release_task("agent-2", t["id"]) is None, "only the owner may release"
    assert tb.release_task("agent-1", t["id"])["status"] == "open"
    # stale claim: fake an ancient heartbeat, any read reaps it
    tb.claim_task("agent-1")
    state = tb._read_state()
    state["tasks"][0]["heartbeat"] = time.time() - tb.CLAIM_TTL - 1
    tb._write_state(state)
    fresh = tb.get_state()
    assert fresh["tasks"][0]["status"] == "open", "stale claim must be reaped"
    assert any("reaped" in n["text"] for n in fresh["tasks"][0]["notes"])


def test_heartbeat_keeps_claim_alive():
    _reset()
    tb.add_task(title="t", recipe="r")
    tb.claim_task("agent-1")
    assert tb.heartbeat("agent-1") == 1
    assert tb.heartbeat("agent-2") == 0


def test_seed_idempotent_and_skips_demoted():
    _reset()
    rows = [
        {"name": "audio_visual_sync/telemetry_accessors", "score": 1.2,
         "capable_only": False, "recipe": "fetch study guide"},
        {"name": "Dead_End_Feature", "score": 0.04, "recipe": "demoted"},
    ]
    research = ["procedural dust-accumulation mask material creation"]
    added = tb.seed_board(rows=rows, research=research)
    assert len(added) == 2, f"expected candidate+research, got {[t['title'] for t in added]}"
    added2 = tb.seed_board(rows=rows, research=research)
    assert added2 == [], "second seed must be a no-op"
    # audio feature got the Sound/** scope from the footprint table
    audio = next(t for t in tb.get_state()["tasks"] if t["feature"])
    assert "Sound" in audio["resources"]["files"][0]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} task_board tests passed")
