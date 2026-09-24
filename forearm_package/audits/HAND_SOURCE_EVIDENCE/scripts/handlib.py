"""Shared library for HAND_SOURCE_EVIDENCE (R2 Form A). stdlib + numpy only."""
from __future__ import annotations

import hashlib
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

XML = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot\source_xml\chimanoid.xml")
VENDOR = Path(r"E:\PythonChimera\vendor\myo_sim\meshes")
OUT = Path(r"E:\PythonChimera\forearm_package\audits\HAND_SOURCE_EVIDENCE")

# the 27 right-hand bones in XML declaration order (L635-661)
BONES = ["pisiform", "lunate", "scaphoid", "triquetrum", "hamate", "capitate",
         "trapezoid", "trapezium", "1mc", "2mc", "3mc", "4mc", "5mc",
         "thumbprox", "thumbdist", "2proxph", "2midph", "2distph",
         "3proxph", "3midph", "3distph", "4proxph", "4midph", "4distph",
         "5proxph", "5midph", "5distph"]
# frozen chain links (prereg 2.4): parent -> child (child anchor on parent surface)
CHAIN = [("1mc", "thumbprox"), ("thumbprox", "thumbdist"),
         ("2mc", "2proxph"), ("2proxph", "2midph"), ("2midph", "2distph"),
         ("3mc", "3proxph"), ("3proxph", "3midph"), ("3midph", "3distph"),
         ("4mc", "4proxph"), ("4proxph", "4midph"), ("4midph", "4distph"),
         ("5mc", "5proxph"), ("5proxph", "5midph"), ("5midph", "5distph"),
         ("trapezium", "1mc"), ("trapezoid", "2mc"), ("capitate", "3mc"),
         ("hamate", "4mc"), ("hamate", "5mc")]
PLATE = ["pisiform", "lunate", "scaphoid", "triquetrum", "hamate", "capitate",
         "trapezoid", "trapezium", "2mc", "3mc", "4mc", "5mc"]
ANCHOR_THRESH = 0.0035  # 3.5 mm anchor class (prereg 2.4)

# frozen site table (chimanoid.xml L663-667), hand_r local, metres
SITES = {
    "ECRL-P4": ((0.021167, -0.036274, 0.008159), "extensor"),
    "ECRB-P4": ((0.008989, -0.026413, 0.010824), "extensor"),
    "ECU-P6": ((-0.018514, -0.029067, 0.001049), "extensor"),
    "FCR-P3": ((0.015227, -0.033494, -0.001851), "flexor"),
    "FCU-P4": ((-0.016364, -0.032707, -0.005191), "flexor"),
}


def parse_hand_xml():
    """geom name -> pos anchor (metres, hand_r local); plus left-side mirrors,
    mesh-asset scale/file attrs, and the hand_r world origin via the body chain."""
    root = ET.parse(XML).getroot()
    world = root.find("worldbody")

    geoms, bodies = {}, {}
    def walk2(body, offs):
        pos = np.array([float(v) for v in body.get("pos", "0 0 0").split()])
        q = body.get("quat")
        if q is not None:
            assert all(abs(float(v) - v0) < 1e-12
                       for v, v0 in zip(q.split(), [1.0, 0.0, 0.0, 0.0])), body.get("name")
        offs = offs + pos
        bodies[body.get("name")] = offs.copy()
        for g in body.findall("geom"):
            if g.get("type") == "mesh":
                geoms[g.get("name")] = np.array(
                    [float(v) for v in g.get("pos", "0 0 0").split()])
        for ch in body.findall("body"):
            walk2(ch, offs)
    walk2(world, np.zeros(3))

    hand_r_anchor = {b: geoms[b] for b in BONES if b in geoms}
    hand_l_anchor = {b + "_l": geoms[b + "_l"] for b in BONES if b + "_l" in geoms}
    sites_r = {}
    hand_r_body = None
    # sites live inside hand_r body; find via raw text line numbers instead: use ET
    for body in world.iter("body"):
        if body.get("name") == "hand_r":
            hand_r_body = body
    assert hand_r_body is not None
    for s in hand_r_body.findall("site"):
        if s.get("name") in SITES:
            sites_r[s.get("name")] = np.array([float(v) for v in s.get("pos").split()])

    meshes = {}
    am = root.find("asset")
    for m in am.findall("mesh"):
        meshes[m.get("name")] = {"file": m.get("file"),
                                 "scale": [float(v) for v in m.get("scale").split()]}
    return hand_r_anchor, hand_l_anchor, sites_r, meshes, bodies


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_stl(path: Path):
    """Return (tris (n,3,3) float64 in STL coordinates, meta dict). Binary or ASCII."""
    b = path.read_bytes()
    meta = {"bytes": len(b)}
    if len(b) >= 84 and struct.unpack("<I", b[80:84])[0] * 50 + 84 == len(b):
        n = struct.unpack("<I", b[80:84])[0]
        arr = np.frombuffer(b, dtype=np.uint8, count=50 * n, offset=84).reshape(n, 50)
        tri = arr[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(np.float64)
        meta.update({"format": "binary", "n_tri": int(n)})
        return tri, meta
    txt = b.decode("ascii", errors="replace")
    vs = np.array([[float(x) for x in m] for m in
                   re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", txt)], dtype=np.float64)
    assert len(vs) % 3 == 0, path
    meta.update({"format": "ascii", "n_tri": int(len(vs) // 3)})
    return vs.reshape(-1, 3, 3), meta


def point_tri_closest(p, a, b, c):
    """closest point on triangle abc to p (Ericson)."""
    ab, ac = b - a, c - a
    ap = p - a
    d1, d2 = ab @ ap, ac @ ap
    if d1 <= 0 and d2 <= 0:
        return a
    bp = p - b
    d3, d4 = ab @ bp, ac @ bp
    if d3 >= 0 and d4 <= d3:
        return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        t = d1 / (d1 - d3)
        return a + t * ab
    cp = p - c
    d5, d6 = ab @ cp, ac @ cp
    if d6 >= 0 and d5 <= d6:
        return c
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        t = d2 / (d2 - d6)
        return a + t * ac
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        t = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return b + t * (c - b)
    denom = 1.0 / (va + vb + vc)
    return a + ab * (vb * denom) + ac * (vc * denom)


def closest_on_mesh(p, tris, tri_cen, cell=0.02):
    d = np.linalg.norm(tri_cen - p, axis=1)
    cand = np.where(d <= d.min() + 3 * cell)[0]
    best, bp, bi = 1e9, None, -1
    for i in cand:
        a, b, c = tris[i]
        q = point_tri_closest(p, a, b, c)
        dd = float(np.linalg.norm(q - p))
        if dd < best:
            best, bp, bi = dd, q, int(i)
    return best, bp, bi
