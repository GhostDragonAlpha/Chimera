"""truth_recorder.py -- the TWIN-ENGINE TRUTH recorder (the pilot's ground
truth instrument).

The engine serves a state pull in ~15 ms median (single HTTP worker; measured
in this lane), so a truth recorder on the CLIENT's own engine would contend
with the client for the engine's ~60 req/s budget. The truth therefore runs
against a TWIN slice (the same code, same boot bytes, own engine): the
determinism the playable-slice receipt banked (byte-clean restart, bit-stable
fixed point) makes the twin's timeline equal to the client engine's up to the
scenario-trigger offset, which the suite ESTIMATES by cross-correlating the
two root_y curves and reports with the receipt. The twin assumption itself is
checked per run (F5-adjacent): final fixed-point /verts shas must be
identical, and the root_y curves must match to the named bar after the
estimated shift.

Records at its own sustainable pace (FULL36, the richest frame): one line per
snapshot in a raw append log:
  [u32 magic 'TRH1'][u64 ts_us][u32 ticks][f32 root_y][f32 root_vy]
  [f32 dimple_m][u64 wall_perf_us][u32 n][36n payload bytes]
plus a final JSON summary.

Usage: python truth_recorder.py --base http://127.0.0.1:PORT --out truth.bin
          [--stop-file path]  (recorder exits when the file appears)
"""
from __future__ import annotations

import argparse
import json
import struct
import time
import urllib.request

MAGIC = 0x31524831  # 'TRH1'


def pull_one(base: str) -> bytes:
    with urllib.request.urlopen(base + "/api/snapshot?fmt=FULL36", timeout=10) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stop-file", default=None)
    ap.add_argument("--max-s", type=float, default=120.0)
    a = ap.parse_args()

    t0 = time.perf_counter()
    n_frames = 0
    intervals = []
    prev_perf = None
    with open(a.out, "wb") as f:
        while time.perf_counter() - t0 < a.max_s:
            if a.stop_file:
                import os
                if os.path.exists(a.stop_file):
                    break
            t_pull = time.perf_counter()
            try:
                raw = pull_one(a.base)
            except OSError:
                time.sleep(0.005)
                continue
            ts_us, ticks = struct.unpack_from("<QI", raw, 4)
            root_y, root_vy, dimple = struct.unpack_from("<fff", raw, 16)
            wall_us = int(time.perf_counter() * 1e6)
            n = struct.unpack_from("<I", raw, 48)[0]
            hdr = struct.pack("<IQIfffQI", MAGIC, ts_us, ticks, root_y,
                              root_vy, dimple, wall_us, n)
            f.write(hdr)
            f.write(raw[52:52 + 36 * n])
            if prev_perf is not None:
                intervals.append(t_pull - prev_perf)
            prev_perf = t_pull
            n_frames += 1
    intervals.sort()
    summary = {
        "frames": n_frames,
        "window_s": round(time.perf_counter() - t0, 2),
        "median_interval_ms": round(1000 * intervals[len(intervals) // 2], 2) if intervals else None,
        "p95_interval_ms": round(1000 * intervals[int(0.95 * len(intervals))], 2) if intervals else None,
        "effective_hz": round(n_frames / (time.perf_counter() - t0), 2),
    }
    with open(a.out + ".summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
