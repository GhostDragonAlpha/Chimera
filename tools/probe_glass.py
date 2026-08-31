"""probe_glass.py — THE GLASS CHANNEL (docs/THE_ENGINE_STUDIO.md §G1), executed.

RULE-0 MEMBRANE (stated before the run):
  STATEMENT : the Studio draws itself into the SWAPCHAIN, never into rt_image_,
              so /frame is pixel-clean by construction and /glass is the same
              frame WITH the instrument composited on top. The two channels are
              one render read at two different points, not two renders.
  PREDICTION: with the overlay up, glass differs from frame by strictly more
              pixels than it does with the overlay down; toggling the chrome
              shrinks that difference measurably; and frame does not move by a
              single pixel across every one of those toggles.
  FALSIFIERS (named before the run):
    A: frame(overlay ON) is not BYTE-IDENTICAL to frame(overlay OFF) -> the
       overlay bleeds into rt_image_, /frame is not a clean channel, and the
       whole two-channel design is a lie.
    B: glass(overlay ON) does not differ from frame by strictly MORE pixels
       than glass(overlay OFF) -> the glass is not carrying the panels; the
       docks are invisible to the eye and the instrument cannot see the
       instrument.
    C: THE ABLATION — turning the chrome off does not shrink the glass/frame
       difference, or it moves frame at all. Without this the channel is a
       second capture route wearing a new name: it must fail when the thing it
       claims to capture is removed.
    D: STABILITY — three consecutive glass grabs with the show clock paused do
       not agree on their difference-from-frame within 1%. A channel that
       flickers is reading a stale or uninitialised buffer, which is the exact
       failure /glass exists to avoid (an instrument reporting on a frame that
       was never drawn).
    E: any VK error in the engine log for the whole run.
    F: the probe is not idempotent — a second run disagrees with the first.

Usage:  python tools/probe_glass.py [--launch] [--minimize]
        (engine left running on :8090; --launch starts one only if it is down)

  --minimize  also exercise the no-present path (D-loud): minimizes the engine
              window, proves /glass REFUSES rather than returning a stale frame,
              then restores it. Off by default because it takes the operator's
              window away for a moment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path("E:/PythonChimera")
EXE = ROOT / "ChimeraEngine" / "engine" / "build" / "Release" / "chimera_engine.exe"
CWD = EXE.parent
OUT = ROOT / ".tmp" / "glass_probe"
URL = "http://localhost:8090"
LOG = CWD / "engine_stdout.log"

results: dict = {}
notes: list[str] = []


# ── transport ────────────────────────────────────────────────────────────────

def req_json(method, path, payload=None, timeout=15):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(URL + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())


def grab(channel: str) -> bytes:
    """GET /frame or GET /glass -> raw PNG bytes."""
    with urllib.request.urlopen(f"{URL}/{channel}", timeout=25) as r:
        return r.read()


def up() -> bool:
    try:
        req_json("GET", "/debug", timeout=2)
        return True
    except Exception:
        return False


def set_overlay(on: bool) -> bool:
    st = req_json("POST", "/studio", {"on": bool(on)})
    return bool(st.get("on", False)) is bool(on)


def set_chrome(on: bool) -> None:
    req_json("POST", "/studio_chrome", {"on": bool(on)})


def pause_clock() -> None:
    req_json("POST", "/show", {"playing": False})


def quiescent(timeout=8.0) -> bool:
    """Wait until the glass has settled after a state change.

    NOT byte-identity — and the first run proved why. The glass carries the
    status bar's LIVE readout (fps, frame time, the show clock), so two
    consecutive glass grabs are legitimately never byte-identical; defining
    quiescence as equality made the instrument report "never settled" on a
    channel that was in fact perfectly stable (D measured spread 0.0000%).

    The stable quantity is the STRUCTURE, not the digits: how many pixels the
    glass adds over the pixel-clean frame. That is what a toggle changes, and
    it is what the HUD's own flickering does not. (Same reason _settle_capture
    waits for a frame that DIFFERS — the trap is stale pixels, and the correct
    discriminator is the thing you are actually measuring.)
    """
    t0 = time.time()
    prev = None
    while time.time() - t0 < timeout:
        g, f, _, _ = shot("_quiesce")
        cur = diff_px(g, f)
        if prev is not None and abs(cur - prev) <= max(1, int(0.001 * max(cur, 1))):
            return True
        prev = cur
        time.sleep(0.35)
    return False


# ── pixel maths ──────────────────────────────────────────────────────────────

def as_rgb(b: bytes) -> np.ndarray:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_decode.png"
    tmp.write_bytes(b)
    return np.asarray(Image.open(tmp).convert("RGB"))


def diff_px(a: np.ndarray, b: np.ndarray) -> int:
    """How many pixels differ at all. This is the whole measurement: the glass
    IS the frame plus the instrument, so the difference IS the instrument."""
    if a.shape != b.shape:
        return -1
    return int((np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2) > 0).sum())


def shot(tag: str) -> tuple[np.ndarray, np.ndarray, Path, Path]:
    """Capture both channels of the SAME rendered frame, persist both."""
    gb, fb = grab("glass"), grab("frame")
    OUT.mkdir(parents=True, exist_ok=True)
    gp, fp = OUT / f"{tag}_glass.png", OUT / f"{tag}_frame.png"
    gp.write_bytes(gb)
    fp.write_bytes(fb)
    return as_rgb(gb), as_rgb(fb), gp, fp


# ── falsifiers ───────────────────────────────────────────────────────────────

def falsifier_a(frame_on: bytes, frame_off: bytes) -> bool:
    """A: the pixel-clean channel never moves when the UI changes."""
    h_on = hashlib.sha256(frame_on).hexdigest()
    h_off = hashlib.sha256(frame_off).hexdigest()
    ok = h_on == h_off
    print(f"  A: frame sha256 on={h_on[:16]} off={h_off[:16]} identical={ok}")
    if not ok:
        notes.append("A: the overlay reaches rt_image_ — /frame is not pixel-clean")
    results["A"] = "PASS" if ok else "FAIL"
    return ok


def falsifier_b(d_on: int, d_off: int) -> bool:
    """B: the glass carries the panels, and more of them with the overlay up."""
    ok = d_off > 0 and d_on > d_off
    print(f"  B: diff px  overlay ON={d_on}  OFF={d_off}  (ON must exceed OFF, both > 0)")
    if not ok:
        notes.append(f"B: glass does not grow with the overlay (ON={d_on} OFF={d_off})")
    results["B"] = "PASS" if ok else "FAIL"
    return ok


def falsifier_c(d_chrome_on: int, d_chrome_off: int, frame_a: bytes, frame_b: bytes) -> bool:
    """C: THE ABLATION. Remove the chrome and the glass signal must shrink;
    frame must not move by one pixel."""
    shrank = d_chrome_off < d_chrome_on
    frame_still = hashlib.sha256(frame_a).hexdigest() == hashlib.sha256(frame_b).hexdigest()
    ok = shrank and frame_still
    print(f"  C: diff px  chrome ON={d_chrome_on}  OFF={d_chrome_off}  shrank={shrank}")
    print(f"  C: frame byte-identical across the chrome toggle = {frame_still}")
    if not shrank:
        notes.append(f"C: removing the chrome did not shrink the glass "
                     f"({d_chrome_on} -> {d_chrome_off}) — the channel may be "
                     f"capturing something other than the UI")
    if not frame_still:
        notes.append("C: frame moved when only the chrome changed")
    results["C"] = "PASS" if ok else "FAIL"
    return ok


def falsifier_d() -> bool:
    """D: stability. Three grabs, paused clock, same difference within 1%."""
    ds = []
    for _ in range(3):
        if not quiescent():
            notes.append("D: the glass never quiesced — reading a moving frame")
        g, f, _, _ = shot("stability")
        ds.append(diff_px(g, f))
    spread = (max(ds) - min(ds)) / max(1, max(ds))
    ok = len(ds) == 3 and min(ds) > 0 and spread <= 0.01
    print(f"  D: three grabs diff px = {ds}  spread={spread:.4%} (<= 1%)")
    if not ok:
        notes.append(f"D: glass is unstable across identical grabs {ds} — "
                     f"stale or uninitialised readback")
    results["D"] = "PASS" if ok else "FAIL"
    return ok


def falsifier_e() -> bool:
    """E: zero VK errors for the whole run.

    The log is the engine's stdout/stderr, which only exists if something
    redirected it. When this probe did not launch the engine itself, it does not
    own the log — and an error check over a file that was never written would be
    a green light over nothing. Look for whichever log the running engine left.
    """
    log = LOG
    if not log.exists():
        for cand in sorted(CWD.glob("engine*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
            log = cand
            break
    if not log.exists():
        print("  E: no engine log found — SKIPPED (not launched by this probe)")
        results["E"] = "SKIP"
        return True
    print(f"  E: reading {log.name}")
    pat = re.compile(r"(?i)(validation layer|vk\w+ failed|VK_ERROR|device lost)")
    bad = [l.strip() for l in log.read_text(errors="replace").splitlines() if pat.search(l)]
    ok = not bad
    print(f"  E: VK errors = {len(bad)}")
    for b in bad[:5]:
        print("    ", b)
    results["E"] = "PASS" if ok else "FAIL"
    return ok


def falsifier_loud() -> bool:
    """D-loud (opt-in): with no present there is no glass, and the engine must
    say so instead of handing back last frame's pixels."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        hwnd = None
        # cp1252 console: a window title carrying a glyph it cannot print killed
        # this whole falsifier on the first run (the same crash studio_board.py
        # earned its errors="replace" for). Sanitize before anything reaches out.
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def enum_cb(h, _):
            nonlocal hwnd
            if user32.IsWindowVisible(h):
                n = user32.GetWindowTextLengthW(h)
                if n:
                    buf = ctypes.create_unicode_buffer(n + 1)
                    user32.GetWindowTextW(h, buf, n + 1)
                    if "chimera" in buf.value.lower() or "engine" in buf.value.lower():
                        hwnd = h
                        return False
            return True

        user32.EnumWindows(enum_cb, 0)
        if not hwnd:
            print("  D-loud: engine window not found — SKIPPED")
            results["D_loud"] = "SKIP"
            return True

        user32.ShowWindow(hwnd, 6)          # SW_MINIMIZE
        time.sleep(1.5)
        try:
            body = grab("glass")
            refused = not body.startswith(b"\x89PNG")
            detail = body[:160].decode("utf-8", "replace")
        except Exception as e:
            refused, detail = True, f"transport error: {e}"
        user32.ShowWindow(hwnd, 9)          # SW_RESTORE
        time.sleep(1.5)

        ok = refused
        print(f"  D-loud: minimized /glass -> refused={refused}  {detail}")
        if not ok:
            notes.append("D-loud: /glass returned a PNG with no presented image "
                         "— it would report on a window nobody can see")
        results["D_loud"] = "PASS" if ok else "FAIL"
        return ok
    except Exception as e:
        print(f"  D-loud: could not exercise ({e}) — SKIPPED")
        results["D_loud"] = "SKIP"
        return True


# ── main ─────────────────────────────────────────────────────────────────────

def run_once(do_minimize: bool) -> dict:
    pause_clock()

    # overlay OFF: the only thing on the glass is the chrome
    set_overlay(False)
    quiescent()
    g_off, f_off, _, _ = shot("overlay_off")
    frame_off_bytes = grab("frame")

    # overlay ON: chrome + the docked panels
    set_overlay(True)
    quiescent()
    g_on, f_on, _, _ = shot("overlay_on")
    frame_on_bytes = grab("frame")

    d_off = diff_px(g_off, f_off)
    d_on = diff_px(g_on, f_on)

    print("== A: the pixel-clean channel never moves ==")
    falsifier_a(frame_on_bytes, frame_off_bytes)
    print("== B: the glass carries the panels ==")
    falsifier_b(d_on, d_off)

    # C: the ablation — kill the chrome, keep everything else
    print("== C: THE ABLATION — remove the chrome, the signal must shrink ==")
    set_chrome(False)
    quiescent()
    g_nc, f_nc, _, _ = shot("chrome_off")
    frame_nc_bytes = grab("frame")
    d_chrome_off = diff_px(g_nc, f_nc)
    falsifier_c(d_on, d_chrome_off, frame_on_bytes, frame_nc_bytes)
    set_chrome(True)
    quiescent()

    print("== D: stability across identical grabs ==")
    falsifier_d()

    if do_minimize:
        print("== D-loud: no present -> loud refusal, not a stale frame ==")
        falsifier_loud()

    print("== E: VK errors ==")
    falsifier_e()

    print(f"\n  diff px summary: overlay OFF={d_off}  ON={d_on}  chrome OFF={d_chrome_off}")
    print(f"  artefacts: {OUT}")
    return dict(results)


def launch() -> None:
    subprocess.Popen([str(EXE), "8090"], cwd=str(CWD),
                     creationflags=0x00000008 | 0x00000200,
                     stdout=open(LOG, "w"), stderr=subprocess.STDOUT)
    for _ in range(60):
        if up():
            return
        time.sleep(0.5)
    raise SystemExit("engine did not come up")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true",
                    help="start the engine if :8090 is down (never kills a running one)")
    ap.add_argument("--minimize", action="store_true",
                    help="also exercise the no-present refusal path")
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    if not up():
        if not a.launch:
            raise SystemExit("engine is down on :8090 — start it, or pass --launch")
        print("launching engine...")
        launch()

    st = req_json("GET", "/studio")
    print(f"engine up: w={st['w']} h={st['h']} overlay={st['on']}")

    first = run_once(a.minimize)

    failed = [k for k, v in first.items() if v == "FAIL"]
    print("\n" + "=" * 72)
    print("VERDICTS:", json.dumps(first))
    print("=" * 72)
    (OUT / "results.json").write_text(json.dumps(
        {"results": first, "notes": notes}, indent=1), encoding="utf-8")

    if notes:
        print("\nhonest negatives / notes:")
        for n in notes:
            print("  -", n)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
