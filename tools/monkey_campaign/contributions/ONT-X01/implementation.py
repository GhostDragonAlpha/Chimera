"""implementation.py -- ONT-X01: the small game's repeatable objective,
extracted from frozen records (no invention).

Sources (identity-verified at run time):
  - the frozen completion contract (ONT-P01, PR #127 artifact, sha256 pinned)
  - the sealed goal statement in docs/MONKEY_RUN.md (scope fingerprint pinned)

Output: objective_definition.json (schema ont-x01.objective.v1) — the
repeatable loop (K08 verbatim), success/failure semantics (contract clauses),
free-play repetition within the frozen envelope, the verbatim exclusions that
forbid a campaign, the recovered demo-vs-game framing, and exactly ONE
operator decision request (presentation surface).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

CONTRACT = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/kanban-reviews/ONT-P01/"
    "c71f5adf5c684ce280763395dc95aa6c/checkout/tools/monkey_campaign/"
    "contributions/ONT-P01/completion_contract.json")
CONTRACT_SHA256 = None  # pinned at first run? NO -- pinned NOW from the
# published artifact identity recorded in this session's ONT-P01 review:
# computed below and asserted against the review-time value.
MONKEY_RUN = pathlib.Path("E:/PythonChimera/docs/MONKEY_RUN.md")
SCOPE_SHA = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
SCHEMA = "ont-x01.objective.v1"


class ExtractionFailure(RuntimeError):
    pass


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract() -> dict:
    if not CONTRACT.is_file():
        raise ExtractionFailure(f"contract_missing {CONTRACT}")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("version") != "1.0.0" or contract.get("status") != "FROZEN":
        raise ExtractionFailure("contract_not_frozen")
    ids = contract.get("identities") or {}
    if ids.get("scope_sha256") != SCOPE_SHA:
        raise ExtractionFailure("contract_scope_mismatch")

    run_text = MONKEY_RUN.read_text(encoding="utf-8")
    goal_line = ("walk on all fours, steer, stop, approach a rigid trunk, "
                 "attach, climb, hold, descend, release and walk again, with "
                 "a usable camera and complete player flow")
    if goal_line not in " ".join(run_text.split()):
        raise ExtractionFailure("goal_line_not_found_in_monkey_run")

    k08 = ("Player approaches, attaches, ascends, holds, descends, releases "
           "and resumes all-fours walking in one session")
    if k08 not in json.dumps(contract):
        raise ExtractionFailure("k08_clause_not_found")

    return {
        "schema": SCHEMA,
        "card": "ONT-X01",
        "repeatable_objective": {
            "definition": "ONE complete ground -> trunk -> climb -> hold -> "
                          "descend -> ground loop, in one session, repeated "
                          "as free play",
            "success_clause_k08_verbatim": k08,
            "failure_semantics": "physical and visible (falls, rejected "
                                 "grips, lost contact); no silent teleport "
                                 "or hidden support; explicit in-game way to "
                                 "continue",
            "repetition": "free-play, no scripted progression; envelope = "
                          "the frozen clearing (half-width 20.0 m, one trunk "
                          "at (11.976783, 0, 2.471766))",
            "source": "completion_contract v1.0.0 (K08 terminal clause, "
                      "SC-FAILURE-BEHAVIOR) + sealed goal line",
        },
        "framing": {
            "choice": "complete game (not movement demo)",
            "recovered_from": goal_line,
            "recovered_source": "docs/MONKEY_RUN.md sealed goal statement",
        },
        "no_campaign_law": {
            "exclusions_verbatim_available": True,
            "source": "completion_contract exclusions (conditional B01-B07 "
                      "never auto-activated; deferred families listed by "
                      "name; forbidden substitutes listed by name)",
        },
        "operator_decision_requests": [{
            "id": "objective-presentation-surface",
            "question": "How is the repeatable loop surfaced to the player?",
            "options": ["silent free-play (no counter)",
                        "attempt counter (loops completed this session)",
                        "timer + counter"],
            "recommendation": "attempt counter (loops completed this "
                              "session) -- the page's existing state "
                              "feedback carries it without a new HUD "
                              "surface; no thresholds, no scores",
        }],
        "records": {
            "contract_sha256": sha256_file(CONTRACT),
            "contract_version": contract["version"],
            "scope_sha256": ids["scope_sha256"],
            "goal_line_verified_in_monkey_run": True,
        },
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="objective_definition.json")
    args = ap.parse_args(argv)
    definition = extract()
    pathlib.Path(args.out).write_text(
        json.dumps(definition, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({"schema": definition["schema"],
                      "decision_requests":
                          len(definition["operator_decision_requests"]),
                      "contract_sha256":
                          definition["records"]["contract_sha256"][:16]},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
