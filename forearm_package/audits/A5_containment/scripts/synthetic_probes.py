"""A5 synthetic boundary probes — tests the four-class LAW on my OWN polygons/meshes.

No baseline data is read. Baseline module copied verbatim to work/target_envelope.py.
Reference distances are computed with an INDEPENDENT implementation (point-to-segment
min + crossing-number inside test) written here, not imported from the module under
test. For curved polygons the expected class is the LAW applied to the reference
distance (chord factor stated); exact -1 mm / 0 boundary semantics are pinned by
axis-aligned square probes where distances are exact in floating point.
"""
import json
import math
import sys

import numpy as np

sys.path.insert(0, "work")
from target_envelope import (  # noqa: E402
    containment,
    section_loop_containment,
    _dist_to_poly,
    _chain_closed_loops,
)

MARGIN = 0.001  # the 1 mm law margin (session-05 table)


# ---------- independent reference implementations (NOT the module under test) ----------
def ref_poly_dist(px, py, poly):
    """Signed distance: min distance to polygon boundary segments, negative inside
    (crossing-number point-in-polygon). Independent of target_envelope."""
    n = len(poly)
    best = math.inf
    inside = False
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        sx, sy = x2 - x1, y2 - y1
        tt = ((px - x1) * sx + (py - y1) * sy) / (sx * sx + sy * sy) if (sx * sx + sy * sy) > 0 else 0.0
        tt = min(1.0, max(0.0, tt))
        d = math.hypot(px - (x1 + tt * sx), py - (y1 + tt * sy))
        best = min(best, d)
        if (y1 > py) != (y2 > py):
            xin = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if xin > px:
                inside = not inside
    return -best if inside else best


def law_cls(d, margin=MARGIN):
    """The session-05 class law, applied to a distance."""
    if d > 0.0:
        return "outside"
    if d <= -margin:
        return "inside"
    return "inside_insufficient_clearance"


def circle_poly(r, n=96):
    ang = np.arange(n) * (2 * math.pi / n)
    return np.column_stack([r * np.cos(ang), r * np.sin(ang)])


results = []


def probe(name, expected, observed, note=""):
    ok = expected == observed
    results.append({"probe": name, "expected": expected, "observed": observed, "match": ok, "note": note})
    print(f"{'PASS' if ok else 'FAIL'}  {name:58s} expected={expected!r} observed={observed!r} {note}")


def geom_probe(name, px, py, poly, note=""):
    """Generic probe: module must agree with the reference distance AND classify by law."""
    d_ref = ref_poly_dist(px, py, poly)
    d_mod = _dist_to_poly(px, py, poly)
    probe(name, (round(d_ref, 9), law_cls(d_ref)), (round(d_mod, 9), law_cls(d_mod)),
          note + f" d_ref={d_ref:.6e} d_mod={d_mod:.6e}")


def hull_verdict_for(hull_narrow, hull_nom, hull_wide, site_bc, axial=0.0, half=0.008):
    sec = {
        "t": 0.5, "axis_pos_m": 0.0, "n_verts": 100, "w_b_m": 0.04, "w_c_m": 0.04,
        "hull_bc": [list(map(float, p)) for p in hull_nom],
        "hull_bc_narrow": [list(map(float, p)) for p in hull_narrow],
        "hull_bc_wide": [list(map(float, p)) for p in hull_wide],
    }
    env = {"sections": [sec], "selected_geometry": {"section_axial_band_half_m": half}}
    site = {"name": "probe", "axial": axial, "b": site_bc[0], "c": site_bc[1]}
    out = containment([site], env, margin_m=MARGIN)
    return out["per_site"]["probe"]


def ref_classes(site_bc, variants):
    return [law_cls(ref_poly_dist(site_bc[0], site_bc[1], h)) for h in variants]


print("=" * 100)
print("PART 1 — EXACT boundary semantics on an axis-aligned square (exact floats)")
print("=" * 100)
SQ = np.array([[0.0, 0.0], [0.04, 0.0], [0.04, 0.04], [0.0, 0.04]])
exact_cases = [
    ("d=0 exactly (on edge)", (0.02, 0.0), "inside_insufficient_clearance"),
    ("d=+1e-12 (just outside)", (0.02, -1e-12), "outside"),
    ("d=-1e-12 (just inside)", (0.02, 1e-12), "inside_insufficient_clearance"),
    ("d=-1mm exactly (AT margin, inclusive <=)", (0.02, MARGIN), "inside"),
    ("d=-1mm-1e-15 (past margin)", (0.02, MARGIN + 1e-15), "inside"),
    ("d=-1mm+1e-15 (shy of margin)", (0.02, MARGIN - 1e-15), "inside_insufficient_clearance"),
    ("d=-0.5mm (tight zone)", (0.02, 0.0005), "inside_insufficient_clearance"),
    ("center (deep inside)", (0.02, 0.02), "inside"),
    ("d=+4.6mm outside (report-05 magnitude)", (0.02, -0.0046), "outside"),
]
for label, (px, py), exp in exact_cases:
    d_mod = _dist_to_poly(px, py, SQ)
    d_ref = ref_poly_dist(px, py, SQ)
    probe(f"square {label}", (exp, round(d_ref, 15)), (law_cls(d_mod), round(d_mod, 15)),
          f"d_mod={d_mod!r}")

print()
print("=" * 100)
print("PART 2 — hull-path four classes via containment() on synthetic band variants")
print("=" * 100)
r_n, r_0, r_w = 0.0198, 0.0202, 0.0206   # concentric 96-gons (chord deficit ~1.02e-5*r)
hn, h0, hw = circle_poly(r_n), circle_poly(r_0), circle_poly(r_w)
site = (0.0196, 0.0)
rc = ref_classes(site, (hn, h0, hw))
assert rc == ["inside_insufficient_clearance"] * 3, f"probe design error: {rc}"
v = hull_verdict_for(hn, h0, hw, site)
probe("hull tight (d in (-1mm,0] at EVERY variant)", "inside_insufficient_clearance", v["verdict"],
      f"ref classes={rc} dists {v.get('dist_narrow_m')}/{v.get('dist_to_hull_m')}/{v.get('dist_wide_m')}")

v = hull_verdict_for(hn, h0, hw, (0.030, 0.0))
rc = ref_classes((0.030, 0.0), (hn, h0, hw))
probe("hull outside (d>0 at every variant)", "outside", v["verdict"], f"ref classes={rc}")

v = hull_verdict_for(hn, h0, hw, (0.010, 0.0))
rc = ref_classes((0.010, 0.0), (hn, h0, hw))
probe("hull inside (d<=-1mm at every variant)", "inside", v["verdict"], f"ref classes={rc}")

# flip across three classes (inside/tight/outside)
hn3, h03, hw3 = circle_poly(0.0210), circle_poly(0.0200), circle_poly(0.0190)
site = (0.0195, 0.0)
rc = ref_classes(site, (hn3, h03, hw3))
assert len(set(rc)) == 3, f"probe design error: {rc}"
v = hull_verdict_for(hn3, h03, hw3, site)
probe("hull flip inside/tight/outside -> unresolved", "unresolved", v["verdict"],
      f"ref classes={rc}")

# flip between inside and inside_tight ONLY (law: ANY class flip -> unresolved)
hn4, h04, hw4 = circle_poly(0.0210), circle_poly(0.0205), circle_poly(0.0200)
site = (0.0198, 0.0)
rc = ref_classes(site, (hn4, h04, hw4))
assert set(rc) == {"inside", "inside_insufficient_clearance"}, f"probe design error: {rc}"
v = hull_verdict_for(hn4, h04, hw4, site)
probe("hull flip inside/inside_tight -> unresolved", "unresolved", v["verdict"],
      f"ref classes={rc} reason={v.get('reason','')[:50]}...")

# no sampled band near axial position
v = hull_verdict_for(hn, h0, hw, (0.010, 0.0), axial=0.05, half=0.008)
probe("hull no-band (axial 50mm, half 8mm) -> unresolved", "unresolved", v["verdict"],
      f"reason={v.get('reason','')[:55]}...")

# a variant hull unusable (<3 points) even with 2 good variants
sec_missing = {
    "t": 0.5, "axis_pos_m": 0.0, "n_verts": 100, "w_b_m": 0.04, "w_c_m": 0.04,
    "hull_bc": [list(map(float, p)) for p in h0],
    "hull_bc_narrow": [list(map(float, p)) for p in hn],
    "hull_bc_wide": [],
}
env_missing = {"sections": [sec_missing], "selected_geometry": {"section_axial_band_half_m": 0.008}}
out = containment([{"name": "probe", "axial": 0.0, "b": 0.010, "c": 0.0}], env_missing, margin_m=MARGIN)
v = out["per_site"]["probe"]
probe("hull missing-variant -> unresolved", "unresolved", v["verdict"],
      f"reason={v.get('reason','')[:55]}...")

# exact -1 mm boundary driven through containment() with square hulls
SQ_LIST = [list(map(float, p)) for p in SQ]
sec_sq = {"t": 0.5, "axis_pos_m": 0.0, "n_verts": 4, "w_b_m": 0.04, "w_c_m": 0.04,
          "hull_bc": SQ_LIST, "hull_bc_narrow": SQ_LIST, "hull_bc_wide": SQ_LIST}
env_sq = {"sections": [sec_sq], "selected_geometry": {"section_axial_band_half_m": 0.008}}
out = containment([{"name": "probe", "axial": 0.0, "b": 0.02, "c": MARGIN}], env_sq, margin_m=MARGIN)
probe("hull square d=-1mm exactly -> inside", "inside", out["per_site"]["probe"]["verdict"])
out = containment([{"name": "probe", "axial": 0.0, "b": 0.02, "c": 0.0}], env_sq, margin_m=MARGIN)
probe("hull square d=0 exactly -> inside_insufficient_clearance",
      "inside_insufficient_clearance", out["per_site"]["probe"]["verdict"])

print()
print("=" * 100)
print("PART 3 — loop-path classes via section_loop_containment on SYNTHETIC tube meshes")
print("=" * 100)


def tube_mesh(cross="circle", r=0.020, length=0.06, na=64, nr=24, x0=0.0, second=None):
    """Tube(s) along +x. second=(radius, cy, owner) adds a disjoint second tube."""
    verts, tris, assign = [], [], []

    def add_tube(radius, cy, own):
        base = len(verts)
        for k in range(nr + 1):
            x = x0 + length * k / nr
            for j in range(na):
                a = 2 * math.pi * j / na
                if cross == "circle":
                    verts.append((x, cy + radius * math.cos(a), radius * math.sin(a)))
                else:  # chamfered-square cross-section walked CCW corner to corner
                    q = na // 4
                    e, f = j // q, j % q
                    t = f / q
                    corners = [(-radius, radius), (radius, radius), (radius, -radius), (-radius, -radius)]
                    sx, sy = corners[e]
                    ex, ey = corners[(e + 1) % 4]
                    verts.append((x, cy + sx + t * (ex - sx), sy + t * (ey - sy)))
                assign.append(own)
        for k in range(nr):
            for j in range(na):
                a0 = base + k * na + j
                a1 = base + k * na + (j + 1) % na
                b0 = a0 + na
                b1 = a1 + na
                tris.append((a0, a1, b0))
                tris.append((a1, b1, b0))

    add_tube(radius=r, cy=0.0, own=0)
    if second is not None:
        r2, cy2, own2 = second
        add_tube(radius=r2, cy=cy2, own=own2)
    V = np.array(verts, dtype=float)
    F = np.array(tris, dtype=np.int64)
    assign = np.array(assign, dtype=np.int64)
    idx = {"elbow_R": 0, "wrist_R": 1, "other_R": 2}
    return V, F, assign, idx


class FakeMT:
    """Minimal mt surface for section_loop_containment: V, F, assign, idx."""

    def __init__(self, V, F, assign, idx):
        self.V, self.F, self.assign, self.idx = V, F, assign, idx


P = np.array([0.0, 0.0, 0.0])
a_dir = np.array([1.0, 0.0, 0.0])
bu = np.array([0.0, 1.0, 0.0])
cu = np.array([0.0, 0.0, 1.0])
AX = 0.03125  # strictly BETWEEN vertex rings (0.030 / 0.0325): strict sign crossings exist
R = 0.020

V, F, assign, idx = tube_mesh()
mt = FakeMT(V, F, assign, idx)

# nominal-intent probes; expected class = LAW applied to the independent reference
# distance on the analytic cross-section polygon (a prism: same polygon at every x).
nominal = [
    ("center (nominal d=-20mm)", 0.0),
    ("d=-0.5mm nominal", R - 0.0005),
    ("d=+0.5mm nominal", R + 0.0005),
    ("d=+5mm nominal", R + 0.005),
    ("d=-1mm nominal (chord -0.9988mm)", R - MARGIN),
]
sites_in = [{"name": n, "axial": AX, "b": y, "c": 0.0} for n, y in nominal]
out = section_loop_containment(mt, P, a_dir, bu, cu, sites_in,
                              margin_m=MARGIN, owner_joint_names=("elbow_R", "wrist_R"))
poly_ring = circle_poly(R, 64)  # the prism cross-section the plane actually cuts
n_pts = int(out["per_site"][sites_in[0]["name"]]["loop_points"])
# each quad strip contributes TWO cut segments sharing an interpolated endpoint ->
# loop carries consecutive duplicated points (zero-length edges guarded in _dist_to_poly)
probe("tube cut yields 128 loop points (64 unique, adjacent duplicates)", 128, n_pts)
v0 = out["per_site"][sites_in[0]["name"]]
probe("tube cut identified exactly 1 loop", 1, int(v0["n_identified_loops"]))
for s in sites_in:
    d_ref = ref_poly_dist(s["b"], s["c"], poly_ring)
    v = out["per_site"][s["name"]]
    d_mod = v.get("dist_to_loop_m")
    probe(f"loop {s['name']}", law_cls(d_ref), v["verdict"],
          f"d_ref={d_ref:.6e} d_mod={d_mod:.6e}")
    probe(f"loop dist agreement@1e-9 {s['name']}", round(abs(d_ref), 9), round(abs(d_mod), 9),
          "module records distances rounded to 1e-9 m")


def square_poly(r, na=16):
    """The same chamfered-square cross-section the tube_mesh constructor lays out (CCW)."""
    q = na // 4
    corners = [(-r, r), (r, r), (r, -r), (-r, -r)]
    pts = []
    for j in range(na):
        e, f = j // q, j % q
        t = f / q
        sx, sy = corners[e]
        ex, ey = corners[(e + 1) % 4]
        pts.append((sx + t * (ex - sx), sy + t * (ey - sy)))
    return np.array(pts)


# ROBUST boundary probes through the LOOP path with the chamfered-square tube
# (exact zero and exact-margin semantics are pinned in Parts 1-2; here the offsets
# are >= 0.5 mm from any class boundary so floats cannot flip the class)
V4, F4, a4, i4 = tube_mesh(cross="square", na=16)
mt4 = FakeMT(V4, F4, a4, i4)
sq_poly = square_poly(0.020, 16)
sq_sites = [
    ("sq d=0 exactly (on flat edge)", 0.020),
    ("sq d=-2mm (robust inside)", 0.018),
    ("sq d=-0.5mm (robust tight)", 0.0195),
    ("sq d=+1mm (robust outside)", 0.021),
]
out4 = section_loop_containment(mt4, P, a_dir, bu, cu,
                                [{"name": n, "axial": AX, "b": y, "c": 0.0} for n, y in sq_sites],
                                margin_m=MARGIN, owner_joint_names=("elbow_R", "wrist_R"))
for n, y in sq_sites:
    d_ref = ref_poly_dist(y, 0.0, sq_poly)
    v = out4["per_site"][n]
    probe(f"loop {n}", law_cls(d_ref), v["verdict"],
          f"d_ref={d_ref:.6e} d_mod={v.get('dist_to_loop_m'):.6e}")

# TWO loops both owned by the side -> 2 identified -> unresolved (no choosing by size)
V2, F2, assign2, idx2 = tube_mesh(second=(0.015, 0.06, 1))
mt2 = FakeMT(V2, F2, assign2, idx2)
out2 = section_loop_containment(mt2, P, a_dir, bu, cu,
                                [{"name": "amb", "axial": AX, "b": 0.0, "c": 0.0}],
                                margin_m=MARGIN, owner_joint_names=("elbow_R", "wrist_R"))
v = out2["per_site"]["amb"]
probe("loop two owned loops -> unresolved", "unresolved", v["verdict"],
      f"n_identified={v['n_identified_loops']}")

# second tube owned by a FOREIGN joint -> only 1 identified -> resolved
V3, F3, assign3, idx3 = tube_mesh(second=(0.015, 0.06, 2))
mt3 = FakeMT(V3, F3, assign3, idx3)
out3 = section_loop_containment(mt3, P, a_dir, bu, cu,
                                [{"name": "disamb", "axial": AX, "b": 0.0, "c": 0.0}],
                                margin_m=MARGIN, owner_joint_names=("elbow_R", "wrist_R"))
v = out3["per_site"]["disamb"]
probe("loop foreign-owned second loop ignored -> inside", "inside", v["verdict"],
      f"n_identified={v['n_identified_loops']}")

# plane misses the mesh -> 0 loops -> unresolved
out5 = section_loop_containment(mt, P, a_dir, bu, cu,
                                [{"name": "beyond", "axial": 0.5, "b": 0.0, "c": 0.0}],
                                margin_m=MARGIN, owner_joint_names=("elbow_R", "wrist_R"))
v = out5["per_site"]["beyond"]
probe("loop axial beyond mesh -> unresolved", "unresolved", v["verdict"],
      f"n_loops={v['n_loops']} n_identified={v['n_identified_loops']}")

print()
print("=" * 100)
print("PART 4 — open chains never close (direct _chain_closed_loops probes)")
print("=" * 100)
segs = [
    (np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), 0),
    (np.array([2.0, 0.0, 0.0]), np.array([3.0, 0.0, 0.0]), 1),
]
loops, n_open, n_degen = _chain_closed_loops(segs)
probe("chain two stray segments", (0, 2, 0), (len(loops), n_open, n_degen))

segs_v = [
    (np.array([0.0, 0.0, 0.0]), np.array([1.0, 1.0, 0.0]), 0),
    (np.array([1.0, 1.0, 0.0]), np.array([2.0, 0.0, 0.0]), 1),
]
loops, n_open, n_degen = _chain_closed_loops(segs_v)
probe("chain open V", (0, 1, 0), (len(loops), n_open, n_degen))

segs_q = [
    (np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), 0),
    (np.array([1.0, 0.0, 0.0]), np.array([1.0, 1.0, 0.0]), 1),
    (np.array([1.0, 1.0, 0.0]), np.array([0.0, 1.0, 0.0]), 2),
    (np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 0.0]), 3),
]
loops, n_open, n_degen = _chain_closed_loops(segs_q)
probe("chain closed quad", (1, 0, 0), (len(loops), n_open, n_degen))
if loops:
    probe("closed quad point count (closing point dropped)", 4, int(len(loops[0][0])))

for gap, expected in ((1e-8, (1, 0, 0)), (1e-6, (0, 1, 0))):
    g = gap
    segs_g = [
        (np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), 0),
        (np.array([1.0, 0.0, 0.0]), np.array([1.0, 1.0, 0.0]), 1),
        (np.array([1.0, 1.0, 0.0]), np.array([0.0, 1.0, 0.0]), 2),
        (np.array([0.0, 1.0 + g, 0.0]), np.array([0.0, 0.0, 0.0]), 3),
    ]
    loops, n_open, n_degen = _chain_closed_loops(segs_g)
    if g < 1e-7:
        label, expected_n = "chain 10nm gap (below 100nm tol) closes", (1, 0, 0)
    else:
        # gapped quad = 3-segment open chain + 1 stranded segment: TWO open chains,
        # zero loops — the law is "open never closes", and it never bridges the gap
        label, expected_n = "chain 1um gap (above tol) never bridges", (0, 2, 0)
    probe(f"{label}", expected_n, (len(loops), n_open, n_degen))

print()
print("=" * 100)
print("PART 5 — _dist_to_poly on a CONCAVE polygon (loop path claims concavity support)")
print("=" * 100)
L_poly = np.array([[0.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0], [1.0, 2.0], [0.0, 2.0]])
concave_cases = [
    ("deep in thick arm", (0.5, 0.5)),
    ("deep in thin arm", (0.5, 1.5)),
    ("inside notch mouth", (1.2, 1.2)),
    ("outside right", (2.5, 0.5)),
    ("exactly at reflex vertex", (1.0, 1.0)),
    ("outside diagonal of notch", (1.3, 1.3)),
]
for label, (px, py) in concave_cases:
    geom_probe(f"concave {label}", px, py, L_poly)

n_pass = sum(1 for r in results if r["match"])
print()
print(f"TOTAL: {n_pass}/{len(results)} probes match the law")
json.dump(results, open("receipts/synthetic_probes.json", "w"), indent=1)
print("receipt -> receipts/synthetic_probes.json")
sys.exit(0 if n_pass == len(results) else 1)
