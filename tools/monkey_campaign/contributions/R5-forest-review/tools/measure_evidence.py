"""R5-forest-review correction evidence — measured fresh, read-only, CPU-only, stdlib-only.

Usage:
  python -B measure_evidence.py <play_worktree> <evidence_out_dir>

Re-measures every identity the corrected review cites:
  - the two claim commits and their subjects;
  - sha256 + git blob ids of the cited documents (R5 review, board, map, F02/F04 reports);
  - pass-flag counts of the three committed R5 receipts (15/36/19 expected);
  - F05/F06 artifact absence (no agent dirs, no tracked files, no board state);
  - first-hand engine contact citations (single-plane / sphere-vs-plane / strict extent);
  - verbatim F05/F06/W10/W05 rows from MONKEY_COMPLETION_MAP.md.

Writes identities.json into <evidence_out_dir>. Touches nothing outside it.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

PLAY = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2]).resolve()

CLAIM_COMMIT = "9afbddcd90164b5544a16fd0bc72278d985eb6e3"
REVIEW_COMMIT = "dc7ea81111d98f32a4d88252c59f2fb8cf3c7399"

DOCS = [
    "tools/monkey_campaign/agents/R5_forest_review/report.md",
    "tools/monkey_campaign/agents/R5_forest_review/brief.md",
    "tools/monkey_campaign/agents/R5_forest_review/receipts/identity_receipt.json",
    "tools/monkey_campaign/agents/R5_forest_review/receipts/integrated_receipt.json",
    "tools/monkey_campaign/agents/R5_forest_review/receipts/citations_receipt.json",
    "tools/monkey_campaign/PLAY_BOARD.md",
    "tools/monkey_campaign/MONKEY_COMPLETION_MAP.md",
    "tools/monkey_campaign/agents/F02_terrain/report.md",
    "tools/monkey_campaign/agents/F04_contact/report.md",
    "ChimeraEngine/engine/gait_controller.hpp",
    "ChimeraEngine/engine/earth_environment.hpp",
]

RECEIPTS = {
    "identity_receipt.json": 15,
    "integrated_receipt.json": 36,
    "citations_receipt.json": 19,
}

ENGINE_CITATIONS = [
    ("ChimeraEngine/engine/gait_controller.hpp", 94, "plane_model_y_"),
    ("ChimeraEngine/engine/gait_controller.hpp", 2005, "contact_friction"),
    ("ChimeraEngine/engine/earth_environment.hpp", 67, "dot(x,n_)-r_"),
    ("ChimeraEngine/engine/earth_environment.hpp", 118, "patch_half_width_m"),
]

MAP_ROWS = ["| F05 |", "| F06 |", "| W05 |", "| W10 |"]


def git(*args):
    return subprocess.run(
        ["git", "-C", str(PLAY), *args], capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def main():
    result = {
        "schema": "r5.correction.evidence.v1",
        "play_worktree": str(PLAY),
        "claims": {},
        "documents": {},
        "r5_receipts": {},
        "f05_f06_absence": {},
        "engine_citations": {},
        "map_rows": {},
        "checks": [],
    }

    def check(name, ok, detail):
        result["checks"].append({"check": name, "ok": bool(ok), "detail": detail})

    # 1. Claim commits -------------------------------------------------------
    for label, rev, needle in [
        ("front_complete_claim", CLAIM_COMMIT, "FOREST FRONT F01-F08 COMPLETE; W10 scene-ready"),
        ("r5_w10_scene_ready_claim", REVIEW_COMMIT, "W10 SCENE-READY"),
    ]:
        subject = git("log", "--format=%s", "-1", rev)
        result["claims"][label] = {"commit": rev, "subject": subject}
        check(f"claim_{label}", needle in subject, f"subject contains {needle!r}: {needle in subject}")

    # 2. Document identities -------------------------------------------------
    for rel in DOCS:
        p = PLAY / rel
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        blob_at_head = git("rev-parse", f"HEAD:{rel}")
        blob_at_claim = git("rev-parse", f"{CLAIM_COMMIT}:{rel}") if label_needs(rel) else ""
        result["documents"][rel] = {
            "sha256": digest,
            "blob_head": blob_at_head,
            "blob_at_claim_commit": blob_at_claim,
            "bytes": p.stat().st_size,
        }
    check(
        "doc_identities_measured",
        len(result["documents"]) == len(DOCS),
        f"{len(result['documents'])}/{len(DOCS)} documents hashed",
    )

    # 3. R5 receipt pass counts ----------------------------------------------
    for name, expected in RECEIPTS.items():
        rel = f"tools/monkey_campaign/agents/R5_forest_review/receipts/{name}"
        data = json.loads((PLAY / rel).read_text(encoding="utf-8"))
        checks = data["checks"]
        passed = sum(1 for c in checks if c.get("ok") is True or c.get("pass") is True)
        result["r5_receipts"][name] = {"total": len(checks), "pass_flagged": passed}
        check(
            f"receipt_{name}",
            passed == expected and len(checks) == expected,
            f"{passed}/{len(checks)} pass-flagged (report claims {expected})",
        )

    # 4. F05/F06 artifact absence ---------------------------------------------
    agents_dir = PLAY / "tools/monkey_campaign/agents"
    dirs = sorted(d.name for d in agents_dir.iterdir() if d.is_dir())
    f05_dirs = [d for d in dirs if d.upper().startswith(("F05", "F06"))]
    tracked = git("ls-files", "tools/monkey_campaign")
    f05_tracked = [ln for ln in tracked.splitlines() if re.search(r"/F0[56]|F0[56][_/.]", ln)]
    board = (PLAY / "tools/monkey_campaign/PLAY_BOARD.md").read_text(encoding="utf-8")
    forest_row = next(ln for ln in board.splitlines() if ln.startswith("| Forest |"))
    result["f05_f06_absence"] = {
        "agent_dirs_present": dirs,
        "f05_f06_dirs": f05_dirs,
        "f05_f06_tracked_files": f05_tracked,
        "forest_row": forest_row,
        "forest_row_names_f05_or_f06": ("F05" in forest_row) or ("F06" in forest_row),
    }
    check("f05_f06_no_agent_dirs", not f05_dirs, f"agent dirs matching F05/F06: {f05_dirs}")
    check("f05_f06_no_tracked_files", not f05_tracked, f"tracked files matching: {f05_tracked}")
    check(
        "f05_f06_not_on_board",
        not result["f05_f06_absence"]["forest_row_names_f05_or_f06"],
        "Forest front row of PLAY_BOARD.md names no F05/F06 state",
    )

    # 5. Engine citations ------------------------------------------------------
    for rel, line_no, needle in ENGINE_CITATIONS:
        src = (PLAY / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        line = src[line_no - 1]
        result["engine_citations"][f"{rel}:{line_no}"] = {
            "line": line.strip(),
            "contains": needle in line,
        }
        check(f"engine_{rel.split('/')[-1]}:{line_no}", needle in line, f"expected {needle!r} in line {line_no}")

    # 6. Map rows verbatim ------------------------------------------------------
    map_text = (PLAY / "tools/monkey_campaign/MONKEY_COMPLETION_MAP.md").read_text(encoding="utf-8")
    for prefix in MAP_ROWS:
        row = next(ln for ln in map_text.splitlines() if ln.startswith(prefix))
        result["map_rows"][prefix.strip("| ").split()[0]] = row

    passed = sum(1 for c in result["checks"] if c["ok"])
    result["summary"] = f"{passed}/{len(result['checks'])} evidence checks green"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "identities.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(result["summary"])
    for c in result["checks"]:
        print(("PASS" if c["ok"] else "FAIL"), c["check"], "-", c["detail"][:100])
    return 0 if passed == len(result["checks"]) else 1


def label_needs(rel):
    # Only pre-existing docs can resolve at the claim commit; R5's dir landed later.
    return not rel.startswith("tools/monkey_campaign/agents/R5_forest_review")


if __name__ == "__main__":
    sys.exit(main())
