"""The one object store behind all three views.

The store holds objects (dicts, see schema.OBJECT_FIELDS) and typed relations.
Authored seed data and engine-extracted data are loaded from SEPARATE files and
joined by stable IDs, so a reindex or engine re-snapshot can never erase
planned anatomy. Layout positions (roadmap graph drawing) live in
`store.layout`, never inside spatial frames.
"""

import hashlib
import copy
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import (  # noqa: E402
    DAG_RELS, PHYSICAL_RELS, REL_DERIVED_FROM, REL_REQUIRES, REL_VERIFIED_BY, SCHEMA_VERSION,
    SCHEMA_VERSION_LEGACY, STATUS_RANK, content_projection, validate_object,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STORE_PATH = os.path.join(DATA_DIR, "creature_graph.json")

# validation states are INDEPENDENT of implementation status (the brief):
#   untested -> passing | failing   (a run happened)
#   any of the above -> stale       (a physics-relevant input changed; the last
#                                    result stays visible in last_result)
VALIDATION_STATES = ("untested", "passing", "failing", "stale")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def content_version(obj: dict) -> str:
    """Stable hash of an object's physics-relevant projection."""
    blob = json.dumps(content_projection(obj), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


class CreatureGraph:
    def __init__(self):
        self.objects = {}    # id -> object dict
        self.relations = []  # {"rid","src","rel","dst","note"} -- a LIST: multiple
                             # distinct relations between the same pair are preserved
        self.layout = {}     # id -> {"roadmap_tier": int, "roadmap_x": float}
                             # NEVER mixed into engine coordinates
        self.meta = {}       # provenance, schema version, input hashes

    # ---------- construction ----------
    def add(self, obj: dict) -> dict:
        oid = obj["id"]
        if oid in self.objects:
            raise ValueError(f"duplicate object id: {oid}")
        errs = validate_object(obj)
        if errs:
            raise ValueError("; ".join(errs))
        self.objects[oid] = obj
        return obj

    def relate(self, src: str, rel: str, dst: str, note: str = "") -> dict:
        """Add ONE typed directed edge. Calling twice with the same pair+rel
        adds two distinct edges (multiplicity is preserved, never collapsed)."""
        for oid in (src, dst):
            if oid not in self.objects:
                raise ValueError(f"relation endpoint missing: {oid} ({src} -{rel}-> {dst})")
        identity = json.dumps([src, rel, dst, note], ensure_ascii=False)
        stem = "r_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
        used = {r["rid"] for r in self.relations}
        ordinal = 0
        while f"{stem}_{ordinal}" in used:
            ordinal += 1
        edge = {"rid": f"{stem}_{ordinal}", "src": src, "rel": rel,
                "dst": dst, "note": note}
        self.relations.append(edge)
        return edge

    def sync_dependencies(self) -> None:
        """Authored `dependencies` fields are the carrier; emit requires_implementation
        relations from them (and `evidence` fields -> verified_by, `enables`
        fields -> enables_player_experience). Idempotent."""
        have_impl = {(r["src"], r["dst"]) for r in self.relations if r["rel"] == REL_REQUIRES}
        have_ev = {(r["src"], r["dst"]) for r in self.relations if r["rel"] == REL_VERIFIED_BY}
        have_en = {(r["src"], r["dst"]) for r in self.relations
                   if r["rel"] == "enables_player_experience"}
        for obj in self.objects.values():
            for dep in obj.get("dependencies") or []:
                if dep not in self.objects:
                    raise ValueError(f"{obj['id']}: dependency missing from store: {dep}")
                if (obj["id"], dep) not in have_impl:
                    self.relate(obj["id"], REL_REQUIRES, dep, note="authored dependency")
                    have_impl.add((obj["id"], dep))
            for ev in obj.get("evidence") or []:
                if ev not in self.objects:
                    raise ValueError(f"{obj['id']}: evidence missing from store: {ev}")
                if (obj["id"], ev) not in have_ev:
                    self.relate(obj["id"], REL_VERIFIED_BY, ev, note="authored evidence")
                    have_ev.add((obj["id"], ev))
            for en in obj.get("enables") or []:
                if en not in self.objects:
                    raise ValueError(f"{obj['id']}: enables target missing from store: {en}")
                if (obj["id"], en) not in have_en:
                    self.relate(obj["id"], "enables_player_experience", en,
                                note="authored enables")
                    have_en.add((obj["id"], en))

    # ---------- access ----------
    def get(self, oid: str) -> dict:
        if oid not in self.objects:
            raise KeyError(f"unknown object: {oid}")
        return self.objects[oid]

    def by_kind(self, kind: str) -> list:
        return [o for o in self.objects.values() if o["kind"] == kind]

    def out_edges(self, oid: str, rel: str = None) -> list:
        return [r for r in self.relations if r["src"] == oid and (rel is None or r["rel"] == rel)]

    def in_edges(self, oid: str, rel: str = None) -> list:
        return [r for r in self.relations if r["dst"] == oid and (rel is None or r["rel"] == rel)]

    def requires(self, oid: str) -> list:
        return [r["dst"] for r in self.out_edges(oid, REL_REQUIRES)]

    def enables(self, oid: str) -> list:
        return [r["dst"] for r in self.out_edges(oid, "enables_player_experience")]

    # ---------- integrity ----------
    def check(self) -> list:
        """Structural integrity: schema, DAGs (requires_implementation,
        derived_from), relation sanity, dependency-mirror consistency."""
        errs = []
        seen_ids = set()
        for obj in self.objects.values():
            errs.extend(validate_object(obj))
            seen_ids.add(obj["id"])
        for r in self.relations:
            if r["src"] not in seen_ids or r["dst"] not in seen_ids:
                errs.append(f"dangling relation {r}")
        rids = [r.get("rid") for r in self.relations]
        if any(not isinstance(rid, str) or not rid for rid in rids) or len(set(rids)) != len(rids):
            errs.append("missing or duplicate relation identity")
        # the DAG relations must each be acyclic
        for dag_rel in DAG_RELS:
            adj = {}
            for r in self.relations:
                if r["rel"] == dag_rel:
                    adj.setdefault(r["src"], set()).add(r["dst"])
            state = {}  # 0 visiting, 1 done

            def visit(node, path):
                if state.get(node) == 1:
                    return
                if state.get(node) == 0:
                    cyc = path[path.index(node):] + [node]
                    errs.append(f"{dag_rel} cycle: " + " -> ".join(cyc))
                    return
                state[node] = 0
                for nxt in adj.get(node, ()):
                    visit(nxt, path + [node])
                state[node] = 1

            for n in adj:
                visit(n, [])
        # mirror consistency: dependencies fields vs relations
        for obj in self.objects.values():
            rels = set(self.requires(obj["id"]))
            if set(obj.get("dependencies") or []) != rels:
                errs.append(f"{obj['id']}: dependencies field != requires_implementation relations")
        return errs

    # ---------- validation lifecycle (staleness) ----------
    def evidence_records(self) -> list:
        """Objects of kind=evidence, which carry:
             validation      untested | passing | failing | stale
             last_result     the pre-staleness verdict (stays VISIBLE)
             deps            [object ids] the evidence was measured against
             captured        {oid: content_version} at measurement time
             captured_utc, engine (ticks/snapshot reference) where relevant
        """
        return [o for o in self.objects.values() if o["kind"] == "evidence"]

    def relation_capture(self, deps) -> dict:
        """Incident physical/provenance edges, including direction and multiplicity.
        Unrelated graph edits and bookkeeping edges do not invalidate a measure.
        """
        scope = set(deps)
        return {r["rid"]: copy.deepcopy(r) for r in self.relations
                if r["rel"] in (*PHYSICAL_RELS, REL_DERIVED_FROM)
                and (r["src"] in scope or r["dst"] in scope)}

    def record_evidence(self, record: dict) -> dict:
        """Record a NEW measurement. Never recapture or overwrite an old ID.
        Caller supplies the measured result/time and its declared input scope.
        """
        ev = copy.deepcopy(record)
        deps = ev.get("deps")
        if ev.get("kind") != "evidence" or ev.get("validation") not in ("passing", "failing"):
            raise ValueError("a measured evidence record requires a passing/failing result")
        if not isinstance(deps, list) or not deps or len(set(deps)) != len(deps):
            raise ValueError("evidence requires nonempty unique dependencies")
        for dep in deps:
            self.get(dep)
        when = ev.get("captured_utc")
        if not isinstance(when, str) or datetime.fromisoformat(when.replace("Z", "+00:00")).tzinfo is None:
            raise ValueError("captured_utc must be an explicit timezone-aware measurement time")
        ev["capture_contract"] = 1
        ev["captured"] = {dep: content_version(self.get(dep)) for dep in deps}
        ev["captured_dependencies"] = sorted(deps)
        ev["captured_relations"] = self.relation_capture(deps)
        ev["last_result"] = ev["validation"]
        return self.add(ev)

    def stale_evidence(self, evidence_oid: str) -> list:
        """Deps whose physics-relevant content changed since the evidence was
        captured (conservative: ANY mismatch stales, none un-stales)."""
        ev = self.get(evidence_oid)
        captured = ev.get("captured")
        mismatches = []
        if not isinstance(captured, dict) or not captured:
            return [{"dep": evidence_oid, "reason": "capture empty/missing"}]
        deps = ev.get("deps") or []
        if not deps or set(captured) != set(deps):
            mismatches.append({"dep": evidence_oid, "reason": "capture does not cover declared dependencies"})
        if ev.get("capture_contract") != 1 or ev.get("captured_dependencies") != sorted(deps):
            mismatches.append({"dep": evidence_oid, "reason": "capture contract or scope missing/changed"})
        if not ev.get("captured_utc"):
            mismatches.append({"dep": evidence_oid, "reason": "measurement time missing"})
        old_relations = ev.get("captured_relations")
        if not isinstance(old_relations, dict):
            mismatches.append({"dep": evidence_oid, "reason": "relation capture missing"})
        elif old_relations != self.relation_capture(deps):
            mismatches.append({"dep": evidence_oid, "reason": "measured relationships changed"})
        for dep_oid, ver in captured.items():
            if dep_oid not in self.objects:
                mismatches.append({"dep": dep_oid, "reason": "dep removed from store"})
            elif content_version(self.get(dep_oid)) != ver:
                mismatches.append({"dep": dep_oid, "reason": "physics-relevant change",
                                   "captured": ver,
                                   "current": content_version(self.get(dep_oid))})
        return mismatches

    def refresh_validation(self, stamp=True) -> list:
        """Recompute validation state of every evidence record. Returns the list
        of records that flipped to stale. A FAILED current test stays failing
        (visible); a relevant change stales passing AND failing alike; source
        availability NEVER flips anything to passing."""
        flipped = []
        for ev in self.evidence_records():
            val = ev.get("validation", "untested")
            if val == "untested" or val == "stale":
                continue
            bad = self.stale_evidence(ev["id"])
            if bad:
                ev["last_result"] = val
                ev["validation"] = "stale"
                ev["stale_reasons"] = bad
                if stamp:
                    ev["staled_utc"] = _utcnow()
                flipped.append(ev["id"])
        return flipped

    def versions(self) -> dict:
        """content_version for every object (used to capture evidence deps)."""
        return {oid: content_version(obj) for oid, obj in self.objects.items()}

    def graph_hash(self) -> str:
        """Deterministic hash of the whole store content (save/reload fidelity)."""
        blob = json.dumps({"objects": self.objects,
                           "relations": sorted(json.dumps(r, sort_keys=True)
                                               for r in self.relations),
                           "layout": self.layout}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # ---------- io ----------
    def save(self, path: str = STORE_PATH) -> str:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.meta["schema_version"] = SCHEMA_VERSION
        self.meta["saved_utc"] = _utcnow()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "meta": self.meta,
            "objects": self.objects,
            "relations": self.relations,
            "layout": self.layout,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1, ensure_ascii=False)
        return path

    @classmethod
    def load(cls, path: str = STORE_PATH) -> "CreatureGraph":
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        version = payload.get("schema_version", SCHEMA_VERSION_LEGACY)
        if version not in (SCHEMA_VERSION, SCHEMA_VERSION_LEGACY):
            raise ValueError(f"unsupported creature graph schema_version: {version!r}")
        g = cls()
        g.objects = payload["objects"]
        g.relations = payload["relations"]
        g.layout = payload.get("layout", {})
        g.meta = payload.get("meta", {})
        g.meta["loaded_schema_version"] = payload.get("schema_version",
                                                      SCHEMA_VERSION_LEGACY)
        return g
