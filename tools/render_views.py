"""Render N standard views of a .splat through the running engine (HTTP :8090).

Uploads once via /membrane_bin, then moves the camera with /camera per view.
"""
import argparse
import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402

VIEWS = {
    "front": (3.14159, 0.15),
    "side": (1.5708, 0.15),
    "back": (0.0, 0.15),
    "high": (3.14159, 1.2),
}


def cam_pos(radius, theta, phi):
    return (radius * math.cos(phi) * math.sin(theta),
            radius * math.sin(phi),
            -radius * math.cos(phi) * math.cos(theta))


def set_camera(radius, theta, phi, timeout=10.0):
    body = json.dumps({"cam_radius": radius, "cam_theta": theta, "cam_phi": phi}).encode()
    req = urllib.request.Request(f"{cb.ENGINE_URL}/camera", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status == 200


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("splat")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--radius", type=float, default=1.8)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    buf = cb.load_splat(args.splat)
    print(f"loaded {len(buf)} splats")

    first = VIEWS["front"]
    ok = cb._post_membrane_bin(len(buf), cam_pos(args.radius, *first), buf, timeout=180.0)
    print("upload:", "ok" if ok else "FAILED")

    from pathlib import Path
    for name, (theta, phi) in VIEWS.items():
        if name != "front":
            set_camera(args.radius, theta, phi)
        png = cb.fetch_frame(timeout=60.0)
        path = Path(args.out_dir) / f"{name}.png"
        path.write_bytes(png)
        print(f"{name}: {path} ({len(png)} bytes)")


if __name__ == "__main__":
    main()
