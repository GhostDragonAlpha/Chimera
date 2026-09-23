"""First-skill scripted baseline controller (runnable form of run_manifest.json).

FROZEN at prereg (see reward.py's Rule-0 note): the baseline is a FIXED SCHEDULE
through the Type-A command adapter's declared channel {commanded_target_velocity_x}
-- action-interface-identical to the trained policy, so the comparison isolates
what was learned, not the interface.

  V_HOLD = 0.60 m/s -- the banked R2 in-band mid command (the command_adapter
                      receipt's F-ZOH-CLOCK twin value): the ONLY non-seed
                      command the ship state has measured end-to-end (graded
                      table, veto-free horizon 140 ticks post-onset, byte-proven
                      ZOH equivalence). Choosing it makes the baseline a banked
                      behavior, not a tuned one.

  schedule: issue ONCE at tick 0, hold forever (ZOH value-only). No stop logic,
  no observation feedback -- a scripted controller with zero per-tick decisions.

MEASURED ON THE SAME BARS: the baseline is evaluated on the identical eval seed
set, episode rules, hard conditions, and CoT band protocol as the trained policy
(acceptance.py); its record is frozen into the acceptance ledger BEFORE any
policy comparison. Per Astra: if this controller matches the trained policy on
every bar, F-FIRST-SKILL fires -- passing the pipeline does not establish that
learning was necessary.
"""
from __future__ import annotations

V_HOLD = 0.60          # m/s, the banked R2 value (command_adapter receipt)
ISSUE_TICK = 0         # single issue at episode start, then ZOH hold


class BaselineController:
    """Scripted goal-tracking baseline: constant 0.60 m/s command, held."""

    def __init__(self, v_hold: float = V_HOLD, issue_tick: int = ISSUE_TICK):
        self.v_hold = float(v_hold)
        self.issue_tick = int(issue_tick)
        self._issued = False

    def reset(self) -> None:
        self._issued = False

    def decide(self, tick: int, obs=None, goal=None) -> dict:
        """Return the adapter command for this decision tick.

        The obs/goal arguments are accepted and IGNORED by contract: a fixed
        schedule reads nothing. Returns the GaitWalker::configure payload.
        """
        if tick < self.issue_tick:
            return {}
        self._issued = True
        return {"commanded_target_velocity_x": self.v_hold}

    @property
    def schedule_fingerprint(self) -> str:
        """Stable identity of the frozen schedule (for the acceptance ledger)."""
        return f"baseline_constant_hold_v={self.v_hold:.6f}@tick{self.issue_tick}"
