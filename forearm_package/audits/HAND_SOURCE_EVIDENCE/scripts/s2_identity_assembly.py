"""S2 — O1-class identity test of the 27 vendor hand bones (frozen prereg sec.2).

Placement convention (frozen): identity scale (XML '1 1 1'), translation by the geom
pos anchor; lunate at the hand origin (no pos attr). Decisive test: the 19 chain links
(d_link = child anchor -> parent surface <= 3.5 mm anchor class). Supporting: per-bone
d_own + inside flag, extents reproduction vs the C2 anchor record, carpal adjacency
(descriptive), the 5 tendon sites (course class, recorded not decisive).

READ-ONLY inputs. Writes receipts/s2_identity.json inside the audit dir.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import handlib as H  # noqa: E402
import numpy as np  # noqa: E402

OUT = H.OUT / "receipts" / "s2_identity.json"
CARPALS = ["pisiform", "lunate", "scaphoid", "triquetrum", "hamate",
           "capitate", "trapezoid", "trapezium"]
# C2's frozen anchor-derived record (handreq R3.4 / R2 A3)
RECORD_DISTAL = 0.15529            # m, |3distph anchor| from hand origin
RECORD_RAYS = [0.0670, 0.0964, 0.1002, 0.0891, 0.0786]  # rays 1..5 chain sums
SITE_BONE = {"ECRL-P4": "2mc", "ECRB-P4": "3mc", "ECU-P6": "5mc",
             "FCR-P3": "2mc", "FCU-P4": "pisiform"}


def tri_circumradius_max(T):
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    ab, ac, bc = b - a, c - a, b - c
    area2 = np.linalg.norm(np.cross(ab, ac), axis=1)
    sides = np.stack([np.linalg.norm(ab, axis=1),
                      np.linalg.norm(ac, axis=1),
                      np.linalg.norm(bc, axis=1)], axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.prod(sides, axis=1) / (2.0 * area2)
    r[~np.isfinite(r)] = 0.0
    return float(r.max())


def closest_points(P, T, rmax):
    """vectorized Ericson closest-point for query block P (n,3) vs triangles T (m,3,3).
    Returns (n,3) closest points and (n,) distances."""
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    cen = (A + B + C) / 3.0
    out_q = np.empty_like(P)
    out_d = np.empty(len(P))
    # prune per query by centroid distance
    d = np.linalg.norm(P[:, None, :] - cen[None, :, :], axis=2)
    dmin_v = np.linalg.norm(P[:, None, :] - A[None, :, :], axis=2).min(axis=1)
    for i, p in enumerate(P):
        cand = np.where(d[i] <= dmin_v[i] + rmax + 1e-9)[0]
        a, b, c = A[cand], B[cand], C[cand]
        ab, ac = b - a, c - a
        ap = p - a
        d1 = np.einsum("ij,ij->i", ab, ap)
        d2 = np.einsum("ij,ij->i", ac, ap)
        bp = p - b
        d3 = np.einsum("ij,ij->i", ab, bp)
        d4 = np.einsum("ij,ij->i", ac, bp)
        cp = p - c
        d5 = np.einsum("ij,ij->i", ab, cp)
        d6 = np.einsum("ij,ij->i", ac, cp)
        va = d3 * d6 - d5 * d4
        vb = d5 * d2 - d1 * d6
        vc = d1 * d4 - d3 * d2
        # region ABC
        denom = va + vb + vc
        denom[denom == 0] = 1e-30
        q_ab = a + (ab * (vb[:, None] / denom[:, None])
                    + ac * (vc[:, None] / denom[:, None]))
        # region AB (v=0): projection on ab
        t = np.where((d1 - d3) != 0, d1 / np.where(d1 - d3 != 0, d1 - d3, 1.0), 0.0)
        q_ab_only = a + t[:, None] * ab
        # region AC
        t2 = np.where((d2 - d6) != 0, d2 / np.where(d2 - d6 != 0, d2 - d6, 1.0), 0.0)
        q_ac_only = a + t2[:, None] * ac
        # region BC
        t3 = np.where((d4 - d3) != 0, d4 / np.where(d4 - d3 != 0, d4 - d3, 1.0), 0.0)
        q_bc_only = b + t3[:, None] * (c - b)
        # Ericson region selection
        m_a = (d1 <= 0) & (d2 <= 0)
        m_b = (d3 >= 0) & (d4 <= d3)
        m_c = (d6 >= 0) & (d5 <= d6)
        m_ab = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
        m_ac = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
        m_bc = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
        Q = q_ab.copy()
        Q[m_a] = a[m_a]
        Q[m_b] = b[m_b]
        Q[m_c] = c[m_c]
        Q[m_ab & ~(m_a | m_b | m_c)] = q_ab_only[m_ab & ~(m_a | m_b | m_c)]
        rest = ~(m_a | m_b | m_c | m_ab)
        Q[m_ac & rest] = q_ac_only[m_ac & rest]
        Q[m_bc & rest] = q_bc_only[m_bc & rest]
        dd = np.linalg.norm(Q - p, axis=1)
        j = int(np.argmin(dd))
        out_q[i], out_d[i] = Q[j], float(dd[j])
    return out_q, out_d


def mesh_dist(P, T, rmax, chunk=192):
    qs = np.empty_like(P)
    ds = np.empty(len(P))
    for s in range(0, len(P), chunk):
        qs[s:s + chunk], ds[s:s + chunk] = closest_points(P[s:s + chunk], T, rmax)
    return qs, ds


def inside_mesh(P, T):
    """ray parity along +x (Moller-Trumbore), vectorized; P (n,3)."""
    v0, e1, e2 = T[:, 0], T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    out = np.zeros(len(P), dtype=bool)
    for i, p in enumerate(P):
        d = np.array([1.0, 1e-9, 1e-9])
        d /= np.linalg.norm(d)
        pv = np.cross(d, e2)
        det = np.einsum("ij,ij->i", e1, pv)
        ok = np.abs(det) > 1e-14
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = p - v0
        u = np.einsum("ij,ij->i", tv, pv) * inv
        qv = np.cross(tv, e1)
        v = np.einsum("j,ij->i", d, qv) * inv
        t = np.einsum("ij,ij->i", e2, qv) * inv
        hit = ok & (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (t > 1e-12)
        out[i] = bool(np.count_nonzero(hit) % 2)
    return out


def main() -> int:
    t0 = time.time()
    anchors_r, anchors_l, sites_r, meshes, bodies = H.parse_hand_xml()
    assert all(meshes[b]["scale"] == [1.0, 1.0, 1.0] for b in H.BONES)

    placed, raw = {}, {}
    for b in H.BONES:
        tri, meta = H.load_stl(H.VENDOR / f"{b}.stl")
        raw[b] = tri
        placed[b] = tri + anchors_r[b][None, None, :]
    # lunate: anchor == origin by construction (no pos attr -> 0,0,0)
    assert np.allclose(anchors_r["lunate"], 0.0)

    rec = {"placement": "v_stl * (1,1,1) + anchor_pos; lunate at origin",
           "threshold_anchor_class_m": H.ANCHOR_THRESH, "bones": {}, "links": [],
           "started": time.strftime("%Y-%m-%dT%H:%M:%S")}

    # ---- per-bone: d_own, inside, extents ------------------------------------
    for b in H.BONES:
        T = placed[b]
        p = anchors_r[b]
        rmax = tri_circumradius_max(T)
        q, d = closest_points(p[None, :], T, rmax)
        ins = inside_mesh(p[None, :], T)[0]
        v = T.reshape(-1, 3)
        rec["bones"][b] = {
            "anchor": [float(x) for x in p],
            "d_own_m": float(d[0]), "own_anchor_inside": bool(ins),
            "n_tri": int(len(T)),
            "centroid_local": [float(x) for x in v.mean(axis=0)],
            "placed_bbox": {k: [float(v[:, i].min()), float(v[:, i].max())]
                            for i, k in enumerate("xyz")},
        }
        print(f"{b:10s} d_own={d[0]*1000:7.2f} mm inside={ins}")

    # ---- the 19 chain links (decisive) ---------------------------------------
    n_pass = 0
    for parent, child in H.CHAIN:
        T = placed[parent]
        rmax = tri_circumradius_max(T)
        p = anchors_r[child]
        q, d = closest_points(p[None, :], T, rmax)
        ins = inside_mesh(p[None, :], T)[0]
        ok = bool(d[0] <= H.ANCHOR_THRESH)
        n_pass += ok
        rec["links"].append({
            "parent": parent, "child": child, "d_link_m": float(d[0]),
            "child_inside_parent": bool(ins),
            "nearest_point_on_parent": [float(x) for x in q[0]],
            "pass_at_3p5mm": ok})
        print(f"link {parent:10s} <- {child:10s} d={d[0]*1000:7.2f} mm "
              f"inside={ins} {'PASS' if ok else 'FAIL'}")
    rec["links_pass"] = n_pass
    rec["links_total"] = len(H.CHAIN)

    # ---- assembly reproduction of the C2 anchor record ------------------------
    def chain_len(ray):
        names = {"1": ["1mc", "thumbprox", "thumbdist"],
                 "2": ["2mc", "2proxph", "2midph", "2distph"],
                 "3": ["3mc", "3proxph", "3midph", "3distph"],
                 "4": ["4mc", "4proxph", "4midph", "4distph"],
                 "5": ["5mc", "5proxph", "5midph", "5distph"]}[ray]
        return float(sum(np.linalg.norm(anchors_r[names[i + 1]] - anchors_r[names[i]])
                         for i in range(len(names) - 1)))
    rec["record_reproduction"] = {
        "distal_3distph_anchor_m": float(np.linalg.norm(anchors_r["3distph"])),
        "distal_3distph_record_m": RECORD_DISTAL,
        "ray_chain_anchors_m": {r: chain_len(r) for r in "12345"},
        "ray_chain_record_m": {str(i + 1): RECORD_RAYS[i] for i in range(5)},
    }
    allv = np.vstack([placed[b].reshape(-1, 3) for b in H.BONES])
    r3 = np.linalg.norm(placed["3distph"].reshape(-1, 3), axis=1)
    rec["assembly_surface"] = {
        "max_radius_from_hand_origin_m": float(np.linalg.norm(allv, axis=1).max()),
        "3distph_max_radius_m": float(r3.max()),
        "max_minus_y_extent_m": float(-allv[:, 1].min()),
        "overall_bbox": {k: [float(allv[:, i].min()), float(allv[:, i].max())]
                         for i, k in enumerate("xyz")},
    }

    # ---- carpal adjacency (descriptive upper bounds) --------------------------
    adj = {}
    for i in range(len(CARPALS)):
        for j in range(i + 1, len(CARPALS)):
            a, b = CARPALS[i], CARPALS[j]
            Ta, Tb = placed[a], placed[b]
            va = Ta.reshape(-1, 3)
            _, dab = mesh_dist(va[::7], Tb, tri_circumradius_max(Tb))
            adj[f"{a}|{b}"] = {
                "centroid_dist_m": float(np.linalg.norm(
                    anchors_r[a] - anchors_r[b])),
                "vert_to_surf_min_m_upper_bound": float(dab.min()),
            }
    rec["carpal_adjacency_descriptive"] = adj

    # ---- tendon sites (course class, recorded) --------------------------------
    st = {}
    for s, (p, comp) in H.SITES.items():
        p = np.array(p)
        bone = SITE_BONE[s]
        T = placed[bone]
        q, d = closest_points(p[None, :], T, tri_circumradius_max(T))
        st[s] = {"compartment": comp, "cited_bone": bone,
                 "dist_to_cited_bone_surface_m": float(d[0]),
                 "local_z_mm": float(p[2] * 1000)}
        print(f"site {s:8s} ({comp}) -> {bone:9s} d={d[0]*1000:6.2f} mm")
    rec["sites_course_class"] = st

    # ---- verdicts (frozen) ----------------------------------------------------
    failed_links = [l for l in rec["links"] if not l["pass_at_3p5mm"]]
    failed_parents = sorted({l["parent"] for l in failed_links})
    # per-bone verdict (prereg 2.4): a bone that parents >=1 link is CHAIN-PASS iff all
    # its links pass; a bone that is only a child is CHAIN-PASS iff its own link passed;
    # a bone that parents no link is ADJACENCY-SUPPORTED (never OUT by chain rule).
    parents_ok = {l["parent"] for l in rec["links"] if l["pass_at_3p5mm"]}
    child_link_ok = {l["child"]: l["pass_at_3p5mm"] for l in rec["links"]}
    bone_verdict = {}
    for b in H.BONES:
        parents_any = [l for l in rec["links"] if l["parent"] == b]
        if parents_any:
            bone_verdict[b] = ("CHAIN-PASS" if all(l["pass_at_3p5mm"] for l in parents_any)
                               else "OUT(link-fail)")
        elif b in child_link_ok:
            bone_verdict[b] = ("CHAIN-PASS" if child_link_ok[b] else "OUT(link-fail)")
        else:
            bone_verdict[b] = "ADJACENCY-SUPPORTED"
    plate_failed = [b for b in H.PLATE if bone_verdict[b] == "OUT(link-fail)"]
    rec["verdict"] = {
        "bone_verdicts": bone_verdict,
        "failed_parents": failed_parents,
        "identity_all_links_pass": len(failed_links) == 0,
        "plate_failed_bones": plate_failed,
        "derivation_gate": ("RUN" if not plate_failed else
                            "BLOCKED-plate-bones-out"),
    }
    rec["elapsed_s"] = time.time() - t0
    OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(f"\nlinks: {n_pass}/{len(H.CHAIN)} pass at 3.5mm; failed parents: {failed_parents}")
    print(f"gate: {rec['verdict']['derivation_gate']}")
    print(f"wrote {OUT}  ({rec['elapsed_s']:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
