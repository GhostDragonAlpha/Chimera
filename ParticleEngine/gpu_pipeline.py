"""Full GPU pipeline — simulation, splats, projection, composite. All on device."""

import numpy as np
from numba import cuda
import math

try:
    import cupy as cp                       # GPU radix sort => tile binning stays on-device (no 41ms host round-trip)
    _HAS_CUPY = True
except Exception:                            # pragma: no cover - CPU fallback path
    _HAS_CUPY = False

import os as _os
_TILE_DIAG = _os.environ.get('CHIMERA_TILE_DIAG') == '1'
# how full a tile must get before it is worth reporting, as a fraction of the cap
_TILE_DIAG_AT = float(_os.environ.get('CHIMERA_TILE_DIAG_AT', '0.5'))
# ── THREE DIAGNOSTIC LENSES OVER THE SAME COST, EACH ANSWERING A DIFFERENT QUESTION ─────────────
# The frame cost is (splat, tile) pairs. Given a scene that costs too much, there are three
# distinct things you can be asking, and one flag cannot serve all three:
#
#   _EXPAND_DIAG  HOW MANY pairs, and how many per splat  -> is this scene's problem SIZE or COUNT
#   _SIZE_DIAG    WHERE in the buffer the large grains are -> is it all of them or a tail
#   _CLAMP_SIZE   what happens if the tail is removed      -> is the tail actually the cost
#
# The third is a LENS, not a physics change: it alters what you SEE, never what the membrane IS,
# which is why it is off by default and named so that leaving it on is obviously a lie.
_EXPAND_DIAG = _os.environ.get('CHIMERA_EXPANSION_DIAG') == '1'
_SIZE_DIAG = _os.environ.get('CHIMERA_SPLAT_SIZE_DIAG') == '1'
_CLAMP_SIZE = _os.environ.get('CHIMERA_CLAMP_SPLAT_SIZE') == '1'
TILE_SIZE = 32
# HOW MANY SPLATS ONE 32-PX TILE MAY HOLD. Past this the far ones are evicted, and if the survivors
# do not happen to cover the tile you get a hard-edged black RECTANGLE on the tile grid.
#
# RAISED 4096 -> 16384 (2026-07-29). A sweep of every membrane found SEVEN over the old cap --
# theGalaxy and theSolarSystem at 221%, theCloud 211%, theHumanClock 170%, theCooling 156%,
# theClock 155%, theDensityClock 101% -- and the cause is not too many grains, it is BIG ones: these
# membranes draw soft fields whose splats reach 68-195 px, so a single one spans up to 144 tiles.
# 4096 was chosen for scenes of small surface grains and was simply too low for a soft field.
#
# It is free on the live path: the CuPy binner allocates `tids` to the KEPT total, not to
# n_tiles*MAX_PER_TILE, so nothing is preallocated against this number. (The numba fallback's
# preallocation is sized off the particle count and does not read it either.)
#
# NOT EVERY OVERRUN IS FIXED HERE. thePlanets' was a real emit bug -- 900 grains packed into a
# sub-pixel world -- and was fixed at the source with matter.grains_for(). Raising a cap is the
# right answer only when the grains themselves are honest. Check with CHIMERA_TILE_DIAG=1 before
# assuming which kind you have: if the splats in the hot tile are LARGE, it is this; if they are
# small and thousands are centred inside one tile, it is the emit.
MAX_PER_TILE = 16384

# ── HOW FAR A SPLAT REACHES, DERIVED FROM THE COMPOSITOR'S OWN CUTOFF ────────────────────────────
# The binner expanded every splat to `1.5 * rad` and nobody had checked that against the number the
# compositor actually uses. `_inv_radii` sets `rad = 3.0 * sqrt(eig_max)`, so 1.5*rad is 4.5 SIGMA.
# `_composite` drops a splat when its Gaussian weight falls under 0.001:
#
#     wgt = exp(-0.5 * ge) < 0.001   =>   ge > -2*ln(0.001) = 13.8155   =>   3.7169 SIGMA
#
# So every pair between 3.7169 and 4.5 sigma was binned, sorted, and walked per pixel, and then
# thrown away by a test it could never pass. Area ratio (4.5/3.7169)^2 = 1.466, i.e. 31.8% of the
# expansions on any splat large enough to span tiles.
#
# THIS IS A DERIVATION, NOT A TUNING, and it is written as one: change the cutoff or change how
# `_inv_radii` defines rad, and this tracks. A typed 1.239 would be the same number with the
# reasoning deleted, and the next person to touch either constant would silently break it.
#
# IT IS ALSO INVISIBLE BY CONSTRUCTION. At the boundary a splat contributes `opacity * 0.001`,
# which is under 0.25 of a 0-255 channel step -- below quantisation even at full opacity. The
# claim was checked rather than argued: all 47 terms render BIT-IDENTICAL frames after the change.
WGT_CUTOFF = 0.001                                       # `_composite`: `if wgt < 0.001: continue`
_SIGMA_REACH = math.sqrt(-2.0 * math.log(WGT_CUTOFF))    # 3.7169 sigma
_RAD_IN_SIGMA = 3.0                                      # `_inv_radii`: rad = 3.0 * sqrt(eig_max)
FOOTPRINT = _SIGMA_REACH / _RAD_IN_SIGMA                 # 1.2390 (was a hand-written 1.5)

PX, PY, PZ = 0, 1, 2
VX, VY, VZ = 3, 4, 5
AX, AY, AZ = 6, 7, 8
MASS, LIFE, TYPE = 9, 10, 11
PROP0, PROP1, PROP2, PROP3 = 12, 13, 14, 15
CR, CG, CB = 16, 17, 18
ALPHA, SIZE = 19, 20
NX, NY, NZ = 21, 22, 23     # optional per-grain surface normal (0,0,0 => no back-face cull)
NCOLS = 28


# ═══════════════════════════════════════════════════════════════════
#  SIM KERNELS
# ═══════════════════════════════════════════════════════════════════
@cuda.jit(cache=True)
def _sim_gravity(dp, gx, gy, gz, n):
    i = cuda.grid(1)
    if i >= n: return
    o = i * NCOLS
    dp[o + AX] += gx; dp[o + AY] += gy; dp[o + AZ] += gz

@cuda.jit(cache=True)
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

@cuda.jit(cache=True)
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

@cuda.jit(cache=True)
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

@cuda.jit(cache=True)
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


@cuda.jit(cache=True)
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
# A tangent disc's variance, as a multiple of the grain's isotropic variance. WIDE across the
# surface so neighbours overlap and the shell has no gaps; THIN along the normal so the disc
# foreshortens at the limb exactly as the grain spacing does -- which is what keeps screen coverage
# constant from the sub-camera point out to the edge.
_DISC_WIDE = 1.45
_DISC_THIN = 0.10


@cuda.jit(device=True, cache=True)
def _profile(tcode):
    if tcode == 0: return 0.3, 1, 0, 0.0    # dust: accum opacity, isotropic
    elif tcode == 1: return 0.5, 0, 1, 2.5  # sand: alpha, anisotropic
    elif tcode == 2: return 0.3, 0, 1, 2.0  # water
    elif tcode == 3: return 1.0, 0, 0, 0.0  # social
    elif tcode == 4: return 1.5, 0, 0, 0.0  # resource
    # WAS 6.0. Removed 2026-07-29 at the operator's call.
    #
    # `matter.GLOW` is 5.0, so every soft-blob grain in the story tree was rendered SIX TIMES the
    # size the membrane asked for -- invisibly, with no way for the author to find out except by
    # measuring pixels. It put seven membranes over the rasteriser's per-tile cap, made
    # `surface_grain()` and `grains_for()` lie whenever the result was painted as GLOW, and gave
    # theStar a 6x jump in apparent grain size at t=0.8 where its type switched from GLOW to SOLID.
    #
    # A membrane states its own grain size and is believed. Every GLOW call in the tree was
    # multiplied by 6 in the same commit, so the pictures did not move -- only the honesty did.
    elif tcode == 5: return 1.0, 0, 0, 0.0  # atmosphere / soft field: the size you asked for
    elif tcode == 6: return 0.8, 0, 1, 2.0  # shellmite
    elif tcode == 7: return 0.05, 0, 1, 3.0 # weapon_glint
    else: return 0.5, 0, 0, 0.0


# ═══════════════════════════════════════════════════════════════════
#  PARTICLE → SPLAT
# ═══════════════════════════════════════════════════════════════════
@cuda.jit(cache=True)
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
        # SURFACE GRAINS ARE DISCS, NOT BALLS.
        # A shell of ISOTROPIC spheres has non-uniform screen coverage: at the limb the grains pile
        # up along the view ray (dense), and at the sub-camera point they spread to their true
        # tangential spacing (sparse). Where coverage is marginal, which grain wins is decided by
        # sub-pixel depth -- so a biome edge SWIMS as the body turns. That is the distortion.
        # A disc lying in the tangent plane fixes it by construction: face-on you see full width,
        # and at the limb it foreshortens by exactly the same cos(phi) as the spacing does, so
        # coverage is constant everywhere. This is why real 3DGS splats are flattened ellipsoids.
        # The normal is already carried per-grain (it drives the back-face cull); this uses it for
        # SHAPE as well. A zero normal (no surface) falls back to the isotropic ball.
        nx = dp[o + NX]; ny = dp[o + NY]; nz = dp[o + NZ]
        nn2 = nx*nx + ny*ny + nz*nz
        s2 = s * s
        if nn2 > 1e-6:
            inv = 1.0 / math.sqrt(nn2)
            ux, uy, uz = nx*inv, ny*inv, nz*inv
            wide = s2 * _DISC_WIDE                     # across the surface
            thin = s2 * _DISC_THIN                     # along the normal
            d = thin - wide
            sc00[i] = wide + d*ux*ux
            sc01[i] = d*ux*uy
            sc02[i] = d*ux*uz
            sc11[i] = wide + d*uy*uy
            sc12[i] = d*uy*uz
            sc22[i] = wide + d*uz*uz
        else:
            sc00[i] = s2; sc01[i] = 0.0; sc02[i] = 0.0
            sc11[i] = s2; sc12[i] = 0.0; sc22[i] = s2


# ═══════════════════════════════════════════════════════════════════
#  PROJECTION
# ═══════════════════════════════════════════════════════════════════
@cuda.jit(cache=True)
def _clear_normals(dp, n):
    """Zero the normal columns so the back-face cull is a no-op (for paths that fill splats directly, not via _p2s)."""
    i = cuda.grid(1)
    if i >= n: return
    o = i * NCOLS
    dp[o + NX] = 0.0; dp[o + NY] = 0.0; dp[o + NZ] = 0.0


@cuda.jit(cache=True)
def _project(dp, wx, wy, wz, cw00, cw01, cw02, cw11, cw12, cw22,
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
    # BACK-FACE CULL: if the grain carries a surface normal, drop it when it faces away from the camera.
    # The far hemisphere of an opaque world is occluded by the near side, so this is pixel-identical but
    # removes ~half the grains BEFORE projection/binning/gather/composite. (0,0,0 normal => never culled.)
    o = i * NCOLS
    nnx = dp[o + NX]; nny = dp[o + NY]; nnz = dp[o + NZ]
    if nnx != 0.0 or nny != 0.0 or nnz != 0.0:
        vnx = v00*nnx + v01*nny + v02*nnz          # rotate normal into view space (rigid view matrix)
        vny = v10*nnx + v11*nny + v12*nnz
        vnz = v20*nnx + v21*nny + v22*nnz
        if vnx*vx + vny*vy + vnz*vz > 0.0:         # normal points away from the camera => hidden
            valid[i] = False; return
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
@cuda.jit(cache=True)
def _cull(sd, valid, n, far):
    i = cuda.grid(1)
    if i >= n: return
    if sd[i] > far: valid[i] = False

@cuda.jit(cache=True)
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

@cuda.jit(cache=True)
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

@cuda.jit(cache=True)
def _gather(jx, jy, jic00, jic01, jic11, jcr, jcg, jcb, jopa, jrad,
            kx, ky, kic00, kic01, kic11, kcr, kcg, kcb, kopa, krad, sidx, n):
    i = cuda.grid(1)
    if i >= n: return
    j = sidx[i]
    kx[i] = jx[j]; ky[i] = jy[j]
    kic00[i] = jic00[j]; kic01[i] = jic01[j]; kic11[i] = jic11[j]
    kcr[i] = jcr[j]; kcg[i] = jcg[j]; kcb[i] = jcb[j]
    kopa[i] = jopa[j]; krad[i] = jrad[j]

@cuda.jit(cache=True)
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


@cuda.jit(cache=True)
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

@cuda.jit(cache=True)
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

@cuda.jit(cache=True)
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


@cuda.jit(cache=True)
def _composite(px, py, ic00, ic01, ic11, cr, cg, cb, opa, rad,
               tile_ids, tile_offsets, out,
               w, h, tiles_x, n_tiles, bg_r, bg_g, bg_b, n_splats):
    # Writes directly to a uint8 (h, w, 3) image -- clip+scale happen IN-KERNEL, so the host does ONE
    # download and no np.stack/np.clip/*255/astype on a 3MB float image every frame (~10ms of host work gone).
    ix = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    iy = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    if ix >= w or iy >= h: return
    r, g, b = bg_r, bg_g, bg_b; trans = 1.0
    tid = (iy // TILE_SIZE) * tiles_x + (ix // TILE_SIZE)
    if tid < n_tiles:
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
            # CORRECT front-to-back "over": the splat's OWN alpha is (opacity * gaussian). Its colour is
            # weighted by the transmittance so far, and transmittance decays by that own alpha -- NOT by
            # the already-weighted contribution. `trans *= (1 - a*wgt*trans)` decayed T far too slowly,
            # so ~35 splats accumulated instead of ~2 (total alpha 2.1 instead of 1.0). THAT was the
            # ~2.5x over-accumulation every hand-calibrated _PLANET_GAIN/_SURFACE_GAIN was compensating,
            # and the source of the dark "dancing dots" and the white blow-out at small scales.
            al = a * wgt
            c = al * trans
            r += cr[i]*c; g += cg[i]*c; b += cb[i]*c
            trans *= (1.0 - al)
            if trans < 0.01: break
    out[iy, ix, 0] = int(max(0.0, min(1.0, r)) * 255.0)
    out[iy, ix, 1] = int(max(0.0, min(1.0, g)) * 255.0)
    out[iy, ix, 2] = int(max(0.0, min(1.0, b)) * 255.0)


# ═══════════════════════════════════════════════════════════════════
#  PIPELINE
# ═══════════════════════════════════════════════════════════════════
def _tile_stats(expansions, kept, n_tiles, nv, hot=None):
    """The per-frame tile-work record. ONE shape, both binner paths, so a reader of
    `pipe.expansion_count()` cannot get a different thing depending on whether CuPy was present.

    `expansions` is the count BEFORE the per-tile cap and `kept` is the count after, and the
    distinction is the whole point rather than bookkeeping:

        the binner EXPANDS all of them        -> cost scales with `expansions`
        the sorter SORTS all of them          -> cost scales with `expansions`
        the compositor BLENDS only survivors  -> cost scales with `kept`

    Two of the three stages pay for the pairs that are about to be thrown away, so a budget written
    against `kept` would under-count the work by exactly the amount the cap is doing. `expansions`
    is the one to budget against; `kept` is here so the gap between them is visible instead of
    inferred, because a large gap means the cap is evicting splats and something is being NOT DRAWN.
    """
    return {"expansions": int(expansions), "kept": int(kept),
            "n_tiles": int(n_tiles), "nv": int(nv),
            "hot": (None if hot is None else int(hot))}


def _build_tiles_cpu(sx, sy, srad, tiles_x, tiles_y, tile_sz, max_pt):
    """Tile binning with DEPTH ORDER preserved, via ONE global (tile, depth) sort -- the 3DGS approach.

    `sx/sy/srad` are the DEPTH-SORTED splats (index i = depth rank, nearest = 0). Each splat is duplicated
    once per tile its 1.5*rad footprint touches; the pairs are sorted by key = tile_id*nv + i, which groups
    by tile and, WITHIN a tile, keeps nearest-first. Returns (tile_ids, tile_offsets). This replaces the
    old atomic tile-write (which SCRAMBLED depth order -> inside-out) + the O(n^2) per-tile insertion sort
    (which was slow): one vectorised numpy sort of ~10^5 pairs, ~tens of ms instead of ~600 ms."""
    nv = len(sx)
    n_tiles = tiles_x * tiles_y
    empty = (np.zeros(0, np.int32), np.zeros(n_tiles + 1, np.int32),
             _tile_stats(0, 0, n_tiles, 0))
    if nv == 0:
        return empty
    # CLAMP BEFORE THE CAST, OR int64 WRAPS AND A SPAN GOES NEGATIVE.
    #
    # `_project` rejects vz >= 0 and cw <= 0, but not cw ~ 0 -- a grain lying in the camera's own
    # view plane divides by a denormal and projects to ~1e33. `astype(int64)` cannot hold that, so it
    # saturates to INT64_MIN, `px - r` WRAPS ROUND to INT64_MAX, and the two clips land on opposite
    # ends: tx0 = tiles_x-1 while tx1 = 0. The span nx = tx1 - tx0 + 1 comes out NEGATIVE and
    # np.repeat/cp.repeat raise "all elements of 'repeats' should not be negative".
    #
    # Found from inside the first-person walk, where a grain of ground sits 1.67 m under the eye and
    # sweeps through the view plane every time you look down -- a framing no orbit camera can reach,
    # which is why 41 orders of magnitude of scenes never hit it.
    #
    # The clamp is exact, not a fudge: a splat further off-screen than the screen is wide contributes
    # to no tile, and one whose radius exceeds the diagonal already covers every tile. Both are
    # unchanged by pinning them at those bounds, and NaN maps to the same finite range.
    span = np.int64(tiles_x * tile_sz + tiles_y * tile_sz)
    srad = np.nan_to_num(srad, nan=0.0, posinf=float(span), neginf=0.0)
    sx = np.nan_to_num(sx, nan=-1e9, posinf=1e9, neginf=-1e9)
    sy = np.nan_to_num(sy, nan=-1e9, posinf=1e9, neginf=-1e9)
    r = np.clip((srad * FOOTPRINT), 0.0, float(span)).astype(np.int64) + 1   # the reach the compositor can use
    px = np.clip(sx, -float(span), float(span)).astype(np.int64)
    py = np.clip(sy, -float(span), float(span)).astype(np.int64)
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
    return (sorted_splat[keep], offsets,
            _tile_stats(total, int(capped.sum()), n_tiles, nv, hot=int(per_tile.max())))


def _build_tiles_gpu(kx, ky, krad, nv, tiles_x, tiles_y, tile_sz, max_pt):
    """Same (tile, depth) binning as _build_tiles_cpu, but ON THE GPU via CuPy -- no host round-trip.

    `kx/ky/krad` are numba device arrays (the DEPTH-SORTED projected splats). We wrap them zero-copy as
    CuPy arrays (shared __cuda_array_interface__), do the expand + radix sort + bincount on-device, and
    return numba-array VIEWS of the result (kept alive by the caller). This deletes the 41ms CPU binning
    AND its 3 host downloads + 2 uploads -- the whole tile stage becomes a sub-ms GPU op."""
    n_tiles = tiles_x * tiles_y
    sx = cp.asarray(kx)[:nv]; sy = cp.asarray(ky)[:nv]; srad = cp.asarray(krad)[:nv]
    # Same clamp as the CPU path -- see the long note in `_build_tiles_cpu`. A grain in the camera's
    # view plane projects to ~1e33, int64 saturates, `px - r` wraps, and the span goes negative.
    span = tiles_x * tile_sz + tiles_y * tile_sz
    srad = cp.nan_to_num(srad, nan=0.0, posinf=float(span), neginf=0.0)
    sx = cp.nan_to_num(sx, nan=-1e9, posinf=1e9, neginf=-1e9)
    sy = cp.nan_to_num(sy, nan=-1e9, posinf=1e9, neginf=-1e9)
    r = cp.clip(srad * FOOTPRINT, 0.0, float(span)).astype(cp.int64) + 1
    px = cp.clip(sx, -float(span), float(span)).astype(cp.int64)
    py = cp.clip(sy, -float(span), float(span)).astype(cp.int64)
    tx0 = cp.clip((px - r) // tile_sz, 0, tiles_x - 1); tx1 = cp.clip((px + r) // tile_sz, 0, tiles_x - 1)
    ty0 = cp.clip((py - r) // tile_sz, 0, tiles_y - 1); ty1 = cp.clip((py + r) // tile_sz, 0, tiles_y - 1)
    nx = tx1 - tx0 + 1; ny = ty1 - ty0 + 1
    counts = (nx * ny).astype(cp.int64)
    # THIS SYNC IS NOT NEW AND THE EXPANSION COUNT IS THEREFORE FREE. `total` has always been
    # computed here because the zero-check below needs it on the host; it was simply thrown away
    # afterwards. Reporting it costs no additional device->host transfer, which is why the count
    # can be on the LIVE path rather than behind a diagnostic flag.
    total = int(counts.sum())
    if nv == 0 or total == 0:
        z = cp.zeros(0, cp.int32); o = cp.zeros(n_tiles + 1, cp.int32)
        return (cuda.as_cuda_array(z), cuda.as_cuda_array(o), (z, o),
                _tile_stats(0, 0, n_tiles, nv))
    splat = cp.repeat(cp.arange(nv, dtype=cp.int64), counts)          # depth rank (nearest first)
    local = cp.arange(total, dtype=cp.int64) - cp.repeat(cp.cumsum(counts) - counts, counts)
    nxr = cp.repeat(nx, counts)
    tile_id = ((cp.repeat(ty0, counts) + local // nxr) * tiles_x
               + (cp.repeat(tx0, counts) + local % nxr))
    # ONE radix sort by the combined key (tile-major, nearest-first within tile). Thrust radix on int64 is
    # ~sub-ms for 10^5-10^6 keys; the unique key means non-stable sort is fine (no tie-break needed).
    order = cp.argsort(tile_id * nv + splat)
    sorted_tile = tile_id[order].astype(cp.int32)
    sorted_splat = splat[order].astype(cp.int32)
    per_tile = cp.bincount(sorted_tile, minlength=n_tiles)[:n_tiles]
    capped = cp.minimum(per_tile, max_pt)
    if _TILE_DIAG:
        _pt = per_tile.get(); _hot = int(_pt.max())
        if _hot > max_pt * _TILE_DIAG_AT:
            # THE HOTTEST FIVE, not just the hottest one. A single maximum cannot tell a scene
            # with one pathological tile from a scene that is uniformly close to the cap, and
            # those want opposite fixes -- the first is a splat too large, the second is a
            # density too high everywhere. It also shows WHERE they are, so "concentrated at the
            # object's centre" becomes something you can read rather than assume.
            _top = _pt.argsort()[::-1][:5]
            for _r, _t in enumerate(_top):
                _t = int(_t)
                if _pt[_t] <= 0:
                    break
                print("[tile-diag]   #%d TILE (%4d,%4d): %6d/%d (%5.1f%%)"
                      % (_r + 1, (_t % tiles_x) * tile_sz, (_t // tiles_x) * tile_sz,
                         int(_pt[_t]), max_pt, 100.0 * _pt[_t] / max_pt), flush=True)
            if int((_pt > max_pt).sum()):
                print("[tile-diag]   *** %d TILE(S) OVER CAP %d -- the far splats in them are "
                      "EVICTED, and if the survivors do not cover the tile you get a hard-edged "
                      "black rectangle on the tile grid. Raise MAX_PER_TILE or shrink the splats."
                      % (int((_pt > max_pt).sum()), max_pt), flush=True)
            _i = int(_pt.argmax())
            print("[tile-diag] busiest tile %d (px x=%d..%d y=%d..%d) holds %d of %d allowed; "
                  "%d tiles over cap; total expansions %d for %d splats"
                  % (_i, (_i % tiles_x) * tile_sz, (_i % tiles_x) * tile_sz + tile_sz - 1,
                     (_i // tiles_x) * tile_sz, (_i // tiles_x) * tile_sz + tile_sz - 1,
                     _hot, max_pt, int((_pt > max_pt).sum()), total, nv), flush=True)
            # WHAT is filling it: the radii of the splats binned there, and how many of them have
            # their CENTRE outside the tile (those are the ones that cost a slot and paint nothing).
            _m = (sorted_tile == _i)
            _ids = sorted_splat[_m]
            _rr = srad[_ids]; _cx = sx[_ids]; _cy = sy[_ids]
            _tx = (_i % tiles_x) * tile_sz; _ty = (_i // tiles_x) * tile_sz
            _inside = ((_cx >= _tx) & (_cx < _tx + tile_sz) & (_cy >= _ty) & (_cy < _ty + tile_sz))
            _kept = _ids[:max_pt]
            _kept_in = int(((sx[_kept] >= _tx) & (sx[_kept] < _tx + tile_sz)
                            & (sy[_kept] >= _ty) & (sy[_kept] < _ty + tile_sz)).sum())
            print("[tile-diag]   radii px: min %.1f med %.1f max %.1f | centres INSIDE the tile: %d of %d"
                  " | of the %d KEPT, %d are centred inside"
                  % (float(_rr.min()), float(cp.median(_rr)), float(_rr.max()),
                     int(_inside.sum()), int(_m.sum()), min(max_pt, int(_m.sum())), _kept_in), flush=True)
    within = cp.arange(total, dtype=cp.int64) - cp.repeat(cp.cumsum(per_tile) - per_tile, per_tile)
    keep = within < cp.repeat(capped, per_tile)
    offsets = cp.zeros(n_tiles + 1, dtype=cp.int32); offsets[1:] = cp.cumsum(capped).astype(cp.int32)
    tids = cp.ascontiguousarray(sorted_splat[keep])
    # KEPT AND HOT COST A SECOND SYNC, SO THEY ARE OPT-IN. `total` above is free (the zero-check
    # already downloaded it); `capped.sum()` and `per_tile.max()` are not, and this runs once per
    # frame on the live viewer's render thread. They are folded into ONE transfer when asked for,
    # never two, and the frame budget in perf_guard is written against `expansions` precisely so
    # that the number it needs is the free one.
    _kept, _hot = -1, None
    if _TILE_DIAG or _EXPAND_DIAG:
        _both = cp.stack([capped.sum(), per_tile.max()]).get()
        _kept, _hot = int(_both[0]), int(_both[1])
    # return numba views + the owning CuPy arrays (caller must hold them so the memory isn't freed)
    return (cuda.as_cuda_array(tids), cuda.as_cuda_array(offsets), (tids, offsets),
            _tile_stats(total, _kept, n_tiles, nv, hot=_hot))


class FullGPUPipeline:
    def __init__(self, bg=(0.01, 0.01, 0.05), base_scale=0.5):
        self.bg = bg; self.base_scale = base_scale
        self._a = 0; self._n = 0
        self.attractors: list = []  # [(x, y, z, strength, type_code, radius), ...]
        # THE FRAME'S WORK, RECORDED RATHER THAN RECOMPUTED. `expansion_count()` returns what the
        # binner actually did on the last frame, not a second pass over the same geometry. A
        # recomputation can disagree with the render -- different visibility, a different camera,
        # a buffer swapped underneath -- and a budget that is checked against a number the frame
        # did not produce is a budget checking a hypothesis.
        self._tile_stats = _tile_stats(0, 0, 0, 0)
        self._last_term = ""

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

    # ── WHAT THE LAST FRAME COST ────────────────────────────────────────────────────────────────
    def _count_expansions(self) -> int:
        """Total (splat, tile) pairs the binner produced for the last rendered frame.

        This is the quantity the pipeline is actually billed for. `MAX_GRAINS_PER_FRAME` budgets
        the splat count instead, and the two come apart badly: theMining draws 9,000 splats and
        costs more than aBlueWorld's 43,000, because at a wide framing each of its grains covers
        hundreds of tiles and each of those coverings is a separate unit of work.

        Returns 0 before the first render -- an honest "no frame has been measured", which reads
        differently from a small number and must not be confused with one.
        """
        return int(self._tile_stats.get("expansions", 0))

    # PUBLIC NAME. `_count_expansions` is the internal one the perf work was specified against;
    # the viewer, the demo tour and the benchmark are separate modules and should not be reaching
    # through an underscore to ask a pipeline what it just did.
    def expansion_count(self) -> int:
        return self._count_expansions()

    def expansions_per_splat(self) -> float:
        """Tiles touched per visible splat. THE SHAPE-FREE FORM OF "the grains are too big".

        Dividing by the visible count rather than the uploaded count is deliberate: a buffer whose
        grains are mostly off-screen or behind the camera would otherwise report a small average
        and hide the fact that the few splats being drawn are enormous.
        """
        st = self._tile_stats
        nv = int(st.get("nv", 0))
        return (float(st.get("expansions", 0)) / nv) if nv > 0 else 0.0

    def tile_stats(self) -> dict:
        """The whole record for the last frame. See `_tile_stats` for what `kept` means and why
        it is -1 unless a diagnostic flag asked for it."""
        return dict(self._tile_stats)

    def _report_expansions(self, tiles_x: int, tiles_y: int) -> None:
        """LOUD warning when one splat is covering a serious fraction of the screen's tiles.

        THE THRESHOLD IS THE SCREEN, NOT THE POPULATION. Half of `tiles_x * tiles_y` is an absolute
        reference that comes from outside the thing being measured -- the same discipline the splat
        densification work had to learn the hard way, where a top-12%-by-gradient rule grew a real
        capture and a known-flat clay control to the same 5,619 splats and could therefore report
        nothing about either. A quantile of the splat sizes in this scene would call the largest
        grains "too large" in every scene, including the ones that are fine.

        It fires on the AVERAGE splat, which makes it deliberately hard to trip: a scene has to be
        broadly over-sized, not merely own a few big grains. A term with a heavy tail and a fine
        median is the case `CHIMERA_SPLAT_SIZE_DIAG=1` exists to show.
        """
        st = self._tile_stats
        nv = int(st.get("nv", 0))
        if nv <= 0:
            return
        eps = float(st["expansions"]) / nv
        half_screen = 0.5 * tiles_x * tiles_y
        if eps > half_screen:
            # THE PROJECTED RADIUS IS MEASURED HERE AND NOT ALWAYS, and the reason is that this
            # branch is rare while the sync it costs is not free. It is what makes the message
            # ACTIONABLE instead of merely alarming.
            #
            # THE WARNING USED TO SAY "shrink SIZE column" AND THAT WAS WRONG ADVICE ON THE ONLY
            # TERM THAT TRIPS IT. theZero has a SIZE of 0.03 -- among the SMALLEST of all 47
            # membranes -- and still covers all 2,040 tiles, because its body_radius is 0 and the
            # framing rule `2.8 * max(R, 1e-6)` puts the camera 2.8 microns away. The grains are
            # not big; the camera is inside them. A diagnostic that names one cause when two
            # produce the identical symptom sends a reader to edit an emit() that is fine.
            try:
                _r = self._krad.copy_to_host()[:nv]
                _r = _r[np.isfinite(_r)]
                _med = float(np.median(_r)) if _r.size else float("nan")
                _mx = float(_r.max()) if _r.size else float("nan")
            except Exception:
                _med = _mx = float("nan")
            print(f"[SPLAT SIZE] {self._last_term or '<untagged>'}: {eps:.0f} tiles/splat "
                  f"(half-screen is {half_screen:.0f} of {tiles_x*tiles_y}; "
                  f"{st['expansions']:,} expansions over {nv:,} visible splats). "
                  f"PROJECTED radius median {_med:.1f} px, max {_mx:.1f} px -- "
                  f"either the SIZE column is too large (check CHIMERA_SPLAT_SIZE_DIAG=1) or the "
                  f"camera is too close for this body's extent (check body_radius vs distance).",
                  flush=True)
        elif _EXPAND_DIAG:
            print(f"[expansion-diag] {self._last_term or '<untagged>'}: "
                  f"{st['expansions']:,} expansions / {nv:,} splats = {eps:.1f} tiles/splat "
                  f"(screen is {tiles_x*tiles_y} tiles)", flush=True)

    @staticmethod
    def _size_histogram(data) -> None:
        """Log-binned histogram of the SIZE column, printed under CHIMERA_SPLAT_SIZE_DIAG=1.

        Task 2's average says WHICH term is expensive; it cannot say whether every grain is large
        or a tail of them is, and those want opposite fixes -- a density that is wrong everywhere
        versus a handful of outliers. The bins are logarithmic because splat size in this project
        spans membranes 41 orders of magnitude apart in scale; linear bins would put every term in
        the first bucket.

        DIAGNOSTIC ONLY. It downloads the size column, so it is never on the live path.
        """
        try:
            col = np.asarray(data[:, SIZE], dtype=np.float64)
        except Exception:
            return
        edges = [0.0, 0.001, 0.01, 0.1, 1.0, 10.0, float("inf")]
        names = ["<1e-3", "1e-3..1e-2", "1e-2..0.1", "0.1..1", "1..10", ">10"]
        counts = [int(((col >= edges[i]) & (col < edges[i + 1])).sum()) for i in range(len(names))]
        finite = col[np.isfinite(col)]
        mean = float(finite.mean()) if finite.size else 0.0
        std = float(finite.std()) if finite.size else 0.0
        mx = float(finite.max()) if finite.size else 0.0
        print("[splat-size] size_hist = {"
              + ", ".join(f"{n}: {c}" for n, c in zip(names, counts)) + "}", flush=True)
        print(f"[splat-size]   n={col.size} mean={mean:.6g} std={std:.6g} max={mx:.6g} "
              f"max/mean={(mx/mean if mean > 0 else 0.0):.1f}x", flush=True)
        if std == 0.0 and col.size > 1:
            # A FLAT HISTOGRAM IS NOW A FACT ABOUT THE MEMBRANE, NOT ABOUT THE RENDERER.
            #
            # It used to mean neither. `lod.build_mips` overwrote this column with the
            # surface-grain law at EVERY level including the base, so 44 of 47 terms arrived here
            # flat no matter what their emit() wrote -- aYellowStar's {0.03, 0.33} core-and-corona
            # became a single 0.044, and the diagnostic could not have told you otherwise.
            # Fixed 2026-08-04; the base level now keeps its emitted sizes and aYellowStar reads
            # two bins.
            #
            # SO THE MESSAGE CHANGED WITH THE CAUSE. A diagnostic that keeps blaming a bug after
            # the bug is gone sends every future reader to the wrong file.
            print("[splat-size]   std is EXACTLY 0 -- every grain identical. That is this "
                  "membrane's own emit()\n[splat-size]   (LOD no longer flattens the base level). "
                  "A COARSER MIP is uniform by\n[splat-size]   construction, so check whether the "
                  "base was selected before reading anything into it.", flush=True)

    def upload(self, data, term=""):
        n = len(data)
        # ── THE BUDGET GUARD, and it is deliberately NON-FATAL here ──────────────────────────────
        # `ChimeraEngine/perf_guard.py` declares the frame and per-surface budgets and raises
        # PerfBudgetError; nothing called it, so an over-budget scene turned into black tiles at
        # playback instead of an error at upload. It is wired at the one place every buffer must
        # pass through.
        #
        # IT WARNS RATHER THAN RAISES, and that is a decision worth stating. This pipeline is the
        # render path for the live viewer, the demo tour and the witnesses; a raise here would take
        # the whole session down over a membrane that is merely dense. The guard's job is to make
        # the overage IMPOSSIBLE TO MISS, not to be the thing that decides the session ends.
        #
        # AND IT IS OPT-IN BY `term`. Without a term there is no surface class to check against and
        # a frame-budget check alone would fire on legitimate composites (the live viewer uploads
        # ground + body + touchables as one buffer). A caller that wants the check names itself.
        #
        # THE FRAME BUDGET IS NO LONGER CHECKED HERE, AND THAT IS THE POINT OF THE CHANGE.
        # `check_frame_budget` used to take this `n` and compare it against MAX_GRAINS_PER_FRAME;
        # the 35-row sweep showed grain count explains R^2 = 0.48 of frame time, so the check was
        # firing on the wrong quantity. It now takes tile EXPANSIONS -- which DO NOT EXIST YET at
        # upload time, because nothing has been projected or binned.
        #
        #     THE COST CANNOT BE KNOWN BEFORE THE FRAME IS BUILT. That is a fact about the
        #     pipeline, not a shortcoming of the guard, and pretending otherwise is what the
        #     grain-count budget was doing.
        #
        # So the frame check moved to the post-render call sites (live_viewer._loop,
        # demo._render_frame, the benchmark), where the number is real. The per-surface grain
        # budget stays here: it is a claim about a MEMBRANE'S DENSITY, which is knowable from the
        # buffer alone and is a different question from what this frame will cost to draw.
        self._last_term = term or ""
        if term:
            try:
                from ChimeraEngine.perf_guard import check_surface_budget, PerfBudgetError
            except Exception:                     # perf_guard absent -> render, do not crash
                pass
            else:
                try:
                    check_surface_budget(term, n)
                except PerfBudgetError as e:
                    print(f"[GPU BUDGET] {e}")
        if _SIZE_DIAG and n:
            print(f"[splat-size] {term or '<untagged>'}:", flush=True)
            self._size_histogram(data)
        data = self._clamp_sizes(data, term) if (_CLAMP_SIZE and n) else data
        self._grow(n); self._n = n
        self._dp[:n*NCOLS] = cuda.to_device(data.ravel().astype(np.float32))[:n*NCOLS]

    @staticmethod
    def _clamp_sizes(data, term=""):
        """Cap the SIZE column at 2x its own mean. A LENS -- gated by CHIMERA_CLAMP_SPLAT_SIZE=1.

        IT COPIES, AND THE COPY IS LOAD-BEARING. The viewer hands `upload()` a view into
        `_lod_base` or a cached mip level, which are built once per load and reused for every
        subsequent frame. Clamping in place would write the lens into the membrane's stored
        buffer, so turning the flag off again would not turn the effect off -- the modification
        would persist for the rest of the session and quietly become what the membrane IS. A lens
        that cannot be removed is not a lens.

        The threshold is 2x THIS BUFFER'S mean, which makes it a within-scene outlier rule and
        therefore unable to say anything about how this scene compares to another -- the same
        limitation the densification work hit. It is the right shape for the question being asked
        here ("is this term's cost carried by its own tail?") and the wrong shape for any question
        about absolute size.
        """
        try:
            col = np.asarray(data[:, SIZE], dtype=np.float32)
            finite = col[np.isfinite(col)]
            if finite.size == 0:
                return data
            cap = 2.0 * float(finite.mean())
            n_over = int((col > cap).sum())
            if n_over == 0:
                return data
            out = np.array(data, dtype=np.float32, copy=True)
            out[:, SIZE] = np.minimum(np.nan_to_num(col, nan=cap, posinf=cap), cap)
            print(f"[clamp] {term or '<untagged>'}: {n_over}/{col.size} splats over 2*mean "
                  f"({cap:.6g}) clamped; was max {float(finite.max()):.6g}", flush=True)
            return out
        except Exception:
            return data                      # a lens must never be the reason a frame fails

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
            self._tile_stats = _tile_stats(0, 0, 0, 0)   # empty buffer: no work, and say so
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
        _project[g, (256,)](self._dp, self._spx, self._spy, self._spz,
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
            # NOTHING SURVIVED THE CULL -> no tiles are built -> the recorded work must be ZEROED,
            # not left holding the previous frame's. A stale count on an empty frame reads as
            # "this scene is expensive" for a scene that drew nothing at all, and it is exactly
            # the framing (camera pointed away, everything behind the near plane) where somebody
            # is already looking for a reason the picture is blank.
            self._tile_stats = _tile_stats(0, 0, 0, 0)
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
        if _HAS_CUPY:
            tids_dev, toff_dev, _own, _st = _build_tiles_gpu(self._kx, self._ky, self._krad, nv,
                                                        tx, ty, TILE_SIZE, MAX_PER_TILE)  # _own kept alive below
        else:
            tids_h, toff_h, _st = _build_tiles_cpu(self._kx.copy_to_host()[:nv], self._ky.copy_to_host()[:nv],
                                              self._krad.copy_to_host()[:nv], tx, ty, TILE_SIZE, MAX_PER_TILE)
            self._tids[:len(tids_h)] = cuda.to_device(tids_h)
            self._to[:nt + 1] = cuda.to_device(toff_h)
            tids_dev, toff_dev, _own = self._tids, self._to, None
        self._tile_stats = _st
        self._report_expansions(tx, ty)

        # GPU composite
        out = cuda.device_array((params.height, params.width, 3), dtype=np.uint8)
        bk2 = (16, 16)
        gk2 = ((params.width + 15) // 16, (params.height + 15) // 16)
        _composite[gk2, bk2](self._kx, self._ky,
            self._kic00, self._kic01, self._kic11,
            self._kcr, self._kcg, self._kcb, self._kopa, self._krad,
            tids_dev, toff_dev, out,
            params.width, params.height, tx, nt,
            self.bg[0], self.bg[1], self.bg[2], nv)
        cuda.synchronize()
        return out.copy_to_host()

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
        _clear_normals[g, (256,)](self._dp, n)   # this path fills splats directly -> no valid normals -> no cull

        # Project
        V = camera.view_matrix().astype(np.float32)
        P = camera.projection_matrix(params.width, params.height).astype(np.float32)
        fy = params.height / (2.0 * np.tan(camera.fov / 2.0))
        _project[g, (256,)](self._dp, self._spx, self._spy, self._spz,
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
            # NOTHING SURVIVED THE CULL -> no tiles are built -> the recorded work must be ZEROED,
            # not left holding the previous frame's. A stale count on an empty frame reads as
            # "this scene is expensive" for a scene that drew nothing at all, and it is exactly
            # the framing (camera pointed away, everything behind the near plane) where somebody
            # is already looking for a reason the picture is blank.
            self._tile_stats = _tile_stats(0, 0, 0, 0)
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
        if _HAS_CUPY:
            tids_dev, toff_dev, _own, _st = _build_tiles_gpu(self._kx, self._ky, self._krad, nv,
                                                        tx, ty, TILE_SIZE, MAX_PER_TILE)  # _own kept alive below
        else:
            tids_h, toff_h, _st = _build_tiles_cpu(self._kx.copy_to_host()[:nv], self._ky.copy_to_host()[:nv],
                                              self._krad.copy_to_host()[:nv], tx, ty, TILE_SIZE, MAX_PER_TILE)
            self._tids[:len(tids_h)] = cuda.to_device(tids_h)
            self._to[:nt + 1] = cuda.to_device(toff_h)
            tids_dev, toff_dev, _own = self._tids, self._to, None
        self._tile_stats = _st
        self._report_expansions(tx, ty)

        out = cuda.device_array((params.height, params.width, 3), dtype=np.uint8)
        bk2 = (16, 16)
        gk2 = ((params.width + 15) // 16, (params.height + 15) // 16)
        _composite[gk2, bk2](self._kx, self._ky,
            self._kic00, self._kic01, self._kic11,
            self._kcr, self._kcg, self._kcb, self._kopa, self._krad,
            tids_dev, toff_dev, out,
            params.width, params.height, tx, nt,
            self.bg[0], self.bg[1], self.bg[2], nv)
        cuda.synchronize()
        return out.copy_to_host()
        self.step_particles(dt, cvars)
        return self.render_from_gpu(camera, params)

    def download_particles(self):
        n = self._n
        return self._dp[:n*NCOLS].copy_to_host().reshape(n, NCOLS)
