"""S2b — REFINED-RULE DIAGNOSIS (frozen in prereg sec.2.4, run because the primary
rule fired): for each failing link, the child anchor's position relative to the parent
surface (recorded in s2), plus the decisive assembly question: do the CMC-joint bone
SURFACES actually meet (coherent carpus+metacarpus assembly) or is there a void
(different family's geometry / incoherent assembly)?

This script computes DIAGNOSTIC numbers only. It does not change any verdict by itself;
verdict logic lives in the report and follows the prereg + the governing R2 spec.

READ-ONLY inputs. Writes receipts/s2b_cmc_diagnosis.json inside the audit dir.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import handlib as H  # noqa: E402
import numpy as np  # noqa: E402
from s2_identity_assembly import closest_points, inside_mesh, mesh_dist, tri_circumradius_max  # noqa: E402

OUT = H.OUT / "receipts" / "s2b_cmc_diagnosis.json"
CMC_PAIRS = [("trapezium", "1mc"), ("trapezoid", "2mc"), ("capitate", "3mc"),
             ("hamate", "4mc"), ("hamate", "5mc")]
MCP_PAIRS = [("1mc", "thumbprox"), ("2mc", "2proxph"), ("3mc", "3proxph"),
             ("4mc", "4proxph"), ("5mc", "5proxph")]


def surf_gap(Ta, Tb, step_a=3, step_b=3):
    """min surface-to-surface distance estimate: vertices of A (subsampled) against all
    triangles of B, and vice versa; returns (gap_upper_bound_estimate, note)."""
    va = Ta.reshape(-1, 3)[::step_a]
    vb = Tb.reshape(-1, 3)[::step_b]
    _, dab = mesh_dist(va, Tb, tri_circumradius_max(Tb))
    _, dba = mesh_dist(vb, Ta, tri_circumradius_max(Ta))
    return float(min(dab.min(), dba.min()))


def main() -> int:
    t0 = time.time()
    anchors_r, _, _, _, _ = H.parse_hand_xml()
    placed = {}
    for b in H.BONES:
        tri, _ = H.load_stl(H.VENDOR / f"{b}.stl")
        placed[b] = tri + anchors_r[b][None, None, :]

    rec = {"purpose": "prereg 2.4 refined-rule diagnosis (primary chain rule FIRED)",
           "cmc_pairs": {}, "mcp_pairs": {}, "mc_proximal_reach": {},
           "anchor_gap_vectors": {}, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}

    # where does each metacarpal surface reach, relative to its own anchor?
    for mc in ["1mc", "2mc", "3mc", "4mc", "5mc"]:
        v = placed[mc].reshape(-1, 3)
        a = anchors_r[mc]
        rec["mc_proximal_reach"][mc] = {
            "anchor_y_mm": float(a[1] * 1000),
            "surf_min_y_mm": float(v[:, 1].min() * 1000),
            "surf_max_y_mm": float(v[:, 1].max() * 1000),
            "proximal_reach_past_anchor_mm": float((a[1] - v[:, 1].min()) * 1000),
        }

    for parent, child in CMC_PAIRS:
        Ta, Tb = placed[parent], placed[child]
        p = anchors_r[child]
        rmax = tri_circumradius_max(Ta)
        q, d = closest_points(p[None, :], Ta, rmax)
        gap = surf_gap(Ta, Tb)
        rec["cmc_pairs"][f"{parent}|{child}"] = {
            "anchor_to_parent_surf_mm": float(d[0] * 1000),
            "surf_to_surf_gap_mm": gap,
            "child_anchor_to_nearest_parent_pt_vec_mm":
                [float(x * 1000) for x in (q[0] - p)],
        }
        print(f"CMC {parent:10s}|{child:6s} anchor->parent surf {d[0]*1000:6.2f} mm ; "
              f"surf-surf gap {gap:6.2f} mm")

    for parent, child in MCP_PAIRS:
        Ta, Tb = placed[parent], placed[child]
        gap = surf_gap(Ta, Tb)
        p = anchors_r[child]
        ins = inside_mesh(p[None, :], Ta)[0]
        rec["mcp_pairs"][f"{parent}|{child}"] = {
            "anchor_to_parent_surf_mm": None,  # already in s2 receipt
            "surf_to_surf_gap_mm": gap,
            "child_anchor_inside_parent": bool(ins),
        }
        print(f"MCP {parent:10s}|{child:6s} surf-surf gap {gap:6.2f} mm "
              f"(child anchor inside parent: {ins})")

    # the vector that would be needed per failing link (prereg refined-rule text)
    for parent, child in H.CHAIN:
        Ta = placed[parent]
        p = anchors_r[child]
        q, d = closest_points(p[None, :], Ta, tri_circumradius_max(Ta))
        rec["anchor_gap_vectors"][f"{parent}|{child}"] = {
            "d_link_mm": float(d[0] * 1000),
            "vec_child_to_parent_surf_mm": [float(x * 1000) for x in (q[0] - p)],
        }

    rec["elapsed_s"] = time.time() - t0
    OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({rec['elapsed_s']:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
