"""Qualification receipt adapter for the asymmetric constant-tension patch
mechanism (seam 2). Reads tools/mechanism_factory/example_packet.json, runs
solve_equilibrium on three small CPU apex-cone fixtures (one per frozen
family), asserts the packet's terminal-state and threshold laws, and stamps a
chimera-mechanism-factory-qualification-receipt-v2 receipt into
docs/evidence/mechanism_factory/ via the lab's resolve_evidence_path law.

Exit 0 pass / 1 threshold-or-status failure / 2 evidence-path-exists refusal.
CPU only; numpy + stdlib. Owners: import, never edit, the membrane_scale_lab.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent            # tools/mechanism_factory
_REPO = _HERE.parent.parent                       # repo root (PythonChimera)

import patch_equilibrium as pe                    # bootstraps sys.path itself
import fixture_generator as fg                    # via pe's lab path insert
from evidence_output import (                     # via pe's lab path insert
    EvidencePathExists,
    resolve_evidence_path,
)

EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"
PACKET_PATH = _HERE / "example_packet.json"
RECEIPT_SCHEMA = "chimera-mechanism-factory-qualification-receipt-v2"
HASHED_SOURCES = [
    "tools/mechanism_factory/patch_equilibrium.py",
    "tools/mechanism_factory/qualification_receipt.py",
    "tools/membrane_scale_lab/surface_energy_reference.py",
    "tools/membrane_scale_lab/overdamped_descent.py",
    "tools/membrane_scale_lab/fixture_generator.py",
]

# Frozen splits: family -> (seed, fan kwargs, loads). Full-rim pins only
# (partial-rim pins have no equilibrium under this law; see the packet's
# exclusions). The free apex is the last vertex (index n_rim); loads are
# vertical-only [N], |f| <= max_force_N from the packet.
CASES = {
    "fan-full-rim-pin":
        {"fixture": {"n_rim": 200, "radius": 1.0, "height": 0.3, "seed": 1},
         "loads": [(0.0, 0.0, -0.8)]},
    "fan-full-rim-pin-alt-geometry":
        {"fixture": {"n_rim": 220, "radius": 0.8, "height": 0.5, "seed": 7},
         "loads": [(0.0, 0.0, -0.6)]},
    "fan-full-rim-pin-alt-load":
        {"fixture": {"n_rim": 240, "radius": 1.2, "height": 0.4, "seed": 13},
         "loads": [(0.0, 0.0, -1.1)]},
}
MAX_STEPS = 60000


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(_REPO), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30, check=True)
        return out.stdout.strip()
    except Exception:                                 # pragma: no cover
        return "unknown"


def run_case(family: str, spec: dict):
    fix = fg.high_degree_fan(**spec["fixture"])
    assert fix.stats.valid, f"{family}: fixture invalid: {fix.stats.checks}"
    pins = list(fix.stats.pinned)                     # full rim, always
    apex = spec["fixture"]["n_rim"]                   # the single free vertex
    loads = [(apex, tuple(f)) for f in spec["loads"]]
    res = pe.solve_equilibrium(fix.positions, fix.faces, fix.gamma,
                               pins, loads, max_steps=MAX_STEPS)
    reactions = np.asarray(res.reaction_forces, dtype=np.float64)
    load_vec = np.zeros(3)
    for _i, f in loads:
        load_vec += np.asarray(f, dtype=np.float64)
    force_res = float(np.max(np.abs(reactions.sum(axis=0) + load_vec)))
    moment = np.zeros(3)
    for k, i in enumerate(pins):                      # pins sit at rest coords
        moment += np.cross(fix.positions[i], reactions[k])
    for idx, f in loads:                              # loads at equilibrium pts
        moment += np.cross(res.positions[idx], np.asarray(f, dtype=np.float64))
    moment_res = float(np.max(np.abs(moment)))
    return {
        "family": family,
        "status": res.status,
        "free_residual": float(res.free_residual),
        "energy": float(res.energy),
        "reactions": reactions,
        "force_balance_residual": force_res,
        "moment_balance_residual": moment_res,
    }


def negative_controls() -> int:
    """0 ok / 1 failed. Declared in the packet; executed before the cases."""
    # (1) a load on a pinned vertex must be refused (no solve performed).
    fx = fg.regular_disk(n_ring=8, radius=1.0, seed=0)
    pin = fx.stats.pinned[0]
    try:
        pe.solve_equilibrium(fx.positions, fx.faces, fx.gamma,
                             list(fx.stats.pinned),
                             [(pin, (0.0, 0.0, -1.0))], max_steps=10)
        print(f"FAIL: load on pinned vertex {pin} was not refused")
        return 1
    except pe.InvalidSurface as ex:
        print(f"control pinned-load refused: {ex.reason}")
    # (2) zero-load flat regular disk: exactly stationary at start.
    res = pe.solve_equilibrium(fx.positions, fx.faces, fx.gamma,
                               list(fx.stats.pinned), [], max_steps=2000)
    ok = res.status == pe.STATIONARY and res.free_residual <= 1e-15
    print(f"control zero-load flat start: status={res.status} "
          f"free_residual={res.free_residual:.3e} -> {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    packet_bytes = PACKET_PATH.read_bytes()
    packet = json.loads(packet_bytes)
    thr = packet["acceptance_thresholds"]
    splits = packet["frozen_splits"]
    expected_families = (splits["train"] + splits["validation"]
                         + splits["holdout"])
    assert set(CASES) == set(expected_families), "case/family mismatch"
    if negative_controls():
        return 1

    allowed_status = {"stationary", "stagnated"}   # packet stopping_conditions
    cases, failures = [], []
    for family in expected_families:
        spec = CASES[family]
        c = run_case(family, spec)
        ok = (c["status"] in allowed_status
              and c["free_residual"] <= thr["max_free_residual_N"]
              and c["force_balance_residual"] <= thr["max_force_balance_residual"]
              and c["moment_balance_residual"] <= thr["max_moment_balance_residual"])
        if not ok:
            failures.append(family)
        print(f"{family}: status={c['status']} "
              f"free_residual={c['free_residual']:.3e} "
              f"force_bal={c['force_balance_residual']:.3e} "
              f"moment_bal={c['moment_balance_residual']:.3e} "
              f"max|R|={np.abs(c['reactions']).max():.4f} N "
              f"energy={c['energy']:.6f} J -> "
              f"{'OK' if ok else 'FAIL'}")
        cases.append({
            "case_id": f"{family}_seed{spec['fixture']['seed']}",
            "family": family,
            "status": c["status"],
            "outputs": {
                "energy_J": c["energy"],
                "max_free_residual_N": c["free_residual"],
                "reactions_N": [[float(v) for v in row]
                                for row in c["reactions"]],
                # v2: the two balance residuals are recorded so the adapter
                # can recompute the packet's force/moment balance thresholds
                # (previously enforced at qualification time only).
                "max_force_balance_residual": c["force_balance_residual"],
                "max_moment_balance_residual": c["moment_balance_residual"],
            },
            "gpu_job": None,
        })

    if failures:
        print(f"FAIL: threshold/status violation in: {', '.join(failures)}")
        return 1

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "adapter_version": "adapter-v1",
        "source_commit": _source_commit(),
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
