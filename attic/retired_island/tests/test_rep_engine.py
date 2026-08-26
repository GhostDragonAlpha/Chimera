"""Tests for core.rep_engine — run: python core/test_rep_engine.py"""

import json
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import rep_engine as re_mod
from core.rep_engine import (_FileCache, make_atom, merge_battery, load_battery,
                             parse_sleepwalker_actions, build, run, status,
                             rep_gate, maybe_promote, tend, export_pie, PROBES)

PASS = 0
TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        print(f"FAIL  {name}")


def sandbox():
    """Point the module at a throwaway ROOT with fixture files."""
    tmp = Path(tempfile.mkdtemp(prefix="rep_engine_test_"))
    re_mod.ROOT = tmp
    re_mod.BATTERY_DIR = tmp / "docs" / "rep_batteries"
    re_mod.PIE_MANIFEST = re_mod.BATTERY_DIR / "pie_manifest.json"
    re_mod.DB_PATH = tmp / "docs" / "world" / "reps.db"
    re_mod.CLAUDE_MD = tmp / "CLAUDE_ABSENT.md"
    src = tmp / re_mod.SOURCE_TREE
    (src / "Sound").mkdir(parents=True)
    (src / "Tools").mkdir(parents=True)
    (src / "Sound" / "SandSoundComponent.h").write_text(
        "UCLASS()\nclass CHIMERA_API USandSoundComponent : public UActorComponent\n"
        "{\n UPROPERTY(EditAnywhere)\n float FootstepVolume = 1.0f;\n"
        " UPROPERTY(EditAnywhere)\n int32 DeadMetadataProp;\n};\n", encoding="utf-8")
    (src / "Sound" / "SandSoundComponent.cpp").write_text(
        "#include \"SandSoundComponent.h\"\n"
        "void F() { float v = FootstepVolume; }\n"
        "// attach: CreateDefaultSubobject<USandSoundComponent>(TEXT(\"Sand\"));\n",
        encoding="utf-8")
    (src / "Tools" / "Shovel.cpp").write_text(
        "void ATool_Shovel::Dig() { /* behavior */ }\n", encoding="utf-8")
    audio = tmp / "Content" / "Audio" / "Footsteps"
    audio.mkdir(parents=True)
    (audio / "SandL1.wav").write_bytes(b"RIFF")
    (audio / "SandL1.uasset").write_bytes(b"\x00asset")
    (audio / "OrphanR9.wav").write_bytes(b"RIFF")      # deliberately unpaired
    (audio / "SOURCES.md").write_text("CC0", encoding="utf-8")
    levels = tmp / "Content" / "Levels"
    levels.mkdir(parents=True)
    (levels / "L_RegolithYard.umap").write_bytes(b"\x01map")
    (levels / "chimeradefaultlevel.umap").write_bytes(b"real level content")
    beats = tmp / "docs" / "beats"
    beats.mkdir(parents=True)
    (beats / "demo.beats.json").write_text(json.dumps({
        "beats": [{"name": "walk", "actions": [{"key": "W", "hold_s": 1.0}]},
                  {"name": "bad", "actions": [{"teleport_home": True}]}]}),
        encoding="utf-8")
    (tmp / "core").mkdir()
    (tmp / "core" / "sleepwalker.py").write_text(
        'def _do_action(self, a):\n'
        '    if "key" in a: pass\n'
        '    elif "wait" in a: pass\n'
        '    elif "screenshot" in a: pass\n', encoding="utf-8")
    (tmp / "tests" / "dsl_grammar").mkdir(parents=True)
    (tmp / "tests" / "dsl_grammar" / "demo.chimera").write_text(
        "FootstepVolume: 1.0\nMissingToken_XYZ: true\n", encoding="utf-8")
    return tmp


def main():
    tmp = sandbox()
    cache = _FileCache(re_mod.ROOT)

    # 1-2: positive probes
    ok, _ = PROBES["glob_nonempty"]({"pattern": "Content/Audio/Footsteps/SandL1.uasset"}, cache)
    check("glob_nonempty hit", ok)
    ok, _ = PROBES["glob_nonempty"]({"pattern": "Content/Audio/Footsteps/OrphanR9.uasset"}, cache)
    check("glob_nonempty miss", not ok)
    ok, _ = PROBES["tree_contains"](
        {"root": re_mod.SOURCE_TREE, "glob": "*.cpp", "regex": r"::Dig\s*\("}, cache)
    check("tree_contains verb body", ok)

    # 3: the inversion probe — passes on ABSENCE, fails on presence
    ok, _ = PROBES["tree_lacks"](
        {"root": f"{re_mod.SOURCE_TREE}/Sound", "glob": "*.cpp", "regex": r"=\s*999\b"}, cache)
    check("tree_lacks clean pass", ok)
    (Path(tmp) / re_mod.SOURCE_TREE / "Sound" / "Bad.cpp").write_text(
        "latency = 999;", encoding="utf-8")
    ok, ev = PROBES["tree_lacks"](
        {"root": f"{re_mod.SOURCE_TREE}/Sound", "glob": "*.cpp", "regex": r"=\s*999\b"},
        _FileCache(re_mod.ROOT))
    check("tree_lacks catches sentinel", not ok and "FORBIDDEN" in ev)
    (Path(tmp) / re_mod.SOURCE_TREE / "Sound" / "Bad.cpp").unlink()

    # 4: template-stamp trap
    ok, _ = PROBES["file_md5_not"](
        {"path": "Content/Levels/chimeradefaultlevel.umap", "md5_prefix": "b734cff5"}, cache)
    check("md5_not passes on real level", ok)

    # 5: beat action registry (H-17)
    registry = parse_sleepwalker_actions((Path(tmp) / "core" / "sleepwalker.py").read_text())
    check("action registry parsed", {"key", "wait", "screenshot"} <= registry)
    ok, ev = PROBES["beats_registered"]({}, _FileCache(re_mod.ROOT))
    check("unregistered beat action caught", not ok and "teleport_home" in ev)

    # 6: battery merge idempotent + additive
    a1 = make_atom("TestFeat", 0, "glob_nonempty", {"pattern": "core/sleepwalker.py"},
                   "exists", "test")
    merged = merge_battery("TestFeat", [a1])
    merged2 = merge_battery("TestFeat", [a1, make_atom(
        "TestFeat", 1, "tree_contains",
        {"root": "core", "glob": "*.py", "regex": "screenshot"}, "used", "test")])
    check("merge idempotent+additive", len(merged) == 1 and len(merged2) == 2
          and len(load_battery("TestFeat")) == 2)

    # 7: generators compose real batteries; run records verdicts
    built = build()
    check("generators build batteries", sum(built.values()) >= 10
          and any("Ground_Sand_Sound" in f for f in built))
    summary = run()
    total_verdicts = sum(s["passed"] + s["failed"] for s in summary.values())
    check("run records verdicts", total_verdicts >= 10)
    orphan_feat = summary.get("Ground_Sand_Sound", {})
    check("orphan wav fails its pairing atom", orphan_feat.get("failed", 0) >= 1)

    # 8: rep gate thresholds (synthetic ledger volume)
    ok, reason = rep_gate("TestFeat")
    check("gate refuses below threshold", not ok)
    con = sqlite3.connect(re_mod.DB_PATH)
    now = time.time()
    for r in range(10):
        rid = f"synth_{r}"
        for i in range(30):
            con.execute("INSERT INTO reps(ts, run_id, feature, atom_id, passed, evidence)"
                        " VALUES(?,?,?,?,?,?)",
                        (now + r * 60 + i, rid, "TestFeat", f"atom_x{i}", 1, "synth"))
    con.commit()
    con.close()
    ok, reason = rep_gate("TestFeat")
    check("gate opens at threshold+streak", ok)

    # 9: shaping promotion on streak
    msg = maybe_promote("TestFeat")
    st = status("TestFeat")
    check("promotion raises tier on streak", st["tier"] == 1 and "tier 0 -> 1" in msg)

    # 10: tend + pie export
    out = tend()
    n_pie = export_pie()
    check("tend summarizes", out.startswith("[rep]") and "reps this pass" in out)
    check("pie manifest written", re_mod.PIE_MANIFEST.exists() and n_pie >= 0)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
