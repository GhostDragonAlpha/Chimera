"""lab_runner.py — orchestrator for the membrane scale lab.

Runs the full pipeline:
  1. Generate fixtures
  2. Verify correctness
  3. Benchmark
  4. Prepare candidates
  5. Generate cost model
  6. Write summary

STATEMENT  The lab produces decision-quality evidence for Chimera's
           membrane computation scaling, bottleneck identification and
           optimization candidates.

PREDICTION  The suite generates valid fixtures across all tested sizes;
            correctness gates pass; timing results identify the dominant
            cost stage for each size class.

FALSIFIER  Any stage that fails to produce output, or any correctness
           gate that fails for a fixture whose CPU reference is finite
           and well-formed.
"""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

from fixture_generator import generate_suite, write_manifest
from correctness_verifier import verify_suite, write_results as write_correctness
from benchmark_harness import benchmark_suite, write_benchmark
from optimize_candidates import main as prepare_candidates, write_candidate_manifest, apply_candidate_a, apply_candidate_b, apply_candidate_c
from cost_model import model_suite, write_cost_model

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def run_lab(sizes=(4, 8, 16, 32, 64), seed_base: int = 0,
            out_root: Path = None) -> dict:
    if out_root is None:
        out_root = Path("docs/evidence/membrane_scale_lab")
    out_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = out_root / f"run_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=False)

    head = __import__("subprocess").run(
        ["git", "-C", str(_TOOLS.parent), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()

    print(f"[lab] source_commit={head}")
    print(f"[lab] run_dir={run_dir}")

    suite = generate_suite(sizes=sizes, seed_base=seed_base)
    fx_manifest = write_manifest(suite, run_dir / "fixtures", head)
    print(f"[lab] fixtures -> {fx_manifest}")

    correctness = verify_suite(suite)
    corr_manifest = write_correctness(correctness, run_dir / "correctness", head)
    print(f"[lab] correctness -> {corr_manifest}")

    benchmark = benchmark_suite(suite, _TOOLS.parent, n_trials=7)
    bench_manifest = write_benchmark(benchmark, run_dir / "benchmark", head)
    print(f"[lab] benchmark -> {bench_manifest}")

    apply_candidate_a()
    apply_candidate_b()
    apply_candidate_c()
    candidates = {
        "A_tree_reduction": {
            "statement": "Serial stage-2 limits GPU utilization for large F",
            "prediction": "Tree reduction reduces stage-2 time ~log2(F)",
            "falsifier": "No speedup or energy deviation > 1e-5 J",
            "patch_file": str(_TOOLS / "membrane_gpu_probe_patches" / "membrane_tree_reduction.comp"),
            "correctness_gate": {k: v for k, v in correctness.items()
                                 if v.get("status") == "PASS"},
        },
        "B_persistent_buffers": {
            "statement": "Per-dispatch allocation dominates small-mesh overhead",
            "prediction": "Amortized setup cost decreases linearly with iteration count",
            "falsifier": "Correctness regression on frozen fixtures",
            "patch_file": str(_TOOLS / "membrane_gpu_probe_patches" / "probe_persistent_buffers.hpp"),
            "correctness_gate": {k: v for k, v in correctness.items()
                                 if v.get("status") == "PASS"},
        },
        "C_fused_trial_eval": {
            "statement": "Host->device transfer latency overlaps poorly with eval",
            "prediction": "Fusing reduces accepted-step wall-clock for small meshes",
            "falsifier": "No improvement; correctness unchanged but timing unchanged",
            "patch_file": str(_TOOLS / "membrane_gpu_probe_patches" / "relax_fused_trial_eval.cpp"),
            "correctness_gate": {k: v for k, v in correctness.items()
                                 if v.get("status") == "PASS"},
        },
    }
    cand_manifest = write_candidate_manifest(candidates, run_dir / "candidates", head)
    print(f"[lab] candidates -> {cand_manifest}")

    models = model_suite(suite)
    cost_manifest = write_cost_model(models, run_dir / "cost_model", head)
    print(f"[lab] cost_model -> {cost_manifest}")

    n_pass = sum(1 for r in correctness.values() if r.get("status") == "PASS")
    n_total = len(correctness)
    summary = {
        "schema": "chimera-membrane-scale-lab-summary-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": head,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "run_dir": str(run_dir),
        "correctness": f"{n_pass}/{n_total} passed",
        "fixtures_generated": len([k for k, v in suite.items() if v is not None]),
        "fixtures_valid": sum(1 for k, v in suite.items() if v is not None and v.stats.valid),
        "artifacts": {
            "fixtures": str(fx_manifest.relative_to(run_dir)),
            "correctness": str(corr_manifest.relative_to(run_dir)),
            "benchmark": str(bench_manifest.relative_to(run_dir)),
            "candidates": str(cand_manifest.relative_to(run_dir)),
            "cost_model": str(cost_manifest.relative_to(run_dir)),
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[lab] summary -> {run_dir / 'summary.json'}")
    return summary

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Run membrane scale lab")
    ap.add_argument("--sizes", type=int, nargs="+", default=[4, 8, 16, 32, 64])
    ap.add_argument("--seed-base", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("docs/evidence/membrane_scale_lab"))
    args = ap.parse_args()
    summary = run_lab(sizes=tuple(args.sizes), seed_base=args.seed_base,
                      out_root=args.out)
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
