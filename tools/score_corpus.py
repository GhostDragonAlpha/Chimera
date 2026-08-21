"""score_corpus.py -- 0-100 fur-score for every patch; the NUMBER is the gate.

Operator ruling (2026-08-21): YES/NO is too coarse and the eye miscalibrated
against the human. Now the eye answers "0-100, how much does this look like
teddy bear fur?" and the operator scores a sample himself; the acceptance
threshold is set where the two agree. Only the numbers matter.

Reuses the already-rendered qualification PNGs when present (fast rescore),
otherwise renders via the real viewer (qualify_corpus --via viewer path).

  .venv-gs/Scripts/python.exe tools/score_corpus.py \
      --workdir .tmp/qualify/full [--samples 3]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import senses  # noqa: E402

QUESTION = ("You are examining a small square material sample taken from a "
            "teddy bear, shown from directly above. On a scale from 0 to 100, "
            "how much does this look like real teddy bear fur? 0 = not fur at "
            "all, 100 = indistinguishable from a real plush fur sample. "
            "Answer with the NUMBER ONLY.")


def parse_score(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"\b(\d{1,3})\b", text.strip())
    if not m:
        return None
    s = int(m.group(1))
    return s if 0 <= s <= 100 else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workdir", required=True, help="dir with pNNNNN.png renders")
    ap.add_argument("--samples", type=int, default=1,
                    help="eye samples per patch; score = median (noise control)")
    a = ap.parse_args()

    if not senses.available():
        print("REFUSED: the eye is dark (Ollama qwen3.8 not serving).")
        return 1

    work = Path(a.workdir)
    pngs = sorted(work.glob("p*.png"))
    if not pngs:
        raise SystemExit(f"no p*.png renders in {work} -- run qualify_corpus first")

    out_path = work / "scores.json"
    scores = json.loads(out_path.read_text()) if out_path.exists() else {}
    for k, png in enumerate(pngs):
        name = png.stem
        got = [s for s in scores.get(name, []) if s is not None]
        while len(got) < a.samples:
            s = parse_score(senses.see(str(png), QUESTION))
            got.append(s if s is not None else -1)  # -1 = unparsable, retry next run
        got = [s for s in got if s >= 0]
        scores[name] = got
        out_path.write_text(json.dumps(scores, indent=1))  # incremental
        if (k + 1) % 10 == 0:
            print(f"{k+1}/{len(pngs)} scored", flush=True)

    med = {n: sorted(v)[len(v) // 2] for n, v in scores.items() if v}
    order = sorted(med, key=med.get, reverse=True)

    # sheet sorted by score, best first -- the operator calibrates against this
    from PIL import Image, ImageDraw
    cols, tw = 5, 256
    rows = math.ceil(len(order) / cols)
    sheet = Image.new("RGB", (cols * tw, rows * (tw + 22)), (12, 12, 16))
    dr = ImageDraw.Draw(sheet)
    for k, name in enumerate(order):
        img = Image.open(work / f"{name}.png").resize((tw, tw))
        x, y = (k % cols) * tw, (k // cols) * (tw + 22)
        sheet.paste(img, (x, y + 22))
        dr.text((x + 6, y + 4), f"{name}  score {med[name]}", fill=(255, 220, 120))
    sheet.save(work / "scored_sheet.png")

    vals = list(med.values())
    print(f"\nscored {len(vals)} patches | p10/p50/p90 = "
          f"{sorted(vals)[len(vals)//10]}/{sorted(vals)[len(vals)//2]}/"
          f"{sorted(vals)[9*len(vals)//10]}")
    print("scores ->", out_path)
    print("sheet  ->", work / "scored_sheet.png  (sorted best-first; your move)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
