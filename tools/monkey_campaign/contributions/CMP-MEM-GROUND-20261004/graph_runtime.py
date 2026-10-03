"""graph_runtime.py -- THE GRAPH-CLASS RUNTIME LAYER of
chimera.membrane_abi.v1 (the declared runtime-class lift).

mathspec lane wk-membrane-abi, Order-17 lift. This module is the NEW stage
BESIDE the frozen bytes (spec_runtime.py is pinned by the delivered modules
and is NEVER edited; the frozen one-connection builder stays exactly as it
is). It generalizes THREE things from the pair class to the declared
membrane-and-port GRAPH (N membranes, M two-member connections, all from
the spec declarations -- no module-name-specific branches anywhere):

1. validate_built_graph -- the ABI built-membrane conformance check with
   PER-CONNECTION WRITER SCOPING. The frozen validate_built checks ONE
   connection's owner against the whole module surface, so it false-positives
   a two-connection member that owns the SECOND connection's record while
   legitimately not owning the first (recorded observation, chain-b lane
   EVIDENCE.md section 3.2). The generalized rule scopes the ONE-writer law
   PER CONNECTION by inspecting what the writer actually PRODUCES:
     - for every connection the membrane OWNS: the module must expose
       exchange_contribution() and it must produce EXACTLY that
       connection's exchange state id;
     - for every connection the membrane does NOT own: the module must not
       produce THAT connection's exchange state id (a writer producing
       several owned records is fine; a writer producing a record the
       module does not own, or an undeclared record, is refused).
   VIOLATION DETECTION IS PRESERVED: a non-owner exposing a writer for a
   record it does not own is still refused by name, and an owner lacking
   its writer is still refused by name.

2. build_contract_groups_graph -- the PORT_CONTRACT_SCHEMA v2 contract for
   the GRAPH: quantities for every declared owned state and EVERY
   connection's exchange quantity, geometry states/vertices/ownership
   assertions for every state, convergence measures per connection
   exchange, accounting heat rows for EVERY declared ledger entry. The
   pinned validator (PORT_CONTRACT_V2.validate_contract_v2) validates the
   result and the caller requires 9/9 coverage -- the same frozen law.

3. Per-connection exchange-quantity accessors: the ABI's singular
   exchange_quantity(view) is unambiguous only for a member of exactly one
   connection; a multi-connection member must expose
   exchange_quantity_for(view, connection_id). exchange_accessor resolves
   the right accessor per (module, connection); validate_built_graph
   refuses a singular-accessor module with more than one membership.

KEPT INVARIANTS (checked by the generated wiring, unchanged law): ONE
signed exchange quantity per connection proven bitwise per window (owner
accessor == other-member accessor == stored record); exactly-once
single-writer store; per-connection paired ledger entries summing to zero
BITWISE; declared refusals in-step; determinism across schedules.

NO PHYSICS CLAIM: interface contract for synthetic teaching mechanisms
declared in chimera.mathspec.spec.v1 documents.
"""
from __future__ import annotations

import math
import pathlib
import sys


def _ensure_path():
    here = pathlib.Path(__file__).resolve().parent
    for p in (str(here), str(here / "pinned_inputs")):
        if p not in sys.path:
            sys.path.insert(0, p)


_ensure_path()

import membrane_abi  # noqa: E402  (THE ABI; this module extends its checks)
import spec_runtime  # noqa: E402  (resolve_ids -- THE ONE id scheme)
from membrane_abi import CombineRefusal  # noqa: E402

# ---------- named refusal codes (the same ABI-layer namespace) -----------------------

E_ABI_MODULE_NOT_CONFORMANT = membrane_abi.E_ABI_MODULE_NOT_CONFORMANT
E_ABI_IDENTITY_MISMATCH = membrane_abi.E_ABI_IDENTITY_MISMATCH
E_ABI_PORT_CONTRACT_MISMATCH = membrane_abi.E_ABI_PORT_CONTRACT_MISMATCH
E_ABI_OWNERSHIP_CONTRACT_MISMATCH = \
    membrane_abi.E_ABI_OWNERSHIP_CONTRACT_MISMATCH
E_ABI_EXCHANGE_WRITER_VIOLATION = membrane_abi.E_ABI_EXCHANGE_WRITER_VIOLATION


# ---------- shared spec helpers -------------------------------------------------------

def _section(spec: dict, membrane_id: str) -> dict:
    for m in spec.get("membranes") or []:
        if m.get("membrane_id") == membrane_id:
            return m
    raise CombineRefusal("spec_validation_failed", {
        "law": "the spec does not declare this membrane",
        "membrane_id": membrane_id})


def _member_connections(spec: dict, membrane_id: str) -> list:
    return [c for c in spec.get("connections") or []
            if membrane_id in (c.get("members") or [])]


def _expected_ownership(spec: dict, membrane_id: str) -> list:
    state_ids, _owner, _ex = spec_runtime.resolve_ids(spec)
    section = _section(spec, membrane_id)
    return [{"var": st["var"], "unit": st["unit"],
             "state_id": state_ids[(membrane_id, st["var"])]}
            for st in section.get("owned_state") or []]


def _ports_normalized(ports: dict) -> dict:
    out = {}
    for direction in ("inputs", "outputs"):
        rows = sorted(
            ({"port_id": p.get("port_id"),
              "quantity_ref": p.get("quantity_ref"),
              "unit": p.get("unit"),
              "connection_ref": p.get("connection_ref")}
             for p in (ports or {}).get(direction) or []),
            key=lambda r: (str(r.get("port_id")),
                           str(r.get("quantity_ref"))))
        out[direction] = rows
    return out


# ---------- the per-connection writer scoping ------------------------------------------

def _writer_produces(membrane) -> tuple:
    """The exchange-state ids the module's writer produces (empty when the
    module exposes no writer). Calling exchange_contribution() is PURE: it
    constructs a pinned Contribution record."""
    fn = getattr(membrane, "exchange_contribution", None)
    if not callable(fn):
        return ()
    contribution = fn()
    produces = getattr(contribution, "produces", None) or []
    return tuple(produces)


def validate_built_graph(membrane, spec: dict, membrane_id: str) -> dict:
    """The generalized built-membrane conformance check: state ownership,
    typed ports with units, the per-connection exchange-quantity accessors
    and the PER-CONNECTION writer scoping of the ONE-writer law. Refuses by
    name; never repairs."""
    got_id = getattr(membrane, "membrane_id", None)
    if got_id != membrane_id:
        raise CombineRefusal(E_ABI_IDENTITY_MISMATCH, {
            "built": got_id, "expected": membrane_id})
    section = _section(spec, membrane_id)
    _state_ids, _owner, exchange_state_ids = spec_runtime.resolve_ids(spec)

    # -- ownership (identical law to the frozen check) -------------------------
    own = getattr(membrane, "ownership", None)
    if not callable(own):
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "membrane_id": membrane_id, "missing": "ownership()"})
    ownership = own()
    expected_rows = _expected_ownership(spec, membrane_id)
    got_rows = [dict(r) for r in (ownership or {}).get("owned_states") or []]
    if got_rows != expected_rows:
        raise CombineRefusal(E_ABI_OWNERSHIP_CONTRACT_MISMATCH, {
            "membrane_id": membrane_id, "expected": expected_rows,
            "declared": got_rows,
            "law": "the ABI ownership declaration must equal the spec "
                   "section's owned states under the ONE deterministic id "
                   "scheme"})
    if (ownership or {}).get("membrane_id") != membrane_id:
        raise CombineRefusal(E_ABI_OWNERSHIP_CONTRACT_MISMATCH, {
            "membrane_id": membrane_id,
            "declared": (ownership or {}).get("membrane_id")})

    # -- typed ports with units (identical law) ---------------------------------
    ports_fn = getattr(membrane, "ports", None)
    if not callable(ports_fn):
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "membrane_id": membrane_id, "missing": "ports()"})
    expected_ports = _ports_normalized(section.get("ports") or {})
    got_ports = _ports_normalized(ports_fn())
    if got_ports != expected_ports:
        raise CombineRefusal(E_ABI_PORT_CONTRACT_MISMATCH, {
            "membrane_id": membrane_id, "expected": expected_ports,
            "declared": got_ports,
            "law": "the ABI port declaration must equal the spec section's "
                   "typed ports (an INPUT carries the connection's exchange "
                   "quantity with the exchange's unit; an OUTPUT carries the "
                   "membrane's own published state)"})

    # -- per-connection memberships and accessor resolution ---------------------
    member_conns = _member_connections(spec, membrane_id)
    if not member_conns:
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "membrane_id": membrane_id,
            "law": "the module's membrane is a member of no connection"})
    has_pcs = callable(getattr(membrane, "exchange_quantity_for", None))
    has_singular = callable(getattr(membrane, "exchange_quantity", None))
    if not has_singular and not has_pcs:
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "membrane_id": membrane_id,
            "missing": "exchange_quantity(view) [or the per-connection "
                       "exchange_quantity_for(view, connection_id)]"})
    if len(member_conns) > 1 and not has_pcs:
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "membrane_id": membrane_id,
            "memberships": len(member_conns),
            "law": "the singular exchange_quantity(view) is unambiguous "
                   "only for a member of exactly one connection; a "
                   "multi-connection member must expose "
                   "exchange_quantity_for(view, connection_id)"})
    if not callable(getattr(membrane, "contribution", None)):
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "membrane_id": membrane_id, "missing": "contribution()"})

    # -- PER-CONNECTION writer scoping of the ONE-writer law ---------------------
    produces = _writer_produces(membrane)
    declared_xsids = set(exchange_state_ids.values())
    unknown = sorted(set(produces) - declared_xsids)
    if unknown:
        raise CombineRefusal(E_ABI_EXCHANGE_WRITER_VIOLATION, {
            "membrane_id": membrane_id, "undeclared_records": unknown,
            "law": "an exchange writer must produce DECLARED exchange "
                   "records only"})
    scoped = []
    for conn in member_conns:
        cid = conn["connection_id"]
        owner = (conn.get("exchange") or {}).get("owner_membrane")
        xsid = exchange_state_ids[cid]
        if membrane_id == owner:
            if xsid not in produces:
                raise CombineRefusal(E_ABI_EXCHANGE_WRITER_VIOLATION, {
                    "membrane_id": membrane_id, "connection_id": cid,
                    "expected_record": xsid,
                    "writer_produces": list(produces),
                    "law": "the exchange-record OWNER must expose a writer "
                           "that produces EXACTLY its connection's record"})
            scoped.append({"connection_id": cid, "role": "owner",
                           "record": xsid, "satisfied": True})
        else:
            if xsid in produces:
                raise CombineRefusal(E_ABI_EXCHANGE_WRITER_VIOLATION, {
                    "membrane_id": membrane_id, "connection_id": cid,
                    "record": xsid, "writer_produces": list(produces),
                    "exchange_owner": owner,
                    "law": "the ONE-writer law PER CONNECTION: a member that "
                           "does not own a connection's record must not "
                           "produce it (a writer for ANOTHER connection it "
                           "owns is legitimate)"})
            scoped.append({"connection_id": cid, "role": "consumer",
                           "record": xsid, "satisfied": True})

    return {"conformant": True, "membrane_id": membrane_id,
            "memberships": [c["connection_id"] for c in member_conns],
            "writer_scoping": scoped,
            "writer_produces": list(produces),
            "owned_states": expected_rows}


# ---------- per-connection exchange accessors -------------------------------------------

def exchange_accessor(membrane, connection_id: str):
    """Resolve the per-connection accessor for ONE (module, connection):
    exchange_quantity_for(view, connection_id) when exposed, else the
    singular exchange_quantity(view) (unambiguous single-membership
    modules -- enforced by validate_built_graph)."""
    pcs = getattr(membrane, "exchange_quantity_for", None)
    if callable(pcs):
        def accessor(view, _pcs=pcs, _cid=connection_id):
            return _pcs(view, _cid)
        return accessor
    singular = getattr(membrane, "exchange_quantity", None)
    if callable(singular):
        return singular
    raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
        "law": "no exchange-quantity accessor on the built membrane",
        "membrane_id": getattr(membrane, "membrane_id", None)})


# ---------- the graph v2 contract groups -------------------------------------------------

def build_contract_groups_graph(spec: dict, spec_sha256: str, state_ids: dict,
                                state_owner: dict, exchange_state_ids: dict,
                                dt: float) -> dict:
    """PORT_CONTRACT_SCHEMA v2 groups for the DECLARED GRAPH (N membranes,
    M two-member connections). Generated from the spec (no hand math);
    validated 9/9 by the pinned validator by the caller. The M==1 output
    carries the same behavioral content as the frozen pair builder."""
    asm = spec.get("assembly") or {}
    numerics = spec.get("numerics") or {}
    conns = spec["connections"]
    frame_id = f"frame.{spec_runtime._tag(asm.get('assembly_id', 'assembly'))}.v1"
    quantities = []
    for m in spec["membranes"]:
        mid = m["membrane_id"]
        for st in m.get("owned_state") or []:
            quantities.append({
                "quantity_id": st["var"], "unit": st["unit"],
                "frame_ref": frame_id,
                "sign_convention":
                    f"absolute thermodynamic state of {mid}; observer output",
                "time_level": "t_n_plus_1", "status": "accepted",
                "owner_membrane": mid})
    for conn in conns:
        ex = conn["exchange"]
        quantities.append({
            "quantity_id": ex["quantity_ref"], "unit": ex["unit"],
            "frame_ref": frame_id,
            "sign_convention": ex["sign_convention"],
            "time_level": "t_n_plus_1", "status": "accepted",
            "owner_membrane": ex["owner_membrane"]})
    states = []
    vertices = []
    assertions = []
    for m in spec["membranes"]:
        mid = m["membrane_id"]
        for st in m.get("owned_state") or []:
            sid = state_ids[(mid, st["var"])]
            states.append({"state_id": sid, "quantity_ref": st["var"],
                           "unit": st["unit"], "owner_membrane": mid})
            vertices.append({"vertex_id":
                             f"v.{st['var']}.{spec_runtime._tag(mid)}",
                             "frame_ref": frame_id, "state_ref": sid,
                             "owner_membrane": mid})
            assertions.append({
                "assertion_id":
                    f"oa.state.{st['var']}.{spec_runtime._tag(mid)}",
                "kind": "unique_state_reference",
                "subject":
                    f"vertex:v.{st['var']}.{spec_runtime._tag(mid)}.state",
                "owner_membrane": mid, "scope": "state", "via": "owns"})
            assertions.append({
                "assertion_id":
                    f"oa.energy.{st['var']}.{spec_runtime._tag(mid)}",
                "kind": "no_duplicate_energy",
                "subject": f"membrane:{mid}.internal_energy",
                "owner_membrane": mid, "scope": "matter", "via": "owns"})
    for conn in conns:
        cid = conn["connection_id"]
        ex = conn["exchange"]
        qref = ex["quantity_ref"]
        xsid = exchange_state_ids[cid]
        states.append({"state_id": xsid, "quantity_ref": qref,
                       "unit": ex["unit"],
                       "owner_membrane": ex["owner_membrane"]})
        vertices.append({"vertex_id":
                         f"v.{qref}.{spec_runtime._conn_tag(cid)}",
                         "frame_ref": frame_id, "state_ref": xsid,
                         "owner_membrane": ex["owner_membrane"]})
        assertions.append({
            "assertion_id":
                f"oa.exchange.{qref}.{spec_runtime._conn_tag(cid)}",
            "kind": "unique_state_reference",
            "subject":
                f"vertex:v.{qref}.{spec_runtime._conn_tag(cid)}.state",
            "owner_membrane": ex["owner_membrane"], "scope": "state",
            "via": "owns"})
    horizon = float(numerics.get("horizon_s") or 0)
    max_windows = int(math.ceil(horizon / dt)) + 1 if horizon > 0 else 1
    heat_rows = []
    for conn in conns:
        for row in conn["transfer_law"]["per_membrane"]:
            heat_rows.append(
                dict(row["ledger_entry"],
                     quantity_ref=conn["exchange"]["quantity_ref"],
                     time_level="t_n_plus_1",
                     balance="the paired transfer entries of THIS connection "
                             "sum to EXACTLY zero (equal-and-opposite, "
                             "applied exactly once); energy = power * "
                             "window dt"))
    measures = []
    for conn in conns:
        qref = conn["exchange"]["quantity_ref"]
        measures.append({
            "measure_id": f"m.abs.{qref}", "quantity_ref": qref,
            "kind": "absolute", "norm": "linf", "limit": 1e-12,
            "suffices": False,
            "note": "dormant under explicit synchronization (no "
                    "iterations); declares the exchange-balance intent"})
    transfers_statement = "; ".join(
        f"{c['connection_id']} transfers energy (connects)" for c in conns)
    groups = {
        "contract_version": "2.0.0",
        "frames": [{
            "frame_id": frame_id, "units_length": "m",
            "axes_or_anchor": "scalar lumped thermal assembly frame; no "
                              "spatial extent; temperatures are absolute K; "
                              "generated from " + spec["spec_id"],
        }],
        "quantities": quantities,
        "geometry": {
            "binding": {
                "store_path": "mathspec/spec/" + spec["spec_id"] + ".json",
                "sha256": spec_sha256,
                "class": "AUTHORED_DECLARED",
                "value_source": "the executable spec document is the "
                                "geometry of record for the lumped scalar "
                                "assembly (no mesh; synthetic provenance "
                                "declared in the spec)",
            },
            "states": states,
            "vertices": vertices,
            "triangles": [],
            "ownership_assertions": assertions,
        },
        "coupling": {
            "synchronization": "explicit",
            "substeps": {"min_per_window": 1, "max_per_window": 1,
                         "rule": "one declared Euler step per window "
                                 "(numerics.method explicit_euler, dt_s "
                                 f"{dt} s)"},
            "time_window": {"size": dt, "unit": "s",
                            "max_windows": max_windows},
            "exchange_points": ["window_end"],
            "checkpoint": {
                "required": True,
                "fields": sorted(state_owner),
                "restore_rule": "the pinned store restores the window-start "
                                "snapshot on any refusal; statuses return "
                                "to predicted",
                "cadence": "every_window",
            },
        },
        "convergence": {
            "measures": measures,
            "max_iterations": 1,
            "min_iterations": 1,
            "evaluating_membrane": conns[0]["exchange"]["owner_membrane"],
            "failure_behavior": {
                "on_non_convergence": "abort_run",
                "detail": "explicit synchronization never iterates; this "
                          "path cannot fire and must never silently accept",
            },
        },
        "accounting": {
            "work": [],
            "work_absent_reason": "no mechanical work channel exists in "
                                  "the lumped thermal class; work accounting "
                                  "is named-absent, not zero",
            "heat": heat_rows,
            "reaction": [],
            "reaction_absent_reason": "no momentum channel exists in the "
                                      "lumped thermal class",
        },
        "relationship_law": {
            "containment_edge": "contains",
            "physical_connection_edge": "connects",
            "dependency_edge": "depends_on",
            "ownership_edge": "owns",
            "transfer_only_via": "connects",
            "statement": "the assembly contains all member membranes "
                         "(contains); " + transfers_statement + "; tooling "
                         "depends on the spec (depends_on); each membrane "
                         "owns its own states and each connection's exchange "
                         "record rides its declared owner membrane (owns); "
                         "the four stay distinct",
        },
    }
    return groups
