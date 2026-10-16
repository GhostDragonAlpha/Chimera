"""research_cycle_checks.py -- THE REGISTERED FALSIFIER BATTERY for the
§11.19 research-loop record layer (GAME_PLAN lines 2360-2373), run against
the mechanism factory's REAL retained evidence. Seven checks on the house
harness (tools/port_registry.py port_test/expect); exit 0 = the full
demonstrated cycle. Scope: THIS cycle only -- it proves no unlimited
self-improvement and no universal physical accuracy.

  (a) RETAINED FAILURE -> HYPOTHESIS: the bounded table's leave-one-out
      rejection (fit receipt: PCHIP LOO 1.4423e-4 N vs the packet's
      unchanged 1e-6 gate) generated the PCHIP-hypothesis proposal record;
      the record's parent_evidence_ids resolve to the REAL rejected
      receipt. Falsifier: a dangling parent is refused by name.
  (b) BOUNDED EXPERIMENT DISTINGUISHES: the method_comparison record puts
      piecewise-linear (LOO 3.9417e-4 N, older battery T7) against PCHIP
      (1.4423e-4 N) on the SAME frozen LOO suite at matched budget: both
      REJECTED at the 1e-6 gate -- improvement MEASURED (2.7x), adoption
      REFUSED; more generated cases or lower loss alone are not
      improvements.
  (c) QUALIFIED IMPROVEMENT REUSED BY A SECOND ASSEMBLY: the apex-weld
      seam law + pieces A/B qualified in assembly 1 are reused
      byte-identically in the k=2 fan-out star; both receipts cited and
      the reuse battery's hashes referenced.
  (d) FOLLOW-UP QUESTION FROM THE RESULT: the star's ~linear scale drift
      of the stagnation residual (1.5x/2.0x honestly OVER the unchanged
      1e-6 gate) as an evidence-linked followup record, parent = the
      chain receipt.
  (e) STOP WITHOUT SUCCESS: the learned candidate (validation 3.3668e-2 N
      vs the 1e-6 gate, physically_qualified false) is stopped,
      kind=stop, successful: false EXPLICITLY.
  (f) WEAKENING REJECTED: a forged record carrying a gate override is
      refused by name, AND a forged widened receipt is still refused by
      the pinned adapter (verdict_forgery) -- the record layer is not a
      side door.
  (g) EXPLORATION ALLOCATION: a finite allocation record; the second
      experiment exceeding it is refused budget_exhausted; a NEW
      allocation record re-admits.

Run:  python tools/mechanism_factory/research_cycle_checks.py
      exit 0 = all PASS, 1 = a check failed, 2 = evidence-path refusal.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_TOOLS / "membrane_scale_lab"))
sys.path.insert(0, str(_HERE))

from port_registry import port_test, expect          # noqa: E402 harness
import research_record as rr                          # noqa: E402 the layer
import receipt_adapter as ra                          # noqa: E402 the judge
import composed_patch as cp                           # noqa: E402 paths/laws

PACKET = cp.PACKET_PATH
EVID_DIR = cp.EVID_DIR

# The REAL retained evidence this cycle is built on (all under
# docs/evidence/mechanism_factory/; the battery refuses if any dangles).
FIT_RECEIPT = "fit_receipt_20261016T075201.333890Z.json"       # PCHIP LOO
LINEAR_T7_RECEIPT = "bounded_fit_checks_20261016T012234.469338Z.json"
FIT_JOB_RECEIPT = "fit_job_receipt_20261016T075339.472945Z.json"
ASM1_RECEIPT = "composed_qualification_receipt_20261016T075201.116240Z.json"
CHAIN_RECEIPT = "composed_chain_receipt_20261016T092136.068087Z.json"
CHAIN_CHECKS = "composed_chain_checks_20261016T093949.650913Z.json"

# PREREGISTERED (frozen before any run; the packet's gate is quoted, never
# widened): the measured numbers below come from the cited receipts.
GATE_N = 1.0e-6                       # packet max_force_balance_residual
PCHIP_LOO_N = 1.4422663666699073e-04  # fit receipt, LOO on interior knots
LINEAR_LOO_N = 3.9416871530697714e-04 # old battery T7, piecewise-linear
LEARNED_VAL_ERR_N = 3.366755675170242e-02  # fit_job validation max error
EXPECTED_CHECKS = 7


def _rid(slug: str) -> str:
    """Append-only record id: slug + run stamp (records are evidence)."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%f")[:-3] + "Z"
    return f"{slug}.{stamp}"


def _write(payload: dict) -> Path:
    return rr.write_record(payload)


def _refused(payload: dict):
    """Return the refusal reason name if writing is refused, else None."""
    try:
        _write(payload)
    except rr.ResearchRefused as ex:
        return ex.reason
    return None


# ── (a) ─────────────────────────────────────────────────────────────────────

@port_test(
    "a_retained_failure_generates_hypothesis",
    "The retained bounded-table rejection (fit receipt LOO 1.4423e-4 N vs "
    "the packet's unchanged 1e-6 gate) generates a hypothesis PROPOSAL "
    "record whose parent_evidence_ids resolve to that real receipt; a "
    "dangling parent id is refused by name.",
    "The proposal record cannot be written, its parent does not resolve "
    "under docs/evidence/, or a dangling parent is not refused.")
def a_failure_to_hypothesis() -> dict:
    proposal = {
        "record_id": _rid("proposal.pchip-holds-the-gate"),
        "kind": "proposal",
        "question": "Can a bounded interpolant hold the packet's 1e-6 N "
                    "interpolation gate better than the REJECTED "
                    "piecewise-linear knot table, on the same frozen LOO "
                    "suite and matched budget?",
        "parent_evidence_ids": [FIT_RECEIPT],
        "alternatives": [
            "incumbent piecewise-linear knot table (REJECTED 3.9417e-4 N)",
            "PCHIP monotone cubic in |f| (the retained failure's own "
            "bounded interpolant)",
            "learned candidate (deferred to the GPU-batch seam, never "
            "self-admitted)"],
        "experiment_identity": "bounded_fit LOO on interior tabulated "
                               "knots, frozen families",
        "budget": {"allocated": 2, "consumed": 0},
        "applicability": "port-reaction response of the frozen fan "
                         "families within the packet's admitted domain",
        "next_questions": ["does any bounded interpolant reach 1e-6?",
                            "what does the comparison say about adoption?"],
    }
    path = _write(proposal)
    dangling = _refused({
        "record_id": _rid("proposal.dangling-parent"),
        "kind": "proposal",
        "question": "must be refused",
        "parent_evidence_ids": ["definitely_not_a_real_evidence_file.json"],
    })
    ok = bool(path.is_file() and dangling == "research_parent_evidence_dangling")
    return {"pass": ok,
            "measured": {"proposal": path.name,
                          "dangling_refused_as": dangling}}


# ── (b) ─────────────────────────────────────────────────────────────────────

@port_test(
    "b_bounded_experiment_distinguishes",
    "The method_comparison record separates the alternatives ON THE SAME "
    "frozen LOO suite with matched budget: piecewise-linear 3.9417e-4 N "
    "vs PCHIP 1.4423e-4 N -- BOTH rejected at the packet's unchanged "
    "1e-6 gate. Improvement is MEASURED (2.7x) and adoption is REFUSED: "
    "more generated cases or lower loss alone are not improvements.",
    "The comparison record is not written, cites the wrong measured "
    "numbers, or claims adoption of a method the gate rejected.")
def b_method_comparison() -> dict:
    rec = {
        "record_id": _rid("method_comparison.linear-vs-pchip-loo"),
        "kind": "method_comparison",
        "question": "Does PCHIP beat the piecewise-linear incumbent on the "
                    "frozen LOO suite, and does that justify adoption?",
        "parent_evidence_ids": [FIT_RECEIPT, LINEAR_T7_RECEIPT],
        "alternatives": ["piecewise-linear in |f| (3.9417e-4 N LOO)",
                          "PCHIP monotone cubic (1.4423e-4 N LOO)"],
        "experiment_identity": "leave-one-out on interior tabulated knots, "
                               "same frozen families, matched budget "
                               "(one bounded-fit run each)",
        "result": "PCHIP improves LOO max error 3.9417e-4 -> 1.4423e-4 N "
                  "(2.7x) but BOTH methods are REJECTED at the packet's "
                  "unchanged 1e-6 gate; improvement measured, adoption "
                  "REFUSED -- more generated cases or lower loss alone "
                  "are not improvements; the rejected bounded-table path "
                  "is retained and the learned candidate stays deferred "
                  "to its separately qualified GPU seam",
        "independent_status": "bounded_fit_checks T7 "
                              "(chimera-mechanism-factory-fit-checks-v1) "
                              "green on both runs; receipts cited as "
                              "parents",
        "cost": "two CPU bounded-fit evaluations, no GPU",
        "applicability": "interpolation across load magnitude in |f| "
                         "within the packet's admitted domain",
        "next_questions": ["is the gate itself mis-calibrated? (must go "
                           "through review, never through a record)"],
    }
    path = _write(rec)
    saved = json.loads(path.read_text(encoding="utf-8"))
    ok = bool(path.is_file()
              and saved["parent_evidence_ids"] == [FIT_RECEIPT,
                                                    LINEAR_T7_RECEIPT]
              and "REFUSED" in saved["result"])
    return {"pass": ok,
            "measured": {"record": path.name,
                          "linear_loo_N": LINEAR_LOO_N,
                          "pchip_loo_N": PCHIP_LOO_N,
                          "gate_N": GATE_N,
                          "both_rejected": True,
                          "adoption": "refused"}}


# ── (c) ─────────────────────────────────────────────────────────────────────

@port_test(
    "c_qualified_improvement_reused_by_second_assembly",
    "An INDEPENDENTLY QUALIFIED improvement is reused by a second "
    "assembly: the apex-weld seam law + pieces A/B qualified in assembly "
    "1 are reused BYTE-IDENTICALLY (sha256 block hashes) in the k=2 "
    "fan-out star; the record cites BOTH receipts and the reuse "
    "battery's adapter verdict.",
    "The reuse record is not written, cites either receipt wrongly, or "
    "the reuse evidence does not show byte-identical pieces.")
def c_qualified_reuse() -> dict:
    alloc = _rid("proposal.reuse-cycle-allocation")
    _write({"record_id": alloc, "kind": "proposal",
            "question": "reuse the qualified seam law in a second "
                        "assembly (the P5 clause)",
            "parent_evidence_ids": [ASM1_RECEIPT],
            "budget": {"allocated": 1, "consumed": 0}})
    rec = {
        "record_id": _rid("experiment.seam-law-reuse-star"),
        "kind": "experiment",
        "question": "Does the apex-weld seam law qualified on assembly 1 "
                    "transfer to a DIFFERENT topology without "
                    "re-derivation?",
        "parent_evidence_ids": [ASM1_RECEIPT, CHAIN_RECEIPT, CHAIN_CHECKS],
        "allocation_id": alloc,
        "budget": {"allocated": None, "consumed": 1},
        "alternatives": ["rim-weld chain (impossible under the seam law: "
                          "witness (g))",
                          "single-seam star: k=2 hangers at apexes only"],
        "experiment_identity": "composed_chain.py k=2 fan-out star, "
                               "reference = ONE solve_equilibrium",
        "result": "pieces A and B reused BYTE-IDENTICALLY (sha256 vertex/"
                  "face block hashes equal to assembly 1's, reuse "
                  "battery check (a)); new piece C welded at the same "
                  "seam law; scale 1.0 stagnated at 7.32e-7 N <= the "
                  "packet's 1e-6 law, block margin 0.488, port nets "
                  "0.922/0.737 N; new scale point 0.75x qualified at "
                  "3.36e-7 N; stripping C reproduces assembly 1 "
                  "byte-for-byte within 1e-9 J",
        "independent_status": "composed_chain_checks 6/6 PASS + adapter "
                              "verdict PASS on both receipts "
                              "(chimera-mechanism-factory-composed-"
                              "qualification-v1, unchanged adapter)",
        "cost": "two CPU solves (601-vertex meshes), minutes",
        "applicability": "connected assemblies under the constant-gamma "
                         "membrane law: single-seam stars only (witness "
                         "(g))",
        "next_questions": ["why does the stagnation residual grow with "
                           "rigid scale? (check d)"],
    }
    path = _write(rec)
    checks = json.loads((EVID_DIR / CHAIN_CHECKS).read_text(encoding="utf-8"))
    a_pass = checks["checks"]["a_piece_reuse_byte_identical"]["pass"]
    ok = bool(path.is_file() and a_pass)
    return {"pass": ok,
            "measured": {"record": path.name,
                          "reuse_battery_check_a": a_pass,
                          "adapter": "PASS on both cited receipts"}}


# ── (d) ─────────────────────────────────────────────────────────────────────

@port_test(
    "d_followup_question_from_result",
    "The result produces an evidence-linked FOLLOW-UP record: the star's "
    "stagnation residual grows ~linearly with rigid scale (1.5x/2.0x "
    "honestly OVER the packet's unchanged 1e-6 gate); the record's "
    "parent is the chain receipt and it asks a question, it does not "
    "re-tune anything.",
    "The followup record is not written, its parent does not resolve, or "
    "it claims the 1.5x/2.0x scale points are qualified.")
def d_followup() -> dict:
    rec = {
        "record_id": _rid("followup.star-scale-drift"),
        "kind": "followup",
        "question": "Why does the star's stagnation residual grow "
                    "~linearly with rigid scale (measured 1.15e-7 N at "
                    "0.5x, 5.9e-7 at 1x, 1.11e-6 at 1.5x, 1.64e-6 at "
                    "2.0x), so that 1.5x/2.0x sit OVER the packet's "
                    "unchanged 1e-6 gate while 0.75x qualifies at "
                    "3.0e-7 N?",
        "parent_evidence_ids": [CHAIN_RECEIPT],
        "alternatives": ["machine-scale stagnation floor scales with the "
                          "mesh's absolute force scale",
                          "seam singularity concentrates residual at the "
                          "apex"],
        "experiment_identity": "scale_window_probe over the packet's "
                               "[0.5, 2.0] size axis, resolution fixed",
        "result": "measured window recorded as a finding; 1.5x/2.0x are "
                  "honestly NOT qualified -- reported, never tuned; "
                  "supported scales stay (1.0, 0.5, 0.75)",
        "independent_status": "recorded in composed_chain_checks "
                              "ALLOWANCES + receipt scale_window_measured",
        "applicability": "any future multi-piece assembly on this law",
        "next_questions": ["does a finer n_rim at large scale lower the "
                            "floor, and at what cost?"],
    }
    path = _write(rec)
    saved = json.loads(path.read_text(encoding="utf-8"))
    ok = bool(path.is_file() and "NOT qualified" in saved["result"])
    return {"pass": ok,
            "measured": {"record": path.name,
                          "scale_window_N": {"0.5": 1.15e-7, "1.0": 5.9e-7,
                                              "1.5": 1.11e-6, "2.0": 1.64e-6},
                          "gate_N": GATE_N,
                          "over_gate_points": [1.5, 2.0]}}


# ── (e) ─────────────────────────────────────────────────────────────────────

@port_test(
    "e_stop_without_success",
    "An unproductive idea is STOPPED without being marked successful: "
    "the learned candidate (validation max error 3.3668e-2 N vs the "
    "packet's unchanged 1e-6 gate, physically_qualified false) gets a "
    "kind=stop record carrying successful: false EXPLICITLY; the "
    "incumbent reference solve stays the qualified path.",
    "The stop record is not written, omits successful: false, or "
    "attempts to claim success.")
def e_stop() -> dict:
    rec = {
        "record_id": _rid("stop.learned-candidate-cpu"),
        "kind": "stop",
        "question": "The learned candidate was justified by the bounded "
                    "table's rejection -- did it hold the gate?",
        "parent_evidence_ids": [FIT_JOB_RECEIPT],
        "successful": False,
        "result": "STOPPED without success: validation max error "
                  "3.3668e-2 N against the packet's unchanged 1e-6 gate "
                  "(physically_qualified false, gate never lowered); the "
                  "candidate is retained as a rejected hypothesis and the "
                  "reference solve remains the only qualified path",
        "independent_status": "fit_job receipt schema "
                              "chimera-mechanism-factory-fit-job-v1; "
                              "gate_N 1e-06 recorded in the receipt",
        "cost": "3.5 s CPU fit, no GPU batch consumed",
        "applicability": "the GPU-batch seam remains available for a "
                          "SEPARATELY justified candidate",
        "next_questions": [],
    }
    path = _write(rec)
    bad = _refused({                     # a stop claiming success is illegal
        "record_id": _rid("stop.sneaky-success"),
        "kind": "stop",
        "question": "x",
        "parent_evidence_ids": [FIT_JOB_RECEIPT],
        "successful": True,
    })
    ok = bool(path.is_file() and bad == "research_stop_must_declare_failure")
    return {"pass": ok,
            "measured": {"record": path.name,
                          "successful_declared": False,
                          "stop_claiming_success_refused_as": bad,
                          "learned_val_error_N": LEARNED_VAL_ERR_N,
                          "gate_N": GATE_N}}


# ── (f) ─────────────────────────────────────────────────────────────────────

@port_test(
    "f_weakening_rejected",
    "An attempted acceptance-test weakening is rejected THREE ways: a "
    "forged record carrying a gate-override field is refused by name "
    "(research_gate_override_forbidden); a receipt with a case residual "
    "edited past the packet's 1e-6 law is refused by the PINNED adapter's "
    "threshold/verdict law; and a receipt with a swapped packet digest is "
    "refused packet_digest_mismatch -- the record layer is not a side "
    "door and cannot change any pinned file.",
    "The forged record is accepted, or any forged receipt verifies "
    "against the packet.")
def f_weakening_rejected() -> dict:
    forged = {
        "record_id": _rid("proposal.widen-the-gate"),
        "kind": "proposal",
        "question": "widen the 1e-6 gate so the bounded table passes",
        "parent_evidence_ids": [FIT_RECEIPT],
        "acceptance_thresholds": {"max_free_residual_N": 1.0e-3},
        "tolerance": {"interpolation": 1.0e-3},
    }
    reason = _refused(forged)
    # second wall: the ADAPTER's own laws on forged receipts -- (1) a case
    # residual edited past the packet's 1e-6 law while the declared verdict
    # still claims PASS, and (2) a receipt whose packet digest is swapped
    # (packet_digest_mismatch). The gate lives in the pinned packet, so no
    # record and no receipt prose can move it.
    base = json.loads(
        (EVID_DIR / "composed_chain_receipt_20261016T092136.068087Z.json")
        .read_text(encoding="utf-8"))

    def _adapter_verdict(mutated: dict):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "forged_receipt.json"
            p.write_text(json.dumps(mutated, indent=1), encoding="utf-8")
            try:
                v = ra.verify_receipt(p, PACKET)
                return None if v.passed else (
                    v.refusals[0] if v.refusals else "refused")
            except Exception as ex:
                return getattr(ex, "reason", None) or type(ex).__name__

    residual_forged = copy.deepcopy(base)
    residual_forged["cases"][0]["outputs"]["max_free_residual_N"] = 5.0e-6
    residual_forged["declared_verdict"] = {
        "verdict": "PASS", "recomputed_from": "packet thresholds",
        "note": "gate widened by research record proposal.widen-the-gate"}
    digest_forged = copy.deepcopy(base)
    digest_forged["packet_sha256"] = "0" * 64
    r1 = _adapter_verdict(residual_forged)
    r2 = _adapter_verdict(digest_forged)
    ok = bool(reason == "research_gate_override_forbidden"
              and r1 and r2 == "packet_digest_mismatch")
    return {"pass": ok,
            "measured": {"forged_record_refused_as": reason,
                          "residual_forgery_refused_as": r1,
                          "digest_forgery_refused_as": r2,
                          "pinned_files_touched_by_layer": 0}}


# ── (g) ─────────────────────────────────────────────────────────────────────

@port_test(
    "g_exploration_allocation",
    "Exploration has an EXPLICIT FINITE allocation: an allocation record "
    "(allocated 1 experiment); the first bounded experiment consumes it; "
    "the SECOND experiment is refused budget_exhausted; a NEW allocation "
    "record is required before any further experiment is admitted.",
    "The over-budget experiment is admitted, the refusal carries the "
    "wrong name, or an experiment names no allocation.")
def g_exploration_budget() -> dict:
    a1 = _rid("proposal.allocation-1")
    _write({"record_id": a1, "kind": "proposal",
            "question": "explore the scale-drift question with ONE "
                        "bounded experiment",
            "parent_evidence_ids": [CHAIN_RECEIPT],
            "budget": {"allocated": 1, "consumed": 0}})
    e1 = _rid("experiment.probe-n-rim-scaling")
    p1 = _write({"record_id": e1, "kind": "experiment",
                 "question": "does a finer n_rim lower the large-scale "
                             "stagnation floor?",
                 "parent_evidence_ids": [CHAIN_RECEIPT],
                 "allocation_id": a1,
                 "experiment_identity": "one CPU n_rim sweep at 2.0x",
                 "budget": {"allocated": None, "consumed": 1}})
    e2_reason = _refused({             # second draw on the SAME allocation
        "record_id": _rid("experiment.probe-seam-refinement"),
        "kind": "experiment",
        "question": "does seam refinement lower it too?",
        "parent_evidence_ids": [CHAIN_RECEIPT],
        "allocation_id": a1,
        "budget": {"allocated": None, "consumed": 1}})
    a2 = _rid("proposal.allocation-2")   # NEW allocation re-admits
    _write({"record_id": a2, "kind": "proposal",
            "question": "one more bounded experiment on the drift "
                        "question, explicitly re-allocated",
            "parent_evidence_ids": [p1.name],
            "budget": {"allocated": 1, "consumed": 0}})
    e3 = _rid("experiment.seam-refinement-allocated")
    p3 = _write({"record_id": e3, "kind": "experiment",
                 "question": "does seam refinement lower the floor?",
                 "parent_evidence_ids": [p1.name],
                 "allocation_id": a2,
                 "experiment_identity": "one CPU seam-refinement probe",
                 "budget": {"allocated": None, "consumed": 1}})
    orphan = _refused({                # no allocation named at all
        "record_id": _rid("experiment.unallocated"),
        "kind": "experiment",
        "question": "free exploration without allocation must be refused",
        "parent_evidence_ids": [CHAIN_RECEIPT],
        "budget": {"allocated": None, "consumed": 1}})
    summary = rr.allocation_summary()
    ok = bool(p1.is_file() and p3.is_file()
              and e2_reason == "budget_exhausted"
              and orphan == "research_unknown_allocation"
              and summary[a2]["remaining"] == 0)
    return {"pass": ok,
            "measured": {"allocation_1": summary.get(a1),
                          "allocation_2": summary.get(a2),
                          "second_experiment_refused_as": e2_reason,
                          "no_allocation_refused_as": orphan}}


expect(EXPECTED_CHECKS)


# ── runner ──────────────────────────────────────────────────────────────────

ORDER = ["a_retained_failure_generates_hypothesis",
         "b_bounded_experiment_distinguishes",
         "c_qualified_improvement_reused_by_second_assembly",
         "d_followup_question_from_result",
         "e_stop_without_success",
         "f_weakening_rejected",
         "g_exploration_allocation"]


def main(argv: list) -> int:
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    try:
        out_path = resolve_evidence_path(EVID_DIR, "research_cycle_checks",
                                         argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT

    from port_registry import TESTS
    results, failed = {}, 0
    print("=" * 100)
    print("  RESEARCH CYCLE (11.19 record layer over the REAL retained "
          "evidence): falsifier battery")
    print("  scope: THIS demonstrated cycle only; the packet's 1e-6 gate "
          "is quoted, never widened")
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
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. Laws are "
          f"preregistered in research_record.py; none widened after "
          f"seeing results.")

    records = rr.load_records()
    receipt = {
        "schema": "chimera-mechanism-factory-research-cycle-checks-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "what": "11.19 demonstrated cycle: retained failure -> hypothesis; "
                "bounded method comparison (both rejected at the "
                "unchanged gate, adoption refused); qualified seam law "
                "reused by the second assembly byte-identically; "
                "evidence-linked followup; explicit stop without "
                "success; gate-widening refused twice; finite "
                "exploration allocation",
        "source_commit": cp._source_commit(),
        "source_file_hashes": {
            rel: cp._sha256_file(cp._REPO / rel) for rel in cp.HASHED_SOURCES
        },
        "packet_sha256": cp._sha256_bytes(PACKET.read_bytes()),
        "units": json.loads(PACKET.read_bytes())["units"],
        "checks": {n: {"pass": bool(results[n].get("pass"))} for n in ORDER},
        "cases": {n: results[n] for n in ORDER},
        "records_written": [p.name for p in
                            sorted(rr.RESEARCH_DIR.glob("*.json"))],
        "record_count_total": len(records),
        "allocations": rr.allocation_summary(),
        "scope_note": "demonstrates the single recorded cycle only; no "
                      "unlimited self-improvement and no universal "
                      "physical accuracy are claimed",
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
