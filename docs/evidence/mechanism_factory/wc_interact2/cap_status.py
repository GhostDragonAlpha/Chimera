"""WC-INTERACT-2 status-line capture: the Studio STATUS panel's build line.

Boots the rebuilt exe, grabs /glass disarmed (expect "build: off"), arms
interactive mode, hovers a part with a real WM_MOUSEMOVE (NO click), waits
past the 1 Hz STATUS refresh, grabs again (expect "build: place off | sel -
| hov block_b"). Pixels are evidence; the state route is the assertion.

Run AFTER the regression suite is finished (one engine at a time).
"""
from __future__ import annotations
import ctypes, ctypes.wintypes as wt, hashlib, json, shutil, socket
import subprocess, sys, time, urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EXE = REPO / ".tmp" / "body-engine" / "Release" / "chimera_engine.exe"
PORT = 8840
WM_MOUSEMOVE = 0x0200
user32 = ctypes.windll.user32
sys.path.insert(0, str(REPO / "tools" / "construction_packet"))
import b2_scene_gen  # noqa: E402

class Http:
    def __init__(self, port): self.base = f"http://127.0.0.1:{port}"
    def get(self, p, t=15):
        with urllib.request.urlopen(self.base + p, timeout=t) as r:
            return json.loads(r.read().decode())
    def raw(self, p, t=25):
        with urllib.request.urlopen(self.base + p, timeout=t) as r:
            return r.read()
    def post(self, p, doc, t=15):
        req = urllib.request.Request(self.base + p,
                                     data=json.dumps(doc).encode(), method="POST")
        with urllib.request.urlopen(req, timeout=t) as r:
            return json.loads(r.read().decode())

def main():
    native = HERE / "native"
    if native.exists(): shutil.rmtree(native)
    native.mkdir()
    shutil.copy2(EXE, native / EXE.name)
    shutil.copytree(EXE.parent / "shaders", native / "shaders", dirs_exist_ok=True)
    with socket.socket() as s:
        assert s.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} busy"
    board = (HERE / "board.json").resolve()
    board.write_text('{"schema":"chimera.studio_board.v1","title":"status cap",'
                     '"workspaces":[]}', encoding="utf-8")
    proc = subprocess.Popen([str(native / EXE.name), str(PORT), str(board),
                             "1600", "900", "--no-restore"], cwd=native,
                            stdout=(native / "stdout.log").open("wb"),
                            stderr=(native / "stderr.log").open("wb"))
    eng = Http(PORT)
    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            try: eng.get("/tick_state"); break
            except Exception: time.sleep(0.25)
        time.sleep(1.5)
        a = b2_scene_gen.box_document("block_a", -0.30, 0.00, 0.00, 0.15,
                                      -0.15, 0.15, 2700, 0.5)
        b = b2_scene_gen.box_document("block_b", 0.20, 0.50, 0.00, 0.10,
                                      -0.10, 0.10, 7850, 0.4)
        eng.post("/tick_b2_admit", {"schema": "chimera.b2_scene.v1",
                                    "gravity_m_s2": 9.81, "parts": [a, b],
                                    "reason": "status cap"})
        eng.post("/tick_b2_pause", {"on": True})
        time.sleep(1.5)
        (HERE / "1-status-off.png").write_bytes(eng.raw("/glass"))
        print("captured 1-status-off.png (expect 'build: off')")
        eng.post("/tick_b2_interactive", {"on": True})
        # hover block_b: centre-most pixel whose ray hits it (same pick the
        # window's handler runs)
        st = eng.get("/studio"); w, h = int(st["w"]), int(st["h"])
        best, best_d = None, 1e30
        for iy in range(20, 80, 2):
            for ix in range(20, 80, 2):
                px, py = ix / 100.0, iy / 100.0
                r = eng.post("/tick_b2_pick", {"px": px, "py": py})
                if r.get("ok") and r.get("id") == "block_b":
                    mx, my = px * w, py * h
                    d = (mx - w / 2) ** 2 + (my - h / 2) ** 2
                    if d < best_d: best_d, best = d, (int(round(mx)), int(round(my)))
        assert best, "no pixel hits block_b"
        hwnd = user32.FindWindowA(b"ChimeraEngine", None)
        pid = wt.DWORD(); user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        assert pid.value == proc.pid
        lx, ly = best
        user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, (ly << 16) | (lx & 0xFFFF))
        time.sleep(2.0)   # > 1 Hz STATUS refresh
        (HERE / "2-status-armed-hover.png").write_bytes(eng.raw("/glass"))
        s = eng.get("/tick_b2_interactive")
        print("state:", json.dumps(s))
        assert s["interactive"] and s["hovered"] == "block_b", s
        print("captured 2-status-armed-hover.png (expect hov block_b)")
    finally:
        proc.terminate(); proc.wait(timeout=15)

if __name__ == "__main__":
    main()
