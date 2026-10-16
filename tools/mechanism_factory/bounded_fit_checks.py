"""bounded_fit_checks.py -- falsifier battery for the §11.18 P3 bounded
fitting/evaluation entrypoint (bounded_fit.py).

Seven checks through the house harness (tools/port_registry.py), all
tolerances preregistered below BEFORE any run:

  T1 determinism: fit on the same adapter-PASSed receipts twice -> the
     identical table hash (canonical-form sha256).
  T2 unqualified receipt refused: the superseded schema-v1 qualification
     receipt is run through the adapter, refused, recorded as
     receipt_unqualified and contributes NO labels (table hash unchanged
     vs. the clean fit).
  T3 holdout sentinel untouched: a copy of the genuine v2 receipt is
     planted with an adapter-PASSable holdout-family case whose reactions
     carry the sentinel value 777.0; the fit's split gate must exclude it
     structurally: table hash unchanged, no sentinel case ID or sentinel
     reaction value anywhere in the table, holdout_cases_read stays 0,
     no_final_test_access stays TRUE.
  T4 out-of-domain refused by name: unknown family and over-admitted load
     magnitude (|f| > admitted max_force_N) both raise
     refusal_out_of_domain; a valid in-domain query is accepted.
  T5 table error vs reference: on the validation cases the table's max
     reaction error is within the preregistered tolerance (the packet's
     own max_force_balance_residual). If it exceeds the threshold that is
     a REAL FINDING: reported, never widened.
  T6 fit-receipt honesty: the receipt records seed, normalization,
     split usage, table hash (recomputed and matched), wall-time/peak-RAM
     cost, and no_final_test_access true; the learned-candidate hook is
     exposed with its gate-consistent named reason.
  T7 interpolation gate consistency: the bounded table is either
     qualified at the preregistered leave-one-out gate (1e-6 N, the
     reference's own error scale) or explicitly REJECTED at it in the
     fit receipt with the learned-candidate hook flipped -- never
     silently passed. The measured error is recorded as data either way.

Run:  python tools/mechanism_factory/bounded_fit_checks.py
      exit 0 = all PASS, 1 = a check failed, 2 = evidence-path refusal.
CPU only. The lab and the pinned writer are imported read-only.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
_REPO = _TOOLS.parent
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_TOOLS / "membrane_scale_lab"))
sys.path.insert(0, str(_HERE))

from port_registry import port_test, expect        # noqa: E402  house harness
import bounded_fit as bf                           # noqa: E402  under test
import receipt_adapter as ra                       # noqa: E402

# Preregistered allowances, frozen before any run. The table-error tolerance
# is the PACKET's own force-balance threshold -- the same machine-scale
# floor; nothing here may be widened after seeing results.
ALLOW = {
    "max_validation_reaction_error_N":
        None,   # filled from the packet below (1e-6); kept packet-derived
}

PACKET = json.loads(bf.PACKET_PATH.read_text(encoding="utf-8"))
ALLOW["max_validation_reaction_error_N"] = float(
    PACKET["acceptance_thresholds"][bf.TABLE_ERROR_TOLERANCE_KEY])
# Preregistered BEFORE any multi-point run: the bounded table's off-point
# (interpolation) gate. Justification: the reference's OWN error scale --
# the solver's machine-scale stagnation floor gives balance residuals
# ~3e-8 N and the packet's force-balance threshold (the fit tolerance
# above) is 1e-6 N; an interpolant over adapter-verified reference labels
# must not err beyond the scale of the references it interpolates. NOT
# widened after seeing results; if the measured curve exceeds it, that is
# a REAL FINDING (reported per knot, nothing widened).
ALLOW["max_interpolation_error_N"] = 1e-6
EXPECTED_CHECKS = 7
EVID_DIR = bf.EVID_DIR


def _qualified_receipt_paths() -> list:
    """Every stamped qualification receipt the adapter PASSES (sorted)."""
    paths = sorted(str(p) for p in EVID_DIR.glob("qualification_receipt_*.json"))
    ok = [p for p in paths if ra.verify_receipt(p, bf.PACKET_PATH).passed]
    if not ok:
        raise bf.FitRefusal("no_qualified_receipt", {"scanned": paths})
    return ok


def _fit_clean():
    return bf.fit(PACKET, _qualified_receipt_paths())


# ── T1 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T1_deterministic_table",
    "Fitting twice on the same adapter-PASSed receipts produces the "
    "identical bounded table (same canonical-form sha256) and the same "
    "label set -- the pipeline has no hidden nondeterminism.",
    "The two table hashes differ, or the second fit silently changes the "
    "label set.")
def t1_deterministic_table() -> dict:
    r1 = _fit_clean()
    r2 = _fit_clean()
    h1 = r1["table"]["table_sha256"]
    h2 = r2["table"]["table_sha256"]
    ok = h1 == h2 and h1 == bf.build_table(PACKET, r1)["table_sha256"]
    return {"pass": bool(ok), "table_hash": h1, "repeat_hash": h2,
            "n_families": len(r1["labels"])}


# ── T2 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T2_unqualified_receipt_refused",
    "A superseded schema-v1 qualification receipt is run through the "
    "adapter, refused (receipt_schema_unsupported), recorded under "
    "receipt_unqualified, and contributes NO label: the table fitted with "
    "and without it is byte-identical.",
    "An unqualified receipt becomes a label source, is silently skipped "
    "without a named refusal, or changes the table.")
def t2_unqualified_receipt_refused(tmp: Path) -> dict:
    stale = sorted(p for p in EVID_DIR.glob("qualification_receipt_*.json")
                   if not ra.verify_receipt(p, bf.PACKET_PATH).passed)
    if not stale:
        raise bf.FitRefusal("no_unqualified_receipt_to_test",
                            {"note": "expected a retained stale receipt"})
    r_with = bf.fit(PACKET, [str(stale[0])] + _qualified_receipt_paths())
    r_without = _fit_clean()
    ref = [x for x in r_with["schema_fields"]["refused_receipts"]
           if x["reason"] == "receipt_unqualified"
           and x["receipt"] == str(stale[0])]
    h_with = r_with["table"]["table_sha256"]
    h_without = r_without["table"]["table_sha256"]
    ok = bool(ref) and h_with == h_without
    return {"pass": bool(ok), "stale_receipt": stale[0].name,
            "adapter_refusals": ref[0]["adapter_refusals"] if ref else None,
            "table_hash_with": h_with, "table_hash_without": h_without}


# ── T3 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T3_holdout_sentinel_untouched",
    "A holdout-family case with sentinel reactions 777.0 is planted into a "
    "receipt copy the adapter PASSES (the family is in the packet's frozen "
    "splits, the recorded residuals are within thresholds): the fit's "
    "split gate must exclude it BEFORE any output read -- table hash "
    "unchanged, no sentinel case ID or sentinel reaction value in the "
    "table, holdout_cases_read == 0, "
    "no_final_test_access stays TRUE.",
    "The sentinel value reaches the table, the table hash changes, the "
    "holdout read counter increments, or no_final_test_access flips.")
def t3_holdout_sentinel_untouched(tmp: Path) -> dict:
    genuine = _qualified_receipt_paths()[0]
    sent = tmp / "sentinel_receipt.json"
    data = json.loads(Path(genuine).read_text(encoding="utf-8"))
    holdout_family = PACKET["frozen_splits"]["holdout"][0]
    data["cases"].append({
        "case_id": "SENTINEL_holdout_case",
        "family": holdout_family,
        "status": "stationary",
        "outputs": {"energy_J": 0.0, "max_free_residual_N": 0.0,
                    "reactions_N": [[777.0, 777.0, 777.0]],
                    "max_force_balance_residual": 0.0,
                    "max_moment_balance_residual": 0.0},
        "gpu_job": None})
    sent.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    v = ra.verify_receipt(sent, bf.PACKET_PATH)
    if not v.passed:
        raise bf.FitRefusal("sentinel_not_adapter_passable",
                            {"refusals": list(v.refusals)})
    # the sentinel receipt carries ALL genuine cases plus the planted one,
    # so the control fit must use exactly the same case set: the genuine
    # receipt alone (NOT the clean multi-receipt fit, whose table now has
    # more knots from the multi-point writer).
    r = bf.fit(PACKET, [str(sent)])
    h_sent = r["table"]["table_sha256"]
    h_clean = bf.fit(PACKET, [genuine])["table"]["table_sha256"]
    # STRUCTURAL probe, not a byte-substring probe: genuine reaction values
    # legitimately contain the digit run "777" (e.g. 0.00889664220777553),
    # so the sentinel is looked for as planted case IDs and exact sentinel
    # reaction values inside the parsed table.
    points = [p for entry in r["table"]["families"].values()
              for p in entry["points"]]
    sentinel_ids = [p["case_id"] for p in points
                    if "SENTINEL" in str(p.get("case_id") or "")]
    sentinel_reactions = [[v for v in row]
                          for p in points for row in (p["reactions_N"] or [])]
    sentinel_value_present = any(
        abs(v - 777.0) <= 0.0
        for row in sentinel_reactions for v in row)
    sf = r["schema_fields"]
    ok = (h_sent == h_clean
          and not sentinel_ids
          and not sentinel_value_present
          and sf["split_usage"]["holdout_cases_read"] == 0
          and sf["split_usage"]["holdout_cases_seen"] >= 1
          and sf["no_final_test_access"] is True)
    return {"pass": bool(ok), "table_hash_unchanged": h_sent == h_clean,
            "sentinel_case_ids_in_table": sentinel_ids,
            "sentinel_reaction_value_present": sentinel_value_present,
            "holdout_cases_seen": sf["split_usage"]["holdout_cases_seen"],
            "holdout_cases_read": sf["split_usage"]["holdout_cases_read"],
            "no_final_test_access": sf["no_final_test_access"]}


# ── T4 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T4_out_of_domain_refused",
    "Queries outside the admitted domain are refused by name, never "
    "silently extrapolated: an unknown family and a load above the "
    "packet's admitted max_force_N both raise refusal_out_of_domain; a "
    "valid in-domain query is accepted.",
    "An out-of-domain query returns a value, is refused under the wrong "
    "name, or a valid query is refused.")
def t4_out_of_domain_refused() -> dict:
    table = _fit_clean()["table"]
    rows, ok = {}, True
    try:
        bf.predict(table, PACKET, "twisted_torus", np.zeros(3))
        rows["unknown_family"] = {"refused": False}
        ok = False
    except bf.FitRefusal as ex:
        rows["unknown_family"] = {"refused": True, "reason": ex.reason,
                                  "name_ok": ex.reason == "refusal_out_of_domain"}
        ok = ok and rows["unknown_family"]["name_ok"]
    try:
        bf.predict(table, PACKET, PACKET["frozen_splits"]["train"][0],
                   np.array([0.0, 0.0, 3.0]))          # > admitted 2.0 N
        rows["over_admitted_load"] = {"refused": False}
        ok = False
    except bf.FitRefusal as ex:
        rows["over_admitted_load"] = {"refused": True, "reason": ex.reason,
                                      "name_ok": ex.reason == "refusal_out_of_domain"}
        ok = ok and rows["over_admitted_load"]["name_ok"]
    fam = PACKET["frozen_splits"]["train"][0]
    mag = bf._load_magnitude(fam)
    pred = bf.predict(table, PACKET, fam, np.array([0.0, 0.0, mag]))
    rows["valid_control"] = {"refused": False,
                             "source": pred["source"],
                             "reactions_shape": np.asarray(
                                 pred["reactions_N"]).shape}
    return {"pass": bool(ok), "cases": rows}


# ── T5 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T5_validation_error_within_tolerance",
    "On the validation cases the bounded table's max reaction error vs the "
    "adapter-verified direct reference solve is within the preregistered "
    "tolerance (the packet's own max_force_balance_residual). A larger "
    "error is a REAL FINDING: the check fails, nothing is widened.",
    "The validation max reaction error exceeds the preregistered "
    "tolerance, or the evaluation is missing the validation split.")
def t5_validation_error_within_tolerance() -> dict:
    r = _fit_clean()
    ev = r["eval"]
    tol = ALLOW["max_validation_reaction_error_N"]
    val_cases = [c for c in ev["cases"] if c["split"] == "validation"]
    ok = (bool(val_cases)
          and ev["validation_max_reaction_error_N"] <= tol
          and ev["within_tolerance"])
    return {"pass": bool(ok),
            "validation_max_reaction_error_N":
                ev["validation_max_reaction_error_N"],
            "validation_mean_reaction_error_N":
                ev["validation_mean_reaction_error_N"],
            "tolerance_N": tol,
            "n_validation_cases": len(val_cases),
            "finding_note": None if ok else
                "REAL FINDING: table error above the packet threshold on "
                "validation; reported, not widened"}


# ── T6 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T6_fit_receipt_honesty",
    "The fit receipt records the P3 fields honestly: seed, normalization, "
    "split usage (fit/evaluation = train+validation; holdout excluded), a "
    "table hash that recomputes from the emitted table, wall-time and "
    "traced-RAM cost, no_final_test_access TRUE backed by "
    "holdout_cases_read == 0, and the learned-candidate hook exposed with "
    "its named refusal learned_candidate_not_justified.",
    "Any P3 field is missing, the recorded hash does not recompute, cost "
    "is absent or non-positive, or the hook is silently skipped.")
def t6_fit_receipt_honesty() -> dict:
    paths = _qualified_receipt_paths()
    r = _fit_clean()
    receipt = bf.build_receipt(PACKET, r, paths)
    recomputed = bf._sha256_bytes(
        bf._canonical(receipt["table"]["families"]))
    # build_receipt flattens the P3 fields at top level
    ev = receipt.get("evaluation", {})
    err = max(ev.get("validation_max_reaction_error_N", 0.0),
              ev.get("interpolation_error", {}).get(
                  "max_reaction_error_N", 0.0))
    thr = float(PACKET["acceptance_thresholds"]
                [bf.TABLE_ERROR_TOLERANCE_KEY])
    expected_reason = ("learned_candidate_not_justified" if err <= thr
                       else "learned_candidate_deferred_gpu_seam")
    lc = receipt.get("learned_candidate", {})
    checks = {
        "seed_recorded": receipt.get("seed") == bf.FIT_SEED,
        "normalization_recorded": bool(receipt.get("normalization", {}).get(
            "world_unit")),
        "split_usage_recorded": (receipt.get("split_usage", {}).get("fit")
                                 == ["train", "validation"]
                                 and receipt.get("split_usage", {}).get(
                                     "holdout_cases_read") == 0),
        "table_hash_recomputes": receipt.get("table_hash") == recomputed
        and receipt.get("table_hash") == receipt["table"]["table_sha256"],
        "cost_recorded": (receipt.get("cost", {}).get("wall_time_s", 0.0) > 0.0
                          and receipt.get("cost", {}).get(
                              "python_traced_peak_mib", 0.0) > 0.0),
        "no_final_test_access_true":
            receipt.get("no_final_test_access") is True,
        "learned_candidate_hook_named":
            lc.get("status") in ("refused", "deferred")
            and lc.get("reason") == expected_reason,
    }
    ok = all(checks.values())
    return {"pass": bool(ok), "fields": checks,
            "table_hash": receipt.get("table_hash"),
            "learned_candidate": lc.get("reason"),
            "expected_reason": expected_reason}


# ── T7 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T7_interpolation_gate_consistency",
    "GATE CONSISTENCY, not a win assertion: the bounded table is EITHER "
    "qualified (measured leave-one-off max error <= the preregistered "
    "1e-6 N gate, the reference's own error scale) OR explicitly REJECTED "
    "at that gate in the fit receipt with the learned-candidate hook "
    "flipped (learned_candidate_deferred_gpu_seam). The measured error is "
    "recorded as data either way. A system that silently passes an "
    "over-gate table -- or flips the hook without recording the "
    "rejection -- trips this check. Nothing is widened.",
    "The measured leave-one-out error exceeds the gate but no rejection "
    "is recorded / the hook did not flip; or the table qualifies while "
    "the receipt still records a rejection or a flipped hook.")
def t7_interpolation_gate_consistency() -> dict:
    r = _fit_clean()
    receipt = bf.build_receipt(PACKET, r, _qualified_receipt_paths())
    loo = r["eval"]["interpolation_error"]
    loo_max = loo["max_reaction_error_N"]
    gate = ALLOW["max_interpolation_error_N"]
    status = (receipt.get("table_status") or {}).get("status")
    hook = (receipt.get("learned_candidate") or {}).get("reason")
    wins = loo_max <= gate
    qualified_branch = (wins and status == "qualified"
                        and hook == "learned_candidate_not_justified")
    rejected_branch = ((not wins)
                       and status == "rejected_at_preregistered_tolerance"
                       and hook == "learned_candidate_deferred_gpu_seam")
    ok = qualified_branch != rejected_branch and (qualified_branch
                                                  or rejected_branch)
    return {"pass": bool(ok),
            "measured_max_interpolation_error_N": loo_max,
            "gate_N": gate,
            "table_status": status,
            "learned_candidate": hook,
            "per_family_curve_N": {
                f: [(e["load_magnitude_N"], e["max_reaction_error_N"])
                    for e in d.get("per_knot", [])]
                for f, d in loo["families"].items() if d.get("gated")},
            "finding_note": None if wins else
                "REAL FINDING: the bounded table does not reach the "
                "reference's own error scale; REJECTED at the "
                "preregistered gate, measured curve recorded, nothing "
                "widened; learned candidate justified (GPU-batch seam)"}


expect(EXPECTED_CHECKS)


# ── runner (evidence law, like patch_equilibrium_checks.main) ───────────────

ORDER = ["T1_deterministic_table", "T2_unqualified_receipt_refused",
         "T3_holdout_sentinel_untouched", "T4_out_of_domain_refused",
         "T5_validation_error_within_tolerance", "T6_fit_receipt_honesty",
         "T7_interpolation_gate_consistency"]


def main(argv: list) -> int:
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    try:
        out_path = resolve_evidence_path(EVID_DIR, "bounded_fit_checks", argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT

    from port_registry import TESTS
    results, failed = {}, 0
    tmp = Path(tempfile.mkdtemp(prefix="fit_checks_tmp_"))
    print("=" * 100)
    print("  BOUNDED FIT / EVALUATION entrypoint: falsifier battery")
    print(f"  allowances (preregistered): validation reaction error <= "
          f"{ALLOW['max_validation_reaction_error_N']:.0e} N "
          f"(packet {bf.TABLE_ERROR_TOLERANCE_KEY}); interpolation "
          f"(leave-one-out) error <= {ALLOW['max_interpolation_error_N']:.0e} N "
          f"(reference's own error scale)")
    print("=" * 100)
    try:
        for name in ORDER:
            rec = TESTS[name]
            print(f"\n[{name}]\n  STATEMENT : {rec['statement'][:96]}...")
            try:
                fn = rec["fn"]
                r = fn(tmp) if name == "T2_unqualified_receipt_refused" or \
                    name == "T3_holdout_sentinel_untouched" else fn()
                results[name] = r
                verdict = "PASS" if r.get("pass") else "FAIL"
                if not r.get("pass"):
                    failed += 1
                meas = {k: v for k, v in r.items() if k != "pass"
                        and not isinstance(v, dict)}
                print(f"  FALSIFIER : {rec['falsifier'][:96]}...")
                print(f"  -> {verdict}   {json.dumps(meas, default=str)[:400]}")
            except Exception as ex:        # a crash is a FAIL, never a skip
                failed += 1
                results[name] = {"pass": False,
                                 "error": f"{type(ex).__name__}: {ex}"}
                print(f"  -> FAIL (exception) {type(ex).__name__}: {ex}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n" + "-" * 100)
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. Tolerances "
          f"preregistered in bounded_fit_checks.ALLOW; none widened after "
          f"seeing results.")

    checks_receipt = {
        "schema": "chimera-mechanism-factory-fit-checks-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "fit_schema": bf.FIT_SCHEMA,
        "tolerances": dict(ALLOW),
        "checks": {n: {"pass": bool(results[n].get("pass")),
                       "measured": {k: v for k, v in results[n].items()
                                    if k != "pass"}}
                   for n in ORDER},
        "all_passed": failed == 0,
    }
    out_path.write_text(json.dumps(checks_receipt, indent=2,
                                   default=str) + "\n", encoding="utf-8")
    print(f"  receipt: {out_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
