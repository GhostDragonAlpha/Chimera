"""score_sources.py -- 0-100 source gate: is this a COMPLETE teddy bear?

Operator (2026-08-21): a source that itself has holes is disqualified before
any patch is cut from it. The ladder is source -> part -> material; each rung
is a 0-100 eye score and each rung gates the next.

Two modes:
  --images  : pre-training filter. Scores 3 frames (25/50/75%) of each CO3D
              sequence; source score = MIN (one bad angle = a hole = rejected).
  --splat X.splat : post-training check. Renders 6 canonical angles through the
              real viewer; score = MIN over angles (the hole test).

  .venv-gs/Scripts/python.exe tools/score_sources.py --images capture/co3d/teddybear --limit 20
  .venv-gs/Scripts/python.exe tools/score_sources.py --splat models/co3d/co3d_34.splat
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import senses  # noqa: E402

# The story defines the bear as FURRY (operator, 2026-08-21) -- the question
# asks for the story's term, not my paraphrase. Eventually this string comes
# from the term's definition in THE_STORY.md / the engine, not from here.
Q_IMG = ("On a scale from 0 to 100, how much does this look like a complete, "
         "intact, FURRY teddy bear? 0 = not a teddy bear / not furry / badly "
         "damaged / missing parts, 100 = a complete furry teddy bear, fully "
         "visible, plush fur clearly present. Answer with the NUMBER ONLY.")
Q_SPLAT = Q_IMG  # same question, different renderer


def parse_score(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"\b(\d{1,3})\b", text.strip())
    if not m:
        return None
    s = int(m.group(1))
    return s if 0 <= s <= 100 else None


def score_images(root: Path, limit: int, out: Path, prior: Path | None = None,
                 prior_min: int = 50) -> None:
    seqs = sorted(d for d in root.iterdir()
                  if d.is_dir() and (d / "pointcloud.ply").exists())
    if prior and prior.exists():
        old = json.loads(prior.read_text())
        seqs = [d for d in seqs if old.get(d.name, {}).get("min", -1) >= prior_min]
        print(f"prior filter: {len(seqs)} sequences at >= {prior_min} carry forward")
    if limit:
        seqs = seqs[:limit]
    scores = json.loads(out.read_text()) if out.exists() else {}
    for k, d in enumerate(seqs):
        if d.name in scores:
            continue
        frames = sorted((d / "images").glob("*.jpg")) or sorted((d / "images").glob("*.png"))
        if not frames:
            continue
        picks = [frames[len(frames) // 4], frames[len(frames) // 2], frames[3 * len(frames) // 4]]
        vals = [s for s in (parse_score(senses.see(str(f), Q_IMG)) for f in picks)
                if s is not None]
        scores[d.name] = {"views": vals, "min": min(vals) if vals else -1}
        out.write_text(json.dumps(scores, indent=1))  # incremental
        print(f"{k+1}/{len(seqs)} {d.name}: min={scores[d.name]['min']} {vals}",
              flush=True)

    # montage: middle frame of each sequence, sorted best-first
    from PIL import Image, ImageDraw
    order = sorted(scores, key=lambda n: scores[n]["min"], reverse=True)
    cols, tw = 6, 200
    rows = math.ceil(len(order) / cols) or 1
    sheet = Image.new("RGB", (cols * tw, rows * (tw + 20)), (12, 12, 16))
    dr = ImageDraw.Draw(sheet)
    for k, name in enumerate(order):
        frames = sorted((root / name / "images").glob("*.jpg"))
        if not frames:
            continue
        img = Image.open(frames[len(frames) // 2]).convert("RGB").resize((tw, tw))
        x, y = (k % cols) * tw, (k // cols) * (tw + 20)
        sheet.paste(img, (x, y + 20))
        dr.text((x + 4, y + 3), f"{name[:14]} min={scores[name]['min']}",
                fill=(255, 220, 120))
    sheet_path = out.with_suffix(".png")
    sheet.save(sheet_path)
    print("sheet ->", sheet_path)


def score_splat(splat: Path, out: Path) -> None:
    work = out.parent / f"source_{splat.stem}"
    work.mkdir(parents=True, exist_ok=True)
    import shutil
    dst = ROOT / "models/triposplat/static/viewer/_qualify" / splat.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(splat, dst)
    names = ["front", "back", "left", "right", "top", "bottom"]  # source_shots.js
    r = subprocess.run(
        ["node", str(ROOT / "tools/source_shots.js"), splat.name,
         work.as_posix(), "1.0"], cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit("FAILED: source shots")
    vals = []
    for name in names:
        s = parse_score(senses.see(str(work / f"{name}.png"), Q_SPLAT))
        vals.append({"view": name, "score": s})
    result = {"splat": str(splat), "views": vals,
              "min": min(v["score"] for v in vals if v["score"] is not None)}
    (work / "source_score.json").write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--images", type=Path, help="CO3D category dir (pre-training filter)")
    ap.add_argument("--splat", type=Path, help="trained splat (post-training hole test)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--prior", type=Path, default=None,
                    help="previous scores.json; only sequences at >= --prior-min are rescored")
    ap.add_argument("--prior-min", type=int, default=50)
    ap.add_argument("--out", default=".tmp/qualify/sources.json")
    a = ap.parse_args()
    if not senses.available():
        print("REFUSED: the eye is dark (Ollama qwen3.8 not serving).")
        return 1
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.images:
        score_images(a.images, a.limit, out, a.prior, a.prior_min)
    elif a.splat:
        score_splat(a.splat, out)
    else:
        ap.error("--images or --splat required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
