"""make_art.py — R7 store art: capture the living creature, compose the store set.

WHAT
  1. CAPTURE  8 full-res frames (2560x1369) from the live engine (127.0.0.1:8107)
     across 8 varied cameras, including one MID-PRESS (tick_touch 30000 N held at
     the shutter) and one POSED KNEE (joint 15 at 40 deg). Every scratch camera
     bookmark is deleted and the operator's view restored afterwards.
  2. COMPOSE  from those captures, with PIL only:
       capsule_616x353.png / capsule_460x215.png  (CHIMERA in strong serif, gold
           rule, "touch the living physics" tagline, hero art full-bleed under a
           dark blue-grey scrim, bg #0b0d10)
       icon_512x512.png   (creature silhouette: warm-light mask -> dark bronze
           gradient body + gold rim + soft gold glow on #0b0d10)
       screenshot_01..06  (1920x1080 crops of 6 of the 8 captures, 16:9 crop
           window centered on the creature's bounding box)
       manifest.json      (every asset -> the exact capture + camera v it came from)

RE-RUN
  `python tools/store_art/make_art.py`              # capture + compose (creature changed)
  `python tools/store_art/make_art.py --compose-only`   # recompose from existing captures
  `python tools/store_art/make_art.py --capture-only`
  `--out DIR` retargets the output tree (default STORE_ART below).

DISCIPLINE
  Read-only to the engine except camera bookmarks (own `_sa2_*` scratch namespace,
  cleaned), two transient tissue ticks (`/tick_touch` cleared, `/tick_pose` returned
  to 0 immediately after their shutter). The engine is never stopped or rebuilt.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

# ---------------------------------------------------------------- constants
ENGINE = "http://127.0.0.1:8107"
OUT = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\STORE_ART")
CAPDIR = OUT / "captures"
SCRATCH = "_sa2_"          # this tool's bookmark namespace, always cleaned up

BG = (11, 13, 16)          # #0b0d10  dark blue-grey store background
GOLD = (212, 165, 55)      # accent rule / rim light
INK = (232, 236, 242)      # title
TAG = (168, 178, 192)      # tagline grey-blue

FONTS = r"C:\Windows\Fonts"
SERIF_B = FONTS + r"\georgiab.ttf"    # strong serif, ships with Windows
SERIF_I = FONTS + r"\georgiai.ttf"

# v = [r, theta, phi, tx, ty, tz, 0, 0]  (engine camera bookmark vector)
SHOTS = [
    #  name            v                                                       action
    ("hero",          [17.5,  0.00, 0.42, 0.0, 4.3, 0.0, 0.0, 0.0], None),
    ("quarter_left",  [18.0, -0.60, 0.45, 0.0, 4.2, 0.0, 0.0, 0.0], None),
    ("quarter_right", [18.0,  0.60, 0.45, 0.0, 4.2, 0.0, 0.0, 0.0], None),
    ("low_angle",     [11.0,  0.30, 0.14, 0.0, 5.4, 0.0, 0.0, 0.0], None),
    ("head_study",    [ 8.5, -0.35, 0.50, 0.0, 6.4, 0.0, 0.0, 0.0], None),
    ("wide_stage",    [25.0, -0.20, 0.35, 0.0, 4.0, 0.0, 0.0, 0.0], None),
    # mid-press: 30 kN held at the back while the shutter opens (camera faces
    # the press point: the creature's back is toward +z / theta 0)
    ("midpress",      [13.5,  0.18, 0.42, 0.0, 4.3, 0.0, 0.0, 0.0],
     ("touch", {"hit": [0.0, 4.5, 0.35], "force_n": 30000})),
    # posed knee: joint 15 bent 40 deg for the shutter, returned to 0 after
    ("posed_knee",    [17.0, -0.45, 0.40, 0.0, 4.2, 0.0, 0.0, 0.0],
     ("pose", {"joint_index": 15, "deg": 40})),
]

SCREENSHOT_PICKS = ["hero", "quarter_left", "low_angle", "head_study", "midpress", "posed_knee"]

# ---------------------------------------------------------------- engine io
def _post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        ENGINE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode(errors="replace"))


def _get_bytes(path: str) -> bytes:
    with urllib.request.urlopen(ENGINE + path, timeout=120) as r:
        return r.read()


def capture(outdir: Path = CAPDIR) -> list[dict]:
    """Shoot the 8 frames; return manifest records for them."""
    outdir.mkdir(parents=True, exist_ok=True)
    scratches = []
    records = []

    prev_name = SCRATCH + "prev"
    _post("/cameras", {"op": "save", "name": prev_name})   # operator's view
    scratches.append(prev_name)

    try:
        for i, (name, v, action) in enumerate(SHOTS, 1):
            bm = f"{SCRATCH}{i:02d}_{name}"
            r = _post("/cameras", {"op": "save", "name": bm, "v": list(v)})
            if not r.get("ok"):
                raise RuntimeError(f"bookmark save failed: {r}")
            scratches.append(bm)
            _post("/cameras", {"op": "recall", "name": bm})
            time.sleep(1.1)

            note = None
            if action:
                kind, payload = action
                if kind == "touch":
                    _post("/tick_touch", payload)
                    note = f"tick_touch {payload} held at shutter"
                    time.sleep(1.2)
                elif kind == "pose":
                    _post("/tick_pose", payload)
                    note = f"tick_pose {payload} held at shutter"
                    time.sleep(1.5)

            path = outdir / f"capture_{i:02d}_{name}.png"
            path.write_bytes(_get_bytes("/frame"))
            records.append({
                "file": path.name, "shot": name, "camera_v": v,
                "action": note, "engine": ENGINE,
            })
            print(f"  {path.name}  {path.stat().st_size/1e6:.1f} MB"
                  + (f"  [{note}]" if note else ""))

            if action:
                kind, payload = action
                if kind == "touch":
                    _post("/tick_touch_clear", {})
                    time.sleep(0.4)
                elif kind == "pose":   # return the joint before anything else
                    _post("/tick_pose", {**payload, "deg": 0})
                    time.sleep(1.5)
    finally:
        # hand the machine back: live camera first, then scratch cleanup
        try:
            _post("/cameras", {"op": "recall", "name": prev_name})
        except Exception:
            pass
        for bm in scratches:
            try:
                _post("/cameras", {"op": "delete", "name": bm})
            except Exception:
                pass
    return records


# ---------------------------------------------------------------- compose
def creature_bbox(im: Image.Image) -> tuple[int, int, int, int]:
    """Bounding box of the warm-lit creature against the cool dark stage.

    The creature is tan/brown everywhere including shadow (R 55-200, R > B);
    the backdrop is neutral grey (32) and the floor grid is blue-grey (R < B),
    so `R > 55 and R > B + 8` isolates body.
    """
    a = np.asarray(im.convert("RGB")).astype(int)
    warm = (a[..., 0] > 55) & (a[..., 0] > a[..., 2] + 8)
    ys, xs = np.nonzero(warm)
    if len(xs) == 0:
        return (0, 0, im.width, im.height)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def crop_aspect_centered(im, bbox, aspect, bias_x: float = 0.0) -> Image.Image:
    """Crop `im` to `aspect` (w/h), window on the creature, sized so the
    creature fits with margin when possible. `bias_x` shifts the window
    left (negative) / right (positive) as a fraction of the crop width, e.g.
    -0.12 pushes the creature toward the right side of the result."""
    W, H = im.size
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    bw, bh = x1 - x0, y1 - y0

    crop_h = min(H, max(round(W / aspect), min(bh + 80, H)))
    crop_w = min(W, max(round(crop_h * aspect), min(bw + 80, W)))
    # if fitting the creature inflates the crop past the aspect, re-derive
    crop_h = min(H, max(round(crop_w / aspect), 1))
    left = max(0, min(round(cx - crop_w / 2 - bias_x * crop_w), W - crop_w))
    top = max(0, min(cy - crop_h // 2, H - crop_h))
    return im.crop((left, top, left + crop_w, top + crop_h))


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _tracked_w(draw, text, font, tracking) -> float:
    return sum(draw.textlength(c, font=font) for c in text) + tracking * (len(text) - 1)


def _draw_tracked(draw, xy, text, font, fill, tracking) -> None:
    x, y = xy
    for c in text:
        draw.text((x, y), c, font=font, fill=fill)
        x += draw.textlength(c, font=font) + tracking


def _scrim(img: Image.Image) -> Image.Image:
    """Dark blue-grey gradient scrim from the left edge (unifies art with bg)."""
    W, H = img.size
    grad = Image.new("L", (W, 1), 0)
    fade = int(W * 0.62)
    for x in range(fade):
        grad.putpixel((x, 0), int(255 * (1.0 - x / fade) ** 1.15))
    mask = grad.resize((W, H))
    overlay = Image.new("RGB", (W, H), BG)
    return Image.composite(overlay, img.convert("RGB"), mask)


def make_capsule(hero_path: Path, out_path: Path, size: tuple[int, int]) -> None:
    """Full-bleed hero art, left scrim, CHIMERA + gold rule + tagline."""
    W, H = size
    hero = Image.open(hero_path).convert("RGB")
    art = crop_aspect_centered(hero, creature_bbox(hero), W / H, bias_x=-0.10) \
        .resize((W, H), Image.LANCZOS)
    img = _scrim(art)

    d = ImageDraw.Draw(img)
    margin = int(W * 0.058)
    if W >= 600:                                    # 616x353
        t_size, t_track, rule_h, tag_size = 66, 4, 3, 19
    else:                                           # 460x215
        t_size, t_track, rule_h, tag_size = 40, 2.5, 2, 13
    tf = _font(SERIF_B, t_size)
    gf = _font(SERIF_I, tag_size)

    tw = _tracked_w(d, "CHIMERA", tf, t_track)
    tb = d.textbbox((0, 0), "CH", font=tf)
    th = tb[3] - tb[1]
    ty = int(H * 0.40)
    tx = margin
    _draw_tracked(d, (tx, ty), "CHIMERA", tf, INK, t_track)

    rule_y = ty + th + int(t_size * 0.42)
    rule_w = int(tw * 0.92)
    d.rectangle([tx, rule_y, tx + rule_w, rule_y + rule_h], fill=GOLD)

    tag_y = rule_y + rule_h + int(t_size * 0.38)
    d.text((tx, tag_y), "touch the living physics", font=gf, fill=TAG)

    img.save(out_path)
    print(f"  {out_path.name}  {out_path.stat().st_size/1e3:.0f} kB")


def _silhouette_mask(crop: Image.Image, S: int) -> Image.Image:
    """Creature silhouette at icon resolution: warm threshold -> morphological
    close -> largest connected component -> hole fill."""
    from collections import deque

    a = np.asarray(crop).astype(int)
    warm = (a[..., 0] > 55) & (a[..., 0] > a[..., 2] + 8)
    m = Image.fromarray((warm * 255).astype(np.uint8), "L") \
             .resize((S, S), Image.LANCZOS)
    m = m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))  # close
    b = np.asarray(m) > 127

    # largest connected component (BFS, 512x512 is small)
    seen = np.zeros_like(b, bool)
    best, best_n = None, 0
    H, W = b.shape
    for sy in range(0, H, 4):
        for sx in range(0, W, 4):
            if b[sy, sx] and not seen[sy, sx]:
                comp = []
                q = deque([(sy, sx)])
                seen[sy, sx] = True
                while q:
                    y, x = q.popleft()
                    comp.append((y, x))
                    for ny, nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                        if 0 <= ny < H and 0 <= nx < W and b[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                if len(comp) > best_n:
                    best_n, best = len(comp), comp
    body = np.zeros_like(b)
    if best:
        for y, x in best:
            body[y, x] = True

    # hole fill: flood the background from the border; unreachable non-body = hole
    bg = np.zeros_like(b, bool)
    q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if not body[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if not body[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for ny, nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0 <= ny < H and 0 <= nx < W and not body[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                q.append((ny, nx))
    body |= ~bg & ~body

    return Image.fromarray((body * 255).astype(np.uint8), "L")


def make_icon(hero_path: Path, out_path: Path, S: int = 512) -> None:
    """Creature silhouette fitted to the icon: bronze gradient body, gold rim,
    soft gold glow, on a #0b0d10 field with a faint vertical lift."""
    hero = Image.open(hero_path).convert("RGB")
    bbox = creature_bbox(hero)
    x0, y0, x1, y1 = bbox
    side = int(max(x1 - x0, y1 - y0) * 1.15)
    side = min(side, hero.width, hero.height)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    left = max(0, min(cx - side // 2, hero.width - side))
    top = max(0, min(cy - side // 2, hero.height - side))
    crop = hero.crop((left, top, left + side, top + side))

    raw = _silhouette_mask(crop, S)
    # fit the silhouette to the icon: crop to its bbox, scale to ~88% height,
    # stand it slightly below center
    ys, xs = np.nonzero(np.asarray(raw) > 127)
    if len(xs) == 0:
        sys.exit("icon: silhouette mask came out empty")
    mx0, mx1, my0, my1 = xs.min(), xs.max(), ys.min(), ys.max()
    glyph = raw.crop((mx0, my0, mx1 + 1, my1 + 1))
    fit_h = int(S * 0.88)
    fit_w = max(1, round(glyph.width * fit_h / glyph.height))
    if fit_w > int(S * 0.92):
        fit_w = int(S * 0.92)
        glyph = glyph.resize((fit_w, max(1, round(glyph.height * fit_w / glyph.width))), Image.LANCZOS)
    else:
        glyph = glyph.resize((fit_w, fit_h), Image.LANCZOS)

    mask = Image.new("L", (S, S), 0)
    glyph = glyph.filter(ImageFilter.GaussianBlur(1.4)).point(
        lambda p: 255 if p > 120 else 0)          # smooth the staircase edge
    mask.paste(glyph, ((S - fit_w) // 2, S - fit_h - int(S * 0.05)))
    m = np.asarray(mask)

    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    for y in range(S):                               # faint vertical lift
        t = 1.0 - abs(y - S / 2) / (S / 2)
        c = tuple(int(v * (1 - t) + w * t) for v, w in zip(BG, (21, 24, 30)))
        d.line([(0, y), (S, y)], fill=c)

    # soft gold glow behind the silhouette
    glow = Image.new("L", (S, S), 0)
    glow.paste(mask, (0, 0))
    glow = glow.filter(ImageFilter.GaussianBlur(24))
    img.paste(Image.new("RGB", (S, S), GOLD), (0, 0), glow.point(lambda p: p * 48 // 255))

    # body: dark bronze vertical gradient inside the mask
    body = Image.new("RGB", (S, S))
    bd = ImageDraw.Draw(body)
    top_c, bot_c = (66, 48, 31), (24, 17, 12)
    for y in range(S):
        t = y / (S - 1)
        bd.line([(0, y), (S, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top_c, bot_c)))
    img.paste(body, (0, 0), mask)

    # gold rim: thin edge inside the silhouette
    edge = (m > 127).astype(np.uint8) - (np.asarray(
        Image.fromarray(m, "L").filter(ImageFilter.MinFilter(5))) > 127).astype(np.uint8)
    rim = Image.fromarray((edge * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6))
    img.paste(Image.new("RGB", (S, S), GOLD), (0, 0), rim)

    img.save(out_path)
    print(f"  {out_path.name}  {out_path.stat().st_size/1e3:.0f} kB")


def make_screenshots(capdir: Path, outdir: Path) -> list[dict]:
    """Six 1920x1080 crops from the picked captures, window on the creature."""
    made = []
    for i, name in enumerate(SCREENSHOT_PICKS, 1):
        src = capdir / f"capture_{SHOT_INDEX[name]:02d}_{name}.png"
        im = Image.open(src).convert("RGB")
        art = crop_aspect_centered(im, creature_bbox(im), 16 / 9)
        art = art.resize((1920, 1080), Image.LANCZOS)
        p = outdir / f"screenshot_{i:02d}_{name}.png"
        art.save(p)
        made.append({"file": p.name, "size": "1920x1080", "source_capture": src.name})
        print(f"  {p.name}  {p.stat().st_size/1e6:.1f} MB  <- {src.name}")
    return made


SHOT_INDEX = {name: i for i, (name, _, _) in enumerate(SHOTS, 1)}


def compose(capdir: Path, outdir: Path, cap_records: list[dict]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    hero = capdir / "capture_01_hero.png"
    print("composing from", capdir)

    made = {"capsules": [], "icon": None, "screenshots": []}
    for size in ((616, 353), (460, 215)):
        p = outdir / f"capsule_{size[0]}x{size[1]}.png"
        make_capsule(hero, p, size)
        made["capsules"].append({"file": p.name, "size": f"{size[0]}x{size[1]}",
                                 "source_capture": hero.name})
    icon = outdir / "icon_512x512.png"
    make_icon(hero, icon)
    made["icon"] = {"file": icon.name, "size": "512x512", "source_capture": hero.name}
    made["screenshots"] = make_screenshots(capdir, outdir)

    manifest = {
        "generated_by": "tools/store_art/make_art.py",
        "engine": ENGINE,
        "background": "#0b0d10", "accent": "#d4a537",
        "tagline": "touch the living physics",
        "captures": cap_records,
        "assets": made,
    }
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("  manifest.json")


# ---------------------------------------------------------------- cli
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(OUT), help="output tree (default STORE_ART)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--capture-only", action="store_true")
    g.add_argument("--compose-only", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.out)
    capdir = outdir / "captures"

    cap_records = []
    if not args.compose_only:
        print("capturing 8 frames from", ENGINE)
        cap_records = capture(capdir)
        # purge any stray probe frames so the capture set stays exactly the 8
        for stray in capdir.glob("_*.png"):
            stray.unlink()
    if not args.capture_only:
        if not (capdir / "capture_01_hero.png").exists():
            sys.exit("no captures found — run without --compose-only first")
        if not cap_records:   # reload capture metadata from previous run
            mf = outdir / "manifest.json"
            cap_records = json.loads(mf.read_text(encoding="utf-8"))["captures"] \
                if mf.exists() else [{"file": p.name, "shot": p.stem.split("_", 2)[-1],
                                      "camera_v": None} for p in sorted(capdir.glob("capture_*.png"))]
        print("composing store art")
        compose(capdir, outdir, cap_records)
    print("done ->", outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
