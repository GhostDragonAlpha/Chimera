"""
Gates — verification checkpoints from the Chimera methodology.

  Witness Gate: beat script ran, expectations checked, evidence recorded.
  Verify Gate:   evidence chain reaches PHYSICS or THE HUMAN.
  Why Gate:      every claim has a because-edge — no assertions without proof.
"""

import json, time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GateResult:
    gate: str
    passed: bool
    evidence: dict
    note: str
    timestamp: float = field(default_factory=time.time)


class WitnessGate:
    """The beat ran. Expectations were checked. Evidence exists."""

    def check(self, beat_run) -> GateResult:
        reached = beat_run.beats_reached
        total = beat_run.beats_total
        passed = reached == total
        evidence = {
            "demo": beat_run.demo,
            "beats_reached": f"{reached}/{total}",
            "temperature": beat_run.temperature,
            "walltime_s": beat_run.walltime_s,
        }
        note = (f"All {total} beats reached." if passed
                else f"Only {reached}/{total} beats reached. Failures:")
        if not passed:
            for o in beat_run.outcomes:
                if not o.reached:
                    for e in o.expectations:
                        if not e["passed"]:
                            note += f"\n  - {o.name}/{e['name']}: {e['detail']}"
        return GateResult("witness", passed, evidence, note)


class VerifyGate:
    """
    Witness passed + evidence recorded to graph = verified.
    In Chimera Engine, evidence is recorded to a local ledger.
    """

    def __init__(self, ledger_path: str = "ChimeraEngine/evidence.json"):
        self.ledger = Path(ledger_path)

    def record(self, gate_result: GateResult):
        entries = []
        if self.ledger.exists():
            entries = json.loads(self.ledger.read_text())
        entries.append({
            "gate": gate_result.gate,
            "passed": gate_result.passed,
            "evidence": gate_result.evidence,
            "note": gate_result.note,
            "timestamp": gate_result.timestamp,
        })
        self.ledger.write_text(json.dumps(entries, indent=2))

    def verify(self, gate_result: GateResult) -> GateResult:
        if gate_result.passed:
            self.record(gate_result)
            return GateResult("verify", True, gate_result.evidence,
                              "Witness passed. Evidence recorded.")
        return GateResult("verify", False, gate_result.evidence,
                          f"Witness failed: {gate_result.note}")
