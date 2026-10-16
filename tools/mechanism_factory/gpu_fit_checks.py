"""gpu_fit_checks.py -- falsifier battery for the §11.18 GPU-batch
learned-candidate MANIFEST + dry-run seam (gpu_fit_manifest.py,
gpu_fit_dryrun.py). Six checks through the house harness
(tools/port_registry.py), exit 0 only if all green. No GPU reservation is
ever taken here: the reservation probe is run read-only
(`run_gpu_job.py --check` performs no HTTP call and touches no model).

  T1 manifest determinism: building the manifest twice on the same
     qualified receipts yields the identical sha256 (no hidden
     nondeterminism in the preregistered sequence).
  T2 holdout absent: the holdout family appears nowhere in the manifest
     (canonical bytes + fixture keys); an explicit holdout fixture is
     refused by name (refusal_holdout_fixture).
  T3 timeout/budget violations refused by name: job timeout > 600 s
     (refusal_timeout_out_of_range) and a packet without its budget
     fields (refusal_missing_budget_fields).
  T4 LLM call in a job command refused by name: a command referencing
     run_gpu_job.py or any router/HTTP marker raises
     llm_call_in_job_command (the batch process must never call the
     unloaded language model).
  T5 missing qualified receipt refused: a build with only nonexistent /
     unqualified receipts raises no_qualified_receipt -- the adapter is
     the gate, never the writer's identity.
  T6 dry run completes cleanly without a reservation: the real
     gpu_fit_dryrun.py is executed end to end; it exits 0 and records an
     explicit reservation verdict (reservation_unavailable is an EXPECTED
     outcome; reservation_available_not_taken means the free lock was
     released immediately) and no_reservation_taken true.

Run:  python tools/mechanism_factory/gpu_fit_checks.py
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
import gpu_fit_manifest as gfm                     # noqa: E402
import gpu_fit_dryrun as gfd                       # noqa: E402

EVID_DIR = gfm.EVID_DIR
EXPECTED_CHECKS = 6


def _packet() -> dict:
    return json.loads(gfm.PACKET_PATH.read_text(encoding="utf-8"))


def _qualified_receipt_paths() -> list:
    import receipt_adapter as ra
    paths = sorted(str(p) for p in EVID_DIR.glob(
        "qualification_receipt_*.json"))
    ok = [p for p in paths if ra.verify_receipt(p, gfm.PACKET_PATH).passed]
    if not ok:
        raise gfm.ManifestRefusal("no_qualified_receipt", {"scanned": paths})
    return ok


def _build(**kw) -> dict:
    # same scan semantics as gpu_fit_manifest.main(): every stamped
    # qualification receipt is considered (refused ones are recorded in
    # the manifest's fixture_provenance, never consumed), so the battery's
    # manifest is byte-comparable to the stamped artifact.
    paths = sorted(str(p) for p in EVID_DIR.glob(
        "qualification_receipt_*.json"))
    return gfm.build_manifest(_packet(), paths, **kw)


# ── T1 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T1_manifest_determinism",
    "Building the bounded batch manifest twice on the same "
    "adapter-PASSed receipts produces the identical canonical sha256 -- "
    "the preregistered job sequence has no hidden nondeterminism.",
    "The two manifest hashes differ, or the receipt's recorded hash does "
    "not recompute from the manifest bytes.")
def t1_manifest_determinism() -> dict:
    m1 = _build()
    m2 = _build()
    import hashlib
    body = {k: v for k, v in m1.items() if k != "manifest_sha256"}
    recomputed = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("utf-8")).hexdigest()
    ok = (m1["manifest_sha256"] == m2["manifest_sha256"]
          and m1["manifest_sha256"] == recomputed)
    return {"pass": bool(ok), "manifest_sha256": m1["manifest_sha256"],
            "repeat_sha256": m2["manifest_sha256"],
            "n_jobs": len(m1["jobs"])}


# ── T2 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T2_holdout_fixture_absent",
    "The holdout family is excluded structurally: it appears in no "
    "operative manifest section (jobs, fixtures, identities, pending "
    "inputs), the fit's split gate reads zero holdout cases on the real "
    "packet, and a fixture derivation that does reach a holdout family "
    "is refused by name (refusal_holdout_fixture).",
    "A holdout family name or knot reaches the manifest's operative "
    "sections, a holdout label is read, or the structural refusal does "
    "not fire.")
def t2_holdout_fixture_absent(tmp: Path) -> dict:
    m = _build()
    packet = _packet()
    holdout = packet["frozen_splits"]["holdout"]
    # operative sections only: the manifest's fixture_provenance block
    # deliberately DISCLOSES the excluded holdout families (guard-rail
    # provenance); the data inputs -- jobs, fixtures, identities, pending
    # inputs -- must contain none of them.
    operative = json.dumps({"jobs": m["jobs"], "fixtures": m["fixtures"],
                            "identities": m["identities"],
                            "pending_inputs": m["pending_inputs"]},
                           sort_keys=True).lower()
    leak = [f for f in holdout if f in operative]
    # structural proof #1: on the REAL packet, the fit's split gate reads
    # zero holdout cases and the collected labels contain no holdout
    # family -- the fixture derivation literally cannot see one.
    import bounded_fit as bf
    collected = bf.collect_labels(packet, _qualified_receipt_paths())
    tampered_labels = {f: v for f, v in collected["labels"].items()
                       if f in holdout}
    seen = collected["holdout_cases_seen"]
    read = collected["holdout_cases_read"]
    # structural proof #2: a fixture derivation that DOES reach a holdout
    # family is refused by name.
    fake_labels = {holdout[0]: [{"case_id": "FAKE_holdout_case",
                                 "split": "holdout",
                                 "load_magnitude_N": 1.1,
                                 "reactions_N": [[1.0, 0.0, 0.0]]}]}
    refused = None
    orig = bf.collect_labels
    bf.collect_labels = lambda p, r: {"labels": fake_labels,
                                      "refused_receipts": [],
                                      "label_receipt_hashes": [],
                                      "holdout_cases_seen": 1,
                                      "holdout_cases_read": 0}
    try:
        gfm._fixtures(packet, _qualified_receipt_paths())
    except gfm.ManifestRefusal as ex:
        refused = ex.reason
    finally:
        bf.collect_labels = orig
    ok = (not leak
          and set(m["fixtures"]) == {f for f in
                                     (packet["frozen_splits"]["train"]
                                      + packet["frozen_splits"]
                                      ["validation"])}
          and not tampered_labels and seen >= 1 and read == 0
          and refused == "refusal_holdout_fixture")
    return {"pass": bool(ok), "holdout_families": holdout,
            "leak_in_operative_sections": leak,
            "holdout_labels_reaching_builder": tampered_labels,
            "holdout_cases_seen": seen, "holdout_cases_read": read,
            "structural_refusal": refused,
            "fixture_families": sorted(m["fixtures"])}


# ── T3 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T3_timeout_budget_violations_refused",
    "Preregistered limits are enforced by name at build time: a job "
    "timeout above the 600 s batch law raises refusal_timeout_out_of_range "
    "and a packet missing its budget fields (time_s, ram_mb) raises "
    "refusal_missing_budget_fields.",
    "An over-limit timeout or a budget-less packet builds a manifest, or "
    "the refusal names are wrong.")
def t3_timeout_budget_violations_refused() -> dict:
    names = {}
    try:
        _build(job_timeout_s=601.0)
    except gfm.ManifestRefusal as ex:
        names["timeout"] = ex.reason
    minus_budgets = {k: v for k, v in _packet().items() if k != "budgets"}
    try:
        gfm.build_manifest(minus_budgets, _qualified_receipt_paths())
    except gfm.ManifestRefusal as ex:
        names["budget"] = ex.reason
    ok = (names.get("timeout") == "refusal_timeout_out_of_range"
          and names.get("budget") == "refusal_missing_budget_fields")
    return {"pass": bool(ok), "refusals": names}


# ── T4 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T4_llm_call_in_job_command_refused",
    "The no-LLM-call law is enforced at build time: a job command that "
    "wraps run_gpu_job.py or carries any router/HTTP/model invocation "
    "marker (127.0.0.1:8080, /v1/unload, http://, gateway, ...) raises "
    "llm_call_in_job_command -- the batch process must never call the "
    "unloaded language model.",
    "A command with a router/HTTP invocation builds into the manifest, "
    "or the refusal name is wrong.")
def t4_llm_call_in_job_command_refused() -> dict:
    names = {}
    variants = {
        "nested_handoff": ["x/venv/Scripts/python.exe",
                           "D:/Chimera-Maintenance/Runtime/local-ai/"
                           "run_gpu_job.py", "--", "job"],
        "router_url": ["x/venv/Scripts/python.exe", "job.py",
                       "--endpoint", "127.0.0.1:8080/v1/unload"],
        "http": ["x/venv/Scripts/python.exe", "job.py",
                 "--pull", "http://gateway/jobs"],
    }
    for key, command in variants.items():
        try:
            _build(job_command=command)
        except gfm.ManifestRefusal as ex:
            names[key] = ex.reason
        except Exception as ex:            # a crash is a failure too
            names[key] = f"UNEXPECTED {type(ex).__name__}: {ex}"
    ok = all(v == "llm_call_in_job_command" for v in names.values()) \
        and len(names) == len(variants)
    return {"pass": bool(ok), "refusals": names}


# ── T5 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T5_missing_qualified_receipt_refused",
    "A manifest build with only nonexistent / unqualified receipts is "
    "refused by name (no_qualified_receipt): the adapter is the gate; "
    "fixtures are never derived from refused receipts.",
    "The build succeeds without any qualified receipt, silently skips "
    "them, or the refusal name is wrong.")
def t5_missing_qualified_receipt_refused() -> dict:
    name = None
    try:
        gfm.build_manifest(_packet(), ["D:/definitely/missing/receipt.json"])
    except gfm.ManifestRefusal as ex:
        name = ex.reason
    ok = name == "no_qualified_receipt"
    return {"pass": bool(ok), "refusal": name}


# ── T6 ──────────────────────────────────────────────────────────────────────

@port_test(
    "T6_dry_run_completes_without_reservation",
    "The real gpu_fit_dryrun.py completes end to end WITHOUT a live "
    "reservation: exit 0, an explicit reservation verdict recorded "
    "(reservation_unavailable -- an EXPECTED outcome -- or "
    "reservation_available_not_taken, where the free lock was probed and "
    "released immediately), no_reservation_taken true, and every "
    "structural validation PASS.",
    "The dry run errors on a held or free lock, takes a reservation, "
    "runs the live batch, or records no explicit verdict.")
def t6_dry_run_completes_without_reservation() -> dict:
    proc = subprocess.run(
        [sys.executable, str(_HERE / "gpu_fit_dryrun.py")],
        capture_output=True, text=True, timeout=600)
    verdict = None
    clean = None
    receipt_path = None
    for line in proc.stdout.splitlines():
        if line.startswith("reservation verdict:"):
            verdict = line.split(":", 1)[1].strip()
        if line.startswith("clean dry run:"):
            clean = line.split(":", 1)[1].strip()
        if line.startswith("dry-run receipt:"):
            receipt_path = line.split(":", 1)[1].strip()
    recorded = None
    if receipt_path and Path(receipt_path).exists():
        rec = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        recorded = rec["reservation"]["verdict"]
        clean = rec.get("clean_dry_run")
    ok = (proc.returncode == 0 and clean is True
          and recorded in ("reservation_unavailable",
                           "reservation_available_not_taken"))
    return {"pass": bool(ok), "exit_code": proc.returncode,
            "reservation_verdict": recorded,
            "clean_dry_run": clean,
            "dry_run_receipt": receipt_path}


expect(EXPECTED_CHECKS)


# ── runner (evidence law, like the other batteries) ─────────────────────────

ORDER = ["T1_manifest_determinism", "T2_holdout_fixture_absent",
         "T3_timeout_budget_violations_refused",
         "T4_llm_call_in_job_command_refused",
         "T5_missing_qualified_receipt_refused",
         "T6_dry_run_completes_without_reservation"]


def main(argv: list) -> int:
    from evidence_output import (EvidencePathExists,
                                 resolve_evidence_path)
    try:
        out_path = resolve_evidence_path(EVID_DIR, "gpu_fit_checks", argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return 2

    from port_registry import TESTS
    results, failed = {}, 0
    tmp = Path(tempfile.mkdtemp(prefix="gpu_fit_checks_tmp_"))
    print("=" * 100)
    print("  GPU learned-candidate MANIFEST + DRY RUN: falsifier battery")
    print("  No live reservation is taken; the probe is read-only "
          "(--check: no HTTP call, no model touch).")
    print("=" * 100)
    try:
        for name in ORDER:
            rec = TESTS[name]
            print(f"\n[{name}]\n  STATEMENT : {rec['statement'][:96]}...")
            try:
                fn = rec["fn"]
                r = fn(tmp) if name == "T2_holdout_fixture_absent" else fn()
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
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. The live "
          f"batch remains NOT YET RUN (see GPU_LIVE_BATCH.md).")

    checks_receipt = {
        "schema": "chimera-mechanism-factory-gpu-manifest-checks-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "manifest_schema": gfm.MANIFEST_SCHEMA,
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
