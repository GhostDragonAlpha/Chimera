"""piece_record.py -- the §11.20.1 PIECE-RECORD LAYER: the qualified
mechanism-factory artifacts (the full-rim-pinned fan patch, the apex-weld
seam law, the k=2 fan-out star assembly) as first-class library citizens
(GAME_PLAN lines 2397-2418; first increment of 11.20 "artificial
proteins"). Schema chimera-mechanism-factory-piece-record-v1 -- the
record table of 11.20.1:

    design_recipe        immutable versioned graph of patches + explicit
                         seam edges; parameters, seed, parent ids; NO
                         executable code (hash-law enforced)
    physical_definition  law id + revision (= the PINNED
                         surface_energy_reference hash), units, topology,
                         valid loads/scales FROM MEASUREMENT (a claim not
                         covered by an in-gate measured case in a cited
                         receipt is refused), excluded phenomena (from the
                         law's own named refusals and witnesses)
    ports                stable attachment ids, patch geometry + local
                         frame, compatible exchanges, sign conventions,
                         prescribed/free variables, work accounting
    instance_state       owner declaration: recipes immutable and SHARED,
                         state PER INSTANCE (state hashes must differ)
    representations      direct reference QUALIFIED with receipt ids;
                         table and learned recorded REJECTED-at-gate with
                         their receipts -- the record carries failures,
                         it does not hide them
    function_card        measured response anchors, operating domain,
                         costs, failures, evidence ids, freshness
                         (= source file pins, re-verified at validation)
    fabrication_binding  permitted assembly ops FROM THE SEAM LAW
                         (apex-weld only; the witness (g) exclusions are
                         recorded, not forgotten)

Records are append-only JSON files under docs/evidence/mechanism_factory/
pieces/; a re-written identical record is idempotent, a changed one is
refused (piece_record_conflict). Refusals are named; none widened after
seeing results. CPU only; stdlib.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

_HERE = Path(__file__).resolve().parent            # tools/mechanism_factory
_REPO = _HERE.parent.parent                       # repo root (PythonChimera)

PIECE_RECORD_SCHEMA = "chimera-mechanism-factory-piece-record-v1"
PIECE_KINDS = ("piece", "law", "assembly")
PIECES_DIR = _REPO / "docs" / "evidence" / "mechanism_factory" / "pieces"
EVID_ROOT = _REPO / "docs" / "evidence"
PACKET_PATH = _HERE / "example_packet.json"
LAW_SOURCE = _REPO / "tools" / "membrane_scale_lab" / "surface_energy_reference.py"

TOP_LEVEL_FIELDS = ("schema", "record_id", "kind", "name", "utc",
                    "design_recipe", "physical_definition", "ports",
                    "instance_state", "representations",
                    "function_card", "fabrication_binding")
REQUIRED_SECTIONS = ("record_id", "kind", "design_recipe",
                     "physical_definition", "ports", "instance_state",
                     "representations", "function_card",
                     "fabrication_binding")
REJECTED_REPRESENTATION_KINDS = ("table", "learned")
PERMITTED_OPS = ("apex-weld",)          # witness (g): apexes only
_AFFORDANCE_KEYS = ("function_label", "affordance", "grants")

# measured response anchors must quote numbers measured under the gate;
# the packet's balance law is quoted, never widened by a record.
_GATE_KEY = "max_free_residual_N"
_SCALE_RE = re.compile(r"_scale(-?\d+(?:\.\d+)?)$")
_LOAD_RE = re.compile(r"_m(\d+(?:\.\d+)?)_")


class PieceRecordRefused(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def _sha256_canonical(obj) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()[:16]


def law_revision() -> str:
    """The pinned physical law's revision = its file hash."""
    return _sha256_file(LAW_SOURCE)


def packet_gate() -> float:
    thr = json.loads(PACKET_PATH.read_bytes())["acceptance_thresholds"]
    return float(thr[_GATE_KEY])


def units() -> dict:
    return json.loads(PACKET_PATH.read_bytes())["units"]


def recipe_hash(design_recipe: dict) -> str:
    """Immutable identity of the recipe graph (nodes + edges only)."""
    return _sha256_canonical({"nodes": design_recipe["nodes"],
                               "edges": design_recipe["edges"]})


def state_hash(state: dict) -> str:
    return _sha256_canonical(state)


def instantiate(record: dict, instance_id: str, state: dict) -> dict:
    """Copy a motif with a NEW instance identity: the recipe is shared
    (immutable), the state is per-instance. Refuses duplicate ids."""
    if not record["instance_state"].get("owner"):
        raise PieceRecordRefused("piece_state_orphaned",
                                 "record declares no instance owner")
    have = {i["instance_id"] for i in record["instance_state"]["instances"]}
    if instance_id in have:
        raise PieceRecordRefused("piece_instance_exists", instance_id)
    return {"instance_id": instance_id, "state": state,
            "state_hash": state_hash(state)}


# ── measurement extraction (domain claims must be COVERED by receipts) ──────

def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _resolve_receipt(name: str) -> Path | None:
    hits = list(EVID_ROOT.rglob(name))
    return hits[0] if hits else None


def measured_domain(receipt_paths: list) -> tuple:
    """(in_gate_scales, in_gate_loads) measured by the cited receipts:
    composed receipts record case dicts '..._scale<s>' with the case's
    max_free_residual_N; multi-point load receipts record '..._m<amp>_';
    an assembly's seam load is recorded in its composition ports prose
    ('(0.8 N ...)'). In-gate = residual <= the packet's unchanged
    max_free_residual_N."""
    gate = packet_gate()
    scales, loads = set(), set()
    for p in receipt_paths:
        p = _resolve_receipt(Path(p).name) or p
        try:
            r = json.loads(Path(p).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue
        for d in _walk(r):
            if not isinstance(d, dict):
                continue
            cid = str(d.get("case_id", ""))
            out = d.get("outputs") if isinstance(d.get("outputs"), dict) else d
            if "max_free_residual_N" in out:
                res = float(out["max_free_residual_N"])
                m = _SCALE_RE.search(cid)
                if m and res <= gate:
                    scales.add(float(m.group(1)))
                m = _LOAD_RE.search(cid)
                if m and res <= gate:
                    loads.add(float(m.group(1)))
        # an assembly's seam load, recorded in the composition ports prose
        comp = r.get("composition") or {}
        for txt in _iter_strings(comp):
            for m in re.finditer(r"\((\d+(?:\.\d+)?) N", txt):
                loads.add(float(m.group(1)))
    return scales, loads


def _iter_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_strings(v)
    elif isinstance(obj, str):
        yield obj


def _receipt_ids(record: dict) -> list:
    out = []
    for s in _iter_strings(record):
        if s.endswith(".json") and "/" not in s and "\\" not in s:
            out.append(s)
    return sorted(set(out))


# ── validation ───────────────────────────────────────────────────────────────

def validate(record: dict) -> dict:
    """Validate ONE record against the schema + laws; returns it unchanged.
    Refuses by name otherwise."""
    if not isinstance(record, dict):
        raise PieceRecordRefused("piece_malformed_record", "not an object")
    unknown = [k for k in record if k not in TOP_LEVEL_FIELDS]
    if unknown:
        raise PieceRecordRefused("piece_unknown_field", str(unknown))
    rec = dict(record)
    rec.setdefault("schema", PIECE_RECORD_SCHEMA)
    if rec["schema"] != PIECE_RECORD_SCHEMA:
        raise PieceRecordRefused("piece_unknown_schema", repr(rec["schema"]))
    for f in REQUIRED_SECTIONS:
        if f not in rec:
            raise PieceRecordRefused("piece_missing_field", f)
    if rec["kind"] not in PIECE_KINDS:
        raise PieceRecordRefused("piece_unknown_kind", repr(rec["kind"]))
    rid = rec["record_id"]
    if not isinstance(rid, str) or not re.match(r"^[A-Za-z0-9][A-Za-z0-9_.\-]*$", rid):
        raise PieceRecordRefused("piece_unsafe_record_id", repr(rid))

    # evidence links resolve (link rot is caught)
    for rid_json in _receipt_ids(rec):
        hits = list(EVID_ROOT.rglob(rid_json))
        if not hits:
            raise PieceRecordRefused("piece_evidence_dangling", rid_json)

    # design recipe: immutable, hash-verified, no executable code
    dr = rec["design_recipe"]
    if dr.get("immutable") is not True or dr.get("executable_code") is not False:
        raise PieceRecordRefused(
            "piece_recipe_mutability_violated",
            "design_recipe must declare immutable=true, executable_code=false")
    if dr.get("recipe_hash") != recipe_hash(dr):
        raise PieceRecordRefused("piece_recipe_hash_mismatch",
                                 "recompute the recipe hash")
    for e in dr.get("edges", []):
        if e.get("kind") not in PERMITTED_OPS:
            raise PieceRecordRefused("piece_edge_op_unqualified",
                                     repr(e.get("kind")))
    node_ids = {n.get("node_id") for n in dr.get("nodes", [])}
    edge_ends = {v for e in dr.get("edges", []) for v in e.get("endpoints", [])}
    if not edge_ends <= node_ids:
        raise PieceRecordRefused("piece_edge_endpoint_missing",
                                 repr(sorted(edge_ends - node_ids)))
    for n in dr.get("nodes", []):
        if not set(n.get("parent_ids", [])) <= node_ids:
            raise PieceRecordRefused("piece_parent_missing",
                                     repr(n.get("parent_ids")))

    # physical definition: law revision = the PINNED law file's hash;
    # domain claims FROM MEASUREMENT only
    pd = rec["physical_definition"]
    if pd.get("law_revision") != law_revision():
        raise PieceRecordRefused(
            "piece_law_revision_mismatch",
            "law_revision must be the pinned surface_energy_reference hash")
    if not pd.get("excluded_phenomena"):
        raise PieceRecordRefused("piece_exclusions_required",
                                 "the law's refusals must be recorded")
    cited = _receipt_ids(rec)
    paths = [EVID_ROOT / n for n in cited]
    scales, loads = measured_domain(paths)
    claim_scales = {float(s) for s in pd.get("valid_scales", [])}
    claim_loads = {float(s) for s in pd.get("valid_loads_N", [])}
    if not claim_scales <= scales:
        raise PieceRecordRefused(
            "piece_domain_unmeasured",
            f"scale claims {sorted(claim_scales - scales)} are not backed "
            f"by an in-gate measured case in the cited receipts")
    if not claim_loads <= loads:
        raise PieceRecordRefused(
            "piece_load_unmeasured",
            f"load claims {sorted(claim_loads - loads)} are not backed by "
            f"an in-gate measured case in the cited receipts")

    # ports
    ports = rec["ports"]
    if not isinstance(ports, list) or not ports:
        raise PieceRecordRefused("piece_ports_required",
                                 "a useful piece does something at a port")
    for p in ports:
        for f in ("port_id", "patch_geometry", "local_frame", "exchanges",
                  "sign_convention", "variables", "work_accounting"):
            if f not in p:
                raise PieceRecordRefused("piece_port_incomplete",
                                         f"{p.get('port_id')}: {f}")

    # instance state: shared immutable recipes, per-instance state
    inst = rec["instance_state"]["instances"]
    if not isinstance(inst, list) or not inst:
        raise PieceRecordRefused("piece_instances_required",
                                 "an instance owner must name >=1 instance")
    if len({i["instance_id"] for i in inst}) != len(inst):
        raise PieceRecordRefused("piece_instance_id_collision", "")
    hashes = [i["state_hash"] for i in inst]
    for i in inst:
        if i["state_hash"] != state_hash(i["state"]):
            raise PieceRecordRefused("piece_state_hash_mismatch",
                                     i["instance_id"])
    if len(set(hashes)) != len(hashes):
        raise PieceRecordRefused(
            "piece_state_collision",
            "instances sharing an immutable recipe still own SEPARATE state")

    # representations: qualified ones cite receipts; the REJECTED ones are
    # retained, never dropped (failure persistence)
    reps = rec["representations"]
    kinds_seen = {r.get("kind"): r.get("status") for r in reps}
    for r in reps:
        if r.get("status") == "qualified" and not r.get("receipt_ids"):
            raise PieceRecordRefused("piece_representation_unqualified",
                                     repr(r.get("kind")))
    if rec["kind"] in ("piece", "assembly"):
        for kind in REJECTED_REPRESENTATION_KINDS:
            if kinds_seen.get(kind) != "rejected_at_gate":
                raise PieceRecordRefused(
                    "representations_incomplete",
                    f"the rejected {kind} representation of this lineage "
                    f"must be retained, not dropped")

    # function card: naming grants nothing
    fc = rec["function_card"]
    claims_a_function = any(fc.get(k) for k in _AFFORDANCE_KEYS)
    if claims_a_function and (not fc.get("measured_response_anchors")
                              or not fc.get("evidence_ids")):
        raise PieceRecordRefused(
            "function_card_required",
            "calling the piece a muscle/valve/whatever grants no law: a "
            "function claim needs measured anchors + evidence ids")
    for eid in fc.get("evidence_ids", []):
        if not list(EVID_ROOT.rglob(eid)):
            raise PieceRecordRefused("piece_evidence_dangling", eid)
    for rel, sha in (fc.get("freshness") or {}).get("source_pins", {}).items():
        src = _REPO / rel
        if not src.is_file() or _sha256_file(src) != sha:
            raise PieceRecordRefused("piece_freshness_violated", rel)

    # fabrication binding: ops from the seam law, exclusions recorded
    fb = rec["fabrication_binding"]
    ops = fb.get("permitted_assembly_ops", [])
    if not set(ops) <= set(PERMITTED_OPS):
        raise PieceRecordRefused("piece_fabrication_op_unqualified",
                                 repr(sorted(set(ops) - set(PERMITTED_OPS))))
    if not fb.get("exclusions"):
        raise PieceRecordRefused("piece_exclusions_required",
                                 "witness (g) exclusions must be recorded")
    return rec


def write_record(record: dict) -> Path:
    """Validate and append ONE record; identical re-writes are idempotent,
    changed ones are refused (append-only evidence)."""
    rec = validate(record)
    PIECES_DIR.mkdir(parents=True, exist_ok=True)
    out = PIECES_DIR / f"{rec['record_id']}.json"
    if out.exists():
        old = json.loads(out.read_text(encoding="utf-8"))
        old.pop("utc", None)
        new = dict(rec)
        new.pop("utc", None)
        if old == new:
            return out
        raise PieceRecordRefused(
            "piece_record_conflict",
            f"{rec['record_id']} is already retained with different bytes "
            f"(append-only; record a NEW record id instead)")
    out.write_text(json.dumps(rec, indent=1, default=str) + "\n",
                   encoding="utf-8")
    return out


def load_record(record_id: str) -> dict:
    p = PIECES_DIR / f"{record_id}.json"
    if not p.is_file():
        raise PieceRecordRefused("piece_record_missing", record_id)
    return json.loads(p.read_text(encoding="utf-8"))


def amend_representations(record_id: str, entry: dict) -> Path:
    """ADDITIVE-ONLY amendment law: append exactly ONE representation
    entry to a retained record; every other byte stays untouched. The
    PRIOR bytes are archived under pieces/archive/ (append-only evidence
    stays intact). Idempotent: if the identical entry is already present,
    the retained record is returned unchanged."""
    rec = load_record(record_id)
    path = PIECES_DIR / f"{record_id}.json"
    for r in rec["representations"]:
        if r.get("kind") == entry.get("kind"):
            if r == entry:
                return path
            raise PieceRecordRefused(
                "piece_representation_kind_exists",
                f"{record_id} already carries a different "
                f"{entry.get('kind')!r} entry")
    prior_bytes = path.read_bytes()
    amended = json.loads(json.dumps(rec))     # deep copy
    amended["representations"].append(entry)
    validate(amended)
    stamp = hashlib.sha256(prior_bytes).hexdigest()[:16]
    archive = PIECES_DIR / "archive" / f"{record_id}.{stamp}.json"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        archive.write_bytes(prior_bytes)
    path.write_text(json.dumps(amended, indent=1, default=str) + "\n",
                    encoding="utf-8")
    return path


def amend_physical_definition(record_id: str, key: str, value) -> Path:
    """ADDITIVE-ONLY amendment law for physical_definition: add exactly ONE
    new key (e.g. a measured resolution validity map) to a retained record;
    every other byte stays untouched. The PRIOR bytes are archived under
    pieces/archive/ (append-only evidence stays intact). Idempotent: if the
    identical key->value is already present, the retained record is
    returned unchanged. Refusals: piece_pd_key_exists when the key exists
    with DIFFERENT bytes (amend by adding a NEW dated key, never by
    overwriting a measured claim), piece_record_missing when the record is
    not retained."""
    rec = load_record(record_id)
    path = PIECES_DIR / f"{record_id}.json"
    pd = rec["physical_definition"]
    if key in pd:
        if pd[key] == value:
            return path
        raise PieceRecordRefused(
            "piece_pd_key_exists",
            f"{record_id} already carries physical_definition.{key!r} with "
            f"different bytes; add a NEW dated key instead of overwriting "
            f"a measured claim")
    prior_bytes = path.read_bytes()
    amended = json.loads(json.dumps(rec))     # deep copy
    amended["physical_definition"][key] = value
    validate(amended)
    stamp = hashlib.sha256(prior_bytes).hexdigest()[:16]
    archive = PIECES_DIR / "archive" / f"{record_id}.{stamp}.json"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        archive.write_bytes(prior_bytes)
    path.write_text(json.dumps(amended, indent=1, default=str) + "\n",
                    encoding="utf-8")
    return path
