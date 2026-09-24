"""O2 figures — explicit-axis documentation figures (Agg, CPU-only).

Figure 1 (source): hand_r viewed along the 27-geom plane normal BOTH ways, plus
signed-offset side views (fitted plane and raw local z), compartments colored.
Figure 2 (target): paddle face profiles vs station with chords, frozen window
shaded, thickness lens inset; R and L panels.

matplotlib with Agg set BEFORE pyplot import (gaming-safety rule; no GPU contexts).
Reads receipts/o2_source_sign.json and receipts/o2_target_curvature.json, plus the
XML for geom positions.  Writes only into figures/.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gaming-safety: software renderer, BEFORE pyplot import
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
XML = BASE / "source_xml" / "chimanoid.xml"
HERE = Path(r"E:\PythonChimera\forearm_package\audits\O2_hand_orientation")
FIG = HERE / "figures"

FLEX = ["FCR-P3", "FCU-P4"]
EXT = ["ECRB-P4", "ECRL-P4", "ECU-P6"]
COLOR = {"flexor": "#c62828", "extensor": "#1565c0"}
COMP = {**{k: "flexor" for k in FLEX}, **{k: "extensor" for k in EXT}}


def _vec(text):
    return np.array([float(v) for v in (text or "").split()], dtype=np.float64)


def _quat_to_rotmat(q):
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def walk(elem, parent_world, parent_rot, geoms_by_body, sites_by_body):
    name = elem.get("name")
    pos = _vec(elem.get("pos", "0 0 0"))
    quat = _vec(elem.get("quat", "1 0 0 0"))
    rot = parent_rot @ _quat_to_rotmat(quat)
    world = parent_world + parent_rot @ pos
    for s in elem.findall("site"):
        sites_by_body.setdefault(name, {})[s.get("name")] = _vec(s.get("pos", "0 0 0"))
    for g in elem.findall("geom"):
        if g.get("type") == "mesh":
            geoms_by_body.setdefault(name, []).append(
                (g.get("name"), _vec(g.get("pos", "0 0 0"))))
    for child in elem.findall("body"):
        walk(child, world, rot, geoms_by_body, sites_by_body)


def source_figure():
    rec = json.load(open(HERE / "receipts" / "o2_source_sign.json"))
    r = rec["hands"]["right"]
    gb, sb = {}, {}
    root = ET.parse(str(XML)).getroot()
    for b in root.find("worldbody").findall("body"):
        walk(b, np.zeros(3), np.eye(3), gb, sb)
    names27 = [nm for nm, _ in gb["hand_r"]]
    P27 = np.array([p for _, p in gb["hand_r"]])
    c = np.array(r["centroid_local"])
    n = np.array(r["normal_unit_undirected"])
    off = r["site_offsets_m"]
    a_len = P27[names27.index("3distph")]
    a_len = a_len / np.linalg.norm(a_len)
    e_u = a_len - n * (n @ a_len)
    e_u = e_u / np.linalg.norm(e_u)          # in-plane length coordinate
    e_v = np.cross(n, e_u)

    snames = ["ECRL-P4", "ECRB-P4", "ECU-P6", "FCR-P3", "FCU-P4"]
    spts = {sn: sb["hand_r"][sn] for sn in snames}

    fig = plt.figure(figsize=(16, 11), dpi=115)
    fig.suptitle(
        "O2 source palm-sign documentation — hand_r (27-geom palm plane of C3; sites NEVER in construction)\n"
        f"plane normal n27 (undirected) = ({n[0]:+.4f}, {n[1]:+.4f}, {n[2]:+.4f}) in hand_r local frame; "
        f"geom residual rms {r['geom_resid_rms_m']*1000:.1f} mm; FROZEN split result: MIXED (see report)",
        fontsize=11)

    # (A) view along +n27: observer on the -n27 side looking toward +n27
    ax = fig.add_subplot(2, 2, 1)
    ax.set_title("A. observer on the -n27 side, looking ALONG +n27 (arrow n27 points away from viewer)\n"
                 "screen right = +e_u (hand length axis, in-plane), screen up = +e_v = n27 x e_u", fontsize=9)
    ax.scatter((P27 - c) @ e_u, (P27 - c) @ e_v, s=14, c="#9e9e9e", label="27 skeleton geoms")
    for sn, p in spts.items():
        ax.scatter((p - c) @ e_u, (p - c) @ e_v, s=110, marker="^" if COMP[sn] == "flexor" else "o",
                   c=COLOR[COMP[sn]], edgecolors="k", zorder=5)
        ax.annotate(f"{sn}\n{off[sn]*1000:+.1f} mm", ((p - c) @ e_u, (p - c) @ e_v),
                    textcoords="offset points", xytext=(8, 4), fontsize=8, color=COLOR[COMP[sn]])
    ax.scatter([0], [0], marker="+", s=140, c="k", label="plane centroid")
    ax.axhline(0, color="k", lw=0.4); ax.axvline(0, color="k", lw=0.4)
    ax.set_xlabel("in-plane coordinate along e_u = hand length axis (m)")
    ax.set_ylabel("in-plane coordinate along e_v = n27 x e_u (m)")
    ax.legend(loc="lower left", fontsize=8)

    # (B) view along -n27: observer on the +n27 side looking toward -n27
    ax = fig.add_subplot(2, 2, 2)
    ax.set_title("B. observer on the +n27 side, looking ALONG -n27 (mirror of A)\n"
                 "screen right = -e_u, screen up = +e_v", fontsize=9)
    ax.scatter(-((P27 - c) @ e_u), (P27 - c) @ e_v, s=14, c="#9e9e9e", label="27 skeleton geoms")
    for sn, p in spts.items():
        ax.scatter(-((p - c) @ e_u), (p - c) @ e_v, s=110, marker="^" if COMP[sn] == "flexor" else "o",
                   c=COLOR[COMP[sn]], edgecolors="k", zorder=5)
        ax.annotate(f"{sn}\n{off[sn]*1000:+.1f} mm", (-((p - c) @ e_u), (p - c) @ e_v),
                    textcoords="offset points", xytext=(8, 4), fontsize=8, color=COLOR[COMP[sn]])
    ax.scatter([0], [0], marker="+", s=140, c="k")
    ax.axhline(0, color="k", lw=0.4); ax.axvline(0, color="k", lw=0.4)
    ax.set_xlabel("in-plane coordinate along -e_u (m)")
    ax.set_ylabel("in-plane coordinate along e_v (m)")

    # (C) side view: SIGNED offset along n27 vs in-plane length coordinate
    ax = fig.add_subplot(2, 2, 3)
    lu = (P27 - c) @ e_u
    ld = (P27 - c) @ n
    ax.set_title("C. signed offset along n27 (m) vs in-plane length coordinate e_u (m)\n"
                 "grey = the 27 geoms' own residuals (plane band); zero line = the fitted plane", fontsize=9)
    ax.scatter(lu * 1000, ld * 1000, s=8, c="#bdbdbd", label="27 geoms (residuals)")
    ax.axhline(0, color="k", lw=0.8)
    for sn, p in spts.items():
        y = off[sn] * 1000
        x = ((p - c) @ e_u) * 1000
        ax.scatter([x], [y], s=110, marker="^" if COMP[sn] == "flexor" else "o",
                   c=COLOR[COMP[sn]], edgecolors="k", zorder=5)
        ax.annotate(f"{sn} {y:+.1f}", (x, y), textcoords="offset points", xytext=(8, 4),
                    fontsize=8, color=COLOR[COMP[sn]])
    ax.set_xlabel("e_u: hand length axis coordinate (mm)  [3distph direction, in-plane]")
    ax.set_ylabel("SIGNED offset along n27 (mm)\n(+ = the side FCU-P4 sits on; FROZEN result: FCR-P3 lies on the opposite side)")
    ax.legend(loc="lower left", fontsize=8)
    ax.text(0.02, 0.97, "FROZEN TEST: MIXED compartment signs\n(clean-split criterion FALSE; stop rule -> BLOCKER)",
            transform=ax.transAxes, va="top", fontsize=9, color="#b71c1c",
            bbox=dict(fc="#ffebee", ec="#b71c1c", alpha=0.9))

    # (D) construction-free raw local z
    ax = fig.add_subplot(2, 2, 4)
    ax.set_title("D. DIAGNOSTIC (not the frozen test): raw local z of sites vs length coordinate\n"
                 "zero line = hand_r origin plane; L/R mirror symmetry proves z IS the palmar-dorsal axis", fontsize=9)
    zr = np.array([p[2] for p in P27]) * 1000
    ax.scatter(lu * 1000, zr, s=8, c="#bdbdbd", label="27 geoms")
    ax.axhline(0, color="k", lw=0.8)
    rz = r["raw_local_z_m"]
    for sn in snames:
        x = ((spts[sn] - c) @ e_u) * 1000
        y = rz[sn] * 1000
        ax.scatter([x], [y], s=110, marker="^" if COMP[sn] == "flexor" else "o",
                   c=COLOR[COMP[sn]], edgecolors="k", zorder=5)
        ax.annotate(f"{sn} {y:+.1f}", (x, y), textcoords="offset points", xytext=(8, 4),
                    fontsize=8, color=COLOR[COMP[sn]])
    ax.set_xlabel("e_u: hand length axis coordinate (mm)")
    ax.set_ylabel("raw local z (mm)  [construction-free; flexors all z<0, extensors all z>0: CLEAN 3/2]")
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = FIG / "o2_source_plane_views.png"
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)


def target_figure():
    rec = json.load(open(HERE / "receipts" / "o2_target_curvature.json"))
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), dpi=115)
    fig.suptitle(
        "O2 target palm-sign documentation — wrist-distal paddle profiles along the elbow->wrist axis (C2/C3 stationing)\n"
        "+T = e1 (fixed rule: rejection of global +x on the plane orthogonal to a); FROZEN window = distal half [55.65, 111.3] mm",
        fontsize=11)
    for col, side in ((0, "R"), (1, "L")):
        r = rec[side]
        p = r["profile"]
        t = np.array(p["t_mm"])
        lo, hi = r["frozen_window_mm"]
        ax = axes[0][col]
        ax.set_title(f"side {side}: face profiles vs station (+T = {np.round(r['basis_e1_plusT'], 3).tolist()} m/m)\n"
                     f"mid-line sag {r['D2_midline_signed_sagitta_mm']:+.2f} mm; D1 = {r['D1_sagitta_difference_mm']:+.2f} mm "
                     f"(trimmed {r['trimmed_window_diagnostic']['D1_mm']:+.2f} mm); FROZEN threshold 1 mm", fontsize=9)
        ax.axvspan(lo, hi, color="#fff9c4", alpha=0.6, label="FROZEN distal-half window")
        ax.plot(t, p["tmax_mm"], "-", c=COLOR["extensor"], lw=1.6, label="+T face (tmax)")
        ax.plot(t, p["tmin_mm"], "-", c=COLOR["flexor"], lw=1.6, label="-T face (tmin)")
        ax.plot(t, p["centroid_T_mm"], "-", c="#2e7d32", lw=1.8, label="mid-line (section centroid)")
        # chords over the frozen window
        m = (t >= lo) & (t <= hi)
        for arr, cc, ls in ((p["tmax_mm"], "#ef9a9a", ":"), (p["tmin_mm"], "#90caf9", ":"),
                            (p["centroid_T_mm"], "#a5d6a7", ":")):
            y = np.array(arr)[m]
            ax.plot(t[m], np.interp(t[m], [lo, hi], [y[0], y[-1]]), ls, c=cc, lw=1.2)
        ax.set_xlabel("station along a from wrist (mm)")
        ax.set_ylabel("coordinate along +T (mm)")
        ax.legend(fontsize=8, loc="upper left")
        ax2 = axes[1][col]
        ax2.set_title(f"side {side}: thickness profile (lens/wedge, NOT uniform bending)\n"
                      "uniform bend would keep thickness constant; rim collapse in the last ~7 mm drives max-dev D1", fontsize=9)
        ax2.plot(t, p["thickness_mm"], "-o", ms=2.5, c="#6a1b9a", lw=1.4)
        ax2.axvspan(lo, hi, color="#fff9c4", alpha=0.6)
        ax2.set_xlabel("station along a from wrist (mm)")
        ax2.set_ylabel("section thickness (mm)")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    out = FIG / "o2_target_paddle_profiles.png"
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    source_figure()
    target_figure()
