"""Offline qualification checks for the grasp-contract admission."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from tools.creature_graph import project_spec
from tools.creature_graph.store import CreatureGraph

ROOT = Path(__file__).resolve().parents[4]
GRAPH = ROOT / "tools/creature_graph/data/creature_graph.json"
PRESTUDY = ROOT / "tools/science_funnel/validation/grasp_contract_20260918/prestudy.json"
WORK_ID = "work.creature.coupled_arm_grasp"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    graph = CreatureGraph.load(str(GRAPH))
    errors = list(graph.check()) + list(project_spec.check(graph))
    work = graph.get(WORK_ID)
    if len(graph.by_kind("evidence")) != 11:
        errors.append(f"historical evidence count changed: {len(graph.by_kind('evidence'))} != 11")
    if work["status"] != "specified":
        errors.append("admission incorrectly claims implementation status")
    if work["evidence"]:
        errors.append("admission added evidence instead of preserving the 11 historical records")
    study = json.loads(PRESTUDY.read_text(encoding="utf-8"))
    if study["rank"]["opposing_row_rank"] != 1:
        errors.append("opposing plane pair did not remain rank one")
    if not study["kkt_example"]["cone_pass"]:
        errors.append("worked KKT example failed its declared cone")
    if not study["catch_example"]["dissipation_split_closes"]:
        errors.append("catch dissipation split does not close")
    if abs(study["catch_example"]["point_velocity_after_m_per_s"][0]) > 1e-12:
        errors.append("catch normal closing velocity was not zeroed")
    dynamics_path = "ChimeraEngine/engine/coupled_dynamics.hpp"
    actual = sha256(ROOT / dynamics_path)
    unchanged = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", dynamics_path],
                               cwd=ROOT).returncode == 0
    if not unchanged:
        errors.append("qualified coupled_dynamics.hpp changed in this lane")
    report = {
        "schema": "chimera.grasp_contract_qualification.v1",
        "work_id": WORK_ID,
        "graph_hash": graph.graph_hash(),
        "project_spec_ok": not project_spec.check(graph),
        "graph_ok": not graph.check(),
        "historical_evidence_count": len(graph.by_kind("evidence")),
        "historical_evidence_unchanged": len(graph.by_kind("evidence")) == 11,
        "prestudy_schema": study["schema"],
        "qualified_coupled_dynamics_sha256": actual,
        "qualified_coupled_dynamics_unchanged_in_lane": unchanged,
        "errors": errors,
        "pass": not errors,
        "scope": "Admission and offline derivation only; no runtime grasp implementation.",
    }
    report_path = ROOT / "tools/science_funnel/validation/grasp_contract_20260918/qualification.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
