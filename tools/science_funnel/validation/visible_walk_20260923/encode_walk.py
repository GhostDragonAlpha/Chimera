"""encode_walk.py -- cut the movie at the MEASURED cadence (lane
visible-walk 20260923; the render-truth lane's encode shape). ffconcat
per-frame durations = the measured capture dt (true time, no fps chosen);
H.264 yuv420p; CRF ladder 20/23/26 under the 25 MB delivery bound.
"""
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


def main() -> int:
    here = Path(__file__).resolve().parent
    frames = here / "frames"
    cap = json.loads((here / "capture_record.json").read_text(encoding="utf-8"))
    per = cap["per_frame"]
    n = len(per)
    out = here / "real_body_walk.mp4"
    lst = frames / "cut.ffconcat"
    lines = ["ffconcat version 1.0"]
    for i in range(n):
        lines.append("file '%s'" % (frames / ("f%05d.jpg" % i)).as_posix())
        if i < n - 1:
            d = per[i + 1]["t"] - per[i]["t"]
            lines.append("duration %.4f" % max(d, 0.001))
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rec = {"schema": "chimera.visible_walk_20260923.encode.v1",
           "frames": n,
           "measured_mean_fps": cap["mean_fps"],
           "cut": "truetime (ffconcat per-frame durations = measured dt)",
           "implied_duration_s": round(per[-1]["t"] + per[0]["t"], 2),
           "crf_ladder": []}
    for crf in (20, 23, 26):
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
               "-fps_mode", "vfr", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-crf", str(crf), str(out)]
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
        pr = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,avg_frame_rate,nb_frames",
             "-show_entries", "format=duration,size", "-of", "json",
             str(out)], capture_output=True, text=True)
        rec["ffprobe"] = json.loads(pr.stdout or "{}")
    (here / "encode_record.json").write_text(json.dumps(rec, indent=1),
                                             encoding="utf-8")
    print(json.dumps(rec, indent=1), flush=True)
    return 0 if rec.get("crf_used") is not None else 1


if __name__ == "__main__":
    sys.exit(main())
