"""render_truth_judge.py -- THE DYAD JUDGE (lane render-truth-20260920).

The realbody-movie lane's judge, unchanged in protocol: the OLLAMA lane of
senses.py (qwen3.8, think:false, num_ctx sized to the frames by senses.py's
own ollama-branch math), ONE senses.watch call over an ORDERED frame sample
from the capture, with the SAME BLIND prompt (it names neither the body's
origin, nor "CT", nor "macaque", nor the expected verdict -- no prompt
tuning between the RED finding and this lane; the falsifier F-CONNECTED is
read off the verbatim text either way).

Env: CHIMERA_VISION_BACKEND=ollama (set here before senses imports it).
Output: judgement.json beside this file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ["CHIMERA_VISION_BACKEND"] = "ollama"   # the movie-judge lane

HERE = Path(__file__).resolve().parent
# senses.py lives in the PHYSICS repo's engine package (E:/PythonChimera);
# the eye is standing shared machinery this lane uses, never edits.
CHIMERA_HOME = Path(r"E:/PythonChimera")
sys.path.insert(0, str(CHIMERA_HOME / "ChimeraEngine"))
sys.path.insert(0, str(CHIMERA_HOME))

# VERBATIM the realbody-movie lane's prompt (the RED finding's prompt):
# changing it between the RED and this run would flatter, not measure.
PROMPT = (
    "You are watching a short movie: an ordered sequence of frames from one "
    "camera watching one creature in a dark 3D world with a floor grid. The "
    "frames are in order and show the same creature over time. Describe what "
    "this creature's body is doing across the frames: which parts you can "
    "see, which parts move, how, and in what order. Then answer the one "
    "question that matters: does the skeleton read as ONE CONNECTED PHYSICAL "
    "ANIMAL being moved and carried by physics, or as SEPARATE FLOATING "
    "PARTS? Be specific and factual; do not speculate beyond the frames.")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True, help="captured frames dir")
    ap.add_argument("--capture-record", required=True)
    ap.add_argument("--n", type=int, default=12)
    a = ap.parse_args()
    frames_dir = Path(a.frames)
    cap = json.loads(Path(a.capture_record).read_text(encoding="utf-8"))
    n_total = cap["frames"]
    idxs = [round(i * (n_total - 1) / (a.n - 1)) for i in range(a.n)]

    watch_dir = frames_dir / "judge_watch"
    watch_dir.mkdir(exist_ok=True)
    from PIL import Image
    inputs = []
    for i in idxs:
        src = frames_dir / ("f%05d.jpg" % i)
        dst = watch_dir / ("f%05d_384.png" % i)
        if not dst.is_file():
            Image.open(src).resize((384, 216), Image.LANCZOS).save(dst)
        inputs.append({"movie_frame": i, "src": str(src),
                       "src_sha256": sha256_file(src),
                       "judge_png": str(dst),
                       "judge_png_sha256": sha256_file(dst)})

    import senses
    rep = senses.watch([d["judge_png"] for d in inputs], PROMPT)
    rec = {"schema": "chimera.render_truth_20260920.judgement.v1",
           "prompt": PROMPT,
           "prompt_provenance": "VERBATIM the realbody_movie_20260920 lane's "
                                "prompt -- the RED finding's own prompt, "
                                "unchanged (no tuning to flatter)",
           "lane": "ollama (senses.py ollama branch: qwen3.8, think:false, "
                   "num_ctx sized to the frames)",
           "model": "qwen3.8",
           "protocol": "ONE senses.watch call over %d ordered 384 px resizes "
                       "of evenly spaced captured frames (walk-movie "
                       "precedent); verdict verbatim below" % a.n,
           "n_frames": a.n,
           "frames_total_captured": n_total,
           "frame_mapping": inputs,
           "verbatim_report": rep,
           "eye_lane_available": senses.available()}
    (HERE / "judgement.json").write_text(json.dumps(rec, indent=1),
                                         encoding="utf-8")
    print("EYE AVAILABLE:", rec["eye_lane_available"], flush=True)
    print("=== VERBATIM VERDICT ===", flush=True)
    print(rep, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
