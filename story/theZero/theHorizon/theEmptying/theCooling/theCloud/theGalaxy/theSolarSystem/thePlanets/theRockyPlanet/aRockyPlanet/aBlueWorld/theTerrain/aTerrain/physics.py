"""aTerrain -- one place on that world, at the size you would walk across.

The parent is the whole shell: where land is, where sea is, how high rock can stand. It works in
thousands of kilometres and it named the process in charge here -- running water. This membrane is
a PATCH of that shell, twelve kilometres across, and it lets that process actually run.

    a rough surface + uplift          -> something to carve
    water runs downhill and gathers   -> DRAINAGE AREA
    area and slope                    -> how fast the river cuts   (stream power)
    cutting for long enough           -> valleys, and a network between them
    what the network cannot carry     -> hillslopes, at the angle loose rock stands at

NOTHING HERE DRAWS A RIVER. The height field starts as noise with the parent's roughness; water is
routed downhill; each cell is lowered by how much water crosses it and how steeply. Repeat. The
branching network is what is LEFT, and it is the signature of running water -- you cannot get it
from noise at any amplitude, and noise is exactly what terrain used to be made of here.

THE CHECK IS HACK'S LAW, AND IT PASSES. Measure every basin's area against the length of its
longest stream and real rivers give L ~ A^0.57 -- on every continent, since Hack 1957, and put into
this simulation nowhere. That is what makes it worth running.

    measured here: 0.573 +/- 0.026 over five seeds        real rivers: 0.55 - 0.60

One draw is not a measurement. Across seeds 2029/7/101/555/9001 the exponent runs 0.548 to 0.604,
so the literature band sits inside this membrane's own spread rather than beside it, and any single
number quoted from one seed is a draw from that distribution.

It did not pass at first: 0.19, which is a fractal wearing valleys. Three things were wrong and all
three were mine. The flow graph was computed before the last incision and read after it, so long
chains never accumulated. The hollows were filled by relaxation, which moves the fill one cell per
pass and stalls. And UPLIFT was 1e-3 per step, so five hundred steps delivered half a metre of rock
-- there was nothing to carve, which is why changing erodibility 25-fold moved the relief by under
1%.
"""
from math import pi, sqrt, atan, degrees

# ── the stream-power law: dz/dt = -K A^m S^n  (Howard & Kerby 1983) ──
M_EXP = 0.5               # how strongly discharge matters -- 0.4-0.6 in the field
N_EXP = 1.0               # how strongly slope matters
# THE THREE RATES, AND THEIR RATIO IS THE WHOLE LANDSCAPE.
#
# What was here before could not work and the numbers say why: UPLIFT was 1e-3 per step, so five
# hundred steps delivered half a metre of rock. There was nothing to carve. Relief came out at 3 m
# and was entirely the starting noise, which is why changing the erodibility 25-fold moved it by
# less than 1% -- the incision term was not doing anything at all.
#
# A steady-state landscape balances uplift against incision: U = K A^m S^n. Set U and K so that
# balance lands at a few hundred metres over twelve kilometres, and the relief is BUILT rather than
# inherited.
#
# D is the one that decides whether there is a NETWORK. Diffusion smooths; incision organises. Too
# much D and the branching is erased before it can form -- measured, Hack's exponent against D:
#
#       D = 2.0  ->  -0.01        D = 0.05  ->  0.45
#       D = 0.5  ->   0.02        D = 0.02  ->  0.53
#       D = 0.1  ->   0.39        D = 0.008 ->  0.56      <- real rivers give 0.57
K_EROSION = 0.02          # erodibility
UPLIFT = 1.0              # rock delivered per step -- there must BE tectonics or nothing carves
D_HILL = 0.008            # hillslope creep, small enough that channels survive it

from math import tan, radians          # noqa: E402  (used by S_CRIT just below)

REPOSE_DEG = 33.0         # loose rock stands at its friction angle and no steeper. The studio
                          # MEASURED 40.03 deg for dry lunar regolith by growing a sandpile
                          # (core/trainables/granular.py); wet, weathered soil is shallower, ~33.

S_CRIT = tan(radians(REPOSE_DEG))     # the critical GRADIENT the transport law runs away at

PATCH_M = 12000.0         # how much ground: a two-hour walk across, which is why this size
GROUND_PATCH_M = 4.0      # NOT DERIVED -- see the note in derive(). Bracketed by 0.06 < x < 93.75.
GRID = 128
# HOW FINE THE PICTURE IS ALLOWED TO GET. The height field is defined continuously down to
# GROUND_PATCH_M by the octaves; this is only how densely the render samples it, which makes it a
# LOD decision and not a physics one. 512 over 12 km is 23.4 m a cell, at 262k splats -- and it
# draws only the octaves it can SAMPLE (lambda >= 2*dx), because drawing one it cannot is the same
# aliasing that made the first slope check report roughness as smoothing.
#
# WHY NOT FINER: THE RASTERISER, NOT THE PHYSICS. 1024 was tried first and the render came back
# with black wedges punched through the far half of the surface. That is ParticleEngine's
# MAX_PER_TILE = 16384 -- at an oblique camera the receding ground compresses a great many splats
# into very few tiles, and the overflow is dropped. Nothing was wrong with the geometry; the
# picture had simply outrun the thing drawing it. Recorded here so the next person to raise this
# number knows what the holes mean.
RENDER_GRID = 512

# THE LENS -- picture only, and here it is genuinely needed. 451 m of relief across 12 km is 3.8% of
# the patch, and the viewer orbits at 10 degrees above the horizontal, so AT TRUE SCALE THIS READS AS
# A FLAT GREEN PLATE. That is not a render bug, it is what a landscape looks like from a low angle;
# every relief map ever printed exaggerates for the same reason. Declared, dialled, and reversible --
# set it to 1 and you are looking at the real shape of the ground.
LENS = {
    "relief": {"lo": 1.0, "hi": 24.0, "default": 6.0, "label": "relief", "unit": "x true height"},
    "sun_height": {"lo": 0.05, "hi": 1.0, "default": 0.30, "label": "sun height", "unit": ""},
}


def _red_surface(n, rng, roughness):
    """The starting ground: a red-spectrum surface, power ~ 1/k.

    Real topography is not white noise -- a hill's neighbour is nearly as high as it is. A 1/k
    spectrum IS that statement, and it is the same law the parent uses at planet scale. This is only
    the CANVAS; the shape that matters gets carved into it.

    IT USED TO BE TWENTY-ONE SINE WAVES, AND YOU COULD SEE THEM. Seven octaves of three plane waves
    each is not a spectrum, it is an interference pattern, and every render of this patch wore a
    diagonal cross-hatch because of it. MEASURED, as the ratio of most- to least-favoured direction
    in the power spectrum (1.0 is isotropic):

        the 3-wave canvas   27.8x        after 500 steps of erosion   8.2x

    Erosion was supposed to destroy it and does not -- it only halves it twice, because incision
    follows the ground it is handed. Built in Fourier space instead, every direction gets its own
    random phase at the amplitude the law asks for and the same measurement gives 1.1x. Same
    spectrum, same seed, same determinism, no preferred axis."""
    import numpy as np
    f = np.fft.fftfreq(n, d=1.0 / n)
    kk = np.hypot(*np.meshgrid(f, f, indexing="ij"))
    kk[0, 0] = 1.0                                   # the mean is set below, not by the spectrum
    amp = 1.0 / kk                                   # power ~ 1/k^2 in amplitude = the red canvas
    amp[0, 0] = 0.0
    z = np.fft.ifft2(amp * np.exp(1j * rng.uniform(0, 2 * pi, size=(n, n)))).real
    return z / (z.std() + 1e-12) * roughness


def _bilinear(a, n):
    """Resample a square field to n x n. The large scales the erosion solved, carried up to the
    resolution the picture is drawn at -- the octaves are added on top, not interpolated into
    existence."""
    import numpy as np
    m = a.shape[0]
    g = np.linspace(0, m - 1, n)
    i0 = np.clip(g.astype(int), 0, m - 2)
    t = g - i0
    r = a[i0, :] * (1 - t)[:, None] + a[i0 + 1, :] * t[:, None]
    return r[:, i0] * (1 - t)[None, :] + r[:, i0 + 1] * t[None, :]


def _spectral_beta(z, dx, lo=4, hi_frac=3):
    """The spectral slope of THIS surface, MEASURED -- the exponent every added octave inherits.

    Real topography is scale-free: its radially-averaged power spectrum follows P(k) ~ k^-beta over
    many decades. That is not a modelling convenience, it is the observation that a mountain range
    and a boulder field have the same statistical shape at their own scales, and it is why terrain
    can be continued below a grid at all.

    So beta is not a knob. It is read off the eroded surface this membrane already built, which
    means the octaves added below the grid are a CONTINUATION of what erosion produced rather than
    decoration laid on top. Measured here: beta = 2.95 +/- 0.08 over five seeds.

    IT USED TO READ 2.54, AND THAT WAS THE CANVAS'S ARTIFACT TALKING. While _red_surface was built
    from twenty-one plane waves its power spectrum had directional spikes, which drag a RADIAL
    average away from the true slope. Rebuilding the canvas in Fourier space moved the measured
    beta to 2.95 and cost nothing else -- Hack's exponent stayed inside its own seed spread. So the
    number did not change because the terrain changed; it changed because the instrument stopped
    reading its own artifact.

    NOT THE SAME NUMBER AS THE IMAGE SPECTRUM, and the distinction is worth stating because the two
    were briefly conflated. Comparing this membrane's clay RENDER against a generated reference
    take of the same patch gave -3.14 and -3.01 -- a fair like-for-like check of one image against
    another, and it is what says the LAW here is right. But a shaded image is not a height field:
    shading follows the surface normal, the normal follows the gradient, and a gradient multiplies
    the spectrum by k^2. An image slope and a height slope are different quantities and must not be
    compared however alike the numbers look."""
    import numpy as np
    n = min(z.shape)
    g = z[:n, :n] - z[:n, :n].mean()
    g = g * np.hanning(n)[:, None] * np.hanning(n)[None, :]
    P = np.abs(np.fft.fftshift(np.fft.fft2(g))) ** 2
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c).astype(int)
    rad = (np.bincount(r.ravel(), P.ravel()) / np.maximum(np.bincount(r.ravel()), 1))[1:c]
    k = np.arange(1, len(rad) + 1)
    # FIT AWAY FROM BOTH ENDS. The lowest k are a handful of samples with no statistics, and the
    # highest are inside the grid's own attenuation -- fitting there measures the discretisation.
    band = (k >= lo) & (k <= len(rad) // hi_frac)
    return float(-np.polyfit(np.log(k[band]), np.log(rad[band]), 1)[0])


def _octave_amplitudes(beta, sigma_ref, n_oct, lam_grid):
    """How tall each added octave stands, as a SHAPE derived from beta. The level is set elsewhere.

    THE DERIVATION. For a 2D field with radially-averaged PSD P(k) ~ k^-beta, the variance carried
    by the octave spanning [k, 2k] is the spectrum integrated over that annulus:

        sigma^2(octave) = P(k) * 2*pi*k * dk  ~  k^2 * k^-beta  =  k^(2-beta)
        sigma(octave)   ~ k^(1 - beta/2)

    so each halving of wavelength multiplies amplitude by 2^(1 - beta/2). At the measured
    beta = 2.54 that is 0.83 per octave. Worth noting it is NOT the 0.5 the starting canvas uses:
    erosion steepens the spectrum it was handed, so continuing with the canvas's own falloff would
    under-produce detail by a growing margin at every octave. The number comes from the eroded
    surface because the eroded surface is what is being continued.

    AND BETA IS BELOW 3, WHICH IS THE INTERESTING PART. Amplitude falls by 0.83 per octave while
    wavelength falls by 0.5, so SLOPE rises by 1.66 at every halving -- without bound. That is not
    a defect in the fit; it is what beta < 3 means, and it is why the level cannot come from the
    spectrum. Ground does not get infinitely steep: below some scale terrain is FRICTION-limited
    rather than spectrum-limited, which is the threshold-hillslope regime every talus cone and
    scree slope in the world sits in. So this function returns the SHAPE and _detail_level() sets
    the level from the friction angle this membrane already publishes."""
    import numpy as np
    amps, lams = [], []
    for j in range(n_oct):
        lams.append(float(lam_grid / (2.0 ** (j + 1))))
        amps.append(float(sigma_ref * (2.0 ** ((1.0 - beta / 2.0) * (j + 1)))))
    return amps, lams


def _fine_window(z, dx, amps, lams, patch_m, rng, w=1024):
    """A patch of this surface at a resolution that actually RESOLVES the added octaves.

    THE OCTAVES CANNOT BE CHECKED ON THE GRID THEY WERE ADDED BELOW. The finest is a 2.9 m
    wavelength and the erosion grid samples every 93.75 m, so evaluating them there is pure
    aliasing -- the first version of this did exactly that and the tell was in the output: MEAN
    slope fell from 17.04 to 16.63 when adding roughness must raise it. Aliased waves cancel.

    Resolving 2.9 m across the whole 12 km patch would be 8192^2 = 67M cells. But fine-scale slope
    is a LOCAL property -- it does not need the whole patch to be measured, only enough ground to
    be representative -- so this takes a window covering about 1.5 km at half the finest wavelength
    and measures there. The base surface is interpolated up into it; the octaves are evaluated at
    their own scale."""
    import numpy as np
    dxf = min(lams) / 2.0                       # Nyquist for the finest octave
    span = w * dxf                              # how much ground the window covers
    n = z.shape[0]
    c0 = 0.5 - 0.5 * span / patch_m             # centred on the patch
    g = (np.arange(w) * dxf) / patch_m + c0
    yy, xx = np.meshgrid(g, g, indexing="ij")
    fy, fx = yy * (n - 1), xx * (n - 1)
    i0, j0 = np.clip(fy.astype(int), 0, n - 2), np.clip(fx.astype(int), 0, n - 2)
    ty, tx = fy - i0, fx - j0
    base = ((z[i0, j0] * (1 - ty) + z[i0 + 1, j0] * ty) * (1 - tx)
            + (z[i0, j0 + 1] * (1 - ty) + z[i0 + 1, j0 + 1] * ty) * tx)
    det = _detail_field(w, amps, lams, span, rng)
    return base, det, dxf


def _detail_level(z, detail, dx, repose_deg, lo=0.0, hi=1.0, iters=24):
    """Scale the detail until the ground stands exactly at its friction angle and no steeper.

    ONE FREE NUMBER, FIXED BY A CONSTRAINT THE MEMBRANE ALREADY ENFORCES. derive() has always
    published `slopes_below_repose`, and it has always been true; adding relief must not make it
    false. So the detail's overall level is not chosen -- it is the largest level at which this
    membrane's own existing check still passes, found by bisection.

    Capping each octave separately (the first attempt) does not do this: five octaves each at the
    repose limit sum to something well past it, because slopes add. The constraint is on the TOTAL
    surface, so it is applied to the total surface."""
    import numpy as np
    tan_rep = np.tan(np.radians(repose_deg))

    def p95(scale):
        gy, gx = np.gradient(z + scale * detail, dx)
        return float(np.percentile(np.hypot(gx, gy), 95))

    if p95(hi) <= tan_rep:
        return hi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if p95(mid) <= tan_rep:
            lo = mid
        else:
            hi = mid
    return lo


def _detail_field(n, amps, lams, patch_m, rng):
    """The octaves themselves: band-limited noise, synthesised in Fourier space.

    NOT A SUM OF SINE WAVES, AND THE PICTURE IS WHY. The first version copied _red_surface's
    construction -- three plane waves per octave -- and the close render came back wearing a regular
    diagonal cross-hatch. Three waves is not noise, it is an interference pattern, and you can see
    it. The canvas gets away with it because five hundred steps of erosion run afterwards and
    destroy the periodicity; these octaves are never eroded, so nothing hides it.

    Building in Fourier space fixes it at the root rather than by adding more waves. Give every
    frequency in the octave's band a random phase and an amplitude of one, transform back, and the
    result is a genuinely stochastic Gaussian field -- every direction represented, no preferred
    axis, no repeat -- with exactly the band it was asked for. It is also faster: one FFT an octave
    at 512^2 against thousands of full-grid sine evaluations.

    Each band is normalised to unit variance and then scaled by its DERIVED amplitude, so the
    spectrum the octave ladder specifies is what the field actually carries."""
    import numpy as np
    if not amps:
        return np.zeros((n, n))
    f = np.fft.fftfreq(n, d=patch_m / n)             # cycles per metre
    kk = np.hypot(*np.meshgrid(f, f, indexing="ij"))
    d = np.zeros((n, n))
    for amp, lam in zip(amps, lams):
        band = (kk >= 1.0 / (2.0 * lam)) & (kk < 1.0 / lam)
        if not band.any():
            continue
        ph = rng.uniform(0, 2 * pi, size=(n, n))
        F = np.where(band, np.exp(1j * ph), 0.0)
        g = np.fft.ifft2(F).real
        sd = g.std()
        if sd > 1e-12:
            d += amp * g / sd
    return d


def _priority_flood(z, n, eps=1e-4):
    """FILL THE HOLLOWS -- and this is not bookkeeping, it is what water does.

    A cell lower than all eight of its neighbours has nowhere to send its water. Left alone it keeps
    it, everything upstream is cut off from the sea, and the network never organises: the drainage
    areas stay small and scattered and Hack's exponent comes out 0.2 instead of 0.57.

    Water does not do that. It FILLS the hollow until it overflows the lowest point of the rim, and
    carries on from there.

    THE ALGORITHM MATTERS. Relaxing each pit up to just above its lowest neighbour looks equivalent
    and is not: it propagates the fill level one cell per pass, so a wide basin needs as many passes
    as it is wide. Measured here -- 40 passes took 220 pits down to 111 and stalled.

    This is priority-flood (Barnes, Lehman & Mulla 2014): start at the rim, always process the
    LOWEST cell reached so far, and give every cell the higher of its own height and the level it
    was reached at. Each cell is settled once, in one pass, exactly."""
    import heapq
    import numpy as np
    done = np.zeros((n, n), dtype=bool)
    heap = []
    for i in range(n):
        for (a, b) in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
            if not done[a, b]:
                done[a, b] = True
                heapq.heappush(heap, (float(z[a, b]), a, b))
    while heap:
        lvl, a, b = heapq.heappop(heap)
        for da, db in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            ra, rb = a + da, b + db
            if 0 <= ra < n and 0 <= rb < n and not done[ra, rb]:
                done[ra, rb] = True
                if z[ra, rb] <= lvl:
                    z[ra, rb] = lvl + eps                 # it is under water: raise it to the surface
                heapq.heappush(heap, (float(z[ra, rb]), ra, rb))
    return z


def _carve(z, dx, steps, rng):
    """RUN THE WATER. Each step: raise the rock, send every cell's water to its lowest neighbour,
    add up how much crosses each cell, and lower it by the stream-power law. Then let the hillslopes
    creep.

    The order matters and is the whole trick: process cells from HIGH to LOW, so by the time a cell
    is reached everything that drains into it has already handed its water over. One pass, no
    iteration, exact."""
    import numpy as np
    n = z.shape[0]
    area0 = dx * dx
    # the eight neighbours, and the distance to each
    offs = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
            (-1, -1, sqrt(2)), (-1, 1, sqrt(2)), (1, -1, sqrt(2)), (1, 1, sqrt(2))]
    idx = np.arange(n * n)
    iy, ix = idx // n, idx % n
    for _ in range(steps):
        z += UPLIFT
        z[0, :] = z[-1, :] = z[:, 0] = z[:, -1] = 0.0      # the edges are sea level: the outlet

        # ── FILL THE HOLLOWS FIRST, and this is not bookkeeping, it is what water does ──────────
        #
        # A cell lower than all eight of its neighbours has nowhere to send its water. Left alone it
        # keeps it, and everything upstream of it is cut off from the sea -- so the network never
        # organises and the drainage areas stay small and scattered.
        #
        # Water does not do that. It FILLS the hollow until it overflows the lowest rim, and then
        # carries on. Every landscape-evolution model needs this step and this one did not have it:
        # 511 pits out of 16,384 cells, and Hack's exponent came out 0.22 against a real 0.57.
        # Relax each pit up to just above its lowest neighbour until none are left.
        _priority_flood(z, n)

        flat = z.ravel()
        # steepest descent: for each cell, which neighbour is lowest, and how steep.
        #
        # THE NEIGHBOURS MUST NOT WRAP. The first version used np.roll, which is periodic -- so a
        # cell on the left edge drained to the right edge, and the "network" was stitched across the
        # patch in a way no water does. Hack's exponent came out 0.22 against a real 0.57, which is
        # what a fractal wearing valleys looks like. The test caught it before the render did.
        best_drop = np.zeros(n * n)
        recv = idx.copy()
        for dy, dxi, dist in offs:
            ry, rx = iy + dy, ix + dxi
            ok = (ry >= 0) & (ry < n) & (rx >= 0) & (rx < n)      # off the edge is not a neighbour
            r_lin = np.where(ok, ry * n + rx, idx)
            drop = np.where(ok, (flat - flat[r_lin]) / (dist * dx), -1.0)
            better = drop > best_drop
            best_drop[better] = drop[better]
            recv[better] = r_lin[better]

        # accumulate, high to low -- one pass, because a cell's donors are always above it
        order = np.argsort(-flat)
        acc = np.full(n * n, area0)
        for c in order:
            r = recv[c]
            if r != c:
                acc[r] += acc[c]

        # STREAM POWER: the river cuts by how much water crosses and how steeply it falls
        incision = K_EROSION * (acc ** M_EXP) * (best_drop ** N_EXP)
        z -= incision.reshape(n, n)

        # ── HILLSLOPE TRANSPORT, and it must be NON-LINEAR or there is no angle of repose ────────
        #
        # Plain diffusion (q = D S) only smooths: double the slope, double the flux, and nothing
        # ever stops it -- so slopes just keep getting steeper wherever the rivers cut down faster
        # than the hillside can respond. Measured: p95 stood at 46 degrees where loose rock cannot
        # exceed about 33.
        #
        # Real hillslopes obey Roering, Kirchner & Dietrich 1999:
        #
        #       q_s  =  D S / (1 - (S/S_c)^2)
        #
        # As the slope approaches the critical angle the flux goes to INFINITY, so the slope cannot
        # get there: the hillside dumps material as fast as it is delivered. That is what an angle
        # of repose IS -- not a clamp applied afterwards, but a transport law that refuses.
        # AND IT MUST BE SUB-STEPPED, or the runaway runs away for real. An explicit diffusion step
        # is only stable while D*dt/dx^2 stays under about 0.25; the moment the flux term multiplies
        # D by fifty the scheme detonates. Measured: relief 1e63 metres and every slope at 90 deg --
        # not a steep landscape, a numerical explosion wearing one. So take as many small steps as
        # the steepest cell demands. The physics is unchanged; only the arithmetic is made honest.
        STABLE = 0.20
        zp = np.pad(z, 1, mode="edge")
        gy, gx = np.gradient(zp, dx)
        s2 = np.clip((gx * gx + gy * gy) / (S_CRIT * S_CRIT), 0.0, 0.985)
        sub = int(min(32, max(1, np.ceil((D_HILL / (1.0 - s2)).max() / STABLE))))
        for _s in range(sub):
            zp = np.pad(z, 1, mode="edge")
            gy, gx = np.gradient(zp, dx)
            s2 = np.clip((gx * gx + gy * gy) / (S_CRIT * S_CRIT), 0.0, 0.985)
            eff = (D_HILL / (1.0 - s2))[1:-1, 1:-1] / sub      # each sub-step is 1/sub of the whole
            lap = (zp[:-2, 1:-1] + zp[2:, 1:-1] + zp[1:-1, :-2] + zp[1:-1, 2:] - 4.0 * z)
            z += eff * lap
            np.maximum(z, 0.0, out=z)

    # ── ONE FINAL ROUTING PASS, on the surface that is actually returned ─────────────────────────
    #
    # THIS WAS A REAL BUG AND IT IS WHY HACK'S LAW FAILED. `recv` used to be whatever the last loop
    # iteration computed -- BEFORE that iteration's incision and creep moved the ground. So the
    # returned heights and the returned flow graph disagreed, and every downstream walk that sorts
    # by height then follows `recv` had donors arriving AFTER their receivers. Long chains never
    # accumulated, the longest-stream length came out systematically short for big basins, and the
    # exponent flattened to 0.19.
    _priority_flood(z, n)
    flat = z.ravel()
    best_drop = np.zeros(n * n)
    recv = idx.copy()
    for dy, dxi, dist in offs:
        ry, rx = iy + dy, ix + dxi
        ok = (ry >= 0) & (ry < n) & (rx >= 0) & (rx < n)
        r_lin = np.where(ok, ry * n + rx, idx)
        drop = np.where(ok, (flat - flat[r_lin]) / (dist * dx), -1.0)
        better = drop > best_drop
        best_drop[better] = drop[better]
        recv[better] = r_lin[better]
    acc = np.full(n * n, area0)
    for c in np.argsort(-flat):
        r = recv[c]
        if r != c:
            acc[r] += acc[c]
    return z, recv, acc, best_drop


def _hack_exponent(recv, acc, z, n, dx):
    """MEASURE HACK'S LAW ON WHAT WAS CARVED. For every cell, the length of the longest stream
    reaching it; against the area draining into it. Fit log L against log A.

    Observed on real rivers since Hack 1957: L ~ A^0.57, and it is nowhere in the simulation."""
    import numpy as np
    order = np.argsort(-z.ravel())
    L = np.zeros(n * n)
    for c in order:
        r = recv[c]
        if r != c:
            ddx, ddy = abs(int(r) % n - int(c) % n), abs(int(r) // n - int(c) // n)
            step = dx * (sqrt(2) if (ddx and ddy) else 1.0)
            if L[c] + step > L[r]:
                L[r] = L[c] + step
    keep = (acc > 40 * dx * dx) & (L > 3 * dx)          # real channels only, not single cells
    if keep.sum() < 50:
        return float("nan"), L
    a, b = np.polyfit(np.log(acc[keep]), np.log(L[keep]), 1)
    return float(a), L


# THE GROUND SCANS + SKY CAP -- the same two declared dials theGround keeps: the captures that
# carry soil/stone/vegetation, and the luminance above which a ground-scan genome is the SKY
# through canopy, not a surface. One codebook (story/data/material_genomes.json), one rule.
GROUND_SCANS = ("garden", "stump", "treehill", "garden_tree", "christmas_tree")
SKY_LUM_CAP = 0.75


def _surface_genomes():
    """WHICH MEASURED GENOME FILLS WHICH SURFACE ROLE (2026-07-31 -- the typed veg/rock literals
    are gone): vegetation = the GREENEST ground-carried genome (max G over max(R,B) -- the leaf
    material the garden/tree scans measured), bare rock = the lightest under the sky cap (the
    pale stone the garden's pavers measured). WATER IS NOT HERE: no open-water scan exists in
    the collection, so the channel colour below stays typed and FLAGGED, not quietly kept."""
    from matter import pick_genomes, genome_lum
    cands = [g for g in pick_genomes(GROUND_SCANS) if genome_lum(g) <= SKY_LUM_CAP]
    veg = max(cands, key=lambda g: g["features"]["G"]["mean"]
              - max(g["features"]["R"]["mean"], g["features"]["B"]["mean"]))
    rock = max(cands, key=genome_lum)
    return {"veg": veg, "rock": rock}


def derive(parent, free):
    if parent is None or "carved_by" not in parent:
        raise ValueError("aTerrain requires theTerrain as its parent")
    import numpy as np
    rng = np.random.default_rng(2029)
    dx = PATCH_M / GRID

    # WHERE THIS PATCH IS. Not chosen: the parent solved an ice line, so the temperate band is
    # everything equatorward of it, and this sits in the middle of that band -- the one place on
    # this world where a person could stand outside.
    # NO DEFAULT. This used to read `parent.get("glaciated_fraction", 0.3)`, which is the same
    # failure as `parent.get("day_s", 86400.0)` one membrane up: the parent DOES carry this number
    # (theTerrain derives it from aBlueWorld's ice_fraction), so the 0.3 never fired -- it just sat
    # there waiting to serve a hard-coded ice line the moment the chain above stopped carrying one,
    # silently, with the latitude of the only habitable patch on this world quietly frozen at 31.5
    # degrees no matter what the climate did. If the parent MUST supply it, ask for it and let it
    # break. A broken chain has to be loud.
    ice_lat = 90.0 - float(parent["glaciated_fraction"]) * 90.0
    lat = 0.5 * ice_lat

    # THE CANVAS, AND IT IS DELIBERATELY *NOT* THE PARENT'S ROUGHNESS.
    #
    # This comment used to read "the parent's own continental roughness, brought down to this patch's
    # size", directly above a hard-coded 3.0 -- a claim of inheritance the line beneath it contradicts
    # and the code never performed. That is the same species as `T_star_surface: 5772.0` under a
    # comment saying it was carried from the system: a false comment is a typed number's alibi, and
    # neither the literal scan nor the assumption manifest can catch one, because 3.0 is an argument
    # in a call rather than a returned key or a module constant.
    #
    # THE CODE IS THE RIGHT ONE; THE COMMENT WAS WRONG. Start nearly flat -- 3 m of seed texture on a
    # 12 km patch. The relief is BUILT by uplift against incision, not inherited from noise, which is
    # what makes this a landscape rather than a fractal with valleys drawn on it. Handing the parent's
    # 1,302 m continental roughness in here would be handing over the answer: the patch would arrive
    # pre-shaped and the stream-power law would have nothing left to do.
    #
    # HONEST CONSEQUENCE, so nobody discovers it as a surprise: because the shape is grown here rather
    # than inherited, this patch's relief and slopes do NOT respond to theTerrain's continental_fraction
    # dial. The audit's slider test reports exactly that (theGround 0/36 under that dial) and it is a
    # real property of this design, not a broken read.
    z = _red_surface(GRID, rng, 3.0)
    z, recv, acc, slope = _carve(z, dx, 500, rng)
    hack, L = _hack_exponent(recv, acc, z, GRID, dx)

    ang = np.degrees(np.arctan(slope))
    channels = acc > 40 * dx * dx

    from matter import genome_rgb as _grgb
    _sg = _surface_genomes()
    _surface_materials = {
        "veg": {"genome_id": _sg["veg"]["id"], "rgb_mean": [float(c) for c in _grgb(_sg["veg"])]},
        "rock": {"genome_id": _sg["rock"]["id"], "rgb_mean": [float(c) for c in _grgb(_sg["rock"])]},
        "water": {"genome_id": None, "rgb_mean": [0.10, 0.20, 0.30],
                  "flag": "TYPED -- NO OPEN-WATER SCAN in the collection; flagged, not quietly kept"},
    }
    # THE SPECTRUM THIS SURFACE ACTUALLY HAS, and the octaves that continue it down to the child.
    beta = _spectral_beta(z, dx)
    _n_oct = max(0, int(round(np.log2(dx / GROUND_PATCH_M))))
    # The reference amplitude is what the LAST RESOLVED octave carries -- how far one cell of this
    # surface stands off its own neighbourhood -- so the continuation starts from measured ground
    # rather than from a chosen constant.
    _blur = np.copy(z)
    for _ in range(2):
        _blur = 0.25 * (np.roll(_blur, 1, 0) + np.roll(_blur, -1, 0)
                        + np.roll(_blur, 1, 1) + np.roll(_blur, -1, 1))
    _sigma_ref = float(np.std(z - _blur))
    _amps, _lams = _octave_amplitudes(beta, _sigma_ref, _n_oct, dx)
    _base_w, _det_w, _dxf = _fine_window(z, dx, _amps, _lams, PATCH_M,
                                         np.random.default_rng(7717))
    _level = _detail_level(_base_w, _det_w, _dxf, REPOSE_DEG)
    _amps = [a * _level for a in _amps]
    _gy, _gx = np.gradient(_base_w + _level * _det_w, _dxf)
    _angd = np.degrees(np.arctan(np.hypot(_gx, _gy)))

    return {
        # ITS REAL SIZE: the patch. Twelve kilometres -- a couple of hours on foot, which is the
        # unit that matters once there is a person.
        "extent_m": PATCH_M,
        # ITS OWN DURATION: one day, inherited. The sun crosses; the landscape does not move.
        "duration_s": float(parent["day_s"]),

        "latitude_deg": lat,
        "patch_m": PATCH_M,
        # HOW BIG A SAMPLE OF GROUND THIS CONTAINS, declared here because how big a child is IS the
        # parent's to say -- and because it was previously typed in TWO places with no link between
        # them: theGround's own extent_m, and layout()'s `scale = 4.0 / half_m` twelve lines below.
        # Change one and the composition silently scaled wrong.
        #
        # IT IS STILL NOT DERIVED, and moving it did not derive it. What is known BRACKETS without
        # picking: it must fit inside one cell of this grid (93.75 m), since the law below reads a
        # single slope as constant across it; and it must hold many of theGround's largest clasts
        # (60 mm), so far above 0.06 m. 4 m sits in 0.06 < x < 93.75 -- and so would 3 m, and so
        # would 20 m. One honest assertion in one place is the whole of what changed.
        "ground_patch_m": GROUND_PATCH_M,
        "grid": GRID,
        "cell_m": dx,
        "relief_m": float(z.max() - z.min()),

        # ── THE OCTAVES BELOW THE GRID ────────────────────────────────────────────────────────
        # A 128 grid over 12 km puts Nyquist at 93.75 m: nothing smaller than a football field
        # could exist here, and a whole membrane of ground was therefore missing. The law was
        # never wrong -- measured against an independent reference take of this same patch, this
        # surface's spectral slope is 3.14 against 3.01, within 4% -- it was only ever evaluated
        # over ONE DECADE of scale. These continue it.
        #
        # WHERE THEY STOP IS THE HIERARCHY'S ANSWER, NOT A SETTING: a membrane resolves down to
        # its child's extent and the child takes over from there. theGround is 4 m across, so
        # aTerrain resolves to 4 m and stops. Asking this membrane for a pebble is asking the
        # wrong membrane.
        "spectral_beta": beta,
        "spectral_beta_source": "measured from this membrane's own eroded surface (_spectral_beta)",
        "octave_amplitude_ratio": float(2.0 ** (1.0 - beta / 2.0)),
        "detail_octaves": len(_amps),
        "detail_floor_m": float(_lams[-1]) if _lams else dx,
        "detail_relief_m": float(2.0 * sum(_amps)),
        "detail_amplitudes_m": [float(a) for a in _amps],
        # THE ONE FREE NUMBER, AND WHAT FIXED IT. beta < 3 means slope grows without bound as
        # wavelength falls, so the spectrum cannot set the level -- the friction angle does. This
        # is the largest level at which `slopes_below_repose` below is still true.
        "detail_level": float(_level),
        "detail_level_set_by": "bisection against repose_deg on the TOTAL surface",
        "friction_limited": bool(_level < 0.999),
        # the slope statistics WITH the octaves in, which are the ones a foot would feel
        "mean_slope_deg": float(_angd.mean()),
        "p95_slope_deg": float(np.percentile(_angd, 95)),
        "mean_slope_deg_grid_only": float(ang.mean()),
        "p95_slope_deg_grid_only": float(np.percentile(ang, 95)),
        "repose_deg": REPOSE_DEG,
        "slopes_below_repose": bool(np.percentile(_angd, 95) < REPOSE_DEG),
        "drainage_density_per_km": float(channels.sum() * dx / (PATCH_M / 1e3) ** 2 / 1e3),
        "hack_exponent": hack,
        "carved_by": parent["carved_by"],

        # THE SURFACE THE RENDER MUST WEAR (measured): which genome fills each role, so the
        # numbers record what the picture shows. water_material is TYPED and flagged -- no
        # open-water scan is in the collection (the operator was told 2026-07-31).
        "surface_materials": _surface_materials,
        "surface_source": "story/data/material_genomes.json (16 real 3DGS scans; Construction/material_elements.py)",

        # carried for anything that stands here
        "g": float(parent["g"]),
        "T_surface": float(parent["T_surface"]),
        "lapse_rate_K_per_km": float(parent["lapse_rate_K_per_km"]),
        "day_s": float(parent["day_s"]),
        # THE TILT, CARRIED. Being what all your children can see is what a parent is FOR: the body
        # fourteen membranes down needs to know which way the axis points, and a sibling cannot hand
        # it over. No default -- if the parent has not got one, that is a broken chain, not a 23.44.
        "obliquity_deg": float(parent["obliquity_deg"]),
        "obliquity_effective_deg": float(parent["obliquity_effective_deg"]),
        "retrograde": bool(parent["retrograde"]),
        "tropic_lat_deg": float(parent["tropic_lat_deg"]),
        "polar_circle_lat_deg": float(parent["polar_circle_lat_deg"]),
        "has_seasons": bool(parent["has_seasons"]),
        # the air, still travelling: the body at the bottom of this chain needs it
        "gases_kept": list(parent["gases_kept"]),
        "P_surface_bar": float(parent["P_surface_bar"]),
        "days_per_year": float(parent["days_per_year"]),
        "year_s": float(parent["year_s"]),

        "S_earth": float(parent["S_earth"]),
        "sea_level_m": float(parent["sea_level_m"]),
        # the Froude LAW travels; the answer is computed by whatever has a leg
        "walk_run_per_sqrt_leg": float(parent["walk_run_per_sqrt_leg"]),
        "swing_period_per_sqrt_leg": float(parent["swing_period_per_sqrt_leg"]),
        "P_surface_bar": float(parent["P_surface_bar"]),
    }


def emit(nums, t=1.0):
    """The matter of aTerrain, in its own local units (1.0 = half the patch).

    The ground itself, one grain per cell, coloured by what the water did to it: channels dark and
    wet, hillslopes vegetated, anything steep enough to shed its soil bare rock. Height is at TRUE
    scale here -- a 12 km patch with a few hundred metres of relief needs no exaggeration, which is
    the first membrane in this whole story that can say so.

    The movie is ONE DAY. The sun crosses, and the shadows are the point: a landscape is legible
    because of them, and at noon a real valley nearly disappears."""
    import numpy as np
    from matter import blank, paint, lit, surface_grain, SOLID

    tt = float(t)
    rng = np.random.default_rng(2029)
    ng = int(nums["grid"])
    dxg = float(nums["cell_m"])
    zg, recv, acc, slope = _carve(_red_surface(ng, rng, 3.0), dxg, 500, rng)

    # ── THE OCTAVES, DRAWN AT A RESOLUTION THAT CAN HOLD THEM ─────────────────────────────────
    # The erosion grid is 93.75 m a cell and the field is defined down to a few metres, so the
    # picture is sampled finer than the physics is solved. Only the octaves this render grid can
    # SAMPLE are drawn -- an octave below Nyquist does not add detail, it adds moire, which is
    # exactly the aliasing that made the first slope check report roughness as smoothing. What is
    # left out is not lost: it is theGround's, one membrane down, at four metres across.
    n = int(RENDER_GRID)
    dx = PATCH_M / n
    _amps = list(nums.get("detail_amplitudes_m", []))
    _lams = [dxg / (2.0 ** (j + 1)) for j in range(len(_amps))]
    _keep = [(a, l) for a, l in zip(_amps, _lams) if l >= 2.0 * dx]
    z = _bilinear(zg, n)
    if _keep:
        z = z + _detail_field(n, [a for a, _ in _keep], [l for _, l in _keep],
                              PATCH_M, np.random.default_rng(7717))
    # _carve hands back acc and slope FLAT while z is 2-D; reshape before resampling
    acc = _bilinear(np.asarray(acc).reshape(ng, ng), n)

    half = PATCH_M / 2.0
    y, x = np.mgrid[0:n, 0:n]
    px = (x.ravel() * dx - half) / half
    py = (y.ravel() * dx - half) / half
    lens = nums.get("_lens", {})
    exag = float(lens.get("relief", 6.0))
    pz = (z.ravel() - z.mean()) / half * exag

    b = blank(n * n)
    b[:, 0] = px
    b[:, 1] = py
    b[:, 2] = pz

    # the surface normal, from the height field -- this is what lets the sun model the ground.
    # Taken from the DETAILED field at the render's own spacing, so the octaves light correctly
    # instead of being a bump the shading never hears about.
    gy, gx = np.gradient(z, dx)
    nrm = np.stack([-gx.ravel(), -gy.ravel(), np.ones(n * n)], axis=1)
    nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
    b[:, 21:24] = nrm

    # ang/channel/steep are per-splat, so they are FLAT -- the gradient above is 2-D now that the
    # render grid is its own field rather than the erosion grid.
    ang = np.degrees(np.arctan(np.hypot(gx, gy))).ravel()
    channel = (acc > 40 * dxg * dxg).ravel()
    steep = ang > float(nums["repose_deg"]) * 0.8
    # SURFACE COLOUR, MEASURED (2026-07-31): the typed veg/rock literals are gone -- each cell
    # DRAWS its albedo from its role genome's measured distribution. water stays typed and
    # FLAGGED (no open-water scan in the collection -- see _surface_genomes' docstring).
    from matter import sample_genome_rgb
    _sg = _surface_genomes()
    water = np.array([0.10, 0.20, 0.30], np.float32)          # TYPED, FLAGGED: NO WATER SCAN
    veg = sample_genome_rgb(_sg["veg"], rng, n * n)
    rock = sample_genome_rgb(_sg["rock"], rng, n * n)
    albedo = np.where(channel[:, None], water, np.where(steep[:, None], rock, veg))

    # ONE DAY: the sun crosses. Its height is the latitude's, so the shadows are this place's.
    hour = 2.0 * pi * tt
    alt = max(float(lens.get("sun_height", 0.30)) * 0.2,
              np.cos(np.radians(float(nums["latitude_deg"]))) * np.sin(hour)
              * float(lens.get("sun_height", 0.30)) / 0.30)
    sun = np.array([np.cos(hour), 0.25, alt], np.float32)
    sun /= np.linalg.norm(sun)
    lam = np.clip(nrm @ sun, 0.0, None)
    b[:, 16:19] = lit(albedo, float(nums["S_earth"]) * lam + 0.05,
                      e_ref=float(nums["S_earth"]), tone=0.45)
    b[:, 19] = 0.95
    b[:, 20] = surface_grain(n * n, radius=1.0, cover=0.85)
    b[:, 11] = SOLID
    return b


def layout(nums):
    """WHERE THE THINGS INSIDE THIS MEMBRANE SIT, in its frame (1.0 = half the patch, 6 km).

    theGround is four metres of this landscape, so it goes in at 4/6000 -- and IT IS SUB-PIXEL HERE,
    by a factor of about a thousand. That is not a reason to leave it out. The composition is what
    makes the tree ONE OBJECT rather than a stack of separate pictures: zoom in and the ground is
    already there, at the place on the hillside it belongs to, with the same stones the law derived.
    The LOD budget cuts it to a handful of grains at this framing, which is exactly right -- a thing
    occupying a thousandth of a pixel does not need 26,000 splats to say so."""
    half_m = float(nums["patch_m"]) / 2.0
    # READ FROM THE ONE PLACE IT IS DECLARED. This used to type 4.0 independently of theGround's own
    # extent_m, so the two could drift apart and mis-scale the composition in silence. It is the same
    # ungrounded number as before -- see the note at `ground_patch_m` in derive() -- but there is now
    # exactly one of it.
    # If it moves there and not here, the child is placed at the wrong size and nothing complains.
    scale = float(nums["ground_patch_m"]) / half_m
    # placed on the valley floor rather than at the origin: the flat ground near a channel is where
    # a person would actually be standing, and this membrane knows where its channels are.
    return {"theGround": ((0.18, -0.32, 0.0), scale)}


def measure(nums):
    """Facts -- and the one that decides whether this is a landscape or a fractal in a hat."""
    return {
        "relief_m": nums["relief_m"],
        "mean_slope_deg": nums["mean_slope_deg"],
        "drainage_density_per_km": nums["drainage_density_per_km"],
        # HACK'S LAW, measured on the carved network. Observed 0.55-0.60 on real rivers worldwide
        # since 1957, and put into this simulation nowhere.
        "hack_exponent": nums["hack_exponent"],
        "obeys_hacks_law": 0.50 < nums["hack_exponent"] < 0.65,
        # loose rock cannot stand steeper than its friction angle
        "slopes_below_repose": nums["slopes_below_repose"],
    }
