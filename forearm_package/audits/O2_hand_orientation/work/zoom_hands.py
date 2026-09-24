"""Zoom crops of existing repo images (Saved/vision_trial) hand regions.
CPU-only: matplotlib Agg before pyplot import (gaming-safety rule). Read-only on inputs."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

SRC = [
    (r"E:\PythonChimera\Saved\vision_trial\A_front_rest.png", "A_front_rest"),
    (r"E:\PythonChimera\Saved\vision_trial\D_front_elbowL50.png", "D_front_elbowL50"),
    (r"E:\PythonChimera\Saved\vision_trial\C_threeq_rest.png", "C_threeq_rest"),
    (r"E:\PythonChimera\Saved\vision_trial\B_leftside_rest.png", "B_leftside_rest"),
]
OUT = Path(r"E:\PythonChimera\forearm_package\audits\O2_hand_orientation\figures")
for path, tag in SRC:
    img = mpimg.imread(path)
    h, w = img.shape[:2]
    fig, axes = plt.subplots(1, 2, figsize=(16, 9), dpi=120)
    half = w // 2
    for ax, (x0, x1), label in ((axes[0], (0, half), "image-LEFT (creature's RIGHT side)"),
                                (axes[1], (half, w), "image-RIGHT (creature's LEFT side)")):
        crop = img[int(h*0.25):int(h*0.48), x0:x1]
        ax.imshow(crop, interpolation="nearest")
        ax.set_title(f"{tag} {label}  crop rows {int(h*0.25)}:{int(h*0.48)} of {h}")
        ax.axis("off")
    fig.suptitle(f"{path}  (existing repo image, read-only; w={w}, h={h})")
    fig.tight_layout()
    out = OUT / f"inventory_zoom_{tag}.png"
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out, "src", w, "x", h)
