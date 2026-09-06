"""vision_trial.py — the P1 VL 30B A3B vision trial (2026-09-05).

The trial cannot be faked: every shot is captured at a KNOWN camera angle and
the posed-shot answer key comes from a MEASURED pixel differential, not taste.

Camera law (engine.cpp update_camera_matrices):
  eye = target + r*(cos(phi)*sin(theta), sin(phi), -cos(phi)*cos(theta))
Creature geometry (/joints): LEFT limbs sit at world +x (shoulder_L x=+1.04),
the face points toward +z (jaw J z=+0.98).
"""
import json, math, struct, sys, time, urllib.request
from PIL import Image
import numpy as np

BASE = "http://127.0.0.1:8090"
OUT = "Saved/vision_trial"

def get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.read()

def post(path, obj, timeout=10):
    req = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def set_cam(theta, phi, radius=26.0):
    print(post("/camera", {"cam_radius": radius, "cam_theta": theta, "cam_phi": phi}))
    time.sleep(0.9)  # let the render thread consume + settle

def capture(name):
    png = get("/frame")
    path = f"{OUT}/{name}.png"
    with open(path, "wb") as f:
        f.write(png)
    print(f"captured {path} ({len(png)//1024} KB)")
    return path

import os
os.makedirs(OUT, exist_ok=True)

# 1) release show ownership of the pose, park the pose joint at rest
print(post("/joints", {"on": False}))
print(post("/joint", {"joint": "elbow_L", "theta": 0.0}))
time.sleep(0.6)

# 2) three rest shots at known angles
shots = {}
set_cam(math.pi, 0.12)          # FRONT: camera on +z, facing the face
shots["A_front"] = capture("A_front_rest")
set_cam(math.pi / 2, 0.12)      # CREATURE'S-LEFT side: camera on +x
shots["B_leftside"] = capture("B_leftside_rest")
set_cam(math.pi / 4, 0.30)      # 3/4 from the left-front quarter, elevated
shots["C_threeq"] = capture("C_threeq_rest")

# 3) the pose question: elbow_L flexion 50 deg (hand curls toward the face)
print(post("/joint", {"joint": "elbow_L", "theta": 50.0}))
time.sleep(0.6)
set_cam(math.pi, 0.12)
shots["D_posed"] = capture("D_front_elbowL50")
print(post("/joint", {"joint": "elbow_L", "theta": 0.0}))  # restore

# 4) the measured answer key: which image half moved?
a = np.asarray(Image.open(shots["A_front"]).convert("L"), dtype=np.int16)
d = np.asarray(Image.open(shots["D_posed"]).convert("L"), dtype=np.int16)
diff = np.abs(a - d) > 12
h, w = diff.shape
left_px, right_px = int(diff[:, : w // 2].sum()), int(diff[:, w // 2 :].sum())
top_px, bot_px = int(diff[: h // 2, :].sum()), int(diff[h // 2 :, :].sum())
print("\n=== MEASURED ANSWER KEY (never shown to the model) ===")
print(f"changed px  image-left {left_px}  vs  image-right {right_px}")
print(f"changed px  image-top  {top_px}  vs  image-bottom {bot_px}")
side = "image-RIGHT (their left, facing us)" if right_px > left_px * 3 else \
       ("image-LEFT" if left_px > right_px * 3 else "AMBIGUOUS — check shots")
print(f"the bent elbow appears on the {side}")
json.dump({"A": shots["A_front"], "B": shots["B_leftside"], "C": shots["C_threeq"],
           "D": shots["D_posed"], "key": {"left_px": left_px, "right_px": right_px}},
          open(f"{OUT}/trial_manifest.json", "w"), indent=1)
print(f"\nmanifest -> {OUT}/trial_manifest.json")
