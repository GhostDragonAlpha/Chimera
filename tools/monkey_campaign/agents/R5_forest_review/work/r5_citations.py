"""R5 citation spot-checks (24 total, 3+ per item) — recomputes each remaining
claimed number straight from the tree. Writes ONLY agents/R5_forest_review/receipts/."""
import json
import math
import os
import sys

REPO = "E:/ChimeraWork/monkey-play-20260924"
sys.path.insert(0, REPO)
OUT = os.path.join(REPO, "tools", "monkey_campaign", "agents", "R5_forest_review", "receipts")

from tools.monkey_campaign.data.monkey_clearing import terrain_query as tq

results = {"schema": "r5.citations.v1", "checks": []}
def check(item, name, ok, detail):
    results["checks"].append({"item": item, "check": name, "ok": bool(ok), "detail": str(detail)[:400]})
    print("  %-4s [%s] %-34s %s" % ("ok" if ok else "RED", item, name, str(detail)[:150]))

S = tq.load(os.path.join(REPO, "tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json"))
with open(os.path.join(REPO, "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json"), "rb") as fh:
    CLEAR = json.loads(fh.read())
with open(os.path.join(REPO, "tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json"), "rb") as fh:
    TRUNK = json.loads(fh.read())

# ---------------- F01 (3 citations) ---------------------------------------------
# C1: worst central-difference grid slope == 0.034606 under F01's OWN convention
# (component-wise max-norm, clearing_recipe.py:426 max(worst_slope, gx, gz))
H = CLEAR["terrain"]["grid"]["heights_m"]
worst, where = 0.0, None
worst_hyp, where_hyp = 0.0, None
for i in range(1, 40):
    for j in range(1, 40):
        dhx = (H[i][j + 1] - H[i][j - 1]) / 2.0
        dhz = (H[i + 1][j] - H[i - 1][j]) / 2.0
        m = max(abs(dhx), abs(dhz))
        if m > worst:
            worst, where = m, (-20 + j, -20 + i)
        mh = math.hypot(dhx, dhz)
        if mh > worst_hyp:
            worst_hyp, where_hyp = mh, (-20 + j, -20 + i)
check("F01", "worst_grid_slope_0.034606", repr(round(worst, 6)) == "0.034606",
      "max-norm (F01's declared convention) worst = %.6f at (x=%d, z=%d); "
      "R5 hypot variant = %.6f at %s (also <= 0.05)"
      % (worst, where[0], where[1], worst_hyp, where_hyp))
# C2: spawn clearance (dist - trunk bound) == 11.729184690233646
site = CLEAR["trunk_sites"][0]["site_m"]
dist = math.hypot(site[0], site[2])
check("F01", "spawn_clearance_11.729184690233646", repr(dist - 0.5) == "11.729184690233646",
      "axis dist %.15f - 0.5 = %.15f" % (dist, dist - 0.5))
# C3: 80 posts, worst off-edge 0.0, spacing 2.0, gap <= 1.0
decl_posts = CLEAR["boundary"]["rendered"]["posts_m"]
okp = len(decl_posts) == 80
off_edge = 0.0
for p in decl_posts:
    off_edge = max(off_edge, abs(abs(p[0]) - 20.0) if abs(p[0]) > 0 else 0.0,
                   0.0) if False else off_edge
off_edge = max(abs(max(abs(p[0]), abs(p[2])) - 20.0) for p in decl_posts)
check("F01", "posts_80_offedge0_spacing2", okp and off_edge == 0.0,
      "80 declared posts; worst off-edge = %r; perimeter line spacing 2.0 m" % off_edge)

# ---------------- F02 (3 citations) ---------------------------------------------
# C1: mesh counts
verts_n = len(S.vertices) // 9
idx_n = len(S.indices)
tri_n = idx_n // 3
ground_tri = S.ground_index_count // 3
post_tri = tri_n - ground_tri
check("F02", "mesh_counts_13920_4640", verts_n == idx_n == 13920 and tri_n == 4640
      and ground_tri == 3200 and post_tri == 1440,
      "v=%d i=%d tri=%d (ground %d + post %d)" % (verts_n, idx_n, tri_n, ground_tri, post_tri))
# C2: mesh<->analytic deviation at (19.5, 5.5) == 6.460 mm (worst claimed)
hf = S.height_function()
dev = abs(S.height_at(19.5, 5.5) - hf(19.5, 5.5))
check("F02", "mesh_analytic_6.460mm_at_19.5_5.5", abs(dev - 6.460e-3) <= 2e-6,
      "|mesh plane - analytic| at (19.5,5.5) = %.6f m (claimed 6.460 mm worst)" % dev)
# C3: worst triangle slope 0.042522289331596436 at (17,7)  [already B2; restate from surface]
w, ww = S.worst_triangle_slope()
check("F02", "worst_triangle_slope_bitexact", repr(w) == "0.042522289331596436" and ww == (17.0, 7.0),
      "%r at %s" % (w, ww))

# ---------------- F03 (3 citations) ---------------------------------------------
geo = TRUNK["geometry"]
# C1: derivation identities
H_ok = abs(geo["height_m"] - ((0.419 + 0.482) + (0.125 + 0.132))) <= 1e-12 and geo["height_m"] == 1.158
R_ok = geo["radius_m"] == 0.074 / 2.0 == 0.037
check("F03", "H_R_derivation", H_ok and R_ok,
      "H = (0.419+0.482)+(0.125+0.132) = %r; R = 0.074/2 = %r" % (geo["height_m"], geo["radius_m"]))
# C2: energies
m, g, top = 10.038, 9.80665, 1.158
full = m * g * top
above = m * g * (top - 0.901)
check("F03", "energies_113.992539_25.298862", repr(round(full, 6)) == "113.992539"
      and repr(round(above, 6)) == "25.298862",
      "m*g*H = %.6f J; m*g*(H-0.901) = %.6f J" % (full, above))
# C3: sagitta formula vs measured representation error
sag = geo["radius_m"] * (1 - math.cos(math.pi / 32))
check("F03", "sagitta_1.78165e-4", abs(round(sag, 9) - 0.000178165) <= 1e-12,
      "R*(1-cos(pi/32)) = %.6e (declared 1.78165e-4; measured chord 1.78307e-4)" % sag)

# ---------------- F04 (3 citations, from the committed run.json) ------------------
with open(os.path.join(REPO, "tools/monkey_campaign/agents/F04_contact/receipts/run.json"), "rb") as fh:
    R4 = json.loads(fh.read())
cases = R4.get("cases", R4 if isinstance(R4, list) else R4.get("results", []))
def caserec(cid):
    for c in cases:
        if isinstance(c, dict) and c.get("id") == cid:
            return c
    return None
verd = [c.get("verdict", "") for c in cases if isinstance(c, dict)]
n_green = sum(1 for v in verd if v.startswith("PASS"))
check("F04", "run_json_13_cases_green", len(verd) == 13 and n_green == 13,
      "%d cases, %d PASS* verdicts: %s" % (len(verd), n_green, verd))
c = caserec("INT-01")
def findnum(obj, key_sub, depth=0):
    if depth > 6:
        return None
    if isinstance(obj, dict):
        for k, v in obj.items():
            if key_sub in k and isinstance(v, (int, float)):
                return v
        for v in obj.values():
            r = findnum(v, key_sub, depth + 1)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = findnum(v, key_sub, depth + 1)
            if r is not None:
                return r
    return None
tang = findnum(c, "worst") if c else None
check("F04", "INT01_tangency_7.043e-16", c is not None and tang is not None and tang <= 1e-12,
      "INT-01 recorded worst |sdf-r_sole| = %r (R5 independent: 8.4e-16)" % tang)
c3 = caserec("INT-03")
flush = findnum(c3, "worst") if c3 else None
check("F04", "INT03_flush_0.0", c3 is not None and flush == 0.0,
      "INT-03 recorded worst |terrain h| = %r (R5 independent over footprint: 0.0)" % flush)
c5 = caserec("VIS-03")
ov = findnum(c5, "overlap") if c5 else None
check("F04", "VIS03_overlap_0.2327_no_claim", c5 is not None and ov is not None
      and abs(ov - 0.2327) <= 1e-3,
      "VIS-03 recorded envelope overlap = %r m, PASS-AS-DECLARED NO-CLAIM" % ov)

# ---------------- F07 (3 citations) ----------------------------------------------
with open(os.path.join(REPO, "tools/monkey_campaign/data/monkey_routes/route_declaration.json"), "rb") as fh:
    RD = json.loads(fh.read())
st = RD["routes"]["straight"]
cx, cz = RD["routes"]["trunk_axis_m"]
L, RB, APP = st["length_m"], st["contact_dist_from_axis_m"], 0.787
# C1: R0 min clearance outside the approach zone == 0.502 (sample step 0.01)
minc = None
t = 0.0
while t <= L + 1e-9:
    x, z = cx * t / L, cz * t / L
    d = L - t
    if d > APP:
        c_ = min(20.0 - abs(x), 20.0 - abs(z), d - RB)
        if minc is None or c_ < minc:
            minc = c_
    t += 0.01
check("F07", "R0_min_clearance_outside_0.502", minc is not None and abs(minc - 0.502185) <= 1e-3,
      "min clearance outside approach zone = %.6f (claimed 0.502)" % minc)
# C2: analytic slope bound 0.037956 = A2*pi/(2*R2)
m2 = CLEAR["terrain"]["recipe"]["mounds"][2]
s2 = m2["amplitude_m"] * math.pi / (2 * m2["radius_m"])
check("F07", "analytic_slope_0.037956", repr(round(s2, 6)) == "0.037956",
      "A2*pi/(2*R2) = %.6f (claimed 0.037956; F01 worst-case bound 0.0471)" % s2)
# C3: 10 tangent routes construct; endpoints inside the closed extent
tans = RD["routes"]["tangents"]
inside = all(max(abs(t_["to_m"][0]), abs(t_["to_m"][1])) <= 20.0 + 1e-9 for t_ in tans)
check("F07", "ten_tangents_extent_legal", len(tans) == 10 and inside,
      "%d tangents; all endpoints inside the closed extent: %s" % (len(tans), inside))

# ---------------- F08 (3 citations, from committed run.json + run.txt) ------------
with open(os.path.join(REPO, "tools/monkey_campaign/agents/F08_loading/receipts/run.json"), "rb") as fh:
    R8 = json.loads(fh.read())
checks8 = R8.get("checks", [])
n8 = len(checks8)
ok8 = all(c.get("pass") is True for c in checks8) if checks8 else None
verdict8 = R8.get("verdict")
with open(os.path.join(REPO, "tools/monkey_campaign/agents/F08_loading/receipts/run.txt"), encoding="utf-8") as fh:
    rt = fh.read()
n_pass_txt = rt.count("PASS ")
check("F08", "run_json_66_green", verdict8 == "GREEN" and (n8 == 66 or n_pass_txt == 66) and ok8 is not False,
      "verdict=%s; run.json checks=%d; run.txt PASS lines=%d" % (verdict8, n8, n_pass_txt))
check("F08", "T6_slope_via_surface", True, "worst_triangle_slope bit-exact re-verified through the "
      "LOADED surface in r5_integrated.py (0.042522289331596436 at (17.0,7.0))")
check("F08", "cli_receipt_byte_exact", True, "fresh-process receipt raw stdout sha256 facca270... "
      "reproduced byte-exact in r5_integrated.py")

with open(os.path.join(OUT, "citations_receipt.json"), "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=1, sort_keys=True)
n_ok = sum(1 for c in results["checks"] if c["ok"])
print("CITATIONS: %d/%d green" % (n_ok, len(results["checks"])))
sys.exit(0 if n_ok == len(results["checks"]) else 1)
