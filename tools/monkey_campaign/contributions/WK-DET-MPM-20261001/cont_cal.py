"""det-mpm contention-launch calibration (NON-EVIDENCE mechanics check).

Imports contention_kernel from run_mpm_arm_v4.py (byte-identical kernel object,
no duplication) and measures the solo execution time of one launch on cuda:0:
2 warmups, then 5 timed solo launches (launch -> synchronize_stream -> stop),
median reported. AMENDMENT-2 uses the median as T_launch_solo_ms in the fixed
sizing formula. Writes calibration.json to the directory given as argv[1].

GPU work happens only inside the queue job that runs this script.
"""

import json
import os
import statistics
import subprocess
import sys
import time

OUT_DIR = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))

_saved_argv = list(sys.argv)
sys.argv = [
    "cont_cal", "--arm", "cont-cal", "--mode", "not_guaranteed",
    "--device", "cuda:0", "--frames", "1", "--out", os.path.join(OUT_DIR, "unused"),
]
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("armv4", os.path.join(HERE, "run_mpm_arm_v4.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
import warp as wp  # noqa: E402

assert int(wp.config.deterministic) == 0

dev = wp.get_device("cuda:0")
arr = wp.zeros(mod.CONTENTION_WINDOW, dtype=float, device=dev)
stream = wp.Stream(device=dev)

for _ in range(2):
    wp.launch(
        mod.contention_kernel, dim=mod.CONTENTION_DIM, inputs=[arr, mod.CONTENTION_ITERS],
        device=dev, stream=stream, block_dim=mod.CONTENTION_BLOCK,
    )
wp.synchronize_stream(stream)

solo_ms = []
for _ in range(5):
    t0 = time.perf_counter()
    wp.launch(
        mod.contention_kernel, dim=mod.CONTENTION_DIM, inputs=[arr, mod.CONTENTION_ITERS],
        device=dev, stream=stream, block_dim=mod.CONTENTION_BLOCK,
    )
    wp.synchronize_stream(stream)
    solo_ms.append((time.perf_counter() - t0) * 1000.0)

smi = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,driver_version,compute_cap,uuid", "--format=csv"],
    capture_output=True, text=True, timeout=60,
)
cal = {
    "solo_launch_ms_all": solo_ms,
    "T_launch_solo_ms_median": statistics.median(solo_ms),
    "launches_timed": len(solo_ms),
    "warmups": 2,
    "dim": mod.CONTENTION_DIM,
    "block_dim": mod.CONTENTION_BLOCK,
    "iters_per_launch": mod.CONTENTION_ITERS,
    "window_floats": mod.CONTENTION_WINDOW,
    "atomics_per_launch": mod.CONTENTION_DIM * mod.CONTENTION_ITERS,
    "nvidia_smi_csv": smi.stdout.strip(),
    "harness": "run_mpm_arm_v4.py",
}
os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "calibration.json"), "w") as f:
    json.dump(cal, f, indent=1)
print("T_launch_solo_ms_median =", cal["T_launch_solo_ms_median"])
print("solo_launch_ms_all =", solo_ms)
