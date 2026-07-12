"""Tests for core.decomposer — run: python core/test_decomposer.py"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS = TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    print(("  ok  " if cond else "FAIL  ") + name)
    PASS += cond


def main():
    tmp = Path(tempfile.mkdtemp(prefix="decomposer_test_"))

    # THE UNIVERSAL SANDBOX (core.testkit): every store redirected in one
    # call — the surprise_e3944cb57b2994f0 leak class is now impossible.
    from core.testkit import sandbox
    graph = sandbox(tmp)
    from core import decomposer as dc
    from core import task_board as tb
    from core import rep_engine as re_mod

    # 1: founding templates self-install
    templates = dc.load_templates()
    check("templates self-install to JSON", dc.TEMPLATES_PATH.exists()
          and "input_rig" in templates and "component_attachment" in templates)
    parts = templates["input_rig"]["parts"]
    check("every part is independently verifiable (footprint + verify)",
          all(p.get("files") and p.get("verify") for p in parts))

    # 2: dry-run resolves parts without touching the board
    manifest = dc.decompose("Sprint_Input", "input_rig",
                            ["simtest_x", "elim_y"], dry_run=True)
    check("dry-run yields 4 parts, no board writes",
          len(manifest["parts"]) == 4 and not tb.STATE_PATH.exists())

    # 3: unknown kind refuses loudly (grow the JSON, never the engine)
    try:
        dc.decompose("X", "nonexistent_kind", ["e"], dry_run=True)
        refused = False
    except KeyError as e:
        refused = "grow docs" in str(e)
    check("unknown kind refuses with growth instruction", refused)

    # 4: live decompose seeds tasks with dependency edges + not_scope
    # (graph writes land in the testkit's in-memory dict, never the live store)
    manifest = dc.decompose("Sprint_Input", "input_rig", ["simtest_x"])
    check("decomposition recorded in SANDBOX graph, real helper exercised",
          any(n.get("type") == "Decomposition" for n in graph["nodes"]))
    state = json.loads(tb.STATE_PATH.read_text(encoding="utf-8"))
    tasks = {t["feature"]: t for t in state["tasks"]}
    check("4 board tasks seeded, one per part", len(state["tasks"]) == 4)
    binding = tasks.get("Sprint_Input/binding")
    stt = tasks.get("Sprint_Input/state")
    check("dependency edges follow the template ('binding' after 'state')",
          binding and stt and stt["id"] in binding["depends_on"])
    check("parts carry not_scope naming their siblings",
          binding and "Sprint_Input/state" in binding["not_scope"]["subsystems"])
    check("task recipes cite the decomposition id + evidence",
          "dc_" in binding["recipe"] and "simtest_x" in binding["recipe"])

    # 5: atoms minted per part (pie parts marked pie, never silently headless)
    readback_battery = re_mod.load_battery("Sprint_Input/readback")
    state_battery = re_mod.load_battery("Sprint_Input/state")
    check("rep atoms minted per part", len(state_battery) == 1
          and len(readback_battery) == 1)
    check("pie verify stays pie", readback_battery[0]["kind"] == "pie"
          and state_battery[0]["kind"] == "headless")

    # 6: monolith guard — a bare-parent open task gets blocked
    tb.add_task("Sprint_Input (the whole system)", "fix sprint",
                feature="Sprint_Input")
    manifest2 = dc.decompose("Sprint_Input", "input_rig", ["simtest_z"])
    state = json.loads(tb.STATE_PATH.read_text(encoding="utf-8"))
    monolith = [t for t in state["tasks"] if t["title"].startswith("Sprint_Input (the whole")]
    check("monolith guard blocks the bare-parent task",
          monolith and monolith[0]["status"] == "blocked"
          and manifest2["blocked_monoliths"] == [monolith[0]["id"]]
          and "claim the parts, not the system" in monolith[0]["notes"][-1]["text"])

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
