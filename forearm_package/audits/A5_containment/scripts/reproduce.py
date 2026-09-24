"""A5 reproduction — 32 sites x 2 authorities.

Path A: re-derive every class from RECORDED distances/verdicts in
        actual_monkey_fit.json + attachment_candidates.json (no geometry loaded).
Path B: recompute BOTH authorities from inputs (mesh + pack) using the verbatim
        code copies in work/, with sites re-projected from the recorded
        fitted_pos_global and the frame rebuilt from the pack joints.
Plus: cut-segment length statistics at every probed axial position (uncertainty budget).
"""
import json
import sys

import numpy as np

sys.path.insert(0, "work")
from target_envelope import containment, section_loop_containment, _plane_cut_segments  # noqa: E402
from mesh_target import MonkeyTarget  # noqa: E402

BASE = r"E:/PythonChimera/forearm_package/baseline_snapshot"
MARGIN = 0.001
BODIES = {"radius": ("elbow_R", "wrist_R"), "radius_l": ("elbow_L", "wrist_L")}


def law_cls(d):
    if d > 0.0:
        return "outside"
    if d <= -MARGIN:
        return "inside"
    return "inside_insufficient_clearance"


def hull_cls(dists, missing):
    """Session-05 hull law applied to recorded variant distances."""
    if missing:
        return "unresolved"
    classes = {law_cls(d) for d in dists}
    if len(classes) > 1:
        return "unresolved"  # class flip under band-width variation
    if classes == {"outside"}:
        return "outside"
    if classes == {"inside_insufficient_clearance"}:
        return "inside_insufficient_clearance"
    return "inside"


fit = json.load(open(BASE + "/runs/actual_monkey_fit.json"))
cand = json.load(open(BASE + "/runs/attachment_candidates.json"))
adm = json.load(open(BASE + "/runs/admission_actual_monkey.json"))

mismatches = []
notes = []


def check(label, expected, observed):
    ok = expected == observed
    if not ok:
        mismatches.append({"check": label, "expected": str(expected), "observed": str(observed)})
    return ok


print("=" * 110)
print("PATH A — re-derive classes from RECORDED data only")
print("=" * 110)
count_tables = {}
for body in BODIES:
    loop = fit["measurements"]["envelope_containment_loop"][body]
    hull = fit["measurements"]["envelope_containment"][body]
    tab = {"loop": {}, "hull": {}}
    for n in sorted(loop["per_site"]):
        rec = loop["per_site"][n]
        v = rec["verdict"]
        if v == "unresolved":
            ok = rec.get("n_identified_loops", 1) != 1
            check(f"loop {body}/{n} unresolved implies n_identified!=1", True, ok)
            check(f"loop {body}/{n} unresolved reason", "ambiguous_section", rec.get("reason", "")[:17])
        else:
            d = rec["dist_to_loop_m"]
            check(f"loop {body}/{n} recorded {v} vs law(d={d})", v, law_cls(d))
        tab["loop"].setdefault(v, []).append(n)
    for n in sorted(hull["per_site"]):
        rec = hull["per_site"][n]
        v = rec["verdict"]
        if v == "unresolved":
            reason = rec.get("reason", "")
            kind = "local_narrowing" if "local_narrowing" in reason else (
                "no_vertices" if "no_vertices" in reason else "flip")
            tab["hull"].setdefault(v, []).append(f"{n}({kind})")
            if kind == "flip":
                # a flip verdict must carry variant distances that genuinely disagree
                ds = [rec.get(k) for k in ("dist_to_hull_m", "dist_narrow_m", "dist_wide_m")]
                have = [d for d in ds if d is not None]
                check(f"hull {body}/{n} flip has >=3 variant dists", True, len(have) == 3)
                check(f"hull {body}/{n} flip classes disagree", True,
                      len({law_cls(d) for d in have}) > 1)
        else:
            ds, missing = [], False
            for k in ("dist_to_hull_m", "dist_narrow_m", "dist_wide_m"):
                if rec.get(k) is None:
                    missing = True
                else:
                    ds.append(rec[k])
            derived = hull_cls(ds, missing)
            check(f"hull {body}/{n} recorded {v} vs law(dists={ds})", v, derived)
            tab["hull"].setdefault(v, []).append(n)
    count_tables[body] = tab
    print(f"\n--- {body}: recorded count tables ---")
    for auth in ("loop", "hull"):
        row = tab[auth]
        print(f"  {auth:5s}: inside={len(row.get('inside', []))} "
              f"tight={len(row.get('inside_insufficient_clearance', []))} "
              f"outside={len(row.get('outside', []))} unresolved={len(row.get('unresolved', []))}")
        for cls, names in sorted(row.items()):
            print(f"     {cls:30s} {sorted(names)}")

print()
print("--- Known-state check (brief): loop 6/1/7/2, hull 3 inside/0 tight/5 outside/8 unresolved ---")
for body in BODIES:
    tab = count_tables[body]
    loop_counts = (len(tab["loop"].get("inside", [])), len(tab["loop"].get("inside_insufficient_clearance", [])),
                   len(tab["loop"].get("outside", [])), len(tab["loop"].get("unresolved", [])))
    hull_counts = (len(tab["hull"].get("inside", [])), len(tab["hull"].get("inside_insufficient_clearance", [])),
                   len(tab["hull"].get("outside", [])), len(tab["hull"].get("unresolved", [])))
    check(f"{body} loop counts 6/1/7/2", (6, 1, 7, 2), loop_counts)
    check(f"{body} hull counts 3/0/5/8", (3, 0, 5, 8), hull_counts)
    print(f"  {body}: loop={loop_counts} hull={hull_counts}")

print()
print("--- fit-json vs attachment-candidates per-site crosscheck ---")
n_x = 0
for body in BODIES:
    loop_ps = fit["measurements"]["envelope_containment_loop"][body]["per_site"]
    hull_ps = fit["measurements"]["envelope_containment"][body]["per_site"]
    for c in cand["bodies"][body]["candidates"]:
        sid = c["site_id"]
        sc = c["skin_containment"]
        check(f"cand auth label {body}/{sid}", "local_triangle_plane_loop", sc["authority"])
        check(f"cand loop verdict {body}/{sid}", loop_ps[sid]["verdict"], sc["loop"]["verdict"])
        if "dist_to_loop_m" in sc["loop"] and "dist_to_loop_m" in loop_ps[sid]:
            check(f"cand loop dist {body}/{sid}", loop_ps[sid]["dist_to_loop_m"], sc["loop"]["dist_to_loop_m"])
        hv, hd = sc["hull_sampling_diagnostic"]["verdict"], sc["hull_sampling_diagnostic"].get("dist_to_hull_m")
        check(f"cand hull verdict {body}/{sid}", hull_ps[sid]["verdict"], hv)
        if hd is not None:
            check(f"cand hull dist {body}/{sid}", hull_ps[sid]["dist_to_hull_m"], hd)
        n_x += 1
print(f"  crosschecked {n_x} candidates (16 x 2 sides), all fields above match" if not mismatches
      else f"  crosschecked {n_x} candidates, MISMATCHES BELOW")

print()
print("--- admission lists vs reproduced verdicts ---")
for body in BODIES:
    env = adm["envelope"][body]
    tab = count_tables[body]
    check(f"admission {body} loop_outside", sorted(tab["loop"].get("outside", [])), sorted(env["loop_outside"]))
    check(f"admission {body} loop_tight", sorted(tab["loop"].get("inside_insufficient_clearance", [])), sorted(env["loop_tight"]))
    check(f"admission {body} loop_ambiguous", sorted(tab["loop"].get("unresolved", [])), sorted(env["loop_ambiguous"]))
    check(f"admission {body} containment_outside", sorted(tab["hull"].get("outside", [])), sorted(env["containment_outside"]))
    check(f"admission {body} containment_unresolved",
          sorted(n.split("(")[0] for n in tab["hull"].get("unresolved", [])),
          sorted(env["containment_unresolved"]))
    # residual flags
    res = fit["residuals"]
    check(f"residual envelope_containment_loop.ok {body}",
          fit["measurements"]["envelope_containment_loop"][body]["ok"],
          not (env["loop_outside"] or env["loop_tight"] or env["loop_ambiguous"]))
    check(f"residual loop_outside flag {body}", bool(env["loop_outside"]),
          bool(res[f"envelope_containment_loop.outside.{body}"]))
    check(f"residual loop_tight flag {body}", bool(env["loop_tight"]),
          bool(res[f"envelope_containment_loop.tight.{body}"]))
    check(f"residual loop_ambiguous flag {body}", bool(env["loop_ambiguous"]),
          bool(res[f"envelope_containment_loop.ambiguous_section.{body}"]))
print("  admission envelope loop/hull lists == reproduced lists; residual flags consistent"
      if not mismatches else "  SEE MISMATCHES")

print()
print("=" * 110)
print("PATH B — full recompute from inputs (mesh + pack) through code copies")
print("=" * 110)
mt = MonkeyTarget(birth_path=BASE + "/inputs/monkey_birth.bin", pack_path=BASE + "/inputs/monkey_joints.bin")
meta = adm["meta"]
check("mesh sha256 == recorded", meta["target_mesh_sha256"], mt.birth_sha)
check("pack sha256 == recorded", meta["target_pack_sha256"], mt.pack_sha)
print(f"  mesh sha {mt.birth_sha[:16]}... pack sha {mt.pack_sha[:16]}...  verts={len(mt.V)} tris={len(mt.F)}")

# roll witness + ONB (verbatim logic from actual_target_fit._band_roll / compiler.onb_from_points)
def _band_roll(mt, prox_joint, P, a):
    verts = mt.band_verts(prox_joint)
    rel = verts - P
    perp = rel - np.outer(rel @ a, a)
    d2 = (perp ** 2).sum(axis=1)
    return verts[int(np.argmax(d2))].copy()


def _unit(v):
    return v / np.linalg.norm(v)


def onb_from_points(p0, p1, q):
    a = _unit(p1 - p0)
    t = (q - p0) - a * (a @ (q - p0))
    b = _unit(t)
    c = np.cross(a, b)
    return a, b, c


sites_all = fit["sites"]
recompute = {}
seg_stats = {}
for body, (pj, dj) in BODIES.items():
    P = mt.joint_pos(pj)
    P_d = mt.joint_pos(dj)
    a_unnorm = P_d - P            # baseline passes the UNNORMALIZED axis to _band_roll
    L = float(np.linalg.norm(a_unnorm))
    a_dir = a_unnorm / L
    q = _band_roll(mt, pj, P, a_unnorm)  # verbatim: actual_target_fit.py L523 uses (P_d - P)
    _, bu, cu = onb_from_points(P, P_d, q)
    geo = fit["measurements"]["outer_envelope"][body]["selected_geometry"]
    check(f"{body} proximal joint == recorded", [round(float(v), 9) for v in P], geo["proximal_joint_m"])
    check(f"{body} distal joint == recorded", [round(float(v), 9) for v in P_d], geo["distal_joint_m"])
    check(f"{body} axis len == recorded", round(L, 9), geo["axis_len_m"])
    db = float(np.max(np.abs(bu - np.array(geo["transverse_axes"]["b"]))))
    dc = float(np.max(np.abs(cu - np.array(geo["transverse_axes"]["c"]))))
    print(f"  {body}: rebuilt frame b dev={db:.2e} c dev={dc:.2e} (vs recorded, 1e-9-rounded)")

    # rebuild sites from the RECORDED fitted positions (rounded at 1e-9 in the packet)
    sites_bc = []
    for s in sites_all:
        if s["segment"] != body or s["unresolved"]:
            continue
        p = np.asarray(s["fitted_pos_global"], dtype=np.float64)
        rel = p - P
        sites_bc.append({"name": s["name"], "axial": float(rel @ a_dir),
                         "b": float(rel @ bu), "c": float(rel @ cu)})
    check(f"{body} 16 resolved sites", 16, len(sites_bc))
    loop_ps = fit["measurements"]["envelope_containment_loop"][body]["per_site"]
    for s in sites_bc:
        check(f"{body}/{s['name']} axial == recorded axial_m", round(loop_ps[s["name"]]["axial_m"], 9),
              round(s["axial"], 9))

    # recompute LOOP authority from mesh + pack
    ct_loop = section_loop_containment(mt, P, a_dir, bu, cu, sites_bc, margin_m=MARGIN,
                                       owner_joint_names=(pj, dj))
    # recompute HULL authority on the recorded envelope sections
    env_rec = fit["measurements"]["outer_envelope"][body]
    env_rec["selected_geometry"] = geo  # recorded geometry (1e-9 rounded)
    ct_hull = containment(sites_bc, env_rec, margin_m=MARGIN)

    recompute[body] = {"loop": ct_loop, "hull": ct_hull}
    for auth, ct in (("loop", ct_loop), ("hull", ct_hull)):
        rec_ps = fit["measurements"][f"envelope_containment{'_loop' if auth == 'loop' else ''}"][body]["per_site"]
        for n in sorted(rec_ps):
            check(f"RECOMPUTE {auth} {body}/{n} verdict", rec_ps[n]["verdict"], ct["per_site"][n]["verdict"])
            dk = "dist_to_loop_m" if auth == "loop" else "dist_to_hull_m"
            if ct["per_site"][n].get(dk) is not None and rec_ps[n].get(dk) is not None:
                ddelta = abs(ct["per_site"][n][dk] - rec_ps[n][dk])
                if ddelta > 2e-9:
                    notes.append(f"{auth} {body}/{n} dist delta {ddelta:.3e} m (> 2e-9 export rounding)")
    print(f"  {body}: recomputed loop verdicts "
          f"{ct_loop['n_inside']}/{ct_loop['n_inside_insufficient_clearance']}/"
          f"{ct_loop['n_outside']}/{ct_loop['n_unresolved']}  hull verdicts "
          f"{ct_hull['n_inside']}/{ct_hull['n_inside_insufficient_clearance']}/"
          f"{ct_hull['n_outside']}/{ct_hull['n_unresolved']}")

    # ---- cut-segment statistics for the uncertainty budget ----
    axials = sorted({round(s["axial"], 9) for s in sites_bc})
    per_ax = {}
    for ax in axials:
        segs = _plane_cut_segments(mt.V, mt.F, P, a_dir, ax)
        lengths = [float(np.linalg.norm(s0 - s1)) for s0, s1, _ in segs]
        # identified-loop segment lengths only (owner majority via re-run of identification)
        per_ax[ax] = {
            "n_segments": len(segs),
            "len_min_m": round(min(lengths), 9),
            "len_median_m": round(float(np.median(lengths)), 9),
            "len_max_m": round(max(lengths), 9),
            "len_mean_m": round(float(np.mean(lengths)), 9),
        }
    seg_stats[body] = per_ax

print()
print("--- cut-segment length statistics per probed axial position (all cut segments) ---")
for body, per_ax in seg_stats.items():
    allm = [d["len_median_m"] for d in per_ax.values()]
    allx = [d["len_max_m"] for d in per_ax.values()]
    print(f"  {body}: {len(per_ax)} axial positions; median-of-medians {np.median(allm)*1000:.3f} mm, "
          f"max-of-max {max(allx)*1000:.3f} mm")
    for ax in sorted(per_ax):
        d = per_ax[ax]
        print(f"    axial {ax:+.9f} m: n_seg={d['n_segments']:4d} min={d['len_min_m']*1000:7.3f} mm "
              f"median={d['len_median_m']*1000:7.3f} mm max={d['len_max_m']*1000:7.3f} mm")

# identified-loop geometry per body: perimeter, effective radius, sagitta, vertex spacing
print()
print("--- identified-loop discretization (per body, per site axial) ---")
loop_geo = {}
for body, (pj, dj) in BODIES.items():
    P = mt.joint_pos(pj)
    P_d = mt.joint_pos(dj)
    a_dir = (P_d - P) / np.linalg.norm(P_d - P)
    bu = np.array(fit["measurements"]["outer_envelope"][body]["selected_geometry"]["transverse_axes"]["b"])
    cu = np.array(fit["measurements"]["outer_envelope"][body]["selected_geometry"]["transverse_axes"]["c"])
    rec_ps = fit["measurements"]["envelope_containment_loop"][body]["per_site"]
    loop_geo[body] = {}
    for n in sorted(rec_ps):
        rec = rec_ps[n]
        if rec["verdict"] == "unresolved":
            continue
        ax = rec["axial_m"]
        segs = _plane_cut_segments(mt.V, mt.F, P, a_dir, ax)
        # identify the limb loop exactly as the module does (majority owner >= 0.5)
        owner_set = {mt.idx[x] for x in (pj, dj)}
        o = mt.assign[mt.F[:, 0]]
        o1, o2, o3 = mt.assign[mt.F[:, 0]], mt.assign[mt.F[:, 1]], mt.assign[mt.F[:, 2]]
        tri_owner = np.where(o1 == o2, o1, o3)
        from target_envelope import _chain_closed_loops
        loops, _, _ = _chain_closed_loops(segs)
        identified = None
        for pts, tris in loops:
            owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)
            if tris and owned / len(tris) >= 0.5:
                identified = (pts, tris)
                break
        if identified is None:
            continue
        pts, tris = identified
        rel = pts - P
        poly = np.column_stack([rel @ bu, rel @ cu])
        edges = poly - np.roll(poly, -1, axis=0)
        segl = np.linalg.norm(edges, axis=1)
        segl = segl[segl > 1e-12]
        # polygon area (shoelace) and perimeter -> effective radius A/p
        x, y = poly[:, 0], poly[:, 1]
        area = 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))
        per = float(segl.sum())
        r_eff = area / per
        sag = (float(np.max(segl)) ** 2) / (8 * r_eff)
        sag_med = (float(np.median(segl)) ** 2) / (8 * r_eff)
        loop_geo[body][n] = {"loop_points": int(len(pts)), "r_eff_m": round(r_eff, 6),
                             "seg_median_m": round(float(np.median(segl)), 9),
                             "seg_max_m": round(float(np.max(segl)), 9),
                             "sagitta_median_m": sag_med, "sagitta_max_m": sag}
    for n, g in sorted(loop_geo[body].items()):
        print(f"  {body}/{n:14s} pts={g['loop_points']:4d} r_eff={g['r_eff_m']*1000:6.2f} mm "
              f"seg_med={g['seg_median_m']*1000:6.3f} mm seg_max={g['seg_max_m']*1000:6.3f} mm "
              f"sagitta_med={g['sagitta_median_m']*1e6:6.2f} um sagitta_max={g['sagitta_max_m']*1e6:6.2f} um")

print()
print("=" * 110)
print("RESULT")
print("=" * 110)
if mismatches:
    print(f"MISMATCHES: {len(mismatches)}")
    for m in mismatches:
        print(f"  {m['check']}: expected {m['expected']} observed {m['observed']}")
else:
    print("ALL reproduction checks match (Path A records, admission crosscheck, Path B recompute).")
if notes:
    print("NOTES:")
    for n in notes:
        print("  " + n)

json.dump({"mismatches": mismatches, "notes": notes,
           "count_tables": {b: {a: {c: sorted(v) for c, v in t.items()} for a, t in tab.items()}
                            for b, tab in count_tables.items()},
           "segment_stats": seg_stats, "loop_geometry": loop_geo},
          open("receipts/reproduction.json", "w"), indent=1, default=str)
print("receipt -> receipts/reproduction.json")
sys.exit(0 if not mismatches else 1)
