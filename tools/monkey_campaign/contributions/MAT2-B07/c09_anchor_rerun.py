#!/usr/bin/env python3
"""MAT2-B07 D4: the C09 anchor-class re-run of the CERTIFIED CPU walk backend.

TC-12 symmetric clause receipt: the certified 10.037998 kg walking line is
re-run IN THIS ATTEMPT from pinned extractions and must reproduce its frozen
anchors EXACTLY — the adoption records invalidate nothing silently. Any
drift = refusal `anchor_drift` (the falsifier must be able to FAIL).

Pinned anchors (MAT2-W03 sealed, independently review-verified):
  scene.json   f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342
  stdout       8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc
  stderr       c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481
  dumps run1==run2  b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93
  ticks 302 (0..301), exit 0
  base dx 0.9131056683968011, base dy -0.7178374101385098
  worst ledger 30.970714 J (raw balance_error_J 30.970713623726674, tick 300)

Method: extract the six pinned 17ba94b9 blobs from the E:/PythonChimera
object store (the W03 extraction record is the pin reference), verify every
sha256, rebuild the statedump with the P02/W03-pinned cl recipe, replay the
SEALED scene bytes (raw byte capture, no argv[2], GAIT_STATE_DUMP{,2} set),
twice, and compare every anchor. Heavy artifacts stay in the attempt scratch
(the receipt + digests land in the card dir); the candidate tree stays clean.

Run:  python -B c09_anchor_rerun.py
Exit: 0 green / 2 named refusal. CPU only.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = Path(r"E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-B07"
          r"\08d3db08d4d64179b2f95a516a2155bd")
SCRATCH = WS / "scratch" / "c09"
REPO = Path("E:/PythonChimera")
W03_SCENE = Path(r"E:\ChimeraWork\monkey-coordination\kanban-attempts"
                 r"\MAT2-W03\sergeant-arrival-db26712d\scene_out\scene.json")
VCVARS = (r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
          r"\VC\Auxiliary\Build\vcvarsall.bat")

REVISION = "17ba94b948ca217c1bbf8f7dee5b51b995b387bb"
BLOBS = {
    "ChimeraEngine/engine/coupled_articulation.hpp":
        "5bd73c2d43b85b229040da1ac779ef3733dc7d4dbe04cbeb1447c03767dc9fb5",
    "ChimeraEngine/engine/earth_environment.hpp":
        "b4747d349ce201ebadb74227b33725466d16edd860ed421ac590ad789178469a",
    "ChimeraEngine/engine/force_models.hpp":
        "483b97f4600ce0e4c178bc0d9420de55ae9cb853910e3c38a3e5cf9919f0630c",
    "ChimeraEngine/engine/gait_controller.hpp":
        "f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd",
    "ChimeraEngine/native/viewer3rd/json.hpp":
        "9bea4c8066ef4a1c206b2be5a36302f8926f7fdc6087af5d20b417d0cf103ea6",
    "tools/science_funnel/validation/visible_walk_20260923/native/"
    "gait_unit_viswalk_dump.cpp":
        "dea2be78762860b201a348824fd6a4a4fe9f2a1dd3f9552157187729568f1cab",
}
SCENE_SHA256 = ("f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25"
                "a8db342")
ANCHORS = {
    "stdout_sha256": "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73"
                     "ed5d60b06cc",
    "stderr_sha256": "c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e19"
                     "50651c37481",
    "dump_sha256": "b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de46"
                   "2319389c93",
    "n_ticks": 302,
    "tick_first_last": [0, 301],
    "base_dx": 0.9131056683968011,
    "base_dy": -0.7178374101385098,
    "refused_tick": 302,
    "worst_ledger_J_rounded": 30.970714,
}

REFUSAL_PIN = "input_pin_mismatch"
REFUSAL_DRIFT = "anchor_drift"
REFUSAL_BUILD = "build_failed"


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def git_blob(rev_path):
    out = subprocess.run(
        ["git", "-C", str(REPO), "cat-file", "blob", rev_path],
        capture_output=True, check=True)
    return out.stdout


def extract_sources():
    layout = SCRATCH / "engine_tree17"
    extracted = {}
    for rel, expected in BLOBS.items():
        data = git_blob(REVISION + ":" + rel)
        digest = sha_bytes(data)
        require(digest == expected,
                REFUSAL_PIN + ":" + rel + ":" + digest[:12])
        target = layout / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        extracted[rel] = {"sha256": digest, "bytes": len(data)}
    return layout, extracted


def stage_scene():
    data = W03_SCENE.read_bytes()
    digest = sha_bytes(data)
    require(digest == SCENE_SHA256,
            REFUSAL_PIN + ":scene:" + digest[:12])
    target = SCRATCH / "scene.json"
    target.write_bytes(data)
    return target, digest


def build(layout):
    native = (layout / "tools/science_funnel/validation"
              / "visible_walk_20260923/native" / "gait_unit_viswalk_dump.cpp")
    require(native.exists(), REFUSAL_BUILD + ":source_missing")
    src = (layout / "ChimeraEngine/engine/tests_coupled_arm"
           / "gait_unit_viswalk_dump.cpp")
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_bytes(native.read_bytes())
    outdir = SCRATCH / "build"
    outdir.mkdir(parents=True, exist_ok=True)
    exe = outdir / "gait_unit_viswalk_dump.exe"
    batch = outdir / "build_cmd.bat"
    batch.write_text(
        "@echo off\r\n"
        "call \"" + VCVARS + "\" x64\r\n"
        "cl /nologo /std:c++17 /O2 /W4 /fp:precise /EHsc /DGAIT_EVENT_TRACE "
        "\"" + str(src) + "\" /Fe:\"" + str(exe) + "\" "
        "/Fo\"" + str(outdir / "dump.obj") + "\" 2>&1\r\n",
        encoding="utf-8")
    proc = subprocess.run(["cmd", "/c", str(batch)], capture_output=True)
    (outdir / "build_log.txt").write_bytes(
        proc.stdout + b"\n" + proc.stderr)
    require(exe.exists(), REFUSAL_BUILD + ":no_exe")
    return exe, sha_bytes(exe.read_bytes())


def run_replay(exe, scene_path, run_index):
    outdir = SCRATCH / ("run" + str(run_index))
    outdir.mkdir(parents=True, exist_ok=True)
    dump1 = outdir / "states_run1.jsonl"
    dump2 = outdir / "states_run2.jsonl"
    env = dict(PATH="", SYSTEMROOT="", TEMP="", TMP="")
    import os
    env = os.environ.copy()
    env["GAIT_STATE_DUMP"] = str(dump1)
    env["GAIT_STATE_DUMP2"] = str(dump2)
    t0 = time.time()
    proc = subprocess.run([str(exe), str(scene_path)], env=env,
                          capture_output=True)
    wall = time.time() - t0
    stdout_path = outdir / "dump_stdout.txt"
    stderr_path = outdir / "dump_stderr.txt"
    stdout_path.write_bytes(proc.stdout)
    stderr_path.write_bytes(proc.stderr)
    require(proc.returncode == 0,
            REFUSAL_DRIFT + ":exit:" + str(proc.returncode))
    return {
        "exit": proc.returncode,
        "wall_s": round(wall, 1),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "dump1_path": str(dump1),
        "dump2_path": str(dump2),
        "stdout_sha256": sha_bytes(proc.stdout),
        "stderr_sha256": sha_bytes(proc.stderr),
        "dump1_sha256": sha_bytes(dump1.read_bytes()),
        "dump2_sha256": sha_bytes(dump2.read_bytes()),
    }


def parse_run(run):
    stdout_text = Path(run["stdout_path"]).read_text(
        encoding="utf-8", errors="replace")
    m = re.search(r"WALK refused_tick=(\d+) "
                  r"worst_ledger_J=([0-9.]+)", stdout_text)
    require(m is not None, REFUSAL_DRIFT + ":walk_line_missing")
    lines = Path(run["dump1_path"]).read_text(encoding="utf-8").splitlines()
    require(lines and lines[0].strip() and lines[-1].strip(),
            REFUSAL_DRIFT + ":dump_empty")
    first = json.loads(lines[0])
    last = json.loads(lines[-1])
    return {"refused_tick": int(m.group(1)),
            "worst_ledger_J_rounded": float(m.group(2)),
            "n_ticks": len(lines),
            "tick_first_last": [first["tick"], last["tick"]],
            "base_dx": last["q"][3] - first["q"][3],
            "base_dy": last["q"][4] - first["q"][4]}


def main():
    layout, extracted = extract_sources()
    scene_path, scene_sha = stage_scene()
    exe, exe_sha = build(layout)
    run1 = run_replay(exe, scene_path, 1)
    run2 = run_replay(exe, scene_path, 2)
    parsed = parse_run(run1)
    comparisons = {}
    for key, frozen in ANCHORS.items():
        if key == "stdout_sha256":
            got = run1["stdout_sha256"]
        elif key == "stderr_sha256":
            got = run1["stderr_sha256"]
        elif key == "dump_sha256":
            got = run1["dump1_sha256"]
        else:
            got = parsed.get(key)
        verdict = "EXACT" if got == frozen else "DRIFT"
        comparisons[key] = {"frozen": frozen, "reproduced": got,
                            "verdict": verdict}
        require(verdict == "EXACT", REFUSAL_DRIFT + ":" + key
                + ":" + repr(got) + "!=" + repr(frozen))
    require(run1["dump1_sha256"] == run1["dump2_sha256"],
            REFUSAL_DRIFT + ":run1_dumps_differ")
    require(run1["dump1_sha256"] == run2["dump1_sha256"],
            REFUSAL_DRIFT + ":rerun_dumps_differ")
    prereg_sha = sha_bytes((HERE / "PREREGISTRATION.md").read_bytes())
    receipt = {
        "schema": "chimera.b07_c09_anchor_rerun.v1",
        "task_id": "B07",
        "card_id": "MAT2-B07",
        "preregistration_sha256": prereg_sha,
        "statement": "TC-12 symmetric clause receipt: the certified CPU "
                     "walk backend re-run from pinned extractions inside "
                     "this attempt reproduces every frozen anchor EXACTLY; "
                     "the adoption records invalidate nothing silently",
        "object_replayed": "the CERTIFIED 10.037998 kg walking line (the "
                           "current body), NOT the adopted assembly",
        "source_revision": REVISION,
        "extraction": {"layout": str(layout).replace("\\", "/"),
                       "blobs": extracted,
                       "pin_reference": "MAT2-W03 extract_record.json "
                                        "(PR-1 four-anchor blob identity)"},
        "scene": {"path": str(scene_path).replace("\\", "/"),
                  "sha256": scene_sha},
        "build": {"recipe": "P02/W03-pinned cl (vcvars x64; /std:c++17 /O2 "
                            "/W4 /fp:precise /EHsc /DGAIT_EVENT_TRACE)",
                  "exe_sha256": exe_sha,
                  "exe_note": "fresh binary hash differs from the P02 "
                              "build by design (compiler embeds paths); "
                              "the outputs are the identity",
                  "build_log": str((SCRATCH / "build"
                                    / "build_log.txt")).replace("\\", "/")},
        "runs": {"run1": run1, "run2": run2,
                 "dumps_bit_identical_within_run": True,
                 "rerun_dump_identity": run1["dump1_sha256"]
                 == run2["dump1_sha256"]},
        "anchor_comparisons": comparisons,
        "scope_law": "this receipt re-runs the EXISTING certified backend; "
                     "it claims no new backend and no adopted-assembly "
                     "runtime (TC-5: a new backend must reproduce the "
                     "anchor class on itself before its outputs are "
                     "evidence)",
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B c09_anchor_rerun.py"},
    }
    out = HERE / "c09_anchor_rerun" / "c09_anchor_rerun.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(json.dumps(receipt, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"),
                               allow_nan=False).encode("utf-8") + b"\n")
    print("wrote", out)
    print("anchors EXACT:", sum(1 for c in comparisons.values()
                                if c["verdict"] == "EXACT"), "/",
          len(comparisons))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
