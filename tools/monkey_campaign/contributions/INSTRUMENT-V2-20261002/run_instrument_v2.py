# run_instrument_v2.py - INSTRUMENT-V2 chain stop 2, job 2 of 2 (FINAL).
# Executes EXACTLY the frozen law of the committed prereg
# (commit b564bdd268a78ee2f7067c331bc8abe012ee2f75; bytes sha256
# 897ca164ac5a63437c465783af2dd8f9c743d6c587d5423f4d3cec1b7190bdaf, embedded
# below and refused on any mismatch) plus the lane declaration
# (sha256 71e31cdd4122e20bfefdf343df28b0e01fc2a51e70cba11296924ca97ce991ea).
#
# ORDER (binding): (0) input gate; (1) the CONTROL BATTERY C1-C5 - the
# validity gate: ANY misclassification => INSTRUMENT_INVALID, all downstream
# verdicts withheld, the defect preserved; (2) only after a green battery,
# the RECHECK: R1 witness postures (q_c PRIMARY sealed, q = 0, F1/F2/F3
# fallbacks) over all 171 non-adjacent pairs with the classification triple
# and the 19-edge joint-region ledger, then R2, the 1,440 placements of the
# GP1-CC3 declared family at q_c(PRIMARY) with per-body mesh-vs-analytic-
# cylinder adjudication and the four placement classes (the anchor
# skin-envelope class recorded per placement and NEVER merged into the bone
# verdict). (3) P6 determinism: the pipeline runs twice per job, byte-
# identical twins (refusal on drift).
#
# Exit semantics: 0 = run completed with recorded verdicts (INSTRUMENT_INVALID
# and honest open existentials are DECLARED OUTCOMES, not run failures);
# 3 = gate refusal (preregistration_sha_mismatch / input_pin_mismatch /
# input_pin_missing / control_input_table_mismatch / level1_witness_mismatch /
# threshold_pin_mismatch) or determinism failure.

import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instrument_v2 as iv  # noqa: E402

CONTROL_TABLE_SHA256 = "d8aacc23b27e2caaf60304c0e9a4fe711ac51245c0ca3bf6d021d8f7b5164bf2"

_report = []

C4_GROSS_MIN_DEPTH = 1.0e-3


def emit(line=""):
    _report.append(line)
    print(line)


def find_prereg():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "PREREGISTRATION.md")
    if not os.path.isfile(p):
        p = os.path.join(os.getcwd(), "tools/monkey_campaign/contributions/"
                                      "INSTRUMENT-V2-20261002/PREREGISTRATION.md")
    if not os.path.isfile(p):
        iv.refuse("input_pin_missing", "committed prereg bytes not found")
    return p


def build_model():
    mut, bodies, joints_by_name, anchor_name, worst = iv.parse_hand_model(
        iv.A05_PATH, iv.A05_XML_PATH)
    stl_local = {}
    sphere_locals = {}
    for name in sorted(bodies):
        if name == anchor_name:
            continue
        geom = next(bb for bb in mut["bodies"] if bb["name"] == name)["geometry"]
        pin = [g["stl_sha256"] for g in geom if "stl_sha256" in g][0]
        path = None
        for k in iv.STL_NAMES:
            fp = iv.VENDOR_MESHES + k + ".stl"
            if iv.sha256_file(fp) == pin:
                path = fp
                break
        if path is None:
            iv.refuse("input_pin_missing", "stl for " + name)
        verts, tris = iv.parse_stl(path)
        stl_local[name] = (verts, tris)
        c, r = iv.bounding_sphere_scaled(verts)
        sphere_locals[name] = (c, r)
    bounds = mut["envelope_check"]["hand_vtp_bounds_m"]
    pts, tris, hist = iv.parse_vtp(iv.VTP_PATH)
    lo = [min(v[k] for v in pts) for k in range(3)]
    hi = [max(v[k] for v in pts) for k in range(3)]
    worst_v = max(max(abs(lo[k] - float(bounds[0][k])),
                      abs(hi[k] - float(bounds[1][k]))) for k in range(3))
    if worst_v > 1e-9:
        iv.refuse("input_pin_mismatch", "scaled VTP AABB worst %r" % worst_v)
    ac, ar = iv.anchor_bounds_sphere(bounds)
    sphere_locals[anchor_name] = (ac, ar)
    return (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
            (pts, tris), bounds)


def frames_at(model, q_map):
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    positions, rotations, joint_records = iv.fk_frames(bodies, anchor_name,
                                                       q_map)
    frames = iv.build_hand_frames(bodies, stl_local, positions, rotations,
                                  sphere_locals, anchor_name, vtp_local)
    return frames, positions, rotations, joint_records


def zero_q(joints_by_name):
    return {jn: 0.0 for jn in joints_by_name}


# ---------------------------------------------------------------------------
# the control battery
# ---------------------------------------------------------------------------

def run_control_battery(model, table):
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    o, u = (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    results = dict(schema="chimera.instrument_v2.control_battery.v1",
                   controls={}, ok=True, failures=[])

    def gate(name, cond, detail):
        if not cond:
            results["ok"] = False
            results["failures"].append(dict(control=name, detail=detail))
        return cond

    c1t = table["c1"]
    frames1, _, _, _ = frames_at(model, zero_q(joints_by_name))
    moved1 = {n: iv.translate_frame(f, tuple(c1t["translation"]))
              for n, f in frames1.items()}
    per = {}
    zero_flags = True
    all_clear = True
    for name in sorted(moved1):
        res = iv.adjudicate_body_vs_cylinder(moved1[name], o, u, iv.TAU)
        per[name] = dict(flag=res["level1"]["flag"], cls=res["class"],
                         d=res["d"])
        if res["level1"]["flag"]:
            zero_flags = False
        if res["class"] != "CLEAR":
            all_clear = False
    results["controls"]["C1"] = dict(expected="zero flags, all CLEAR",
                                     zero_flags=zero_flags,
                                     all_clear=all_clear, per_body=per)
    gate("C1", zero_flags and all_clear,
         "C1 separated-scene misclassified (zero_flags=%s all_clear=%s)"
         % (zero_flags, all_clear))

    c23 = table["c2_c3"]
    base = moved1[c23["target_body"]]
    radial = tuple(c23["radial"])
    frame_c2 = iv.translate_frame(
        base, tuple(-c23["t_touch"] * radial[k] for k in range(3)))
    res2 = iv.adjudicate_body_vs_cylinder(frame_c2, o, u, iv.TAU)
    results["controls"]["C2"] = dict(expected="TOUCHING",
                                     cls=res2["class"], d=res2["d"],
                                     depth=res2["depth"])
    gate("C2", res2["class"] == "TOUCHING",
         "C2 touching-scene classified %s (d=%r)" % (res2["class"], res2["d"]))
    frame_c3 = iv.translate_frame(frame_c2, tuple(c23["gross_translation"]))
    res3 = iv.adjudicate_body_vs_cylinder(frame_c3, o, u, iv.TAU)
    results["controls"]["C3"] = dict(expected="GENUINE_PENETRATION ~5mm",
                                     cls=res3["class"], depth=res3["depth"])
    gate("C3", res3["class"] == "GENUINE_PENETRATION"
         and res3["depth"] is not None and res3["depth"] >= 4.0e-3,
         "C3 gross-intrusion scene classified %s depth=%r"
         % (res3["class"], res3["depth"]))

    c5t = table["c5"]
    if c5t["kind"] == "FOLD_Q":
        qf5 = zero_q(joints_by_name)
        qf5[c5t["joint"]] = c5t["q"]
        frames5, _, _, _ = frames_at(model, qf5)
        scene_note5 = ("kinematic fold near-touch of %s at q=%r"
                       % (c5t["joint"], c5t["q"]))
    else:
        frames5, _, _, _ = frames_at(model, zero_q(joints_by_name))
        frames5 = dict(frames5)
        frames5[c5t["pair"][1]] = iv.translate_frame(
            frames5[c5t["pair"][1]], tuple(c5t["translation"]))
        scene_note5 = ("rigid near-touch translation of %s (d_final=%r m)"
                       % (c5t["pair"][1], c5t["d_final"]))
    row5 = iv.adjudicate_pair(frames5, bodies, anchor_name,
                              c5t["pair"][0], c5t["pair"][1], iv.TAU)
    results["controls"]["C5"] = dict(expected="TOUCHING (declared contact "
                                     "tolerance)",
                                     cls=row5["class"], d=row5["d"],
                                     scene=scene_note5,
                                     features=row5.get("features"))
    gate("C5", row5["class"] == "TOUCHING",
         "C5 near-touch scene classified %s" % row5["class"])
    c45 = table["c4_c5"]
    parent, child = c45["pair"][0], c45["pair"][1]
    if c45["mode"] == "KINEMATIC_FOLD":
        qf4 = zero_q(joints_by_name)
        qf4[c45["joint"]] = c45["q"]
        frames4, _, _, _ = frames_at(model, qf4)
        scene_note4 = ("kinematic fold of %s at the gross q=%r"
                       % (c45["joint"], c45["q"]))
    else:
        frames4, _, _, _ = frames_at(model, zero_q(joints_by_name))
        frames4 = dict(frames4)
        frames4[child] = iv.translate_frame(
            frames4[child], tuple(c45["direction"][k] * c45["t_gross"]
                                  for k in range(3)))
        scene_note4 = ("rigid telescoping translation of %s by t_gross=%r m "
                       "along the frozen direction"
                       % (child, c45["t_gross"]))
    row4 = iv.adjudicate_pair(frames4, bodies, anchor_name, parent, child,
                              iv.TAU)
    results["controls"]["C4"] = dict(
        expected="GENUINE_PENETRATION (active, outside the joint region)",
        cls=row4["class"], d=row4["d"], depth=row4["depth"],
        features=row4.get("features"),
        construction_mode=c45["mode"], scene=scene_note4)
    gate("C4", row4["class"] == "GENUINE_PENETRATION",
         "C4 gross-overlap scene classified %s (depth=%r)"
         % (row4["class"], row4["depth"]))
    results["control_input_table_sha256"] = CONTROL_TABLE_SHA256
    return results


# ---------------------------------------------------------------------------
# R1: the witness postures (parallel: per-config worker frames cache; the
# Captain's order 2026-10-02 mandates the 4-worker runner budget; results are
# recombined by canonical index so the output is byte-identical to the serial
# traversal regardless of completion order)
# ---------------------------------------------------------------------------

WITNESS_CONFIGS = ["q_c_PRIMARY", "q_zero", "F1", "F2", "F3"]

_MP_STATE = {}
_HB = {"done": 0, "total": 0, "t0": None, "label": ""}


def _hb_start(label, total):
    import time as _time
    _HB.update(done=0, total=total, t0=_time.time(), label=label)


def _hb_tick():
    import time as _time
    _HB["done"] += 1
    n = _HB["done"]
    if n % 10 == 0 or n == _HB["total"]:
        el = _time.time() - _HB["t0"]
        rate = (n / el * 60.0) if el > 0 else 0.0
        print("[hb] %s: %d/%d cells, %.1f cells/min, %.1f s elapsed"
              % (_HB["label"], n, _HB["total"], rate, el), flush=True)


def _mp_init_r1(model):
    _verify_worker_inputs()
    _MP_STATE["model"] = model
    _MP_STATE["frames"] = {}


def _verify_worker_inputs():
    """Stable-inputs law (Captain order 2026-10-02, point 4): every worker
    re-verifies the pinned mesh bytes it will load, and refuses on drift."""
    with open(iv.A05_PATH) as fh:
        mut = json.load(fh)
    on_disk = {k: iv.sha256_file(iv.VENDOR_MESHES + k + ".stl")
               for k in iv.STL_NAMES}
    for b in mut["bodies"]:
        name = b["name"]
        pin = [g["stl_sha256"] for g in b.get("geometry", [])
               if "stl_sha256" in g][0]
        hits = [k for k, h in on_disk.items() if h == pin]
        if len(hits) != 1:
            iv.refuse("input_pin_mismatch", "worker stl pin drift for " + name)
    vh = iv.sha256_file(iv.VTP_PATH)
    if vh != iv.GP1_PINS_ABS[iv.VTP_PATH]:
        iv.refuse("input_pin_mismatch", "worker vtp drift")


def _mp_init_r2(model, q_c):
    """Worker initializer for the placement sweep: build the q_c frames once
    per worker (the hand never moves across the family)."""
    _verify_worker_inputs()
    _MP_STATE["model"] = model
    frames, _, _, _ = frames_at(model, q_c)
    _MP_STATE["r2_frames"] = frames
    _MP_STATE["bone_names"] = [n for n in sorted(model[0]) if n != model[2]]


def _r1_adjudicate_pair_task(cname, na, nb, adjacent, tau):
    """Worker task: one flagged pair at one witness configuration. The
    worker caches the configuration frames (build once per worker per
    config)."""
    model = _MP_STATE["model"]
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    cache = _MP_STATE["frames"]
    frames = cache.get(cname)
    if frames is None:
        frames, _, _, _ = frames_at(model, config_q(joints_by_name, cname))
        cache[cname] = frames
    row = iv.adjudicate_pair(frames, bodies, anchor_name, na, nb, tau)
    row["a"] = na
    row["b"] = nb
    row["adjacent"] = bool(adjacent)
    row["config"] = cname
    return row


def config_q(joints_by_name, name):
    q = zero_q(joints_by_name)
    if name == "q_c_PRIMARY":
        q.update(iv.Q_C_PRIMARY)
    elif name == "F1":
        q.update(iv.Q_C_FALLBACKS["F1"])
    elif name == "F2":
        q.update(iv.Q_C_FALLBACKS["F2"])
    elif name == "F3":
        q.update(iv.Q_C_FALLBACKS["F3"])
    return q


def _r1_config_serial_part(model, cname):
    """Parent-side cheap parts: frames, Level-1 rows, ledger geometry, and
    the lists of flagged pairs for the parallel stage."""
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    q = config_q(joints_by_name, cname)
    frames, positions, rotations, joint_records = frames_at(model, q)
    rows = iv.level1_pair_rows(frames, bodies, anchor_name)
    ledger_edges = []
    flagged = []
    for r in rows:
        na, nb = r["a"], r["b"]
        child = nb if bodies[nb]["parent"] == na else (
            na if bodies[na]["parent"] == nb else None)
        if r["adjacent"]:
            jc = frames[child].pos
            hinges = [jn for (jn, ax, rg) in bodies[child]["joints"]] or \
                ["carpal_chain_folded_into_anchor"]
            ledger_edges.append(dict(
                pair=[na, nb], child=child, hinges=hinges,
                joint_center=list(jc), r_joint=iv.R_JOINT,
                level1_flag=r["proxy_overlap"]))
        if r["proxy_overlap"]:
            flagged.append((na, nb, bool(r["adjacent"])))
    return dict(q=q, frames=frames, rows=rows, ledger_edges=ledger_edges,
                flagged=flagged)


def run_r1(model, pool_factory=None):
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    parts = {}
    tasks = []
    for cname in WITNESS_CONFIGS:
        parts[cname] = _r1_config_serial_part(model, cname)
        for (na, nb, adj) in parts[cname]["flagged"]:
            tasks.append((cname, na, nb, adj))
    results_by_key = {}
    _hb_start("R1.flagged_pairs", len(tasks))
    if pool_factory is not None and tasks:
        with pool_factory() as pool:
            for (cname, na, nb, adj), row in zip(
                    tasks, pool.map(_r1_task_wrapper, tasks)):
                results_by_key[(cname, na, nb)] = row
                _hb_tick()
    else:
        for t in tasks:
            row = _r1_adjudicate_pair_task(t[0], t[1], t[2], t[3], iv.TAU)
            results_by_key[(t[0], t[1], t[2])] = row
            _hb_tick()
    out = {}
    import time as _time
    t0 = _time.time()
    for cname in WITNESS_CONFIGS:
        p = parts[cname]
        n_flag = 0
        pair_rows = []
        cls_counts = {}
        ledger = dict(edges=p["ledger_edges"])
        for r in p["rows"]:
            na, nb = r["a"], r["b"]
            if r["adjacent"]:
                if not r["proxy_overlap"]:
                    r2 = dict(a=na, b=nb, adjacent=True, level1_flag=False,
                              note="not flagged at Level 1; ledger dormant")
                else:
                    r2 = results_by_key[(cname, na, nb)]
            else:
                if not r["proxy_overlap"]:
                    r2 = dict(a=na, b=nb, adjacent=False, level1_flag=False,
                              cleared_at_screening=True)
                else:
                    n_flag += 1
                    r2 = results_by_key[(cname, na, nb)]
            cls = r2.get("class", "LEVEL1_CLEAR")
            cls_counts[cls] = cls_counts.get(cls, 0) + 1
            r2 = dict(r2)
            r2["level1"] = dict(distance=r["distance"],
                                radius_sum=r["radius_sum"],
                                clearance=r["clearance"],
                                flagged=r["proxy_overlap"])
            pair_rows.append(r2)
        out[cname] = dict(q={jn: p["q"][jn] for jn in sorted(p["q"])},
                          n_nonadjacent_flagged=n_flag,
                          class_counts=cls_counts,
                          pairs=pair_rows, ledger=ledger)
        emit("R1 %s: %d non-adjacent flagged; classes %s"
             % (cname, n_flag, json.dumps(cls_counts, sort_keys=True)))
    r1_in = len(tasks)
    r1_out = len(results_by_key)
    r1_unique = (r1_in == r1_out) and \
        (len(set((t[0], t[1], t[2]) for t in tasks)) == r1_in)
    if not r1_unique:
        iv.refuse("coverage_check_failed",
                  "R1 cells in=%d out=%d unique=%s"
                  % (r1_in, r1_out, r1_unique))
    elapsed = _time.time() - t0
    out["coverage"] = dict(r1_cells_in=r1_in, r1_cells_out=r1_out,
                           r1_cells_unique=r1_unique,
                           r1_elapsed_s=elapsed,
                           r1_cells_per_min=(r1_out / elapsed * 60.0)
                           if elapsed > 0 else None,
                           pool_used=bool(pool_factory is not None and
                                          tasks))
    return out


def robustness_columns(model, r1):
    """Recorded, never decisive: tau and r_joint variants re-derived from the
    recorded exact quantities of the q_c(PRIMARY) configuration."""
    (bodies, joints_by_name, anchor_name, _, _, _, _) = model
    q = config_q(joints_by_name, "q_c_PRIMARY")
    frames, _, _, _ = frames_at(model, q)
    cols = dict(tau={}, r_joint={})
    rows = r1["q_c_PRIMARY"]["pairs"]
    for tv in iv.TAU_VARIANTS:
        counts = {}
        for row in rows:
            cls = row.get("class")
            if cls is None:
                continue
            if cls == "GENUINE_PENETRATION":
                newc = "GENUINE_PENETRATION"
            elif cls == "UNRESOLVED_GEOMETRY":
                newc = "UNRESOLVED_GEOMETRY"
            elif cls == "JOINT_REGION_EXEMPT":
                newc = "JOINT_REGION_EXEMPT"
            elif cls == "TOUCHING":
                d = row.get("d", 0.0)
                newc = "GENUINE_PENETRATION" if (d is not None and d < -tv) \
                    else "TOUCHING"
            elif cls == "PROXY_FALSE_POSITIVE":
                d = row.get("d")
                newc = "TOUCHING" if (d is not None and d <= tv) \
                    else "PROXY_FALSE_POSITIVE"
            else:
                newc = cls
            counts[newc] = counts.get(newc, 0) + 1
        cols["tau"]["%r" % tv] = counts
    for rv in iv.R_JOINT_VARIANTS:
        counts = {}
        for row in rows:
            cls = row.get("class")
            if cls is None:
                continue
            if cls == "JOINT_REGION_EXEMPT":
                fd = row["features"]["max_feature_dist_to_joint_center"]
                newc = "JOINT_REGION_EXEMPT" if (fd is not None
                                                 and fd <= rv) \
                    else "TOUCHING"
            else:
                newc = cls
            counts[newc] = counts.get(newc, 0) + 1
        cols["r_joint"]["%r" % rv] = counts
    return cols


# ---------------------------------------------------------------------------
# R2: the 1,440 placements at q_c(PRIMARY)
# ---------------------------------------------------------------------------

CLASS_CODE = {"CLEAR": 0, "TOUCHING": 1, "GENUINE_PENETRATION": 2,
              "LEVEL1_CLEAR": 0}
PLACE_CODE = {"PENETRATION_FREE": 0, "CONTACT_ONLY": 1,
              "GENUINE_PENETRATION": 2, "UNRESOLVED_GEOMETRY": 3}
PLACE_NAME = {v: k for k, v in PLACE_CODE.items()}


def _r1_task_wrapper(t):
    return _r1_adjudicate_pair_task(t[0], t[1], t[2], t[3], iv.TAU)


def make_pool_r1(model):
    import concurrent.futures as cf
    return cf.ProcessPoolExecutor(max_workers=4, initializer=_mp_init_r1,
                                  initargs=(model,))


def make_pool_r2(model, q_c):
    import concurrent.futures as cf
    return cf.ProcessPoolExecutor(max_workers=4, initializer=_mp_init_r2,
                                  initargs=(model, q_c))


def _boundary_cell(task):
    """Worker task for the tolerance-edge boundary cells: rebuilds the frozen
    control scene from the pinned table inside the worker and classifies it
    (same functions the battery uses; frozen constants only)."""
    model = _MP_STATE["model"]
    (bodies, joints_by_name, anchor_name, _, _, _, _) = model
    kind = task["kind"]
    if kind == "cylinder_body":
        frames, _, _, _ = frames_at(model, zero_q(joints_by_name))
        t = task
        moved = {n: iv.translate_frame(f, tuple(t["hand_translation"]))
                 for n, f in frames.items()}
        frame = moved[t["body"]]
        if t.get("extra_translation") is not None:
            frame = iv.translate_frame(frame,
                                       tuple(t["extra_translation"]))
        res = iv.adjudicate_body_vs_cylinder(
            frame, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), iv.TAU)
        return (task["label"], res["class"], res["d"], res["depth"])
    if kind == "pair":
        frames, _, _, _ = frames_at(model, zero_q(joints_by_name))
        frames = dict(frames)
        frames[task["mover"]] = iv.translate_frame(
            frames[task["mover"]], tuple(task["translation"]))
        row = iv.adjudicate_pair(frames, bodies, anchor_name,
                                 task["pair"][0], task["pair"][1], iv.TAU)
        return (task["label"], row["class"], row["d"], row["depth"])
    iv.refuse("selfcheck_unknown_boundary_kind", kind)


def parallel_selfcheck(model, witness, table):
    """The Captain's determinism law (2026-10-02 order, extended per the
    second order): the parallel battery must reproduce the serial battery
    EXACTLY on a control slice BEFORE the full run. Slice: all flagged pairs
    at q_c(PRIMARY), the first 50 placement cells, AND the tolerance-edge
    boundary scenes (C2 tangency d=0; C5 near-touch d=tau/2; C3 gross 5 mm
    as contrast). Canonical-JSON byte-compare; any mismatch refuses the run
    (determinism failure)."""
    q_c = config_q(model[1], "q_c_PRIMARY")
    # R1 slice
    part = _r1_config_serial_part(model, "q_c_PRIMARY")
    serial_rows = []
    _mp_init_r1(model)
    _hb_start("selfcheck.R1.serial", len(part["flagged"]))
    for (na, nb, adj) in part["flagged"]:
        serial_rows.append(_r1_adjudicate_pair_task("q_c_PRIMARY", na, nb,
                                                    adj, iv.TAU))
        _hb_tick()
    tasks = [("q_c_PRIMARY", na, nb, adj) for (na, nb, adj)
             in part["flagged"]]
    parallel_rows = []
    _hb_start("selfcheck.R1.parallel", len(tasks))
    with make_pool_r1(model) as pool:
        for row in pool.map(_r1_task_wrapper, tasks):
            parallel_rows.append(row)
            _hb_tick()
    s1 = json.dumps(serial_rows, sort_keys=True)
    p1 = json.dumps(parallel_rows, sort_keys=True)
    r1_match = (s1 == p1)
    # R2 slice (first 50 cells)
    a = tuple(witness["a"])
    b = tuple(witness["b"])
    placements = iv.placement_family(a, b)[:50]
    tasks2 = [(k, pl["theta_index"], pl["mirror"], pl["o"], pl["u"])
              for k, pl in enumerate(placements)]
    _mp_init_r2(model, q_c)
    serial_cells = []
    _hb_start("selfcheck.R2.serial", len(tasks2))
    for t in tasks2:
        serial_cells.append(_r2_placement_cell(t))
        _hb_tick()
    parallel_cells = []
    _hb_start("selfcheck.R2.parallel", len(tasks2))
    with make_pool_r2(model, q_c) as pool:
        for cell in pool.map(_r2_placement_cell, tasks2, chunksize=8):
            parallel_cells.append(cell)
            _hb_tick()
    s2 = json.dumps(serial_cells, sort_keys=True)
    p2 = json.dumps(parallel_cells, sort_keys=True)
    r2_match = (s2 == p2)
    # boundary cells (tolerance edges): C2 tangency, C5 near-touch, C3 gross
    c23 = table["c2_c3"]
    btask_c2 = dict(kind="cylinder_body", label="C2_tangency",
                    body=c23["target_body"],
                    hand_translation=table["c1"]["translation"],
                    extra_translation=[-c23["t_touch"] * c23["radial"][k]
                                       for k in range(3)])
    btask_c3 = dict(kind="cylinder_body", label="C3_gross_5mm",
                    body=c23["target_body"],
                    hand_translation=table["c1"]["translation"],
                    extra_translation=[
                        -c23["t_touch"] * c23["radial"][k]
                        + c23["gross_translation"][k] for k in range(3)])
    c5t = table["c5"]
    btask_c5 = dict(kind="pair", label="C5_near_touch_tau_half",
                    pair=c5t["pair"], mover=c5t["pair"][1],
                    translation=c5t["translation"])
    btasks = [btask_c2, btask_c3, btask_c5]
    _mp_init_r1(model)
    serial_b = [_boundary_cell(t) for t in btasks]
    with make_pool_r1(model) as pool:
        parallel_b = list(pool.map(_boundary_cell, btasks))
    s3 = json.dumps(serial_b, sort_keys=True)
    p3 = json.dumps(parallel_b, sort_keys=True)
    b_match = (s3 == p3)
    return dict(r1_match=r1_match, r2_match=r2_match, boundary_match=b_match,
                r1_cells=len(tasks), r2_cells=len(tasks2),
                boundary_cells=len(btasks),
                boundary_serial=serial_b,
                ok=bool(r1_match and r2_match and b_match))


def _r2_placement_cell(task):
    """Worker task: one placement of the GP1-CC3 declared family. Returns
    (idx, row, verdict_code, anchor_genuine_class)."""
    (idx, theta_index, mirror, o, u) = task
    frames = _MP_STATE["r2_frames"]
    anchor_name = "macaque_hand_anchor"
    bone_names = _MP_STATE["bone_names"]
    contact = set(iv.CONTACT_BODIES)
    placement_genuine = False
    any_contact = False
    body_cells = []
    for name in bone_names:
        res = iv.adjudicate_body_vs_cylinder(frames[name], o, u, iv.TAU)
        cls = res["class"]
        d = res["d"]
        dep = res["depth"]
        code = CLASS_CODE[cls]
        if cls == "GENUINE_PENETRATION":
            if name in contact:
                if dep > iv.PI_C:
                    placement_genuine = True
            else:
                placement_genuine = True
        elif cls == "TOUCHING":
            if name in contact:
                if d is not None and d < -iv.PI_C:
                    placement_genuine = True
                else:
                    any_contact = True
            else:
                any_contact = True
        body_cells.append([code,
                           d if d is not None else 0.0,
                           dep if dep is not None else 0.0,
                           1 if res["level1"]["flag"] else 0])
    ares = iv.adjudicate_body_vs_cylinder(frames[anchor_name], o, u, iv.TAU)
    if placement_genuine:
        verdict = "GENUINE_PENETRATION"
    elif any_contact:
        verdict = "CONTACT_ONLY"
    else:
        verdict = "PENETRATION_FREE"
    code = PLACE_CODE[verdict]
    depmax = max((c[2] for c in body_cells), default=0.0)
    row = [theta_index, mirror, code,
           ares["class"] == "GENUINE_PENETRATION",
           ares["d"] if ares["d"] is not None else 0.0,
           ares["depth"] if ares["depth"] is not None else 0.0,
           1 if ares["level1"]["flag"] else 0,
           depmax] + [c for cell in body_cells for c in cell]
    return (idx, row, code, ares["class"], ares["d"], ares["depth"])


def run_r2(model, witness, pool_factory=None):
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    a = tuple(witness["a"])
    b = tuple(witness["b"])
    placements = iv.placement_family(a, b)
    q = config_q(joints_by_name, "q_c_PRIMARY")
    bone_names = [n for n in sorted(bodies) if n != anchor_name]
    contact = set(iv.CONTACT_BODIES)
    tasks = [(k, pl["theta_index"], pl["mirror"], pl["o"], pl["u"])
             for k, pl in enumerate(placements)]
    cells = [None] * len(tasks)
    import time as _time
    t0 = _time.time()
    _hb_start("R2.placements", len(tasks))
    if pool_factory is not None:
        with pool_factory() as pool:
            for (idx, row, code, acls, ad, adepth) in pool.map(
                    _r2_placement_cell, tasks, chunksize=24):
                cells[idx] = (idx, row, code, acls, ad, adepth)
                _hb_tick()
    else:
        _mp_init_r2(model, q)
        for t in tasks:
            (idx, row, code, acls, ad, adepth) = _r2_placement_cell(t)
            cells[idx] = (idx, row, code, acls, ad, adepth)
            _hb_tick()
    elapsed = _time.time() - t0
    # coverage check (Captain order point 4): every expected cell exactly once
    idxs = [c[0] for c in cells]
    r2_unique = (None not in cells) and \
        (sorted(idxs) == list(range(len(tasks)))) and \
        (len(set(idxs)) == len(tasks))
    if not r2_unique:
        iv.refuse("coverage_check_failed",
                  "R2 cells in=%d out=%d unique=%s"
                  % (len(tasks), sum(1 for c in cells if c is not None),
                     r2_unique))
    # deterministic recombination: aggregates re-derived from the ordered rows
    rows = [c[1] for c in cells]
    counts = {}
    anchor_counts = {}
    clean_count = 0
    min_clear_margin = None
    min_clear_idx = None
    worst_depth = None
    worst_idx = None
    for c in cells:
        (idx, row, code, acls, ad, adepth) = c
        verdict = PLACE_NAME[code]
        counts[verdict] = counts.get(verdict, 0) + 1
        acls_name = acls
        anchor_counts[acls_name] = anchor_counts.get(acls_name, 0) + 1
        if code in (PLACE_CODE["CONTACT_ONLY"], PLACE_CODE["PENETRATION_FREE"]):
            clean_count += 1
            if code == PLACE_CODE["PENETRATION_FREE"]:
                for k, name in enumerate(bone_names):
                    d = row[8 + 4 * k + 1]
                    if min_clear_margin is None or d < min_clear_margin:
                        min_clear_margin = d
                        min_clear_idx = [row[0], row[1], name]
        depmax = row[7]
        if worst_depth is None or depmax > worst_depth:
            worst_depth = depmax
            worst_idx = [row[0], row[1]]
    # pi_c robustness (recorded, never decisive): reclassify the contact
    # segments from the recorded depths
    pi_cols = {}
    for pv in iv.PI_C_VARIANTS:
        ccounts = {}
        for row in rows:
            code = row[2]
            cells_r = row[8:]
            offend = False
            for k, name in enumerate(bone_names):
                c = cells_r[4 * k]
                dep = cells_r[4 * k + 2]
                if c == 2:
                    if name in contact:
                        if dep > pv:
                            offend = True
                    else:
                        offend = True
            key = "GENUINE" if offend else \
                ("clean" if code in (0, 1) else PLACE_NAME[code])
            ccounts[key] = ccounts.get(key, 0) + 1
        pi_cols["%r" % pv] = ccounts
    return dict(
        n_placements=len(rows),
        coverage=dict(r2_cells_in=len(tasks), r2_cells_out=len(cells),
                      r2_cells_unique=r2_unique, r2_elapsed_s=elapsed,
                      r2_cells_per_min=(len(cells) / elapsed * 60.0)
                      if elapsed > 0 else None,
                      pool_used=bool(pool_factory is not None)),
        verdict_counts=counts,
        anchor_envelope_counts=anchor_counts,
        clean_placements=clean_count,
        min_clear_margin=(None if min_clear_margin is None
                          else dict(margin=min_clear_margin, at=min_clear_idx)),
        worst_depth=(None if worst_depth is None
                     else dict(depth=worst_depth, at=worst_idx)),
        pi_c_robustness=pi_cols,
        bone_order=bone_names,
        rows=rows,
    )


# ---------------------------------------------------------------------------
# the pipeline (run twice per job for P6 determinism)
# ---------------------------------------------------------------------------

def pipeline():
    del _report[:]
    here = os.path.dirname(os.path.abspath(__file__))
    prereg = find_prereg()
    table_path = os.path.join(here, "control_input_table.json")
    if not os.path.isfile(table_path):
        table_path = os.path.join(
            os.getcwd(), "tools/monkey_campaign/contributions/"
                         "INSTRUMENT-V2-20261002/control_input_table.json")
    gate, mut, stl_files, bounds = iv.run_input_gate(
        prereg, table_path, CONTROL_TABLE_SHA256)
    emit("=" * 78)
    emit("GATE. prereg %s (%s) MATCH; declaration %s MATCH; %d inherited pins"
         " MATCH; 19/19 STL pins 1:1; GRASP_MECHANISMS prefix identity at %d"
         " bytes; scaled VTP AABB == hand_vtp_bounds_m (worst %r)."
         % (gate["preregistration_sha256"][:16], gate["prereg_commit"][:12],
            gate["declaration_sha256"][:16], len(gate["pins"]),
            gate["grasp_mechanisms_prefix_len"],
            gate["vtp_envelope"]["scaled_aabb_worst_delta"]))
    with open(table_path, "r", encoding="utf-8") as fh:
        table = json.load(fh)
    model = build_model()
    witness = iv.check_witness_identity(model[0], model[1], model[2])
    emit("WITNESS. sealed q_c(PRIMARY) FK reproduces the GP1 receipt tips and"
         " chord %r (refuse on drift)." % witness["chord"])

    frames_qc, _, _, _ = frames_at(model, config_q(model[1], "q_c_PRIMARY"))
    lev1 = iv.build_level1_expectation_check(frames_qc, model[0], model[2])
    emit("LEVEL-1 WITNESS CROSS-CHECK: %d non-adjacent tested, %d overlaps,"
         " all clearances match the sealed GP1 CC2 table (tol %r)."
         % (lev1["nonadjacent_tested"], lev1["nonadjacent_overlaps"],
            iv.LEVEL1_MATCH_TOL))

    emit("=" * 78)
    emit("CONTROL BATTERY (gates everything; declaration 4.1)")
    battery = run_control_battery(model, table)
    for cname in ("C1", "C2", "C3", "C4", "C5"):
        c = battery["controls"].get(cname, {})
        emit("  %s: expected %s -> %s" % (cname, c.get("expected"),
                                          c.get("cls", c.get("zero_flags"))))
    receipt = dict(
        schema="chimera.instrument_v2.receipt.v1",
        task="INSTRUMENT-V2-20261002 (corrected two-level collision/penetration"
             " instrument: mesh-level adjudication + control battery + GP1"
             " recheck)",
        implementation_lane="wk-instrument-v2 (resumed after power failure;"
                            " E:/ChimeraWork/monkey-coordination/instrument-v2/)",
        preregistration_sha256=iv.PREREG_SHA256,
        prereg_commit=iv.PREREG_COMMIT,
        prereg_branch="origin/review/INSTRUMENT-V2-20261002",
        declaration_sha256=iv.DECLARATION_SHA256,
        control_input_table_sha256=CONTROL_TABLE_SHA256,
        frozen_constants=dict(tau=iv.TAU, pi_c=iv.PI_C, r_joint=iv.R_JOINT,
                              tau_variants=list(iv.TAU_VARIANTS),
                              pi_c_variants=list(iv.PI_C_VARIANTS),
                              r_joint_variants=list(iv.R_JOINT_VARIANTS),
                              scale=iv.SCALE, anchor_r=iv.ANCHOR_R,
                              trunk_r=iv.TRUNK_R, trunk_h=iv.TRUNK_H,
                              n_theta=iv.N_THETA, n_mirror=iv.N_MIRROR),
        gp1_preservation=(
            "GP1 (merge c258ae1f..., PR #317) preserved byte-for-byte as the"
            " negative result under its ORIGINAL instrument; every comparison"
            " herein is an instrument difference, never a rewrite"),
        input_gate=gate,
        collision_inventory=dict(
            objects=20,
            named=("19 A05-pinned bone STLs (firstmc, proximal_thumb, "
                   "distal_thumb, secondmc, proxph2, midph2, distph2, "
                   "thirdmc, proxph3, midph3, distph3, fourthmc, proxph4, "
                   "midph4, distph4, fifthmc, proxph5, midph5, distph5) + "
                   "the anchor body macaque_hand_anchor whose only Level-2 "
                   "surface is the pinned hand.vtp envelope"),
            pairs_total=190,
            pairs_nonadjacent=171,
            excluded_pairs=19,
            excluded_note="the 19 CERTIFIED parent-child edges, each a "
                          "JOINT-REGION exemption (r_joint=5e-3 at the "
                          "certified child-frame origin), never a pair "
                          "disable; the TRUNK is NOT among the 20 objects: "
                          "it enters only as the exact analytic cylinder in "
                          "the controls and the placement sweep",
            factoring=dict(
                fixed_anatomical=("bone-bone and anchor-envelope pairs at "
                                  "the 5 witness configurations: "
                                  "placement-independent, run ONCE per "
                                  "configuration in R1 and NEVER repeated "
                                  "at placements"),
                placement_dependent=("body-vs-trunk-cylinder per body per "
                                     "placement (19 bones + the anchor "
                                     "envelope column recorded separately) "
                                     "in R2 only; no anatomical check is "
                                     "repeated at placements"))),
        parallel=dict(workers=4,
                      budget="the runner profile's 4-thread per-job allowance",
                      scheme="R1: per-config worker frames cache, per-flagged-"
                             "pair tasks; R2: the 1,440 placements in 24-"
                             "placement cells; recombination by canonical "
                             "index (config order, theta/mirror order); "
                             "byte-identical to the serial traversal by "
                             "construction and by the control slice"),
        witness_identity=witness,
        level1_witness_crosscheck=lev1,
        control_battery=battery,
    )
    if not battery["ok"]:
        receipt["verdict"] = "INSTRUMENT_INVALID"
        receipt["downstream"] = "WITHHELD (no candidate/placement result carries)"
        emit("VERDICT: INSTRUMENT_INVALID - control battery failures: %s"
             % json.dumps(battery["failures"]))
        return receipt
    emit("  BATTERY GREEN: all five controls classified correctly.")

    emit("=" * 78)
    emit("PARALLEL CONTROL SLICE (Captain order 2026-10-02: serial vs")
    emit("  parallel byte-compare on ~50 cells BEFORE the full recheck)")
    selfcheck = parallel_selfcheck(model, witness, table)
    emit("  selfcheck: %s" % json.dumps(selfcheck, sort_keys=True))
    if not selfcheck["ok"]:
        receipt["verdict"] = "DETERMINISM_FAILURE_PARALLEL_SLICE"
        receipt["parallel_selfcheck"] = selfcheck
        emit("  REFUSAL: the parallel slice did not reproduce the serial")
        emit("  slice byte-identically; no full recheck runs.")
        return receipt
    emit("  SLICE BYTE-IDENTICAL: parallel == serial on the control cells.")
    receipt["parallel_selfcheck"] = selfcheck

    emit("=" * 78)
    emit("RECHECK R1. witness postures (q_c PRIMARY sealed, q=0, F1/F2/F3)")
    r1 = run_r1(model, pool_factory=lambda: make_pool_r1(model))
    robust = robustness_columns(model, r1)
    emit("  robustness columns (recorded, never decisive): %s"
         % json.dumps(dict(tau=sorted(robust["tau"].keys()),
                           r_joint=sorted(robust["r_joint"].keys()))))

    emit("=" * 78)
    emit("RECHECK R2. the 1,440 placements of the GP1-CC3 declared family at"
         " q_c(PRIMARY)")
    r2 = run_r2(model, witness,
                pool_factory=lambda: make_pool_r2(model, config_q(
                    model[1], "q_c_PRIMARY")))
    emit("  placement verdicts: %s" % json.dumps(r2["verdict_counts"],
                                                 sort_keys=True))
    emit("  anchor envelope classes (recorded separately, never merged): %s"
         % json.dumps(r2["anchor_envelope_counts"], sort_keys=True))
    emit("  clean placements (PENETRATION_FREE or CONTACT_ONLY): %d of %d"
         % (r2["clean_placements"], r2["n_placements"]))
    if r2["min_clear_margin"]:
        emit("  best clean margin %r m at %s"
             % (r2["min_clear_margin"]["margin"],
                r2["min_clear_margin"]["at"]))

    # P2: the 10 mc-mc pairs at q=0 and q_c
    mcs = ["firstmc", "secondmc", "thirdmc", "fourthmc", "fifthmc"]
    def mc_rows(cfg):
        out = {}
        for row in r1[cfg]["pairs"]:
            if row["a"] in mcs and row["b"] in mcs:
                out[row["a"] + "+" + row["b"]] = row.get("class")
        return out
    p2 = dict(q_zero=mc_rows("q_zero"), q_c_PRIMARY=mc_rows("q_c_PRIMARY"))
    # P3: the anchor class at q_c
    p3 = {}
    for row in r1["q_c_PRIMARY"]["pairs"]:
        if (row["a"] == "macaque_hand_anchor" or
                row["b"] == "macaque_hand_anchor") and not row.get("adjacent"):
            other = row["b"] if row["a"] == "macaque_hand_anchor" else row["a"]
            p3[other] = row.get("class")
    # P4: thumb-opposition pairs at q_c
    thumb_bodies = ["firstmc", "proximal_thumb", "distal_thumb"]
    p4 = {}
    for row in r1["q_c_PRIMARY"]["pairs"]:
        ta = row["a"] in thumb_bodies
        tb = row["b"] in thumb_bodies
        if ta != tb and not row.get("adjacent"):
            key = row["a"] + "+" + row["b"]
            p4[key] = row.get("class")
    preds = dict(
        P1=dict(name="control_battery_gates", verdict="SUPPORTED"
                if battery["ok"] else "FALSIFIED", detail=battery["controls"]),
        P2=dict(name="metacarpal_mutual_class", observed=p2,
                prediction="shaft-region pairs PROXY_FALSE_POSITIVE; "
                           "CMC-base-region pairs TOUCHING or "
                           "GENUINE_PENETRATION (honest possibility declared)"),
        P3=dict(name="anchor_envelope_class", observed=p3,
                prediction="UNRESOLVED_GEOMETRY for the class; falsified if "
                           "the VTP proves fine-grained enough to adjudicate "
                           "(measured either way, never forced)"),
        P4=dict(name="witness_posture_remainder", observed=p4,
                prediction="TOUCHING or near-touch on the opposition axis; a "
                           "crossing would be a real GENUINE_PENETRATION "
                           "finding, recorded plainly"),
        P5=dict(name="the_1440_placements", observed=r2["verdict_counts"],
                existential=(">= 1 PENETRATION_FREE or CONTACT_ONLY placement"
                             " is THE measurement of this card; no predicted "
                             "direction"),
                clean_placements=r2["clean_placements"],
                anchor_separate=r2["anchor_envelope_counts"]),
        P6=dict(name="determinism", verdict="recorded in the determinism "
                "receipt (twins)"),
    )
    overall = "RECHECK_RECORDED"
    if r2["clean_placements"] == 0:
        overall = "RECHECK_RECORDED_ZERO_CLEAN_REAL_GEOMETRY_FINDING"
    receipt["verdict"] = overall
    receipt["downstream"] = "RECHECK_RECORDED (battery green)"
    receipt["r1"] = r1
    receipt["r1_robustness"] = robust
    receipt["r2"] = r2
    receipt["predictions"] = preds
    receipt["honest_limits"] = dict(
        source_fidelity_gap="hand bone surfaces are mutated HUMAN donor shapes"
                            " at macaque scale; UNQUANTIFIED",
        faceting="max triangle edge 1.2e-3..3.57e-3 m is the resolution "
                 "witness (mesh_input_table.json)",
        anchor_envelope="1920-point whole-hand skin envelope; an order "
                        "coarser than the bone STLs; anchor-bone pairs "
                        "UNRESOLVED unless the surfaces cross",
        pads_absent="cartilage/soft tissue and fingertip pads ABSENT (A2)",
        feasibility_only="any clean placement is feasibility evidence at the "
                         "represented geometry only; never a grasp claim, "
                         "never species-true anatomy",
    )
    return receipt


def write_outputs(outdir, names_values):
    for name, value in names_values:
        with open(os.path.join(outdir, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(value)


def main():
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    try:
        receipt1 = pipeline()
        text1 = "\n".join(_report) + "\n"
        receipt2 = pipeline()
        text2 = "\n".join(_report) + "\n"
    except iv.GateRefusal as exc:
        emit("")
        emit("REFUSAL RECORDED: %s" % exc.detail)
        emit("nothing is normalized; the run stops (exit 3)")
        write_outputs(outdir, [("instrument_v2_gate_receipt.json",
                                json.dumps(dict(
                                    schema="chimera.instrument_v2.gate.v1",
                                    ok=False, refusal=exc.detail),
                                    indent=1) + "\n")])
        raise SystemExit(3)
    # P6 determinism: the SCIENTIFIC content must be byte-identical. The
    # declared non-deterministic bookkeeping (measured wall-clock timings and
    # derived rates of the parallel execution) is stripped from BOTH receipts
    # before the comparison and listed here; nothing else is excluded.
    NONDETERMINISTIC_KEYS = {"r1_elapsed_s", "r1_cells_per_min",
                             "r2_elapsed_s", "r2_cells_per_min"}

    def strip_timing(obj):
        if isinstance(obj, dict):
            return {k: strip_timing(v) for k, v in obj.items()
                    if k not in NONDETERMINISTIC_KEYS}
        if isinstance(obj, list):
            return [strip_timing(v) for v in obj]
        return obj

    clean1 = strip_timing(receipt1)
    clean2 = strip_timing(receipt2)
    s1 = json.dumps(clean1, indent=1, sort_keys=True) + "\n"
    s2 = json.dumps(clean2, indent=1, sort_keys=True) + "\n"
    identical = (s1 == s2) and (text1 == text2)
    det = dict(
        schema="chimera.instrument_v2.determinism.v1",
        rerun_identical=identical,
        stripped_nondeterministic_keys=sorted(NONDETERMINISTIC_KEYS),
        receipt_sha256_run1=hashlib.sha256(s1.encode("utf-8")).hexdigest(),
        receipt_sha256_run2=hashlib.sha256(s2.encode("utf-8")).hexdigest(),
        report_sha256_run1=hashlib.sha256(text1.encode("utf-8")).hexdigest(),
        report_sha256_run2=hashlib.sha256(text2.encode("utf-8")).hexdigest(),
        note="P6: every pipeline repeat byte-identical (GP1 CC6 law)",
    )
    write_outputs(outdir, [
        ("instrument_v2_receipt.json", s1),
        ("instrument_v2_receipt_rerun2.json", s2),
        ("instrument_v2_report.txt", text1),
        ("instrument_v2_report_rerun2.txt", text2),
        ("determinism_receipt.json", json.dumps(det, indent=1) + "\n"),
        ("instrument_v2_gate_receipt.json", json.dumps(dict(
            schema="chimera.instrument_v2.gate.v1",
            ok=bool(receipt1["input_gate"]["ok"]),
            pins=len(receipt1["input_gate"]["pins"]),
            verdict=receipt1["verdict"]), indent=1) + "\n"),
    ])
    emit("=" * 78)
    emit("P6 DETERMINISM: rerun bit-identical = %s" % identical)
    emit("OVERALL VERDICT: %s" % receipt1["verdict"])
    if not identical:
        raise SystemExit(3)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
