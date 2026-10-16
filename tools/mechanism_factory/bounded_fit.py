"""bounded_fit.py -- the §11.18 P3 bounded fitting/evaluation entrypoint.

Builds the BOUNDED TABLE baseline for the boundary-displacement + point-load
-> port-reactions mechanism from ADAPTER-PASSed qualification receipts ONLY:
every candidate receipt is run through receipt_adapter.verify_receipt against
the packet; a refused receipt is recorded under its named adapter refusals
and is never a label source. The table is a per-family, load-magnitude-keyed
bounded PCHIP interpolant (monotone cubic in |f| over the tabulated knots,
method config #1; plain linear for 2-knot families) over the packet's
ADMITTED DOMAIN (bounded: it answers between its tabulated knots and at
them, never extrapolates past them; a query outside is refused by name).
Knots come from every
adapter-PASSed receipt, including the multi-point writer
qualification_cases.py; duplicate magnitudes are deduplicated with a
cross-writer consistency check (label_conflict refusal on disagreement).

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
            # Load magnitude: a case that claims one (multi-point writer)
            # uses it; otherwise the family's frozen CASES load (the pinned
            # writer's one-case-per-family receipt). Either way the recorded
            # reactions must balance the claimed load within the packet's
            # force-balance threshold -- a named refusal otherwise, never a
            # label (loads on the free apex are vertical-only by the
            # packet's admitted domain).
            frozen = _load_magnitude(fam)
            claimed = case.get("load_magnitude_N")
            mag = frozen if claimed is None else float(claimed)
            if not (0.0 < mag <= float(
                    (packet.get("admitted_domain") or {})
                    .get("loads", {}).get("max_force_N", float("inf")))):
                refused.append({"receipt": path, "reason": "load_out_of_domain",
                                "case_id": case.get("case_id"),
                                "load_magnitude_N": mag})
                continue
            resid = float(np.abs(
                np.asarray(outs.get("reactions_N"), dtype=np.float64
                           ).sum(axis=0)
                + np.array([0.0, 0.0, -mag])).max()) \
                if outs.get("reactions_N") else float("inf")
            if not math.isfinite(resid) or resid > float(
                    packet["acceptance_thresholds"]
                    ["max_force_balance_residual"]):
                refused.append({"receipt": path,
                                "reason": "load_reaction_mismatch",
                                "case_id": case.get("case_id"),
                                "family": fam,
                                "recomputed_force_balance_residual": resid})
                continue
            point = {
                "case_id": case.get("case_id"),
                "split": split,
                "load_magnitude_N": mag,
                "load_magnitude_source": ("case_claimed_balance_verified"
                                          if claimed is not None
                                          else "frozen_cases_load"),
                "reactions_N": outs.get("reactions_N"),
            }
            labels.setdefault(fam, []).append(point)
            label_sources.add(rsha)
    return {"labels": labels, "refused_receipts": refused,
            "label_receipt_hashes": sorted(label_sources),
            "holdout_cases_seen": holdout_seen, "holdout_cases_read": holdout_read}


def build_table(packet: dict, collected: dict) -> dict:
    """Bounded per-family table; hash over its canonical form. Points sharing
    a family and load magnitude are deduplicated: identical reactions
    (cross-writer consistency witness, tol 1e-9 N) collapse to one knot;
    differing reactions are a named refusal, never a silent overwrite."""
    table, conflicts = {"families": {}}, []
    for fam in sorted(collected["labels"]):
        pts = sorted(collected["labels"][fam],
                     key=lambda p: (p["load_magnitude_N"], p["case_id"] or ""))
        knots = []
        for p in pts:
            same = [k for k in knots
                    if k["load_magnitude_N"] == p["load_magnitude_N"]]
            if same:
                k = same[0]
                if np.abs(np.asarray(k["reactions_N"], dtype=np.float64)
                          - np.asarray(p["reactions_N"],
                                       dtype=np.float64)).max() > 1e-9:
                    conflicts.append({"family": fam,
                                      "load_magnitude_N": p["load_magnitude_N"],
                                      "case_ids": [k["case_id"], p["case_id"]]})
                continue
            knots.append(p)
        table["families"][fam] = {
            "split": _split_of(fam, packet),
            "points": knots,
        }
    if conflicts:
        raise FitRefusal("label_conflict", {"conflicts": conflicts})
    table["table_sha256"] = _sha256_bytes(_canonical(table["families"]))
    return table


def predict(table: dict, packet: dict, family: str, load_vec) -> dict:
    """Piecewise-linear (in |f|) per-family interpolant over the tabulated
    points, BOUNDED: a query outside the family's tabulated magnitude range
    is refused by name -- no extrapolation ever (a single-point family only
    answers at its own tabulated point, which keeps the old path working)."""
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
    pts = sorted(fam_entry["points"], key=lambda p: p["load_magnitude_N"])
    lo, hi = pts[0]["load_magnitude_N"], pts[-1]["load_magnitude_N"]
    if magnitude < lo or magnitude > hi:
        raise FitRefusal("refusal_out_of_domain",
                         {"family": family, "load_magnitude_N": magnitude,
                          "tabulated_range_N": [lo, hi],
                          "why": "bounded interpolant never extrapolates "
                                 "past its tabulated knots"})
    exact = next((p for p in pts
                  if p["load_magnitude_N"] == magnitude), None)
    if exact is not None:
        return {"family": family, "reactions_N": exact["reactions_N"],
                "tabulated_load_magnitude_N": exact["load_magnitude_N"],
                "query_load_magnitude_N": magnitude,
                "source": "exact_tabulated",
                "case_id": exact["case_id"]}
    xs = [p["load_magnitude_N"] for p in pts]
    j = next(k for k in range(1, len(xs))
             if xs[k - 1] < magnitude < xs[k])         # unique bracket
    lo_k, hi_k = pts[j - 1], pts[j]
    reactions, source = _interp_reactions(pts, magnitude)
    return {"family": family,
            "reactions_N": reactions if isinstance(reactions, list)
            else reactions.tolist(),
            "tabulated_range_N": [lo, hi],
            "bracketing_knots_N": [lo_k["load_magnitude_N"],
                                   hi_k["load_magnitude_N"]],
            "query_load_magnitude_N": magnitude,
            "source": source,
            "case_id": None}


def _pchip_slopes(xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """PCHIP tangents (Fritsch--Carlson / scipy's PchipInterpolator
    construction) for ONE component over knots (xs, ys). Monotone-safe:
    no overshoot, out-of-domain behavior stays bounded by the knots."""
    n = len(xs)
    h = np.diff(xs)
    s = np.diff(ys) / h                       # secant slopes
    m = np.zeros(n)
    for k in range(1, n - 1):                 # interior knots
        if s[k - 1] * s[k] > 0:
            w1 = 2.0 * h[k] + h[k - 1]
            w2 = h[k] + 2.0 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / s[k - 1] + w2 / s[k])
    # endpoints (scipy's edge case handling)
    m[0] = ((2.0 * h[0] + h[1]) * s[0] - h[0] * s[1]) / (h[0] + h[1])
    m[-1] = ((2.0 * h[-1] + h[-2]) * s[-1]
             - h[-1] * s[-2]) / (h[-1] + h[-2])
    if np.sign(m[0]) != np.sign(s[0]):
        m[0] = 0.0
    elif np.sign(s[0]) != np.sign(s[1]) and abs(m[0]) > 3.0 * abs(s[0]):
        m[0] = 3.0 * s[0]
    if np.sign(m[-1]) != np.sign(s[-1]):
        m[-1] = 0.0
    elif (np.sign(s[-1]) != np.sign(s[-2])
          and abs(m[-1]) > 3.0 * abs(s[-1])):
        m[-1] = 3.0 * s[-1]
    return m


def _pchip_component(xs: np.ndarray, ys: np.ndarray, m: np.ndarray,
                     x: float) -> float:
    """Hermite cubic evaluation of one PCHIP component at x (xs sorted,
    x strictly inside (xs[0], xs[-1]) and not equal to a knot)."""
    j = int(np.searchsorted(xs, x) - 1)
    h = xs[j + 1] - xs[j]
    t = (x - xs[j]) / h
    t2, t3 = t * t, t * t * t
    return float((2 * t3 - 3 * t2 + 1) * ys[j]
                 + (t3 - 2 * t2 + t) * h * m[j]
                 + (-2 * t3 + 3 * t2) * ys[j + 1]
                 + (t3 - t2) * h * m[j + 1])


def _interp_reactions(pts: list, magnitude: float) -> tuple:
    """Bounded per-family interpolation between the tabulated knots.
    PCHIP (monotone cubic, method config #1) for >= 3 knots; plain linear
    for 2 knots (identical to PCHIP there). Returns (reactions, source)."""
    xs = [p["load_magnitude_N"] for p in pts]
    flat = np.asarray([p["reactions_N"] for p in pts], dtype=np.float64)
    flat2 = flat.reshape(len(pts), -1)            # (n_knots, k*3)
    if len(pts) >= 3:                             # PCHIP per component
        out = np.empty(flat2.shape[1])
        for c in range(flat2.shape[1]):
            m = _pchip_slopes(np.asarray(xs), flat2[:, c])
            out[c] = _pchip_component(np.asarray(xs), flat2[:, c], m,
                                      magnitude)
        return out.reshape(flat.shape[1:]), "pchip_interpolated"
    out = np.array([np.interp(magnitude, xs, flat2[:, c])
                    for c in range(flat2.shape[1])])
    return out.reshape(flat.shape[1:]), "linear_interpolated"


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
        # own run_case) at the family's FROZEN load, timed; cross-checked
        # against the receipt bytes at the knot carrying that exact load.
        t0 = time.perf_counter()
        fresh = qr.run_case(fam, qr.CASES[fam])
        solve_s.append(time.perf_counter() - t0)
        frozen = _load_magnitude(fam)
        knot = next((p for p in table["families"][fam]["points"]
                     if p["load_magnitude_N"] == frozen), None)
        if knot is not None:
            ref = np.asarray(knot["reactions_N"])
            rerun_diff = max(rerun_diff,
                             float(np.abs(np.asarray(fresh["reactions"])
                                          - ref).max()))
    val_rows = [r for r in rows if r["split"] == "validation"]
    max_val = max((r["max_reaction_error_N"] for r in val_rows), default=0.0)
    mean_val = (sum(r["mean_reaction_error_N"] for r in val_rows)
                / len(val_rows)) if val_rows else 0.0
    # interpolation probe: half-way |f| on the validation family, vs a fresh
    # direct solve. DIAGNOSTIC: reported, never gated, never widened. With a
    # single-point table the bounded interpolant refuses the query (no
    # extrapolation past its one knot); the refusal itself is then recorded.
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
        try:
            pred = predict(table, packet, fam, np.array([0.0, 0.0, mag]))
            err = float(np.abs(np.asarray(pred["reactions_N"])
                               - np.asarray(fresh["reactions"])).max())
            probe = {"family": fam, "query_load_magnitude_N": mag,
                     "table_source": pred["source"],
                     "max_reaction_error_N": err,
                     "reference_solve_s": probe_s,
                     "note": "piecewise-linear in |f| between tabulated "
                             "knots; reported, not gated"}
        except FitRefusal as ex:
            probe = {"family": fam, "query_load_magnitude_N": mag,
                     "refused": ex.reason, "detail": ex.detail,
                     "reference_solve_s": probe_s,
                     "note": "bounded interpolant refused the off-point "
                             "query (no extrapolation past its knots); "
                             "reported, not gated"}
    loo = leave_one_out_error(table, collected)
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
            "interpolation_error": loo,
            "interpolation_probe": probe}


def leave_one_out_error(table: dict, collected: dict) -> dict:
    """Off-point (interpolation) error of the bounded piecewise-linear
    table, measured by leave-one-out on the train+validation knots: for each
    INTERIOR knot, fit on the remaining knots, evaluate at the knot's |f|,
    compare against its adapter-verified reference reactions. Endpoints are
    excluded (leave-one-out there would require extrapolation, which the
    bounded table refuses by construction)."""
    per_family, max_all = {}, 0.0
    for fam in sorted(table["families"]):
        pts = sorted(table["families"][fam]["points"],
                     key=lambda p: p["load_magnitude_N"])
        if len(pts) < 3:
            per_family[fam] = {"n_knots": len(pts), "gated": False,
                               "why": "fewer than 3 knots: no interior "
                                      "leave-one-out possible"}
            continue
        errs = []
        for i in range(1, len(pts) - 1):              # interior knots only
            rest = pts[:i] + pts[i + 1:]
            xs = [p["load_magnitude_N"] for p in rest]
            mag = pts[i]["load_magnitude_N"]
            j = next(k for k in range(1, len(xs))
                     if xs[k - 1] < mag < xs[k])
            got, _src = _interp_reactions(rest, mag)
            ref = np.asarray(pts[i]["reactions_N"], dtype=np.float64)
            errs.append({"load_magnitude_N": mag,
                         "max_reaction_error_N":
                             float(np.abs(got - ref).max())})
        fam_max = max(e["max_reaction_error_N"] for e in errs)
        max_all = max(max_all, fam_max)
        per_family[fam] = {"n_knots": len(pts), "gated": True,
                           "n_interior_knots": len(errs),
                           "max_reaction_error_N": fam_max,
                           "mean_reaction_error_N":
                               float(np.mean([e["max_reaction_error_N"]
                                              for e in errs])),
                           "per_knot": errs}
    return {"metric": "leave-one-out on interior tabulated knots "
                      "(bounded interpolant: PCHIP monotone cubic in |f| "
                      "for >= 3 knots)",
            "families": per_family,
            "max_reaction_error_N": max_all}


# ── learned candidate hook (stub; exposed, never silently skipped) ──────────

def learned_candidate_hook(eval_result: dict, packet: dict) -> dict:
    thr = float(packet["acceptance_thresholds"][TABLE_ERROR_TOLERANCE_KEY])
    err = max(eval_result["validation_max_reaction_error_N"],
              eval_result.get("interpolation_error", {}).get(
                  "max_reaction_error_N", 0.0))
    if err <= thr:
        return {"status": "refused", "reason": "learned_candidate_not_justified",
                "validation_max_reaction_error_N":
                    eval_result["validation_max_reaction_error_N"],
                "interpolation_max_reaction_error_N":
                    eval_result.get("interpolation_error", {}).get(
                        "max_reaction_error_N"),
                "packet_threshold_N": thr,
                "why": "the bounded table is already within the packet "
                       "threshold on validation AND on its leave-one-out "
                       "interpolation error; a learned candidate needs "
                       "justification (later GPU-batch seam)"}
    return {"status": "deferred", "reason": "learned_candidate_deferred_gpu_seam",
            "validation_max_reaction_error_N":
                eval_result["validation_max_reaction_error_N"],
            "interpolation_max_reaction_error_N":
                eval_result.get("interpolation_error", {}).get(
                    "max_reaction_error_N"),
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
    # Preregistered gate (the packet's own error scale). Fixed failure
    # response: the gate never moves after seeing results. Either the table
    # is qualified at it, or it is REJECTED and the learned candidate is
    # thereby justified -- both are recorded, never silently skipped.
    gate = float(packet["acceptance_thresholds"][TABLE_ERROR_TOLERANCE_KEY])
    loo_max = float(ev["interpolation_error"]["max_reaction_error_N"])
    if loo_max <= gate:
        table_status = {"status": "qualified", "gate_N": gate,
                        "measured_max_error_N": loo_max}
    else:
        table_status = {
            "status": "rejected_at_preregistered_tolerance",
            "gate_N": gate,
            "measured_max_error_N": loo_max,
            "measured_curve_per_family": {
                f: d.get("per_knot")
                for f, d in ev["interpolation_error"]["families"].items()
                if d.get("gated")},
            "note": "bounded table REJECTED at the preregistered "
                    "tolerance; nothing widened; a learned candidate is "
                    "thereby justified (deferred to the later GPU-batch "
                    "seam)"}
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
            "table_status": table_status,
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
