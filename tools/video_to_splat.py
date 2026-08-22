"""video_to_splat.py — VIDEO PHOTOGRAMMETRY: a phone video of a real object -> photoreal 3DGS.

WHY (operator directive, 2026-08-19): video is "the only reliable source of visual data" —
single-image AI generation is rejected, and a video orbit around a real object is the
real-capture route to a photoreal splat (the SOURCE step's first lane).

THEORY (Rule 0):
  STATEMENT  — a slow orbit video (object static, lighting constant, ~200 sharp frames)
               gives COLMAP enough parallax to solve the cameras, and gsplat enough views
               to train a photoreal cloud.
  PREDICTION — the trained splat renders novel views indistinguishable from held-out frames.
  FALSIFIER  — if COLMAP registers < ~80% of frames or the render blurs/ghosts vs a held-out
               frame, the capture was bad (motion blur / too few views / moving light), not
               the trainer. Re-capture slower, closer, with the object lit and STILL.

PIPELINE (each stage resumable; paths relative to --dir):
    frames    ffmpeg: video -> frames/ (~--frames target, sharp frames)
    sfm       COLMAP (tools/colmap): feature -> sequential match -> map -> undistort
    train     gsplat simple_trainer (tools/gsplat/examples) -> ckpt
    export    ckpt -> .ply -> 32-byte .splat (engine/web-viewer format)

Requires: tools/colmap/COLMAP.bat (4.1.1 CUDA), .venv-gs (torch cu128 + gsplat + pycolmap),
ffmpeg on PATH. The trainer JIT-compiles its CUDA ops on first run (needs MSVC + CUDA 12.8).

Usage (from the repo root):
    python tools/video_to_splat.py frames path/to/orbit.mp4 --dir capture/myobject
    python tools/video_to_splat.py sfm    --dir capture/myobject
    python tools/video_to_splat.py train  --dir capture/myobject --steps 30000
    python tools/video_to_splat.py export --dir capture/myobject --out models/capture/myobject.splat
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLMAP = ROOT / "tools" / "colmap" / "COLMAP.bat"
VENV_PY = ROOT / ".venv-gs" / "Scripts" / "python.exe"
GSPLAT = ROOT / "tools" / "gsplat" / "examples"
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


def _run(cmd: list[str], **kw):
    print("+", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def _duration(video: Path) -> float:
    out = subprocess.run([FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(video)], capture_output=True, text=True,
                         check=True).stdout.strip()
    return float(out)


def stage_frames(video: Path, workdir: Path, n_frames: int):
    frames = workdir / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    fps = max(1.0, n_frames / _duration(video))
    _run([FFMPEG, "-y", "-i", video, "-vf", f"fps={fps:.3f}", "-qscale:v", "2",
          frames / "%04d.png"])
    print(f"frames -> {frames} ({len(list(frames.glob('*.png')))} at {fps:.2f} fps)")


def stage_sfm(workdir: Path):
    """COLMAP SfM on the extracted frames: sequential matching (video frames are ordered),
    then undistort to PINHOLE images for the trainer."""
    db = workdir / "colmap" / "database.db"
    sparse = workdir / "colmap" / "sparse"
    dense = workdir / "colmap" / "dense"
    sparse.mkdir(parents=True, exist_ok=True)
    dense.mkdir(parents=True, exist_ok=True)
    _run([COLMAP, "feature_extractor", "--database_path", db,
          "--image_path", workdir / "frames", "--ImageReader.single_camera", "1"])
    _run([COLMAP, "sequential_matcher", "--database_path", db,
          "--SequentialMatching.loop_detection", "1",
          "--SequentialMatching.quadratic_overlap", "1"])
    _run([COLMAP, "mapper", "--database_path", db,
          "--image_path", workdir / "frames", "--output_path", sparse])
    # The mapper can emit several disconnected models (sparse/0, 1, 2, ...) and they are
    # NOT size-ordered (seen live: 4 / 10 / 250 images). Undistort the LARGEST one.
    models = [d for d in sparse.iterdir() if d.is_dir() and (d / "images.bin").exists()]
    if not models:
        raise SystemExit("COLMAP produced no model — capture failed the gate (see THEORY).")
    model = max(models, key=lambda d: (d / "images.bin").stat().st_size)
    print(f"sfm: {len(models)} model(s), using {model.name} "
          f"(images.bin {(model / 'images.bin').stat().st_size} bytes)")
    _run([COLMAP, "image_undistorter", "--image_path", workdir / "frames",
          "--input_path", model, "--output_path", dense, "--output_type", "COLMAP"])
    # trainer layout: images/ + sparse/0/
    data = workdir / "data"
    data.mkdir(exist_ok=True)
    if (data / "images").exists():
        shutil.rmtree(data / "images")
    if (data / "sparse").exists():
        shutil.rmtree(data / "sparse")
    shutil.move(str(dense / "images"), data / "images")
    shutil.copytree(dense / "sparse", data / "sparse")
    registered = len(list((data / "images").glob("*.png")))
    total = len(list((workdir / "frames").glob("*.png")))
    print(f"sfm: {registered}/{total} frames registered")
    if registered < 0.8 * total:
        print("WARNING: < 80% registered — the capture gate says re-shoot (see THEORY).")
    print(f"data -> {data}")


def stage_train(workdir: Path, steps: int):
    result = workdir / "train_out"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(GSPLAT) + os.pathsep + env.get("PYTHONPATH", "")
    # gsplat JIT-compiles its CUDA kernels on first use; give it the toolchain.
    env.setdefault("CUDA_HOME", r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8")
    env.setdefault("CUDA_PATH", env["CUDA_HOME"])
    env.setdefault("TORCH_CUDA_ARCH_LIST", "8.9")
    # torch's extension loader spawns `ninja` by name — put the venv's Scripts on PATH.
    env["PATH"] = str(VENV_PY.parent) + os.pathsep + env.get("PATH", "")
    # If a first-ever JIT compile is needed, MSVC must be on PATH — run this
    # stage via tools/train_capture.bat (vcvars64 wrapper) in that case.
    _run([VENV_PY, GSPLAT / "simple_trainer.py", "default",
          "--data_dir", (workdir / "data").resolve(), "--result_dir", result.resolve(),
          "--data_factor", "1", "--max_steps", str(steps), "--save_ply",
          "--disable_viewer"],
         cwd=GSPLAT, env=env)
    print(f"train -> {result}")


def stage_export(workdir: Path, out: Path, steps: int):
    """train_out/ply/*.ply (--save_ply at 7k + final) -> 32-byte .splat (ply_to_splat.py)."""
    plys = sorted((workdir / "train_out" / "ply").glob("*.ply"),
                  key=lambda p: int("".join(c for c in p.stem if c.isdigit()) or 0))
    if not plys:
        raise SystemExit("no ply in train_out/ply — run train first (it passes --save_ply)")
    _run([ROOT / ".venv" / "Scripts" / "python.exe",
          ROOT / "ChimeraEngine" / "native" / "ply_to_splat.py", plys[-1], "--out", out])
    print(f"splat -> {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["frames", "sfm", "train", "export"])
    ap.add_argument("video", nargs="?", default=None, help="frames: input video")
    ap.add_argument("--dir", required=True, help="capture workdir")
    ap.add_argument("--frames", type=int, default=250, help="frames: target frame count")
    ap.add_argument("--steps", type=int, default=30_000, help="train: max steps")
    ap.add_argument("--out", default=None, help="export: output .splat")
    a = ap.parse_args()
    workdir = Path(a.dir)
    workdir.mkdir(parents=True, exist_ok=True)

    if a.stage == "frames":
        if not a.video:
            raise SystemExit("frames needs a video path")
        stage_frames(Path(a.video), workdir, a.frames)
    elif a.stage == "sfm":
        stage_sfm(workdir)
    elif a.stage == "train":
        stage_train(workdir, a.steps)
    else:
        stage_export(workdir, Path(a.out) if a.out else workdir / "export.splat", a.steps)


if __name__ == "__main__":
    main()
