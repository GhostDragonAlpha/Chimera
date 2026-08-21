"""prep_co3d_sfm.py -- CO3D sequence WITHOUT known cameras -> gsplat dataset.

The teddybear_002 set zips carry images/masks/depths/pointcloud but NO camera
annotations. So the cameras are RECOVERED: COLMAP SfM (the video_to_splat lane)
on the raw frames, then the CO3D masks black out the background so the trainer
spends its gaussians on the bear (same treatment as the known-camera lane).

  .venv-gs/Scripts/python.exe tools/prep_co3d_sfm.py --seq 246_26300_51362 \
      --workdir capture/co3d/sfm_246_26300_51362

Then: tools/video_to_splat.py train --dir <workdir> && export.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from video_to_splat import stage_sfm  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seq", required=True)
    ap.add_argument("--workdir", required=True)
    a = ap.parse_args()

    src = ROOT / "capture/co3d/teddybear" / a.seq
    workdir = Path(a.workdir)
    frames = workdir / "frames"
    frames.mkdir(parents=True, exist_ok=True)

    imgs = sorted((src / "images").glob("*.jpg"))
    for i, f in enumerate(imgs):
        dst = frames / f"{i+1:04d}.png"   # ordered names: sequential_matcher needs order
        if not dst.exists():
            Image.open(f).save(dst)
        # keep the mask mapping by new name
    print(f"frames <- {len(imgs)} images")

    stage = workdir / "data" / "images"
    if stage.exists():
        print("sfm output exists -- skipping COLMAP")
    else:
        stage_sfm(workdir)  # COLMAP: feature -> sequential match -> map -> undistort

    # black-mask the undistorted training images (CO3D mask per original frame)
    data_imgs = workdir / "data" / "images"
    applied = 0
    for f in sorted(data_imgs.glob("*.png")):
        orig = imgs[int(f.stem) - 1]
        mask_p = src / "masks" / (orig.stem + ".png")
        if not mask_p.exists():
            continue
        img = np.array(Image.open(f).convert("RGB"))  # np.array: writable copy
        msk = np.asarray(Image.open(mask_p).convert("L").resize(img.shape[1::-1])) > 127
        img[~msk] = 0
        Image.fromarray(img).save(f)
        applied += 1
    print(f"masked {applied} training images; dataset -> {workdir/'data'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
