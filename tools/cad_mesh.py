#!/usr/bin/env python
"""cad_mesh.py -- PRIMS -> skinned GLB. No AI, no trained assets: pure geometry.

Every part in cad_core.PRIMS becomes:
  - one watertight tessellated primitive (ellipsoid = scaled UV sphere,
    capsule = cylinder + hemisphere caps), with analytic normals;
  - one glTF material (the part's measured color);
  - one BONE at the part's pivot (capsules pivot at the a-end, ellipsoids at
    center), parented torso-root -> limbs/head -- the membrane hierarchy;
  - rigid skin weights (v1; smooth joint blending is a later milestone).

Frame: canonical is +Y up / face +Z, which is exactly the glTF convention, so
positions pass through unchanged; UE's Interchange glTF importer converts to
its own frame on import. Units: meters (glTF standard).

  .venv-gs/Scripts/python.exe tools/cad_mesh.py [out.glb]
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cad_core import PRIMS  # the measured part table -- single source of truth

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "models" / "cad_bear" / "cad_bear.glb"

SEG = 48   # around -- faceting sagitta << INER_TOL/4 (run-2: 28-seg faceting
RING = 32  # pole to pole   ate half the inertia tolerance by itself)


# ---------------------------------------------------------------- tessellation
def uv_ellipsoid(c, r, sole=None):
    c, r = np.asarray(c, float), np.asarray(r, float)
    vs, ns = [], []
    if sole is None:
        phi_max = np.pi
        cap = False
    else:
        # flat-soled variant: rings stop at the cut phi (cos phi = -sole),
        # then one degenerate ring at the cap center closes the flat face
        # (same winding convention as the -Y pole row: cap faces down/out)
        phi_max = float(np.arccos(-sole))
        cap = True
    for i in range(RING + 1):
        phi = phi_max * i / RING       # 0..phi_max, +Y pole to cut/pole
        for j in range(SEG):
            th = 2 * np.pi * j / SEG
            d = np.array([np.sin(phi) * np.cos(th), np.cos(phi), np.sin(phi) * np.sin(th)])
            vs.append(c + d * r)
            ns.append(d / (r * r))
    nrows = RING + 1
    if cap:
        for j in range(SEG):           # cap center row (flat face, normal -Y)
            vs.append(c + np.array([0.0, -sole * r[1], 0.0]))
            ns.append(np.array([0.0, -1.0, 0.0]))
        nrows += 1
    v = np.asarray(vs, np.float32)
    nrm = np.asarray(ns, np.float32)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    return v, nrm, _grid_indices(nrows, SEG)


def capsule(a, b, rad):
    a, b = np.asarray(a, float), np.asarray(b, float)
    w = b - a
    L = np.linalg.norm(w)
    w /= L
    ref = np.array([0.0, 0.0, 1.0]) if abs(w[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(w, ref); u /= np.linalg.norm(u)
    v2 = np.cross(w, u)
    vs, ns = [], []
    rows = RING // 2  # hemisphere rings per cap
    # Row order is one continuous surface -- NO duplicated seam rings
    # (run-1 bug: duplicated equator rings made a spurious interior cone,
    # silently eating ~25% of the volume while rendering fine):
    #   bottom cap pole -> equator@a | cylinder wall (one band) | equator@b -> top pole
    for i in range(rows + 1):                       # bottom cap: phi pi -> pi/2
        phi = np.pi - (np.pi / 2) * i / rows
        for j in range(SEG):
            th = 2 * np.pi * j / SEG
            d = np.cos(phi) * w + np.sin(phi) * (np.cos(th) * u + np.sin(th) * v2)
            vs.append(a + rad * d); ns.append(d)
    for j in range(SEG):                            # cylinder end ring at b
        th = 2 * np.pi * j / SEG
        d = np.cos(th) * u + np.sin(th) * v2
        vs.append(b + rad * d); ns.append(d)
    for i in range(rows + 1):                       # top cap: phi pi/2 -> 0
        phi = np.pi / 2 - (np.pi / 2) * i / rows
        for j in range(SEG):
            th = 2 * np.pi * j / SEG
            d = np.cos(phi) * w + np.sin(phi) * (np.cos(th) * u + np.sin(th) * v2)
            vs.append(b + rad * d); ns.append(d)
    v = np.asarray(vs, np.float32)
    nrm = np.asarray(ns, np.float32)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    nrows = 2 * (rows + 1) + 1
    return v, nrm, _grid_indices(nrows, SEG)


def _grid_indices(nrows, seg):
    idx = []
    for i in range(nrows - 1):
        for j in range(seg):
            j2 = (j + 1) % seg
            a, b_, c_, d = i * seg + j, i * seg + j2, (i + 1) * seg + j2, (i + 1) * seg + j
            idx += [a, c_, b_, a, d, c_]
    return np.asarray(idx, np.uint32)


# ---------------------------------------------------------------- bones
def pivot_of(p):
    return np.asarray(p["a"] if p["kind"] == "cap" else p["c"], float)

# parent bone name per part: torso is root; head-family and sweater ride the
# torso; limbs chain shoulder->paw / hip->foot. (groups come from cad_core.)
PARENT = {
    "torso": None,
    "head": "torso", "ear_L": "head", "ear_R": "head", "muzzle": "head",
    "eye_L": "head", "eye_R": "head", "nose": "head",
    "arm_L": "torso", "paw_L": "arm_L",
    "arm_R": "torso", "paw_R": "arm_R",
    "leg_L": "torso", "foot_L": "leg_L",
    "leg_R": "torso", "foot_R": "leg_R",
    "sweater_body": "torso", "sleeve_L": "arm_L", "sleeve_R": "arm_R",
}


# ---------------------------------------------------------------- GLB writer
def build_glb(path: Path) -> None:
    bin_chunks: list[bytes] = []
    accessors, bufviews, materials, prims_out = [], [], [], []
    nodes, joints = [], []

    def push(data: bytes, target: int) -> int:
        while sum(len(c) for c in bin_chunks) % 4:
            bin_chunks.append(b"\x00")
        off = sum(len(c) for c in bin_chunks)
        bin_chunks.append(data)
        bufviews.append({"buffer": 0, "byteOffset": off, "byteLength": len(data), "target": target})
        return len(bufviews) - 1

    def acc(bv: int, ctype: str, count: int, atype: str, mn=None, mx=None) -> int:
        a = {"bufferView": bv, "componentType": ctype, "count": count, "type": atype}
        if mn is not None:
            a["min"], a["max"] = mn, mx
        accessors.append(a)
        return len(accessors) - 1

    FLOAT, UINT32, USHORT = 5126, 5125, 5123
    ARR34962, ARR34963, ARR = 34962, 34963, None

    # one node per part = one bone
    name2joint = {}
    for i, p in enumerate(PRIMS):
        name2joint[p["name"]] = i
        nodes.append({"name": p["name"], "translation": [float(x) for x in pivot_of(p)]})
        joints.append(i)

    # world rest position of each joint (for IBM = translate(-world_pos);
    # bones carry no rest rotation, and pivots are defined in canonical space)
    world = {}
    for p in PRIMS:
        par = PARENT[p["name"]]
        world[p["name"]] = pivot_of(p)  # translations are ABSOLUTE in PRIMS
    # make node translations relative to parent
    for p in PRIMS:
        par = PARENT[p["name"]]
        if par:
            rel = world[p["name"]] - world[par]
            nodes[name2joint[p["name"]]]["translation"] = [float(x) for x in rel]
            nodes[name2joint[par]].setdefault("children", []).append(name2joint[p["name"]])

    # inverse bind matrices: pure translation (no rest rotation)
    ibm = np.zeros((len(PRIMS), 16), np.float32)
    for p in PRIMS:
        m = np.eye(4, dtype=np.float32)
        m[:3, 3] = -world[p["name"]]
        ibm[name2joint[p["name"]]] = m.T.flatten()  # glTF matrices are column-major
    ibm_acc = acc(push(ibm.tobytes(), ARR or 0), FLOAT, len(PRIMS), "MAT4")
    bufviews[-1].pop("target", None)

    for p in PRIMS:
        if p["kind"] == "ell":
            v, nrm, idx = uv_ellipsoid(p["c"], p["r"], p.get("sole"))
        else:
            v, nrm, idx = capsule(p["a"], p["b"], p["rad"])

        j = np.zeros((len(v), 4), np.uint16)
        j[:, 0] = name2joint[p["name"]]
        wts = np.zeros((len(v), 4), np.float32)
        wts[:, 0] = 1.0

        pa = acc(push(v.tobytes(), ARR34962), FLOAT, len(v), "VEC3",
                 mn=[float(x) for x in v.min(0)], mx=[float(x) for x in v.max(0)])
        na = acc(push(nrm.tobytes(), ARR34962), FLOAT, len(v), "VEC3")
        ja = acc(push(j.tobytes(), ARR34962), USHORT, len(v), "VEC4")
        wa = acc(push(wts.tobytes(), ARR34962), FLOAT, len(v), "VEC4")
        ia = acc(push(idx.tobytes(), ARR34963), UINT32, len(idx), "SCALAR")

        col = p["color"]
        materials.append({"name": p["name"], "pbrMetallicRoughness": {
            "baseColorFactor": [col[0], col[1], col[2], 1.0],
            "metallicFactor": 0.0, "roughnessFactor": 0.9}})
        prims_out.append({"attributes": {"POSITION": pa, "NORMAL": na,
                                         "JOINTS_0": ja, "WEIGHTS_0": wa},
                          "indices": ia, "material": len(materials) - 1})

    skin = {"inverseBindMatrices": ibm_acc, "joints": joints,
            "skeleton": name2joint["torso"]}
    mesh_node = {"name": "cad_bear", "mesh": 0, "skin": 0}

    gltf = {
        "asset": {"version": "2.0", "generator": "chimera cad_mesh (pure geometry)"},
        "scene": 0,
        "scenes": [{"nodes": [name2joint["torso"], len(nodes)]}],
        "nodes": nodes + [mesh_node],
        "meshes": [{"name": "cad_bear", "primitives": prims_out}],
        "skins": [skin],
        "materials": materials,
        "accessors": accessors,
        "bufferViews": bufviews,
        "buffers": [],
    }
    binblob = b"".join(bin_chunks)
    gltf["buffers"] = [{"byteLength": len(binblob)}]

    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    while len(binblob) % 4:
        binblob += b"\x00"
    total = 12 + 8 + len(js) + 8 + len(binblob)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(binblob), 0x004E4942) + binblob)
    print(f"WROTE {path}: {len(PRIMS)} parts/bones, "
          f"{sum(a['count'] for a in accessors if a['type'] == 'VEC3' and a.get('min'))} verts, "
          f"{path.stat().st_size} bytes")


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    build_glb(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
