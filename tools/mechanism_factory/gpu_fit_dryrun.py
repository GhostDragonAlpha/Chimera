"""gpu_fit_dryrun.py -- validates the §11.18 learned-candidate GPU-batch
manifest WITHOUT reserving the GPU. The live batch is a separately
scheduled action; a dry run never unloads, never loads and never holds a
reservation beyond the momentary `run_gpu_job.py --check` lock probe (whose
check path performs no HTTP call and touches no model).

Validated, in order:
  1. manifest schema: reparsed and re-validated through gpu_batch.load_plan
     (the runner's own law: nonempty jobs, absolute executables, no nested
     run_gpu_job.py, timeout 0..600 s, available cwd, identities match the
     files on disk);
  2. absolute executable paths exist; per-job timeouts within range;
  3. memory/time/disk budget fields present (packet budgets verbatim);
  4. fixture list matches the qualified receipts: every label receipt is
     re-run through receipt_adapter.verify_receipt (PASS required) and the
     train/validation knots are recomputed via bounded_fit and compared
     exactly; the holdout family must be absent;
  5. no-LLM-call law: no job command or cwd contains any router/HTTP/model
     invocation marker (the batch process must not call the unloaded model);
  6. reservation probe: `run_gpu_job.py --check` is invoked read-only.
     Exit 75 (lock held) -> reservation_unavailable, an EXPECTED dry-run
     outcome, never an error. Exit 0 -> the reservation is currently free
     and was NOT taken (the check path releases immediately). Any other
     exit is a dry-run failure.

Exit 0 clean dry run (reservation verdict recorded) / 1 validation failure
(named) / 2 evidence-path refusal. CPU only.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "membrane_scale_lab"))

import bounded_fit as bf
import gpu_fit_manifest as gfm
import receipt_adapter as ra
from evidence_output import (EvidencePathExists, resolve_evidence_path)

RUN_GPU_JOB = gfm.RUN_GPU_JOB
EVID_DIR = gfm.EVID_DIR
DRYRUN_SCHEMA = "chimera-mechanism-factory-gpu-dryrun-v1"


class DryRunRefusal(Exception):
    def __init__(self, reason: str, detail: dict | None = None):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail or {}


def _load_gpu_batch_module():
    # gpu_batch.py does `import run_gpu_job`, which resolves only from its
    # own directory -- put that directory on sys.path first.
    runtime = str(gfm.GPU_BATCH.parent)
    if runtime not in sys.path:
        sys.path.insert(0, runtime)
    spec = importlib.util.spec_from_file_location(
        "gpu_batch_ref", str(gfm.GPU_BATCH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gpu_batch_ref"] = mod
    spec.loader.exec_module(mod)          # imports run_gpu_job + controller
    return mod


def _probe_reservation() -> dict:
    """Read-only `run_gpu_job.py --check`. The check path performs no HTTP
    call and touches no model; exit 75 means the lock is held."""
    proc = subprocess.run(
        [sys.executable, str(RUN_GPU_JOB), "--check"],
        capture_output=True, text=True, timeout=120)
    if proc.returncode == 0:
        return {"verdict": "reservation_available_not_taken",
                "exit_code": 0,
                "note": "the reservation is currently free; the check "
                        "path released the momentary lock immediately; "
                        "no unload, load or inference call was made"}
    if proc.returncode == 75:
        return {"verdict": "reservation_unavailable",
                "exit_code": 75,
                "note": "EXPECTED dry-run outcome: an exclusive "
                        "reservation is held elsewhere; the live batch "
                        "must be scheduled separately"}
    return {"verdict": "probe_unexpected_exit", "exit_code": proc.returncode,
            "stderr": proc.stderr[-400:]}


def validate(manifest: dict) -> dict:
    rows = {}
    # 1. schema: through the runner's own load_plan (its law: nonempty
    #    jobs, absolute executables, no nested run_gpu_job.py, timeout
    #    0..600 s, available cwd, identities match the files on disk)
    gpu_batch = _load_gpu_batch_module()
    import os
    import tempfile
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as fh:
            json.dump(manifest, fh)
            tmp = fh.name
        try:
            gpu_batch.load_plan(Path(tmp))
        finally:
            os.unlink(tmp)
        rows["manifest_schema"] = {
            "pass": True,
            "note": "gpu_batch.load_plan accepted the manifest "
                    "(jobs/identities/cwd/timeout law)"}
    except (ValueError, OSError) as ex:
        rows["manifest_schema"] = {"pass": False,
                                   "reason": "manifest_schema_invalid",
                                   "error": str(ex)}
    # identities must match the files on disk (load_plan already checked);
    # record them for the receipt
    rows["identities"] = {"pass": True,
                          "n_pinned_inputs": len(manifest.get("identities",
                                                              {}))}
    # 2. absolute executable paths exist; timeouts in range
    bad_paths, bad_timeouts = [], []
    for job in manifest["jobs"]:
        exe = job["command"][0]
        if not Path(exe).is_absolute() or not Path(exe).exists():
            bad_paths.append(exe)
        if not 0 < float(job.get("timeout", 300)) <= 600.0:
            bad_timeouts.append(job.get("timeout"))
    rows["paths_and_timeouts"] = {
        "pass": not bad_paths and not bad_timeouts,
        "bad_executables": bad_paths, "bad_timeouts": bad_timeouts}
    # 3. budgets present
    budget = manifest["jobs"][0].get("budgets") or {}
    missing = [k for k in ("packet_time_s", "packet_ram_mb", "max_vram_mib",
                           "min_free_vram_mib", "evidence_disk_mb")
               if k not in budget]
    rows["budgets"] = {"pass": not missing, "missing_fields": missing,
                       "budgets": budget}
    # 4. fixture list matches the qualified receipts; holdout absent
    packet = json.loads(bf.PACKET_PATH.read_text(encoding="utf-8"))
    holdout = set(packet["frozen_splits"]["holdout"])
    label_receipts = manifest["fixture_provenance"]["label_receipts"]
    bad_receipts = []
    for path in label_receipts:
        v = ra.verify_receipt(path, bf.PACKET_PATH)
        if not v.passed:
            bad_receipts.append({"receipt": path,
                                 "adapter_refusals": list(v.refusals)})
    collected = bf.collect_labels(packet, label_receipts)
    table = bf.build_table(packet, collected)
    expected = {f: sorted(p["load_magnitude_N"]
                          for p in table["families"][f]["points"])
                for f in table["families"]}
    found = {f: sorted(v["load_magnitudes_N"])
             for f, v in manifest["fixtures"].items()}
    splits_ok = all(v["split"] in bf.FIT_SPLITS
                    for v in manifest["fixtures"].values())
    holdout_leak = bool(holdout & set(manifest["fixtures"]))
    rows["fixtures"] = {
        "pass": (not bad_receipts and expected == found
                 and splits_ok and not holdout_leak),
        "bad_label_receipts": bad_receipts,
        "expected_knots": expected, "manifest_knots": found,
        "holdout_families": sorted(holdout),
        "holdout_absent": not holdout_leak,
        "splits_ok": splits_ok}
    # 5. no-LLM-call law over every command and cwd
    violations = []
    for job in manifest["jobs"]:
        try:
            gfm._no_llm_calls(job["command"], job.get("cwd", ""))
        except gfm.ManifestRefusal as ex:
            violations.append({"marker": ex.detail.get("marker"),
                               "text": ex.detail.get("text")})
    rows["no_llm_calls"] = {"pass": not violations,
                            "violations": violations,
                            "n_markers": len(gfm.FORBIDDEN_MARKERS)}
    # 6. reservation probe (read-only)
    rows["reservation"] = _probe_reservation()
    ok = all(v.get("pass", True) for k, v in rows.items()
             if k not in ("reservation", "identities"))
    clean_probe = rows["reservation"]["verdict"] in (
        "reservation_unavailable", "reservation_available_not_taken")
    return {"all_validations_pass": bool(ok), "clean_probe": clean_probe,
            "rows": rows}


def main(argv: list) -> int:
    import re
    stamp = re.compile(r"gpu_fit_manifest_\d{8}T\d{6}.*\.json$")
    paths = sorted(p for p in EVID_DIR.glob("gpu_fit_manifest_*.json")
                   if stamp.match(p.name))
    target = None
    if "--manifest" in argv:
        target = argv[argv.index("--manifest") + 1]
    elif paths:
        target = str(paths[-1])            # latest stamped manifest
    if not target or not Path(target).exists():
        print("REFUSED: no manifest to validate "
              "(run gpu_fit_manifest.py first)")
        return 1
    try:
        out_path = resolve_evidence_path(EVID_DIR, "gpu_fit_dryrun", argv)
    except EvidencePathExists as ex:
        print(f"REFUSED: {ex}")
        return 2
    manifest = json.loads(Path(target).read_text(encoding="utf-8"))
    if manifest.get("schema") != gfm.MANIFEST_SCHEMA:
        print(f"REFUSED: manifest_schema_unsupported "
              f"{manifest.get('schema')}")
        return 1
    try:
        result = validate(manifest)
    except DryRunRefusal as ex:
        print(f"REFUSED: {ex.reason} {json.dumps(ex.detail)}")
        return 1
    receipt = {
        "schema": DRYRUN_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "manifest_path": target,
        "manifest_sha256": manifest.get("manifest_sha256"),
        "reservation": result["rows"]["reservation"],
        "no_reservation_taken": True,
        "live_batch_not_run": True,
        "validation": result,
        "clean_dry_run": bool(result["all_validations_pass"]
                              and result["clean_probe"]),
    }
    out_path.write_text(json.dumps(receipt, indent=2) + "\n",
                        encoding="utf-8")
    print(f"manifest: {target}")
    print(f"reservation verdict: "
          f"{result['rows']['reservation']['verdict']} "
          f"(exit {result['rows']['reservation']['exit_code']})")
    for k, v in result["rows"].items():
        if k == "reservation":
            continue
        print(f"  {k}: {'PASS' if v.get('pass', True) else 'FAIL'}")
    print(f"clean dry run: {receipt['clean_dry_run']}")
    print(f"dry-run receipt: {out_path}")
    return 0 if receipt["clean_dry_run"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
