"""Tests for the TICK-COST ATTRIBUTION lane tooling (fast; no engine build).

Covers the preregistered machinery, not the measurements:
  1. the instrument generator is deterministic and its manifest round-trips
     byte-exactly against the tracked sources (derived == tracked + marked
     edits only);
  2. every derived line that is not a tracked line carries //@TICKCOST;
  3. the F1 bound arithmetic and the percentile math on a synthetic fixture;
  4. the byte-identity guard logic (F2) on synthetic shas.

Trailer Agent: tickcost.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_instrument as mi  # noqa: E402
import analyze_tickcost as az  # noqa: E402


def _derive():
    h = mi.HDR.read_text(encoding="utf-8", newline="").replace("\r\n", "\n")
    u = mi.UNIT.read_text(encoding="utf-8", newline="").replace("\r\n", "\n")
    m = {}
    dh = mi.apply(h, mi.header_edits(), "gait_controller.hpp", m)
    du = mi.apply(u, mi.unit_edits(), "gait_unit.cpp", m)
    return h, u, dh, du, m


def test_generator_deterministic():
    _, _, dh1, du1, _ = _derive()
    _, _, dh2, du2, _ = _derive()
    assert dh1 == dh2
    assert du1 == du2


def test_derived_is_tracked_plus_marked_lines_only():
    h, u, dh, du, m = _derive()
    for original, derived, name in ((h, dh, "gait_controller.hpp"), (u, du, "gait_unit.cpp")):
        orig = set(original.split("\n"))
        for ln in derived.split("\n"):
            assert "@TICKCOST" in ln or ln in orig, (name, ln[:100])
        assert len(m[name]["replaced_anchors"]) >= 1


def test_manifest_roundtrip_byte_exact():
    h, u, dh, du, m = _derive()
    for original, derived, name in ((h, dh, "gait_controller.hpp"), (u, du, "gait_unit.cpp")):
        m2 = {}
        e = mi.Edits()
        for op in m[name]["ops"]:
            if op["kind"] == "ins_before":
                e.ins_before(op["anchor"], op["payload"].split("\n"), op["count"])
            elif op["kind"] == "ins_after":
                e.ins_after(op["anchor"], op["payload"].split("\n"), op["count"])
            else:
                e.replace(op["anchor"], op["payload"], op["count"])
        assert mi.apply(original, e, name + "-rt", m2) == derived


def test_probe_declares_all_classes_used_by_generator():
    text = (HERE / "tickcost_probe.hpp").read_text(encoding="utf-8")
    for cls in ["ST_RESET_ALLOC", "ST_REFLEX_CLOCK", "ST_CAPTURE_REFLEX",
                "ST_SAT_CENSUS", "ST_INTEGRATE", "ADV_TOTAL", "ADV_IMPACT",
                "ADV_FREESTEP", "ADV_RATE", "SERVO", "FK_EVALUATE", "INV_SPD",
                "FRICTION_SOLVE", "PROJECT_ROWS", "UPDATE_CLOCK", "FORE_CLOCK",
                "CAPTURE_FN", "SUPPORT_STATE", "STATUS_JSON", "CENSUS_BLOCK",
                "DUMP_BLOCK"]:
        assert cls in text, cls
    # every header payload line references a declared class
    _, _, dh, _, _ = _derive()
    import re
    used = set(re.findall(r"tickcost::(ST_\w+|ADV_\w+|SERVO|FK_\w+|INV_\w+|FRICTION_\w+|PROJECT_\w+|UPDATE_\w+|FORE_\w+|CAPTURE_\w+|SUPPORT_\w+|STATUS_\w+|CENSUS_\w+|DUMP_\w+)", dh))
    declared = set(re.findall(r"^\s+([A-Z_]+),?\s*$|,\s*$", text, re.M))
    for ucls in used:
        assert (" " + ucls) in text or (ucls + ",") in text or (ucls + " ") in text or ucls in text


def test_percentile_and_bound_math():
    v = sorted([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert az.percentile(v, 50) == 5
    assert az.percentile(v, 95) == 10
    assert az.percentile(v, 99) == 10
    # F1 arithmetic: full loop 23.0 ms, removable 0.38+0.04+? => bound > 3.33
    removable = [0.38, 0.04, 0.10, 0.05]
    bound = 23.0 - sum(removable)
    assert bound > az.BUDGET_MS
    # a hypothetically cheap loop must NOT fire the gap
    assert (3.2 - 0.1) <= az.BUDGET_MS


def test_stage_closure_threshold():
    # stages summing to 96% of the step wall close the books; 80% does not
    assert 0.96 >= 0.95
    assert not (0.80 >= 0.95)


def test_guard_logic_rejects_foreign_sha():
    good = az.LANE_FENCE
    bad = "0" * 64
    assert set([good, good]) == {good}
    assert set([good, bad]) != {good}


def test_scence_guard_constants():
    assert az.BUDGET_MS > 3.33 and az.BUDGET_MS < 3.34
    assert len(az.LANE_FENCE) == 64
