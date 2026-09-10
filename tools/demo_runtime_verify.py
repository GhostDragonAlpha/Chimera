"""Metamorphic reset/status consistency gate for an explicitly owned demo endpoint.

Run only after obtaining the engine-demo/GPU reservation and verifying the
endpoint's process identity. This script initializes and changes that demo.
Outputs are immutable. Existing frozen B2 reference gates remain separate.
"""
import argparse
import hashlib
import json
import math
import urllib.request
from pathlib import Path

from membrane_demo_client import load_b2, md01_packet


def request(base, method, path, body=None):
    is_packet = isinstance(body, bytes)
    data = body if is_packet else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(base.rstrip("/") + path, data=data, method=method,
                                 headers={"Content-Type": "application/octet-stream"
                                          if is_packet else "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        value = json.load(response)
    if value.get("ok") is False:
        raise RuntimeError(f"{path}: {value}")
    return value.get("status", value)


def _finite_number(value, name):
    finite = False
    if type(value) in (int, float):
        try:
            finite = math.isfinite(float(value))
        except (OverflowError, ValueError):
            pass
    if not finite:
        raise ValueError(f"{name} must be a finite JSON number")
    return value


def _nonnegative_int(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative JSON integer")
    return value


def state_fields(status):
    if not isinstance(status, dict):
        raise ValueError("status must be a JSON object")
    fields = {key: status[key] for key in
              ("iteration", "accepted_state_id", "centre", "centre_force", "energy")}
    material_snapshot = status["material_snapshot"]
    if not isinstance(material_snapshot, dict):
        raise ValueError("material_snapshot must be a JSON object")
    fields["gamma"] = material_snapshot["gamma_admitted_f64"]
    _nonnegative_int(fields["iteration"], "iteration")
    _nonnegative_int(fields["accepted_state_id"], "accepted_state_id")
    for key in ("centre", "centre_force"):
        values = fields[key]
        if not isinstance(values, list) or len(values) != 3:
            raise ValueError(f"{key} must contain exactly three components")
        for index, value in enumerate(values):
            _finite_number(value, f"{key}[{index}]")
    _finite_number(fields["energy"], "energy")
    _finite_number(fields["gamma"], "gamma")
    return fields


def validate_initial_state(initial):
    if initial["gamma"] <= 0.0:
        raise ValueError("frozen B2 initial gamma must be positive")
    if not any(value != 0.0 for value in initial["centre_force"]):
        raise ValueError("frozen B2 initial centre force must be nonzero")


def validate_control_effect(label, initial, changed):
    if label == "zero_gamma_then_reset":
        if changed["gamma"] != 0.0 or changed["energy"] != 0.0:
            raise ValueError("gamma=0 control did not produce zero gamma and energy")
        if any(value != 0.0 for value in changed["centre_force"]):
            raise ValueError("gamma=0 control did not produce zero centre force")
        if (changed["accepted_state_id"] != initial["accepted_state_id"] or
                changed["centre"] != initial["centre"]):
            raise ValueError("gamma=0 control changed accepted geometry")
    elif label == "step_then_reset":
        if changed["iteration"] <= initial["iteration"]:
            raise ValueError("step control did not advance iteration")
        if changed["accepted_state_id"] == initial["accepted_state_id"]:
            raise ValueError("step control did not change accepted_state_id")
        if changed["centre"] == initial["centre"]:
            raise ValueError("step control did not change accepted centre")
    else:
        raise ValueError(f"unknown control {label}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    args = parser.parse_args()
    identity = json.loads(args.identity.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=False)
    result = {"identity": identity, "base": args.base,
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "comparison": "exact serialized initialization fields", "checks": []}
    try:
        request(args.base, "POST", "/membrane_demo_bin", md01_packet(load_b2(), 1.0))
        initial = request(args.base, "GET", "/membrane_demo")
        expected = state_fields(initial)
        validate_initial_state(expected)
        result["initial"] = initial
        for label, control in (("zero_gamma_then_reset", {"op": "gamma", "gamma": 0}),
                               ("step_then_reset", {"op": "step", "n_steps": 1})):
            request(args.base, "POST", "/membrane_demo", control)
            changed = request(args.base, "GET", "/membrane_demo")
            validate_control_effect(label, expected, state_fields(changed))
            request(args.base, "POST", "/membrane_demo", {"op": "reset"})
            restored = request(args.base, "GET", "/membrane_demo")
            actual = state_fields(restored)
            mismatched = [key for key in expected if actual[key] != expected[key]]
            result["checks"].append({"name": label, "before_reset": changed,
                                     "after_reset": restored, "mismatched": mismatched,
                                     "verdict": "FAIL" if mismatched else "PASS"})
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["passed"] = ("error" not in result and len(result["checks"]) == 2 and
                        all(check["verdict"] == "PASS" for check in result["checks"]))
    with (args.output / "result.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({"passed": result["passed"], "checks": [
        {key: check[key] for key in ("name", "verdict", "mismatched")}
        for check in result["checks"]], "error": result.get("error")}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
