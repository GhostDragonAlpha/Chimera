"""R5 identity check A1-A6: recompute the four declarations from the recipes in
FRESH SUBPROCESSES, byte-compare vs committed files, verify mutual pins and the
one-number invariants. Writes ONLY agents/R5_forest_review/receipts/."""
import hashlib
import json
import math
import os
import subprocess
import sys

REPO = "E:/ChimeraWork/monkey-play-20260924"
CAMP = os.path.join(REPO, "tools", "monkey_campaign")
OUT = os.path.join(CAMP, "agents", "R5_forest_review", "receipts")

PATHS = {
    "clearing": "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
    "terrain": "tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json",
    "trunk": "tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json",
    "routes": "tools/monkey_campaign/data/monkey_routes/route_declaration.json",
}
EXPECT = {  # from the reports (claims under test)
    "clearing": {"pin": "aa2607df97e0d6ec6a132b1e1ed0686da2ae920de7d659a8bb5ced013a358474",
                 "file": "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1",
                 "bytes": 13112},
    "terrain": {"pin": "8c7d60c88a75234a4ea94bc5ec83b666d620502b47cac8667e83b8713cb04fe0",
                "file": "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52",
                "bytes": 877752},
    "trunk": {"pin": "b7089e7826a221a570b261b8c69666a4017a6ab62d20a2223d061654d0f63fe3",
              "file": "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1",
              "bytes": 16634},
    "routes": {"pin": "7c3ad6e86039b63324e4695abe5e5525e2693a98f9a0ef91355b804da8b8e211",
               "file": "28dff2b33e74fcc4103ac3699899b0937f6975323758d1fa142092704bf4496c",
               "bytes": 8495},
}

RECOMPILE_SNIPPET = r'''
import json, os, sys, tempfile
sys.path.insert(0, REPO)
def load(name, rel):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
import recompile_child  # placeholder never used
'''

CHILD = r'''
import json, os, sys, tempfile, importlib.util
REPO = r"%(repo)s"
sys.path.insert(0, REPO)
def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
clearing_mod = load("clearing_recipe", "tools/monkey_campaign/data/monkey_clearing/clearing_recipe.py")
terrain_mod  = load("terrain_bundle",  "tools/monkey_campaign/data/monkey_clearing/terrain_bundle.py")
trunk_mod    = load("trunk_recipe",    "tools/monkey_campaign/data/monkey_trunk/trunk_recipe.py")
routes_mod   = load("route_recipe",    "tools/monkey_campaign/data/monkey_routes/route_recipe.py")

def canon(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()

import hashlib
def sha(b): return hashlib.sha256(b).hexdigest()

out = {}
c = clearing_mod.compile_declaration(seed=4598321)
clearing_mod.validate_declaration(c)
cb = canon(c)
out["clearing"] = {"bytes": len(cb), "file_sha256": sha(cb), "self_pin": c["declaration_sha256"]}
with tempfile.TemporaryDirectory() as tmp:
    p = os.path.join(tmp, "clearing_declaration.json")
    with open(p, "wb") as fh: fh.write(cb)
    t = terrain_mod.compile_bundle(p)
terrain_mod.validate_bundle(t)
tb = canon(t)
out["terrain"] = {"bytes": len(tb), "file_sha256": sha(tb), "self_pin": t["bundle_sha256"]}
tr = trunk_mod.compile_declaration(f01_declaration=c)
trunk_mod.validate_declaration(tr)
trb = canon(tr)
out["trunk"] = {"bytes": len(trb), "file_sha256": sha(trb), "self_pin": tr["declaration_sha256"]}
rt = routes_mod.compile_declaration()
routes_mod.validate_declaration(rt)
rtb = canon(rt)
out["routes"] = {"bytes": len(rtb), "file_sha256": sha(rtb), "self_pin": rt["route_declaration_sha256"]}
print(json.dumps(out, sort_keys=True))
''' % {"repo": REPO}

results = {"schema": "r5.identity.v1", "checks": [], "fired": []}

def check(name, ok, detail):
    results["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
    if not ok:
        results["fired"].append(name)

# --- A1: fresh-subprocess recompiles vs committed bytes -----------------------
proc = subprocess.run([sys.executable, "-c", CHILD], capture_output=True, text=True,
                      cwd=REPO, timeout=600)
if proc.returncode != 0:
    check("A1_recompile_subprocess", False, "child failed: " + proc.stderr[-800:])
    recomp = {}
else:
    recomp = json.loads(proc.stdout.strip().splitlines()[-1])
    for key, spec in EXPECT.items():
        r = recomp.get(key, {})
        with open(os.path.join(REPO, PATHS[key]), "rb") as fh:
            raw = fh.read()
        fh_sha = hashlib.sha256(raw).hexdigest()
        ok = (r.get("bytes") == spec["bytes"] == len(raw)
              and r.get("file_sha256") == spec["file"] == fh_sha
              and r.get("self_pin") == spec["pin"])
        check("A1_recompile_%s" % key, ok,
              "recompiled %d B sha %s pin %s | committed %d B sha %s | claimed %d B sha %s pin %s"
              % (r.get("bytes", -1), r.get("file_sha256", "?")[:16], str(r.get("self_pin"))[:16],
                 len(raw), fh_sha[:16], spec["bytes"], spec["file"][:16], spec["pin"][:16]))

# --- load committed objects for pin checks ------------------------------------
objs = {}
for key, rel in PATHS.items():
    with open(os.path.join(REPO, rel), "rb") as fh:
        objs[key] = json.loads(fh.read())

# --- A2: mutual pins -----------------------------------------------------------
trunk_site_pin = objs["trunk"]["site"]["provenance"]["declaration_sha256"]
check("A2_trunk_pins_clearing", trunk_site_pin == objs["clearing"]["declaration_sha256"] == EXPECT["clearing"]["pin"],
      "trunk.site.provenance=%s clearing=%s" % (trunk_site_pin[:16], objs["clearing"]["declaration_sha256"][:16]))
rin = objs["routes"]["inputs"]
pin_ok = (rin["clearing"]["declaration_sha256"] == EXPECT["clearing"]["pin"]
          and rin["clearing"]["file_sha256"] == EXPECT["clearing"]["file"]
          and rin["terrain"]["bundle_sha256"] == EXPECT["terrain"]["pin"]
          and rin["terrain"]["file_sha256"] == EXPECT["terrain"]["file"]
          and rin["trunk"]["declaration_sha256"] == EXPECT["trunk"]["pin"]
          and rin["trunk"]["file_sha256"] == EXPECT["trunk"]["file"])
check("A2_routes_pins_upstream", pin_ok, json.dumps({k: {kk: vv[:12] for kk, vv in v.items() if kk.endswith("sha256")} for k, v in rin.items()}, sort_keys=True))

# --- A3/A4: one-number invariants ----------------------------------------------
site = [11.976783, 0.0, 2.471766]
f01_site = objs["clearing"]["trunk_sites"][0]["site_m"]
f03_site = objs["trunk"]["site"]["base_centre_m"]
f03_solid_base = objs["trunk"]["collision_representation"]["solid"]["axis_base_m"]
f07_axis = objs["routes"]["routes"]["trunk_axis_m"]
f07_b2 = [b for b in objs["routes"]["blocking_causes"]["blockers"] if b["id"] == "B2"][0]["site_m"]
def planar(v):  # route layer stores [x, z] (row=z, col=x)
    return [v[0], v[2]] if len(v) == 3 else v
check("A3_site_identity", all(a == b for a, b in zip(f01_site, site))
      and f03_site == site and f03_solid_base == site
      and f07_axis == planar(site) and f07_b2 == planar(site),
      "F01=%s F03site=%s F03solid=%s F07axis=%s F07B2=%s" % (f01_site, f03_site, f03_solid_base, f07_axis, f07_b2))
check("A3_site_id_and_footprint", objs["clearing"]["trunk_sites"][0]["id"] == objs["trunk"]["object_id"] == "trunk_01",
      "ids: %s / %s" % (objs["clearing"]["trunk_sites"][0]["id"], objs["trunk"]["object_id"]))

sp = [0.0, 0.0, 0.0]
check("A4_spawn_identity",
      objs["clearing"]["spawn"]["position_m"] == sp
      and objs["trunk"]["approach_and_bounds"]["spawn_position_m"] == sp
      and objs["routes"]["routes"]["spawn_m"] == sp,
      "F01=%s F03=%s F07=%s" % (objs["clearing"]["spawn"]["position_m"],
                                objs["trunk"]["approach_and_bounds"]["spawn_position_m"],
                                objs["routes"]["routes"]["spawn_m"]))

# --- A5: derived cross-artifact numbers ----------------------------------------
r_trunk = objs["trunk"]["geometry"]["radius_m"]
r_body = objs["clearing"]["spawn"]["body_radius_envelope_m"]
r_block = objs["routes"]["blocking_causes"]["blockers"][1]["r_block_m"]
check("A5_r_block_derivation", abs(r_block - (r_trunk + r_body)) <= 1e-12 and r_block == 0.287,
      "r_block=%s r_trunk=%s r_body=%s" % (r_block, r_trunk, r_body))
# R0 geometry: to_m is the axis; length_m is the axis distance; contact at 0.287
straight = objs["routes"]["routes"]["straight"]
axis_dist = math.hypot(site[0], site[2])
check("A5_R0_length_is_axis_distance",
      abs(straight["length_m"] - axis_dist) <= 1e-6
      and straight["to_m"] == planar(site)
      and straight["contact_dist_from_axis_m"] == r_block,
      "length_m=%s axis_dist=%.6f to_m=%s contact=%s" % (straight["length_m"], axis_dist, straight["to_m"], straight["contact_dist_from_axis_m"]))
# spawn clearance claims across artifacts
cl_f01 = objs["clearing"]["spawn"]["required_clearance_m"]
cl_f03 = objs["trunk"]["approach_and_bounds"]["clearance_with_trunk_radius_m"]
check("A5_clearances_consistent",
      cl_f01 == 1.5 and abs(cl_f03 - (axis_dist - r_trunk)) <= 1e-6 and cl_f03 == 12.192185,
      "F01 required=%.6f F03 clearance=%.6f axis-r_trunk=%.6f" % (cl_f01, cl_f03, axis_dist - r_trunk))
# site terrain claims: F01 slope 0.0, F03 terrain_height 0.0
check("A5_site_terrain_claims",
      objs["clearing"]["trunk_sites"][0]["terrain_slope_at_site_m_per_m"] == 0.0
      and objs["trunk"]["site"]["terrain_height_at_site_m"] == 0.0
      and objs["trunk"]["site"]["terrain_slope_at_site_m_per_m"] == 0.0
      and objs["trunk"]["geometry"]["base_elevation_m"] == 0.0,
      "F01 slope=%s F03 h=%s slope=%s base=%s" % (
          objs["clearing"]["trunk_sites"][0]["terrain_slope_at_site_m_per_m"],
          objs["trunk"]["site"]["terrain_height_at_site_m"],
          objs["trunk"]["site"]["terrain_slope_at_site_m_per_m"],
          objs["trunk"]["geometry"]["base_elevation_m"]))
# seed identity
check("A5_seed_identity", objs["clearing"]["seed"] == 4598321,
      "seed=%s" % objs["clearing"]["seed"])
# extent identity across artifacts
check("A5_extent_identity",
      objs["clearing"]["extent"]["half_width_m"] == objs["routes"]["blocking_causes"]["blockers"][0]["half_width_m"] == 20.0,
      "half_width F01=%s F07B1=%s" % (objs["clearing"]["extent"]["half_width_m"],
                                      objs["routes"]["blocking_causes"]["blockers"][0]["half_width_m"]))

with open(os.path.join(OUT, "identity_receipt.json"), "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=1, sort_keys=True)
n_ok = sum(1 for c in results["checks"] if c["ok"])
print("IDENTITY: %d/%d green; fired=%s" % (n_ok, len(results["checks"]), results["fired"]))
for c in results["checks"]:
    print("  %-4s %s" % ("ok" if c["ok"] else "RED", c["check"]))
    print("       %s" % c["detail"][:190])
sys.exit(1 if results["fired"] else 0)
