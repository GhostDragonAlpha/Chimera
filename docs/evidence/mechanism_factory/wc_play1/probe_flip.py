"""WC-PLAY-1 flip DISCRIMINATOR v2: FORCE run8's off-centre anchor.

v1 reproduced the arc's call sequence but the pick coverage was rich and the
aim landed centred -- both beats settled perfectly (up_y 1, speed 0.0,
pp_ct 4). run8's failure needs the anchor at z ~ -0.036 (16 mm bottom-face
overhang of the pad's -z edge). This probe hovers the top-face pixel whose
world z is nearest -0.036, commits, and traces the pillar's FULL pose
(com + quat + up_y + speed + pen + pp contact telemetry) for 120 s, then a
centred control beat for 30 s.

Decides between:
  (A) the pillar TIPPED (up_y far from 1) and leans on the pad edge/ground,
  (B) it stayed UPRIGHT wedged deeper than the pair equilibrium (the pp
      entry-face rule flipped to the far face) and creeps forever.
"""
from __future__ import annotations
import json
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
import walk_player_arc as W  # noqa: E402

EXE = W.EXE
SCENE = W.SCENE
NATIVE = HERE / "probe_flip_native"
BOARD = (HERE / "probe_flip_board.json").resolve()
PORT = 8847
OUT = HERE / "probe_flip_trace.json"
RUN8_ANCHOR_Z = -0.03616


def trace_part(st: dict, pid_prefix: str) -> dict:
    out = {}
    for p in st["parts"]:
        if p["id"] == pid_prefix or p["id"].startswith(pid_prefix):
            q = p["pose_q_wxyz"]
            out[p["id"]] = {
                "com": [round(v, 6) for v in p["com_m"]],
                "quat": [round(v, 5) for v in q],
                "up_y": round(1 - 2 * (q[1] ** 2 + q[3] ** 2), 5),
                "speed": round(p["speed_m_s"], 7),
                "pen_step": round(p["pen_step_m"], 6),
                "pen_run": round(p["pen_run_m"], 6),
                "pp_n": round(p.get("contact_pp_n", -1), 3),
                "pp_ct": p.get("contacts_pp_active", -1),
            }
    return out


def run_beat(eng, hwnd, w, h, label, want_z, dur):
    """hover the pad's top-face pixel nearest want_z, commit, trace dur s"""
    slab_hits = W.scan_part(eng, hwnd, w, h, "hazard_pad", attempts=3,
                            step=0.02)
    slab_fine = []
    for h0 in sorted(slab_hits, key=lambda k: (k["mx"] - w / 2) ** 2
                     + (k["my"] - h / 2) ** 2)[:6]:
        slab_fine += W.refine(eng, w, h, h0)
    slab_top = W.top_face_hits(slab_fine + slab_hits, "hazard_pad")
    print(label, "top hits", len(slab_top),
          "z", round(min(x["hit"][2] for x in slab_top), 4),
          "..", round(max(x["hit"][2] for x in slab_top), 4))

    def off(k):
        return (k["hit"][2] - want_z) ** 2

    pix = min(slab_top, key=off)
    print(label, "aim ->", json.dumps(pix["hit"]))
    pix, s = W.hover_and_check(eng, hwnd, w, h, [pix], "hazard_pad", label)
    print(label, "anchor:", json.dumps(s["anchor"]))
    W.post_key(hwnd, W.VK_RETURN)
    time.sleep(0.8)
    pid = W.istate(eng)["selected"]
    print(label, "pillar placed:", pid)
    rows = []
    t0 = time.time()
    while time.time() - t0 < dur:
        got = time.time() - t0
        stx = eng.get("/tick_b2_state")
        rows.append({"t": round(got, 2),
                     "parts": trace_part(stx, "pillar")
                              | trace_part(stx, "hazard_pad")})
        dt = 0.15 if got < 8.0 else (0.5 if got < 40.0 else 5.0)
        time.sleep(dt)
    print(label, "final:", json.dumps(rows[-1]["parts"]))
    # creep rate over the last 20 s
    if len(rows) > 3:
        a, b = rows[0]["parts"], rows[-1]["parts"]
        for k in a:
            if k in b:
                dr = max(abs(x - y) for x, y in zip(a[k]["com"], b[k]["com"]))
                print(label, k, "max |dcom| first->last:",
                      round(dr * 1000, 3), "mm")
    return {"label": label, "anchor": s["anchor"], "pillar": pid,
            "rows": rows}


def main() -> int:
    if NATIVE.exists():
        shutil.rmtree(NATIVE)
    NATIVE.mkdir()
    shutil.copy2(EXE, NATIVE / EXE.name)
    shutil.copytree(EXE.parent / "shaders", NATIVE / "shaders",
                    dirs_exist_ok=True)
    with socket.socket() as s:
        assert s.connect_ex(("127.0.0.1", PORT)) != 0, "port busy"
    argv = [str(NATIVE / EXE.name), str(PORT), str(BOARD), "1600", "900",
            "--no-restore", "--interactive", "--scene", str(SCENE.resolve())]
    proc = subprocess.Popen(argv, cwd=NATIVE,
                            stdout=(NATIVE / "stdout.log").open("wb"),
                            stderr=(NATIVE / "stderr.log").open("wb"))
    eng = W.Http(PORT)
    trace = []
    try:
        t0 = time.time()
        while time.time() - t0 < 30:
            try:
                eng.get("/tick_state")
                break
            except Exception:
                time.sleep(0.25)
        time.sleep(1.0)
        hwnd = W.find_window(proc.pid)
        st = eng.get("/studio")
        w, h = int(st["w"]), int(st["h"])
        W.wait_until(lambda: "no camera yet" not in
                     json.dumps(eng.post("/tick_b2_pick", {"px": 0.5, "py": 0.5})),
                     30.0, "pick camera ready")
        slab0 = W.wait_supports_at_rest(eng, timeout=240.0)
        print("rest gate open:",
              json.dumps({p["id"]: p["com_m"] for p in slab0["parts"]}))
        W.zoom_in(hwnd)
        W.tab_to_mode(eng, hwnd, "place_2")

        trace.append(run_beat(eng, hwnd, w, h, "offcentre", RUN8_ANCHOR_Z,
                              120.0))

        # control: remove the wedged pillar, wait for the pad to drain, commit
        # centred, trace 30 s
        W.post_key(hwnd, W.VK_X)
        time.sleep(2.0)
        trace.append(run_beat(eng, hwnd, w, h, "centred_control", 0.0, 30.0))
        OUT.write_text(json.dumps(trace, indent=1), encoding="utf-8")
    finally:
        OUT.write_text(json.dumps(trace, indent=1), encoding="utf-8")
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
    print("PROBE DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
