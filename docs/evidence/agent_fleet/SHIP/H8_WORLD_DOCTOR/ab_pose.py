#!/usr/bin/env python
"""H8 falsifier A/B: identical creature + identical 40-deg knee pose on the
NO-GUARD and the GUARDED scratch engine. Per arm: boot isolated cwd (G4
recipe), import the live blobs, run the 3 foundation seals (+ the same
51-line history), then sample /tick_state every 0.25 s for 4 s under the
pose. Records: cell table, which cell peaks, peak |P|, degenerate flags.
Usage: python ab_pose.py <exe> <port> <arm> <replay_full_history:0|1>
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
LIVE_SNAP = REPO / ".tmp" / "build_tick" / "Release" / "session_snapshot"
SCRATCH = REPO / ".h8_scratch"
ENDPOINTS = ["mesh_bin", "tick_joints", "tick_classify", "tick_vertbind"]


def get_json(base, path, timeout=5):
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def post_raw(base, path, body, timeout=120):
    req = urllib.request.Request(
        base + path, data=body if isinstance(body, bytes) else body.encode(),
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return f"HTTP{e.code}"


def cells(st):
    return [{k: c[k] for k in ("v0", "V", "P", "pieces", "ylo", "yhi")}
            | {"deg": c.get("degenerate")} for c in st.get("cells", [])]


def main():
    exe, port, arm, full = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3], \
        sys.argv[4] == "1"
    base = f"http://127.0.0.1:{port}"
    run_dir = SCRATCH / f"run_ab_{arm}"
    try:
        out = subprocess.run(["netstat", "-ano"], capture_output=True,
                             text=True).stdout
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                subprocess.run(["taskkill", "/F", "/T", "/PID",
                                line.split()[-1]], capture_output=True)
                time.sleep(1)
    except Exception:
        pass
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(exe.parent / "shaders", run_dir / "shaders")
    logf = open(run_dir / "engine.log", "ab")
    proc = subprocess.Popen([str(exe), str(port), "--hidden"],
                            cwd=str(run_dir), stdout=logf, stderr=logf,
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    try:
        deadline = time.time() + 120
        while time.time() < deadline:
            if proc.poll() is not None:
                print("engine died at boot"); return 2
            try:
                if get_json(base, "/tick_state", 2).get("sealed") is not True:
                    break
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
        for ep in ENDPOINTS:
            post_raw(base, f"/{ep}", (LIVE_SNAP / f"{ep}.blob").read_bytes())
        seals = ['{"y":3.415}', '{"y":1.903,"cell":0}', '{"y":0.338,"cell":0}']
        if full:
            seals = [l.strip() for l in
                     (LIVE_SNAP / "tick_seal_history.log").read_text().splitlines()
                     if l.strip()]
        for s in seals:
            r = post_raw(base, "/tick_seal", s)
            if '"ok":true' in r:
                print(f"seal OK : {s}")
            elif arm == "guarded" and full:
                pass    # 48 refusals: noise; the refusal name is in state
            else:
                print(f"seal ref: {s}")
        st = get_json(base, "/tick_state")
        pre = cells(st)
        print(f"[{arm}] pre-pose cells ({st['n_cells']}): "
              + json.dumps(pre))
        result = {"arm": arm, "pre": pre,
                  "seal_refusal": st.get("seal_refusal", "")}
        # THE POSE WINDOW: knee_L (pin 15) to 40 deg, sample 4 s at 4 Hz
        pr = post_raw(base, "/tick_pose", '{"joint_index":15,"deg":40}')
        result["pose_resp"] = pr
        best = None
        for _ in range(16):
            time.sleep(0.25)
            st = get_json(base, "/tick_state")
            cs = cells(st)
            pk = max(cs, key=lambda c: abs(c["P"]))
            if best is None or abs(pk["P"]) > abs(best["peak"]["P"]):
                best = {"peak": pk, "cells": cs, "t": len(result.get("samps", []))}
            result.setdefault("samps", []).append(
                [round(c["P"]) for c in cs])
        result["peak"] = best
        print(f"[{arm}] peak |P| cell during pose: "
              + json.dumps(best["peak"]))
        out = SCRATCH / "evidence" / f"ab_pose_{arm}.json"
        out.write_text(json.dumps(result, indent=1))
        print(f"[{arm}] wrote {out}")
        return 0
    finally:
        if proc.poll() is None:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True)
            proc.wait(timeout=20)
        time.sleep(1.0)


if __name__ == "__main__":
    sys.exit(main())
