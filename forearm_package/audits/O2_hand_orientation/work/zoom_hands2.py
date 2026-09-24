"""Tight crops of hand regions. CPU-only matplotlib Agg (gaming-safety rule)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

OUT = Path(r"E:\PythonChimera\forearm_package\audits\O2_hand_orientation\figures")
# (path, tag, [(x0,x1,y0,y1,label)])
JOBS = [
    (r"E:\PythonChimera\Saved\vision_trial\A_front_rest.png", "A_front_rest",
     [(980, 1260, 380, 640, "hand img-LEFT (creature R)"), (1300, 1580, 380, 640, "hand img-RIGHT (creature L)")]),
    (r"E:\PythonChimera\Saved\vision_trial\D_front_elbowL50.png", "D_front_elbowL50",
     [(980, 1260, 380, 640, "hand img-LEFT (creature R)"), (1300, 1580, 380, 640, "hand img-RIGHT (creature L)")]),
    (r"E:\PythonChimera\Saved\vision_trial\B_leftside_rest.png", "B_leftside_rest",
     [(640, 1920, 380, 700, "whole central band")]),
]
for path, tag, crops in JOBS:
    img = mpimg.imread(path)
    for k, (x0, x1, y0, y1, label) in enumerate(crops):
        crop = img[y0:y1, x0:x1]
        h, w = crop.shape[:2]
        scale = 4 if max(h, w) < 400 else 2
        fig, ax = plt.subplots(figsize=(w*scale/100, h*scale/100), dpi=100)
        ax.imshow(crop, interpolation="nearest")
        ax.set_title(f"{tag} {label} px[{x0}:{x1},{y0}:{y1}] x{scale}")
        ax.axis("off")
        fig.tight_layout()
        out = OUT / f"inventory_zoom_{tag}_{k}.png"
        fig.savefig(out)
        plt.close(fig)
        print("wrote", out)
