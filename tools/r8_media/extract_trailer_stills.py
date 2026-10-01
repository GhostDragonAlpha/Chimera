"""extract_trailer_stills.py -- D2 R8 MEDIA: stills from the R7 trailer.

Pulls single frames with ffmpeg out of the DELIVERED trailer
(C:/Users/allen/Desktop/CHIMERA_PROOF/TRAILER/chimera_trailer.mp4, 28.04 s,
1920x1080 -- already 1080p, no crop or resize) at the three beats the
motion-absent defect is judged on:

    trailer_press_peak.png  ~16.2 s   the 30 kN belly press at full dent
    trailer_healing.png     ~19.5 s   the release -- tau = 0.5 s healing
    trailer_end_card.png    ~26.3 s   the end card

Then writes a 1280-px JPG preview of EVERY asset in R8_MEDIA (the previews
are the review surface; the PNGs stay the deliverable).

Run: python tools/r8_media/extract_trailer_stills.py
Output: C:/Users/allen/Desktop/CHIMERA_PROOF/R8_MEDIA/
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image

TRAILER = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\TRAILER\chimera_trailer.mp4")
OUT = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\R8_MEDIA")
PREVIEW_W = 1280

# (seconds, filename) -- the trailer's spine: press peak, heal, end card
BEATS = [
    (16.2, "trailer_press_peak.png"),
    (19.5, "trailer_healing.png"),
    (26.3, "trailer_end_card.png"),
]


def extract() -> None:
    if not TRAILER.exists():
        raise SystemExit(f"trailer not found: {TRAILER}")
    OUT.mkdir(parents=True, exist_ok=True)
    for t, name in BEATS:
        dst = OUT / name
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-ss", f"{t:.3f}", "-i", str(TRAILER),
               "-frames:v", "1", str(dst)]
        subprocess.run(cmd, check=True)
        img = Image.open(dst)
        print(f"  {name}  @ {t:.2f}s  {img.size[0]}x{img.size[1]}")


def previews() -> None:
    """A 1280-px JPG preview beside every full-res PNG in R8_MEDIA."""
    for png in sorted(OUT.glob("*.png")):
        if png.stem.endswith("_preview"):
            continue
        img = Image.open(png).convert("RGB")
        if img.width <= PREVIEW_W:
            scaled = img
        else:
            h = int(round(img.height * PREVIEW_W / img.width))
            scaled = img.resize((PREVIEW_W, h), Image.LANCZOS)
        dst = OUT / f"{png.stem}_preview.jpg"
        scaled.save(dst, quality=88)
        print(f"  {dst.name}  <- {png.name}")


if __name__ == "__main__":
    print("extracting trailer stills ...")
    extract()
    print("writing 1280-px previews ...")
    previews()
    print("done.")
