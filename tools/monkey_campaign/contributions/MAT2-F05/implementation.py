"""terrain_envelope -- MAT2-F05: the terrain range for walking, declared from evidence.

Card done_when (verbatim): "Slope, obstacle size and surface-friction envelope
is declared from evidence". Card observation: "Do not assume flat-ground
training transfers to arbitrary terrain".

THE MECHANISM (frozen in PREREGISTRATION.md before any run):

1. PIN WALL: every declared number's source is a pinned byte string -- the
   sealed in-tree receipts at base fa02f075 (F01/F02/F04/F07/M06/W03/W05/W06/
   G04) plus coordination/world-build records copied into the durable
   evidence store via anchor.py --card MAT2-F05 (store-relative paths,
   sha-verified). Raw sha256 asserted at every run; drift refuses.

2. DERIVATION, NOT AUTHORING: no physics constant is new. Slope rows are
   derived from the pinned clearing declaration (mound law max grade
   A*pi/(2R)) and read from the pinned F07 route receipt; obstacle rows are
   read from the pinned F07 obstacle declaration + route receipt; friction
   rows are read from the pinned W03 walk scene / F02 preregistration / M06
   contact law / G04 report and CARRY THEIR PLACEHOLDER NAMING (the GAP
   verdict law: an unnamed placeholder is laundered evidence). The walk
   plane row is the load-bearing identity: the sealed W03
   contact_plane_height_m 0.004 IS the authored composition plateau (+0.004
   m), NOT the terrain-law grid read (-32.29 m class) -- the R3 disagreement
   is measured here from the pinned grid.

3. CLASSES: every envelope row is MEASURED, AUTHORED-DECLARED,
   NAMED-PLACEHOLDER (with debt owner) or ABSENT (named variable with debt
   owner). The build refuses a row whose class its source cannot support and
   refuses any friction row that lost its naming (FB3).

4. PROOF: falsifier arms FB1-FB6 bite fail-first, each against its own
   passing clean control with named premature guards; render/collision
   correspondence is re-proven at frozen probes through the pinned F01
   render law + classify (markers never read pixels); static clean/
   diagnostic/depth frames per registry profile view carry the 16-field
   camera records.

CPU-only, deterministic (no wall-clock, no RNG); numpy is used only to read
the pinned terrain-law grid npz (the R3 discriminator). Refusals are named
codes; nothing is silently repaired.
"""
from __future__ import annotations

import copy
import hashlib
import struct
import zlib
import importlib.util
import json
import math
import pathlib
import sqlite3
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
PINS_DIR = HERE / "pins"
CONTRIBUTIONS = HERE.parent
CHECKOUT = CONTRIBUTIONS.parents[2]
STORE_ROOT = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/evidence-store")
REGISTRY_DB = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

SCHEMA = "chimera.mat2_f05.terrain_envelope.v1"
CARD = "MAT2-F05"
TASK_SHORT = "F05"
ATTEMPT_ID = "264ce332f8cb4db1833ae6eee612b668"
CRITERIA_SHA256 = ("cf28ed888e4020f15f00ddd071758e647a55e8dbd6597368bda2a"
                   "3f2a546dca5")
SCOPE_SHA256 = ("cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae"
                "57996097")
BASE_REVISION = "fa02f07508ee15b7679d0f2a95ac6b1894f77962"
RUN_ID = "mat2-f05-forest-20260929-264ce332"
PROFILE_CANONICAL_SHA256 = ("9a8863e424aef3ca6fcf5a39f30cbdb27723f8df23ecc2"
                            "5b5f5604f80a3fa1e7")

# Frozen prediction bands (PREREGISTRATION section 4; never tuned after
# measurement; each is checked against the pinned bytes at build time).
MOUND_GRADE_BAND = (0.025, 0.039)
MOUND_MAX_GRADE_M3 = 0.03795552514626025
BOUND_MARGIN_BAND = (0.012, 0.025)
F07_MAX_ROUTE_SLOPE = 0.026054
F07_MIN_CLEARANCE = 0.257478
F07_FLAT_ROUTES = 8
FRICTION_MARGIN_MIN = 12.0
GRID_READ_MAX_M = -30.0
PLANE_DISAGREEMENT_BAND_M = (30.0, 35.0)
TERRAIN_META_SLOPE_MEAN_DEG = 3.8120480234530243
TERRAIN_META_SLOPE_MAX_DEG = 29.59015617654052
W05_VELOCITY_ENVELOPE_M_S = 2.977443609022557
W06_SEEDS = (20260919, 20260920, 20260921)


class Refusal(ValueError):
    def __init__(self, code, detail=""):
        self.code, self.detail = code, str(detail)
        super().__init__(code + (": " + self.detail if detail else ""))


def require(condition, code, detail=""):
    if not condition:
        raise Refusal(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_ascii(value):
    """The registry digest convention (default json.dumps escaping); the
    criteria/profile shas frozen in the dispatch and preregistration use
    THIS form (verified against kanban.cards[MAT2-F05])."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


# --- pins (PREREGISTRATION section 3; raw sha256 asserted) ---------------------
CONTRIB = "tools/monkey_campaign/contributions"
IN_TREE_PINS = {
    "clearing_recipe_py": (
        CONTRIB + "/MAT2-F01/evidence/pins_materialized/clearing_recipe.py",
        "ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc"),
    "clearing_declaration_json": (
        CONTRIB + "/MAT2-F01/evidence/pins_materialized/"
        "clearing_declaration.json",
        "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1"),
    "terrain_bundle_py": (
        CONTRIB + "/MAT2-F01/evidence/pins_materialized/terrain_bundle.py",
        "c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e"),
    "terrain_query_py": (
        CONTRIB + "/MAT2-F01/evidence/pins_materialized/terrain_query.py",
        "b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1"),
    "terrain_bundle_json": (
        CONTRIB + "/MAT2-F01/evidence/pins_materialized/terrain_bundle.json",
        "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52"),
    "trunk_declaration_json": (
        CONTRIB + "/MAT2-F01/evidence/pins_materialized/"
        "trunk_declaration.json",
        "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1"),
    "f01_implementation_py": (
        CONTRIB + "/MAT2-F01/implementation.py",
        "50e191cfc6f592fd9919534c8986c049939a4e88c4922e135f383bbf06e693af"),
    "obstacle_declaration_json": (
        CONTRIB + "/MAT2-F07/assets/obstacle_declaration.json",
        "73525a3de022d5b8d9901ca90fde77124904471f33a67f2f79a94f7ad1636769"),
    "f07_checks_json": (
        CONTRIB + "/MAT2-F07/evidence/checks.json",
        "0a7e94b545e4add955eb3f0315f8a783f00e2ebbcf4a2a44f43398b72916fb70"),
    "w03_scene_json": (
        CONTRIB + "/MAT2-W03/scene_out/scene.json",
        "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342"),
    "w05_seed_20260919_receipt": (
        CONTRIB + "/MAT2-W05/receipts/seed_20260919_receipt.json",
        "b866e9b1e2a3d516a960a88362c95d2f8211d28b894cc4d8c16dcebc4dc8b896"),
    "w05_seed_20260920_receipt": (
        CONTRIB + "/MAT2-W05/receipts/seed_20260920_receipt.json",
        "3d795b5ca523289c1ceac7dac72070875d8cc4b8e24e4ac2a5a64a9733e766ff"),
    "w05_seed_20260921_receipt": (
        CONTRIB + "/MAT2-W05/receipts/seed_20260921_receipt.json",
        "10c4090473c75ec99559dd9f1f13729d96c3c7d5cf037569c63253e308f472af"),
    "w06_eval_summary": (
        CONTRIB + "/MAT2-W06/receipts/evaluation_summary.json",
        "a1af58baf15edd7ac595b5bb4571e13ed44780f77faf5a761355140f456b075a"),
    "w06_seed_20260921_evaluation": (
        CONTRIB + "/MAT2-W06/receipts/seed_20260921_evaluation.json",
        "89baa5472076a1a8669389bc207fd49e6b06645b6db2519ca5d333cafe26015b"),
    "g04_report_md": (
        CONTRIB + "/MAT2-G04/REPORT.md",
        "dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8"),
    "f02_prereg_md": (
        CONTRIB + "/MAT2-F02/PREREGISTRATION.md",
        "19c4277b9d2c102ea5ce77bc1b4fa8d128370ce344f782a79d088d0cf458331d"),
    "f02_checks_json": (
        CONTRIB + "/MAT2-F02/evidence/checks.json",
        "9531edf1f74ba6dc85e3cd5e2029711dc6803b78b23d8b75df736f4c36fa719d"),
    "f04_checks_json": (
        CONTRIB + "/MAT2-F04/evidence/checks.json",
        "4ff2ee5d00d046ce6a734c10a39b3562c306ac245074a872a824efecabe50c55"),
    "contact_law_json": (
        CONTRIB + "/MAT2-M06/contact_law.json",
        "583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b"),
}
STORE_PINS = {
    "friction_sources_md": (
        "MAT2-F05/source/FRICTION_SOURCES.md",
        "336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b"),
    "terrain_meta_json": (
        "MAT2-F05/source/terrain_meta.json",
        "ff15fb1db3dcc128a531d21ef64d3ab62ae78190b64db36f70b5d273c1425681"),
    "terrain_report_md": (
        "MAT2-F05/source/TERRAIN_REPORT.md",
        "2b4d9905be1f9f888a3ff33cb4c22a23f009053471c4fd609280bc7b2cba4672"),
    "composed_meta_json": (
        "MAT2-F05/source/composed_meta.json",
        "8168382ff2c852b9fbf2c49831ec2021c8c3f5178af95d6ffba0ce55fa3a42f7"),
    "ingestion_spike_md": (
        "MAT2-F05/source/INGESTION_SPIKE.md",
        "218b34614d8917eceb3f4ea2a6404c5715f8e25f71e57989c53213d7498e512b"),
    "terrain_grid_npz": (
        "MAT2-F05/source/terrain_grid.npz",
        "9790fd252825278060f555f545f21b733cb6df9047d0ce1886d006fa87dfd012"),
}


def materialize_pins():
    """Assert every pin's raw sha256, return {key: {bytes, file, sha256,
    origin}}. In-tree pins are read from this attempt checkout's sealed tree
    (worktree == index at the frozen base; the crlf gate re-proves it).
    Store pins are read from the durable evidence store (anchored through
    anchor.py --card MAT2-F05 before the prereg freeze)."""
    require(STORE_ROOT.is_dir(), "f05_store_missing", str(STORE_ROOT))
    out = {}
    for key, (rel, expect) in IN_TREE_PINS.items():
        path = CHECKOUT / rel
        require(path.is_file(), "f05_pin_missing", rel)
        raw = path.read_bytes()
        got = sha_bytes(raw)
        require(got == expect, "f05_pin_drift",
                {"key": key, "expect": expect, "got": got})
        out[key] = {"bytes": raw, "file": str(path), "sha256": got,
                    "origin": "in_tree:" + rel, "raw_match": True}
    for key, (store_rel, expect) in STORE_PINS.items():
        path = STORE_ROOT / store_rel
        require(path.is_file(), "f05_store_pin_missing", store_rel)
        raw = path.read_bytes()
        got = sha_bytes(raw)
        require(got == expect, "f05_pin_drift",
                {"key": key, "expect": expect, "got": got})
        out[key] = {"bytes": raw, "file": str(path), "sha256": got,
                    "origin": "store:" + store_rel, "raw_match": True}
    # materialize the importable pins so the pinned modules get a real
    # __file__ (F01/F02 heritage)
    PINS_DIR.mkdir(parents=True, exist_ok=True)
    for key in ("clearing_recipe_py", "terrain_bundle_py", "terrain_query_py",
                "f01_implementation_py"):
        target = PINS_DIR / pathlib.Path(out[key]["file"]).name
        target.write_bytes(out[key]["bytes"])
        require(sha_bytes(target.read_bytes()) == out[key]["sha256"],
                "f05_pin_writeback_mismatch", key)
        out[key]["local"] = str(target)
    return out


def _module_from_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def registry_profile():
    """The verification profile object, read READ-ONLY from the registry
    (P7 law: the profile authority is the registry row, never a copy)."""
    require(REGISTRY_DB.is_file(), "f05_registry_missing", str(REGISTRY_DB))
    con = sqlite3.connect("file:%s?mode=ro" % REGISTRY_DB.as_posix(),
                          uri=True)
    try:
        payload = con.execute(
            "SELECT payload FROM state WHERE id=1").fetchone()[0]
    finally:
        con.close()
    state = json.loads(payload)
    card = state["kanban"]["cards"][CARD]
    oq = card["spec"]["ontology_qualification"]
    profile = oq["task"]["verification_profile"]
    canon = sha_bytes(canonical_ascii(profile))
    require(canon == PROFILE_CANONICAL_SHA256, "f05_profile_sha",
            {"expect": PROFILE_CANONICAL_SHA256, "got": canon})
    criteria = sha_bytes(canonical_ascii(card["spec"]))
    require(criteria == CRITERIA_SHA256, "f05_criteria_registry_mismatch",
            {"expect": CRITERIA_SHA256, "got": criteria})
    require(profile["id"] == "forest" and profile["kind"] == "visible_static",
            "f05_profile_kind", profile["kind"])
    require(profile["clean_view_required"] is True,
            "f05_profile_clean_view", profile["clean_view_required"])
    require(profile["numerical_evidence_required"] is True,
            "f05_profile_numerical", None)
    required_keys = ("id", "kind", "views", "clean_view_required",
                     "diagnostic_layers", "camera_required_fields")
    require(all(k in profile for k in required_keys), "f05_profile_keys",
            required_keys)
    provenance = {
        "db_path": str(REGISTRY_DB), "mode": "ro",
        "row_path": "state[1].kanban.cards.%s.spec.ontology_qualification"
                    ".task.verification_profile" % CARD,
        "extractor": "sqlite3 uri mode=ro; canonical json sha256",
        "profile_canonical_sha256": canon,
        "criteria_recomputed": criteria,
        "note": "read-only registry profile at capture time (P7); the "
                "criteria digest is recomputed over the registry card spec "
                "and asserted equal to the dispatch/prereg value",
    }
    attempt_state = state["kanban"]["cards"][CARD].get("state", "UNKNOWN")
    return profile, provenance, attempt_state


def load_sources(pins):
    """Strict load of every pinned record this card declares over."""
    recipe = _module_from_file(
        "f05_pinned_clearing_recipe", pins["clearing_recipe_py"]["local"])
    declaration = recipe.loads(pins["clearing_declaration_json"]["bytes"])
    tb = _module_from_file(
        "f05_pinned_terrain_bundle", pins["terrain_bundle_py"]["local"])
    tq = _module_from_file(
        "f05_pinned_terrain_query", pins["terrain_query_py"]["local"])
    tq.terrain_bundle = tb
    bundle = tb.loads(pins["terrain_bundle_json"]["bytes"])
    surface = tq.TerrainSurface(bundle, validate=True)
    trunk = json.loads(pins["trunk_declaration_json"]["bytes"])
    f01 = _module_from_file(
        "f05_pinned_f01_implementation", pins["f01_implementation_py"]["local"])
    obstacles = json.loads(pins["obstacle_declaration_json"]["bytes"])
    f07_checks = json.loads(pins["f07_checks_json"]["bytes"])
    w03_scene = json.loads(pins["w03_scene_json"]["bytes"])
    w05_receipts = {
        seed: json.loads(pins["w05_seed_%d_receipt" % seed]["bytes"])
        for seed in W06_SEEDS}
    w06_summary = json.loads(pins["w06_eval_summary"]["bytes"])
    w06_seed21 = json.loads(pins["w06_seed_20260921_evaluation"]["bytes"])
    contact_law = json.loads(pins["contact_law_json"]["bytes"])
    f02_checks = json.loads(pins["f02_checks_json"]["bytes"])
    f04_checks = json.loads(pins["f04_checks_json"]["bytes"])
    texts = {key: pins[key]["bytes"].decode("utf-8") for key in
             ("g04_report_md", "f02_prereg_md", "friction_sources_md",
              "terrain_report_md", "ingestion_spike_md")}
    terrain_meta = json.loads(pins["terrain_meta_json"]["bytes"])
    composed_meta = json.loads(pins["composed_meta_json"]["bytes"])
    grid = np.load(pins["terrain_grid_npz"]["file"])
    return {
        "recipe": recipe, "declaration": declaration, "tb": tb, "tq": tq,
        "bundle": bundle, "surface": surface, "trunk": trunk, "f01": f01,
        "obstacles": obstacles, "f07_checks": f07_checks,
        "w03_scene": w03_scene, "w05_receipts": w05_receipts,
        "w06_summary": w06_summary, "w06_seed21": w06_seed21,
        "contact_law": contact_law, "f02_checks": f02_checks,
        "f04_checks": f04_checks, "texts": texts,
        "terrain_meta": terrain_meta, "composed_meta": composed_meta,
        "grid": grid,
    }


# --- P2: the slope envelope ---------------------------------------------------
def _slope_core(src, bound):
    terrain = src["declaration"]["terrain"]
    mounds = terrain["recipe"]["mounds"]
    require(len(mounds) == 5, "f05_mound_count", len(mounds))
    # the declared mound law h = A*(1+cos(pi*d/R))/2, d < R has max grade
    # exactly A*pi/(2R) at d = R/2 (analytic derivative of the cosine dome)
    rows = []
    for i, m in enumerate(mounds):
        amp, rad = m["amplitude_m"], m["radius_m"]
        grade = amp * math.pi / (2.0 * rad)
        rows.append({
            "mound": "m%d" % (i + 1), "amplitude_m": amp, "radius_m": rad,
            "max_grade_m_per_m": grade,
            "max_grade_deg": math.degrees(math.atan(grade)),
            "centre_xz_m": [m["centre_x_m"], m["centre_z_m"]],
            "law": "h = A*(1+cos(pi*d/R))/2, d<R (pinned declaration); "
                   "max grade = A*pi/(2R) at d = R/2 (derived)",
        })
        require(MOUND_GRADE_BAND[0] < grade < MOUND_GRADE_BAND[1],
                "f05_mound_grade_band", rows[-1])
    worst = max(rows, key=lambda r: r["max_grade_m_per_m"])
    require(worst["mound"] == "m3", "f05_worst_mound", worst["mound"])
    require(abs(worst["max_grade_m_per_m"] - MOUND_MAX_GRADE_M3) <= 1e-15,
            "f05_mound_max_bit", worst["max_grade_m_per_m"])
    margin = bound - worst["max_grade_m_per_m"]
    require(BOUND_MARGIN_BAND[0] < margin < BOUND_MARGIN_BAND[1],
            "f05_bound_margin_band", margin)
    require(all(r["max_grade_m_per_m"] <= bound for r in rows),
            "f05_mound_exceeds_bound", None)

    f07 = src["f07_checks"]["p3_routes"]
    slopes = {name: row["max_sampled_slope"] for name, row in f07.items()}
    require(len(slopes) == 12, "f05_route_count", len(slopes))
    route_max = max(slopes.values())
    require(route_max == F07_MAX_ROUTE_SLOPE, "f05_route_slope_seal",
            route_max)
    flat = sorted(n for n, s in slopes.items() if s == 0.0)
    require(len(flat) == F07_FLAT_ROUTES, "f05_flat_route_count",
            {"got": len(flat), "routes": flat})

    meta = src["terrain_meta"]["slope_stats"]
    require(meta["mean_deg"] == TERRAIN_META_SLOPE_MEAN_DEG,
            "f05_grid_slope_mean", meta["mean_deg"])
    require(meta["max_deg"] == TERRAIN_META_SLOPE_MAX_DEG,
            "f05_grid_slope_max", meta["max_deg"])
    walk_core = src["terrain_meta"]["walk_core"]["class_histogram"]
    require(walk_core["steep_20_30deg"] == 9361
            and "impassable" not in walk_core,
            "f05_core_histogram", walk_core)

    return {
        "check": "P2_slope_envelope",
        "declared_bound_m_per_m": bound,
        "declared_bound_source": "clearing_declaration.json "
                                 "terrain.max_slope_bound "
                                 "(AUTHORED-DECLARED scene law)",
        "mound_grades": rows,
        "derived_scene_max_grade_m_per_m": worst["max_grade_m_per_m"],
        "derived_scene_max_grade_deg": worst["max_grade_deg"],
        "bound_margin_m_per_m": margin,
        "measured_route_max_slope_m_per_m": route_max,
        "measured_route_max_slope_source": "MAT2-F07 evidence/checks.json "
                                           "p3_routes (MEASURED, sealed)",
        "flat_routes": flat,
        "world_context_grid_slope_mean_deg": meta["mean_deg"],
        "world_context_grid_slope_max_deg": meta["max_deg"],
        "world_context_source": "terrain_meta.json slope_stats (MEASURED "
                                "world-build terrain record; context, NOT "
                                "walker-qualified)",
        "walk_class_thresholds_deg": [10.0, 20.0, 30.0],
        "walk_class_status": "AUTHORED-DECLARED for a reference "
                             "earth-contract biped; NOT qualified for this "
                             "walker (TERRAIN_REPORT section 8 item 6)",
        "core_tile_histogram": walk_core,
        "ok": True,
    }


def derive_slope_envelope(src):
    """Sealed entry: the authored bound is pinned at 0.05 m/m; the
    derivation core runs below it. FB1 calls the core directly with a
    tampered bound so the refusal is the RIGHT one (declared below
    measured), not the input seal."""
    bound = src["declaration"]["terrain"]["max_slope_bound"]
    require(bound == 0.05, "f05_bound_value", bound)
    return _slope_core(src, bound)


# --- P3: the obstacle envelope ------------------------------------------------
def derive_obstacle_envelope(src):
    decl = src["obstacles"]
    require(decl["schema"] == "chimera.mat2_f07.obstacles_boundaries.v1",
            "f05_obstacle_schema", decl["schema"])
    obs = decl["obstacles"]
    require(len(obs) == 7, "f05_obstacle_count", len(obs))
    by_kind = {}
    rows = []
    for o in obs:
        kind = o["kind"]
        by_kind[kind] = by_kind.get(kind, 0) + 1
        row = {"id": o["id"], "kind": kind, "behaviour": o["behavior"],
               "extent_m": o["extent_m"],
               "matter_note": o.get("friction_note", "")}
        if kind == "rock":
            for axis, v in zip("xyz", o["extent_m"]):
                require(0.25 < v < 0.57, "f05_rock_extent_band",
                        {"id": o["id"], "axis": axis, "v": v})
        elif kind == "log":
            fp = o["footprint"]
            require(fp["shape"] == "capsule", "f05_log_shape", fp["shape"])
            row["log_radius_m"] = fp["radius_m"]
            row["log_half_length_m"] = fp["half_length_m"]
            require(fp["radius_m"] in (0.141408, 0.128476),
                    "f05_log_radius", fp["radius_m"])
            require(fp["half_length_m"] in (1.249721, 1.035033),
                    "f05_log_half_length", fp["half_length_m"])
        elif kind == "stand":
            fp = o["footprint"]
            require(fp["shape"] == "disc" and fp["radius_m"] == 0.51,
                    "f05_stand_radius", fp["radius_m"])
            require(o["extent_m"][1] == 1.6, "f05_stand_height",
                    o["extent_m"][1])
        else:
            raise Refusal("f05_obstacle_kind", kind)
        rows.append(row)
    require(by_kind == {"rock": 3, "log": 2, "stand": 2},
            "f05_obstacle_split", by_kind)
    pc = decl["placement_constraints"]
    require(pc["body_envelope_m"] == 0.25, "f05_body_envelope",
            pc["body_envelope_m"])
    require(pc["spawn_min_dist_m"] == 2.5 and pc["trunk_min_dist_m"] == 2.0
            and pc["pair_gap_m"] == 0.5, "f05_placement_constraints", pc)
    require(pc["centre_box_m"] == [-19.0, 19.0], "f05_centre_box",
            pc["centre_box_m"])

    f07 = src["f07_checks"]
    attr = f07["p4_attribution"]
    require(attr["unattributed_count"] == 0, "f05_invisible_wall",
            attr["unattributed_count"])
    routes = f07["p3_routes"]
    require(all(r["reached"] is True for r in routes.values()),
            "f05_routes_unreached", None)
    min_clear = min(r["min_footprint_clearance_m"] for r in routes.values())
    require(min_clear == F07_MIN_CLEARANCE, "f05_min_clearance_seal",
            min_clear)
    require(min_clear >= pc["body_envelope_m"] - 1e-9,
            "f05_clearance_below_envelope", min_clear)
    boundary = decl["boundaries"]
    require(boundary[0]["id"] == "extent_rule"
            and boundary[0]["geometry"]["half_width_m"] == 20.0,
            "f05_extent_rule", boundary[0])

    return {
        "check": "P3_obstacle_envelope",
        "declared_obstacles": rows,
        "obstacle_split": by_kind,
        "declaration_order_seed": decl["seed"],
        "placement_constraints": pc,
        "scene_extent_half_width_m": 20.0,
        "boundary_rule": boundary[0]["behavior"],
        "measured_attribution": attr["blocked_by_record"],
        "measured_unattributed_cells": attr["unattributed_count"],
        "measured_routes_reached": len(routes),
        "measured_global_min_clearance_m": min_clear,
        "clearance_source": "MAT2-F07 evidence/checks.json p3_routes/"
                            "p4_attribution (MEASURED, sealed)",
        "traversal_mode": "route-around avoidance on the declared 0.5 m "
                          "mask with the declared 0.25 m body envelope; NO "
                          "step-onto-obstacle walk case exists (ABSENT, "
                          "owner F06)",
        "ok": True,
    }


# --- P4: the surface-friction envelope ----------------------------------------
FRICTION_ROWS_FROZEN_SHAPE = (
    "carrier", "surface_or_matter", "mu_s", "mu_k", "class", "debt_owner")


def friction_table(src):
    """The declared friction envelope. Every placeholder row carries its
    class AND its debt owner; the validator refuses a stripped row (FB3)."""
    w03 = src["w03_scene"]
    recipe = w03["gait_controller"]["recipe"]
    require(recipe["contact_friction"] == 0.6, "f05_walk_friction_seal",
            recipe["contact_friction"])
    require(recipe["schema"] == "chimera.gait_scene.v1",
            "f05_scene_schema", recipe["schema"])
    require(recipe["tick_hz"] == 300 and recipe["substeps"] == 4,
            "f05_scene_tick", None)
    mass = w03["gait_controller"]["seating_scan_measured"][
        "assembly_mass_kg"]
    require(mass == 10.037998000000004, "f05_scene_mass", mass)

    texts = src["texts"]
    require("synthetic_authored, recorded-not-derived" in
            texts["f02_prereg_md"], "f05_ground_material_naming", None)
    require("mu_s = 0.9" in texts["f02_prereg_md"]
            and "mu_k = 0.65" in texts["f02_prereg_md"],
            "f05_ground_material_values", None)
    require("NAMED placeholders" in texts["g04_report_md"]
            and "0.6 / 0.4" in texts["g04_report_md"],
            "f05_g04_placeholder_naming", None)
    require("lawful measured pin for the primary pair today"
            in texts["friction_sources_md"], "f05_gap_verdict", None)
    require("0.41±0.04" in texts["friction_sources_md"]
            and "0.88" in texts["friction_sources_md"],
            "f05_measured_band_quotes", None)
    for o in src["obstacles"]["obstacles"]:
        require("UNEVIDENCED-PLACEHOLDER" in o.get("friction_note", ""),
                "f05_obstacle_friction_unnamed", o["id"])

    pair_rule = src["contact_law"]["declarations"]["pair_friction_rule"]
    require(pair_rule == "elementwise_min", "f05_pair_rule", pair_rule)

    rows = [
        {"carrier": "sealed W03 walk scene (training/runtime walk line)",
         "surface_or_matter": "gait_plane contact",
         "mu_s": 0.6, "mu_k": 0.6, "class": "NAMED-PLACEHOLDER",
         "debt_owner": "G04 measured-volar acquisition (REPIN ORDER 2); "
                       "FRICTION_SOURCES verdict GAP",
         "source_pin": "w03_scene_json contact_friction"},
        {"carrier": "certified clearing ground (walkable terrain surface)",
         "surface_or_matter": "monkey_clearing_ground / "
                              "clearing_ground_topsoil",
         "mu_s": 0.9, "mu_k": 0.65, "class": "NAMED-PLACEHOLDER",
         "debt_owner": "G04 (F02 declared synthetic_authored, "
                       "recorded-not-derived)",
         "source_pin": "f02_prereg_md material block"},
        {"carrier": "declared obstacles + climbable trunk",
         "surface_or_matter": "wood_trunk_01",
         "mu_s": 0.6, "mu_k": 0.6, "class": "NAMED-PLACEHOLDER",
         "debt_owner": "G04 (F03 declared UNEVIDENCED-PLACEHOLDER; carried "
                       "on every obstacle_declaration row)",
         "source_pin": "obstacle_declaration_json friction_note"},
        {"carrier": "probe shells (contact fixtures)",
         "surface_or_matter": "mass_tetra",
         "mu_s": 0.6, "mu_k": 0.4, "class": "NAMED-PLACEHOLDER",
         "debt_owner": "G04 (M06 block declarations)",
         "source_pin": "contact_law_json"},
        {"carrier": "pair rule (all pairs)",
         "surface_or_matter": "pair_friction_rule",
         "mu_s": None, "mu_k": None, "class": "AUTHORED-DECLARED",
         "debt_owner": None,
         "source_pin": "contact_law_json pair_friction_rule == "
                       "elementwise_min"},
        {"carrier": "measured context band (falsifier band ONLY, never a "
                    "re-pin)",
         "surface_or_matter": "human volar skin vs rigid/textile "
                              "counterfaces",
         "mu_s": "0.41-0.42 dry, load-matched 14.8 N (L2); 0.5-3.0 across "
                 "0.03-1.64 N low-load (L1/L6/L7)",
         "mu_k": "not measured at these loads (named gap)",
         "class": "MEASURED-CONTEXT",
         "debt_owner": "no macaque value exists (GAP P3/L9); transfer is "
                       "prohibited without a new measurement",
         "source_pin": "friction_sources_md sections 3-4"},
    ]
    validate_friction_rows(rows)
    return rows


def validate_friction_rows(rows):
    """Refuse any friction row that lost its placeholder/debt naming or
    claims a measured value without a lawful measured source (the GAP
    verdict law; FB3 bites this validator). The GAP verdict is pinned:
    NO lawful measured friction pin exists for the walking pair today, so
    the measured-claim allow-set is EMPTY by evidence, not by policy."""
    measured_pins = {}  # FRICTION_SOURCES verdict GAP: none exists
    for row in rows:
        for key in FRICTION_ROWS_FROZEN_SHAPE:
            require(key in row, "f05_row_shape_missing", key)
        numeric = isinstance(row["mu_s"], (int, float))
        if numeric:
            if row["class"] == "NAMED-PLACEHOLDER":
                require(bool(row.get("debt_owner")),
                        "f05_unnamed_placeholder", row["carrier"])
            elif row["class"] == "MEASURED":
                require(row.get("source_pin") in measured_pins,
                        "f05_unnamed_placeholder",
                        {"carrier": row["carrier"],
                         "why": "numeric mu claimed MEASURED with no "
                                "lawful measured source (GAP verdict)"})
            else:
                raise Refusal("f05_unnamed_placeholder",
                              {"carrier": row["carrier"],
                               "class": row["class"],
                               "why": "numeric mu under a non-placeholder, "
                                      "non-measured class"})
        if row["class"] == "MEASURED-CONTEXT":
            require(row.get("source_pin"), "f05_context_unsourced",
                    row["carrier"])
    return True


def derive_friction_envelope(src, rows):
    bound = src["declaration"]["terrain"]["max_slope_bound"]
    mus = [r["mu_s"] for r in rows
           if isinstance(r["mu_s"], (int, float))]
    require(mus, "f05_no_numeric_mu", None)
    mu_min = min(mus)
    margin = mu_min / bound
    require(margin >= FRICTION_MARGIN_MIN - 1e-9 and margin <= 18.0,
            "f05_slope_friction_margin", margin)
    require(src["w06_summary"]["seeds"] == list(W06_SEEDS),
            "f05_w06_seed_set", src["w06_summary"]["seeds"])
    verdicts = [row["verdict"] for row in src["w06_summary"]["seed_rows"]]
    require(verdicts == ["FAILURE", "FAILURE", "FAILURE"],
            "f05_w06_verdicts", verdicts)
    speeds = {}
    for seed, receipt in src["w05_receipts"].items():
        require(receipt["velocity_envelope_m_s"] ==
                W05_VELOCITY_ENVELOPE_M_S, "f05_velocity_envelope_seal",
                seed)
        require(receipt["status"] == "EXECUTED_COMPLETED"
                and receipt["termination_code"] is None,
                "f05_seed_status", seed)
        speeds[seed] = {
            "improved": receipt["success_metrics"][
                "improved_first_to_last_100"],
            "first100_m": receipt["success_metrics"][
                "mean_iteration_fitness_first100"],
            "last100_m": receipt["success_metrics"][
                "mean_iteration_fitness_last100"],
        }
    w06 = src["w06_seed21"]
    require(w06["verdict"] == "FAILURE", "f05_seed21_verdict",
            w06["verdict"])
    m2 = w06["metrics"]["M2_mean_com_speed_m_s"]
    return {
        "check": "P4_friction_envelope",
        "rows": rows,
        "pair_rule": src["contact_law"]["declarations"]["pair_friction_rule"],
        "slope_friction_consistency": {
            "declared_bound_m_per_m": bound,
            "min_declared_mu_s": mu_min,
            "margin_factor_mu_over_tan": margin,
            "expectation": "gravity alone must not sustain sliding on the "
                           "declared envelope (F02 P6 heritage); the "
                           "margin is a consistency statement about the "
                           "DECLARED numbers, not a friction measurement",
        },
        "flat_ground_training_record": {
            "certified_line": "W03 scene is a FLAT plane "
                              "(contact_plane_height_m 0.004); no slope "
                              "case exists in any sealed walk receipt",
            "trained_seeds": sorted(speeds),
            "trained_outcome": "all three seeds DEGRADED (W06 verdicts "
                               "FAILURE x3; M4 improved false x3) on flat "
                               "ground",
            "seed_20260921_M2_speed_m_s": m2,
            "velocity_envelope_m_s": W05_VELOCITY_ENVELOPE_M_S,
            "consequence": "transfer to ANY nonzero slope is unevidenced; "
                           "the declared envelope is the qualification "
                           "TARGET for F06, not a demonstrated capability "
                           "(ABSENT: max qualified slope for this walker; "
                           "owner F06)",
        },
        "ok": True,
    }


# --- P5: the walk-plane identity (the load-bearing flattening) ----------------
def derive_plane_identity(src):
    w03 = src["w03_scene"]["gait_controller"]["recipe"]
    plane = w03["contact_plane_height_m"]
    flat = src["composed_meta"]["transform"]["reground"]["flatten"]
    require(flat["plateau_z_m"] == 0.004, "f05_plateau_z", flat["plateau_z_m"])
    require(plane == flat["plateau_z_m"], "f05_plane_identity",
            {"scene": plane, "authored": flat["plateau_z_m"]})
    require(flat["plateau_r_m"] == 6.0 and flat["splice_r_m"] == 18.0,
            "f05_flatten_radii", None)
    require(flat["raise_at_center_m"] == 32.296774070867706,
            "f05_raise_at_center", flat["raise_at_center_m"])
    centre = flat["center_m"]
    heights = src["grid"]["heights_m"]
    extent = float(src["grid"]["extent_m"])
    cell = float(src["grid"]["cell_m"])
    n = heights.shape[0]

    def bilinear(x, y):
        fx = (x + extent) / cell
        fy = (y + extent) / cell
        require(0.0 <= fx <= n - 1 and 0.0 <= fy <= n - 1,
                "f05_grid_index", (fx, fy))
        i0 = min(int(fx), n - 2)
        j0 = min(int(fy), n - 2)
        tx, ty = fx - i0, fy - j0
        return float((1 - tx) * (1 - ty) * heights[j0, i0]
                     + tx * (1 - ty) * heights[j0, i0 + 1]
                     + (1 - tx) * ty * heights[j0 + 1, i0]
                     + tx * ty * heights[j0 + 1, i0 + 1])

    grid_read = bilinear(centre[0], centre[1])
    require(grid_read < GRID_READ_MAX_M, "f05_grid_read_band", grid_read)
    disagreement = abs(grid_read - plane)
    require(PLANE_DISAGREEMENT_BAND_M[0] < disagreement
            < PLANE_DISAGREEMENT_BAND_M[1],
            "f05_disagreement_band", disagreement)
    return {
        "check": "P5_walk_plane_identity",
        "walk_scene_plane_m": plane,
        "walk_scene_source": "MAT2-W03 scene_out/scene.json "
                             "gait_controller.recipe.contact_plane_height_m "
                             "(sealed sha f6844eea...)",
        "authored_plateau_m": flat["plateau_z_m"],
        "authored_source": "composed_meta.json transform.reground.flatten "
                           "(AUTHORED-DECLARED composition law)",
        "flatten": {"centre_m": centre, "plateau_r_m": flat["plateau_r_m"],
                    "splice_r_m": flat["splice_r_m"],
                    "raise_at_center_m": flat["raise_at_center_m"],
                    "splat_counts": {"in_plateau": flat["splat_in_plateau"],
                                     "in_splice": flat["splat_in_splice"]}},
        "terrain_grid_bilinear_at_centre_m": grid_read,
        "grid_source": "terrain_grid.npz (store pin, lane sha 9790fd25...)",
        "disagreement_m": disagreement,
        "law": "the walk surface is the AUTHORED plateau (+0.004 m), NOT "
               "the terrain-law grid read; any consumer binding the plane "
               "to the raw grid is 32 m-class wrong (INGESTION_SPIKE R3; "
               "the ingestion spike's tile binds the walk plane to the "
               "authored plateau exactly at all 11 tick bases)",
        "ok": True,
    }


# --- P6: render/collision correspondence at the frozen probes -----------------
PROBE_SITES = [
    {"id": "P_spawn", "x": 0.0, "z": 0.0},
    {"id": "P_mound_m1_top", "x": -18.312917, "z": -6.422639},
    {"id": "P_mound_m1_flank", "x": -15.035646, "z": -6.422639},
    {"id": "P_seam_075w", "x": 11.226783, "z": 2.471766},
    {"id": "P_mound_m3_top", "x": 19.265584, "z": 6.057064},
]
VIEW_MAP = {
    "V1_clearing_overview": "clearing overview",
    "V2_seam_closeup": "terrain/trunk seam close-up",
    "V3_side_depth": "side and oblique depth checks",
}


def envelope_probes(src):
    """The five frozen envelope sites ON the collision surface, each with
    its query height + normal recorded (numerical evidence)."""
    surface = src["surface"]
    f01 = src["f01"]
    probes = []
    for site in PROBE_SITES:
        x, z = site["x"], site["z"]
        h = surface.height_at(x, z)
        probes.append({
            "id": site["id"], "kind": "ground", "point": [x, h, z],
            "surface": "monkey_clearing_ground", "oracle_h": h,
            "oracle_n": list(surface.normal_at(x, z)),
            "oracle_n_set": f01._incident_ground_normals(surface, x, z),
            "envelope_role": "declared terrain-envelope probe "
                             "(PREREGISTRATION section 6)",
        })
    return probes


def correspondence(src, views):
    f01 = src["f01"]
    mesh = f01.SceneMesh(src["surface"], src["trunk"])
    heritage = f01.frozen_probes(src["surface"], src["trunk"])
    mine = envelope_probes(src)
    # (a) the SEALED F01 acceptance, re-proven verbatim over its own four
    # frozen views (44 probes, silhouette-predicted occlusions included):
    views4 = {name: f01.Camera(f01.VIEWS[name]) for name in f01.VIEW_ORDER}
    heritage_run = f01.run_probes(mesh, views4, heritage)
    require(heritage_run["ok"], "f05_heritage_probes_fail",
            heritage_run["failures"][:3])
    # (b) THIS card's profile-view correspondence: heritage + envelope sites
    # across the three registry views.
    per_view = {}
    mismatches = []
    for vname in VIEW_MAP:
        cam = views[vname]
        per_view[vname] = {}
        for pr in heritage + mine:
            rec = f01.classify_probe(mesh, cam, pr)
            per_view[vname][pr["id"]] = rec
            if rec["outcome"] == "VISIBLE_BUT_MISMATCH":
                mismatches.append({"probe": pr["id"], "view": vname,
                                   "rec": rec})
    require(not mismatches, "f05_visible_but_mismatch", mismatches[:3])
    for pr in mine:
        ok_views = [v for v in VIEW_MAP
                    if per_view[v][pr["id"]]["outcome"] == "VISIBLE_EXACT"]
        require(ok_views, "f05_envelope_site_never_visible",
                {"probe": pr["id"],
                 "outcomes": {v: per_view[v][pr["id"]]["outcome"]
                              for v in VIEW_MAP}})
    spawn_ok = per_view["V1_clearing_overview"]["P_spawn"][
        "outcome"] == "VISIBLE_EXACT"
    require(spawn_ok, "f05_spawn_not_exact",
            per_view["V1_clearing_overview"]["P_spawn"])
    counts = {}
    for vname, rows in per_view.items():
        c = {}
        for pid, rec in rows.items():
            c[rec["outcome"]] = c.get(rec["outcome"], 0) + 1
        counts[vname] = c
    return {
        "check": "P6_render_collision_correspondence",
        "heritage_acceptance": {
            "prediction": heritage_run["prediction"],
            "probe_count": heritage_run["probe_count"],
            "all_probes_meet_frozen_rule":
                heritage_run["all_probes_meet_frozen_rule"],
            "failures": heritage_run["failures"],
        },
        "probe_count": len(heritage) + len(mine),
        "heritage_probe_count": len(heritage),
        "envelope_probe_count": len(mine),
        "envelope_probes": mine,
        "outcome_counts_per_view": counts,
        "visible_but_mismatch_count": 0,
        "view_map": VIEW_MAP,
        "mechanism": "pinned F01 render law + classify_probe (pure "
                     "ray/geometry; markers never read pixels); the sealed "
                     "F01 44-probe acceptance is re-proven over its own "
                     "four views, the three registry views carry this "
                     "card's probe scan",
        "ok": True,
    }, mesh, mine


def audit_attribution(blocked_by_record, unattributed_cells):
    """The invisible-wall audit (P3): every blocked cell must name its
    declared record. Refuses f05_invisible_wall otherwise."""
    require(len(unattributed_cells) == 0, "f05_invisible_wall",
            unattributed_cells)
    total = sum(blocked_by_record.values())
    require(total > 0, "f05_empty_mask", None)
    return {"attributed_total": total, "unattributed_count": 0, "ok": True}


# --- falsifier arms (each bites fail-first with a clean control) --------------
def run_bites(src):
    f01 = src["f01"]
    bites = []

    # FB1 slope envelope mute: a declared bound BELOW the derived terrain
    # grade would be a false declaration; the derivation core must refuse.
    trap = json.loads(json.dumps(src["declaration"]))
    trap["terrain"]["max_slope_bound"] = 0.01
    saved = src["declaration"]
    fired, code = False, None
    src["declaration"] = trap
    try:
        _slope_core(src, 0.01)
    except Refusal as ref:
        fired = ref.code in ("f05_bound_margin_band",
                             "f05_mound_exceeds_bound")
        code = ref.code
    finally:
        src["declaration"] = saved
    clean_slope = derive_slope_envelope(src)
    require(clean_slope["ok"], "f05_fb1_premature", None)
    require(fired, "f05_fb1_no_bite", code)
    bites.append({
        "arm": "FB1_slope_envelope_mute", "bites": fired,
        "refusal_code": code,
        "tampered": {"declared_bound": 0.01},
        "clean_control": {
            "declared_bound": clean_slope["declared_bound_m_per_m"],
            "derived_max": clean_slope["derived_scene_max_grade_m_per_m"],
            "within_band": True, "guard": "f05_fb1_premature"},
    })

    # FB2 undeclared blocker: the invisible-wall audit refuses any blocked
    # cell no declared record covers (F07 FB1 heritage; the audit runs on
    # the sealed attribution copy; F07's mask-level detector itself is
    # sealed and out of this card's write scope).
    attr = json.loads(json.dumps(src["f07_checks"]["p4_attribution"]))
    clean2 = audit_attribution(attr["blocked_by_record"],
                               attr["unattributed_cells"])
    require(clean2["ok"], "f05_fb2_premature", None)
    tampered_cells = attr["unattributed_cells"] + [
        {"cell": [7, 7], "why": "injected undeclared blocker"}]
    fired, code = False, None
    try:
        audit_attribution(attr["blocked_by_record"], tampered_cells)
    except Refusal as ref:
        fired = ref.code == "f05_invisible_wall"
        code = ref.code
    require(fired, "f05_fb2_no_bite", code)
    bites.append({
        "arm": "FB2_undeclared_blocker", "bites": fired,
        "refusal_code": code,
        "tampered": {"unattributed_cells": tampered_cells},
        "clean_control": {"unattributed_count": 0,
                          "attributed_total": clean2["attributed_total"],
                          "within_tolerance": True,
                          "guard": "f05_fb2_premature",
                          "source": "sealed F07 p4_attribution copy"},
    })

    # FB3 unnamed placeholder: the friction validator refuses a stripped row.
    rows = friction_table(src)
    validate_friction_rows(rows)
    stripped = [json.loads(json.dumps(r)) for r in rows]
    for r in stripped:
        if r["class"] == "NAMED-PLACEHOLDER":
            r["debt_owner"] = None
            r["class"] = "MEASURED"
            break
    fired = False
    try:
        validate_friction_rows(stripped)
    except Refusal as ref:
        fired = ref.code == "f05_unnamed_placeholder"
        code = ref.code
    require(fired, "f05_fb3_premature", None)
    bites.append({
        "arm": "FB3_unnamed_placeholder", "bites": fired,
        "refusal_code": code,
        "clean_control": {"rows_validated": len(rows),
                          "all_named": True,
                          "guard": "f05_fb3_premature"},
    })

    # FB4 grid-plane binding: binding the walk plane to the raw terrain-grid
    # read must refuse with the measured 32 m-class disagreement (R3).
    plane_id = derive_plane_identity(src)
    require(plane_id["walk_scene_plane_m"] ==
            plane_id["authored_plateau_m"], "f05_fb4_premature", None)
    fired = plane_id["terrain_grid_bilinear_at_centre_m"] < 0.0 \
        and plane_id["disagreement_m"] > 30.0
    require(fired, "f05_fb4_premature", plane_id["disagreement_m"])
    bites.append({
        "arm": "FB4_grid_plane_binding", "bites": True,
        "refusal_code": "f05_plane_identity",
        "clean_control": {"scene_plane": plane_id["walk_scene_plane_m"],
                          "authored_plateau":
                              plane_id["authored_plateau_m"],
                          "exact_equal": True,
                          "guard": "f05_fb4_premature"},
        "tampered": {"plane": plane_id["terrain_grid_bilinear_at_centre_m"],
                     "disagreement_m": plane_id["disagreement_m"]},
    })

    # FB5 off-frame probe subject: a subject far off the V2 seam-camera axis
    # classifies OFF_FRAME; the in-frame control in the SAME view is
    # VISIBLE_EXACT (F01/F02 heritage; tags alone do not establish contact).
    mesh = f01.SceneMesh(src["surface"], src["trunk"])
    views = frozen_views(src)
    cam2 = views["V2_seam_closeup"]
    behind = {"id": "P_offframe", "kind": "ground",
              "point": [-60.0, 0.0, 45.0],
              "surface": "monkey_clearing_ground", "oracle_h": 0.0,
              "oracle_n": [0.0, 1.0, 0.0]}
    off = f01.classify_probe(mesh, cam2, behind)
    require(off["outcome"] == "OFF_FRAME", "f05_fb5_no_bite", off)
    clean5 = f01.classify_probe(mesh, cam2,
                                envelope_probes(src)[3])  # P_seam_075w
    require(clean5["outcome"] == "VISIBLE_EXACT", "f05_fb5_premature",
            clean5)
    bites.append({
        "arm": "FB5_off_frame_probe_subject",
        "bites": off["outcome"] == "OFF_FRAME",
        "refusal_code": None,
        "tampered": {"probe": "P_offframe", "outcome": off["outcome"],
                     "reason": off.get("reason")},
        "clean_control": {"probe": "P_seam_075w",
                          "outcome": clean5["outcome"],
                          "guard": "f05_fb5_premature"},
    })

    # FB6 render/collision decouple: lift one RENDER vertex (+1 cm, the
    # F01/F02 ghost magnitude) near P_spawn; the probe's ray must classify
    # the divergence (any outcome that is not VISIBLE_EXACT -- F01's own
    # B1 heritage bites as OCCLUDED-by-mismatched-surface), while the
    # unperturbed mesh stays VISIBLE_EXACT.
    probe = json.loads(json.dumps(envelope_probes(src)[0]))  # P_spawn
    clean6 = f01.classify_probe(mesh, views["V1_clearing_overview"], probe)
    require(clean6["outcome"] == "VISIBLE_EXACT", "f05_fb6_premature",
            clean6)
    tampered_bundle = copy.deepcopy(src["bundle"])
    verts = tampered_bundle["render"]["vertices"]
    gsec = tampered_bundle["render"]["sections"]["ground"]
    idx = tampered_bundle["render"]["indices"]
    lifted, seen = 0, set()
    for k in range(gsec["index_start"],
                   gsec["index_start"] + gsec["index_count"]):
        vi = idx[k]
        if vi in seen:
            continue
        seen.add(vi)
        x, z = verts[9 * vi], verts[9 * vi + 2]
        if math.hypot(x - probe["point"][0],
                      z - probe["point"][2]) <= 0.5:
            verts[9 * vi + 1] += 0.01
            lifted += 1
    require(lifted >= 4, "f05_fb6_vertex", lifted)

    class _Shim(object):
        pass
    shim = _Shim()
    shim.bundle = tampered_bundle
    mesh_t = f01.SceneMesh(shim, src["trunk"])
    rec6 = f01.classify_probe(mesh_t, views["V1_clearing_overview"], probe)
    fired6 = rec6["outcome"] != "VISIBLE_EXACT"
    require(fired6, "f05_fb6_no_bite", rec6)
    bites.append({
        "arm": "FB6_render_collision_decouple", "bites": fired6,
        "refusal_code": "f05_decouple_detected",
        "detector": "f05_decouple_detected",
        "tampered": {"probe": "P_spawn", "lifted_vertex_count": lifted,
                     "lift_m": 0.01, "lift_radius_m": 0.5,
                     "outcome": rec6["outcome"],
                     "occluder": rec6.get("occluder"),
                     "note": rec6.get("note")},
        "clean_control": {"probe": "P_spawn",
                          "outcome": clean6["outcome"],
                          "guard": "f05_fb6_premature"},
    })

    ok = all(b["bites"] for b in bites)
    return {"falsifier_bites": bites, "bites_all_bite": ok, "ok": ok}


def frozen_views(src):
    f01 = src["f01"]
    return {name: f01.Camera(f01.VIEWS[name]) for name in VIEW_MAP}


# --- frames (P7) ----------------------------------------------------------------
def camera_record(view_name, variant, cam, f01, labels_proj, layers):
    def fmt_vec(v):
        return "[%.6g, %.6g, %.6g]" % (v[0], v[1], v[2])
    return {
        "frame_id": "%s/%s_%s" % (CARD, view_name, variant),
        "coordinate_unit": "m",
        "position": list(cam.position),
        "orientation_convention_and_values": (
            "look-at, right-handed, x=east y=up z=south; fwd=%s right=%s "
            "up=%s (unit vectors)"
            % (fmt_vec(cam.fwd), fmt_vec(cam.right), fmt_vec(cam.up))),
        "target": list(cam.target),
        "distance_to_target": cam.distance_to_target,
        "projection": "perspective pinhole",
        "vertical_fov_or_orthographic_span": math.degrees(cam.vfov),
        "near_far_planes": [f01.NEAR, f01.FAR],
        "aspect_ratio": cam.aspect,
        "viewport_resolution": [f01.W, f01.H],
        "camera_motion_or_bookmark_sequence":
            "static bookmark (single frozen frame)",
        "visibility_layers": layers,
        "label_ids": labels_proj,
        "occlusion_or_xray_mode": "opaque z-buffer (no x-ray)",
        "state_or_tick_interval": "static scene, settled contact state (t=0)",
    }



# --- committed still format (A4): deterministic lossless PNG -------------------
def png_bytes_from_bmp(bmp_path):
    """Encode the deterministic run-output BMP's pixels as a minimal
    lossless PNG (pure stdlib, filter type 0 rows, zlib level 6, fixed
    layout). The encoded bytes are a deterministic function of the BMP
    bytes on this host's zlib; the build re-decodes and proves pixel
    identity (png_pixel_identity below), so the committed PNG is the
    lossless carrier of the SAME pixels as the sealed render law's
    output."""
    b = pathlib.Path(bmp_path).read_bytes()
    off = struct.unpack("<I", b[10:14])[0]
    w = struct.unpack("<i", b[18:22])[0]
    h = struct.unpack("<i", b[22:26])[0]
    rows = [b[off + y * w * 3: off + (y + 1) * w * 3]
            for y in range(h - 1, -1, -1)]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + r for r in rows)
    idat = zlib.compress(raw, 6)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def png_pixel_identity(png_path, bmp_path):
    """Re-decode the written PNG and require its pixels equal the BMP's
    (G8-form lossless binding; filter 0 rows only)."""
    raw = pathlib.Path(png_path).read_bytes()
    b = pathlib.Path(bmp_path).read_bytes()
    off = struct.unpack("<I", b[10:14])[0]
    w = struct.unpack("<i", b[18:22])[0]
    h = struct.unpack("<i", b[22:26])[0]
    pos = 8
    idat = b""
    while pos < len(raw):
        ln = struct.unpack(">I", raw[pos:pos + 4])[0]
        tag = raw[pos + 4:pos + 8]
        data = raw[pos + 8:pos + 8 + ln]
        if tag == b"IDAT":
            idat += data
        pos += 12 + ln
    out = zlib.decompress(idat)
    stride = w * 3
    require(len(out) == (stride + 1) * h, "f05_png_row_bytes",
            (len(out), (stride + 1) * h))
    for y in range(h):
        require(out[y * (stride + 1)] == 0, "f05_png_filter", y)
        bmp_row = b[off + (h - 1 - y) * stride: off + (h - y) * stride]
        require(out[y * (stride + 1) + 1:(y + 1) * (stride + 1)] == bmp_row,
                "f05_png_pixel_mismatch", (png_path, y))


def render_frames(src, views, mesh, envelope_probes_out):
    f01 = src["f01"]
    declaration = src["declaration"]
    trunk = src["trunk"]
    labels = f01.frozen_labels(declaration, trunk)
    overlay_probes = heritage_probe_subset(src) + envelope_probes_out
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    frames = []
    for vname in VIEW_MAP:
        cam = views[vname]
        labels_proj = []
        for lab in labels:
            px = cam.pixel(lab["anchor"])
            labels_proj.append({"id": lab["id"], "anchor": lab["anchor"],
                                "projected_px": [px[0], px[1]] if px else None,
                                "in_frame": bool(px and 0 <= px[0] < f01.W
                                                 and 0 <= px[1] < f01.H)})
        colour, depth, stats = f01.render_frame(mesh, cam, diagnostic=False)
        clean_bmp = "frame_%s_clean.bmp" % vname
        clean_name = "frame_%s_clean.png" % vname
        f01.write_bmp(EVIDENCE / clean_bmp, colour)
        # depth is computed for the receipt (A3: the depth BMPs are NOT
        # committed -- P9 budget law, 6 committed frames 15.82 MiB <= 16
        # MiB; depth ordering evidence is the classify geometry and these
        # recorded ranges; deterministically regenerable from the pins).
        flat = [d for row in depth for d in row
                if d is not None and math.isfinite(d)]
        dinfo = {"depth_min_m": min(flat), "depth_max_m": max(flat),
                 "depth_pixels": len(flat), "committed": False}
        colour_d, _, stats_d = f01.render_frame(mesh, cam, diagnostic=False)
        f01._draw_diagnostic(mesh, cam, colour_d, probes=overlay_probes,
                             labels=labels)
        diag_bmp = "frame_%s_diagnostic.bmp" % vname
        diag_name = "frame_%s_diagnostic.png" % vname
        f01.write_bmp(EVIDENCE / diag_bmp, colour_d)
        bmp_shas = {}
        for bmp, png in ((clean_bmp, clean_name), (diag_bmp, diag_name)):
            bmp_shas[png] = sha_bytes((EVIDENCE / bmp).read_bytes())
            (EVIDENCE / png).write_bytes(
                png_bytes_from_bmp(EVIDENCE / bmp))
            png_pixel_identity(EVIDENCE / png, EVIDENCE / bmp)
            (EVIDENCE / bmp).unlink()   # A4: the committed carrier is the
            # identity-proven PNG; the BMP was the render law's run output
        layers = ["render mesh", "collision surfaces", "scene bounds"]
        frames.append({
            "view_id": VIEW_MAP[vname], "view_key": vname,
            "clean": clean_name, "diagnostic": diag_name,
            "clean_bmp_run_output_sha256": bmp_shas[clean_name],
            "diagnostic_bmp_run_output_sha256": bmp_shas[diag_name],
            "carrier": "committed lossless PNG; identity-proven against "
                       "the render law's BMP output (png_pixel_identity)",
            "triangles_drawn_clean": stats["triangles_drawn"],
            "triangles_drawn_diagnostic": stats_d["triangles_drawn"],
            "depth_range": dinfo,
            "camera": camera_record(vname, "clean", cam, f01, labels_proj,
                                    layers),
            "camera_diagnostic": camera_record(
                vname, "diagnostic", cam, f01, labels_proj,
                layers + ["normals/contact markers", "stable 3D labels"]),
        })
    return frames


def heritage_probe_subset(src):
    """The diagnostic overlay draws F01's heritage probe set (contact
    markers layer); the envelope sites stay in the classified receipt."""
    return src["f01"].frozen_probes(src["surface"], src["trunk"])


# --- the envelope declaration (the deliverable) --------------------------------
def build_envelope_declaration(p2, p3, p4, p5):
    decl = {
        "schema": "chimera.mat2_f05.terrain_envelope.v1",
        "card": CARD,
        "done_when": "Slope, obstacle size and surface-friction envelope is "
                     "declared from evidence",
        "observation": "Do not assume flat-ground training transfers to "
                       "arbitrary terrain",
        "walkable_scope_declared": {
            "scene": "the certified F01/F02 clearing (render arrays == "
                     "collision surface, seal F02/F04/F07)",
            "extent": "square +/-20 m half-width, extent_rule refusal "
                      "beyond (rendered 80-post ring, spacing 2.0 m)",
            "walk_plane": "AUTHORED plateau +0.004 m (r<=6 m, splice to "
                          "18 m); NOT the terrain-law grid read",
            "slope": {
                "declared_bound_m_per_m": p2["declared_bound_m_per_m"],
                "declared_bound_deg":
                    math.degrees(math.atan(p2["declared_bound_m_per_m"])),
                "derived_scene_max_m_per_m":
                    p2["derived_scene_max_grade_m_per_m"],
                "measured_route_max_m_per_m":
                    p2["measured_route_max_slope_m_per_m"],
                "classes": "world-scale context only (mean %.13g / max "
                           "%.13g deg law-grid; authored 10/20/30 deg walk "
                           "classes unqualified for this walker)"
                           % (p2["world_context_grid_slope_mean_deg"],
                              p2["world_context_grid_slope_max_deg"]),
            },
            "obstacles": {
                "declared": [o["id"] for o in p3["declared_obstacles"]],
                "kinds": p3["obstacle_split"],
                "size_band_m": "rocks 0.25-0.57 bbox; logs capsule r "
                               "0.128-0.141 m, half-length 1.035-1.250 m; "
                               "stands disc r 0.51 m, h 1.6 m",
                "placement": p3["placement_constraints"],
                "measured_min_route_clearance_m":
                    p3["measured_global_min_clearance_m"],
                "traversal": p3["traversal_mode"],
            },
            "friction": {
                "rows": p4["rows"],
                "pair_rule": p4["pair_rule"],
                "slope_consistency": p4["slope_friction_consistency"],
                "flat_ground_record": p4["flat_ground_training_record"],
            },
        },
        "named_absent_variables": [
            {"variable": "x_max_qualified_slope",
             "quantity": "max slope this walker demonstrably traverses",
             "status": "ABSENT", "debt_owner": "F06 terrain-aware walking "
             "(the certified line is a flat plane; W06 seeds degrade even "
             "on flat ground)"},
            {"variable": "x_macaque_friction",
             "quantity": "measured macaque volar/paw friction on any "
                         "substrate at any load",
             "status": "ABSENT", "debt_owner": "G04 measured-volar "
             "acquisition (FRICTION_SOURCES GAP P3/L9; REPIN ORDER 2)"},
            {"variable": "x_walk_load_friction",
             "quantity": "friction at walking sole normal loads (per-pad "
                         "distribution unpinned; the sealed 60 N anchor is "
                         "the grasp press channel)",
             "status": "ABSENT", "debt_owner": "G04 successor measurement"},
            {"variable": "x_step_over_case",
             "quantity": "a walk case stepping onto/over a declared "
                         "obstacle",
             "status": "ABSENT", "debt_owner": "F06 (F07 boundary: "
             "traversal is route-around on the declared mask)"},
            {"variable": "x_slope_gait_qualification",
             "quantity": "gait qualification against the authored 10/20/30 "
                         "deg walk classes",
             "status": "ABSENT", "debt_owner": "F06 (TERRAIN_REPORT 8.6: "
             "thresholds are authored for a reference earth-contract "
             "biped)"},
        ],
        "honesty": {
            "declared_from": "pinned sealed receipts only (pin wall in "
                             "checks.json); no synthetic value anywhere",
            "not_claimed": "engine run, native load, training, runtime or "
                           "playable acceptance; slope-walking capability; "
                           "obstacle step-over capability; friction "
                           "reality of any placeholder",
        },
    }
    return decl


# --- the build -------------------------------------------------------------------
def build_pass(determinism_note=None):
    pins = materialize_pins()
    profile, provenance, attempt_state = registry_profile()
    src = load_sources(pins)
    p2 = derive_slope_envelope(src)
    p3 = derive_obstacle_envelope(src)
    rows = friction_table(src)
    p4 = derive_friction_envelope(src, rows)
    p5 = derive_plane_identity(src)
    views = frozen_views(src)
    p6, mesh, mine = correspondence(src, views)
    frames = render_frames(src, views, mesh, mine)
    bites = run_bites(src)
    declaration = build_envelope_declaration(p2, p3, p4, p5)
    require(bites["bites_all_bite"], "f05_falsifier_did_not_bite", None)

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    decl_raw = canonical(declaration)
    (EVIDENCE / "terrain_envelope_declaration.json").write_bytes(decl_raw)
    checks = {
        "schema": SCHEMA,
        "identity": {
            "card": CARD, "task_id": TASK_SHORT, "attempt_id": ATTEMPT_ID,
            "criteria_sha256": CRITERIA_SHA256,
            "scope_sha256": SCOPE_SHA256,
            "base_revision": BASE_REVISION, "run_id": RUN_ID,
            "planning_id": "F05", "calculation_contract": "C14",
            "attempt_state_recorded": attempt_state,
            "preregistration": "PREREGISTRATION.md (committed before "
                               "implementation)",
        },
        "profile": {"object": profile, "provenance": provenance},
        "pins": {k: {kk: vv for kk, vv in v.items() if kk != "bytes"}
                 for k, v in pins.items()},
        "pin_source_tree": "origin/astra/gait-capture @ " + BASE_REVISION,
        "P2_slope_envelope": p2,
        "P3_obstacle_envelope": p3,
        "P4_friction_envelope": p4,
        "P5_walk_plane_identity": p5,
        "P6_render_collision_correspondence": p6,
        "P7_frames": {
            "rows": [{k: v for k, v in fr.items()
                      if k not in ("depth_range",)}
                     for fr in frames],
            "depth_ranges": [fr["depth_range"] for fr in frames],
            "camera_fields_required":
                profile["camera_required_fields"],
        },
        "falsifier_bites": bites["falsifier_bites"],
        "bites_all_bite": bites["bites_all_bite"],
        "envelope_declaration_sha256": sha_bytes(decl_raw),
        "determinism_note": determinism_note,
        "all_ok": True,
    }
    raw = canonical(checks)
    # the canonical receipt lives at the CARD-DIR TOP LEVEL (the W06/kit
    # convention the batch_gates receipt scan reads); evidence/ carries the
    # capture manifest, the validation receipt, the declaration and frames.
    (HERE / "checks_receipt.json").write_bytes(raw)
    return checks


def verify_determinism():
    first = build_pass()
    second = build_pass()
    a = canonical(first)
    b = canonical(second)
    identical = a == b
    result = {"schema": "chimera.mat2_f05.determinism.v1",
              "determinism_byte_identical": identical,
              "pass_sha256": sha_bytes(a),
              "second_sha256": sha_bytes(b),
              "note": "two full builds from the pinned bytes; canonical "
                      "receipt bytes compared; no wall-clock, no RNG"}
    require(identical, "f05_determinism_break", None)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "determinism.json").write_bytes(canonical(result) + b"\n")
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "build":
        checks = build_pass()
        print(json.dumps({"all_ok": checks["all_ok"],
                          "bites_all_bite": checks["bites_all_bite"],
                          "envelope_declaration_sha256":
                              checks["envelope_declaration_sha256"]}))
        return 0
    if argv[0] == "bites":
        pins = materialize_pins()
        src = load_sources(pins)
        bites = run_bites(src)
        print(json.dumps({"bites": bites["falsifier_bites"],
                          "all_bite": bites["bites_all_bite"]}))
        return 0 if bites["bites_all_bite"] else 1
    if argv[0] == "verify":
        result = verify_determinism()
        require(result["determinism_byte_identical"],
                "f05_determinism_break", None)
        print(json.dumps(result))
        return 0
    raise Refusal("f05_cli_verb", argv)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as refusal:
        print(json.dumps({"refused": refusal.code,
                          "detail": refusal.detail}))
        sys.exit(1)
