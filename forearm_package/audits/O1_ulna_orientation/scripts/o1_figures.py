"""O1 script 4 — FIGURES (preregistered method (b) + target profiles).

RENDERING LAW (GAMING-SAFETY, verbatim compliance): every figure is produced by
matplotlib with `import matplotlib; matplotlib.use("Agg")` called BEFORE any pyplot
import (pure software rasterizer). No OpenGL/Vulkan/WebGL/GPU context exists in this
audit. Figures DOCUMENT the identifications; the evidence is the measured receipts.

Explicit viewing axes (method (b)): each panel states the camera position, the view
direction, and the world direction of the screen's right/up, computed by
screen_right = view_dir x up_world, screen_up = screen_right x view_dir.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # BEFORE pyplot import — CPU-only software rendering
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

O1 = Path(r"E:\PythonChimera\forearm_package\audits\O1_ulna_orientation")
BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
STL = Path(r"E:\PythonChimera\vendor\myo_sim\meshes\ulna.stl")
sys.path.insert(0, str(O1 / "work"))

FLEX = {"BRA-P4", "BRA-P3", "PT-P2"}
SITES = {
    "TRIlong-P5": (-0.0219, 0.01046, -0.00078),
    "TRIlat-P5": (-0.0219, 0.01046, -0.00078),
    "TRImed-P5": (-0.0219, 0.01046, -0.00078),
    "ANC-P2": (-0.02532, -0.00124, 0.006),
    "BRA-P4": (-0.0032, -0.0239, 0.0009),
    "BRA-P3": (0.00498, -0.01463, 0.00128),
    "ECU-P2": (-0.01391, -0.03201, 0.02947),
    "ECU-P3": (-0.01705, -0.05428, 0.02868),
    "ECU-P4": (-0.01793, -0.09573, 0.03278),
    "PT-P2": (0.00846, -0.03373, -0.01432),
}
SCALE = np.array([1.0, 1.2, 1.0])


def load_stl_verts(path):
    b = path.read_bytes()
    n = struct.unpack("<I", b[80:84])[0]
    arr = np.frombuffer(b, np.uint8, count=50 * n, offset=84).reshape(n, 50)
    tri = arr[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(np.float64)
    return tri.reshape(-1, 3) * SCALE


def view_axes(f):
    """screen right/up for camera looking along f (world frame)."""
    up = np.array([0.0, 1.0, 0.0])
    r = np.cross(f, up)
    if np.linalg.norm(r) < 1e-9:
        r = np.array([1.0, 0.0, 0.0])
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return r, u


def compass_name(v):
    """SOURCE convention (+x forward/ANT, +y up, +z RIGHT side)."""
    x, y, z = v
    parts = []
    parts.append("ANT(+x)" if x > 0.3 else ("POST(-x)" if x < -0.3 else None))
    parts.append("UP(+y)" if y > 0.3 else ("DOWN(-y)" if y < -0.3 else None))
    parts.append("RIGHT(+z)" if z > 0.3 else ("LEFT(-z)" if z < -0.3 else None))
    return "+".join(p for p in parts if p)


def fig_source_views():
    V = load_stl_verts(STL)
    P = {k: np.array(v) for k, v in SITES.items()}
    views = [
        ("ANTERIOR view: camera at +x, looking along -x", np.array([-1.0, 0, 0])),
        ("POSTERIOR view: camera at -x, looking along +x", np.array([1.0, 0, 0])),
        ("RIGHT-LATERAL view (source right side = +z): camera at +z, looking along -z", np.array([0, 0, -1.0])),
        ("LEFT-LATERAL view: camera at -z, looking along +z", np.array([0, 0, 1.0])),
        ("SUPERIOR view: camera at +y, looking along -y", np.array([0, -1.0, 0])),
        ("INFERIOR view: camera at -y, looking along +y", np.array([0, 1.0, 0])),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    for ax, (title, f) in zip(axes.ravel(), views):
        r, u = view_axes(f)
        ax.scatter(V @ r, V @ u, s=0.3, c="lightgray")
        for name, p in P.items():
            col = "crimson" if name in FLEX else "royalblue"
            ax.scatter(p @ r, p @ u, s=42, c=col, zorder=5,
                       marker="o" if name in FLEX else "^")
        ax.set_title(title, fontsize=9)
        ax.text(0.02, 0.02, f"screen right = {compass_name(r)}   screen up = {compass_name(u)}",
                transform=ax.transAxes, fontsize=8,
                bbox=dict(facecolor="white", alpha=0.85))
        ax.set_aspect("equal")
        ax.grid(alpha=0.2)
    red = plt.Line2D([], [], color="crimson", marker="o", ls="", label="flexor compartment (volar, BRA/PT)")
    blu = plt.Line2D([], [], color="royalblue", marker="^", ls="", label="extensor compartment (dorsal, TRI/ANC/ECU)")
    axes[0, 0].legend(handles=[red, blu], loc="upper right", fontsize=8)
    fig.suptitle("SOURCE ulna (right) — bone mesh (vendor ulna.stl, scale 1,1.2,1; identity-tested) "
                 "+ 10 named sites, viewed along each anatomical axis (Agg)", fontsize=11)
    fig.tight_layout()
    out = O1 / "figures" / "o1_source_axes_views.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def fig_target_profiles():
    receipt = json.loads((O1 / "receipts" / "o1_target_sections_directed.json").read_text())
    R = receipt["sides"]["R"]
    fig = plt.figure(figsize=(15, 6.4))
    az = np.linspace(-180, 180, len(R["stations"][0]["profile_rho_max_by_bin_mm"]), endpoint=False)

    ax1 = fig.add_subplot(1, 2, 1, projection="polar")
    for st, lw in ((R["stations"][1], 1.2), (R["stations"][3], 1.2),
                   (R["stations"][6], 2.4), (R["stations"][10], 1.2)):
        rr = np.array([np.nan if v is None else v for v in st["profile_rho_max_by_bin_mm"]] +
                      [np.nan if R["stations"][1]["profile_rho_max_by_bin_mm"][0] is None else
                       R["stations"][1]["profile_rho_max_by_bin_mm"][0]])
        theta = np.radians(np.concatenate([az, [180.0]]))
        ax1.plot(theta, rr[:-1] if len(rr) > len(theta) else rr, lw=lw,
                 label=f"t={st['t_mm']:+.0f} mm (n={st['n']})")
    ax1.set_theta_zero_location("E")
    ax1.set_theta_direction(1)
    ax1.set_rlabel_position(0)
    ax1.set_title("TARGET right forearm: directed section radius rho(psi)\n"
                  "(azimuth in the C3 (e1,e2) basis: 0=+x LEFT, +90=+z ANTERIOR, "
                  "180=-x RIGHT, -90=-z POSTERIOR)", fontsize=9)
    ax1.legend(loc="lower right", fontsize=8)

    ax2 = fig.add_subplot(1, 2, 2)
    for side, col in (("R", "tab:red"), ("L", "tab:blue")):
        rows = [r for r in receipt["sides"][side]["stations"] if r["usable"]]
        ax2.errorbar([r["t_mm"] for r in rows], [r["D_post_minus_ant_mm"] for r in rows],
                     yerr=[r["boot_D_std_mm"] for r in rows], marker="o", color=col,
                     label=f"{side} side (mirror check)")
    ax2.axhline(2.0, color="k", ls="--", lw=1, label="preregistered threshold 2 mm (C3 camber scale)")
    ax2.axhline(0.0, color="gray", lw=0.8)
    ax2.set_xlabel("t along elbow->wrist axis [mm] (t<0 = proximal of the hinge)")
    ax2.set_ylabel("D = posterior sector radius - anterior sector radius [mm]")
    ax2.set_title("OLECRANON TEST: posterior(-z, az -90) vs anterior(+z, az +90)\n"
                  "elbow-region protrusion; error = bootstrap std (200 resamples)", fontsize=9)
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=8)
    fig.suptitle("Agg figures — documents the measured identification (evidence = receipts JSON)", fontsize=10)
    fig.tight_layout()
    out = O1 / "figures" / "o1_target_elbow_sections.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def main() -> int:
    p1 = fig_source_views()
    print("wrote", p1)
    p2 = fig_target_profiles()
    print("wrote", p2)
    (O1 / "receipts" / "o1_figures_note.txt").write_text(
        "Both figures produced with matplotlib Agg backend set BEFORE pyplot import "
        "(CPU-only software rasterizer); no GPU/OpenGL/Vulkan/WebGL context anywhere in this audit.\n"
        f"{p1.name}: method-(b) documentation — source bone + sites viewed along each anatomical axis, "
        "screen axes labeled per panel.\n"
        f"{p2.name}: method-(c) documentation — directed section profiles + the D(t) olecranon test.\n",
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
