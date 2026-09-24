"""figure_forearm_candidates.py — ENLARGED forearm attachment-candidate figures.

Session-5 rendering contract:
  COLOUR = placement status under the FINAL loop authority
           (inside=green, inside_insufficient_clearance=amber, outside=red,
            unresolved/ambiguous=grey);
  MARKER SHAPE = tendon-path role
           (filled circle = first/last ENDPOINT, hollow circle = waypoint).

All positions are fitted target metres read from the packet; the hull of the
session-4 band sampling is drawn as a light diagnostic next to the identified
skin loop. No inference is drawn from the picture; it is a static record.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUNS = Path(r"E:\PythonChimera\.tmp\anatomy_compiler\runs")
OUT = RUNS / "figure_forearm_candidates.png"

STATUS_COLOR = {
    "inside": "#1e8449",
    "inside_insufficient_clearance": "#d68910",
    "outside": "#c0392b",
    "unresolved": "#7f8c8d",
    "not_measured": "#bdc3c7",
}


def main() -> int:
    packet = json.loads((RUNS / "actual_monkey_fit.json").read_text(encoding="utf-8"))
    cand = json.loads((RUNS / "attachment_candidates.json").read_text(encoding="utf-8"))
    for f in ("attachment_candidates.json", "actual_monkey_fit.json"):
        if not (RUNS / f).exists():
            print(f"MISSING {f} — run actual_target_fit.py first")
            return 1

    meas = packet["measurements"]
    section_hulls = {
        body: {s["t"]: s["hull_bc"] for s in env["sections"]}
        for body, env in meas["outer_envelope"].items()
    }

    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    for row, (body, info) in enumerate(cand["bodies"].items()):
        g = meas["outer_envelope"][body]["selected_geometry"]
        P = np.asarray(g["proximal_joint_m"])
        P_d = np.asarray(g["distal_joint_m"])
        b = np.asarray(g["transverse_axes"]["b"])
        c = np.asarray(g["transverse_axes"]["c"])
        a = P_d - P
        L = float(np.linalg.norm(a))
        a = a / L

        ax_ax = axes[row, 0]
        ax_bc = axes[row, 1]

        # session-4 hull diagnostic (light) at each sampled section
        for t, hull in section_hulls[body].items():
            hull = np.asarray(hull)
            if len(hull) < 3:
                continue
            mid = float(t * L)
            hc = np.vstack([hull, hull[:1]])
            ax_bc.plot(hc[:, 0] * 1000, hc[:, 1] * 1000, "-", color="#c8d0d6", lw=1.2, zorder=2)
            ax_ax.plot(np.full(len(hc), mid * 1000), hc[:, 0] * 1000, "-", color="#c8d0d6",
                       lw=0.8, zorder=2, alpha=0.8)

        for rec in info["candidates"]:
            sid = rec["site_id"]
            fitted = rec["fitted"]
            if not fitted["resolved"]:
                continue
            pos = np.asarray(fitted["fitted_pos_global"])
            rel = pos - P
            ax_x = float(rel @ a) * 1000
            ax_b = float(rel @ b) * 1000
            ax_c = float(rel @ c) * 1000
            status = rec["skin_containment"]["loop"].get("verdict", "not_measured")
            is_endpoint = bool(rec["endpoint_roles"])
            color = STATUS_COLOR.get(status, STATUS_COLOR["not_measured"])
            marker = "o" if is_endpoint else None
            scatter_kw = dict(s=95 if is_endpoint else 55, color=color, zorder=5,
                              edgecolors="#111111" if is_endpoint else "white",
                              linewidths=1.1 if is_endpoint else 0.0)
            if is_endpoint:
                ax_ax.scatter(ax_x, ax_b, marker="o", **scatter_kw)
                ax_bc.scatter(ax_b, ax_c, marker="o", **scatter_kw)
            else:
                ax_ax.scatter(ax_x, ax_b, facecolors="none", edgecolors=color, s=45,
                              marker="o", linewidths=1.4, zorder=5)
                ax_bc.scatter(ax_b, ax_c, facecolors="none", edgecolors=color, s=45,
                              marker="o", linewidths=1.4, zorder=5)
            if is_endpoint:
                role = rec["endpoint_roles"][0].replace("_endpoint", "")
                ax_bc.annotate(role, (ax_b, ax_c), textcoords="offset points",
                               xytext=(5, 4), fontsize=6.5)
        ax_ax.set_title(f"{body} — axial (elbow->wrist) vs b (enlarged)", fontsize=10)
        ax_ax.set_xlabel("axial [mm]")
        ax_ax.set_ylabel("b [mm]")
        ax_ax.set_aspect("equal", adjustable="datalim")
        ax_bc.set_title(f"{body} — cross-section b vs c: colour=placement status, shape=role", fontsize=10)
        ax_bc.set_xlabel("b [mm]")
        ax_bc.set_ylabel("c [mm]")
        ax_bc.set_aspect("equal", adjustable="datalim")

    handles = [
        plt.Line2D([0], [0], marker="o", color="#1e8449", ls="none", ms=9, label="INSIDE (loop authority, >= margin)"),
        plt.Line2D([0], [0], marker="o", color="#d68910", ls="none", ms=9, label="inside, INSUFFICIENT clearance"),
        plt.Line2D([0], [0], marker="o", color="#c0392b", ls="none", ms=9, label="OUTSIDE"),
        plt.Line2D([0], [0], marker="o", color="#7f8c8d", ls="none", ms=9, label="UNRESOLVED / ambiguous section"),
        plt.Line2D([0], [0], marker="o", color="#555555", ls="none", ms=9, mfc="white", label="filled = first/last ENDPOINT role"),
        plt.Line2D([0], [0], marker="o", color="#555555", ls="none", ms=8, mfc="white", mec="#555555", label="hollow = waypoint (not an endpoint)"),
        plt.Line2D([0], [0], color="#c8d0d6", lw=1.4, label="session-4 band hull (diagnostic)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=8, frameon=False)
    fig.suptitle(
        "Forearm attachment candidates (v5) — every site mechanical_qualification=false; "
        "endpoint roles are path positions, not qualifications",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    fig.savefig(OUT, dpi=150)
    print(f"figure -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
