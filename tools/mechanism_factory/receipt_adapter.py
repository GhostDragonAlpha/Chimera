"""Versioned, independent qualification-receipt verifier (seam 2b).

verify_receipt(receipt_path, packet_path) -> Verdict(passed, refusals, detail).
Trusts nothing it can recompute: packet digest, solver/law/fixture hashes,
units, finiteness, the convergence acceptance law, domain/split integrity,
the declared verdict (recomputed from PACKET thresholds only -- tolerances in
the receipt are inert), and gpu_job reservation/release with clean-resume.

CLI: python tools/mechanism_factory/receipt_adapter.py RECEIPT PACKET
     exit 0 pass / 1 refused / 2 usage-or-unreadable.
CPU only; stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

# -- preregistered adapter constants -----------------------------------------
ADAPTER_VERSION = "receipt-adapter-v1"
ACCEPTED_RECEIPT_SCHEMA = "chimera-mechanism-factory-qualification-receipt-v1"
GPU_RELEASED_STATE = "released"
RESUME_BLOCK_KEY = "resume"            # receipt["resume"] = {checkpoint_path,
RESUME_PATH_KEY = "checkpoint_path"    #   resumed_from_checkpoint_sha256}
RESUME_HASH_KEY = "resumed_from_checkpoint_sha256"
CONVERGED_STATUSES = ("stationary", "stagnated")

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent


@dataclass
class Verdict:
    passed: bool
    refusals: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str | None:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return None


def _resolve_repo_path(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else _REPO / rel


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, ValueError):
        return None, "unreadable"


def _case_outputs_finite(case: dict) -> bool:
    out = case.get("outputs") or {}
    vals = [out.get("energy_J"), out.get("max_free_residual_N")]
    vals += [v for row in (out.get("reactions_N") or []) for v in row]
    return all(isinstance(v, (int, float)) and math.isfinite(v) for v in vals)


def _case_converged(case: dict, thr: dict) -> bool:
    """The recorded acceptance law: stationary, OR stagnated with every
    residual within its packet threshold."""
    status = case.get("status")
    if status == "stationary":
        return True
    if status != "stagnated":
        return False
    residual = (case.get("outputs") or {}).get("max_free_residual_N")
    return (isinstance(residual, (int, float)) and math.isfinite(residual)
            and residual <= thr["max_free_residual_N"])


def _gpu_released(receipt: dict) -> bool:
    """gpu_job null (CPU) is unaffected; a reserved job needs a clean resume
    block whose checkpoint hash is verifiable on disk."""
    jobs = [receipt.get("gpu_job")] + [
        c.get("gpu_job") for c in receipt.get("cases", [])]
    reserved = [j for j in jobs
                if j is not None and not (isinstance(j, dict)
                                          and j.get("state") == GPU_RELEASED_STATE)]
    if not reserved:
        return True
    resume = receipt.get(RESUME_BLOCK_KEY) or {}
    cp = resume.get(RESUME_PATH_KEY)
    want = resume.get(RESUME_HASH_KEY)
    if not cp or not want:
        return False
    got = _sha256_file(_resolve_repo_path(str(cp)))
    return got is not None and got == want


def verify_receipt(receipt_path, packet_path) -> Verdict:
    receipt, err = _load_json(Path(receipt_path))
    if err:
        return Verdict(False, ["receipt_missing"], {"receipt_error": err})
    if not isinstance(receipt, dict) or \
            receipt.get("schema") != ACCEPTED_RECEIPT_SCHEMA:
        return Verdict(False, ["receipt_schema_unsupported"],
                       {"got_schema": receipt.get("schema")
                        if isinstance(receipt, dict) else None})
    packet, err = _load_json(Path(packet_path))
    if err:
        return Verdict(False, ["packet_unreadable"], {"packet_error": err})

    refusals: list = []
    # packet digest, against the packet AS IT IS NOW
    try:
        packet_bytes = Path(packet_path).read_bytes()
    except OSError:
        packet_bytes = b""
    if receipt.get("packet_sha256") != _sha256_bytes(packet_bytes):
        refusals.append("packet_digest_mismatch")

    # solver/law/fixture hashes, against each file on disk now
    for rel, want in (receipt.get("source_file_hashes") or {}).items():
        got = _sha256_file(_resolve_repo_path(rel))
        if got != want:
            refusals.append(f"solver_hash_mismatch:{rel}")

    # units
    if receipt.get("units") != packet.get("units"):
        refusals.append("unit_mismatch")

    # domain and split integrity (packet side)
    splits = packet.get("frozen_splits") or {}
    names = [f for lst in splits.values() for f in lst]
    union = set(names)
    if len(names) != len(union) or any(
            set(a) & set(b) for a, b in _pairs(list(splits.values()))):
        refusals.append("split_overlap")

    # cases: finiteness, convergence, domain; verdict recomputed from PACKET
    thr = packet.get("acceptance_thresholds") or {}
    recomputed_pass = True
    for case in receipt.get("cases", []):
        fam = case.get("family")
        if fam not in union:
            refusals.append(f"out_of_domain:{fam}")
            recomputed_pass = False
            continue
        if not _case_outputs_finite(case):
            refusals.append(f"nonfinite_output:{case.get('case_id')}")
            recomputed_pass = False
        if not _case_converged(case, thr):
            refusals.append(f"unconverged_label:{case.get('case_id')}")
            recomputed_pass = False

    # gpu_job reservation/release
    if not _gpu_released(receipt):
        refusals.append("interrupted_gpu_job")

    # declared verdict forgery: tolerances read ONLY from the packet; any
    # thresholds the receipt carries are inert by construction.
    declared = (receipt.get("declared_verdict") or {}).get("verdict")
    if declared == "PASS" and not recomputed_pass:
        refusals.append("verdict_forgery")

    return Verdict(passed=not refusals, refusals=refusals,
                   detail={"recomputed_verdict":
                           "PASS" if recomputed_pass else "FAIL",
                           "declared_verdict": declared})


def _pairs(items):
    return [(items[i], items[j])
            for i in range(len(items)) for j in range(i + 1, len(items))]


def main(argv) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(__file__).name} RECEIPT PACKET")
        return 2
    v = verify_receipt(argv[0], argv[1])
    if v.refusals and v.detail.get("receipt_error"):
        print(f"REFUSED: receipt_missing ({v.detail['receipt_error']})")
        return 2
    if v.refusals and v.detail.get("packet_error"):
        print(f"REFUSED: packet_unreadable ({v.detail['packet_error']})")
        return 2
    if v.passed:
        print(f"PASS {v.detail}")
        return 0
    print(f"REFUSED: {', '.join(v.refusals)}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
