"""native_binding.py -- §11.20 stage 9 wiring, first increment: bind a
QUALIFIED piece record (tools/mechanism_factory/piece_record.py layer) into
the EXISTING compile path. This module adds no physics, no solver, no
second compiler and no engine seam: the geometry compile is the record's own
qualified direct-reference path -- composed_chain.build_star for the k=2
fan-out star assembly (tools/mechanism_factory/composed_chain.py:126) and
the lab's fixture generator for a single patch
(tools/membrane_scale_lab/fixture_generator.py, high_degree_fan) -- with the
pinned surface-energy law validating every compiled geometry
(surface_energy_reference.evaluate_surface; the law's own named refusals).

What a "compile transaction" is here (§11.20.2 item 6): a self-verifying
document carrying the compiled rest geometry, the native-experiment packet
fields (positions, faces, gamma, vertex-corner adjacency, pins, port load)
and the STABLE region/face/port ids re-derived from the record -- never
invented. Applying a transaction onto an accepted world is transactional:

  * the transaction hash must reproduce from its own content
    (binding_transaction_hash_mismatch),
  * the compile must be reproducible FROM THE RECORD byte-for-byte
    (binding_transaction_stale: a self-consistent but non-reproducible
    transaction -- e.g. tampered positions -- is refused),
  * the instance id must be new (binding_instance_exists),
  * only then does a NEW accepted-world document get built. The caller's
    bytes are never mutated, so a rejected compile leaves the accepted
    world byte-identical by construction.

Domain law: the compile refuses, BY NAME, any instance parameter outside
the RECORD's measured domain (physical_definition.valid_scales /
valid_loads_N -- claims already backed by in-gate receipts at validation).
The compile path's own refusals (unsupported_scale, seam ownership,
InvalidSurface) stay in force underneath; nothing is widened.

Out of scope (recorded honestly, as the records already do): the engine-side
render/pick/inspector binding (fabrication_binding.physical_to_render is
"unset" in every retained record) and any live solve inside this module.
CPU only; numpy + stdlib; no engine, no GPU, no network.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent            # tools/mechanism_factory
_REPO = _HERE.parent.parent
_TOOLS = _HERE.parent
_LAB = _TOOLS / "membrane_scale_lab"
for _p in (str(_TOOLS), str(_LAB), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import piece_record as pr                                   # noqa: E402
import composed_chain as cc                                 # noqa: E402
import composed_patch as cp                                 # noqa: E402
import fixture_generator as fg                              # noqa: E402
from surface_energy_reference import (                      # noqa: E402
    build_vertex_corner_adjacency, evaluate_surface)

__all__ = [
    "BINDING_SCHEMA", "WORLD_SCHEMA", "BindingRefused",
    "compile_transaction", "apply_transaction", "restore_world",
    "transaction_hash",
]

BINDING_SCHEMA = "chimera-mechanism-factory-compile-transaction-v1"
WORLD_SCHEMA = "chimera-mechanism-factory-accepted-world-v1"

_PIECE_GENERATOR = "fixture_generator.high_degree_fan"
_PIECE_COMPILE_PATH = "tools/membrane_scale_lab/fixture_generator.high_degree_fan"
_STAR_COMPILE_PATH = "tools/mechanism_factory/composed_chain.build_star"


class BindingRefused(RuntimeError):
    """A named refusal. The reason is machine-readable; never widened."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def _sha256_canonical(obj) -> str:
    import hashlib
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()[:16]


def _f64_hex(a: np.ndarray) -> str:
    return np.asarray(a, dtype="<f8").tobytes().hex()


def _qualified_direct_reference(rec: dict) -> dict:
    for r in rec["representations"]:
        if r.get("kind") == "direct-reference" and r.get("status") == "qualified":
            return r
    raise BindingRefused(
        "binding_record_unqualified",
        f"{rec['record_id']} carries no qualified direct-reference "
        f"representation; there is no compile path to bind")


def _in_domain(rec: dict, scale: float, load_N: float) -> None:
    pd = rec["physical_definition"]
    scales = {float(s) for s in pd.get("valid_scales", [])}
    loads = {float(s) for s in pd.get("valid_loads_N", [])}
    if float(scale) not in scales:
        raise BindingRefused(
            "binding_scale_out_of_domain",
            f"scale {scale} is not in {rec['record_id']}'s MEASURED domain "
            f"{sorted(scales)}; domain drift is refused, not tuned")
    if float(load_N) not in loads:
        raise BindingRefused(
            "binding_load_out_of_domain",
            f"load {load_N} N is not in {rec['record_id']}'s MEASURED domain "
            f"{sorted(loads)}; domain drift is refused, not tuned")


def _merged_params(node: dict) -> dict:
    """The generator parameter dict the compile path consumes."""
    return {**node["params"], "seed": node["seed"]}


def _input_port(rec: dict) -> dict:
    inputs = [p for p in rec["ports"] if p.get("kind") == "input"]
    if len(inputs) != 1:
        raise BindingRefused(
            "binding_port_ambiguous",
            f"exactly one input port is bindable; found {len(inputs)}")
    p = inputs[0]
    frame = str(p.get("local_frame", ""))
    if "vertical" not in frame or "-z" not in frame:
        raise BindingRefused(
            "binding_port_unqualified",
            f"{p['port_id']}: the qualified load frame is the vertical -z "
            f"dead-load axis; record declares {frame!r}")
    return p


def _load_vector(load_N: float) -> tuple:
    return (0.0, 0.0, -float(load_N))


def _ids_for_star(rec: dict, star: dict) -> dict:
    """Region/face/port ids RE-DERIVED from the compiled star + the record.

    Region = one recipe node's film (its vertex block + contiguous face
    block); ports bind the record's declared port ids to the compiled
    vertex blocks. Any drift between record and compiled path is refused."""
    nodes = rec["design_recipe"]["nodes"]
    rims = [int(nd["params"]["n_rim"]) for nd in nodes]
    if len(set(rims)) != 1:
        raise BindingRefused(
            "binding_recipe_unmatched",
            f"the existing compile path assumes one fan resolution; recipe "
            f"declares n_rim {sorted(set(rims))}")
    n = rims[0]
    F = np.asarray(star["faces"])
    n_faces = int(F.shape[0])
    if n_faces != len(nodes) * n:
        raise BindingRefused(
            "binding_recipe_unmatched",
            f"compiled star has {n_faces} faces; the recipe declares "
            f"{len(nodes)} pieces x {n} faces -- record and compile path "
            f"disagree, refusing")
    owner = {e["seam_owner"] for e in rec["design_recipe"]["edges"]}
    if len(owner) != 1:
        raise BindingRefused(
            "binding_recipe_unmatched",
            "the star law has ONE seam owner; recipe declares "
            f"{sorted(owner)}")
    owner_id = owner.pop()
    hangers = [nd["node_id"] for nd in nodes if nd["node_id"] != owner_id]
    if len(rec["design_recipe"]["edges"]) != len(hangers):
        raise BindingRefused(
            "binding_recipe_unmatched",
            "every hanger must arrive by exactly one apex weld")

    # vertex blocks: the owner piece owns vertices [0, n] (rim + apex);
    # each hanger contributes its n far-rim vertices (its apex dedups onto
    # the seam), in recipe node order -- the same stacking law build_star
    # records in star["blocks"].
    rim_blocks = star["blocks"][1:]
    if [len(b) for b in rim_blocks] != [n] * len(hangers):
        raise BindingRefused(
            "binding_recipe_unmatched",
            "hanger rim blocks do not match the recipe's fan sizes")
    seam = int(star["seam_index"])
    regions = [{"region_id": owner_id,
                "vertex_block": list(range(n + 1)),
                "face_block": list(range(0, n))}]
    for k, nid in enumerate(hangers):
        regions.append({
            "region_id": nid,
            "vertex_block": list(rim_blocks[k]) + [seam],
            "face_block": list(range((k + 1) * n, (k + 2) * n)),
        })

    ports = []
    inputs = [p for p in rec["ports"] if p.get("kind") == "input"]
    ports.append({"port_id": inputs[0]["port_id"], "kind": "input",
                  "vertex": seam})
    outputs = [p for p in rec["ports"] if p.get("kind") == "output"]
    if len(outputs) != len(hangers):
        raise BindingRefused(
            "binding_port_ambiguous",
            f"{len(outputs)} output ports cannot bind {len(hangers)} "
            f"hanger rim blocks")
    for p, nid in zip(outputs, hangers):
        if nid not in str(p.get("port_id", "")):
            raise BindingRefused(
                "binding_port_ambiguous",
                f"output port {p['port_id']!r} does not name its hanger "
                f"piece {nid!r}; the binding would be a guess")
        k = hangers.index(nid)
        ports.append({"port_id": p["port_id"], "kind": "output",
                      "vertices": list(rim_blocks[k])})
    return {"regions": regions, "ports": ports, "seam_vertex": seam}


def _compile_piece(rec: dict, scale: float, load_N: float) -> dict:
    node = rec["design_recipe"]["nodes"][0]
    if len(rec["design_recipe"]["nodes"]) != 1 or rec["design_recipe"]["edges"]:
        raise BindingRefused(
            "binding_recipe_unmatched",
            "the single-patch compile path owns ONE node and no edges")
    prm = _merged_params(node)
    fx = fg.high_degree_fan(seed=prm["seed"], n_rim=prm["n_rim"],
                            radius=prm["radius"], height=prm["height"])
    if not fx.stats.valid:
        raise BindingRefused("binding_geometry_refused",
                             "the fixture validator refused the compiled "
                             f"patch: {fx.stats.checks}")
    V = fx.positions.copy()
    if float(scale) != 1.0:
        V = V * float(scale)          # the qualified rigid physical-size law
    n = prm["n_rim"]
    return {"positions": V, "faces": np.asarray(fx.faces, dtype=np.int64),
            "gamma": np.asarray(fx.gamma, dtype=np.float64),
            "pins": list(range(n)), "loads": [(n, _load_vector(load_N))],
            "compile_path": _PIECE_COMPILE_PATH}


def _compile_star(rec: dict, scale: float, load_N: float) -> dict:
    nodes = rec["design_recipe"]["nodes"]
    owner_id = {e["seam_owner"] for e in rec["design_recipe"]["edges"]}.pop()
    ground = [nd for nd in nodes if nd["node_id"] == owner_id][0]
    # The existing compile path owns the ground piece's compiled identity
    # (byte-identical reuse of assembly 1's A is a qualified check); a
    # record claiming different ground parameters has no compile path.
    if _merged_params(ground) != dict(cp.PIECE_A):
        raise BindingRefused(
            "binding_recipe_unmatched",
            f"ground piece {owner_id} params {_merged_params(ground)} are "
            f"not the compile path's qualified ground piece {cp.PIECE_A}")
    hangers = tuple(_merged_params(nd) for nd in nodes
                    if nd["node_id"] != owner_id)
    try:
        star = cc.build_star(scale=float(scale), hangers=hangers,
                             load=_load_vector(load_N))
    except cp.InvalidSurface as ex:      # the compile path's own named law
        raise BindingRefused("binding_geometry_refused",
                             f"{ex.reason}: {ex.message}") from ex
    star["compile_path"] = _STAR_COMPILE_PATH
    return star


def compile_transaction(record_id: str, instance_id: str, *,
                        scale: float, load_N: float) -> dict:
    """Compile ONE qualified record + instance parameters into a compile
    transaction for the EXISTING compile path. Refuses, by name, before any
    world is touched: unqualified records, out-of-measured-domain scale or
    load, ambiguous ports, and any geometry the pinned law refuses."""
    try:
        rec = pr.validate(pr.load_record(record_id))
    except pr.PieceRecordRefused as ex:
        raise BindingRefused("binding_record_refused",
                             f"{ex.reason}: {ex.detail}") from ex
    _qualified_direct_reference(rec)
    if instance_id in {i["instance_id"]
                       for i in rec["instance_state"]["instances"]}:
        raise BindingRefused(
            "binding_instance_exists",
            f"{instance_id} is already owned by {record_id}'s instance "
            "ledger; copy the motif with a NEW instance identity")
    _in_domain(rec, scale, load_N)
    load_N, scale = float(load_N), float(scale)

    kind = rec["kind"]
    if kind == "assembly":
        star = _compile_star(rec, scale, load_N)
        ids = _ids_for_star(rec, star)
    elif kind == "piece":
        star = _compile_piece(rec, scale, load_N)
        ids = {
            "regions": [{"region_id": rec["design_recipe"]["nodes"][0]["node_id"],
                         "vertex_block": list(range(star["positions"].shape[0])),
                         "face_block": list(range(int(np.asarray(star["faces"]).shape[0])))}],
            "ports": [
                {"port_id": _input_port(rec)["port_id"], "kind": "input",
                 "vertex": int(star["loads"][0][0])},
                *({"port_id": p["port_id"], "kind": "output",
                   "vertices": list(star["pins"])}
                  for p in rec["ports"] if p.get("kind") == "output"),
            ],
            "seam_vertex": int(star["loads"][0][0]),
        }
    else:
        raise BindingRefused("binding_recipe_unmatched",
                             f"no compile path owns record kind {kind!r}")

    V = np.asarray(star["positions"], dtype=np.float64)
    F = np.asarray(star["faces"], dtype=np.int64)
    gamma = np.asarray(star["gamma"], dtype=np.float64)
    try:
        ev = evaluate_surface(V, F, gamma)   # the pinned law's own refusals
    except cp.InvalidSurface as ex:
        raise BindingRefused("binding_geometry_refused",
                             f"{ex.reason}: {ex.message}") from ex
    off, cor = build_vertex_corner_adjacency(F, V.shape[0])

    txn = {
        "schema": BINDING_SCHEMA,
        "record_id": record_id,
        "instance_id": instance_id,
        "scale": scale,
        "load_N": load_N,
        "compile_path": star["compile_path"],
        "compiled": {
            "positions_f64": _f64_hex(V),
            "n_vertices": int(V.shape[0]),
            "faces": [[int(a) for a in f] for f in F],
            "gamma": [float(g) for g in gamma],
            "csr_off": [int(o) for o in off],
            "csr_cor": [int(c) for c in cor],
            "pins": [int(i) for i in star["pins"]],
            "loads": [{"vertex": int(v), "f": [float(x) for x in f]}
                      for v, f in star["loads"]],
        },
        "ids": ids,
        "law_reference": {
            "law_revision": rec["physical_definition"]["law_revision"],
            "rest_energy_J": float(ev.energy),
            "units": rec["physical_definition"]["units"],
        },
    }
    txn["transaction_hash"] = _sha256_canonical(
        {k: v for k, v in txn.items() if k != "transaction_hash"})
    return txn


def transaction_hash(txn: dict) -> str:
    return _sha256_canonical(
        {k: v for k, v in txn.items() if k != "transaction_hash"})


def _world(accepted) -> dict:
    if accepted is None or accepted == b"":
        return {"schema": WORLD_SCHEMA, "instances": {}}
    try:
        doc = json.loads(accepted.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as ex:
        raise BindingRefused("binding_world_unreadable", str(ex)) from ex
    if not isinstance(doc, dict) or doc.get("schema") != WORLD_SCHEMA:
        raise BindingRefused(
            "binding_world_schema_unknown",
            f"accepted world is {doc.get('schema')!r}, not {WORLD_SCHEMA!r}")
    return doc


def apply_transaction(accepted, txn: dict) -> bytes:
    """Transactionally compile ONE transaction into the accepted world.

    Returns the NEW accepted-world bytes. Every refusal happens BEFORE the
    new document is built and nothing ever mutates the caller's bytes, so a
    rejected compile leaves the accepted world byte-identical."""
    doc = _world(accepted)
    if not isinstance(txn, dict) or txn.get("schema") != BINDING_SCHEMA:
        raise BindingRefused(
            "binding_transaction_schema_unknown",
            f"transaction schema is {txn.get('schema')!r}")
    if txn.get("transaction_hash") != transaction_hash(txn):
        raise BindingRefused("binding_transaction_hash_mismatch",
                             "the transaction's bytes do not reproduce its "
                             "declared hash")
    iid = txn["instance_id"]
    if iid in doc["instances"]:
        raise BindingRefused("binding_instance_exists",
                             f"{iid} is already compiled into the world")
    # The compile must be reproducible FROM THE RECORD (the recipe is the
    # immutable shared artifact): a self-consistent transaction that the
    # record + compile path no longer produce is stale, never admitted.
    fresh = compile_transaction(txn["record_id"], iid,
                                scale=txn["scale"], load_N=txn["load_N"])
    if fresh["transaction_hash"] != txn["transaction_hash"]:
        raise BindingRefused(
            "binding_transaction_stale",
            "the transaction is not byte-reproducible from the record and "
            "the existing compile path; refusing a silent reconstruction")
    doc["instances"][iid] = {
        "record_id": txn["record_id"],
        "transaction_hash": txn["transaction_hash"],
        "scale": txn["scale"],
        "load_N": txn["load_N"],
        "compiled": txn["compiled"],
        "ids": txn["ids"],
    }
    return _canonical(doc).encode("utf-8")


def restore_world(accepted) -> dict:
    """RESTORE: re-derive every instance from its shared immutable record
    and require byte-identical compiled state and ids. Nothing is silently
    reconstructed under a different law: a drifted record, law or compile
    path refuses the restore by name."""
    doc = _world(accepted)
    for iid, inst in doc["instances"].items():
        fresh = compile_transaction(inst["record_id"], iid,
                                    scale=inst["scale"],
                                    load_N=inst["load_N"])
        if (_canonical(fresh["compiled"]) != _canonical(inst["compiled"])
                or _canonical(fresh["ids"]) != _canonical(inst["ids"])):
            raise BindingRefused(
                "binding_restore_mismatch",
                f"{iid}: the saved compiled state is not reproducible from "
                f"{inst['record_id']} under the pinned law; refusing to "
                "restore a state the record no longer compiles")
    return doc
