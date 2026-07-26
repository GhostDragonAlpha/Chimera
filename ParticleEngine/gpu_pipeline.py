"""Full GPU pipeline — simulation, splats, projection, composite. All on device."""

import numpy as np
from numba import cuda
import math

TILE_SIZE = 32
MAX_PER_TILE = 4096
PX, PY, PZ = 0, 1, 2
VX, VY, VZ = 3, 4, 5
AX, AY, AZ = 6, 7, 8
MASS, LIFE, TYPE = 9, 10, 11
PROP0, PROP1, PROP2, PROP3 = 12, 13, 14, 15
CR, CG, CB = 16, 17, 18
ALPHA, SIZE = 19, 20
NCOLS = 28


# ═══════════════════════════════════════════════════════════════════
#  SIM KERNELS
# ═══════════════════════════════════════════════════════════════════
@cuda.jit
def _sim_gravity(dp, gx, gy, gz, n):
    i = cuda.grid(1)
    if i >= n: return
    o = i * NCOLS
    dp[o + AX] += gx; dp[o + AY] += gy; dp[o + AZ] += gz

@cuda.jit
def _sim_wind(dp, wx, wy, wz, strength, n):
    i = cuda.grid(1)
    if i >= n: return
    o = i * NCOLS
    s = dp[o + SIZE]
    drag = 1.0 / (s + 0.01)
    if drag > 10.0: drag = 10.0
    if drag < 0.1: drag = 0.1
    dp[o + AX] += wx * strength * drag
    dp[o + AY] += wy * strength * drag
    dp[o + AZ] += wz * strength * drag

@cuda.jit
def _sim_boundary(dp, bx0, by0, bz0, bx1, by1, bz1, rest, n):
    i = cuda.grid(1)
    if i >= n: return
    o = i * NCOLS
    for axis, lo, hi in [(PX, bx0, bx1), (PY, by0, by1), (PZ, bz0, bz1)]:
        val = dp[o + axis]
        if val < lo:
            dp[o + axis] = lo
            v = dp[o + VX + axis - PX]
            if v < 0: v = -v
            dp[o + VX + axis - PX] = v * rest
        elif val > hi:
            dp[o + axis] = hi
            v = dp[o + VX + axis - PX]
            if v > 0: v = -v
            dp[o + VX + axis - PX] = v * rest

@cuda.jit
def _sim_accumulate(dp, thresh, rate, dt, n):
    i = cuda.grid(1)
    if i >= n: return
    o = i * NCOLS
    t = int(dp[o + TYPE])
    if t != 0 and t != 1: return
    vx = dp[o + VX]; vy = dp[o + VY]; vz = dp[o + VZ]
    if math.sqrt(vx*vx + vy*vy + vz*vz) < thresh:
        dp[o + PROP0] += rate * dt
        a = dp[o + ALPHA] - 0.1 * dt
        if a < 0.0: a = 0.0
        dp[o + ALPHA] = a

@cuda.jit
def _sim_integrate(dp, dt, n):
    i = cuda.grid(1)
    if i >= n: return
    o = i * NCOLS
    dp[o + VX] += dp[o + AX] * dt
    dp[o + VY] += dp[o + AY] * dt
    dp[o + VZ] += dp[o + AZ] * dt
    dp[o + PX] += dp[o + VX] * dt
    dp[o + PY] += dp[o + VY] * dt
    dp[o + PZ] += dp[o + VZ] * dt
    dp[o + AX] = 0.0; dp[o + AY] = 0.0; dp[o + AZ] = 0.0
    life = dp[o + LIFE]
    if life >= 0: dp[o + LIFE] = life - dt


@cuda.jit
def _sim_attract(dp, ax, ay, az, strength, target_type, radius, n):
    """Attract particles of target_type toward (ax, ay, az) with inverse-square force."""
    i = cuda.grid(1)
    if i >= n: return
    o = i * NCOLS
    t = int(dp[o + TYPE])
    if t != target_type: return
    dx = ax - dp[o + PX]
    dy = ay - dp[o + PY]
    dz = az - dp[o + PZ]
    dist2 = dx*dx + dy*dy + dz*dz
    r2 = radius * radius
    if dist2 > r2 or dist2 < 1e-6: return
    dist = math.sqrt(dist2)
    # Inverse-square attraction, capped
    force = strength / (dist2 + 10.0)
    if force > 1000: force = 1000
    dp[o + AX] += dx / dist * force
    dp[o + AY] += dy / dist * force
    dp[o + AZ] += dz / dist * force


# ═══════════════════════════════════════════════════════════════════
#  TYPE PROFILE
# ═══════════════════════════════════════════════════════════════════
@cuda.jit(device=True)
def _profile(tcode):
    if tcode == 0: return 0.3, 1, 0, 0.0    # dust: accum opacity, isotropic
    elif tcode == 1: return 0.5, 0, 1, 2.5  # sand: alpha, anisotropic
    elif tcode == 2: return 0.3, 0, 1, 2.0  # water
    elif tcode == 3: return 1.0, 0, 0, 0.0  # social
    elif tcode == 4: return 1.5, 0, 0, 0.0  # resource
    elif tcode == 5: return 6.0, 0, 0, 0.0  # atmosphere
    elif tcode == 6: return 0.8, 0, 1, 2.0  # shellmite
    elif tcode == 7: return 0.05, 0, 1, 3.0 # weapon_glint
    else: return 0.5, 0, 0, 0.0


# ═══════════════════════════════════════════════════════════════════
#  PARTICLE → SPLAT
# ═══════════════════════════════════════════════════════════════════
@cuda.jit
def _p2s(dp, base_scale, spx, spy, spz, sc00, sc01, sc02, sc11, sc12, sc22, scr, scg, scb, sopa, n):
    i = cuda.grid(1)
    if i >= n: return
    o = i * NCOLS
    spx[i] = dp[o + PX]; spy[i] = dp[o + PY]; spz[i] = dp[o + PZ]
    scr[i] = dp[o + CR]; scg[i] = dp[o + CG]; scb[i] = dp[o + CB]

    t = int(dp[o + TYPE])
    sm, osrc, aniso, astr = _profile(t)

    if osrc == 1:
        o2 = dp[o + PROP0] * 10.0
        if o2 > 1.0: o2 = 1.0
        if o2 < 0.01: o2 = 0.01
        sopa[i] = o2
    elif osrc == 2:
        o2 = dp[o + PROP2]
        if o2 > 1.0: o2 = 1.0
        if o2 < 0.0: o2 = 0.0
        sopa[i] = o2
    else:
        o2 = dp[o + ALPHA]
        if o2 > 1.0: o2 = 1.0
        if o2 < 0.0: o2 = 0.0
        sopa[i] = o2

    s = dp[o + SIZE] * sm * base_scale
    vx = dp[o + VX]; vy = dp[o + VY]; vz = dp[o + VZ]
    sp2 = vx*vx + vy*vy + vz*vz

    if aniso and sp2 > 1e-6:
        sp = math.sqrt(sp2)
        dx, dy, dz = vx/sp, vy/sp, vz/sp
        st = astr
        sp2p = (s / math.sqrt(st)) ** 2
        sp2a = (s * math.sqrt(st)) ** 2
        sc00[i] = sp2p + (sp2a - sp2p) * dx*dx
        sc01[i] = (sp2a - sp2p) * dx*dy
        sc02[i] = (sp2a - sp2p) * dx*dz
        sc11[i] = sp2p + (sp2a - sp2p) * dy*dy
        sc12[i] = (sp2a - sp2p) * dy*dz
        sc22[i] = sp2p + (sp2a - sp2p) * dz*dz
    else:
        s2 = s * s
        sc00[i] = s2; sc01[i] = 0.0; sc02[i] = 0.0
        sc11[i] = s2; sc12[i] = 0.0; sc22[i] = s2


# ═══════════════════════════════════════════════════════════════════
#  PROJECTION
# ═══════════════════════════════════════════════════════════════════
@cuda.jit
def _project(wx, wy, wz, cw00, cw01, cw02, cw11, cw12, cw22,
             v00, v01, v02, v03, v10, v11, v12, v13, v20, v21, v22, v23,
             p00, p11, p22, p23, p32, fx, fy, width, height, n,
             sx, sy, sd, pc00, pc01, pc11, valid):
    i = cuda.grid(1)
    if i >= n: return
    px, py, pz = wx[i], wy[i], wz[i]
    vx = v00*px+v01*py+v02*pz+v03
    vy = v10*px+v11*py+v12*pz+v13
    vz = v20*px+v21*py+v22*pz+v23
    if vz >= 0: valid[i] = False; return
    cw = -vz
    if cw <= 0: valid[i] = False; return
    sx[i] = ((p00*vx)/cw * 0.5 + 0.5) * width
    sy[i] = (1.0 - ((p11*vy)/cw * 0.5 + 0.5)) * height
    sd[i] = -vz; valid[i] = True
    z = -vz; z2 = z*z
    j00, j02 = fx/z, -fx*vx/z2
    j11, j12 = fy/z, -fy*vy/z2
    c00, c01, c02 = cw00[i], cw01[i], cw02[i]
    c11, c12, c22 = cw11[i], cw12[i], cw22[i]
    c10, c20, c21 = c01, c02, c12
    r00, r01, r02 = v00, v01, v02
    r10, r11, r12 = v10, v11, v12
    r20, r21, r22 = v20, v21, v22
    sc00 = r00*c00+r01*c10+r02*c20; sc01 = r00*c01+r01*c11+r02*c21; sc02 = r00*c02+r01*c12+r02*c22
    sc10 = r10*c00+r11*c10+r12*c20; sc11 = r10*c01+r11*c11+r12*c21; sc12 = r10*c02+r11*c12+r12*c22
    sc20 = r20*c00+r21*c10+r22*c20; sc21 = r20*c01+r21*c11+r22*c21; sc22 = r20*c02+r21*c12+r22*c22
    cc00 = sc00*r00+sc01*r01+sc02*r02; cc01 = sc00*r10+sc01*r11+sc02*r12; cc02 = sc00*r20+sc01*r21+sc02*r22
    cc11 = sc10*r10+sc11*r11+sc12*r12; cc12 = sc10*r20+sc11*r21+sc12*r22; cc22 = sc20*r20+sc21*r21+sc22*r22
    s00 = j00*cc00*j00+j00*cc02*j02+j02*cc02*j00+j02*cc22*j02
    s01 = j00*cc01*j11+j00*cc02*j12+j02*cc12*j11+j02*cc22*j12
    s11 = j11*cc11*j11+j11*cc12*j12+j12*cc12*j11+j12*cc22*j12
    s00 += 1.5; s11 += 1.5
    if s00 < 0.5: s00 = 0.5
    if s11 < 0.5: s11 = 0.5
    pc00[i] = s00; pc01[i] = s01; pc11[i] = s11


# ═══════════════════════════════════════════════════════════════════
#  CULL + INVERSE + COMPACT + GATHER + TILES + COMPOSITE
# ═══════════════════════════════════════════════════════════════════
@cuda.jit
def _cull(sd, valid, n, far):
    i = cuda.grid(1)
    if i >= n: return
    if sd[i] > far: valid[i] = False

@cuda.jit
def _inv_radii(pc00, pc01, pc11, ic00, ic01, ic11, rad, n):
    i = cuda.grid(1)
    if i >= n: return
    c00 = pc00[i]; c01 = pc01[i]; c11 = pc11[i]
    if c00 > 1e6: c00 = 1e6
    if c11 > 1e6: c11 = 1e6
    if c01 > 1e6: c01 = 1e6
    if c01 < -1e6: c01 = -1e6
    det = c00*c11 - c01*c01
    if det < 1e-12:
        c00 += 5.0; c11 += 5.0; c01 = 0.0; det = c00*c11
    idet = 1.0 / det
    v = c11*idet
    if v > 1e4: v = 1e4
    if v < -1e4: v = -1e4
    ic00[i] = v
    v = -c01*idet
    if v > 1e4: v = 1e4
    if v < -1e4: v = -1e4
    ic01[i] = v
    v = c00*idet
    if v > 1e4: v = 1e4
    if v < -1e4: v = -1e4
    ic11[i] = v
    tr = c00 + c11; disc = tr*tr - 4*det
    if disc < 0: disc = 0
    eig = 0.5*(tr + math.sqrt(disc))
    if eig < 0.01: eig = 0.01
    r = 3.0 * math.sqrt(eig)
    if r < 1: r = 1
    if r > 5000: r = 5000
    rad[i] = r

@cuda.jit
def _compact(sx, sy, sd, sv, ic00, ic01, ic11, scr, scg, scb, sopa, srad,
             jx, jy, jd, jic00, jic01, jic11, jcr, jcg, jcb, jopa, jrad, pfx, n):
    i = cuda.grid(1)
    if i >= n: return
    if sv[i]:
        j = pfx[i]
        jx[j] = sx[i]; jy[j] = sy[i]; jd[j] = sd[i]
        jic00[j] = ic00[i]; jic01[j] = ic01[i]; jic11[j] = ic11[i]
        jcr[j] = scr[i]; jcg[j] = scg[i]; jcb[j] = scb[i]
        jopa[j] = sopa[i]; jrad[j] = srad[i]

@cuda.jit
def _gather(jx, jy, jic00, jic01, jic11, jcr, jcg, jcb, jopa, jrad,
            kx, ky, kic00, kic01, kic11, kcr, kcg, kcb, kopa, krad, sidx, n):
    i = cuda.grid(1)
    if i >= n: return
    j = sidx[i]
    kx[i] = jx[j]; ky[i] = jy[j]
    kic00[i] = jic00[j]; kic01[i] = jic01[j]; kic11[i] = jic11[j]
    kcr[i] = jcr[j]; kcg[i] = jcg[j]; kcb[i] = jcb[j]
    kopa[i] = jopa[j]; krad[i] = jrad[j]

@cuda.jit
def _tiles_count(pos_x, pos_y, radii, tile_fill, tiles_x, tiles_y, tile_sz, n):
    """First pass: atomically count splats per tile."""
    i = cuda.grid(1)
    if i >= n: return
    px = int(pos_x[i]); py = int(pos_y[i]); r = int(radii[i] * 1.5) + 1   # cover the splat's FULL footprint: the
    if r < 1: r = 1                                                        # compositor reaches 1.5*rad -> else a tile-edge GRID
    tx0 = max(0, (px - r) // tile_sz); ty0 = max(0, (py - r) // tile_sz)
    tx1 = min(tiles_x - 1, (px + r) // tile_sz); ty1 = min(tiles_y - 1, (py + r) // tile_sz)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            cuda.atomic.add(tile_fill, ty * tiles_x + tx, 1)


@cuda.jit
def _tiles_write(pos_x, pos_y, radii, tile_ids, tile_offsets, tile_fill, tiles_x, tiles_y, tile_sz, max_pt, n):
    """Second pass: write splat indices to tiles using computed offsets."""
    i = cuda.grid(1)
    if i >= n: return
    px = int(pos_x[i]); py = int(pos_y[i]); r = int(radii[i] * 1.5) + 1   # cover the splat's FULL footprint: the
    if r < 1: r = 1                                                        # compositor reaches 1.5*rad -> else a tile-edge GRID
    tx0 = max(0, (px - r) // tile_sz); ty0 = max(0, (py - r) // tile_sz)
    tx1 = min(tiles_x - 1, (px + r) // tile_sz); ty1 = min(tiles_y - 1, (py + r) // tile_sz)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            tid = ty * tiles_x + tx
            slot = cuda.atomic.add(tile_fill, tid, 1)
            if slot < max_pt:
                tile_ids[tile_offsets[tid] + slot] = i

@cuda.jit
def _tile_offsets(tile_fill, tile_offsets, n_tiles, max_pt):
    i = cuda.grid(1)
    if i > 0: return
    acc = 0
    for t in range(n_tiles):
        tile_offsets[t] = acc
        c = tile_fill[t]
        if c > max_pt: c = max_pt
        acc += c
    tile_offsets[n_tiles] = acc

@cuda.jit
def _sort_tiles(tile_ids, tile_offsets, n_tiles):
    """Restore DEPTH ORDER inside each tile. `_tiles_write` fills slots via atomic.add, whose retirement
    order is nondeterministic -- so the CPU depth-sort was being scrambled and closed surfaces rendered
    INSIDE-OUT. The stored ids are the gathered indices, which ARE depth rank (argsort(hd), nearest = 0),
    so sorting each tile's segment ASCENDING puts it nearest-first for the front-to-back compositor.
    Insertion sort: tile lists are short, and a correct order lets the compositor's opaque early-out fire."""
    tid = cuda.grid(1)
    if tid >= n_tiles: return
    start = tile_offsets[tid]; end = tile_offsets[tid + 1]
    for a in range(start + 1, end):
        key = tile_ids[a]; b = a - 1
        while b >= start and tile_ids[b] > key:
            tile_ids[b + 1] = tile_ids[b]; b -= 1
        tile_ids[b + 1] = key


@cuda.jit
def _composite(px, py, ic00, ic01, ic11, cr, cg, cb, opa, rad,
               tile_ids, tile_offsets, canvas_r, canvas_g, canvas_b,
               w, h, tiles_x, n_tiles, bg_r, bg_g, bg_b, n_splats):
    ix = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    iy = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    if ix >= w or iy >= h: return
    r, g, b = bg_r, bg_g, bg_b; trans = 1.0
    tid = (iy // TILE_SIZE) * tiles_x + (ix // TILE_SIZE)
    if tid >= n_tiles:
        canvas_r[iy, ix] = r; canvas_g[iy, ix] = g; canvas_b[iy, ix] = b; return
    start = tile_offsets[tid]; end = tile_offsets[tid + 1]
    for si in range(start, end):
        i = tile_ids[si]
        if i < 0 or i >= n_splats: continue
        a = opa[i]
        if a < 0.0001: continue
        dx = float(ix) - px[i]; dy = float(iy) - py[i]
        if dx*dx + dy*dy > rad[i]*rad[i] * 2.25: continue
        ge = dx*dx*ic00[i] + 2.0*dx*dy*ic01[i] + dy*dy*ic11[i]
        if ge > 20.0: continue
        wgt = math.exp(-0.5 * ge)
        if wgt < 0.001: continue
        c = a * wgt * trans
        r += cr[i]*c; g += cg[i]*c; b += cb[i]*c
        trans *= (1.0 - c)
        if trans < 0.01: break
    canvas_r[iy, ix] = max(0.0, min(1.0, r))
    canvas_g[iy, ix] = max(0.0, min(1.0, g))
    canvas_b[iy, ix] = max(0.0, min(1.0, b))


# ═══════════════════════════════════════════════════════════════════
#  PIPELINE
# ═══════════════════════════════════════════════════════════════════
def _build_tiles_cpu(sx, sy, srad, tiles_x, tiles_y, tile_sz, max_pt):
    """Tile binning with DEPTH ORDER preserved, via ONE global (tile, depth) sort -- the 3DGS approach.

    `sx/sy/srad` are the DEPTH-SORTED splats (index i = depth rank, nearest = 0). Each splat is duplicated
    once per tile its 1.5*rad footprint touches; the pairs are sorted by key = tile_id*nv + i, which groups
    by tile and, WITHIN a tile, keeps nearest-first. Returns (tile_ids, tile_offsets). This replaces the
    old atomic tile-write (which SCRAMBLED depth order -> inside-out) + the O(n^2) per-tile insertion sort
    (which was slow): one vectorised numpy sort of ~10^5 pairs, ~tens of ms instead of ~600 ms."""
    nv = len(sx)
    n_tiles = tiles_x * tiles_y
    empty = (np.zeros(0, np.int32), np.zeros(n_tiles + 1, np.int32))
    if nv == 0:
        return empty
    r = np.maximum((srad * 1.5).astype(np.int64) + 1, 1)             # match the compositor's 1.5*rad reach
    px = sx.astype(np.int64); py = sy.astype(np.int64)
    tx0 = np.clip((px - r) // tile_sz, 0, tiles_x - 1); tx1 = np.clip((px + r) // tile_sz, 0, tiles_x - 1)
    ty0 = np.clip((py - r) // tile_sz, 0, tiles_y - 1); ty1 = np.clip((py + r) // tile_sz, 0, tiles_y - 1)
    nx = tx1 - tx0 + 1; ny = ty1 - ty0 + 1
    counts = nx * ny
    total = int(counts.sum())
    if total == 0:
        return empty
    splat = np.repeat(np.arange(nv, dtype=np.int32), counts)          # already depth-ordered (nearest first)
    local = np.arange(total, dtype=np.int64) - np.repeat(np.cumsum(counts) - counts, counts)
    nxr = np.repeat(nx, counts)
    tile_id = ((np.repeat(ty0, counts) + local // nxr) * tiles_x
               + (np.repeat(tx0, counts) + local % nxr)).astype(np.int32)
    # COUNTING SORT by tile_id: stable => radix on a small-range int32 (values < n_tiles), O(total).
    # `splat` is already ascending = depth order, so a STABLE regroup keeps each tile nearest-first.
    # (Was argsort on int64 `tile_id*nv+splat` -> 95ms; the combined key forced a wide radix. This is ~4x cheaper.)
    order = np.argsort(tile_id, kind="stable")
    sorted_tile = tile_id[order]; sorted_splat = splat[order]
    per_tile = np.bincount(sorted_tile, minlength=n_tiles)
    capped = np.minimum(per_tile, max_pt)
    within = np.arange(total, dtype=np.int64) - np.repeat(np.cumsum(per_tile) - per_tile, per_tile)
    keep = within < np.repeat(capped, per_tile)                       # cap per tile -> keep the NEAREST
    offsets = np.zeros(n_tiles + 1, dtype=np.int32); offsets[1:] = np.cumsum(capped)
    return sorted_splat[keep], offsets


class FullGPUPipeline:
    def __init__(self, bg=(0.01, 0.01, 0.05), base_scale=0.5):
        self.bg = bg; self.base_scale = base_scale
        self._a = 0; self._n = 0
        self.attractors: list = []  # [(x, y, z, strength, type_code, radius), ...]

    def _grow(self, n):
        if n <= self._a: return
        self._a = max(n, self._a * 2 if self._a else n)
        A = lambda: cuda.device_array(self._a, dtype=np.float32)
        Ai = lambda: cuda.device_array(self._a, dtype=np.int32)
        Ab = lambda: cuda.device_array(self._a, dtype=np.bool_)
        self._dp = cuda.device_array(self._a * NCOLS, dtype=np.float32)
        self._spx = A(); self._spy = A(); self._spz = A()
        self._sc00 = A(); self._sc01 = A(); self._sc02 = A()
        self._sc11 = A(); self._sc12 = A(); self._sc22 = A()
        self._scr = A(); self._scg = A(); self._scb = A(); self._sopa = A()
        self._sx = A(); self._sy = A(); self._sd = A(); self._sv = Ab()
        self._pc00 = A(); self._pc01 = A(); self._pc11 = A()
        self._ic00 = A(); self._ic01 = A(); self._ic11 = A(); self._rad = A()
        self._jx = A(); self._jy = A(); self._jd = A()
        self._jic00 = A(); self._jic01 = A(); self._jic11 = A()
        self._jcr = A(); self._jcg = A(); self._jcb = A()
        self._jopa = A(); self._jrad = A()
        self._kx = A(); self._ky = A()
        self._kic00 = A(); self._kic01 = A(); self._kic11 = A()
        self._kcr = A(); self._kcg = A(); self._kcb = A()
        self._kopa = A(); self._krad = A()
        self._pfx = Ai()
        # Tile arrays: need n_tiles*MAX_PER_TILE entries. Allocate large enough.
        # Worst case: 1920x1080 = 8100 tiles @ 1024 = 8.3M. Cap at a reasonable size.
        max_tile_entries = max(self._a * 16, 2000000)  # generous: 16× particle count for tile coverage
        self._tf = cuda.device_array(max(20000, self._a), dtype=np.int32)  # n_tiles worst case
        self._to = cuda.device_array(max(20000, self._a), dtype=np.int32)
        self._tids = cuda.device_array(max_tile_entries, dtype=np.int32)

    def upload(self, data):
        n = len(data); self._grow(n); self._n = n
        self._dp[:n*NCOLS] = cuda.to_device(data.ravel().astype(np.float32))[:n*NCOLS]

    def step_particles(self, dt, cvars):
        n = self._n
        if n == 0: return
        g = (n + 255) // 256
        gx, gy, gz = cvars.get('gravity', (0, 0, -981))
        wx, wy, wz = cvars.get('wind_vector', (0, 0, 0))
        ws = cvars.get('wind_strength', 1.0)
        bmin = cvars.get('boundary_min', (-5000, -5000, -1000))
        bmax = cvars.get('boundary_max', (5000, 5000, 5000))
        rest = cvars.get('boundary_restitution', 0.4)
        _sim_gravity[g, (256,)](self._dp, gx, gy, gz, n)
        _sim_wind[g, (256,)](self._dp, wx, wy, wz, ws, n)
        _sim_boundary[g, (256,)](self._dp, bmin[0], bmin[1], bmin[2],
                                 bmax[0], bmax[1], bmax[2], rest, n)
        _sim_accumulate[g, (256,)](self._dp,
            cvars.get('accumulation_threshold', 5.0),
            cvars.get('accumulation_rate', 0.05), dt, n)
        # Attractors: social+resource particles flow toward attractor points
        for (ax, ay, az, strength, tcode, radius) in self.attractors:
            _sim_attract[g, (256,)](self._dp, ax, ay, az, strength, tcode, radius, n)
        _sim_integrate[g, (256,)](self._dp, dt, n)

    def render_from_gpu(self, camera, params):
        n = self._n
        if n == 0:
            return (np.full((params.height, params.width, 3),
                    [b*255 for b in self.bg], dtype=np.uint8))
        self._grow(n)
        g = (n + 255) // 256

        # Particle → splat
        _p2s[g, (256,)](self._dp, self.base_scale,
            self._spx, self._spy, self._spz,
            self._sc00, self._sc01, self._sc02, self._sc11, self._sc12, self._sc22,
            self._scr, self._scg, self._scb, self._sopa, n)

        # Project
        V = camera.view_matrix().astype(np.float32)
        P = camera.projection_matrix(params.width, params.height).astype(np.float32)
        fy = params.height / (2.0 * np.tan(camera.fov / 2.0))
        _project[g, (256,)](self._spx, self._spy, self._spz,
            self._sc00, self._sc01, self._sc02, self._sc11, self._sc12, self._sc22,
            V[0, 0], V[0, 1], V[0, 2], V[0, 3], V[1, 0], V[1, 1], V[1, 2], V[1, 3],
            V[2, 0], V[2, 1], V[2, 2], V[2, 3],
            P[0, 0], P[1, 1], P[2, 2], P[2, 3], P[3, 2], fy, fy,
            params.width, params.height, n,
            self._sx, self._sy, self._sd, self._pc00, self._pc01, self._pc11, self._sv)

        # Cull + inv + radii
        _cull[g, (256,)](self._sd, self._sv, n, camera.far)
        _inv_radii[g, (256,)](self._pc00, self._pc01, self._pc11,
            self._ic00, self._ic01, self._ic11, self._rad, n)

        # Compact (prefix sum on CPU, compact on GPU)
        hv = self._sv.copy_to_host()[:n]
        nv = int(hv.sum())
        if nv == 0:
            return (np.full((params.height, params.width, 3),
                    [b*255 for b in self.bg], dtype=np.uint8))
        self._pfx[:n] = cuda.to_device(np.cumsum(hv.astype(np.int32)) - 1)
        _compact[(n + 255) // 256, (256,)](
            self._sx, self._sy, self._sd, self._sv,
            self._ic00, self._ic01, self._ic11,
            self._scr, self._scg, self._scb, self._sopa, self._rad,
            self._jx, self._jy, self._jd,
            self._jic00, self._jic01, self._jic11,
            self._jcr, self._jcg, self._jcb, self._jopa, self._jrad,
            self._pfx, n)

        # Sort on CPU, gather on GPU (saves 10 downloads + 10 uploads)
        hd = self._jd.copy_to_host()[:nv]
        sidx = np.argsort(hd)   # NEAREST first: front-to-back over-compositing. `-hd` (farthest first) rendered every closed surface INSIDE-OUT.
        self._pfx[:nv] = cuda.to_device(sidx.astype(np.int32))
        _gather[(nv + 255) // 256, (256,)](
            self._jx, self._jy, self._jic00, self._jic01, self._jic11,
            self._jcr, self._jcg, self._jcb, self._jopa, self._jrad,
            self._kx, self._ky, self._kic00, self._kic01, self._kic11,
            self._kcr, self._kcg, self._kcb, self._kopa, self._krad,
            self._pfx, nv)

        # Tile binning: ONE global (tile, depth) sort on CPU -- depth order preserved (no atomic scramble ->
        # no inside-out) and no O(n^2) per-tile sort. kx/ky/krad are already depth-sorted (index = depth rank).
        tx = (params.width + TILE_SIZE - 1) // TILE_SIZE
        ty = (params.height + TILE_SIZE - 1) // TILE_SIZE
        nt = tx * ty
        tids_h, toff_h = _build_tiles_cpu(self._kx.copy_to_host()[:nv], self._ky.copy_to_host()[:nv],
                                          self._krad.copy_to_host()[:nv], tx, ty, TILE_SIZE, MAX_PER_TILE)
        self._tids[:len(tids_h)] = cuda.to_device(tids_h)
        self._to[:nt + 1] = cuda.to_device(toff_h)

        # GPU composite
        cr = cuda.device_array((params.height, params.width), dtype=np.float32)
        cg = cuda.device_array((params.height, params.width), dtype=np.float32)
        cb = cuda.device_array((params.height, params.width), dtype=np.float32)
        bk2 = (16, 16)
        gk2 = ((params.width + 15) // 16, (params.height + 15) // 16)
        _composite[gk2, bk2](self._kx, self._ky,
            self._kic00, self._kic01, self._kic11,
            self._kcr, self._kcg, self._kcb, self._kopa, self._krad,
            self._tids, self._to, cr, cg, cb,
            params.width, params.height, tx, nt,
            self.bg[0], self.bg[1], self.bg[2], nv)
        cuda.synchronize()
        r = cr.copy_to_host(); g = cg.copy_to_host(); b = cb.copy_to_host()
        canvas = np.stack([r, g, b], axis=2)
        canvas = np.clip(canvas, 0, 1)
        return (canvas * 255).astype(np.uint8)

    def render_splats(self, positions, covariances_3x3, colors, opacities, camera, params):
        """Render pre-computed splats — used by Nanite cluster selection."""
        n = len(positions)
        if n == 0:
            return (np.full((params.height, params.width, 3),
                    [b*255 for b in self.bg], dtype=np.uint8))
        self._grow(n)
        g = (n + 255) // 256

        # Fill splat arrays directly
        self._spx[:n] = cuda.to_device(positions[:, 0].astype(np.float32))
        self._spy[:n] = cuda.to_device(positions[:, 1].astype(np.float32))
        self._spz[:n] = cuda.to_device(positions[:, 2].astype(np.float32))
        self._sc00[:n] = cuda.to_device(covariances_3x3[:, 0, 0].astype(np.float32))
        self._sc01[:n] = cuda.to_device(covariances_3x3[:, 0, 1].astype(np.float32))
        self._sc02[:n] = cuda.to_device(covariances_3x3[:, 0, 2].astype(np.float32))
        self._sc11[:n] = cuda.to_device(covariances_3x3[:, 1, 1].astype(np.float32))
        self._sc12[:n] = cuda.to_device(covariances_3x3[:, 1, 2].astype(np.float32))
        self._sc22[:n] = cuda.to_device(covariances_3x3[:, 2, 2].astype(np.float32))
        self._scr[:n] = cuda.to_device(colors[:, 0].astype(np.float32))
        self._scg[:n] = cuda.to_device(colors[:, 1].astype(np.float32))
        self._scb[:n] = cuda.to_device(colors[:, 2].astype(np.float32))
        self._sopa[:n] = cuda.to_device(opacities.astype(np.float32))
        self._n = n

        # Project
        V = camera.view_matrix().astype(np.float32)
        P = camera.projection_matrix(params.width, params.height).astype(np.float32)
        fy = params.height / (2.0 * np.tan(camera.fov / 2.0))
        _project[g, (256,)](self._spx, self._spy, self._spz,
            self._sc00, self._sc01, self._sc02, self._sc11, self._sc12, self._sc22,
            V[0,0],V[0,1],V[0,2],V[0,3],V[1,0],V[1,1],V[1,2],V[1,3],V[2,0],V[2,1],V[2,2],V[2,3],
            P[0,0],P[1,1],P[2,2],P[2,3],P[3,2], fy, fy,
            params.width, params.height, n,
            self._sx, self._sy, self._sd, self._pc00, self._pc01, self._pc11, self._sv)

        return self._finish_render_path(n, params)

    def _finish_render_path(self, n, params):
        """Cull → inv → compact → gather → tiles → composite. Shared by render paths."""
        g = (n + 255) // 256
        _cull[g, (256,)](self._sd, self._sv, n, 100000.0)
        _inv_radii[g, (256,)](self._pc00, self._pc01, self._pc11,
            self._ic00, self._ic01, self._ic11, self._rad, n)

        hv = self._sv.copy_to_host()[:n]
        nv = int(hv.sum())
        if nv == 0:
            return (np.full((params.height, params.width, 3),
                    [b*255 for b in self.bg], dtype=np.uint8))
        self._pfx[:n] = cuda.to_device(np.cumsum(hv.astype(np.int32)) - 1)
        _compact[(n + 255) // 256, (256,)](
            self._sx, self._sy, self._sd, self._sv,
            self._ic00, self._ic01, self._ic11,
            self._scr, self._scg, self._scb, self._sopa, self._rad,
            self._jx, self._jy, self._jd,
            self._jic00, self._jic01, self._jic11,
            self._jcr, self._jcg, self._jcb, self._jopa, self._jrad, self._pfx, n)

        hd = self._jd.copy_to_host()[:nv]
        sidx = np.argsort(hd)   # NEAREST first: front-to-back over-compositing. `-hd` (farthest first) rendered every closed surface INSIDE-OUT.
        self._pfx[:nv] = cuda.to_device(sidx.astype(np.int32))
        _gather[(nv + 255) // 256, (256,)](
            self._jx, self._jy, self._jic00, self._jic01, self._jic11,
            self._jcr, self._jcg, self._jcb, self._jopa, self._jrad,
            self._kx, self._ky, self._kic00, self._kic01, self._kic11,
            self._kcr, self._kcg, self._kcb, self._kopa, self._krad, self._pfx, nv)

        tx = (params.width + TILE_SIZE - 1) // TILE_SIZE
        ty = (params.height + TILE_SIZE - 1) // TILE_SIZE
        nt = tx * ty
        tids_h, toff_h = _build_tiles_cpu(self._kx.copy_to_host()[:nv], self._ky.copy_to_host()[:nv],
                                          self._krad.copy_to_host()[:nv], tx, ty, TILE_SIZE, MAX_PER_TILE)
        self._tids[:len(tids_h)] = cuda.to_device(tids_h)
        self._to[:nt + 1] = cuda.to_device(toff_h)

        cr = cuda.device_array((params.height, params.width), dtype=np.float32)
        cg = cuda.device_array((params.height, params.width), dtype=np.float32)
        cb = cuda.device_array((params.height, params.width), dtype=np.float32)
        bk2 = (16, 16)
        gk2 = ((params.width + 15) // 16, (params.height + 15) // 16)
        _composite[gk2, bk2](self._kx, self._ky,
            self._kic00, self._kic01, self._kic11,
            self._kcr, self._kcg, self._kcb, self._kopa, self._krad,
            self._tids, self._to, cr, cg, cb,
            params.width, params.height, tx, nt,
            self.bg[0], self.bg[1], self.bg[2], nv)
        cuda.synchronize()
        r = cr.copy_to_host(); g = cg.copy_to_host(); b = cb.copy_to_host()
        canvas = np.stack([r, g, b], axis=2)
        canvas = np.clip(canvas, 0, 1)
        return (canvas * 255).astype(np.uint8)
        self.step_particles(dt, cvars)
        return self.render_from_gpu(camera, params)

    def download_particles(self):
        n = self._n
        return self._dp[:n*NCOLS].copy_to_host().reshape(n, NCOLS)
