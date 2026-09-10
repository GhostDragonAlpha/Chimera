"""Validate bounded correspondence between a native demo capture and status IDs."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


VERDICTS = {"consistent_snapshot", "changed_during_capture", "insufficient_evidence"}
IDENTITY_KEYS = ("commit", "executable_sha256", "shader_sha256")


def _finite(value) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    return True


def _parse_time(value: str) -> datetime:
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
    if not isinstance(source, dict) or any(not source.get(k) for k in IDENTITY_KEYS):
        reasons.append("incomplete_source_identity")
    if expected:
        for key in IDENTITY_KEYS:
            if source.get(key) != expected.get(key):
                reasons.append(f"source_mismatch_{key}")
    parsed = urlparse(str(record.get("endpoint", "")))
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        reasons.append("endpoint_not_loopback")
    if not isinstance(process, dict) or not isinstance(process.get("pid"), int) or process.get("pid", 0) <= 0 or not process.get("exe"):
        reasons.append("incomplete_process_identity")
    if expected:
        if "pid" in expected and process.get("pid") != expected["pid"]:
            reasons.append("process_identity_mismatch")
        if "exe" in expected and process.get("exe") != expected["exe"]:
            reasons.append("process_identity_mismatch")
    for name, status in (("before", before), ("after", after)):
        if not isinstance(status, dict):
            reasons.append(f"{name}_status_not_object")
        elif not _finite(status):
            reasons.append(f"{name}_status_nonfinite")
        elif not status.get("accepted_state_id"):
            reasons.append(f"{name}_accepted_state_id_missing")
    if not isinstance(capture, dict) or not capture.get("path") or not capture.get("sha256"):
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
        started, finished = _parse_time(request["started_utc"]), _parse_time(request["finished_utc"])
        if finished < started:
            reasons.append("request_time_reversed")
    except (KeyError, TypeError, ValueError):
        reasons.append("request_timestamps_invalid")
    if reasons:
        verdict = "insufficient_evidence"
    elif before["accepted_state_id"] != after["accepted_state_id"]:
        verdict = "changed_during_capture"
    else:
        verdict = "consistent_snapshot"
    return {"verdict": verdict, "reasons": reasons,
            "accepted_state_ids": [before.get("accepted_state_id"), after.get("accepted_state_id")],
            "render_submission_identity": "bound" if before.get("render_state_id") and after.get("render_state_id") else "unbound",
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
