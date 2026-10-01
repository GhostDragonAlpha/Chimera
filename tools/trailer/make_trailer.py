"""make_trailer.py — R7 SPINE: the 25-30 s press-and-answer trailer, as MP4.

Captures the LIVE engine (127.0.0.1:8107, sealed creature) through its real HTTP
surface — /cameras bookmarks, /tick_touch (world-space hit), /tick_touch_clear,
/tick_pose, /frame?w=1920 — and encodes the result with ffmpeg at 24 fps.

THE METHOD (stated honestly, because the capture rate forces a choice):
  GET /frame costs ~1 s floor regardless of size (render + readback + PNG), and the
  physics runs in WALL time (dimple heals at tau = 0.5 s real seconds), so a 24 fps
  fresh capture of a 28 s timeline is physically impossible without speeding up the
  sim — which we must not do. Instead:
    - every beat is PERFORMED slowly in wall time (force ramped in 12 steps, healing
      given ~6 s), and one REAL engine frame is captured every ~0.9-1.2 s;
    - each captured frame is time-remapped onto the 24 fps timeline (held, or chained
      through short crossfades for the camera moves — no optical-flow interpolation,
      every visible frame is a genuine engine render);
    - the camera is interpolated BETWEEN captures (bookmarked v[8] per frame), so the
      orbit and push-in are true camera moves, not crops.
  The HUD blood panel is drawn from the same /tick_state JSON the game page at :8206
  renders (V m3, P MPa, conserve %) plus dimple_m — the numbers are live per capture.

SCENE SPINE (R7):
  01 slow orbit establishing shot          (~7 s)
  02 push-in to the belly                  (~2.5 s)
  03 30 kN belly press, ramped + held      (~8 s, the dimple forms on camera)
  04 release — tau = 0.5 s healing         (~4 s, HUD dimple decays exponentially)
  05 knee pose 40 deg                      (~3 s)
  06 end card                              (~3.6 s)

Usage:
    python tools/trailer/make_trailer.py               # capture + encode + deliver
    python tools/trailer/make_trailer.py --keep-frames # keep the source PNGs
    python tools/trailer/make_trailer.py --out DIR     # override output path
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
FRAMES = Path(__file__).resolve().parent / ".frames"
BUILD = Path(__file__).resolve().parent / ".build"

ENGINE = "http://127.0.0.1:8107"
SCRAP_BOOKMARK = "trailer_dyn"
# full native capture is 2560x1440; the engine's ?w= quantizes to odd non-16:9
# crops (measured: 1920 -> 2560x1369), so we take full frames and scale in encode
OUT_W, OUT_H = 1920, 1080
FPS = 24

# The belly surface point the engine itself reported from a screen-space pick
# (POST /tick_touch {"px":0.483,"py":0.544} on the front view) — a real vertex
# region on the torso, not a guess.
BELLY_HIT = [-0.707, 3.806, -0.054]

CAM_ORBIT_A = [15.5, -3.40, 0.30, 0.0, 4.3, 0.0, 0, 0]   # sweep start (back 3/4)
CAM_ORBIT_B = [15.5, -1.45, 0.30, 0.0, 4.3, 0.0, 0, 0]   # sweep end   (front 3/4)
# the press hit sits on the creature's LEFT flank (hit x=-0.707): the dent faces
# left-front, measured to read best from theta ~ -3.3 (probe frames .tmp/flank_*)
CAM_PRESS   = [5.0, -3.30, 0.22, -0.707, 3.806, -0.054, 0, 0]   # dead on the hit
CAM_LEGS    = [6.0, -1.95, 0.12, 0.0, 1.35, 0.0, 0, 0]   # knee closeup

RAMP_FORCES = [3000, 6000, 10000, 14000, 18000, 22000, 26000, 30000]
KNEE_JOINT = 15          # knee_L, per tools/mitosis_run.py
KNEE_DEG = 40

# ---- timeline (seconds on the 24 fps timeline) ------------------------------
XFADE_D, XFADE_F = 1.00, 0.45      # orbit: per-frame hold / crossfade
XFADE_B_D, XFADE_B_F = 0.85, 0.45  # push-in
HOLD_RAMP = 16 / FPS               # each ramp step held 16 output frames
HOLD_HELD = 16 / FPS               # each "hold" frame
HOLD_HEAL = 12 / FPS               # each heal frame
HOLD_KNEE = 18 / FPS
END_CARD_S = 3.6

ACCENT = (255, 106, 61)            # awake pressure (the game page's accent)
INK = (232, 230, 226)
DIM = (140, 142, 148)

FONT_DIR = Path("C:/Windows/Fonts")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(FONT_DIR / name), size)
    except OSError:
        return ImageFont.load_default()


F_TITLE = font("arialbd.ttf", 150)
F_TAG = font("arial.ttf", 46)
F_SMALL = font("arialbd.ttf", 26)
F_TINY = font("arial.ttf", 20)
F_MONO = font("consola.ttf", 24)
F_MONO_SM = font("consola.ttf", 20)
F_LABEL = font("arialbd.ttf", 27)


# ---------------------------------------------------------------- engine HTTP
def _with_retries(fn, tries: int = 8, wait: float = 10.0, what: str = ""):
    """The engine may be mid-restart (fleet shares the slot): back off and retry."""
    last = None
    for k in range(tries):
        try:
            return fn()
        except Exception as e:
            last = e
            if k < tries - 1:
                print(f"  [retry {k + 1}/{tries}] {what}: {e} — waiting {wait:.0f}s", flush=True)
                time.sleep(wait)
    raise RuntimeError(f"{what} failed after {tries} tries: {last}")


def post(path: str, body: dict, timeout: float = 20.0) -> dict:
    def go():
        req = urllib.request.Request(
            ENGINE + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    return _with_retries(go, what=f"POST {path}")


def get_state() -> dict:
    def go():
        with urllib.request.urlopen(ENGINE + "/tick_state", timeout=15) as r:
            return json.loads(r.read().decode())
    return _with_retries(go, what="GET /tick_state")


def set_cam(v: list) -> None:
    """Bookmark the exact 8-float camera and recall it (save+recall = set)."""
    r = post("/cameras", {"op": "save", "name": SCRAP_BOOKMARK, "v": [float(x) for x in v]})
    if not r.get("ok"):
        raise RuntimeError(f"camera save failed: {r}")
    r = post("/cameras", {"op": "recall", "name": SCRAP_BOOKMARK})
    if not r.get("ok"):
        raise RuntimeError(f"camera recall failed: {r}")


def lerp_cam(a: list, b: list, t: float) -> list:
    return [x + (y - x) * t for x, y in zip(a, b)]


def grab(path: Path) -> None:
    """One real engine render (native 2560x1440) -> PNG on disk, with retries."""
    url = f"{ENGINE}/frame"

    def go():
        urllib.request.urlretrieve(url, path)
    _with_retries(go, tries=8, wait=10.0, what="GET /frame")


# ---------------------------------------------------------------------- HUD
def fmt3(x) -> str:
    x = float(x)
    if x != x or x in (float("inf"), float("-inf")):
        x = 0.0
    return f"{x:.3f}"


def draw_hud(img: Image.Image, st: dict, label: str, force_n: int | None,
             heal: bool = False) -> None:
    """Blood panel + dimple + scene label, drawn over the capture."""
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")

    # top-left scene label on a soft bar
    lb = f" {label} "
    tw = d.textlength(lb, font=F_LABEL)
    d.rounded_rectangle([28, 26, 28 + tw + 28, 26 + 46], 10, fill=(8, 10, 14, 165))
    d.text((28 + 14, 26 + 8), label, font=F_LABEL, fill=INK)

    # top-right watermark
    wm = "CHIMERA ENGINE 127.0.0.1:8107 · LIVE CAPTURE"
    tw = d.textlength(wm, font=F_MONO_SM)
    d.text((W - tw - 30, 34), wm, font=F_MONO_SM, fill=DIM)

    # bottom-left: THE CREATURE'S BLOOD — same fields the :8206 page renders
    cells = st.get("cells") or []
    lines = [("THE CREATURE'S BLOOD", ACCENT)]
    for i, c in enumerate(cells):
        p = float(c.get("P") or 0.0)
        awake = abs(p) >= 2e5
        lines.append((f"cell {i}: V={fmt3(c.get('V'))} m3  P={fmt3(p / 1e6)} MPa",
                      ACCENT if awake else INK))
    if st.get("conserve_pct") is not None:
        lines.append((f"conserve: {float(st['conserve_pct']):.2f} %", DIM))
    dim = float(st.get("dimple_m") or 0.0)
    lines.append((f"dimple: {dim:.3f} m", ACCENT if dim > 0.005 else DIM))
    if force_n:
        lines.append((f"press: {force_n:,} N", INK))
    if heal:
        lines.append(("healing  ·  tau = 0.5 s", DIM))

    pad, lh, x0 = 16, 30, 28
    y0 = H - 20 - (len(lines) * lh + 2 * pad)
    widest = max(d.textlength(t, font=F_MONO if i else F_SMALL) for i, (t, _) in enumerate(lines))
    d.rounded_rectangle([x0 - 8, y0 - 4, x0 + widest + 2 * pad, y0 + len(lines) * lh + 2 * pad + 4],
                        10, fill=(8, 10, 14, 175))
    for i, (t, col) in enumerate(lines):
        yy = y0 + i * lh
        f = F_SMALL if i == 0 else F_MONO
        d.text((x0 + pad, yy), t, font=f, fill=col)


def make_end_card(src_png: Path, out_png: Path) -> None:
    """Darkened real capture + title. The background is a genuine engine frame."""
    img = Image.open(src_png).convert("RGB")
    img = ImageEnhance.Brightness(img).enhance(0.32)
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")

    # vignette
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, 70))

    title, tracking = "CHIMERA", 18
    widths = [d.textlength(ch, font=F_TITLE) for ch in title]
    tw = sum(widths) + tracking * (len(title) - 1)
    x = (W - tw) / 2
    y = H * 0.40
    for ch, w in zip(title, widths):
        d.text((x + 3, y + 3), ch, font=F_TITLE, fill=(0, 0, 0, 200))
        d.text((x, y), ch, font=F_TITLE, fill=INK)
        x += w + tracking

    tag = "touch the living physics"
    tw = d.textlength(tag, font=F_TAG)
    d.text(((W - tw) / 2, y + 190), tag, font=F_TAG, fill=(210, 206, 200))

    sub = "real-time soft-body  ·  sealed fluid cells  ·  30 kN press  ·  0.5 s healing"
    tw = d.textlength(sub, font=F_SMALL)
    d.text(((W - tw) / 2, y + 270), sub, font=F_SMALL, fill=ACCENT)

    note = ("captured live from the running engine at ~1 fps  ·  time-remapped to 24 fps  ·  "
            "every frame is a real render, nothing interpolated")
    tw = d.textlength(note, font=F_TINY)
    d.text(((W - tw) / 2, H - 64), note, font=F_TINY, fill=DIM)

    img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
    img.save(out_png)


# ------------------------------------------------------------------- capture
def lerp(a, b, t):
    return a + (b - a) * t


def capture_beat(name: str, cams, label: str, fn=None, settle: float = 0.9) -> list:
    """cams: list of camera v[8]; fn(i) performs the beat action BEFORE frame i.

    The state is polled BEFORE the ~1.7 s full-frame grab: the engine composes the
    PNG at request time, so the HUD numbers must be the numbers of that moment,
    not of the moment the download finishes."""
    out = []
    for i, cam in enumerate(cams):
        if fn:
            fn(i)
        set_cam(cam)
        time.sleep(max(0.0, settle - 0.05))
        st = get_state()                      # state at the frame's composition
        png = FRAMES / f"{name}_{i:02d}.png"
        grab(png)
        force = fn.force_n if fn is not None and hasattr(fn, "force_n") else None
        heal = getattr(fn, "heal", False) if fn is not None else False
        img = Image.open(png).convert("RGB")
        draw_hud(img, st, label, force, heal)
        img.save(png)
        out.append(png)
        print(f"  [{name}] {i + 1}/{len(cams)}  dimple={st.get('dimple_m', 0):.4f} m  "
              f"P_up={st.get('P_upper', 0) / 1e6:.3f} MPa", flush=True)
    return out


def run_capture() -> dict:
    FRAMES.mkdir(parents=True, exist_ok=True)
    segs = {}

    print("warming up /frame ...", flush=True)
    set_cam([15.5, -1.90, 0.28, 0.0, 4.2, 0.0, 0, 0])   # end-card 3/4 front, clean (no HUD)
    time.sleep(0.4)
    t0 = time.time()
    grab(FRAMES / "warmup.png")
    warm = Image.open(FRAMES / "warmup.png")
    print(f"  warmup frame {warm.size} in {time.time() - t0:.2f}s", flush=True)

    # 01 orbit — camera only, creature untouched
    n = 12
    print("01 orbit establishing shot", flush=True)
    segs["A"] = capture_beat(
        "A_orbit",
        [lerp_cam(CAM_ORBIT_A, CAM_ORBIT_B, i / (n - 1)) for i in range(n)],
        "01 · ESTABLISHING — THE SPECIMEN",
    )

    # 02 push-in to the belly
    n = 5
    print("02 push-in to the belly", flush=True)
    segs["B"] = capture_beat(
        "B_push",
        [lerp_cam(CAM_ORBIT_B, CAM_PRESS, i / (n - 1)) for i in range(n)],
        "02 · THE HOOK — PRESS AND ANSWER",
    )

    # 03 press ramp — force steps up, the dimple forms on camera
    print("03 belly press ramp", flush=True)
    def ramp(i):
        post("/tick_touch", {"hit": BELLY_HIT, "force_n": RAMP_FORCES[i]})
        ramp.force_n = RAMP_FORCES[i]
    ramp.force_n = 0
    segs["C"] = capture_beat(
        "C_ramp",
        [list(CAM_PRESS)] * len(RAMP_FORCES),
        "03 · 30,000 N BELLY PRESS",
        fn=ramp, settle=1.0,
    )

    # 03b held — force stays on, the dent holds
    print("03b press held", flush=True)
    def held(i):
        held.force_n = 30000
    held.force_n = 30000
    segs["D"] = capture_beat(
        "D_held",
        [list(CAM_PRESS)] * 4,
        "03 · 30,000 N HELD",
        fn=held, settle=1.0,
    )

    # 04 release — the tau = 0.5 s healing, STROBOSCOPIC. The transient is done in
    # ~2 s of wall time — faster than one full-frame grab — but it is DETERMINISTIC:
    # the same 30 kN press re-reaches the same 0.4513 m dimple every time (measured).
    # So we press/release 8 times, waiting a different delay after each clear; each
    # frame is one REAL engine state of the decay, sampled at its own delay:
    # 0.4513 * exp(-delay / 0.5).
    print("04 release / heal (stroboscopic over repeated identical releases)", flush=True)
    heal_delays = [0.10, 0.30, 0.50, 0.70, 0.95, 1.20, 1.50, 1.90]
    def healing(i):
        post("/tick_touch", {"hit": BELLY_HIT, "force_n": 30000})
        time.sleep(0.8)                      # settle to the full 0.4513 m dimple
        post("/tick_touch_clear", {})
        time.sleep(heal_delays[i])           # sample the decay here
        healing.force_n = None
        healing.heal = True
    healing.force_n = None
    healing.heal = True
    segs["E"] = capture_beat(
        "E_heal",
        [list(CAM_PRESS)] * len(heal_delays),
        "04 · RELEASE — TAU = 0.5 S HEALING",
        fn=healing, settle=0.05,             # the delay already elapsed inside fn
    )

    # 05 knee pose 40 deg
    print("05 knee pose", flush=True)
    post("/tick_pose", {"joint_index": KNEE_JOINT, "deg": KNEE_DEG})
    segs["F"] = capture_beat(
        "F_knee",
        [list(CAM_LEGS)] * 4,
        "05 · ANSWER — KNEE FLEX 40°",
        settle=0.8,
    )
    post("/tick_pose", {"joint_index": KNEE_JOINT, "deg": 0})   # restore

    # 06 end card — darkened real capture (the clean warmup frame)
    print("06 end card", flush=True)
    make_end_card(FRAMES / "warmup.png", FRAMES / "G_end.png")
    segs["G"] = [FRAMES / "G_end.png"]

    return segs


# -------------------------------------------------------------------- encode
SCALE = (f"scale={OUT_W}:{OUT_H}:flags=lanczos,format=yuv420p,setsar=1")


def enc_xfade(pngs: list, d: float, f: float, out: Path) -> None:
    """Chain short crossfades — the 1 fps camera move reads as a slow continuum."""
    n = len(pngs)
    args = ["ffmpeg", "-y"]
    for p in pngs:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", str(p)]
    fc = []
    for k in range(n):
        fc.append(f"[{k}:v]{SCALE}[p{k}]")
    prev = "p0"
    for k in range(1, n):
        offset = k * (d - f)
        lbl = f"x{k}" if k < n - 1 else "v"
        fc.append(f"[{prev}][p{k}]xfade=transition=fade:duration={f:.3f}:offset={offset:.3f}[{lbl}]")
        prev = lbl
    args += ["-filter_complex", ";".join(fc), "-map", "[v]", "-r", str(FPS),
             "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-pix_fmt", "yuv420p", str(out)]
    subprocess.run(args, check=True, capture_output=True)


def enc_hold(entries: list, out: Path) -> None:
    """entries: [(png, seconds)] — each real frame held exactly on the 24 fps grid.
    Uses the concat FILTER (not the concat demuxer): the demuxer pads the tail and
    silently stretched an earlier build from 28 s to 34 s."""
    n = len(entries)
    args = ["ffmpeg", "-y"]
    for p, dur in entries:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.4f}", "-i", str(p)]
    fc = [f"[{k}:v]{SCALE}[h{k}]" for k in range(n)]
    fc.append("".join(f"[h{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[v]")
    args += ["-filter_complex", ";".join(fc), "-map", "[v]", "-r", str(FPS),
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", str(out)]
    subprocess.run(args, check=True, capture_output=True)


def xfade_len(n: int, d: float, f: float) -> float:
    return n * d - (n - 1) * f


def build_movie(segs: dict, out_mp4: Path) -> float:
    BUILD.mkdir(parents=True, exist_ok=True)
    parts = {}

    parts["A"] = xfade_len(len(segs["A"]), XFADE_D, XFADE_F)
    enc_xfade(segs["A"], XFADE_D, XFADE_F, BUILD / "A.mp4")

    parts["B"] = xfade_len(len(segs["B"]), XFADE_B_D, XFADE_B_F)
    enc_xfade(segs["B"], XFADE_B_D, XFADE_B_F, BUILD / "B.mp4")

    parts["C"] = len(segs["C"]) * HOLD_RAMP
    enc_hold([(p, HOLD_RAMP) for p in segs["C"]], BUILD / "C.mp4")

    parts["D"] = len(segs["D"]) * HOLD_HELD
    enc_hold([(p, HOLD_HELD) for p in segs["D"]], BUILD / "D.mp4")

    parts["E"] = len(segs["E"]) * HOLD_HEAL
    enc_hold([(p, HOLD_HEAL) for p in segs["E"]], BUILD / "E.mp4")

    parts["F"] = len(segs["F"]) * HOLD_KNEE
    enc_hold([(p, HOLD_KNEE) for p in segs["F"]], BUILD / "F.mp4")

    parts["G"] = END_CARD_S
    enc_hold([(segs["G"][0], END_CARD_S)], BUILD / "G.mp4")

    total = sum(parts.values())
    lst = BUILD / "concat.txt"
    with open(lst, "w") as f:
        for k in "ABCDEFG":
            f.write(f"file '{(BUILD / (k + '.mp4')).as_posix()}'\n")

    fade_out_start = max(0.0, total - 0.7)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-vf", (f"fade=t=in:st=0:d=0.5,fade=t=out:st={fade_out_start:.3f}:d=0.7,"
                 f"format=yuv420p"),
         "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-movflags", "+faststart", str(out_mp4)],
        check=True, capture_output=True,
    )
    return total


# ---------------------------------------------------------------------- main
def restore_engine() -> None:
    """Leave the engine as we found it: no touch, pose 0, wide bookmark."""
    for act in (lambda: post("/tick_touch_clear", {}),
                lambda: post("/tick_pose", {"joint_index": KNEE_JOINT, "deg": 0}),
                lambda: post("/cameras", {"op": "recall", "name": "wide"})):
        try:
            act()
        except Exception as e:
            print(f"  restore step failed (non-fatal): {e}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="R7 spine: the press-and-answer trailer")
    ap.add_argument("--out", default=r"C:\Users\allen\Desktop\CHIMERA_PROOF\TRAILER\chimera_trailer.mp4")
    ap.add_argument("--keep-frames", action="store_true")
    ap.add_argument("--no-capture", action="store_true",
                    help="reuse existing .frames and only re-encode")
    a = ap.parse_args()

    out_mp4 = Path(a.out)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    if not a.no_capture:
        try:
            segs = run_capture()
        except Exception:
            restore_engine()
            raise
    else:
        segs = {
            "A": sorted(FRAMES.glob("A_orbit_*.png")),
            "B": sorted(FRAMES.glob("B_push_*.png")),
            "C": sorted(FRAMES.glob("C_ramp_*.png")),
            "D": sorted(FRAMES.glob("D_held_*.png")),
            "E": sorted(FRAMES.glob("E_heal_*.png")),
            "F": sorted(FRAMES.glob("F_knee_*.png")),
            "G": [FRAMES / "G_end.png"],
        }

    print("encoding ...", flush=True)
    total = build_movie(segs, out_mp4)
    restore_engine()

    if not a.keep_frames:
        shutil.rmtree(FRAMES, ignore_errors=True)
        shutil.rmtree(BUILD, ignore_errors=True)

    sz = out_mp4.stat().st_size / 1e6
    print(f"DONE {out_mp4}")
    print(f"  duration ~{total:.2f} s  size {sz:.1f} MB  method: ~1 fps live captures, "
          f"time-remapped to {FPS} fps (held frames + short crossfades, no interpolation)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
