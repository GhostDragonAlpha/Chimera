"""08 — IMPLICIT-EVIDENCE INVENTORY (hand/ulna correspondence evidence already in the
artifacts, with nobody having proposed a mapping).

Read-only diagnostics; no mapping proposed, no fitting, no utility numbers.
Measured conventions (checked in-script, not assumed): raw mesh RIGHT = -x
(elbow_R x=-0.1155 < elbow_L x=+0.1155); source XML RIGHT = +z.

Items:
 A. Pack triangle ownership (JNT3 `assign`, majority of the 3 vertex owners):
    elbow_L/R, wrist_L/R counts; hand region = centroid distal of the wrist along the
    elbow->wrist axis AND within `HAND_PERP_CAP` perpendicular distance of that axis
    (raw projection counts also recorded); laterality consistency per side.
 B. Pack joint ledger: names, FK parents, band vertex counts, positions.
 C. Mesh extents + rig's own measured hand tips.
 D. Source XML parentage facts (humerus->?->hand) + per-body site counts.
 E. Source bilateral mirror audit: body pos_local and site pos_local across paired
    limbs (site pairing law: right "X-Pk" <-> left "X_l-Pk").
 F. Fit-packet partial records for ulna/ulna_l/hand_r/hand_l.
"""
import json
import sys
from pathlib import Path
from collections import Counter

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b4_common as C  # noqa: E402

sys.path.insert(0, str(C.B4 / "work" / "modules"))
from mesh_target import MESH_UNIT_TO_M, load_mesh, load_pack  # noqa: E402

HAND_PERP_CAP_FACTOR = 1.0   # hand region perp cap = 1.0 x |elbow->wrist| (stated)


def chain_to_root(b, parent_of):
    out = []
    while b is not None:
        out.append(b)
        b = parent_of[b]
    return out


def main() -> int:
    inv: dict = {"meta": {"mesh_units_to_m": MESH_UNIT_TO_M,
                          "hand_perp_cap_factor": HAND_PERP_CAP_FACTOR}}

    V_units, F = load_mesh(str(C.MESH_PATH))
    V = V_units * MESH_UNIT_TO_M
    pk = load_pack(str(C.PACK_PATH))
    names = pk["names"]
    J = pk["J"] * MESH_UNIT_TO_M
    assign = pk["assign"]
    parents = pk["parents"]
    idx = {n: i for i, n in enumerate(names)}

    # convention check (measured, then asserted)
    assert J[idx["elbow_R"], 0] < 0 < J[idx["elbow_L"], 0], "mesh x-side convention changed"

    # ---- A. triangle ownership
    majority = []
    for row in assign[F]:
        top, n = Counter(row.tolist()).most_common(1)[0]
        majority.append(top if n >= 2 else -1)
    majority = np.array(majority)
    owner_counts = Counter(names[i] if i >= 0 else "NO_MAJORITY" for i in majority)
    inv["A_tri_ownership"] = {
        "n_triangles": int(len(F)),
        "n_no_majority": int((majority == -1).sum()),
        "owner_joint_counts": dict(sorted(owner_counts.items())),
        "arm_regions": {}, "beyond_wrist_all_owners": {},
    }

    cents = V[F].mean(axis=1)
    for side, suf in (("right", "R"), ("left", "L")):
        E, W = J[idx[f"elbow_{suf}"]], J[idx[f"wrist_{suf}"]]
        a = (W - E) / np.linalg.norm(W - E)
        L_ew = float(np.linalg.norm(W - E))
        t = (cents - E) @ a
        rel = cents - E
        perp = np.sqrt(np.maximum((rel * rel).sum(1) - t * t, 0.0))
        cap = HAND_PERP_CAP_FACTOR * L_ew
        hand_mask = (t > L_ew) & (perp < cap)
        rows = {}
        for jname in (f"elbow_{suf}", f"wrist_{suf}"):
            m = majority == idx[jname]
            lat_consistent = int((cents[m, 0] < 0).sum()) if suf == "R" else int((cents[m, 0] > 0).sum())
            hand = m & hand_mask
            rows[jname] = {
                "triangles_total": int(m.sum()),
                "forearm_region_t_in_0..L": int((m & (t >= 0) & (t <= L_ew)).sum()),
                "hand_region_capped": int(hand.sum()),
                "hand_region_projection_only": int((m & (t > L_ew)).sum()),
                "lateral_consistent": lat_consistent,
                "lateral_inconsistent": int(m.sum()) - lat_consistent,
                "hand_cluster_median_perp_m": float(np.median(perp[hand])) if hand.any() else None,
                "hand_cluster_centroid_m": cents[hand].mean(axis=0).tolist() if hand.any() else None,
                "hand_cluster_distal_extent_m": float(t[hand].max() - L_ew) if hand.any() else None,
            }
        inv["A_tri_ownership"]["arm_regions"][side] = {
            "elbow_wrist_len_m": L_ew, "hand_perp_cap_m": cap, "owners": rows}
        m_all = hand_mask
        c = Counter(names[i] if i >= 0 else "NO_MAJORITY" for i in majority[m_all])
        inv["A_tri_ownership"]["beyond_wrist_all_owners"][side] = {
            "n_triangles_capped": int(m_all.sum()), "owner_counts": dict(c)}

    # ---- B. pack joint ledger
    inv["B_pack_joints"] = {
        n: {"fk_parent": names[parents[i]] if 0 <= parents[i] < len(names) else None,
            "band_vertices": int((assign == i).sum()), "pos_m": J[i].tolist()}
        for i, n in enumerate(names)}
    inv["B_pack_joints"]["_n_joints"] = len(names)
    inv["B_pack_joints"]["_hand_or_digit_joints"] = [
        n for n in names if "hand" in n.lower() or "finger" in n.lower() or "digit" in n.lower()]

    # ---- C. mesh extents + hand tips
    def tip(suf):
        dJ, pJ = J[idx[f"wrist_{suf}"]], J[idx[f"elbow_{suf}"]]
        dd = np.linalg.norm(V - dJ, axis=1)
        pdd = np.linalg.norm(V - pJ, axis=1)
        arm = np.linalg.norm(dJ - pJ)
        cand = np.where((pdd < 1.2 * arm) & (dd > arm))[0]
        ids = cand[np.argsort(-dd[cand])][:30]
        return V[ids].mean(axis=0)
    inv["C_mesh"] = {
        "n_vertices": int(len(V)), "n_triangles": int(len(F)),
        "extents_m": {ax: [float(V[:, k].min()), float(V[:, k].max())]
                      for k, ax in enumerate("xyz")},
        "hand_tip_right_m": tip("R").tolist(),
        "hand_tip_left_m": tip("L").tolist(),
        "wrist_to_handtip_right_m": float(np.linalg.norm(tip("R") - J[idx["wrist_R"]])),
        "wrist_to_handtip_left_m": float(np.linalg.norm(tip("L") - J[idx["wrist_L"]])),
    }

    # ---- D. source parentage + site counts
    bodies, parent_of, sites_of = C.load_xml_tree()
    inv["D_source_parentage"] = {
        "hand_r_rootward_chain": chain_to_root("hand_r", parent_of),
        "hand_l_rootward_chain": chain_to_root("hand_l", parent_of),
        "site_counts_arm_chain": {n: len(sites_of[n]) for n in
                                  ("humerus", "ulna", "radius", "hand_r",
                                   "humerus_l", "ulna_l", "radius_l", "hand_l")},
    }

    # ---- E. bilateral mirror audit
    import xml.etree.ElementTree as ET
    root = ET.parse(str(C.XML_PATH)).getroot()
    body_pos: dict[str, list] = {}
    body_sites: dict[str, dict[str, list]] = {}
    paired_bodies = {b for p in (("femur_r", "femur_l"), ("tibia_r", "tibia_l"),
                                 ("talus_r", "talus_l"), ("toes_r", "toes_l"),
                                 ("humerus", "humerus_l"), ("ulna", "ulna_l"),
                                 ("radius", "radius_l"), ("hand_r", "hand_l"))
                     for b in p}
    for bel in root.iter("body"):
        nm = bel.get("name")
        if nm not in paired_bodies:
            continue
        body_pos[nm] = [float(v) for v in bel.get("pos").split()]
        body_sites[nm] = {s.get("name"): [float(v) for v in s.get("pos").split()]
                          for s in bel.findall("site") if s.get("name") and s.get("pos")}

    def mirror_off(a, b):
        return float(max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] + b[2])))

    def left_counterpart(sname: str) -> str:
        # measured source naming law: leg sites carry a side suffix ("glut_med1_r-P2"
        # <-> "glut_med1_l-P2"); arm right sites are unmarked ("PT-P2" <-> "PT_l-P2")
        if "_r-P" in sname:
            return sname.replace("_r-P", "_l-P")
        return sname.replace("-P", "_l-P")

    mirror_audit = {}
    n_bodypos_exact = 0
    for r, l in (("femur_r", "femur_l"), ("tibia_r", "tibia_l"), ("talus_r", "talus_l"),
                 ("toes_r", "toes_l"), ("humerus", "humerus_l"), ("ulna", "ulna_l"),
                 ("radius", "radius_l"), ("hand_r", "hand_l")):
        d_body = mirror_off(body_pos[r], body_pos[l])
        body_exact = d_body < 1e-12
        n_bodypos_exact += int(body_exact)
        sr, sl = body_sites[r], body_sites[l]
        paired = exact = 0
        offs = []
        unmatched_r = [s for s in sr if left_counterpart(s) not in sl]
        for s, p in sr.items():
            cp = left_counterpart(s)
            if cp in sl:
                paired += 1
                d = mirror_off(p, sl[cp])
                if d < 1e-12:
                    exact += 1
                else:
                    offs.append((s, d))
        sites_exact = paired > 0 and exact == paired and not unmatched_r
        mirror_audit[f"{r}|{l}"] = {
            "body_pos_mirror_offset_m": d_body, "body_pos_exact": body_exact,
            "sites_right": len(sr), "sites_left": len(sl),
            "sites_paired_by_name_law": paired, "exact_z_mirror_site_pairs": exact,
            "sites_unmatched_right": unmatched_r,
            "worst_site_offset_m": max((d for _, d in offs), default=0.0),
            "off_examples": sorted(offs, key=lambda x: -x[1])[:3],
            "site_sets_exact_z_mirror": sites_exact,
        }
    n_site_exact = sum(1 for v in mirror_audit.values() if v["site_sets_exact_z_mirror"])
    inv["E_mirror_audit"] = {
        "bodies_paired": len(mirror_audit),
        "body_pos_exact_z_mirror": n_bodypos_exact,
        "body_pairs_with_exact_site_z_mirror": n_site_exact,
        "pairs": mirror_audit,
    }

    # ---- F. fit-packet partial records
    packet = C.load_packet()
    pack_pos = {n: J[idx[n]] for n in names}
    partial = {"unresolved_segments": [], "joints_with_measured_anchor": [],
               "unplaced_sites": {}}
    for u in packet["unresolved_segments"]:
        if u["body"] in ("ulna", "ulna_l", "hand_r", "hand_l"):
            partial["unresolved_segments"].append(u)
    for j in packet["joints"]:
        if j["body"] in ("ulna", "ulna_l", "hand_r", "hand_l") and j["origin"] is not None:
            origin = np.asarray(j["origin"])
            nearest = min(pack_pos.items(), key=lambda kv: np.linalg.norm(kv[1] - origin))
            partial["joints_with_measured_anchor"].append({
                "joint": j["name"], "body": j["body"], "origin_m": j["origin"],
                "nearest_pack_joint": nearest[0],
                "gap_m": float(np.linalg.norm(nearest[1] - origin)),
                "status": j["status"]})
    cnt = Counter(s["segment"] for s in packet["sites"] if s["unresolved"])
    partial["unplaced_sites"] = dict(cnt)
    partial["unplaced_total"] = int(sum(cnt.values()))
    inv["F_packet_partial_records"] = partial

    C.save_receipt("08_inventory.json", inv)

    print("A. tri ownership (arm owners; hand region = distal of wrist AND perp < "
          f"{HAND_PERP_CAP_FACTOR:.1f}x|EW|):")
    for side in ("right", "left"):
        ar = inv["A_tri_ownership"]["arm_regions"][side]
        for jn, d in ar["owners"].items():
            print(f"   {jn:9s} total={d['triangles_total']:5d} forearm={d['forearm_region_t_in_0..L']:5d} "
                  f"hand_capped={d['hand_region_capped']:4d} (proj_only={d['hand_region_projection_only']:4d}) "
                  f"lateral_ok={d['lateral_consistent']:5d}/{d['triangles_total']} "
                  f"med_perp={d['hand_cluster_median_perp_m'] and round(d['hand_cluster_median_perp_m'],4)}")
    for side in ("right", "left"):
        b = inv["A_tri_ownership"]["beyond_wrist_all_owners"][side]
        print(f"   capped beyond-wrist ({side}): {b['n_triangles_capped']} tris, owners={b['owner_counts']}")
    print("D. hand_r chain:", " -> ".join(inv["D_source_parentage"]["hand_r_rootward_chain"]))
    print("   hand_l chain:", " -> ".join(inv["D_source_parentage"]["hand_l_rootward_chain"]))
    print("   arm site counts:", inv["D_source_parentage"]["site_counts_arm_chain"])
    print(f"E. body pos exact mirrors: {n_bodypos_exact}/{len(mirror_audit)}; "
          f"site sets exact: {n_site_exact}/{len(mirror_audit)}")
    for k, v in mirror_audit.items():
        if not v["body_pos_exact"] or not v["site_sets_exact_z_mirror"]:
            print(f"   NOT exact: {k}: body_off={v['body_pos_mirror_offset_m']:.2e} "
                  f"sites_exact={v['exact_z_mirror_site_pairs']}/{v['sites_paired_by_name_law']} "
                  f"unmatched_r={v['sites_unmatched_right'][:2]} "
                  f"worst={v['worst_site_offset_m']:.2e} {v['off_examples'][:2]}")
    print("F. anchors:", [(a['joint'], a['nearest_pack_joint'], a['gap_m'])
                          for a in partial['joints_with_measured_anchor']])
    print("   unplaced sites:", partial["unplaced_sites"])
    print("B. hand/digit joints in pack:", inv["B_pack_joints"]["_hand_or_digit_joints"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
