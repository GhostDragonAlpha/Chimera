"""feet_splat_membrane.py -- the foot membranes as SPLATS through the
certified /membrane_bin pipeline (the membrane system, not the skin mesh).

FEET PREREGISTRATION (e8c96bfd): sole plane y = 0, toes -z, ankles at
(+/-0.4609, 0.3378, 0.0678), foot 0.78 x 0.39, ankle 30% from the heel.
The foot membrane renders as splat grain: the five outer faces of the
foot wedge (sole, heel, toe, two sides) surfaced at ~0.09 spacing with
isotropic sigma ~= half the spacing -- a solid grounded surface, open on
top where the leg enters. Skin color measured from the creature.

Reversible: --restore re-posts the teddy mesh (the game view).
"""
from __future__ import annotations

import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np

ANKLE_L = (+0.4609, 0.3378, 0.0678)
ANKLE_R = (-0.4609, 0.3378, 0.0678)
FOOT_LEN, FOOT_W = 0.78, 0.39
HEEL_DZ = FOOT_LEN * 0.30
TOE_DZ = FOOT_LEN * 0.70
COLLAR_Y = 0.30
SPACING = 0.09
SIGMA = SPACING * 0.55
SKIN = (0.80, 0.55, 0.35)


def face_splats(p0, p1, p2, p3):
    """A rectangular face (4 corners) surfaced with a splat grid."""
    out = []
    u = (np.asarray(p1) - np.asarray(p0))
    v = (np.asarray(p3) - np.asarray(p0))
    nu = max(2, int(round(np.linalg.norm(u) / SPACING)))
    nv = max(2, int(round(np.linalg.norm(v) / SPACING)))
    for i in range(nu + 1):
        for j in range(nv + 1):
            p = np.asarray(p0) + u * (i / nu) + v * (j / nv)
            out.append(p)
    return out


def build_feet() -> np.ndarray:
    rows = []
    for ax, ay, az in (ANKLE_L, ANKLE_R):
        hw = FOOT_W / 2.0
        hz, tz = az + HEEL_DZ, az - TOE_DZ
        hwi = hw * 0.45
        sole = [(ax - hw, 0.0, hz), (ax + hw, 0.0, hz),
                (ax + hw, 0.0, tz), (ax - hw, 0.0, tz)]
        collar = [(ax - hwi, COLLAR_Y, hz), (ax + hwi, COLLAR_Y, hz),
                  (ax + hwi, COLLAR_Y, tz), (ax - hwi, COLLAR_Y, tz)]
        faces = [
            sole,                                   # sole: the contact plane
            [collar[0], collar[1], sole[1], sole[0]],   # heel wall
            [collar[2], collar[3], sole[3], sole[2]],   # toe wall
            [collar[0], sole[0], sole[3], collar[3]],   # left wall
            [collar[1], collar[2], sole[2], sole[1]],   # right wall
        ]
        for f in faces:
            for p in face_splats(*f):
                rows.append((*p, *SKIN, 1.0, SIGMA, SIGMA, SIGMA, 1.0, 0.0, 0.0, 0.0))
    return np.asarray(rows, dtype=np.float32)


def post_membrane_bin(base: str, buf14: np.ndarray, cam=(3.2, -0.7, 0.42)) -> None:
    n = buf14.shape[0]
    r, theta, phi = cam
    payload = struct.pack("<I3f", n, r, theta, phi) + \
        np.ascontiguousarray(buf14, dtype=np.float32).tobytes()
    req = urllib.request.Request(base + "/membrane_bin", data=payload,
                                 method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode()
        if '"ok":true' not in body:
            raise SystemExit(f"membrane_bin rejected: {body[:120]}")
        print(f"membrane_bin: {n} splats accepted")


def restore_mesh(release: Path, base: str) -> None:
    blob = (release / "session_snapshot" / "mesh_bin.blob").read_bytes()
    req = urllib.request.Request(base + "/mesh_bin", data=blob, method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        print("mesh restored ->", resp.read().decode()[:40])


def capture(base: str, out: Path) -> None:
    with urllib.request.urlopen(base + "/frame", timeout=30) as r:
        out.write_bytes(r.read())
    print("frame captured:", out)


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8107"
    mode = sys.argv[2] if len(sys.argv) > 2 else "load"
    release = Path(r"E:\ChimeraWork\slot-05\.tmp\engine_build"
                   r"\roottranslation-BASE\Release")
    proof = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\FEET")
    proof.mkdir(parents=True, exist_ok=True)

    if mode == "restore":
        restore_mesh(release, base)
        capture(base, proof / "after_restore_mesh.png")
        return 0

    buf = build_feet()
    print(f"foot membranes: {buf.shape[0]} splats, "
          f"y range [{buf[:, 1].min():.4f}, {buf[:, 1].max():.4f}] "
          f"(sole plane 0.0)")
    post_membrane_bin(base, buf)
    time.sleep(1)
    capture(base, proof / "feet_membrane_frame.png")
    return 0


import time  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())



