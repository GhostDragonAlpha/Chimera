"""gpu_gate.py — THE GPU MUST GET HOT, OR THE TRAINING DID NOT USE IT.

    "The only thing that is a successful measure is GPU temperature."   -- the operator, 2026-07-27

He is right, and it is the project's own method: measure the PHYSICAL thing, not a proxy. World
count is a proxy (you can pass a big number and still stall on Python overhead). Utilization % can
mislead (a driver reports "busy" for a kernel that barely touches the cores). HEAT cannot lie --
it is thermodynamics. Watts in become degrees out. A GPU that stays at idle temperature during a
training run did no real work, full stop.

The operator caught this by hand: "the GPU temperature doesn't climb when you train." The cause was
running 256 worlds when this 4090 does 16,384 in one kernel -- the kernels were microscopic and the
card sat idle between Python steps. This gate makes that failure LOUD instead of invisible: it
reads the GPU temperature before and during a run, and REFUSES the run as GPU-starved if the card
never heated up.

    A promise that I will use the GPU is worth nothing (proven this session). A gate that fails when
    the GPU stays cold is worth everything. This is that gate.

Usage in a trainer:
    from gpu_gate import GPUHeatGate
    gate = GPUHeatGate().start()
    ... training ...
    gate.enforce()          # prints the verdict, raises SystemExit(1) if the GPU stayed cold
"""
from __future__ import annotations

import subprocess
import threading
import time


def gpu_temp() -> float:
    """Current GPU temperature in Celsius, straight from the driver. The ground truth."""
    out = subprocess.check_output(
        ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
        timeout=3).decode().strip().splitlines()
    return float(out[0])


class GPUHeatGate:
    """Samples GPU temperature across a run and judges whether the card actually did work.

    `min_peak_c` is the ABSOLUTE temperature the GPU must reach to count as "used" -- set by the
    operator at 54 C. Idle on this 4090 is ~41 C; a real training kernel pushes it well past 55-60 C.
    An absolute floor is stricter and clearer than a relative rise: it does not matter what the card
    started at, it has to physically get hot. A run whose peak never reaches `min_peak_c` was
    starved -- the kernels were too small and the GPU waited on the host.
    """

    def __init__(self, min_peak_c: float = 54.0, period: float = 1.0):
        self.min_peak_c = min_peak_c
        self.period = period
        self.idle = None
        self.samples = []
        self._run = False
        self._t = None

    def start(self) -> 'GPUHeatGate':
        self.idle = gpu_temp()                     # baseline BEFORE the work starts
        self._run = True
        self._t = threading.Thread(target=self._poll, daemon=True)
        self._t.start()
        return self

    def _poll(self):
        while self._run:
            try:
                self.samples.append(gpu_temp())
            except Exception:
                pass
            time.sleep(self.period)

    def verdict(self) -> tuple:
        self._run = False
        if self._t is not None:
            self._t.join(timeout=3)
        idle = self.idle if self.idle is not None else 0.0
        peak = max(self.samples, default=idle)
        return (peak >= self.min_peak_c,
                dict(idle=idle, peak=peak, required=self.min_peak_c,
                     samples=len(self.samples)))

    def enforce(self) -> dict:
        """Print the verdict and REFUSE (exit 1) if the GPU never reached min_peak_c. Call at the
        end of a run."""
        ok, s = self.verdict()
        print(f"\n[gpu-heat-gate] idle {s['idle']:.0f} C -> peak {s['peak']:.0f} C  "
              f"(over {s['samples']} samples; the GPU MUST reach {s['required']:.0f} C)")
        if not ok:
            print(f"[gpu-heat-gate] REFUSED: peak {s['peak']:.0f} C < the required {s['required']:.0f} C "
                  "-- the GPU did not do real work.")
            print("  Temperature is the witness. The training ran starved: small kernels, the card")
            print("  idle between Python steps. Raise the world/env count toward the 16,384 this")
            print("  4090 runs in one kernel (docs: GPU for the population).")
            raise SystemExit(1)
        print(f"[gpu-heat-gate] PASS: the GPU reached {s['peak']:.0f} C -- it did real work.")
        return s


if __name__ == '__main__':
    # Self-test: read the temperature and prove the gate REFUSES a cold (no-work) run.
    print(f"current GPU temperature: {gpu_temp():.0f} C")
    print("\nproving the gate fires on a COLD run (no GPU work for 4 s):")
    g = GPUHeatGate(min_peak_c=54.0).start()
    time.sleep(4)                                  # do nothing -- the GPU should stay cold
    try:
        g.enforce()
        print("  (did not refuse -- GPU was already warm from prior work)")
    except SystemExit:
        print("  ^ correct: a cold GPU is REFUSED. This is the gate working.")
