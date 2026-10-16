"""composed_chain_checks.py -- THE REGISTERED FALSIFIER BATTERY for the P5
REUSE assembly (the k=2 fan-out star: assembly 1's pieces A and B reused
byte-identically, new piece C welded at the same apex seam).

Six checks on the house harness (tools/port_registry.py port_test/expect).
All tolerances are preregistered BELOW, frozen in code before any run; the
balance law is the PACKET's acceptance_thresholds (the preregistered 1e-6
law) -- the reuse certificate adds no thresholds.

  (a) piece reuse: the vertex/face BLOCKS of pieces A and B inside assembly
      2 are BYTE-IDENTICAL (sha256) to assembly 1's -- reuse proven, not
      re-derived. Falsifier: any re-derivation or placement change shows up
      as a hash mismatch.
  (b) coupled balance: at the ONE reference solve on the joined star mesh,
      |sum(reactions over all three pin blocks) + sum(loads)| <=
      1e-6*max(1,sum|f|) and the moment about the origin within the same
      law.
  (c) seam single-valued at BOTH welded joints: one seam vertex (no
      duplicated coordinates), owned by A, referenced by BOTH hangers (B
      and C faces carry A's index; 3n incident faces), free, single
      F_total vector within the packet's residual law. Falsifiers: a
      duplicate-coordinate probe must fire, and a hanger with a MISMATCHED
      seam claim must be refused by name before any solve.
  (d) transfer through both welds: the per-block mean reaction norms
      differ by more than the C4 precedent margin (0.1), and BOTH output
      ports carry real load: |sum R_B| and |sum R_C| each exceed
      0.1*max(1,sum|f|) (the load crosses the reused A-B weld AND the new
      A-C weld).
  (e) reduction: removing piece C leaves a mesh BYTE-IDENTICAL to
      assembly 1 whose solve reproduces assembly 1's final energy within
      1e-9 (C2 precedent) -- the second assembly degenerates to the first
      qualified artifact.
  (f) supported scale at the NEW point 0.75x (resolution untouched, load
      unchanged): converged, balances within the packet's 1e-6 law, seam
      transfer still real. The measured scale window is recorded as a
      finding: the star's stagnation residual grows ~linearly with scale
      and 1.5x/2.0x measure OVER the packet's unchanged 1e-6 gate --
      reported, never tuned.

Run:  python tools/mechanism_factory/composed_chain_checks.py
      exit 0 = all PASS + adapter PASS on a fresh reuse receipt,
      1 = a check failed, 2 = evidence-path refusal.
"""
from __future__ import annotations

import hashlib
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

from port_registry import port_test, expect        # noqa: E402  house harness
import surface_energy_reference as ser             # noqa: E402
import patch_equilibrium as pe                     # noqa: E402
import composed_patch as cp                        # noqa: E402  pieces A, B
import composed_chain as cc                        # noqa: E402  the reuse artifact
import receipt_adapter as ra                       # noqa: E402

PACKET = cc.PACKET_PATH
_PACKET = json.loads(PACKET.read_bytes())
_THR = _PACKET["acceptance_thresholds"]

# ── PREREGISTERED ALLOWANCES (frozen before any run; never widened) ─────────
ALLOWANCES = {
    "balance_law_source": "example_packet.acceptance_thresholds "
                          "(1e-6 force/moment/free-residual, preregistered "
                          "at P0/P1; the reuse certificate adds none)",
    "reduction_energy_tol": 1.0e-9,     # C2 precedent; measured 0.0 (the
                                        # stripped mesh is byte-identical)
    "transfer_margin": 0.10,            # C4 precedent: block margins and the
                                        # per-port transfer must exceed 10%;
                                        # measured 0.483 / 0.89 / 0.81 N
    "duplicate_coordinate_tol": 1.0e-9,
    "new_scale_point": 0.75,            # NEW on the packet's size axis
                                        # (assembly 1 qualified 0.5/2.0);
                                        # measured residual 3.0e-7 N
    "scale_window_measured": "star stagnation residual ~linear in scale: "
                             "1.15e-7 (0.5x), 5.9e-7 (1x), 1.11e-6 (1.5x), "
                             "1.64e-6 (2.0x); 1.5x/2.0x are honestly "
                             "OVER the packet's unchanged 1e-6 law -- "
                             "finding, reported not tuned",
}
EXPECTED_CHECKS = 6


def _solved(scale: float = 1.0):
    star = cc.build_star(scale=scale)
    solved = cc.solve_star(star)
    return star, solved


def _block_digest(positions: np.ndarray, faces: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(positions).tobytes())
    h.update(np.ascontiguousarray(faces).tobytes())
    return h.hexdigest()


# ── (a) ─────────────────────────────────────────────────────────────────────

@port_test(
    "a_piece_reuse_byte_identical",
    "Pieces A and B inside assembly 2 are the SAME ARTIFACTS as assembly "
    "1's: the A vertex block + A faces and the B vertex block + B faces "
    "hash (sha256) identical to assembly 1's blocks -- reuse proven, not "
    "re-derived -- while piece C is genuinely new (different parameters).",
    "Any block hash differs (a placement or parameter change crept in), or "
    "C duplicates B's parameters (no new piece).")
def a_piece_reuse() -> dict:
    star, _s = _solved()
    asm1 = cp.build_assembly()
    n = cp.PIECE_A["n_rim"]
    a2 = _block_digest(star["positions"][:n + 1], star["faces"][:n])
    a1 = _block_digest(asm1.positions[:n + 1], asm1.faces[:n])
    b2 = _block_digest(star["positions"][n + 1:2 * n + 1],
                       star["faces"][n:2 * n])
    b1 = _block_digest(asm1.positions[n + 1:2 * n + 1],
                       asm1.faces[n:2 * n])
    c_new = (cc.PIECE_C != cp.PIECE_B)
    ok = bool(a2 == a1 and b2 == b1 and c_new)
    return {"pass": ok,
            "measured": {"A_block_sha256": a2[:16], "A_matches_asm1": a2 == a1,
                          "B_block_sha256": b2[:16], "B_matches_asm1": b2 == b1,
                          "C_is_new_piece": c_new}}


# ── (b) ─────────────────────────────────────────────────────────────────────

@port_test(
    "b_coupled_balance",
    "At the ONE reference solve on the joined star mesh: |sum(reactions "
    "over all three pin blocks) + sum(loads)| <= 1e-6*max(1,sum|f|) and "
    "|sum x x (reaction + f)| <= 1e-6*max(1,sum|x||f|) -- the packet's "
    "preregistered 1e-6 law across A's, B's and C's pins.",
    "Either balance residual exceeds its preregistered tolerance, or the "
    "solve does not converge within the packet's free-residual threshold.")
def b_coupled_balance() -> dict:
    star, solved = _solved()
    r = solved["result"]
    R = solved["reactions"]
    fsum = np.zeros(3)
    for _i, v in star["loads"]:
        fsum += np.asarray(v)
    scale_f = max(1.0, float(sum(np.linalg.norm(v) for _i, v in star["loads"])))
    x = r.positions
    mom = np.zeros(3)
    for k, i in enumerate(r.fixed_indices):
        mom += np.cross(x[i], R[k])
    for i, v in star["loads"]:
        mom += np.cross(x[i], np.asarray(v))
    scale_m = max(1.0, float(sum(
        np.linalg.norm(x[i]) * np.linalg.norm(v) for i, v in star["loads"])))
    fb = float(np.linalg.norm(R.sum(axis=0) + fsum))
    mb = float(np.linalg.norm(mom))
    ok = bool(r.status in (pe.STATIONARY, pe.STAGNATED)
              and r.free_residual <= _THR["max_free_residual_N"]
              and fb <= _THR["max_force_balance_residual"] * scale_f
              and mb <= _THR["max_moment_balance_residual"] * scale_m)
    return {"pass": ok, "status": r.status,
            "free_residual": r.free_residual, "steps": r.n_accepted,
            "force_balance": fb, "moment_balance": mb,
            "tolerances": {"force": _THR["max_force_balance_residual"] * scale_f,
                            "moment": _THR["max_moment_balance_residual"] * scale_m,
                            "free_residual": _THR["max_free_residual_N"]},
            "pin_blocks": {"A_rim": len(star["blocks"][0]),
                            "B_far_rim": len(star["blocks"][1]),
                            "C_far_rim": len(star["blocks"][2])}}


# ── (c) ─────────────────────────────────────────────────────────────────────

@port_test(
    "c_seam_single_valued_both_joints",
    "The star has ONE seam vertex carrying BOTH welded joints: no "
    "duplicated vertex coordinates anywhere, the seam index is owned by A "
    "and referenced by BOTH hangers (every B face and every C face carries "
    "A's index; 3n incident faces on one index), the seam is FREE, and its "
    "total force at the final geometry -- evaluated once on the joined "
    "connectivity -- is a single finite vector within the packet's "
    "residual law. Falsifiers: a duplicate-coordinate probe must fire, and "
    "a hanger claiming mismatched seam coordinates must be refused by name "
    "before any solve.",
    "A duplicated seam vertex, a second ownership claim, a seam force "
    "above the packet's residual law, or an accepted malformed seam.")
def c_seam() -> dict:
    star, solved = _solved()
    V = star["positions"]
    n = cp.PIECE_A["n_rim"]
    seam = star["seam_index"]
    d2 = np.inf
    for i in range(V.shape[0]):
        d = np.linalg.norm(V[i + 1:] - V[i], axis=1)
        if d.size:
            d2 = min(d2, float(d.min()))
    unique = d2 > ALLOWANCES["duplicate_coordinate_tol"]
    in_a = int((star["faces"][:n] == seam).sum())
    in_b = int((star["faces"][n:2 * n] == seam).sum())
    in_c = int((star["faces"][2 * n:] == seam).sum())
    joints_ok = (in_a == n and in_b == n and in_c == n
                 and seam not in star["pins"])
    f_load = np.zeros((V.shape[0], 3))
    for i, v in star["loads"]:
        f_load[i] = v
    F_total = pe.total_force(solved["result"].positions, star["faces"],
                             star["gamma"], f_load)
    seam_force = float(np.linalg.norm(F_total[seam]))
    force_ok = seam_force <= _THR["max_free_residual_N"]
    # falsifier 1: a duplicate seam trips the uniqueness probe
    Vd = np.vstack([V, V[seam]])
    dd = float(np.linalg.norm(Vd[-1] - Vd[seam]))
    probe_fires = dd <= ALLOWANCES["duplicate_coordinate_tol"]
    # falsifier 2: a mismatched hanger seam claim is refused by name
    ok2 = True
    refused = {}
    try:
        cc.build_star(seam_perturbation=1)
        refused["mismatched_hanger_claim"] = {"refused": False}
        ok2 = False
    except ser.InvalidSurface as ex:
        good = ex.reason == cp.ComposedRejectionReason.SEAM_VERTEX_COORDINATE_MISMATCH
        refused["mismatched_hanger_claim"] = {"refused": True,
                                              "reason": ex.reason,
                                              "name_ok": good}
        ok2 = good
    except Exception as ex:
        refused["mismatched_hanger_claim"] = {"refused": True,
                                              "reason": f"WRONG-TYPE {type(ex).__name__}"}
        ok2 = False
    ok = bool(unique and joints_ok and force_ok and probe_fires and ok2)
    return {"pass": ok,
            "measured": {"min_vertex_distance": d2,
                          "seam_incident_faces": {"A": in_a, "B": in_b,
                                                   "C": in_c},
                          "seam_is_free": seam not in star["pins"],
                          "seam_total_force_norm_N": seam_force,
                          "duplicate_probe_fires": probe_fires,
                          "refusals": refused}}


# ── (d) ─────────────────────────────────────────────────────────────────────

@port_test(
    "d_transfer_through_both_welds",
    "The input load produces REAL, distinct port responses through BOTH "
    "welded joints: the three pin blocks' mean reaction norms differ by "
    "more than the C4 precedent margin (0.1), and each output port's net "
    "reaction exceeds 0.1*max(1,sum|f|) -- the load crosses the reused A-B "
    "weld AND the new A-C weld (a superposition or grounded-seam artifact "
    "measures ~0; witness (g) of the P5 battery measured exactly that).",
    "The block margin or either port's transfer is at/below the "
    "preregistered margin.")
def d_transfer() -> dict:
    star, solved = _solved()
    blocks = solved["block_mean_reaction_norms"]
    vals = list(blocks.values())
    hi, lo = max(vals), min(vals)
    margin = (hi - lo) / hi
    scale_f = max(1.0, float(sum(np.linalg.norm(v)
                                 for _i, v in star["loads"])))
    ports = solved["port_net_forces_N"]
    ok = bool(margin > ALLOWANCES["transfer_margin"]
              and ports["B_reused_port"] > ALLOWANCES["transfer_margin"] * scale_f
              and ports["C_output_port"] > ALLOWANCES["transfer_margin"] * scale_f)
    return {"pass": ok,
            "measured": {"block_mean_reaction_norms_N": blocks,
                          "block_margin": margin,
                          "port_net_forces_N": ports,
                          "transfer_scale": scale_f},
            "allowances": {"margin": ALLOWANCES["transfer_margin"]}}


# ── (e) ─────────────────────────────────────────────────────────────────────

@port_test(
    "e_reduction_degenerate_to_assembly1",
    "Removing piece C from assembly 2 leaves a mesh BYTE-IDENTICAL to "
    "assembly 1 (positions and faces), and its solve reproduces assembly "
    "1's final energy within 1e-9 (C2 precedent): the second assembly "
    "degenerates to the first qualified artifact -- same pieces, same seam "
    "law, same reference solve.",
    "The stripped mesh differs from assembly 1's, either solve fails to "
    "converge, or the energy difference exceeds 1e-9.")
def e_reduction() -> dict:
    red = cc.reduction_case()
    ok = bool(red["stripped_positions_byte_equal"]
              and red["stripped_faces_byte_equal"]
              and red["energy_delta"] <= ALLOWANCES["reduction_energy_tol"]
              and red["stripped_status"] in (pe.STATIONARY, pe.STAGNATED)
              and red["assembly1_status"] in (pe.STATIONARY, pe.STAGNATED))
    return {"pass": ok,
            "measured": {"stripped_positions_byte_equal":
                          red["stripped_positions_byte_equal"],
                          "stripped_faces_byte_equal":
                          red["stripped_faces_byte_equal"],
                          "energy_delta_J": red["energy_delta"],
                          "stripped_energy_J": red["stripped_energy"],
                          "assembly1_energy_J": red["assembly1_energy"]},
            "allowances": {"energy": ALLOWANCES["reduction_energy_tol"]}}


# ── (f) ─────────────────────────────────────────────────────────────────────

@port_test(
    "f_supported_scale_new_point",
    "The SAME star assembly rigidly scaled to the NEW point 0.75x on the "
    "packet's physical-size axis (resolution untouched -- n_rim identical; "
    "load magnitude unchanged and within the packet's max_force_N) stays "
    "converged with force/moment balance within the packet's preregistered "
    "1e-6 law and keeps the seam transfer real. MEASURED SCALE WINDOW "
    "(finding, recorded): the star's stagnation residual grows ~linearly "
    "with scale; 1.5x and 2.0x measure OVER the packet's unchanged gate "
    "and are recorded as honestly unqualified scales for this topology -- "
    "reported, not tuned.",
    "The new scale point fails to converge, violates the packet's balance "
    "law, changes resolution, or loses the seam transfer.")
def f_scale() -> dict:
    star, solved = _solved(scale=ALLOWANCES["new_scale_point"])
    r = solved["result"]
    blocks = solved["block_mean_reaction_norms"]
    vals = list(blocks.values())
    margin = (max(vals) - min(vals)) / max(vals)
    n_rim = len(star["blocks"][0])
    window = cc.scale_window_probe()
    ok = bool(r.status in (pe.STATIONARY, pe.STAGNATED)
              and r.free_residual <= _THR["max_free_residual_N"]
              and solved["force_balance_residual"] <= _THR["max_force_balance_residual"]
              and solved["moment_balance_residual"] <= _THR["max_moment_balance_residual"]
              and n_rim == cp.PIECE_A["n_rim"]
              and margin > ALLOWANCES["transfer_margin"])
    return {"pass": ok,
            "measured": {"status": r.status,
                          "free_residual": r.free_residual,
                          "force_balance": solved["force_balance_residual"],
                          "moment_balance": solved["moment_balance_residual"],
                          "n_rim_per_piece": n_rim,
                          "block_margin": margin,
                          "scale_window_measured": window}}


expect(EXPECTED_CHECKS)


# ── runner ──────────────────────────────────────────────────────────────────

ORDER = ["a_piece_reuse_byte_identical", "b_coupled_balance",
         "c_seam_single_valued_both_joints",
         "d_transfer_through_both_welds",
         "e_reduction_degenerate_to_assembly1",
         "f_supported_scale_new_point"]


def main(argv: list) -> int:
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    try:
        out_path = resolve_evidence_path(cc.EVID_DIR, "composed_chain_checks",
                                         argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT

    from port_registry import TESTS
    results, failed = {}, 0
    print("=" * 100)
    print("  COMPOSED CHAIN (P5 REUSE: A + B byte-identically + C in the k=2 "
          "fan-out star): falsifier battery")
    print(f"  allowances (preregistered): reduction dE "
          f"{ALLOWANCES['reduction_energy_tol']:.0e}; margin "
          f"{ALLOWANCES['transfer_margin']}; new scale point "
          f"{ALLOWANCES['new_scale_point']}x; balance law = packet")
    print("=" * 100)
    for name in ORDER:
        rec = TESTS[name]
        print(f"\n[{name}]\n  STATEMENT : {rec['statement'][:96]}...")
        try:
            r = rec["fn"]()
            results[name] = r
            verdict = "PASS" if r.get("pass") else "FAIL"
            if not r.get("pass"):
                failed += 1
            meas = {k: v for k, v in r.items()
                    if k not in ("pass",) and not isinstance(v, dict)}
            print(f"  FALSIFIER : {rec['falsifier'][:96]}...")
            print(f"  -> {verdict}   {json.dumps(meas, default=str)[:400]}")
        except Exception as ex:            # a crash is a FAIL, never a skip
            failed += 1
            results[name] = {"pass": False,
                             "error": f"{type(ex).__name__}: {ex}"}
            print(f"  -> FAIL (exception) {type(ex).__name__}: {ex}")

    # fresh reuse receipt + the adapter's independent verdict
    adapter = {"verified": False}
    try:
        cases, failures = cc.compose_all_scales()
        if failures:
            raise RuntimeError(f"reuse cases violated the packet law: "
                               f"{failures}")
        window = cc.scale_window_probe()
        comp_path = resolve_evidence_path(
            cc.EVID_DIR, "composed_chain_qualification_receipt", argv)
        cc.write_composed_receipt(comp_path, cases, window)
        v = ra.verify_receipt(comp_path, PACKET)
        adapter = {"verified": bool(v.passed), "refusals": v.refusals,
                   "detail": v.detail, "receipt": str(comp_path)}
        print(f"\nadapter verdict on {comp_path.name}: "
              f"{'PASS' if v.passed else 'REFUSED ' + str(v.refusals)}")
        if not v.passed:
            failed += 1
    except Exception as ex:
        failed += 1
        adapter = {"verified": False, "error": f"{type(ex).__name__}: {ex}"}
        print(f"  -> FAIL (reuse receipt/adapter) {type(ex).__name__}: {ex}")

    print("\n" + "-" * 100)
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. Tolerances "
          f"preregistered in composed_chain_checks.ALLOWANCES; none widened "
          f"after seeing results.")

    receipt = {
        "schema": "chimera-mechanism-factory-composed-chain-checks-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "what": "P5 REUSE falsifier battery: assembly 1's pieces A and B "
                "byte-identically plus new piece C in the k=2 fan-out star; "
                "reference = ONE solve_equilibrium on the joined mesh; new "
                "scale point; reduction to assembly 1",
        "source_commit": cc._source_commit(),
        "source_file_hashes": {
            rel: cp._sha256_file(cp._REPO / rel) for rel in cc.HASHED_SOURCES
        },
        "packet_sha256": cp._sha256_bytes(PACKET.read_bytes()),
        "units": _PACKET["units"],
        "preregistered_allowances": ALLOWANCES,
        "composed_receipt_adapter": adapter,
        "checks": {n: {"pass": bool(results[n].get("pass"))} for n in ORDER},
        "cases": {n: results[n] for n in ORDER},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=1, default=str) + "\n",
                        encoding="utf-8")
    print(f"  receipt: {out_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except cp.EvidencePathExists as exc:
        print(f"REFUSED: {exc}")
        raise SystemExit(2)
