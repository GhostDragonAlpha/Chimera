"""qualification_cases.py -- multi-point qualification-case writer (P3
bounded-fit seam, follow-up).

The genuine qualification receipt carries ONE case per family, which is a
degenerate interpolant. This writer generates ~5 load magnitudes per
TRAIN and VALIDATION family across the packet's admitted domain
(|f| <= max_force_N, vertical-only loads, same frozen fixtures) and writes a
schema chimera-mechanism-factory-qualification-receipt-v2 receipt stamped
into docs/evidence/mechanism_factory/ via the lab's resolve_evidence_path.

Provenance/enforcement design (the adapter is the gate, not the writer's
identity):
  * the solve path is the PINNED writer's own run_case
    (tools/mechanism_factory/qualification_receipt.py), imported read-only
    and never edited -- identical solver, fixtures, MAX_STEPS, negative
    controls and residual bookkeeping;
  * the receipt records source_file_hashes for every file on the solve
    path INCLUDING this writer, so receipt_adapter.verify_receipt
    re-verifies solver/law/fixture/writer bytes, the packet digest, units,
    the convergence law and the packet's balance thresholds against
    whatever bytes are on disk when the receipt is consumed;
  * a receipt that does not PASS the adapter is never a label source.
  * the HOLDOUT family is never run here -- the fit's split gate plus the
    sentinel check (bounded_fit_checks T3) stay meaningful.

Exit 0 receipt written / 1 threshold-or-status or negative-control failure /
2 evidence-path-exists refusal. CPU only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent            # tools/mechanism_factory
_REPO = _HERE.parent.parent

import patch_equilibrium as pe                    # bootstraps the lab path
import qualification_receipt as qr                # PINNED writer, read-only
from evidence_output import (                     # via pe's lab path insert
    EvidencePathExists,
    resolve_evidence_path,
)

EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"
PACKET_PATH = _HERE / "example_packet.json"
RECEIPT_SCHEMA = "chimera-mechanism-factory-qualification-receipt-v2"

# Files on the solve path whose bytes the adapter re-verifies at consumption
# time (superset of the pinned writer's list: this writer is included).
HASHED_SOURCES = [
    "tools/mechanism_factory/patch_equilibrium.py",
    "tools/mechanism_factory/qualification_receipt.py",
    "tools/mechanism_factory/qualification_cases.py",
    "tools/membrane_scale_lab/surface_energy_reference.py",
    "tools/membrane_scale_lab/overdamped_descent.py",
    "tools/membrane_scale_lab/fixture_generator.py",
]

# ~5 vertical load magnitudes per train/validation family across the
# admitted domain (|f| <= admitted max_force_N = 2.0), each family's set
# containing its frozen qualification load so the table subsumes the
# genuine receipt's points. Fixtures are the frozen ones from the pinned
# writer's CASES, byte-identical. The holdout family is deliberately absent.
LOAD_MAGNITUDES = {
    "fan-full-rim-pin":                [0.4, 0.8, 1.2, 1.6, 2.0],
    "fan-full-rim-pin-alt-geometry":   [0.2, 0.6, 1.0, 1.4, 1.8],
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    packet_bytes = PACKET_PATH.read_bytes()
    packet = json.loads(packet_bytes)
    thr = packet["acceptance_thresholds"]
    splits = packet["frozen_splits"]
    fit_families = splits["train"] + splits["validation"]
    assert set(LOAD_MAGNITUDES) == set(fit_families), "case/family mismatch"
    max_f = float(packet["admitted_domain"]["loads"]["max_force_N"])
    for fam, mags in LOAD_MAGNITUDES.items():
        assert all(0.0 < m <= max_f for m in mags), f"{fam}: |f| out of domain"
        assert len(mags) == len(set(mags)), f"{fam}: duplicate magnitudes"
    if qr.negative_controls():
        return 1

    allowed_status = {"stationary", "stagnated"}   # packet stopping_conditions
    cases, failures = [], []
    for family in fit_families:
        fixture = qr.CASES[family]["fixture"]      # frozen fixture, untouched
        for mag in LOAD_MAGNITUDES[family]:
            spec = {"fixture": fixture, "loads": [(0.0, 0.0, -float(mag))]}
            c = qr.run_case(family, spec)
            ok = (c["status"] in allowed_status
                  and c["free_residual"] <= thr["max_free_residual_N"]
                  and c["force_balance_residual"] <= thr["max_force_balance_residual"]
                  and c["moment_balance_residual"] <= thr["max_moment_balance_residual"])
            if not ok:
                failures.append(f"{family}@{mag}")
            print(f"{family} |f|={mag:.2f} N: status={c['status']} "
                  f"free_residual={c['free_residual']:.3e} "
                  f"force_bal={c['force_balance_residual']:.3e} "
                  f"moment_bal={c['moment_balance_residual']:.3e} "
                  f"max|R|={np.abs(c['reactions']).max():.4f} N -> "
                  f"{'OK' if ok else 'FAIL'}")
            cases.append({
                "case_id": f"{family}_m{mag:.2f}_qcases",
                "family": family,
                "status": c["status"],
                # the case claims its own load magnitude (the frozen CASES
                # load is only one of the magnitudes here); consumers
                # cross-check it against the recorded reactions' force
                # balance within the packet threshold.
                "load_magnitude_N": float(mag),
                "outputs": {
                    "energy_J": c["energy"],
                    "max_free_residual_N": c["free_residual"],
                    "reactions_N": [[float(v) for v in row]
                                    for row in c["reactions"]],
                    "max_force_balance_residual": c["force_balance_residual"],
                    "max_moment_balance_residual": c["moment_balance_residual"],
                },
                "gpu_job": None,
            })

    if failures:
        print(f"FAIL: threshold/status violation in: {', '.join(failures)}")
        return 1

    writer = _HERE / "qualification_cases.py"
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "adapter_version": "adapter-v1",
        "source_file_hashes": {
            rel: _sha256_file(_REPO / rel) for rel in HASHED_SOURCES
        },
        "packet_sha256": _sha256_bytes(packet_bytes),
        "units": packet["units"],
        "cases": cases,
        "declared_verdict": {
            "verdict": "PASS",
            "recomputed_from": "packet thresholds",
        },
        # provenance beyond the adapter's own checks (informational; the
        # adapter's hash re-verification remains the gate).
        "provenance": {
            "writer": "tools/mechanism_factory/qualification_cases.py",
            "writer_sha256": _sha256_file(writer),
            "solve_path": "qualification_receipt.run_case (pinned writer, "
                          "unmodified; same solver, fixtures, MAX_STEPS and "
                          "negative controls)",
            "max_steps": qr.MAX_STEPS,
            "load_magnitudes_N": {f: list(m)
                                  for f, m in LOAD_MAGNITUDES.items()},
            "families": "train+validation only; holdout never run",
            "why": "one case per family is a degenerate interpolant; these "
                   "extra qualified cases make the bounded table a real "
                   "piecewise interpolant (P3 first-deliverable comparison)",
        },
    }
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    out_path = resolve_evidence_path(EVID_DIR, "qualification_receipt",
                                     sys.argv[1:])
    out_path.write_text(json.dumps(receipt, indent=2) + "\n",
                        encoding="utf-8")
    print(f"receipt: {out_path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except EvidencePathExists as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)
