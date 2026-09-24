"""figure_fit.py — static inspection figure of the ACTUAL monkey fit.

Panels: front (x lateral / y vertical) and side (z sagittal / y vertical).
Contents: the birth mesh (grey), the pack joints (dark), the resolved segment
skeletons with their fitted axial scales (blue), the forearm outer-envelope
bands (green, SKIN constraint — not internal anatomy), and the unresolved
coordinate anchors (orange x). No inference is drawn from the picture; it is a
static record of where the box said things are.

Run:  python figure_fit.py   -> runs/figure_actual_fit.png
"""
from __future__ import annotations

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from aspect_bounds import POLICED_FLAG
from mesh_target import MonkeyTarget
from synthetic_fixtures import load_real
from actual_target_fit import build_correspondence_envelope
from intake import global_site_positions

OUT = r"E:\PythonChimera\.tmp\anatomy_compiler\runs\figure_actual_fit.png"
SUBSAMPLE = 12000

# distal (wrist) joint of the forearm pair, and their measured skin-envelope medians
FOREARM_JOINTS = {"radius": "wrist_R", "radius_l": "wrist_L"}


def main() -> int:
    real = load_real()
    mt = MonkeyTarget()
    sw = global_site_positions(real)
    corr, _notes = build_correspondence_envelope(real, mt, sw)
    from compiler import fit

    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG)

    J = mt.J
    rng = np.random.default_rng(7)
    V = mt.V[rng.choice(len(mt.V), min(SUBSAMPLE, len(mt.V)), replace=False)]

    cseg_by = {s.source_body: s for s in corr.segments}
    scales = {s.source_body: (np.asarray(s.scale), s.status) for s in f.segments}
    flags = {k.split(".")[1] for k in f.residuals if k.startswith("aspect_flag")}
    flags = {b for b in flags if any(s.source_body == b and s.status == "flagged_aspect" for s in f.segments)}
    envelopes = f.measurements.get("outer_envelope", {})

    fig, axes = plt.subplots(1, 2, figsize=(15, 8.5))
    views = {
        "front (x lateral, y up)": (0, 1),
        "side (z sagittal, y up)": (2, 1),
    }
    for ax, (title, (x, y)) in zip(axes, views.items()):
        ax.scatter(V[:, x], V[:, y], s=1.0, c="#bbbbbb", alpha=0.35, linewidths=0)
        ax.scatter(J[:, x], J[:, y], s=8, c="#111111", zorder=5, label="pack joint")
        for body in sorted(scales):
            seg = cseg_by[body]
            sc, status = scales[body]
            p0 = corr.landmarks[seg.proximal_landmark]
            p1 = corr.landmarks[seg.distal_landmark]
            col = "#c0392b" if body in flags else "#1a5276"
            ax.plot([p0[x], p1[x]], [p0[y], p1[y]], "-", color=col, lw=3, zorder=6)
            ax.scatter([p0[x], p1[x]], [p0[y], p1[y]], s=60, marker="o", color=col, zorder=7)
            ax.text(
                np.mean([p0[x], p1[x]]), np.mean([p0[y], p1[y]]),
                f"{sc[0]:.3f}", color=col, fontsize=8, zorder=8,
                ha="center", va="center", bbox=dict(facecolor="white", alpha=0.7, pad=0.5),
            )
        # forearm outer-envelope SKIN constraint at the wrist: a bounding box around
        # the measured interior width (green, labeled SKIN) — never internal geometry
        for body, joint in FOREARM_JOINTS.items():
            env = envelopes.get(body)
            if env is None or joint not in mt.idx:
                continue
            p1 = mt.joint_pos(joint)
            wb = env["per_axis"]["b"]["median"]
            wc = env["per_axis"]["c"]["median"]
            angs = np.linspace(0, 2 * np.pi, 40)
            rx, ry = 0.5 * wb, 0.5 * wc
            pts = np.stack([p1[x] + rx * np.cos(angs), p1[y] + ry * np.sin(angs)], axis=1)
            ax.plot(pts[:, 0], pts[:, 1], "g-", lw=1.4, zorder=4)
            ax.text(p1[x], p1[y], "SKIN", color="#117a3a", fontsize=7, zorder=9,
                    ha="center", va="center", bbox=dict(facecolor="white", alpha=0.85, pad=0.5))
        for u in f.unresolved_segments:
            body = u["body"]
            seg = cseg_by.get(body)
            if seg is None:
                continue
            p = corr.landmarks[seg.proximal_landmark]
            ax.plot(p[x], p[y], "x", color="#e67e22", ms=11, mew=2, zorder=6)
        r0 = corr.landmarks["root"]
        ax.scatter(r0[x], r0[y], s=90, marker="*", c="#000000", zorder=8)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("x" if x == 0 else "z", fontsize=9)
        ax.set_ylabel("y", fontsize=9)
        ax.set_aspect("equal")
    handles = [
        plt.Line2D([0], [0], color="#1a5276", lw=3, label="resolved segment (label = axial scale)"),
        plt.Line2D([0], [0], color="#c0392b", lw=3, label="aspect-FLAGGED (radius b/c)"),
        plt.Line2D([0], [0], color="#117a3a", lw=1.6, label="forearm SKIN envelope (outer; not internal)"),
        plt.Line2D([0], [0], marker="x", color="#e67e22", ls="none", ms=11, mew=2, label="unresolved anchor"),
        plt.Line2D([0], [0], marker="o", color="#111111", ls="none", ms=6, label="pack joint"),
        plt.Line2D([0], [0], marker="*", color="#000000", ls="none", ms=14, label="root (spine_lower)"),
    ]
    adm = f.admission.get("counts", {})
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8.5, frameon=False)
    fig.suptitle(
        f"Chimera anatomy fit vs actual monkey   (mesh unit x {0.065} m)   chirality +1, "
        f"{adm.get('geometrically_resolved', len(f.segments))} resolved / "
        f"{adm.get('unresolved', len(f.unresolved_segments))} unresolved, "
        f"{adm.get('transported_under_assumption', 0)} transported under assumption "
        f"(physically admitted 0; flags: {sorted(flags) or 'none'}; pelvis = root-reference frame, not scaled)",
        fontsize=10.5,
    )
    fig.tight_layout(rect=(0, 0.07, 1, 0.93))
    fig.savefig(OUT, dpi=150)
    print(f"figure -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())