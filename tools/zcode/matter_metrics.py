"""Read-only metrics for a matter-construction bundle (chimera.matter-workflow.v1).

Aggregates the persistent checkpoints under flow/reports/ plus the
coordinator-recorded flow/timings.json (workflow run wall time and tokens,
which the actor reports cannot see). Reports measured agent wall time, rework
(extra attempts per stage) and per-stage status history. Resource sampling is
separate: use matter_observe.py for host/GPU/gateway samples.

Usage:
    C:/Python314/python.exe -B matter_metrics.py ABSOLUTE_BUNDLE
"""
import json
import re
import sys
from pathlib import Path

STAGES = ("spatial", "research", "experiment", "implement", "test", "review", "deliver")


def load_reports(bundle: Path) -> dict:
    reports = {stage: [] for stage in STAGES}
    reports_dir = bundle / "flow" / "reports"
    if not reports_dir.is_dir():
        return reports
    for path in sorted(reports_dir.glob("*.json")):
        match = re.match(r"([a-z]+)-(\d+)\.json$", path.name)
        if not match or match.group(1) not in reports:
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            reports[match.group(1)].append({"attempt": int(match.group(2)),
                                            "status": "UNREADABLE", "error": str(exc),
                                            "wall_seconds": 0.0, "path": str(path)})
            continue
        reports[match.group(1)].append({"attempt": int(match.group(2)),
                                        "status": report.get("status", "MISSING"),
                                        "wall_seconds": float(report.get("wall_seconds", 0.0) or 0.0),
                                        "path": str(path)})
    for stage in reports:
        reports[stage].sort(key=lambda item: item["attempt"])
    return reports


def main(argv: list) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    bundle = Path(argv[1])
    reports = load_reports(bundle)
    timings_path = bundle / "flow" / "timings.json"
    timings = []
    if timings_path.is_file():
        try:
            timings = json.loads(timings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            print(f"timings.json unreadable: {exc}", file=sys.stderr)

    stages_out = {}
    rework_total = 0
    agent_seconds = 0.0
    for stage, attempts in reports.items():
        if not attempts:
            continue
        rework = len(attempts) - 1
        rework_total += rework
        seconds = round(sum(a["wall_seconds"] for a in attempts), 3)
        agent_seconds += seconds
        stages_out[stage] = {
            "attempts": len(attempts),
            "rework": rework,
            "agent_wall_seconds": seconds,
            "statuses": [a["status"] for a in attempts],
            "last_status": attempts[-1]["status"],
            "report_paths": [a["path"] for a in attempts],
        }

    coordinator = [t for t in timings if t.get("source") != "workflow-script"]
    scripted = [t for t in timings if t.get("source") == "workflow-script"]
    run_seconds = round(sum(float(t.get("elapsed_seconds", 0.0)) for t in coordinator), 3)
    run_tokens = sum(int(t.get("tokens", 0)) for t in coordinator)
    stage_run_seconds = round(sum(float(t.get("elapsed_seconds", 0.0)) for t in scripted), 3)
    result = {
        "schema": "chimera.matter-metrics.v1",
        "bundle": str(bundle),
        "stages": stages_out,
        "rework_total": rework_total,
        "measured_agent_wall_seconds": round(agent_seconds, 3),
        "workflow_run_seconds": run_seconds,
        "workflow_run_tokens": run_tokens,
        "stage_run_seconds": stage_run_seconds,
        "timings_records": len(timings),
        "not_covered": "host/GPU/gateway resource sampling (matter_observe.py); "
                       "coordinator inference time; between-sample peaks",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
