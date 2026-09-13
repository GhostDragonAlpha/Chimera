"""leg_membranes.py -- author the LEGS as hinged membrane chains.

Three membranes per leg (thigh, shin, foot) joined at shared hinge
rings, pins from the measured live /joints (LEG_PREREGISTRATION.md).
Builds the whole scene blob (legs + feet) for /mesh_bin. Poses are
applied engine-side by /tick_pose (the tick's chain FK).
"""
from __future__ import annotations

import math
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np

COLOR = (0.80, 0.55, 0.35)

PINS = {  # measured, live /joints
    "hip_L":  (+0.1734, 3.4153, 0.1155), "hip_R":  (-0.1734, 3.4153, 0.1155),
    "knee_L": (+0.4833, 1.9033, -0.0155), "knee_R": (-0.4833, 1.9033, -0.0155),
    "ankle_L": (+0.4609, 0.3378, 0.0678), "ankle_R": (-0.4609, 0.3378, 0.0678),
}
THIGH_R, SHIN_R = 0.17, 0.13


def basis_along(d: np.ndarray):
    """Orthonormal (u, v) perpendicular to direction d."""
    fwd = d / np.linalg.norm(d)
    helper = np.array([1.0, 0, 0]) if abs(fwd[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(fwd, helper)
    u /= np.linalg.norm(u)
    v = np.cross(fwd, u)
    return u, v


def tube(a, b, radius, sides=8):
    """Open 8-sided tube from a to b (per-quad unwelded verts).
    Returns (verts, tris): 4*sides verts, 2*sides tris."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u, v = basis_along(b - a)
    verts, tris = [], []
    for i in range(sides):
        j = (i + 1) % sides
        ang_i, ang_j = 2 * math.pi * i / sides, 2 * math.pi * j / sides
        a0 = tuple(a + u * (math.cos(ang_i) * radius) + v * (math.sin(ang_i) * radius))
        b0 = tuple(b + u * (math.cos(ang_i) * radius) + v * (math.sin(ang_i) * radius))
        b1 = tuple(b + u * (math.cos(ang_j) * radius) + v * (math.sin(ang_j) * radius))
        a1 = tuple(a + u * (math.cos(ang_j) * radius) + v * (math.sin(ang_j) * radius))
        t = len(verts)
        verts.extend([(*a0, 0, 0, 0, 0, 0, 0), (*b0, 0, 0, 0, 0, 0, 0),
                      (*b1, 0, 0, 0, 0, 0, 0), (*a1, 0, 0, 0, 0, 0, 0)])
        tris.append((t, t + 1, t + 2))
        tris.append((t, t + 2, t + 3))
    return verts, tris


def foot_membrane(side_x_sign: int):
    """The B-FEET foot membrane (toes -z), centered on this side's ankle."""
    sys.path.insert(0, r"E:\ChimeraWork\slot-01\tools")
    from feet_membranes import build_foot
    v, t = build_foot(side_x_sign * 0.4609)
    v[:, 6:9] = COLOR
    return v, t


def leg_scene():
    """Builds the legs+feet scene blob AND the rig config (parts in
    dependency order). Returns (blob, rig_config)."""
    verts: list = []
    tris: list = []
    rig_lines: list = []
    total = 0

    def add(v, t):
        nonlocal total
        start = total
        tris.extend([tuple(i + total for i in tri) for tri in t])
        verts.extend(v)
        total += len(v)
        return start, len(v)

    rig: list = []
    for suffix, xs in (("L", 1.0), ("R", -1.0)):
        hip, knee, ankle = PINS[f"hip_{suffix}"], PINS[f"knee_{suffix}"], PINS[f"ankle_{suffix}"]
        mir = (lambda p: tuple(p[0] * xs if k == 0 else c for k, c in enumerate(p)))

        tv, tt = tube(hip, knee, THIGH_R)
        tv = [tuple(c * xs if k == 0 else c for k, c in enumerate(p)) for p in tv]
        s, c0 = add(tv, tt)
        rig.append((f"thigh_{suffix}", s, c0, mir(hip), -1))

        sv, st = tube(knee, ankle, SHIN_R)
        sv = [tuple(c * xs if k == 0 else c for k, c in enumerate(p)) for p in sv]
        s, c1 = add(sv, st)
        rig.append((f"shin_{suffix}", s, c1, mir(knee), len(rig) - 1))

        fv, ft = foot_membrane(xs)
        s, c2 = add(fv, ft)
        rig.append((f"foot_{suffix}", s, c2, mir(ankle), len(rig) - 1))

    arr_v = np.asarray(verts, dtype=np.float32)
    arr_v[:, 6:9] = COLOR
    header = struct.pack("<IIffff", len(arr_v), len(tris) * 3, 8.0, -0.7, 0.35, 0.0)
    blob = header + np.ascontiguousarray(arr_v).tobytes() \
        + np.ascontiguousarray(np.asarray(tris, dtype=np.uint32).reshape(-1)).tobytes()

    # rig lines reference indices by part order (parents first by build)
    index_of = {name: i for i, (name, _, _, _, _) in enumerate(rig)}
    for name, s, c, piv, parent in rig:
        parent_name = rig[parent][0] if parent >= 0 else ""
        rig_lines.append(f"{name}|{s}|{c}|{piv[0]:.4f}|{piv[1]:.4f}|{piv[2]:.4f}|"
                         f"{index_of.get(parent_name, -1)}")
    return blob, "\n".join(rig_lines) + "\n"


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8107"
    blob, rig = leg_scene()
    n = struct.unpack_from("<II", blob, 0)
    print(f"leg scene: verts={n[0]} idx={n[1]} bytes={len(blob)}")
    req = urllib.request.Request(base + "/mesh_bin", data=blob, method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=60) as r:
        print("POST ->", r.read().decode()[:50])
    req = urllib.request.Request(base + "/tick_rig", data=rig.encode(),
                                 method="POST",
                                 headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("rig POST ->", r.read().decode()[:50])
    return 0


if __name__ == "__main__":
    sys.exit(main())
