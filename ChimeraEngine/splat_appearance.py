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
    return dropped


def term_numbers(term: str) -> dict:
    """Return the numbers.json for a membrane (its derived quantities)."""
    return dict(_NUMBERS.get(term, {}))


# SIZE column index — must match ParticleEngine.gpu_pipeline.SIZE and matter.SIZE
SIZE = 20


if __name__ == "__main__":
    terms = scene_terms()
    print(f"Found {len(terms)} renderable membranes:")
    for t in terms:
        buf = scene_buffer(t)
        n = buf.shape[0] if buf is not None else 0
        nums = term_numbers(t)
        extent = nums.get("extent_m", "?")
        print(f"  {t:30s}  {n:>6d} grains  extent={extent}")