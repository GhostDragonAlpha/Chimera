#!/usr/bin/env python
"""H8 world-doctor scratch repro: replay the LIVE seal history on a private
engine (port 8138, isolated cwd, G4's throwaway recipe) and bisect which
/tick_seal entry creates the degenerate (V~0) cell.

Modes:
  bisect  - boot EMPTY cwd, POST the four snapshot blobs, then POST each
            history line, capturing /tick_state after every entry.
  restore - copy blobs+history into the cwd BEFORE boot (boot restore replays
            them), then capture /tick_state -- the live-boot equivalence test.
"""
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(r"E:\ChimeraWork\slot-01")
EXE = REPO / ".h8_scratch" / "build" / "Release" / "chimera_engine.exe"
LIVE_SNAP = REPO / ".tmp" / "build_tick" / "Release" / "session_snapshot"
SCRATCH = REPO / ".h8_scratch"
PORT = 8138
BASE = f"http://127.0.0.1:{PORT}"
ENDPOINTS = ["mesh_bin", "tick_joints", "tick_classify", "tick_vertbind"]


def get_json(path, timeout=5):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def post_raw(path, body, timeout=120):
    req = urllib.request.Request(
        BASE + path, data=body if isinstance(body, bytes) else body.encode(),
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return f"HTTP{e.code}:{e.read().decode('utf-8', 'replace')[:200]}"


def cell_summary(st):
    out = []
    for i, c in enumerate(st.get("cells", [])):
        out.append({"i": i, "v0": c["v0"], "V": c["V"], "P": c["P"],
                    "pieces": c["pieces"], "caps": c["caps"],
                    "ylo": c["ylo"], "yhi": c["yhi"],
                    "degenerate": c.get("degenerate")})
    return out


def wait_up(proc, log_path, wait_s=120):
    deadline = time.time() + wait_s
    while time.time() < deadline:
        if proc.poll() is not None:
            print(f"engine DIED at boot rc={proc.returncode}; log tail:")
            print("\n".join(log_path.read_text(errors='replace').splitlines()[-25:]))
            sys.exit(2)
        try:
            st = get_json("/tick_state", timeout=2)
            if st.get("sealed") is True:
                print("boot: engine answered but already SEALED -- isolation failed")
                sys.exit(3)
            return st
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    print("engine never answered")
    sys.exit(4)


def boot(run_dir):
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(EXE.parent / "shaders", run_dir / "shaders",
                    dirs_exist_ok=True)
    log_path = run_dir / "engine.log"
    logf = open(log_path, "ab")
    proc = subprocess.Popen(
        [str(EXE), str(PORT), "--hidden"], cwd=str(run_dir),
        stdout=logf, stderr=logf,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    return proc, log_path


def kill(proc):
    if proc and proc.poll() is None:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True)
        proc.wait(timeout=20)
    time.sleep(1.0)


def mode_bisect(out_path):
    run_dir = SCRATCH / "run_bisect"
    kill_by_port_dir(run_dir)
    if run_dir.exists():
        shutil.rmtree(run_dir)
    proc, log_path = boot(run_dir)
    st = wait_up(proc, log_path)
    print("boot: empty, sealed =", st["sealed"])
    timeline = []
    # 1. the four blobs, k_snapshot_endpoints order
    for ep in ENDPOINTS:
        blob = (LIVE_SNAP / f"{ep}.blob").read_bytes()
        resp = post_raw(f"/{ep}", blob)
        timeline.append({"step": f"POST /{ep}", "resp": resp[:80],
                         "n_cells": len(get_json("/tick_state")["cells"])})
        print(f"{ep}: {resp[:60]} n_cells={timeline[-1]['n_cells']}")
    # 2. the seal history, entry by entry
    lines = [l.strip() for l in
             (LIVE_SNAP / "tick_seal_history.log").read_text().splitlines()
             if l.strip()]
    for n, line in enumerate(lines, 1):
        resp = post_raw("/tick_seal", line)
        st = get_json("/tick_state")
        rec = {"step": n, "body": line, "resp": resp[:80],
               "n_cells": st["n_cells"], "cells": cell_summary(st),
               "conserve_pct": st["conserve_pct"],
               "seal_refusal": st.get("seal_refusal", "")}
        timeline.append(rec)
        deg = [c for c in rec["cells"]
               if c["v0"] < 1e-6 or abs(c["P"]) > 1e8]
        print(f"seal {n:2d} {line:32s} ok={resp[:12]} n_cells={st['n_cells']}"
              f" refusal={st.get('seal_refusal','')!r}"
              + (f"  DEGENERATE: {json.dumps(deg)}" if deg else ""))
    # THE POSE PROBE: the live poison read 1.6228 GPa under lesson poses.
    # On the guarded build every cell must answer a finite, sub-yield P.
    pose_resp = post_raw("/tick_pose", "{\"joint\":\"knee_L\",\"deg\":40}")
    time.sleep(1.0)   # let a few ticks run the pose
    st = get_json("/tick_state")
    pose_cells = cell_summary(st)
    pmax = max(abs(c["P"]) for c in pose_cells)
    print(f"pose knee_L 40: {pose_resp[:20]} pmax={pmax:.1f} Pa")
    print("  ", json.dumps(pose_cells))
    post_raw("/tick_pose", "{\"joint\":\"knee_L\",\"deg\":0}")
    out_path.write_text("\n".join(json.dumps(r) for r in timeline),
                        encoding="utf-8")
    (out_path.parent / "pose_probe.json").write_text(json.dumps(
        {"pose_resp": pose_resp, "pmax": pmax, "cells": pose_cells}, indent=1))
    final = get_json("/tick_state")
    (out_path.parent / "bisect_final_state.json").write_text(
        json.dumps(final, indent=1))
    print("FINAL n_cells:", final["n_cells"])
    return proc


def mode_restore(out_path):
    run_dir = SCRATCH / "run_restore"
    kill_by_port_dir(run_dir)
    if run_dir.exists():
        shutil.rmtree(run_dir)
    (run_dir / "session_snapshot").mkdir(parents=True)
    for ep in ENDPOINTS:
        shutil.copy2(LIVE_SNAP / f"{ep}.blob", run_dir / "session_snapshot")
    shutil.copy2(LIVE_SNAP / "tick_seal_history.log",
                 run_dir / "session_snapshot")
    proc, log_path = boot(run_dir)
    st = wait_up(proc, log_path)
    # boot restore runs 1.5 s after the loop is alive; wait for it to land
    deadline = time.time() + 60
    while time.time() < deadline:
        st = get_json("/tick_state")
        if st["sealed"] and st["n_cells"] >= 4:
            break
        time.sleep(1.0)
    log = log_path.read_text(errors="replace")
    restore_line = [l for l in log.splitlines() if "boot restore" in l]
    print("restore log:", restore_line)
    print("n_cells:", st["n_cells"], "sealed:", st["sealed"],
          "refusal:", st.get("seal_refusal", ""))
    for c in cell_summary(st):
        print(" ", json.dumps(c))
    out_path.write_text(json.dumps(
        {"restore": restore_line, "state": st}, indent=1), encoding="utf-8")
    return proc


def kill_by_port_dir(run_dir):
    # best effort: a leftover engine from a previous attempt holds the port
    try:
        out = subprocess.run(["netstat", "-ano"], capture_output=True,
                             text=True).stdout
        for line in out.splitlines():
            if f":{PORT}" in line and "LISTENING" in line:
                pid = line.split()[-1]
                subprocess.run(["taskkill", "/F", "/T", "/PID", pid],
                               capture_output=True)
                time.sleep(1.0)
    except Exception:
        pass


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "bisect"
    out = SCRATCH / "evidence"
    out.mkdir(exist_ok=True)
    if mode == "bisect":
        p = mode_bisect(out / "bisect_timeline.jsonl")
    else:
        p = mode_restore(out / "restore_run.json")
    kill(p)
    print("done, engine killed")
