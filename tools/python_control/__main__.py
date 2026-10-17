"""Run explicit, bounded matter experiments against a chosen native engine."""
import argparse
import json
from pathlib import Path
from .client import EngineControl


def run_scenario(engine, scenario):
    operations = scenario["operations"]
    if not isinstance(operations, list) or len(operations) > 1000:
        raise ValueError("Scenario needs at most 1000 operations")
    allowed = {"fixture": engine.membrane.load_fixture, "reset": engine.membrane.reset,
               "tension": engine.membrane.tension, "step": engine.membrane.step,
               "pause": engine.membrane.pause, "state": engine.membrane.state,
               "matter": engine.matter.configure, "matter_state": engine.matter.state,
               "physics": engine.physics.intent, "physics_state": engine.physics.state,
               "surface": engine.physics.surface, "telemetry": engine.telemetry,
               "assembly": engine.assembly.command, "assembly_state": engine.assembly.state,
               "assembly_clock": engine.assembly.clock}
    # Reject typos before applying any operations; native refusal stops immediately.
    for operation in operations:
        if operation.get("op") not in allowed or not isinstance(operation.get("args", {}), dict):
            raise ValueError(f"Invalid scenario operation: {operation}")
    return [{"op": op["op"], "result": allowed[op["op"]](**op.get("args", {}))}
            for op in operations]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Explicit native engine URL; choose a private test world")
    parser.add_argument("--scenario", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    with EngineControl(args.base) as engine:
        result = run_scenario(engine, json.loads(args.scenario.read_text())) if args.scenario else engine.telemetry()
        if args.capture:
            args.capture.parent.mkdir(parents=True, exist_ok=True)
            args.capture.write_bytes(engine.frame())
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n")
    print(text)

if __name__ == "__main__": main()
