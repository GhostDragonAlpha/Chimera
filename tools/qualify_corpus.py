"""qualify_corpus.py -- every corpus patch faces the eye before it may teach.

The qualification process of the workflow (operator, 2026-08-21): each patch is
rendered top-down and qwen3.8 answers ONE question -- "does this patch look like
teddy bear fur?" NO (or an unclear answer) eliminates the patch. Clean data is
worth the wait.

Patch VALUE = its real splat count (density): larger/denser patches are more
likely to read as the true material and count for more at training time.
(operator: "larger patches have a higher probability of looking like the thing")

Outputs: qualified npz (patches + weights), a JSON report with every verdict and
the eye's exact words, and a contact sheet of the REJECTS for operator audit --
the eye's decisions are reviewable, never silent.

  .venv-gs/Scripts/python.exe tools/qualify_corpus.py \
      --corpus models/co3d/corpus/fur_bear34.npz models/co3d/corpus/fur_bear187.npz \
      --out models/co3d/corpus/fur_qualified.npz --workdir .tmp/qualify
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import lasso_label as ll  # noqa: E402
import senses  # noqa: E402
from extract_genomes import quat_mul  # noqa: E402

QUESTION = ("You are examining a small square material sample taken from a teddy "
            "bear, shown from directly above. Does this patch look like teddy bear "
            "fur? Answer YES or NO first, then one short reason.")


def render_soft(buf: np.ndarray, cam, w: int = 640, h: int = 360) -> "object":
    """Truthful mini splat rasterizer: each splat is a 2D GAUSSIAN (soft falloff),
    alpha-composited back-to-front. The eye must judge fur as fur actually
    renders, not hard polygon shards."""
    u, v, z, sa, sb, th, ok = ll.ellipses_2d(buf, cam, w, h, k=1.0)  # true sigmas
    rgb = buf[ok, 3:6]
    alpha = np.clip(buf[ok, 6], 0, 1)
    acc = np.zeros((h, w, 3))
    acc_a = np.zeros((h, w))
    for i in np.argsort(-z):
        rad_a, rad_b = 3 * sa[i], 3 * sb[i]
        rad = int(math.ceil(max(rad_a, rad_b))) + 1
        x0, x1 = max(0, int(u[i]) - rad), min(w, int(u[i]) + rad + 1)
        y0, y1 = max(0, int(v[i]) - rad), min(h, int(v[i]) + rad + 1)
        if x1 <= x0 or y1 <= y0 or sa[i] < 1e-3 or sb[i] < 1e-3:
            continue
        ys, xs = np.mgrid[y0:y1, x0:x1]
        dx, dy = xs - u[i], ys - v[i]
        c, s = math.cos(th[i]), math.sin(th[i])
        da = dx * c + dy * s
        db = -dx * s + dy * c
        gw = alpha[i] * np.exp(-0.5 * ((da / sa[i]) ** 2 + (db / sb[i]) ** 2))
        a = acc_a[y0:y1, x0:x1]
        acc[y0:y1, x0:x1] = acc[y0:y1, x0:x1] + (1 - a)[..., None] * gw[..., None] * rgb[i]
        acc_a[y0:y1, x0:x1] = a + (1 - a) * gw
    bg = np.array([10, 10, 16]) / 255.0
    out = acc + (1 - acc_a)[..., None] * bg[None, None, :]
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def patch_buffer(p: np.ndarray) -> np.ndarray:
    """(512,14) patch row -> 14-float splat buffer (padding dropped).
    Patch frame is (u, v, h); the renderer orbits Y-up, so h -> +Y puts the
    membrane plane horizontal and the camera looks straight DOWN the normal.
    The frame change is the PROPER rotation (u,v,h)->(u,h,-v) = -90deg about u,
    and the splat quats are conjugated by it (a plain axis swap would mirror)."""
    real = p[p[:, 6] > 0]
    b = np.zeros((len(real), 14), dtype=np.float64)
    b[:, 0] = real[:, 0]    # u -> x
    b[:, 1] = real[:, 2]    # h -> y (the normal is UP in render space)
    b[:, 2] = -real[:, 1]   # v -> -z (keeps the frame right-handed)
    b[:, 3:6] = real[:, 3:6]
    b[:, 6] = real[:, 6]
    b[:, 7:10] = np.exp(real[:, 7:10])
    s = math.sqrt(0.5)
    Q = np.tile(np.array([s, -s, 0.0, 0.0]), (len(real), 1))  # -90deg about x
    b[:, 10:14] = quat_mul(Q, real[:, 10:14])
    return b


def verdict(text: str | None) -> bool:
    """The eye's answer, parsed strictly: YES qualifies; NO, silence, or mush
    eliminates (clean data is biased toward rejection)."""
    if not text:
        return False
    t = text.strip().upper()
    if t.startswith("YES"):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workdir", default=".tmp/qualify")
    ap.add_argument("--limit", type=int, default=0, help="debug: only first N patches")
    ap.add_argument("--via", choices=["viewer", "soft"], default="viewer",
                    help="viewer = the REAL renderer (playwright screenshot of "
                         "viewer.html); soft = the numpy mini-rasterizer (fast, "
                         "approximate -- never for a final verdict)")
    a = ap.parse_args()

    if not senses.available():
        print("REFUSED: the eye is dark (Ollama qwen3.8 not serving). "
              "Qualification requires the local vision model.")
        return 1

    work = Path(a.workdir)
    work.mkdir(parents=True, exist_ok=True)
    from cut_patches import PATCH_HALF, N_PTS
    # NATIVE-RESOLUTION presentation (2026-08-21, eye-verified): splats are
    # trained at ~1 px per splat footprint (~0.8 mm); zooming past that reads
    # as sparse dust and the eye is RIGHT to reject it. Present the window at
    # its native pixel size, then crop and upscale for the eye.
    VIEWER_R = 0.2          # viewer.html clamps OrbitControls to >= 0.2 m
    NATIVE_PX = 150.0       # window spans ~150 px at r=0.2 (~0.65 mm/px)
    r_soft = (2 * PATCH_HALF / NATIVE_PX) * 360 / \
        (2 * math.tan(math.radians(ll.FOV_DEG) / 2.0))

    # phase 1: decode every patch to its truthful splat buffer
    jobs = []   # (corpus, index, buf)
    for cpath in a.corpus:
        P = np.load(cpath)["patches"]
        n = len(P) if not a.limit else min(a.limit, len(P))
        for i in range(n):
            buf = patch_buffer(P[i])
            if len(buf) < 64:
                report_rec = {"corpus": cpath, "index": i, "verdict": "REJECT",
                              "reason": f"too few splats ({len(buf)})", "n": len(buf)}
                jobs.append((cpath, i, None, report_rec))
            else:
                jobs.append((cpath, i, buf, None))

    # phase 2 (viewer only): one browser session renders them all
    shot_dir = work / "shots"
    if a.via == "viewer":
        import subprocess
        shot_dir.mkdir(exist_ok=True)
        import cpp_bridge as cb
        manifest = []
        qdir = Path("models/triposplat/static/viewer/_qualify")
        qdir.mkdir(parents=True, exist_ok=True)
        for k, (_, _, buf, rec) in enumerate(jobs):
            if rec is not None:
                continue
            name = f"p{k:05d}"
            b = buf.astype(np.float32).copy()
            b[:, 0:3] -= b[:, 0:3].mean(0)
            cb.save_splat(str(qdir / f"{name}.splat"), b)
            manifest.append(name)
        (shot_dir / "manifest.json").write_text(json.dumps(manifest))
        r = subprocess.run(
            ["node", str(ROOT / "tools/qualify_shots.js"), str(shot_dir),
             str(VIEWER_R)], cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit("FAILED: qualify_shots.js")

    # phase 3: present + judge
    kept, report, reject_pngs = [], [], []
    rep_path = work / "report.json"
    for k, (cpath, i, buf, rec) in enumerate(jobs):
        total = k + 1
        if rec is not None:
            report.append(rec)
            continue
        png = str(work / f"p{total:05d}.png")
        if a.via == "viewer":
            img = Image.open(shot_dir / f"p{k:05d}.png")
            cw = int(NATIVE_PX / 2 * 1.15)
            img = img.crop((320 - cw, 180 - cw, 320 + cw, 180 + cw))
            img = img.resize((640, 640), Image.LANCZOS)
            img.save(png)
        else:
            tgt = np.array([0.0, float(np.median(buf[:, 1])), 0.0])
            cam = ll.camera(0.0, math.pi / 2 - 0.06, r_soft, tgt)
            img = render_soft(buf, cam)
            cw = int(NATIVE_PX / 2 * 1.15)
            img = img.crop((320 - cw, 180 - cw, 320 + cw, 180 + cw))
            img = img.resize((640, 640), Image.LANCZOS)
            img.save(png)
        text = senses.see(png, QUESTION)
        ok = verdict(text)
        report.append({"corpus": cpath, "index": i, "verdict": "PASS" if ok else "REJECT",
                       "eye": (text or "")[:300], "n": int(len(buf))})
        if ok:
            kept.append((cpath, i, len(buf)))
        else:
            reject_pngs.append(png)
        if total % 10 == 0:  # incremental: a crash must not lose verdicts
            rep_path.write_text(json.dumps({"question": QUESTION, "verdicts": report},
                                           indent=1))
            print(f"{total}: qualified {len(kept)} / examined {total}", flush=True)

    out_p = np.stack([np.load(c)["patches"][i] for c, i, _ in kept]) if kept \
        else np.zeros((0, N_PTS, 14), np.float32)
    weights = np.array([w for _, _, w in kept], dtype=np.float32)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, patches=out_p, weights=weights,
                        source=np.array([f"{c}#{i}" for c, i, _ in kept]))
    rep_path.write_text(json.dumps({
        "question": QUESTION, "examined": len(jobs),
        "qualified": len(kept), "rejected": len(jobs) - len(kept),
        "verdicts": report}, indent=1))

    if reject_pngs:
        cols = 6
        tw, th = 320, 320
        rows = math.ceil(len(reject_pngs) / cols)
        sheet = Image.new("RGB", (cols * tw, rows * th), (20, 8, 8))
        dr = ImageDraw.Draw(sheet)
        for k, png in enumerate(reject_pngs):
            img = Image.open(png).resize((tw, th))
            sheet.paste(img, ((k % cols) * tw, (k // cols) * th))
            dr.text(((k % cols) * tw + 4, (k // cols) * th + 4), f"reject {k}",
                    fill=(255, 120, 120))
        sheet.save(work / "rejects_sheet.png")
        print("rejects sheet ->", work / "rejects_sheet.png")

    print(f"\nQUALIFIED {len(kept)}/{len(jobs)} patches -> {a.out}")
    print(f"report -> {rep_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
