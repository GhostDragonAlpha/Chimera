"""forest_loader -- M-F08: the one-shot, repeatable forest loader.

Map item F08, verbatim (MONKEY_COMPLETION_MAP.md:124): "Scene seed/configuration
reproduces assets, collision and initial state with clear failures for missing
assets. Resource cleanup uses existing lifecycle machinery."

THE RECOMPILE-NOT-COPY LAW (F07's handoff, frozen in
agents/F08_loading/PREREGISTRATION.md BEFORE this file): the committed
declarations are DERIVED data; the recipe modules are the law. This loader never
trusts a stored pin alone -- it re-compiles all four artifacts from the recipes
(each from the RECOMPILED upstream, never from the committed copy), validates
the recompiles with each module's own validator, and only then byte-compares
them against the committed files. A committed file that fails to parse, breaks
its own self-pin, or diverges from its recompilation is refused BY NAME with
the exact artifact:

    f08_missing_artifact   an artifact absent at the configured root (Phase A,
                           all four checked before any recompile)
    f08_invalid_artifact   committed bytes unparseable or failing their own
                           validator (``cause`` carries the recipe's own code:
                           f01_digest_mismatch, f02_*, f03_digest_mismatch,
                           f07_digest_mismatch, ...)
    f08_recompile_refused  the recompilation itself refused (live-tree drift;
                           ``cause`` carries the recipe's own code, e.g.
                           f07_input_drift)
    f08_recompile_drift    committed bytes differ from the recompilation (the
                           self-consistent re-forge case the self-pin cannot
                           see)
    f08_teardown_leak      a registered resource failed its release
    f08_cli_verb           unknown CLI verb

THE CLEANUP HOOK: the engine-process lifecycle already exists and is cited, not
rebuilt -- World.shutdown_engine() (tools/playable_slice/slice_server.py:174-181,
terminate -> wait(10 s) -> kill, called in main()'s finally and at the top of
every boot) and SessionFlow's exit transition
(tools/monkey_campaign/product/session_flow.py: teardown callable fired exactly
once; a second exit is "a named drop, never a second teardown"; TeardownDouble
at :141-151). NOTHING exists for the data layer, so the smallest adapter lives
here: ForestScene.teardown() is a zero-arg callable in EXACTLY SessionFlow's
teardown shape -- optional injected engine_shutdown first (declared referent
World.shutdown_engine), then every registered resource released BY NAME in
reverse-load order, then a zero-live audit, idempotent per SessionFlow's
terminal-state law.

Initial state is DERIVED, never restated: the record composes spawn pose, trunk
site, route-graph parameters and the collision-surface identity only from the
four proven declarations plus the ONE physical query surface
(terrain_query.TerrainSurface -- walker.py:163-174, no second scalar truth),
and self-pins itself with the house digest (initial_state_sha256).

Scene seed: 4598321 (F01's frozen ``seed``; consumed, never re-chosen).
Stdlib-only, CPU-only, headless. Run from the repo root:
    python tools/monkey_campaign/data/monkey_forest/forest_loader.py receipt
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
import tempfile

SCHEMA = "chimera.monkey_forest.v1"
NAME = "monkey_forest"

# repo root: forest_loader.py -> monkey_forest -> data -> monkey_campaign -> tools -> root
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))

# The four integrated artifacts, in dependency order (F01 -> F02 -> F03 -> F07).
ARTIFACTS = {
    "clearing": {
        "path": "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
        "schema": "chimera.monkey_clearing.v1",
        "pin_field": "declaration_sha256",
    },
    "terrain": {
        "path": "tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json",
        "schema": "chimera.monkey_terrain.v1",
        "pin_field": "bundle_sha256",
    },
    "trunk": {
        "path": "tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json",
        "schema": "chimera.trunk_asset.v1",
        "pin_field": "declaration_sha256",
    },
    "routes": {
        "path": "tools/monkey_campaign/data/monkey_routes/route_declaration.json",
        "schema": "chimera.monkey_routes.v1",
        "pin_field": "route_declaration_sha256",
    },
}
ORDER = ("clearing", "terrain", "trunk", "routes")
GRID_DECIMALS = 6            # the house 1e-6 determinism grid (F01's rule)
SCENE_SEED = 4598321         # F01's frozen seed; the "scene seed" of map item F08


class Refusal(ValueError):
    """Strict intake refusal, house style, plus the artifact identity F08 owes.

    ``artifact``/``path`` name the exact offending input; ``cause`` carries the
    underlying recipe-layer code (f01_*/f02_*/f03_*/f07_*) when one fired, so
    callers can assert the recipe codes F07's handoff demands without losing
    the forest-layer identity.
    """

    def __init__(self, code, detail="", artifact=None, path=None, cause=None):
        self.code, self.detail = code, str(detail)
        self.artifact, self.path, self.cause = artifact, path, cause
        super().__init__(code + (": " + self.detail if detail else ""))


def require(condition, code, detail="", **identity):
    if not condition:
        raise Refusal(code, detail, **identity)


def canonical(value):
    """House canonical bytes (tools/science_funnel/common.py::canonical)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(canonical(value))


def _grid6(value):
    return round(float(value), GRID_DECIMALS)


def file_sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _load_module(name, rel_path):
    """Import a sibling artifact module by package name, else by file path.

    ``rel_path`` is repo-relative without the .py extension (route_recipe's
    pattern). Recipe modules are CODE and always come from this module's own
    tree; only DATA paths are root-configurable.
    """
    dotted = rel_path.replace("/", ".")
    try:
        return __import__("tools." + dotted, fromlist=[name])
    except ImportError:
        path = os.path.join(_REPO, *rel_path.split("/")) + ".py"
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


_MODULES = None


def modules():
    """The four recipe modules + the one query surface, loaded once."""
    global _MODULES
    if _MODULES is None:
        _MODULES = {
            "clearing_mod": _load_module(
                "clearing_recipe",
                "tools/monkey_campaign/data/monkey_clearing/clearing_recipe"),
            "terrain_mod": _load_module(
                "terrain_bundle",
                "tools/monkey_campaign/data/monkey_clearing/terrain_bundle"),
            "query_mod": _load_module(
                "terrain_query",
                "tools/monkey_campaign/data/monkey_clearing/terrain_query"),
            "trunk_mod": _load_module(
                "trunk_recipe",
                "tools/monkey_campaign/data/monkey_trunk/trunk_recipe"),
            "routes_mod": _load_module(
                "route_recipe",
                "tools/monkey_campaign/data/monkey_routes/route_recipe"),
        }
    return _MODULES


# --- the recompile chain (each from the RECOMPILED upstream, never a copy) -----
def recompile_all():
    """Recompile all four declarations from the recipe modules. Returns
    {key: (object, canonical bytes)}. Raises the recipes' own Refusals wrapped
    as f08_recompile_refused (a live-tree drift is a global refusal)."""
    mods = modules()
    out = {}
    recipe_refusals = (mods["clearing_mod"].Refusal, mods["terrain_mod"].Refusal,
                       mods["trunk_mod"].Refusal, mods["routes_mod"].Refusal)
    try:
        clearing = mods["clearing_mod"].compile_declaration(seed=SCENE_SEED)
        mods["clearing_mod"].validate_declaration(clearing)
        terrain = None
        with tempfile.TemporaryDirectory(prefix="f08_recompile_") as tmp:
            # terrain_bundle compiles FROM A PATH: feed it the recompiled
            # clearing bytes, never the committed copy (recompile-not-copy).
            tmp_clearing = os.path.join(tmp, "clearing_declaration.json")
            with open(tmp_clearing, "wb") as handle:
                handle.write(canonical(clearing))
            terrain = mods["terrain_mod"].compile_bundle(tmp_clearing)
        mods["terrain_mod"].validate_bundle(terrain)
        trunk = mods["trunk_mod"].compile_declaration(f01_declaration=clearing)
        mods["trunk_mod"].validate_declaration(trunk)
        routes = mods["routes_mod"].compile_declaration()
        mods["routes_mod"].validate_declaration(routes)
    except recipe_refusals as exc:
        # every recipe carries the house Refusal (code, detail); attribute the
        # live-tree drift to the chain, preserving the recipe's own code
        raise Refusal("f08_recompile_refused", (exc.code, exc.detail),
                      cause=exc.code) from exc
    for key, obj in (("clearing", clearing), ("terrain", terrain),
                     ("trunk", trunk), ("routes", routes)):
        out[key] = (obj, canonical(obj))
    return out


# --- per-artifact committed-file checks (fixed order, prereg-frozen) -----------
def _check_committed(key, root, recompiled_bytes):
    mods = modules()
    spec = ARTIFACTS[key]
    path = os.path.join(root, *spec["path"].split("/"))
    with open(path, "rb") as handle:
        raw = handle.read()
    module = {"clearing": mods["clearing_mod"], "terrain": mods["terrain_mod"],
              "trunk": mods["trunk_mod"], "routes": mods["routes_mod"]}[key]
    validator_name = ("validate_bundle" if key == "terrain"
                      else "validate_declaration")
    try:
        obj = module.loads(raw)
        receipt = getattr(module, validator_name)(obj)
    except module.Refusal as exc:
        raise Refusal("f08_invalid_artifact", (key, spec["path"], exc.code,
                                               exc.detail),
                      artifact=key, path=path, cause=exc.code) from exc
    # committed bytes must equal the recompilation exactly (any one byte off
    # is falsifier (a), even when the file self-pins coherently)
    if sha(raw) != sha(recompiled_bytes):
        raise Refusal("f08_recompile_drift",
                      (key, spec["path"], sha(recompiled_bytes), sha(raw)),
                      artifact=key, path=path)
    return {"path": spec["path"], "bytes": len(raw), "file_sha256": sha(raw),
            "schema": spec["schema"], "pin_field": spec["pin_field"],
            "self_pin": obj[spec["pin_field"]], "recompiled_identical": True,
            "validator_receipt": receipt}, obj, path


# --- the derived initial-state record (T4; composed, never restated) -----------
def initial_state_record(clearing, terrain, trunk, routes, surface, sources):
    """Compose the initial scene state from the four proven declarations and
    the ONE physical query surface. Every float is on the 1e-6 grid."""
    spawn = clearing["spawn"]["position_m"]
    site = trunk["site"]["base_centre_m"]
    solid = trunk["collision_representation"]["solid"]
    spawn_h = _grid6(surface.height_at(spawn[0], spawn[2]))
    spawn_g = surface.gradient_at(spawn[0], spawn[2])
    record = {
        "schema": SCHEMA,
        "name": NAME,
        "scene_seed": clearing["seed"],
        "derived_from": sources,
        "extent": {"half_width_m": _grid6(clearing["extent"]["half_width_m"]),
                   "shape": clearing["extent"]["shape"],
                   "boundary_rule": clearing["extent"]["boundary_rule"]},
        "spawn": {"position_m": [_grid6(v) for v in spawn],
                  "terrain_height_m": spawn_h,
                  "gradient_m_per_m": [_grid6(spawn_g[0]), _grid6(spawn_g[1])],
                  "body_radius_envelope_m": _grid6(
                      clearing["spawn"]["body_radius_envelope_m"]),
                  "required_clearance_m": _grid6(
                      clearing["spawn"]["required_clearance_m"])},
        "trunk_site": {"id": trunk["object_id"],
                       "base_centre_m": [_grid6(v) for v in site],
                       "axis_dir": [_grid6(v) for v in trunk["site"]["axis_dir"]],
                       "radius_m": _grid6(trunk["geometry"]["radius_m"]),
                       "height_m": _grid6(trunk["geometry"]["height_m"]),
                       "base_elevation_m": _grid6(
                           trunk["geometry"]["base_elevation_m"]),
                       "collision_kind":
                           trunk["collision_representation"]["kind"],
                       "climbable_surface_id": "trunk_01.lateral"},
        "route_graph": {
            "spawn_m": [_grid6(v) for v in routes["routes"]["spawn_m"]],
            "trunk_axis_m": [_grid6(v) for v in routes["routes"]["trunk_axis_m"]],
            "straight": {k: routes["routes"]["straight"][k] for k in
                         ("id", "kind", "from_m", "to_m", "length_m",
                          "contact_dist_from_axis_m")},
            "tangents": [{k: t[k] for k in ("id", "mound_index", "side",
                                            "from_m", "dir_m", "t_end_m",
                                            "end_cause", "closest_approach_m")}
                         for t in routes["routes"]["tangents"]],
            "route_grid": {k: routes["route_grid"][k] for k in
                           ("step_m", "x0_m", "z0_m", "nx", "nz",
                            "connectivity", "row", "col", "snap_decimals")},
            "bounds": dict(routes["bounds"]),
            "blockers": [b["id"] for b in routes["blocking_causes"]["blockers"]],
        },
        "collision": {
            "terrain": {"kind": terrain["collision"]["kind"],
                        "surface_id": terrain["collision"]["surface_id"],
                        "same_arrays_as_render":
                            terrain["collision"]["same_arrays_as_render"],
                        "boundary": dict(terrain["collision"]["boundary"]),
                        "query_outside_refusal":
                            terrain["collision"]["query_outside_refusal"]},
            "trunk": {"kind": trunk["collision_representation"]["kind"],
                      "exact": trunk["collision_representation"]["exact"],
                      "solid": {"axis_base_m": [_grid6(v) for v in
                                                solid["axis_base_m"]],
                                "axis_dir": [_grid6(v) for v in
                                             solid["axis_dir"]],
                                "radius_m": _grid6(solid["radius_m"]),
                                "height_m": _grid6(solid["height_m"])}},
        },
        "surfaces": [s["id"] for s in trunk["surface_ids"]],
    }
    record["initial_state_sha256"] = digest(record)   # over bytes without it
    return record


# --- the teardown adapter (the data-layer gap, SessionFlow's shape) ------------
class _EngineShutdownSlot:
    """Resource wrapper for the injected engine teardown. The DECLARED referent
    of ``shutdown`` is World.shutdown_engine (slice_server.py:174-181)."""

    def __init__(self, shutdown):
        self._shutdown = shutdown

    def release(self):
        self._shutdown()


class ForestScene:
    """The loaded forest: four proven declarations + the ONE query surface +
    the derived initial state, every piece registered for teardown BY NAME.

    Teardown contract (SessionFlow's law, session_flow.py:107-117, 344-349):
    exactly one real teardown; releases run in reverse-load order (an injected
    engine_shutdown dies FIRST -- engine before data, the boot ordering);
    a second call is a named no-op receipt, never a second teardown.
    """

    def __init__(self, objects, surface, initial_state, receipt,
                 engine_shutdown=None):
        self.clearing = objects["clearing"]
        self.terrain = objects["terrain"]
        self.trunk = objects["trunk"]
        self.routes = objects["routes"]
        self.terrain_surface = surface
        self.initial_state = initial_state
        self.receipt = receipt
        self._resources = {}
        for key in ORDER:                       # load order = dependency order
            self._resources[key] = objects[key]
        self._resources["terrain_surface"] = surface
        self._resources["initial_state"] = initial_state
        self._torn_down = False
        if engine_shutdown is not None:
            self.attach_engine_shutdown(engine_shutdown)

    def attach_engine_shutdown(self, shutdown):
        """Inject the engine teardown (declared referent World.shutdown_engine).
        Registered LAST so reverse-order release kills the engine FIRST."""
        require(callable(shutdown), "f08_teardown_state", "shutdown must be callable")
        require("engine_shutdown" not in self._resources, "f08_teardown_state",
                "engine_shutdown already attached")
        require(not self._torn_down, "f08_teardown_state", "scene already torn down")
        self._resources["engine_shutdown"] = _EngineShutdownSlot(shutdown)

    def live_resources(self):
        """Names still registered to a live (non-released) resource."""
        return [n for n, v in self._resources.items() if v is not None]

    def teardown(self):
        """The zero-arg teardown callable (SessionFlow's ``teardown`` shape)."""
        if self._torn_down:
            return {"already_torn_down": True, "released": [],
                    "live_after": self.live_resources()}
        released = []
        for name in list(self._resources)[::-1]:        # reverse-load order
            res = self._resources[name]
            if res is None:
                continue
            release = getattr(res, "release", None)
            if callable(release):
                try:
                    release()
                except Exception as exc:                # a loud leak, by name
                    raise Refusal("f08_teardown_leak", (name, repr(exc)),
                                  artifact=name, cause="release_failed") from exc
            self._resources[name] = None                # drop BY NAME
            released.append(name)
        self._torn_down = True
        # drop the direct handles too: post-teardown the scene holds nothing
        self.clearing = self.terrain = self.trunk = self.routes = None
        self.terrain_surface = None
        self.initial_state = None
        return {"already_torn_down": False, "released": released,
                "live_after": self.live_resources()}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.teardown()
        return False


# --- the one-shot load ----------------------------------------------------------
def load_forest(root=None, engine_shutdown=None):
    """Load the integrated forest: recompile all four declarations, prove the
    committed files byte-identical, build the query surface and initial state.
    Raises a named Refusal on any missing/corrupt/drifting input."""
    root = _REPO if root is None else os.path.abspath(root)
    # Phase A: presence of ALL FOUR before any recompile (prereg, Amendment 1)
    paths = {}
    for key in ORDER:
        path = os.path.join(root, *ARTIFACTS[key]["path"].split("/"))
        require(os.path.isfile(path), "f08_missing_artifact", (key, path),
                artifact=key, path=path)
        paths[key] = path
    # Phase B: recompile the chain, then prove each committed file
    recompiled = recompile_all()
    checked, objects = {}, {}
    for key in ORDER:
        checked[key], objects[key], _ = _check_committed(
            key, root, recompiled[key][1])
    surface = modules()["query_mod"].TerrainSurface(
        objects["terrain"], validate=False)   # validated once above; ONE law
    sources = {key: {"path": checked[key]["path"],
                     "schema": checked[key]["schema"],
                     "file_sha256": checked[key]["file_sha256"],
                     "self_pin": checked[key]["self_pin"]}
               for key in ORDER}
    state = initial_state_record(objects["clearing"], objects["terrain"],
                                 objects["trunk"], objects["routes"],
                                 surface, sources)
    receipt = {"schema": SCHEMA, "name": NAME, "root_kind":
               "repo" if os.path.abspath(root) == _REPO else "configured",
               "artifacts": checked,
               "initial_state_sha256": state["initial_state_sha256"],
               "resources": ORDER + ("terrain_surface", "initial_state")}
    return ForestScene(objects, surface, state, receipt,
                       engine_shutdown=engine_shutdown)


# --- CLI (deterministic receipt: no timestamps, no absolute paths) --------------
def receipt_document(root=None):
    scene = load_forest(root=root)
    try:
        state = scene.initial_state
        doc = {"schema": SCHEMA, "name": NAME,
               "artifacts": {k: {f: scene.receipt["artifacts"][k][f]
                                 for f in ("path", "bytes", "file_sha256",
                                           "self_pin", "recompiled_identical")}
                             for k in ORDER},
               "initial_state_sha256": state["initial_state_sha256"],
               "scene_seed": state["scene_seed"],
               "spawn": state["spawn"],
               "trunk_site": state["trunk_site"],
               "route_graph": {"spawn_m": state["route_graph"]["spawn_m"],
                               "trunk_axis_m":
                                   state["route_graph"]["trunk_axis_m"],
                               "straight_id":
                                   state["route_graph"]["straight"]["id"],
                               "straight_length_m":
                                   state["route_graph"]["straight"]["length_m"],
                               "tangent_ids": [t["id"] for t in
                                               state["route_graph"]["tangents"]],
                               "blockers": state["route_graph"]["blockers"],
                               "grid_cells": state["route_graph"]["route_grid"]["nx"]
                                             * state["route_graph"]["route_grid"]["nz"]},
               "surfaces": state["surfaces"]}
    finally:
        scene.teardown()
    return doc


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "receipt":
        root = argv[1] if len(argv) > 1 else None
        print(json.dumps(receipt_document(root), sort_keys=True))
        return 0
    if argv[0] == "selftest":
        scene = load_forest()
        teardown_receipt = scene.teardown()
        ok = (teardown_receipt["live_after"] == []
              and not teardown_receipt["already_torn_down"]
              and scene.live_resources() == []
              and scene.clearing is None)
        print(json.dumps({"selftest": "pass" if ok else "FAIL",
                          "initial_state_sha256":
                              scene.receipt["initial_state_sha256"],
                          "released": teardown_receipt["released"]},
                         sort_keys=True))
        return 0 if ok else 1
    raise Refusal("f08_cli_verb", argv)


if __name__ == "__main__":
    sys.exit(main())
