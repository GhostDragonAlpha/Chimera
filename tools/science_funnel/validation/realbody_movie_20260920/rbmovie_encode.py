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
    ap.add_argument("--truetime", action="store_true",
                    help="cut the movie at the MEASURED per-frame timing "
                         "(ffconcat durations from capture_record's "
                         "frame_dt_ms): motion speed is exact, not re-timed "
                         "to a chosen fps")
    a = ap.parse_args()
    frames = Path(a.frames)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cap = json.loads(Path(a.record).read_text(encoding="utf-8"))
    n = cap["frames"]
    rec = {"schema": "chimera.realbody_movie_20260920.encode.v1",
           "measured_mean_fps": cap["mean_fps"],
           "frames": n,
           "crf_ladder": []}
    if a.truetime:
        dts = cap["frame_dt_ms"]
        assert len(dts) == n - 1, "frame_dt_ms must cover every interval"
        lst = frames / "cut.ffconcat"
        lines = ["ffconcat version 1.0"]
        for i in range(n):
            lines.append("file '%s'" % (frames / ("f%05d.jpg" % i)).as_posix())
            if i < n - 1:
                lines.append("duration %.4f" % (dts[i] / 1000.0))
        lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
        rec["cut"] = "truetime (ffconcat per-frame durations = measured dt)"
    else:
        fps = int(round(cap["mean_fps"]))
        rec["encoded_fps"] = fps
        rec["cut"] = "uniform at the rounded measured mean fps"
        lst = None
    rec["implied_duration_s"] = (
        round(sum(dts) / 1000.0 + dts[-1] / 1000.0, 2) if a.truetime
        else round(n / int(rec["encoded_fps"]), 2))
    for crf in (20, 23, 26):
        if a.truetime:
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
                   str(lst), "-fps_mode", "vfr", "-c:v", "libx264",
                   "-pix_fmt", "yuv420p", "-crf", str(crf), str(out)]
        else:
            cmd = ["ffmpeg", "-y", "-framerate", str(rec["encoded_fps"]),
                   "-i", str(frames / "f%05d.jpg"), "-c:v", "libx264",
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
