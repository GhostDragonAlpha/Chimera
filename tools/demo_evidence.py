"""Validate bounded correspondence between a native demo capture and status IDs."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


VERDICTS = {"consistent_snapshot", "changed_during_capture", "insufficient_evidence"}
IDENTITY_KEYS = ("commit", "executable_sha256", "shader_sha256")


def _finite(value) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        try:
            return math.isfinite(value)
        except (OverflowError, ValueError):
            return False
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    return True


def _uint64(value, positive=False) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)
            and (value > 0 if positive else value >= 0) and value <= 0xFFFFFFFFFFFFFFFF)


def _number(value) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _hex(value, length: int) -> bool:
    return isinstance(value, str) and re.fullmatch(rf"[0-9a-fA-F]{{{length}}}", value) is not None


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise TypeError
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_record(record: dict, expected: dict | None = None) -> dict:
    reasons = []
    required = ("source", "endpoint", "process", "before", "after", "capture", "request")
    if not isinstance(record, dict):
        return {"verdict": "insufficient_evidence", "reasons": ["record_not_object"]}
    reasons.extend(f"missing_{key}" for key in required if key not in record)
    source = record.get("source", {})
    process = record.get("process", {})
    before = record.get("before", {})
    after = record.get("after", {})
    capture = record.get("capture", {})
    request = record.get("request", {})
    source_obj = source if isinstance(source, dict) else {}
    process_obj = process if isinstance(process, dict) else {}
    if not isinstance(source, dict) or not _hex(source.get("commit"), 40) or not _hex(source.get("executable_sha256"), 64) or not _hex(source.get("shader_sha256"), 64):
        reasons.append("incomplete_source_identity")
    if expected and not isinstance(expected, dict):
        reasons.append("expected_identity_not_object")
        expected = None
    if expected:
        if any(key in expected and not _hex(expected.get(key), 40 if key == "commit" else 64)
               for key in IDENTITY_KEYS):
            reasons.append("expected_identity_invalid")
        for key in IDENTITY_KEYS:
            if key in expected and source_obj.get(key) != expected.get(key):
                reasons.append(f"source_mismatch_{key}")
    endpoint = record.get("endpoint")
    try:
        parsed = urlparse(endpoint) if isinstance(endpoint, str) else None
    except ValueError:
        parsed = None
    try:
        endpoint_bad = (parsed is None or parsed.scheme != "http"
                        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
                        or parsed.username is not None or parsed.password is not None
                        or parsed.port is None or not (1 <= parsed.port <= 65535))
    except ValueError:
        endpoint_bad = True
    if endpoint_bad:
        reasons.append("endpoint_not_loopback")
    if expected and "endpoint" in expected and endpoint != expected["endpoint"]:
        reasons.append("endpoint_mismatch")
    if not isinstance(process, dict) or not _uint64(process.get("pid"), positive=True) or not isinstance(process.get("exe"), str) or not process.get("exe"):
        reasons.append("incomplete_process_identity")
    if expected:
        if "pid" in expected and process_obj.get("pid") != expected["pid"]:
            reasons.append("process_identity_mismatch")
        if "exe" in expected and process_obj.get("exe") != expected["exe"]:
            reasons.append("process_identity_mismatch")
    for name, status in (("before", before), ("after", after)):
        if not isinstance(status, dict):
            reasons.append(f"{name}_status_not_object")
        else:
            if not _finite(status):
                reasons.append(f"{name}_status_nonfinite")
            for field in ("accepted_state_id", "render_state_id", "iteration", "energy", "centre"):
                if field not in status:
                    reasons.append(f"{name}_{field}_missing")
            if not _uint64(status.get("accepted_state_id"), positive=True):
                reasons.append(f"{name}_accepted_state_id_invalid")
            if not _uint64(status.get("render_state_id")):
                reasons.append(f"{name}_render_state_id_invalid")
            if not _uint64(status.get("iteration")):
                reasons.append(f"{name}_iteration_invalid")
            if not _number(status.get("energy")):
                reasons.append(f"{name}_energy_invalid")
            centre = status.get("centre")
            if not isinstance(centre, list) or len(centre) != 3 or not all(_number(v) for v in centre):
                reasons.append(f"{name}_centre_invalid")
    if not isinstance(capture, dict) or not isinstance(capture.get("path"), (str, Path)) or not _hex(capture.get("sha256"), 64):
        reasons.append("capture_identity_missing")
    else:
        path = Path(capture["path"])
        try:
            actual = _sha(path)
            if actual.lower() != str(capture["sha256"]).lower():
                reasons.append("capture_hash_mismatch")
        except OSError:
            reasons.append("capture_unreadable")
    try:
        if not isinstance(request, dict):
            raise TypeError
        started, finished = _parse_time(request["started_utc"]), _parse_time(request["finished_utc"])
        if finished < started:
            reasons.append("request_time_reversed")
    except (KeyError, TypeError, ValueError):
        reasons.append("request_timestamps_invalid")
    before_obj = before if isinstance(before, dict) else {}
    after_obj = after if isinstance(after, dict) else {}
    compared_fields = ("accepted_state_id", "render_state_id", "iteration", "energy", "centre",
                       "material_snapshot", "centre_force")
    changed = (not reasons and any(before.get(field) != after.get(field)
                                   for field in compared_fields
                                   if field in before_obj or field in after_obj))
    if reasons:
        verdict = "insufficient_evidence"
    elif changed:
        verdict = "changed_during_capture"
    else:
        verdict = "consistent_snapshot"
    return {"verdict": verdict, "reasons": reasons,
            "accepted_state_ids": [before_obj.get("accepted_state_id"), after_obj.get("accepted_state_id")],
            "render_submission_identity": "unbound",
            "render_state_ids_present": [before_obj.get("render_state_id"), after_obj.get("render_state_id")],
            "physics_certified": False}


def write_result(result: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("record", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--expected", type=Path)
    args = ap.parse_args(argv)
    record = json.loads(args.record.read_text(encoding="utf-8"))
    expected = json.loads(args.expected.read_text(encoding="utf-8")) if args.expected else None
    result = validate_record(record, expected)
    write_result(result, args.output)
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == "consistent_snapshot" else 1


if __name__ == "__main__":
    raise SystemExit(main())
