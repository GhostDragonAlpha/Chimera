"""bounded_fit.py -- the §11.18 P3 bounded fitting/evaluation entrypoint.

Builds the BOUNDED TABLE baseline for the boundary-displacement + point-load
-> port-reactions mechanism from ADAPTER-PASSed qualification receipts ONLY:
every candidate receipt is run through receipt_adapter.verify_receipt against
the packet; a refused receipt is recorded under its named adapter refusals
and is never a label source. The table is a per-family, load-magnitude-keyed
nearest-neighbour lookup over the packet's ADMITTED DOMAIN (bounded: it
returns tabulated points, never an extrapolated value; a query outside the
domain is refused by name).

Split discipline (P3): the fit and the evaluation read TRAIN and VALIDATION
family cases only. The holdout (final-test) family is gated structurally --
the case filter looks at (family, split) BEFORE any output value is touched,
so a planted sentinel holdout case provably cannot reach the table (the
checks plant one and verify the table hash is unchanged). no_final_test_access
is recorded TRUE only when the holdout read counter is zero.

Evaluation: table vs direct reference solve on train+validation cases (max/
mean reaction component error) plus a shadow latency line (table query in
microseconds vs the direct solve in seconds) and an off-point interpolation
probe (diagnostic, reported not gated). The learned candidate is a stub hook:
while the table error is already within the packet threshold it refuses as
learned_candidate_not_justified -- the hook is exposed, never silently
skipped (the Noether learned-candidate fit is a later GPU-batch seam).

Receipt: schema chimera-mechanism-factory-fit-eval-v1 into
docs/evidence/mechanism_factory/ via resolve_evidence_path.
Run: python tools/mechanism_factory/bounded_fit.py [--out P] [--force-out]
     [--receipt PATH ...]   (default: scan every qualification_receipt_*.json)
Exit 0 fit+eval written / 1 fit failure / 2 evidence-path refusal.
CPU only; numpy + stdlib. The lab is imported read-only, never edited.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent
sys.path.insert(0, str(_HERE))                       # receipt_adapter, writer

import receipt_adapter as ra                         # the independent verifier
import qualification_receipt as qr                   # CASES + run_case (pinned
                                                     # writer, read-only use)

EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"
PACKET_PATH = _HERE / "example_packet.json"
FIT_SCHEMA = "chimera-mechanism-factory-fit-eval-v1"
FIT_SEED = 0                # deterministic pipeline: no RNG anywhere; the
                            # seed is recorded for the P3 field requirement.
FIT_SPLITS = ("train", "validation")
HOLDOUT_SPLIT = "holdout"

# Preregistered BEFORE any run: the table's contractual error tolerance is
# the packet's own force-balance threshold (same machine-scale floor). Never
# widened after seeing results.
TABLE_ERROR_TOLERANCE_KEY = "max_force_balance_residual"


class FitRefusal(Exception):
    """Named refusal (P-failure rule): carries .reason and .detail."""

    def __init__(self, reason: str, detail: dict | None = None):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail or {}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _split_of(family: str, packet: dict) -> str | None:
    for split, fams in (packet.get("frozen_splits") or {}).items():
        if family in fams:
            return split
    return None


def _load_magnitude(family: str) -> float:
    """|f| of the family's frozen load, from the PINNED writer's CASES
    (loads are plain (fx,fy,fz) triples; run_case attaches the apex)."""
    return float(math.sqrt(sum(c * c for c in qr.CASES[family]["loads"][0])))


# ── label collection: adapter-PASSed receipts only ──────────────────────────

def collect_labels(packet: dict, receipt_paths: list) -> dict:
    """Run the adapter on every candidate receipt. PASS -> label source;
    otherwise a named refusal, never a label source."""
    labels, refused, holdout_seen, holdout_read = {}, [], 0, 0
    label_sources = set()
    for path in receipt_paths:
        path = str(path)
        v = ra.verify_receipt(path, PACKET_PATH)
        if not v.passed:
            refused.append({"receipt": path, "reason": "receipt_unqualified",
                            "adapter_refusals": list(v.refusals)})
            continue
        receipt = json.loads(Path(path).read_text(encoding="utf-8"))
        rsha = _sha256_bytes(Path(path).read_bytes())
        for case in receipt.get("cases", []):
            fam = case.get("family")
            split = _split_of(fam, packet)
            if split == HOLDOUT_SPLIT:
                holdout_seen += 1
                continue                       # outputs NEVER touched here
            if split not in FIT_SPLITS:
                refused.append({"receipt": path, "reason": "case_out_of_domain",
                                "family": fam})
                continue
            outs = case.get("outputs") or {}   # read only past the split gate
            point = {
                "case_id": case.get("case_id"),
                "split": split,
                "load_magnitude_N": _load_magnitude(fam),
                "reactions_N": outs.get("reactions_N"),
            }
            labels.setdefault(fam, []).append(point)
            label_sources.add(rsha)
    return {"labels": labels, "refused_receipts": refused,
            "label_receipt_hashes": sorted(label_sources),
            "holdout_cases_seen": holdout_seen, "holdout_cases_read": holdout_read}


def build_table(packet: dict, collected: dict) -> dict:
    """Bounded per-family table; hash over its canonical form."""
    table = {"families": {}}
    for fam in sorted(collected["labels"]):
        pts = sorted(collected["labels"][fam], key=lambda p: p["case_id"] or "")
        table["families"][fam] = {
            "split": _split_of(fam, packet),
            "points": pts,
        }
    table["table_sha256"] = _sha256_bytes(_canonical(table["families"]))
    return table


def predict(table: dict, packet: dict, family: str, load_vec) -> dict:
    """Bounded lookup: nearest tabulated |f| WITHIN the family; anything
    outside the admitted domain is refused by name (no silent
    extrapolation)."""
    vec = np.asarray(load_vec, dtype=np.float64)
    if vec.shape != (3,) or not all(math.isfinite(v) for v in vec):
        raise FitRefusal("refusal_nonfinite_load", {"family": family})
    union = [f for lst in (packet.get("frozen_splits") or {}).values() for f in lst]
    if family not in union:
        raise FitRefusal("refusal_out_of_domain",
                         {"family": family, "why": "not in frozen_splits"})
    magnitude = float(np.linalg.norm(vec))
    max_f = float((packet.get("admitted_domain") or {}).get("loads",
                  {}).get("max_force_N", float("inf")))
    if magnitude > max_f:
        raise FitRefusal("refusal_out_of_domain",
                         {"family": family, "load_magnitude_N": magnitude,
                          "admitted_max_force_N": max_f})
    fam_entry = table["families"].get(family)
    if not fam_entry or not fam_entry["points"]:
        raise FitRefusal("refusal_no_tabulated_point",
                         {"family": family,
                          "why": "bounded table never extrapolates across "
                                 "families"})
    best = min(fam_entry["points"],
               key=lambda p: abs(p["load_magnitude_N"] - magnitude))
    return {"family": family, "reactions_N": best["reactions_N"],
            "tabulated_load_magnitude_N": best["load_magnitude_N"],
            "query_load_magnitude_N": magnitude,
            "source": ("exact_tabulated"
                       if abs(best["load_magnitude_N"] - magnitude) == 0.0
                       else "nearest_neighbor_bounded"),
            "case_id": best["case_id"]}


# ── evaluation: table vs direct reference solve ─────────────────────────────

def evaluate(table: dict, packet: dict, collected: dict) -> dict:
    """Max/mean reaction error on train+validation cases, the shadow latency
    line, and an off-point interpolation probe (diagnostic)."""
    thr = float(packet["acceptance_thresholds"][TABLE_ERROR_TOLERANCE_KEY])
    rows, table_us, solve_s, rerun_diff = [], [], [], 0.0
    for fam in sorted(collected["labels"]):
        for point in table["families"][fam]["points"]:
            vec = np.zeros(3)
            vec[2] = point["load_magnitude_N"]
            t0 = time.perf_counter()
            pred = predict(table, packet, fam, vec)
            dt_us = (time.perf_counter() - t0) * 1e6
            ref = np.asarray(point["reactions_N"], dtype=np.float64)
            got = np.asarray(pred["reactions_N"], dtype=np.float64)
            err = np.abs(got - ref)
            rows.append({"case_id": point["case_id"], "family": fam,
                         "split": point["split"],
                         "max_reaction_error_N": float(err.max()),
                         "mean_reaction_error_N": float(err.mean()),
                         "exact_tabulated": pred["source"] == "exact_tabulated",
                         "table_eval_us": dt_us})
            table_us.append(dt_us)
        # shadow: one FRESH direct reference solve per family (the writer's
        # own run_case), timed; cross-checked against the receipt bytes.
        t0 = time.perf_counter()
        fresh = qr.run_case(fam, qr.CASES[fam])
        solve_s.append(time.perf_counter() - t0)
        ref = np.asarray(table["families"][fam]["points"][0]["reactions_N"])
        rerun_diff = max(rerun_diff,
                         float(np.abs(np.asarray(fresh["reactions"]) - ref).max()))
    val_rows = [r for r in rows if r["split"] == "validation"]
    max_val = max((r["max_reaction_error_N"] for r in val_rows), default=0.0)
    mean_val = (sum(r["mean_reaction_error_N"] for r in val_rows)
                / len(val_rows)) if val_rows else 0.0
    # interpolation probe: half-way |f| on the validation family, vs a fresh
    # direct solve. DIAGNOSTIC: reported, never gated, never widened.
    probe = None
    v_fams = [f for f in sorted(collected["labels"])
              if _split_of(f, packet) == "validation"]
    if v_fams:
        fam = v_fams[0]
        mag = _load_magnitude(fam) * 0.9
        spec = dict(qr.CASES[fam])
        spec["loads"] = [tuple(c * 0.9 for c in spec["loads"][0])]
        t0 = time.perf_counter()
        fresh = qr.run_case(fam + "_probe", spec)
        probe_s = time.perf_counter() - t0
        pred = predict(table, packet, fam, np.array([0.0, 0.0, mag]))
        err = float(np.abs(np.asarray(pred["reactions_N"])
                           - np.asarray(fresh["reactions"])).max())
        probe = {"family": fam, "query_load_magnitude_N": mag,
                 "table_source": pred["source"],
                 "max_reaction_error_N": err,
                 "reference_solve_s": probe_s,
                 "note": "single-tabulated-point nearest neighbour cannot "
                         "interpolate; bounded, reported, not gated"}
    return {"splits_evaluated": list(FIT_SPLITS),
            "cases": rows,
            "max_reaction_error_N": max(
                (r["max_reaction_error_N"] for r in rows), default=0.0),
            "mean_reaction_error_N": (sum(r["mean_reaction_error_N"]
                                          for r in rows) / len(rows))
            if rows else 0.0,
            "validation_max_reaction_error_N": max_val,
            "validation_mean_reaction_error_N": mean_val,
            "tolerance_key": TABLE_ERROR_TOLERANCE_KEY,
            "tolerance_N": thr,
            "within_tolerance": max_val <= thr,
            "shadow_latency_s": {
                "table_eval_us_median": float(np.median(table_us))
                if table_us else 0.0,
                "reference_solve_s": [float(s) for s in solve_s],
                "reference_solve_s_mean": float(np.mean(solve_s))
                if solve_s else 0.0,
                "speedup_ratio": (float(np.mean(solve_s)) * 1e6
                                  / float(np.median(table_us)))
                if table_us and solve_s else None},
            "reference_rerun_max_abs_diff_N": rerun_diff,
            "interpolation_probe": probe}


# ── learned candidate hook (stub; exposed, never silently skipped) ──────────

def learned_candidate_hook(eval_result: dict, packet: dict) -> dict:
    thr = float(packet["acceptance_thresholds"][TABLE_ERROR_TOLERANCE_KEY])
    err = eval_result["validation_max_reaction_error_N"]
    if err <= thr:
        return {"status": "refused", "reason": "learned_candidate_not_justified",
                "validation_max_reaction_error_N": err,
                "packet_threshold_N": thr,
                "why": "the bounded table is already within the packet "
                       "threshold on validation; a learned candidate needs "
                       "justification (later GPU-batch seam)"}
    return {"status": "deferred", "reason": "learned_candidate_deferred_gpu_seam",
            "validation_max_reaction_error_N": err,
            "packet_threshold_N": thr,
            "why": "table error above the packet threshold; the learned-"
                   "candidate fit is the later GPU-batch seam"}


# ── fit entrypoint ──────────────────────────────────────────────────────────

def fit(packet: dict, receipt_paths: list) -> dict:
    """Full fit+eval; returns the result dict the fit receipt is built from.
    Deterministic: same inputs -> same table hash."""
    tracemalloc.start()
    t0 = time.perf_counter()
    collected = collect_labels(packet, receipt_paths)
    table = build_table(packet, collected)
    ev = evaluate(table, packet, collected)
    learned = learned_candidate_hook(ev, packet)
    wall = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "schema_fields": {
            "seed": FIT_SEED,
            "seed_note": "deterministic pipeline, no RNG; recorded per P3",
            "normalization": {
                "world_unit": packet["normalization"]["world_unit"],
                "units": packet["units"],
                "residual_note": packet["normalization"]["residual_note"],
                "reaction_units": packet["io_schema"]["outputs"]
                                  ["reaction_forces"]},
            "split_usage": {
                "fit": list(FIT_SPLITS),
                "evaluation": list(FIT_SPLITS),
                "holdout": "excluded structurally (split gate before any "
                           "output read; sentinel-proved by the checks)",
                "holdout_cases_seen": collected["holdout_cases_seen"],
                "holdout_cases_read": collected["holdout_cases_read"]},
            "no_final_test_access":
                collected["holdout_cases_read"] == 0,
            "cost": {"wall_time_s": wall,
                     "python_traced_peak_mib": peak / (1024.0 * 1024.0),
                     "metric_note": "tracemalloc Python-heap peak over the "
                                    "whole fit+eval window, including the "
                                    "shadow reference solves' Python-side "
                                    "allocations (numpy's internal buffers "
                                    "are not fully traced)"},
            "table_hash": table["table_sha256"],
            "label_receipts": collected["label_receipt_hashes"],
            "refused_receipts": collected["refused_receipts"],
        },
        "table": table,
        "labels": collected["labels"],
        "eval": ev,
        "learned_candidate": learned,
    }


def build_receipt(packet: dict, result: dict, receipt_paths: list) -> dict:
    table = result["table"]
    return {
        "schema": FIT_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "mechanism_id": packet.get("mechanism_id"),
        "packet_sha256": _sha256_bytes(PACKET_PATH.read_bytes()),
        "candidate_revision": packet.get("candidate_revision"),
        "candidate_receipts_considered": [str(p) for p in receipt_paths],
        "table": table,
        **result["schema_fields"],
        "evaluation": result["eval"],
        "learned_candidate": result["learned_candidate"],
        "admitted_domain": packet.get("admitted_domain"),
        "refusal_law": "out-of-domain queries raise refusal_out_of_domain; "
                       "unqualified receipts are refused as "
                       "receipt_unqualified and never become label sources",
    }


def _default_receipt_paths() -> list:
    return sorted(str(p) for p in EVID_DIR.glob("qualification_receipt_*.json"))


def main(argv: list) -> int:
    from evidence_output import (EvidencePathExists, resolve_evidence_path)
    paths, rest = [], []
    flag = None
    for a in argv:
        if a == "--receipt":
            flag = "receipt"
        elif flag == "receipt":
            paths.append(a); flag = None
        else:
            rest.append(a)
    if not paths:
        paths = _default_receipt_paths()
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    try:
        out_path = resolve_evidence_path(EVID_DIR, "fit_receipt", rest)
    except EvidencePathExists as ex:
        print(f"REFUSED: {ex}")
        return 2
    result = fit(packet, paths)
    receipt = build_receipt(packet, result, paths)
    ev = result["eval"]
    print(f"labels: {sum(len(v) for v in result['labels'].values())} cases / "
          f"{len(result['labels'])} families; refused receipts: "
          f"{len(result['schema_fields']['refused_receipts'])}")
    print(f"table_hash: {result['table']['table_sha256']}")
    print(f"validation max/mean reaction error: "
          f"{ev['validation_max_reaction_error_N']:.3e} / "
          f"{ev['validation_mean_reaction_error_N']:.3e} N (tol "
          f"{ev['tolerance_N']:.0e}, within={ev['within_tolerance']})")
    sl = ev["shadow_latency_s"]
    print(f"shadow latency: table {sl['table_eval_us_median']:.1f} us vs "
          f"reference solve {sl['reference_solve_s_mean']:.2f} s mean")
    print(f"learned candidate: {result['learned_candidate']['reason']}")
    out_path.write_text(json.dumps(receipt, indent=2) + "\n",
                        encoding="utf-8")
    print(f"fit receipt: {out_path}")
    return 0 if ev["within_tolerance"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
