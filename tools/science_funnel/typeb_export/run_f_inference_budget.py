"""TypeB-P3: F-INFERENCE-BUDGET driver.

Measured batch-one latency per decision (numpy) at the 20 Hz clock, per the frozen
prereg protocol: single process, time.perf_counter, 200 warmup decisions discarded,
3000 timed decisions, each timed end-to-end (projection + normalization + forward +
action mapping + clock bookkeeping), worst-case trace records (all groups available).

F-INFERENCE-BUDGET fires if p50/p95/p99 exceeds 50 ms (the 20 Hz budget) or peak
process memory exceeds 256 MB. Prereg prediction: p99 <= 0.5 ms.

Usage: python run_f_inference_budget.py <validation_dir>
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import policy_manifest as pman  # noqa: E402
from infer_numpy import NumpyPolicy  # noqa: E402

N_WARMUP = 200
N_TIMED = 3000
BUDGET_MS = 50.0
PREDICTION_MS = 0.5
MEMORY_BUDGET_MB = 256.0


def peak_rss_mb() -> float:
    """Windows: GetProcessMemoryInfo.PeakWorkingSetSize."""
    class PMC(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t)]
    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = ctypes.c_void_p  # pseudo-handle must stay 64-bit
    proc = k32.GetCurrentProcess()
    fn = getattr(ctypes.windll.psapi, "GetProcessMemoryInfo", None)
    if fn is None:  # Win7+ export also lives in kernel32 as K32GetProcessMemoryInfo
        fn = k32.K32GetProcessMemoryInfo
    fn.argtypes = [ctypes.c_void_p, ctypes.POINTER(PMC), ctypes.c_ulong]
    fn.restype = ctypes.c_int
    if not fn(proc, ctypes.byref(pmc), pmc.cb):
        raise OSError(f"GetProcessMemoryInfo failed (err={k32.GetLastError()})")
    return pmc.PeakWorkingSetSize / (1024.0 * 1024.0)


def worst_case_record(t: int) -> dict:
    """All groups available: the projector's full-cost path."""
    return {
        "tick": t, "phase_left": (t % 213) / 213.0,
        "phase_right": (((t % 213) / 213.0) + 0.5) % 1.0,
        "phase_frac": (t % 213) / 213.0, "phase_rate": 1.0 / 213.0,
        "contact_count": 2 + (t % 2), "contact_count_prev": 2 + ((t + 1) % 2),
        "foot_contacts": [1, 1, 0, 0, 1, 0], "foot_forces": [0.31, 0.29, 0.0, 0.0, 0.22, 0.0],
        "unload_class": 0, "hind_step_class": 0,
        "com_vel": [0.42, 0.03, -0.01], "yaw_rate": 0.05,
        "requested_cmd": [0.0] * 8, "applied_cmd": [0.0] * 8,
        "limiter_saturation": [0] * 8, "intervention_reason": "none",
        "ticks_since_intervention": 10**6, "hold_tick": t % 15,
        "freq_scale": 1.0, "ticks_since_reset": t,
        "available_groups": None,  # None = every group delivered
    }


def main() -> None:
    vd = os.path.abspath(sys.argv[1])
    manifest = pman.load_manifest(os.path.join(vd, "policy_manifest.json"),
                                  os.path.join(vd, "dummy_actor.npz"))
    params = dict(np.load(os.path.join(vd, "dummy_actor.npz")))
    policy = NumpyPolicy(manifest, params)

    for t in range(N_WARMUP):
        policy.act(worst_case_record(t))
    policy.reset()

    samples_ms = np.empty(N_TIMED, dtype=np.float64)
    for t in range(N_TIMED):
        rec = worst_case_record(t)
        t0 = time.perf_counter()
        policy.act(rec)
        samples_ms[t] = (time.perf_counter() - t0) * 1000.0

    p50, p95, p99 = (float(np.percentile(samples_ms, q)) for q in (50, 95, 99))
    peak = peak_rss_mb()
    fired = (max(p50, p95, p99) > BUDGET_MS) or (peak > MEMORY_BUDGET_MB)
    report = {
        "falsifier": "F-INFERENCE-BUDGET",
        "fires": fired,
        "pass": not fired,
        "protocol": {"n_warmup": N_WARMUP, "n_timed": N_TIMED, "batch": 1,
                     "clock": "20 Hz decisions, 15-tick hold (decision every 15th tick)",
                     "scope": "end-to-end act(): projection+normalization+forward+action map+clock",
                     "runtime": f"numpy {np.__version__} / python {sys.version.split()[0]}"},
        "budget": {"latency_ms_per_decision": BUDGET_MS, "peak_memory_mb": MEMORY_BUDGET_MB},
        "prereg_prediction_ms": PREDICTION_MS,
        "measured": {"p50_ms": p50, "p95_ms": p95, "p99_ms": p99,
                     "max_ms": float(samples_ms.max()),
                     "mean_ms": float(samples_ms.mean()),
                     "decisions_per_s_20hz_duty": 1000.0 / p99,
                     "peak_rss_mb": peak,
                     "mac_count": manifest["policy"]["mac_count"],
                     "macs_per_s_at_p99": manifest["policy"]["mac_count"] / (p99 / 1000.0)},
        "margin_vs_budget_x": BUDGET_MS / max(p99, 1e-12),
        "detail": (f"batch-one numpy per-decision latency p50={p50:.6f} ms p95={p95:.6f} ms "
                   f"p99={p99:.6f} ms (budget {BUDGET_MS} ms, margin {BUDGET_MS / max(p99, 1e-12):.0f}x; "
                   f"prereg prediction <= {PREDICTION_MS} ms: {'HELD' if p99 <= PREDICTION_MS else 'MISSED'}); "
                   f"peak RSS {peak:.1f} MB (budget {MEMORY_BUDGET_MB} MB)"),
    }
    with open(os.path.join(vd, "latency.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps({"falsifier": report["falsifier"], "pass": report["pass"],
                      "detail": report["detail"]}, indent=1))


if __name__ == "__main__":
    main()
