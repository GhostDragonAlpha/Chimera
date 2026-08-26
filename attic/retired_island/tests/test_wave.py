"""Tests for the improvement wave (herald/ripener/bloodhound/metronome/fuzz).
Run: python core/test_wave.py"""

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS = TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    print(("  ok  " if cond else "FAIL  ") + name)
    PASS += cond


def main():
    tmp = Path(tempfile.mkdtemp(prefix="wave_test_"))
    from core.testkit import sandbox
    graph = sandbox(tmp)

    # ---- herald: renders plain words from injected facts -------------------
    from core.herald import render
    md = render({"date": "2026-07-12", "graduated": ["Ground_Sand_Sound"],
                 "breaches": [], "open_tasks": 4, "open_pains": 7,
                 "proposals": [{"direction": "loosen", "axis": "open_board_tasks"}],
                 "will": "trust the red atoms"})
    check("herald: graduation in plain words", "earned full trust" in md
          and "Ground_Sand_Sound" in md)
    check("herald: proposal surfaces as the one human ask",
          "Needs you today:" in md and "rule on the container proposal" in md)
    md2 = render({"date": "x", "open_tasks": 0, "open_pains": 0})
    check("herald: quiet day says rest", "nothing — rest." in md2)

    # ---- ripener: ripe selection + dedupe + seeding -------------------------
    import core.ripener as rip
    import core.graphify_interface as gi
    gi.collect_inheritance = lambda nodes: {"open_pains": [
        {"id": "phase_a:P1", "text": "old worry", "age_days": 9},
        {"id": "phase_b:P1", "text": "fresh worry", "age_days": 1}]}
    ripe = rip.ripe_pains([], age_days=5)
    check("ripener: only aged pains ripen", [p["id"] for p in ripe] == ["phase_a:P1"])
    check("ripener: citation dedupe",
          rip.already_cited("phase_a:P1", [{"recipe": "... phase_a:P1 ...",
                                            "status": "open"}]))
    seeded = rip.tend(max_new=2, age_days=5)
    from core.task_board import _read_state
    tasks = _read_state().get("tasks", [])
    check("ripener: seeds a verdict micro-task with the disposition command",
          len(seeded) == 1 and any("pain-verdict" in t["recipe"] for t in tasks))

    # ---- bloodhound: flip detection + bisect in a throwaway repo -----------
    import core.rep_engine as re_mod
    import sqlite3
    con = sqlite3.connect(re_mod.DB_PATH if re_mod.DB_PATH.parent.exists()
                          else (re_mod.DB_PATH.parent.mkdir(parents=True) or re_mod.DB_PATH))
    con.executescript("CREATE TABLE IF NOT EXISTS reps(id INTEGER PRIMARY KEY, ts REAL,"
                      " run_id TEXT, feature TEXT, atom_id TEXT, passed INTEGER, evidence TEXT);")
    now = time.time()
    rows = [(now - 300, "r1", "F", "atom_z", 1), (now - 100, "r2", "F", "atom_z", 0),
            (now - 300, "r1", "F", "atom_ok", 1), (now - 100, "r2", "F", "atom_ok", 1)]
    con.executemany("INSERT INTO reps(ts, run_id, feature, atom_id, passed, evidence)"
                    " VALUES(?,?,?,?,?,'e')", rows)
    con.commit(); con.close()
    from core.bloodhound import fresh_flips, bisect_flip
    flips = fresh_flips(re_mod.DB_PATH)
    check("bloodhound: detects exactly the still-red flip",
          [f["atom_id"] for f in flips] == ["atom_z"])
    # tiny repo: 3 commits, middle one breaks the probe target
    repo = tmp / "repo"; (repo / "Chimera" / "src").mkdir(parents=True)
    def g(*a): subprocess.run(["git", "-C", str(repo)] + list(a),
                              capture_output=True, timeout=30)
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    f = repo / "Chimera" / "src" / "x.cpp"
    f.write_text("GOOD_TOKEN", encoding="utf-8"); g("add", "-A"); g("commit", "-qm", "c1")
    f.write_text("broken", encoding="utf-8"); g("add", "-A"); g("commit", "-qm", "c2 guilty")
    f.write_text("broken still", encoding="utf-8"); g("add", "-A"); g("commit", "-qm", "c3")
    import core.bloodhound as bh
    bh.REPO = repo
    atom = {"kind": "headless", "probe": {"type": "tree_contains", "root": "src",
                                          "glob": "*.cpp", "regex": "GOOD_TOKEN"}}
    bh._load_atom = lambda feat, aid: atom
    verdict = bisect_flip({"atom_id": "atom_z", "feature": "F",
                           "green_ts": now - 3600, "red_ts": now + 60})
    check("bloodhound: bisect names the guilty commit",
          "guilty_sha" in verdict and "c2 guilty" in verdict.get("subject", ""))
    check("bloodhound: worktree cleaned",
          not any(p.name.startswith("bloodhound_") and (p / "wt").exists()
                  for p in Path(tempfile.gettempdir()).glob("bloodhound_*")))

    # ---- metronome: parsers + metrics ---------------------------------------
    from core.metronome import parse_inputs, parse_feedback, feel_metrics
    chron = [{"kind": "action", "utc": "2026-07-12T18:00:00+00:00", "data": {"key": "W"}},
             {"kind": "action", "utc": "2026-07-12T18:00:02+00:00", "data": {"key_down": "LeftShift"}}]
    log = ("[2026.07.12-18.00.00:080][1]LogTemp: Footstep Sync: Latency=5ms\n"
           "[2026.07.12-18.00.02:120][9]LogTemp: Sprint ON: MaxWalkSpeed=1200\n")
    ins, fbs = parse_inputs(chron), parse_feedback(log)
    check("metronome: both streams parse with UTC alignment",
          len(ins) == 2 and len(fbs) == 2)
    m = feel_metrics(ins, fbs)
    check("metronome: latency median ~100ms band and juice measured",
          m["input_feedback_ms"] is not None and 50 <= m["input_feedback_ms"] <= 150
          and m["juice_density"] > 0)
    check("metronome: honest note when no inputs",
          "note" in feel_metrics([], fbs))

    # ---- fuzz: deterministic jitter, order preserved -------------------------
    from core.sleepwalker import fuzz_spec
    spec = {"beats": [{"name": "a", "actions": [{"key": "W", "hold_s": 2.0},
                                                {"wait": 1.0}]},
                      {"name": "b", "actions": []}]}
    f1, f2 = fuzz_spec(spec, seed=7), fuzz_spec(spec, seed=7)
    check("fuzz: deterministic per seed and order preserved",
          f1 == f2 and [b["name"] for b in f1["beats"]] == ["a", "b"]
          and f1["beats"][0]["actions"][0]["hold_s"] != 2.0
          and spec["beats"][0]["actions"][0]["hold_s"] == 2.0)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
