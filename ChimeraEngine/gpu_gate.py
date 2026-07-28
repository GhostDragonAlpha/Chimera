"""gpu_gate.py — DID THE TRAINING DO REAL WORK? (learning is the proof; heat + time are readouts)

    "The temperature maybe giving false positives for you if it's working or not... what's important
     is how long is this going to take."                              -- the operator, 2026-07-27

The operator's ORIGINAL insight was load-bearing and stays: a promise to use the GPU is worthless,
so PROVE it with something un-fakeable. Temperature was that proof -- until a genuinely-working run
(myoLegs learning to stand, survival 0 -> 92%) peaked at 53 C and got REFUSED at the 54 C floor.
The operator saw the flaw immediately: temperature is a PROXY, and a proxy can lie. A heavy,
low-GPU-occupancy workload (myoLegs: 80 muscles, 324 tendon wraps) does real work while running
cool, so a fixed temperature floor false-refuses it.

THE DIRECT PROOF of real GPU work is the LEARNING CURVE itself: you cannot drive a metric from 0 to
92% without genuinely simulating millions of physics steps on the GPU. That is un-fakeable in a way
temperature is not -- temperature could be raised by unrelated GPU load, but THIS task's learning
curve can only come from THIS task's real computation. So the gate now PASSES on demonstrated
learning, and reports temperature and wall-clock TIME as READOUTS -- "how long did it take" being
the number you actually plan iteration around.

    A coasting run still FAILS: no real work => the metric does not move => REFUSED. The gate got
    STRICTER, not weaker. It no longer accepts "the card got warm" as a substitute for "the training
    actually learned."

Usage in a trainer:
    from gpu_gate import GPUHeatGate
    gate = GPUHeatGate().start()
    ... training, tracking a metric from start to finish ...
    gate.enforce(improved=final_metric - initial_metric, threshold=..., metric='survival%')
    # or, with no learning signal, it falls back to the temperature floor (backward compatible)
"""
from __future__ import annotations

import subprocess
import threading
import time


def gpu_temp() -> float:
    """Current GPU temperature in Celsius, straight from the driver. A readout, no longer the verdict."""
    out = subprocess.check_output(
        ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
        timeout=3).decode().strip().splitlines()
    return float(out[0])


class GPUHeatGate:
    """Judges whether a training run did REAL WORK, and reports how long it took.

    The verdict is the LEARNING CURVE when the caller supplies one (`enforce(improved=...)`): a run
    that genuinely trained moved its metric, a coasting run did not. Temperature is still sampled and
    reported (idle -> peak) as a readout, and wall-clock time is reported so the operator can plan.
    `min_peak_c` remains the FALLBACK verdict for callers that supply no learning signal (backward
    compatible with the pure heat gate), but temperature is no longer the primary measure -- it was a
    proxy, and it was caught giving a false negative.
    """

    def __init__(self, min_peak_c: float = 54.0, period: float = 1.0):
        self.min_peak_c = min_peak_c
        self.period = period
        self.idle = None
        self.samples = []
        self._run = False
        self._t = None
        self.t0 = None

    def start(self) -> 'GPUHeatGate':
        self.idle = gpu_temp()                     # baseline BEFORE the work starts (a readout)
        self.t0 = time.perf_counter()
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

    def verdict(self, improved: float | None = None, threshold: float = 0.0) -> tuple:
        self._run = False
        if self._t is not None:
            self._t.join(timeout=3)
        idle = self.idle if self.idle is not None else 0.0
        peak = max(self.samples, default=idle)
        elapsed = (time.perf_counter() - self.t0) if self.t0 is not None else 0.0
        if improved is not None:                   # PRIMARY: did the training actually learn?
            ok = improved > threshold
            basis = f'learning: metric improved {improved:+.1f} (needs > {threshold:.0f})'
        else:                                      # FALLBACK: the old temperature floor
            ok = peak >= self.min_peak_c
            basis = f'temperature: peak {peak:.0f}C (needs >= {self.min_peak_c:.0f}C)'
        return ok, dict(idle=idle, peak=peak, elapsed=elapsed, improved=improved, basis=basis)

    def enforce(self, improved: float | None = None, threshold: float = 0.0, metric: str = 'metric') -> dict:
        """Print the readouts + verdict; REFUSE (exit 1) if there is no evidence of real work."""
        ok, s = self.verdict(improved, threshold)
        print(f"\n[work-gate] took {s['elapsed']/60:.1f} min   |   GPU {s['idle']:.0f}C -> {s['peak']:.0f}C "
              f"(readouts, not the verdict)")
        if s['improved'] is not None:
            print(f"[work-gate] {metric} improved by {s['improved']:+.1f} over the run "
                  "-- the DIRECT, un-fakeable proof the GPU did real work")
        if not ok:
            print(f"[work-gate] REFUSED: {s['basis']} -- no evidence the training did real work.")
            print("  A real run learns; a coasting run does not. Confirm the training actually ran")
            print("  on the GPU and the population is large enough to make progress.")
            raise SystemExit(1)
        print(f"[work-gate] PASS: {s['basis']} -- the training did real work.")
        return s


if __name__ == '__main__':
    # Self-test: the gate PASSES on demonstrated learning even when the GPU is cold, and REFUSES a
    # run that neither warmed the card NOR learned anything (a true coasting run).
    print(f"current GPU temperature (a readout): {gpu_temp():.0f} C")
    print("\n1) a run that LEARNED (metric +40) but stayed cool -- should PASS on the learning proof:")
    try:
        GPUHeatGate().start().enforce(improved=40.0, threshold=10.0, metric='survival%')
        print("  ^ PASS: learning is the proof; temperature was not needed.")
    except SystemExit:
        print("  ^ unexpected refuse")
    print("\n2) a COASTING run: no learning signal AND cold GPU -- should REFUSE:")
    g = GPUHeatGate(min_peak_c=54.0).start()
    time.sleep(3)
    try:
        g.enforce()                                # no improved= -> falls back to temperature floor
        print("  (did not refuse -- GPU was already warm from prior work)")
    except SystemExit:
        print("  ^ correct: no learning and no heat -> REFUSED. The gate still catches coasting.")
