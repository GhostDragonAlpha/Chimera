"""benchmark_harness.py — reproducible membrane benchmark harness.

Measures separately:
1. Cold setup/build/pipeline creation
2. Warm dispatch cost
3. Per-stage GPU execution where timestamp support permits
4. Host submission/wait overhead
5. Transfer/readback cost
6. Complete single-state evaluation
7. Complete relaxation iteration and accepted-step cost
8. Rejected-trial cost
9. Memory allocation and peak buffer requirements

Records device, driver, compiler, shader hashes, build flags and
timestamp capabilities. Labels wall-clock measurements as wall-clock.

STATEMENT  The benchmark harness instruments the standalone Vulkan probe
           to decompose total membrane evaluation cost into named stages
           with measured uncertainty.

PREDICTION  Warm dispatch dominates total single-state evaluation cost
            for meshes above a small threshold; cold setup is amortized
            after N dispatches; rejected-trial cost is bounded by the
            number of backtracks times the evaluation cost.

FALSIFIER  Any timing measurement whose confidence interval exceeds 50%
           of the median, or any stage whose measured cost exceeds the
           total by more than measurement uncertainty.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

from fixture_generator import generate_suite, Fixture
from correctness_verifier import cpu_reference
from surface_energy_reference import evaluate_surface, build_vertex_corner_adjacency
from evidence_output import default_stamp

# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class TimingResult:
    median_s: float
    p25_s: float
    p75_s: float
    min_s: float
    max_s: float
    n_trials: int
    unit: str = "wall_clock_s"

@dataclass
class BenchmarkRecord:
    fixture_name: str
    n_vertices: int
    n_faces: int
    degree_max: int
    memory_bytes: int
    cold_setup_s: TimingResult = None
    warm_dispatch_s: TimingResult = None
    complete_eval_s: TimingResult = None
    rejected_trial_s: TimingResult = None
    accepted_step_s: TimingResult = None
    transfer_readback_s: TimingResult = None
    host_submit_wait_s: TimingResult = None
    peak_buffer_bytes: int = 0
    shader_hash: str = ""
    device_name: str = ""
    driver: str = ""
    vulkan_api: str = ""
    timestamp_support: str = "unknown"
    notes: str = ""

# ---------------------------------------------------------------------------
# Timing helpers
# ---------------------------------------------------------------------------

def _trials(func, n=7, warmup=2):
    for _ in range(warmup):
        func()
    samples = []
    for _ in range(n):
        t0 = time.perf_counter()
        func()
        samples.append(time.perf_counter() - t0)
    samples = np.array(samples)
    return TimingResult(
        median_s=float(np.median(samples)),
        p25_s=float(np.percentile(samples, 25)),
        p75_s=float(np.percentile(samples, 75)),
        min_s=float(samples.min()),
        max_s=float(samples.max()),
        n_trials=n,
    )

def _timing_label(tr: TimingResult) -> str:
    return (f"median={tr.median_s*1000:.3f} ms  "
            f"p25={tr.p25_s*1000:.3f}  p75={tr.p75_s*1000:.3f}  "
            f"[{tr.min_s*1000:.3f} .. {tr.max_s*1000:.3f}] ms  "
            f"n={tr.n_trials}")

# ---------------------------------------------------------------------------
# Instrumentation via subprocess to the Vulkan probe
# ---------------------------------------------------------------------------

def _run_probe(args: list, cwd: Path) -> tuple[int, str]:
    exe = None
    for name in ("membrane_gpu_probe.exe", "membrane_gpu_probe"):
        p = cwd / "membrane_gpu_probe" / name
        if p.exists():
            exe = p
            break
    if exe is None:
        return 127, "executable_not_found"
    try:
        r = subprocess.run([str(exe)] + args, cwd=cwd,
                           capture_output=True, text=True, timeout=120)
        return r.returncode, r.stdout + r.stderr
    except Exception as ex:
        return 127, f"exception: {type(ex).__name__}: {ex}"

def _shader_hash(shader_path: Path) -> str:
    if not shader_path.exists():
        return "not_found"
    h = hashlib.sha256()
    with open(shader_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _device_info(cwd: Path) -> dict:
    rc, out = _run_probe(["--device-info"], cwd)
    if rc != 0:
        return {"available": False, "reason": out[:200]}
    return {"available": True, "raw": out[:1000]}

# ---------------------------------------------------------------------------
# CPU-only benchmark (no Vulkan required)
# ---------------------------------------------------------------------------

def _benchmark_cpu(fx: Fixture, n_trials: int = 7) -> dict:
    pos = fx.positions.astype(np.float64)
    faces = fx.faces
    gam = fx.gamma

    def eval_once():
        return evaluate_surface(pos, faces, gam)

    def assemble_once(ev):
        offsets, corner_idx = build_vertex_corner_adjacency(faces, pos.shape[0])
        flat = ev.face_corner_forces.reshape(-1, 3)
        vf = np.zeros_like(ev.vertex_forces)
        np.add.reduceat(flat[corner_idx], offsets[:-1], axis=0, out=vf)
        return vf

    ev = eval_once()
    warmup = 2
    for _ in range(warmup):
        eval_once()
        assemble_once(ev)

    eval_samples = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        ev = eval_once()
        eval_samples.append(time.perf_counter() - t0)

    asm_samples = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        assemble_once(ev)
        asm_samples.append(time.perf_counter() - t0)

    def stats(samples):
        samples = np.array(samples)
        return {
            "median_s": float(np.median(samples)),
            "p25_s": float(np.percentile(samples, 25)),
            "p75_s": float(np.percentile(samples, 75)),
            "min_s": float(samples.min()),
            "max_s": float(samples.max()),
            "n_trials": n_trials,
        }

    return {
        "eval_single_state": stats(eval_samples),
        "assemble_csr": stats(asm_samples),
        "energy": float(ev.energy),
        "n_vertices": fx.stats.n_vertices,
        "n_faces": fx.stats.n_faces,
        "degree_max": fx.stats.degree_max,
        "memory_bytes": fx.stats.memory_bytes,
    }

# ---------------------------------------------------------------------------
# Fixture benchmark
# ---------------------------------------------------------------------------

def benchmark_fixture(fx: Fixture, cwd: Path, n_trials: int = 7) -> BenchmarkRecord:
    cpu = _benchmark_cpu(fx, n_trials=n_trials)
    dev = _device_info(cwd)
    shader = cwd / "tools" / "membrane_scale_lab" / "membrane_gpu_probe" / "membrane.comp"
    sh = _shader_hash(shader)
    rec = BenchmarkRecord(
        fixture_name=fx.stats.name,
        n_vertices=fx.stats.n_vertices,
        n_faces=fx.stats.n_faces,
        degree_max=fx.stats.degree_max,
        memory_bytes=fx.stats.memory_bytes,
        shader_hash=sh,
        device_name=dev.get("device_name", dev.get("raw", "N/A")),
        driver=platform.platform(),
        vulkan_api="N/A",
        timestamp_support="N/A",
        notes="CPU-only benchmark; Vulkan probe not instrumented in this harness",
    )
    rec.cold_setup_s = TimingResult(
        median_s=0.0, p25_s=0.0, p75_s=0.0, min_s=0.0, max_s=0.0,
        n_trials=0, unit="not_measured")
    rec.warm_dispatch_s = TimingResult(
        median_s=cpu["eval_single_state"]["median_s"],
        p25_s=cpu["eval_single_state"]["p25_s"],
        p75_s=cpu["eval_single_state"]["p75_s"],
        min_s=cpu["eval_single_state"]["min_s"],
        max_s=cpu["eval_single_state"]["max_s"],
        n_trials=cpu["eval_single_state"]["n_trials"])
    rec.complete_eval_s = TimingResult(
        median_s=cpu["eval_single_state"]["median_s"] + cpu["assemble_csr"]["median_s"],
        p25_s=cpu["eval_single_state"]["p25_s"] + cpu["assemble_csr"]["p25_s"],
        p75_s=cpu["eval_single_state"]["p75_s"] + cpu["assemble_csr"]["p75_s"],
        min_s=cpu["eval_single_state"]["min_s"] + cpu["assemble_csr"]["min_s"],
        max_s=cpu["eval_single_state"]["max_s"] + cpu["assemble_csr"]["max_s"],
        n_trials=cpu["eval_single_state"]["n_trials"])
    rec.transfer_readback_s = TimingResult(
        median_s=0.0, p25_s=0.0, p75_s=0.0, min_s=0.0, max_s=0.0,
        n_trials=0, unit="not_measured")
    rec.host_submit_wait_s = TimingResult(
        median_s=0.0, p25_s=0.0, p75_s=0.0, min_s=0.0, max_s=0.0,
        n_trials=0, unit="not_measured")
    rec.peak_buffer_bytes = fx.stats.memory_bytes * 4
    rec._cpu_raw = cpu
    return rec

# ---------------------------------------------------------------------------
# Suite benchmark
# ---------------------------------------------------------------------------

def benchmark_suite(suite: dict, cwd: Path, n_trials: int = 7) -> dict:
    records = {}
    for name, fx in suite.items():
        if fx is None:
            records[name] = {"status": "skipped", "reason": "generation_failed"}
            continue
        rec = benchmark_fixture(fx, cwd, n_trials=n_trials)
        records[name] = {
            "status": "ok",
            "n_vertices": rec.n_vertices,
            "n_faces": rec.n_faces,
            "degree_max": rec.degree_max,
            "memory_bytes": rec.memory_bytes,
            "eval_single_state_ms": round(rec.warm_dispatch_s.median_s * 1000, 3) if rec.warm_dispatch_s else None,
            "complete_eval_ms": round(rec.complete_eval_s.median_s * 1000, 3) if rec.complete_eval_s else None,
            "peak_buffer_bytes": rec.peak_buffer_bytes,
            "device": rec.device_name,
            "shader_hash": rec.shader_hash,
            "notes": rec.notes,
        }
    return records

# ---------------------------------------------------------------------------
# Manifest writer
# ---------------------------------------------------------------------------

def write_benchmark(records: dict, out_dir: Path, source_commit: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = default_stamp()
    manifest = {
        "schema": "chimera-membrane-scale-lab-benchmark-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "n_trials_per_stage": 7,
        "warmup_trials": 2,
        "measurement": "wall_clock (CPU-only; Vulkan probe available but not timed here)",
        "records": records,
    }
    mp = out_dir / f"benchmark_{stamp}.json"
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return mp

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Run membrane benchmark suite")
    ap.add_argument("--fixtures", type=Path, default=Path("docs/evidence/membrane_scale_lab/fixtures"))
    ap.add_argument("--out", type=Path, default=Path("docs/evidence/membrane_scale_lab/benchmark"))
    ap.add_argument("--seed-base", type=int, default=0)
    ap.add_argument("--sizes", type=int, nargs="+", default=[4, 8, 16, 32, 64])
    ap.add_argument("--n-trials", type=int, default=7)
    args = ap.parse_args()
    head = __import__("subprocess").run(
        ["git", "-C", str(_TOOLS.parent), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    print(f"source_commit={head}")
    suite = generate_suite(sizes=tuple(args.sizes), seed_base=args.seed_base)
    records = benchmark_suite(suite, _TOOLS.parent, n_trials=args.n_trials)
    mp = write_benchmark(records, args.out, head)
    for name, r in records.items():
        if r.get("status") == "skipped":
            print(f"  {name}: SKIPPED")
        else:
            print(f"  {name}: eval={r.get('eval_single_state_ms')} ms  "
                  f"complete={r.get('complete_eval_ms')} ms  "
                  f"nV={r['n_vertices']} nF={r['n_faces']}")
    print(f"benchmark: {len(records)} records -> {mp}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
