"""b4_common — shared setup for B4 challenge scripts (read-only over the baseline).

Loads the baseline artifacts from the snapshot ONLY. Never writes into
baseline_snapshot. No fitting, no moment arms, no path lengths (T6 process law).
"""
from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

B4 = Path(r"E:/PythonChimera/forearm_package/audits/B4_correspondence_challenge")
SNAP = Path(r"E:/PythonChimera/forearm_package/baseline_snapshot")
RECEIPTS = B4 / "receipts"
RECEIPTS.mkdir(exist_ok=True)

XML_PATH = SNAP / "source_xml" / "chimanoid.xml"
PACKET_PATH = SNAP / "runs" / "actual_monkey_fit.json"
MESH_PATH = SNAP / "inputs" / "monkey_birth.bin"
PACK_PATH = SNAP / "inputs" / "monkey_joints.bin"
MANIFEST_PATH = SNAP / "MANIFEST.json"

sys.path.insert(0, str(B4 / "work" / "modules"))

# constants cited by the protocol (measured from the baseline, with locations)
ROLL_EPS = 1e-9       # compiler.py:48  (axis_parallel_roll floor)
JOINT_EPS = 1e-9      # compiler.py:47  (shared-joint closure, F1)
RECON_TOL_M = 1e-6    # protocol preregistration (step-A bound)
ORTHO_CONSTRUCTED = 1e-12
ORTHO_PACKET = 1e-9
DET_TOL = 1e-12
DEGENERATE_FLOOR = 1e-12
SCALE_BAND_FACTOR = 2.0
T5_LOG_MARGIN = float(np.log(2.0))


def load_packet() -> dict:
    with open(PACKET_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_xml_tree():
    """(bodies, parent_of, sites_of) from LIVE elements only (ElementTree drops
    XML comments, so the commented duplicate bodies in the source are excluded
    automatically — matching the intake law)."""
    root = ET.parse(str(XML_PATH)).getroot()
    bodies: dict[str, dict] = {}

    def walk(el, parent):
        for b in el.findall("body"):
            name = b.get("name")
            sites = [s.get("name") for s in b.findall("site") if s.get("name")]
            pos = np.array([float(v) for v in b.get("pos", "0 0 0").split()])
            bodies[name] = {"parent": parent, "sites": sites, "pos_local": pos}
            walk(b, name)

    wb = root.find("worldbody")
    walk(wb, None)
    parent_of = {n: d["parent"] for n, d in bodies.items()}
    sites_of = {n: list(d["sites"]) for n, d in bodies.items()}
    return bodies, parent_of, sites_of


def onb(p0: np.ndarray, p1: np.ndarray, q: np.ndarray):
    """DERIVATION 5.1 ONB construction (same procedure as compiler.onb_from_points;
    reimplemented locally so the challenge never imports the fitting machinery)."""
    a = p1 - p0
    n = np.linalg.norm(a)
    if n < DEGENERATE_FLOOR:
        raise ValueError("degenerate bone")
    a = a / n
    t = (q - p0) - a * (a @ (q - p0))
    tnorm = float(np.linalg.norm(t))
    if tnorm < ROLL_EPS:
        raise ValueError("axis_parallel_roll")
    b = t / tnorm
    c = np.cross(a, b)
    B = np.column_stack([a, b, c])
    assert abs(np.linalg.det(B) - 1.0) <= 1e-9
    return B


def verdict(name: str, ok: bool, detail: str = "") -> str:
    line = f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else "")
    print(line)
    return line


def save_receipt(name: str, payload: dict) -> Path:
    def enc(o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        return float(o)

    p = RECEIPTS / name
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=enc)
    return p
