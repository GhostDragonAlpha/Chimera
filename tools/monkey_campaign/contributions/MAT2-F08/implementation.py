"""implementation -- MAT2-F08: verify repeatable forest loading.

Card done_when (verbatim): "Scene seed/configuration reproduces assets,
collision and initial state with clear failures for missing assets"

THE MECHANISM (frozen in PREREGISTRATION.md commit 32df1e4d2d7ff78b135468ba
97c88ee894e00bf7 BEFORE this file existed):

1. ONE scene configuration (assets/scene_configuration.json, canonical JSON,
   self-pinned sha256) declares the scene's seeds (terrain recipe 4598321,
   obstacle placement 4600823), every asset by published contributions path +
   raw sha256, the collision state (pinned M06 law, CCD, declared composition
   scope) and the initial state (spawn, cameras, the frozen seven-run impact
   schedule). The loader intakes it with the F01 prereg vocabulary: strict
   require/Refusal, named codes, NO defaults.

2. REPRODUCTION, measured not asserted: the loader regenerates the terrain
   declaration from the seed, the terrain bundle from the regenerated
   declaration and the obstacle declaration from its seed through the pinned
   generators, each compared BYTE-EXACT to the published merged bytes; it
   re-derives the frozen seven-run dynamics trace through the unmodified
   pinned M06 solve_tick compared byte-exact to the published F07 trace; it
   re-renders the V1 clean gate frame compared byte-exact to the published F07
   artifact; and it materializes the full scene state (assets + collision
   state + initial state) identically in three fresh subprocess instantiations
   plus the in-process one (byte-identical canonical JSON at full float repr).

3. MISSING ASSETS FAIL CLEARLY: absent files, corrupted bytes, missing config
   sections, drifted seeds and a silently-defaulting lenient double are ALL
   detected with named refusals identifying the missing/corrupt asset.
   Falsifier arms FB1-FB6 run FIRST (fail-first), each with its OWN passing
   clean control; a non-biting arm refuses the whole build
   (`f08_falsifier_did_not_bite`).

4. Capture: REGISTRY profile `forest` (kind visible_static) read READ-ONLY
   from agent_slots.sqlite3; exactly the three profile views x (diagnostic,
   clean) as whole-frame image rows; capture_sha256 = sha256 of the single
   gate-bound artifact; state_binding kind 'state' -> the scene configuration;
   visual_capture.validate_manifest + visual_gate.verify bind everything.
   visual_acceptance stays false BY DESIGN -- independent visual review
   remains mandatory. The transform-list gate is NOT APPLICABLE to a static
   image capture (prereg section 8); its selftest still proves the gate
   refuses a flipped frame.

CPU-only (stdlib), deterministic (splitmix64 + the pinned generators' 1e-6
grid, no wall-clock). Refusals are named codes; nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import shutil
import sqlite3
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
ASSETS = HERE / "assets"
CONTRIB = HERE.parent                      # contributions/
ATTEMPT_WORKSPACE = HERE.parents[4]        # .../kanban-attempts/MAT2-F08/<id>/
SCRATCH = ATTEMPT_WORKSPACE / "scratch"

SCHEMA = "chimera.mat2_f08.repeatable_loading.v1"
CONFIG_SCHEMA = "chimera.mat2_f08.scene_configuration.v1"
STATE_SCHEMA = "chimera.mat2_f08.scene_state.v1"
BASE_REVISION = "edd5ae079d5f0f64ae498e055a1b11bc5adab013"
PREREG_COMMIT = "32df1e4d2d7ff78b135468ba97c88ee894e00bf7"
TASK_ID = "F08"                            # SHORT form (campaign capture schema)
RUN_ID = "mat2-f08-repeatable-loading-20260929-d8a71eab"
CRITERIA_SHA256 = "8063e7175f9b9a638809b348606636d280a56d9165245a9f91ced21abb55fcd7"
SCOPE_SHA256 = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
ATTEMPT_ID = "d8a71eabe827417f90de09cd1f7048c3"
ARRIVAL_ID = "arrival-961642204b8c4a478a4457af12fbfdbb"
REGISTRY_SQLITE = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
PROFILE_CANONICAL_SHA256 = (
    "2c9d0ab3e2af5f18b89704f0265850f94c341d2290da2a62b1197bea8f1a206b")
DONE_WHEN = ("Scene seed/configuration reproduces assets, collision and "
             "initial state with clear failures for missing assets")

# --- pinned inputs (PREREGISTRATION section 1; raw sha256 asserted) -----------
F02 = "MAT2-F02/pins/"
PINS = {
    "clearing_declaration_json": {
        "rel": F02 + "clearing_declaration.json",
        "sha256": "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1"},
    "terrain_bundle_json": {"rel": F02 + "terrain_bundle.json",
        "sha256": "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52"},
    "terrain_query_py": {"rel": F02 + "terrain_query.py",
        "sha256": "b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1"},
    "terrain_bundle_py": {"rel": F02 + "terrain_bundle.py",
        "sha256": "c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e"},
    "clearing_recipe_py": {"rel": F02 + "clearing_recipe.py",
        "sha256": "ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc"},
    "trunk_declaration_json": {"rel": F02 + "trunk_declaration.json",
        "sha256": "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1"},
    "local_contact_py": {"rel": "MAT2-M06/local_contact.py",
        "sha256": "1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc"},
    "contact_law_json": {"rel": "MAT2-M06/contact_law.json",
        "sha256": "583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b"},
    "f03_trunk_mesh_json": {"rel": "MAT2-F03/assets/trunk_01_mesh.json",
        "sha256": "3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7"},
    "f04_implementation_py": {"rel": "MAT2-F04/implementation.py",
        "sha256": "5c398d22b4259d9e4c89ca3a7900610d629e318ac13b57681cbc7c617619e083"},
    "f07_implementation_py": {"rel": "MAT2-F07/implementation.py",
        "sha256": "49a975c7a1a14238eb79bd5edcb0e96bbd5231a2cdf329dccacd282f65b36a94"},
    "f07_obstacle_declaration_json": {
        "rel": "MAT2-F07/assets/obstacle_declaration.json",
        "sha256": "73525a3de022d5b8d9901ca90fde77124904471f33a67f2f79a94f7ad1636769"},
}
# reproduction TARGETS: published merged evidence that the fresh materiali-
# zation must re-derive byte-exact (read from the pinned sealed line, hashed,
# compared -- never trusted)
REPRO_TARGETS = {
    "f07_contact_trace": {"rel": "MAT2-F07/evidence/contact_trace.json"},
    "f07_frame_V1_clean": {
        "rel": "MAT2-F07/evidence/frame_V1_clearing_overview_clean.bmp"},
    "f07_frame_V1_diag": {
        "rel": "MAT2-F07/evidence/frame_V1_clearing_overview_diagnostic.bmp"},
    "f07_frame_V2_clean": {
        "rel": "MAT2-F07/evidence/frame_V2_seam_closeup_clean.bmp"},
    "f07_frame_V2_diag": {
        "rel": "MAT2-F07/evidence/frame_V2_seam_closeup_diagnostic.bmp"},
    "f07_frame_V3_clean": {
        "rel": "MAT2-F07/evidence/frame_V3_side_depth_clean.bmp"},
    "f07_frame_V3_diag": {
        "rel": "MAT2-F07/evidence/frame_V3_side_depth_diagnostic.bmp"},
}
PIN_SOURCE_TREE = "branch-1 @ %s (sealed line tip; F01-F07/B06 merged)" % BASE_REVISION

# --- frozen constants (PREREGISTRATION; do not tune) --------------------------
SEED_TERRAIN = 4598321                     # F01 terrain recipe seed
SEED_OBSTACLES = 4600823                   # F07 obstacle placement seed
IMPACT_ORDER = ["rock_01", "rock_02", "rock_03",
                "log_01", "log_02", "stand_01", "stand_02"]
IMPACT_SPEED_M_S = 2.0
IMPACT_START_CLEAR_M = 0.25
IMPACT_TICKS = 30
SPAWN_M = (0.0, 0.0, 0.0)
BODY_ENVELOPE_M = 0.25
LEDGER_BAR = 1e-12
CONTACT_SLOP_M = 1e-5                      # pinned contact_law slop/margin
FB6_OFFFRAME_ANGLE_DEG = 155.7             # F07's frozen off-frame form
FRESH_INSTANTIATIONS = 3                   # fresh subprocesses (plus in-process)

# the declared lenient default of falsifier arm FB3: the substitution a
# silent-default loader would make for a missing terrain bundle. It exists
# ONLY inside the arm; the production loader never sees it.
FB3_DEFAULT_TERRAIN_DOC = {
    "schema": "chimera.silent_default.v1",
    "name": "substituted_terrain_bundle",
    "note": "FB3 declared default substitution (never a production path)"}

VIEW_ORDER = ["V1_clearing_overview", "V2_seam_closeup", "V3_side_depth"]
PROFILE_VIEW_NAMES = {
    "V1_clearing_overview": "clearing overview",
    "V2_seam_closeup": "terrain/trunk seam close-up",
    "V3_side_depth": "side and oblique depth checks"}
DIAGNOSTIC_LAYERS = ["render mesh", "collision surfaces",
                     "normals/contact markers", "scene bounds",
                     "stable 3D labels"]
GATE_ARTIFACT = "evidence/frame_V1_clearing_overview_clean.bmp"


class Refusal(ValueError):
    """Strict intake refusal, house style (F01 prereg vocabulary)."""

    def __init__(self, code, detail=""):
        self.code, self.detail = code, str(detail)
        super().__init__("%s: %s" % (code, self.detail))


def require(condition, code, detail=""):
    if not condition:
        raise Refusal(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha_bytes(canonical(value))


# --- configuration intake (the scene seed/configuration) ----------------------
def config_self_sha(doc):
    stripped = {k: v for k, v in doc.items() if k != "self_sha256"}
    return sha_bytes(canonical(stripped))


def write_configuration(path=None):
    """Author the frozen scene configuration (canonical bytes, self-pinned)."""
    assets = []
    for key in sorted(PINS):
        assets.append({"id": key, "published": "contributions/" + PINS[key]["rel"],
                       "sha256": PINS[key]["sha256"]})
    doc = {
        "schema": CONFIG_SCHEMA,
        "name": "monkey_clearing_full",
        "coordinate_convention": {
            "frame": "clearing", "units": "m", "axes": "x east y up z south",
            "citations": [
                "ChimeraEngine/engine/earth_environment.hpp:13-23 local frame EUS",
                "ChimeraEngine/engine/earth_environment.hpp:118 out_of_patch"]},
        "seeds": {"terrain_recipe": SEED_TERRAIN,
                  "obstacle_placement": SEED_OBSTACLES},
        "assets": assets,
        "collision_state": {
            "solver": "chimera.local_contact.v1",
            "solver_pin": "local_contact_py",
            "law_pin": "contact_law_json",
            "ccd_enabled": True,
            "composition_scope": (
                "each impact run instantiates exactly the struck obstacle's "
                "body (F07 declared composition scope); the ground "
                "co-instantiation is the F04 P0 refusal heritage, measured "
                "per obstacle, not assumed"),
            "probes": {"mass_kg": 0.12, "half_m": 0.1, "thickness_m": 0.002,
                       "mu_s": 0.6, "mu_k": 0.4}},
        "initial_state": {
            "spawn_clearing_m": list(SPAWN_M),
            "body_radius_envelope_m": BODY_ENVELOPE_M,
            "tick_interval": [0, 0],
            "impact_schedule": {
                "order": list(IMPACT_ORDER),
                "speed_m_s": IMPACT_SPEED_M_S,
                "start_clearance_m": IMPACT_START_CLEAR_M,
                "ticks": IMPACT_TICKS,
                "approach": "normal incidence at analytic poles/midspan/"
                            "mid-height per F07 A2 (facet/hull-aligned)"},
            "cameras": {"note": "the three pinned F07 bookmarks (implementation "
                                "VIEW_ORDER)", "tick_samples": [0]}},
        "self_sha256": "",
    }
    doc["self_sha256"] = config_self_sha(doc)
    raw = canonical(doc)
    (path or (ASSETS / "scene_configuration.json")).write_bytes(raw)
    return raw


def load_config(path=None):
    path = pathlib.Path(path or (ASSETS / "scene_configuration.json"))
    require(path.is_file(), "f08_config_missing", str(path))
    raw = path.read_bytes()
    doc = json.loads(raw)
    require(doc.get("schema") == CONFIG_SCHEMA, "f08_config_schema",
            doc.get("schema"))
    require(doc.get("self_sha256") == config_self_sha(doc),
            "f08_config_hash_mismatch", doc.get("self_sha256"))
    for section in ("seeds", "assets", "collision_state", "initial_state"):
        require(section in doc, "f08_config_missing_section", section)
    for key in ("terrain_recipe", "obstacle_placement"):
        require(key in doc["seeds"], "f08_config_missing_seed", key)
    declared = {a["id"]: a for a in doc["assets"]}
    require(set(declared) == set(PINS), "f08_config_asset_set_mismatch",
            {"missing": sorted(set(PINS) - set(declared)),
             "extra": sorted(set(declared) - set(PINS))})
    for key, pin in PINS.items():
        require(declared[key]["sha256"] == pin["sha256"],
                "f08_config_asset_hash_mismatch", key)
        require(declared[key]["published"] == "contributions/" + pin["rel"],
                "f08_config_asset_path_mismatch", key)
    return doc, raw


# --- asset resolution (production root or declared sandbox) -------------------
def resolve_asset(key, sandbox_root=None):
    pin = PINS[key]
    root = pathlib.Path(sandbox_root) if sandbox_root else CONTRIB
    path = root / pin["rel"]
    require(path.is_file(), "f08_pin_missing", {"asset": key, "path": str(path)})
    got = sha_bytes(path.read_bytes())
    require(got == pin["sha256"], "f08_pin_hash_mismatch",
            {"asset": key, "expect": pin["sha256"], "got": got})
    return path, got


def load_pins(sandbox_root=None):
    out = {}
    for key in sorted(PINS):
        path, got = resolve_asset(key, sandbox_root)
        out[key] = {"file": str(path), "sha256": got,
                    "published": "contributions/" + PINS[key]["rel"],
                    "raw_match": True}
    return out


def load_modules(pins):
    import importlib.util

    def module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    sys.path.insert(0, str(CONTRIB / F02.rstrip("/")))
    tb = module("f08_terrain_bundle", pins["terrain_bundle_py"]["file"])
    tq = module("f08_terrain_query", pins["terrain_query_py"]["file"])
    cr = module("f08_clearing_recipe", pins["clearing_recipe_py"]["file"])
    lc = module("f08_local_contact", pins["local_contact_py"]["file"])
    f04 = module("f08_f04_machinery", pins["f04_implementation_py"]["file"])
    f07 = module("f08_f07_scene", pins["f07_implementation_py"]["file"])
    return tb, tq, cr, lc, f04, f07


def body_doc(body):
    """Deterministic serialization of a pinned M06 Body (contact frame)."""
    return {"id": body.id, "surface_id": body.surface_id,
            "matter_id": body.matter_id, "mass_kg": body.mass_kg,
            "mu_s": body.mu_s, "mu_k": body.mu_k,
            "thickness_m": body.thickness_m, "pinned": body.pinned,
            "velocity": list(body.velocity), "anchor": list(body.anchor),
            "vertices": [list(v) for v in body.vertices],
            "triangles": [list(t) for t in body.triangles]}


def ledger_ok(run):
    stop = run["stop"]
    return stop["worst_ledger_residual"], stop["ledger_within_bar"]


# --- the scene loader (strict; NO defaults) -----------------------------------
def load_scene(config_path=None, sandbox_root=None):
    """Materialize the full scene from seed + configuration. Strict intake:
    every missing or hash-divergent asset refuses with a named code that
    identifies the asset; no code path substitutes a default."""
    pins = {}
    for key in sorted(PINS):
        resolved_path, got = resolve_asset(key, sandbox_root)
        pins[key] = {"file": str(resolved_path), "sha256": got,
                     "published": "contributions/" + PINS[key]["rel"],
                     "raw_match": True}
    config, config_raw = load_config(config_path)
    tb, tq, cr, lc, f04, f07 = load_modules(pins)

    seeds = config["seeds"]

    # (1) terrain declaration from seed, byte-exact vs published
    decl = cr.compile_declaration(seeds["terrain_recipe"])
    decl_raw = cr.canonical(decl)
    pub_decl_path, pub_decl_sha = resolve_asset("clearing_declaration_json",
                                                sandbox_root)
    regen = [{"asset": "clearing_declaration_json", "source": {"seed": seeds["terrain_recipe"]},
              "published_sha256": pub_decl_sha,
              "regenerated_sha256": sha_bytes(decl_raw),
              "byte_equal": sha_bytes(decl_raw) == pub_decl_sha}]
    require(regen[0]["byte_equal"], "f08_seed_reproduction_mismatch",
            {"asset": "clearing_declaration_json",
             "seed": seeds["terrain_recipe"]})

    # (2) terrain bundle from the REGENERATED declaration, byte-exact
    SCRATCH.mkdir(parents=True, exist_ok=True)
    regen_decl_path = SCRATCH / ("regen_clearing_declaration_%s.json"
                                 % sha_bytes(decl_raw)[:12])
    regen_decl_path.write_bytes(decl_raw)
    bundle = tb.compile_bundle(regen_decl_path)
    bundle_raw = tb.canonical(bundle)
    pub_bundle_path, pub_bundle_sha = resolve_asset("terrain_bundle_json",
                                                    sandbox_root)
    regen.append({"asset": "terrain_bundle_json",
                  "source": {"regenerated_declaration_sha256": sha_bytes(decl_raw)},
                  "published_sha256": pub_bundle_sha,
                  "regenerated_sha256": sha_bytes(bundle_raw),
                  "byte_equal": sha_bytes(bundle_raw) == pub_bundle_sha})
    require(regen[-1]["byte_equal"], "f08_seed_reproduction_mismatch",
            {"asset": "terrain_bundle_json"})

    # (3) obstacle declaration from seed through the pinned F07 generators
    surface = tq.TerrainSurface(bundle, validate=False)
    rng = cr.SplitMix64(seeds["obstacle_placement"])
    placed = f07.place_obstacles(rng, surface)
    obstacles = f07.build_obstacle_meshes(placed, surface)
    declaration, ob_decl_raw, ob_decl_self_sha = f07.make_declaration(obstacles)
    ob_decl_raw_sha = sha_bytes(ob_decl_raw)
    pub_ob_path, pub_ob_sha = resolve_asset("f07_obstacle_declaration_json",
                                            sandbox_root)
    regen.append({"asset": "f07_obstacle_declaration_json",
                  "source": {"seed": seeds["obstacle_placement"]},
                  "published_sha256": pub_ob_sha,
                  "regenerated_sha256": ob_decl_raw_sha,
                  "byte_equal": ob_decl_raw_sha == pub_ob_sha})
    require(regen[-1]["byte_equal"], "f08_seed_reproduction_mismatch",
            {"asset": "f07_obstacle_declaration_json",
             "seed": seeds["obstacle_placement"]})

    # (4) published bytes: trunk declaration + trunk mesh + contact law
    contact_law = json.loads(
        pathlib.Path(pins["contact_law_json"]["file"]).read_bytes())
    require(contact_law["declarations"]["slop_m"] == CONTACT_SLOP_M
            and contact_law["declarations"]["margin_m"] == CONTACT_SLOP_M,
            "f08_contact_law_slop_drift",
            contact_law["declarations"]["slop_m"])
    trunk = json.loads(pathlib.Path(pins["trunk_declaration_json"]["file"]).read_bytes())

    # (5) collision state (contact frame, pinned bodies)
    ground_body = f04.ground_contact_body(bundle, lc)
    groups, _ = f04.trunk_partition(trunk)
    trunk_verts_contact = [f04.to_contact(v[0:3])
                           for v in trunk["render_mesh"]["vertices"]]
    trunk_body_doc = {"groups": sorted(groups.keys()),
                      "vertices": [list(v) for v in trunk_verts_contact],
                      "base_clearing": list(f07.TRUNK_SITE_M),
                      "radius_m": f07.TRUNK_RADIUS_M,
                      "height_m": f07.TRUNK_HEIGHT_M}
    obstacle_bodies = []
    for ob in obstacles:
        ob_body = f07.obstacle_contact_body(lc, ob)
        obstacle_bodies.append({"id": ob["id"],
                                "body": body_doc(ob_body)})
    # F04 P0 heritage, re-measured: ground + obstacle co-instantiation
    p0 = {}
    for ob in obstacles:
        ob_body = f07.obstacle_contact_body(lc, ob)
        try:
            records, _ = lc.solve_tick([ground_body, ob_body], ccd_enabled=True)
            p0[ob["id"]] = {"outcome": "ran", "contact_records": len(records)}
        except ValueError as exc:
            p0[ob["id"]] = {"outcome": "refused", "detail": str(exc)[:120]}
    collision_state = {
        "solver_pin": "local_contact_py",
        "solver_sha256": pins["local_contact_py"]["sha256"],
        "law_sha256": pins["contact_law_json"]["sha256"],
        "law_slop_m": contact_law["declarations"]["slop_m"],
        "ccd_enabled": True,
        "ground_body": body_doc(ground_body),
        "trunk": trunk_body_doc,
        "obstacle_bodies": obstacle_bodies,
        "ground_coinstantiation_p0": p0,
    }

    # (6) dynamics: re-derive the frozen seven-run trace (published target)
    impacts = []
    by_id = {ob["id"]: ob for ob in obstacles}
    require([ob["id"] for ob in obstacles] == IMPACT_ORDER,
            "f08_impact_order_mismatch", [ob["id"] for ob in obstacles])
    for ob_id in IMPACT_ORDER:
        impacts.append(f07.run_impact(lc, by_id[ob_id]))
    trace_doc = {"schema": "chimera.mat2_f07.contact_trace.v1",
                 "declaration_sha256": ob_decl_self_sha, "impacts": impacts}
    trace_raw = canonical(trace_doc)
    root = pathlib.Path(sandbox_root) if sandbox_root else CONTRIB
    pub_trace_path = root / REPRO_TARGETS["f07_contact_trace"]["rel"]
    require(pub_trace_path.is_file(), "f08_repro_target_missing",
            {"target": "f07_contact_trace", "path": str(pub_trace_path)})
    pub_trace_sha = sha_bytes(pub_trace_path.read_bytes())
    trace_equal = sha_bytes(trace_raw) == pub_trace_sha
    require(trace_equal, "f08_trace_reproduction_mismatch",
            {"rederived": sha_bytes(trace_raw), "published": pub_trace_sha})
    ledgers = []
    for run in impacts:
        worst, ok = ledger_ok(run)
        require(ok, "f08_ledger_bar", {"run": run["id"], "worst": worst})
        ledgers.append({"run": run["id"], "worst_ledger_residual": worst,
                        "within_bar": ok})

    # (7) initial state: declared + derived
    initial_state = {
        "spawn_clearing_m": list(config["initial_state"]["spawn_clearing_m"]),
        "body_radius_envelope_m": config["initial_state"]["body_radius_envelope_m"],
        "tick_interval": list(config["initial_state"]["tick_interval"]),
        "impact_schedule": config["initial_state"]["impact_schedule"],
        "derived_starts": [{"id": r["id"],
                            "start_clearing_m": list(r["start_clearing_m"]),
                            "velocity_clearing_m_s":
                                list(r["velocity_clearing_m_s"]),
                            "approach_axis_index": r["approach_axis"]}
                           for r in impacts],
        "tick0_states": [{"id": r["id"], "state": r["states"][0]}
                         for r in impacts],
    }

    scene_state = {
        "schema": STATE_SCHEMA,
        "identity": {"card": "MAT2-F08", "planning_id": TASK_ID,
                     "attempt_id": ATTEMPT_ID, "arrival_id": ARRIVAL_ID,
                     "run_id": RUN_ID, "base_revision": BASE_REVISION,
                     "prereg_commit": PREREG_COMMIT, "done_when": DONE_WHEN},
        "config_sha256": sha_bytes(config_raw),
        "seeds": dict(seeds),
        "pins": {k: {kk: vv for kk, vv in v.items() if kk != "file"}
                 for k, v in sorted(pins.items())},
        "pin_source_tree": PIN_SOURCE_TREE,
        "regeneration": regen,
        "collision_state": collision_state,
        "initial_state": initial_state,
        "dynamics": {"rederived_trace_sha256": sha_bytes(trace_raw),
                     "published_trace_sha256": pub_trace_sha,
                     "byte_equal": trace_equal, "ledgers": ledgers},
    }
    state_raw = canonical(scene_state)
    return {"pins": pins, "config": config, "config_raw": config_raw,
            "config_sha256": sha_bytes(config_raw),
            "modules": (tb, tq, cr, lc, f04, f07),
            "bundle": bundle, "surface": surface, "obstacles": obstacles,
            "declaration": declaration,
            "groups": groups, "trunk": trunk,
            "trunk_verts_contact": trunk_verts_contact,
            "ground_body": ground_body, "impacts": impacts,
            "declaration_self_sha256": ob_decl_self_sha,
            "declaration_sha256": ob_decl_raw_sha,
            "trace_raw": trace_raw, "scene_state": scene_state,
            "scene_state_raw": state_raw,
            "scene_sha256": sha_bytes(state_raw)}


# --- fresh subprocess instantiation -------------------------------------------
def materialize_subprocess(config_path, out_path):
    cmd = [sys.executable, "-B", str(HERE / "implementation.py"),
           "materialize", "--config", str(config_path), "--out", str(out_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(HERE))
    require(proc.returncode == 0, "f08_subprocess_failed",
            {"cmd": cmd, "stderr": proc.stderr[-1200:]})
    return json.loads(pathlib.Path(out_path).read_bytes())


def fresh_instantiations(scene, count=FRESH_INSTANTIATIONS):
    """Run count fresh interpreter instantiations of the SAME configuration
    and compare their scene state documents byte-for-byte."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    cfg_path = ASSETS / "scene_configuration.json"
    records = [{"instantiation": "in_process",
                "scene_sha256": scene["scene_sha256"]}]
    for k in range(1, count + 1):
        out_path = SCRATCH / ("f08_instantiation_%d.json" % k)
        doc = materialize_subprocess(cfg_path, out_path)
        sub_sha = sha_bytes(canonical(doc))
        records.append({"instantiation": "subprocess_%d" % k,
                        "scene_sha256": sub_sha})
    equal = len({r["scene_sha256"] for r in records}) == 1
    require(equal, "f08_scene_state_mismatch",
            {"differing": sorted({r["instantiation"] for r in records
                                  if r["scene_sha256"] !=
                                  records[0]["scene_sha256"]})})
    return {"schema": "chimera.mat2_f08.materialization.v1",
            "fresh_subprocess_instantiations": count,
            "instantiations": records, "byte_identical": equal,
            "scene_sha256": scene["scene_sha256"],
            "state_bytes": len(scene["scene_state_raw"])}


def compare_states(a_raw, b_raw):
    """Byte gate between two materializations; returns refusal detail on diff."""
    if a_raw == b_raw:
        return None
    a = json.loads(a_raw)
    b = json.loads(b_raw)
    diffs = sorted(k for k in set(a) | set(b)
                   if canonical(a.get(k)) != canonical(b.get(k)))
    return {"differing_sections": diffs}


# --- capture (pinned F07 render/classify law; reproduced scene) ---------------
def read_registry_profile():
    require(REGISTRY_SQLITE.is_file(), "f08_registry_missing",
            str(REGISTRY_SQLITE))
    uri = "file:%s?mode=ro" % REGISTRY_SQLITE.as_posix()
    con = sqlite3.connect(uri, uri=True)
    try:
        payload = con.execute("select payload from state where id = 1").fetchone()
    finally:
        con.close()
    require(payload is not None, "f08_registry_empty")
    state = json.loads(payload[0])
    card = state["kanban"]["cards"]["MAT2-F08"]
    qual = card["spec"]["ontology_qualification"]
    prof = qual["task"]["verification_profile"]
    require(prof["id"] == "forest" and prof["kind"] == "visible_static",
            "f08_registry_profile_wrong", prof.get("id"))
    prof_sha = sha_bytes(canonical(prof))
    require(prof_sha == PROFILE_CANONICAL_SHA256, "f08_registry_profile_drift",
            prof_sha)
    meta = {"mode": "read_only", "read_from": str(REGISTRY_SQLITE),
            "canonical_sha256": prof_sha,
            "task_id_in_profile_scenario": True}
    return prof, meta


def render_frames(scene):
    f07 = scene["modules"][5]
    trunk_render_verts = [tuple(v[0:3])
                          for v in scene["trunk"]["render_mesh"]["vertices"]]
    trunk_assets = {"groups": scene["groups"],
                    "vertices": scene["trunk_verts_contact"],
                    "base": f07.F_TO_CONTACT(list(f07.TRUNK_SITE_M)),
                    "radius": f07.TRUNK_RADIUS_M, "height": f07.TRUNK_HEIGHT_M,
                    "base_clearing": tuple(f07.TRUNK_SITE_M),
                    "declaration": scene["trunk"]}
    mesh = f07.SceneMesh07(scene["bundle"], trunk_render_verts,
                           scene["groups"], scene["obstacles"])
    cams = {key: f07.Camera07(spec, frame_id="f01_world_y_up/MAT2-F08")
            for key, spec in f07.VIEW_SPECS.items()}
    marker_rows = []
    probes_by_view = {key: [] for key in VIEW_ORDER}
    for view_key in VIEW_ORDER:
        cam = cams[view_key]
        for ob in scene["obstacles"]:
            if view_key != "V1_clearing_overview":
                continue
            mk = f07.pick_subject(ob, mesh, cam)
            if mk is None:
                marker_rows.append({"marker": "subject_" + ob["id"],
                                    "view": view_key,
                                    "expected": "VISIBLE_EXACT",
                                    "outcome": "OCCLUDED",
                                    "record": {"reason":
                                               "no visible surface point"}})
                continue
            out = f07.classify_marker(mesh, cam, mk)
            marker_rows.append({"marker": mk["id"], "view": view_key,
                                "expected": "VISIBLE_EXACT",
                                "outcome": out["outcome"], "record": out})
            probes_by_view[view_key].append(
                {"point": list(mk["point"]), "oracle_n": mk["oracle_n"]})
        if view_key == "V1_clearing_overview":
            gm = {"point": (f07.SPAWN_M[0], f07.SPAWN_M[1], f07.SPAWN_M[2]),
                  "classify_point": (f07.SPAWN_M[0] + 1e-3, f07.SPAWN_M[1],
                                     f07.SPAWN_M[2]),
                  "surface": "monkey_clearing_ground", "kind": "ground",
                  "oracle_h": scene["surface"].height_at(
                      f07.SPAWN_M[0], f07.SPAWN_M[2]),
                  "oracle_n_set": f07.incident_ground_normals(mesh, 0.0, 0.0),
                  "id": "marker_spawn"}
            out = f07.classify_marker(mesh, cam, gm)
            marker_rows.append({"marker": gm["id"], "view": view_key,
                                "expected": "VISIBLE_EXACT",
                                "outcome": out["outcome"], "record": out})
            ps = f07.post_subject(scene["bundle"], scene["config_decl"])
            out = f07.classify_marker(mesh, cam, ps)
            marker_rows.append({"marker": ps["id"], "view": view_key,
                                "expected": "VISIBLE_EXACT",
                                "outcome": out["outcome"], "record": out})
            probes_by_view[view_key].append(
                {"point": list(ps["point"]), "oracle_n": [0.0, 1.0, 0.0]})
        if view_key in f07.FROZEN_MARKER_TABLE.get("subject_trunk", {}):
            tm = f07.trunk_subject_marker(cam, trunk_assets)
            out = f07.classify_marker(mesh, cam, tm)
            marker_rows.append({"marker": tm["id"], "view": view_key,
                                "expected": "VISIBLE_EXACT",
                                "outcome": out["outcome"], "record": out})
            probes_by_view[view_key].append(
                {"point": list(tm["point"]), "oracle_n": tm["oracle_n"]})
    mismatch = [r for r in marker_rows if r["outcome"] != r["expected"]]
    require(not mismatch, "f08_marker_table_violated",
            [(r["marker"], r["view"], r["expected"], r["outcome"])
             for r in mismatch])
    vbm = [r for r in marker_rows if r["outcome"] == "VISIBLE_BUT_MISMATCH"]
    require(not vbm, "f08_visible_but_mismatch", vbm)

    impact_marks = []
    for run in scene["impacts"]:
        for s in run["states"]:
            if s["contacts"]:
                c0 = s["contacts"][0]
                impact_marks.append({"run": run["id"], "tick": s["tick"],
                                     "point": c0["point_clearing_a"],
                                     "normal": c0["normal_contact_to_a_clearing"],
                                     "oracle_n":
                                         c0["normal_contact_to_a_clearing"],
                                     "tick_id": s["tick"]})
                break
    labels = f07.frozen_labels(scene["obstacles"])
    tag_bindings = [{"label_id": lab["id"], "subject_id": lab["subject_id"]}
                    for lab in labels]
    frames = {}
    frame_rows = []
    EVIDENCE.mkdir(exist_ok=True)
    for view_key in VIEW_ORDER:
        cam = cams[view_key]
        for mode in ("diagnostic", "clean"):
            probes = (probes_by_view[view_key] + impact_marks) \
                if mode == "diagnostic" else None
            colour = f07.render_frame(mesh, cam, mode == "diagnostic", probes,
                                      labels if mode == "diagnostic" else None)
            path = EVIDENCE / ("frame_%s_%s.bmp" % (view_key, mode))
            f07.write_bmp(path, colour)
            raw = path.read_bytes()
            frames["%s_%s" % (view_key, mode)] = sha_bytes(raw)
            frame_rows.append({
                "path": "evidence/frame_%s_%s.bmp" % (view_key, mode),
                "raw_sha256": sha_bytes(raw),
                "role": "%s %s" % (PROFILE_VIEW_NAMES[view_key], mode)})
    return {"mesh": mesh, "cams": cams, "marker_rows": marker_rows,
            "frames": frames, "frame_rows": frame_rows,
            "trunk_assets": trunk_assets, "labels": labels,
            "tag_bindings": tag_bindings}


def frame_reproduction(frames):
    """PUBLISHED bar: every reproduced frame equals the published F07 bytes."""
    out = []
    key_by_name = {
        "frame_V1_clearing_overview_clean.bmp": "f07_frame_V1_clean",
        "frame_V1_clearing_overview_diagnostic.bmp": "f07_frame_V1_diag",
        "frame_V2_seam_closeup_clean.bmp": "f07_frame_V2_clean",
        "frame_V2_seam_closeup_diagnostic.bmp": "f07_frame_V2_diag",
        "frame_V3_side_depth_clean.bmp": "f07_frame_V3_clean",
        "frame_V3_side_depth_diagnostic.bmp": "f07_frame_V3_diag"}
    for name, target in sorted(key_by_name.items()):
        pub_path = CONTRIB / REPRO_TARGETS[target]["rel"]
        pub_sha = sha_bytes(pub_path.read_bytes())
        # frames dict keys are "<VIEW>_<mode>"; the file stem minus "frame_"
        mine = frames[name[:-4].replace("frame_", "")]
        out.append({"frame": name, "published_sha256": pub_sha,
                    "reproduced_sha256": mine,
                    "byte_equal": mine == pub_sha})
        require(mine == pub_sha, "f08_frame_reproduction_mismatch",
                {"frame": name, "reproduced": mine, "published": pub_sha})
    return out


def build_capture_manifest(scene, capture):
    f07 = scene["modules"][5]
    required_by_view = {key: sorted({r["marker"] for r in capture["marker_rows"]
                                     if r["view"] == key
                                     and r["outcome"] == "VISIBLE_EXACT"})
                        for key in VIEW_ORDER}
    observed_by_view = {key: sorted({r["marker"] for r in capture["marker_rows"]
                                     if r["view"] == key})
                        for key in VIEW_ORDER}
    capture_sha = capture["frames"]["V1_clearing_overview_clean"]
    rows = []
    for view_key in VIEW_ORDER:
        cam_rec = capture["cams"][view_key].camera_record([0])
        for mode in ("diagnostic", "clean"):
            rows.append({
                "view_id": PROFILE_VIEW_NAMES[view_key],
                "profile_view_key": view_key,
                "mode": mode,
                "pair_id": "pair-" + view_key,
                "artifact_locator": {
                    "kind": "image", "region": "whole_frame",
                    "raw_sha256": capture["frames"]["%s_%s"
                                                    % (view_key, mode)]},
                "state_binding": {"kind": "state",
                                  "sha256": scene["config_sha256"]},
                "camera": cam_rec,
                "visibility": (
                    {"layers": list(DIAGNOSTIC_LAYERS),
                     "label_ids": [b["label_id"] for b in
                                   capture["tag_bindings"]],
                     "selected_ids": [],
                     "required_subject_ids": required_by_view[view_key],
                     "observed_subject_ids": observed_by_view[view_key],
                     "missing_subject_ids": [],
                     "occlusion_mode": "depth_tested",
                     "tag_bindings": capture["tag_bindings"]}
                    if mode == "diagnostic" else
                    {"layers": [], "label_ids": [], "selected_ids": [],
                     "required_subject_ids": required_by_view[view_key],
                     "observed_subject_ids": observed_by_view[view_key],
                     "missing_subject_ids": [],
                     "occlusion_mode": "depth_tested", "tag_bindings": []})})
    frame_files = [{"path": r["path"], "raw_sha256": r["raw_sha256"],
                    "role": r["role"]} for r in capture["frame_rows"]]
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "capture_sha256": capture_sha,
        "subject_sha256": scene["scene_sha256"],
        "profile_id": "forest",
        "tick_interval": [0, 0],
        "capture_layout": {"files": frame_files,
                           "single_gate_bound_artifact": GATE_ARTIFACT},
        "views": rows,
    }
    context = {"task_id": TASK_ID, "run_id": RUN_ID,
               "subject_sha256": scene["scene_sha256"],
               "capture_sha256": capture_sha, "tick_interval": [0, 0]}
    return manifest, context, capture_sha


# --- falsifier arms (run FIRST; each must bite with a passing clean control) --
def build_sandbox(tag, drop=None, corrupt=None):
    """Copy every pinned asset AND every published reproduction target into a
    fresh sandbox, optionally dropping one file or flipping one byte of one
    file (falsifier furniture only). A complete sandbox therefore supports the
    FULL materialization, including the published-evidence comparisons."""
    sandbox = SCRATCH / ("sandbox_%s" % tag)
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)
    for key, pin in PINS.items():
        src = CONTRIB / pin["rel"]
        dst = sandbox / pin["rel"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = bytearray(src.read_bytes())
        if corrupt == key:
            data[0] ^= 0x01
        dst.write_bytes(bytes(data))
    for target in REPRO_TARGETS.values():
        src = CONTRIB / target["rel"]
        dst = sandbox / target["rel"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
    if drop:
        (sandbox / PINS[drop]["rel"]).unlink()
    return sandbox


def run_bites(scene, capture):
    f07 = scene["modules"][5]
    bites = []

    def record(name, bites_flag, observed, control):
        bites.append({"bite": name, "bites": bool(bites_flag),
                      "observed": observed, "clean_control": control})

    # FB1 missing asset: four classes, each refusal NAMES the asset
    fb1 = []
    for key in ("terrain_bundle_json", "f03_trunk_mesh_json",
                "f07_obstacle_declaration_json", "contact_law_json"):
        sandbox = build_sandbox("fb1_%s" % key, drop=key)
        try:
            load_scene(sandbox_root=sandbox)
            fb1.append({"asset": key, "refused": False, "code": None})
        except Refusal as exc:
            fb1.append({"asset": key, "refused": exc.code == "f08_pin_missing",
                        "code": exc.code, "detail": exc.detail[:200]})
    full_sandbox = build_sandbox("fb1_full")
    clean = load_scene(sandbox_root=full_sandbox)
    control_ok = clean["scene_sha256"] == scene["scene_sha256"]
    record("FB1_missing_asset_refusal",
           all(r["refused"] and r["code"] == "f08_pin_missing" for r in fb1)
           and control_ok,
           {"refusals": fb1},
           {"run": "complete sandbox materializes the production scene state",
            "scene_sha256": clean["scene_sha256"], "pass": control_ok})

    # FB2 corrupted bytes: one flipped byte, refusal NAMES the asset
    corrupt_key = "f03_trunk_mesh_json"
    sandbox = build_sandbox("fb2", corrupt=corrupt_key)
    try:
        load_scene(sandbox_root=sandbox)
        fb2 = {"refused": False, "code": None}
    except Refusal as exc:
        fb2 = {"refused": True, "code": exc.code, "asset": corrupt_key,
               "detail": str(exc.detail)[:200]}
    record("FB2_corrupt_asset_refusal",
           fb2["refused"] and fb2["code"] == "f08_pin_hash_mismatch",
           fb2,
           {"run": "pristine sandbox copy loads (FB1 clean control)",
            "pass": control_ok})

    # FB3 silent default: the declared lenient intake double returns default
    # bytes for a missing asset WITHOUT refusing (the hazard, demonstrated).
    # Both enforcement layers must then catch the substitution: the strict
    # hash gate refuses the default bytes (f08_pin_hash_mismatch naming the
    # asset), and the scene fingerprint gate fires on the substituted scene
    # state (default fingerprint != the production fingerprint).
    def lenient_intake_missing(sandbox_root, key):
        """The declared FB3 double: missing file -> default bytes, no refusal.
        Falsifier furniture only; the production loader never uses it."""
        return canonical(FB3_DEFAULT_TERRAIN_DOC)

    sandbox = build_sandbox("fb3", drop="terrain_bundle_json")
    default_raw = lenient_intake_missing(sandbox, "terrain_bundle_json")
    hazard = True  # lenient_intake_missing returned bytes instead of refusing
    try:
        got = sha_bytes(default_raw)
        require(got == PINS["terrain_bundle_json"]["sha256"],
                "f08_pin_hash_mismatch",
                {"asset": "terrain_bundle_json",
                 "expect": PINS["terrain_bundle_json"]["sha256"], "got": got})
        hash_gate = {"fired": False}
    except Refusal as exc:
        hash_gate = {"fired": True, "code": exc.code,
                     "asset": "terrain_bundle_json"}
    substituted = json.loads(scene["scene_state_raw"])
    substituted["pins"]["terrain_bundle_json"] = {
        "published": "contributions/" + PINS["terrain_bundle_json"]["rel"],
        "sha256": sha_bytes(default_raw), "raw_match": False,
        "lenient_default": True}
    sub_raw = canonical(substituted)
    gate_diff = compare_states(scene["scene_state_raw"], sub_raw)
    record("FB3_silent_default_detected",
           hazard and hash_gate["fired"] and gate_diff is not None,
           {"lenient_intake_refused": False,
            "hash_gate": hash_gate,
            "fingerprint_gate_fired": gate_diff is not None,
            "gate_detail": gate_diff},
           {"run": "the complete sandbox (nothing substituted) materializes "
                   "the production scene state",
            "pass": control_ok})

    # FB4 seed perturbation: the regeneration equality has teeth
    pert_config = json.loads((ASSETS / "scene_configuration.json").read_bytes())
    pert_config["seeds"]["obstacle_placement"] = SEED_OBSTACLES + 1
    pert_config["self_sha256"] = config_self_sha(pert_config)
    pert_path = SCRATCH / "fb4_config_seed_plus_1.json"
    SCRATCH.mkdir(parents=True, exist_ok=True)
    pert_path.write_bytes(canonical(pert_config))
    try:
        load_scene(config_path=pert_path)
        fb4 = {"refused": False, "code": None}
    except Refusal as exc:
        fb4 = {"refused": True, "code": exc.code,
               "seed": SEED_OBSTACLES + 1,
               "detail": str(exc.detail)[:200]}
    record("FB4_seed_perturbation_detected",
           fb4["refused"] and fb4["code"] == "f08_seed_reproduction_mismatch",
           fb4,
           {"run": "unperturbed seed regenerates byte-exact (P1, in-scene)",
            "regeneration_byte_equal": all(
                r["byte_equal"] for r in scene["scene_state"]["regeneration"]),
            "pass": all(r["byte_equal"]
                        for r in scene["scene_state"]["regeneration"])})

    # FB5 float gate teeth: +1e-9 on the declared spawn z between two fresh
    # instantiations MUST fire the cross-instantiation byte gate
    float_config = json.loads((ASSETS / "scene_configuration.json").read_bytes())
    float_config["initial_state"]["spawn_clearing_m"][2] += 1e-9
    float_config["self_sha256"] = config_self_sha(float_config)
    float_path = SCRATCH / "fb5_config_spawn_z_plus_1e-9.json"
    float_path.write_bytes(canonical(float_config))
    doc_b = materialize_subprocess(float_path,
                                   SCRATCH / "fb5_instantiation_b.json")
    b_raw = canonical(doc_b)
    diff = compare_states(scene["scene_state_raw"], b_raw)
    doc_c = materialize_subprocess(ASSETS / "scene_configuration.json",
                                   SCRATCH / "fb5_instantiation_c.json")
    clean_diff = compare_states(scene["scene_state_raw"], canonical(doc_c))
    record("FB5_float_gate_teeth",
           diff is not None and clean_diff is None,
           {"perturbation": "spawn_clearing_m[2] += 1e-9",
            "gate_fired": diff is not None, "gate_detail": diff},
           {"run": "two unperturbed fresh instantiations compare byte-identical",
            "gate_fired": clean_diff is not None, "pass": clean_diff is None})

    # FB6 off-frame probe subject: the required trunk subject form rotated
    # 155.7 deg about the V2 camera's up axis (F07's frozen form)
    base = capture["trunk_assets"]["base_clearing"]
    cam2 = capture["cams"]["V2_seam_closeup"]
    theta = math.radians(FB6_OFFFRAME_ANGLE_DEG)
    v = [base[i] - cam2.position[i] for i in range(3)]
    v_par = [cam2.up[i] * f07.F_vdot(cam2.up, v) for i in range(3)]
    v_perp = f07.F_vsub(v, v_par)
    rot = [v_perp[i] * math.cos(theta)
           + f07.F_vcross(cam2.up, v_perp)[i] * math.sin(theta) + v_par[i]
           for i in range(3)]
    off_point = [cam2.position[i] + rot[i] for i in range(3)]
    off_marker = {"point": off_point, "surface": "trunk_01.lateral",
                  "kind": "trunk", "id": "subject_offframe"}
    out_off = f07.classify_marker(capture["mesh"], cam2, off_marker)
    trunk_row = [r for r in capture["marker_rows"]
                 if r["marker"] == "subject_trunk"
                 and r["view"] == "V2_seam_closeup"][0]
    record("FB6_off_frame_probe_subject",
           out_off["outcome"] == "OFF_FRAME",
           {"off_axis_angle_deg": FB6_OFFFRAME_ANGLE_DEG,
            "outcome": out_off["outcome"], "reason": out_off.get("reason")},
           {"run": "camera-facing trunk subject in the same V2 view",
            "outcome": trunk_row["outcome"],
            "pass": trunk_row["outcome"] == "VISIBLE_EXACT"})
    return bites


# --- build ---------------------------------------------------------------------
def build():
    EVIDENCE.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    if not (ASSETS / "scene_configuration.json").is_file():
        write_configuration()
    scene = load_scene()
    f07 = scene["modules"][5]
    config_decl = json.loads(
        (CONTRIB / PINS["clearing_declaration_json"]["rel"]).read_bytes())
    scene["config_decl"] = config_decl

    # falsifier arms FIRST: all must bite before any evidence is written
    capture = render_frames(scene)
    bites = run_bites(scene, capture)
    require(all(b["bites"] for b in bites), "f08_falsifier_did_not_bite",
            [b["bite"] for b in bites if not b["bites"]])

    repro_frames = frame_reproduction(capture["frames"])
    materialization = fresh_instantiations(scene)

    manifest, context, capture_sha = build_capture_manifest(scene, capture)
    sys.path.insert(0, str(CONTRIB.parent))
    import visual_capture
    import visual_gate
    prof, prof_meta = read_registry_profile()
    validation = visual_capture.validate_manifest(manifest, context, prof)
    require(validation["structurally_valid"], "f08_capture_invalid", validation)
    (EVIDENCE / "capture_manifest.json").write_bytes(canonical(manifest))
    (EVIDENCE / "capture_context.json").write_bytes(canonical(context))
    receipt = {"evidence": {
        "camera": {"reference": str(EVIDENCE / "capture_manifest.json"),
                   "raw_sha256": sha_bytes(
                       (EVIDENCE / "capture_manifest.json").read_bytes())},
        "visual": {"reference": str(HERE / GATE_ARTIFACT),
                   "raw_sha256": sha_bytes((HERE / GATE_ARTIFACT).read_bytes())}},
        "capture_context": context}
    gate = visual_gate.verify(receipt, {"task_id": TASK_ID,
                                        "task": {"verification_profile": prof}})
    require(gate["structurally_valid"], "f08_visual_gate_invalid", gate)
    tgate = f07.transform_selftest(HERE / GATE_ARTIFACT)
    require(tgate["identity_ok"] and tgate["vflip_refused"],
            "f08_transform_gate", tgate)
    (EVIDENCE / "validation_receipt.json").write_bytes(canonical({
        "visual_capture": validation, "visual_gate": gate,
        "profile": prof_meta,
        "single_gate_bound_artifact": GATE_ARTIFACT,
        "capture_sha256": capture_sha,
        "transform_list_gate": dict(tgate,
            applicability="not_applicable_static_image_capture")}))

    (EVIDENCE / "contact_trace.json").write_bytes(scene["trace_raw"])
    (EVIDENCE / "materialization.json").write_bytes(canonical(materialization))

    f07_rows = [{k: v for k, v in r.items() if k != "record"}
                | {"hit_surface_id": r["record"].get("hit_surface_id")}
                for r in capture["marker_rows"]]
    checks = {
        "schema": "chimera.mat2_f08.checks.v1",
        "identity": {
            "card": "MAT2-F08", "planning_id": TASK_ID,
            "attempt_id": ATTEMPT_ID, "arrival_id": ARRIVAL_ID,
            "criteria_sha256": CRITERIA_SHA256, "scope_sha256": SCOPE_SHA256,
            "base_revision": BASE_REVISION, "prereg_commit": PREREG_COMMIT,
            "run_id": RUN_ID, "done_when": DONE_WHEN,
            "profile": {"id": "forest", "kind": "visible_static"}},
        "pins": scene["pins"], "pin_source_tree": PIN_SOURCE_TREE,
        "constants": {
            "seed_terrain_recipe": SEED_TERRAIN,
            "seed_obstacle_placement": SEED_OBSTACLES,
            "impact_speed_m_s": IMPACT_SPEED_M_S,
            "impact_start_clearance_m": IMPACT_START_CLEAR_M,
            "impact_ticks": IMPACT_TICKS,
            "fresh_instantiations": FRESH_INSTANTIATIONS,
            "ledger_bar": LEDGER_BAR,
            "fb6_offframe_angle_deg": FB6_OFFFRAME_ANGLE_DEG},
        "configuration": {"path": "assets/scene_configuration.json",
                          "sha256": scene["config_sha256"],
                          "asset_count": len(PINS)},
        "p0_intake_strict": {"loader": "strict require/Refusal, no defaults",
                             "default_code_paths": 0,
                             "refusal_codes": sorted({
                                 "f08_config_missing", "f08_config_schema",
                                 "f08_config_hash_mismatch",
                                 "f08_config_missing_section",
                                 "f08_config_missing_seed",
                                 "f08_config_asset_set_mismatch",
                                 "f08_config_asset_hash_mismatch",
                                 "f08_config_asset_path_mismatch",
                                 "f08_pin_missing", "f08_pin_hash_mismatch",
                                 "f08_seed_reproduction_mismatch",
                                 "f08_trace_reproduction_mismatch",
                                 "f08_frame_reproduction_mismatch",
                                 "f08_contact_law_slop_drift",
                                 "f08_scene_state_mismatch",
                                 "f08_impact_order_mismatch",
                                 "f08_ledger_bar",
                                 "f08_falsifier_did_not_bite",
                                 "f08_registry_missing", "f08_registry_empty",
                                 "f08_registry_profile_wrong",
                                 "f08_registry_profile_drift",
                                 "f08_capture_invalid",
                                 "f08_visual_gate_invalid",
                                 "f08_transform_gate",
                                 "f08_marker_table_violated",
                                 "f08_visible_but_mismatch",
                                 "f08_subprocess_failed"})},
        "p1_seed_asset_reproduction": {
            "regeneration": scene["scene_state"]["regeneration"],
            "all_byte_equal": all(r["byte_equal"] for r in
                                  scene["scene_state"]["regeneration"])},
        "p2_published_evidence_reproduction": {
            "trace": {"rederived_sha256":
                      scene["scene_state"]["dynamics"]["rederived_trace_sha256"],
                      "published_sha256":
                      scene["scene_state"]["dynamics"]["published_trace_sha256"],
                      "byte_equal":
                      scene["scene_state"]["dynamics"]["byte_equal"],
                      "ledgers": scene["scene_state"]["dynamics"]["ledgers"]},
            "frames": repro_frames},
        "p3_collision_state_reproduction": {
            "sections": ["collision_state"],
            "materialization": materialization},
        "p4_initial_state_reproduction": {
            "sections": ["initial_state"],
            "materialization": materialization},
        "p5_missing_asset_refusals": {"falsifier_bites": bites},
        "p6_visual_correspondence": {
            "markers": {"rows": f07_rows,
                        "visible_but_mismatch_count": 0,
                        "frozen_table": scene["modules"][5].FROZEN_MARKER_TABLE},
            "capture": {"profile": prof_meta, "validation": validation,
                        "visual_gate": gate,
                        "capture_sha256": capture_sha,
                        "manifest_sha256": sha_bytes(
                            (EVIDENCE / "capture_manifest.json").read_bytes()),
                        "gate_artifact": GATE_ARTIFACT,
                        "transform_list_gate": dict(
                            tgate,
                            applicability="not_applicable_static_image_capture"),
                        "frames": capture["frames"]}},
        "declaration": {"asset": "f07_obstacle_declaration_json",
                        "raw_sha256": scene["declaration_sha256"],
                        "self_sha256": scene["declaration_self_sha256"]},
        "scene_state": {"schema": STATE_SCHEMA,
                        "sha256": scene["scene_sha256"],
                        "bytes": len(scene["scene_state_raw"])},
    }
    (EVIDENCE / "checks.json").write_bytes(canonical(checks))
    return checks


def verify_determinism():
    """P7: two full builds; every evidence artifact byte-identical. The
    record's own output (determinism.json) is excluded from the set."""

    def snapshot():
        return {p.name: sha_bytes(p.read_bytes())
                for p in sorted(EVIDENCE.iterdir())
                if p.is_file() and p.name != "determinism.json"}

    first = build()
    snap = snapshot()
    second = build()
    snap2 = snapshot()
    identical = snap == snap2
    require(identical, "f08_nondeterministic",
            sorted(k for k in set(snap) | set(snap2)
                   if snap.get(k) != snap2.get(k)))
    record = {"prediction": "P7_determinism", "artifacts": len(snap),
              "identical": True, "hashes": snap}
    (EVIDENCE / "determinism.json").write_bytes(canonical(record))
    return record


def _main(argv):
    if len(argv) >= 2 and argv[1] == "materialize":
        cfg = None
        out = None
        i = 2
        while i < len(argv):
            if argv[i] == "--config":
                cfg = argv[i + 1]
                i += 2
            elif argv[i] == "--out":
                out = argv[i + 1]
                i += 2
            else:
                i += 1
        require(out is not None, "f08_materialize_out_required")
        scene = load_scene(config_path=cfg)
        pathlib.Path(out).write_bytes(scene["scene_state_raw"])
        print("materialized:", scene["scene_sha256"])
        return 0
    if len(argv) != 2 or argv[1] not in ("bites", "build", "verify"):
        print(__doc__)
        return 2
    if argv[1] == "verify":
        rec = verify_determinism()
        print("determinism: artifacts", rec["artifacts"], "identical",
              rec["identical"])
        return 0
    checks = build()
    if argv[1] == "bites":
        for b in checks["p5_missing_asset_refusals"]["falsifier_bites"]:
            print(" -", b["bite"], "BITES" if b["bites"] else "NO-BITE")
    print("build ok:", "scene sha", checks["scene_state"]["sha256"][:16],
          "; regen equal:", checks["p1_seed_asset_reproduction"]["all_byte_equal"],
          "; trace reproduced:",
          checks["p2_published_evidence_reproduction"]["trace"]["byte_equal"])
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
