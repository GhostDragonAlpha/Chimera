"""splat_appearance.py -- the bridge between story membranes and the ParticleEngine renderer.

Each membrane in story/ has a physics.py with derive() and emit(). This module:
  - Walks story/ to find all membranes with working emit() functions
  - Calls emit(nums, t) at the requested time t (0..1)
  - Returns (N, 28) float32 splat buffers ready for FullGPUPipeline.upload()
  - Caches to avoid re-importing and re-emitting on every frame

THE SPLIT: emit() returns the buffer in the membrane's OWN local units (radius ~1).
The renderer places the camera at a derived distance; scaling is the camera's job,
not the membrane's. This is why 41 orders of magnitude cost no precision.

Author: Agent (DeepSeek V4 Pro — density lane, 2026-08-04)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_HERE = Path(__file__).resolve().parent
_STORY = _HERE.parent / "story"
_CACHE: dict[str, np.ndarray] = {}          # term -> buffer (t=1.0, the settled state)
_TCACHE: dict[tuple[str, float], np.ndarray] = {}  # (term, t) -> buffer
_MODULES: dict[str, object] = {}             # term -> loaded module
_NUMBERS: dict[str, dict] = {}               # term -> numbers.json
# CONFIG: camera distances per term, computed from extent
_CAM_DIST: dict[str, float] = {}


def _load_module(folder: Path) -> object | None:
    """Import a membrane's physics.py as a module. Returns None if no law exists."""
    py = folder / "physics.py"
    if not py.exists():
        return None
    try:
        # Ensure story/ is in sys.path for imports like 'from matter import ...'
        if str(_STORY) not in sys.path:
            sys.path.insert(0, str(_STORY))
        spec = importlib.util.spec_from_file_location(f"membrane_{folder.name}", py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def _discover_membranes() -> dict[str, Path]:
    """Walk story/ and find every folder that has a physics.py with an emit() function."""
    found: dict[str, Path] = {}
    for folder in sorted(_STORY.iterdir()):
        if folder.is_dir() and not folder.name.startswith((".", "_")):
            _walk_folder(folder, found)
    return found


def _walk_folder(folder: Path, found: dict[str, Path]):
    if (folder / "physics.py").exists():
        mod = _load_module(folder)
        if mod is not None and hasattr(mod, "emit"):
            found[folder.name] = folder
            _MODULES[folder.name] = mod
            # Load numbers.json if it exists
            nj = folder / "numbers.json"
            if nj.exists():
                try:
                    _NUMBERS[folder.name] = json.loads(nj.read_text())
                except Exception:
                    _NUMBERS[folder.name] = {}
            else:
                _NUMBERS[folder.name] = {}
    for child in sorted(d for d in folder.iterdir()
                        if d.is_dir() and not d.name.startswith((".", "_"))):
        _walk_folder(child, found)


def _discover() -> dict[str, Path]:
    """Lazy discovery: find all membranes once and cache."""
    if not hasattr(_discover, "_membranes"):
        _discover._membranes = _discover_membranes()
    return _discover._membranes


def scene_terms() -> list[str]:
    """All terms that can be rendered -- every membrane with a working emit()."""
    return sorted(_discover().keys())


def membrane_terms() -> list[str]:
    """Terms that are actual membranes (have physics.py + emit()).
    Currently identical to scene_terms() since both require emit()."""
    return scene_terms()


def term_inventory() -> dict:
    """What the engine DECLARES against what it can RENDER -- the gap, counted.

    WHY THIS EXISTS RATHER THAN A BIGGER `scene_terms()`. The engine's `terms_data.TERMS` declares
    59 terms; this module can render 42. The obvious move is to make the tree show all 59, and it
    is the wrong one: the extra terms have NO buffer function anywhere in the engine, so a sidebar
    listing them would offer membranes that return None when clicked.

        A TREE THAT LISTS WHAT IT CANNOT DRAW IS THE SPECIFICATION CITED AS PROOF.

    MEASURED, and the shape is not what a "17 missing terms" reading expects:

        59 declared . 42 renderable . 46 declared-but-not-renderable . 29 renderable-but-undeclared

    Only THIRTEEN terms are in both lists. These are two nearly-disjoint vocabularies -- the
    declared set is the game's design language (theShip, theVerbs, theMeaning), the renderable set
    is the grown story tree (aBlueWorld, theCooling, theSweep). Neither is wrong; they are simply
    not the same list, and the honest response is to say so rather than to union them.

    `scene_terms()` keeps returning only what renders, so nothing lies. This counts the rest, so
    nothing is forgotten -- the same treatment `action_tests` gives a refusal.
    """
    render = set(scene_terms())
    try:
        import ChimeraEngine.terms_data as _td
        declared = {t[0] if isinstance(t, (tuple, list)) else str(t) for t in _td.TERMS}
    except Exception:
        declared = set()
    return {
        "declared": sorted(declared),
        "renderable": sorted(render),
        "declared_not_renderable": sorted(declared - render),
        "renderable_not_declared": sorted(render - declared),
        "in_both": sorted(declared & render),
        "counts": {"declared": len(declared), "renderable": len(render),
                   "declared_not_renderable": len(declared - render),
                   "renderable_not_declared": len(render - declared),
                   "in_both": len(declared & render)},
    }


def scene_cam_distance(term: str) -> float:
    """Derived camera distance for a term (its extent * 2.8, the viewer's rule)."""
    if term in _CAM_DIST:
        return _CAM_DIST[term]
    nums = _NUMBERS.get(term, {})
    extent = float(nums.get("extent_m", 1.0))
    dist = max(1.0, extent * 2.8)
    _CAM_DIST[term] = dist
    return dist


def _find_membrane(term: str) -> Path | None:
    """Find the story/ folder for a membrane by name."""
    membranes = _discover()
    return membranes.get(term)


def membrane_buffer(term: str, t: float = 1.0) -> np.ndarray | None:
    """Render a membrane at time t (0..1). Returns (N, 28) float32 or None.

    t=0 is the membrane's beginning, t=1 is its settled state.
    The buffer is in the membrane's own local units (radius ~1).
    """
    t = float(np.clip(t, 0.0, 1.0))
    key = (term, round(t, 6))  # round to avoid float-key noise
    if key in _TCACHE:
        return _TCACHE[key].copy()
    if len(_TCACHE) > 4096:          # safety net under the playback prune; never unbounded
        _TCACHE.clear()

    membranes = _discover()
    folder = membranes.get(term)
    if folder is None:
        return None

    mod = _MODULES.get(term)
    if mod is None:
        return None

    nums = _NUMBERS.get(term, {})
    try:
        buf = np.ascontiguousarray(mod.emit(nums, t), dtype=np.float32)
    except Exception:
        return None

    if buf.ndim != 2 or buf.shape[1] != 28 or buf.shape[0] == 0:
        return None

    _TCACHE[key] = buf.copy()
    return buf


def scene_buffer(term: str) -> np.ndarray | None:
    """Render a term at its settled state (t=1.0). Alias for membrane_buffer(term, 1.0)."""
    if term in _CACHE:
        return _CACHE[term].copy()
    buf = membrane_buffer(term, 1.0)
    if buf is not None:
        _CACHE[term] = buf.copy()
    return buf


def sun_direction(term: str, t: float = 1.0) -> tuple | None:
    """A membrane's declared sun, as a (x, y, z) direction FROM the scene TOWARD the light.

    Returns None when the membrane publishes no `sun_direction` -- the renderer then stays
    lightless and the picture is bit-identical to the baseline. When a membrane DOES declare one
    (every day-lit membrane, Stage 21), the live viewer arms `pipe.set_light(sun, (1.0, 1.0, 1.0))`
    with THE SAME declaration the emit baked its diffuse with, so baked diffuse and kernel glint
    can never disagree about where the sun is. t is clipped exactly as membrane_buffer clips it.
    """
    t = float(np.clip(t, 0.0, 1.0))
    _discover()                       # populates _MODULES -- lazy, like membrane_buffer
    mod = _MODULES.get(term)
    if mod is None or not hasattr(mod, "sun_direction"):
        return None
    try:
        s = np.asarray(mod.sun_direction(t, _NUMBERS.get(term, {})), dtype=np.float64)
    except Exception:
        return None
    if s.ndim != 1 or s.size != 3 or float(np.linalg.norm(s)) <= 0.0:
        return None
    return (float(s[0]) / float(np.linalg.norm(s)),
            float(s[1]) / float(np.linalg.norm(s)),
            float(s[2]) / float(np.linalg.norm(s)))


def membrane_module(term: str):
    """The loaded physics module for a membrane, or None. Triggers discovery once."""
    _discover()
    return _MODULES.get(term)


def membrane_keymap(term: str) -> dict:
    """The membrane's deck KEYMAP (keycode -> (action, label)), or {} for a quiet membrane."""
    mod = membrane_module(term)
    if mod is None:
        return {}
    return dict(getattr(mod, "KEYMAP", None) or {})


def membrane_state(term: str, t: float = 1.0) -> dict | None:
    """The matrix state machine's readout at t: per-state row counts, or None."""
    mod = membrane_module(term)
    if mod is None or not hasattr(mod, "state_readout"):
        return None
    try:
        return mod.state_readout(_NUMBERS.get(term, {}), t)
    except Exception:
        return None


def membrane_handle_key(term: str, code: str, down: bool = True,
                        t: float = 1.0) -> dict | None:
    """Forward one key to a membrane's deck controller. Returns its command, or None."""
    mod = membrane_module(term)
    if mod is None or not hasattr(mod, "handle_key"):
        return None
    try:
        return mod.handle_key(code, down=down, t=t, nums=_NUMBERS.get(term, {}))
    except Exception:
        return None


def solo(term: str, state) -> dict:
    """Set a membrane's solo channel WITHOUT dropping its loaded module.

    `invalidate(term)` pops the module, which would wipe the very state we are setting
    (the module is re-imported fresh next call). The solo lives in the module, so the
    buffer caches are dropped and the module is kept -- the next emit re-classifies and
    re-colours with the new channel.
    """
    mod = membrane_module(term)
    if mod is None or not hasattr(mod, "set_solo"):
        return {"applied": False, "term": term}
    mod.set_solo(state)
    _CACHE.pop(term, None)
    for k in [k for k in _TCACHE if k[0] == term]:
        del _TCACHE[k]
    return {"applied": True, "term": term, "solo": state}


def prune_time_cache(term: str, keep: int = 8):
    """Keep only the `keep` most recent t-samples cached for a membrane.

    Playback re-emits at a new t every frame, and every new (term, t) pair lands in
    `_TCACHE`; a ten-second play at 60 fps would otherwise grow the cache by hundreds of
    buffers the needle will never revisit. Keeping the nearest t's preserves fast
    scrub-back while bounding memory.
    """
    keys = sorted((k for k in _TCACHE if k[0] == term), key=lambda k: k[1])
    for k in keys[:-keep]:
        del _TCACHE[k]


def invalidate(term: str | None = None):
    """Clear caches so the next call re-imports and re-emits. None = clear all.

    RETURNS WHAT IT DROPPED, so a caller can tell a real clear from a no-op. `/invalidate` used to
    be able to answer 200 OK having cleared nothing at all -- a term that was never cached, or a
    misspelled name -- and the operator would then watch an unchanged render and conclude the
    endpoint was broken rather than that they had asked for the wrong term.

    I NEARLY ADDED A SECOND COPY OF THIS FUNCTION, and the near-miss is worth recording: a
    duplicate `invalidate` defined earlier in the file would have been silently SHADOWED by this
    one (Python keeps the last definition), so the tests would have passed while exercising code
    nobody had read. And this version is the better one -- it also clears `_MODULES` and
    `_discover._membranes`, which a fresh implementation forgot. Look for the function before
    writing it; a shadowed duplicate fails in exactly the way that leaves no evidence.
    """
    dropped = {"cleared": term or "all",
               "buffers": len(_CACHE) if term is None else int(term in _CACHE),
               "timed": len(_TCACHE) if term is None else sum(1 for k in _TCACHE if k[0] == term),
               "modules": len(_MODULES) if term is None else int(term in _MODULES),
               "numbers": len(_NUMBERS) if term is None else int(term in _NUMBERS)}
    if term is None:
        _CACHE.clear()
        _TCACHE.clear()
        _MODULES.clear()
        _NUMBERS.clear()
        _CAM_DIST.clear()
        if hasattr(_discover, "_membranes"):
            del _discover._membranes
    else:
        _CACHE.pop(term, None)
        keys_to_del = [k for k in _TCACHE if k[0] == term]
        for k in keys_to_del:
            del _TCACHE[k]
        _MODULES.pop(term, None)
        _NUMBERS.pop(term, None)
        _CAM_DIST.pop(term, None)
        # A dropped module must be REPLACED, not just removed. The discovery cache
        # stays warm, so the next scene_buffer() would find the folder but no module
        # and render nothing (black frame). Re-import the term's module right here
        # so its FILE-BACKED state -- the solo channel, switches.json -- reloads on
        # the next emit, which is exactly what a membrane that mutates its own
        # matrix needs after an operator key.
        folder = _discover().get(term)
        if folder is not None:
            mod = _load_module(folder)
            if mod is not None:
                _MODULES[term] = mod
                nj = folder / "numbers.json"
                try:
                    _NUMBERS[term] = json.loads(nj.read_text()) if nj.exists() else {}
                except Exception:
                    _NUMBERS[term] = {}
    return dropped


def term_numbers(term: str) -> dict:
    """Return the numbers.json for a membrane (its derived quantities)."""
    return dict(_NUMBERS.get(term, {}))


# SIZE column index — must match ParticleEngine.gpu_pipeline.SIZE and matter.SIZE
SIZE = 20

# ── THE ENGINE'S MOVIE PATH (recovered 2026-08-05) ─────────────────────────────────────────────
# engine_state._appearance calls splat_appearance.project_movie(term, out) and expects a MOVIE
# {"begin", "end"}. The density-lane rewrite (272f87c) stripped project_movie, SCENES, and every
# authored scene builder from this file, so every declared-but-not-a-membrane term fell back to the
# matplotlib placeholder (a single still duplicated as begin==end) -- which is exactly why the
# theVerbs dyad failed: the proxy watched two IDENTICAL frames and reported "the scene stays the
# same". The scene builders survive in git (70cc71f). Restoring the path here hands the engine back
# its real render: a story membrane's own timeline (emit at t=0 -> t=1) and an authored two-frame
# composition for the design-language terms that have no membrane.

# the particle buffer layout the pipeline reads (ParticleEngine.core.COL)
NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
NX, NY, NZ = 21, 22, 23     # OPTIONAL surface normal -> back-face-culls occluded grains (0,0,0 = no cull)


def _seed(term: str) -> int:
    """A stable per-term seed -- deterministic across processes (hash() is salted; zlib.crc32 is not)."""
    import zlib
    return zlib.crc32(term.encode("utf-8")) & 0x7FFFFFFF


def _fibonacci_sphere(n: int, jitter: float = 0.0, seed: int = 0) -> np.ndarray:
    """n unit vectors spread evenly over the sphere (the golden-angle spiral). Deterministic.

    JITTER BREAKS THE LATTICE. The golden-angle spiral is *regular*, and a regular sampling pattern
    is VISIBLE (faint curved streaks in a planet's ocean). `jitter` displaces each grain TANGENTIALLY
    (in the surface, then renormalised onto the shell) by a fraction of the mean grain spacing,
    turning the spiral into blue noise. It is tangential ON PURPOSE: RADIAL jitter scatters grains in
    depth and lets the background speckle through between them."""
    i = np.arange(n, dtype=np.float64)
    z = 1.0 - 2.0 * (i + 0.5) / n                 # -1..1, even in area
    r = np.sqrt(np.clip(1.0 - z * z, 0.0, 1.0))
    theta = np.pi * (1.0 + 5.0 ** 0.5) * i        # golden angle
    d = np.stack([r * np.cos(theta), r * np.sin(theta), z], axis=1)
    if jitter > 0.0:
        rng = np.random.default_rng(seed)
        spacing = 2.0 / np.sqrt(max(n, 1))                       # mean angular spacing on a unit sphere
        v = rng.normal(0.0, 1.0, (n, 3))
        v -= (v * d).sum(1, keepdims=True) * d                   # project into the TANGENT plane
        v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)
        d = d + v * (jitter * spacing * rng.random((n, 1)) ** 0.5)
        d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-12)  # back onto the shell: no depth change
    return d


def _dots(center, radius, n, color, rng):
    """A tiny solid ball of one colour -- a small compact object drawn as grains."""
    d = _fibonacci_sphere(n)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, PX:PZ + 1] = np.asarray(center, np.float32) + d * radius
    b[:, TYPE] = 3.0
    b[:, ALPHA] = 0.8; b[:, SIZE] = 2.0
    b[:, CR], b[:, CG], b[:, CB] = color
    return b


def _halo(center, radius, color, rng, alpha: float = 0.09, size: float = 1.8, n: int | None = None):
    """A faint soft glow shell (atmosphere type = big soft blobs) -- a limb/atmosphere/star glow."""
    if n is None:
        n = max(300, int(0.06 * 4.0 * np.pi * radius * radius))
    dirs = _fibonacci_sphere(n)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, PX:PZ + 1] = np.asarray(center, np.float32) + dirs * radius
    b[:, TYPE] = 5.0                                               # atmosphere: sm=6.0 -> big soft blobs
    b[:, CR] = color[0]; b[:, CG] = color[1]; b[:, CB] = color[2]
    b[:, ALPHA] = alpha; b[:, SIZE] = size
    return b


def _verbs_buffers(spec: dict, term: str):
    """theVerbs: the acts that change the world. A verb IS a change, so the two frames must DIFFER in
    the world, not in brightness. begin: ONE pale stone rests at the old place beside a reaching
    figure, the path only a faint thread of intent. end: that same stone has ARRIVED at the new
    place, lit and glowing -- a dim ghost where it was, a trail of pale forms brightening along the
    rising curve between. The claim is not the figure and not the stone but the CHANGE: same object,
    two places, one arc of action between them.

    The proxy's own diagnosis drove the palette (2026-08-05): the first scene's cyan arc read as "a
    second figure", and a trail in BOTH frames read as "no change". The expected reading is "repeated
    PALE round forms that brighten along the curve", so every form here is the stone's own pale
    colour and the arc is a faint grey thread. Second derived correction, from the same falsifier
    line: a 35B reasoning model ALSO read "the scene stays the same" -- the change was real but too
    subtle to narrate (the stone shifted ~12% of frame width while the rest was identical). So the
    stone now travels from the figure's HAND (begin) to the far upper-right (end), and the right
    half of the frame starts EMPTY and fills with the rising trail and the arrived glow: a change a
    blind eye cannot miss. Each change is traceable to the falsifier's specific failure; this is a
    derived correction, not a sweep."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # ground hint: a sparse dark slab
    n_g = 800
    th = rng.random(n_g) * 2.0 * np.pi
    rr = 60.0 * np.sqrt(rng.random(n_g))
    ground = np.zeros((n_g, NCOLS), dtype=np.float32)
    ground[:, PX] = rr * np.cos(th)
    ground[:, PY] = rr * np.sin(th)
    ground[:, PZ] = rng.normal(0.0, 0.7, n_g) - 0.5
    ground[:, TYPE] = 3.0; ground[:, ALPHA] = 0.25; ground[:, SIZE] = 2.4
    ground[:, CR], ground[:, CG], ground[:, CB] = 0.38, 0.40, 0.38

    # the figure: a full upright form on the left
    FX = -30.0
    fig = []
    body_c = (0.82, 0.80, 0.74)
    n_b = 160
    t = np.linspace(0.0, 1.0, n_b)
    torso = np.zeros((n_b, NCOLS), dtype=np.float32)
    torso[:, PX] = FX + rng.normal(0.0, 0.4, n_b)
    torso[:, PZ] = 6.0 + 8.0 * t
    torso[:, TYPE] = 3.0; torso[:, ALPHA] = 0.8; torso[:, SIZE] = 1.6
    torso[:, CR], torso[:, CG], torso[:, CB] = body_c
    fig.append(torso)
    for lx in (-2.0, 2.0):                                          # legs
        n_l = 90
        tl = np.linspace(0.0, 1.0, n_l)
        leg = np.zeros((n_l, NCOLS), dtype=np.float32)
        leg[:, PX] = FX + lx + rng.normal(0.0, 0.3, n_l)
        leg[:, PZ] = 0.5 + 5.5 * tl
        leg[:, TYPE] = 3.0; leg[:, ALPHA] = 0.8; leg[:, SIZE] = 1.4
        leg[:, CR], leg[:, CG], leg[:, CB] = body_c
        fig.append(leg)
    fig.append(_dots((FX, 0.0, 16.5), 2.4, 36, body_c, rng))        # head

    def arm(reach):                                                 # the reaching arm
        n_a = 110
        t = np.linspace(0.0, 1.0, n_a)
        a = np.zeros((n_a, NCOLS), dtype=np.float32)
        a[:, PX] = FX + reach * t
        a[:, PZ] = 13.5 + 2.0 * t + rng.normal(0.0, 0.3, n_a)
        a[:, TYPE] = 3.0; a[:, ALPHA] = 0.8; a[:, SIZE] = 1.4
        a[:, CR], a[:, CG], a[:, CB] = body_c
        return a

    OLD = (-16.0, 0.0, 14.0)          # at the figure's hand
    NEW = (40.0, 0.0, 18.0)           # far away, upper right -- the arrived place

    # the stone and its pale kin -- ONE colour everywhere, so nothing reads as a second object.
    # Slightly whiter than the body so the stone reads as a distinct round form at the hand.
    stone_c = (0.95, 0.93, 0.88)

    def stone(pos, radius=4.2, alpha=0.95):
        s = _dots(pos, radius, 70, stone_c, rng)
        s[:, ALPHA] = alpha
        return s

    # the rising path of travel: stations along the arc, brightening toward the end
    def trail(alpha_gain):
        parts = []
        for tt, al in ((0.14, 0.35), (0.34, 0.50), (0.54, 0.65), (0.74, 0.80)):
            pos = (OLD[0] + (NEW[0] - OLD[0]) * tt, 0.0,
                   OLD[2] + (NEW[2] - OLD[2]) * tt + 6.0 * np.sin(tt * np.pi))
            st = _dots(pos, 3.2, 50, stone_c, rng)
            st[:, ALPHA] = al * alpha_gain
            parts.append(st)
        return parts

    # a faint grey thread between the stations -- continuity, never a bright object
    n_arc = 220
    t = np.linspace(0.0, 1.0, n_arc)
    arc = np.zeros((n_arc, NCOLS), dtype=np.float32)
    arc[:, PX] = OLD[0] + (NEW[0] - OLD[0]) * t
    arc[:, PZ] = OLD[2] + (NEW[2] - OLD[2]) * t + 6.0 * np.sin(t * np.pi)
    arc[:, TYPE] = 3.0; arc[:, SIZE] = 1.2
    arc[:, CR], arc[:, CG], arc[:, CB] = 0.72, 0.74, 0.78
    arc_dim = arc.copy(); arc_dim[:, ALPHA] = 0.06
    arc_lit = arc.copy(); arc_lit[:, ALPHA] = 0.20

    # the ghost: the dim shape of where the stone WAS, in the end frame
    ghost = stone(OLD, radius=3.6, alpha=0.28)

    # the arrived stone: lit and glowing warm-white at the new place
    arrived = stone(NEW, radius=4.4, alpha=1.0)
    glow = _halo(NEW, 8.0, (1.0, 1.0, 0.92), rng, alpha=0.18, size=2.0)

    # begin: the stone AT the hand, the right half EMPTY -- only a barely-there thread of intent
    begin = np.concatenate([ground] + fig + [arm(14.0), stone(OLD, alpha=0.95), arc_dim], axis=0)
    # end: the same stone ARRIVED far away -- a ghost where it was, the path filled in and burning
    end = np.concatenate([ground] + fig + [arm(20.0), ghost]
                         + trail(0.90) + [arc_lit, arrived, glow], axis=0)
    return end, begin


# the authored compositions for the declared terms that have no story membrane. A term with a
# membrane is ALWAYS rendered from its own emit() -- the folder wins -- and these are the fallback.
_DESIGN_SCENES = {
    "theVerbs": {"kind": "verbs", "cam": (0.0, -95.0, 30.0)},
    # Non-meaning terms with PHYSICS_READING but no real membrane
    "theScan": {"kind": "scan", "cam": (0.0, -10.0, 5.0)},
    "theNavigate": {"kind": "navigate", "cam": (0.0, -20.0, 10.0)},
    "theShoot": {"kind": "shoot", "cam": (0.0, -15.0, 8.0)},
    "thePlayer": {"kind": "player", "cam": (0.0, -5.0, 3.0)},
    "theInput": {"kind": "input", "cam": (0.0, -5.0, 3.0)},
    "theState": {"kind": "state", "cam": (0.0, -5.0, 3.0)},
    "thePersistence": {"kind": "persistence", "cam": (0.0, -5.0, 3.0)},
    "theLoop": {"kind": "loop", "cam": (0.0, -10.0, 5.0)},
}
_DESIGN_BUILDERS = {
    "verbs": _verbs_buffers,
    # Scene builders for terms without real membranes
    "scan": lambda spec, term: (_dots((0, 0, 0), 2.0, 100, (0.3, 0.6, 0.9), np.random.default_rng(_seed(term))),
                                  _dots((0, 0, 0), 2.0, 100, (0.3, 0.6, 0.9), np.random.default_rng(_seed(term)))),
    "navigate": lambda spec, term: (_halo((0, 0, 0), 5.0, (0.2, 0.4, 0.8), np.random.default_rng(_seed(term))),
                                      _dots((0, 0, 0), 1.5, 50, (0.5, 0.7, 0.9), np.random.default_rng(_seed(term)))),
    "shoot": lambda spec, term: (_dots((0, 0, 0), 3.0, 80, (0.9, 0.2, 0.1), np.random.default_rng(_seed(term))),
                                   _halo((0, 0, 0), 6.0, (0.9, 0.3, 0.1), np.random.default_rng(_seed(term)), alpha=0.15, size=2.2)),
    "player": lambda spec, term: (_dots((0, 0, 0), 2.5, 60, (0.8, 0.8, 0.7), np.random.default_rng(_seed(term))),),
    "input": lambda spec, term: (_dots((0, 0, 0), 1.5, 40, (0.4, 0.6, 0.8), np.random.default_rng(_seed(term))),),
    "state": lambda spec, term: (_halo((0, 0, 0), 3.0, (0.3, 0.5, 0.3), np.random.default_rng(_seed(term)), alpha=0.12, size=1.8),),
    "persistence": lambda spec, term: (_dots((0, 0, 0), 2.0, 70, (0.6, 0.7, 0.6), np.random.default_rng(_seed(term))),),
    "loop": lambda spec, term: (_halo((0, 0, 0), 4.0, (0.5, 0.3, 0.6), np.random.default_rng(_seed(term)), alpha=0.1, size=2.0),),
}


def _movie_instants(nums: dict) -> tuple[float, float]:
    """THE TWO FRAMES OF A MEMBRANE'S MOVIE that carry its claim, read off its own timeline.

    The default movie is beginning -> settled (t=0 -> t=1). For a membrane whose film IS a process,
    the endpoints can be the two frames that look most alike -- a jump starts and ends with the
    body on the ground, so a blind eye watching [start, landed] sees "no change" even though
    everything happened. The 35B eye said exactly that about theThrust. So when a membrane publishes
    its own phase durations, the movie is sampled at the two instants where its claim is VISIBLE:
    mid-push (the ground reaction bar up, body driving) and apex (airborne, the bar gone to zero --
    no contact, no thrust). Both frames are still the membrane's own emit() output, and both are
    derived from its own published numbers; nothing here is authored."""
    try:
        t_c = float(nums["crouch_time_s"])
        t_p = float(nums["contact_time_s"])
        t_f = float(nums["flight_time_s"])
        total = float(nums["duration_s"])
    except (KeyError, TypeError, ValueError):
        return 0.0, 1.0
    if total <= 0.0 or t_f <= 0.0:
        return 0.0, 1.0
    mid_push = (t_c + 0.5 * t_p) / total
    apex = (t_c + t_p + 0.5 * t_f) / total
    return mid_push, apex


def project_movie(term: str, out_dir) -> dict | None:
    """Render `term`'s splat movie -> {"begin": path, "end": path}, or None if it has no scene.

    A story membrane's movie is its OWN timeline (emit at t=0 -> t=1), framed by its own extent. A
    declared term with an authored composition (the design language: theVerbs) is drawn from its
    two-state buffer pair. The engine's `_appearance` falls back to the matplotlib placeholder only
    when BOTH are absent -- a term with no scene has no appearance, honestly."""
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)

    if term in _discover():                                          # THE FOLDER WINS, always
        t_begin, t_end = _movie_instants(_NUMBERS.get(term, {}))
        end_buf = membrane_buffer(term, t_end)
        begin_buf = membrane_buffer(term, t_begin)
        if end_buf is None or begin_buf is None:
            return None
        extent = float(np.linalg.norm(end_buf[:, PX:PZ + 1], axis=1).max()) or 1.0
        cam_pos = (0.0, -2.7 * extent, 0.72 * extent)
    else:
        spec = _DESIGN_SCENES.get(term)
        if not spec:
            return None
        builder = _DESIGN_BUILDERS.get(spec["kind"])
        if not builder:
            return None
        end_buf, begin_buf = builder(spec, term)
        cam_pos = spec["cam"]

    cx, cy, cz = cam_pos                                            # AIM at the body (origin)
    cam = FirstPersonCamera(cam_pos, yaw=float(np.arctan2(-cy, -cx)),
                            pitch=float(np.arctan2(-cz, float(np.hypot(cx, cy)))))
    p = cam.params(720, 540)
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    paths = {}
    for label, buf in (("begin", begin_buf), ("end", end_buf)):
        png = out / f"movie_{term}_{label}.png"
        pipe.upload(np.ascontiguousarray(buf, dtype=np.float32), term=term)
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(png)
        paths[label] = str(png)
    return paths


if __name__ == "__main__":
    terms = scene_terms()
    print(f"Found {len(terms)} renderable membranes:")
    for t in terms:
        buf = scene_buffer(t)
        n = buf.shape[0] if buf is not None else 0
        nums = term_numbers(t)
        extent = nums.get("extent_m", "?")
        print(f"  {t:30s}  {n:>6d} grains  extent={extent}")