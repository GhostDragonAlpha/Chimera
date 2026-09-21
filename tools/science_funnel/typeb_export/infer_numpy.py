"""TypeB-P3 CPU inference: the deterministic pure-numpy recipe (the export runtime).

Deterministic inference recipe (pinned in the manifest `inference` block):
  1. observation projection (observation_schema.project_trace) -> x[64] float32
  2. normalize: x = clip((x - mean)/std, -8, +8); unavailable channels are already
     mean-filled by the projector, i.e. exactly 0.0 in normalized space
  3. forward: h1 = tanh(x@W0 + b0); h2 = tanh(h1@W1 + b1); a = tanh(h2@W2 + b2)
     -- float32 throughout, batch one, np.dot on C-contiguous arrays
  4. action mapping: applied = clip(center + scale * a, lo, hi)  (the command limiter)
  5. limiter saturation indicator: sat = |applied - (center + scale*a)| > 0
  6. clock: a decision happens iff physics_tick % hold_ticks == 0; otherwise the last
     applied commands are held (zero-order hold). 20 Hz decisions over 300 Hz physics,
     hold_ticks=15 (Astra's pilot config).

Engine runtime note (documented option, not built in this lane): the same recipe maps
1:1 onto the engine loop -- W/b as float32 arrays, tanh per layer, one matvec per
layer; the engine can either call this module through cpp_bridge or reimplement the
five steps; whichever it does, the manifest hash pins the recipe and F-CPU-POLICY-BYTES
must be re-run against the new implementation's byte stream before deployment.
"""
from __future__ import annotations

import numpy as np

from observation_schema import OBS_DIM, project_trace


class PolicyClock:
    """20 Hz decision clock with 15-tick zero-order hold (300 Hz physics)."""

    def __init__(self, policy_hz: int, physics_hz: int, hold_ticks: int):
        assert policy_hz * hold_ticks == physics_hz, "clock arithmetic must close"
        self.policy_hz = policy_hz
        self.physics_hz = physics_hz
        self.hold_ticks = hold_ticks
        self.tick = 0
        self.decisions = 0

    def reset(self) -> None:
        self.tick = 0
        self.decisions = 0

    @property
    def is_decision_tick(self) -> bool:
        return self.tick % self.hold_ticks == 0

    def advance(self) -> None:
        self.tick += 1


class NumpyPolicy:
    """Frozen actor + normalization + limiter + clock. Batch one, pure numpy."""

    def __init__(self, manifest: dict, params: dict[str, np.ndarray]):
        # manifest validated by policy_manifest.load_manifest before construction
        self.manifest = manifest
        self.arch = manifest["policy"]["architecture"]
        self.mean = np.asarray(manifest["normalization"]["mean"], dtype=np.float32)
        self.std = np.asarray(manifest["normalization"]["std"], dtype=np.float32)
        self.clip = float(manifest["normalization"].get("clip", 8.0))
        self.W = [np.ascontiguousarray(params[f"W{i}"], dtype=np.float32)
                  for i in range(len(self.arch) - 1)]
        self.b = [np.ascontiguousarray(params[f"b{i}"], dtype=np.float32)
                  for i in range(len(self.arch) - 1)]
        act = manifest["action"]
        self.lo = np.asarray(act["bounds_lo"], dtype=np.float32)
        self.hi = np.asarray(act["bounds_hi"], dtype=np.float32)
        self.scale = np.asarray(act["scale"], dtype=np.float32)
        self.center = np.asarray(act["center"], dtype=np.float32)
        clk = act["clock"]
        self.clock = PolicyClock(clk["policy_hz"], clk["physics_hz"], clk["hold_ticks"])
        self.prev_applied = self.center.copy()
        self.prev_limiter_sat = np.zeros(act["dim"], dtype=np.float32)
        self.ticks_since_intervention = 10**6
        self.ticks_since_reset = 0
        self._prev_yaw_rate = 0.0

    def reset(self) -> None:
        """Reset semantics: neutral commands, phase 0, mask filled by first tick."""
        self.clock.reset()
        self.prev_applied = self.center.copy()
        self.prev_limiter_sat = np.zeros_like(self.prev_applied)
        self.ticks_since_intervention = 10**6
        self.ticks_since_reset = 0
        self._prev_yaw_rate = 0.0

    def _forward(self, x: np.ndarray) -> np.ndarray:
        h = x
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            h = h @ W + b
            h = np.tanh(h, out=h) if h.dtype == np.float32 else np.tanh(h)
            h = h.astype(np.float32, copy=False)
        return h

    def act(self, trace_rec: dict) -> tuple[np.ndarray, dict]:
        """One engine tick. Returns (applied_commands[8], bookkeeping dict).

        On a decision tick: project -> normalize -> forward -> map. Otherwise hold.
        The tick's trace record must carry the pre-decision state of this tick.
        """
        trace_rec = dict(trace_rec)
        trace_rec.setdefault("available_groups", None)
        deciding = self.clock.is_decision_tick
        trace_rec["is_decision_tick"] = deciding
        trace_rec.setdefault("hold_tick", self.clock.tick % self.clock.hold_ticks)
        trace_rec.setdefault("ticks_since_reset", self.ticks_since_reset)
        trace_rec.setdefault("ticks_since_intervention", self.ticks_since_intervention)
        reason = trace_rec.get("intervention_reason", "none")
        if reason != "none":
            self.ticks_since_intervention = 0
        trace_rec["ticks_since_intervention"] = min(self.ticks_since_intervention, 3000)

        if deciding:
            x, _mask = project_trace(trace_rec, self.mean, self.std,
                                     {"yaw_rate": self._prev_yaw_rate})
            a = self._forward(x)
            raw = self.center + self.scale * a
            applied = np.clip(raw, self.lo, self.hi).astype(np.float32)
            sat = (np.abs(applied - raw) > 0).astype(np.float32)
            self.prev_applied = applied
            self.prev_limiter_sat = sat
            self.clock.decisions += 1
        applied = self.prev_applied

        self.ticks_since_intervention += 1
        self.ticks_since_reset += 1
        self._prev_yaw_rate = float(trace_rec.get("yaw_rate", 0.0) or 0.0)
        self.clock.advance()
        return applied, {
            "deciding": deciding, "decision_index": self.clock.decisions - 1,
            "tick": self.clock.tick - 1, "limiter_saturation": self.prev_limiter_sat.copy(),
        }
