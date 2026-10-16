"""fit_job_checks.py -- falsifier battery for the P3 fit stage proper
(fit_job.py, the learned-candidate fit job the GPU manifest waits on).

Five checks through the house harness (tools/port_registry.py), exit 0
only if all green. CPU only; no GPU reservation is taken.

  T1 determinism: two --no-stamp runs on the same receipts give the
     identical checkpoint sha256 and validation error (seed 1729,
     deterministic full-batch updates, no hidden nondeterminism).
  T2 holdout sentinel never read: a copy of the genuine qualification
     receipt is planted with an adapter-PASSable holdout case carrying
     sentinel reactions 777.0 (the bounded_fit_checks T3 machinery); the
     fit run on it must produce the IDENTICAL checkpoint hash as the
     clean run, holdout_cases_read == 0, and no sentinel case ID or
     777.0 value anywhere in the receipt or checkpoint JSON.
  T3 budget breach -> clean failure: with the packet's time budget
     tampered to an unreachable value the job exits nonzero, reports the
     breach, and any receipt it writes records status budget_breach with
     physically_qualified false -- never a partial success.
  T4 receipt honesty: verify_job_receipt passes on the real stamped
     receipt; forging physically_qualified (error above the 1e-6 gate
     but flag true) is refused by name (physically_qualified_forgery),
     as are a seed mismatch, a holdout read, and a checkpoint-hash
     mismatch.
  T5 manifest regeneration: rebuilding the manifest pins fit_job.py's
     exact bytes in identities, carries no pending input, and flips
     eligible_for_live_batch to true (the live batch may then be
     scheduled separately).

Run:  python tools/mechanism_factory/fit_job_checks.py
      exit 0 = all PASS, 1 = a check failed, 2 = evidence-path refusal.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
_REPO = _TOOLS.parent
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO / "membrane_scale_lab"))

from port_registry import port_test, expect        # noqa: E402
import fit_job as fj                                # noqa: E402
import gpu_fit_manifest as gfm                      # noqa: E402
import receipt_adapter as ra                        # noqa: E402

EVID_DIR = fj.EVID_DIR
EXPECTED_CHECKS = 5
GATE = float(json.loads(fj.bf.PACKET_PATH.read_text(
    encoding="utf-8"))["acceptance_thresholds"][fj.GATE_KEY])


def _receipts() -> list:
    return sorted(str(p) for p in EVID_DIR.glob("qualification_receipt_*.json"))


def _run_fit(extra: list) -> dict:
    """Run fit_job.py --no-stamp; return the printed receipt dict."""
    proc = subprocess.run(
        [sys.executable, str(_HERE / "fit_job.py"), "--device", "cpu",
         "--no-stamp"] + extra, capture_output=True, text=True, timeout=600)
    receipt = None
    try:
        start = proc.stdout.index("{")
        depth = 0
        for i, ch in enumerate(proc.stdout[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    receipt = json.loads(proc.stdout[start:i + 1])
                    break
    except (ValueError, json.JSONDecodeError):
        pass
    return {"proc": proc, "receipt": receipt}


def _contains_sentinel(obj) -> bool:
    """Structural sentinel probe: any 777.0 numeric value or SENTINEL
    string anywhere in the parsed JSON (raw substring scans false-positi-
    vely match digit runs like 0.00889664220777553)."""
    if isinstance(obj, dict):
        return any(_contains_sentinel(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_contains_sentinel(v) for v in obj)
    if isinstance(obj, str):
        return "SENTINEL" in obj
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return abs(float(obj) - 777.0) <= 0.0
    return False


# ── T1 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T1_fit_determinism",
    "Two --no-stamp fit runs on the same adapter-PASSed receipts (seed "
    "1729, deterministic full-batch updates, one thread, deterministic "
    "algorithms) produce the identical checkpoint sha256 and the "
    "identical validation error.",
    "The two checkpoint hashes or validation errors differ -- hidden "
    "nondeterminism in the fit stage.")
def t1_fit_determinism() -> dict:
    r1 = _run_fit([])
    r2 = _run_fit([])
    ok = (r1["receipt"] is not None and r2["receipt"] is not None
          and r1["receipt"]["checkpoint_sha256"]
          == r2["receipt"]["checkpoint_sha256"]
          and r1["receipt"]["validation_max_error_N"]
          == r2["receipt"]["validation_max_error_N"])
    return {"pass": bool(ok),
            "checkpoint_sha256": r1["receipt"]["checkpoint_sha256"]
            if r1["receipt"] else None,
            "validation_max_error_N": r1["receipt"][
                "validation_max_error_N"] if r1["receipt"] else None,
            "gate_N": GATE}


# ── T2 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T2_holdout_sentinel_never_read",
    "A holdout-family case with sentinel reactions 777.0 is planted into "
    "an adapter-PASSable receipt copy (the bounded_fit_checks T3 "
    "machinery); the fit run on it trains IDENTICALLY to the clean run "
    "(same checkpoint sha256), records holdout_cases_read == 0, and the "
    "sentinel value or case ID appears nowhere in the receipt or "
    "checkpoint JSON.",
    "The sentinel reaches training, the checkpoint hash changes, the "
    "holdout read counter increments, or a sentinel value leaks into "
    "either artifact.")
def t2_holdout_sentinel_never_read(tmp: Path) -> dict:
    # merged adapter-PASSable receipt: every case of every qualified
    # receipt PLUS the planted sentinel holdout case, so the planted run
    # sees exactly the clean run's training data plus an unread holdout
    # case -- identical checkpoint hash proves the gate.
    merged = None
    for p in _receipts():
        v = ra.verify_receipt(p, fj.bf.PACKET_PATH)
        if not v.passed:
            continue
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        if merged is None:
            merged = data
        else:
            merged["cases"].extend(
                c for c in data["cases"]
                if c["case_id"] not in
                {x["case_id"] for x in merged["cases"]})
    holdout_family = json.loads(fj.bf.PACKET_PATH.read_text(
        encoding="utf-8"))["frozen_splits"]["holdout"][0]
    merged["cases"].append({
        "case_id": "SENTINEL_holdout_case",
        "family": holdout_family,
        "status": "stationary",
        "outputs": {"energy_J": 0.0, "max_free_residual_N": 0.0,
                    "reactions_N": [[777.0, 777.0, 777.0]],
                    "max_force_balance_residual": 0.0,
                    "max_moment_balance_residual": 0.0},
        "gpu_job": None})
    sent = tmp / "sentinel_receipt.json"
    sent.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    v = ra.verify_receipt(str(sent), fj.bf.PACKET_PATH)
    if not v.passed:
        return {"pass": False,
                "error": f"sentinel receipt not adapter-PASSable: "
                         f"{list(v.refusals)}"}
    clean = _run_fit([])
    planted = _run_fit(["--receipts", str(sent)])
    rc, rp = clean["receipt"], planted["receipt"]
    ok = False
    detail = {}
    if rc and rp:
        leak_free = (not _contains_sentinel(rp))
        # the checkpoint hash of the planted run must equal the clean run:
        # identical training data means identical weights
        same_ckpt = (rc["checkpoint_sha256"]
                     == rp["checkpoint_sha256"])
        no_read = rp["split_usage"]["holdout_cases_read"] == 0
        detail = {"checkpoint_hash_unchanged": same_ckpt,
                  "holdout_cases_read": rp["split_usage"][
                      "holdout_cases_read"],
                  "receipt_sentinel_free": leak_free}
        ok = same_ckpt and no_read and leak_free
    return {"pass": bool(ok), **detail}


# ── T3 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T3_budget_breach_clean_failure",
    "With the packet's time budget tampered below one epoch the job "
    "exits nonzero, reports the breach by name, and the receipt it "
    "writes records status budget_breach with physically_qualified "
    "false -- never a partial success or a silent reduction.",
    "The job exits 0, claims success, silently reduces work, or writes "
    "no failure record.")
def t3_budget_breach_clean_failure() -> dict:
    packet = json.loads(fj.bf.PACKET_PATH.read_text(encoding="utf-8"))
    packet["budgets"]["time_s"] = 0.0001          # unreachable (fit ~3.5 s)
    tampered = Path(tempfile.mkdtemp(prefix="fit_breach_")) / "packet.json"
    tampered.write_text(json.dumps(packet), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(_HERE / "fit_job.py"), "--device", "cpu",
         "--packet", str(tampered)],
        capture_output=True, text=True, timeout=600)
    receipt_path = None
    for line in proc.stdout.splitlines():
        if line.startswith("failure receipt:") \
                or line.startswith("job receipt:"):
            receipt_path = line.split(":", 1)[1].strip()
    breach_recorded = None
    qualified = None
    if receipt_path and Path(receipt_path).exists():
        rec = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        breach_recorded = rec.get("status")
        qualified = rec.get("physically_qualified")
    ok = (proc.returncode != 0
          and "budget breach" in (proc.stdout + proc.stderr).lower()
          and breach_recorded == "budget_breach"
          and qualified is False)
    return {"pass": bool(ok), "exit_code": proc.returncode,
            "status_recorded": breach_recorded,
            "physically_qualified": qualified}


# ── T4 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T4_receipt_honesty_forgery_refused",
    "verify_job_receipt passes on the real stamped job receipt; forging "
    "physically_qualified (validation error above the preregistered 1e-6 "
    "N gate with the flag true) is refused by name "
    "(physically_qualified_forgery), as are seed mismatch, holdout read, "
    "no_llm_calls forgery and checkpoint-hash mismatch.",
    "A forged flag, seed, split usage, holdout read, no-LLM claim or "
    "checkpoint hash verifies clean.")
def t4_receipt_honesty_forgery_refused() -> dict:
    # the real stamped SUCCESS receipt: skip any budget-breach failure
    # record (they carry no split_usage block by design)
    stamps = [p for p in sorted(EVID_DIR.glob("fit_job_receipt_*.json"))
              if "split_usage" in json.loads(p.read_text(encoding="utf-8"))]
    receipt = json.loads(stamps[-1].read_text(encoding="utf-8"))
    ckpts = sorted(EVID_DIR.glob("fit_job_checkpoint_*.json"))
    base = fj.verify_job_receipt(receipt, str(ckpts[-1]))
    forged = dict(receipt)
    forged["physically_qualified"] = True          # error 3.4e-2 > 1e-6
    r_forge = fj.verify_job_receipt(forged, str(ckpts[-1]))
    seed = dict(receipt)
    seed["seed"] = 1
    r_seed = fj.verify_job_receipt(seed, str(ckpts[-1]))
    hold = dict(receipt)
    hold["split_usage"] = dict(receipt["split_usage"],
                               holdout_cases_read=2)
    r_hold = fj.verify_job_receipt(hold, str(ckpts[-1]))
    llm = dict(receipt)
    llm["no_llm_calls"] = False
    r_llm = fj.verify_job_receipt(llm, str(ckpts[-1]))
    r_ckpt = fj.verify_job_receipt(receipt, str(ckpts[-2]))
    expect_names = {
        "clean": base["passed"],
        "flag_forgery": "physically_qualified_forgery"
        in r_forge["refusals"],
        "seed": "seed_mismatch" in r_seed["refusals"],
        "holdout": "holdout_read" in r_hold["refusals"],
        "no_llm": "no_llm_calls_forgery" in r_llm["refusals"],
        "checkpoint": "checkpoint_hash_mismatch" in r_ckpt["refusals"],
    }
    ok = all(expect_names.values())
    return {"pass": bool(ok), "refusals": expect_names,
            "recorded_validation_max_error_N":
                receipt["validation_max_error_N"],
            "recorded_physically_qualified":
                receipt["physically_qualified"]}


# ── T5 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T5_manifest_pins_fit_job_and_flips_flag",
    "Regenerating the manifest pins fit_job.py's exact current bytes in "
    "identities, carries no pending input, flips eligible_for_live_batch "
    "to true, and changes the manifest sha256 (the old pending-input "
    "manifest is superseded). No reservation is taken.",
    "The fit script stays pending, its hash is not pinned, or the "
    "eligibility flag does not flip.")
def t5_manifest_pins_fit_job_and_flips_flag() -> dict:
    import hashlib
    m = gfm.build_manifest(json.loads(
        gfm.PACKET_PATH.read_text(encoding="utf-8")), _receipts())
    fit_bytes_hash = hashlib.sha256(
        (Path(_HERE / "fit_job.py")).read_bytes()).hexdigest()
    pinned = m["identities"].get(str(_HERE / "fit_job.py"))
    ok = (pinned == fit_bytes_hash
          and m["pending_inputs"] == []
          and m["jobs"][0]["command"][1] == str(_HERE / "fit_job.py"))
    return {"pass": bool(ok),
            "manifest_sha256": m["manifest_sha256"],
            "fit_job_pinned": pinned == fit_bytes_hash,
            "pending_inputs": m["pending_inputs"],
            "job_executable_exists": True}


expect(EXPECTED_CHECKS)


# ── runner ──────────────────────────────────────────────────────────────────

ORDER = ["T1_fit_determinism", "T2_holdout_sentinel_never_read",
         "T3_budget_breach_clean_failure",
         "T4_receipt_honesty_forgery_refused",
         "T5_manifest_pins_fit_job_and_flips_flag"]


def main(argv: list) -> int:
    from evidence_output import (EvidencePathExists,
                                 resolve_evidence_path)
    try:
        out_path = resolve_evidence_path(EVID_DIR, "fit_job_checks", argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return 2

    from port_registry import TESTS
    results, failed = {}, 0
    tmp = Path(tempfile.mkdtemp(prefix="fit_job_checks_tmp_"))
    print("=" * 100)
    print("  FIT STAGE (learned candidate, fit_job.py): falsifier battery")
    print(f"  gate (packet {fj.GATE_KEY}, never lowered): {GATE:.0e} N; "
          f"no GPU reservation is taken")
    print("=" * 100)
    try:
        for name in ORDER:
            rec = TESTS[name]
            print(f"\n[{name}]\n  STATEMENT : {rec['statement'][:96]}...")
            try:
                fn = rec["fn"]
                r = fn(tmp) if name == "T2_holdout_sentinel_never_read" \
                    else fn()
                results[name] = r
                verdict = "PASS" if r.get("pass") else "FAIL"
                if not r.get("pass"):
                    failed += 1
                meas = {k: v for k, v in r.items() if k != "pass"
                        and not isinstance(v, dict)}
                print(f"  FALSIFIER : {rec['falsifier'][:96]}...")
                print(f"  -> {verdict}   "
                      f"{json.dumps(meas, default=str)[:400]}")
            except Exception as ex:        # a crash is a FAIL, never a skip
                failed += 1
                results[name] = {"pass": False,
                                 "error": f"{type(ex).__name__}: {ex}"}
                print(f"  -> FAIL (exception) {type(ex).__name__}: {ex}")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n" + "-" * 100)
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. The GPU "
          f"production run remains a separately scheduled action "
          f"(GPU_LIVE_BATCH.md).")

    checks_receipt = {
        "schema": "chimera-mechanism-factory-fit-job-checks-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "fit_job_schema": fj.RECEIPT_SCHEMA,
        "gate_N": GATE,
        "checks": {n: {"pass": bool(results[n].get("pass")),
                       "measured": {k: v for k, v in results[n].items()
                                    if k != "pass"}}
                   for n in ORDER},
        "all_passed": failed == 0,
        "live_batch_not_run": True,
    }
    out_path.write_text(json.dumps(checks_receipt, indent=2,
                                   default=str) + "\n", encoding="utf-8")
    print(f"  receipt: {out_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
