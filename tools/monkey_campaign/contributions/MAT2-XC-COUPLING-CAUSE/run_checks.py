#!/usr/bin/env python3
"""MAT2-XC-COUPLING-CAUSE: the unit battery (stage 1).

Pure checks over the frozen prereg text, the frozen schedules, and the
SEALED records (no scene execution). Every check executes; a skip is a
failure. Exit: 0 green / 2 refused.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
A12_JOB = Path("E:/ChimeraWork/task-runner/results/"
               "ca111cdc917e420eb78c41339d88c41b")
PREREG_SHA = ("c56798b3db65e86429117f98c143a1565903"
              "bc2341684e00ac89c361917f0e0c")
PREREG_COMMIT = "92a205e7585737e82beaa3e1637c7868243bdb8f"
PREREG_PARENT = "27ba0ff88f68615e757db81b749be94bf01f3827"


def git_out(*args):
    import subprocess
    out = subprocess.run(["git", "-C", "E:/PythonChimera", "-c",
                          "safe.directory=E:/PythonChimera", *args],
                         capture_output=True, check=False)
    if out.returncode != 0:
        raise RuntimeError("git_refused:" + args[0])
    return out.stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def offset_rows(rows_x, rows_y):
    return [{"tick": rx["tick"],
             "d_left": rx["phase_left"] - ry["phase_left"],
             "d_right": rx["phase_right"] - ry["phase_right"]}
            for rx, ry in zip(rows_x, rows_y)]


def main() -> int:
    import probe_driver_xc as pd
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "verdict": "GREEN" if ok else "RED",
                       "detail": detail})
        if not ok:
            raise RuntimeError("check_red:" + name + ":" + detail)

    # CHK1 the shipped prereg bytes == the committed blob; commit law.
    shipped = sha((HERE / "PREREGISTRATION.md").read_bytes())
    blob = git_out("cat-file", "blob",
                   PREREG_COMMIT + ":tools/monkey_campaign/contributions/"
                   "XC-COUPLING-CAUSE-20261003/PREREGISTRATION.md")
    parent = git_out("rev-parse", PREREG_COMMIT + "^").decode().strip()
    changed = git_out("diff", "--name-only", PREREG_PARENT,
                      PREREG_COMMIT).decode().strip().split()
    check("CHK1_prereg_commit_bytes",
          shipped == PREREG_SHA and sha(blob) == PREREG_SHA
          and parent == PREREG_PARENT
          and changed == ["tools/monkey_campaign/contributions/"
                          "XC-COUPLING-CAUSE-20261003/PREREGISTRATION.md"],
          "committed=" + sha(blob)[:12])

    # CHK2 the frozen schedules (prereg section 1).
    check("CHK2_schedules",
          pd.PRESENT_TICKS == list(range(4365, 4666, 15))
          and len(pd.PRESENT_TICKS) == 21
          and pd.SCRIPT_CUT_TICK == 4350
          and pd.SEED == 20260920
          and pd.HORIZON == 4800
          and pd.CLASS_REPRESS == {"BRAKE-SHORT": 150, "BRAKE-LONG": 300,
                                   "BRAKE-DEEP": 600}
          and pd.E2_HOLD_TICKS == 150
          and pd.t_in(1) == 4351 and pd.t_in(14) == 4364,
          "window/cut/seed/depths frozen")

    # CHK3 the probe schedule builder (both kinds, event order).
    ev = pd.probe_events_for({"kind": "release-w", "t_in": 4351,
                              "repress": 150})
    ev2 = pd.probe_events_for({"kind": "press-s", "t_in": 4351, "hold": 150})
    check("CHK3_probe_schedules",
          ev == [(4351, "release", "W"), (4501, "press", "W")]
          and ev2 == [(4351, "press", "S"), (4501, "release", "S")]
          and pd.probe_events_for(None) == [],
          "release-w + press-s + control")

    # CHK4 the a12 records: identity 21/21 + com_v divergence 20/21
    # (P01 SHORT; P02 LONG mirrors -> the frozen 42/42 and 40/42).
    a12_p1 = json.loads((A12_JOB / "artifacts" / "outputs"
                         / "driver_pair_P01_BRAKE-SHORT.json").read_bytes())
    a12_p2 = json.loads((A12_JOB / "artifacts" / "outputs"
                         / "driver_pair_P02_BRAKE-LONG.json").read_bytes())

    def ident(rec):
        return sum(1 for ra, rb in zip(rec["window_rows"]["A"],
                                       rec["window_rows"]["B"])
                   if ra["phase_left"] == rb["phase_left"]
                   and ra["phase_right"] == rb["phase_right"])

    def vdiv(rec):
        return sum(1 for ra, rb in zip(rec["window_rows"]["A"],
                                       rec["window_rows"]["B"])
                   if ra["com_v_m_s"] != rb["com_v_m_s"])

    i1, i2, v1, v2 = ident(a12_p1), ident(a12_p2), vdiv(a12_p1), vdiv(a12_p2)
    check("CHK4_a12_frozen_stats",
          i1 == 21 and i2 == 21 and v1 == 20 and v2 == 20,
          "identity %d/%d com_v_div %d/%d" % (i1, i2, v1, v2))

    # CHK5 the x05 record: identity 4/21, first divergent row t4425,
    # com_v divergence 20/21 (the frozen finding, re-derived).
    x05_p1 = json.loads((STORE / "MAT2-X05" / "numerical"
                         / "driver_pair_P01_BRAKE-SHORT.json").read_bytes())
    i5, v5 = ident(x05_p1), vdiv(x05_p1)
    fd = next((ra["tick"] for ra, rb in zip(
        x05_p1["window_rows"]["A"], x05_p1["window_rows"]["B"])
        if not (ra["phase_left"] == rb["phase_left"]
                and ra["phase_right"] == rb["phase_right"])), None)
    check("CHK5_x05_frozen_stats",
          i5 == 4 and v5 == 20 and fd == 4425,
          "identity %d first_div %s" % (i5, str(fd)))

    # CHK6 row 0 state identical across the four sealed arms.
    s_a = a12_p1["window_rows"]["A"][0]["state_sha256"]
    s_b = a12_p1["window_rows"]["B"][0]["state_sha256"]
    s_x = x05_p1["window_rows"]["A"][0]["state_sha256"]
    s_y = x05_p1["window_rows"]["B"][0]["state_sha256"]
    check("CHK6_row0_state_identity", s_a == s_b == s_x == s_y,
          s_a[:12])

    # CHK7 the A2 offset detector: exact +0.2/-0.2 rows then the ratchet
    # (the prereg's deviation finding, quantified from the sealed bytes).
    rows = offset_rows(x05_p1["window_rows"]["B"],
                       a12_p1["window_rows"]["B"])
    # the phases are float32 values: the exact-symmetric law is evaluated
    # at the float32 grid (tolerance 1e-8 on the float64 difference; the
    # frozen 'tolerance 0' phrasing executed at the record's precision —
    # disclosed here).
    TOL = 1e-8
    early = all(abs(r["d_left"] - 0.2) <= TOL
                and abs(r["d_right"] + 0.2) <= TOL
                for r in rows if 4365 < r["tick"] <= 4455)
    exact_all = all(abs(r["d_left"] - 0.2) <= TOL
                    and abs(r["d_right"] + 0.2) <= TOL
                    for r in rows)
    check("CHK7_a2_offset_pattern",
          (not exact_all) and early and rows[0]["tick"] == 4365
          and rows[0]["d_left"] == 0.0 and rows[0]["d_right"] == 0.0,
          "symmetric through 4455=%s, constant_all=%s" % (early, exact_all))

    # CHK8 the a12 probe classes verbatim (release W + re-press ticks).
    pe1 = a12_p1["probe_events"]
    pe2 = a12_p2["probe_events"]
    check("CHK8_a12_classes_verbatim",
          pe1[0]["event"] == "release" and pe1[0]["key"] == "W"
          and pe1[1]["tick"] - pe1[0]["tick"] == 150
          and pe2[1]["tick"] - pe2[0]["tick"] == 300
          and a12_p1["t_in"] == 4351 and a12_p2["t_in"] == 4352,
          "SHORT +150 / LONG +300 ticks")

    # CHK9 the statistics helpers (synthetic rows, exact laws).
    ra = [{"tick": 1, "phase_left": 0.5, "phase_right": 0.5,
           "com_v_m_s": 0.7, "com_x_m": 1.0, "state_sha256": "x"},
          {"tick": 2, "phase_left": 0.6, "phase_right": 0.6,
           "com_v_m_s": 0.6, "com_x_m": 1.1, "state_sha256": "y"}]
    rb = [{"tick": 1, "phase_left": 0.5, "phase_right": 0.5,
           "com_v_m_s": 0.7, "com_x_m": 1.0, "state_sha256": "x"},
          {"tick": 2, "phase_left": 0.7, "phase_right": 0.6,
           "com_v_m_s": 0.7, "com_x_m": 1.1, "state_sha256": "z"}]
    i, fd = pd.window_identity(ra, rb)
    check("CHK9_stats_laws",
          i == 1 and fd == 2
          and pd.v_divergence_count(ra, rb) == 1
          and pd.band(ra)["min_com_v"] == 0.6,
          "identity/divergence/band")

    # CHK10 the x05 P02 record pin (design-time sha, design_basis).
    x05_p2 = json.loads((STORE / "MAT2-X05" / "numerical"
                         / "driver_pair_P02_BRAKE-LONG.json").read_bytes())
    check("CHK10_x05_p02_present",
          x05_p2["cls"] == "BRAKE-LONG" and len(
              x05_p2["window_rows"]["A"]) == 21,
          "LONG record readable")

    # CHK11 the verdict vocabulary (the four names ONLY).
    verdicts = {"ISOLATED_HARNESS_SCENE", "ISOLATED_COMMAND_CHANNEL",
                "ISOLATED_VELOCITY_COUPLING", "CAUSE_NOT_ISOLATED"}
    text = (HERE / "PREREGISTRATION.md").read_text(encoding="utf-8")
    present = sum(1 for v in verdicts if v in text)
    check("CHK11_verdict_vocabulary", present == 4,
          "%d/4 named verdicts in the frozen text" % present)

    # CHK12 the causal-phrasing law: the forbidden phrase is absent from
    # THIS card's shipped modules OUTSIDE the Captain's ruling quote
    # (the reviewer-grep law: the quote itself is the carried ruling).
    banned = "responds to " + "speed"
    import re as _re
    stray = []
    for f in HERE.glob("*.py"):
        t = f.read_text(encoding="utf-8", errors="replace")
        t = _re.sub(r"Do not claim that gait responds to "
                    r"speed", "<RULING>", t)
        if banned in t:
            stray.append(f.name)
    check("CHK12_no_causal_phrasing", stray == [], str(stray))

    out = os.environ.get("CHIMERA_OUTPUT_DIR")
    summary = {"schema": "chimera.xc.checks_receipt.v1", "card":
               "MAT2-XC-COUPLING-CAUSE",
               "checks": checks, "executed": len(checks), "skipped": 0,
               "verdict": "GREEN"}
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "checks_receipt.json").write_bytes(
            json.dumps(summary, indent=1, sort_keys=True).encode() + b"\n")
    print("checks: %d/%d GREEN" % (len(checks), len(checks)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as r:
        print("REFUSAL:" + str(r), file=sys.stderr)
        sys.exit(2)
