#!/usr/bin/env python3
"""Extract frames from Lane C orbit video for AnySplat."""
import os
import argparse
from pathlib import Path
import imageio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="capture/genbear3/laneC_ltx.mp4")
    ap.add_argument("--out", default="capture/genbear3/laneC_frames")
    ap.add_argument("--stride", type=int, default=2, help="keep 1 of every N frames")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    reader = imageio.get_reader(args.video)
    meta = reader.get_meta_data()
    fps = meta.get("fps", 24)
    total = reader.count_frames()
    print(f"[extract] {args.video}: {total} frames @ {fps} fps, stride {args.stride}")

    kept = 0
    for i, frame in enumerate(reader):
        if i % args.stride == 0:
            out_path = out_dir / f"frame_{kept:05d}.png"
            imageio.imwrite(out_path, frame)
            kept += 1
    reader.close()
    print(f"[extract] kept {kept} frames in {out_dir}")


if __name__ == "__main__":
    main()
