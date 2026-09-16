"""Read project instructions and planning records without changing any graph.

Admission to the active specification is independent of implementation or proof.
This CLI reads a file snapshot; it does not claim a controller task or publish.
"""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sys

from .project_documents import verify as verify_document
from .queries import blockers_of
from .store import CreatureGraph, STORE_PATH

SPEC_SCHEMA = "chimera.project_spec.v1"
ADMISSION = "active_specification"
CATEGORIES = {"documentation", "release", "inventory", "concept", "work"}
POLICY_IDS = ("req.documentation_admission", "req.agent_operation",
              "req.engine_game_release", "req.encapsulation_inventory")


def active(obj):
    record = obj.get("project_spec")
    return isinstance(record, dict) and record.get("schema") == SPEC_SCHEMA and record.get("admission") == ADMISSION


def check(g):
    """Structural and admission checks only. Does not refresh/stamp evidence."""
    errors = list(g.check())
    for key, obj in g.objects.items():
        if key != obj.get("id"):
            errors.append(f"{key}: object key differs from id")
        document = obj.get("document")
        archived = isinstance(document, dict) and (
            bool({"bytes_base64", "sha256", "byte_count", "original_path"} & document.keys())
            or document.get("authority") == "imported_untrusted")
        if archived:
            try:
                raw = verify_document(obj)
                try:
                    expected_text = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    expected_text = None
                if obj["document"].get("text") != expected_text:
                    raise ValueError("searchable text differs from archived bytes")
            except (ValueError, KeyError, TypeError) as error:
                errors.append(f"{key}: archived document invalid: {error}")
        if "project_spec" not in obj:
            continue
        spec = obj["project_spec"]
        if not isinstance(spec, dict):
            errors.append(f"{key}: project_spec must be an object")
            continue
        if spec.get("schema") != SPEC_SCHEMA:
            errors.append(f"{key}: unsupported project_spec schema: {spec.get('schema')!r}")
        if spec.get("admission") != ADMISSION:
            errors.append(f"{key}: unsupported project_spec admission: {spec.get('admission')!r}")
        if spec.get("category") not in CATEGORIES:
            errors.append(f"{key}: unsupported project_spec category")
        origin = spec.get("origin_id")
        if not isinstance(origin, str) or not origin or origin not in g.objects:
            errors.append(f"{key}: missing project_spec origin")
        elif g.objects[origin].get("kind") != "source":
            errors.append(f"{key}: project_spec origin must be a source")
        elif not any(r["src"] == key and r["rel"] == "derived_from" and r["dst"] == origin for r in g.relations):
            errors.append(f"{key}: missing derived_from origin edge")
        try:
            when = datetime.fromisoformat(spec.get("admitted_utc", "").replace("Z", "+00:00"))
            if when.tzinfo is None:
                raise ValueError("timezone missing")
        except (ValueError, AttributeError, TypeError):
            errors.append(f"{key}: admitted_utc must include a timezone")
        physical = obj.get("physical")
        if not isinstance(physical, dict):
            physical = {}
        for field in ("statement", "prediction"):
            if not isinstance(physical.get(field), str) or not physical[field].strip():
                errors.append(f"{key}: physical.{field} required")
        if not isinstance(physical.get("contract"), dict) or not physical["contract"]:
            errors.append(f"{key}: nonempty physical.contract required")
        falsifier = obj.get("falsifier")
        if not isinstance(falsifier, dict) or not isinstance(falsifier.get("statement"), str) or not falsifier["statement"].strip():
            errors.append(f"{key}: falsifier.statement required")
        if spec.get("category") == "concept":
            if obj.get("kind") != "capability" or not key.startswith("concept."):
                errors.append(f"{key}: concept must be a concept.* capability")
            contract = physical.get("contract")
            layer = contract.get("layer") if isinstance(contract, dict) else None
            if not isinstance(layer, str) or not layer.strip():
                errors.append(f"{key}: concept layer required")
        if spec.get("category") == "work" and obj.get("kind") != "work":
            errors.append(f"{key}: work admission requires kind=work")
    return errors


def evidence(g, oid):
    ids = set(g.get(oid).get("evidence") or [])
    ids.update(r["dst"] for r in g.out_edges(oid, "verified_by"))
    if g.get(oid).get("kind") == "evidence":
        ids.add(oid)
    records = []
    for eid in sorted(ids):
        obj = g.objects.get(eid)
        if obj is None or obj.get("kind") != "evidence":
            records.append({"id": eid, "effective_validation": "unknown", "reason": "missing evidence record"})
            continue
        stored = obj.get("validation", "untested")
        reasons = g.stale_evidence(eid) if stored != "untested" else []
        effective = "stale" if stored == "stale" or reasons else stored
        records.append({"id": eid, "stored_validation": stored, "effective_validation": effective,
                        "last_result": obj.get("last_result", stored),
                        "captured_utc": obj.get("captured_utc"),
                        "stale_reasons": reasons or obj.get("stale_reasons", [])})
    return records


def show(g, oid):
    obj = g.get(oid)
    return {"object": obj, "admission": ADMISSION if active(obj) else "reference_or_experimental",
            "dependencies": [{"id": dep, "status": g.get(dep)["status"]} for dep in g.requires(oid)],
            "blockers": blockers_of(g, oid), "evidence_freshness": evidence(g, oid),
            "relations": g.out_edges(oid)}


def concepts(g):
    records = [o for o in g.objects.values() if active(o) and o["project_spec"]["category"] == "concept"]
    def order(o):
        value = o.get("catalog_order", o["physical"]["contract"].get("catalog_order", 999999))
        return (value if isinstance(value, (int, float)) else 999999, o["id"])
    return [{"id": o["id"], "name": o["name"], "layer": o["physical"]["contract"]["layer"],
             "status": o["status"], "statement": o["physical"]["statement"],
             "falsifier": o["falsifier"]["statement"]} for o in sorted(records, key=order)]


def checklist(g, oid):
    if not isinstance(g.get(oid).get("execution_workflow"), dict):
        return {"structurally_complete": False, "reason": "execution_workflow missing",
                "dispatchable": False}
    # Use the controller's real binding validator; do not invent a parallel checklist contract.
    fleet = str(Path(__file__).resolve().parents[1] / "agent_fleet")
    if fleet not in sys.path:
        sys.path.insert(0, fleet)
    from graph_workflow import binding
    try:
        bound = binding(g, oid)
    except (ValueError, KeyError, TypeError) as error:
        return {"structurally_complete": False, "reason": str(error), "dispatchable": False}
    return {"structurally_complete": True, "input_hash": bound["input_hash"],
            "dispatchable": None, "reason": "checklist binds; controller admission, ownership and resources not checked"}


def planning(g):
    records = [o for o in g.objects.values() if active(o) and o["project_spec"]["category"] == "work"]
    def order(o):
        rank = o.get("build_rank")
        return (rank if isinstance(rank, (int, float)) else 999999, o["id"])
    return {"view": "planning_order", "qualification": "Planning order is not permission to execute or evidence of completion.",
            "work": [{"id": o["id"], "name": o["name"], "build_rank": o.get("build_rank"),
                      "status": o["status"], "blockers": blockers_of(g, o["id"]),
                      "checklist": checklist(g, o["id"]),
                      "evidence_freshness": evidence(g, o["id"])} for o in sorted(records, key=order)]}


def searchable(value):
    if isinstance(value, dict):
        return " ".join(searchable(v) for k, v in value.items() if k != "bytes_base64")
    if isinstance(value, list):
        return " ".join(searchable(v) for v in value)
    return str(value)


def search(g, term):
    if not term.strip():
        raise ValueError("search requires a nonempty term")
    result = []
    for oid, obj in sorted(g.objects.items()):
        text = searchable(obj)
        position = text.casefold().find(term.casefold())
        if position >= 0:
            result.append({"id": oid, "name": obj["name"], "kind": obj["kind"],
                           "admission": ADMISSION if active(obj) else "reference_or_experimental",
                           "excerpt": text[max(0, position - 70):position + 170]})
    return result


def summary(g, path):
    admitted = [o for o in g.objects.values() if active(o)]
    return {"store": str(Path(path).resolve()), "graph_hash": g.graph_hash(),
            "authority": "Selected graph file snapshot; a provisioned controller graph_snapshot is authoritative for its service.",
            "active_specifications": len(admitted),
            "active_categories": dict(sorted(Counter(o["project_spec"]["category"] for o in admitted).items())),
            "reference_or_experimental": len(g.objects) - len(admitted),
            "policies": [{"id": oid, "present_and_active": oid in g.objects and active(g.objects[oid])} for oid in POLICY_IDS],
            "queries": ["--show ID", "--concepts", "--next", "--search WORD", "--check", "--json"],
            "meaning": "Active specification means an adopted requirement, not implemented or verified behavior."}


def render(result):
    if isinstance(result, list):
        lines = []
        for row in result:
            lines.append(f"{row['id']} | {row.get('name', '')}")
            for key in ("layer", "admission", "status", "statement", "falsifier", "excerpt"):
                if key in row:
                    lines.append(f"  {key}: {row[key]}")
        return "\n".join(lines) if lines else "No matching records."
    if "object" in result:
        # Human output retains every field; archived prose is printed with real line breaks.
        raw = json.dumps(result, indent=2, ensure_ascii=False)
        document = result["object"].get("document", {})
        if isinstance(document, dict) and isinstance(document.get("text"), str):
            raw += "\n\nArchived document text (reference; admission is shown above):\n" + document["text"]
        return raw
    return json.dumps(result, indent=2, ensure_ascii=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path(STORE_PATH))
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--concepts", action="store_true")
    actions.add_argument("--next", action="store_true")
    actions.add_argument("--show", metavar="ID")
    actions.add_argument("--check", action="store_true")
    actions.add_argument("--search", metavar="WORD")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        g = CreatureGraph.load(str(args.store))
        errors = check(g)
        if errors:
            result = {"ok": False, "errors": errors, "store": str(args.store.resolve())}
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 2
        if args.check:
            result = {**summary(g, args.store), "ok": True, "scope": "Graph structure and active-specification contracts only"}
        elif args.concepts:
            result = concepts(g)
        elif args.next:
            result = planning(g)
        elif args.show:
            result = show(g, args.show)
        elif args.search is not None:
            result = search(g, args.search)
        else:
            result = summary(g, args.store)
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else render(result))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
