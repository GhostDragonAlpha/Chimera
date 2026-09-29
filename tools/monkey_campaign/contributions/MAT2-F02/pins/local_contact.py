"""MAT2-M06 local triangle contact and finite sliding law.

Implements the frozen PREREGISTRATION.md (Amendments A1-A3) exactly:

- candidate search: sweep-and-prune over swept-inflated triangle AABBs; the
  narrow phase sees ONLY candidate pairs (frozen subset property);
- local surface contact: exact triangle-triangle closest features -> contact
  points, normals, midsurface gaps with per-surface thickness inflation;
- Coulomb friction: stick below mu_s * Jn, slip at mu_k * Jn; finite sliding
  displacement per tick (bounded by the per-tick motion);
- declared thin-feature treatment: shell midsurfaces + declared thickness;
- declared high-speed treatment: per-tick conservative-advancement CCD
  (exact one-step for linear motion; crossing trajectories cannot tunnel);
- reciprocal impulses: every impulse recorded two-sided; pinned bodies emit
  an anchor reaction; per-tick ledger (Amendment A2):
  sum(m*dv) per body == gravity + contact + anchor; sum(contact) == 0;
- area-scaled per-triangle load report: uniform contact pressure over the
  contacted area, F_i = p * a_i (B2 heritage: capacity = strength x area).

CPU-only, stdlib-only, deterministic (no wall-clock, no RNG). Refusals are
named codes; nothing is silently repaired.
"""
from __future__ import annotations

import math

SCHEMA = 'chimera.local_contact.v1'

# ---- frozen declarations (PREREGISTRATION.md) ----
G = 9.81                 # m/s^2, gravity along -z
DT = 0.005               # s tick
THICKNESS_M = 0.002      # m, pinned from MAT2-M02 shell_thickness_m
SLOP_M = 1e-5            # m
MARGIN = 1e-5            # m, contact activation margin (= slop)
BETA = 0.2               # Baumgarte bias coefficient (G3 heritage)
RESTITUTION = 0.0        # declared inelastic
CCD_MAX_ITERS = 64
CCD_TOL_M = 1e-12        # declared CCD activation tolerance above MARGIN
MU_TINY = 1e-15          # tangential speed under which no friction acts


def require(ok, code):
    if not ok:
        raise ValueError(code)


# ---------- vector helpers (3-tuples) ----------

def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vlen(a):
    return math.sqrt(vdot(a, a))


def vunit(a):
    n = vlen(a)
    require(n > 0.0, 'degenerate_normal')
    return (a[0] / n, a[1] / n, a[2] / n)


def finite_vec(v):
    return all(isinstance(x, (int, float)) and math.isfinite(x) for x in v)


def nonfinite(value):
    if isinstance(value, (int, float)):
        return not math.isfinite(value)
    if isinstance(value, (list, tuple)):
        return any(nonfinite(x) for x in value)
    return False


# ---------- triangle geometry ----------

def tri_area(p0, p1, p2):
    c = vcross(vsub(p1, p0), vsub(p2, p0))
    require(all(math.isfinite(x) for x in c), 'nonfinite_state')
    a = 0.5 * vlen(c)
    require(a > 0.0, 'zero_area_interface')
    return a


def tri_normal(ta):
    """Declared degenerate-case contact normal: the triangle's own right-hand
    rule normal (used only when the closest points coincide, dist == 0)."""
    return vunit(vcross(vsub(ta[1], ta[0]), vsub(ta[2], ta[0])))


def tri_aabb(tri, inflate=0.0):
    xs = [v[0] for v in tri]
    ys = [v[1] for v in tri]
    zs = [v[2] for v in tri]
    return ((min(xs) - inflate, min(ys) - inflate, min(zs) - inflate),
            (max(xs) + inflate, max(ys) + inflate, max(zs) + inflate))


def point_tri_closest(p, a, b, c):
    """Closest point on triangle abc to p (Ericson). Returns (q, dist2)."""
    ab = vsub(b, a)
    ac = vsub(c, a)
    ap = vsub(p, a)
    d1, d2 = vdot(ab, ap), vdot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return a, vdot(vsub(p, a), vsub(p, a))
    bp = vsub(p, b)
    d3, d4 = vdot(ab, bp), vdot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return b, vdot(vsub(p, b), vsub(p, b))
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        t = d1 / (d1 - d3)
        q = vadd(a, vscale(ab, t))
        return q, vdot(vsub(p, q), vsub(p, q))
    cp = vsub(p, c)
    d5, d6 = vdot(ab, cp), vdot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return c, vdot(vsub(p, c), vsub(p, c))
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        t = d2 / (d2 - d6)
        q = vadd(a, vscale(ac, t))
        return q, vdot(vsub(p, q), vsub(p, q))
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        t = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        q = vadd(b, vscale(vsub(c, b), t))
        return q, vdot(vsub(p, q), vsub(p, q))
    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    q = vadd(a, vadd(vscale(ab, v), vscale(ac, w)))
    return q, vdot(vsub(p, q), vsub(p, q))


def seg_seg_closest(p1, q1, p2, q2):
    """Closest points between segments p1q1 and p2q2 (Ericson)."""
    d1 = vsub(q1, p1)
    d2 = vsub(q2, p2)
    r = vsub(p1, p2)
    a, e = vdot(d1, d1), vdot(d2, d2)
    f = vdot(d2, r)
    eps = 1e-30
    if a <= eps and e <= eps:
        return p1, p2
    if a <= eps:
        s = 0.0
        t = min(1.0, max(0.0, f / e))
    else:
        c = vdot(d1, r)
        if e <= eps:
            t = 0.0
            s = min(1.0, max(0.0, -c / a))
        else:
            b = vdot(d1, d2)
            denom = a * e - b * b
            s = min(1.0, max(0.0, (b * f - c * e) / denom)) if denom > eps else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t = 0.0
                s = min(1.0, max(0.0, -c / a))
            elif t > 1.0:
                t = 1.0
                s = min(1.0, max(0.0, (b - c) / a))
    return vadd(p1, vscale(d1, s)), vadd(p2, vscale(d2, t))


def tri_tri_closest(pa, pb, pc, qa, qb, qc):
    """Closest points between triangles P and Q: returns (p, q, dist)."""
    best = None
    for p in (pa, pb, pc):
        q, _ = point_tri_closest(p, qa, qb, qc)
        d = vlen(vsub(p, q))
        if best is None or d < best[0]:
            best = (d, p, q)
    for q in (qa, qb, qc):
        p, _ = point_tri_closest(q, pa, pb, pc)
        d = vlen(vsub(p, q))
        if best is None or d < best[0]:
            best = (d, p, q)
    for e1 in ((pa, pb), (pb, pc), (pc, pa)):
        for e2 in ((qa, qb), (qb, qc), (qc, qa)):
            c1, c2 = seg_seg_closest(e1[0], e1[1], e2[0], e2[1])
            d = vlen(vsub(c1, c2))
            if best is None or d < best[0]:
                best = (d, c1, c2)
    return best[1], best[2], best[0]


# ---------- bodies ----------

class Body:
    """A declared triangle soup (shell) with rigid translation kinematics."""

    def __init__(self, body_id, surface_id, matter_id, mass_kg, mu_s, mu_k,
                 thickness_m, vertices, triangles, velocity=(0.0, 0.0, 0.0),
                 pinned=False):
        require(isinstance(body_id, str) and body_id, 'unknown_surface_id')
        for v in vertices:
            require(finite_vec(v), 'nonfinite_state')
        require(thickness_m >= 0.0, 'bad_thickness')
        require(0.0 <= mu_k <= mu_s <= 1.0, 'bad_friction')
        self.id = body_id
        self.surface_id = surface_id
        self.matter_id = matter_id
        self.mass_kg = None if pinned else float(mass_kg)
        require(self.mass_kg is None or self.mass_kg > 0.0, 'bad_friction')
        self.mu_s = float(mu_s)
        self.mu_k = float(mu_k)
        self.thickness_m = float(thickness_m)
        self.vertices = [tuple(v) for v in vertices]
        self.triangles = [tuple(t) for t in triangles]
        require(bool(self.triangles), 'zero_area_interface')
        for t in self.triangles:
            self.tri_area(t)  # refuses zero_area_interface eagerly
        self.velocity = tuple(float(x) for x in velocity)
        self.pinned = bool(pinned)
        self.anchor = (0.0, 0.0, 0.0)

    def inv_mass(self):
        return 0.0 if self.pinned else 1.0 / self.mass_kg

    def tri_verts(self, t):
        return (self.vertices[t[0]], self.vertices[t[1]], self.vertices[t[2]])

    def tri_area(self, t):
        a, b, c = self.tri_verts(t)
        return tri_area(a, b, c)


# ---------- candidate search ----------

def swept_aabb(body, t, motion_bound):
    """Triangle AABB inflated by the declared swept bound: the body's per-tick
    motion plus both thickness radii plus the activation margin."""
    inflate = motion_bound + body.thickness_m + MARGIN
    a, b, c = body.tri_verts(t)
    return tri_aabb((a, b, c), inflate)


def _overlaps(lo1, hi1, lo2, hi2):
    return all(lo1[k] <= hi2[k] and lo2[k] <= hi1[k] for k in range(3))


def sweep_prune(entries):
    """entries: list of (body_index, tri_index, lo, hi). Returns sorted
    candidate index pairs (i < j); same-body pairs excluded. Sweep axis =
    largest variance of box centers (deterministic tie-break to the lowest
    axis index)."""
    require(bool(entries), 'empty_entries')
    centers = [((lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5,
                (lo[2] + hi[2]) * 0.5) for _, _, lo, hi in entries]
    means = [sum(c[k] for c in centers) / len(centers) for k in range(3)]
    var = [sum((c[k] - means[k]) ** 2 for c in centers) for k in range(3)]
    axis = max(range(3), key=lambda k: (var[k], -k))
    order = sorted(range(len(entries)), key=lambda k: (entries[k][2][axis], k))
    pairs = set()
    for pos, i in enumerate(order):
        bi, _, loi, hii = entries[i]
        for j in order[pos + 1:]:
            bj, _, loj, hij = entries[j]
            if loj[axis] > hii[axis]:
                break
            if bi == bj:
                continue
            if _overlaps(loi, hii, loj, hij):
                pairs.add((i, j) if i < j else (j, i))
    return sorted(pairs)


def exhaustive_pairs(entries):
    """The comparison reference: ALL cross-body triangle pairs."""
    return [(i, j) for i in range(len(entries))
            for j in range(i + 1, len(entries))
            if entries[i][0] != entries[j][0]]


# ---------- friction pair rule ----------

def pair_mu(body_a, body_b):
    """Declared rule: elementwise min of the two surface declarations."""
    return min(body_a.mu_s, body_b.mu_s), min(body_a.mu_k, body_b.mu_k)


# ---------- contact solve ----------

def solve_contact(body_a, body_b, gap, normal, pair_key):
    """Solve one local contact (normal, then Coulomb friction) and return the
    two-sided record. normal points from B's surface toward A's surface. The
    impulses are applied here, reciprocally, exactly once."""
    require(finite_vec(normal), 'nonfinite_state')
    n = normal
    inv_ma, inv_mb = body_a.inv_mass(), body_b.inv_mass()
    denom = inv_ma + inv_mb
    require(denom > 0.0, 'nonfinite_state')
    m_eff = 1.0 / denom
    rv = vsub(body_a.velocity, body_b.velocity)
    vn = vdot(rv, n)
    pen = -gap
    bias = BETA / DT * max(pen - SLOP_M, 0.0)
    jn = max(m_eff * (-(1.0 + RESTITUTION) * vn + bias), 0.0)
    jn_vec = vscale(n, jn)
    body_a.velocity = vadd(body_a.velocity, vscale(jn_vec, inv_ma))
    body_b.velocity = vsub(body_b.velocity, vscale(jn_vec, inv_mb))
    rv = vsub(body_a.velocity, body_b.velocity)
    vn_after = vdot(rv, n)
    vt_vec = vsub(rv, vscale(n, vn_after))
    vt_pre = vlen(vt_vec)
    mu_s, mu_k = pair_mu(body_a, body_b)
    jt_mag, mode = 0.0, 'still'
    jt_vec = (0.0, 0.0, 0.0)
    if vt_pre > MU_TINY:
        jt_req = m_eff * vt_pre
        jt_dir = vscale(vt_vec, -1.0 / vt_pre)
        if jt_req <= mu_s * jn:
            jt_mag, mode = jt_req, 'stick'
        else:
            jt_mag, mode = mu_k * jn, 'slip'
        jt_vec = vscale(jt_dir, jt_mag)
        body_a.velocity = vadd(body_a.velocity, vscale(jt_vec, inv_ma))
        body_b.velocity = vsub(body_b.velocity, vscale(jt_vec, inv_mb))
    rv = vsub(body_a.velocity, body_b.velocity)
    vt_post_vec = vsub(rv, vscale(n, vdot(rv, n)))
    vt_post = vlen(vt_post_vec)
    w_f_ke = 0.5 * m_eff * max(vt_pre * vt_pre - vt_post * vt_post, 0.0)
    impulse = vadd(jn_vec, jt_vec)
    return {
        'pair_key': pair_key, 'normal': list(n), 'gap_m': gap,
        'penetration_m': pen, 'jn_Ns': jn, 'jt_Ns': jt_mag, 'mode': mode,
        'impulse_on_a': list(impulse), 'impulse_on_b': list(vscale(impulse, -1.0)),
        'inv_ma': inv_ma, 'inv_mb': inv_mb, 'm_eff': m_eff,
        'vt_pre': vt_pre, 'vt_post': vt_post, 'w_f_ke_J': w_f_ke,
        'mu_used': (0.0 if jt_mag == 0.0 else
                    (mu_s if mode == 'stick' else mu_k)),
    }


# ---------- conservative-advancement CCD (declared high-speed treatment) ----------

def ccd_toc(body_a, body_b, ta, tb, dt, max_iters=CCD_MAX_ITERS):
    """Contact time within [0, dt] for two translating triangles, or None.
    Distance under linear translation is 1-Lipschitz in t with constant
    |relative velocity|, so the advance (gap - MARGIN)/|w| is exact and
    converges in one step for head-on approaches. Near-tangential resting
    pairs can make the Lipschitz advance crawl; if the iteration cap is hit,
    the declared fallback uniformly resamples the remaining window (S = cap
    samples; sampling can only under-detect a dip shorter than dt/S, whose
    depth bound is |w|*dt/S -- recorded in the law document)."""
    w = vsub(body_a.velocity, body_b.velocity)
    speed = vlen(w)

    def state(t):
        off_a = vscale(body_a.velocity, t)
        off_b = vscale(body_b.velocity, t)
        ta_off = tuple(vadd(v, off_a) for v in ta)
        tb_off = tuple(vadd(v, off_b) for v in tb)
        p, q, dist = tri_tri_closest(*ta_off, *tb_off)
        gap = dist - 0.5 * (body_a.thickness_m + body_b.thickness_m)
        return p, q, gap

    t = 0.0
    for _ in range(max_iters):
        p, q, gap = state(t)
        if gap <= MARGIN + CCD_TOL_M:
            return {'toc': t, 'gap': gap, 'point_a': list(p), 'point_b': list(q),
                    'normal': list(vunit(vsub(p, q))) if dist_f(p, q) > 0.0 else None}
        if speed <= 0.0:
            return None
        step = (gap - MARGIN) / speed
        if step <= 0.0:
            return {'toc': t, 'gap': gap, 'point_a': list(p), 'point_b': list(q),
                    'normal': list(vunit(vsub(p, q))) if dist_f(p, q) > 0.0 else None}
        t = t + step
        if t > dt:
            return None
    # declared fallback: uniform resample of the remaining window
    for k in range(1, max_iters + 1):
        ts = dt * k / max_iters
        p, q, gap = state(ts)
        if gap <= MARGIN + CCD_TOL_M:
            return {'toc': ts, 'gap': gap, 'point_a': list(p), 'point_b': list(q),
                    'normal': list(vunit(vsub(p, q))) if dist_f(p, q) > 0.0 else None}
    return None


def dist_f(p, q):
    return vlen(vsub(p, q))


# ---------- per-tick solve ----------

def solve_tick(bodies, exhaustive=False, ccd_enabled=True, gravity=True):
    """One deterministic tick: gravity -> candidates -> persistent contacts ->
    CCD contacts -> anchors -> position integration -> ledger.

    Returns (records, ledger). With exhaustive=True the candidate stage
    enumerates ALL cross-body pairs (the comparison reference)."""
    v_start = {b.id: b.velocity for b in bodies}
    # 1. gravity (declared external impulse)
    gravity_impulse = {}
    if gravity:
        for b in bodies:
            if not b.pinned:
                b.velocity = vsub(b.velocity, (0.0, 0.0, G * DT))
                gravity_impulse[b.id] = list(vscale((0.0, 0.0, -G * DT), b.mass_kg))
    # 2. candidates over swept-inflated AABBs
    motion = max((vlen(b.velocity) * DT for b in bodies), default=0.0)
    entries = []
    for bi, b in enumerate(bodies):
        for ti, t in enumerate(b.triangles):
            lo, hi = swept_aabb(b, t, motion)
            entries.append((bi, ti, lo, hi))
    cand = exhaustive_pairs(entries) if exhaustive else sweep_prune(entries)
    cand_keys = {(entries[i][0], entries[i][1], entries[j][0], entries[j][1])
                 for (i, j) in cand}
    # 3. persistent contacts among candidates (gap <= MARGIN + tol now)
    records = []
    persist_keys = set()
    for (i, j) in cand:
        ba, bb = bodies[entries[i][0]], bodies[entries[j][0]]
        ta, tb = ba.tri_verts(ba.triangles[entries[i][1]]), \
            bb.tri_verts(bb.triangles[entries[j][1]])
        p, q, dist = tri_tri_closest(*ta, *tb)
        gap = dist - 0.5 * (ba.thickness_m + bb.thickness_m)
        if gap <= MARGIN + CCD_TOL_M:
            normal = vunit(vsub(p, q)) if dist > 0.0 else tri_normal(ta)
            require(normal is not None, 'degenerate_normal')
            key = (entries[i][0], entries[i][1], entries[j][0], entries[j][1])
            persist_keys.add(key)
            rec = solve_contact(ba, bb, gap, normal, key)
            _tag(rec, ba, bb, entries[i][1], entries[j][1], 'persistent', 0.0, p, q)
            records.append(rec)
    # 4. CCD, event-driven: solve the earliest hit, COMMIT the advance (free
    # bodies move to the contact time), then rescan the remaining window.
    # This is what lets a resting patch settle onto the surface (gap -> MARGIN)
    # instead of hovering one substep short of it.
    advanced = {id(b): 0.0 for b in bodies}
    if ccd_enabled:
        solved = set(persist_keys)
        t_used = 0.0
        for _ in range(CCD_MAX_ITERS):
            hits = []
            for (i, j) in cand:
                key = (entries[i][0], entries[i][1], entries[j][0], entries[j][1])
                if key in solved:
                    continue
                ba, bb = bodies[entries[i][0]], bodies[entries[j][0]]
                ta, tb = ba.tri_verts(ba.triangles[entries[i][1]]), \
                    bb.tri_verts(bb.triangles[entries[j][1]])
                hit = ccd_toc(ba, bb, ta, tb, DT - t_used)
                if hit is not None and hit['normal'] is not None:
                    hits.append((hit['toc'], key, hit, i, j))
            if not hits:
                break
            hits.sort(key=lambda h: (h[0], h[1]))
            toc, key, hit, i, j = hits[0]
            ba, bb = bodies[entries[i][0]], bodies[entries[j][0]]
            for b in (ba, bb):
                if not b.pinned:
                    b.vertices = [vadd(v, vscale(b.velocity, toc))
                                  for v in b.vertices]
                    advanced[id(b)] += toc
            rec = solve_contact(ba, bb, hit['gap'], tuple(hit['normal']), key)
            _tag(rec, ba, bb, entries[i][1], entries[j][1], 'ccd',
                 t_used + hit['toc'], hit['point_a'], hit['point_b'])
            records.append(rec)
            solved.add(key)
            t_used += toc
            if DT - t_used <= 0.0:
                break
        else:
            raise ValueError('ccd_iteration_overflow')
    # 5. anchors: pinned bodies receive -sum(received contact impulses)
    contact_impulse = {b.id: (0.0, 0.0, 0.0) for b in bodies}
    for rec in records:
        contact_impulse[rec['body_a']] = vadd(contact_impulse[rec['body_a']],
                                              tuple(rec['impulse_on_a']))
        contact_impulse[rec['body_b']] = vadd(contact_impulse[rec['body_b']],
                                              tuple(rec['impulse_on_b']))
    anchors = {}
    for b in bodies:
        if b.pinned:
            b.anchor = vscale(contact_impulse[b.id], -1.0)
            anchors[b.id] = list(b.anchor)
        else:
            anchors[b.id] = [0.0, 0.0, 0.0]
    # 6. position integration (free bodies only; finite sliding displacement;
    # bodies already advanced by CCD substeps integrate only the remainder)
    for b in bodies:
        if not b.pinned:
            rem = DT - advanced[id(b)]
            if rem > 0.0:
                b.vertices = [vadd(v, vscale(b.velocity, rem))
                              for v in b.vertices]
    # 7. ledger identity (Amendment A2): m*dv == gravity + contact + anchor
    ledger = {'gravity': gravity_impulse, 'anchor': anchors,
              'contact': {bid: list(v) for bid, v in contact_impulse.items()},
              'm_dv': {}, 'residual': {},
              'candidates': len(cand), 'entries': len(entries),
              'cand_set': cand, 'cand_keys': cand_keys, 'motion_bound': motion}
    for b in bodies:
        dv = vsub(b.velocity, v_start[b.id])
        m_dv = tuple(dv) if b.pinned else vscale(dv, b.mass_kg)
        ext = vadd(tuple(ledger['gravity'].get(b.id, (0.0, 0.0, 0.0))),
                   tuple(anchors[b.id]))
        contact = tuple(contact_impulse[b.id])
        total_in = vadd(vadd(ext, contact), (0.0, 0.0, 0.0))
        resid = vsub(m_dv, total_in)
        ledger['m_dv'][b.id] = list(m_dv)
        ledger['residual'][b.id] = list(resid)
        require(vlen(resid) <= 1e-12, 'ledger_imbalance')
    recip = (0.0, 0.0, 0.0)
    for rec in records:
        recip = vadd(recip, tuple(rec['impulse_on_a']))
        recip = vadd(recip, tuple(rec['impulse_on_b']))
    require(vlen(recip) <= 1e-12, 'ledger_imbalance')
    ledger['reciprocity_residual'] = list(recip)
    return records, ledger


def _tag(rec, ba, bb, tri_a, tri_b, kind, toc, p, q):
    rec.update({
        'kind': kind, 'toc': toc, 'point_a': list(p), 'point_b': list(q),
        'tri_a': tri_a, 'tri_b': tri_b,
        'body_a': ba.id, 'body_b': bb.id,
        'surface_a': ba.surface_id, 'surface_b': bb.surface_id,
        'matter_a': ba.matter_id, 'matter_b': bb.matter_id,
        'thickness_a': ba.thickness_m, 'thickness_b': bb.thickness_m,
        'area_a': ba.tri_area(ba.triangles[tri_a]),
        'area_b': bb.tri_area(bb.triangles[tri_b]),
    })


# ---------- area-scaled per-triangle load report ----------

def area_split(bodies, records):
    """Declared report: per (body, counterparty), uniform contact pressure
    over the CONTACTED area (every triangle in the tick's contact patch):
    p = Jn_total/(dt*sum(a_i)); F_i = p*a_i."""
    groups = {}
    for rec in records:
        groups.setdefault((rec['body_a'], rec['body_b']), {}).setdefault(rec['tri_a'], 0.0)
        groups[(rec['body_a'], rec['body_b'])][rec['tri_a']] += rec['jn_Ns']
        groups.setdefault((rec['body_b'], rec['body_a']), {}).setdefault(rec['tri_b'], 0.0)
        groups[(rec['body_b'], rec['body_a'])][rec['tri_b']] += rec['jn_Ns']
    by_id = {b.id: b for b in bodies}
    out = {}
    for (body_id, _other), tris in groups.items():
        body = by_id[body_id]
        areas = {ti: body.tri_area(body.triangles[ti]) for ti in tris}
        total_a = sum(areas.values())
        require(total_a > 0.0, 'zero_area_interface')
        p = sum(tris.values()) / (DT * total_a)
        out.setdefault(body_id, {})
        for ti, a in sorted(areas.items()):
            out[body_id][str(ti)] = p * a
    return out


# ---------- document validation ----------

DECL_KEYS = (('g', G), ('dt', DT), ('thickness_m', THICKNESS_M),
             ('slop_m', SLOP_M), ('margin_m', MARGIN), ('beta', BETA),
             ('restitution', RESTITUTION))


def validate_local_contact(doc, known_surfaces):
    require(isinstance(doc, dict) and doc.get('schema') == SCHEMA, 'bad_document')
    require(doc.get('revision') == 1, 'bad_document')
    decl = doc.get('declarations')
    require(isinstance(decl, dict), 'bad_document')
    for key, val in DECL_KEYS:
        require(decl.get(key) == val, 'declaration_drift:' + key)
    surfaces = doc.get('surfaces')
    require(isinstance(surfaces, list) and surfaces, 'bad_document')
    seen = set()
    for s in surfaces:
        require(s.get('id') in known_surfaces, 'unknown_surface_id')
        require(s['id'] not in seen, 'duplicate_surface_id')
        seen.add(s['id'])
        require(s.get('thickness_m', -1.0) >= 0.0, 'bad_thickness')
        require(0.0 <= s.get('mu_k', -1.0) <= s.get('mu_s', -1.0) <= 1.0,
                'bad_friction')
        require(bool(s.get('matter_id')), 'unknown_surface_id')
    for rec in doc.get('contacts', []):
        require(rec.get('surface_a') in known_surfaces, 'unknown_surface_id')
        require(rec.get('surface_b') in known_surfaces, 'unknown_surface_id')
        require(not nonfinite(rec.get('gap_m')), 'nonfinite_state')
    return True


def summary(doc):
    return {
        'schema': doc['schema'], 'revision': doc['revision'],
        'surface_count': len(doc.get('surfaces', [])),
        'contact_record_count': len(doc.get('contacts', [])),
    }
