"""Standalone assert-script for core/gauntlet.py (repo non-pytest convention).
Run: python core/test_gauntlet.py

All state (gauntlet dir, board, tunnel sessions) redirects to a temp dir BEFORE
import; collect_facts() is monkeypatched so verifiers cross-examine against
controlled facts instead of the live graph. One test walks an agent through the
ENTIRE gauntlet — the full pass the human described, compressed.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="chimera_gauntlet_test_"))
os.environ["CHIMERA_GAUNTLET_DIR"] = str(_tmp / "gauntlet")
os.environ["CHIMERA_GAUNTLET_LOCK"] = str(_tmp / "gauntlet.lock")
os.environ["CHIMERA_TASK_BOARD_STATE"] = str(_tmp / "board.json")
os.environ["CHIMERA_TASK_BOARD_LOCK"] = str(_tmp / "board.lock")
os.environ["CHIMERA_TUNNEL_SESSIONS"] = str(_tmp / "sessions")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import gauntlet as gl   # noqa: E402
from core import task_board as tb  # noqa: E402
from core import agent_tunnel as tun  # noqa: E402

AGENT = "trial-1"


def _facts(**over):
    base = {
        "gpa": 1.92,
        "current_loop": 1,
        "open_features": ["Ground_Rock_Surface", "Ground_Metal_Surface"],
        "open_task_ids": [t["id"] for t in tb.get_state()["tasks"] if t["status"] == "open"],
        "open_pain_ids": ["phase_4d2da4e032a4aa07:P1"],
        "latest_build": {"result": "pass", "timestamp": "2026-07-12T01:23:58", "id": "mut_b1"},
        "failed_builds": [{"id": "mut_f9", "timestamp": "2026-07-10T22:10:00"}],
        "feature_statuses": {"Ground_Sand_Footprints": "sim_verified"},
        "h_rule_ids": ["H-31", "H-2"],
        "candidates": ["audio_visual_sync/telemetry_accessors"],
        "nodes": [],
    }
    base.update(over)
    return base


def _patch_facts(**over):
    gl.collect_facts = lambda: _facts(**over)


def _write(agent, name, text):
    d = gl._artifacts_dir(agent)
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(text, encoding="utf-8")


def _reset():
    import shutil
    if gl.GAUNTLET_DIR.exists():
        shutil.rmtree(gl.GAUNTLET_DIR)
    for f in (tb.STATE_PATH, tb.STATE_PATH.with_suffix(".json.bak")):
        if f.exists():
            f.unlink()
    if tun.SESSIONS_DIR.exists():
        for f in tun.SESSIONS_DIR.glob("*.json"):
            f.unlink()
    _patch_facts()


def test_enter_persists_across_turns():
    _reset()
    run1 = gl.enter(AGENT)
    assert run1["station"] == 0 and gl._artifacts_dir(AGENT).exists()
    _write(AGENT, "orientation.md", "garbage that fails")
    run, checks, passed = gl.submit(AGENT)
    assert not passed and run["attempts"][0]["failed_checks"], "bounce must name the failed checks"
    run2 = gl.enter(AGENT)  # a later turn resumes, never restarts
    assert run2["station"] == 0 and len(run2["attempts"]) == 1


def test_full_pass_earns_journeyman_and_specialties():
    _reset()
    tb.add_task(title="real work", recipe="r", files=["docs/research/**"])
    gl.enter(AGENT)
    open_id = tb.get_state()["tasks"][0]["id"]

    # 1 ORIENTATION — artifact must cross-check against live facts
    _write(AGENT, "orientation.md",
           f"GPA 1.92. We are in Loop 1; Ground_Rock_Surface is open. "
           f"Top claimable: {open_id}. Pain: phase_4d2da4e032a4aa07:P1.")
    _patch_facts()
    run, checks, passed = gl.submit(AGENT)
    assert passed, f"orientation failed: {[d for d, ok in checks if not ok]}"

    # 2 THE SCRIBE — the graph must hold a typed surprise with the run token
    _patch_facts(nodes=[{"type": "SurpriseMoment", "source": "agent",
                         "context": f"gauntlet:{AGENT} trial run"}])
    run, checks, passed = gl.submit(AGENT)
    assert passed, f"scribe failed: {[d for d, ok in checks if not ok]}"

    # 3 THE SCHOLAR'S DESK — cites real on-disk sources + a numeric criterion
    _write(AGENT, "research.md",
           f"For {open_id}: dust mask needs 60 fps floor and 0.5 m displacement. "
           f"Sources: docs/RESULT_GRADING_RUBRIC.md and docs/MCP_PATHWAYS.md.")
    run, checks, passed = gl.submit(AGENT)
    assert passed, f"scholar failed: {[d for d, ok in checks if not ok]}"
    assert gl.has_role(AGENT, "initiate"), "three stations must earn initiate mid-run"

    # 4 THE CARTOGRAPHER — latest build to the minute, statuses correctly paired
    _write(AGENT, "graph.md",
           "Latest build: pass @ 2026-07-12T01:23 (mut_b1). "
           "Ground_Sand_Footprints latest status: sim_verified.")
    run, checks, passed = gl.submit(AGENT)
    assert passed, f"cartographer failed: {[d for d, ok in checks if not ok]}"

    # 5 THE GATEKEEPER'S DRILL — autopsy a real failure with gate + H-rule
    _write(AGENT, "gates.md",
           "Failed build mut_f9 @ 2026-07-10T22:10 would be caught by "
           "gate_build_succeeded; H-31 applies (component integration).")
    run, checks, passed = gl.submit(AGENT)
    assert passed, f"gatekeeper failed: {[d for d, ok in checks if not ok]}"

    # 6 THE TUNNEL RUN — the sandbox was seeded on advancing; walk the single entry
    sandbox = next(t for t in tb.get_state()["tasks"]
                   if t["title"] == f"Gauntlet sandbox: {AGENT}")
    tun.enter(AGENT, task_id=sandbox["id"], assemble=False)
    _write(AGENT, "tunnel_note.md", "My footprint is docs/gauntlet/trial-1/** only.")
    tun.exit_tunnel(AGENT, "done",
                    result=f"wrote docs/gauntlet/{AGENT}/tunnel_note.md as instructed")
    run, checks, passed = gl.submit(AGENT)
    assert passed, f"tunnel run failed: {[d for d, ok in checks if not ok]}"

    # 7 THE EXIT GATE — a defended, research-grounded choice
    _write(AGENT, "verdict.md",
           "I choose audio_visual_sync/telemetry_accessors. My research.md set a 60 fps "
           "floor for the same subsystem family; H-31 says telemetry defaults mean the "
           "component is not populating at runtime, so the fix is attachment-first. "
           "Prior: surprise_79acef63880dfc4d shows graph parameters can be strings, so "
           "read-backs must be type-guarded. This choice unblocks two rejected features "
           "with one root cause, which is the highest-leverage move on the board.")
    run, checks, passed = gl.submit(AGENT)
    assert passed, f"exit gate failed: {[d for d, ok in checks if not ok]}"
    assert run["completed_at"], "the gauntlet must be complete"
    creds = gl.load_credentials()[AGENT]
    assert "journeyman" in creds["roles"]
    assert "researcher" in creds["roles"] and "tunnel-runner" in creds["roles"], \
        f"100-score stations must tag specialties: {creds['roles']}"
    assert len(creds["station_scores"]) == 7


def test_capable_claims_require_the_credential():
    _reset()
    tb.add_task(title="capable job", recipe="r", capable_only=True)
    try:
        tb.claim_task("unqualified-1", capable=True)
        assert False, "capable claim without credential must refuse"
    except ValueError as e:
        assert "gauntlet" in str(e)
    gl._grant("unqualified-1", ["journeyman"], note="human fiat test")
    got = tb.claim_task("unqualified-1", capable=True)
    assert got and got["title"] == "capable job"


def test_grant_is_the_human_override():
    _reset()
    entry = gl._grant("fiat-1", ["journeyman"], note="one sentence outranks the machine")
    assert "journeyman" in entry["roles"]
    assert entry["history"][0]["note"] == "one sentence outranks the machine"


def test_bounce_records_every_attempt_for_the_profile():
    _reset()
    gl.enter(AGENT)
    for _ in range(3):
        run, checks, passed = gl.submit(AGENT)  # no artifact at all
        assert not passed
    assert len(gl._load_run(AGENT)["attempts"]) == 3, "the beating is part of the record"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} gauntlet tests passed")
