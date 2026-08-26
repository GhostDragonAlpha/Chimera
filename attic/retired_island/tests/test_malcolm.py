"""Tests for core.malcolm — run: python core/test_malcolm.py"""

import json
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS = TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    print(("  ok  " if cond else "FAIL  ") + name)
    PASS += cond


def main():
    tmp = Path(tempfile.mkdtemp(prefix="malcolm_test_"))
    from core import malcolm as m
    m.ENVELOPE_PATH = tmp / "envelope.json"
    m.SOURCE_TREE = tmp / "gen"
    m.TELEMETRY_LAST = tmp / "telemetry_last.json"
    (tmp / "gen").mkdir()
    (tmp / "gen" / "A.cpp").write_text("int a;\nint b;\n", encoding="utf-8")
    (tmp / "gen" / "A.h").write_text("#pragma once\n", encoding="utf-8")

    # 1: founding envelope self-installs with bands + provenance
    env = m.load_envelope()
    check("founding envelope self-installs", m.ENVELOPE_PATH.exists()
          and "engine_surprise_rate_per_week" in env["axes"])
    check("every wall carries provenance",
          all(a.get("source", {}).get("kind") for a in env["axes"].values()))
    check("bands not ceilings: emergence floors exist",
          env["axes"]["interacting_systems_per_slice"]["min"] == 3
          and env["axes"]["open_board_tasks"]["min"] == 3)
    check("hardware walls keep an emergence reserve",
          env["axes"]["frame_time_ms"]["reserve_pct"] >= 15)

    # 2: band state math (OK / WARN inside reserve / BREACH / floor / unmeasured)
    ax = {"min": 3, "max": 10, "reserve_pct": 20}
    check("state OK", m.axis_state(ax, 5) == "OK")
    check("state WARN inside the reserve band", m.axis_state(ax, 8.5) == "WARN")
    check("state BREACH over ceiling", m.axis_state(ax, 11) == "BREACH")
    check("state BELOW-FLOOR (sterility)", m.axis_state(ax, 2) == "BELOW-FLOOR")
    check("state UNMEASURED never fabricates", m.axis_state(ax, None) == "UNMEASURED")

    # 3: measurement — injectable inputs; sandbox tree counted honestly
    v, ev = m.measure_axis("generated_files")
    check("generated_files measured from sandbox tree", v == 2)
    v, _ = m.measure_axis("generated_loc")
    check("generated_loc measured", v == 3)
    nodes = [{"type": "SurpriseMoment", "source": "engine",
              "timestamp": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()},
             {"type": "SurpriseMoment", "source": "agent",
              "timestamp": datetime.now(timezone.utc).isoformat()}]
    v, ev = m.measure_axis("engine_surprise_rate_per_week", graph_nodes=nodes)
    check("emergence gauge counts ONLY engine-sourced surprises",
          v == 1 and "emergence gauge" in ev)
    board = {"tasks": [{"status": "open"}, {"status": "open"}, {"status": "done"}]}
    v, _ = m.measure_axis("open_board_tasks", board_state=board)
    check("board axis measured from injected state", v == 2)

    # 4: admission control — refuse at wall, name the occupancy rule
    env["axes"]["open_board_tasks"]["max"] = 3
    ok, reason = m.admit("open_board_tasks", delta=2, env=env, board_state=board)
    check("admission refused at the wall, occupancy rule cited",
          not ok and "REFUSED by the container" in reason and "lowest-graded" in reason)
    ok, reason = m.admit("open_board_tasks", delta=1, env=env, board_state=board)
    check("admission allowed inside the wall", ok)
    ok, reason = m.admit("interacting_systems_per_slice", env=env, board_state=board)
    check("unmeasured axis admits on trust, demands a sensor",
          ok and "unmeasured" in reason)

    # 5: the breath — low gauge + headroom => LOOSEN proposal (never applied)
    env2 = m.load_envelope()
    calm_nodes = []          # zero engine surprises this week: sterile
    report = m.tune(env=env2, graph_nodes=calm_nodes, board_state=board)
    env_after = json.loads(m.ENVELOPE_PATH.read_text(encoding="utf-8"))
    pend = env_after.get("pending_adjustments", [])
    check("sterile gauge + headroom -> LOOSEN proposed",
          any(p["direction"] == "loosen" for p in pend) and "BELOW floor" in report)
    check("proposals are pending, walls untouched",
          env_after["axes"]["open_board_tasks"]["max"]
          == m.FOUNDING_ENVELOPE["axes"]["open_board_tasks"]["max"])

    # 6: breach dominates — tighten proposed, never loosen
    board_flood = {"tasks": [{"status": "open"}] * 99}
    report = m.tune(env=json.loads(m.ENVELOPE_PATH.read_text(encoding="utf-8")),
                    graph_nodes=calm_nodes, board_state=board_flood)
    check("breach forces TIGHTEN even when gauge is sterile",
          "TIGHTEN" in report and "LOOSEN" not in report)

    # 7: hard-check feeds the gate (measured hardware/systemic breaches only)
    breaches = m.check_hard(env=json.loads(m.ENVELOPE_PATH.read_text(encoding="utf-8")),
                            graph_nodes=calm_nodes, board_state=board_flood)
    check("gate feed reports the flood, ignores unmeasured axes",
          any(b["axis"] == "open_board_tasks" for b in breaches)
          and all(b["state"] == "BREACH" for b in breaches))

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
