"""gpu_fit_manifest.py -- builds the §11.18 bounded GPU-batch manifest for
the learned-candidate fit of THIS mechanism (implementation-only seam: the
live batch is a separately scheduled action; nothing here reserves the GPU).

Law implemented (11.18 "GPU work as one reserved batch" + GPU_BATCHING.md):
  * one reservation for the whole batch; the preregistered manifest
    determines the sequence; the batch process NEVER calls the unloaded
    language model (no router/HTTP invocation in any job command --
    refused by name at build time and re-checked by the dry run);
  * jobs are raw commands (no nested run_gpu_job.py), absolute executable,
    per-job timeout <= 600 s, sequential, stop on failure;
  * release-in-cleanup: run_gpu_job's GpuLease closes on success, error
    and cancellation (context manager), timeouts close the whole owned
    process tree (OwnedChild), and the reservation is released in the
    runner's finally path -- recorded here as the contract;
  * fixtures are derived ONLY from adapter-PASSed qualification receipts,
    train+validation splits; the holdout family is excluded structurally;
  * packet budgets are copied verbatim (time_s, ram_mb); an OOM must fail
    the job -- silently changing precision, physical steps or dropping
    cases is forbidden by the manifest's stopping conditions;
  * checkpoint policy is the packet's own, verbatim;
  * seed 1729 -- the reference bounded fit's seed (Runtime/physics-ai/
    elasticity_probe.py, JSON receipt with physically_qualified flag).

Exit 0 manifest + manifest receipt written / 1 build refusal (named) /
2 evidence-path refusal. CPU only; no reservation is ever taken here.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "membrane_scale_lab"))

import bounded_fit as bf                 # label collection + table knots
import receipt_adapter as ra             # independent verifier

from evidence_output import (            # via bounded_fit's lab path insert
    EvidencePathExists,
    resolve_evidence_path,
)

EVID_DIR = bf.EVID_DIR
PACKET_PATH = bf.PACKET_PATH
MANIFEST_SCHEMA = "chimera-mechanism-factory-gpu-manifest-v1"
FIT_RECEIPT_SCHEMA = "chimera-mechanism-factory-learned-candidate-fit-v1"
SEED = 1729                              # reference bounded-fit seed
# torch lives in the local Python (2.13+cu126), not in the Strata venv;
# the batch job is a raw command, so the executable just has to exist.
FIT_PYTHON = Path("C:/Python314/python.exe")
RUN_GPU_JOB = Path(
    "D:/Chimera-Maintenance/Runtime/local-ai/run_gpu_job.py")
GPU_BATCH = Path(
    "D:/Chimera-Maintenance/Runtime/local-ai/gpu_batch.py")
FIT_SCRIPT = _HERE / "fit_job.py"        # the P3 fit stage (this seam)
LIVE_COMMAND = [                        # NOT YET RUN (see GPU_LIVE_BATCH.md)
    "D:/Chimera-Maintenance/Runtime/local-ai/Strata/.venv/Scripts/python.exe",
    str(GPU_BATCH), "<manifest_path>",
]

# No-LLM-call law: the batch process must not call the unloaded language
# model. Any router/HTTP/model invocation marker in a job command (or cwd)
# is refused by name at build time and re-checked by the dry run.
FORBIDDEN_MARKERS = (
    "run_gpu_job", "gpu_batch", "strata_model_router", "127.0.0.1:8080",
    "localhost:8080", "/v1/unload", "/health", "http://", "https://",
    "lmstudio", "gateway", "ensure_local_gateway", "invoke-webrequest",
    "curl", "urllib", "requests.", "websocket", "socket.",
)
REQUIRED_PACKET_BUDGET_KEYS = ("time_s", "ram_mb")


class ManifestRefusal(Exception):
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


def _no_llm_calls(command: list, cwd: str) -> None:
    low = [str(x).lower() for x in command] + [str(cwd).lower()]
    for text in low:
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                raise ManifestRefusal(
                    "llm_call_in_job_command",
                    {"marker": marker, "text": text,
                     "why": "the batch process must not call the "
                            "unloaded language model (no router/HTTP "
                            "invocation in any job command)"})


def _label_receipts(packet: dict, receipt_paths: list) -> tuple:
    """Adapter-PASSed receipts become label sources; a refused receipt is
    recorded under its name and never consumed. The build is refused only
    when NO qualified receipt exists at all."""
    qualified, refused = [], []
    for path in receipt_paths:
        v = ra.verify_receipt(path, PACKET_PATH)
        if not v.passed:
            refused.append({"receipt": str(path),
                            "adapter_refusals": list(v.refusals)})
            continue
        qualified.append(str(path))
    if not qualified:
        raise ManifestRefusal(
            "no_qualified_receipt",
            {"scanned": [str(p) for p in receipt_paths],
             "refused": refused})
    return qualified, refused


def _fixtures(packet: dict, receipt_paths: list) -> dict:
    """Frozen train/validation fixture list from the qualified receipts'
    knots (holdout excluded structurally by the fit's split gate)."""
    collected = bf.collect_labels(packet, receipt_paths)
    table = bf.build_table(packet, collected)
    fixtures = {}
    for fam in sorted(table["families"]):
        split = table["families"][fam]["split"]
        if split == bf.HOLDOUT_SPLIT:
            raise ManifestRefusal("refusal_holdout_fixture",
                                  {"family": fam,
                                   "why": "the holdout family must never "
                                          "be read during fit or eval"})
        fixtures[fam] = {
            "split": split,
            "load_magnitudes_N": [p["load_magnitude_N"]
                                  for p in table["families"][fam]["points"]],
            "n_knots": len(table["families"][fam]["points"]),
        }
    return fixtures


def build_manifest(packet: dict, receipt_paths: list, *,
                   job_timeout_s: float = 600.0,
                   job_command: list | None = None,
                   job_cwd: str = str(_REPO)) -> dict:
    """Deterministic bounded batch manifest; same inputs -> same sha256."""
    if not (0 < float(job_timeout_s) <= 600.0):
        raise ManifestRefusal(
            "refusal_timeout_out_of_range",
            {"job_timeout_s": job_timeout_s,
             "law": "per-job timeout must be 0 < t <= 600 s (GPU_BATCHING)"})
    budgets = packet.get("budgets") or {}
    missing = [k for k in REQUIRED_PACKET_BUDGET_KEYS if k not in budgets]
    if missing:
        raise ManifestRefusal("refusal_missing_budget_fields",
                              {"missing": missing,
                               "why": "memory/time budget fields must come "
                                      "from the packet"})
    if job_command is None:
        job_command = [
            str(FIT_PYTHON), str(FIT_SCRIPT),
            "--device", "cuda", "--seed", str(SEED),
            "--packet", str(PACKET_PATH),
        ]
    _no_llm_calls(job_command, job_cwd)
    if not str(job_command[0]).strip() or \
            not Path(job_command[0]).is_absolute():
        raise ManifestRefusal("refusal_non_absolute_executable",
                              {"command": job_command})
    if not Path(job_command[0]).exists():
        raise ManifestRefusal("refusal_executable_missing",
                              {"executable": job_command[0]})
    qualified, refused = _label_receipts(packet, receipt_paths)
    fixtures = _fixtures(packet, qualified)

    # identities: data inputs the fit consumes, sha-pinned so gpu_batch
    # refuses the batch if any label source changes after preregistration.
    identities = {str(PACKET_PATH): _sha256_bytes(PACKET_PATH.read_bytes())}
    for path in qualified:
        identities[path] = _sha256_bytes(Path(path).read_bytes())

    # the fit script is authored in the following seam; until it exists the
    # manifest is a preregistered PLAN, not a runnable batch.
    pending = []
    if not FIT_SCRIPT.exists():
        pending.append({"path": str(FIT_SCRIPT),
                        "role": "learned-candidate fit job script",
                        "status": "authored_in_next_seam"})
    else:
        identities[str(FIT_SCRIPT)] = _sha256_bytes(
            FIT_SCRIPT.read_bytes())

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "batch_runner": str(GPU_BATCH),
        "seed": SEED,
        "seed_provenance": "reference bounded fit seed (Runtime/physics-ai/"
                           "elasticity_probe.py)",
        "jobs": [{
            "name": "learned_candidate_fit",
            "command": job_command,
            "cwd": job_cwd,
            "timeout": job_timeout_s,
            "expect": ["learned-candidate receipt written"],
            "budgets": {
                "packet_time_s": budgets["time_s"],
                "packet_ram_mb": budgets["ram_mb"],
                "max_vram_mib": 1024,
                "min_free_vram_mib": 384,
                "evidence_disk_mb": 512,
                "why": "packet budgets verbatim plus preregistered GPU "
                       "headroom (the small-fixture floor is 384 MiB "
                       "reported free); an OOM FAILS the job -- never "
                       "silently change precision, physical steps or "
                       "drop cases",
            },
            "output_schemas": {
                "receipt": FIT_RECEIPT_SCHEMA,
                "required_fields": ["seed", "device", "splits_used",
                                    "labels_receipt_hashes", "train_mse",
                                    "validation_mse", "physically_qualified",
                                    "gpu_memory_sampled"],
                "physically_qualified_law": "true only if the packet's "
                                            "thresholds are met on the "
                                            "validation split; the flag "
                                            "defaults false",
            },
        }],
        "fixtures": fixtures,
        "fixture_provenance": {
            "label_receipts": qualified,
            "refused_receipts": refused,
            "holdout_families": list(packet["frozen_splits"]["holdout"]),
            "holdout_excluded": "structurally (split gate before any "
                                "output read; sentinel-proven by "
                                "bounded_fit_checks T3)",
        },
        "identities": identities,
        "pending_inputs": pending,
        "continue_on_failure": False,
        "checkpoint_policy": packet.get("checkpoint_policy"),
        "stopping_conditions": [
            "jobs run sequentially in preregistered order; stop on first "
            "failure (continue_on_failure false)",
            "stop when the packet's acceptance thresholds are met on the "
            "validation split; the physically_qualified flag is the only "
            "success marker",
            "an OOM or any packet-limit breach FAILS the job: silently "
            "changing precision, physical steps or dropping cases is "
            "forbidden",
            "the batch never calls the unloaded language model between "
            "jobs; results are read only after the entire suite returns",
        ],
        "release_contract": {
            "one_reservation": "gpu_batch.py invokes the handoff once and "
                               "holds the OS reservation across every job",
            "release_in_cleanup": "run_gpu_job's GpuLease closes on "
                                  "success, error and cancellation "
                                  "(context manager); timeouts close the "
                                  "whole owned process tree (OwnedChild); "
                                  "the runner releases in its finally "
                                  "path; the next inference reloads the "
                                  "requested model normally",
            "no_model_touching": "this manifest's jobs contain no "
                                 "router/HTTP invocation; the batch "
                                 "process must not call the unloaded "
                                 "language model",
        },
    }
    manifest["manifest_sha256"] = _sha256_bytes(_canonical(
        {k: v for k, v in manifest.items() if k != "manifest_sha256"}))
    return manifest


def build_receipt(packet: dict, manifest: dict, receipt_paths: list) -> dict:
    return {
        "schema": MANIFEST_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "mechanism_id": packet.get("mechanism_id"),
        "manifest_path": None,          # filled by main() after stamping
        "manifest_sha256": manifest["manifest_sha256"],
        "seed": manifest["seed"],
        "fixture_provenance": manifest["fixture_provenance"],
        "budgets": manifest["jobs"][0]["budgets"],
        "checkpoint_policy": manifest["checkpoint_policy"],
        "stopping_conditions": manifest["stopping_conditions"],
        "release_contract": manifest["release_contract"],
        "pending_inputs": manifest["pending_inputs"],
        "eligible_for_live_batch": not manifest["pending_inputs"],
        "no_live_reservation_taken": True,
        "candidate_receipts_considered": [str(p) for p in receipt_paths],
        "live_command_not_yet_run": LIVE_COMMAND,
    }


def main(argv: list) -> int:
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    receipt_paths = sorted(
        str(p) for p in EVID_DIR.glob("qualification_receipt_*.json"))
    try:
        manifest_path = resolve_evidence_path(EVID_DIR, "gpu_fit_manifest",
                                              argv)
        receipt_path = resolve_evidence_path(EVID_DIR,
                                             "gpu_manifest_receipt", argv)
    except EvidencePathExists as ex:
        print(f"REFUSED: {ex}")
        return 2
    try:
        manifest = build_manifest(packet, receipt_paths)
    except ManifestRefusal as ex:
        print(f"REFUSED: {ex.reason} {json.dumps(ex.detail)}")
        return 1
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                             encoding="utf-8")
    receipt = build_receipt(packet, manifest, receipt_paths)
    receipt["manifest_path"] = str(manifest_path)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n",
                            encoding="utf-8")
    print(f"manifest: {manifest_path}")
    print(f"manifest_sha256: {manifest['manifest_sha256']}")
    print(f"pending inputs: {len(manifest['pending_inputs'])} "
          f"(eligible_for_live_batch={receipt['eligible_for_live_batch']})")
    print(f"manifest receipt: {receipt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
