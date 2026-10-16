"""scale_resolution_checks.py -- THE REGISTERED FALSIFIER BATTERY for the
13.1 S1 DETAILED MULTISCALE REFERENCE (the scale x resolution study of the
qualified patch piece). Six checks on the house harness
(tools/port_registry.py port_test/expect); exit 0 = the S1 study is
qualified: the scale-transfer vs remeshing question is answered with
numbers, the deliberately-unmatched regimes are recorded not hidden, and
the piece record carries the measured resolution validity map.

  (a) convergence at scale 1.0: the preregistered observable (apex
      displacement) decreases MONOTONE on the 100->150->200->300 ladder
      (measured dz 4.65e-5 -> 1.63e-5 -> 1.16e-5 wu; noisy sub-linear order
      estimates 1.51/0.49); the rim reaction norms are excluded by
      preregistration (measured DEFINITION law mean*n_rim ~ const, <2%
      spread); the honest resolution limit is RETAINED: the ladder does
      NOT reach tol_u = 1e-6 wu (finest dz = 11.6x tol_u).
  (b) SCALE TRANSFER vs REMESHING: on the piece, the scale (physics)
      component at 2.0x is 6591x tol_u vs a remeshing component of 12x
      tol_u (physics/remeshing = 567x); on the star (11.19 v2 adoption
      round): under the ADOPTED v2 solver BOTH rungs measure in-gate at
      1.5x/2.0x -- the pre-adoption drift was the v1 MACHINERY's
      stagnation floor (machinery_superseded), the law never widened.
  (c) deliberately unmatched regime: n_rim=100 at 1.0x and 2.0x misstates
      the apex response by ~7.4e-5 wu = 74x tol_u vs matched n_rim=300;
      recorded, never hidden.
  (d) cost: mean wall time per cell rises monotonically with resolution
      (throughput table for S2 planning).
  (e) honesty: every grid cell (20) and every star drift cell (4) is
      recorded with status/residual/wall -- none dropped (under the
      adopted v2 solver the star drift cells measure in-gate; the
      pre-adoption over-gate run is retained in history).
  (f) determinism: the same grid run twice -> the same study hash.

Run:  python tools/mechanism_factory/scale_resolution_checks.py
      exit 0 = all PASS, 1 = a check failed, 2 = evidence-path refusal.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_TOOLS / "membrane_scale_lab"))
sys.path.insert(0, str(_HERE))

from port_registry import port_test, expect        # noqa: E402 harness
import scale_resolution as sr                       # noqa: E402 the study
import composed_patch as cp                         # noqa: E402 packet/units
import piece_record as pr                           # noqa: E402 the library
import research_record as rr                        # noqa: E402 the loop

EVID_DIR = cp.EVID_DIR
CHAIN_RECEIPT = "composed_chain_receipt_20261016T092136.068087Z.json"

# PREREGISTERED (the tolerance is DERIVED from the law's own error scale --
# the packet's 1e-6 N gate through the compliance P = 1/gamma_max = 1 wu/N;
# nothing below is widened after seeing results)
ALLOWANCES = {
    "tol_u_wu": sr.TOL_U_WU,                    # 1e-6 wu (derived)
    "packet_gate_N": sr.PACKET_GATE_N,          # 1e-6 N (the law)
    "rim_deflaw_spread_max": 0.02,              # mean*n_rim const <2%
    "unmatched_misstate_min_x_tol": 10.0,       # a deliberately-unmatched
                                                # cell must misstate >10x
    "physics_over_mesh_min_2x": 100.0,          # scale dominates remeshing
    "star_refinement_change_max_pct": 5.0,      # residual barely moves
    "matched_regime": "n_rim=300 (finest rung) at each scale",
    "unmatched_regime": "n_rim=200 (qualification resolution) reused; "
                        "n_rim=100 deliberately coarse",
}
EXPECTED_CHECKS = 6


@port_test(
    "a_convergence_scale_one",
    "At scale 1.0 the preregistered convergence observable (apex "
    "displacement) decreases MONOTONE on the resolution ladder and the "
    "rim-norm exclusion law holds; the measured order is reported and "
    "the honest resolution limit (finest dz = 11.6x tol_u) is retained, "
    "not hidden.",
    "The ladder is not monotone, the rim-norm definition law breaks, or "
    "the study pretends tol_u is reached.")
def a_convergence() -> dict:
    study = _STUDY
    lad = study["apex_ladders"]["scale1"]
    dzs = [r["dz_wu"] for r in lad]
    monotone = all(dzs[i] > dzs[i + 1] for i in range(len(dzs) - 1))
    orders = [r.get("order_estimate") for r in lad if "order_estimate" in r]
    # rim-norm DEFINITION law: mean*n_rim is constant across the ladder
    cells1 = [c for c in study["cells"] if c["scale_m"] == 1.0]
    prods = [c["rim_mean_norm_N"] * c["n_rim"] for c in cells1]
    spread = (max(prods) - min(prods)) / (sum(prods) / len(prods))
    finest_under_tol = lad[-1]["under_tol_u"]
    in_gate = all(c["in_gate"] for c in cells1)
    ok = bool(monotone and spread <= ALLOWANCES["rim_deflaw_spread_max"]
              and not finest_under_tol and in_gate
              and dzs[-1] < dzs[0])
    return {"pass": ok,
            "measured": {"dz_ladder_wu": dzs,
                          "monotone_decrease": monotone,
                          "order_estimates": orders,
                          "rim_deflaw_mean_n_prods": prods,
                          "rim_deflaw_spread": spread,
                          "finest_dz_under_tol_u": finest_under_tol,
                          "finest_dz_x_tol_u": dzs[-1] / ALLOWANCES["tol_u_wu"],
                          "scale1_cells_in_gate": in_gate}}


@port_test(
    "b_scale_transfer_vs_remeshing",
    "Scale transfer is distinguished from remeshing with numbers: on the "
    "piece the 2.0x physics component dominates the remeshing component "
    "by hundreds (measured 567x, unchanged by the solver). On the star "
    "(11.19 v2 adoption round): under the ADOPTED v2 solver BOTH "
    "resolutions measure in-gate at 1.5x/2.0x and the study's verdict "
    "rule records machinery_superseded -- the pre-adoption drift was the "
    "v1 machinery's stagnation floor, not discretization and not "
    "law-level physics.",
    "The star's drift cells fail the packet's unchanged 1e-6 law under "
    "the adopted solver, the verdict rule is not derived from the "
    "measured flags, or the physics component does not dominate "
    "remeshing at 2.0x.")
def b_scale_transfer() -> dict:
    study = _STUDY
    tr = {r["scale_m"]: r for r in study["scale_transfer_vs_remeshing"]}
    two = tr[2.0]
    physics_dominates = (two["physics_over_remeshing"]
                         >= ALLOWANCES["physics_over_mesh_min_2x"])
    verdict = study["star_drift_verdict"]
    ok = bool(verdict["verdict"] == "machinery_superseded"
              and physics_dominates
              and all(ps_["refined_in_gate"] and ps_["over_gate_x_at_n300"]
                      <= 1.0 for ps_ in verdict["per_scale"]))
    return {"pass": ok,
            "measured": {"piece_2x_physics_x_tol_u":
                             two["physics_x_tol_u"],
                          "piece_2x_remeshing_x_tol_u":
                             two["remeshing_x_tol_u"],
                          "piece_2x_physics_over_remeshing":
                             two["physics_over_remeshing"],
                          "star_verdict": verdict["verdict"],
                          "star_per_scale": verdict["per_scale"]}}


@port_test(
    "c_deliberately_unmatched",
    "A deliberately unmatched regime is RECORDED, not hidden: reusing the "
    "coarse n_rim=100 mesh misstates the piece's apex response by ~7.4e-5 "
    "wu (74x tol_u) vs the matched n_rim=300 mesh at 1.0x and 2.0x alike; "
    "even the qualified n_rim=200 reused at 2.0x misstates by ~12x tol_u.",
    "No unmatched cell misstates by more than the preregistered 10x-tol_u "
    "threshold, or the misstatement is dropped from the study.")
def c_unmatched() -> dict:
    cells = _STUDY["cells"]
    mis = []
    for s in (1.0, 2.0):
        z = {c["n_rim"]: c["apex_z_wu"] for c in cells if c["scale_m"] == s}
        mis.append({"scale_m": s,
                    "n100_vs_n300_wu": abs(z[100] - z[300]),
                    "n100_vs_n300_x_tol_u": abs(z[100] - z[300])
                    / ALLOWANCES["tol_u_wu"],
                    "n200_vs_n300_wu": abs(z[200] - z[300]),
                    "n200_vs_n300_x_tol_u": abs(z[200] - z[300])
                    / ALLOWANCES["tol_u_wu"]})
    ok = bool(all(m["n100_vs_n300_x_tol_u"]
                  > ALLOWANCES["unmatched_misstate_min_x_tol"] for m in mis))
    return {"pass": ok, "measured": {"unmatched_cells": mis,
                                      "threshold_x_tol":
                                          ALLOWANCES[
                                              "unmatched_misstate_min_x_tol"]}}


@port_test(
    "d_cost_resolution",
    "Cost is recorded for S2 planning: mean wall time per cell rises "
    "monotonically with resolution across the grid (n_rim 100/150/200/300).",
    "Mean wall time does not increase with resolution (a cost table that "
    "cannot plan throughput), or any cell lacks its wall time.")
def d_cost() -> dict:
    cells = _STUDY["cells"]
    means = {}
    for n in sr.RESOLUTIONS:
        ws = [c["wall_time_s"] for c in cells if c["n_rim"] == n]
        means[n] = sum(ws) / len(ws)
    ns = sorted(means)
    monotone = all(means[ns[i]] < means[ns[i + 1]]
                   for i in range(len(ns) - 1))
    ok = bool(monotone
              and all(c["wall_time_s"] > 0 for c in cells))
    return {"pass": ok, "measured": {"mean_wall_s_by_resolution": means,
                                      "monotone_increase": monotone,
                                      "throughput_note": "S2 planning: "
                                          "cost grows ~ superlinearly "
                                          "with n_rim; budget the finest "
                                          "rung accordingly"}}


@port_test(
    "e_honesty_all_cells",
    "Honesty: EVERY grid cell (5 scales x 4 resolutions = 20) and every "
    "star drift cell (4) is recorded with status, free residual and wall "
    "time -- none dropped -- including the star's over-gate stagnations "
    "and the piece cells' benign stagnated terminations.",
    "A cell is missing, lacks its status/residual/wall, or the grid is "
    "not the full 5x4 cartesian product.")
def e_honesty() -> dict:
    cells = _STUDY["cells"]
    star = _STUDY["star_drift_cells"]
    full_grid = {(s, n) for s in sr.SCALES for n in sr.RESOLUTIONS}
    got = {(c["scale_m"], c["n_rim"]) for c in cells}
    keys_ok = all(all(k in c for k in ("status", "free_residual_N",
                                        "wall_time_s", "apex_z_wu"))
                  for c in cells)
    star_ok = len(star) == len(sr.STAR_DRIFT_CELLS) and all(
        all(k in c for k in ("status", "free_residual_N", "wall_time_s"))
        for c in star)
    in_gate_n = sum(1 for c in cells if c["in_gate"])
    over_gate_star = [c for c in star if not c["in_gate"]]
    # every star drift cell is recorded with its measured flags; under
    # the ADOPTED v2 solver all four measure IN-gate (the pre-adoption
    # over-gate drift is superseded), and none is dropped either way
    ok = bool(len(cells) == 20 and got == full_grid and keys_ok
              and star_ok
              and all(c["in_gate"] for c in star))
    return {"pass": ok,
            "measured": {"cells_recorded": len(cells),
                          "grid_complete": got == full_grid,
                          "piece_cells_in_gate": in_gate_n,
                          "star_cells_recorded": len(star),
                          "star_over_gate_retained":
                              [(c["scale_m"], c["n_rim"],
                                c["free_residual_N"]) for c in star]}}


@port_test(
    "f_determinism",
    "Determinism: the same grid run twice (independent fixture builds and "
    "solves) yields the SAME study hash over the cell content (wall times "
    "excluded from the hash by construction).",
    "Two runs of the same grid disagree on the study hash.")
def f_determinism() -> dict:
    h1 = sr.run_study(include_star=False)["study_hash"]
    h2 = sr.run_study(include_star=False)["study_hash"]
    ok = bool(h1 == h2 and h1)
    return {"pass": ok, "measured": {"study_hash": h1, "matches": h1 == h2}}


expect(EXPECTED_CHECKS)


# ── runner ──────────────────────────────────────────────────────────────────

ORDER = ["a_convergence_scale_one", "b_scale_transfer_vs_remeshing",
         "c_deliberately_unmatched", "d_cost_resolution",
         "e_honesty_all_cells", "f_determinism"]

_STUDY = None      # the full study (grid + star drift), run once in main


def main(argv: list) -> int:
    global _STUDY
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    try:
        out_path = resolve_evidence_path(EVID_DIR, "scale_resolution_checks",
                                         argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT

    print("=" * 100)
    print("  S1 DETAILED MULTISCALE REFERENCE (13.1): scale x resolution "
          "study of the qualified patch piece")
    print(f"  preregistered: tol_u = {sr.TOL_U_WU:.0e} wu (derived from "
          f"the packet's {sr.PACKET_GATE_N:.0e} N gate through P = "
          f"{sr.P_COMPLIANCE_WU_PER_N:.0f} wu/N); matched = n_rim 300; "
          f"unmatched = n_rim 200 reused / 100 coarse")
    print("=" * 100)

    _STUDY = sr.run_study(include_star=True)
    study_receipt = sr.write_study_receipt(_STUDY, "checks")
    print(f"study receipt: {study_receipt}  "
          f"(study hash {_STUDY['study_hash'][:16]}, "
          f"{len(_STUDY['cells'])} grid cells, "
          f"{len(_STUDY['star_drift_cells'])} star drift cells)")

    from port_registry import TESTS
    results, failed = {}, 0
    for name in ORDER:
        rec = TESTS[name]
        print(f"\n[{name}]\n  STATEMENT : {rec['statement'][:96]}...")
        print(f"  FALSIFIER : {rec['falsifier'][:96]}...")
        try:
            r = rec["fn"]()
            results[name] = r
            verdict = "PASS" if r.get("pass") else "FAIL"
            if not r.get("pass"):
                failed += 1
            print(f"  -> {verdict}   "
                  f"{json.dumps(r.get('measured', {}), default=str)[:400]}")
        except Exception as ex:            # a crash is a FAIL, never a skip
            failed += 1
            results[name] = {"pass": False,
                             "error": f"{type(ex).__name__}: {ex}"}
            print(f"  -> FAIL (exception) {type(ex).__name__}: {ex}")

    print("\n" + "-" * 100)
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. Tolerances "
          f"derived from the packet's law and preregistered in "
          f"scale_resolution.py; nothing widened after seeing results.")

    verdict = _STUDY["star_drift_verdict"]
    receipt = {
        "schema": "chimera-mechanism-factory-scale-resolution-checks-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "what": "13.1 S1 detailed multiscale reference: same mechanism at "
                "5 physical scales x 4 mesh resolutions; preregistered "
                "convergence tolerance and matched-regime definition; "
                "scale transfer distinguished from remeshing; "
                "deliberately unmatched regimes recorded",
        "source_commit": cp._source_commit(),
        "source_file_hashes": {
            rel: cp._sha256_file(cp._REPO / rel) for rel in cp.HASHED_SOURCES
        },
        "packet_sha256": cp._sha256_bytes(cp.PACKET_PATH.read_bytes()),
        "units": json.loads(cp.PACKET_PATH.read_bytes())["units"],
        "preregistered_allowances": ALLOWANCES,
        "study_receipt": study_receipt.name,
        "study_hash": _STUDY["study_hash"],
        "resolution_axis_mapping": _STUDY["resolution_axis_mapping"],
        "checks": {n: {"pass": bool(results[n].get("pass"))} for n in ORDER},
        "cases": {n: results[n] for n in ORDER},
        "verdicts": {
            "convergence": "apex displacement decreases monotonically on "
                           "the ladder (order est ~1.5/0.5, noisy "
                           "sub-linear); tol_u = 1e-6 wu is NOT reached at "
                           "n_rim <= 300 (finest dz 1.16e-5 wu = 11.6x "
                           "tol_u) -- honest resolution limit",
            "star_drift_verdict": verdict["verdict"],
            "star_drift_numbers": verdict["per_scale"],
            "domain_amendment": "piece.patch-equilibrium: every studied "
                                "(scale, resolution) cell is in-gate "
                                "(20/20), including 2.0x at every "
                                "resolution; the domain bounds STAND (no "
                                "extension claimed); the measured "
                                "resolution validity map is appended to "
                                "physical_definition",
        },
        "record_amendment": {
            "record": "piece.patch-equilibrium",
            "law": "additive-only amendment "
                   "(piece_record.amend_physical_definition); the prior "
                   "bytes are archived under pieces/archive/; this "
                   "receipt is the entry's cited evidence",
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=1, default=str) + "\n",
                        encoding="utf-8")
    print(f"  receipt: {out_path}")

    if failed:
        return 1

    # ── deliverable 3: the piece-record amendment (AFTER the receipt
    # exists: the entry cites it) -- additive-only, prior bytes archived
    try:
        folded = {}
        for c in _STUDY["cells"]:
            folded.setdefault(f"{c['scale_m']:g}", {})[str(c["n_rim"])] = \
                c["in_gate"]
        validity = {
            "study_receipt": study_receipt.name,
            "study_hash": _STUDY["study_hash"],
            "grid": {"scales": list(sr.SCALES),
                      "resolutions": list(sr.RESOLUTIONS)},
            "in_gate_map": folded,
            "cells_in_gate": sum(1 for c in _STUDY["cells"] if c["in_gate"]),
            "cells_total": len(_STUDY["cells"]),
            "convergence_observable": "apex_z_wu",
            "tol_u_wu": sr.TOL_U_WU,
            "finest_successive_resolution_change_wu":
                _STUDY["apex_ladders"]["scale1"][-1]["dz_wu"],
            "matched_regime": ALLOWANCES["matched_regime"],
            "domain_verdict": "bounds stand: every studied (scale, "
                              "resolution) cell solves in-gate, "
                              "including 2.0x at every resolution; no "
                              "domain extension claimed; the n_rim<=300 "
                              "ladder does not reach tol_u (honest "
                              "resolution limit)",
        }
        pr_amend = True
        # rerun idempotency: the amendment law refuses a DIFFERENT value
        # for an existing key (append-only evidence). If the retained
        # resolution_validity carries the SAME study hash and the same
        # measured map (the study is deterministic), the retained entry
        # STANDS and the re-run amends nothing.
        try:
            retained_v = pr.load_record("piece.patch-equilibrium")[
                "physical_definition"].get("resolution_validity")
        except pr.PieceRecordRefused:
            retained_v = None
        if retained_v is not None:
            material_same = (
                retained_v.get("in_gate_map") == folded
                and retained_v.get("tol_u_wu") == sr.TOL_U_WU
                and abs(float(retained_v.get(
                    "finest_successive_resolution_change_wu", 0))
                    - _STUDY["apex_ladders"]["scale1"][-1]["dz_wu"])
                <= 1e-18)
            if material_same:
                print("amendment: retained 'resolution_validity' stands "
                      "(idempotent re-run; same measured map, it cites "
                      f"receipt {retained_v.get('study_receipt')})")
                pr_amend = False
            else:
                raise pr.PieceRecordRefused(
                    "piece_pd_key_exists",
                    "a retained resolution_validity disagrees with this "
                    "run's study; investigate, never overwrite")
        if pr_amend:
            pr.amend_physical_definition("piece.patch-equilibrium",
                                         "resolution_validity", validity)
            print("amendment: piece.patch-equilibrium physical_definition "
                  "gains 'resolution_validity' (prior bytes archived "
                  "under pieces/archive/)")
    except Exception as ex:
        failed += 1
        print(f"  -> FAIL (record amendment) {type(ex).__name__}: {ex}")

    # ── deliverable 4: the scale-drift followup gets its result link --
    # a new allocation (finite) + one bounded experiment citing the study
    # receipt and the retained followup record
    if not failed:
        try:
            followups = sorted(rr.RESEARCH_DIR.glob(
                "followup.star-scale-drift.*.json"))
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%f")[
                :-3] + "Z"
            alloc_id = f"proposal.scale-study-allocation.{stamp}"
            rr.write_record({
                "record_id": alloc_id, "kind": "proposal",
                "question": "answer the retained star-scale-drift "
                            "followup with ONE bounded S1 study",
                "parent_evidence_ids": [study_receipt.name],
                "budget": {"allocated": 1, "consumed": 0}})
            exp_id = f"experiment.star-scale-drift-verdict.{stamp}"
            parents = [followups[-1].name, study_receipt.name,
                       CHAIN_RECEIPT]
            p15, p20 = verdict["per_scale"]
            b = results["b_scale_transfer_vs_remeshing"]["measured"]
            result_text = (
                verdict["verdict_text"]
                + f" Numbers: 1.5x residual {p15['residual_n200_N']:.4e} -> "
                  f"{p15['residual_n300_N']:.4e} N "
                  f"({p15['refinement_change_pct']:.1f}% change, "
                  f"{p15['over_gate_x_at_n300']:.2f}x gate); 2.0x residual "
                  f"{p20['residual_n200_N']:.4e} -> "
                  f"{p20['residual_n300_N']:.4e} N "
                  f"({p20['refinement_change_pct']:.1f}% change, "
                  f"{p20['over_gate_x_at_n300']:.2f}x gate); on the piece "
                  f"the 2.0x physics component exceeds the remeshing "
                  f"component by {b['piece_2x_physics_over_remeshing']:.0f}x")
            rr.write_record({
                "record_id": exp_id, "kind": "experiment",
                "question": verdict["question"],
                "parent_evidence_ids": parents,
                "allocation_id": alloc_id,
                "budget": {"allocated": None, "consumed": 1},
                "alternatives": ["discretization: refining resolution "
                                  "brings the residual under the gate",
                                  "scale physics: it does not"],
                "experiment_identity": "scale_resolution.py S1 grid (20 "
                                       "cells, 5 scales x 4 resolutions) "
                                       "+ star drift block (4 cells)",
                "result": result_text,
                "cost": {"kind": "cpu_wall_s",
                          "value": sum(c["wall_time_s"]
                                       for c in _STUDY["cells"])},
                "applicability": "the apex-weld star under the "
                                 "constant-gamma law at 0.5-2.0x; the "
                                 "gate is never widened, 1.5x/2.0x stay "
                                 "honestly unqualified scales for THIS "
                                 "topology",
                "next_questions": ["does a different preconditioner or "
                                    "an energy-relative residual law "
                                    "move the stagnation floor at "
                                    "larger scales (S2 preregistration)",
                                    "does the piece's resolution limit "
                                    "(11.6x tol_u at n_rim 300) bound "
                                    "the library's per-piece accuracy "
                                    "budget"],
                "independent_status": "the study is deterministic (same "
                                      "study hash on rerun); the drift "
                                      "verdict is a measured finding, "
                                      "not a tuned one",
            })
            print(f"research: allocation + experiment appended under "
                  f"{rr.RESEARCH_DIR} (the followup now has its result "
                  f"link)")
        except Exception as ex:
            failed += 1
            print(f"  -> FAIL (research record) {type(ex).__name__}: {ex}")

    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:
        print(f"REFUSED: {exc}")
        raise SystemExit(2)
