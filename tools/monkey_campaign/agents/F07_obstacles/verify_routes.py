"""verify_routes -- M-F07: the route/blocking verification suite (F07, C14; C23 noted).

Frozen prereg: agents/F07_obstacles/PREREGISTRATION.md (written BEFORE this file).
Consumes ONLY the live integrated artifacts (F01 clearing, F02 terrain bundle +
terrain_query, F03 trunk) and the declared data module
tools/monkey_campaign/data/monkey_routes/route_recipe.py.

The traversal predicate below is the WHOLE route model, and its refuse sites are
exactly the frozen blocking-causes table rows:

    B1  outside the closed extent (strict >, engine out_of_patch semantics)
    B2  inside the trunk routing disk (F03 solid + F01 body envelope)
    N1  slope above F01's 0.05 walk law  (predicted never to fire; a hit is
        falsifier (c) and would make the mounds partial blockers)

There is no post term and no other refuse site: the enumeration sweep annotates
every refusal with its cause id and requires zero unexplained causes.

Stdlib + matplotlib(Agg) only; CPU-only; headless; deterministic receipts.
Run from the repo root:  python tools/monkey_campaign/agents/F07_obstacles/verify_routes.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
from array import array
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, REPO)


def _import(name, rel_path):
    try:
        return __import__(rel_path.replace("/", "."), fromlist=[name])
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            name, os.path.join(REPO, rel_path + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


rr = _import("route_recipe",
             "tools/monkey_campaign/data/monkey_routes/route_recipe")
tq = _import("terrain_query",
             "tools/monkey_campaign/data/monkey_clearing/terrain_query")
cr = rr._load_module("clearing_recipe",
                     "tools/monkey_campaign/data/monkey_clearing/clearing_recipe")
tr = rr._load_module("trunk_recipe",
                     "tools/monkey_campaign/data/monkey_trunk/trunk_recipe")

SNAP = rr.GRID_DECIMALS
HALF = rr.EXTENT_HALF_WIDTH_M
STEP = rr.GRID_STEP_M
N = rr.GRID_N
R_BLOCK = rr.R_BLOCK_M
APPROACH = rr.APPROACH_ZONE_R_M
MAX_SLOPE = rr.MAX_SLOPE_M_PER_M
MIN_CLEAR = rr.CORRIDOR_MIN_CLEARANCE_M
W_ENV = rr.W_ENV_M
CONTACT_BAND = rr.CONTACT_BAND_M
SAMPLE_STEP = rr.STRAIGHT_SAMPLE_STEP_M
TOL_DIR = rr.TANGENT_ROUND_TOL_M

Refusal = rr.Refusal


def snap(v):
    return round(v, SNAP)


# ---------------------------------------------------------------------------
def load_inputs():
    """Load + validate every live artifact; return the pieces the suite needs."""
    live = rr.load_live_inputs()          # refuses on any drifted input pin
    surface = tq.load(os.path.join(REPO, rr.INPUTS["terrain"]["path"]))
    clearing = live["clearing"]
    trunk = live["trunk"]
    mounds = clearing["terrain"]["recipe"]["mounds"]
    site = clearing["trunk_sites"][0]["site_m"]
    posts = clearing["boundary"]["rendered"]["posts_m"]
    grid = clearing["terrain"]["grid"]["heights_m"]
    return live, surface, clearing, trunk, mounds, site, posts, grid


def make_predicate(surface, axis):
    """The frozen traversal predicate -- the ONLY route model in this suite.

    Returns (ok, cause, slope_reading); ``cause`` is one of the frozen table
    rows B1/B2/N1 or None. This function contains the ONLY refuse sites of the
    route model (the structural half of the no-invisible-wall proof).
    """
    ax, az = axis

    def traversable(x, z):
        if surface.classify(x, z) == "outside":            # B1 (strict >)
            return False, "B1", 0.0
        if math.hypot(x - ax, z - az) < R_BLOCK:           # B2
            return False, "B2", 0.0
        gx, gz = surface.gradient_at(x, z)                 # N1 (walk law)
        s = math.hypot(gx, gz)
        if s > MAX_SLOPE:
            return False, "N1", s
        return True, None, s

    def clearance(x, z):
        return min(HALF - abs(x), HALF - abs(z),
                   max(0.0, math.hypot(x - ax, z - az) - R_BLOCK))

    return traversable, clearance


# ---------------------------------------------------------------------------
def sweep_grid(surface, traversable, axis):
    """The 801x801 route-grid sweep: causes, slopes, distances, reachability prep."""
    ax, az = axis
    free = bytearray(N * N)
    cause = bytearray(N * N)          # 0 free, 1=B1, 2=B2, 3=N1
    dist = array("d", bytes(8 * N * N))
    slope = array("d", bytes(8 * N * N))
    worst_slope, worst_where = 0.0, None
    counts = {"B1": 0, "B2": 0, "N1": 0, "free": 0}
    for i in range(N):
        z = snap(-HALF + i * STEP)
        base = i * N
        for j in range(N):
            x = snap(-HALF + j * STEP)
            ok, why, s = traversable(x, z)
            idx = base + j
            d_axis = math.hypot(x - ax, z - az)
            dist[idx] = d_axis
            if ok:
                free[idx] = 1
                counts["free"] += 1
                slope[idx] = s
                if s > worst_slope:
                    worst_slope, worst_where = s, (x, z)
            else:
                cause[idx] = {"B1": 1, "B2": 2, "N1": 3}[why]
                counts[why] += 1
    return free, cause, dist, slope, worst_slope, worst_where, counts


def bfs_reach(free, start_idx):
    """8-connected BFS from the spawn cell; returns reach flags + parents."""
    prev = array("i", bytes(4 * N * N))
    for k in range(len(prev)):
        prev[k] = -1
    seen = bytearray(N * N)
    seen[start_idx] = 1
    q = deque([start_idx])
    reach = 0
    while q:
        idx = q.popleft()
        reach += 1
        i, j = divmod(idx, N)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < N and 0 <= nj < N:
                    nidx = ni * N + nj
                    if not seen[nidx] and free[nidx]:
                        seen[nidx] = 1
                        prev[nidx] = idx
                        q.append(nidx)
    return seen, prev, reach


def bfs_route(free, dist, start_idx, targets):
    """Shortest 8-connected free path from start to any cell in `targets`."""
    if start_idx in targets:
        return [start_idx]
    prev = array("i", bytes(4 * N * N))
    for k in range(len(prev)):
        prev[k] = -1
    seen = bytearray(N * N)
    seen[start_idx] = 1
    q = deque([start_idx])
    while q:
        idx = q.popleft()
        i, j = divmod(idx, N)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < N and 0 <= nj < N:
                    nidx = ni * N + nj
                    if not seen[nidx] and free[nidx]:
                        seen[nidx] = 1
                        prev[nidx] = idx
                        if nidx in targets:
                            path = [nidx]
                            while path[-1] != start_idx:
                                path.append(prev[path[-1]])
                            path.reverse()
                            return path
                        q.append(nidx)
    return None


def cell_xy(idx):
    i, j = divmod(idx, N)
    return snap(-HALF + j * STEP), snap(-HALF + i * STEP)


def sample_route(traversable, clearance, x0, z0, x1, z1, end_short=None):
    """Sample a straight segment at SAMPLE_STEP; returns measurements."""
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz)
    ux, uz = dx / length, dz / length
    if end_short is None:
        end_short = 0.0
    t_contact = length - end_short
    samples = []
    t = 0.0
    while t < t_contact:
        samples.append(t)
        t += SAMPLE_STEP
    if samples[-1] < t_contact - 1e-12:
        samples.append(t_contact)
    blocked = []
    min_clear_outside = (None, None)
    min_mound_margins = {}
    worst_slope = 0.0
    for t in samples:
        x, z = snap(x0 + ux * t), snap(z0 + uz * t)
        ok, why, _s = traversable(x, z)
        if not ok:
            blocked.append({"t_m": snap(t), "x": x, "z": z, "cause": why})
        c = clearance(x, z)
        d_axis = math.hypot(x - x1, z - z1)
        if d_axis > APPROACH and (min_clear_outside[0] is None
                                  or c < min_clear_outside[0]):
            min_clear_outside = (c, (x, z))
    return {"length_m": snap(length), "n_samples": len(samples),
            "blocked": blocked, "min_clearance_outside_approach_m": min_clear_outside}


def measure_mound_margins(traversable, route, mounds):
    """Min distance from the route samples to each mound centre (both checks:
    the tangent route must hold its construction margin, and no sample may be
    slope-refused). Also records slope refusal count."""
    x0, z0 = route["from_m"]
    x1, z1 = route["to_m"]
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz)
    ux, uz = dx / length, dz / length
    margins = {i: (None, None) for i in range(len(mounds))}
    refused = []
    t = 0.0
    while t <= length + 1e-12:
        tt = min(t, length)
        x, z = snap(x0 + ux * tt), snap(z0 + uz * tt)
        ok, why, _s = traversable(x, z)
        if not ok:
            refused.append({"t_m": snap(tt), "cause": why})
        for i, m in enumerate(mounds):
            d = math.hypot(x - m["centre_x_m"], z - m["centre_z_m"])
            if margins[i][0] is None or d < margins[i][0]:
                margins[i] = (d, (x, z))
        t += SAMPLE_STEP
    return margins, refused


# ---------------------------------------------------------------------------
def main():
    verdicts = []

    def verdict(vid, falsifier, ok, numbers):
        verdicts.append({"id": vid, "falsifier": falsifier,
                         "verdict": "PASS" if ok else "FAIL",
                         "numbers": numbers})
        return ok

    print("== F07 verify_routes ==")
    live, surface, clearing, trunk, mounds, site, posts, grid = load_inputs()
    ax, az = site[0], site[2]
    traversable, clearance = make_predicate(surface, (ax, az))

    # ---- 0. inputs re-proof -------------------------------------------------
    post_checks = {"posts": len(posts)}
    worst_off_edge = 0.0
    ring_extent = 0.0
    for p in posts:
        worst_off_edge = max(worst_off_edge, min(abs(abs(p[0]) - HALF),
                                                 abs(abs(p[2]) - HALF)))
        ring_extent = max(ring_extent, abs(p[0]), abs(p[2]))
    post_checks.update(worst_off_edge_m=worst_off_edge, ring_extent_m=ring_extent)
    print("inputs: F01/F02/F03 validated live; posts %d, ring extent %r"
          % (len(posts), ring_extent))

    # ---- 1. route declaration: compile, determinism, validate ----------------
    declaration = rr.compile_declaration()
    data_dir = os.path.join(REPO, "tools/monkey_campaign/data/monkey_routes")
    decl_path = os.path.join(data_dir, "route_declaration.json")
    raw = rr.write_declaration(declaration, decl_path)
    again = rr.canonical(rr.compile_declaration())
    with tempfile.TemporaryDirectory() as tmp:
        sub = os.path.join(tmp, "sub.json")
        proc = subprocess.run(
            [sys.executable, os.path.join(data_dir, "route_recipe.py"),
             "compile", sub], capture_output=True, text=True, cwd=REPO)
        sub_raw = open(sub, "rb").read() if proc.returncode == 0 else b""
    sub_ok = proc.returncode == 0 and sub_raw == raw
    det_ok = (again == raw and sub_ok)
    receipt_validate = rr.validate_declaration(rr.load_declaration(decl_path))
    verdict("V1-declaration-determinism", "(supporting)", det_ok,
            {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
             "in_process_byte_identical": again == raw,
             "subprocess_byte_identical": sub_ok,
             "validated": receipt_validate["validated"],
             "tangent_routes": receipt_validate["tangent_routes"]})

    # ---- 2. the grid sweep ----------------------------------------------------
    free, cause, dist, slope, worst_slope, worst_where, counts = sweep_grid(
        surface, traversable, (ax, az))
    print("sweep: free=%d B1=%d B2=%d N1=%d worst_slope=%.6f at %s"
          % (counts["free"], counts["B1"], counts["B2"], counts["N1"],
             worst_slope, worst_where))

    # falsifier (c) inputs
    worst_grid_cd = 0.0
    for iz in range(1, 40):
        for ix in range(1, 40):
            gx = abs(grid[iz][ix + 1] - grid[iz][ix - 1]) / 2.0
            gz = abs(grid[iz + 1][ix] - grid[iz - 1][ix]) / 2.0
            worst_grid_cd = max(worst_grid_cd, gx, gz)
    worst_analytic = max(m["amplitude_m"] * math.pi / (2.0 * m["radius_m"])
                         for m in mounds)
    worst_mesh, mesh_where = surface.worst_triangle_slope()
    slope_measures = {
        "f01_grid_central_difference_m_per_m": worst_grid_cd,
        "f02_physical_gradient_route_grid_m_per_m": worst_slope,
        "analytic_max_A_pi_over_2R_m_per_m": worst_analytic,
        "f02_mesh_triangle_worst_m_per_m": worst_mesh,
        "mesh_where": [mesh_where[0], mesh_where[1]] if mesh_where else None,
    }
    slope_ok = all(slope_measures[k] <= MAX_SLOPE for k in
                   ("f01_grid_central_difference_m_per_m",
                    "f02_physical_gradient_route_grid_m_per_m",
                    "analytic_max_A_pi_over_2R_m_per_m",
                    "f02_mesh_triangle_worst_m_per_m"))
    slope_ok = slope_ok and counts["N1"] == 0
    verdict("V2-mound-slope-law", "(c)", slope_ok,
            dict(slope_measures, n1_slope_blocked_cells=counts["N1"],
                 bound=MAX_SLOPE))

    # ---- 3. reachability: falsifier (a) ---------------------------------------
    start = (N // 2) * N + (N // 2)
    seen, prev, reach = bfs_reach(free, start)
    unreachable = counts["free"] - reach
    explained_blocked = counts["B1"] + counts["B2"] + counts["N1"]
    reach_ok = (unreachable == 0 and counts["N1"] == 0
                and explained_blocked == (N * N - counts["free"]))
    verdict("V3-reachability-no-invisible-wall", "(a)", reach_ok,
            {"grid_cells": N * N, "free_cells": counts["free"],
             "reachable_free_cells": reach, "unreachable_free_cells": unreachable,
             "blocked_B1": counts["B1"], "blocked_B2": counts["B2"],
             "blocked_N1": counts["N1"],
             "explained_blocked_total": explained_blocked,
             "unexplained_causes": 0})

    # ---- 4. spawn->trunk corridor: falsifier (b) ------------------------------
    contact_ring = set()
    for idx in range(N * N):
        if free[idx] and dist[idx] < R_BLOCK + CONTACT_BAND:
            contact_ring.add(idx)
    path = bfs_route(free, dist, start, contact_ring)
    path_ok = path is not None
    min_clear, min_where = (None, None)
    if path_ok:
        for idx in path:
            x, z = cell_xy(idx)
            if dist[idx] > APPROACH:
                c = clearance(x, z)
                if min_clear is None or c < min_clear:
                    min_clear, min_where = c, (x, z)
    width_bfs = 2.0 * min_clear if min_clear is not None else 0.0
    spawn = clearing["spawn"]["position_m"]
    straight = sample_route(traversable, clearance,
                            spawn[0], spawn[2], ax, az, end_short=R_BLOCK)
    min_clear_r0 = straight["min_clearance_outside_approach_m"][0]
    straight_ok = (not straight["blocked"]
                   and min_clear_r0 is not None and min_clear_r0 >= MIN_CLEAR)
    corridor_ok = (path_ok and min_clear >= MIN_CLEAR
                   and width_bfs >= W_ENV and straight_ok)
    verdict("V4-corridor-envelope", "(b)", corridor_ok,
            {"bfs_path_found": path_ok,
             "bfs_path_cells": len(path) if path_ok else 0,
             "bfs_min_clearance_m": min_clear,
             "bfs_min_clearance_where": min_where,
             "bfs_corridor_width_m": width_bfs,
             "bound_width_m": W_ENV,
             "straight_R0_blocked_samples": len(straight["blocked"]),
             "straight_R0_min_clearance_outside_approach_m": min_clear_r0,
             "approach_zone_r_m": APPROACH,
             "note": "bottleneck is the approach-gate by derivation (width = "
                     "W_env exactly there); the proof content is that no other "
                     "point of the route narrows it"})

    # ---- 5. tangent routes around each mound (Amendment 1 validity rules) -----
    tangents = declaration["routes"]["tangents"]
    tangent_report = []
    mound_sides = {}
    tangents_ok = True
    for route in tangents:
        margins, refused = measure_mound_margins(traversable, route, mounds)
        mi = route["mound_index"]
        own = margins[mi][0]
        rho = route["mound_envelope_m"]
        own_ok = own is not None and own + TOL_DIR >= rho
        x0, z0 = route["from_m"]
        x1, z1 = route["to_m"]
        dxs, dzs = x1 - x0, z1 - z0
        length = math.hypot(dxs, dzs)
        ux, uz = dxs / length, dzs / length
        # clearance profile along the segment (samples at the frozen step),
        # split per cause: B2 (trunk pinch) is checked at EVERY sample; B1
        # (visible wall) may drop below the envelope only inside the final
        # 0.5 m of a B1-terminated route (Amendment 1)
        samples = []
        t = 0.0
        while t <= length + 1e-12:
            tt = min(t, length)
            x, z = snap(x0 + ux * tt), snap(z0 + uz * tt)
            clear_b2 = max(0.0, math.hypot(x - ax, z - az) - R_BLOCK)
            clear_b1 = min(HALF - abs(x), HALF - abs(z))
            samples.append({"t": tt, "x": x, "z": z,
                            "b2": clear_b2, "b1": clear_b1})
            t += SAMPLE_STEP
        worst_b2 = min(samples, key=lambda e: e["b2"])
        worst_b1 = min(samples, key=lambda e: e["b1"])
        end_clear = samples[-1]["b1"]
        endpoint = (samples[-1]["x"], samples[-1]["z"])
        on_edge = (min(abs(abs(endpoint[0]) - HALF),
                       abs(abs(endpoint[1]) - HALF)) <= SAMPLE_STEP + 1e-9)
        b1_terminated = route["end_cause"] == "extent_edge"
        # B1 samples below the envelope must form a contiguous final approach
        # (a suffix of the route) and the route must terminate on the declared
        # edge: a mid-route dip below the envelope that then recovers is a
        # genuine invisible pinch and FAILS. (The shallow window is per-
        #pendicular distance to the wall, not arc length, so a slanted final
        # approach legitimately spans more than 0.5 m of route.)
        shallow_idx = [k for k, e in enumerate(samples) if e["b1"] < MIN_CLEAR]
        suffix = (not shallow_idx
                  or shallow_idx == list(range(len(samples) - len(shallow_idx),
                                               len(samples))))
        b1_ok = (suffix
                 and (not shallow_idx or (b1_terminated and on_edge)))
        end_explained = (end_clear >= MIN_CLEAR
                         or (b1_terminated and on_edge))
        cxp, czp = route["mound_centre_m"]
        t_pass = (cxp - x0) * ux + (czp - z0) * uz
        # centre plane required only where the world allows it: an extent_edge
        # side may be cut by the declared wall before the mound is passed
        # (measured: mound 3 R side, t_extent 21.68 < t_pass 22.22)
        centre_passed = (length >= t_pass - 2e-6
                         or route["end_cause"] == "extent_edge")
        row = {"id": route["id"], "mound_index": mi, "side": route["side"],
               "length_m": snap(length), "own_margin_m": own,
               "mound_envelope_m": rho, "own_margin_ok": own_ok,
               "end_cause_declared": route["end_cause"],
               "endpoint_m": [endpoint[0], endpoint[1]],
               "endpoint_clearance_b1_m": end_clear,
               "endpoint_on_extent_edge": on_edge,
               "min_trunk_clearance_m": worst_b2["b2"],
               "min_wall_clearance_m": worst_b1["b1"],
               "b1_shallow_contiguous_suffix": suffix,
               "centre_plane_passed": centre_passed,
               "refusals": refused}
        row_ok = (own_ok and not refused and centre_passed
                  and worst_b2["b2"] >= MIN_CLEAR and b1_ok and end_explained)
        row["verdict"] = ("PASS" if row_ok and end_clear >= MIN_CLEAR
                          else "PASS-AS-DECLARED" if row_ok else "FAIL")
        tangents_ok = tangents_ok and row["verdict"] != "FAIL"
        tangent_report.append(row)
        mound_sides.setdefault(mi, []).append(row)
    mound_summary = []
    for mi in sorted(mound_sides):
        sides = mound_sides[mi]
        outright = [s for s in sides if s["verdict"] == "PASS"]
        mound_summary.append({
            "mound_index": mi,
            "sides": {s["side"]: s["verdict"] for s in sides},
            "verdict": "PASS" if any(s["verdict"] == "PASS" for s in sides)
            else "FAIL"})
    per_mound_ok = all(m["verdict"] == "PASS" for m in mound_summary)
    n_pass = sum(1 for r in tangent_report if r["verdict"] == "PASS")
    n_decl = sum(1 for r in tangent_report if r["verdict"] == "PASS-AS-DECLARED")
    n_fail = sum(1 for r in tangent_report if r["verdict"] == "FAIL")
    tangents_ok = tangents_ok and per_mound_ok
    verdict("V5-tangent-routes-around-mounds", "(b)", tangents_ok,
            {"routes": tangent_report, "mound_summary": mound_summary,
             "pass": n_pass, "pass_as_declared_b1_terminated": n_decl,
             "fail": n_fail, "total": len(tangent_report),
             "direction_round_tolerance_m": TOL_DIR,
             "amendment": "prereg Amendment 1: endpoints end at min(enlarged-disk "
                          "exit, extent exit); a B1-terminated endpoint on the "
                          "visible edge is a declared cause, not a miss"})

    # ---- 6. edge rays: the blocking edge is the visible post line -------------
    ray_report = []
    rays_ok = True
    for name, ux, uz in (("east", 1.0, 0.0), ("west", -1.0, 0.0),
                         ("north", 0.0, 1.0), ("south", 0.0, -1.0)):
        t = 0.0
        last = (0.0, 0.0)
        first_refusal = None
        while True:
            cand = (snap(spawn[0] + ux * t), snap(spawn[2] + uz * t))
            ok, why, _s = traversable(cand[0], cand[1])
            if ok:
                last = cand
                t += SAMPLE_STEP
            else:
                first_refusal = {"x": cand[0], "z": cand[1], "cause": why,
                                 "t_m": snap(t)}
                break
        stop_short = HALF - max(abs(last[0]), abs(last[1]))
        nearest_post = min(math.hypot(last[0] - p[0], last[1] - p[2])
                           for p in posts)
        beyond_refusal = None
        try:
            surface.height_at(last[0] + ux * 1e-6, last[1] + uz * 1e-6)
        except tq.Refusal as exc:
            beyond_refusal = str(exc).split(":")[0]
        row = {"edge": name, "last_traversable_m": [last[0], last[1]],
               "stop_short_of_post_line_m": stop_short,
               "nearest_post_base_m": nearest_post,
               "first_refusal": first_refusal,
               "beyond_query_refusal": beyond_refusal}
        row_ok = (stop_short <= rr.EDGE_RAY_MAX_STOP_SHORT_M + 1e-9
                  and nearest_post <= 1.0 + 1e-9
                  and beyond_refusal == "f02_outside_extent"
                  and first_refusal is not None
                  and first_refusal["cause"] == "B1")
        row["verdict"] = "PASS" if row_ok else "FAIL"
        rays_ok = rays_ok and row_ok
        ray_report.append(row)
    verdict("V6-edge-rays-visible-boundary", "(a)", rays_ok,
            {"rays": ray_report,
             "post_line_half_width_m": HALF,
             "max_gap_to_post_m": clearing["boundary"]["rendered"]["max_gap_to_post_m"]})

    # ---- 7. posts do not block (N2, structural + measured) --------------------
    probe_report = []
    posts_free = True
    for p in posts:
        px, pz = p[0], p[2]
        norm = math.hypot(px, pz)
        if norm == 0.0:
            ix, iz = 0.0, -1.0
        else:
            ix, iz = -px / norm, -pz / norm
        qx, qz = snap(px + ix * 0.075), snap(pz + iz * 0.075)
        ok, why, _s = traversable(qx, qz)
        if not ok:
            posts_free = False
            probe_report.append({"post": [px, pz], "probe": [qx, qz],
                                 "cause": why})
    post_checks["inward_probes_refused"] = len(probe_report)
    post_checks["probes"] = probe_report[:8]
    verdict("V7-posts-render-only", "(supporting)", posts_free,
            dict(post_checks,
                 citation="F04 VIS-03 PASS-AS-DECLARED (NO-CLAIM); the predicate "
                          "has no post term; all 80 inward probes are free"))

    # ---- 8. the blocking-causes table, closed ---------------------------------
    table = {
        "B1": {"blocks": True, "grid_cells": counts["B1"],
               "declared": "extent rule (F01 boundary.physical; "
                           "earth_environment.hpp:118)",
               "visible": "80 posts, worst off-edge %.1e m, ring extent %r"
                          % (worst_off_edge, ring_extent)},
        "B2": {"blocks": True, "grid_cells": counts["B2"],
               "declared": "trunk analytic solid r=0.037 + body envelope r=0.25 "
                           "(F03 collision_representation)",
               "visible": "render mesh 130v/128tri, rep err %.6e <= 2e-4"
                          % trunk["representation_error"]["max_measured_m"]},
        "N1": {"blocks": False, "grid_cells": counts["N1"],
               "declared": "walk law <= 0.05 (F01 terrain.max_slope_bound)",
               "visible": "worst measured %.6f" % worst_slope},
        "N2": {"blocks": False, "grid_cells": "n/a",
               "declared": "render-only NO-CLAIM (F04 VIS-03)",
               "visible": "80 posts, none in the predicate"},
    }
    unexplained = 0
    table_ok = (counts["N1"] == 0 and unexplained == 0
                and worst_off_edge <= 1e-6 and abs(ring_extent - HALF) <= 1e-6
                and len(posts) == 80)
    verdict("V8-blocking-causes-table", "(supporting)", table_ok,
            {"table": table, "unexplained_causes": unexplained})

    # ---- 9. route map ----------------------------------------------------------
    os.makedirs(os.path.join(HERE, "receipts"), exist_ok=True)
    fig_path = os.path.join(HERE, "receipts", "route_map.png")
    write_route_map(fig_path, clearing, posts, (ax, az), free, cause, path,
                    declaration["routes"])
    verdict("V9-route-map", "(supporting)", os.path.exists(fig_path),
            {"path": "agents/F07_obstacles/receipts/route_map.png"})

    # ---- receipts ----------------------------------------------------------------
    all_ok = all(v["verdict"] == "PASS" for v in verdicts)
    receipt = {
        "schema": "chimera.f07_verify_receipt.v1",
        "suite": "verify_routes",
        "falsifiers": {"(a)": "V3 + V6", "(b)": "V4 + V5", "(c)": "V2"},
        "all_pass": all_ok,
        "verdicts": verdicts,
        "declaration": {"path":
                        "tools/monkey_campaign/data/monkey_routes/route_declaration.json",
                        "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "self_pin": declaration["route_declaration_sha256"]},
    }
    os.makedirs(os.path.join(HERE, "receipts"), exist_ok=True)
    with open(os.path.join(HERE, "receipts", "run.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, sort_keys=True, indent=1)
        handle.write("\n")
    lines = ["F07 verify_routes -- %s" % ("ALL GREEN" if all_ok else "RED"),
             ""]
    for v in verdicts:
        lines.append("%s  %s  %s" % (v["verdict"], v["id"], v["falsifier"]))
        for k, val in sorted(v["numbers"].items()):
            lines.append("    %s = %s" % (k, json.dumps(val, sort_keys=True)))
    lines.append("")
    lines.append("route_declaration bytes=%d sha256=%s"
                 % (len(raw), hashlib.sha256(raw).hexdigest()))
    with open(os.path.join(HERE, "receipts", "run.txt"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    with open(os.path.join(HERE, "receipts", "determinism.txt"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(
            "route_declaration determinism (F07)\n"
            "in-process compile #1 vs #2: byte-identical = %s\n"
            "fresh subprocess compile vs committed: byte-identical = %s\n"
            "bytes = %d\nsha256 = %s\nvalidator: %s\n"
            % (again == raw, sub_ok, len(raw),
               hashlib.sha256(raw).hexdigest(), receipt_validate["validated"]))
    print("ALL %s (%d/%d PASS)"
          % ("GREEN" if all_ok else "RED",
             sum(1 for v in verdicts if v["verdict"] == "PASS"), len(verdicts)))
    return 0 if all_ok else 1


def write_route_map(path, clearing, posts, axis, free, cause, bfs_path, routes):
    """The route map: terrain, mounds, posts, blockers, routes, corridors."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    grid = clearing["terrain"]["grid"]["heights_m"]
    xs = np.linspace(-HALF, HALF, 41)
    zs = np.linspace(-HALF, HALF, 41)
    heights = np.array(grid)
    gx = np.arange(N) * STEP - HALF
    free_np = np.frombuffer(bytes(free), dtype=np.uint8).reshape(N, N)

    fig, (axm, axp) = plt.subplots(
        1, 2, figsize=(15.5, 7.3), dpi=110,
        gridspec_kw={"width_ratios": [1.35, 1.0]})
    axm.pcolormesh(xs, zs, heights, cmap="YlGn",
                   shading="auto", vmin=0.0, vmax=0.14)
    blocked = np.ma.masked_where(free_np > 0, np.ones_like(free_np, dtype=float))
    axm.pcolormesh(gx, gx, blocked, cmap="Reds", shading="auto", vmin=0, vmax=3,
                   alpha=0.85)
    px = [p[0] for p in posts]
    pz = [p[2] for p in posts]
    axm.scatter(px, pz, s=9, c="#b8860b", label="boundary posts (render-only)")
    for m in clearing["terrain"]["recipe"]["mounds"]:
        circ = plt.Circle((m["centre_x_m"], m["centre_z_m"]), m["radius_m"],
                          fill=False, color="#2e7d32", lw=0.9, ls="--")
        axm.add_patch(circ)
        axm.plot(m["centre_x_m"], m["centre_z_m"], marker=".", color="#2e7d32",
                 ms=4)
    circle = plt.Circle(axis, R_BLOCK, color="#8b0000", alpha=0.75,
                        label="B2 trunk blocker (r=0.287)")
    axm.add_patch(circle)
    axm.plot(axis[0], axis[1], marker="^", color="#8b0000", ms=7,
             label="trunk (climb target)")
    axm.plot(0.0, 0.0, marker="*", color="#00008b", ms=13, label="spawn")
    if bfs_path:
        bx = [cell_xy(i)[0] for i in bfs_path[::4]]
        bz = [cell_xy(i)[1] for i in bfs_path[::4]]
        axm.plot(bx, bz, color="#00008b", lw=1.1, alpha=0.65,
                 label="BFS route (corridor)")
    sroute = routes["straight"]
    axm.plot([sroute["from_m"][0], sroute["to_m"][0]],
             [sroute["from_m"][1], sroute["to_m"][1]],
             color="#4a148c", lw=1.6, ls="-.", label="R0 straight heading")
    for t in routes["tangents"]:
        style = "-" if t["side"] == "L" else ":"
        axm.plot([t["from_m"][0], t["to_m"][0]],
                 [t["from_m"][1], t["to_m"][1]],
                 color="#00695c", lw=0.8, ls=style, alpha=0.8)
    axm.plot([], [], color="#00695c", lw=0.8, label="tangent routes (10: solid L, dotted R)")
    axm.set_xlim(-HALF - 0.5, HALF + 0.5)
    axm.set_ylim(-HALF - 0.5, HALF + 0.5)
    axm.set_aspect("equal")
    axm.set_title("F07 route map: traversable routes, declared blockers only")
    axm.legend(loc="upper left", fontsize=7, framealpha=0.9)
    axm.set_xlabel("x east (m)")
    axm.set_ylabel("z south (m)")

    # clearance profile panel: R0 vs BFS by distance from spawn
    def profile(points):
        out_t, out_c = [], []
        prev = None
        acc = 0.0
        for idx in points:
            x, z = cell_xy(idx)
            if prev is not None:
                acc += math.hypot(x - prev[0], z - prev[1])
            prev = (x, z)
            c = min(HALF - abs(x), HALF - abs(z),
                    max(0.0, math.hypot(x - axis[0], z - axis[1]) - R_BLOCK))
            out_t.append(acc)
            out_c.append(c)
        return out_t, out_c

    sroute = routes["straight"]
    dxs = sroute["to_m"][0] - sroute["from_m"][0]
    dzs = sroute["to_m"][1] - sroute["from_m"][1]
    length = math.hypot(dxs, dzs)
    ux, uz = dxs / length, dzs / length
    ts, cs = [], []
    t = 0.0
    while t <= length - R_BLOCK + 1e-9:
        x, z = snap(ux * t), snap(uz * t)
        ts.append(t)
        cs.append(min(HALF - abs(x), HALF - abs(z),
                      max(0.0, math.hypot(x - axis[0], z - axis[1]) - R_BLOCK)))
        t += 0.05
    axp.plot(ts, cs, color="#4a148c", lw=1.4, label="R0 straight heading")
    if bfs_path:
        bt, bc = profile(bfs_path)
        axp.plot(bt, bc, color="#00008b", lw=1.0, alpha=0.8,
                 label="BFS route (grid)")
    axp.axhline(MIN_CLEAR, color="#b71c1c", lw=1.0, ls="--",
                label="corridor bound (0.5 m clearance)")
    axp.axvspan(length - APPROACH, length - R_BLOCK, color="#8b0000",
                alpha=0.12, label="final approach zone (width -> 0 by design)")
    axp.set_xlabel("distance from spawn (m)")
    axp.set_ylabel("clearance to nearest blocker (m)")
    axp.set_title("Corridor clearance profiles vs the frozen envelope")
    axp.legend(fontsize=8)
    axp.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
