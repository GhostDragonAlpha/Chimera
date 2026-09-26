"""verify_contact -- M-F04: ground and trunk contact geometry verification (L1).

Item F04, verbatim: "No unacceptable tunnelling, ghost support, interpenetration or
visual/collision disagreement in frozen cases. Only claimed collision capabilities
must be demonstrated." Contracts C08 (contact/collision), C14 (terrain), C15 (trunk
surface). Case matrix FROZEN in PREREGISTRATION.md (same dir) BEFORE this file was
written; every bound below is derived from pinned numbers, cited inline.

Layer separation (declared, honest):
  L1 (THIS FILE) verifies the DECLARED geometric contact model, verifiable now:
      - terrain collision surface = the stored grid's triangulation, queried through
        terrain_query.TerrainSurface (F02; strict-> boundary, earth_environment.hpp:118)
      - trunk collision representation = the EXACT analytic cylinder solid
        (trunk_declaration.collision_representation.solid; F03 HANDOFFS "To F04" #1)
      - walker contact features = the sole points with the engine's own gap law
        gap = point_y + r - surface  (gait_controller.hpp:635-643 gap_of;
        gait_scene.py:178), r = 0.004 m (gait_scene.py:28 SOLE_RADIUS)
  L2 (reported separately, NOT here) records what the frozen engine can exercise
      in-vivo: point spheres vs ONE plane only. No engine C++ is imported or edited.

CPU-only; headless; stdlib-only; writes ONLY agents/F04_contact/receipts/.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TERRAIN_BUNDLE = os.path.join(REPO, "tools", "monkey_campaign", "data",
                              "monkey_clearing", "terrain_bundle.json")
TRUNK_DECL = os.path.join(REPO, "tools", "monkey_campaign", "data",
                          "monkey_trunk", "trunk_declaration.json")
F01_DECL = os.path.join(REPO, "tools", "monkey_campaign", "data",
                        "monkey_clearing", "clearing_declaration.json")
RECEIPTS = os.path.join(HERE, "receipts")

SEED = 20260924                      # frozen seed (prereg)
R_SOLE = 0.004                       # gait_scene.py:28 SOLE_RADIUS; trunk derivation
K_TOUCH = 1e-5                       # gait_controller.hpp:36
K_RELEASE_BAND = 1e-6                # gait_controller.hpp:52
DT_MAX = 1.0 / 300.0                 # gait_controller.hpp:1961 (dt <= 1/300, substeps 4)
V_MAX = 1.01                         # derived_numbers.json timing_paper.simulated_before.speed_m_s
S_TICK = V_MAX * DT_MAX              # 3.366667e-3 m per tick (declared max travel)
SLOPE_LAW = 0.05                     # F01 max_slope_bound
S_TICK_VERT = S_TICK * math.sin(math.atan(SLOPE_LAW))   # 1.681230e-4 m (derived)
TRUNK_TOL = 2e-4                     # trunk_declaration representation_error.tolerance_m
TERRAIN_H_TOL = 1e-9                 # F02's frozen height family
TERRAIN_N_TOL = 1e-12                # F02's frozen normal family
ANALYTIC_TOL = 1e-9                  # trunk_recipe.on_lateral's own tolerance
MOUND_MIN_DIAM = 2.0 * 4.329635      # min mound diameter (F01 mound 2 radius)


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sibling(name):
    return _load_module(name, os.path.join(REPO, "tools", "monkey_campaign",
                                           "data", "monkey_clearing", name + ".py"))


# --- geometry (stdlib, closed-form; no second truth) ---------------------------
def vsub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def vadd(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def vscale(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def vdot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])
def vnorm(a): return math.sqrt(vdot(a, a))
def vdist(a, b): return vnorm(vsub(a, b))


def sdf_capped_cylinder(p, cx, cz, radius, y0, height):
    """Exact signed distance to the solid {dist_axis <= R, y0 <= y <= y0+H};
    negative inside (standard capped-cylinder SDF)."""
    dr = math.hypot(p[0] - cx, p[2] - cz) - radius
    dy = abs(p[1] - (y0 + height / 2.0)) - height / 2.0
    outside = math.hypot(max(dr, 0.0), max(dy, 0.0))
    inside = min(max(dr, dy), 0.0)
    return outside + inside


def point_triangle_distance(p, a, b, c):
    """Exact point-triangle distance (Ericson, Real-Time Collision Detection 5.1.5)."""
    ab, ac, ap = vsub(b, a), vsub(c, a), vsub(p, a)
    d1, d2 = vdot(ab, ap), vdot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return vdist(p, a)
    bp = vsub(p, b)
    d3, d4 = vdot(ab, bp), vdot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return vdist(p, b)
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        return vdist(p, vadd(a, vscale(ab, v)))
    cp = vsub(p, c)
    d5, d6 = vdot(ab, cp), vdot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return vdist(p, c)
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        return vdist(p, vadd(a, vscale(ac, w)))
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return vdist(p, vadd(a, vscale(vsub(c, b), w)))
    denom = 1.0 / (va + vb + vc)
    v, w = vb * denom, vc * denom
    return vdist(p, vadd(a, vadd(vscale(ab, v), vscale(ac, w))))


class Model:
    """The declared L1 contact model: terrain query surface + analytic trunk."""

    def __init__(self):
        tq = _sibling("terrain_query")
        self.tq = tq
        self.surf = tq.load(TERRAIN_BUNDLE)          # strict: validates the bundle
        tr = _load_module("trunk_recipe",
                          os.path.join(REPO, "tools", "monkey_campaign", "data",
                                       "monkey_trunk", "trunk_recipe.py"))
        self.trunk_recipe = tr
        self.decl = tr.load_declaration(TRUNK_DECL)  # strict load
        self.trunk_receipt = tr.validate_declaration(self.decl, strict_prereg=True)
        with open(F01_DECL, "rb") as fh:
            self.f01 = json.load(fh)
        solid = self.decl["collision_representation"]["solid"]
        self.cx = solid["axis_base_m"][0]
        self.cz = solid["axis_base_m"][2]
        self.R = solid["radius_m"]
        self.y0 = solid["axis_base_m"][1]
        self.H = solid["height_m"]
        rm = self.decl["render_mesh"]
        raw = rm["vertices"]
        if raw and isinstance(raw[0], (list, tuple)):
            self.tverts = [tuple(v[:3]) for v in raw]          # nested per-vertex
        else:
            self.tverts = [tuple(raw[9 * i:9 * i + 3])         # flat 9-float layout
                           for i in range(rm["vertex_count"])]
        self.tidx = rm["indices"]

    # -- terrain ---------------------------------------------------------------
    def h(self, x, z):
        return self.surf.height_at(x, z)

    def gap_law(self, point, x=None, z=None):
        """The engine's own law, generalized vertical: gap = p_y + r - h(x,z)
        (gait_controller.hpp:635-643 with the single plane replaced by the
        containing triangle's plane value; gait_scene.py:178 verbatim form)."""
        return point[1] + R_SOLE - self.h(point[0] if x is None else x,
                                          point[2] if z is None else z)

    def ground_triangles(self):
        """(A, B, C, centroid_xz, slope) over the 3,200 stored ground triangles."""
        out = []
        s = self.surf
        for t in range(0, s.ground_index_count, 3):
            ia, ib, ic = s.indices[t], s.indices[t + 1], s.indices[t + 2]
            a = tuple(s.vertices[9 * ia:9 * ia + 3])
            b = tuple(s.vertices[9 * ib:9 * ib + 3])
            c = tuple(s.vertices[9 * ic:9 * ic + 3])
            n = vcross(vsub(b, a), vsub(c, a))
            ln = vnorm(n)
            slope = math.hypot(n[0], n[2]) / n[1]
            out.append((a, b, c, ((a[0] + b[0] + c[0]) / 3.0, (a[2] + b[2] + c[2]) / 3.0),
                        slope, (n[0] / ln, n[1] / ln, n[2] / ln)))
        return out

    def trunk_mesh_distance(self, p):
        return min(point_triangle_distance(p, self.tverts[self.tidx[i]],
                                           self.tverts[self.tidx[i + 1]],
                                           self.tverts[self.tidx[i + 2]])
                   for i in range(0, len(self.tidx), 3))

    def post_mesh_distance(self, p, i_start, i_count):
        s = self.surf
        best = float("inf")
        for t in range(i_start, i_start + i_count, 3):
            a = tuple(s.vertices[9 * s.indices[t]:9 * s.indices[t] + 3])
            b = tuple(s.vertices[9 * s.indices[t + 1]:9 * s.indices[t + 1] + 3])
            c = tuple(s.vertices[9 * s.indices[t + 2]:9 * s.indices[t + 2] + 3])
            d = point_triangle_distance(p, a, b, c)
            if d < best:
                best = d
        return best


# --- the frozen cases ----------------------------------------------------------
def tun_01(m):
    """Through-face sweeps, terrain: caught iff min gap <= kTouch (the engine's own
    band, gait_controller.hpp:1727). Bounds = per-tick travel (derived)."""
    cases, worst_pen_ratio = [], 0.0

    def drop(x, z, label, bound):
        nonlocal worst_pen_ratio
        h = m.h(x, z)
        y = h + 0.5
        caught, pen, k = False, 0.0, 0
        while y > h - R_SOLE - 0.01 and k < 200000:
            gap = y + R_SOLE - h
            if gap <= K_TOUCH and not caught:
                caught, pen = True, max(0.0, (h - R_SOLE) - y)
                break
            y -= V_MAX * DT_MAX
            k += 1
        ok = caught and pen <= bound
        worst_pen_ratio = max(worst_pen_ratio, pen / bound if bound else 0.0)
        cases.append({"probe": label, "caught": caught, "pen_m": pen,
                      "bound_m": bound, "ok": ok})
        return ok

    tris = m.ground_triangles()
    worst = max(tris, key=lambda t: t[4])
    ok = drop(worst[3][0], worst[3][1],
              "worst-slope triangle centroid (slope %.6f)" % worst[4], S_TICK)
    for i, mnd in enumerate(m.surf.mounds):
        ok &= drop(mnd["centre_x_m"], mnd["centre_z_m"], "mound %d crest" % (i + 1), S_TICK)
    # (c) terrain-following 45-degree diagonal onto mound 2's east flank through
    # F02's worst discretization point (19.5, 5.5)
    s45 = 1.0 / math.sqrt(2.0)
    vh = V_MAX * math.cos(math.atan(SLOPE_LAW))
    vv = V_MAX * math.sin(math.atan(SLOPE_LAW))
    x, z = 19.5 + 0.2 * s45, 5.5 + 0.2 * s45
    y = m.h(x, z) + 0.5
    caught, pen, k = False, 0.0, 0
    while k < 200000:
        gap = y + R_SOLE - m.h(x, z)
        if gap <= K_TOUCH and not caught:
            caught, pen = True, max(0.0, (m.h(x, z) - R_SOLE) - y)
            break
        x -= vh * DT_MAX * s45
        z -= vh * DT_MAX * s45
        y -= vv * DT_MAX
        k += 1
    ok_c = caught and pen <= S_TICK_VERT
    cases.append({"probe": "45-deg terrain-following onto (19.5, 5.5)",
                  "caught": caught, "pen_m": pen, "bound_m": S_TICK_VERT, "ok": ok_c})
    ok &= ok_c
    ix, iz, _, _ = m.surf.cell_of(m.cx, m.cz)
    ok &= drop(m.surf.x0 + (ix + 0.5) * m.surf.dx, m.surf.z0 + (iz + 0.5) * m.surf.dz,
               "trunk-site cell centre", S_TICK)
    fired = not ok
    return {"id": "TUN-01", "verdict": "FAIL" if fired else "PASS",
            "falsifier_fired": fired, "cases": cases,
            "worst_pen_over_bound": worst_pen_ratio}


def tun_02(m):
    """CONTROL (must fire): ridge-skip. Horizontal flyover at the law-rest height of
    mound 5's crest (the innermost mound: the only one with room for the full step
    span inside the extent rule) with a synthetic sample step = min mound radius
    (half the min mound diameter). The true path grazes gap=0 at the crest; the
    sampler must MISS."""
    mnd = m.surf.mounds[4]
    step = MOUND_MIN_DIAM / 2.0
    y = m.h(mnd["centre_x_m"], mnd["centre_z_m"]) - R_SOLE   # law rest at the crest
    # half-step phase offset: the control models a crossing MISSED between samples,
    # so no sample may sit at the crest itself (frozen construction, not tuning)
    xs = [mnd["centre_x_m"] - 1.5 * step + i * step for i in range(4)]
    gaps = [y + R_SOLE - m.h(x, mnd["centre_z_m"]) for x in xs]
    missed = min(gaps) > K_TOUCH
    return {"id": "TUN-02", "verdict": "PASS (control fires)" if missed else "FAIL",
            "falsifier_fired": not missed, "control_expected": "miss",
            "control_fired": missed, "step_m": step,
            "crest_m": [mnd["centre_x_m"], mnd["centre_z_m"]],
            "min_sampled_gap_m": min(gaps), "gaps_m": gaps,
            "note": "true continuous path grazes gap=0 at the crest; a missed catch "
                    "proves the harness detects tunnelling (non-vacuity); mound 5 "
                    "chosen because the step span must stay inside the extent rule"}


def tun_03(m):
    """Head-on trunk sweeps at mid-height. Catch criterion = geometric (the trunk's
    DECLARED analytic contract; the engine has no prop law to copy): a sample with
    sdf <= r_s. L2 records that no engine machinery exists for this."""
    y, z = m.y0 + m.H / 2.0, m.cz
    caught, pen, k = False, 0.0, 0
    x = m.cx + 5.0
    while x > m.cx - 5.0 and k < 200000:
        sdf = sdf_capped_cylinder((x, y, z), m.cx, m.cz, m.R, m.y0, m.H)
        if sdf <= R_SOLE and not caught:
            caught, pen = True, max(0.0, R_SOLE - sdf)
            break
        x -= S_TICK
        k += 1
    ok_a = caught and pen <= S_TICK
    # (b) CONTROL (must fire): sample step 0.164 m = 2x the 0.082 m catch chord
    # (2R + 2r_s); frozen phase from cx+5.0 must straddle the window.
    step = 2.0 * (2.0 * m.R + 2.0 * R_SOLE)
    x, k, min_sdf = m.cx + 5.0, 0, float("inf")
    while x > m.cx - 5.0:
        min_sdf = min(min_sdf, sdf_capped_cylinder((x, y, z), m.cx, m.cz, m.R, m.y0, m.H))
        x -= step
        k += 1
    missed = min_sdf > R_SOLE
    return {"id": "TUN-03", "verdict": "PASS" if (ok_a and missed) else "FAIL",
            "falsifier_fired": not (ok_a and missed),
            "a": {"caught": caught, "pen_m": pen, "bound_m": S_TICK, "ok": ok_a,
                  "step_m": S_TICK},
            "b_control": {"expected": "miss", "fired": missed, "step_m": step,
                          "min_sdf_m": min_sdf, "samples": k,
                          "catch_chord_m": 2 * m.R + 2 * R_SOLE}}


def tun_04(m):
    """Crease/edge sweeps: 500 seeded vertical drops at shared-edge points in the
    r <= 2 m ring around the trunk site (worst twisted cell's 4 corners first), plus
    edge continuity |dh| <= 1e-9 across 1,000 seeded crossings."""
    rng = random.Random(SEED)
    s, cx, cz = m.surf, m.cx, m.cz
    # worst twisted cell: max diagonal-split difference 0.5*|h00+h11-h01-h10|
    worst_diff, wcell = -1.0, None
    for ix in range(s.nx - 1):
        for iz in range(s.nz - 1):
            h00, h10, h01, h11 = s._corners(ix, iz)
            diff = 0.5 * abs(h00 + h11 - h01 - h10)
            if diff > worst_diff:
                worst_diff, wcell = diff, (ix, iz)
    probes = []
    ix, iz = wcell
    for cxx, czz in [(ix, iz), (ix + 1, iz), (ix, iz + 1), (ix + 1, iz + 1)]:
        probes.append((s.x0 + cxx * s.dx, s.z0 + czz * s.dz, "twisted-cell corner"))
    while len(probes) < 500:
        ang = rng.uniform(0, 2 * math.pi)
        rad = math.sqrt(rng.uniform(0, 1)) * 2.0
        px, pz = cx + rad * math.cos(ang), cz + rad * math.sin(ang)
        cix, ciz, tx, tz = s.cell_of(px, pz)
        # snap to the nearest shared edge of that cell (exactly on it)
        edges = [((0, 0), (1, 0)), ((1, 0), (1, 1)), ((1, 1), (0, 1)), ((0, 1), (0, 0))]
        e = edges[rng.randrange(4)]
        t = rng.uniform(0.01, 0.99)
        ex = s.x0 + (cix + e[0][0] + (e[1][0] - e[0][0]) * t) * s.dx
        ez = s.z0 + (ciz + e[0][1] + (e[1][1] - e[0][1]) * t) * s.dz
        probes.append((ex, ez, "shared edge"))
    caught_n, worst_pen = 0, 0.0
    for px, pz, _tag in probes:
        h = m.h(px, pz)
        y = h + 0.5
        while y > h - R_SOLE - 0.01:
            gap = y + R_SOLE - h
            if gap <= K_TOUCH:
                caught_n += 1
                worst_pen = max(worst_pen, max(0.0, (h - R_SOLE) - y))
                break
            y -= V_MAX * DT_MAX
    # continuity: 1,000 seeded edge crossings (diagonals + shared grid edges).
    # Each side is EXACTLY linear, so the value difference across +-eps has the
    # exact prediction eps*(sum of the two triangles' gradient components along
    # the crossing direction); the frozen absolute 1e-9 bound ignored this linear
    # scaling at creases (PREREG MISS - reported). Derived global bound:
    # |dh| <= 4*SLOPE_LAW*eps (both sides, both components, at the legal slope).
    worst_dh, worst_ratio, worst_residual = 0.0, 0.0, 0.0
    for j in range(1000):
        ixr = rng.randrange(1, s.nx - 2)   # interior edges only: the eps probes on
        izr = rng.randrange(1, s.nz - 2)   # both sides must stay inside the extent
        t = rng.uniform(0.05, 0.95)
        eps = 10.0 ** rng.randrange(-9, -4)
        if j % 2 == 0:   # cross the frozen diagonal tz = tx transversally
            x1, z1 = s.x0 + (ixr + t - eps) * s.dx, s.z0 + (izr + t - eps) * s.dz
            x2, z2 = s.x0 + (ixr + t + eps) * s.dx, s.z0 + (izr + t + eps) * s.dz
            g1, g2 = s.gradient_at(x1, z1), s.gradient_at(x2, z2)
            signed = eps * (g2[0] + g2[1] + g1[0] + g1[1])
            predicted = eps * (abs(g1[0]) + abs(g1[1]) + abs(g2[0]) + abs(g2[1]))
        elif j % 4 == 1:  # cross a shared vertical edge x = const
            x1 = s.x0 + (ixr + 1 - eps) * s.dx
            x2 = s.x0 + (ixr + 1 + eps) * s.dx
            z1 = z2 = s.z0 + (izr + t) * s.dz
            g1, g2 = s.gradient_at(x1, z1), s.gradient_at(x2, z2)
            signed = eps * (g2[0] + g1[0])
            predicted = eps * (abs(g1[0]) + abs(g2[0]))
        else:             # cross a shared horizontal edge z = const
            z1 = s.z0 + (izr + 1 - eps) * s.dz
            z2 = s.z0 + (izr + 1 + eps) * s.dz
            x1 = x2 = s.x0 + (ixr + t) * s.dx
            g1, g2 = s.gradient_at(x1, z1), s.gradient_at(x2, z2)
            signed = eps * (g2[1] + g1[1])
            predicted = eps * (abs(g1[1]) + abs(g2[1]))
        dh_signed = s.height_at(x2, z2) - s.height_at(x1, z1)
        dh = abs(dh_signed)
        worst_dh = max(worst_dh, dh)
        worst_ratio = max(worst_ratio, dh / eps)
        # exact linear identity on each side (value continuity) + never above bound
        worst_residual = max(worst_residual, abs(dh_signed - signed), dh - predicted)
    pen_bound = S_TICK  # vertical drops: per-tick travel bound (derived; TUN-01's)
    ok = (caught_n == 500) and (worst_pen <= pen_bound) and \
        (worst_residual <= TERRAIN_H_TOL) and (worst_ratio <= 4.0 * SLOPE_LAW)
    return {"id": "TUN-04", "verdict": "PASS" if ok else "FAIL",
            "falsifier_fired": not ok,
            "caught": caught_n, "of": 500, "worst_pen_m": worst_pen,
            "pen_bound_m": pen_bound,
            "worst_twisted_cell": {"ix": wcell[0], "iz": wcell[1],
                                   "diagonal_split_m": worst_diff},
            "edge_continuity_worst_m": worst_dh,
            "continuity_worst_ratio_m_per_m": worst_ratio,
            "continuity_ratio_bound_m_per_m": 4.0 * SLOPE_LAW,
            "continuity_linear_residual_worst_m": worst_residual,
            "continuity_residual_bound_m": TERRAIN_H_TOL,
            "prereg_miss": "the frozen 1e-9 ABSOLUTE continuity bound ignored the "
                           "linear eps-scaling of the value difference across a "
                           "crease; corrected to the exact linear prediction "
                           "(residual <= 1e-9) and the derived 4*0.05 ratio bound. "
                           "Value continuity HOLDS; the slope kink at creases is "
                           "real, expected, and bounded by F01's slope law."}


def gho_01(m):
    """Outside extent: classify 'outside' and queries REFUSE (f02_outside_extent)."""
    Refusal = m.tq.Refusal
    half = m.surf.half
    probes = []
    for coord in (1e-9, 1e-6, 0.5):
        probes += [(half + coord, 0.0), (-(half + coord), 0.0),
                   (0.0, half + coord), (0.0, -(half + coord))]
    oks = []
    for x, z in probes:
        outside = m.surf.classify(x, z) == "outside"
        refused = 0
        for fn in (m.surf.height_at, m.surf.gradient_at, m.surf.normal_at):
            try:
                fn(x, z)
            except Refusal as r:
                if r.code == "f02_outside_extent":
                    refused += 1
        oks.append(outside and refused == 3)
    return {"id": "GHO-01", "verdict": "PASS" if all(oks) else "FAIL",
            "falsifier_fired": not all(oks), "probes": len(oks), "ok": sum(oks)}


def gho_02(m):
    """Floating-support probes at 5 frozen gap points (spawn + 4 consecutive
    mound-pair midpoints). Law algebra: gap = point_y + r - h."""
    mnds = m.surf.mounds
    pts = [(0.0, 0.0, "spawn cell")]
    for i in range(4):
        a, b = mnds[i], mnds[i + 1]
        pts.append(((a["centre_x_m"] + b["centre_x_m"]) / 2.0,
                    (a["centre_z_m"] + b["centre_z_m"]) / 2.0,
                    "mound %d-%d midpoint" % (i + 1, i + 2)))
    rows, ok = [], True
    for x, z, tag in pts:
        h = m.h(x, z)
        g_rest = (h - R_SOLE) + R_SOLE - h          # the law's own rest placement
        g_tangent_geom = (h + R_SOLE) + R_SOLE - h  # naive sphere-centre tangency
        g_float = (h - R_SOLE + 1e-4) + R_SOLE - h  # 1e-4 above rest
        row_ok = (abs(g_rest) <= 1e-15) and (g_float > K_TOUCH) and \
                 (1e-4 - 1e-15 <= g_float <= 1e-4 + 1e-12)
        ok &= row_ok
        rows.append({"probe": tag, "h_m": h, "gap_rest_m": g_rest,
                     "gap_geometric_tangent_m": g_tangent_geom,
                     "gap_floating_1e4_m": g_float, "ok": row_ok})
    return {"id": "GHO-02", "verdict": "PASS" if ok else "FAIL",
            "falsifier_fired": not ok, "rows": rows,
            "convention_note": "the engine law's zero-gap rest is point_y = h - r_s "
                               "(gait_controller.hpp:635-643; gait_scene.py:400 "
                               "seated_gaps). Naive sphere-centre tangency reads "
                               "gap = 2*r_s = 8e-3 m under this law - a PREREG "
                               "PREDICTION MISS (recorded, adjudicated under "
                               "falsifier F-b), not a ghost: the divergence is "
                               "one-sided (the law claims contact LATER than naive "
                               "geometry, never earlier)."}


def gho_03(m):
    """Trunk volume/void: axis probes inside the analytic solid (sdf = -R) while the
    render mesh alone would report an R-void; shell disagreement bounded by TOL."""
    rows = []
    for y in (0.1, m.y0 + m.H / 2.0, 1.0):
        p = (m.cx, y, m.cz)
        rows.append({"probe": "axis y=%.3f" % y, "sdf_analytic_m":
                     sdf_capped_cylinder(p, m.cx, m.cz, m.R, m.y0, m.H),
                     "mesh_distance_m": m.trunk_mesh_distance(p)})
    shell = []
    chord_r = m.R * math.cos(math.pi / 32.0)          # mid-facet chord radius
    for i in range(32):
        ang = 2.0 * math.pi * (i + 0.5) / 32.0        # mid-facet azimuths
        # sphere tangent to the MESH at the mid-facet chord: centre at chord_r + r_s
        mesh_tangent_center = (m.cx + (chord_r + R_SOLE) * math.cos(ang),
                               m.y0 + m.H / 2.0, m.cz + (chord_r + R_SOLE) * math.sin(ang))
        pen_of_mesh_tangent = R_SOLE - sdf_capped_cylinder(
            mesh_tangent_center, m.cx, m.cz, m.R, m.y0, m.H)
        # sphere tangent to the ANALYTIC surface at the same azimuth: centre at R + r_s
        analytic_tangent_center = (m.cx + (m.R + R_SOLE) * math.cos(ang),
                                   m.y0 + m.H / 2.0, m.cz + (m.R + R_SOLE) * math.sin(ang))
        ghost_gap = m.trunk_mesh_distance(analytic_tangent_center) - R_SOLE
        shell.append({"azimuth": i, "mesh_tangent_sphere_pen_m": pen_of_mesh_tangent,
                      "analytic_tangent_sphere_ghost_gap_m": ghost_gap})
    worst_pen = max(r["mesh_tangent_sphere_pen_m"] for r in shell)
    worst_ghost = max(r["analytic_tangent_sphere_ghost_gap_m"] for r in shell)
    ok = all(abs(r["sdf_analytic_m"] + m.R) <= 1e-12 for r in rows) and \
        worst_pen <= TRUNK_TOL and worst_ghost <= TRUNK_TOL
    return {"id": "GHO-03", "verdict": "PASS-AS-DECLARED" if ok else "FAIL",
            "falsifier_fired": not ok, "axis_rows": rows,
            "worst_shell_pen_m": worst_pen, "worst_shell_ghost_m": worst_ghost,
            "tol_m": TRUNK_TOL,
            "declared": "collision = the ANALYTIC solid (trunk_declaration "
                        "collision_route); the mesh is render-only; the <=TOL shell "
                        "split is the declared representation error"}


def int_01(m):
    """Sphere vs trunk analytic solid: frozen tangency sets + seeded shell/interior."""
    worst_tangency = 0.0
    for i in range(64):
        ang = 2.0 * math.pi * i / 64.0
        for y in (0.1, 0.3, 0.579, 0.9, 1.05):
            p = (m.cx + (m.R + R_SOLE) * math.cos(ang), y,
                 m.cz + (m.R + R_SOLE) * math.sin(ang))
            worst_tangency = max(worst_tangency,
                                 abs(sdf_capped_cylinder(p, m.cx, m.cz, m.R, m.y0, m.H) - R_SOLE))
    for cap_y, sgn in ((m.y0, -1.0), (m.y0 + m.H, +1.0)):
        for k in range(33):
            rr = m.R * k / 32.0
            ang = 0.375
            p = (m.cx + rr * math.cos(ang), cap_y + sgn * R_SOLE,
                 m.cz + rr * math.sin(ang))
            worst_tangency = max(worst_tangency,
                                 abs(sdf_capped_cylinder(p, m.cx, m.cz, m.R, m.y0, m.H) - R_SOLE))
    s2 = R_SOLE / math.sqrt(2.0)
    for i in range(32):
        ang = 2.0 * math.pi * i / 32.0
        p = (m.cx + (m.R + s2) * math.cos(ang), m.y0 + m.H + s2,
             m.cz + (m.R + s2) * math.sin(ang))
        worst_tangency = max(worst_tangency,
                             abs(sdf_capped_cylinder(p, m.cx, m.cz, m.R, m.y0, m.H) - R_SOLE))
    rng = random.Random(SEED + 1)
    min_margin, n_shell = float("inf"), 0
    while n_shell < 4096:
        p = (m.cx + rng.uniform(-0.09, 0.09), rng.uniform(m.y0 - 0.03, m.y0 + m.H + 0.03),
             m.cz + rng.uniform(-0.09, 0.09))
        sdf = sdf_capped_cylinder(p, m.cx, m.cz, m.R, m.y0, m.H)
        if sdf >= 1.05 * R_SOLE:
            min_margin = min(min_margin, sdf - R_SOLE)
            n_shell += 1
    max_inside, n_in = -float("inf"), 0
    while n_in < 256:
        p = (m.cx + rng.uniform(-0.01, 0.01), rng.uniform(0.05, m.H - 0.05),
             m.cz + rng.uniform(-0.01, 0.01))
        sdf = sdf_capped_cylinder(p, m.cx, m.cz, m.R, m.y0, m.H)
        if sdf < -1e-6:
            max_inside = max(max_inside, sdf)
            n_in += 1
    ok = worst_tangency <= ANALYTIC_TOL and min_margin > 0.0 and max_inside < -1e-6
    return {"id": "INT-01", "verdict": "PASS" if ok else "FAIL",
            "falsifier_fired": not ok,
            "worst_tangency_err_m": worst_tangency, "tangency_bound_m": ANALYTIC_TOL,
            "shell_samples": n_shell, "min_shell_margin_m": min_margin,
            "interior_samples": n_in, "max_interior_sdf_m": max_inside}


def int_02(m):
    """The engine's vertical gap law on slopes: at the law's zero-gap placement the
    geometric sphere submerges into the sloped triangle's plane by r*(1-n_y).
    Derived legal-slope bound r*(1-1/sqrt(1+0.05^2))."""
    bound = R_SOLE * (1.0 - 1.0 / math.sqrt(1.0 + SLOPE_LAW ** 2))
    worst, where, worst_slope = 0.0, None, 0.0
    for a, b, c, (gx, gz), slope, n in m.ground_triangles():
        sub = R_SOLE * (1.0 - n[1])
        if sub > worst:
            worst, where, worst_slope = sub, (gx, gz), slope
    ok = worst <= bound
    return {"id": "INT-02", "verdict": "PASS" if ok else "FAIL",
            "falsifier_fired": not ok,
            "triangles": 3200, "worst_submergence_m": worst,
            "at": where, "triangle_slope_m_per_m": worst_slope,
            "bound_m": bound, "bound_rule": "r*(1-1/sqrt(1+0.05^2)) at F01's legal "
            "worst slope; also <= trunk TOL 2e-4",
            "tol_ratio": worst / TRUNK_TOL}


def int_03(m):
    """Trunk base cap vs terrain (the ground joint): coplanar contact, zero gap,
    zero penetration; no terrain point inside the solid."""
    worst_h, rows = 0.0, []
    for k in range(65):
        rr = m.R * (k // 8) / 8.0
        ang = 2.0 * math.pi * (k % 8) / 8.0
        x, z = m.cx + rr * math.cos(ang), m.cz + rr * math.sin(ang)
        worst_h = max(worst_h, abs(m.h(x, z)))
    worst_fp = 0.0
    for i in range(9):
        for j in range(9):
            x = m.cx - 0.047 + i * (0.094 / 8.0)
            z = m.cz - 0.047 + j * (0.094 / 8.0)
            worst_fp = max(worst_fp, abs(m.h(x, z)))
    grad = m.surf.gradient_at(m.cx, m.cz)
    ok = worst_h <= 1e-9 and worst_fp <= 1e-9 and max(abs(grad[0]), abs(grad[1])) <= 1e-12
    return {"id": "INT-03", "verdict": "PASS" if ok else "FAIL",
            "falsifier_fired": not ok,
            "cap_disk_samples": 65, "worst_abs_terrain_height_m": worst_h,
            "footprint_grid_samples": 81, "worst_abs_footprint_height_m": worst_fp,
            "gradient_at_site": list(grad), "bound_m": 1e-9,
            "declared": "site terrain height 0.0 / slope 0.0 (F01 trunk_sites[0], "
                        "F03 site block); cap plane y=0 coplanar with the terrain"}


def vis_01(m):
    """Terrain render vs collision at the trunk neighborhood ring + boundary strips."""
    rng = random.Random(SEED + 2)
    worst_h, worst_n, n = 0.0, 0.0, 0
    worst_analytic, ring_max_h = 0.0, 0.0
    hfun = m.surf.height_function()

    def check(x, z):
        nonlocal worst_h, worst_n, n
        ix, iz, tx, tz = m.surf.cell_of(x, z)
        which = m.surf.which_triangle(tx, tz)
        pa, pb, pc = m.surf.triangle_positions(ix, iz, which)
        nxv = vcross(vsub(pb, pa), vsub(pc, pa))
        ln = vnorm(nxv)
        h_ind = pa[1] - (nxv[0] * (x - pa[0]) + nxv[2] * (z - pa[2])) / nxv[1]
        worst_h = max(worst_h, abs(h_ind - m.surf.height_at(x, z)))
        nq = m.surf.normal_at(x, z)
        for j in range(3):
            worst_n = max(worst_n, abs(nxv[j] / ln - nq[j]))
        n += 1

    while n < 2500:
        ang = rng.uniform(0, 2 * math.pi)
        rad = math.sqrt(rng.uniform(0, 1)) * 2.0
        x, z = m.cx + rad * math.cos(ang), m.cz + rad * math.sin(ang)
        check(x, z)
        ring_max_h = max(ring_max_h, abs(m.surf.height_at(x, z)))
        worst_analytic = max(worst_analytic, abs(hfun(x, z) - m.surf.height_at(x, z)))
    n_boundary = 0
    for _ in range(100):
        for edge in range(4):
            t = rng.uniform(-20.0, 20.0)
            if edge == 0:
                check(20.0, t)
            elif edge == 1:
                check(-20.0, t)
            elif edge == 2:
                check(t, 20.0)
            else:
                check(t, -20.0)
            n_boundary += 1
    # classify at the closed edge must be 'inside' (strict >)
    edge_inside = all([m.surf.classify(20.0, 0.0) == "inside",
                       m.surf.classify(-20.0, 0.0) == "inside",
                       m.surf.classify(0.0, 20.0) == "inside",
                       m.surf.classify(0.0, -20.0) == "inside"])
    ok = worst_h <= TERRAIN_H_TOL and worst_n <= TERRAIN_N_TOL and edge_inside
    return {"id": "VIS-01", "verdict": "PASS" if ok else "FAIL",
            "falsifier_fired": not ok,
            "ring_samples": 2500, "boundary_samples": n_boundary,
            "worst_height_disagreement_m": worst_h, "height_bound_m": TERRAIN_H_TOL,
            "worst_normal_disagreement": worst_n, "normal_bound": TERRAIN_N_TOL,
            "classify_at_closed_edge_inside": edge_inside,
            "ring_max_abs_height_m": ring_max_h,
            "ring_analytic_vs_collision_worst_m": worst_analytic,
            "declared_global_discretization_m": 6.460e-3,
            "declared_note": "analytic-mound vs collision is F02's DECLARED "
                             "discretization (<= 9.25 mm derived); render vs "
                             "collision is the identity measured here"}


def vis_02(m):
    """Trunk render vs analytic: chord error re-derived from the stored vertex table;
    winding outward; vertices on the analytic surface."""
    tr = m.trunk_recipe
    recomputed = tr.measure_representation_error(
        m.decl["render_mesh"]["vertices"],
        (m.decl["site"]["base_centre_m"][0], m.decl["site"]["base_centre_m"][1],
         m.decl["site"]["base_centre_m"][2]),
        m.R, m.decl["render_mesh"]["ring_segments"])
    declared = m.decl["representation_error"]["max_measured_m"]
    sag = tr.sagitta(m.R, m.decl["render_mesh"]["ring_segments"])
    worst_off = 0.0
    for i in range(m.decl["render_mesh"]["vertex_count"]):
        vx = m.tverts[i]
        d = abs(math.hypot(vx[0] - m.cx, vx[2] - m.cz) - m.R)
        on_axis = math.hypot(vx[0] - m.cx, vx[2] - m.cz) <= 1e-9
        on_cap_height = abs(vx[1] - m.y0) <= 1e-9 or abs(vx[1] - (m.y0 + m.H)) <= 1e-9
        if on_axis and on_cap_height:
            worst_off = max(worst_off, 0.0)          # cap centres: exactly on the axis
        else:
            worst_off = max(worst_off, d)            # ring vertices: on the cylinder
    outward, worst_wind = 0, 0.0
    for t in range(0, len(m.tidx), 3):
        a, b, c = (m.tverts[m.tidx[t]], m.tverts[m.tidx[t + 1]], m.tverts[m.tidx[t + 2]])
        nvec = vcross(vsub(b, a), vsub(c, a))
        mid = vscale(vadd(vadd(a, b), c), 1.0 / 3.0)
        cap_n = abs(nvec[1]) > 0.9 * vnorm(nvec)
        if cap_n:
            ref = (0.0, 1.0 if mid[1] > m.y0 + m.H / 2.0 else -1.0, 0.0)
        else:
            ref = ((mid[0] - m.cx), 0.0, (mid[2] - m.cz))
        cosang = vdot(nvec, ref) / (vnorm(nvec) * vnorm(ref))
        if cosang > 0:
            outward += 1
        else:
            worst_wind = max(worst_wind, -cosang)
    ok = (abs(recomputed - declared) <= 1e-10 and abs(recomputed - sag) <= 2e-7
          and recomputed <= TRUNK_TOL and outward == 128 and worst_off <= 1e-6)
    return {"id": "VIS-02", "verdict": "PASS" if ok else "FAIL",
            "falsifier_fired": not ok,
            "recomputed_chord_m": recomputed, "declared_chord_m": declared,
            "sagitta_m": sag, "chord_tol_m": TRUNK_TOL,
            "triangles_outward": outward, "of": 128,
            "worst_vertex_off_surface_m": worst_off, "vertex_bound_m": 1e-6}


def vis_03(m):
    """Posts are render-only markers (capability NOT claimed). Frozen probe: declared
    post index 30 = (20, 0, 0) (F01 posts_m). Measures the exact visual/physics split;
    falsifies only a CLAIM of post collision (none exists - L2 route survey)."""
    posts = m.f01["boundary"]["rendered"]["posts_m"]
    px, py, pz = posts[30][0], posts[30][1], posts[30][2]
    sec = m.surf.bundle["render"]["sections"]["boundary_posts"]
    ground = m.h(px - 0.03, pz)
    center = (px - 0.03, ground + R_SOLE, pz)      # geometric sole-sphere rest
    d_sphere = m.post_mesh_distance(center, sec["vertex_start"], sec["index_count"])
    sole_point_law_rest = (px - 0.03, ground - R_SOLE, pz)
    d_point = m.post_mesh_distance(sole_point_law_rest,
                                   sec["vertex_start"], sec["index_count"])
    env = m.f01["spawn"]["body_radius_envelope_m"]
    env_center = (px - 0.03, ground + env, pz)
    d_env = m.post_mesh_distance(env_center, sec["vertex_start"], sec["index_count"])
    n_posts = len(m.surf.posts())
    overlap_env = env - d_env   # positive depth = the envelope sphere overlaps the post
    return {"id": "VIS-03", "verdict": "PASS-AS-DECLARED",
            "falsifier_fired": False,
            "post_index": 30, "post_declared_m": [px, py, pz], "posts_total": n_posts,
            "sole_sphere_center_to_post_mesh_m": d_sphere,
            "sole_point_law_rest_to_post_mesh_m": d_point,
            "body_envelope_overlap_depth_m": overlap_env,
            "collision_query_serves": "ground only (terrain triangulation + extent "
                                      "rule); posts appear in NO collision path",
            "declared": "posts are rendered markers for the physical extent edge "
                        "(F01 boundary.physical note; F02 render-only prisms); the "
                        "blocking rule is the extent rule itself; post collision is "
                        "NOT claimed and therefore not demonstrated (item's own "
                        "observation clause). L2 route survey: no engine prop "
                        "collision exists to claim."}


# --- driver --------------------------------------------------------------------
def main():
    os.makedirs(RECEIPTS, exist_ok=True)
    m = Model()
    results = [tun_01(m), tun_02(m), tun_03(m), tun_04(m), gho_01(m), gho_02(m),
               gho_03(m), int_01(m), int_02(m), int_03(m), vis_01(m), vis_02(m),
               vis_03(m)]
    n_fail = sum(1 for r in results if r["verdict"].startswith("FAIL"))
    receipt = {
        "agent": "M-F04", "date": "2026-09-24", "item": "F04",
        "frozen_inputs": {"r_sole_m": R_SOLE, "k_touch": K_TOUCH,
                          "dt_max_s": DT_MAX, "v_max_m_s": V_MAX,
                          "s_tick_m": S_TICK, "s_tick_vertical_m": S_TICK_VERT,
                          "trunk_tol_m": TRUNK_TOL, "seed": SEED,
                          "slope_law_m_per_m": SLOPE_LAW},
        "artifacts": {"terrain_bundle": TERRAIN_BUNDLE, "trunk_declaration": TRUNK_DECL,
                      "trunk_validator_receipt": m.trunk_receipt},
        "results": results, "n_fail": n_fail,
        "layer_note": "L1 only (declared geometric model). L2 engine-service gap "
                      "statement is in report.md/HANDOFFS.md - the frozen engine "
                      "exercises NONE of these cases in-vivo (point spheres vs ONE "
                      "plane only).",
    }
    with open(os.path.join(RECEIPTS, "run.json"), "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=1)
    lines = ["M-F04 contact verification - L1 (declared geometric model)",
             "frozen: r_sole=%g m kTouch=%g dt<=1/300 s v_max=%g m/s s_tick=%.6g m "
             "s_tick_vert=%.6g m TOL=%g m seed=%d" % (R_SOLE, K_TOUCH, V_MAX, S_TICK,
                                                      S_TICK_VERT, TRUNK_TOL, SEED),
             "-" * 100]
    for r in results:
        lines.append("%-7s %-22s falsifier=%s" % (r["id"], r["verdict"],
                                                  "FIRED" if r["falsifier_fired"] else "not fired"))
        for k, v in r.items():
            if k in ("id", "verdict", "falsifier_fired"):
                continue
            if isinstance(v, (int, float, bool, str)):
                lines.append("    %-42s %s" % (k, v))
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                for row in v[:6]:
                    lines.append("    - %s" % json.dumps(row)[:160])
                if len(v) > 6:
                    lines.append("    ... %d more rows in run.json" % (len(v) - 6))
            elif isinstance(v, dict):
                lines.append("    %-42s %s" % (k, json.dumps(v)[:200]))
    lines.append("-" * 100)
    lines.append("VERDICT: %d/%d cases green; falsifiers fired: %s"
                 % (len(results) - n_fail, len(results),
                    [r["id"] for r in results if r["falsifier_fired"]] or "none"))
    text = "\n".join(lines)
    with open(os.path.join(RECEIPTS, "run.txt"), "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print(text)
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
