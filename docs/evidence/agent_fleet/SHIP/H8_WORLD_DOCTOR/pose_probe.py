#!/usr/bin/env python
"""H8 pose probe on the GUARDED scratch build: seal the 4 clean cells, pose
the left knee 40 deg (joint_index 15), hold, and record every cell's P.
The falsifier's live-poison arm: without the guard the same pose held
cell 4 at 1.6228 GPa; with the guard no cell may exceed the skin yield.
"""
import json
import sys
import time

sys.path.insert(0, r"E:\ChimeraWork\slot-01\.h8_scratch")
from repro import (BASE, ENDPOINTS, EXE, LIVE_SNAP, SCRATCH, boot, cell_summary,
                   get_json, kill, kill_by_port_dir, post_raw, wait_up)
from pathlib import Path


def main():
    out = SCRATCH / "evidence"
    run_dir = SCRATCH / "run_pose"
    kill_by_port_dir(run_dir)
    if run_dir.exists():
        import shutil
        shutil.rmtree(run_dir)
    proc, log_path = boot(run_dir)
    try:
        st = wait_up(proc, log_path)
        for ep in ENDPOINTS:
            print(ep, post_raw(f"/{ep}", (LIVE_SNAP / f"{ep}.blob").read_bytes())[:14])
        for body in ('{"y":3.415}', '{"y":1.903,"cell":0}',
                     '{"y":0.338,"cell":0}'):
            print("seal", post_raw("/tick_seal", body)[:14])
        st0 = get_json("/tick_state")
        print("rest :", json.dumps(cell_summary(st0)))
        rows = {"rest": cell_summary(st0), "posed": None, "pressed": None}
        print("pose ", post_raw("/tick_pose", '{"joint_index":15,"deg":40}')[:14])
        # hold the pose while ticks run, sampling P a few times
        samples = []
        for _ in range(6):
            time.sleep(0.5)
            samples.append(cell_summary(get_json("/tick_state")))
        rows["posed"] = samples[-1]
        pmax = max(abs(c["P"]) for s in samples for c in s)
        print("posed pmax over 3 s:", pmax)
        # and a standing press: 20 kN on the knee pin (the gentle-hand class)
        print("press", post_raw("/tick_intent_joint",
                                '{"joint_index":15,"force_n":20000}')[:14])
        time.sleep(2.0)
        rows["pressed"] = cell_summary(get_json("/tick_state"))
        print("pressed:", json.dumps(rows["pressed"]))
        pmax_all = max(max(abs(c["P"]) for c in rows[k] or []) for k in rows)
        rows["pmax"] = pmax_all
        out.joinpath("pose_probe_guarded.json").write_text(json.dumps(rows, indent=1))
        print("GUARD POSE PROBE pmax:", pmax_all, "Pa (skin yield 15 MPa)")
        return 0 if pmax_all < 15e6 else 1
    finally:
        kill(proc)


if __name__ == "__main__":
    sys.exit(main())
