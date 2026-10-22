"""WC-PLAY-1 WALKTHROUGH -- the full player arc through REAL Win32 input.

Drives the newly built chimera_engine.exe window (booted WITH the hazard
scene via --scene and the interactive arm via --interactive) with
PostMessageW mouse and keyboard events only -- every game action (Tab place
mode, hover, Enter commit, click select, X remove, F9 save, F10 load) is a
real window message. HTTP is read-only evidence (state, log, pick, glass)
exactly as in the published WC-INTERACT-1/2 smokes; no POST mutates the
scene.

The arc (GAME_PLAN_ACTION_RPG.md §5.1 "deliver and observe"):

    boot --scene workshop1_scene.json  -> hazard slab ALREADY in the scene
    board feed (GET-only accessory)    -> live verdict chip on the board
    Tab x2 (pillar), hover slab, Enter -> pillar on the slab
    Tab x2 (crate), hover pillar, Enter-> crate on the pillar
    settle                             -> board flips HELD (green)
    F9                                 -> workshop_save.json written + log
    X, click pillar, X                 -> invention wiped
                                       -> board flips LOST: "place a crate"
    F10                                -> invention restored
                                       -> settle -> board HELD again
    failure beat: click crate, X, hover the pillar's EDGE pixel, Enter
                                       -> off-centre crate topples onto the
                                          hazard -> board LOST with the
                                          ACTION line

Evidence: this script + results.json + /glass PNGs land in this directory.

Run:  C:/Python314/python.exe .tmp/wc_play1_walk/walk_player_arc.py
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
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EXE = REPO / ".tmp" / "body-engine" / "Release" / "chimera_engine.exe"
SCENE = REPO / "tools" / "construction_packet" / "workshop1_scene.json"
FEED = REPO / "tools" / "construction_packet" / "workshop_board_feed.py"
OUT = HERE

PORT = 8841
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
WM_MOUSEMOVE = 0x0200
MK_LBUTTON = 1
VK_TAB, VK_RETURN, VK_ESCAPE, VK_X = 0x09, 0x0D, 0x1B, 0x58
VK_F9, VK_F10, VK_SPACE, VK_CONTROL = 0x78, 0x79, 0x20, 0x11

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
        req = urllib.request.Request(
            self.base + path, data=json.dumps(doc).encode(), method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())


def find_window(pid: int):
    hwnd = user32.FindWindowA(b"ChimeraEngine", None)
    assert hwnd, "game window (class ChimeraEngine) not found"
    buf = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(buf))
    assert buf.value == pid, f"window pid {buf.value} != engine pid {pid}"
    return hwnd


def post_click(hwnd, mx: int, my: int) -> None:
    lp = (my & 0xFFFF) << 16 | (mx & 0xFFFF)
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)


def post_move(hwnd, mx: int, my: int) -> None:
    # a HOVER: WM_MOUSEMOVE with NO button bits in wParam (smoke-proven)
    lp = (my & 0xFFFF) << 16 | (mx & 0xFFFF)
    user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)


def post_key(hwnd, vk: int) -> None:
    # lparam 0: bit 30 clear -> the engine's edge trigger sees a fresh press
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


def istate(eng: Http) -> dict:
    return eng.get("/tick_b2_interactive")


def state(eng: Http) -> dict:
    return eng.get("/tick_b2_state")


def part_ids(eng: Http) -> list:
    return [p["id"] for p in eng.get("/tick_b2_parts")["parts"]]


def log_lines(eng: Http) -> list:
    return eng.get("/log")["lines"]


def wait_until(fn, timeout: float, desc: str, poll: float = 0.25):
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        last = fn()
        if last:
            return last
        time.sleep(poll)
    raise AssertionError(f"timeout waiting for {desc} (last={last!r})")


def settle(eng: Http, timeout: float = 20.0, vthresh: float = 2e-3) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = state(eng)
        if all(p["speed_m_s"] < vthresh for p in st["parts"]):
            time.sleep(0.4)
            return state(eng)
        time.sleep(0.2)
    return state(eng)


def board(eng_feed_ready: Path) -> dict:
    return json.loads(eng_feed_ready.read_text(encoding="utf-8"))


def verdict_of(doc: dict) -> tuple:
    st = doc["stages"][0]
    return ("HELD" if st["status"] == "green" else "LOST"), st["cell"], st["law"]


def wait_verdict(eng: Http, want: str, timeout: float = 8.0) -> tuple:
    def check():
        try:
            v, cell, law = verdict_of(board(BOARD))
            return (v, cell, law) if v == want else None
        except Exception:
            return None
    return wait_until(check, timeout, f"board verdict {want}")


# ── pixel finding: the SAME camera ray + B2Scene::pick the window's own
#    click/hover handlers run (the smoke's /tick_b2_pick instrument) ────────
def zoom_in(hwnd, seconds: float = 1.1) -> None:
    """A real player zoom: hold SPACE (the polled per-frame zoom key,
    zoom_speed 8 units/s) so the workshop fills the frame enough for the
    pick scan and the hover pixels. Key-down + hold + key-up."""
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_SPACE, 0)
    time.sleep(seconds)
    user32.PostMessageW(hwnd, WM_KEYUP, VK_SPACE, 0)
    time.sleep(0.5)


def zoom_out(hwnd, seconds: float = 1.5) -> None:
    """A real player zoom: hold CTRL (the polled per-frame zoom-OUT key,
    zoom_speed 8 units/s, radius capped at 100). The deterministic escape
    from an over-zoomed camera -- measured run 8: the old per-attempt
    zoom-IN retry took the radius-12 camera to ~0.8, INSIDE the scene,
    and every later scan then saw a handful of sparse pick hits."""
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_CONTROL, 0)
    time.sleep(seconds)
    user32.PostMessageW(hwnd, WM_KEYUP, VK_CONTROL, 0)
    time.sleep(0.5)


def camera_reset(hwnd) -> None:
    """Back to the PROVEN scan view: zoom out to the default radius (~12),
    then the arc's 1.1 s zoom-in. Measured from that state (probe_flip
    runs 1-2): 19-221 slab pick hits at step 0.02 and a fully supporting
    anchor always available."""
    zoom_out(hwnd)
    zoom_in(hwnd)


def scan_hits(eng: Http, w: int, h: int, x0=0.05, x1=0.95, y0=0.05, y1=0.95,
              step=0.03):
    hits = []
    iy = y0
    while iy <= y1 + 1e-9:
        ix = x0
        while ix <= x1 + 1e-9:
            r = eng.post("/tick_b2_pick", {"px": ix, "py": iy})
            if r.get("ok") and r.get("id"):
                hits.append({"mx": int(round(ix * w)), "my": int(round(iy * h)),
                             "hit": [float(v) for v in r["hit"]],
                             "id": r["id"]})
            ix += step
        iy += step
    return hits


def scan_part(eng: Http, hwnd, w: int, h: int, part_id: str,
              attempts: int = 3, step: float = 0.02):
    """Full-frame scan for part_id's pixels, zooming IN between attempts —
    at the default camera (radius ~12) the 280 mm slab is ~25 px wide and
    even a 0.02-fraction grid can miss it entirely. Real-input zoom (held
    SPACE) between scans; the zoom is a player action, not a shortcut."""
    hits: list = []
    for attempt in range(attempts):
        all_hits = scan_hits(eng, w, h, step=step)
        hits = [h for h in all_hits if h["id"] == part_id]
        print(f"    scan attempt {attempt + 1} (step {step}): "
              f"{len(all_hits)} pick hits, {len(hits)} for {part_id}")
        if hits:
            return hits
        # BOUNDED retry: reset the camera to the proven scan view instead of
        # zooming further IN -- the old 0.3 s zoom-in steps only made an
        # over-zoomed camera worse (measured run 8: radius ~0.8, INSIDE the
        # scene, sparse hits forever).
        camera_reset(hwnd)
    raise AssertionError(f"no pick pixels for {part_id} after {attempts} "
                         f"scan/zoom attempts")


def refine(eng: Http, w: int, h: int, around: dict, span=0.06, step=0.004):
    x0 = max(0.0, (around["mx"] / w) - span)
    x1 = min(1.0, (around["mx"] / w) + span)
    y0 = max(0.0, (around["my"] / h) - span)
    y1 = min(1.0, (around["my"] / h) + span)
    return scan_hits(eng, w, h, x0, x1, y0, y1, step)


def top_face_hits(hits: list, part_id: str, tol_m: float = 0.002) -> list:
    """The hits on part_id whose world y is within tol of the highest hit y —
    the visible TOP face (the surface a player builds on)."""
    ph = [h for h in hits if h["id"] == part_id]
    assert ph, f"no pick pixels found for {part_id}"
    ytop = max(h["hit"][1] for h in ph)
    return [h for h in ph if abs(h["hit"][1] - ytop) <= tol_m]


def centre_pixel(hits: list):
    cx = sum(h["mx"] for h in hits) / len(hits)
    cy = sum(h["my"] for h in hits) / len(hits)
    return min(hits, key=lambda h: (h["mx"] - cx) ** 2 + (h["my"] - cy) ** 2)


# ── the careful AIM: a real player looks before pressing Enter ────────────
# Measured (run 8 receipt + probe_flip): the engine's pick and commit are
# LIVE and correct -- a centred anchor settles in <1 s (up_y 1, speed 0,
# 4 pair contacts) -- but run 8's over-zoomed scan served an anchor 36 mm
# off-centre, the 120 mm pillar spawned with a 16 mm bottom-face overhang,
# wedged into a lean against the pad and crept at sub-gate speed forever.
# The aim therefore gates on the kit part's WHOLE bottom face fitting the
# support's top footprint (B9's own base-band discipline, 2 mm, plus 1 mm).
KIT_HALF_XZ = {"pier": (0.05, 0.09), "pillar": (0.06, 0.06),
               "deck": (0.31, 0.07), "crate": (0.05, 0.025)}
AIM_MARGIN_M = 0.003


def scene_footprints() -> dict:
    """authored world x/z footprint (cx, cz, hx, hz) per boot-scene part:
    vertices_local_m are the world footprint at the authored pose, which IS
    the rung-law rest the build gate waits for."""
    doc = json.loads(SCENE.read_text(encoding="utf-8"))
    out = {}
    for p in doc["parts"]:
        vs = p["vertices_local_m"]
        xs, zs = vs[0::3], vs[2::3]
        out[p["id"]] = ((min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2,
                        (max(xs) - min(xs)) / 2, (max(zs) - min(zs)) / 2)
    return out


FOOTPRINTS = scene_footprints()


def support_footprint(eng: Http, support_id: str) -> tuple:
    if support_id in FOOTPRINTS:
        return FOOTPRINTS[support_id]
    com = part_by_id(eng, support_id)["com_m"]
    hx, hz = KIT_HALF_XZ[support_id.rsplit("_", 1)[0]]
    return (com[0], com[2], hx, hz)


def fitting(hits: list, eng: Http, support_id: str, kit_prefix: str) -> list:
    fp = support_footprint(eng, support_id)
    hx, hz = KIT_HALF_XZ[kit_prefix]
    return [k for k in hits
            if abs(k["hit"][0] - fp[0]) <= fp[2] - hx - AIM_MARGIN_M
            and abs(k["hit"][2] - fp[1]) <= fp[3] - hz - AIM_MARGIN_M]


def aim_at_support(eng: Http, hwnd, w: int, h: int, support_id: str,
                   kit_prefix: str, rounds: int = 3):
    """scan -> double refine -> the top-face hit nearest the support's live
    COM whose world x/z puts the kit part's WHOLE bottom face inside the
    support's top footprint. Camera-reset between rounds (run 8: an
    over-zoomed camera served 22 sparse hits and a wedging anchor; the
    reset view serves hundreds)."""
    for r in range(rounds):
        hits = scan_part(eng, hwnd, w, h, support_id)
        fine = []
        for h0 in sorted(hits, key=lambda k: (k["mx"] - w / 2) ** 2
                         + (k["my"] - h / 2) ** 2)[:6]:
            fine += refine(eng, w, h, h0)
        top = top_face_hits(fine + hits, support_id)
        com = part_by_id(eng, support_id)["com_m"]

        def off(k):
            return (k["hit"][0] - com[0]) ** 2 + (k["hit"][2] - com[2]) ** 2

        best = min(top, key=off)
        # second, tighter refine pass around the best hit -- one pass leaves
        # ~6 mm pixel resolution (the crate path's measured fix)
        fine2 = refine(eng, w, h, best, span=0.015, step=0.001)
        top2 = top_face_hits(fine2, support_id) or top
        ok = fitting(top2, eng, support_id, kit_prefix)
        print(f"    aim round {r + 1}: {len(top)} top hits, {len(top2)} "
              f"refined, {len(ok)} fit the {kit_prefix} bottom face")
        if ok:
            return min(ok, key=off)
        camera_reset(hwnd)
    raise AssertionError(f"no fully-supporting anchor for {kit_prefix} on "
                         f"{support_id} after {rounds} aim rounds")


def hover_and_check(eng: Http, hwnd, w: int, h: int, cands: list,
                    want_id: str, label: str):
    """Hover candidate pixels until the interactive state names want_id.
    Panels are not transparent to input, so the first pixel may be under
    one -- the candidate list IS the fallback (centre-most first for build
    anchors; max-x first for the edge beat)."""
    for c in cands:
        post_move(hwnd, c["mx"], c["my"])
        time.sleep(0.35)
        s = istate(eng)
        if s["hovered"] == want_id and s["anchor"] is not None:
            return c, s
    raise AssertionError(f"{label}: hover never reached {want_id}")


def up_y_of(part: dict) -> float:
    q = part["pose_q_wxyz"]
    return 1 - 2 * (q[1] * q[1] + q[3] * q[3])


def part_by_id(eng: Http, pid: str) -> dict:
    return next(p for p in state(eng)["parts"] if p["id"] == pid)


def wait_static(eng: Http, pid: str, timeout: float = 45.0,
                drift_m: float = 0.0005) -> dict:
    """The part (and scene) quiet: every speed < 2e-3 (challenge 1's
    SETTLE_V) AND this part's COM drifting < drift_m over 4 s — the live
    scene's post-spawn recovery creep (the b2i spawn is not pre-sunk, so a
    placed stack sinks ~17 mm and creeps back for tens of seconds) must be
    drained before anything builds on it."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if all(p["speed_m_s"] < 2e-3 for p in state(eng)["parts"]):
            c0 = part_by_id(eng, pid)["com_m"]
            time.sleep(4.0)
            p2 = part_by_id(eng, pid)
            d = max(abs(a - b) for a, b in zip(c0, p2["com_m"]))
            if d < drift_m:
                return p2
        time.sleep(0.5)
    return part_by_id(eng, pid)


def wait_supports_at_rest(eng: Http, timeout: float = 240.0,
                          band_m: float = 0.0025) -> dict:
    """The SETTLE-BEFORE-BUILD gate, in the engine's own rung law.

    Measured (probe_settle.log, run 5 trace): a pillar committed while its
    support still owes rung sink wedges (up_y 0.967) and creeps in z
    forever (0.09 mm/s, sub-gate), so 'pillar never settled'. Committed
    with the support AT REST the same interactive path lands the pillar
    upright, speed 0.0 at the probe-verified 0.06305 m within ~1 s.

    Rest is READ from the engine's own equilibrium report, not re-derived:
    the rung law's rest penetration is p* = m*g/k_total (k_site is
    calibrated as m*g/(4*0.01), so p* is 10 mm for every ground part), and
    the live /tick_b2_state part carries pen_step_m / pen_run_m. At rest
    both equal p* exactly (measured: pad 4746.47 * 0.01 = 47.4647 N =
    weight, pallet 1017.10 * 0.01 = 10.171 N = weight, speeds ~1e-17).
    An earlier version re-derived a rest COM height from the authored
    vertices; that frame is not com-relative, the derived rest was wrong
    by ~10 mm, and the gate could never open. Gate: every part's
    min(pen_step, pen_run) within band_m of its p* AND all speeds quiet
    AND the strict 4 s drift window passes."""
    st0 = state(eng)
    p_star = {p["id"]: p["mass_kg"] * 9.81 /
              (4.0 * p["ground"]["k_n_per_m"]) for p in st0["parts"]}
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = state(eng)
        near = all(min(p["pen_step_m"], p["pen_run_m"])
                   >= p_star[p["id"]] - band_m for p in st["parts"])
        if near and all(p["speed_m_s"] < 2e-3 for p in st["parts"]):
            c0 = {p["id"]: p["com_m"] for p in st["parts"]}
            time.sleep(4.0)
            st2 = state(eng)
            drained = all(
                max(abs(a - b) for a, b in zip(c0[p2["id"]], p2["com_m"])) < 0.0002
                for p2 in st2["parts"] if p2["id"] in c0)
            if drained:
                return st2
        time.sleep(0.5)
    raise AssertionError(
        f"boot supports never reached their rung-law rest "
        f"(pen >= p* - {band_m}) within {timeout} s "
        f"(p_star={p_star}, last={json.dumps(st)})")


def wait_settled(eng: Http, pid: str, timeout: float = 120.0,
                 drift_m: float = 0.0002) -> dict:
    """STRICT settle: RAISES if the drift window never passes. wait_static
    returns quietly on timeout, and a live-base part creeps at sub-2e-3
    speed (measured: the pillar sank 14 mm in the ~30 s of one crate step
    -- 0.5 mm/s, invisible to the speed gate) -- so a crate aimed at the
    scanned pillar top spawned 14 mm above the support and slid off."""
    t0 = time.time()
    trace: list = []
    while time.time() - t0 < timeout:
        st = state(eng)
        quiet = all(p["speed_m_s"] < 2e-3 for p in st["parts"])
        trace.append({"t": round(time.time() - t0, 2), "quiet": quiet,
                      "parts": {p["id"]: (round(p["speed_m_s"], 6),
                                          [round(v, 6) for v in p["com_m"]])
                                for p in st["parts"]}})
        if quiet:
            c0 = part_by_id(eng, pid)["com_m"]
            time.sleep(4.0)
            p2 = part_by_id(eng, pid)
            d = max(abs(a - b) for a, b in zip(c0, p2["com_m"]))
            if d < drift_m:
                return p2
        time.sleep(0.5)
    (OUT / "wait_settled_trace.json").write_text(
        json.dumps(trace, indent=1), encoding="utf-8")
    raise AssertionError(f"{pid} never settled within {timeout} s")


def build_with_retries(eng: Http, hwnd, w: int, h: int, mode: str,
                       cands_fn, hover_id: str, prefix: str, verify,
                       label: str, tries: int = 4) -> str:
    """Place -> settle -> verify -> (X the selected new part) -> re-place.
    The player's own repair loop with shipped keys only: a live-scene
    placement that wedges (the support leans) or drops its load is removed
    and re-placed, exactly the 'build, test, repair' loop of the game."""
    tab_to_mode(eng, hwnd, mode)
    for attempt in range(tries):
        cands = cands_fn()
        pix, s = hover_and_check(eng, hwnd, w, h, cands, hover_id, label)
        print(f"    {label} commit anchor: {s['anchor']} "
              f"hovered={s['hovered']} px=({pix['mx']},{pix['my']})")
        post_key(hwnd, VK_RETURN)
        time.sleep(0.8)
        s = istate(eng)
        pid = s["selected"]
        if not (pid and pid.startswith(prefix) and pid in part_ids(eng)):
            raise AssertionError(f"{label}: commit did not land (state {s})")
        try:
            ok, detail = verify(pid)
        except AssertionError as e:
            ok, detail = False, str(e)   # the player's repair loop, not an abort
        results["steps"].append({"step": f"{label} attempt {attempt + 1}",
                                 "part": pid, "ok": ok, "detail": detail})
        print(f"    {label} attempt {attempt + 1}: {'ok' if ok else detail}")
        if ok:
            return pid
        post_key(hwnd, VK_X)          # the new part is still selected
        time.sleep(1.0)
    raise AssertionError(f"{label}: {tries} placements all failed")


def tab_to_mode(eng: Http, hwnd, want: str):
    for _ in range(6):
        s = istate(eng)
        if s["mode"] == want:
            return s
        post_key(hwnd, VK_TAB)
        time.sleep(0.3)
    raise AssertionError(f"Tab never reached mode {want}")


BOARD = (OUT / "studio_board_walk.json").resolve()


def main() -> int:
    results["exe_sha256"] = hashlib.sha256(EXE.read_bytes()).hexdigest()
    results["scene_sha256"] = hashlib.sha256(SCENE.read_bytes()).hexdigest()
    results["feed_sha256"] = hashlib.sha256(FEED.read_bytes()).hexdigest()

    native = OUT / "native"
    if native.exists():
        shutil.rmtree(native)
    native.mkdir()
    shutil.copy2(EXE, native / EXE.name)
    shutil.copytree(EXE.parent / "shaders", native / "shaders",
                    dirs_exist_ok=True)
    with socket.socket() as s:
        assert s.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} busy"

    save_path = native / "workshop_save.json"
    if save_path.exists():
        save_path.unlink()

    # ── boot: scene + interactive arm are ARGV, the board path ABSOLUTE ──
    argv = [str(native / EXE.name), str(PORT), str(BOARD), "1600", "900",
            "--no-restore", "--interactive",
            "--scene", str(SCENE.resolve())]
    proc = subprocess.Popen(argv, cwd=native,
                            stdout=(native / "stdout.log").open("wb"),
                            stderr=(native / "stderr.log").open("wb"))
    results["pid"] = proc.pid
    eng = Http(PORT)
    feed = None
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
        st = eng.get("/studio")
        w, h = int(st["w"]), int(st["h"])
        results["client"] = [w, h]
        print(f"window hwnd=0x{hwnd:x} client={w}x{h}")

        # ── the live verdict accessory: GET-only board feed subprocess ──
        feed = subprocess.Popen(
            [sys.executable, str(FEED), "--port", str(PORT),
             "--board", str(BOARD), "--interval", "0.5"],
            cwd=OUT, stdout=(OUT / "feed_stdout.log").open("wb"),
            stderr=(OUT / "feed_stderr.log").open("wb"))
        time.sleep(1.5)

        # ── STEP 1: the scene booted WITH the hazard already in it ──
        st = state(eng)
        ids = [p["id"] for p in st["parts"]]
        assert_("scene booted admitted (no HTTP admit posted)",
                st.get("active") is True, json.dumps({k: st[k] for k in
                                                      ("active", "steps")}))
        assert_("hazard slab in the booted scene", "hazard_pad" in ids,
               json.dumps(ids))
        assert_("scene has exactly the boot scene's parts",
                sorted(ids) == ["hazard_pad", "kit_pallet"], json.dumps(ids))
        law_seen = wait_verdict(eng, "LOST", timeout=8.0)   # no crate yet
        assert_("board feed states the upright law",
                "upright" in law_seen[2], law_seen[2])
        assert_("board LOST with the ACTION line before any build",
                "place a crate" in law_seen[1], law_seen[1])
        shot(eng, "1-scene-startup")

        # ── STEP 2: Tab to pillar mode (off -> place_1 pier -> place_2) ──
        # the pick needs the render camera up; then zoom IN like a player so
        # the workshop fills the frame (the default radius-12 view renders
        # the 280 mm slab ~25 px wide — too small to hover reliably)
        wait_until(lambda: "no camera yet" not in
                   json.dumps(eng.post("/tick_b2_pick",
                                       {"px": 0.5, "py": 0.5})),
                   30.0, "pick camera ready")

        # The pad boots FLUSH (zero spring penetration), so the old drift
        # window passed at boot while the pad still owed its whole ~10 mm
        # own-weight rung sink; a pillar committed during that drain wedged
        # (up_y 0.967) and crept in z forever -- run 2/3/5's 'pillar never
        # settled'. Wait until the pad is at its RUNG-LAW REST first
        # (probe_settle.log: at-rest support -> pillar upright, speed 0.0
        # at 0.06305 m in ~1 s).
        slab0 = wait_supports_at_rest(eng, timeout=240.0)
        results["steps"].append({"step": "supports at rung-law rest before build",
                                 "com": {p["id"]: p["com_m"]
                                         for p in slab0["parts"]}})
        zoom_in(hwnd)
        tab_to_mode(eng, hwnd, "place_2")
        s = istate(eng)
        assert_("Tab arms place_2 (the pillar kit part)",
                s["mode"] == "place_2", json.dumps(s))
        assert_("the board's tool line names the player's keys",
                "F9 save" in verdict_of(board(BOARD))[1] or
                "F9 save" in board(BOARD)["stages"][0]["tool"],
                board(BOARD)["stages"][0]["tool"])

        # hover the slab's top face, Enter -> pillar on the slab. The AIM is
        # gated: the pillar's WHOLE bottom face must fit the pad's top
        # footprint (run 8's receipt: a 36 mm off-centre anchor overhung the
        # pad edge by 16 mm and the pillar wedged into a lean that creeps at
        # sub-gate speed forever; probe_flip proved the centred anchor
        # settles in <1 s -- the pick and commit are live and correct).
        pix_slab = aim_at_support(eng, hwnd, w, h, "hazard_pad", "pillar")
        print(f"    pillar aim: {json.dumps(pix_slab['hit'])}")
        pix_slab, s = hover_and_check(eng, hwnd, w, h, [pix_slab],
                                      "hazard_pad", "slab hover")

        # the pillar: place -> settle -> verify upright+static; a live-scene
        # placement can WEDGE the pillar into a lean (the b2i spawn is not
        # pre-sunk), so the player's repair loop is: X it, place again
        def pillar_verify(pid):
            p = wait_settled(eng, pid)
            uy = up_y_of(p)
            ok = uy > 0.999 and p["speed_m_s"] < 2e-3
            return ok, (f"up_y={uy:.4f} speed={p['speed_m_s']:.5f} "
                        f"com={p['com_m']}")

        pillar_id = build_with_retries(
            eng, hwnd, w, h, "place_2", lambda: [pix_slab], "hazard_pad",
            "pillar", pillar_verify, label="pillar")
        s = istate(eng)
        assert_("pillar selection + mode survive the commit",
                s["mode"] == "place_2", json.dumps(s))
        shot(eng, "2-pillar-placed")

        # ── STEP 3: Tab to crate mode, hover the pillar TOP, Enter ──
        # fresh top-face pixels per attempt (a re-placed pillar moves)
        def crate_cands():
            pil_fine = refine(eng, w, h, pix_slab, span=0.08, step=0.003)
            pil_top = top_face_hits(pil_fine, pillar_id)
            assert pil_top, f"no top-face pixels on {pillar_id}"
            # Aim at the top-face point whose WORLD x/z is nearest the
            # pillar's COM, not the pixel-space centre: the visible top face
            # is a camera-skewed trapezoid, and its pixel centre sat ~13 mm
            # off-axis (measured: the eccentric load walked the light pillar
            # out from under the crate -- crate toppled +z as the pillar
            # slid -z).
            pc = part_by_id(eng, pillar_id)["com_m"]

            def off(k):
                return (k["hit"][0] - pc[0]) ** 2 + (k["hit"][2] - pc[2]) ** 2

            best = min(pil_top, key=off)
            # one refine pass leaves ~6 mm pixel resolution -- the best hit
            # was still 11 mm off-axis and the eccentric load walked the
            # pillar. A second, tighter pass around the on-axis hit lands
            # the commit anchor within a few mm.
            fine2 = refine(eng, w, h, best, span=0.015, step=0.001)
            top2 = top_face_hits(fine2, pillar_id) or pil_top
            rest = sorted(top2, key=off)
            # prefer fully-supporting anchors (the pillar step's aim gate);
            # a crate's slight overhang topples CLEANLY (measured probe_flip:
            # an overhanging spawn either settles or falls upright at rest,
            # both inside the verify band), so the gate is a preference, not
            # a hard requirement here
            fits = fitting(rest, eng, pillar_id, "crate")
            if fits:
                rest = fits
            return rest[:3]          # on-axis first, two fallbacks

        def crate_verify(cid):
            p = wait_settled(eng, cid)
            uy = up_y_of(p)
            pil = part_by_id(eng, pillar_id)
            pil_top_y = pil["com_m"][1] + 0.05
            bottom = p["com_m"][1] - 0.025
            # resting ON the top: the pair-equilibrium sink is w_crate/
            # pair_kt = 6.7 mm (measured, probe_flush.py), so the band is
            # [-12, +4] mm around the live top face, not a flush touch
            near = -0.012 < bottom - pil_top_y < 0.004
            ok = uy > 0.999 and near and p["speed_m_s"] < 2e-3
            anch = istate(eng).get("anchor")
            return ok, (f"up_y={uy:.4f} bottom-top={1000 * (bottom - pil_top_y):.1f} mm "
                        f"speed={p['speed_m_s']:.5f} crate_com={p['com_m']} "
                        f"pillar_com={pil['com_m']} anchor={anch}")

        crate_id = build_with_retries(
            eng, hwnd, w, h, "place_4", crate_cands, pillar_id,
            "crate", crate_verify, label="crate")
        assert_("exactly one crate in the scene",
                sum(1 for p in part_ids(eng) if p.startswith("crate")) == 1,
                json.dumps(part_ids(eng)))
        pil_fine = refine(eng, w, h, pix_slab, span=0.08, step=0.003)
        pil_top = top_face_hits(pil_fine, pillar_id)
        pix_pil = centre_pixel(pil_top)

        # ── STEP 4: settle -> the live verdict flips HELD ──
        settle(eng, timeout=20.0)
        held = wait_verdict(eng, "HELD", timeout=8.0)
        assert_("board verdict HELD after the build settles",
                held[0] == "HELD", held[1])
        st = state(eng)
        results["held_state"] = {
            "ids": [p["id"] for p in st["parts"]],
            "crate_com_m": next(p["com_m"] for p in st["parts"]
                                if p["id"] == crate_id)}
        shot(eng, "3-crate-HELD")

        # ── STEP 5: F9 saves the invention ──
        post_key(hwnd, VK_F9)
        wait_until(lambda: save_path.exists(), 5.0,
                   "workshop_save.json written by F9")
        lines = log_lines(eng)
        assert_("F9 logged 'saved 4 parts to workshop_save.json'",
                any(e.get("kind") == "b2i"
                    and "saved 4 parts to workshop_save.json" in e["detail"]
                    for e in lines), json.dumps(lines[-8:]))
        save_doc = json.loads(save_path.read_text(encoding="utf-8"))
        assert_("save doc carries the 4-part invention",
                len(save_doc["parts"]) == 4
                and sorted(p["id"] for p in save_doc["parts"])
                == sorted(["hazard_pad", "kit_pallet", pillar_id, crate_id]),
                json.dumps([p["id"] for p in save_doc["parts"]]))

        # ── STEP 6: wipe it — X the crate, click the pillar, X ──
        post_key(hwnd, VK_X)
        time.sleep(0.6)
        assert_("X removed the selected crate",
                crate_id not in part_ids(eng), json.dumps(part_ids(eng)))
        pix_pil2, s = hover_and_check(eng, hwnd, w, h, [pix_pil], pillar_id,
                                      "pillar re-hover for select")
        post_click(hwnd, pix_pil2["mx"], pix_pil2["my"])
        time.sleep(0.5)
        s = istate(eng)
        assert_("click selects the pillar", s["selected"] == pillar_id,
                json.dumps(s))
        post_key(hwnd, VK_X)
        time.sleep(0.6)
        assert_("X removed the pillar — the invention is wiped",
                sorted(part_ids(eng)) == ["hazard_pad", "kit_pallet"],
                json.dumps(part_ids(eng)))
        lost = wait_verdict(eng, "LOST", timeout=8.0)
        assert_("board verdict LOST after the wipe", lost[0] == "LOST",
                lost[1])
        assert_("LOST names the ACTION: place a crate",
                "place a crate" in lost[1], lost[1])
        shot(eng, "4-broken-LOST")

        # ── STEP 7: F10 brings it back ──
        post_key(hwnd, VK_F10)
        lines = wait_until(
            lambda: [e for e in log_lines(eng)
                     if e.get("kind") == "b2i"
                     and "loaded 4 parts from workshop_save.json"
                     in e["detail"]] or None,
            6.0, "F10 load log line")
        assert_("F10 logged the 4-part load", bool(lines), json.dumps(lines))
        ids = wait_until(
            lambda: part_ids(eng) if pillar_id in part_ids(eng)
            and crate_id in part_ids(eng) else None,
            6.0, "restored parts in the scene")
        assert_("F10 restored the invention",
                sorted(ids) == sorted(["hazard_pad", "kit_pallet",
                                       pillar_id, crate_id]), json.dumps(ids))
        settle(eng, timeout=20.0)
        held2 = wait_verdict(eng, "HELD", timeout=8.0)
        assert_("board verdict HELD again after the load", held2[0] == "HELD",
                held2[1])
        shot(eng, "5-loaded-HELD")

        # ── STEP 8: FAILURE BEAT — off-centre crate near the pillar edge ──
        # a FRESH fine scan: the loaded crate now occupies the pixel that
        # hit the pillar top before, so the crate's own pixels come from the
        # live pick, not the pre-build scan
        cr_fine = refine(eng, w, h, pix_pil, span=0.05, step=0.003)
        cr_hits = [h2 for h2 in cr_fine if h2["id"] == crate_id]
        cands = [centre_pixel(cr_hits)] if cr_hits else [centre_pixel(pil_top)]
        pix_cr, s = hover_and_check(
            eng, hwnd, w, h, cands, crate_id, "crate hover for select")
        post_click(hwnd, pix_cr["mx"], pix_cr["my"])
        time.sleep(0.5)
        s = istate(eng)
        assert_("click selects the crate", s["selected"] == crate_id,
                json.dumps(s))
        post_key(hwnd, VK_X)
        time.sleep(0.6)
        assert_("crate removed for the retry",
                crate_id not in part_ids(eng), json.dumps(part_ids(eng)))
        wait_verdict(eng, "LOST", timeout=8.0)   # no crate again

        tab_to_mode(eng, hwnd, "place_4")
        # the EDGE pixel: the pillar top-face hit with the FURTHEST +x world
        # coordinate — the commit spawns the crate's COM directly above it,
        # at/over the support edge (the B8/B9 topple class)
        edge = max(pil_top, key=lambda k: k["hit"][0])
        edge_c, s = hover_and_check(eng, hwnd, w, h, [edge], pillar_id,
                                    "pillar-edge hover")
        results["edge_anchor"] = edge["hit"]
        post_key(hwnd, VK_RETURN)
        time.sleep(0.6)
        s = istate(eng)
        crate2 = s["selected"]
        assert_("off-centre crate committed at the edge",
                crate2 and crate2.startswith("crate")
                and crate2 in part_ids(eng), json.dumps(s))
        st = settle(eng, timeout=25.0)
        c2 = next(p for p in st["parts"] if p["id"] == crate2)
        q = c2["pose_q_wxyz"]
        up_y2 = 1 - 2 * (q[1] * q[1] + q[3] * q[3])
        st_last = state(eng)
        slab_p = next(p for p in st_last["parts"] if p["id"] == "hazard_pad")
        results["offcentre"] = {
            "crate2_com_m": c2["com_m"],
            "crate2_speed_m_s": c2["speed_m_s"],
            "crate2_up_y": up_y2,
            "edge_hit_m": edge["hit"],
            "slab_com_y": slab_p["com_m"][1]}
        assert_("the off-centre crate actually toppled (up-axis far off "
                "vertical)", up_y2 < 0.9848, f"up_y={up_y2:.4f}")
        lost2 = wait_verdict(eng, "LOST", timeout=8.0)
        assert_("board verdict LOST for the off-centre crate",
                lost2[0] == "LOST", lost2[1])
        assert_("LOST carries the challenge-1 ACTION line",
                "remove the crate and centre it over its support" in lost2[1],
                lost2[1])
        shot(eng, "6-offcentre-LOST")

        results["verdict"] = "PASS"
    finally:
        (OUT / "results.json").write_text(json.dumps(results, indent=2),
                                          encoding="utf-8", newline="\n")
        if feed is not None and feed.poll() is None:
            feed.terminate()
            try:
                feed.wait(10)
            except subprocess.TimeoutExpired:
                feed.kill()
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
    print("VERDICT PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
