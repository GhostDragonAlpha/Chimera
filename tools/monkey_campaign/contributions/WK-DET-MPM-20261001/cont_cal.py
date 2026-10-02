"""det-mpm contention-launch calibration (NON-EVIDENCE mechanics check).

AMENDMENT-5 version (cal4): optional argv[2] = iters (e.g. 1024 for the r2r variant). measures the solo execution time of one contention_kernel
launch on cuda:0 in BOTH determinism modes, because the R2R path records
(key, value) scatter records (bounded by deterministic_max_records) and has a
completely different per-launch cost than the NG path:

  Phase NG  : import run_mpm_arm_v5.py in not_guaranteed mode, 2 warmups +
              5 timed solo launches (launch -> synchronize_stream -> stop).
  Phase R2R : import run_mpm_arm_v5.py again as a fresh module in run_to_run
              mode (module options bind at creation), 2 warmups + 5 timed.

Each launch performs 268,435,456 float atomic_adds into a 4096-float window.
Writes calibration.json to the directory given as argv[1] with both medians.
GPU work happens only inside the queue job that runs this script.
"""

import json
import os
import statistics
import subprocess
import sys
import time

OUT_DIR = sys.argv[1]
CAL_ITERS = int(sys.argv[2]) if len(sys.argv) > 2 else None
HERE = os.path.dirname(os.path.abspath(__file__))

import importlib.util  # noqa: E402
import warp as wp  # noqa: E402


def load_module(mode_name, tag):
    saved = list(sys.argv)
    sys.argv = [
        "cont_cal", "--arm", "cont-cal", "--mode", mode_name,
        "--device", "cuda:0", "--frames", "1", "--out", os.path.join(OUT_DIR, "unused"),
    ]
    try:
        spec = importlib.util.spec_from_file_location(
            f"armv6_{tag}", os.path.join(HERE, "run_mpm_arm_v6.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.argv[:] = saved


def measure(mod):
    iters = mod.CONTENTION_ITERS_EFFECTIVE
    dev = wp.get_device("cuda:0")
    arr = wp.zeros(mod.CONTENTION_WINDOW, dtype=float, device=dev)
    stream = wp.Stream(device=dev)
    for _ in range(2):
        wp.launch(
            mod.contention_kernel, dim=mod.CONTENTION_DIM,
            inputs=[arr, iters], device=dev, stream=stream,
            block_dim=mod.CONTENTION_BLOCK,
        )
    wp.synchronize_stream(stream)
    solo_ms = []
    for _ in range(5):
        t0 = time.perf_counter()
        wp.launch(
            mod.contention_kernel, dim=mod.CONTENTION_DIM,
            inputs=[arr, iters], device=dev, stream=stream,
            block_dim=mod.CONTENTION_BLOCK,
        )
        wp.synchronize_stream(stream)
        solo_ms.append((time.perf_counter() - t0) * 1000.0)
    return solo_ms


mod_ng = load_module("not_guaranteed", "ng")
assert int(wp.config.deterministic) == 0
ng_ms = measure(mod_ng)

mod_r2r = load_module("run_to_run", "r2r")
assert int(wp.config.deterministic) == 1
r2r_ms = measure(mod_r2r)

smi = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,driver_version,compute_cap,uuid", "--format=csv"],
    capture_output=True, text=True, timeout=60,
)
cal = {
    "ng_solo_launch_ms_all": ng_ms,
    "T_ng_solo_ms_median": statistics.median(ng_ms),
    "r2r_solo_launch_ms_all": r2r_ms,
    "T_r2r_solo_ms_median": statistics.median(r2r_ms),
    "launches_timed_per_mode": 5,
    "warmups_per_mode": 2,
    "dim": mod_r2r.CONTENTION_DIM,
    "block_dim": mod_r2r.CONTENTION_BLOCK,
    "iters_per_launch": mod_r2r.CONTENTION_ITERS_EFFECTIVE,
    "window_floats": mod_r2r.CONTENTION_WINDOW,
    "atomics_per_launch": mod_r2r.CONTENTION_DIM * mod_r2r.CONTENTION_ITERS_EFFECTIVE,
    "deterministic_max_records": int(wp.config.deterministic_max_records),
    "nvidia_smi_csv": smi.stdout.strip(),
    "harness": "run_mpm_arm_v6.py",
}
os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "calibration.json"), "w") as f:
    json.dump(cal, f, indent=1)
print("T_ng_solo_ms_median =", cal["T_ng_solo_ms_median"])
print("T_r2r_solo_ms_median =", cal["T_r2r_solo_ms_median"])
print("ng_all =", ng_ms)
print("r2r_all =", r2r_ms)
