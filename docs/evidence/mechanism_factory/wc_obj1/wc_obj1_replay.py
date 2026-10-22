"""WC-OBJ-1 part A receipts: tilted-corner replay + pause replay.

Runs against a LIVE engine (chimera_engine.exe <port> --hidden --interactive
--scene <scene>.json). This script POSTs the scene admits/placements and the
weld (the ONLY mutations), runs the revised board feed as a subprocess, and
records evidence into this receipt directory:

  tilt : settles the pad, then admits a crate tilted ~8 deg about z with its
         lowest corners ON the live pad top, WELDed to the pad (the board's
         own "F weld" tool; a free tilted box rights itself and the soft
         pair contact sinks ~5.8 mm, so only a weld holds the tilt), waits
         for settle, dumps the live /tick_b2_state (with the old-rule
         comparison computed from the same snapshot) and the board file the
         feed wrote.
  pause: builds a HELD scene (pillar pre-sunk onto the pad, crate pre-sunk
         onto the pillar top -- the engine's own pair-equilibrium spawn
         law), runs the feed across >=2 poll intervals on each side of
         POST /tick_b2_pause {"on": true|false}, recording steps/paused/
         chip per poll.

Usage:
  python wc_obj1_replay.py tilt  --port 8845 --tilt-deg 8
  python wc_obj1_replay.py pause --port 8845 --interval 0.7
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
FEED = REPO / "tools" / "construction_packet" / "workshop_board_feed.py"
SCENE1 = REPO / "tools" / "construction_packet" / "workshop1_scene.json"

# kit constants (engine membrane_tick.cpp kInteractiveKit + rung law:
# k_total = m*g/0.01, c_total = 2*0.7*sqrt(k_total*m), 4 ground sites)
G = 9.81
REST_SINK = 0.01
ZETA = 0.7


def rung(mass: float) -> dict:
    k_total = mass * G / REST_SINK
    c_total = 2.0 * ZETA * math.sqrt(k_total * mass)
    return {"k_n_per_m": k_total / 4.0, "c_n_s_per_m": c_total / 4.0}


def box_part(pid: str, hx: float, hy: float, hz: float, rho: float, mu: float,
             com_world, q=(1.0, 0.0, 0.0, 0.0)) -> dict:
    mass = rho * (2 * hx) * (2 * hy) * (2 * hz)
    ixx = mass / 12.0 * ((2 * hy) ** 2 + (2 * hz) ** 2)
    iyy = mass / 12.0 * ((2 * hx) ** 2 + (2 * hz) ** 2)
    izz = mass / 12.0 * ((2 * hx) ** 2 + (2 * hy) ** 2)
    # b2i_kit_doc_ vertex order (x fastest, then y, then z) so the proven
    # CCW-outward kBoxTris winding applies; any other order flips face
    # normals and bodies fall through (the WC-PLAY-1 winding bug).
    verts = [[-hx, -hy, -hz], [hx, -hy, -hz], [hx, hy, -hz], [-hx, hy, -hz],
             [-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz]]
    # b2i_kit_doc_ vertex order (proven CCW-outward winding, kBoxTris)
    order = [0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7,
             0, 1, 5, 0, 5, 4, 2, 3, 7, 2, 7, 6,
             0, 4, 7, 0, 7, 3, 1, 2, 6, 1, 6, 5]
    return {"id": pid, "mass_kg": mass,
            "com_local_m": [0.0, 0.0, 0.0],
            "inertia_com_local_kg_m2": [ixx, 0, 0, 0, iyy, 0, 0, 0, izz],
            "vertices_local_m": [v for xyz in verts for v in xyz],
            "boundary_triangles": order,
            "pose_c_m": list(com_world), "pose_q_wxyz": list(q),
            "ground": {"k_n_per_m": rung(mass)["k_n_per_m"],
                       "c_n_s_per_m": rung(mass)["c_n_s_per_m"]},
            "mu": mu}


def get(port: int, path: str, timeout: float = 5.0) -> dict:
    last = None
    for _ in range(6):
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:                     # engine still booting
            last = e
            time.sleep(1.0)
    raise RuntimeError(f"GET {path} failed: {last}")


def post(port: int, path: str, doc: dict, timeout: float = 5.0) -> dict:
    last = None
    for _ in range(6):
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}",
                data=json.dumps(doc).encode(), method="POST",
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last = e
            time.sleep(1.0)
    raise RuntimeError(f"POST {path} failed: {last}")


def start_feed(port: int, board: Path) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, str(FEED), "--port", str(port),
         "--board", str(board)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def old_rule(st: dict) -> dict:
    """The PREVIOUS board-feed predicate, computed from the same live
    snapshot: axis-aligned bottom (COM y - 0.025), region, tilt gate."""
    crate = None
    best = None
    for i, p in enumerate(st.get("parts", [])):
        if p.get("id", "").startswith("crate"):
            best = p                                  # last list position
    crate = best
    slab = next((p for p in st.get("parts", [])
                 if p.get("id") == "hazard_pad"), None)
    slab_top = slab["com_m"][1] + 0.02
    com = crate["com_m"]
    q = crate.get("pose_q_wxyz", [1, 0, 0, 0])
    up_y = 1 - 2 * (q[1] * q[1] + q[3] * q[3])
    in_region = 0.54 <= com[0] <= 0.70 and -0.05 <= com[2] <= 0.05
    clear = com[1] - 0.025 - slab_top
    return {"rule": "OLD: bottom = COM y - 0.025 (upright approximation), "
                    "up_y >= 0.9848",
            "slab_top_m": slab_top,
            "old_bottom_clear_m": clear,
            "old_clear_mm": round(clear * 1000, 2),
            "in_region": in_region,
            "up_y": round(up_y, 5),
            "old_held": bool(in_region and clear >= 0.004 and up_y >= 0.9848)}


def new_rule(st: dict) -> dict:
    """The revised corner-rule predicate, same snapshot (mirrors the feed)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "wbf", str(FEED))
    wbf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wbf)
    slab = next((p for p in st.get("parts", [])
                 if p.get("id") == "hazard_pad"), None)
    slab_top = slab["com_m"][1] + 0.02
    v = wbf.verdict(st.get("parts", []), [0.54, 0.70, -0.05, 0.05], slab_top,
                    0.004, [0.05, 0.025, 0.025],
                    [0.48, 0.76, -0.08, 0.08])
    v["slab_top_m"] = slab_top
    v["min_clear_mm"] = (None if v["min_clear_m"] is None
                         else round(v["min_clear_m"] * 1000, 2))
    return v


def cmd_tilt(args) -> int:
    tilt = math.radians(args.tilt_deg)
    q = [math.cos(tilt / 2), 0.0, 0.0, math.sin(tilt / 2)]
    hx, hy, hz = 0.05, 0.025, 0.025

    # STAGE 1: settle the pad alone, measure the LIVE slab top.
    base = json.loads(SCENE1.read_text(encoding="utf-8"))
    warm = {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
            "parts": base["parts"],
            "reason": "WC-OBJ-1 receipt 1 stage 1: settle the pad to "
                      "measure the live slab top"}
    r = post(args.port, "/tick_b2_admit", warm)
    print("stage-1 admit:", json.dumps(r))
    L = None
    for i in range(6):
        time.sleep(0.5)
        st = get(args.port, "/tick_b2_state")
        L = next(p for p in st["parts"]
                 if p["id"] == "hazard_pad")["com_m"][1] + 0.02
    print(f"live slab top measured: {L:.5f} m")

    # STAGE 2: crate tilted ~7 deg about z, its two lowest bottom-face
    # corners exactly ON the live pad top, WELDED to the pad (the board's
    # own "F weld" player tool; a free tilted box rights itself and the
    # soft pair contact sinks ~5.8 mm, so only a weld holds the tilt).
    # rotation about z: corner world y-offset = x*sin + y*cos
    dy_low = -hx * math.sin(tilt) - hy * math.cos(tilt)      # lowest corners
    com = [0.62, L - dy_low, 0.0]
    crate = box_part("crate_1", hx, hy, hz, 7850.0, 0.4, com, q)
    doc = {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
           "parts": base["parts"] + [crate],
           "reason": "WC-OBJ-1 receipt 1: crate tilted "
                     f"{args.tilt_deg:.0f} deg about z, lowest corners on "
                     "the pad top, welded to the pad (old rule reads HELD)"}
    (HERE / "tilt_admit_doc.json").write_text(
        json.dumps(doc, indent=1), encoding="utf-8")

    r = post(args.port, "/tick_b2_admit", doc)
    print("stage-2 admit:", json.dumps(r))

    # weld: 4 anchor pairs at the crate's bottom-face corners (world)
    anchors = []
    for lx in (-hx, hx):
        for lz in (-hz, hz):
            c = (lx * math.cos(tilt) - (-hy) * math.sin(tilt),
                 lx * math.sin(tilt) + (-hy) * math.cos(tilt), lz)
            w = (com[0] + c[0], com[1] + c[1], com[2] + c[2])
            anchors.append([w[0], w[1], w[2], w[0], w[1], w[2]])
    weld = {"a": "crate_1", "b": "hazard_pad", "k": 400000.0,
            "c_damp": 450.0, "anchors_world": anchors}
    (HERE / "tilt_weld_doc.json").write_text(
        json.dumps(weld, indent=1), encoding="utf-8")
    print("weld:", json.dumps(post(args.port, "/tick_b2_weld", weld)))

    board = HERE / "tilt_board.json"
    feed = start_feed(args.port, board)
    try:
        snap = None
        for i in range(12):                     # ~6 s settle
            time.sleep(0.5)
            st = get(args.port, "/tick_b2_state")
            crate_p = next((p for p in st["parts"]
                            if p["id"].startswith("crate")), None)
            print(f"poll {i}: steps {st.get('steps')} paused {st.get('paused')} "
                  f"com_y {crate_p['com_m'][1]:.5f} q "
                  f"{[round(x, 4) for x in crate_p.get('pose_q_wxyz', [])]}")
            if i >= 6:
                snap = st                        # keep a settled snapshot
        assert snap is not None
        time.sleep(1.0)                          # let the feed write once more
        snap["old_rule_comparison"] = old_rule(snap)
        snap["new_rule_check"] = new_rule(snap)
        snap["weld_document"] = weld
        (HERE / "tilt_state.json").write_text(
            json.dumps(snap, indent=1), encoding="utf-8")
        old = snap["old_rule_comparison"]
        print("OLD rule:", json.dumps(old))
        print("NEW rule:", json.dumps(snap["new_rule_check"]))
        cell = json.loads(board.read_text(encoding="utf-8"))
        print("board cell:", cell["stages"][0]["cell"])
        print("board status:", cell["stages"][0]["status"])
    finally:
        feed.terminate()
        try:
            feed.wait(timeout=5)
        except subprocess.TimeoutExpired:
            feed.kill()
    return 0


def cmd_pause(args) -> int:
    # HELD scene built the way the engine's own interactive kit spawns parts:
    # settle the support, then place the next part PRE-SUNK to its pair
    # equilibrium (y0 = support_top - w_new/pair_kt, pair_kt = (kt_new +
    # kt_support)/2, the workshop drivers' chain law) so it never free-falls
    # into the soft contact (a flush spawn overshoots and walks the stack).
    base = json.loads(SCENE1.read_text(encoding="utf-8"))
    pad = base["parts"][0]
    kt_pad = pad["mass_kg"] * G / REST_SINK          # 4-site total rung k

    def kt_part(hx, hy, hz, rho):
        return rho * (2 * hx) * (2 * hy) * (2 * hz) * G / REST_SINK

    def presunk(hx, hy, hz, rho, support_top, kt_support):
        mass = rho * (2 * hx) * (2 * hy) * (2 * hz)
        w = mass * G
        pair_kt = (kt_part(hx, hy, hz, rho) + kt_support) / 2.0
        # y0 (the part's BOTTOM face) = support_top - w/pair_kt; the part
        # com sits half a height above its bottom face.
        com_y = support_top - w / pair_kt + hy
        return com_y, w / pair_kt

    r = post(args.port, "/tick_b2_admit",
             {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
              "parts": base["parts"],
              "reason": "WC-OBJ-1 receipt 2 stage A: settle the pad"})
    print("stage-A admit:", json.dumps(r))
    time.sleep(2.0)
    st = get(args.port, "/tick_b2_state")
    L = next(p for p in st["parts"]
             if p["id"] == "hazard_pad")["com_m"][1] + 0.02
    print(f"live pad top: {L:.5f}")

    # stage B: pillar (0.12 x 0.10 x 0.12, rho 2700) pre-sunk on the pad
    com_y, sink = presunk(0.06, 0.05, 0.06, 2700.0, L, kt_pad)
    pillar = box_part("pillar_1", 0.06, 0.05, 0.06, 2700.0, 0.6,
                      [0.62, com_y, 0.0])
    kt_pillar = kt_part(0.06, 0.05, 0.06, 2700.0)
    r = post(args.port, "/tick_b2_place", pillar)
    print(f"place pillar (pre-sink {sink * 1000:.1f} mm):", json.dumps(r))
    time.sleep(2.0)
    st = get(args.port, "/tick_b2_state")
    T = next(p for p in st["parts"]
             if p["id"] == "pillar_1")["com_m"][1] + 0.05
    print(f"live pillar top: {T:.5f}")

    # stage C: crate pre-sunk on the pillar top
    com_y, sink = presunk(0.05, 0.025, 0.025, 7850.0, T, kt_pillar)
    crate = box_part("crate_1", 0.05, 0.025, 0.025, 7850.0, 0.4,
                     [0.62, com_y, 0.0])
    r = post(args.port, "/tick_b2_place", crate)
    print(f"place crate (pre-sink {sink * 1000:.1f} mm):", json.dumps(r))
    time.sleep(2.0)
    st = get(args.port, "/tick_b2_state")
    for p in st["parts"]:
        print("  part", p["id"], "com_y", round(p["com_m"][1], 5))
    (HERE / "pause_scene_receipt.json").write_text(
        json.dumps({"pad_top_m": L, "pillar_top_m": T,
                    "crate_com_y_authored": com_y, "state": st}, indent=1),
        encoding="utf-8")

    board = HERE / "pause_board.json"
    feed = start_feed(args.port, board)
    log = []
    try:
        def poll(label):
            time.sleep(args.interval)
            st = get(args.port, "/tick_b2_state")
            b = json.loads(board.read_text(encoding="utf-8")) \
                if board.exists() else {"stages": [{"cell": "(not written)",
                                                    "status": "?"}]}
            entry = {"label": label, "t": round(time.time(), 3),
                     "steps": st.get("steps"), "paused": st.get("paused"),
                     "cell": b["stages"][0]["cell"],
                     "status": b["stages"][0]["status"]}
            log.append(entry)
            print(f"[{label}] steps {entry['steps']} paused {entry['paused']} "
                  f"status {entry['status']}\n    {entry['cell']}")
            return st

        for i in range(3):                        # warm-up + pre-pause polls
            poll(f"pre-{i}")
        print("pause ->", json.dumps(post(args.port, "/tick_b2_pause",
                                          {"on": True})))
        for i in range(3):
            poll(f"paused-{i}")
        print("resume ->", json.dumps(post(args.port, "/tick_b2_pause",
                                           {"on": False})))
        for i in range(3):
            poll(f"resumed-{i}")
        (HERE / "pause_poll_log.json").write_text(
            json.dumps(log, indent=1), encoding="utf-8")
    finally:
        post(args.port, "/tick_b2_pause", {"on": False})
        feed.terminate()
        try:
            feed.wait(timeout=5)
        except subprocess.TimeoutExpired:
            feed.kill()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    t = sub.add_parser("tilt")
    t.add_argument("--port", type=int, required=True)
    t.add_argument("--tilt-deg", type=float, default=7.0)
    p = sub.add_parser("pause")
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--interval", type=float, default=0.7)
    args = ap.parse_args(argv)
    return cmd_tilt(args) if args.mode == "tilt" else cmd_pause(args)


if __name__ == "__main__":
    raise SystemExit(main())
