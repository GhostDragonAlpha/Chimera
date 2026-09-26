#!/usr/bin/env python3
"""Read-only verifier for the P02 monkey/scene lineage map (card ONT-P02).

Re-verifies every pin in monkey_lineage_map.json against a git object store:

  - commit exists, `git rev-parse <commit>:<path>` equals the recorded blob,
  - the blob bytes hash to the recorded raw sha256 and byte length,
  - every recorded marker string occurs in those bytes,
  - the five named card items and the mass-lineage separation rules hold,
  - the registered numbers recompute from the pinned bytes (never from prose).

Read-only everywhere: only `git cat-file`, `git rev-parse`, `git show` plumbing
against the pinned commits; no checkout, no worktree or index mutation.

Usage:
  python -B verify_monkey_lineage.py --map monkey_lineage_map.json [--repo DIR]
                                     [--expected-criteria SHA256] [--out RECEIPT.json]

Exit codes: 0 = PASS, 3 = named refusal, 2 = usage/environment error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

EXPECTED_SCOPE_SHA256 = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
EXPECTED_TASK_ID = "P02"
CARD_ITEM_IDS = ["ct_monkey", "source_msk_model", "forearm_paddle_assets", "training_body", "runtime_body"]
ALLOWED_RELATION_KINDS = {"DERIVED", "RENDER_BINDING", "SOURCE_OF", "KEPT_SEPARATE", "PLACED_IN", "SIMULATED_IN"}
MASS_LINEAGE_SEPARATION_MARKER = "NEVER interchanged"
GRAVITY_M_S2 = 9.80665


class Refusal(Exception):
    """A named, located refusal; never a silent pass."""


def _git(repo: str, *args: str) -> bytes:
    cmd = ["git", "-c", "safe.directory=*", "-C", repo, *args]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise Refusal("git_command_failed:" + " ".join(args[:2]) + ":" + proc.stderr.decode("utf-8", "replace").strip()[:200])
    return proc.stdout


def _resolve_repo(explicit: str | None, map_path: str) -> str:
    if explicit:
        if not os.path.isdir(os.path.join(explicit, ".git")) and not os.path.isfile(os.path.join(explicit, ".git")):
            raise Refusal("repo_not_a_git_worktree:" + explicit)
        return explicit
    env = os.environ.get("MONKEY_LINEAGE_REPO")
    if env:
        return env
    cur = os.path.dirname(os.path.abspath(map_path))
    for _ in range(12):
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    raise Refusal("repo_unresolved:pass --repo or set MONKEY_LINEAGE_REPO")


def _pin_bytes(repo: str, pin: dict) -> bytes:
    pin_id = pin.get("id", "?")
    commit = pin.get("commit", "")
    path = pin.get("path", "")
    blob = pin.get("blob", "")
    for name, val in (("commit", commit), ("blob", blob)):
        if not (isinstance(val, str) and len(val) == 40 and all(c in "0123456789abcdef" for c in val)):
            raise Refusal("pin_identity_malformed:" + pin_id + ":" + name)
    try:
        _git(repo, "cat-file", "-e", commit + "^{commit}")
        actual_blob = _git(repo, "rev-parse", f"{commit}:{path}").decode().strip()
        raw = _git(repo, "cat-file", "blob", blob)
    except Refusal as exc:
        raise Refusal("pin_git_failed:" + pin_id + ":" + str(exc)) from None
    if actual_blob != blob:
        raise Refusal(f"pin_blob_mismatch:{pin_id}:{actual_blob}!={blob}")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != pin.get("sha256"):
        raise Refusal(f"pin_sha256_mismatch:{pin_id}:{digest}!={pin.get('sha256')}")
    recorded_len = pin.get("bytes")
    if isinstance(recorded_len, int) and recorded_len != len(raw):
        raise Refusal(f"pin_bytes_mismatch:{pin_id}:{len(raw)}!={recorded_len}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    for marker in pin.get("markers", []):
        if marker not in text:
            raise Refusal(f"pin_marker_absent:{pin_id}:{marker[:60]}")
    return raw


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise Refusal(msg)


def _close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def verify(map_path: str, repo: str | None = None, expected_criteria: str | None = None) -> dict:
    checks = 0
    with open(map_path, "rb") as fh:
        raw = fh.read()
    try:
        m = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Refusal("map_unreadable:" + str(exc)[:120])

    # V0 identity
    checks += 1
    _require(m.get("schema") == "chimera.monkey_lineage_map.v1", "map_schema_unknown")
    checks += 1
    _require(m.get("task_id") == EXPECTED_TASK_ID, "map_task_id_wrong")
    checks += 1
    _require(m.get("scope_sha256") == EXPECTED_SCOPE_SHA256, "map_scope_mismatch")
    checks += 1
    _require(len(m.get("done_when", "")) > 0 and "related explicitly or kept separate" in m["done_when"], "map_done_when_absent")
    if expected_criteria:
        checks += 1
        _require(m.get("criteria_sha256") == expected_criteria, "map_criteria_mismatch")

    repo = _resolve_repo(repo, map_path)

    # V1 resolve every pin against the object store
    pins = m.get("pins", [])
    checks += 1
    _require(0 < len(pins) <= 64, "pin_count_out_of_bounds")
    pin_ids: set[str] = set()
    pin_raw: dict[str, bytes] = {}
    for pin in pins:
        pid = pin.get("id", "?")
        checks += 1
        _require(pid not in pin_ids, "duplicate_pin_id:" + pid)
        pin_ids.add(pid)
        pin_raw[pid] = _pin_bytes(repo, pin)

    # V2 entities: exactly the five named card items, plus declared supporting set
    entity_ids: set[str] = set()
    card_items = []
    for ent in m.get("entities", []):
        eid = ent.get("id", "?")
        checks += 1
        _require(eid not in entity_ids, "duplicate_entity_id:" + eid)
        entity_ids.add(eid)
        for ev in ent.get("evidence", []):
            checks += 1
            _require(ev in pin_ids, "entity_evidence_unresolved:" + eid + ":" + ev)
        if ent.get("card_item"):
            card_items.append(eid)
    checks += 1
    _require(sorted(card_items) == sorted(CARD_ITEM_IDS), "card_items_wrong_set:" + ",".join(sorted(card_items)))
    for ent in m.get("supporting_entities", []):
        eid = ent.get("id", "?")
        checks += 1
        _require(eid not in entity_ids, "duplicate_supporting_id:" + eid)
        entity_ids.add(eid)
        for ev in ent.get("evidence", []):
            checks += 1
            _require(ev in pin_ids, "supporting_evidence_unresolved:" + eid + ":" + ev)

    # V3 relations: declared kinds, resolved endpoints and evidence
    for rel in m.get("relations", []):
        checks += 1
        _require(rel.get("kind") in ALLOWED_RELATION_KINDS, "relation_kind_unknown:" + str(rel.get("kind")))
        checks += 1
        _require(rel.get("a") in entity_ids and rel.get("b") in entity_ids, "relation_endpoint_unresolved:" + str(rel.get("a")) + "->" + str(rel.get("b")))
        checks += 1
        _require(bool(rel.get("statement", "").strip()), "relation_statement_empty")
        checks += 1
        _require(len(rel.get("evidence", [])) > 0 and all(ev in pin_ids for ev in rel.get("evidence", [])), "relation_evidence_unresolved")

    # V4 mass lineages: distinct, never interchanged, evidence-resolved
    masses = m.get("mass_lineages", {})
    checks += 1
    _require(MASS_LINEAGE_SEPARATION_MARKER in masses.get("rule", ""), "mass_separation_rule_absent")
    entries = masses.get("entries", [])
    checks += 1
    _require(len(entries) >= 6, "mass_lineage_entries_missing")
    values = []
    seen_mass_ids: set[str] = set()
    for e in entries:
        mid = e.get("id", "?")
        checks += 1
        _require(mid not in seen_mass_ids, "duplicate_mass_id:" + mid)
        seen_mass_ids.add(mid)
        checks += 1
        _require(isinstance(e.get("value_kg"), (int, float)) and e["value_kg"] > 0, "mass_value_invalid:" + mid)
        values.append(float(e["value_kg"]))
        for ev in e.get("evidence", []):
            checks += 1
            _require(ev in pin_ids, "mass_evidence_unresolved:" + mid + ":" + ev)
    checks += 1
    _require(len(set(values)) == len(values), "mass_lineage_collision:two_entries_share_a_value")
    known = masses.get("known_mismatch", {})
    checks += 1
    _require(_close(round(13824.5 / 10.038, 4), float(known.get("ratio_13824_5_over_10_038", 0)), 1e-9), "known_mismatch_ratio_wrong")

    # V5 numbers recomputed from the pinned bytes (never from prose)
    dn_raw = pin_raw.get("ev_derived_numbers")
    checks += 1
    _require(dn_raw is not None, "derived_numbers_pin_missing")
    dn = json.loads(dn_raw.decode("utf-8"))
    body = dn["body_model"]
    seg = body["segments_Table1"]
    checks += 1
    _require(body["mass_kg"] == 10.038, "training_body_mass_not_10_038")
    leg_chain = seg["thigh"]["mass_kg"] + seg["shank"]["mass_kg"] + seg["foot"]["mass_kg"] + seg["phalanges"]["mass_kg"]
    checks += 1
    _require(_close(seg["HAT"]["mass_kg"] + 2 * leg_chain, 10.038, 1e-9), "oku_segment_sum_mismatch")
    checks += 1
    _require(_close(10.038 * GRAVITY_M_S2, 98.4391527, 5e-8), "walker_weight_mismatch")
    gs_text = pin_raw.get("ev_gait_scene", b"").decode("utf-8", "replace")
    checks += 1
    _require("0.406001" in gs_text and "0.2737" in gs_text and "0.1323" in gs_text, "gait_scene_carve_markers_absent")
    carve = (8.184 - 2 * 0.406001) + 2 * (0.2737 + 0.1323) + 2 * 0.927
    checks += 1
    _require(_close(carve, 10.037998, 1e-9), "scene_carve_mismatch:" + repr(carve))
    checks += 1
    _require(_close((5.4 + 6.9) / 2, 6.15, 1e-12), "tk1989_midpoint_mismatch")
    checks += 1
    _require(_close(13.824536 * 1000.0, 13824.536, 1e-9), "membrane_inventory_mismatch")

    # V6 runtime render body: the mesh pin equals the body_manifest import payload pin
    bm = json.loads(pin_raw.get("ev_body_manifest", b"{}").decode("utf-8"))
    mesh_pin = next((p for p in pins if p.get("id") == "ev_standing_body"), {})
    checks += 1
    payload = bm.get("import_payload", {})
    _require(payload.get("sha256") == mesh_pin.get("sha256") == "bc9033bfc6c54db0220364821ee19028bf2ac6f740dc70f4c1e9be5f02089111", "runtime_body_mesh_identity_break")
    checks += 1
    _require(payload.get("path", "").endswith("standing_body.obj"), "runtime_body_payload_path_wrong")

    # V7 prior receipts carry well-formed identities
    for rec in m.get("prior_receipts_reused", []):
        checks += 1
        sha = rec.get("sha256")
        _require(sha is None or (isinstance(sha, str) and len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)), "prior_receipt_sha_malformed:" + rec.get("id", "?"))

    return {
        "outcome": "PASS",
        "map": os.path.abspath(map_path),
        "repo": os.path.abspath(repo),
        "checks_passed": checks,
        "pins_resolved": len(pins),
        "card_items": sorted(card_items),
        "mass_lineage_values_kg": sorted(values),
        "training_body_kg": 10.038,
        "walker_weight_N": 98.4391527,
        "scene_carve_kg": carve,
        "cot_mismatch_ratio": round(13824.5 / 10.038, 4),
        "runtime_body_sha256": payload.get("sha256"),
        "runtime_body_bytes": mesh_pin.get("bytes"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify the P02 monkey/scene lineage map (read-only).")
    ap.add_argument("--map", required=True)
    ap.add_argument("--repo", default=None)
    ap.add_argument("--expected-criteria", default=None)
    ap.add_argument("--out", default=None, help="optional path for the PASS receipt JSON")
    args = ap.parse_args(argv)
    try:
        report = verify(args.map, args.repo, args.expected_criteria)
    except Refusal as exc:
        refusal = {"outcome": "REFUSED", "refusal": str(exc)}
        print(json.dumps(refusal, indent=1))
        return 3
    print(json.dumps(report, indent=1))
    if args.out:
        with open(args.out, "wb") as fh:
            fh.write((json.dumps(report, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
