"""CPU-only regression tests for the native reset metamorphic gate.

These tests replace the HTTP request function with deterministic fakes.  They
never start the engine and write results only below TemporaryDirectory.
"""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location(
    "demo_runtime_verify", TOOLS / "demo_runtime_verify.py"
)
GATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GATE)


def status(**updates):
    value = {
        "iteration": 0,
        "accepted_state_id": 100,
        "centre": [0.0, 0.0, 0.125],
        "centre_force": [0.0, 2.98023224e-08, -0.428571433],
        "energy": 2.625,
        "material_snapshot": {"gamma_admitted_f64": 1.0},
    }
    value.update(updates)
    return value


INITIAL = status()
GAMMA_ZERO = status(
    centre_force=[0.0, 0.0, 0.0],
    energy=0.0,
    material_snapshot={"gamma_admitted_f64": 0.0},
)
STEPPED = status(
    iteration=1,
    accepted_state_id=101,
    centre=[0.0, 0.0, 0.123999998],
    centre_force=[0.0, -2.98023224e-08, -0.425212026],
    energy=2.62457323,
)


def run_gate(responses):
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        identity = directory / "identity.json"
        identity.write_text("{}", encoding="utf-8")
        output = directory / "result"
        argv = ["demo_runtime_verify.py", "--base", "http://fake",
                "--output", str(output), "--identity", str(identity)]
        with patch.object(GATE, "request", side_effect=[copy.deepcopy(v) for v in responses]), \
                patch.object(GATE, "load_b2", return_value=[]), \
                patch.object(GATE, "md01_packet", return_value=b"packet"), \
                patch.object(sys, "argv", argv):
            return_code = GATE.main()
        result = json.loads((output / "result.json").read_text(encoding="utf-8"))
        return return_code, result


class ResetGateTests(unittest.TestCase):
    def test_valid_controls_and_restores_pass(self):
        responses = [
            {}, INITIAL, {}, GAMMA_ZERO, {}, INITIAL,
            {}, STEPPED, {}, INITIAL,
        ]
        return_code, result = run_gate(responses)
        self.assertEqual(return_code, 0)
        self.assertTrue(result["passed"])
        self.assertEqual([check["verdict"] for check in result["checks"]],
                         ["PASS", "PASS"])

    def test_ignored_controls_fail_instead_of_passing(self):
        responses = [INITIAL] * 10
        return_code, result = run_gate(responses)
        self.assertEqual(return_code, 1)
        self.assertFalse(result["passed"])
        self.assertIn("gamma=0 control did not produce", result["error"])

    def test_step_without_accepted_geometry_change_fails(self):
        unchanged_step = status(iteration=1)
        responses = [
            {}, INITIAL, {}, GAMMA_ZERO, {}, INITIAL,
            {}, unchanged_step,
        ]
        return_code, result = run_gate(responses)
        self.assertEqual(return_code, 1)
        self.assertFalse(result["passed"])
        self.assertIn("did not change accepted_state_id", result["error"])

    def test_malformed_force_shape_fails(self):
        malformed = status(centre_force=[])
        return_code, result = run_gate([{}, malformed])
        self.assertEqual(return_code, 1)
        self.assertFalse(result["passed"])
        self.assertIn("centre_force must contain exactly three", result["error"])

    def test_boolean_or_nonfinite_component_fails(self):
        for component in (True, float("nan")):
            malformed = status(centre=[component, 0.0, 0.125])
            return_code, result = run_gate([{}, malformed])
            self.assertEqual(return_code, 1)
            self.assertFalse(result["passed"])
            self.assertIn("centre[0] must be a finite JSON number", result["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
