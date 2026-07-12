"""Standalone assert-script for core/agent_tunnel.py (repo non-pytest convention).
Run: python core/test_agent_tunnel.py

Board state + tunnel sessions are redirected to a temp dir BEFORE import; the
editor_scheduler functions are monkeypatched on the tunnel module so tests can
never kill or launch a real Unreal process.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="chimera_tunnel_test_"))
os.environ["CHIMERA_TASK_BOARD_STATE"] = str(_tmp / "board.json")
os.environ["CHIMERA_TASK_BOARD_LOCK"] = str(_tmp / "board.lock")
os.environ["CHIMERA_TUNNEL_SESSIONS"] = str(_tmp / "sessions")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import agent_tunnel as tun  # noqa: E402
from core import task_board as tb     # noqa: E402

EDITOR_CALLS = []


def _fake_request(mode, agent, timeout=120.0, grant=True):
    EDITOR_CALLS.append(("request", mode, agent))
    return grant


def _patch_editor(grant=True):
    tun.request_editor = lambda mode, agent, timeout=120.0: _fake_request(mode, agent, timeout, grant)
    tun.release_editor = lambda agent: EDITOR_CALLS.append(("release", None, agent)) or True
    tun.editor_heartbeat = lambda agent: True


def _reset():
    EDITOR_CALLS.clear()
    _patch_editor(grant=True)
    for f in (tb.STATE_PATH, tb.STATE_PATH.with_suffix(".json.bak")):
        if f.exists():
            f.unlink()
    if tun.SESSIONS_DIR.exists():
        for f in tun.SESSIONS_DIR.glob("*.json"):
            f.unlink()


def test_enter_claims_and_acquires_editor_then_exit_releases():
    _reset()
    tb.add_task(title="pie verify", recipe="run beats", files=["a/**"],
                editor="open", exclusive=["pie"], feature="Verb_Look")
    packet = tun.enter("agent-1", assemble=False)
    assert packet["task"]["title"] == "pie verify"
    assert packet["editor_held"] and ("request", "open", "agent-1") in EDITOR_CALLS
    assert tun.active_sessions()[0]["task_id"] == packet["task"]["id"]
    out = tun.exit_tunnel("agent-1", "done", result="5/5 beats reached, read-backs ok")
    assert out["task"]["status"] == "done"
    assert ("release", None, "agent-1") in EDITOR_CALLS
    assert "postflight" in out and "pie verify" in out["postflight"]
    assert tun.active_sessions() == []


def test_editor_timeout_releases_the_claim():
    _reset()
    _patch_editor(grant=False)
    t = tb.add_task(title="build fix", recipe="r", files=["b/**"], editor="closed")
    try:
        tun.enter("agent-1", assemble=False)
        assert False, "editor refusal must raise"
    except TimeoutError:
        pass
    fresh = next(x for x in tb.get_state()["tasks"] if x["id"] == t["id"])
    assert fresh["status"] == "open", "claim must be released when the editor is refused"
    assert tun.active_sessions() == [], "no session may survive a failed enter"


def test_no_editor_task_never_touches_scheduler():
    _reset()
    tb.add_task(title="research", recipe="r", files=["docs/research/**"], editor="none")
    packet = tun.enter("agent-1", assemble=False)
    assert not packet["editor_held"] and EDITOR_CALLS == []
    tun.exit_tunnel("agent-1", "release", note="parking it")
    assert EDITOR_CALLS == [], "release must not touch an editor that was never held"


def test_double_enter_refused_and_empty_board_returns_none():
    _reset()
    tb.add_task(title="only", recipe="r", files=["a/**"])
    assert tun.enter("agent-1", assemble=False) is not None
    try:
        tun.enter("agent-1", assemble=False)
        assert False, "second enter without exit must refuse"
    except ValueError as e:
        assert "exit it first" in str(e)
    assert tun.enter("agent-2", assemble=False) is None  # board drained


def test_exit_enforces_evidence_via_board():
    _reset()
    tb.add_task(title="t", recipe="r")
    tun.enter("agent-1", assemble=False)
    try:
        tun.exit_tunnel("agent-1", "done", result="  ")
        assert False, "done without evidence must refuse"
    except ValueError:
        pass
    out = tun.exit_tunnel("agent-1", "blocked", reason="Content/Audio empty")
    assert out["task"]["status"] == "blocked"


def test_heartbeat_refreshes_board_and_editor():
    _reset()
    tb.add_task(title="t", recipe="r", editor="open")
    tun.enter("agent-1", assemble=False)
    hb = tun.tunnel_heartbeat("agent-1")
    assert hb == {"board_claims": 1, "editor": True}
    assert tun.tunnel_heartbeat("stranger") == {"board_claims": 0, "editor": False}


def test_keyword_matching_is_relevance_ranked():
    toks = tun._tokens("audio_visual_sync/telemetry_accessors", None,
                       "verify SandSoundComponent attachment")
    assert {"audio", "telemetry", "sandsoundcomponent"} <= toks
    text = ("**[H-31]** telemetry commands that fall back to defaults...\n"
            "**[H-13]** economy features grade C/F on partial coverage\n"
            "**[H-32]** telemetry queries return hardcoded defaults; verify "
            "SandSoundComponent attachment and audio events\n")
    hits = tun._match_lines(text, toks, cap=2)
    assert len(hits) == 2 and hits[0].startswith("**[H-32]"), f"got {hits}"
    assert all("H-13" not in h for h in hits)


def test_tend_closes_sessions_whose_claim_vanished():
    _reset()
    tb.add_task(title="long job", recipe="r", editor="open")
    tun.enter("agent-1", assemble=False)
    # the agent dies: its board heartbeat goes stale and the reaper reopens the task
    state = tb._read_state()
    state["tasks"][0]["heartbeat"] = 1.0
    tb._write_state(state)
    closed = tun.tend()
    assert len(closed) == 1 and closed[0]["outcome"] == "abandoned"
    assert ("release", None, "agent-1") in EDITOR_CALLS, "tend must free the dead agent's editor"
    assert tun.active_sessions() == []
    assert tb.get_state()["tasks"][0]["status"] == "open", "task must be claimable again"


def test_footprint_offenders_pure():
    scopes = ["Source/Chimera/ProceduralGenerated/Sound/**", "docs/beats/*.json"]
    porcelain = (
        " M Chimera/Source/Chimera/ProceduralGenerated/Sound/SandSound.cpp\n"
        " M Chimera/docs/beats/audio.beats.json\n"
        " M Chimera/core/task_board.py\n"
        "?? task_progress.md\n")
    off = tun._offenders_from_porcelain(porcelain, scopes)
    assert "Chimera/core/task_board.py" in off and "task_progress.md" in off
    assert all("Sound" not in o and "beats" not in o for o in off)
    assert tun._offenders_from_porcelain(porcelain, []) == [], "no scopes -> no check"


def test_board_cli_is_the_single_entry_and_exit():
    _reset()
    import contextlib, io
    tb.add_task(title="research", recipe="do it", files=["docs/research/**"], editor="none")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        tb.main(["claim", "--agent", "cli-1"])
    assert "TUNNEL PACKET" in buf.getvalue(), "board claim must print the work packet"
    assert tun.active_sessions()[0]["agent"] == "cli-1", "board claim must open the tunnel"
    tid = tun.active_sessions()[0]["task_id"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        tb.main(["done", "--agent", "cli-1", "--id", tid, "--result", "evidence here"])
    out = buf.getvalue()
    assert "tunnel exited" in out and "postflight" in out
    assert tun.active_sessions() == []


def test_full_packet_assembly_reads_live_docs():
    # Read-only integration: real CLAUDE.md + real graph; never mutates them.
    _reset()
    tb.add_task(title="audio_visual_sync/telemetry_accessors", recipe="fix telemetry",
                feature="audio_visual_sync/telemetry_accessors",
                files=["Source/Chimera/ProceduralGenerated/Sound/**"], editor="none")
    packet = tun.enter("agent-1", assemble=True)
    assert any("H-3" in h for h in packet.get("heuristics", [])), \
        "H-31/32/33 mention telemetry and must surface for this feature"
    assert "exit_contract" in packet


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} agent_tunnel tests passed")
