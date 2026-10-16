"""Fault-injection acceptance suite for the seam-2b receipt adapter.

Generates one genuine receipt/packet pair fresh (subprocess of
qualification_receipt.py into a temp evidence dir), then injects faults F1-F12
and checks each expected named refusal against the adapter's observed
refusals. F12 exercises the schema-v2 balance-residual law: a recorded
balance residual above the packet threshold under a declared PASS is
verdict_forgery. Emits chimera-mechanism-factory-adapter-faults-v1 JSON into
docs/evidence/mechanism_factory/ via resolve_evidence_path.

Exit 0 only if ALL faults green / 1 a fault failed / 2 evidence-path refusal.
Run: python tools/mechanism_factory/receipt_adapter_faults.py
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent
sys.path.insert(0, str(_HERE))

import receipt_adapter as ra                 # the adapter under test
_LAB = _REPO / "tools" / "membrane_scale_lab"
if str(_LAB) not in sys.path:
    sys.path.insert(0, str(_LAB))            # owners: import, never edit
from evidence_output import (
    EvidencePathExists,
    resolve_evidence_path,
)

EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"
TMP = EVID_DIR / "adapter_faults_tmp"
PACKET = _HERE / "example_packet.json"
QUAL = _HERE / "qualification_receipt.py"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _mutate(src: Path, dst: Path, fn) -> Path:
    data = _read_json(src)
    fn(data)
    _write_json(dst, data)
    return dst


def _verify(receipt, packet):
    return ra.verify_receipt(receipt, packet)


def _run(expected, receipt, packet):
    v = _verify(receipt, packet)
    observed = [r.split(":")[0] if isinstance(r, str) else r
                for r in v.refusals]
    return {"expected": expected, "observed": observed,
            "pass": set(expected) <= set(observed)}


def main() -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    genuine = TMP / "genuine_receipt.json"
    if not genuine.exists():
        r = subprocess.run(
            [sys.executable, str(QUAL), "--out", str(genuine)],
            capture_output=True, text=True, cwd=_REPO, timeout=600)
        if r.returncode != 0:
            print(f"FAIL: genuine receipt generation exit {r.returncode}\n{r.stdout}{r.stderr}")
            return 1
    receipt = _read_json(genuine)
    case0 = receipt["cases"][0]["case_id"]
    rows = []

    def check(name, expected, v):
        observed = [r.split(":")[0] for r in v.refusals]
        rows.append({"fault": name, "expected": expected,
                     "observed": observed,
                     "pass": set(expected) <= set(observed)})

    # F0 control: genuine pair -> PASS
    v = _verify(genuine, PACKET)
    rows.append({"fault": "F0_genuine_pair", "expected": [],
                 "observed": v.refusals, "pass": v.passed})

    # F1 receipt deleted
    missing = TMP / "deleted_receipt.json"
    if missing.exists():
        missing.unlink()
    rows.append({"fault": "F1_receipt_missing",
                 "expected": ["receipt_missing"],
                 "observed": _verify(missing, PACKET).refusals,
                 "pass": _verify(missing, PACKET).refusals == ["receipt_missing"]})

    # F2 one source hash byte changed (file untouched)
    def f2(d):
        k = next(iter(d["source_file_hashes"]))
        h = d["source_file_hashes"][k]
        d["source_file_hashes"][k] = ("0" if h[0] != "0" else "1") + h[1:]
    r2 = _mutate(genuine, TMP / "f2.json", f2)
    check("F2_solver_hash_mismatch", ["solver_hash_mismatch"],
          _verify(r2, PACKET))

    # F3 units length cm
    r3 = _mutate(genuine, TMP / "f3.json",
                 lambda d: d["units"].__setitem__("length", "cm"))
    check("F3_unit_mismatch", ["unit_mismatch"], _verify(r3, PACKET))

    # F4 holdout family also listed under train (packet copy -> digest also
    # fires; the split law is still evaluated against the packet as it is)
    def f4(d):
        d["frozen_splits"]["train"].append(
            d["frozen_splits"]["holdout"][0])
    p4 = _mutate(PACKET, TMP / "f4_packet.json", f4)
    check("F4_split_overlap", ["split_overlap"], _verify(genuine, p4))

    # F5 one output NaN
    def f5(d):
        d["cases"][0]["outputs"]["energy_J"] = float("nan")
    r5 = _mutate(genuine, TMP / "f5.json", f5)
    check("F5_nonfinite_output", ["nonfinite_output"], _verify(r5, PACKET))

    # F6a status step_limit
    def f6a(d):
        d["cases"][0]["status"] = "step_limit"
    r6a = _mutate(genuine, TMP / "f6a.json", f6a)
    check("F6a_unconverged_step_limit", ["unconverged_label"],
          _verify(r6a, PACKET))

    # F6b stagnated with residual above packet threshold
    def f6b(d):
        d["cases"][0]["outputs"]["max_free_residual_N"] = 1e-3
    r6b = _mutate(genuine, TMP / "f6b.json", f6b)
    check("F6b_unconverged_over_threshold", ["unconverged_label"],
          _verify(r6b, PACKET))

    # F7 family not in packet domain
    def f7(d):
        d["cases"].append({"case_id": "twisted", "family": "twisted_torus",
                           "status": "stationary",
                           "outputs": {"energy_J": 1.0,
                                       "max_free_residual_N": 0.0,
                                       "reactions_N": [[0.0, 0.0, 0.0]]},
                           "gpu_job": None})
    r7 = _mutate(genuine, TMP / "f7.json", f7)
    check("F7_out_of_domain", ["out_of_domain"], _verify(r7, PACKET))

    # F8 packet threshold widened after the receipt was written
    def f8(d):
        d["acceptance_thresholds"]["max_free_residual_N"] = 1e6
    p8 = _mutate(PACKET, TMP / "f8_packet.json", f8)
    check("F8_packet_digest_mismatch", ["packet_digest_mismatch"],
          _verify(genuine, p8))

    # F9 declared PASS while a receipt number exceeds the packet threshold
    def f9(d):
        d["cases"][0]["outputs"]["max_free_residual_N"] = 1e-3
    r9 = _mutate(genuine, TMP / "f9.json", f9)
    check("F9_verdict_forgery", ["verdict_forgery"], _verify(r9, PACKET))

    # F10a gpu_job reserved, no release
    def f10a(d):
        d["gpu_job"] = {"job_id": "gpu-1", "state": "reserved"}
    r10a = _mutate(genuine, TMP / "f10a.json", f10a)
    check("F10a_interrupted_gpu_job", ["interrupted_gpu_job"],
          _verify(r10a, PACKET))

    # F10b clean resume: real checkpoint file whose sha256 matches
    ck = TMP / "checkpoint.bin"
    ck.write_bytes(b"checkpoint-bytes-2026")
    def f10b(d):
        d["gpu_job"] = {"job_id": "gpu-1", "state": "reserved"}
        d["resume"] = {"checkpoint_path": str(ck),
                       "resumed_from_checkpoint_sha256": _sha256_file(ck)}
    r10b = _mutate(genuine, TMP / "f10b.json", f10b)
    v10b = _verify(r10b, PACKET)
    rows.append({"fault": "F10b_clean_resume", "expected": [],
                 "observed": v10b.refusals, "pass": v10b.passed})

    # F11 receipt carries absurd thresholds: packet values must rule
    def f11(d):
        d["acceptance_thresholds"] = {"max_free_residual_N": 1e9,
                                      "max_force_balance_residual": 1e9,
                                      "max_moment_balance_residual": 1e9}
        d["cases"][0]["outputs"]["max_free_residual_N"] = 1e-3
    r11 = _mutate(genuine, TMP / "f11.json", f11)
    check("F11_forged_thresholds_inert",
          ["unconverged_label", "verdict_forgery"], _verify(r11, PACKET))

    # F12 v2 balance residuals: a recorded balance residual above the packet
    # threshold under a declared PASS is forgery, recomputed from the PACKET.
    def f12(d):
        d["cases"][0]["outputs"]["max_force_balance_residual"] = 1e-3
    r12 = _mutate(genuine, TMP / "f12.json", f12)
    check("F12_balance_residual_forgery", ["verdict_forgery"],
          _verify(r12, PACKET))

    # F13 P5 composition: a v0/unknown composed schema is refused explicitly,
    # never silently upgraded (the adapter accepts exactly
    # chimera-mechanism-factory-composed-qualification-v1 alongside v2).
    def f13(d):
        d["schema"] = "chimera-mechanism-factory-composed-qualification-v0"
    r13 = _mutate(genuine, TMP / "f13.json", f13)
    check("F13_unknown_composed_schema", ["receipt_schema_unsupported"],
          _verify(r13, PACKET))

    all_passed = all(row["pass"] for row in rows)
    fault_receipt = {
        "schema": "chimera-mechanism-factory-adapter-faults-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "adapter_version": ra.ADAPTER_VERSION,
        "accepted_schema": ra.ACCEPTED_RECEIPT_SCHEMA,
        "accepted_composed_schema": ra.COMPOSED_RECEIPT_SCHEMA,
        "genuine_receipt_sha256": _sha256_file(genuine),
        "packet_sha256": _sha256_file(PACKET),
        "faults": rows,
        "all_passed": all_passed,
    }
    out = resolve_evidence_path(EVID_DIR, "adapter_faults", sys.argv[1:])
    _write_json(out, fault_receipt)
    for row in rows:
        print(f"{row['fault']}: expected={row['expected']} "
              f"observed={row['observed']} -> "
              f"{'OK' if row['pass'] else 'FAIL'}")
    print(f"fault receipt: {out}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except EvidencePathExists as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)
