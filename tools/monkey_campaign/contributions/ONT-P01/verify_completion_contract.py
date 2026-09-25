#!/usr/bin/env python3
"""Executable identity oracle for the frozen playable-monkey completion contract.

Verifies that every identity recorded in completion_contract.json can be recomputed
from the actual campaign records (completion map, scope lock, ontology definition,
scope amendments). The hash algorithm mirrors tools/monkey_campaign/integrity.py
semantics (sha256-chimera-json-v1); it is reimplemented here self-contained because
the contribution checkout is sparse and does not carry the campaign package.

Refuses with named failures; never mutates any record. Exit 0 = all checks pass.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ALGORITHM = "sha256-chimera-json-v1"


class Refusal(Exception):
    """Named, machine-checkable refusal."""


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Refusal("duplicate_json_key:" + key)
        out[key] = value
    return out


def _reject_constant(value):
    raise Refusal("nonfinite_json_number:" + str(value))


def strict_load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"),
                          object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
    except Refusal:
        raise
    except (OSError, ValueError) as exc:
        raise Refusal(f"unreadable_or_invalid_json:{path}:{exc}") from exc


def content_digest(data) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def raw_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise Refusal(f"unreadable_file:{path}:{exc}") from exc


def verify(contract_path: Path, map_path: Path, lock_path: Path,
           ontology_path: Path, expected_scope_sha: str = None,
           verify_amendments: bool = True) -> dict:
    """Run every probe; raise Refusal on the first failure; return a check log."""
    contract = strict_load(contract_path)
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL",
                       "detail": detail})
        if not ok:
            raise Refusal(f"{name}:{detail}")

    ids = contract.get("identities")
    if not isinstance(ids, dict):
        raise Refusal("contract_missing_identities")
    if contract.get("schema") != "chimera.completion_contract.v1":
        raise Refusal("unsupported_contract_schema:" + str(contract.get("schema")))
    if contract.get("status") != "FROZEN":
        raise Refusal("contract_not_frozen:" + str(contract.get("status")))

    # P-1: scope content digest of the map vs contract, lock record and human pin.
    catalog = strict_load(map_path)
    actual_scope = content_digest(catalog)
    check("P1a_scope_digest_matches_contract",
          actual_scope == ids.get("scope_sha256"),
          f"actual={actual_scope} contract={ids.get('scope_sha256')}")
    lock = strict_load(lock_path)
    if lock.get("algorithm") != ALGORITHM:
        raise Refusal("unsupported_integrity_algorithm:" + str(lock.get("algorithm")))
    check("P1b_scope_digest_matches_lock",
          lock.get("scope_sha256") == actual_scope,
          f"lock={lock.get('scope_sha256')} actual={actual_scope}")
    pin = expected_scope_sha or ids.get("scope_sha256")
    if pin != actual_scope:
        raise Refusal(f"P1c_trust_anchor_mismatch:pin={pin} actual={actual_scope}")
    checks.append({"check": "P1c_trust_anchor", "result": "PASS", "detail": pin})

    # P-2: lock raw_file_sha256 binds the exact map bytes.
    map_raw = raw_sha256(map_path)
    check("P2a_map_raw_sha_matches_contract",
          map_raw == ids.get("map_raw_sha256"),
          f"actual={map_raw} contract={ids.get('map_raw_sha256')}")
    check("P2b_map_raw_sha_matches_lock",
          map_raw == lock.get("raw_file_sha256"),
          f"lock={lock.get('raw_file_sha256')} actual={map_raw}")
    lock_raw = raw_sha256(lock_path)
    check("P2c_lock_raw_sha_matches_contract",
          lock_raw == ids.get("lock_raw_sha256"),
          f"actual={lock_raw} contract={ids.get('lock_raw_sha256')}")

    # P-3: ontology definition raw sha agrees across contract, bytes and map record.
    onto_raw = raw_sha256(ontology_path)
    check("P3a_ontology_raw_sha",
          onto_raw == ids.get("ontology_definition_raw_sha256"),
          f"actual={onto_raw} contract={ids.get('ontology_definition_raw_sha256')}")
    onto_record = catalog.get("ontology_contract", {}).get("definition_raw_sha256")
    check("P3b_map_ontology_sha_agrees", onto_record == onto_raw,
          f"map={onto_record} actual={onto_raw}")

    # P-4: task inventory.
    tasks = catalog.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise Refusal("P4_map_has_no_tasks")
    by_id = {}
    for task in tasks:
        tid = task.get("id")
        if not tid or tid in by_id:
            raise Refusal(f"P4_duplicate_or_missing_task_id:{tid}")
        by_id[tid] = task
    check("P4a_task_count",
          len(tasks) == ids.get("task_count") == lock.get("task_count"),
          f"map={len(tasks)} contract={ids.get('task_count')} lock={lock.get('task_count')}")
    conditional = sorted(t["id"] for t in tasks if t.get("scope") == "conditional")
    want_cond = sorted(ids.get("conditional_ids") or [])
    check("P4b_conditional_set", conditional == want_cond,
          f"map={conditional} contract={want_cond}")
    selected_count = sum(1 for t in tasks if t.get("scope") != "conditional")
    check("P4c_selected_count",
          selected_count == ids.get("selected_count"),
          f"actual={selected_count} contract={ids.get('selected_count')}")
    empty = [t["id"] for t in tasks if not str(t.get("done_when", "")).strip()]
    check("P4d_done_when_nonempty", not empty, f"empty={empty}")
    calc_count = len(catalog.get("calculations", []))
    check("P4e_calculation_count",
          calc_count == ids.get("calculation_contract_count"),
          f"actual={calc_count} contract={ids.get('calculation_contract_count')}")

    # P-4f/P-4g: terminal clauses verbatim; evidence-bound tasks exist and are selected.
    for condition in contract.get("success_conditions", []):
        for tid, quote in (condition.get("terminal_done_when_verbatim") or {}).items():
            actual = str(by_id.get(tid, {}).get("done_when", ""))
            check(f"P4f_terminal_verbatim_{tid}", actual == quote,
                  f"map={actual!r} contract={quote!r}")
        for tid in condition.get("evidence_bound_tasks", []):
            if tid not in by_id:
                raise Refusal(f"P4g_evidence_task_not_in_map:{tid}")
            if by_id[tid].get("scope") == "conditional":
                raise Refusal(f"P4g_evidence_task_is_conditional:{tid}")

    # P-4h: excluded deferred families quote actual later_backlog titles.
    backlog_titles = [f.get("title") for f in catalog.get("later_backlog", [])]
    contract_families = contract.get("exclusions", {}).get("deferred_families", [])
    missing = [f for f in contract_families if f not in backlog_titles]
    check("P4h_deferred_families_exist_in_map", not missing, f"missing={missing}")

    # P-4i: amendment chain continuity; raw hashes recomputed when files are present.
    chain = ids.get("amendment_chain") or []
    if not chain or chain[-1] != ids.get("scope_sha256"):
        raise Refusal("P4i_amendment_chain_does_not_end_at_pin")
    if len(set(chain)) != len(chain):
        raise Refusal("P4i_amendment_chain_repeats_digest")
    amendments = ids.get("amendments", [])
    if len(amendments) != len(chain) - 1:
        raise Refusal(
            f"P4i_amendment_count_mismatch:chain={len(chain)} "
            f"amendments={len(amendments)}")
    for index, amendment in enumerate(amendments):
        if amendment.get("previous_scope_sha256") != chain[index]:
            raise Refusal(f"P4i_amendment_chain_broken:{amendment.get('path')}")
        if amendment.get("resulting_scope_sha256") != chain[index + 1]:
            raise Refusal(
                f"P4i_amendment_result_not_in_chain:{amendment.get('path')}")
    if verify_amendments:
        for amendment in amendments:
            amendment_path = map_path.parent / Path(amendment["path"]).name
            actual = raw_sha256(amendment_path)
            check(f"P4i_amendment_raw_sha:{amendment['path']}",
                  actual == amendment.get("raw_sha256"),
                  f"actual={actual} contract={amendment.get('raw_sha256')}")

    # P-6a: forbidden-substitution clauses present (their authority lives in the map).
    forbidden = contract.get("exclusions", {}).get("forbidden_substitutes", [])
    check("P6a_forbidden_substitutes_nonempty", bool(forbidden), "list_empty")

    return {"algorithm": ALGORITHM,
            "scope_sha256": actual_scope,
            "task_count": len(tasks),
            "selected_count": selected_count,
            "conditional_ids": conditional,
            "checks": checks,
            "outcome": "PASS"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    parser.add_argument("--contract", type=Path,
                        default=here / "completion_contract.json")
    parser.add_argument("--map", dest="map_path", type=Path,
                        default=here.parent.parent / "monkey_completion_map.json")
    parser.add_argument("--lock", type=Path,
                        default=here.parent.parent / "APPROVED_SCOPE.json")
    parser.add_argument("--ontology", type=Path,
                        default=here.parent.parent.parent
                        / "membrane_ontology" / "ontology.json")
    parser.add_argument("--expected-scope", default=None,
                        help="Human-pinned digest override; defaults to the contract record")
    parser.add_argument("--no-amendment-files", action="store_true",
                        help="Skip recomputing amendment raw hashes from disk")
    args = parser.parse_args(argv)
    try:
        result = verify(args.contract, args.map_path, args.lock, args.ontology,
                        args.expected_scope, verify_amendments=not args.no_amendment_files)
    except Refusal as refusal:
        print(json.dumps({"outcome": "REFUSED", "refusal": str(refusal)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
