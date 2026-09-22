"""rbmovie_encode.py -- cut the movie at the MEASURED cadence (lane
realbody-movie-20260920). Reads capture_record.json for the measured mean fps,
encodes f%05d.jpg -> H.264 MP4 through the established encode_movie shape
(ffmpeg libx264 yuv420p), and records duration/size/sha. If the movie exceeds
the mission's own <= ~25 MB bound, the CRF ladder (20 -> 23 -> 26) is walked
down rung by rung -- the bound is the law, the ladder is its arithmetic, and
every rung tried is recorded.

Output: encode_record.json beside this file. Exits 0 iff the encode exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(mp4: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,nb_frames",
         "-show_entries", "format=duration,size", "-of", "json",
         str(mp4)], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--record", required=True, help="capture_record.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    frames = Path(a.frames)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cap = json.loads(Path(a.record).read_text(encoding="utf-8"))
    fps = int(round(cap["mean_fps"]))
    n = cap["frames"]
    rec = {"schema": "chimera.realbody_movie_20260920.encode.v1",
           "measured_mean_fps": cap["mean_fps"], "encoded_fps": fps,
           "frames": n, "implied_duration_s": round(n / fps, 2),
           "crf_ladder": []}
    for crf in (20, 23, 26):
        cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i",
               str(frames / "f%05d.jpg"), "-c:v", "libx264",
               "-pix_fmt", "yuv420p", "-crf", str(crf), str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            rec["crf_ladder"].append({"crf": crf, "error": r.stderr[-400:]})
            continue
        mb = out.stat().st_size / (1024 * 1024)
        rec["crf_ladder"].append({"crf": crf, "mb": round(mb, 2)})
        if mb <= 25.0:
            rec["crf_used"] = crf
            break
    if rec.get("crf_used") is None:
        rec["error"] = "no encode under the 25 MB bound"
    else:
        rec["mp4"] = {"path": str(out), "bytes": out.stat().st_size,
                      "sha256": sha256_file(out)}
        rec["ffprobe"] = probe(out)
    (Path(a.record).parent / "encode_record.json").write_text(
        json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps(rec, indent=1), flush=True)
    return 0 if rec.get("crf_used") is not None else 1


if __name__ == "__main__":
    sys.exit(main())
