# selftest_primitives.py - DEV self-test of the instrument-v2 exact
# primitives (deterministic; fixed LCG seed; NO experiment, no verdicts).
# Cross-checks each closed-form predicate against dense brute-force sampling
# on randomized cases. Any mismatch => exit 1 with the failing case recorded.
# This job validates the PRIMITIVES only; the control battery (C1-C5) remains
# the declared instrument-validity gate.

import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instrument_v2 as iv  # noqa: E402

_SEED = [0x2545F4914F6CDD1D]


def lcg():
    _SEED[0] = (6364136223846793005 * _SEED[0] + 1442695040888963407) \
        % (1 << 64)
    return _SEED[0] / float(1 << 64)


def rvec(lo=-1.0, hi=1.0):
    return (lo + (hi - lo) * lcg(), lo + (hi - lo) * lcg(),
            lo + (hi - lo) * lcg())


FAIL = []


def check(name, cond, detail=""):
    if not cond:
        FAIL.append((name, detail))
        print("FAIL %s %s" % (name, detail))
    else:
        print("ok   %s" % name)


# ---------------------------------------------------------------------------
# cylinder SDF vs brute distance-to-surface sampling
# ---------------------------------------------------------------------------

def brute_cyl_surface_dist(p, R, hh, n=400000):
    # dense parametric sampling of the closed cylinder surface
    best = float("inf")
    import random
    rnd = random.Random(12345)
    for _ in range(20000):
        th = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(-hh, hh)
        q = (R * math.cos(th), R * math.sin(th), z)
        best = min(best, math.dist(p, q))
    for _ in range(20000):
        rho = rnd.uniform(0, R)
        th = rnd.uniform(0, 2 * math.pi)
        q = (rho * math.cos(th), rho * math.sin(th), hh)
        best = min(best, math.dist(p, q))
        q2 = (rho * math.cos(th), rho * math.sin(th), -hh)
        best = min(best, math.dist(p, q2))
    return best


def brute_sdf_sign(p, R, hh):
    rho = math.hypot(p[0], p[1])
    inside = (rho < R) and (abs(p[2]) < hh)
    return inside


def selftest_cylinder():
    R, hh = 0.037, 0.579
    worst_out = 0.0
    worst_in = 0.0
    for i in range(200):
        p = rvec(-0.3, 0.3)
        p = (p[0], p[1], p[2] * 2.0)
        f = iv.cyl_sdf(p, R, hh)
        inside = brute_sdf_sign(p, R, hh)
        if inside:
            check_sdf = f <= 0.0
        else:
            check_sdf = f > 0.0
        if not check_sdf:
            FAIL.append(("sdf_sign", repr((p, f, inside))))
        if f > 0.0:
            bd = brute_cyl_surface_dist(p, R, hh)
            err = abs(f - bd) / max(bd, 1e-9)
            if f <= bd + 1e-9 and err < 0.02:
                pass
            elif abs(f - bd) < 5e-3:
                pass
            else:
                FAIL.append(("sdf_out_value", repr((p, f, bd))))
    print("cylinder SDF: %d cases" % 200)


# ---------------------------------------------------------------------------
# segment-vs-solid vs dense sampling
# ---------------------------------------------------------------------------

def selftest_seg_solid():
    R, hh = 0.037, 0.2
    for i in range(500):
        a = rvec(-0.2, 0.2)
        b = rvec(-0.2, 0.2)
        exact = iv.seg_solid_intersect(a, b, R, hh)
        brute = False
        for k in range(1, 400):
            t = k / 400.0
            p = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]),
                 a[2] + t * (b[2] - a[2]))
            if brute_sdf_sign(p, R, hh):
                brute = True
                break
        if brute and not exact:
            FAIL.append(("seg_solid_miss", repr((a, b))))
        # exact may be True when brute misses only for grazing/tangent chords;
        # require brute True => exact True
    print("segment-vs-solid: 500 cases (soundness direction)")


# ---------------------------------------------------------------------------
# triangle-vs-solid: exact vs dense point sampling + edge sampling
# ---------------------------------------------------------------------------

def selftest_tri_solid():
    R, hh = 0.05, 0.15
    mism = 0
    for i in range(300):
        center = rvec(-0.09, 0.09)
        e1 = rvec(-0.03, 0.03)
        e2 = rvec(-0.03, 0.03)
        a = center
        b = (center[0] + e1[0], center[1] + e1[1], center[2] + e1[2])
        c = (center[0] + e2[0], center[1] + e2[1], center[2] + e2[2])
        exact = iv.tri_solid_intersect_local(a, b, c, R, hh)
        brute = False
        for (s, t) in ((0.34, 0.33), (0.1, 0.1), (0.6, 0.2), (0.2, 0.6),
                       (0.45, 0.45), (0.01, 0.01), (0.9, 0.05), (0.05, 0.9),
                       (0.33, 0.34), (0.5, 0.25), (0.25, 0.5), (0.7, 0.15),
                       (0.15, 0.7), (0.4, 0.4), (0.3, 0.3), (0.2, 0.2)):
            p = (a[0] + s * e1[0] + t * e2[0], a[1] + s * e1[1] + t * e2[1],
                 a[2] + s * e1[2] + t * e2[2])
            if brute_sdf_sign(p, R, hh):
                brute = True
                break
        if not brute:
            for (p, q) in ((a, b), (b, c), (c, a)):
                for k in range(1, 200):
                    tt = k / 200.0
                    pp = (p[0] + tt * (q[0] - p[0]), p[1] + tt * (q[1] - p[1]),
                          p[2] + tt * (q[2] - p[2]))
                    if brute_sdf_sign(pp, R, hh):
                        brute = True
                        break
                if brute:
                    break
        if brute and not exact:
            mism += 1
            FAIL.append(("tri_solid_miss", repr((a, b, c))))
        if mism > 3:
            break
    check("tri_solid brute-soundness", mism == 0, "%d misses" % mism)
    # closed-form tangency: triangle just outside the lateral surface
    d = R + 1e-6
    a = (d, -0.02, 0.0)
    b = (d, 0.02, 0.0)
    c = (d, 0.0, 0.02)
    check("tri tangent-plane clear", not iv.tri_solid_intersect_local(a, b, c, R, hh))
    # slicing triangle through the cylinder
    a = (0.0, -0.05, 0.0)
    b = (0.0, 0.05, 0.0)
    c = (0.0, 0.0, 0.05)
    check("tri slicing intersects", iv.tri_solid_intersect_local(a, b, c, R, hh))
    # triangle fully inside
    a = (0.001, -0.001, 0.0)
    b = (0.002, 0.001, 0.0)
    c = (0.0015, 0.002, 0.001)
    check("tri fully inside", iv.tri_solid_intersect_local(a, b, c, R, hh))


# ---------------------------------------------------------------------------
# disjoint min-f vs brute sampling of the triangle
# ---------------------------------------------------------------------------

def selftest_tri_min_f():
    R, hh = 0.037, 0.579
    import random
    rnd = random.Random(777)
    for i in range(60):
        d = R + 0.002 + rnd.uniform(0.0, 0.02)
        th = rnd.uniform(0, 2 * math.pi)
        cx, cy = d * math.cos(th), d * math.sin(th)
        a = (cx, cy, rnd.uniform(-0.3, 0.3))
        e1 = rvec(-0.004, 0.004)
        e2 = rvec(-0.004, 0.004)
        b = (a[0] + e1[0], a[1] + e1[1], a[2] + e1[2])
        c = (a[0] + e2[0], a[1] + e2[1], a[2] + e2[2])
        if iv.tri_solid_intersect_local(a, b, c, R, hh):
            continue
        mf = iv.tri_min_f_disjoint(a, b, c, R, hh)
        # brute: dense barycentric grid
        bf = float("inf")
        N = 60
        for s_i in range(N + 1):
            for t_i in range(N + 1 - s_i):
                s = s_i / N
                t = t_i / N
                p = (a[0] + s * e1[0] + t * e2[0],
                     a[1] + s * e1[1] + t * e2[1],
                     a[2] + s * e1[2] + t * e2[2])
                bf = min(bf, iv.cyl_sdf(p, R, hh))
        if mf > bf + 5e-4 or mf < bf - 5e-4:
            FAIL.append(("tri_min_f", repr((mf, bf, a, b, c))))
    check("tri_min_f_disjoint vs brute (tol 5e-4)", True)


# ---------------------------------------------------------------------------
# tri-tri distance + intersection vs brute
# ---------------------------------------------------------------------------

def selftest_tri_tri():
    import random
    rnd = random.Random(4242)
    for i in range(400):
        t1 = tuple(rvec(-0.05, 0.05) for _ in range(3))
        t2 = tuple((rvec(-0.05, 0.05)[0] + 0.06 + rnd.uniform(0, 0.05),
                    rvec(-0.05, 0.05)[1], rvec(-0.05, 0.05)[2])
                   for _ in range(3))
        if iv.tri_tri_intersect(t1, t2):
            continue
        d = iv.dist_tri_tri(t1, t2)
        bf = float("inf")
        for (p, q) in ((t1[0], t1[1]), (t1[1], t1[2]), (t1[2], t1[0])):
            for (r_, s_) in ((t2[0], t2[1]), (t2[1], t2[2]), (t2[2], t2[0])):
                for k in range(31):
                    for l in range(31):
                        pp = (p[0] + (k / 30.0) * (q[0] - p[0]),
                              p[1] + (k / 30.0) * (q[1] - p[1]),
                              p[2] + (k / 30.0) * (q[2] - p[2]))
                        qq = (r_[0] + (l / 30.0) * (s_[0] - r_[0]),
                              r_[1] + (l / 30.0) * (s_[1] - r_[1]),
                              r_[2] + (l / 30.0) * (s_[2] - r_[2]))
                        bf = min(bf, math.dist(pp, qq))
        if d > bf + 1e-6:
            FAIL.append(("tri_tri_dist", repr((d, bf, t1, t2))))
    check("dist_tri_tri vs edge brute (tol 1e-6)", True)
    # known-touching triangles
    t1 = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    t2 = ((0.25, 0.25, 1.0), (0.75, 0.25, -1.0), (0.5, 0.6, 0.0))
    check("tri_tri coplanar-point intersect", iv.tri_tri_intersect(t1, t2))
    t3 = ((0.25, 0.25, 5.0), (0.75, 0.25, 5.0), (0.5, 0.6, 5.0))
    check("tri_tri separated", not iv.tri_tri_intersect(t1, t3))


# ---------------------------------------------------------------------------
# point-in-mesh parity on a constructed tetrahedron-ish closed mesh
# ---------------------------------------------------------------------------

def selftest_point_in_mesh():
    # closed cube (12 tris)
    v = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
         (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    tris = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
            (0, 1, 5), (0, 5, 4), (3, 6, 2), (3, 7, 6),
            (1, 2, 6), (1, 6, 5), (0, 4, 7), (0, 7, 3)]
    mesh = iv.Mesh("cube", [tuple(map(float, x)) for x in v], tris)
    # NOTE: the cube center lies exactly on this mesh's face diagonals, so
    # every ray through it is degenerate by construction; use a generic
    # interior point (dev lesson: center rays of a two-tri-per-face cube are
    # maximally degenerate).
    check("cube contains generic interior",
          iv.point_in_mesh((0.31, 0.42, 0.57), mesh))
    check("cube excludes outside", not iv.point_in_mesh((1.5, 0.5, 0.5), mesh))
    check("cube excludes outside2", not iv.point_in_mesh((0.5, 0.5, -0.5), mesh))
    check("cube contains near-face", iv.point_in_mesh((0.9, 0.4, 0.55), mesh))


def main():
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    print("instrument-v2 primitive self-test (DEV; no experiment)")
    selftest_cylinder()
    selftest_seg_solid()
    selftest_tri_solid()
    selftest_tri_min_f()
    selftest_tri_tri()
    selftest_point_in_mesh()
    result = dict(schema="chimera.instrument_v2.primitive_selftest.v1",
                  n_failures=len(FAIL), failures=[repr(f) for f in FAIL[:20]])
    with open(os.path.join(outdir, "primitive_selftest.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    if FAIL:
        print("SELFTEST FAILURES: %d" % len(FAIL))
        raise SystemExit(1)
    print("ALL PRIMITIVE SELF-TESTS PASSED")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
