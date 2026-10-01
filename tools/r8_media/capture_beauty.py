"""capture_beauty.py -- D2 R8 MEDIA: beauty shots of the live creature.

Mirrors tools/trailer/make_trailer.py's HTTP + PIL helpers (the same
_with_retries discipline -- the engine is shared, a failed request waits 10 s
and retries). Frames the sealed creature through its real camera surface:
POST /cameras {"op":"save","name":...,"v":[8]} + {"op":"recall"} = an exact
8-float bookmark, then GET /frame = one genuine engine render.

Two phases, because the pick is a JUDGMENT, not a formula:

    python tools/r8_media/capture_beauty.py --capture   # 6 candidates -> cand_*.png
    python tools/r8_media/capture_beauty.py --pick 0,2,4  # vision's choice -> beauty_NN.png

Candidates: r 9-14, phi 0.10-0.25, target (0, 4, 0) (the torso), thetas across
both 3/4 fronts plus a close side. The pick agent looks at all six and chooses
the three that answer the "prototype-look" defect -- shots where the creature
reads as a living specimen, not a tech demo.

Restore (both phases): touch clear, knee pose 0, recall the 'wide' bookmark.
Output: C:/Users/allen/Desktop/CHIMERA_PROOF/R8_MEDIA/
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

from PIL import Image

ENGINE = "http://127.0.0.1:8107"
OUT = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\R8_MEDIA")
BOOKMARK = "d2_media"
KNEE_JOINT = 15          # knee_L, per tools/mitosis_run.py and lessons.json

# v[8] = [r, theta, phi, target_x, target_y, target_z, pan_x, pan_y]
# thetas MEASURED from the first probe round (cand_* round 1): the face fronts
# theta ~ -2.6..-3.3 (the trailer's "dead on the hit" flank); -1.45/+1.45 are
# SIDE profiles, not 3/4 fronts. r >= 13 keeps the head in frame at phi 0.2.
CANDIDATES = [
    ("front34_a",   [14.0, -2.60, 0.25, 0, 4, 0, 0, 0]),   # front 3/4, full body
    ("front34_b",   [14.0,  2.60, 0.25, 0, 4, 0, 0, 0]),   # front 3/4, mirrored
    ("front_sym",   [14.0, -3.30, 0.20, 0, 4, 0, 0, 0]),   # near-frontal, wide
    ("front_soft",  [13.0, -2.95, 0.22, 0, 4, 0, 0, 0]),   # gentle 3/4, closer
    ("side_close",  [9.0,  -1.45, 0.18, 0, 4, 0, 0, 0]),   # close true-side profile
    ("back34",      [14.0, -1.90, 0.25, 0, 4, 0, 0, 0]),   # back 3/4, full body
]


# ---------------------------------------------------------------- engine HTTP
def _with_retries(fn, tries: int = 8, wait: float = 10.0, what: str = ""):
    """The engine may be mid-restart or busy (fleet shares the slot): back off."""
    last = None
    for k in range(tries):
        try:
            return fn()
        except Exception as e:
            last = e
            if k < tries - 1:
                print(f"  [retry {k + 1}/{tries}] {what}: {e} -- waiting {wait:.0f}s", flush=True)
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


def set_cam(v: list) -> None:
    """Bookmark the exact 8-float camera and recall it (save+recall = set)."""
    r = post("/cameras", {"op": "save", "name": BOOKMARK, "v": [float(x) for x in v]})
    if not r.get("ok"):
        raise RuntimeError(f"camera save failed: {r}")
    r = post("/cameras", {"op": "recall", "name": BOOKMARK})
    if not r.get("ok"):
        raise RuntimeError(f"camera recall failed: {r}")


def grab(path: Path) -> None:
    """One real engine render (native resolution) -> PNG on disk, with retries."""
    def go():
        urllib.request.urlretrieve(ENGINE + "/frame", path)
    _with_retries(go, tries=8, wait=10.0, what="GET /frame")


def restore_engine() -> None:
    """Leave the engine as we found it: no touch, knee 0, the wide bookmark."""
    for act in (lambda: post("/tick_touch_clear", {}),
                lambda: post("/tick_pose", {"joint_index": KNEE_JOINT, "deg": 0}),
                lambda: post("/cameras", {"op": "recall", "name": "wide"})):
        try:
            act()
        except Exception as e:
            print(f"  restore step failed (non-fatal): {e}", flush=True)


# ------------------------------------------------------------------- phases
def capture() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # the beauty shot is of the CREATURE AT REST -- no press held, no pose bent
    post("/tick_touch_clear", {})
    for i, (name, v) in enumerate(CANDIDATES):
        set_cam(v)
        time.sleep(0.9)                    # the recall lands on the render thread
        png = OUT / f"cand_{i}_{name}.png"
        grab(png)
        img = Image.open(png)
        print(f"  [{i}] {name}: cam={v} -> {png.name} {img.size[0]}x{img.size[1]}", flush=True)
    restore_engine()
    print("capture done -- inspect cand_*.png and pick three.")


def finalize(picks: str) -> None:
    idx = [int(s) for s in picks.split(",")]
    if len(idx) != 3:
        raise SystemExit("--pick needs exactly three candidate indexes")
    for slot, i in enumerate(idx, start=1):
        src = next(OUT.glob(f"cand_{i}_*.png"))
        img = Image.open(src).convert("RGB")
        # center-crop to 16:9 (no-op when the engine already yields 16:9), then
        # Lanczos down to 1920x1080
        w, h = img.size
        target = 16 / 9
        if abs(w / h - target) > 1e-3:
            if w / h > target:             # too wide -> trim the sides
                nw = int(round(h * target))
                x0 = (w - nw) // 2
                img = img.crop((x0, 0, x0 + nw, h))
            else:                          # too tall -> trim top/bottom evenly
                nh = int(round(w / target))
                y0 = (h - nh) // 2
                img = img.crop((0, y0, w, y0 + nh))
        img = img.resize((1920, 1080), Image.LANCZOS)
        dst = OUT / f"beauty_{slot:02d}.png"
        img.save(dst)
        print(f"  beauty_{slot:02d}.png <- {src.name}")
    restore_engine()
    print("finalize done.")


def main() -> int:
    ap = argparse.ArgumentParser(description="D2 R8 MEDIA: beauty shots")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--capture", action="store_true", help="grab the 6 candidates")
    g.add_argument("--pick", metavar="I,J,K", help="finalize three chosen candidates")
    a = ap.parse_args()
    try:
        if a.capture:
            capture()
        else:
            finalize(a.pick)
    except Exception:
        restore_engine()
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
