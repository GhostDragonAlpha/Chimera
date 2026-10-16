"""port_solve_checks.py -- THE REGISTERED FALSIFIER BATTERY for the
11.20.5 PORT-BASED ASSEMBLY SOLVE (the LEGO composition primitive): two
pieces coupled through their port response operators ONLY, against the
fused-mesh reference (composed artifact). Six checks on the house
harness (tools/port_registry.py port_test/expect); exit 0 = the port
solve is qualified FOR THIS INTERFACE and the fused solve stays the
named detailed fallback.

  (a) AGREEMENT: the port-based solve reproduces the fused-mesh
      reference's seam force split and B-port reactions within the
      preregistered tolerances (measured: rim-net differences ~3e-8 N,
      seam position ~1e-8 wu).
  (b) balance: the coupled solution satisfies global force AND moment
      balance at the packet's unchanged 1e-6 law.
  (c) NOT one-shot: a single isolated evaluation of each piece at the
      built configuration FAILS the interface residual by a measured
      margin (|R| = 8.2e-1 N vs the 1e-6 law gate) -- the iteration is
      load-bearing.
  (d) work/energy: at convergence the interface exchange is closed
      (equal-and-opposite with the load, both pieces at bit-identical
      seam positions), the massless joint creates no net work over the
      solved displacement, and the coupled stored energy matches the
      fused reference.
  (e) refusals: out-of-domain and non-convergence are both refused by
      name, each with the qualified detailed fallback (the fused-mesh
      solve) already run and attached.
  (f) determinism: same inputs -> same interface solution hash.

Run:  python tools/mechanism_factory/port_solve_checks.py
      exit 0 = all PASS, 1 = a check failed, 2 = evidence-path refusal.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_TOOLS / "membrane_scale_lab"))
sys.path.insert(0, str(_HERE))

from port_registry import port_test, expect        # noqa: E402 harness
import port_solve as ps                             # noqa: E402 the solve
import composed_patch as cp                         # noqa: E402 the reference
import piece_record as pr                           # noqa: E402 the library

PACKET = cp.PACKET_PATH
EVID_DIR = cp.EVID_DIR
ASM1_RECEIPT = "composed_qualification_receipt_20261016T075201.116240Z.json"

# PREREGISTERED (frozen before any run; the packet's law is quoted,
# never widened; the solve law itself is preregistered in port_solve.py)
ALLOWANCES = {
    "agreement_tol_N": ps.AGREEMENT_TOL_N,      # 1e-6 N; measured 3.2e-8
    "agreement_tol_wu": ps.AGREEMENT_TOL_WU,    # 1e-5 wu; measured 1.0e-8
    "balance_law_source": "example_packet.acceptance_thresholds (1e-6)",
    "joint_work_tol_J": ps.JOINT_WORK_TOL_J,    # 1e-7 J; measured ~1e-12
    "energy_tol_J": 1.0e-6,                     # coupled stored energy vs
                                                # the fused reference
    "interface_gate_N": ps.INTERFACE_GATE_N,    # 1e-10; measured 3.5e-12
    "domain_radius_wu": ps.DOMAIN_RADIUS_WU,
}
EXPECTED_CHECKS = 6


def _coupled_moment(out: dict, problem) -> float:
    """Global moment about the origin of the coupled solution: rim pin
    reactions at their (fixed) coordinates + the load at the seam."""
    mom = np.zeros(3)
    for piece, rows in ((problem.piece_a, "A"), (problem.piece_b, "B")):
        resp = piece.response(out["seam_position"])
        R = resp["reactions"]
        pins = piece.pins
        pos = resp["positions"]
        for k, v in enumerate(pins):
            if v == piece.seam_local:
                continue
            mom += np.cross(pos[v], R[k])
    mom += np.cross(out["seam_position"], problem.f_load)
    return float(np.linalg.norm(mom))


@port_test(
    "a_agreement_with_fused_reference",
    "The port-based solve reproduces the fused-mesh reference (the "
    "composed artifact solved by mesh fusion): seam force split (A rim "
    "net = film A's seam force) and the B-port reactions agree within "
    "the preregistered 1e-6 N, the seam position within 1e-5 wu.",
    "Any rim-net difference, seam-force difference or seam-position "
    "difference exceeds its preregistered tolerance.")
def a_agreement() -> dict:
    problem = ps.build_two_piece_interface(scale=1.0)
    out = ps.solve_interface(problem)
    ref = ps.fused_reference(problem)
    d_a = float(np.linalg.norm(out["A_rim_net_N"] - ref["A_rim_net_N"]))
    d_b = float(np.linalg.norm(out["B_rim_net_N"] - ref["B_rim_net_N"]))
    d_x = float(np.linalg.norm(out["seam_position"] - ref["seam_position"]))
    ok = bool(d_a <= ALLOWANCES["agreement_tol_N"]
              and d_b <= ALLOWANCES["agreement_tol_N"]
              and d_x <= ALLOWANCES["agreement_tol_wu"])
    return {"pass": ok,
            "measured": {"A_rim_net_diff_N": d_a, "B_rim_net_diff_N": d_b,
                          "seam_pos_diff_wu": d_x,
                          "iters": out["iterations"],
                          "interface_residual_N": out["interface_residual_N"]}}


@port_test(
    "b_coupled_balance",
    "The coupled solution satisfies GLOBAL force and moment balance at "
    "the packet's unchanged 1e-6 law: sum of both pieces' rim "
    "reactions + the seam load = 0, and the moment about the origin "
    "closes.",
    "Either the global force residual or the global moment residual "
    "exceeds the packet's 1e-6 law.")
def b_balance() -> dict:
    problem = ps.build_two_piece_interface(scale=1.0)
    out = ps.solve_interface(problem)
    f_res = float(np.linalg.norm(out["A_rim_net_N"] + out["B_rim_net_N"]
                                  + problem.f_load))
    m_res = _coupled_moment(out, problem)
    ok = bool(f_res <= 1e-6 and m_res <= 1e-6)
    return {"pass": ok,
            "measured": {"global_force_residual_N": f_res,
                          "global_moment_residual_Nm": m_res}}


@port_test(
    "c_not_one_shot",
    "A single isolated evaluation of each piece at the built "
    "configuration FAILS the interface residual by a measured margin "
    "(|R| = 8.2e-1 N, ~8e5 times the packet's 1e-6 gate): evaluating "
    "each piece once in isolation is insufficient; the interface "
    "iteration is load-bearing.",
    "A one-shot evaluation passes the gate, or the converged solve "
    "needed zero iterations.")
def c_not_one_shot() -> dict:
    problem = ps.build_two_piece_interface(scale=1.0)
    R0, _sides = ps.interface_residual(problem, problem.x_ref)
    r0 = float(np.linalg.norm(R0))
    out = ps.solve_interface(problem)
    ok = bool(r0 > 1e-6 and out["iterations"] >= 1
              and out["interface_residual_N"] <= ALLOWANCES["interface_gate_N"])
    return {"pass": ok,
            "measured": {"one_shot_residual_N": r0,
                          "gate_N": 1e-6,
                          "margin_factor": r0 / 1e-6,
                          "converged_residual_N":
                              out["interface_residual_N"],
                          "iterations": out["iterations"]}}


@port_test(
    "d_work_energy_interface",
    "At convergence the interface exchange is closed in consistent "
    "frames: both piece responses sit at BIT-IDENTICAL seam positions "
    "(compatible motion), the equal-and-opposite closure with the load "
    "holds within the gate, the massless joint creates no net work over "
    "the solved displacement (closure . displacement within the "
    "preregistered 1e-7 J), and the coupled stored energy matches the "
    "fused reference within 1e-6 J.",
    "Frame incompatibility, an unclosed exchange, net joint work, or a "
    "stored-energy mismatch beyond tolerance.")
def d_work_energy() -> dict:
    problem = ps.build_two_piece_interface(scale=1.0)
    out = ps.solve_interface(problem)
    closure = (out["seam_force_A_N"] + out["seam_force_B_N"]
               + problem.f_load)
    closed = float(np.linalg.norm(closure))
    dx = out["seam_position"] - problem.x_ref
    w_joint = float(abs(np.dot(closure, dx)))
    u_port = (out["surface_energy_J"]["A"] + out["surface_energy_J"]["B"])
    ref = ps.fused_reference(problem)
    d_u = abs(u_port - ref["surface_energy_J"])
    compat = out["seam_positions_bit_identical"]
    ok = bool(closed <= 1e-6 and compat and w_joint <= ALLOWANCES["joint_work_tol_J"]
              and d_u <= ALLOWANCES["energy_tol_J"])
    return {"pass": ok,
            "measured": {"closure_N": closed,
                          "frames_bit_identical": compat,
                          "net_joint_work_J": w_joint,
                          "stored_energy_diff_J": d_u}}


@port_test(
    "e_named_refusals_with_fallback",
    "Both failure modes are refused BY NAME with the qualified detailed "
    "fallback (the fused-mesh solve_equilibrium) already run and "
    "attached: an initial seam displacement outside the preregistered "
    "domain box -> port_solve_out_of_domain; a truncated iteration "
    "budget -> port_solve_not_converged.",
    "A refusal without its name, without the named fused fallback, or a "
    "fake pass.")
def e_refusals() -> dict:
    problem = ps.build_two_piece_interface(scale=1.0)
    ood_reason = nc_reason = None
    ood_fb = nc_fb = None
    try:
        ps.solve_interface(problem, x_init=np.asarray([0.0, 0.0, 5.0]))
    except ps.PortSolveRefused as ex:
        ood_reason = ex.reason
        ood_fb = ex.fallback
    try:
        ps.solve_interface(problem, max_iterations=2)
    except ps.PortSolveRefused as ex:
        nc_reason = ex.reason
        nc_fb = ex.fallback
    fb_ok = (ood_fb.get("fallback") == ps.FALLBACK_NAME
             and nc_fb.get("fallback") == ps.FALLBACK_NAME
             and ood_fb["result"]["free_residual_N"] <= 1e-6
             and nc_fb["result"]["free_residual_N"] <= 1e-6)
    ok = bool(ood_reason == "port_solve_out_of_domain"
              and nc_reason == "port_solve_not_converged" and fb_ok)
    return {"pass": ok,
            "measured": {"out_of_domain_refused_as": ood_reason,
                          "not_converged_refused_as": nc_reason,
                          "fallback": ps.FALLBACK_NAME,
                          "fallback_fused_residual_N":
                              ood_fb["result"]["free_residual_N"]}}


@port_test(
    "f_determinism",
    "Same inputs -> same interface solution: two independent solves "
    "(fresh response operators) produce the same solution hash over the "
    "seam position, seam forces and rim nets.",
    "Two solves of the same problem disagree.")
def f_determinism() -> dict:
    h = []
    for _ in range(2):
        problem = ps.build_two_piece_interface(scale=1.0)
        out = ps.solve_interface(problem)
        h.append(out["solution_hash"])
    ok = bool(h[0] == h[1] and h[0])
    return {"pass": ok, "measured": {"hash": h[0], "matches": h[0] == h[1]}}


expect(EXPECTED_CHECKS)


# ── runner ──────────────────────────────────────────────────────────────────

ORDER = ["a_agreement_with_fused_reference", "b_coupled_balance",
         "c_not_one_shot", "d_work_energy_interface",
         "e_named_refusals_with_fallback", "f_determinism"]


def main(argv: list) -> int:
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    try:
        out_path = resolve_evidence_path(EVID_DIR, "port_solve_checks", argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT

    from port_registry import TESTS
    results, failed = {}, 0
    print("=" * 100)
    print("  PORT-BASED ASSEMBLY SOLVE (11.20.5 LEGO primitive vs the "
          "fused-mesh reference): falsifier battery")
    print(f"  allowances (preregistered): agreement {ALLOWANCES['agreement_tol_N']:.0e} N "
          f"/ {ALLOWANCES['agreement_tol_wu']:.0e} wu; balance law = "
          f"packet 1e-6; joint work {ALLOWANCES['joint_work_tol_J']:.0e} J; "
          f"interface gate {ALLOWANCES['interface_gate_N']:.0e} N")
    print("=" * 100)
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
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. The solve "
          f"law is preregistered in port_solve.py; nothing widened after "
          f"seeing results.")

    receipt = {
        "schema": "chimera-mechanism-factory-port-solve-checks-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "what": "11.20.5 port-based assembly solve qualified against the "
                "fused-mesh reference: agreement, coupled balance, "
                "one-shot insufficiency, interface work accounting, "
                "named refusals with the fused fallback, determinism",
        "source_commit": cp._source_commit(),
        "source_file_hashes": {
            rel: cp._sha256_file(cp._REPO / rel) for rel in cp.HASHED_SOURCES
        },
        "packet_sha256": cp._sha256_bytes(PACKET.read_bytes()),
        "units": json.loads(PACKET.read_bytes())["units"],
        "preregistered_allowances": ALLOWANCES,
        "checks": {n: {"pass": bool(results[n].get("pass"))} for n in ORDER},
        "cases": {n: results[n] for n in ORDER},
        "solve_law": {"interface_gate_N": ps.INTERFACE_GATE_N,
                       "max_iterations": ps.MAX_ITERATIONS,
                       "fd_h_wu": ps.FD_H_WU,
                       "domain_radius_wu": ps.DOMAIN_RADIUS_WU,
                       "fallback": ps.FALLBACK_NAME,
                       "interface_dof": "the seam vertex's FULL 3D "
                                         "displacement (no reduction; the "
                                         "weld consumes every other DOF "
                                         "and vertex forces are local to "
                                         "incident faces)"},
        "record_amendment": {
            "record": "assembly.star-k2",
            "entry_kind": "port-based",
            "law": "additive-only amendment (piece_record."
                    "amend_representations); the prior bytes are "
                    "archived under pieces/archive/; this receipt is the "
                    "entry's cited evidence",
        },
        "scope_note": "qualified for THIS apex-weld interface and load "
                      "class; the fused-mesh solve remains the qualified "
                      "detailed fallback and the admission path for "
                      "other interfaces",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=1, default=str) + "\n",
                        encoding="utf-8")
    print(f"  receipt: {out_path}")

    # the piece-record amendment (AFTER the receipt exists: the entry
    # cites it): assembly.star-k2 gains the port-based representation
    # entry -- additive-only, prior bytes archived
    if not failed:
        try:
            measured = {
                "A_rim_net_diff_N":
                    results["a_agreement_with_fused_reference"]["measured"]
                    ["A_rim_net_diff_N"],
                "B_rim_net_diff_N":
                    results["a_agreement_with_fused_reference"]["measured"]
                    ["B_rim_net_diff_N"],
                "seam_pos_diff_wu":
                    results["a_agreement_with_fused_reference"]["measured"]
                    ["seam_pos_diff_wu"],
                "iterations":
                    results["a_agreement_with_fused_reference"]["measured"]
                    ["iters"],
                "interface_residual_N":
                    results["a_agreement_with_fused_reference"]["measured"]
                    ["interface_residual_N"]}
            entry = ps.port_representation_entry(out_path.name, measured)
            # rerun idempotency: the amendment law refuses a DIFFERENT
            # entry of the same kind (append-only evidence). If a
            # port-based entry is already retained and materially
            # identical (same law, measured agreement within the same
            # preregistered tolerances), the retained entry STANDS and
            # the re-run amends nothing.
            existing = None
            try:
                retained = pr.load_record("assembly.star-k2")
                existing = next((r for r in retained["representations"]
                                 if r.get("kind") == "port-based"), None)
            except pr.PieceRecordRefused:
                existing = None          # first run: nothing retained yet
            if existing is not None:
                m_old = existing.get("measured", {})
                close = (abs(m_old.get("A_rim_net_diff_N", 1.0)
                             - measured["A_rim_net_diff_N"])
                         <= ALLOWANCES["agreement_tol_N"]
                         and abs(m_old.get("B_rim_net_diff_N", 1.0)
                                 - measured["B_rim_net_diff_N"])
                         <= ALLOWANCES["agreement_tol_N"]
                         and abs(m_old.get("seam_pos_diff_wu", 1.0)
                                 - measured["seam_pos_diff_wu"])
                         <= ALLOWANCES["agreement_tol_wu"])
                if close:
                    print(f"amendment: retained port-based entry stands "
                          f"(idempotent re-run; it cites receipt "
                          f"{existing.get('receipt_ids', ['?'])[0]})")
                else:
                    raise pr.PieceRecordRefused(
                        "piece_representation_kind_exists",
                        "a retained port-based entry disagrees with this "
                        "run's measurements; investigate, never overwrite")
            else:
                pr.amend_representations("assembly.star-k2", entry)
                amended = pr.load_record("assembly.star-k2")
                kinds = [r["kind"] for r in amended["representations"]]
                print(f"amendment: assembly.star-k2 representations now "
                      f"{kinds} (prior bytes archived under pieces/archive/)")
        except Exception as ex:
            failed += 1
            print(f"  -> FAIL (record amendment) {type(ex).__name__}: {ex}")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except cp.EvidencePathExists as exc:
        print(f"REFUSED: {exc}")
        raise SystemExit(2)
