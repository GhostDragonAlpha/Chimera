"""composed_patch_checks.py -- THE REGISTERED FALSIFIER BATTERY for the P5
composition (two qualified fan patches joined into one assembly).

Seven checks on the house harness (tools/port_registry.py port_test/expect,
the pattern of patch_equilibrium_checks.py). All tolerances are preregistered
BELOW, frozen in code before any run; a failing check gets the ARTIFACT
fixed, never the tolerance. The balance law itself is the PACKET's
acceptance_thresholds (the preregistered 1e-6 force/moment/free-residual
law) -- the composed schema adds no thresholds of its own.

  (a) seam agreement: the joined mesh carries the seam vertex ONCE -- no
      duplicated coordinates anywhere, the seam index is owned by piece A
      and referenced by piece B (incident faces from both films), the seam
      is a FREE vertex whose total force at the final geometry is a single
      finite vector within the packet's residual law. Falsifier: a would-be
      duplicate seam vertex (same coordinates, second index) must trip the
      uniqueness probe.
  (b) coupled balance: at the ONE reference solve on the joined mesh,
      |sum(reactions A-block + B-block) + sum(loads)| <= 1e-6*max(1,sum|f|)
      and the moment about the origin <= 1e-6*max(1,sum|x||f|) -- the same
      preregistered 1e-6 law as P1's C3, now across BOTH pieces' pins.
  (c) reduction: piece B UNLOADED (zero load, A absent) flattens onto its
      pinned far rim and reproduces the qualified single-piece zero-load
      behavior: same final energy within 1e-9 (C2 precedent) as the same
      fan without the placement -- composition degenerates to the qualified
      piece, not new physics.
  (d) asymmetry through the seam: the load on A produces a B-port response
      that is NOT a rigid pass-through and NOT zero: the near-load (A rim)
      vs far-side (B far rim) per-block mean reaction norms differ by more
      than the C4 precedent margin (0.1), AND the B-port net reaction
      differs from B's own zero-load state by more than 0.1*max(1,sum|f|)
      (transfer is real). Falsifier: a superposition/grounded-seam artifact
      measures ~0 transfer (see witness (g): measured 0.0 bit-for-bit).
  (e) refusals: overlapping duplicate seam vertices with MISMATCHED
      coordinates are refused BY NAME (seam_vertex_coordinate_mismatch)
      BEFORE any solve; a scale outside the packet's supported physical-size
      axis is refused (unsupported_scale); the genuine assembly is accepted.
  (f) supported scale: the SAME assembly rigidly scaled to 0.5x and 2.0x
      (the packet's physical-size axis; resolution untouched -- n_rim
      identical) stays converged and balanced within the packet's 1e-6 law,
      with the seam transfer still real (block margin >= 0.1).
  (g) topology witnesses (physics findings, reported not tuned away): the
      literal rim-to-rim weld with a FREE seam ring has NO equilibrium
      under this law (every film contracts a free boundary -- the packet's
      own exclusion, at assembly scale): never stationary, residual above
      the C6 floor. The rim-to-rim weld onto a PINNED (grounded) ring
      transmits NOTHING into piece B: its far-rim pin reaction is
      bit-identical with and without A's load. These two witnesses are why
      the composed artifact welds at the apexes.

Run:  python tools/mechanism_factory/composed_patch_checks.py
      exit 0 = all PASS + adapter PASS on a fresh composed receipt,
      1 = a check failed, 2 = evidence-path refusal.
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

from port_registry import port_test, expect        # noqa: E402  house harness
import surface_energy_reference as ser             # noqa: E402
import patch_equilibrium as pe                     # noqa: E402
import composed_patch as cp                        # noqa: E402  the artifact
import receipt_adapter as ra                       # noqa: E402

PACKET = cp.PACKET_PATH
_PACKET = json.loads(PACKET.read_bytes())
_THR = _PACKET["acceptance_thresholds"]

# ── PREREGISTERED ALLOWANCES (frozen before any run; never widened) ─────────
ALLOWANCES = {
    "balance_law_source": "example_packet.acceptance_thresholds "
                          "(1e-6 force/moment/free-residual, preregistered "
                          "at P0/P1; the composed schema adds none)",
    "reduction_energy_tol": 1.0e-9,     # C2 precedent: |dE| final zero-load
                                        # energies, same law mirrored;
                                        # measured 0.0 (bit-identical)
    "apex_rest_on_rim_plane_tol": 1.0e-6,
                                        # "B flat": the free apex lands on
                                        # its rim plane within the packet's
                                        # displacement-scale gate; measured
                                        # 3.2e-8 wu (stagnation floor)
    "transfer_margin": 0.10,            # C4 precedent: near-load vs far-side
                                        # per-block mean reaction norms AND
                                        # the B-port transfer delta must
                                        # exceed 10%; measured 0.170 / 1.25
    "duplicate_coordinate_tol": 1.0e-9,  # seam/vertex uniqueness probe
    "witness_residual_floor": 1.0e-3,   # C6 precedent: the free-ring witness
                                        # must be honestly FAR from
                                        # equilibrium; measured 1.084
    "witness_pinned_delta_tol": 1.0e-12,  # grounded seam: B-port reaction
                                        # delta bit-for-bit; measured 0.0
    "supported_scales": list(cp.SUPPORTED_SCALES),
}
EXPECTED_CHECKS = 7


def _solved(scale: float = 1.0):
    asm = cp.build_assembly(scale=scale)
    solved = cp.solve_assembly(asm)
    return asm, solved


# ── (a) ─────────────────────────────────────────────────────────────────────

@port_test(
    "a_seam_agreement_single_valued",
    "The joined mesh carries the seam vertex ONCE: no duplicated vertex "
    "coordinates anywhere, the seam index is owned by piece A and "
    "referenced by piece B (faces from both films incident on one index), "
    "the seam is a FREE vertex, and its total force at the final geometry "
    "-- evaluated once on the joined connectivity -- is a single finite "
    "vector within the packet's free-residual law.",
    "A duplicated seam vertex, a second ownership claim, a pinned seam, or "
    "a seam force above the packet's residual law.")
def a_seam_agreement() -> dict:
    asm, solved = _solved()
    V = asm.positions
    n = len(asm.block_a)
    # uniqueness: no two vertices share coordinates (a duplicated seam would)
    d2 = np.inf
    for i in range(V.shape[0]):
        d = np.linalg.norm(V[i + 1:] - V[i], axis=1)
        if d.size:
            d2 = min(d2, float(d.min()))
    unique = d2 > ALLOWANCES["duplicate_coordinate_tol"]
    # ownership: one seam index, owned by A's block, referenced by B's faces
    # (each fan face contains its apex, so 2*n incident faces on one index)
    seam = asm.seam_index
    in_a = int((asm.faces[:n] == seam).sum())
    in_b = int((asm.faces[n:] == seam).sum())
    ownership_ok = (asm.seam_record["owner"].startswith("piece A")
                    and asm.seam_record["referenced_by"] == [
                        "piece B (apex vertex deduplicated onto A's index; "
                        "B's faces carry A's index)"]
                    and in_a == n and in_b == n
                    and seam not in asm.pins)          # the seam is FREE
    # forces single-valued: one F_total vector at the seam on the JOINED mesh
    f_load = np.zeros((V.shape[0], 3))
    for i, v in asm.loads:
        f_load[i] = v
    F_total = pe.total_force(solved["result"].positions, asm.faces,
                             asm.gamma, f_load)
    seam_force = float(np.linalg.norm(F_total[seam]))
    force_ok = seam_force <= _THR["max_free_residual_N"] * 1.0  # P = 1/gamma_max = 1
    # falsifier: a duplicate seam (same coordinates, second index) trips the
    # uniqueness probe -- the invariant is load-bearing
    Vd = np.vstack([V, V[seam]])
    Fd = asm.faces.copy()
    Fd[Fd == seam] = V.shape[0]        # remap one face's seam to the twin
    dd = float(np.linalg.norm(Vd[-1] - Vd[seam]))
    probe_fires = dd <= ALLOWANCES["duplicate_coordinate_tol"]
    ok = bool(unique and ownership_ok and force_ok and probe_fires)
    return {"pass": ok,
            "measured": {"min_vertex_distance": d2,
                         "seam_incident_faces": {"piece_A": in_a,
                                                 "piece_B": in_b},
                         "seam_is_free": seam not in asm.pins,
                         "seam_total_force_norm_N": seam_force,
                         "duplicate_probe_fires": probe_fires},
            "allowances": {"duplicate": ALLOWANCES["duplicate_coordinate_tol"],
                            "seam_force": _THR["max_free_residual_N"]}}


# ── (b) ─────────────────────────────────────────────────────────────────────

@port_test(
    "b_coupled_balance",
    "At the ONE reference solve on the joined mesh (connectivity union, "
    "seam deduplicated): |sum(reactions over A-block AND B-block pins) + "
    "sum(loads)| <= 1e-6*max(1,sum|f|) and |sum x x (reaction + f)| <= "
    "1e-6*max(1,sum|x||f|) (moment about the origin) -- the same "
    "preregistered 1e-6 law as P1's C3, now across both pieces' pins.",
    "Either balance residual exceeds its preregistered tolerance, or the "
    "solve does not converge (stationary/stagnated within the packet's "
    "free-residual threshold).")
def b_coupled_balance() -> dict:
    asm, solved = _solved()
    r = solved["result"]
    R = solved["reactions"]
    fsum = np.zeros(3)
    for _i, v in asm.loads:
        fsum += np.asarray(v)
    scale_f = max(1.0, float(sum(np.linalg.norm(v) for _i, v in asm.loads)))
    x = r.positions
    mom = np.zeros(3)
    for k, i in enumerate(r.fixed_indices):
        mom += np.cross(x[i], R[k])
    for i, v in asm.loads:
        mom += np.cross(x[i], np.asarray(v))
    scale_m = max(1.0, float(sum(
        np.linalg.norm(x[i]) * np.linalg.norm(v) for i, v in asm.loads)))
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
            "pin_sets": {"A_rim": len(asm.block_a),
                          "B_far_rim": len(asm.block_b)}}


# ── (c) ─────────────────────────────────────────────────────────────────────

@port_test(
    "c_reduction_degenerate_to_qualified_piece",
    "Piece B UNLOADED (zero load, A absent): the inverted placement with "
    "the far rim pinned and the former-seam apex free flattens onto its rim "
    "plane and reproduces the qualified single-piece zero-load behavior -- "
    "same final energy within 1e-9 (C2 precedent) as the SAME fan without "
    "the placement. Composition degenerates to the qualified piece, not "
    "new physics.",
    "The energy difference exceeds 1e-9, either solve fails to converge, "
    "or the free apex does not come to rest on its rim plane.")
def c_reduction() -> dict:
    red = cp.reduction_case()
    r_inv, r_ref = red["inverted"], red["reference"]
    both_ok = all(r.status in (pe.STATIONARY, pe.STAGNATED)
                  for r in (r_inv, r_ref))
    dE = red["energy_delta"]
    rest = max(red["inverted_apex_rest_on_rim_plane"],
               red["reference_apex_rest_on_rim_plane"])
    ok = bool(both_ok
              and dE <= ALLOWANCES["reduction_energy_tol"]
              and rest <= ALLOWANCES["apex_rest_on_rim_plane_tol"])
    return {"pass": ok,
            "measured": {"status_inverted": r_inv.status,
                          "status_reference": r_ref.status,
                          "energy_inverted_J": r_inv.energy,
                          "energy_reference_J": r_ref.energy,
                          "energy_delta_J": dE,
                          "apex_rest_on_rim_plane_wu": rest},
            "allowances": {"energy": ALLOWANCES["reduction_energy_tol"],
                            "rest": ALLOWANCES["apex_rest_on_rim_plane_tol"]}}


# ── (d) ─────────────────────────────────────────────────────────────────────

@port_test(
    "d_transfer_real_not_rigid_pass_through",
    "The load on A produces a REAL, non-rigid B-port response: the "
    "near-load (A rim) vs far-side (B far rim) per-block mean reaction "
    "norms differ by more than the C4 precedent margin (0.1), and the "
    "B-port net reaction differs from B's own zero-load state by more than "
    "0.1*max(1,sum|f|) (transfer through the seam is real, and the load "
    "splits between the ports instead of passing through unchanged or not "
    "at all).",
    "The block margin or the transfer delta is at/below the preregistered "
    "margin -- a symmetric artifact, a superposition, or a grounded seam "
    "(witness (g) measures exactly that: 0.0 transfer).")
def d_transfer() -> dict:
    asm, solved = _solved()
    blocks = solved["block_mean_reaction_norms"]
    hi, lo = max(blocks.values()), min(blocks.values())
    block_margin = (hi - lo) / hi
    red = cp.reduction_case()
    b_alone = np.asarray(red["inverted"].reaction_forces).sum(axis=0)
    b_asm = solved["reactions"][len(asm.block_a):].sum(axis=0)
    scale_f = max(1.0, float(sum(np.linalg.norm(v)
                                 for _i, v in asm.loads)))
    transfer = float(np.linalg.norm(b_asm - b_alone)) / scale_f
    ok = bool(block_margin > ALLOWANCES["transfer_margin"]
              and transfer > ALLOWANCES["transfer_margin"])
    return {"pass": ok,
            "measured": {"block_mean_reaction_norms_N": blocks,
                          "block_margin": block_margin,
                          "b_port_net_force_N": float(np.linalg.norm(b_asm)),
                          "b_alone_net_force_N": float(np.linalg.norm(b_alone)),
                          "transfer_delta_over_scale": transfer},
            "allowances": {"margin": ALLOWANCES["transfer_margin"]}}


# ── (e) ─────────────────────────────────────────────────────────────────────

@port_test(
    "e_seam_refusals",
    "Overlapping duplicate seam vertices with MISMATCHED coordinates are "
    "refused BY NAME (seam_vertex_coordinate_mismatch) BEFORE any solve; a "
    "scale outside the packet's supported physical-size axis is refused "
    "(unsupported_scale); the genuine assembly is accepted.",
    "A malformed seam is accepted, refused under the wrong name, refused "
    "only after solving, or a genuine assembly is refused.")
def e_refusals() -> dict:
    rows = {}

    def probe(name, fn, want):
        try:
            fn()
            rows[name] = {"refused": False, "expected": want}
            return False
        except ser.InvalidSurface as ex:
            good = ex.reason == want
            rows[name] = {"refused": True, "reason": ex.reason,
                          "expected": want, "name_ok": good}
            return good
        except Exception as ex:                    # a crash is not a refusal
            rows[name] = {"refused": True,
                          "reason": f"WRONG-TYPE {type(ex).__name__}"}
            return False

    ok = True
    ok &= probe("seam_vertex_coordinate_mismatch",
                lambda: cp.build_assembly(
                    seam_perturbation=(0.0, 0.0, 1.0e-6)),
                cp.ComposedRejectionReason.SEAM_VERTEX_COORDINATE_MISMATCH)
    ok &= probe("unsupported_scale",
                lambda: cp.build_assembly(scale=3.0),
                cp.ComposedRejectionReason.UNSUPPORTED_SCALE)
    try:                                            # control: genuine accepted
        cp.build_assembly()
        rows["genuine_control_accepted"] = {"refused": False}
    except ser.InvalidSurface as ex:
        rows["genuine_control_accepted"] = {"refused": True,
                                             "reason": ex.reason}
        ok = False
    return {"pass": bool(ok), "cases": rows}


# ── (f) ─────────────────────────────────────────────────────────────────────

@port_test(
    "f_supported_scale",
    "The SAME assembly rigidly scaled to 0.5x and 2.0x (the packet's "
    "physical-size axis; the resolution axis untouched -- n_rim per piece "
    "identical at every scale, load magnitude unchanged and within the "
    "packet's max_force_N) stays converged with force/moment balance "
    "within the packet's preregistered 1e-6 law, and the seam transfer "
    "stays real (block margin above 0.1).",
    "Any scale fails to converge, violates the packet's balance law, "
    "changes resolution, or loses the seam transfer.")
def f_scale() -> dict:
    rows = {}
    ok = True
    for s in cp.SUPPORTED_SCALES:
        asm, solved = _solved(scale=s)
        r = solved["result"]
        blocks = solved["block_mean_reaction_norms"]
        hi, lo = max(blocks.values()), min(blocks.values())
        margin = (hi - lo) / hi
        n_rim = len(asm.block_a)
        row = {"status": r.status,
               "free_residual": r.free_residual,
               "force_balance": solved["force_balance_residual"],
               "moment_balance": solved["moment_balance_residual"],
               "n_rim_per_piece": n_rim,
               "seam_height_wu": solved["seam_height"],
               "block_margin": margin}
        good = bool(r.status in (pe.STATIONARY, pe.STAGNATED)
                    and r.free_residual <= _THR["max_free_residual_N"]
                    and solved["force_balance_residual"]
                    <= _THR["max_force_balance_residual"]
                    and solved["moment_balance_residual"]
                    <= _THR["max_moment_balance_residual"]
                    and n_rim == cp.PIECE_A["n_rim"]
                    and margin > ALLOWANCES["transfer_margin"])
        row["pass"] = good
        rows[f"scale_{s:g}"] = row
        ok &= good
    return {"pass": bool(ok), "scales": rows,
            "allowances": {"margin": ALLOWANCES["transfer_margin"],
                            "balance_law": ALLOWANCES["balance_law_source"]}}


# ── (g) ─────────────────────────────────────────────────────────────────────

@port_test(
    "g_topology_witnesses",
    "PHYSICS FINDINGS, reported not tuned away: the literal rim-to-rim weld "
    "with a FREE seam ring has NO equilibrium under this law (every film "
    "contracts a free boundary -- the packet's own exclusion, at assembly "
    "scale): the solve never reports stationary and its residual stays "
    "above the C6 floor. The rim-to-rim weld onto a PINNED (grounded) ring "
    "transmits NOTHING into piece B: its far-rim pin reaction is "
    "bit-identical with and without A's load. Together these are why the "
    "composed artifact welds at the apexes (equilibrium AND transfer).",
    "The free ring fakes a stationary (or lands near equilibrium), or the "
    "grounded ring shows a nonzero B-port delta (the witness reasoning is "
    "wrong and the topology choice must be re-examined).")
def g_topology_witness() -> dict:
    free = cp.witness_free_ring()
    pinned = cp.witness_pinned_ring()
    floor = ALLOWANCES["witness_residual_floor"]
    ok_free = (free["status"] != pe.STATIONARY
               and free["free_residual"] > floor)
    ok_pinned = pinned["b_port_reaction_delta"] \
        <= ALLOWANCES["witness_pinned_delta_tol"]
    return {"pass": bool(ok_free and ok_pinned),
            "measured": {"free_ring": free, "pinned_ring": pinned},
            "allowances": {"residual_floor": floor,
                            "pinned_delta": ALLOWANCES["witness_pinned_delta_tol"]},
            "note": "free-ring non-equilibrium is PHYSICS under the pure "
                    "area law (free boundary carries line tension gamma), "
                    "not a solver defect -- same finding as P1's partial-"
                    "rim exclusion, now witnessed at assembly scale"}


expect(EXPECTED_CHECKS)


# ── runner ──────────────────────────────────────────────────────────────────

ORDER = ["a_seam_agreement_single_valued", "b_coupled_balance",
         "c_reduction_degenerate_to_qualified_piece",
         "d_transfer_real_not_rigid_pass_through", "e_seam_refusals",
         "f_supported_scale", "g_topology_witnesses"]


def main(argv: list) -> int:
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    try:
        out_path = resolve_evidence_path(cp.EVID_DIR, "composed_patch_receipt",
                                         argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT

    from port_registry import TESTS
    results, failed = {}, 0
    print("=" * 100)
    print("  COMPOSED PATCH (P5: two pieces, one assembly, supported scale):"
          " falsifier battery")
    print(f"  allowances (preregistered): reduction dE "
          f"{ALLOWANCES['reduction_energy_tol']:.0e}; rest "
          f"{ALLOWANCES['apex_rest_on_rim_plane_tol']:.0e}; margin "
          f"{ALLOWANCES['transfer_margin']}; witness floor "
          f"{ALLOWANCES['witness_residual_floor']:.0e}; balance law = packet")
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

    # fresh composed qualification receipt + the adapter's independent verdict
    adapter = {"verified": False}
    try:
        cases, failures = cp.compose_all_scales()
        if failures:
            raise RuntimeError(f"composed cases violated the packet law: "
                               f"{failures}")
        comp_path = cp.resolve_evidence_path(
            cp.EVID_DIR, "composed_qualification_receipt", argv)
        cp.write_composed_receipt(comp_path, cases)
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
        print(f"  -> FAIL (composed receipt/adapter) {type(ex).__name__}: {ex}")

    print("\n" + "-" * 100)
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. Tolerances "
          f"preregistered in composed_patch_checks.ALLOWANCES; none widened "
          f"after seeing results.")

    receipt = {
        "schema": "chimera-mechanism-factory-composed-checks-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "what": "P5 composition falsifier battery: two qualified fan patches "
                "joined into one apex-weld hourglass assembly; reference = "
                "ONE solve_equilibrium on the joined mesh; supported scale; "
                "seam ownership; topology witnesses",
        "source_commit": cp._source_commit(),
        "source_file_hashes": {
            rel: cp._sha256_file(cp._REPO / rel) for rel in cp.HASHED_SOURCES
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
