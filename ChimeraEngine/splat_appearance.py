"""splat_appearance.py -- THE APPEARANCE as a Gaussian-splat MOVIE (beginning -> end), via ParticleEngine.

The mandatory visual test judges the REAL engine render, not a diagram; and a term is a SLICE of the
timeline UNFOLDING, so the appearance is a MOVIE: a scene rendered at its BEGINNING (t=0) and its END
(settled). Two ends of the dial. The physics (the agent) owns this; the human side reads it.

Two scene KINDS, because different matter renders differently (no aesthetic passes -- the look DERIVES
from what the thing IS):

  * "collapse" -- a diffuse body of one colour drawn together by a central attractor. Correct for a
    STAR or a dust cloud: plasma and dust ARE diffuse. begin = dispersed, end = coalesced.
  * "planet"   -- a SOLID world. Splats are placed ON a sphere shell (Fibonacci distribution) and
    painted by surface type: deep OCEANS, continent-noise LAND, polar ICE caps, wrapped in a faint
    ATMOSPHERE halo. Depth-sorted opaque compositing gives a crisp limb -- a world seen from space,
    not a fog ball. begin = the world ACCRETING from its own cloud of dust, end = the settled sphere.

Terms with a scene render as splats; terms without one return None (the engine falls back to the
matplotlib placeholder until their scene is authored). Needs the GPU (Numba CUDA) -- rendering is
physics, so it belongs to the same hardware. Deterministic: the RNG is seeded from the term name, so
a term renders byte-identically every time (same seed, same world, forever).
"""
from __future__ import annotations

import sys
import zlib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# term -> scene spec.
#   collapse: a particle body of a colour, drawn together by a central attractor as it evolves.
#   planet:   a solid habitable sphere (radius in world units; ocean = fraction of the surface that is sea).
SCENES = {
    "theStar":        {"kind": "collapse", "type": "atmosphere", "count": 7000, "spread": 55, "size": 3.4,
                       "color": (1.0, 0.93, 0.82, 1.0), "pull": 1.4, "cam": (0.0, -210.0, 26.0)},
    "aPlanet":        {"kind": "planet", "radius": 88.0, "ocean": 0.66, "cam": (0.0, -250.0, 40.0)},
    "thePlanets":     {"kind": "row", "span": 500.0, "cam": (0.0, -520.0, 55.0),
                       "planets": [((1.00, 0.28, 0.12), 30.0),   # molten red   (hottest)
                                   ((1.00, 0.52, 0.16), 30.0),   # orange
                                   ((0.92, 0.80, 0.42), 30.0),   # warm tan
                                   ((0.32, 0.60, 0.52), 30.0),   # temperate blue-green
                                   ((0.24, 0.42, 0.85), 30.0),   # cold blue
                                   ((0.90, 0.95, 1.00), 30.0)]},  # frozen white (coldest)
    "theSolarSystem": {"kind": "system", "cam": (0.0, -400.0, 230.0)},
}

# ── the particle buffer layout the pipeline reads (ParticleEngine.core.COL) ──
NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA, SIZE = 16, 17, 18, 19, 20
NX, NY, NZ = 21, 22, 23     # OPTIONAL surface normal -> the pipeline back-face-culls occluded grains (0,0,0 = no cull)

# ── ONE calibration, shared by every solid-sphere scene ──
# A dense splat shell over-accumulates ~2x: overlapping Gaussian tails sum before the opacity
# saturates (MEASURED -- a uniform (0.05,0.15,0.45) navy sphere rendered (0.20,0.58,0.95) cyan-white).
# The transfer is ~proportional per channel, so we invert it: pre-multiply surface colours by the gain
# so the render lands on the intended palette. Keeping GRAIN size/alpha/DENSITY constant across scenes
# keeps the over-accumulation factor constant, so the ONE measured gain holds for every world.
_SURFACE_GAIN = 0.45      # invert the measured ~2x over-accumulation (translucent shells: _solid_sphere/theStar)
_PLANET_GAIN = (0.420, 0.409, 0.405)   # aPlanet surface: OPAQUE (alpha 0.92) + SMALL grains (3.5) + BACK-FACE CULL.
                          # Culling the far hemisphere removes its bleed-through, so over-accumulation drops ~3.0x -> ~2.4x;
                          # re-MEASURED per-channel against a uniform navy sphere WITH culling active (err 0,0,0 on target).
_GRAIN_SIZE = 5.0         # per-grain render size (world units)
_GRAIN_ALPHA = 0.5        # per-grain opacity
_GRAIN_DENSITY = 0.185    # grains per unit sphere AREA (= aPlanet's 18000 / 4pi*88^2)


def _seed(term: str) -> int:
    """A stable per-term seed -- deterministic across processes (hash() is salted; zlib.crc32 is not)."""
    return zlib.crc32(term.encode("utf-8")) & 0x7FFFFFFF


def _fibonacci_sphere(n: int) -> "any":
    """n unit vectors spread evenly over the sphere (the golden-angle spiral). Deterministic."""
    import numpy as np
    i = np.arange(n, dtype=np.float64)
    z = 1.0 - 2.0 * (i + 0.5) / n                 # -1..1, even in area
    r = np.sqrt(np.clip(1.0 - z * z, 0.0, 1.0))
    theta = np.pi * (1.0 + 5.0 ** 0.5) * i        # golden angle
    return np.stack([r * np.cos(theta), r * np.sin(theta), z], axis=1)


def _fbm(dirs, rng, octaves: int = 4):
    """Smooth blobby noise over unit directions -> continents, not speckle. Range ~ -1..1."""
    import numpy as np
    val = np.zeros(len(dirs)); total = 0.0; amp = 1.0
    for o in range(octaves):
        freq = 1.15 * (1.9 ** o)                  # low freqs first -> a few big land masses
        for _ in range(2):                        # two waves/octave for isotropy
            k = rng.normal(size=3); k /= (np.linalg.norm(k) + 1e-9)
            phase = rng.uniform(0.0, 2.0 * np.pi)
            val += amp * np.sin(freq * np.pi * (dirs @ k) + phase)
            total += amp
        amp *= 0.55
    return val / max(total, 1e-9)


def _planet_buffers(spec: dict, term: str):
    """Build (end_buffer, begin_buffer) for a solid world: surface shell + atmosphere halo."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec["radius"])
    ocean_frac = float(spec.get("ocean", 0.66))

    # ── SURFACE: an even shell of opaque splats ──
    n_s = 40000                                                     # MORE, SMALLER grains: fills the shell with no lattice while
                                                                     # each grain covers ~8x less area than SIZE 9 -> ~8x less overdraw
    dirs = _fibonacci_sphere(n_s)                                    # (n,3) unit
    z = dirs[:, 2]                                                   # latitude sine
    surf = np.zeros((n_s, NCOLS), dtype=np.float32)
    jitter = 1.0 + rng.normal(0.0, 0.006, n_s)                      # a touch of shell thickness
    surf[:, PX:PZ + 1] = dirs * (R * jitter[:, None])
    surf[:, NX:NZ + 1] = dirs                                       # outward normal = the shell direction -> back-face cull the far side
    surf[:, TYPE] = 3.0                                             # "social": sm=1.0, opaque, isotropic -> clean round grains
    surf[:, ALPHA] = 0.92                                           # OPAQUE surface: line-of-sight stops here (Nanite-style). The
                                                                     # front-to-back early-out (trans<0.01) now fires after ~2 grains,
                                                                     # so the ~24 grains BEHIND the visible surface are never composited.
    surf[:, SIZE] = 3.5                                             # SMALL grains: projected ~15px (was ~42px) -> ~8x less overdraw,
                                                                     # the dominant render cost. 40k of them still fill the shell (gap 0, measured).

    # classify each grain: ICE at the poles, else LAND vs OCEAN by continent noise
    land_noise = _fbm(dirs, rng)
    thresh = np.quantile(land_noise, ocean_frac)                   # top (1-ocean) fraction becomes land
    is_land = land_noise > thresh
    is_ice = np.abs(z) > 0.88                                       # small polar caps override (lat > ~62 deg)
    is_land &= ~is_ice
    is_ocean = ~is_land & ~is_ice

    # ocean: DEEP navy, a shade lighter/greener in the shallows (a second noise = depth)
    depth = 0.5 + 0.5 * _fbm(dirs, rng)                            # 0..1
    surf[is_ocean, CR] = 0.02 + 0.04 * depth[is_ocean]
    surf[is_ocean, CG] = 0.08 + 0.12 * depth[is_ocean]
    surf[is_ocean, CB] = 0.30 + 0.22 * depth[is_ocean]            # -> (0.02,0.08,0.30) abyss to (0.06,0.20,0.52) shelf (navy)
    # land: vivid equatorial green -> mid-latitude arid tan (aridity from |lat| + noise)
    aridity = np.clip(np.abs(z) * 0.9 + 0.30 * _fbm(dirs, rng), 0.0, 1.0)
    surf[is_land, CR] = 0.13 + 0.34 * aridity[is_land]
    surf[is_land, CG] = 0.44 - 0.12 * aridity[is_land]
    surf[is_land, CB] = 0.12 + 0.05 * aridity[is_land]           # -> (0.13,0.44,0.12) jungle to (0.47,0.32,0.17) desert
    # ice: near-white with a cold blue tint
    surf[is_ice, CR] = 0.90; surf[is_ice, CG] = 0.93; surf[is_ice, CB] = 0.97

    surf[:, CR:CB + 1] *= _PLANET_GAIN                             # opaque surface => ~no over-accumulation, so show TRUE colors (gain~1)

    # ── ATMOSPHERE: a faint pale-blue halo -- thin enough to glow at the LIMB without hazing the disk ──
    n_a = 1800
    adirs = _fibonacci_sphere(n_a)
    atm = np.zeros((n_a, NCOLS), dtype=np.float32)
    atm[:, PX:PZ + 1] = adirs * (R * 1.05)
    atm[:, TYPE] = 5.0                                             # "atmosphere": sm=6.0 -> big soft blobs
    atm[:, CR] = 0.36; atm[:, CG] = 0.56; atm[:, CB] = 0.90
    atm[:, ALPHA] = 0.05
    atm[:, SIZE] = 1.2

    end = np.concatenate([surf, atm], axis=0)

    # ── BEGIN: the world ACCRETING -- its own grains flung out into a dust cloud that will condense ──
    begin = end.copy()
    spread = R * (1.4 + 2.2 * rng.random(len(begin)))             # push each grain radially outward
    tang = rng.normal(0.0, R * 0.5, (len(begin), 3))             # + tangential scatter -> a cloud
    ndir = end[:, PX:PZ + 1] / (np.linalg.norm(end[:, PX:PZ + 1], axis=1, keepdims=True) + 1e-9)
    begin[:, PX:PZ + 1] = ndir * spread[:, None] + tang
    return end, begin


def _solid_sphere(center, radius, color, rng, gain: float = _SURFACE_GAIN):
    """A solid opaque sphere of one colour at `center` -- the reusable body (calibrated over-accumulation)."""
    import numpy as np
    n = max(500, int(_GRAIN_DENSITY * 4.0 * np.pi * radius * radius))
    dirs = _fibonacci_sphere(n)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    jit = 1.0 + rng.normal(0.0, 0.006, n)
    b[:, PX:PZ + 1] = np.asarray(center, np.float32) + dirs * (radius * jit[:, None])
    b[:, TYPE] = 3.0
    b[:, ALPHA] = _GRAIN_ALPHA
    b[:, SIZE] = _GRAIN_SIZE
    b[:, CR] = color[0] * gain; b[:, CG] = color[1] * gain; b[:, CB] = color[2] * gain
    return b


def _halo(center, radius, color, rng, alpha: float = 0.09, size: float = 1.8, n: int | None = None):
    """A faint soft glow shell (atmosphere type = big soft blobs) -- a limb/atmosphere/star glow."""
    import numpy as np
    if n is None:
        n = max(300, int(0.06 * 4.0 * np.pi * radius * radius))
    dirs = _fibonacci_sphere(n)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, PX:PZ + 1] = np.asarray(center, np.float32) + dirs * radius
    b[:, TYPE] = 5.0                                               # atmosphere: sm=6.0 -> big soft blobs
    b[:, CR] = color[0]; b[:, CG] = color[1]; b[:, CB] = color[2]
    b[:, ALPHA] = alpha; b[:, SIZE] = size
    return b


def _orbit_ring(radius, rng, color=(0.42, 0.42, 0.48), n: int = 900):
    """A thin ring of dust in the z=0 orbital plane -- an ORBIT drawn as splats."""
    import numpy as np
    th = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, PX] = radius * np.cos(th)
    b[:, PY] = radius * np.sin(th)
    b[:, PZ] = rng.normal(0.0, 1.5, n)                            # a thin band, not a wire
    b[:, TYPE] = 3.0
    b[:, CR] = color[0]; b[:, CG] = color[1]; b[:, CB] = color[2]
    b[:, ALPHA] = 0.5; b[:, SIZE] = 2.4
    return b


def _row_buffers(spec: dict, term: str):
    """thePlanets: a ROW of solid worlds, hot colours on one side -> cold on the other (a temperature gradient)."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    planets = spec["planets"]                                     # [(color, radius), ...] hot -> cold
    span = float(spec.get("span", 500.0))
    xs = np.linspace(-span / 2.0, span / 2.0, len(planets))
    parts = []
    for (color, radius), x in zip(planets, xs):
        parts.append(_solid_sphere((x, 0.0, 0.0), radius, color, rng))
        if color[0] > 0.75 and color[2] < 0.4:                   # a HOT world -> a molten glow so it reads as hot
            parts.append(_halo((x, 0.0, 0.0), radius * 1.18, (0.95, 0.35, 0.12), rng, alpha=0.11, size=1.7))
    end = np.concatenate(parts, axis=0)
    begin = end.copy()
    begin[:, PX:PZ + 1] += rng.normal(0.0, 55.0, (len(begin), 3))  # dispersed dust -> the worlds condense
    return end, begin


def _system_buffers(spec: dict, term: str):
    """theSolarSystem: the brightest thing (the STAR) at the centre, with planets on ORBIT rings around it."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    parts = [
        _solid_sphere((0.0, 0.0, 0.0), 34.0, (1.0, 0.93, 0.78), rng, gain=0.85),  # the star: brightest, central
        _halo((0.0, 0.0, 0.0), 48.0, (1.0, 0.82, 0.5), rng, alpha=0.11, size=2.4),
    ]
    rings = [(85.0, (0.62, 0.45, 0.34)), (150.0, (0.34, 0.55, 0.82)),
             (215.0, (0.70, 0.62, 0.42)), (280.0, (0.78, 0.86, 0.95))]           # a planet's colour per orbit
    angles = [0.7, 2.3, 3.9, 5.3]
    for (r, pcolor), a in zip(rings, angles):
        parts.append(_orbit_ring(r, rng))
        parts.append(_solid_sphere((r * np.cos(a), r * np.sin(a), 0.0), 12.0, pcolor, rng))
    end = np.concatenate(parts, axis=0)
    begin = end.copy()
    begin[:, PX:PZ + 1] += rng.normal(0.0, 80.0, (len(begin), 3))  # a protoplanetary cloud -> star + orbits
    return end, begin


def project_movie(term: str, out_dir) -> dict | None:
    """Render `term`'s splat movie -> {"begin": path, "end": path}, or None if it has no scene.

    A term with a COMPOSITION renders from its PROVEN children (appearance from decomposition) -- that is
    now the DEFAULT for composite terms; hand-authored SCENES are the fallback for leaf terms."""
    comp = COMPOSITIONS.get(term)
    spec = SCENES.get(term)
    if not comp and not spec:
        return None
    import numpy as np
    from PIL import Image
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    cam_pos = comp["cam"] if comp else spec["cam"]               # composition owns its own camera
    cx, cy, cz = cam_pos                                          # AIM at the body (origin): yaw=0 looks +X
    yaw = float(np.arctan2(-cy, -cx))
    pitch = float(np.arctan2(-cz, float(np.hypot(cx, cy))))
    cam = FirstPersonCamera(cam_pos, yaw=yaw, pitch=pitch)
    p = cam.params(720, 540)
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))

    begin_png = out / f"movie_{term}_begin.png"
    end_png = out / f"movie_{term}_end.png"

    if comp:                                                     # DEFAULT for composite terms: built from proven children
        end_buf = compose_buffer(term)
        begin_buf = _disperse(end_buf, term, 90.0)
        pipe.upload(begin_buf)
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(begin_png)
        pipe.upload(end_buf)
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(end_png)
        return {"begin": str(begin_png), "end": str(end_png)}

    _BUILDERS = {"planet": _planet_buffers, "row": _row_buffers, "system": _system_buffers}
    builder = _BUILDERS.get(spec.get("kind"))
    if builder:
        # Two hand-built states, uploaded directly -- no physics kernel needed (these bodies are already settled).
        end_buf, begin_buf = builder(spec, term)
        pipe.upload(begin_buf)
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(begin_png)
        pipe.upload(end_buf)
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(end_png)
        return {"begin": str(begin_png), "end": str(end_png)}

    # ── collapse kind: spawn a body, let a central attractor draw it together over the timeline ──
    from ParticleEngine.core import ParticleSimulator, PARTICLE_TYPES
    from ParticleEngine.control_vars import default_physics_registry
    sim = ParticleSimulator(spec["count"] + 64)
    sim.spawn(spec["count"], spec["type"], position=(0, 0, 0), spread=float(spec["spread"]),
              color=spec["color"], size=float(spec["size"]), life=-1.0)
    pipe.upload(sim._data[:sim._count])
    pipe.attractors.append((0.0, 0.0, 0.0, float(spec["pull"]), PARTICLE_TYPES[spec["type"]], 500.0))
    reg = default_physics_registry()
    reg.set("gravity", (0.0, 0.0, 0.0))                          # SPACE: bodies float, they do not fall out of frame
    reg.set("wind_vector", (0.0, 0.0, 0.0))
    cvars = reg.snapshot()
    Image.fromarray(pipe.render_from_gpu(cam, p)).save(begin_png)
    for _ in range(90):                                          # evolve to the settled END state
        pipe.step_particles(1 / 60, cvars)
    Image.fromarray(pipe.render_from_gpu(cam, p)).save(end_png)
    return {"begin": str(begin_png), "end": str(end_png)}


def scene_terms() -> list:
    """The terms that have a splat scene (what the live viewer can show)."""
    return list(SCENES)


def scene_cam_distance(term: str) -> float:
    """How far the live viewer should orbit this term (from its still-camera distance)."""
    import numpy as np
    cam = (COMPOSITIONS.get(term) or SCENES.get(term) or {}).get("cam")
    return float(np.linalg.norm(cam)) if cam else 300.0


def scene_buffer(term: str):
    """The term's SETTLED 3D scene as a particle buffer (N,28) -- the real volume the live viewer orbits.

    The still `project_movie` renders two frames; the live viewer needs the settled body itself so it can
    turn it in real time (the time axis) and let the operator orbit it (verify it is a true 3D volume, not
    a flat disk). Solid scenes hand back their END buffer directly; a collapse scene is settled once here
    (spawn -> attractor -> 90 steps) and its particles returned."""
    if term in COMPOSITIONS:                                     # DEFAULT for composite terms: built from proven children
        return compose_buffer(term)
    spec = SCENES.get(term)
    if not spec:
        return None
    _BUILDERS = {"planet": _planet_buffers, "row": _row_buffers, "system": _system_buffers}
    builder = _BUILDERS.get(spec.get("kind"))
    if builder:
        return builder(spec, term)[0]                            # the settled END buffer
    # collapse: settle the body once and return its particles
    from ParticleEngine.core import ParticleSimulator, PARTICLE_TYPES
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.control_vars import default_physics_registry
    sim = ParticleSimulator(spec["count"] + 64)
    sim.spawn(spec["count"], spec["type"], position=(0, 0, 0), spread=float(spec["spread"]),
              color=spec["color"], size=float(spec["size"]), life=-1.0)
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    pipe.upload(sim._data[:sim._count])
    pipe.attractors.append((0.0, 0.0, 0.0, float(spec["pull"]), PARTICLE_TYPES[spec["type"]], 500.0))
    reg = default_physics_registry()
    reg.set("gravity", (0.0, 0.0, 0.0)); reg.set("wind_vector", (0.0, 0.0, 0.0))
    cvars = reg.snapshot()
    for _ in range(90):
        pipe.step_particles(1 / 60, cvars)
    return pipe.download_particles()


# ═══════════════════════════════════════════════════════════════════════
#  APPEARANCE FROM DECOMPOSITION -- a membrane's render built from its PROVEN children
#  (the LOD-of-meaning principle: each level is composed of the rung below it, so adding detail to the
#  STORY -- and proving it -- enriches the parent's render, no hand-authored scene. The child's own
#  matter supplies its APPEARANCE; the parent's LAYOUT supplies only WHERE each child sits, which is
#  structure -- a solar system's orbits -- not an aesthetic pass.)
# ═══════════════════════════════════════════════════════════════════════
COMPOSITIONS = {
    "theSolarSystem": {
        "cam": (0.0, -400.0, 230.0),
        "rings": [85.0, 150.0, 215.0, 280.0],
        # the REAL proven bodies, placed on the orbital plane (child, center, scale):
        "place": [("theStar", (0.0, 0.0, 0.0), 0.45),
                  ("aPlanet", (150.0, 0.0, 0.0), 0.13)],
    },
}


def _place(buf, center, scale: float):
    """Translate + scale a child's scene buffer into the parent's frame (positions AND grain size)."""
    import numpy as np
    b = np.array(buf, dtype=np.float32, copy=True)
    b[:, PX:PZ + 1] = b[:, PX:PZ + 1] * float(scale) + np.asarray(center, dtype=np.float32)
    b[:, SIZE] = b[:, SIZE] * float(scale)
    return b


def _disperse(buf, term: str, sigma: float):
    """Scatter a settled buffer into a 'before' cloud -- the movie's begin frame (the system accreting)."""
    import numpy as np
    rng = np.random.default_rng(_seed(term) ^ 0x9E3779B9)
    b = np.array(buf, dtype=np.float32, copy=True)
    b[:, PX:PZ + 1] += rng.normal(0.0, sigma, (len(b), 3))
    return b


def compose_buffer(term: str):
    """Build `term`'s scene from its PROVEN children -- appearance derived from the decomposition.

    Returns the composed (N,28) buffer, or None if the term has no layout. Each placed child is its OWN
    `scene_buffer` (the real proven matter -- the actual blue marble, the actual star), so the parent is
    literally made of its children. Rings are structure (the orbits), drawn as dust."""
    import numpy as np
    lay = COMPOSITIONS.get(term)
    if not lay:
        return None
    rng = np.random.default_rng(_seed(term))
    parts = [_orbit_ring(r, rng) for r in lay.get("rings", [])]
    for child, center, scale in lay.get("place", []):
        cb = scene_buffer(child)                                  # the child's own settled matter
        if cb is not None:
            parts.append(_place(cb, center, scale))
    return np.concatenate(parts, axis=0) if parts else None


if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else "theStar"
    import numpy as np
    from PIL import Image
    m = project_movie(term, Path(__file__).parent / "output")
    for k, v in (m or {}).items():
        arr = np.asarray(Image.open(v))
        print(f"  {k}: {v}  max_rgb={int(arr.max())}")
