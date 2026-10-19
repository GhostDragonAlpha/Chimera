"""WC-INTERACT SMOKE -- player-directed construction through REAL Win32 input.

Drives the NEWLY BUILT chimera_engine.exe window with PostMessageW mouse and
keyboard events (no /tick_b2_place anywhere; the only transactions fired are
the engine's own construction-mode key handlers) and asserts, after each
input, the interactive state route GET /tick_b2_interactive:

    click a part  -> selected == that part id        (pick + highlight)
    Tab           -> mode == "place_1"               (kit cycle)
    click a part  -> anchor set                      (ghost anchor)
    Enter         -> /tick_b2_parts count +1         (real b2_place commit)
    Esc           -> mode off, count unchanged       (cancel, nothing changed)
    click, X      -> count -1                        (b2_remove_part)

Evidence: this script + results JSON + /glass PNGs land in this directory.

Run:  python .tmp/wc_interact_smoke/wc_interact_smoke.py
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EXE = REPO / ".tmp" / "body-engine" / "Release" / "chimera_engine.exe"
OUT = HERE

sys.path.insert(0, str(REPO / "tools" / "construction_packet"))
import b2_scene_gen  # noqa: E402

PORT = 8830
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
MK_LBUTTON = 1
VK_TAB, VK_RETURN, VK_ESCAPE = 0x09, 0x0D, 0x1B
VK_X = 0x58

user32 = ctypes.windll.user32

results: dict = {"steps": [], "shots": {}, "asserts": []}


def assert_(name: str, cond: bool, detail: str = "") -> None:
    results["asserts"].append({"name": name, "ok": bool(cond), "detail": detail})
    print(("PASS  " if cond else "FAIL  ") + name + ("  " + detail if detail else ""))
    if not cond:
        raise AssertionError(name)


class Http:
    def __init__(self, port: int):
        self.base = f"http://127.0.0.1:{port}"

    def get(self, path: str, timeout=15):
        with urllib.request.urlopen(self.base + path, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def raw(self, path: str, timeout=25) -> bytes:
        with urllib.request.urlopen(self.base + path, timeout=timeout) as r:
            return r.read()

    def post(self, path: str, doc: dict, timeout=15):
        req = urllib.request.Request(self.base + path,
                                     data=json.dumps(doc).encode(),
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode())


def find_window(pid: int):
    """The game window by class name, verified against the engine pid."""
    hwnd = user32.FindWindowA(b"ChimeraEngine", None)
    assert hwnd, "game window (class ChimeraEngine) not found"
    buf = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(buf))
    assert buf.value == pid, f"window pid {buf.value} != engine pid {pid}"
    return hwnd


def client_size(hwnd) -> tuple[int, int]:
    rc = wt.RECT()
    assert user32.GetClientRect(hwnd, ctypes.byref(rc))
    return rc.right, rc.bottom


def post_click(hwnd, mx: int, my: int) -> None:
    lp = (my & 0xFFFF) << 16 | (mx & 0xFFFF)
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)


def post_key(hwnd, vk: int) -> None:
    # lparam 0: bit 30 (previous key state) clear -> the engine's edge
    # trigger sees a fresh press, no autorepeat.
    user32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, WM_KEYUP, vk, 0)


def shot(eng: Http, name: str) -> None:
    png = eng.raw("/glass")
    out = OUT / f"{name}.png"
    out.write_bytes(png)
    results["shots"][name] = {
        "file": out.name,
        "sha256": hashlib.sha256(png).hexdigest(),
        "bytes": len(png),
    }
    print(f"shot  {name}: {len(png)} bytes")
    time.sleep(0.3)


def hit_pixel(eng: Http, part_id: str, w: int, h: int):
    """A client pixel whose camera ray hits part_id, nearest the screen
    centre (panels are not transparent to input, so centre-most is safest).
    Uses POST /tick_b2_pick -- the SAME camera_ray + B2Scene::pick the
    window's click handler runs."""
    best = None
    best_d = 1e30
    for iy in range(20, 80, 2):
        for ix in range(20, 80, 2):
            px, py = ix / 100.0, iy / 100.0
            r = eng.post("/tick_b2_pick", {"px": px, "py": py})
            if r.get("ok") and r.get("id") == part_id:
                mx, my = px * w, py * h
                d = (mx - w / 2) ** 2 + (my - h / 2) ** 2
                if d < best_d:
                    best_d, best = d, (int(round(mx)), int(round(my)))
    return best


def istate(eng: Http) -> dict:
    return eng.get("/tick_b2_interactive")


def nparts(eng: Http) -> int:
    return len(eng.get("/tick_b2_parts")["parts"])


def main() -> int:
    results["exe_sha256"] = hashlib.sha256(EXE.read_bytes()).hexdigest()
    results["exe"] = str(EXE)

    # ── boot (the workshop-driver layout: exe + shaders beside it, native cwd,
    # board path ABSOLUTE -- the engine resolves argv[2] against ITS cwd) ──
    native = OUT / "native"
    if native.exists():
        shutil.rmtree(native)
    native.mkdir()
    shutil.copy2(EXE, native / EXE.name)
    shutil.copytree(EXE.parent / "shaders", native / "shaders",
                    dirs_exist_ok=True)
    with socket.socket() as s:
        assert s.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} busy"
    board = (OUT / "studio_board_smoke.json").resolve()
    argv = [str(native / EXE.name), str(PORT), str(board),
            "1600", "900", "--no-restore"]
    proc = subprocess.Popen(argv, cwd=native,
                            stdout=(native / "stdout.log").open("wb"),
                            stderr=(native / "stderr.log").open("wb"))
    results["pid"] = proc.pid
    eng = Http(PORT)
    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                eng.get("/tick_state")
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("engine did not answer /tick_state within 30 s")
        time.sleep(1.0)
        hwnd = find_window(proc.pid)
        w, h = client_size(hwnd)
        st = eng.get("/studio")
        w, h = int(st["w"]), int(st["h"])     # the client size the engine sees
        results["client"] = [w, h]
        print(f"window hwnd=0x{hwnd:x} client={w}x{h}")

        # ── scene: two granite/steel blocks on the ground, admitted then
        # PAUSED (the analytic-rest discipline the drivers use) ──
        a = b2_scene_gen.box_document("block_a", -0.30, 0.00, 0.00, 0.15,
                                      -0.15, 0.15, 2700, 0.5)
        b = b2_scene_gen.box_document("block_b", 0.20, 0.50, 0.00, 0.10,
                                      -0.10, 0.10, 7850, 0.4)
        r = eng.post("/tick_b2_admit",
                     {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
                      "parts": [a, b], "reason": "wc-interact smoke scene"})
        assert_("admit ok", r.get("ok") is True, str(r))
        assert_(("pause ok"), eng.post("/tick_b2_pause", {"on": True}).get("ok") is True)
        n0 = nparts(eng)
        assert_("scene has 2 parts", n0 == 2, f"n={n0}")
        time.sleep(0.5)

        # ── enable interactive mode ──
        r = eng.post("/tick_b2_interactive", {"on": True})
        assert_("interactive arm ok", r.get("ok") is True, str(r))
        s = istate(eng)
        assert_("interactive:true, mode off",
                s["interactive"] is True and s["mode"] == "off"
                and s["selected"] is None and s["anchor"] is None, json.dumps(s))

        # ── STEP 1: click block_a -> selected == block_a ──
        pix = hit_pixel(eng, "block_a", w, h)
        assert pix, "no /tick_b2_pick pixel for block_a"
        print(f"click block_a at {pix}")
        post_click(hwnd, *pix)
        time.sleep(0.4)
        s = istate(eng)
        assert_("select block_a", s["selected"] == "block_a", json.dumps(s))
        shot(eng, "1-selected-highlight")

        # ── STEP 2: Tab -> place mode 1 ──
        post_key(hwnd, VK_TAB)
        time.sleep(0.4)
        s = istate(eng)
        assert_("mode place_1", s["mode"] == "place_1", json.dumps(s))

        # ── STEP 3: click block_b -> anchor set (ghost preview) ──
        pix_b = hit_pixel(eng, "block_b", w, h)
        assert pix_b, "no /tick_b2_pick pixel for block_b"
        print(f"click block_b at {pix_b}")
        post_click(hwnd, *pix_b)
        time.sleep(0.4)
        s = istate(eng)
        assert_("anchor set on block_b pick",
                s["anchor"] is not None and s["selected"] == "block_b",
                json.dumps(s))
        shot(eng, "2-ghost-preview")

        # ── STEP 4: Enter -> real b2_place transaction ──
        n1 = nparts(eng)
        post_key(hwnd, VK_RETURN)
        time.sleep(0.6)
        n2 = nparts(eng)
        s = istate(eng)
        ids = [p["id"] for p in eng.get("/tick_b2_parts")["parts"]]
        assert_("part count +1", n2 == n1 + 1, f"{n1} -> {n2}")
        assert_("placed part exists + selected",
                s["selected"] == "pier_0" and "pier_0" in ids, json.dumps(s))
        shot(eng, "3-placed")

        # ── STEP 5: Esc -> cancel; nothing changes ──
        post_key(hwnd, VK_ESCAPE)
        time.sleep(0.4)
        s = istate(eng)
        n3 = nparts(eng)
        assert_("esc: mode off, selection cleared, count unchanged",
                s["mode"] == "off" and s["selected"] is None and n3 == n2,
                json.dumps(s) + f" n={n3}")

        # ── STEP 6: re-select block_a, X -> removed ──
        pix = hit_pixel(eng, "block_a", w, h)
        assert pix, "no /tick_b2_pick pixel for block_a (second pass)"
        post_click(hwnd, *pix)
        time.sleep(0.4)
        s = istate(eng)
        assert_("re-select block_a", s["selected"] == "block_a", json.dumps(s))
        post_key(hwnd, VK_X)
        time.sleep(0.6)
        n4 = nparts(eng)
        s = istate(eng)
        ids = [p["id"] for p in eng.get("/tick_b2_parts")["parts"]]
        assert_("X removed block_a", n4 == n3 - 1 and "block_a" not in ids
                and s["selected"] is None, json.dumps(s) + f" n={n4}")
        shot(eng, "4-removed")

        # ── STEP 7: interactive OFF -> the shipped input paths ──
        eng.post("/tick_b2_interactive", {"on": False})
        time.sleep(0.2)
        s = istate(eng)
        assert_("disable resets state",
                s["interactive"] is False and s["mode"] == "off"
                and s["selected"] is None, json.dumps(s))
        post_click(hwnd, *pix)
        time.sleep(0.4)
        s = istate(eng)
        assert_("click with mode OFF changes nothing",
                s["selected"] is None and s["mode"] == "off", json.dumps(s))

        results["verdict"] = "PASS"
    finally:
        (OUT / "results.json").write_text(json.dumps(results, indent=2),
                                          encoding="utf-8", newline="\n")
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("VERDICT PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
