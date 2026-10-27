"""CPU checks for matter_metrics.py using a temporary bundle fixture."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "matter_metrics.py"


def make_bundle(root: Path) -> Path:
    reports = root / "flow" / "reports"
    reports.mkdir(parents=True)
    (reports / "spatial-1.json").write_text(json.dumps(
        {"stage": "spatial", "status": "NEEDS_EVIDENCE", "wall_seconds": 10.0}), encoding="utf-8")
    (reports / "spatial-2.json").write_text(json.dumps(
        {"stage": "spatial", "status": "READY", "wall_seconds": 20.0}), encoding="utf-8")
    (reports / "broken-1.json").write_text("{not json", encoding="utf-8")
    (reports / "unrelated-9.json").write_text("{}", encoding="utf-8")
    (root / "flow" / "timings.json").write_text(json.dumps(
        [{"stage": "spatial", "elapsed_seconds": 100.0, "tokens": 500}]), encoding="utf-8")
    return root


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        bundle = make_bundle(Path(tmp))
        out = subprocess.run([sys.executable, "-B", str(SCRIPT), str(bundle)],
                             capture_output=True, text=True, check=True)
        result = json.loads(out.stdout)
        spatial = result["stages"]["spatial"]
        assert spatial["attempts"] == 2, spatial
        assert spatial["rework"] == 1, spatial
        assert spatial["agent_wall_seconds"] == 30.0, spatial
        assert spatial["statuses"] == ["NEEDS_EVIDENCE", "READY"], spatial
        assert "broken" not in json.dumps(result["stages"]), "broken fixture must not crash stages"
        assert result["workflow_run_seconds"] == 100.0, result
        assert result["workflow_run_tokens"] == 500, result
        assert result["rework_total"] == 1, result
        # Empty bundle: zero stages, exit 0.
        empty = Path(tmp) / "empty"
        (empty / "flow").mkdir(parents=True)
        out2 = subprocess.run([sys.executable, "-B", str(SCRIPT), str(empty)],
                              capture_output=True, text=True, check=True)
        assert json.loads(out2.stdout)["stages"] == {}, out2.stdout
    print("test_matter_metrics: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
