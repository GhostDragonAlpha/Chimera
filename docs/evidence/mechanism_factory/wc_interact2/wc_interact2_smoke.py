"""WC-INTERACT-2 SMOKE -- hover-follow ghost + weld verb through REAL Win32 input.

Extends the published WC-INTERACT-1 smoke (copied, not edited): drives the
newly built chimera_engine.exe window with PostMessageW mouse and keyboard
events and asserts the interactive state route GET /tick_b2_interactive plus
the weld list on GET /tick_b2_state and the engine log (GET /log):

    WM_MOUSEMOVE over A (no button) -> hovered == A, anchor == A's surface
    WM_MOUSEMOVE over B (no button) -> hovered == B, anchor MOVED to B
                                       (hover-follow: no click anywhere)
    F with nothing selected         -> refusal logged, no weld added
    Tab, hover B                    -> ghost follows the cursor (screenshot)
    click A, hover B, F             -> weld block_a->block_b in /tick_b2_state
                                       (3 anchors, k 10000), selection kept
    hover A (== selected), F        -> "cannot weld to itself", weld unchanged
    Esc, X                          -> still work (X drops the welded part)
    interactive OFF                 -> hovered resets too

Evidence: this script + results JSON + /glass PNGs land in this directory.

Run:  python .tmp/wc_interact2_smoke/wc_interact2_smoke.py
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

PORT = 8833
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
WM_MOUSEMOVE = 0x0200
MK_LBUTTON = 1
VK_TAB, VK_RETURN, VK_ESCAPE = 0x09, 0x0D, 0x1B
VK_X, VK_F = 0x58, 0x46

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


def post_move(hwnd, mx: int, my: int) -> None:
    """A HOVER: WM_MOUSEMOVE with NO button bits in wParam -- no press, no
    capture, no click. The hover-follow proof rides on exactly this."""
    lp = (my & 0xFFFF) << 16 | (mx & 0xFFFF)
    user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)


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
    window's click AND hover handlers run."""
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
                    best_d, best = d, (int(round(mx)), int(round(my)),
                                       [float(v) for v in r["hit"]])
    return best


def istate(eng: Http) -> dict:
    return eng.get("/tick_b2_interactive")


def ref_hit(eng: Http, pix: tuple, w: int, h: int) -> list:
    """The pick hit for the EXACT pixel a hover/click will land on: the
    window computes u = mx/w, v = my/h (client fractions), so the reference
    must be the SAME ray, not the search scan's coarser pixel."""
    r = eng.post("/tick_b2_pick", {"px": pix[0] / w, "py": pix[1] / h})
    assert r.get("ok") and r.get("id"), f"reference pick missed: {r}"
    return [float(v) for v in r["hit"]]


def nparts(eng: Http) -> int:
    return len(eng.get("/tick_b2_parts")["parts"])


def welds(eng: Http) -> list:
    return eng.get("/tick_b2_state")["welds"]


def b2i_log_lines(eng: Http) -> list:
    return eng.get("/log")["lines"]


def near(a: list, b: list, eps: float = 1e-3) -> bool:
    return all(abs(x - y) <= eps for x, y in zip(a, b))


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
    clicks_posted = 0
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
                      "parts": [a, b], "reason": "wc-interact2 smoke scene"})
        assert_("admit ok", r.get("ok") is True, str(r))
        assert_(("pause ok"), eng.post("/tick_b2_pause", {"on": True}).get("ok") is True)
        n0 = nparts(eng)
        assert_("scene has 2 parts", n0 == 2, f"n={n0}")
        time.sleep(0.5)

        # ── enable interactive mode ──
        r = eng.post("/tick_b2_interactive", {"on": True})
        assert_("interactive arm ok", r.get("ok") is True, str(r))
        s = istate(eng)
        assert_("arm state: off/none/null incl. hovered",
                s["interactive"] is True and s["mode"] == "off"
                and s["selected"] is None and s["anchor"] is None
                and s["hovered"] is None, json.dumps(s))

        # ── STEP 1: HOVER block_a -- WM_MOUSEMOVE with NO button ──
        pix_a = hit_pixel(eng, "block_a", w, h)
        assert pix_a, "no /tick_b2_pick pixel for block_a"
        ref_a = ref_hit(eng, pix_a, w, h)
        print(f"hover block_a at {pix_a[:2]}")
        post_move(hwnd, pix_a[0], pix_a[1])
        time.sleep(0.4)
        s = istate(eng)
        assert_("hover A: hovered == block_a, NO selection, no click posted",
                s["hovered"] == "block_a" and s["selected"] is None
                and s["anchor"] is not None, json.dumps(s))
        assert_("hover A: anchor == the pick hit on A's surface",
                near(s["anchor"], ref_a), f"anchor={s['anchor']} hit={ref_a}")
        anchor_a = s["anchor"]

        # ── STEP 2: HOVER block_b -- the ghost anchor FOLLOWS the cursor ──
        pix_b = hit_pixel(eng, "block_b", w, h)
        assert pix_b, "no /tick_b2_pick pixel for block_b"
        ref_b = ref_hit(eng, pix_b, w, h)
        print(f"hover block_b at {pix_b[:2]}")
        post_move(hwnd, pix_b[0], pix_b[1])
        time.sleep(0.4)
        s = istate(eng)
        assert_("hover B: hovered == block_b, still no click posted",
                s["hovered"] == "block_b" and s["selected"] is None,
                json.dumps(s))
        assert_("hover B: anchor MOVED off A onto B's surface",
                s["anchor"] is not None and not near(s["anchor"], anchor_a)
                and near(s["anchor"], ref_b),
                f"anchor={s['anchor']} hit_b={ref_b}")
        assert_("parts and welds untouched by hover",
                nparts(eng) == 2 and len(welds(eng)) == 0)

        # ── STEP 3: F with NOTHING selected -> honest refusal ──
        post_key(hwnd, VK_F)
        time.sleep(0.4)
        lines = b2i_log_lines(eng)
        assert_("F no selection: refusal logged by name",
                any(e["kind"] == "b2i"
                    and "select a part first" in e["detail"] for e in lines),
                json.dumps(lines[-6:]))
        assert_("F no selection: no weld added, scene untouched",
                len(welds(eng)) == 0 and nparts(eng) == 2)

        # ── STEP 4: Tab arms the place mode; hover B -> the GHOST follows ──
        post_key(hwnd, VK_TAB)
        time.sleep(0.4)
        s = istate(eng)
        assert_("mode place_1", s["mode"] == "place_1", json.dumps(s))
        post_move(hwnd, pix_b[0], pix_b[1])
        time.sleep(0.4)
        s = istate(eng)
        assert_("ghost follows: mode armed + hovered B + anchor on B",
                s["mode"] == "place_1" and s["hovered"] == "block_b"
                and s["anchor"] is not None and near(s["anchor"], ref_b),
                json.dumps(s))
        shot(eng, "5-hover-ghost-over-b")

        # ── STEP 5: click A (selection AND anchor, the click path as shipped)
        # then hover B again -- selection white, hover carries the weld point ──
        post_click(hwnd, pix_a[0], pix_a[1])
        clicks_posted += 1
        time.sleep(0.4)
        s = istate(eng)
        assert_("click A selects it (click path unchanged)",
                s["selected"] == "block_a", json.dumps(s))
        post_move(hwnd, pix_b[0], pix_b[1])
        time.sleep(0.4)
        s = istate(eng)
        assert_("selected A + hovered B coexist in state",
                s["selected"] == "block_a" and s["hovered"] == "block_b"
                and s["anchor"] is not None and near(s["anchor"], ref_b),
                json.dumps(s))

        # ── STEP 6: F -> the real finite-area weld ──
        post_key(hwnd, VK_F)
        time.sleep(0.4)
        wl = welds(eng)
        assert_("F weld: one connector in /tick_b2_state",
                len(wl) == 1, json.dumps(wl))
        assert_("F weld: block_a -> block_b, 3 anchors, k 10000",
                wl and wl[0]["a"] == "block_a" and wl[0]["b"] == "block_b"
                and wl[0]["n_anchors"] == 3
                and abs(wl[0]["k_n_per_m"] - 10000.0) < 1e-6, json.dumps(wl[0]))
        s = istate(eng)
        assert_("F weld: selection KEPT, state route shows the pair",
                s["selected"] == "block_a" and s["hovered"] == "block_b"
                and nparts(eng) == 2, json.dumps(s))
        lines = b2i_log_lines(eng)
        assert_("F weld: success logged with real names",
                any(e["kind"] == "b2i" and "welded block_a to block_b" in e["detail"]
                    for e in lines), json.dumps(lines[-6:]))
        shot(eng, "6-welded")

        # ── STEP 7: F hovering the SELECTED part itself -> refusal ──
        post_move(hwnd, pix_a[0], pix_a[1])
        time.sleep(0.4)
        s = istate(eng)
        assert_("hover A again: hovered == selected == block_a",
                s["hovered"] == "block_a" and s["selected"] == "block_a",
                json.dumps(s))
        post_key(hwnd, VK_F)
        time.sleep(0.4)
        lines = b2i_log_lines(eng)
        assert_("F self-weld: refusal logged by name",
                any(e["kind"] == "b2i" and "cannot weld to itself" in e["detail"]
                    for e in lines), json.dumps(lines[-6:]))
        wl = welds(eng)
        assert_("F self-weld: the existing weld is unchanged",
                len(wl) == 1 and wl[0]["a"] == "block_a"
                and wl[0]["b"] == "block_b", json.dumps(wl))

        # ── STEP 8: Esc and X still work (Esc count / removal law) ──
        post_key(hwnd, VK_ESCAPE)
        time.sleep(0.4)
        s = istate(eng)
        assert_("esc: mode off, selection cleared, parts unchanged",
                s["mode"] == "off" and s["selected"] is None
                and nparts(eng) == 2, json.dumps(s))
        pix_b2 = hit_pixel(eng, "block_b", w, h)
        assert pix_b2, "no /tick_b2_pick pixel for block_b (X pass)"
        post_click(hwnd, pix_b2[0], pix_b2[1])
        clicks_posted += 1
        time.sleep(0.4)
        post_key(hwnd, VK_X)
        time.sleep(0.6)
        s = istate(eng)
        ids = [p["id"] for p in eng.get("/tick_b2_parts")["parts"]]
        assert_("X removed the welded block_b; its weld dropped with it",
                s["selected"] is None and "block_b" not in ids
                and len(welds(eng)) == 0, json.dumps(s) + " welds=" + json.dumps(welds(eng)))
        shot(eng, "7-removed")
        results["clicks_posted"] = clicks_posted

        # ── STEP 9: interactive OFF resets the hover too ──
        eng.post("/tick_b2_interactive", {"on": False})
        time.sleep(0.2)
        s = istate(eng)
        assert_("disable resets state incl. hovered",
                s["interactive"] is False and s["mode"] == "off"
                and s["selected"] is None and s["hovered"] is None
                and s["anchor"] is None, json.dumps(s))

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
