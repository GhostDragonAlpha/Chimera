"""run_judge_walk.py -- THE BLIND JUDGE (lane visible-walk 20260923).

The render-truth lane's judge protocol unchanged: ollama qwen3.8, think:false,
ONE senses.watch call over 12 ordered 384px resizes of evenly spaced captured
frames, infrastructure failures preserved verbatim as attempts. The PROMPT is
the house prompt STYLE with the question pointed at THIS lane's falsifier
(walking on all fours, connected) -- it names neither the body's origin, nor
"CT", nor "macaque", nor the expected verdict (no tuning to flatter).
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

os.environ["CHIMERA_VISION_BACKEND"] = "ollama"

HERE = Path(__file__).resolve().parent
CHIMERA_HOME = Path(r"E:/PythonChimera")
sys.path.insert(0, str(CHIMERA_HOME / "ChimeraEngine"))
sys.path.insert(0, str(CHIMERA_HOME))

PROMPT = (
    "You are watching a short movie: an ordered sequence of frames from one "
    "camera watching one creature in a dark 3D world with a floor grid. The "
    "frames are in order and show the same creature over time. Describe what "
    "this creature's body is doing across the frames: which parts you can "
    "see, which parts move, how, and in what order. Then answer the "
    "questions that matter: does the creature read as ONE CONNECTED PHYSICAL "
    "ANIMAL, or as SEPARATE FLOATING PARTS? And does it read as WALKING ON "
    "ALL FOURS -- four limbs stepping, the body advancing through the world "
    "-- or as static, carried, or motionless? Be specific and factual; do "
    "not speculate beyond the frames.")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--capture-record", required=True)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--url", default=None)
    ap.add_argument("--max-attempts", type=int, default=6)
    ap.add_argument("--window", default=None,
                    help="AMENDMENT sampling window 'start:end' frame range "
                         "(e.g. the stride phase); default: the whole movie")
    ap.add_argument("--out", default="judgement.json")
    a = ap.parse_args()
    if a.url:
        os.environ["CHIMERA_VISION_URL"] = a.url
    frames_dir = Path(a.frames)
    cap = json.loads(Path(a.capture_record).read_text(encoding="utf-8"))
    n_total = cap["frames"]
    if a.window:
        s, e = (int(v) for v in a.window.split(":"))
        idxs = [round(s + i * (e - 1 - s) / (a.n - 1)) for i in range(a.n)]
        window_note = "AMENDMENT window frames [%d,%d)" % (s, e)
    else:
        idxs = [round(i * (n_total - 1) / (a.n - 1)) for i in range(a.n)]
        window_note = "evenly spaced over the whole movie"

    watch_dir = frames_dir.parent / "judge_watch"
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
    rep = None
    attempts = []
    for k in range(1, a.max_attempts + 1):
        t0 = time.perf_counter()
        try:
            rep = senses.watch([d["judge_png"] for d in inputs], PROMPT)
            if rep:
                attempts.append({"attempt": k, "ok": True,
                                 "wall_s": round(time.perf_counter() - t0, 1)})
                print("attempt %d OK (%.1f s)" % (k, attempts[-1]["wall_s"]),
                      flush=True)
                break
            attempts.append({"attempt": k, "ok": False, "reason": "empty",
                             "wall_s": round(time.perf_counter() - t0, 1)})
        except Exception as e:  # noqa: BLE001 -- infrastructure failures kept
            attempts.append({"attempt": k, "ok": False,
                             "error": repr(e)[:400],
                             "wall_s": round(time.perf_counter() - t0, 1)})
        (HERE / "judgement_attempts.json").write_text(
            json.dumps(attempts, indent=1), encoding="utf-8")
        time.sleep(5)
    rec = {"schema": "chimera.visible_walk_20260923.judgement.v1",
           "sampling_window": window_note,
           "prompt": PROMPT,
           "prompt_provenance": "the render-truth lane's house prompt with "
                                "the final question pointed at this lane's "
                                "falsifier (walking on all fours, "
                                "connected); still blind (no origin, no "
                                "expected verdict)",
           "lane": "ollama (senses.py ollama branch: qwen3.8, think:false)",
           "vision_url": os.environ.get("CHIMERA_VISION_URL",
                                        "http://localhost:11434"),
           "model": "qwen3.8",
           "protocol": "ONE senses.watch call over %d ordered 384 px resizes "
                       "of evenly spaced captured frames; attempts list "
                       "preserves every infrastructure failure verbatim" % a.n,
           "n_frames": a.n,
           "frames_total_captured": n_total,
           "frame_mapping": inputs,
           "attempts": attempts,
           "verbatim_report": rep,
           "eye_lane_available": senses.available()}
    (HERE / a.out).write_text(json.dumps(rec, indent=1),
                                         encoding="utf-8")
    print("EYE AVAILABLE:", rec["eye_lane_available"], flush=True)
    print("=== VERBATIM VERDICT ===", flush=True)
    print(rep, flush=True)
    return 0 if rep else 1


if __name__ == "__main__":
    sys.exit(main())
