"""gen_orbit_video.py — AI-GENERATED ORBIT VIDEO: one still image -> a 360 orbit clip.

WHY (operator directive, 2026-08-19): instead of filming a real object, generate the
capture video with Seedance 2.5 (via the operator's FAL.ai subscription) — a single,
3D-consistent, continuous camera orbit around a static object. The output feeds
`tools/video_to_splat.py` exactly like real footage.

THEORY (Rule 0):
  STATEMENT  — Seedance 2.5 image-to-video, anchored on one still and prompted for a
               slow single-shot 360-degree orbit with the object frozen and the lighting
               fixed, produces frames consistent enough for COLMAP to solve the cameras.
  PREDICTION — COLMAP registers >= 80% of extracted frames (the video_to_splat capture
               gate) and the trained splat renders the back that the single still never
               showed.
  FALSIFIER  — if COLMAP registers < 80%, the video drifts/morphs (AI inconsistency),
               not the pipeline: re-generate with a stricter prompt ("locked object,
               no deformation") or a shorter duration.

Anchor image: any good front view (e.g. models/imagegen/tpose2_640.png). Sent as a
base64 data URI. Needs FAL_KEY in the environment (operator's fal.ai account).

Usage (from the repo root):
    set FAL_KEY=...   (Windows)  /  export FAL_KEY=...   (bash)
    python tools/gen_orbit_video.py path/to/front.png --name myobject [--seconds 30]
"""
from __future__ import annotations

import argparse
import base64
import mimetypes
import os
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# The prompt IS the capture protocol: object frozen, lighting fixed, camera does all
# the moving, one continuous shot, nothing enters or leaves the frame.
ORBIT_PROMPT = (
    "Single continuous unbroken shot. The camera slowly orbits a full 360 degrees "
    "around the object at constant height and constant distance, one complete circle, "
    "ending exactly where it started: the final frame is identical to the first frame. "
    "The object is a rigid inanimate statue: it stays perfectly still, no pose change, "
    "no breathing, no squashing, no deformation, no change in any detail. Lighting "
    "stays constant and even. Pure black void background, no floor, no reflections, "
    "no environment. Sharp focus, no motion blur, no cuts, no zoom, no people, "
    "nothing enters or leaves the frame."
)


def _black_bg_anchor(image: Path, out: Path) -> Path:
    """Composite the anchor onto a pure black void (removes white-studio background,
    which Seedance otherwise preserves and which destroys the silhouette carve)."""
    from PIL import Image
    img = Image.open(image).convert("RGBA")
    # flood-key: treat near-white as background
    px = np.asarray(img).astype(np.int16)
    white = (px[:, :, 0] > 235) & (px[:, :, 1] > 235) & (px[:, :, 2] > 235)
    img.putalpha(Image.fromarray(np.where(white, 0, 255).astype(np.uint8)))
    black = Image.new("RGBA", img.size, (0, 0, 0, 255))
    black.alpha_composite(img)
    black.convert("RGB").save(out)
    return out


def _data_uri(image: Path) -> str:
    mime = mimetypes.guess_type(image.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(image.read_bytes()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path, help="anchor still (front view of the object)")
    ap.add_argument("--name", required=True, help="capture name -> capture/<name>/orbit.mp4")
    ap.add_argument("--seconds", default="30", help="4-30 (default 30 — one slow orbit)")
    ap.add_argument("--resolution", default="1080p", choices=["480p", "720p", "1080p"])
    ap.add_argument("--prompt", default=ORBIT_PROMPT)
    ap.add_argument("--black-bg", action="store_true",
                    help="composite the anchor onto pure black first (kills white-studio bg)")
    a = ap.parse_args()

    if not os.environ.get("FAL_KEY"):
        raise SystemExit("FAL_KEY not set — get it from your fal.ai dashboard keys page.")

    import fal_client

    out_dir = ROOT / "capture" / a.name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / "orbit.mp4"

    anchor = a.image
    if a.black_bg:
        anchor = _black_bg_anchor(a.image, out_dir / "anchor_black.png")
        print(f"black-bg anchor -> {anchor}")

    print(f"submitting: {anchor} -> seedance-2.5/image-to-video ({a.seconds}s, {a.resolution}, high bitrate, loop-closed)")
    result = fal_client.subscribe(
        "bytedance/seedance-2.5/image-to-video",
        arguments={
            "prompt": a.prompt,
            "image_url": _data_uri(anchor),
            "end_image_url": _data_uri(anchor),   # 360 orbit closes the loop: last == first
            "resolution": a.resolution,
            "duration": str(a.seconds),
            "bitrate_mode": "high",
            "generate_audio": False,
        },
        with_logs=True,
    )
    url = result["video"]["url"]
    print(f"seed={result.get('seed')}  video={url}")
    urllib.request.urlretrieve(url, out_mp4)
    print(f"saved -> {out_mp4}")
    print("next: tools\\train_capture.bat frames " + str(out_mp4) + f" --dir capture/{a.name}")


if __name__ == "__main__":
    main()
