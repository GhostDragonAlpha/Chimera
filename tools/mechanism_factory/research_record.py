"""research_record.py -- the §11.19 research-loop RECORD LAYER for the
mechanism factory (11.18 adapter/checklist base, extended; GAME_PLAN
"Implementation and acceptance of the recursive loop", lines 2360-2373).

Experimental proposal records, evidence-linked follow-up questions,
method-version comparisons, stops and an explicit exploration allocation,
schema chimera-mechanism-factory-research-record-v1:

    {record_id, kind: proposal|experiment|method_comparison|followup|stop,
     question, parent_evidence_ids[] (must resolve to files under
     docs/evidence/ -- dangling parents are refused by name), alternatives[],
     experiment_identity, result, independent_status (adapter/battery
     verdict reference), cost, applicability, next_questions[],
     budget {allocated, consumed}}

Records are append-only JSON files under
docs/evidence/mechanism_factory/research/. The layer is NOT a side door:

  * a record can write ONLY into the research/ directory (path escape is
    refused); it never modifies any pinned file;
  * any payload field that would represent an acceptance-gate change
    (thresholds, tolerances, packet digest, gate overrides) is refused by
    name -- a record claiming a gate change cannot exist, and the adapter's
    packet_digest_mismatch/verdict_forgery law still binds every receipt;
  * every parent_evidence_id must resolve to a real file under
    docs/evidence/ (dangling linkage is refused);
  * an experiment consumes the exploration budget named by its
    allocation_id; exceeding the allocation is refused budget_exhausted
    until a NEW allocation record exists;
  * a stop record must explicitly declare successful: false.

No new graph commands are invented: graph attachment goes through the
store's existing kinds and the workflow's graph_apply provenance law
(derived_from edges only), separately witnessed. Exit-code law: callers
catch ResearchRefused; this module refuses by name, never by silent drop.

CPU only; stdlib. Owners: import, never edit, the membrane_scale_lab.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent            # tools/mechanism_factory
_REPO = _HERE.parent.parent                       # repo root (PythonChimera)

RESEARCH_RECORD_SCHEMA = "chimera-mechanism-factory-research-record-v1"
RESEARCH_KINDS = ("proposal", "experiment", "method_comparison", "followup",
                  "stop")
REQUIRED_FIELDS = ("record_id", "kind", "question", "parent_evidence_ids")
EVID_ROOT = _REPO / "docs" / "evidence"
RESEARCH_DIR = _REPO / "docs" / "evidence" / "mechanism_factory" / "research"

# THE GATE LAW: a research record is a record, never an acceptance change.
# No payload field anywhere in the record may look like a threshold,
# tolerance, digest or gate override -- those live ONLY in the pinned
# example_packet.json and are enforced by receipt_adapter.py. A record
# claiming a gate change is therefore unrepresentable, and the adapter
# still refuses any receipt that forges one (verdict_forgery /
# packet_digest_mismatch -- reuse, not re-derivation).
FORBIDDEN_KEYS = (
    "acceptance_thresholds", "thresholds", "threshold", "tolerance",
    "tolerances", "packet_sha256", "gate", "gate_n", "override",
    "max_free_residual_n", "max_force_balance_residual",
    "max_moment_balance_residual", "physically_qualified",
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,180}$")


class ResearchRefused(Exception):
    """A named refusal; .reason is the machine-readable name."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%f")[:-3] + "Z"


def _iter_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _iter_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_keys(v)


def _resolve_parent(pid) -> Path:
    """Resolve one parent_evidence_id to a real file under docs/evidence/."""
    if not isinstance(pid, str) or not pid.strip():
        raise ResearchRefused("research_parent_evidence_dangling",
                              f"parent id is not a nonempty string: {pid!r}")
    p = pid.strip()
    if "\\" in p or ":" in p:
        raise ResearchRefused("research_parent_evidence_dangling",
                              f"parent id must be repo-relative or a bare "
                              f"filename: {pid!r}")
    cand = EVID_ROOT / p
    if cand.is_file() and EVID_ROOT in cand.parents:
        return cand
    hits = [h for h in EVID_ROOT.rglob(Path(p).name) if h.is_file()]
    exact = [h for h in hits if h.name == p]
    if exact:
        return exact[0]
    if hits:
        return hits[0]
    raise ResearchRefused(
        "research_parent_evidence_dangling",
        f"parent evidence id {pid!r} resolves to no file under docs/evidence/")


def resolve_parents(parent_ids) -> list:
    if not isinstance(parent_ids, list) or not parent_ids:
        raise ResearchRefused(
            "research_parent_evidence_dangling",
            "parent_evidence_ids must be a nonempty list")
    return [_resolve_parent(p) for p in parent_ids]


def load_records() -> dict:
    """All retained records under research/, keyed by record_id."""
    out = {}
    if not RESEARCH_DIR.is_dir():
        return out
    for f in sorted(RESEARCH_DIR.glob("*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(rec, dict) and isinstance(rec.get("record_id"), str):
            out[rec["record_id"]] = rec
    return out


def _check_budget_law(payload: dict, existing: dict) -> None:
    """An experiment consumes the allocation named by allocation_id; a NEW
    allocation record is the only way to raise capacity."""
    if payload["kind"] != "experiment":
        return
    alloc_id = payload.get("allocation_id")
    if not isinstance(alloc_id, str) or alloc_id not in existing:
        raise ResearchRefused(
            "research_unknown_allocation",
            f"allocation_id {alloc_id!r} names no retained allocation record")
    alloc = existing[alloc_id]
    allocated = (alloc.get("budget") or {}).get("allocated")
    if not isinstance(allocated, (int, float)) or allocated < 0:
        raise ResearchRefused(
            "research_unknown_allocation",
            f"allocation {alloc_id!r} carries no finite budget.allocated")
    consumed_here = (payload.get("budget") or {}).get("consumed")
    if not isinstance(consumed_here, (int, float)) or consumed_here < 0:
        raise ResearchRefused(
            "research_malformed_budget",
            "an experiment needs budget.consumed = its finite cost")
    already = sum(
        ((r.get("budget") or {}).get("consumed") or 0)
        for r in existing.values()
        if r.get("kind") == "experiment" and r.get("allocation_id") == alloc_id)
    if already + consumed_here > allocated:
        raise ResearchRefused(
            "budget_exhausted",
            f"allocation {alloc_id!r}: allocated {allocated}, already "
            f"consumed {already}, requested {consumed_here}; a new "
            f"allocation record is required first")


def write_record(payload: dict) -> Path:
    """Validate ONE record against the schema + laws and append it under
    research/. Returns the written path; refuses by name otherwise."""
    if not isinstance(payload, dict):
        raise ResearchRefused("research_malformed_record", "not an object")
    rec = dict(payload)
    rec.setdefault("schema", RESEARCH_RECORD_SCHEMA)
    if rec["schema"] != RESEARCH_RECORD_SCHEMA:
        raise ResearchRefused(
            "research_unknown_schema",
            f"schema {rec['schema']!r} != {RESEARCH_RECORD_SCHEMA!r}")
    for f in REQUIRED_FIELDS:
        if f not in rec:
            raise ResearchRefused("research_missing_field", f)
    if rec["kind"] not in RESEARCH_KINDS:
        raise ResearchRefused(
            "research_unknown_kind",
            f"{rec['kind']!r} not in {RESEARCH_KINDS}")
    rid = rec["record_id"]
    if not isinstance(rid, str) or not _SAFE_ID.match(rid) or ".." in rid:
        raise ResearchRefused("research_unsafe_record_id", repr(rid))
    for k, _v in _iter_keys(rec):
        if isinstance(k, str) and k.lower() in FORBIDDEN_KEYS:
            raise ResearchRefused(
                "research_gate_override_forbidden",
                f"record field {k!r} would represent an acceptance-law "
                f"change; gates live only in the pinned example_packet.json "
                f"and are enforced by receipt_adapter")
    resolve_parents(rec["parent_evidence_ids"])
    if rec["kind"] == "stop":
        if rec.get("successful") is not False:
            raise ResearchRefused(
                "research_stop_must_declare_failure",
                "a stop record must carry successful: false explicitly")
    existing = load_records()
    if rid in existing:
        raise ResearchRefused("research_record_exists",
                              f"{rid} is already retained (append-only)")
    _check_budget_law(rec, existing)
    rec.setdefault("utc", _utcnow())
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    out = RESEARCH_DIR / f"{rid}.json"
    out.write_text(json.dumps(rec, indent=1, default=str) + "\n",
                   encoding="utf-8")
    return out


def allocation_summary() -> dict:
    """For every allocation record: allocated, consumed by its experiments,
    remaining."""
    recs = load_records()
    out = {}
    for rid, r in recs.items():
        allocated = (r.get("budget") or {}).get("allocated")
        if not isinstance(allocated, (int, float)):
            continue
        consumed = sum(((x.get("budget") or {}).get("consumed") or 0)
                       for x in recs.values()
                       if x.get("kind") == "experiment"
                       and x.get("allocation_id") == rid)
        out[rid] = {"allocated": allocated, "consumed": consumed,
                    "remaining": allocated - consumed}
    return out
