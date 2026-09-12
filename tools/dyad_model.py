"""Inspect the checked-in permanent DYAD model policy.

The 2026-09-10 operator selection is a project policy, not a Saved runtime pin.
This tool never writes Saved files, loads/evicts models, or changes context.
Changing or clearing fixed mode requires an explicit operator-owned code change.

Usage:
  python tools/dyad_model.py
  python tools/dyad_model.py qwen3.8-27b-nvfp4-mtp   # verify/no-op
  python tools/dyad_model.py auto                    # refused in fixed mode
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path


LMSTUDIO_URL = "http://localhost:1234"
POLICY = Path(__file__).resolve().parent.parent / "ChimeraEngine" / "dyad_model_policy.json"


class PolicyError(ValueError):
    pass


def read_policy() -> dict:
    try:
        payload = json.loads(POLICY.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        raise PolicyError(f"cannot read permanent DYAD policy {POLICY}: {e}") from e
    if not isinstance(payload, dict):
        raise PolicyError("permanent DYAD policy must be a JSON object")
    if payload.get("schema") != "chimera-dyad-model-policy-v1":
        raise PolicyError("unsupported permanent DYAD policy schema")
    if payload.get("mode") != "fixed":
        raise PolicyError("DYAD policy mode must be 'fixed'")
    for field in ("model_id", "model_relative_path"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise PolicyError(f"permanent DYAD policy requires non-empty {field}")
    return payload


def loaded_ids() -> list[str]:
    """Return only model ids explicitly loaded according to the native API."""
    with urllib.request.urlopen(LMSTUDIO_URL + "/api/v0/models", timeout=4) as r:
        payload = json.load(r)
    if not isinstance(payload, dict) or not isinstance(payload.get("data", []), list):
        raise PolicyError("LM Studio returned a malformed loaded-model list")
    loaded = []
    for record in payload.get("data", []):
        if not isinstance(record, dict):
            continue
        if record.get("state") == "loaded" or record.get("status") == "loaded":
            model_id = record.get("id")
            if isinstance(model_id, str) and model_id and model_id not in loaded:
                loaded.append(model_id)
    return loaded


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        policy = read_policy()
    except PolicyError as e:
        print(f"REFUSED [dyad_model_policy_invalid]: {e}")
        return 2

    intended = policy["model_id"]
    print("DYAD model policy: fixed")
    print(f"model id        : {intended}")
    print(f"LM Studio path  : {policy['model_relative_path']}")
    print(f"policy file     : {POLICY}")

    if args:
        requested = args[0].strip()
        if requested != intended:
            print(
                f"REFUSED [dyad_model_policy_permanent]: runtime selection {requested!r} "
                f"cannot replace permanent model {intended!r}. An operator-owned "
                "checked-in policy change is required."
            )
            return 2
        print("requested id already equals the permanent policy; no file was written")

    try:
        loaded = loaded_ids()
    except Exception as e:
        print(f"REFUSED [dyad_loaded_model_list_unavailable]: {e}")
        return 1
    print(f"loaded ids      : {loaded}")
    if intended not in loaded:
        print(
            f"REFUSED [dyad_required_model_not_loaded]: {intended!r} is not "
            "explicitly loaded"
        )
        return 1
    print("ready            : permanent DYAD model is explicitly loaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
