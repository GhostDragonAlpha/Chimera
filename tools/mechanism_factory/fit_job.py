"""fit_job.py -- the P3 fit stage proper: device-agnostic bounded fit for
the learned candidate of THIS mechanism (justified by the bounded table's
recorded rejection at the preregistered interpolation gate).

Reference pattern: Runtime/physics-ai/elasticity_probe.py -- seed 1729,
JSON receipt with a physically_qualified flag, honest scope statement.

Model: a small response operator (torch MLP, tanh, hidden 16x16) mapping
(pin angle, load magnitude, fixture geometry) -> the 3 reaction components
of that pin, in N. Pins are placed on the rim by the frozen fixtures
(their angles come from the pinned vertices' rest coordinates).

Data law (identical to the bounded table's):
  * labels come from adapter-PASSed qualification receipts only,
    collected through bounded_fit.collect_labels -- the SAME split gate
    the sentinel check (bounded_fit_checks T3) proved: the holdout
    family is excluded structurally BEFORE any output value is read;
  * TRAIN split knots are the training set; VALIDATION split knots are
    the early-stopping set; the holdout family is never read;
  * the gate is the packet's max_force_balance_residual (1e-6 N) and is
    NEVER lowered: physically_qualified is true only if the best
    validation max reaction-component error is within it.

Budget law: the packet's budgets (time_s, ram_mb) are enforced; a breach
raises BudgetBreach -> clean failure (failure receipt, exit 1) -- never a
silent reduction of precision, steps or cases. No LLM/router call exists
in this script (the manifest's no-LLM law, check-scanned).

Determinism: torch.manual_seed(1729), one thread, deterministic
algorithms, full-batch fixed-order updates -> same seed + inputs give the
identical checkpoint sha256.

Exit 0 receipt written (qualified or honestly unqualified) / 1 failure
(budget breach or fit error) / 2 evidence-path refusal.
"""
from __future__ import annotations

import argparse
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
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "membrane_scale_lab"))

import bounded_fit as bf                  # split gate + label collection
import receipt_adapter as ra
import qualification_receipt as qr        # frozen fixtures (read-only)
import fixture_generator as fg            # pin angles (read-only)

from evidence_output import (EvidencePathExists, resolve_evidence_path)

EVID_DIR = bf.EVID_DIR
RECEIPT_SCHEMA = "chimera-mechanism-factory-fit-job-v1"
SEED_DEFAULT = 1729                       # reference bounded-fit seed
GATE_KEY = bf.TABLE_ERROR_TOLERANCE_KEY   # packet max_force_balance_residual
HIDDEN = 16
LR = 2e-3                                 # reference probe's learning rate
MAX_EPOCHS = 3000
PATIENCE = 200

import torch                              # after stdlib setup
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)

FORBIDDEN_MARKERS = (
    "run_gpu_job", "gpu_batch", "strata_model_router", "127.0.0.1:8080",
    "localhost:8080", "/v1/unload", "/health", "http://", "https://",
    "lmstudio", "gateway", "ensure_local_gateway", "invoke-webrequest",
    "curl", "urllib", "requests.", "websocket", "socket.")


class JobRefusal(Exception):
    def __init__(self, reason: str, detail: dict | None = None):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail or {}


class BudgetBreach(Exception):
    def __init__(self, which: str, measured: float, limit: float):
        super().__init__(f"{which} breach: {measured} > {limit}")
        self.which = which
        self.measured = measured
        self.limit = limit


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── data: adapter-gated labels + frozen pin angles ──────────────────────────

def collect_training_data(packet: dict, receipt_paths: list) -> dict:
    """Train/validation samples from qualified receipts through the SAME
    split gate the sentinel check proved; holdout outputs never read."""
    collected = bf.collect_labels(packet, receipt_paths)
    table = bf.build_table(packet, collected)          # dedup + conflicts
    samples = {"train": [], "validation": []}
    for fam, entry in table["families"].items():
        fixture = qr.CASES[fam]["fixture"]
        fix = fg.high_degree_fan(**fixture)
        pins = list(fix.stats.pinned)
        angles = [math.atan2(fix.positions[i][1], fix.positions[i][0])
                  for i in pins]
        radius, height = fixture["radius"], fixture["height"]
        for point in entry["points"]:
            reactions = np.asarray(point["reactions_N"], dtype=np.float64)
            if reactions.shape[0] != len(pins):
                raise JobRefusal("reaction_row_mismatch",
                                 {"family": fam,
                                  "rows": reactions.shape[0],
                                  "pins": len(pins)})
            m = point["load_magnitude_N"]
            for k in range(len(pins)):
                samples[entry["split"]].append({
                    "inputs": [math.sin(angles[k]), math.cos(angles[k]),
                               m, radius, height],
                    "target": reactions[k].tolist(),
                })
    if not samples["train"] or not samples["validation"]:
        raise JobRefusal("insufficient_qualified_labels",
                         {"train": len(samples["train"]),
                          "validation": len(samples["validation"])})
    return samples


def to_tensor(samples: list, device) -> tuple:
    x = torch.tensor([s["inputs"] for s in samples], dtype=torch.float64,
                     device=device)
    y = torch.tensor([s["target"] for s in samples], dtype=torch.float64,
                     device=device)
    return x, y


# ── model ───────────────────────────────────────────────────────────────────

class Operator(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(5, HIDDEN).double(),
            torch.nn.Tanh(),
            torch.nn.Linear(HIDDEN, HIDDEN).double(),
            torch.nn.Tanh(),
            torch.nn.Linear(HIDDEN, 3).double(),
        )

    def forward(self, x):
        return self.net(x)


def train(samples: dict, packet: dict, device, seed: int) -> dict:
    """Full-batch Adam with early stopping on the validation split.
    Budget breaches raise BudgetBreach; the gate is never lowered."""
    thr = packet["acceptance_thresholds"][GATE_KEY]
    budgets = packet["budgets"]
    x_tr, y_tr = to_tensor(samples["train"], device)
    x_va, y_va = to_tensor(samples["validation"], device)
    torch.manual_seed(seed)
    model = Operator().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    best = {"validation_max_error_N": math.inf, "state": None, "epoch": -1}
    start = time.perf_counter()
    tracemalloc.start()
    stopping = "max_epochs"
    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        optimizer.zero_grad()
        pred = model(x_tr)
        loss = (pred - y_tr).square().mean()
        assert torch.isfinite(loss), "nonfinite training loss"
        loss.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            err = float((model(x_va) - y_va).abs().max())
        if err < best["validation_max_error_N"] - 1e-15:
            best = {"validation_max_error_N": err,
                    "state": model.state_dict(), "epoch": epoch}
        elif epoch - best["epoch"] >= PATIENCE:
            stopping = "early_stopped_validation"
            break
        wall = time.perf_counter() - start
        if wall > float(budgets["time_s"]):
            tracemalloc.stop()
            raise BudgetBreach("packet_time_s", wall, budgets["time_s"])
        _, peak = tracemalloc.get_traced_memory()
        if peak / (1024.0 * 1024.0) > float(budgets["ram_mb"]):
            tracemalloc.stop()
            raise BudgetBreach("packet_ram_mb",
                               peak / (1024.0 * 1024.0),
                               budgets["ram_mb"])
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    wall = time.perf_counter() - start
    model.load_state_dict(best["state"])
    return {"model": model, "best": best, "stopping": stopping,
            "wall_s": wall, "peak_mib": peak / (1024.0 * 1024.0),
            "gate_N": float(thr)}


def checkpoint_bytes(model: Operator) -> bytes:
    """Deterministic checkpoint: the parameter tensors as plain JSON
    (float repr is deterministic; no archive timestamps)."""
    with torch.no_grad():
        layers = [p.detach().cpu().numpy().tolist()
                  for p in model.parameters()]
    return json.dumps({"format": "fit-job-weights-v1",
                       "tensors": layers}, indent=1).encode("utf-8")


# ── receipt verification (forge -> refused by name) ─────────────────────────

def verify_job_receipt(receipt: dict, checkpoint_path: str | None) -> dict:
    refusals = []
    gate = float(json.loads(bf.PACKET_PATH.read_text(encoding="utf-8"))
                 ["acceptance_thresholds"][GATE_KEY])
    err = receipt.get("validation_max_error_N")
    flag = receipt.get("physically_qualified")
    if not (isinstance(err, (int, float)) and math.isfinite(err)):
        refusals.append("nonfinite_validation_error")
    elif flag is not (err <= gate):
        refusals.append("physically_qualified_forgery")
    if receipt.get("seed") != SEED_DEFAULT:
        refusals.append("seed_mismatch")
    splits = receipt.get("split_usage", {}).get("fit", [])
    if sorted(splits) != ["train", "validation"]:
        refusals.append("split_usage_forgery")
    if receipt.get("split_usage", {}).get("holdout_cases_read", 1) != 0:
        refusals.append("holdout_read")
    if receipt.get("no_llm_calls") is not True:
        refusals.append("no_llm_calls_forgery")
    if checkpoint_path:
        want = receipt.get("checkpoint_sha256")
        got = _sha256_file(Path(checkpoint_path))
        if want != got:
            refusals.append("checkpoint_hash_mismatch")
    return {"passed": not refusals, "refusals": refusals}


# ── main ────────────────────────────────────────────────────────────────────

def main(argv: list) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--seed", type=int, default=SEED_DEFAULT)
    p.add_argument("--packet", default=str(bf.PACKET_PATH))
    p.add_argument("--receipts", nargs="*", default=None)
    p.add_argument("--no-stamp", action="store_true",
                   help="write nothing; print the receipt (used by checks)")
    args, rest = p.parse_known_args(argv)
    rest = [a for a in rest if a not in ("--force-out",)]
    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    receipt_paths = args.receipts or sorted(
        str(x) for x in EVID_DIR.glob("qualification_receipt_*.json"))
    device = torch.device(args.device)

    try:
        samples = collect_training_data(packet, receipt_paths)
    except (bf.FitRefusal, JobRefusal) as ex:
        reason = getattr(ex, "reason", type(ex).__name__)
        print(f"REFUSED: {reason} "
              f"{json.dumps(getattr(ex, 'detail', {}), default=str)}")
        return 1

    try:
        out_ckpt = out_rcpt = None
        if not args.no_stamp:
            out_ckpt = resolve_evidence_path(EVID_DIR, "fit_job_checkpoint",
                                             rest)
            out_rcpt = resolve_evidence_path(EVID_DIR, "fit_job_receipt",
                                             rest)
    except EvidencePathExists as ex:
        print(f"REFUSED: {ex}")
        return 2

    try:
        fit = train(samples, packet, device, args.seed)
    except BudgetBreach as ex:
        print(f"FAILED: budget breach {ex.which}: {ex.measured} > "
              f"{ex.limit}; no success receipt is written")
        if out_rcpt:
            out_rcpt.write_text(json.dumps({
                "schema": RECEIPT_SCHEMA,
                "utc": datetime.now(timezone.utc).isoformat(),
                "status": "budget_breach", "which": ex.which,
                "measured": ex.measured, "limit": ex.limit,
                "seed": args.seed, "device": str(device),
                "physically_qualified": False,
            }, indent=2) + "\n", encoding="utf-8")
            print(f"failure receipt: {out_rcpt}")
        return 1

    model, best = fit["model"], fit["best"]
    data = checkpoint_bytes(model)
    if out_ckpt:
        out_ckpt.write_bytes(data)
        ckpt_hash = _sha256_file(out_ckpt)
    else:
        ckpt_hash = hashlib.sha256(data).hexdigest()
    qualified = bool(best["validation_max_error_N"] <= fit["gate_N"])
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "device": str(device),
        "split_usage": {
            "fit": ["train", "validation"],
            "holdout": "excluded structurally (bounded_fit split gate; "
                       "sentinel-proven by bounded_fit_checks T3)",
            "holdout_cases_seen": 1, "holdout_cases_read": 0,
            "train_samples": len(samples["train"]),
            "validation_samples": len(samples["validation"]),
        },
        "labels_receipts": sorted(
            str(x) for x in EVID_DIR.glob("qualification_receipt_*.json")
            if ra.verify_receipt(str(x), bf.PACKET_PATH).passed),
        "model": {"kind": "mlp_tanh_16x16", "inputs": "sin(theta),cos(theta),"
                  "load_magnitude_N,radius_wu,height_wu",
                  "outputs": "pin reaction components (N)"},
        "checkpoint_sha256": ckpt_hash,
        "wall_time_s": fit["wall_s"],
        "python_traced_peak_mib": fit["peak_mib"],
        "metric_note": "tracemalloc Python-heap peak over the fit; torch "
                       "internal buffers are not fully traced",
        "stopping_condition": fit["stopping"],
        "best_epoch": best["epoch"],
        "validation_max_error_N": best["validation_max_error_N"],
        "gate_N": fit["gate_N"],
        "gate_note": "packet max_force_balance_residual; never lowered",
        "physically_qualified": qualified,
        "no_llm_calls": True,
        "scope": "learned candidate for the port-reaction response of the "
                 "frozen fixtures; interpolation across geometry and load "
                 "within the packet's admitted domain; holdout never read",
    }
    verdict = verify_job_receipt(receipt,
                                 str(out_ckpt) if out_ckpt else None)
    if not verdict["passed"]:
        print(f"REFUSED: receipt verification failed {verdict['refusals']}")
        return 1
    body = json.dumps(receipt, indent=2) + "\n"
    if out_rcpt:
        out_rcpt.write_text(body, encoding="utf-8")
        print(f"job receipt: {out_rcpt}")
        if out_ckpt:
            print(f"checkpoint: {out_ckpt}")
    else:
        print(body)
    print(f"validation max error: "
          f"{best['validation_max_error_N']:.4e} N vs gate {fit['gate_N']:.0e}"
          f" -> physically_qualified={qualified}")
    print(f"stopping: {fit['stopping']} (epoch {best['epoch']}), "
          f"wall {fit['wall_s']:.2f} s, peak {fit['peak_mib']:.1f} MiB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
