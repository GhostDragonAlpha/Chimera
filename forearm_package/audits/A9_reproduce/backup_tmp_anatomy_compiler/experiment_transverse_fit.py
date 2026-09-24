"""experiment_transverse_fit.py — ONE preregistered placement experiment (session 5).

The baseline (actual_monkey_fit.json, session-5 revision) is preserved untouched.
This module runs three preregistered steps ONCE and writes its own outputs:

  A. frame/unit/mirror verification of the exported packet coordinates;
  B. baseline containment under the FINAL loop authority (triangle-plane section
     loops at each site's exact axial position);
  C. a single joint-anchored TRANSVERSE fitting candidate per forearm side, with
     the measured axial length held fixed, compared against the baseline — and
     then it STOPS, pass or fail.

================================================================================
PREREGISTRATION (declared before fitting; copied verbatim into the output)
================================================================================
Adjustable parameters (SHARED per side — one parameter pair for ALL sites of a
side; no per-site snapping):
    db, dc : transverse translation of the side's muscle-site cluster along the
             envelope frame axes (bu, cu), applied as world' = world + db*bu + dc*cu.
             Joint anchors (elbow, wrist = fitted_origin and dist landmark) do NOT
             move; the axial component of every site does NOT change.

Fixed by construction:
    - axial length / axial scale: the pack-measured value, untouched;
    - segment geometry, joints, masses, physiology: untouched;
    - the OTHER side is fitted independently (mirror is NOT assumed).

Bounds (declared a priori):
    -8.0 mm <= db, dc <= +8.0 mm  (half the ~20 mm envelope half-width).

Objective (fitting data ONLY: the session-4 sampled bands, nominal hulls at
t = 0.35 / 0.50 / 0.65):
    J(db, dc) = sum_over_sites sum_over_fitting_sections
                    max(0, margin - clearance(site, section; db, dc))^2
                + 1e-2 * (db^2 + dc^2)          [units m^2; margin = 1 mm]
    clearance = signed distance to the section hull polygon (negative inside).

Clearance requirement (declared a priori):
    every site of the side inside EVERY fitting-section hull with d <= -margin.

Search (deterministic, no RNG): grid over the bound box at 1 mm; then coordinate
refinement at 0.1 mm; then 0.01 mm, each stage re-evaluating J at the running
best point's 3x3 neighbourhood, clipped to bounds.

Evaluation (NOT used for fitting):
    1. FINAL loop authority at each site's exact axial position (baseline AND
       candidate positions);
    2. hulls at ADDITIONAL sections t = 0.42 and 0.58 (sites within a section's
       documented axial band are judged; the rest are not established there);
    3. per-tendon path-length changes (pairs where both endpoints resolved);
    4. per-tendon analytic moment-arm changes (recomputed with the same code for
       baseline and candidate positions).

Success criteria (declared a priori; ALL must hold):
    (i)   the clearance requirement holds on the fitting sections;
    (ii)  loop authority: no site of the side is `outside` at its exact axial
          position (tight/ambiguous reported, and counted as NOT met if any);
    (iii) additional-section hulls: no site judged there is `outside`;
    (iv)  db, dc strictly interior to the declared bounds.

Interpretation limit: even a PASSING candidate is AUTHORED transverse geometry —
a placement correction under declared bounds — never recovered anatomy, never a
measurement of where tendons actually attach, never mechanical qualification.
================================================================================

Run:  python experiment_transverse_fit.py
  -> runs/experiment_transverse_candidate.json
  -> runs/figure_transverse_candidate.png   (baseline vs candidate on loops)
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np

from actual_target_fit import (
    POLICED_FLAG,
    _band_roll,
    _fitted_sites_bc,
    build_correspondence_envelope,
    chain_child,
    load_real,
    onb_from_points,
)
from attachment_candidates import build_attachment_candidates
from compiler import _analytic_arm, fit
from intake import global_site_positions
from mesh_target import MESH_UNIT_TO_M, MonkeyTarget
from target_envelope import (
    BAND_HALF_M,
    _dist_to_poly,
    measure_forearm_envelope,
    section_loop_containment,
)

RUNS = Path(r"E:\PythonChimera\.tmp\anatomy_compiler\runs")

# --- PREREGISTRATION (single source of truth for step C) ----------------------
MARGIN_M = 0.001
BOUND_M = 0.008
FITTING_T = (0.35, 0.50, 0.65)
EVAL_T = (0.42, 0.58)
LAMBDA_RIDGE = 1e-2
GRID_STAGES = ((0.001, 1), (0.0001, 1), (0.00001, 1))  # (step, neighbourhood radius)

PREREG = {
    "candidate": "joint-anchored transverse translation (db, dc) per forearm side; all sites of a side share the pair",
    "fixed": "axial length (pack-measured); segment geometry, joints, masses untouched; other side independent",
    "bounds_m": {"db": [-BOUND_M, BOUND_M], "dc": [-BOUND_M, BOUND_M]},
    "objective": (
        "sum over sites x fitting sections of max(0, margin - clearance)^2 "
        f"+ {LAMBDA_RIDGE} * (db^2 + dc^2); fitting sections t={FITTING_T} nominal hulls"
    ),
    "clearance_requirement": f"every site inside every fitting-section hull with d <= -{MARGIN_M} m",
    "search": "deterministic 3-stage grid: 1 mm box, then 0.1 mm, then 0.01 mm neighbourhood refinement",
    "evaluation": {
        "loop_authority": "triangle-plane loops at each site's exact axial position",
        "additional_sections": list(EVAL_T),
        "tendon_lengths": "sum over consecutive path pairs with both endpoints resolved (same rule both revisions)",
        "moment_arms": "compiler._analytic_arm recomputed identically for baseline and candidate positions",
    },
    "success_criteria": [
        "(i) clearance requirement holds on fitting sections",
        "(ii) loop authority: zero `outside` (and zero `tight`/`unresolved`) at exact axial",
        "(iii) additional-section hulls: zero `outside` among judged sites",
        "(iv) (db, dc) strictly interior to bounds",
    ],
    "interpretation_limit": (
        "a passing candidate is AUTHORED transverse geometry under declared bounds — "
        "not recovered anatomy, not measured attachment, not mechanical qualification"
    ),
}


def _side_frames(mt: MonkeyTarget, pk: tuple[str, str]):
    P = mt.joint_pos(pk[0])
    P_d = mt.joint_pos(pk[1])
    q = _band_roll(mt, pk[0], P, P_d - P)
    _, bu, cu = onb_from_points(P, P_d, q)
    a = (P_d - P) / np.linalg.norm(P_d - P)
    return P, P_d, a, bu, cu


def _loop_at(mt: MonkeyTarget, P, a, bu, cu, axial: float, owner: tuple[str, str]):
    """Identified loop polygon (b,c) at an axial position, or None if ambiguous."""
    from target_envelope import _chain_closed_loops, _plane_cut_segments

    owner_set = {mt.idx[n] for n in owner if n in mt.idx}
    o1, o2, o3 = mt.assign[mt.F[:, 0]], mt.assign[mt.F[:, 1]], mt.assign[mt.F[:, 2]]
    tri_owner = np.where(o1 == o2, o1, o3)
    segs = _plane_cut_segments(mt.V, mt.F, P, a, axial)
    loops, n_open, _ = _chain_closed_loops(segs)
    identified = []
    for pts, tris in loops:
        frac = sum(1 for t in tris if int(tri_owner[t]) in owner_set) / len(tris)
        if frac >= 0.5:
            rel = pts - P
            identified.append(np.column_stack([rel @ bu, rel @ cu]))
    if len(identified) != 1:
        return None, {"n_loops": len(loops), "n_identified": len(identified), "n_open": n_open}
    return identified[0], {"n_loops": len(loops), "n_identified": len(identified), "n_open": n_open}


# --- step A: frame / unit / mirror verification --------------------------------
def step_A(f, real, mt, corr, sw) -> dict:
    out: dict = {"reconstruction_max_err_m": None, "unit_separation": {}, "mirror": {}}
    cand = build_attachment_candidates(f, real, mt, corr, sw)
    worst = 0.0
    for body in ("radius", "radius_l"):
        l2w = cand["bodies"][body]["local_to_world"]
        R = np.asarray(l2w["R_source_local_to_target"])
        t = np.asarray(l2w["t_fitted_origin_m"])
        for rec in cand["bodies"][body]["candidates"]:
            if not rec["fitted"]["resolved"]:
                continue
            w = t + R @ np.asarray(rec["source_pos_local"])
            worst = max(worst, float(np.linalg.norm(w - np.asarray(rec["fitted"]["fitted_pos_global"]))))
    # 1e-6 m bound: the export rounds coordinates to 1e-9; a micron is still ~1000x
    # tighter than the 1 mm clearance margin, and any frame bug shows up at mm scale
    assert worst < 1e-6, f"exported transforms do not reconstruct the fit's worlds: {worst}"
    out["reconstruction_max_err_m"] = worst

    # unit separation: source coords == intake (SI), target coords == metres via mt
    src_by_name = {s.name: s for s in real.sites}
    assert all(
        np.array_equal(np.asarray(r["source_pos_local"]), np.asarray(src_by_name[r["site_id"]].pos_local))
        for body in ("radius", "radius_l") for r in cand["bodies"][body]["candidates"]
    )
    out["unit_separation"] = {
        "source_coords": "verbatim intake/XML SI values (asserted equal)",
        "target_mesh_factor": MESH_UNIT_TO_M,
        "target_coords": "metres (factor applied to TARGET mesh vertices only)",
    }

    # mirror: reflect right world points across the target sagittal plane and
    # compare with the corresponding left points (sanity bound 20 mm, declared)
    sx = float(np.mean([mt.joint_pos(j)[0] for j in ("spine_lower", "spine_mid", "spine_upper")]))
    right = {r["site_id"]: np.asarray(r["fitted"]["fitted_pos_global"])
             for r in cand["bodies"]["radius"]["candidates"]}
    left = {r["site_id"]: np.asarray(r["fitted"]["fitted_pos_global"])
            for r in cand["bodies"]["radius_l"]["candidates"]}
    errs = []
    for sid, w in right.items():
        twin = sid.replace("-P", "_l-P")
        if twin not in left:
            continue
        refl = np.array([2 * sx - w[0], w[1], w[2]])
        errs.append((float(np.linalg.norm(refl - left[twin])), sid))
    errs.sort(reverse=True)
    out["mirror"] = {
        "sagittal_plane_x_m": sx,
        "n_pairs": len(errs),
        "max_pair_error_m": round(errs[0][0], 6),
        "mean_pair_error_m": round(float(np.mean([e for e, _ in errs])), 6),
        "worst_pairs": [(s, round(e, 6)) for e, s in errs[:3]],
        "sanity_bound_m": 0.02,
    }
    assert errs[0][0] < 0.02, f"mirror sanity violated: {errs[0]}"
    return out


def main() -> int:
    real = load_real()
    mt = MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = build_correspondence_envelope(real, mt, sw)
    prov = {"source_identity": {"raw_sha256": "x", "canonical": {"source_sha256_canonical": "y"}}}
    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG, provenance=prov)

    report: dict = {"preregistration": PREREG}

    # --- A: verification BEFORE any fitting -----------------------------------
    report["step_A_verification"] = step_A(f, real, mt, corr, sw)
    print("A: frame/unit/mirror verification OK:",
          json.dumps(report["step_A_verification"]["mirror"], indent=None))

    # --- shared per-side setup --------------------------------------------------
    seg_by_body = {s.source_body: s for s in f.segments}
    side_data: dict[str, dict] = {}
    for body, pk in (("radius", ("elbow_R", "wrist_R")), ("radius_l", ("elbow_L", "wrist_L"))):
        P, P_d, a, bu, cu = _side_frames(mt, pk)
        env = measure_forearm_envelope(mt, P, P_d, bu, cu)
        sites_bc = _fitted_sites_bc(f, real, mt, body, pk, seg_by_body.get(body))
        hulls = {s["t"]: np.asarray(s["hull_bc"]) for s in env["sections"]}
        side_data[body] = {
            "pk": pk, "P": P, "P_d": P_d, "a": a, "bu": bu, "cu": cu,
            "env": env, "sites": sites_bc, "hulls": hulls,
        }

    # --- B: baseline under the FINAL loop authority ------------------------------
    step_b: dict[str, dict] = {}
    for body, sd in side_data.items():
        res = section_loop_containment(mt, sd["P"], sd["a"], sd["bu"], sd["cu"], sd["sites"],
                                       margin_m=MARGIN_M, owner_joint_names=sd["pk"])
        step_b[body] = {k: res[k] for k in (
            "ok", "n_inside", "n_inside_insufficient_clearance", "n_outside", "n_unresolved",
            "outside", "inside_insufficient_clearance", "unresolved", "per_site")}
        print(f"B[{body}]: loop authority baseline -> outside={res['n_outside']} "
              f"tight={res['n_inside_insufficient_clearance']} ambiguous={res['n_unresolved']}")
    report["step_B_baseline_loop_authority"] = step_b

    # --- C: the ONE candidate per side ------------------------------------------
    def _obj(sites, hulls, db: float, dc: float) -> float:
        """Exactly the preregistered objective: clearance = -signed_distance."""
        j = LAMBDA_RIDGE * (db * db + dc * dc)
        for s in sites:
            for poly in hulls.values():
                d = _dist_to_poly(s["b"] + db, s["c"] + dc, poly)
                clearance = -d
                j += max(0.0, MARGIN_M - clearance) ** 2
        return j

    def _optimize(sites, hulls):
        best = np.array([0.0, 0.0])
        bj = _obj(sites, hulls, float(best[0]), float(best[1]))
        # stage 0: coarse box grid at 1 mm
        g = np.arange(-BOUND_M, BOUND_M + 1e-12, 0.001)
        for db in g:
            for dc in g:
                j = _obj(sites, hulls, float(db), float(dc))
                if j < bj:
                    bj, best = j, np.array([float(db), float(dc)])
        # refinement stages: 3x3 neighbourhood at 0.1 mm then 0.01 mm
        for step, _rad in GRID_STAGES[1:]:
            for _ in range(64):
                improved = False
                for ddb, ddc in itertools.product((-step, 0.0, step), repeat=2):
                    p = np.clip(best + np.array([ddb, ddc]), -BOUND_M, BOUND_M)
                    j = _obj(sites, hulls, float(p[0]), float(p[1]))
                    if j < bj - 1e-18:
                        bj, best = j, p
                        improved = True
                if not improved:
                    break
        return float(best[0]), float(best[1]), float(bj)

    candidates: dict[str, dict] = {}
    for body, sd in side_data.items():
        fitting_hulls = sd["hulls"]  # fitting data = the session-4 sampled bands only
        db, dc, j = _optimize(sd["sites"], fitting_hulls)

        # candidate world positions (transverse shift only; axial untouched)
        bu, cu = sd["bu"], sd["cu"]
        moved = [{"name": s["name"], "axial": s["axial"], "b": s["b"] + db, "c": s["c"] + dc}
                 for s in sd["sites"]]
        disp = [float(np.hypot(m["b"] - s["b"], m["c"] - s["c"]))
                for m, s in zip(moved, sd["sites"])]

        # evaluation 1: loop authority at exact axial, candidate positions
        loop_c = section_loop_containment(mt, sd["P"], sd["a"], bu, cu, moved,
                                          margin_m=MARGIN_M, owner_joint_names=sd["pk"])
        # evaluation 2: ADDITIONAL sections (not used for fitting); the documented
        # band rule applies — only sites within +-BAND_HALF_M of a section's axial
        # are judged there, the rest are not established at that section
        L = float(np.linalg.norm(sd["P_d"] - sd["P"]))
        add_hulls = {}
        for t in EVAL_T:
            poly, diag = _loop_at(mt, sd["P"], sd["a"], bu, cu, t * L, sd["pk"])
            if poly is not None:
                add_hulls[t] = {"poly": poly, **diag}
        add_verdicts: dict[str, dict] = {}
        add_judged = 0
        for m in moved:
            for t, rec in add_hulls.items():
                if abs(m["axial"] - t * L) <= BAND_HALF_M:
                    d = _dist_to_poly(m["b"], m["c"], rec["poly"])
                    add_verdicts.setdefault(m["name"], {})[str(t)] = round(float(d), 9)
                    add_judged += 1

        bounds_ok = (abs(db) < BOUND_M - 1e-12) and (abs(dc) < BOUND_M - 1e-12)
        fit_ok = all(
            _dist_to_poly(s["b"] + db, s["c"] + dc, poly) <= -MARGIN_M
            for s in sd["sites"] for poly in fitting_hulls.values()
        )
        loop_ok = loop_c["n_outside"] == 0 and loop_c["n_unresolved"] == 0 and loop_c["n_inside_insufficient_clearance"] == 0
        add_ok = all(d <= 0.0 for vd in add_verdicts.values() for d in vd.values())
        passed = bool(bounds_ok and fit_ok and loop_ok and add_ok)

        candidates[body] = {
            "db_m": round(db, 6), "dc_m": round(dc, 6), "objective_m2": round(float(j), 12),
            "bounds_ok": bounds_ok, "fitting_sections_ok": fit_ok,
            "loop_authority_ok": loop_ok, "additional_sections_ok": add_ok,
            "additional_sections_sites_judged": add_judged,
            "passed": passed,
            "loop_authority_candidate": {k: loop_c[k] for k in (
                "n_inside", "n_inside_insufficient_clearance", "n_outside", "n_unresolved",
                "outside", "inside_insufficient_clearance", "unresolved")},
            "additional_sections": {
                "n_identified_loops": {str(t): rec["n_identified"] for t, rec in add_hulls.items()},
                "per_site_signed_distance_m": add_verdicts,
            },
            "per_site_displacement_m": {
                s["name"]: round(d, 9) for s, d in zip(sd["sites"], disp)
            },
            "max_displacement_m": round(max(disp), 9),
        }
        print(f"C[{body}]: db={db*1000:+.2f}mm dc={dc*1000:+.2f}mm passed={passed} "
              f"(fitting={fit_ok} loop={loop_ok} additional={add_ok} bounds={bounds_ok})")

    report["step_C_candidate"] = candidates

    # --- tendon length + moment-arm deltas --------------------------------------
    site_fit = {s.name: s.fitted_pos_global for s in f.sites}  # ALL sites (NaN = unresolved)
    body_of_site = {s.name: s.segment for s in f.sites}
    # joint-body origins straight from the packet (covers unresolved bodies, whose
    # anchors are measured and identical in both revisions)
    fitted_origin = {j.body: np.asarray(j.origin, dtype=np.float64) for j in f.joints}
    fitted_origin.update({s.source_body: s.fitted_origin for s in f.segments})
    joint_axis = {j.name: j for j in f.joints}
    shifted = {}
    for body, cd in candidates.items():
        sd = side_data[body]
        bu, cu, db, dc = sd["bu"], sd["cu"], cd["db_m"], cd["dc_m"]
        for s in sd["sites"]:
            w = np.asarray(site_fit[s["name"]])
            shifted[s["name"]] = w + db * bu + dc * cu
    cand_fit = dict(site_fit)
    cand_fit.update(shifted)

    tendon_deltas = {}
    for t_src in real.tendons:  # source tendons carry ordered site_names
        t = next(ft for ft in f.tendons if ft.name == t_src.name)
        base_len = cand_len = 0.0
        pts_b, pts_c = [], []
        ok_chain = True
        for sn in t.sites:
            wb, wc = site_fit.get(sn), cand_fit.get(sn)
            if wb is None or (not np.all(np.isfinite(wb))):
                ok_chain = False
                continue
            if pts_b:
                base_len += float(np.linalg.norm(wb - pts_b[-1]))
                cand_len += float(np.linalg.norm(wc - pts_c[-1]))
            pts_b.append(wb)
            pts_c.append(wc)
        arm_d = []
        for j in f.joints:
            ab = _analytic_arm(t_src, j, site_fit, body_of_site, fitted_origin, joint_axis, real)
            ac = _analytic_arm(t_src, j, cand_fit, body_of_site, fitted_origin, joint_axis, real)
            if np.isfinite(ab) and np.isfinite(ac):
                arm_d.append(abs(ac - ab))
        tendon_deltas[t.name] = {
            "comparable": ok_chain,
            "path_length_delta_m": round(cand_len - base_len, 9) if ok_chain else None,
            "moment_arm_max_abs_delta_m": (round(float(max(arm_d)), 12) if arm_d else None),
        }
    report["tendon_deltas"] = tendon_deltas

    RUNS.mkdir(parents=True, exist_ok=True)
    out_json = RUNS / "experiment_transverse_candidate.json"
    out_json.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(f"experiment -> {out_json}")

    # --- figure: baseline vs candidate on identified loops -----------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    verdict_color = {"inside": "#1e8449", "inside_insufficient_clearance": "#d68910",
                     "outside": "#c0392b", "unresolved": "#7f8c8d", "not_measured": "#bdc3c7"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    for ax, (body, cd) in zip(axes, candidates.items()):
        sd = side_data[body]
        base_v = {n: r["verdict"] for n, r in step_b[body]["per_site"].items()}
        # identified loop at the worst outside site's axial (or mid) for context
        outs = [n for n, r in step_b[body]["per_site"].items() if r["verdict"] == "outside"]
        probe = step_b[body]["per_site"][outs[0]]["axial_m"] if outs else 0.5 * float(np.linalg.norm(sd["P_d"] - sd["P"]))
        poly, _ = _loop_at(mt, sd["P"], sd["a"], sd["bu"], sd["cu"], probe, sd["pk"])
        if poly is not None:
            closed = np.vstack([poly, poly[:1]])
            ax.plot(closed[:, 0] * 1000, closed[:, 1] * 1000, "-", color="#8f9aa3", lw=1.6,
                    label=f"skin loop @ {probe*1000:.0f} mm axial")
        for s, m in zip(sd["sites"], [dict(b=s["b"] + candidates[body]["db_m"],
                                           c=s["c"] + candidates[body]["dc_m"]) for s in sd["sites"]]):
            ax.scatter(s["b"] * 1000, s["c"] * 1000, s=55, marker="o",
                       color=verdict_color.get(base_v.get(s["name"], "not_measured")),
                       zorder=5, label="baseline (coloured by loop verdict)")
            ax.annotate("", xy=(m["b"] * 1000, m["c"] * 1000), xytext=(s["b"] * 1000, s["c"] * 1000),
                        arrowprops=dict(arrowstyle="->", color="#555555", lw=0.7))
            ax.scatter(m["b"] * 1000, m["c"] * 1000, s=30, marker="x", color="#111111", zorder=6)
        ax.scatter([], [], marker="x", color="#111111", label="candidate position")
        ax.set_title(f"{body}: db={candidates[body]['db_m']*1000:+.1f} mm dc={candidates[body]['dc_m']*1000:+.1f} mm "
                     f"passed={candidates[body]['passed']}")
        ax.set_xlabel("b [mm]"), ax.set_ylabel("c [mm]")
        ax.set_aspect("equal", adjustable="datalim")
        ax.legend(fontsize=7, loc="best")
    fig.suptitle("Session-5 placement experiment: baseline (coloured by placement status) -> candidate (x)", fontsize=11)
    fig.tight_layout()
    out_png = RUNS / "figure_transverse_candidate.png"
    fig.savefig(out_png, dpi=150)
    print(f"figure -> {out_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
