"""R5 integrated scenario: load via F08's loader, query F02's surface, apply
F04-style SDF, walk F07's corridor — one coherent world. Headless, CPU, stdlib.
Writes ONLY agents/R5_forest_review/receipts/."""
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import deque

REPO = "E:/ChimeraWork/monkey-play-20260924"
sys.path.insert(0, REPO)
CAMP = os.path.join(REPO, "tools", "monkey_campaign")
OUT = os.path.join(CAMP, "agents", "R5_forest_review", "receipts")

from tools.monkey_campaign.data.monkey_forest import forest_loader as fl
from tools.monkey_campaign.data.monkey_clearing import terrain_query as tq

results = {"schema": "r5.integrated.v1", "checks": [], "numbers": {}}
def check(name, ok, detail):
    results["checks"].append({"check": name, "ok": bool(ok), "detail": str(detail)[:400]})
    print("  %-4s %-38s %s" % ("ok" if ok else "RED", name, str(detail)[:170]))

# ---------- B1: the loader ------------------------------------------------------
scene = fl.load_forest()
art = scene.receipt["artifacts"]
check("B1_load_forest", all(art[k]["recompiled_identical"] for k in fl.ORDER),
      "four artifacts recompiled-identical; file shas " +
      ", ".join(art[k]["file_sha256"][:8] for k in fl.ORDER))
check("A6_initial_state_sha", scene.initial_state["initial_state_sha256"]
      == "c3286e14a787f6bb65ccc93dc3e80b0412d777048d109d404ca49328fe1bf627",
      scene.initial_state["initial_state_sha256"])

# CLI receipt from scratch, twice, byte-compare + sha (RAW pipe bytes, as F08 hashed)
outs = []
for _ in range(2):
    p = subprocess.run([sys.executable, "tools/monkey_campaign/data/monkey_forest/forest_loader.py",
                        "receipt"], capture_output=True, cwd=REPO, timeout=600)
    outs.append(p.stdout)
cli_sha = hashlib.sha256(outs[0]).hexdigest()
check("B1_cli_determinism", p.returncode == 0 and outs[0] == outs[1]
      and cli_sha == "facca270dcd4fd9e7cce5cea913c56baf7816c9aea747bf91aaecd77f7cc01f5",
      "exit=%d raw stdout sha=%s == F08's claimed facca270... (byte-exact)"
      % (p.returncode, cli_sha[:16]))
cli = json.loads(outs[0].decode("utf-8"))
check("B1_cli_initial_state", cli["initial_state_sha256"] == scene.initial_state["initial_state_sha256"],
      cli["initial_state_sha256"][:16])
check("B1_cli_trunk_site", cli["trunk_site"]["base_centre_m"] == [11.976783, 0.0, 2.471766]
      and cli["trunk_site"]["radius_m"] == 0.037 and cli["trunk_site"]["height_m"] == 1.158,
      json.dumps(cli["trunk_site"]))

# ---------- B2: F02 surface at site + spawn -------------------------------------
S = scene.terrain_surface
site = (11.976783, 2.471766)
h_site, g_site = S.height_at(*site), S.gradient_at(*site)
n_site = S.normal_at(*site)
h_spawn, g_spawn = S.height_at(0.0, 0.0), S.gradient_at(0.0, 0.0)
check("B2_site_surface", h_site == 0.0 and g_site == (0.0, 0.0) and n_site == (0.0, 1.0, 0.0),
      "h=%r grad=%r n=%r" % (h_site, g_site, n_site))
check("B2_spawn_surface", h_spawn == 0.0 and g_spawn == (0.0, 0.0)
      and S.classify(0.0, 0.0) == "inside", "h=%r grad=%r" % (h_spawn, g_spawn))
# T6 claims through the loader
w, wwhere = S.worst_triangle_slope()
check("B2_worst_triangle_slope", repr(w) == "0.042522289331596436" and wwhere == (17.0, 7.0),
      "worst=%r at %s" % (w, wwhere))
check("B2_extent_strict_gt", S.classify(20.0, 0.0) == "inside" and S.classify(20.05, 0.0) == "outside",
      "20.0 inside, 20.05 outside")
try:
    S.height_at(20.05, 0.0)
    refused = False
except tq.Refusal as e:
    refused = (e.code == "f02_outside_extent")
check("B2_outside_refusal", refused, "f02_outside_extent past edge")

# ---------- B3: F04-style trunk SDF (my own exact capped-cylinder) --------------
TR = scene.trunk
sol = TR["collision_representation"]["solid"]
CX, CZ = sol["axis_base_m"][0], sol["axis_base_m"][2]
R, H = sol["radius_m"], sol["height_m"]
def sdf(x, y, z):
    a = abs(y - (0.0 + H / 2.0)) - H / 2.0
    dxy = math.hypot(x - CX, z - CZ) - R
    return min(max(a, dxy), 0.0) + math.hypot(max(a, 0.0), max(dxy, 0.0))
s_axis = sdf(CX, H / 2.0, CZ)
check("B3_axis_sdf", s_axis == -R, "on-axis sdf=%r (F04 GHO-03 claimed -0.037)" % s_axis)
r_sole = 0.004
worst_t = 0.0
for k in range(320):
    ang = 2 * math.pi * k / 320
    x, z = CX + (R + r_sole) * math.cos(ang), CZ + (R + r_sole) * math.sin(ang)
    worst_t = max(worst_t, abs(sdf(x, 0.5, z) - r_sole))
check("B3_tangency", worst_t <= 1e-12, "worst |sdf-r_sole| over 320 lateral points = %.3e (F04 INT-01 7.0e-16)" % worst_t)
# flushness: terrain over the base-cap disk + footprint grid
worst_h, worst_g = 0.0, 0.0
for i in range(81):
    for j in range(81):
        x, z = CX - 0.5 + 0.0125 * i, CZ - 0.5 + 0.0125 * j
        if math.hypot(x - CX, z - CZ) <= 0.5:
            worst_h = max(worst_h, abs(S.height_at(x, z)))
            gg = S.gradient_at(x, z)
            worst_g = max(worst_g, math.hypot(*gg))
check("B3_flush_terrain_footprint", worst_h == 0.0 and worst_g == 0.0,
      "worst |terrain h| over 0.5 m footprint = %r, worst |grad| = %r (F04 INT-03)" % (worst_h, worst_g))
# trunk base ring vertices sit exactly on the terrain
verts = TR["render_mesh"]["vertices"]
base_ys = [v[1] for v in verts if v[1] == 0.0]
check("B3_base_ring_y0", len(base_ys) >= 65, "%d vertices at y=0.0 (base rings)" % len(base_ys))
# VIS-02 chord error recompute from stored vertices
bottom = verts[0:32]
mid_err = 0.0
for k in range(32):
    a, b = bottom[k], bottom[(k + 1) % 32]
    mx, mz = (a[0] + b[0]) / 2.0, (a[2] + b[2]) / 2.0
    mid_err = max(mid_err, R - math.hypot(mx - CX, mz - CZ))
check("B3_chord_error", repr(round(mid_err, 9)) == "0.000178307" or abs(mid_err - 1.78307e-4) <= 1e-9,
      "recomputed chord error = %.6e m (declared 1.78307e-4, TOL 2e-4)" % mid_err)

# ---------- B4: F07 corridor (my own sweep + BFS) --------------------------------
RD = scene.routes
half = 20.0
step, x0, nx = 0.05, -20.0, 801
cx, cz = RD["routes"]["trunk_axis_m"]
RB = 0.287
blocked_cells = []
grad_worst, grad_where = 0.0, None
free = bytearray(nx * nx)
N = nx
for i in range(N):          # row = z
    z = x0 + i * step
    for j in range(N):      # col = x
        x = x0 + j * step
        d = math.hypot(x - cx, z - cz)
        if d < RB:
            blocked_cells.append((round(x, 2), round(z, 2)))
        else:
            free[i * N + j] = 1
        g = S.gradient_at(x, z)
        m = math.hypot(g[0], g[1])
        if m > grad_worst:
            grad_worst, grad_where = m, (x, z)
check("B4_blocked_count_B2", len(blocked_cells) == 107,
      "blocked cells = %d (F07 claimed 107, all B2)" % len(blocked_cells))
check("B4_slope_never_blocks", grad_worst <= 0.05,
      "worst grid gradient = %.6f at %s (claimed 0.042522 at (17.0,7.0))" % (grad_worst, grad_where))
# BFS reachability of all free cells from spawn cell
start = (int(round((0.0 - x0) / step)), int(round((0.0 - x0) / step)))  # (i=z, j=x)
seen = bytearray(N * N)
dq = deque()
si = start[0] * N + start[1]
seen[si] = 1
dq.append(si)
reach = 1
while dq:
    cur = dq.popleft()
    i, j = divmod(cur, N)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ii, jj = i + di, j + dj
            if 0 <= ii < N and 0 <= jj < N:
                idx = ii * N + jj
                if free[idx] and not seen[idx]:
                    seen[idx] = 1
                    reach += 1
                    dq.append(idx)
n_free = sum(free)
check("B4_reachability", reach == n_free == 641494,
      "reachable %d of free %d (claimed 641,494/641,494)" % (reach, n_free))
# corridor >= 1.0 m: BFS on cells with clearance >= 0.5 (envelope), spawn -> approach zone
def clearance(x, z):
    return min(half - abs(x), half - abs(z), math.hypot(x - cx, z - cz) - RB)
seen2 = bytearray(N * N)
seen2[si] = 1
dq.append(si)
entered = False
best = None
while dq:
    cur = dq.popleft()
    i, j = divmod(cur, N)
    x, z = x0 + j * step, x0 + i * step
    c = clearance(x, z)
    if c + 1e-9 >= 0.5:
        if best is None or c < best[0]:
            best = (c, (x, z))
        d = math.hypot(x - cx, z - cz)
        if d <= RB + 0.5 + 2 * 0.25:     # inside/near the declared approach zone
            entered = True
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ii, jj = i + di, j + dj
                if 0 <= ii < N and 0 <= jj < N:
                    idx = ii * N + jj
                    if free[idx] and not seen2[idx]:
                        seen2[idx] = 1
                        dq.append(idx)
check("B4_corridor_envelope", entered and best is not None and best[0] + 1e-9 >= 0.5,
      "1.0 m-wide corridor connects spawn to the approach zone; tightest corridor cell on the route c=%.4f at %s" % (best[0], best[1]))
c_gate = clearance(11.3, 2.0)
check("B4_gate_number", abs(c_gate - 0.538) <= 5e-4,
      "clearance at (11.3, 2.0) = %.6f (F07 claimed 0.538 -> width 1.076; R5's precomputed "
      "0.538247 was R5's own arithmetic slip, honest row)" % c_gate)

# ---------- D1: R0 endpoint semantics -------------------------------------------
straight = RD["routes"]["straight"]
L = straight["length_m"]
ux, uz = cx / L, cz / L
d_at_L = math.hypot(cx - ux * L, cz - uz * L)   # position at t = length_m
t_contact = L - straight["contact_dist_from_axis_m"]
overshoot_samples = sum(1 for k in range(int((L - t_contact) / 0.01) + 1)
                        if t_contact + k * 0.01 <= L)
check("D1_R0_note_vs_numbers",
      abs(d_at_L) <= 1e-9 and t_contact < L,
      "at t=length_m the walker centre is ON the axis (dist_to_axis=%.4f); "
      "contact ring is at t=%.6f; walking the full declared length puts ~%d samples inside B2 "
      "(envelope 0.287 m into the blocker). Suites stop at t_contact; the committed "
      "note/fields can mislead a naive W10 consumer" % (d_at_L, t_contact, overshoot_samples))
results["numbers"]["R0"] = {"length_m": L, "t_contact_m": t_contact,
                            "dist_at_length_m": d_at_L, "hazard_samples": overshoot_samples}

# ---------- B5/D2: negative + edge coordinates -----------------------------------
ok_corners = True
for x, z in ((-20.0, -20.0), (20.0, 20.0), (-20.0, 20.0), (20.0, -20.0), (-0.0, -0.0)):
    try:
        h = S.height_at(x, z)
        g = S.gradient_at(x, z)
        n = S.normal_at(x, z)
        ok_corners = ok_corners and math.isfinite(h) and all(math.isfinite(v) for v in n)
    except tq.Refusal:
        ok_corners = False
check("B5_closed_corners_finite", ok_corners, "all four closed corners + -0.0 answer finite")
refused_n = 0
for x, z in ((-20.0 - 1e-9, 0.0), (20.0 + 1e-9, 0.0), (0.0, -20.0 - 1e-9), (0.0, 20.0 + 1e-9),
             (-20.5, 0.0), (25.0, 25.0)):
    try:
        S.height_at(x, z)
    except tq.Refusal as e:
        refused_n += (e.code == "f02_outside_extent")
check("B5_negative_refusals", refused_n == 6, "6/6 past-edge (incl. negative) queries refused")
# diagonal continuity: A/B formulas agree on the diagonal
hdiag = 0.0
for i in range(40):
    for j in range(40):
        ix, iz = j, i
        h00, h10, h01, h11 = (S.heights[iz][ix], S.heights[iz][ix + 1],
                              S.heights[iz + 1][ix], S.heights[iz + 1][ix + 1])
        t = j % 1 if False else 0.5
        hA = h00 + (h11 - h01) * t + (h01 - h00) * t
        hB = h00 + (h10 - h00) * t + (h11 - h10) * t
        hdiag = max(hdiag, abs(hA - hB))
check("B5_diagonal_identity", hdiag <= 1e-9,
      "max |A-B| on cell diagonals = %.4e m (R5 predicted exactly 0.0; measured ~1 ulp = 2.8e-17, "
      "the SAME misprediction F02 recorded in its honesty row; within the frozen 1e-9 family)" % hdiag)

# ---------- B6/D3: site slope truth ----------------------------------------------
mounds = scene.clearing["terrain"]["recipe"]["mounds"]
d_mounds = [round(math.hypot(site[0] - m["centre_x_m"], site[1 - 1] - m["centre_z_m"]) - m["radius_m"], 4)
            for m in mounds]
check("B6_site_clear_of_mounds", all(d > 0 for d in d_mounds),
      "site margin outside each mound radius: %s" % d_mounds)
try:
    from tools.monkey_campaign.data.monkey_clearing import terrain_bundle as tbm
    hf = S.height_function()
    ha = hf(site[0], site[1])
    check("B6_analytic_site_height", ha == 0.0, "analytic h(site) = %r" % ha)
except Exception as exc:
    check("B6_analytic_site_height", False, repr(exc))

# ---------- D5: mound 2 crosses the east edge ------------------------------------
m2 = mounds[2]
reach_e = m2["centre_x_m"] + m2["radius_m"]
h_out = None
try:
    hf = S.height_function()
    h_out = hf(21.0, 6.0)
except Exception as exc:
    h_out = repr(exc)
xs = None
mesh_max_x = max(S.vertices[9 * S.indices[t]] for t in range(S.ground_index_count))  # GROUND only
mesh_max_x_all = max(S.vertices[9 * i] for i in range(len(S.vertices) // 9))        # incl. posts
refused_out = False
try:
    S.height_at(21.0, 6.0)
except tq.Refusal as e:
    refused_out = (e.code == "f02_outside_extent")
check("D5_mound2_edge_clip", reach_e > 20.0 and h_out > 0 and refused_out
      and abs(mesh_max_x - 20.0) <= 1e-12 and abs(mesh_max_x_all - 20.05) <= 1e-12,
      "mound 2 analytic reach x=%.3f m; h_analytic(21,6)=%.4f m exists but query refuses; "
      "GROUND mesh max x=%.6f (clipped at the edge); all-vertex max x=%.6f = posts straddling "
      "the edge by their 0.05 m radius (F02's declared amendment)" % (reach_e, h_out, mesh_max_x, mesh_max_x_all))

# ---------- D7: loader initial_state == F07 declaration ---------------------------
rg = scene.initial_state["route_graph"]
st = RD["routes"]["straight"]
ok_d7 = (rg["spawn_m"] == RD["routes"]["spawn_m"]
         and rg["trunk_axis_m"] == RD["routes"]["trunk_axis_m"]
         and rg["straight"]["id"] == st["id"] and rg["straight"]["length_m"] == st["length_m"]
         and rg["straight"]["to_m"] == st["to_m"]
         and [t["id"] for t in rg["tangents"]] == [t["id"] for t in RD["routes"]["tangents"]]
         and rg["route_grid"]["nx"] == RD["route_grid"]["nx"]
         and rg["blockers"] == ["B1", "B2"])
check("D7_initial_state_copies_f07", ok_d7,
      "spawn/axis/straight/tangents/grid/blockers copied verbatim")

# ---------- posts ------------------------------------------------------------------
posts = S.posts()
check("B4_posts_80", len(posts) == 80, "recovered %d posts from the mesh" % len(posts))

scene.teardown()
check("B1_teardown_clean", scene.live_resources() == [] and scene.clearing is None,
      "teardown: zero live resources")

# ---------- committed receipt hash claims (no re-run of sibling suites) -----------
HASH_CLAIMS = {
    "F04 receipts/run.json": ("tools/monkey_campaign/agents/F04_contact/receipts/run.json", 10442, "efded804"),
    "F07 receipts/run.json": ("tools/monkey_campaign/agents/F07_obstacles/receipts/run.json", None, "7baaf018"),
    "F08 receipts/run.json": ("tools/monkey_campaign/agents/F08_loading/receipts/run.json", None, "4ebd3a6c"),
    "F08 receipts/run.txt": ("tools/monkey_campaign/agents/F08_loading/receipts/run.txt", None, "235938d7"),
    "forest_loader.py": ("tools/monkey_campaign/data/monkey_forest/forest_loader.py", None, "53d7fdde"),
    "verify_loading.py": ("tools/monkey_campaign/agents/F08_loading/verify_loading.py", None, "fc4d34ab"),
}
for name, (rel, nbytes, prefix) in HASH_CLAIMS.items():
    full = os.path.join(REPO, rel)
    with open(full, "rb") as fh:
        raw = fh.read()
    h = hashlib.sha256(raw).hexdigest()
    okh = h.startswith(prefix) and (nbytes is None or len(raw) == nbytes)
    check("receipt_hash_%s" % name.split()[-1].replace(".json", "").replace(".txt", "").replace(".py", ""),
          okh, "%s: %d B sha %s... (claimed %s...%s)"
          % (rel.split("/")[-2] + "/" + rel.split("/")[-1], len(raw), h[:8], prefix,
             "" if nbytes is None else ", %d B" % nbytes))

with open(os.path.join(OUT, "integrated_receipt.json"), "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=1, sort_keys=True)
n_ok = sum(1 for c in results["checks"] if c["ok"])
print("INTEGRATED: %d/%d green; fired=%s" % (n_ok, len(results["checks"]), 
      [c["check"] for c in results["checks"] if not c["ok"]]))
sys.exit(0 if n_ok == len(results["checks"]) else 1)
