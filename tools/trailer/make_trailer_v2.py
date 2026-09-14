"""make_trailer_v2.py — G10: the trailer v2, REAL-TIME — the answer to the judges.

Round 1 (make_trailer.py) captured the engine at ~1 fps and time-remapped the
frames onto a 24 fps timeline. The judges' verdict: that "leaves responsiveness
unproven." V2 removes every remap:

  1. CAPTURE  tools/trailer/capture_v2.js opens the game page (127.0.0.1:8206)
     in HEADED Chrome, drives a genuine press through the page's own rail
     (SPACE -> the page POSTs /api/touch_hit {hit, force_n}; ESCAPE ->
     /api/touch_clear) and samples the WebGL canvas in-page at ~24 fps
     (a rAF callback chained after the page's frame() calls canvas.toDataURL
     inside the same rendering opportunity). Every frame is a real
     browser-rendered frame with a real wall-clock timestamp.
  2. ENCODE   each captured frame is shown for EXACTLY the interval at which it
     was captured (ffconcat per-frame durations -> libx264). The video's clock
     IS the wall clock of the take. Nothing is held, crossfaded, or warped.
  3. PROVE    a frame-by-frame diff (PIL) of every consecutive pair, plus the
     per-frame capture interval, goes to diff_report.json + v2_frame_diff.png:
     the motion is smooth — no frame interval anywhere near 1 s and no
     static run >= 1 s anywhere in the take.

The engine at :8107 is never built, stopped, or reconfigured. The take's only
engine traffic is the touch press and its clear; afterwards this script waits
for the creature to be calm again, so it is left exactly as it was found.

Usage:
    python tools/trailer/make_trailer_v2.py                # capture+encode+prove
    python tools/trailer/make_trailer_v2.py --skip-capture # re-encode only
    python tools/trailer/make_trailer_v2.py --clean-frames # delete JPGs after
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

ROOT = Path(__file__).resolve().parents[2]
CAPDIR = Path(__file__).resolve().parent / ".frames_v2"      # capture workspace
CAP_JS = Path(__file__).resolve().parent / "capture_v2.js"

GAME = "http://127.0.0.1:8206"
OUT_W, OUT_H = 1920, 1080
CONTAINER_FPS = 24

DEFAULT_OUT = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\TRAILER\V2")

# diff thresholds: a frame is "static" only if essentially nothing changed
STATIC_MEANDIFF = 0.20          # mean |delta| on 0..255, 480x270 thumb
STATIC_CHGFRAC = 0.004          # fraction of pixels with |delta| > 8

ACCENT = (255, 106, 61)
INK = (32, 34, 38)
DIM = (110, 114, 120)
GOOD = (34, 120, 70)


def font(name: str, size: int):
    try:
        return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)
    except OSError:
        return ImageFont.load_default()


F_HEAD = font("consolab.ttf", 26)
F_LBL = font("consola.ttf", 19)
F_SM = font("consola.ttf", 15)

# ----------------------------------------------------------------- 1 capture
def run_capture() -> None:
    CAPDIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(CAPDIR / "frames", ignore_errors=True)
    print("== 1. CAPTURE — headed Chrome, real-time canvas samples ==", flush=True)
    r = subprocess.run(["node", str(CAP_JS), str(CAPDIR), GAME])
    if r.returncode != 0:
        raise RuntimeError(f"capture_v2.js exited {r.returncode} — see log above")


def load_timeline() -> dict:
    return json.loads((CAPDIR / "timeline.json").read_text())


def guard_blank_frames(tl: dict) -> dict:
    """The pixel-real check the JS probe cannot do: a sampled frame must not be
    one flat color (a cleared/blank WebGL buffer would be exactly that)."""
    checks = {}
    for frac in (0.0, 0.5):
        i = min(int(frac * (len(tl["frames"]) - 1)), len(tl["frames"]) - 1)
        p = CAPDIR / "frames" / f"frame_{i:05d}.jpg"
        im = Image.open(p).convert("L").resize((320, 180), Image.BILINEAR)
        colors = im.getcolors(maxcolors=65536)
        ncol = len(colors) if colors else 65536
        lo, hi = im.getextrema()
        checks[str(i)] = {"distinct_grays": ncol, "extrema": [lo, hi]}
        if ncol < 8:
            raise RuntimeError(f"frame {i} looks BLANK ({ncol} distinct grays) — "
                               f"the sampler captured an empty buffer")
    return checks


# ----------------------------------------------------------------- 2 encode
def build_concat(entries: list[tuple[Path, float]], lst: Path) -> None:
    """ffconcat with per-frame wall-clock durations: the encode's clock is the
    take's clock. The final file is repeated bare (concat-demuxer tail quirk)."""
    with open(lst, "w") as f:
        f.write("ffconcat version 1.0\n")
        for p, dur in entries:
            f.write(f"file '{p.as_posix()}'\nduration {dur:.5f}\n")
        f.write(f"file '{entries[-1][0].as_posix()}'\n")


def encode(tl: dict, out_mp4: Path) -> float:
    frames = sorted((CAPDIR / "frames").glob("frame_*.jpg"))
    t = [f["t_s"] for f in tl["frames"]]
    if len(frames) != len(t):
        raise RuntimeError(f"{len(frames)} jpgs but {len(t)} timeline entries")
    dts = [t[i + 1] - t[i] for i in range(len(t) - 1)]
    med = statistics.median(dts)
    durs = dts + [med]                                   # last frame shows ~one median tick
    lst = CAPDIR / "concat.txt"
    build_concat(list(zip(frames, durs)), lst)

    vf = "format=yuv420p,setsar=1"
    if (tl.get("canvas", {}).get("w"), tl.get("canvas", {}).get("h")) != (OUT_W, OUT_H):
        vf = f"scale={OUT_W}:{OUT_H}:flags=lanczos," + vf
    print("== 2. ENCODE — wall-clock-true concat -> H.264 1080p ==", flush=True)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-vf", vf, "-r", str(CONTAINER_FPS), "-c:v", "libx264",
         "-preset", "medium", "-crf", "18", "-movflags", "+faststart", str(out_mp4)],
        check=True, capture_output=True)
    return t[-1] + durs[-1]


def ffprobe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name,width,height,avg_frame_rate",
         "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True, capture_output=True, text=True)
    j = json.loads(r.stdout)
    st = j["streams"][0]
    return {"codec": st["codec_name"], "w": st["width"], "h": st["height"],
            "container_fps": st.get("avg_frame_rate"), "duration_s": float(j["format"]["duration"])}


# ------------------------------------------------------------- 3 prove (diff)
def analyze(tl: dict) -> dict:
    print("== 3. PROVE — frame-by-frame diff of every consecutive pair ==", flush=True)
    frames = sorted((CAPDIR / "frames").glob("frame_*.jpg"))
    t = [f["t_s"] for f in tl["frames"]]
    n = len(frames)
    dts = [t[i + 1] - t[i] for i in range(n - 1)]

    TH_W, TH_H = 480, 270
    meandiff, chgfrac = [], []
    npix = TH_W * TH_H
    prev = None
    for p in frames:
        im = Image.open(p).convert("L").resize((TH_W, TH_H), Image.BILINEAR)
        if prev is not None:
            diff = ImageChops.difference(prev, im)
            meandiff.append(ImageStat.Stat(diff).mean[0])
            chgfrac.append(sum(diff.histogram()[9:]) / npix)   # pixels with |d| > 8
        prev = im

    static = [(m < STATIC_MEANDIFF and c < STATIC_CHGFRAC) for m, c in zip(meandiff, chgfrac)]

    # longest static RUN (consecutive static frames) in wall time
    best_len, best_i, cur_len, cur_i = 0, 0, 0, 0
    for i, s in enumerate(static):
        if s:
            if cur_len == 0:
                cur_i = i
            cur_len += 1
            if cur_len > best_len:
                best_len, best_i = cur_len, cur_i
        else:
            cur_len = 0
    med_dt = statistics.median(dts) if dts else 0.0
    longest_static_s = (t[best_i + best_len] - t[best_i] + med_dt) if best_len else 0.0

    inst_fps = [1.0 / d for d in dts if d > 0]
    rep = {
        "frame_count": n,
        "footage_wall_s": round(t[-1] + med_dt, 3),
        "max_frame_interval_s": round(max(dts), 4),
        "mean_interval_ms": round(1000 * sum(dts) / len(dts), 2),
        "instant_fps_min": round(min(inst_fps), 2),
        "instant_fps_median": round(statistics.median(inst_fps), 2),
        "instant_fps_max": round(max(inst_fps), 2),
        "mean_fps_over_take": round((n - 1) / (t[-1] - t[0]), 2),
        "static_frame_count": sum(static),
        "longest_static_run_frames": best_len,
        "longest_static_run_s": round(longest_static_s, 3),
        "longest_static_run_at_s": round(t[best_i], 2) if best_len else None,
        "diff_thresholds": {"static_meandiff_lt": STATIC_MEANDIFF,
                            "static_chgfrac_lt": STATIC_CHGFRAC,
                            "thumb": "480x270 grayscale"},
        "per_frame": [{"i": i, "t_s": round(t[i], 4), "dt_s": round(dts[i], 4) if i < len(dts) else None,
                       "meandiff": round(meandiff[i], 3), "chgfrac": round(chgfrac[i], 5),
                       "static": static[i]} for i in range(n - 1)],
    }
    rep["verdict_smooth"] = bool(rep["max_frame_interval_s"] < 0.5
                                 and rep["longest_static_run_s"] < 1.0)
    return rep


def chart(rep: dict, tl: dict, out_png: Path) -> None:
    W, H = 1680, 780
    img = Image.new("RGB", (W, H), (246, 245, 242))
    d = ImageDraw.Draw(img)
    pf = rep["per_frame"]
    n = len(pf)
    if not n:
        return
    x0, x1, ytop = 90, W - 40, 96
    t_end = pf[-1]["t_s"]

    def X(t):
        return x0 + (x1 - x0) * t / t_end

    # phase bands
    bands = []
    ph = tl.get("phases_s", {})
    if "press_key" in ph:
        bands.append((0.0, ph["press_key"], "REST + ORBIT", (226, 236, 232)))
        bands.append((ph["press_key"], ph["release_key"], "PRESS + HOLD", (247, 231, 219)))
        bands.append((ph["release_key"], ph.get("orbit2_start", ph["healed"]), "RELEASE + HEAL", (224, 236, 247)))
        bands.append((ph.get("orbit2_start", ph["healed"]), t_end, "TAIL ORBIT", (236, 232, 244)))
    for a, b, lbl, col in bands:
        d.rectangle([X(a), ytop, X(b), H - 46], fill=col)
        d.text((X(a) + 8, ytop - 24), lbl, font=F_LBL, fill=DIM)

    # panel A: frame interval
    d.text((x0, 18), "A — capture interval per frame (ms). A 1 s hold would sit at the red line.",
           font=F_HEAD, fill=INK)
    spanA, yA0, yA1 = 200.0, 96, 330          # 0..200 ms axis
    for gy in (0, 50, 100, 150, 200):
        yy = yA1 - (yA1 - yA0) * gy / spanA
        d.line([x0, yy, x1, yy], fill=(224, 223, 219))
        d.text((30, yy - 8), f"{gy}", font=F_SM, fill=DIM)
    for i, e in enumerate(pf):
        yy = yA1 - (yA1 - yA0) * min(e["dt_s"] * 1000, spanA) / spanA
        d.point([X(e["t_s"]), yy], fill=ACCENT)
        d.line([X(e["t_s"]), yy, X(e["t_s"]), yy + 1], fill=ACCENT, width=2)
    y1s = yA1 - (yA1 - yA0) * min(1000, spanA) / spanA
    d.line([x0, y1s, x1, y1s], fill=(200, 40, 40), width=3)
    d.text((x1 - 330, y1s - 22), "1000 ms — a >1 s hold would be HERE", font=F_LBL, fill=(200, 40, 40))

    # panel B: inter-frame diff
    d.text((x0, 386), "B — mean |frame[i] - frame[i-1]| (0..255). Zero would mean a still picture.",
           font=F_HEAD, fill=INK)
    yB0, yB1 = 470, 700
    spanB = 8.0
    for gy in (0, 2, 4, 6, 8):
        yy = yB1 - (yB1 - yB0) * gy / spanB
        d.line([x0, yy, x1, yy], fill=(224, 223, 219))
        d.text((30, yy - 8), f"{gy:.0f}", font=F_SM, fill=DIM)
    ys = yB1 - (yB1 - yB0) * min(spanB, STATIC_MEANDIFF) / spanB
    d.line([x0, ys, x1, ys], fill=(150, 150, 155), width=2)
    d.text((x1 - 250, ys - 22), "static threshold", font=F_LBL, fill=DIM)
    for i, e in enumerate(pf):
        yy = yB1 - (yB1 - yB0) * min(e["meandiff"], spanB) / spanB
        d.point([X(e["t_s"]), yy], fill=INK)
        d.line([X(e["t_s"]), yy, X(e["t_s"]), yy + 1], fill=INK, width=2)

    # axis + footer
    d.line([x0, H - 46, x1, H - 46], fill=INK)
    for tt in range(0, int(t_end) + 1):
        d.line([X(tt), H - 46, X(tt), H - 40], fill=INK)
        d.text((X(tt) - 8, H - 34), f"{tt}s", font=F_SM, fill=DIM)

    verd = "SMOOTH — no >1 s holds, no static run >= 1 s" if rep["verdict_smooth"] \
        else "CHECK FAILED — see diff_report.json"
    d.text((x0, 728), verd, font=F_HEAD, fill=GOOD if rep["verdict_smooth"] else (180, 40, 40))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)


# ------------------------------------------------------------------ restore
def restore_calm() -> dict:
    """Leave the creature exactly as found: clear any lingering touch, wait for
    calm. v2 never sends camera or pose commands (the SPACE rail posts hit only)."""
    out = {"touch_clear_sent": False, "calm_after": None}
    try:
        req = urllib.request.Request(GAME + "/api/touch_clear",
                                     data=json.dumps({}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            out["touch_clear_sent"] = bool(json.loads(r.read().decode()).get("ok", True))
    except Exception as e:
        out["touch_clear_error"] = str(e)
    t0 = time.time()
    while time.time() - t0 < 20:
        try:
            with urllib.request.urlopen(GAME + "/api/state", timeout=10) as r:
                ps = [abs(float(c.get("P")) or 0.0) for c in json.loads(r.read().decode())["cells"]]
            if ps and all(p < 1000 for p in ps):
                out["calm_after"] = True
                break
        except Exception:
            pass
        time.sleep(0.4)
    else:
        out["calm_after"] = False
    return out


# ---------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="trailer v2: real-time browser capture")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--skip-capture", action="store_true", help="reuse existing .frames_v2")
    ap.add_argument("--clean-frames", action="store_true", help="delete capture JPGs after encode")
    a = ap.parse_args()

    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    out_mp4 = outdir / "v2_trailer.mp4"

    if not a.skip_capture:
        run_capture()
    tl = load_timeline()
    blank = guard_blank_frames(tl)

    wall = encode(tl, out_mp4)
    probe = ffprobe(out_mp4)

    rep = analyze(tl)
    rep["blank_frame_check"] = blank
    rep["output"] = str(out_mp4)
    rep["container"] = probe
    rep["method"] = {
        "capture": "headed Chrome (channel:'chrome') on the game page at 127.0.0.1:8206; "
                   "canvas sampled in-page by a rAF callback chained after the page's own "
                   "frame() — canvas.toDataURL in the same rendering opportunity, gated ~24 fps",
        "press": "real SPACE keydown — the page itself POSTs /api/touch_hit "
                 "{hit:[0.0,4.5,0.35], force_n:30000} (lesson 5 'THE WHOLE BODY' touch target); "
                 "real ESCAPE keydown POSTs /api/touch_clear",
        "encode": "ffconcat with per-frame wall-clock durations -> libx264 crf18, "
                  f"{CONTAINER_FPS} fps container; no holds, no crossfades, no interpolation",
        "engine_8107": "never built, stopped, or reconfigured; no /cameras or /tick_pose calls",
        "captured_at": tl.get("captured_at"),
        "lesson": tl.get("lesson"), "force": tl.get("force"),
        "player_name": tl.get("player_name"),
        "calm_before_take": tl.get("calm_before_take"),
        "press_registered": tl.get("pressed"),
        "healed": tl.get("healed"),
        "hold_dimple_m": tl.get("hold_dimple_m"),
        "capture_notes": tl.get("notes", []),
    }
    rep["restore_after_take"] = restore_calm()

    (outdir / "diff_report.json").write_text(json.dumps(rep, indent=1))
    chart(rep, tl, outdir / "v2_frame_diff.png")
    shutil.copyfile(CAPDIR / "timeline.json", outdir / "capture_timeline.json")

    if a.clean_frames:
        shutil.rmtree(CAPDIR / "frames", ignore_errors=True)

    ok = (probe["codec"] == "h264" and probe["w"] == OUT_W and probe["h"] == OUT_H
          and probe["duration_s"] >= 15.0 and rep["verdict_smooth"])
    print("", flush=True)
    print(f"DONE {out_mp4}")
    print(f"  ffprobe: {probe['codec']} {probe['w']}x{probe['h']} "
          f"duration {probe['duration_s']:.2f} s (wall footage {wall:.2f} s), "
          f"container {probe['container_fps']} fps")
    print(f"  capture: {rep['frame_count']} frames, mean {rep['mean_interval_ms']:.1f} ms/frame "
          f"(mean {rep['mean_fps_over_take']:.1f} fps, min {rep['instant_fps_min']}, "
          f"median {rep['instant_fps_median']}, max {rep['instant_fps_max']})")
    print(f"  smoothness: max frame interval {rep['max_frame_interval_s'] * 1000:.1f} ms; "
          f"longest static run {rep['longest_static_run_s']:.2f} s "
          f"({rep['longest_static_run_frames']} frames at t={rep['longest_static_run_at_s']} s) "
          f"-> verdict_smooth={rep['verdict_smooth']}")
    print(f"  engine restore: calm_after={rep['restore_after_take']['calm_after']}")
    print(f"  ACCEPTED" if ok else "  NOT ACCEPTED — fix the failing line above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
