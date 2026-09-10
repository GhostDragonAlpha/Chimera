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


def state_fields(status):
    fields = {key: status[key] for key in
              ("iteration", "accepted_state_id", "centre", "centre_force", "energy")}
    fields["gamma"] = status["material_snapshot"]["gamma_admitted_f64"]
    values = [fields["energy"], fields["gamma"], *fields["centre"], *fields["centre_force"]]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("nonfinite status")
    return fields


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
        result["initial"] = initial
        for label, control in (("zero_gamma_then_reset", {"op": "gamma", "gamma": 0}),
                               ("step_then_reset", {"op": "step", "n_steps": 1})):
            request(args.base, "POST", "/membrane_demo", control)
            changed = request(args.base, "GET", "/membrane_demo")
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
