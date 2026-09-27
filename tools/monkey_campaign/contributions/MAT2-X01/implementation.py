"""implementation.py -- MAT2-X01: the small game's repeatable objective,
re-derived from CURRENT frozen records (no invention, no archived-DONE
promotion).

Sources (full-hash identity-verified at run time):
  - the frozen MAT2-P01 completion contract (board evidence artifact,
    sha256 e255eb44... pinned; merged at 97993cbe via PR #192)
  - the pinned authority files it names (MATERIAL_PLAN_ADOPTION.md,
    APPROVED_SCOPE.json, docs/MONKEY_RUN.md)
  - the current operator completion catalog (monkey_completion_map.json +
    docs/roadmap/holodeck_tasks.json), where K08/X02/S05 are live tasks

Output: objective_definition.json (schema mat2-x01.objective.v1) -- the
selected finite repeatable objective (complete-game framing, one loop,
explicit success/failure, free-play repetition, material-first milestone
order, no-campaign law), explicit unresolved inventory, the one carried
operator decision request, a legacy crosswalk with provenance, and an
evidence map whose every quote must reproduce from its pinned source.

CPU-only, stdlib only. Any identity mismatch refuses loudly (ExtractionFailure)
and no artifact is written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

CONTRACT = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/lead-verify-20260926/"
    "MAT2-P01-accept-materialized/contract.json")
CONTRACT_SHA256 = "e255eb44203212c039598d28629c21e6e1c019d1abe6caa07b4430fca53715a5"

MATERIAL_PLAN = pathlib.Path(
    "E:/PythonChimera/tools/monkey_campaign/MATERIAL_PLAN_ADOPTION.md")
MATERIAL_PLAN_SHA256 = "81f432fc9fcee8aee6fcdcac39487f50538f1f4c1b9d4c2821d3bb0f40e47287"
APPROVED_SCOPE = pathlib.Path(
    "E:/PythonChimera/tools/monkey_campaign/APPROVED_SCOPE.json")
APPROVED_SCOPE_SHA256 = "fe74180d7b6ad584f48c5fd9a642db4393c26c4e4cd64c8b41652e9b30c27660"
MONKEY_RUN = pathlib.Path("E:/PythonChimera/docs/MONKEY_RUN.md")
MONKEY_RUN_SHA256 = "2d4611802c6338c26c43bd5217e59ab514588a0a25b949ac5c8fbbe22651359d"
COMPLETION_MAP = pathlib.Path(
    "E:/PythonChimera/tools/monkey_campaign/monkey_completion_map.json")
COMPLETION_MAP_SHA256 = "8fa2e1409a2da1e3cbe70a84f59f7620a61d3eed12519171190e9c61543cb272"
HOLODECK_CATALOG = pathlib.Path(
    "E:/PythonChimera/docs/roadmap/holodeck_tasks.json")
HOLODECK_CATALOG_SHA256 = "d5c7aa8b9e264e96bb3de6a0f3d48069ee0b88c9f10ae84b52bd8cfce797fcd8"

SCOPE_SHA = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
ARCHIVED_SCOPE_SHA = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
P01_CRITERIA_SHA = "e4521ad79a5bc263ba333b81ebe36599e1d6da5a13eed92c2ff5fa3a0e670c5e"
CARD_CRITERIA_SHA = "e2f2c219a438c9575c01698dc5dd66f799f6eef8a7577ad3571dcae8c8d1c9aa"
INSTRUCTION_REVISION = "astra-0031"

CARD_DONE_WHEN = (
    "A finite purpose/lesson/free-play completion definition is selected "
    "without inventing a campaign"
)
SCHEMA = "mat2-x01.objective.v1"

# Legacy crosswalk provenance (read-only; NOT promoted to acceptance).
LEGACY = {
    "card": "ONT-X01",
    "attempt_id": "30614130594b42b1afd8cbcfe5e6c840",
    "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/136",
    "pr_head_sha": "0c9a615cceccf7f7269b9545f555bd2be8daa138",
    "criteria_sha256": "ff69d9a1099058276b43af6721a2ff118523235f936bc6de0782173dbbbaa74f",
    "archived_scope_sha256": ARCHIVED_SCOPE_SHA,
    "archived_contract_sha256": "80b2e2f2736ce6fd594633f85fa22bda702991c3ed4d415a0d9c4eadd377163b",
    "definition_rerun_sha256": "45e97fc64df8f28b15da80affc0124af5a631075149806503e81a3108960057d",
    "state": "DONE (archived board); reused as structure/provenance only",
}


class ExtractionFailure(RuntimeError):
    pass


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def require_id(path: pathlib.Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise ExtractionFailure(f"{label}_missing {path}")
    actual = sha256_file(path)
    if actual != expected:
        raise ExtractionFailure(
            f"{label}_identity_mismatch expected {expected} got {actual}")


def load_pinned() -> dict:
    """P1/P3/P4: identity-pin every record; refuse loudly on drift."""
    require_id(CONTRACT, CONTRACT_SHA256, "mat2_p01_contract")
    require_id(MATERIAL_PLAN, MATERIAL_PLAN_SHA256, "material_plan_adoption")
    require_id(APPROVED_SCOPE, APPROVED_SCOPE_SHA256, "approved_scope")
    require_id(MONKEY_RUN, MONKEY_RUN_SHA256, "monkey_run")
    require_id(COMPLETION_MAP, COMPLETION_MAP_SHA256, "completion_map")
    require_id(HOLODECK_CATALOG, HOLODECK_CATALOG_SHA256, "holodeck_catalog")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("schema") != "chimera.completion_contract.v1":
        raise ExtractionFailure("contract_schema_unexpected")
    if contract.get("task_id") != "MAT2-P01":
        raise ExtractionFailure("contract_task_id_mismatch")
    ids = contract.get("identities") or {}
    expected_ids = {
        "criteria_sha256": P01_CRITERIA_SHA,
        "active_scope_sha256": SCOPE_SHA,
        "archived_scope_sha256": ARCHIVED_SCOPE_SHA,
        "instruction_revision": INSTRUCTION_REVISION,
    }
    for key, val in expected_ids.items():
        if ids.get(key) != val:
            raise ExtractionFailure(
                f"contract_identity_mismatch {key}: expected {val}")

    catalog = json.loads(COMPLETION_MAP.read_text(encoding="utf-8"))
    if catalog.get("schema") != "chimera-monkey-completion-planning-handoff-v1":
        raise ExtractionFailure("completion_map_schema_unexpected")
    if (catalog.get("revision") or {}).get("id") != "material-first-v2":
        raise ExtractionFailure("completion_map_revision_unexpected")
    tasks = {t.get("id"): t for t in catalog.get("tasks", [])}
    for needed in ("K08", "X02", "S05", "X01", "F01", "P06", "P01"):
        if needed not in tasks:
            raise ExtractionFailure(f"catalog_task_missing {needed}")
    return {"contract": contract, "catalog": catalog, "tasks": tasks}


def quote(source_text: str, needle: str, label: str) -> str:
    """P4/F5 oracle: the quote must reproduce (whitespace-normalized)."""
    if norm(needle) not in norm(source_text):
        raise ExtractionFailure(f"quote_not_reproduced {label}")
    return needle


def extract() -> dict:
    pinned = load_pinned()
    contract = pinned["contract"]
    catalog = pinned["catalog"]
    tasks = pinned["tasks"]

    run_text = MONKEY_RUN.read_text(encoding="utf-8")

    core_clause = contract["core_clause"]["text"]
    quote(json.dumps(contract), core_clause, "contract.core_clause")
    material_addition = contract["material_first_addition"]["text"]
    quote(json.dumps(contract), material_addition, "contract.material_first_addition")
    game_completion = contract["completion_semantics"]["game_completion"]
    quote(json.dumps(contract), game_completion, "contract.game_completion")

    # P2 CLAUSE_CARRY: the frozen clauses carry verbatim inside the current
    # catalog's P01 done_when sentence (the planning clauses the contract
    # froze), exactly as the MAT2-P01 acceptance test enforced.
    p01_done = tasks["P01"]["done_when"]
    quote(json.dumps(tasks["P01"]), p01_done, "catalog.P01.done_when")
    if norm(core_clause) not in norm(p01_done):
        raise ExtractionFailure("core_clause_not_carried_in_p01_done_when")
    if norm(material_addition) not in norm(p01_done):
        raise ExtractionFailure("material_addition_not_carried_in_p01_done_when")

    k08_done = tasks["K08"]["done_when"]
    quote(json.dumps(tasks["K08"]), k08_done, "catalog.K08.done_when")
    x02_done = tasks["X02"]["done_when"]
    quote(json.dumps(tasks["X02"]), x02_done, "catalog.X02.done_when")
    s05_done = tasks["S05"]["done_when"]
    quote(json.dumps(tasks["S05"]), s05_done, "catalog.S05.done_when")
    x01_observation = tasks["X01"]["observation"]
    quote(json.dumps(tasks["X01"]), x01_observation, "catalog.X01.observation")
    finish_line = catalog["finish_line"]
    quote(json.dumps(catalog), finish_line, "catalog.finish_line")

    goal_line = (
        "The goal is one physically controlled monkey in a small forest: "
        "walk on all fours, steer, stop, approach a rigid trunk, attach, "
        "climb, hold, descend, release and walk again, with a usable camera "
        "and complete player flow."
    )
    quote(run_text, goal_line, "monkey_run.goal_line")
    physical_law = "No kinematic locomotion substitute or invisible support force is permitted."
    quote(run_text, physical_law, "monkey_run.physical_law")
    backlog_law = "Keep broader Chimera features in the later backlog."
    quote(run_text, backlog_law, "monkey_run.backlog_law")
    b_required = (
        "The selected material assembly consumes B01-B07, so those seven "
        "items are required in this revision."
    )
    quote(run_text, b_required, "monkey_run.b01_b07_required")

    # Card done_when must itself be live in the current catalog (X01).
    if norm(tasks["X01"]["done_when"]) != norm(CARD_DONE_WHEN):
        raise ExtractionFailure("card_done_when_drift_from_catalog")

    definition = {
        "schema": SCHEMA,
        "card": "MAT2-X01",
        "planning_id": "X01",
        "done_when": CARD_DONE_WHEN,
        "selected_definition": {
            "framing": {
                "choice": "complete game (not movement demo)",
                "recovered_from": goal_line,
                "observation_source": x01_observation,
            },
            "repeatable_objective": {
                "definition": (
                    "ONE complete ground -> trunk -> climb -> hold -> "
                    "descend -> release -> ground loop, in one session, "
                    "repeated as free play"
                ),
                "finite_frame_core_clause_verbatim": core_clause,
                "success_loop_clause_current_verbatim": k08_done,
                "failure_semantics": (
                    "explicit success/failure behavior per the frozen core "
                    "clause; failures stay physical under the pinned law: "
                    + physical_law
                ),
                "repetition": (
                    "free-play repetition, no scripted progression; the "
                    "loop is the whole game frame, so each session is one "
                    "more attempt at the same finite objective"
                ),
                "milestone_order_material_first_verbatim": material_addition,
            },
            "session_and_completion_semantics": {
                "card_completion": contract["completion_semantics"]["card_completion"],
                "game_completion": game_completion,
                "session_flow_owner": {
                    "task": "MAT2-X02",
                    "done_when_current_verbatim": x02_done,
                },
                "operator_acceptance_owner": {
                    "task": "S05",
                    "done_when_current_verbatim": s05_done,
                },
            },
            "no_campaign_law": {
                "contract_clause_verbatim": (
                    "broader features excluded"),
                "catalog_finish_line_verbatim": finish_line,
                "monkey_run_backlog_law_verbatim": backlog_law,
                "note": (
                    "In this revision the selected material assembly "
                    "consumes B01-B07 as required selected tasks; that is "
                    "the approved scope, not a campaign: nothing outside "
                    "the selected tasks gates completion.")
            },
        },
        "unresolved_inventory": [
            {
                "id": "mat2-f01-spatial-envelope",
                "pending": "finite clearing extent/coordinates and safe spawn",
                "owner_card": "MAT2-F01",
                "owner_done_when_current_verbatim": tasks["F01"]["done_when"],
                "archived_envelope_numbers_promoted": False,
            },
            {
                "id": "mat2-p06-acceptance-limits",
                "pending": "hardware/controls/duration/latency/frame-time limits",
                "owner_card": "MAT2-P06",
                "archived_limit_values_promoted": False,
            },
            {
                "id": "mat2-x02-session-flow",
                "pending": "start/pause/restart/exit implementation (definition names the owner only)",
                "owner_card": "MAT2-X02",
            },
        ],
        "operator_decision_requests": [
            {
                "id": "objective-presentation-surface",
                "question": "How is the repeatable loop surfaced to the player?",
                "options": [
                    "silent free-play (no counter)",
                    "attempt counter (loops completed this session)",
                    "timer + counter",
                ],
                "recommendation": (
                    "attempt counter (loops completed this session) -- the "
                    "page's existing state feedback carries it without a new "
                    "HUD surface; no thresholds, no scores"),
                "provenance": (
                    "carried unresolved from ONT-X01; disclosed open in the "
                    "lead review of PR #136 (presentation, not definition)"),
            }
        ],
        "legacy_crosswalk": {
            "reused": [
                "definition structure (selected_definition / framing / no_campaign_law / single decision request)",
                "objective-presentation-surface decision request (still unresolved)",
            ],
            "not_carried": [
                "archived envelope numbers (20.0 m clearing half-width; trunk 11.976783/2.471766) -- spatial envelope is MAT2-F01 scope, not yet frozen",
                "archived 'B01-B07 never auto-activated' wording -- obsolete: this revision requires B01-B07 as selected tasks",
                "K08 sourced from the archived contract -- now cited from the live catalog",
                "archived SC-FAILURE-BEHAVIOR verbatim clause -- replaced by the frozen core clause plus the pinned MONKEY_RUN physical law",
            ],
            "promotion_claim": "NONE -- archived DONE is not new acceptance",
            "provenance": LEGACY,
        },
        "evidence_map": {
            "finite_frame_core_clause_verbatim": {
                "path": str(CONTRACT), "sha256": CONTRACT_SHA256,
                "quote": core_clause},
            "p01_done_when_carry": {
                "path": str(COMPLETION_MAP), "sha256": COMPLETION_MAP_SHA256,
                "quote": p01_done},
            "milestone_order_material_first_verbatim": {
                "path": str(CONTRACT), "sha256": CONTRACT_SHA256,
                "quote": material_addition},
            "success_loop_clause_current_verbatim": {
                "path": str(COMPLETION_MAP), "sha256": COMPLETION_MAP_SHA256,
                "quote": k08_done},
            "framing_recovered_from": {
                "path": str(MONKEY_RUN), "sha256": MONKEY_RUN_SHA256,
                "quote": goal_line},
            "failure_semantics_law": {
                "path": str(MONKEY_RUN), "sha256": MONKEY_RUN_SHA256,
                "quote": physical_law},
            "no_campaign_backlog_law": {
                "path": str(MONKEY_RUN), "sha256": MONKEY_RUN_SHA256,
                "quote": backlog_law},
            "b01_b07_required_note": {
                "path": str(MONKEY_RUN), "sha256": MONKEY_RUN_SHA256,
                "quote": b_required},
            "card_completion": {
                "path": str(CONTRACT), "sha256": CONTRACT_SHA256,
                "quote": contract["completion_semantics"]["card_completion"]},
            "game_completion": {
                "path": str(CONTRACT), "sha256": CONTRACT_SHA256,
                "quote": game_completion},
            "session_flow_owner": {
                "path": str(COMPLETION_MAP), "sha256": COMPLETION_MAP_SHA256,
                "quote": x02_done},
            "operator_acceptance_owner": {
                "path": str(COMPLETION_MAP), "sha256": COMPLETION_MAP_SHA256,
                "quote": s05_done},
            "framing_observation_source": {
                "path": str(COMPLETION_MAP), "sha256": COMPLETION_MAP_SHA256,
                "quote": x01_observation},
            "no_campaign_catalog_finish_line": {
                "path": str(COMPLETION_MAP), "sha256": COMPLETION_MAP_SHA256,
                "quote": finish_line},
        },
        "records": {
            "criteria_sha256": CARD_CRITERIA_SHA,
            "active_scope_sha256": SCOPE_SHA,
            "archived_scope_sha256": ARCHIVED_SCOPE_SHA,
            "instruction_revision": INSTRUCTION_REVISION,
            "mat2_p01_contract_sha256": CONTRACT_SHA256,
            "material_plan_adoption_sha256": MATERIAL_PLAN_SHA256,
            "approved_scope_sha256": APPROVED_SCOPE_SHA256,
            "monkey_run_sha256": MONKEY_RUN_SHA256,
            "completion_map_sha256": COMPLETION_MAP_SHA256,
            "holodeck_catalog_sha256": HOLODECK_CATALOG_SHA256,
            "archived_ont_p01_contract_sha256": LEGACY["archived_contract_sha256"],
            "legacy_definition_rerun_sha256": LEGACY["definition_rerun_sha256"],
            "goal_line_verified_in_monkey_run": True,
        },
    }
    return definition


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="objective_definition.json")
    args = ap.parse_args(argv)
    definition = extract()
    pathlib.Path(args.out).write_text(
        json.dumps(definition, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({
        "schema": definition["schema"],
        "decision_requests": len(definition["operator_decision_requests"]),
        "evidence_quotes": len(definition["evidence_map"]),
        "unresolved_inventory": len(definition["unresolved_inventory"]),
        "contract_sha256": definition["records"]["mat2_p01_contract_sha256"][:16],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
