"""The COMPATIBILITY CERTIFICATE: schema, issuer, validator, deploy gate.

The relation of record (Astra round 5, prereg
tools/science_funnel/validation/upgrade_gate_20260920/receipt.json):

    (policy bundle, physics build, runtime profile, body/domain, test suite)
        -> certificate

compat_key  = sha256 over the canonical JSON of the 5-tuple (the relation key a
              deployment request must present).
cert_hash   = sha256 over the canonical JSON of the certificate with the
              cert_hash field itself excluded (the P3 manifest-hash convention).

Four bundle parts (prereg "certificate_format_declared"):
  (a) execution identity   -- artifact shas, timestep, graph/weights sha,
                              adapters + normalization, runtime,
                              compiler/hardware/driver settings as available
  (b) restart-state inventory -- the complete 8-item inventory; items not yet
                              snapshotable are REGISTERED GAPS, named, with
                              cause and clearing check; PRODUCTION-class
                              certificates require zero unresolved gaps
  (c) replay evidence      -- initial snapshot sha, tick-ordered events in a
                              HASH CHAIN (each event carries the running chain
                              sha), periodic state hashes, monitor outputs
  (d) qualification scope  -- bodies/skills/transitions/ranges/horizons/bars +
                              non-regression margins, each margin REQUIRING a
                              derivation string (a margin without a derivation
                              is a schema violation: Rule 1)

The validator is the ONLY authority: a certificate carries no self-status; its
validity is recomputed from its bytes every time. Deployment check: missing
certificate -> BLOCK; any validator violation -> BLOCK (invalidated);
compat_key mismatch -> BLOCK; otherwise ALLOW.
"""
from __future__ import annotations

import copy
import hashlib
import json

from . import SCHEMA_VERSION

DEPLOYMENT_CLASSES = ("surrogate", "evaluation", "production")

# The 5-tuple relation components (part (a) is their content).
RELATION_KEYS = ("policy_bundle", "physics_build", "runtime_profile",
                 "body_domain", "test_suite")

# The complete restart-state inventory (part (b)); prereg "restart_state_inventory_declared".
INVENTORY_ITEMS = (
    "body_state",
    "contact_warm_start_cache",
    "reflex_state",
    "held_command",
    "decision_phase",
    "controller_history",
    "rng_stream",
    "world_state",
)

REQUIRED_SCOPE_BARS = (
    "bounds_honored",       # every applied command within the manifest limiter bounds
    "no_nan_inf",           # no NaN/Inf in any recorded state quantity
    "no_intervention",      # intervention_reason == "none" at every tick
    "contact_floor",        # contact_count >= 2 at every tick
    "availability_exact",   # available_groups exactly as the scope declares
    "velocity_envelope",    # |v_t| <= v_max at every tick (the drive fixed-point bound)
)


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def compat_key(components: dict) -> str:
    """sha256 over the canonical JSON of exactly the 5-tuple components."""
    tup = {k: components[k] for k in RELATION_KEYS}
    return sha256_hex(canonical_json(tup))


def cert_hash(cert: dict) -> str:
    m = copy.deepcopy(cert)
    m.pop("cert_hash", None)
    return sha256_hex(canonical_json(m))


# ---------------------------------------------------------------- issuance

def issue_certificate(relation: dict, inventory: dict, evidence: dict,
                      scope: dict, meta: dict) -> dict:
    """Assemble a certificate from the four bundle parts + the 5-tuple relation.

    relation: the 5 RELATION_KEYS -> component dicts (content hashes).
    inventory: {"items": [{name, snapshotable, snapshot_key, contents}...],
                "registered_gaps": [{name, item, status, cause, clears_when}],
                "deployment_class": one of DEPLOYMENT_CLASSES}
    evidence: {"initial_snapshot_sha256", "events": [{tick, kind, state_sha256,
                chain_sha256}...], "periodic_stride", "final_state_sha256",
                "monitors": [{name, pass, detail_sha256}...],
                "trajectory_sha256"}
    scope: {"bodies", "skills", "transitions", "ranges", "horizons", "bars",
            "non_regression_margins": [{name, quantity, bound, derivation}]}
    meta: {"issued_by", "lane", "base_commit", "prereg_receipt",
           "prereg_rule0_sha"}
    """
    missing = [k for k in RELATION_KEYS if k not in relation]
    if missing:
        raise ValueError(f"relation missing components: {missing}")
    cert = {
        "schema_version": SCHEMA_VERSION,
        "kind": "policy_compat_certificate",
        "cert_version": 1,
        "compat_key": compat_key(relation),
        "relation": {k: relation[k] for k in RELATION_KEYS},
        "execution_identity": dict(relation),  # part (a): the relation IS the identity
        "restart_state_inventory": inventory,  # part (b)
        "replay_evidence": evidence,           # part (c)
        "qualification_scope": scope,          # part (d)
        "issued_by": meta["issued_by"],
        "lane": meta["lane"],
        "base_commit": meta["base_commit"],
        "prereg_receipt": meta["prereg_receipt"],
        "prereg_rule0_sha": meta["prereg_rule0_sha"],
    }
    cert["cert_hash"] = cert_hash(cert)
    return cert


# --------------------------------------------------------------- validation

def _validate_inventory(inv: dict, errs: list[str]) -> None:
    if not isinstance(inv, dict):
        errs.append("restart_state_inventory must be an object")
        return
    cls = inv.get("deployment_class")
    if cls not in DEPLOYMENT_CLASSES:
        errs.append(f"deployment_class must be one of {DEPLOYMENT_CLASSES}")
    items = inv.get("items")
    if not isinstance(items, list):
        errs.append("restart_state_inventory.items must be a list")
        return
    by_name = {}
    for it in items:
        if not isinstance(it, dict) or not {"name", "snapshotable", "contents"} <= set(it):
            errs.append("inventory item must carry name/snapshotable/contents")
            continue
        by_name[it["name"]] = it
        if not isinstance(it["snapshotable"], bool):
            errs.append(f"inventory item {it['name']}: snapshotable must be bool")
    for name in INVENTORY_ITEMS:
        if name not in by_name:
            errs.append(f"restart-state inventory INCOMPLETE: missing item {name} "
                        f"(the inventory is complete or the certificate is invalid)")
    gaps = inv.get("registered_gaps")
    if not isinstance(gaps, list):
        errs.append("registered_gaps must be a list (possibly empty)")
        return
    for g in gaps:
        if not {"name", "item", "status", "cause", "clears_when"} <= set(g):
            errs.append(f"registered gap must carry name/item/status/cause/clears_when: {g!r}")
        elif g["item"] not in INVENTORY_ITEMS:
            errs.append(f"registered gap {g['name']} names unknown item {g['item']}")
    if cls == "production":
        unresolved = [g["name"] for g in gaps if "RESOLVED" not in str(g.get("status", "")).upper()]
        if unresolved:
            errs.append(
                "PRODUCTION certificate with UNRESOLVED registered gaps: "
                + ", ".join(unresolved)
                + " -- deployment BLOCKED until the engine binding clears each gap")
        non_snap = [n for n, it in by_name.items() if it.get("snapshotable") is False]
        if non_snap:
            errs.append(f"PRODUCTION certificate with non-snapshotable items: {non_snap}")


def verify_evidence_chain(evidence: dict) -> tuple[bool, str]:
    """Recompute the hash chain: chain_0 = sha256('chain0:' + initial snapshot
    sha), then each event's chain_sha256 = sha256(prev_chain + ':' + tick + ':'
    + kind + ':' + state_sha256). Any mismatch invalidates the certificate.
    (The issuer's convention -- runner.run_closed_loop -- seeds chain0 exactly
    this way; the verifier recomputes from the pinned initial snapshot.)"""
    initial = evidence.get("initial_snapshot_sha256")
    if not initial:
        return False, "evidence missing initial_snapshot_sha256"
    prev = sha256_hex(f"chain0:{initial}".encode("utf-8"))
    for ev in evidence.get("events", []):
        want = sha256_hex(f"{prev}:{ev['tick']}:{ev['kind']}:{ev['state_sha256']}".encode("utf-8"))
        if want != ev["chain_sha256"]:
            return False, (f"evidence chain mismatch at tick {ev['tick']}: recorded "
                           f"{ev['chain_sha256'][:16]}... != recomputed {want[:16]}...")
        prev = ev["chain_sha256"]
    if not evidence.get("final_state_sha256"):
        return False, "evidence missing final_state_sha256"
    return True, "chain verifies"


def _validate_evidence(ev: dict, errs: list[str]) -> None:
    if not isinstance(ev, dict):
        errs.append("replay_evidence must be an object")
        return
    missing = [k for k in ("initial_snapshot_sha256", "events", "periodic_stride",
                           "final_state_sha256", "monitors", "trajectory_sha256")
               if k not in ev]
    for k in missing:
        errs.append(f"replay_evidence missing: {k}")
    if missing:
        return
    ok, detail = verify_evidence_chain(ev)
    if not ok:
        errs.append(f"replay evidence INVALIDATED: {detail}")
    if not isinstance(ev["events"], list) or not ev["events"]:
        errs.append("replay_evidence.events must be a non-empty tick-ordered list")
    else:
        ticks = [e.get("tick", -1) for e in ev["events"]]
        if ticks != sorted(ticks):
            errs.append("replay_evidence.events are not tick-ordered")
    mons = ev["monitors"]
    if not isinstance(mons, list) or not mons:
        errs.append("replay_evidence.monitors must be a non-empty list")
    else:
        for m in mons:
            if not {"name", "pass", "detail_sha256"} <= set(m):
                errs.append(f"monitor must carry name/pass/detail_sha256: {m!r}")
            elif m["pass"] is not True:
                errs.append(f"monitor {m['name']} did not pass -- certificate invalid")


def _validate_scope(scope: dict, errs: list[str]) -> None:
    if not isinstance(scope, dict):
        errs.append("qualification_scope must be an object")
        return
    missing = [k for k in ("bodies", "skills", "transitions", "ranges", "horizons",
                           "bars", "non_regression_margins") if k not in scope]
    for k in missing:
        errs.append(f"qualification_scope missing: {k}")
    if missing:
        return
    missing_bars = [b for b in REQUIRED_SCOPE_BARS if b not in scope["bars"]]
    if missing_bars:
        errs.append(f"qualification_scope.bars missing required bars: {missing_bars}")
    margins = scope["non_regression_margins"]
    if not isinstance(margins, list) or not margins:
        errs.append("non_regression_margins must be a non-empty list "
                    "(a scope without margins is not a qualification)")
    for m in margins or []:
        if not {"name", "quantity", "bound", "derivation"} <= set(m):
            errs.append(f"margin must carry name/quantity/bound/derivation: {m!r}")
        elif not str(m.get("derivation", "")).strip():
            errs.append(f"margin {m.get('name')}: DERIVATION REQUIRED (Rule 1: "
                        f"a number without a derivation is taste, not a margin)")


def validate_certificate(cert: dict) -> list[str]:
    """Return the list of violations; EMPTY == valid. The only authority."""
    errs: list[str] = []
    if not isinstance(cert, dict):
        return ["certificate must be a JSON object"]
    if cert.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"schema_version != {SCHEMA_VERSION} (unknown format -> BLOCK)")
    if cert.get("kind") != "policy_compat_certificate":
        errs.append("kind != policy_compat_certificate")
    for part in ("compat_key", "relation", "execution_identity",
                 "restart_state_inventory", "replay_evidence",
                 "qualification_scope"):
        if part not in cert:
            errs.append(f"missing certificate part: {part}")
    if errs:
        return errs
    if set(cert["relation"].keys()) != set(RELATION_KEYS):
        errs.append(f"relation must carry exactly {list(RELATION_KEYS)}")
    else:
        if cert["compat_key"] != compat_key(cert["relation"]):
            errs.append("compat_key does not match the relation -- the 5-tuple "
                        "and its key disagree")
    _validate_inventory(cert["restart_state_inventory"], errs)
    _validate_evidence(cert["replay_evidence"], errs)
    _validate_scope(cert["qualification_scope"], errs)
    for k in ("issued_by", "lane", "base_commit", "prereg_receipt", "prereg_rule0_sha"):
        if not cert.get(k):
            errs.append(f"certificate missing provenance: {k}")
    recorded = cert.get("cert_hash")
    if not recorded:
        errs.append("missing cert_hash")
    elif recorded != cert_hash(cert):
        errs.append(f"cert_hash mismatch: recorded {str(recorded)[:16]}... != "
                    f"recomputed {cert_hash(cert)[:16]}... -- the certificate bytes "
                    f"were altered after issuance")
    return errs


# ------------------------------------------------------------- deploy gate

def check_deploy(request: dict, certificate: dict | None) -> dict:
    """The deployment gate. ANY block reason is a hard BLOCK; missing or
    invalidated certificate can never deploy (the Astra round-5 decision)."""
    reasons: list[str] = []
    if certificate is None:
        reasons.append("BLOCKED: no compatibility certificate -- deployment "
                       "without a certificate is forbidden (missing cert)")
    else:
        errs = validate_certificate(certificate)
        if errs:
            reasons.append("BLOCKED: invalidated certificate: " + "; ".join(errs))
        else:
            want = compat_key({k: request[k] for k in RELATION_KEYS
                               if k in request})
            have = set(RELATION_KEYS) - set(request)
            if have:
                reasons.append(f"BLOCKED: deployment request missing relation "
                               f"components: {sorted(have)}")
            elif want != certificate["compat_key"]:
                reasons.append(
                    "BLOCKED: compatibility key mismatch -- the request's 5-tuple "
                    f"({want[:16]}...) is NOT the certificate's ({certificate['compat_key'][:16]}...); "
                    "the bundle/build/runtime/body/suite is not the certified one")
    decision = "BLOCK" if reasons else "ALLOW"
    return {"decision": decision, "reasons": reasons,
            "compat_key": compat_key(request) if set(RELATION_KEYS) <= set(request) else None,
            "certificate_sha256": sha256_hex(canonical_json(certificate)) if certificate else None}


# ------------------------------------------------------------ JSON schema

def json_schema() -> dict:
    """A draft-2020-12 schema for the certificate format (documentation and
    external validation; validate_certificate remains the authority)."""
    item_schema = {
        "type": "object",
        "required": ["name", "snapshotable", "contents"],
        "properties": {
            "name": {"type": "string", "enum": list(INVENTORY_ITEMS)},
            "snapshotable": {"type": "boolean"},
            "snapshot_key": {"type": "string"},
            "contents": {"type": "string"},
        },
    }
    gap_schema = {
        "type": "object",
        "required": ["name", "item", "status", "cause", "clears_when"],
        "properties": {
            "name": {"type": "string"},
            "item": {"type": "string", "enum": list(INVENTORY_ITEMS)},
            "status": {"type": "string"},
            "cause": {"type": "string"},
            "clears_when": {"type": "string"},
        },
    }
    event_schema = {
        "type": "object",
        "required": ["tick", "kind", "state_sha256", "chain_sha256"],
        "properties": {
            "tick": {"type": "integer", "minimum": 0},
            "kind": {"type": "string"},
            "state_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "chain_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }
    margin_schema = {
        "type": "object",
        "required": ["name", "quantity", "bound", "derivation"],
        "properties": {
            "name": {"type": "string"},
            "quantity": {"type": "string"},
            "bound": {"type": ["number", "string"]},
            "derivation": {"type": "string", "minLength": 1},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "chimera:policy_compat:certificate:1.0.0",
        "title": "Chimera policy compatibility certificate",
        "type": "object",
        "required": ["schema_version", "kind", "cert_version", "compat_key",
                     "relation", "execution_identity", "restart_state_inventory",
                     "replay_evidence", "qualification_scope", "issued_by",
                     "lane", "base_commit", "prereg_receipt", "prereg_rule0_sha",
                     "cert_hash"],
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "kind": {"const": "policy_compat_certificate"},
            "cert_version": {"const": 1},
            "compat_key": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "relation": {
                "type": "object",
                "required": list(RELATION_KEYS),
                "properties": {k: {"type": "object"} for k in RELATION_KEYS},
                "additionalProperties": False,
            },
            "execution_identity": {
                "type": "object",
                "description": "part (a): artifact shas, timestep, graph/weights "
                               "sha, adapters + normalization, runtime, "
                               "compiler/hardware/driver settings as available",
                "required": list(RELATION_KEYS),
            },
            "restart_state_inventory": {
                "type": "object",
                "description": "part (b): the COMPLETE restart-state inventory; "
                               "items not yet snapshotable = REGISTERED GAPS",
                "required": ["items", "registered_gaps", "deployment_class"],
                "properties": {
                    "items": {"type": "array", "items": item_schema,
                              "minItems": len(INVENTORY_ITEMS)},
                    "registered_gaps": {"type": "array", "items": gap_schema},
                    "deployment_class": {"enum": list(DEPLOYMENT_CLASSES)},
                },
            },
            "replay_evidence": {
                "type": "object",
                "description": "part (c): tick-ordered events, initial snapshot, "
                               "periodic state hashes, monitor outputs",
                "required": ["initial_snapshot_sha256", "events",
                             "periodic_stride", "final_state_sha256",
                             "monitors", "trajectory_sha256"],
                "properties": {
                    "initial_snapshot_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "events": {"type": "array", "items": event_schema, "minItems": 1},
                    "periodic_stride": {"type": "integer", "minimum": 1},
                    "final_state_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "monitors": {
                        "type": "array", "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["name", "pass", "detail_sha256"],
                            "properties": {
                                "name": {"type": "string"},
                                "pass": {"const": True},
                                "detail_sha256": {"type": "string"},
                            },
                        },
                    },
                    "trajectory_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "qualification_scope": {
                "type": "object",
                "description": "part (d): declared qualification scope",
                "required": ["bodies", "skills", "transitions", "ranges",
                             "horizons", "bars", "non_regression_margins"],
                "properties": {
                    "bodies": {"type": "array"},
                    "skills": {"type": "array"},
                    "transitions": {"type": "array"},
                    "ranges": {"type": "object"},
                    "horizons": {"type": "object"},
                    "bars": {"type": "object"},
                    "non_regression_margins": {"type": "array", "items": margin_schema,
                                               "minItems": 1},
                },
            },
            "issued_by": {"type": "string"},
            "lane": {"type": "string"},
            "base_commit": {"type": "string"},
            "prereg_receipt": {"type": "string"},
            "prereg_rule0_sha": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "cert_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }
