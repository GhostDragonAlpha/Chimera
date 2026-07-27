"""planet_membrane — the planet as an ONION of nested height-map membranes.

THE RUNG (2026-07-24, operator's frame, three messages). Terrain is NOT grown patch by
patch. It is the planet's OUTER MEMBRANE and it is produced ALL AT ONCE, whole-sphere. And
it is not ONE surface: dig down and you cross topsoil, subsoil, bedrock, mantle, lava, core
-- an ONION of height maps, one per depth. The governing law the operator named:

    "if we modify the base then all elements down should be able to be transformed based on
     the changes ... use the hierarchy as the consideration for everything so when you
     affect the parent it doesn't break the child."

That invariant DICTATES the representation. It is satisfiable only if every child layer is
stored RELATIVE to its parent (a thickness field), never as an absolute radius. Then raising
a mountain in the base surface carries its topsoil, bedrock, and everything resting on them
UPWARD with it -- the child's relative state is untouched (not broken); only its absolute
position follows the parent. Store children absolutely and every parent edit shatters them.
This module measures that difference and shows the shatter it avoids.

WHY SPHERICAL HARMONICS. A whole-sphere field "produced all at once" IS an SH synthesis: you
sum global basis functions and the entire globe appears together, with no pole seam and no
tiling. And SH is the LITERAL realization of the operator's hierarchy: low degrees are
continents (the parent), high degrees are mountains (the child); edit a low-degree
coefficient and a whole continent moves with every mountain riding on it. LOD is degree
truncation -- `depth()` of the membrane IS the max degree resolved. Real Earth topography is
canonically stored exactly this way, so "drop in real Earth data later" is the SAME
representation with measured coefficients instead of Earth-realistic ones (`from_topo_grid`).

HONEST STATUS. The surface here is EARTH-REALISTIC BY STATISTICS, not the pixel-exact Earth:
a two-crust continent field (the bimodal hypsometry that continental vs oceanic crust makes)
plus a red-spectrum roughness field. Land fraction, hypsometric bimodality, and relief are
MEASURED against Earth's real numbers below. It is not the real Earth until a real DEM or a
real SH topo expansion is loaded through the seam -- which changes the seed, not the rung.

Instances core/membranes.py (the boundary-is-a-scale primitive); the onion IS nested
Membrane nodes, so address = path of layers crossed and LOD = depth, for free.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.special import sph_harm_y

R_EARTH = 6.371e6                         # m
EARTH_LAND_FRACTION = 0.291               # the number the surface is tuned to hit
EARTH_OCEAN_MODE = -3700.0               # m, abyssal-plain modal depth
EARTH_LAND_MODE = 300.0                  # m, continental-platform modal height

# The onion, outer -> inner. Each layer's thickness is RELATIVE to the layer above it, so a
# base edit carries all of them. Depths are Earth-typical order-of-magnitude (the mantle and
# core dominate; topsoil is the "top six inches" the operator named -- both must coexist).
LAYERS = [
    ('surface', 0.0),            # the SH elevation field itself (the base every child rides)
    ('topsoil', 0.15),           # ~6 inches of living soil
    ('subsoil', 1.2),            # weathered mineral soil
    ('bedrock', 60.0),           # to competent rock
    ('crust',   35_000.0),       # continental crust base (Moho ~35 km)
    ('mantle',  2_890_000.0),    # to the core-mantle boundary
    ('core',    3_480_000.0),    # to the planet centre
]


# --- spherical-harmonic field synthesis ------------------------------------
#
# A real, orthonormal SH basis built from scipy's complex Y_l^m. For random-field generation
# the exact per-harmonic sign convention is irrelevant; what matters is that the basis is
# real and orthonormal so the angular power spectrum C_l is controllable by the coefficient
# variance at each degree. Coeffs are stored keyed (l, m, 'c'|'s') -- THIS is the adjustable,
# LOD-truncatable, real-data-swappable representation.


def _synth(coeffs: dict, lmax: int, lat_rad: np.ndarray, lon_rad: np.ndarray) -> np.ndarray:
    """Synthesize the field on the (latitude x longitude) grid -- SEPARABLY.

    The key identity that makes a whole-sphere synthesis fast: Y_lm(theta, phi) =
    Y_lm(theta, 0) * exp(i*m*phi). The costly associated-Legendre part depends only on
    LATITUDE, so it is evaluated on a 1-D column of ~180 colatitudes -- not the full 64,800
    -point grid -- and longitude enters as a cheap cos/sin outer product. That is ~360x fewer
    special-function calls, and turns a multi-minute synth into a fraction of a second.

    Y_lm(theta,0) is real (= N_lm * P_lm(cos theta)); Y_lm.real = that * cos(m phi) and
    Y_lm.imag = that * sin(m phi), which is exactly the real cos/sin SH basis.
    """
    theta = np.pi / 2 - lat_rad                          # colatitude column, (nlat,)
    nlat, nlon = lat_rad.size, lon_rad.size
    field = np.zeros((nlat, nlon), dtype=np.float64)
    cosm = [np.cos(m * lon_rad) for m in range(lmax + 1)]
    sinm = [np.sin(m * lon_rad) for m in range(lmax + 1)]
    for l in range(lmax + 1):
        c0 = coeffs.get((l, 0, 'c'), 0.0)
        if c0:
            Yl0 = sph_harm_y(l, 0, theta, 0.0).real      # (nlat,)
            field += c0 * Yl0[:, None]                   # cos(0*phi) = 1
        for m in range(1, l + 1):
            cc = coeffs.get((l, m, 'c'), 0.0)
            cs = coeffs.get((l, m, 's'), 0.0)
            if cc or cs:
                Ylm0 = sph_harm_y(l, m, theta, 0.0).real  # (nlat,) real at phi=0
                col = np.sqrt(2.0) * Ylm0
                if cc:
                    field += cc * np.outer(col, cosm[m])
                if cs:
                    field += cs * np.outer(col, sinm[m])
    return field


def _random_coeffs(lmax: int, power_fn, rng, lmin: int = 1) -> dict:
    """Draw an isotropic Gaussian random field's coefficients: a_lm ~ N(0, sqrt(C_l/(2l+1))).

    power_fn(l) is the degree power C_l. A red spectrum (power falling with l) is what makes
    terrain look like terrain -- big landforms, fine detail, self-similar between.
    """
    out = {}
    for l in range(lmin, lmax + 1):
        sigma = np.sqrt(max(power_fn(l), 0.0) / (2 * l + 1))
        if sigma <= 0:
            continue
        out[(l, 0, 'c')] = float(rng.normal(0, sigma))
        for m in range(1, l + 1):
            out[(l, m, 'c')] = float(rng.normal(0, sigma))
            out[(l, m, 's')] = float(rng.normal(0, sigma))
    return out


# --- the onion -------------------------------------------------------------


@dataclass
class PlanetOnion:
    """A planet as nested height-map membranes, children stored RELATIVE to their parents.

    Two SH coefficient banks ARE the stored planet:
        cont_coeffs   low-degree continent potential -> the two-crust bimodal base
        rough_coeffs  full-degree red-spectrum roughness -> mountains and ridges
    Elevation is a bimodal transfer of the continent potential (ocean floor vs land platform,
    with a continental-shelf slope between) plus roughness, amplified on land. The layer
    thicknesses below the surface are RELATIVE fields; radius_of composes parent minus them.
    """
    radius: float = R_EARTH
    lmax: int = 40
    cont_lmax: int = 6
    cont_coeffs: dict = field(default_factory=dict)
    rough_coeffs: dict = field(default_factory=dict)
    sea_thr: float = 0.0                  # continent-potential threshold for sea level
    shelf_w: float = 0.18                 # width of the continental-shelf transition (steep margins)
    rough_amp: float = 1700.0             # m, RMS roughness scale
    # per-layer relative thickness fields, keyed by layer name -> ndarray(nlat,nlon) or scalar
    thickness: dict = field(default_factory=dict)
    _grid: tuple = None                   # (nlat, nlon, elevation_grid) cache
    _dem: np.ndarray = None               # a loaded REAL heightmap; resampled, never synthesized over

    # --- construction ------------------------------------------------------

    @classmethod
    def earthlike(cls, seed: int = 0, lmax: int = 40,
                  land_fraction: float = EARTH_LAND_FRACTION) -> 'PlanetOnion':
        """Seed an Earth-REALISTIC planet: two-crust bimodal hypsometry + red roughness.
        land_fraction tunes how much of the sphere is above sea level (raise it for a
        land-rich, less ocean-dominated world)."""
        rng = np.random.default_rng(seed)
        self = cls(lmax=lmax)
        # continents: a few large highs/lows (low degree). Unit-ish variance.
        self.cont_coeffs = _random_coeffs(self.cont_lmax, lambda l: 1.0 / l**2, rng)
        # roughness: red spectrum C_l ~ l^-2 across all degrees.
        self.rough_coeffs = _random_coeffs(lmax, lambda l: 1.0 / l**2, rng)
        self.thickness = {nm: d for nm, d in LAYERS if nm != 'surface'}
        self._tune_sea_level(land_fraction)
        return self

    # --- the surface field -------------------------------------------------

    def _grid_angles(self, nlat: int, nlon: int):
        lat = np.linspace(np.pi / 2, -np.pi / 2, nlat)      # +90..-90, radians
        lon = np.linspace(0, 2 * np.pi, nlon, endpoint=False)
        return lat, lon

    def elevation_grid(self, nlat: int = 180, nlon: int = 360, force: bool = False):
        """Synthesize the WHOLE surface at once -- the outer membrane. Cached. If a REAL DEM was
        loaded, RESAMPLE it to the requested resolution instead of synthesizing (so the real
        Earth survives whatever resolution biomes/layers/render ask for)."""
        if self._grid and self._grid[0] == nlat and self._grid[1] == nlon and not force:
            return self._grid[2]
        if self._dem is not None:
            elev = _resample_grid(self._dem, nlat, nlon)
            self._grid = (nlat, nlon, elev)
            return elev
        lat, lon = self._grid_angles(nlat, nlon)
        pot = _synth(self.cont_coeffs, self.cont_lmax, lat, lon)
        pot = pot / (np.std(pot) + 1e-12)                    # normalize the potential
        rough = _synth(self.rough_coeffs, self.lmax, lat, lon)
        rough = rough / (np.std(rough) + 1e-12)
        elev = self._elev_from(pot, rough)
        self._grid = (nlat, nlon, elev)
        return elev

    def _elev_from(self, pot, rough):
        """Bimodal transfer: continent potential -> two crust levels with a shelf slope, plus
        roughness amplified on land. This is where Earth's bimodal hypsometry comes from -- it
        is the two-crust structure, not a tuned histogram."""
        s = 1.0 / (1.0 + np.exp(-(pot - self.sea_thr) / self.shelf_w))   # 0=ocean .. 1=land
        base = EARTH_OCEAN_MODE * (1 - s) + EARTH_LAND_MODE * s
        land_amp = 0.12 + 0.88 * s                           # abyssal plains flat, mountains on land
        return base + self.rough_amp * rough * land_amp

    def _tune_sea_level(self, target_land: float, nlat: int = 120, nlon: int = 240):
        """Shift the sea-level threshold until the area-weighted land fraction hits target."""
        lat, lon = self._grid_angles(nlat, nlon)
        pot = _synth(self.cont_coeffs, self.cont_lmax, lat, lon)
        pot = pot / (np.std(pot) + 1e-12)
        rough = _synth(self.rough_coeffs, self.lmax, lat, lon)
        rough = rough / (np.std(rough) + 1e-12)
        w = np.cos(lat)[:, None] * np.ones((1, nlon))        # cell area weight
        lo, hi = -3.0, 3.0
        for _ in range(40):                                  # bisection on the threshold
            self.sea_thr = 0.5 * (lo + hi)
            land = ((self._elev_from(pot, rough) > 0) * w).sum() / w.sum()
            if land > target_land:
                lo = self.sea_thr                            # too much land -> raise threshold
            else:
                hi = self.sea_thr
        self._grid = None

    # --- the onion: radius of each layer, composed parent - relative -------

    def radius_of(self, layer: str, elev: np.ndarray) -> np.ndarray:
        """Absolute radius of a layer's LOWER boundary = planet radius + surface elevation,
        minus the RELATIVE thicknesses of every layer down to and including it. Because the
        thicknesses are relative, editing `elev` (the base) moves every layer together --
        the invariant, in one line."""
        r = self.radius + elev
        if layer == 'surface':
            return r
        for nm, _ in LAYERS[1:]:
            r = r - self._thick(nm, elev.shape)
            if nm == layer:
                break
        return r

    def _thick(self, layer: str, shape) -> np.ndarray:
        t = self.thickness.get(layer, 0.0)
        return t if np.ndim(t) else np.full(shape, float(t))

    # --- adjustment: the algorithms on the sphere --------------------------

    def uplift(self, lat_deg: float, lon_deg: float, radius_deg: float, amount_m: float):
        """Raise (or lower) a region of the BASE surface -- a coefficient-free local edit that
        rides on the cached grid. Every layer below follows because they are relative."""
        elev = self.elevation_grid().copy()
        nlat, nlon = elev.shape
        lat = np.linspace(90, -90, nlat)[:, None]
        lon = np.linspace(0, 360, nlon, endpoint=False)[None, :]
        d = np.sqrt((lat - lat_deg) ** 2 + (np.minimum(np.abs(lon - lon_deg),
                                                        360 - np.abs(lon - lon_deg))) ** 2)
        self._grid = (nlat, nlon, elev + amount_m * np.exp(-(d ** 2) / (2 * radius_deg ** 2)))

    def scale_relief(self, factor: float):
        """Scale roughness (mountains) while keeping the continents -- a parent-level edit."""
        for k in self.rough_coeffs:
            self.rough_coeffs[k] *= factor
        self._grid = None

    def truncate_lod(self, max_degree: int):
        """LOD: drop all detail above a degree. Coarser membrane, same continents. This is the
        onion getting shallower -- depth() of the surface membrane in SH terms."""
        self.lmax = min(self.lmax, max_degree)
        self.rough_coeffs = {k: v for k, v in self.rough_coeffs.items() if k[0] <= max_degree}
        self._grid = None

    # --- the invariant: affect the parent, don't break the child -----------

    def check_nesting(self, elev: np.ndarray = None) -> dict:
        """Every layer boundary must sit below the one above it, everywhere. This is what
        "doesn't break the child" MEANS, made checkable."""
        if elev is None:
            elev = self.elevation_grid()
        radii = [self.radius_of(nm, elev) for nm, _ in LAYERS]
        violations = 0
        for a, b in zip(radii, radii[1:]):
            violations += int((b > a + 1e-6).sum())          # inner above outer = broken
        return {'nesting_ok': violations == 0, 'violations': int(violations)}

    def witness_invariant(self, uplift_m: float = 8000.0) -> dict:
        """PROVE the representation is what preserves the child. Do a violent base edit, then
        compare RELATIVE layers (carried) against an ABSOLUTE counterfactual (shattered)."""
        base = self.elevation_grid().copy()
        before = self.check_nesting(base)
        # relative: uplift the base; radius_of recomposes, children ride up.
        self.uplift(0.0, 0.0, 12.0, uplift_m)
        after_rel = self.check_nesting()
        # absolute counterfactual: layers pinned at their pre-edit radii, only surface moves.
        elev2 = self.elevation_grid()
        surf2 = self.radius + elev2
        abs_topsoil = (self.radius + base) - self._thick('topsoil', base.shape)  # frozen
        abs_violations = int((surf2 > abs_topsoil + 1e-6).sum())
        self._grid = (base.shape[0], base.shape[1], base)    # restore
        return {
            'before': before,
            'relative_after_uplift': after_rel,
            'absolute_counterfactual_violations': abs_violations,
        }

    # --- the connection point: the stud every object grows from ------------

    def sample(self, lat_deg: float, lon_deg: float) -> dict:
        """Surface elevation, outward normal, and top material layer at a point -- the stud an
        object's morphogenesis attaches to. Bilinear on the cached whole-sphere grid."""
        elev = self.elevation_grid()
        nlat, nlon = elev.shape
        fi = (90 - lat_deg) / 180 * (nlat - 1)
        fj = (lon_deg % 360) / 360 * nlon
        i0, j0 = int(np.clip(fi, 0, nlat - 2)), int(fj) % nlon
        di, dj = fi - i0, fj - j0
        j1 = (j0 + 1) % nlon
        h = (elev[i0, j0] * (1 - di) * (1 - dj) + elev[i0, j1] * (1 - di) * dj
             + elev[i0 + 1, j0] * di * (1 - dj) + elev[i0 + 1, j1] * di * dj)
        # normal from local gradient (a real slope, in metres per degree -> per metre)
        gi = (elev[min(i0 + 1, nlat - 1), j0] - elev[max(i0 - 1, 0), j0])
        gj = (elev[i0, j1] - elev[i0, (j0 - 1) % nlon])
        mperdeg = np.pi / 180 * self.radius
        n = np.array([-gj / mperdeg, -gi / mperdeg, 1.0])
        n = n / np.linalg.norm(n)
        return {'elevation': float(h), 'radius': float(self.radius + h),
                'normal': n, 'material': 'ocean' if h <= 0 else 'topsoil',
                'above_sea': float(h)}

    # --- instance the membrane primitive: the onion IS nested membranes ----

    def to_membranes(self):
        """Build the core/membranes.py hierarchy: planet -> surface -> ... -> core, each a
        child (relative origin), so address = path and LOD = depth come for free."""
        from core import membranes as M
        planet = M.Membrane('planet', scale=self.radius, serial='P-earthlike')
        planet.prop(radius_m=self.radius, land_fraction=self.measure()['land_fraction'])
        parent = planet
        for nm, _ in LAYERS:
            child = parent.add(M.Membrane(nm, scale=self.radius, serial=f'L-{nm}'))
            child.prop(relative_thickness_m=self.thickness.get(nm, 0.0))
            parent = child
        return planet

    # --- measurement: Earth-realism, in facts ------------------------------

    def measure(self) -> dict:
        elev = self.elevation_grid()
        nlat, nlon = elev.shape
        lat = np.linspace(90, -90, nlat)
        w = np.cos(np.radians(lat))[:, None] * np.ones((1, nlon))
        wf = w / w.sum()
        land = float((elev > 0).astype(float).__mul__(wf).sum())
        ocean = elev[elev <= 0]
        landv = elev[elev > 0]
        # bimodality coefficient b = (skew^2 + 1)/kurtosis; > 0.555 => bimodal.
        e = elev.ravel()
        mu, sd = e.mean(), e.std() + 1e-12
        z = (e - mu) / sd
        skew, kurt = float((z**3).mean()), float((z**4).mean())
        bimod = (skew**2 + 1) / max(kurt, 1e-6)
        inv = self.check_nesting(elev)
        return {
            'land_fraction': land,
            'ocean_mode_m': float(np.median(ocean)) if ocean.size else 0.0,
            'land_mode_m': float(np.median(landv)) if landv.size else 0.0,
            'relief_m': float(elev.max() - elev.min()),
            'bimodality_coeff': float(bimod),
            'nesting_ok': inv['nesting_ok'],
        }

    # --- the real-data seam ------------------------------------------------

    def from_topo_grid(self, elev: np.ndarray):
        """Load a REAL heightmap (equirectangular metres, lat 90..-90 top-to-bottom) as the
        surface, upgrading the seed without changing the rung. Stored as the DEM and resampled
        to any requested resolution; the onion, adjust ops, invariant, biomes, layers, mining
        and the verbs all run on it because they read elevation_grid()."""
        self._dem = np.asarray(elev, float)
        self._grid = (self._dem.shape[0], self._dem.shape[1], self._dem)
        return self


def _resample_grid(grid: np.ndarray, nlat: int, nlon: int) -> np.ndarray:
    """Bilinear resample an equirectangular grid to (nlat, nlon) -- so a loaded DEM survives
    whatever resolution the stack asks for."""
    H, W = grid.shape
    if (H, W) == (nlat, nlon):
        return grid
    yi = np.linspace(0, H - 1, nlat)
    xi = np.linspace(0, W - 1, nlon)
    y0 = np.floor(yi).astype(int); y1 = np.minimum(y0 + 1, H - 1)
    x0 = np.floor(xi).astype(int); x1 = np.minimum(x0 + 1, W - 1)
    fy = (yi - y0)[:, None]; fx = (xi - x0)[None, :]
    top = grid[np.ix_(y0, x0)] * (1 - fx) + grid[np.ix_(y0, x1)] * fx
    bot = grid[np.ix_(y1, x0)] * (1 - fx) + grid[np.ix_(y1, x1)] * fx
    return top * (1 - fy) + bot * fy


def load_dem(path, radius: float = R_EARTH, seed: int = 0) -> 'PlanetOnion':
    """Load a REAL equirectangular elevation DEM (metres, lat 90..-90 top-to-bottom, lon 0..360)
    as a planet. Accepts .npy / .npz (key 'elevation' or first array) / .txt / .csv. The WHOLE
    stack -- biomes, layers, mining, the verbs -- then runs on the real planet, because
    from_topo_grid feeds the same onion the synthesis did.

    THIS is the seam the operator asked for: drop a real Earth DEM (GEBCO/ETOPO sub-sampled to an
    equirectangular metres grid, saved as .npy) here and the game IS the actual Earth. A binary
    DEM cannot be fetched from a headless session -- the file is the operator's to provide; the
    load is one call and everything downstream is unchanged."""
    from pathlib import Path
    p = Path(path)
    if p.suffix == '.npy':
        elev = np.load(p)
    elif p.suffix == '.npz':
        z = np.load(p)
        elev = z['elevation'] if 'elevation' in z.files else z[z.files[0]]
    else:
        elev = np.loadtxt(p, delimiter=',' if p.suffix == '.csv' else None)
    elev = np.asarray(elev, float)
    if elev.ndim != 2:
        raise ValueError(f'DEM must be a 2-D equirectangular grid; got shape {elev.shape}')
    onion = PlanetOnion.earthlike(seed=seed)         # a valid onion (layers, thicknesses)
    onion.radius = radius
    return onion.from_topo_grid(elev)


def _hillshade(elev, mperdeg):
    gy, gx = np.gradient(elev)
    nx, ny = -gx / mperdeg, -gy / mperdeg
    nz = np.ones_like(elev)
    nrm = np.stack([nx, ny, nz], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    ldir = np.array([-0.5, -0.5, 0.7]); ldir /= np.linalg.norm(ldir)
    return np.clip(nrm @ ldir, 0, 1)


def _main() -> int:
    import argparse
    import sys
    import time
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='the planet as an onion of height-map membranes')
    ap.add_argument('--seed', type=int, default=3)
    ap.add_argument('--render', action='store_true')
    a = ap.parse_args()

    t0 = time.time()
    p = PlanetOnion.earthlike(seed=a.seed)
    p.elevation_grid()                                       # force the whole-sphere synth
    dt = time.time() - t0

    m = p.measure()
    print(f"  synthesized a whole-sphere planet in {dt:.1f}s (SH lmax={p.lmax})\n")
    print("  === Earth-realism (measured vs Earth's real numbers) ===")
    print(f"  {'land fraction':22} {m['land_fraction']:.3f}   (Earth {EARTH_LAND_FRACTION})")
    print(f"  {'ocean modal depth':22} {m['ocean_mode_m']:>8.0f} m (Earth ~{EARTH_OCEAN_MODE:.0f})")
    print(f"  {'land modal height':22} {m['land_mode_m']:>8.0f} m (Earth ~{EARTH_LAND_MODE:.0f})")
    print(f"  {'relief (max-min)':22} {m['relief_m']:>8.0f} m (Earth ~19800: Everest+Mariana)")
    print(f"  {'bimodality coeff':22} {m['bimodality_coeff']:.3f}   (>0.555 => bimodal, Earth's signature)")

    print("\n  === the invariant: affect the parent, don't break the child ===")
    w = p.witness_invariant(uplift_m=8000.0)
    print(f"  before any edit:           nesting_ok={w['before']['nesting_ok']}")
    print(f"  RELATIVE, after +8km uplift: nesting_ok={w['relative_after_uplift']['nesting_ok']}"
          f"  <- children rode up with the base")
    print(f"  ABSOLUTE counterfactual:     {w['absolute_counterfactual_violations']:,} broken cells"
          f"  <- surface punched through frozen topsoil")

    print("\n  === the onion as addressable membranes (LOD = depth) ===")
    root = p.to_membranes()
    for d, mem in root.walk():
        print("    " + "  " * d + f"{mem.path()}  depth={mem.depth()}")

    print("\n  === a connection point (the stud an object grows from) ===")
    for (la, lo) in [(0, 0), (45, 200), (-60, 300)]:
        s = p.sample(la, lo)
        print(f"    ({la:+3},{lo:3}) -> elev {s['elevation']:>7.0f} m  "
              f"material {s['material']:7}  up={np.round(s['normal'], 3)}")

    if a.render:
        from pathlib import Path
        try:
            from PIL import Image
        except Exception:
            print('\n  (PIL absent -- skipping render)'); return 0
        elev = p.elevation_grid(360, 720, force=True)
        mperdeg = np.pi / 180 * p.radius
        # (1) hypsometric-tinted equirectangular map
        rgb = np.zeros((*elev.shape, 3), np.uint8)
        sea = elev <= 0
        depth = np.clip(-elev / 6000, 0, 1)
        rgb[..., 2] = np.where(sea, (120 + 100 * (1 - depth)).astype(np.uint8), rgb[..., 2])
        rgb[..., 1] = np.where(sea, (60 + 90 * (1 - depth)).astype(np.uint8), rgb[..., 1])
        h = np.clip(elev / 5000, 0, 1)
        shade = _hillshade(elev, mperdeg)
        land_r = (120 + 100 * h) * (0.5 + 0.5 * shade)
        land_g = (110 + 60 * h) * (0.5 + 0.5 * shade)
        land_b = (80 + 40 * h) * (0.5 + 0.5 * shade)
        rgb[..., 0] = np.where(~sea, np.clip(land_r, 0, 255).astype(np.uint8), rgb[..., 0])
        rgb[..., 1] = np.where(~sea, np.clip(land_g, 0, 255).astype(np.uint8), rgb[..., 1])
        rgb[..., 2] = np.where(~sea, np.clip(land_b, 0, 255).astype(np.uint8), rgb[..., 2])
        out = Path('Saved/SplatEmit'); out.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgb).save(out / 'planet_membrane_map.png')
        # (2) orthographic globe (the outer membrane, whole)
        N = 400
        yy, xx = np.mgrid[0:N, 0:N]
        X = (xx - N / 2) / (N / 2); Y = (N / 2 - yy) / (N / 2)
        disc = X**2 + Y**2 <= 1
        Z = np.sqrt(np.clip(1 - X**2 - Y**2, 0, 1))
        latg = np.degrees(np.arcsin(np.clip(Y, -1, 1)))
        long = np.degrees(np.arctan2(X, Z)) % 360
        glr = np.zeros((N, N, 3), np.uint8)
        ii = np.clip(((90 - latg) / 180 * (elev.shape[0] - 1)), 0, elev.shape[0] - 1).astype(int)
        jj = np.clip((long / 360 * elev.shape[1]), 0, elev.shape[1] - 1).astype(int)
        glr[disc] = rgb[ii[disc], jj[disc]]
        Image.fromarray(glr).save(out / 'planet_membrane_globe.png')
        # (3) the onion cross-section along a meridian (deep + near-surface zoom)
        cs = np.zeros((300, 600, 3), np.uint8) + 20
        lat = np.linspace(90, -90, 600)
        el = p.sample  # per-point sample along lon=0
        elm = np.array([el(la, 0)['elevation'] for la in lat])
        cols = {'surface': (230, 230, 255), 'topsoil': (120, 90, 60), 'subsoil': (150, 120, 70),
                'bedrock': (110, 110, 120), 'crust': (90, 80, 90)}
        for k, (nm, _) in enumerate(LAYERS[:5]):
            r0 = 40 + k * 8
            span = float(np.ptp(elm))
            y = (150 - (elm / span * 60 if span else 0)).astype(int) + r0
            for x in range(600):
                cs[np.clip(y[x], 0, 299), x] = cols.get(nm, (80, 80, 80))
        Image.fromarray(cs).save(out / 'planet_membrane_onion.png')
        print(f"\n  wrote 3 renders to {out}/planet_membrane_*.png "
              f"(map | globe | onion cross-section)")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
