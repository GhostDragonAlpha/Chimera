"""target_envelope.py — bounded forearm OUTER-ENVELOPE estimator (read-only).

MEASURES the target's SKIN envelope of the forearm cross-section, away from the
wrist/palm and the elbow, at interior sections of the elbow->wrist axis. This is an
OUTER-ENVELOPE (skin surface) measurement. It is NOT an internal anatomy measurement:
target skin width and source muscle-site spread are different quantities, and their
ratio is never promoted to evidence for bone/tissue cross-section scaling (see
actual_target_fit.py — the forearm b/c axes are AUTHORED assumptions bounded by this
envelope, and only a feasibility check uses it: fitted internal spread must stay
inside the measured skin envelope).

Records for every section the selected geometry, and reports per-direction median /
min / max / std / uncertainty, plus sensitivity to section placement and band width.
"""
from __future__ import annotations

import json

import numpy as np

from mesh_target import MonkeyTarget, MESH_UNIT_TO_M

SECTION_T = (0.35, 0.50, 0.65)   # interior fractions of the elbow->wrist axis
BAND_HALF_M = 0.008              # axial half-width of each section slice (documented geometry)
BAND_SWEEP_FRAC = 0.25           # sensitivity: band half-width x (1 +- sweep)
SECTION_TOL = 0.05               # sensitivity: section position x (1 +- tol) around each t


def measure_forearm_envelope(
    mt: MonkeyTarget,
    P: np.ndarray,
    P_d: np.ndarray,
    b: np.ndarray,
    c: np.ndarray,
    sections: tuple[float, ...] = SECTION_T,
    band_half: float = BAND_HALF_M,
    radial_cap: float = 0.05,
) -> dict:
    """Outer (skin) envelope widths along the transverse axes b and c at interior
    sections of the (elbow -> wrist) bone axis. Returns a structured record.

    P, P_d  : proximal (elbow) and distal (wrist) joint positions, metres.
    b, c    : the segment's fitted transverse frame axes (unit, right-handed).
    radial_cap : the section slice is BOUNDED as a radial cylinder around the bone
        axis (rejects shoulder/torso/hand vertices whose axial projection alone
        would land inside the band).

    Session-4: every section additionally stores the 2D CONVEX HULL of its sampled
    band vertices in the (b,c) plane (nominal band AND the BAND_SWEEP_FRAC narrow/
    wide variants used by containment()'s both-sign sensitivity).
    """
    a = P_d - P
    L = float(np.linalg.norm(a))
    if L < 1e-9:
        raise ValueError("forearm axis degenerate")
    a = a / L
    rel = mt.V - P
    proj = rel @ a  # metres along the bone axis
    radial = np.linalg.norm(rel - np.outer(proj, a), axis=1)
    b_comp = rel @ b
    c_comp = rel @ c

    def _slice_v(mid: float, half: float) -> np.ndarray:
        return np.nonzero((np.abs(proj - mid) <= half) & (radial <= radial_cap))[0]

    def _hull_for(ids: np.ndarray) -> np.ndarray:
        if len(ids) < 3:
            return np.empty((0, 2))
        return _convex_hull_2d(np.column_stack([b_comp[ids], c_comp[ids]]))

    secs: list[dict] = []
    stats: dict[str, dict] = {}
    for t in sections:
        mid = float(t * L)
        ids = _slice_v(mid, band_half)
        nv = int(len(ids))
        wb = (float(b_comp[ids].max() - b_comp[ids].min()) if nv else 0.0)
        wc = (float(c_comp[ids].max() - c_comp[ids].min()) if nv else 0.0)
        sec = {
            "t": float(t),
            "axis_pos_m": float(mid),
            "n_verts": nv,
            "w_b_m": wb,
            "w_c_m": wc,
            "hull_bc": [[round(float(x), 9) for x in p] for p in _hull_for(ids)],
        }
        # both-sign band-width variants (nominal-narrow/nominal/wide) for containment
        for tag, mult in (("narrow", 1.0 - BAND_SWEEP_FRAC), ("wide", 1.0 + BAND_SWEEP_FRAC)):
            ids_v = _slice_v(mid, mult * band_half)
            sec[f"hull_bc_{tag}"] = [[round(float(x), 9) for x in p] for p in _hull_for(ids_v)]
        secs.append(sec)

    for ax in ("b", "c"):
        vals = np.array([s[f"w_{ax}_m"] for s in secs])
        stats[ax] = {
            "median": float(np.median(vals)),
            "min": float(vals.min()),
            "max": float(vals.max()),
            "std": float(vals.std()),
            "uncertainty": float((vals.max() - vals.min()) / 2.0),
            "n_sections_measured": int((vals > 0).sum()),
        }

    # sensitivity: (1) section placement at each t +- SECTION_TOL, (2) band half-width
    # +- BAND_SWEEP_FRAC. Reported as the spread of the per-direction median.
    sens: dict[str, dict] = {}
    for ax in ("b", "c"):
        medians: list[float] = []
        for t in sections:
            for tt in (t * (1 - SECTION_TOL), t, t * (1 + SECTION_TOL)):
                mid = float(tt * L)
                dw = band_half * (1.0 + BAND_SWEEP_FRAC)
                ids = _slice_v(mid, dw)
                if len(ids) == 0:
                    continue
                comp = b_comp if ax == "b" else c_comp
                medians.append(float(comp[ids].max() - comp[ids].min()))
        sens[ax] = {
            "median_range_min": float(min(medians)) if medians else None,
            "median_range_max": float(max(medians)) if medians else None,
            "n_variants": len(medians),
            "mean": float(np.mean(medians)) if medians else None,
        }

    return {
        "nature": "outer_envelope",
        "units": "m",
        "note": (
            "skin (outer) envelope cross-section widths measured on interior sections "
            "of the elbow->wrist axis, away from wrist/palm and elbow. An outer-envelope "
            "constraint only — NOT internal (bone/tissue) anatomy evidence."
        ),
        "selected_geometry": {
            "proximal_joint_m": [round(float(v), 9) for v in P],
            "distal_joint_m": [round(float(v), 9) for v in P_d],
            "axis_len_m": round(L, 9),
            "section_t": list(sections),
            "section_axial_band_half_m": band_half,
            "radial_cap_m": radial_cap,
            "transverse_axes": {"b": [round(float(v), 9) for v in b], "c": [round(float(v), 9) for v in c]},
        },
        "sections": secs,
        "per_axis": stats,
        "sensitivity": sens,
    }


def _convex_hull_2d(pts: np.ndarray) -> np.ndarray:
    """Andrew monotone-chain 2D convex hull (no scipy dependency). Returns the
    ordered CCW polygon of the given 2D points (len >= 3; duplicates removed)."""
    pts = np.unique(np.asarray(pts, dtype=np.float64).round(12), axis=0)
    if len(pts) < 3:
        return pts
    order = np.lexsort((pts[:, 1], pts[:, 0]))
    p = pts[order]
    lower: list[int] = []
    for i in range(len(p)):
        while len(lower) >= 2 and np.cross(p[lower[-1]] - p[lower[-2]], p[i] - p[lower[-2]]) <= 0:
            lower.pop()
        lower.append(i)
    upper: list[int] = []
    for i in range(len(p) - 1, -1, -1):
        while len(upper) >= 2 and np.cross(p[upper[-1]] - p[upper[-2]], p[i] - p[upper[-2]]) <= 0:
            upper.pop()
        upper.append(i)
    return p[np.array(lower[:-1] + upper[:-1], dtype=int)]


def _in_polygon(px: float, py: float, poly: np.ndarray) -> bool:
    """Ray-casting point-in-polygon for a convex CCW polygon."""
    if len(poly) < 3:
        d = np.linalg.norm(poly - np.array([px, py]))
        return bool(d.min() <= 1e-12)
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            x_int = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if x_int > px:
                inside = not inside
    return inside


def _dist_to_poly(mx: float, my: float, poly: np.ndarray) -> float:
    """Signed-ish distance from (mx,my) to a convex polygon: negative inside, 0 on
    edge, positive outside (measured to the nearest polygon point)."""
    if len(poly) < 3:
        return float(np.linalg.norm(poly - np.array([mx, my])))
    n = len(poly)
    best = float("inf")
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        seg = b - a
        t = float(np.clip(((mx - a[0]) * seg[0] + (my - a[1]) * seg[1]) / (seg @ seg) if seg @ seg > 0 else 0, 0, 1))
        d = float(np.hypot(mx - (a[0] + t * seg[0]), my - (a[1] + t * seg[1])))
        best = min(best, d)
    inside = _in_polygon(mx, my, poly)
    return -best if inside else best


def width_screen(fitted_internal_spread: dict[str, float], env: dict, margin_m: float = 0.001) -> dict:
    """COARSE WIDTH SCREEN (session-4 relabel): compares a per-axis fitted internal
    spread against the envelope MEDIAN width. This is a one-dimensional screen, NOT
    a spatial containment test — a narrow cluster displaced transversally (narrow on
    both axes, but outside the cross-section) passes this check by construction. Use
    containment() for actual inside/outside judgement. Never a scale confirmation."""
    out: dict[str, object] = {
        "ok": True,
        "kind": "width_screen_coarse",
        "claim": (
            "one-dimensional median-width screen only — does NOT certify spatial "
            "containment; a displaced narrow cluster can pass it. Use containment() "
            "for a geometric inside/outside verdict."
        ),
        "per_axis": {},
    }
    for ax, fit in fitted_internal_spread.items():
        bound = env["per_axis"][ax]["median"]
        slack = bound - fit
        ok = float(slack) >= margin_m
        out["per_axis"][ax] = {
            "fitted_internal_spread_m": float(fit),
            "envelope_median_m": float(bound),
            "clearance_m": float(slack),
            "required_clearance_m": margin_m,
            "ok": bool(ok),
        }
        if not ok:
            out["ok"] = False
    return out


def containment(
    fitted_sites_bc: list[dict],
    env: dict,
    margin_m: float = 0.001,
    band_sweep_frac: float = BAND_SWEEP_FRAC,
) -> dict:
    """SPATIAL containment of fitted internal sites inside each MEASURED section
    polygon (convex hull of the sampled band in the b-c plane, at each section's
    axial band). Verdict per site: ok | outside | unresolved(narrowing | no_vertices).

    Contract (session-4): the median width screen must NOT be the only check — a
    translated narrow cluster must FAIL here even when its per-axis spread is small.
    Sites whose axial position has NO sampled band near it are UNRESOLVED (the
    sampled geometry cannot establish containment; local narrowing between sections
    is reported, never assumed inside). Radial-cap sensitivity re-runs the section
    selection with BOTH signs of band-width variation; if a site's verdict flips it
    is reported unresolved (the measurement cannot certify it either way).

    fitted_sites_bc: [{name, axial (m along the axis), b, c (m, transverse)}]
    """
    sections = env["sections"]  # each has t, axis_pos_m, centroids, hull (b,c frame)
    if not sections:
        raise ValueError("containment(): envelope has no sampled sections")
    # per-section axial coverage: the SAME documented band half-width used to pick them
    half = env["selected_geometry"].get("section_axial_band_half_m", BAND_HALF_M)

    # signed-distance classes (session-5): d > 0 is geometrically OUTSIDE; inside with
    # clearance below the margin is INSIDE_TIGHT (a weaker, distinct verdict — "none
    # clears the margin" is NOT "all are outside"); d <= -margin is INSIDE.
    def _cls(d: float) -> str:
        if d > 0.0:
            return "outside"
        if d <= -margin_m:
            return "inside"
        return "inside_tight"

    per_site: dict[str, dict] = {}
    for site in fitted_sites_bc:
        name, axial, b, c = site["name"], float(site["axial"]), float(site["b"]), float(site["c"])
        # radial-cap -> axial-window resolved membership is AUTHORED (radial_cap), so
        # a site can only be judged against the section bands whose geometry was sampled
        candidates = [s for s in sections if abs(axial - s["axis_pos_m"]) <= half]
        if not candidates:
            per_site[name] = {
                "verdict": "unresolved",
                "reason": "local_narrowing: no sampled section band near this axial position",
            }
            continue
        cover = candidates[np.argmin([abs(axial - s["axis_pos_m"]) for s in candidates])]
        # class per variant (nominal + both band-width signs)
        variants = [("nominal", "hull_bc"), ("narrow", "hull_bc_narrow"), ("wide", "hull_bc_wide")]
        classes: list[str] = []
        dists: dict[str, float] = {}
        missing = False
        for tag, key in variants:
            h = np.asarray(cover.get(key, []) or [])
            if len(h) < 3:
                missing = True
                continue
            d = _dist_to_poly(b, c, h)
            dists[tag] = round(float(d), 9)
            classes.append(_cls(d))
        if missing or len(classes) < 2:
            per_site[name] = {
                "verdict": "unresolved",
                "reason": "no_vertices: section band geometry unusable for all band-width variants",
            }
            continue
        per_site[name] = {
            "section_t": cover["t"],
            "hull_points": int(len(np.asarray(cover["hull_bc"]))),
            "dist_to_hull_m": dists.get("nominal"),
            "dist_narrow_m": dists.get("narrow"),
            "dist_wide_m": dists.get("wide"),
        }
        setc = set(classes)
        if len(setc) > 1:
            # flips between inside and outside across band-width signs — the sampled
            # geometry cannot certify the site either way
            per_site[name]["verdict"] = "unresolved"
            per_site[name]["reason"] = (
                "radial_cap_sensitivity: class flips between inside and outside "
                "under band-width variation"
            )
        elif setc == {"outside"}:
            per_site[name]["verdict"] = "outside"
        elif setc == {"inside_tight"}:
            per_site[name]["verdict"] = "inside_insufficient_clearance"
            per_site[name]["reason"] = (
                "inside the hull at every band-width variant but clearance never "
                "reaches the required margin"
            )
        else:
            per_site[name]["verdict"] = "inside"

    def _named(verdict: str) -> list[str]:
        return sorted(n for n, d in per_site.items() if d["verdict"] == verdict)

    unresolved = _named("unresolved")
    outside = _named("outside")
    inside = _named("inside")
    tight = _named("inside_insufficient_clearance")
    return {
        "ok": bool(not outside and not unresolved and not tight and inside),
        "n_sites": len(per_site),
        "n_inside": len(inside),
        "n_inside_insufficient_clearance": len(tight),
        "n_outside": len(outside),
        "n_unresolved": len(unresolved),
        "outside": outside,
        "inside_insufficient_clearance": tight,
        "unresolved": unresolved,
        "per_site": {n: per_site[n] for n in sorted(per_site)},
        "claim": (
            "per-section 2D containment in the measured (b,c) hull of the sampled band "
            "-- spatial, not a width screen. Signed-distance classes are DISTINCT: d>0 "
            "is OUTSIDE; inside with clearance below the margin is "
            "inside_insufficient_clearance (never reported as outside); d<=-margin is "
            "INSIDE; a class that flips under band-width variation, or a site with no "
            "sampled band near its axial position, is UNRESOLVED, never assumed inside."
        ),
    }


def _plane_cut_segments(V: np.ndarray, F: np.ndarray, P: np.ndarray, a: np.ndarray, x0: float) -> list:
    """All triangle-plane intersection segments for the plane {(v - P).a = x0}.
    Each segment carries its source triangle index (for ownership identification).
    A crossing point on a shared edge is computed from the same two vertices and
    signed distances by every incident triangle, so chained endpoints agree to
    float32 noise."""
    d = (V - P) @ a - x0
    tri = d[F]
    mask = (tri > 0).any(axis=1) & (tri < 0).any(axis=1)
    segs: list = []
    for f in np.nonzero(mask)[0]:
        ids = F[f]
        dd = d[ids]
        pts: list = []
        for i in range(3):
            j = (i + 1) % 3
            d1, d2 = float(dd[i]), float(dd[j])
            if (d1 > 0.0) != (d2 > 0.0):
                t = d1 / (d1 - d2)
                pts.append(V[ids[i]] + t * (V[ids[j]] - V[ids[i]]))
        if len(pts) == 2 and float(np.linalg.norm(pts[1] - pts[0])) > 1e-12:
            segs.append((pts[0], pts[1], int(f)))
    return segs


def _chain_closed_loops(segs: list, tol: float = 1e-7):
    """Chain plane-cut segments into closed loops by matching endpoint keys
    (rounded to `tol`, ~float32 noise). Returns (loops, n_open, n_degenerate)
    where each loop is (points (K,3), tri_indices list). Never bridges gaps:
    an unmatched endpoint ends a chain as OPEN."""
    from collections import defaultdict

    def key(p) -> tuple:
        return (round(float(p[0]) / tol), round(float(p[1]) / tol), round(float(p[2]) / tol))

    end_map: dict = defaultdict(list)
    for i, seg in enumerate(segs):
        tri = seg[2] if len(seg) > 2 else -1
        end_map[key(seg[0])].append((i, 0))
        end_map[key(seg[1])].append((i, 1))
    used = [False] * len(segs)
    loops: list = []
    n_open = 0
    n_degenerate = 0
    for i0 in range(len(segs)):
        if used[i0]:
            continue
        used[i0] = True
        tri0 = segs[i0][2] if len(segs[i0]) > 2 else -1
        chain = [(segs[i0][0], tri0), (segs[i0][1], tri0)]
        closed = False
        for _ in range(len(segs) + 1):
            tail = key(chain[-1][0])
            nxt = None
            for (j, end) in end_map[tail]:
                if not used[j]:
                    nxt = (j, end)
                    break
            if nxt is None:
                break
            j, end = nxt
            used[j] = True
            seg_j = segs[j]
            chain.append((seg_j[1 - end], seg_j[2] if len(seg_j) > 2 else -1))
            if key(chain[-1][0]) == key(chain[0][0]):
                closed = True
                break
        if closed and len(chain) >= 4:
            pts = np.array([c[0] for c in chain[:-1]])
            tris = [c[1] for c in chain[:-1]]
            loops.append((pts, tris))  # drop the duplicated closing point
        elif closed:
            n_degenerate += 1
        else:
            n_open += 1
    return loops, n_open, n_degenerate


def section_loop_containment(
    mt,
    P: np.ndarray,
    a: np.ndarray,
    bu: np.ndarray,
    cu: np.ndarray,
    fitted_sites_bc: list,
    margin_m: float = 0.001,
    owner_joint_names: tuple = ("", ""),
) -> dict:
    """FINAL skin-containment authority (session-5): local triangle-plane section
    loops at each site's EXACT axial position, replacing the band-vertex convex
    hull (kept as a diagnostic by the caller). The mesh speaks for itself: the
    plane cut is chained into closed boundary loops and a site is judged against
    the IDENTIFIED skin loop — concave boundary included (ray-cast inside test).

    Loop identification (declared, mechanical — not proximity repair): the plane
    is infinite, so one cut may cross several body parts (the other forearm, the
    torso). Each cut segment carries its source triangle; each triangle votes the
    MAJORITY pack-owner of its three vertices (`mt.assign`, the pack's own
    per-vertex ownership — independent data, not invented here). A closed loop is
    IDENTIFIED as the evaluated limb's skin boundary when >= 50 % of its segments'
    triangles are owned by the segment's proximal/distal joints. EXACTLY ONE loop
    must identify; 0 or >= 2 identified loops (or open chains) leave every site at
    that axial position UNRESOLVED. No bridging, no repair, no choosing by size.

    Verdict classes are the session-5 signed-distance classes:
    inside (d <= -margin) | inside_insufficient_clearance (-margin < d <= 0) |
    outside (d > 0) | unresolved (section ambiguity).
    """
    owner_set = {
        mt.idx[n] for n in owner_joint_names if n and n in mt.idx
    }

    def _tri_owner() -> np.ndarray:
        o1, o2, o3 = mt.assign[mt.F[:, 0]], mt.assign[mt.F[:, 1]], mt.assign[mt.F[:, 2]]
        return np.where(o1 == o2, o1, o3)  # majority of 3

    tri_owner = _tri_owner() if owner_set else None

    def _identify(loops) -> tuple:
        identified, diag = [], []
        for pts, tris in loops:
            if tri_owner is None:
                frac = float("nan")
            else:
                owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)
                frac = owned / len(tris) if tris else 0.0
            diag.append({"points": int(len(pts)), "owner_fraction": round(float(frac), 4)})
            if frac >= 0.5:
                identified.append((pts, tris))
        return identified, diag

    per_site: dict[str, dict] = {}
    sections_diag: dict[str, dict] = {}
    cache: dict = {}
    for site in fitted_sites_bc:
        name, axial = site["name"], float(site["axial"])
        k = round(axial, 9)
        if k not in cache:
            segs = _plane_cut_segments(mt.V, mt.F, P, a, axial)
            loops, n_open, n_degen = _chain_closed_loops(segs)
            identified, idiag = _identify(loops)
            cache[k] = (identified, len(loops), n_open, n_degen, len(segs), idiag)
        identified, n_loops, n_open, n_degen, n_seg, idiag = cache[k]
        rec: dict = {
            "axial_m": k,
            "n_loops": n_loops,
            "n_identified_loops": len(identified),
            "n_open_chains": n_open,
            "n_degenerate_chains": n_degen,
            "n_cut_segments": n_seg,
        }
        if k not in sections_diag:
            sections_diag[k] = {"n_loops": n_loops, "loop_diagnostics": idiag}
        if len(identified) != 1:
            rec["verdict"] = "unresolved"
            rec["reason"] = (
                f"ambiguous_section: {n_loops} closed loop(s) ({len(identified)} identified "
                f"as this limb's skin by pack ownership) + {n_open} open chain(s) at this "
                f"axial position; no bridging, no repair, no proximity choice"
            )
            per_site[name] = rec
            continue
        pts, _tris = identified[0]
        rel = pts - P
        poly = np.column_stack([rel @ bu, rel @ cu])
        d = _dist_to_poly(float(site["b"]), float(site["c"]), poly)
        rec["loop_points"] = int(len(pts))
        rec["dist_to_loop_m"] = round(float(d), 9)
        if d > 0.0:
            rec["verdict"] = "outside"
        elif d <= -margin_m:
            rec["verdict"] = "inside"
        else:
            rec["verdict"] = "inside_insufficient_clearance"
            rec["reason"] = "inside the skin loop but clearance below the required margin"
        per_site[name] = rec

    def _named(verdict: str) -> list[str]:
        return sorted(n for n, r in per_site.items() if r["verdict"] == verdict)

    inside, tight, outside, unresolved = (
        _named("inside"),
        _named("inside_insufficient_clearance"),
        _named("outside"),
        _named("unresolved"),
    )
    return {
        "authority": "local_triangle_plane_loop",
        "loop_identification": "majority pack-owner (mt.assign) of cut-segment triangles >= 0.5; exactly one identified loop required",
        "ok": bool(not outside and not unresolved and not tight and inside),
        "n_sites": len(per_site),
        "n_inside": len(inside),
        "n_inside_insufficient_clearance": len(tight),
        "n_outside": len(outside),
        "n_unresolved": len(unresolved),
        "outside": outside,
        "inside_insufficient_clearance": tight,
        "unresolved": unresolved,
        "sections": sections_diag,
        "per_site": {n: per_site[n] for n in sorted(per_site)},
        "claim": (
            "FINAL authority: triangle-plane section loops at each site's exact axial "
            "position; hulls remain diagnostics. The limb's skin loop is IDENTIFIED "
            "mechanically by the pack's per-vertex ownership (>= 50 % majority), and "
            "exactly one loop must identify — otherwise UNRESOLVED (no bridging, no "
            "repair). Signed-distance classes are distinct: outside (d>0) is never "
            "conflated with inside-but-short-of-margin."
        ),
    }


# --- legacy alias (WARNED subject): the coarse one-dimensional screen, not containment
feasibility = width_screen


if __name__ == "__main__":
    mt = MonkeyTarget()
    from compiler import onb_from_points

    for wrist, elbow in (("wrist_R", "elbow_R"), ("wrist_L", "elbow_L")):
        P = mt.joint_pos(elbow)
        P_d = mt.joint_pos(wrist)
        q = mt.joint_pos(elbow) + np.array([0.05, 0.0, 0.05])
        _, bu, cu = onb_from_points(P, P_d, q)
        env = measure_forearm_envelope(mt, P, P_d, bu, cu)
        print(elbow, "->", wrist)
        print("  sections:", [(s["t"], s["n_verts"], round(s["w_b_m"], 4), round(s["w_c_m"], 4)) for s in env["sections"]])
        print("  per-axis:", {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in env["per_axis"].items()})
        print("  sensitivity:", {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in env["sensitivity"].items()})
    json.dump({"proto": "see actual_target_fit for the full record"}, open(r"E:\PythonChimera\.tmp\anatomy_compiler\runs\_envelope_probe.json", "w"))
    print("probe written")