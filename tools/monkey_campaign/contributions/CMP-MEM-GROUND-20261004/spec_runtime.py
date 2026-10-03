"""spec_runtime.py -- binds an EXECUTABLE MATHEMATICAL SPEC to the REAL
frozen runtime (pinned combine_core + pinned PORT_CONTRACT_V2).

mathspec lane wk-mathspec-core, phase 1. This module contains NO membrane
math of its own: every equation is compiled from the spec document's
restricted-language expressions by spec_lang (AST walker, never eval/exec),
and every state mutation is routed through the pinned combine_core owner
store. The assembly law lives here:

  - the connection computes ONE signed exchange quantity: the exchange AST is
    compiled EXACTLY ONCE per connection; every consumer (membrane
    evolution scopes, the exchange state record, the ledger value
    expressions) references THE SAME compiled closure (identity asserted);
  - the assembly applies the equal-and-opposite transfers EXACTLY ONCE per
    window: each member membrane owns exactly one integrate contribution
    writing its OWN state; the pinned runtime refuses any second writer and
    any non-owner write;
  - power vs energy over the window is EXPLICIT: the exchange quantity is a
    POWER (W); the applied transfer and the ledger entries are ENERGY over
    the window (J = W * dt), declared in the spec, never implicit.

Defect hooks: build_assembly(..., defect=<declared id>) exists ONLY for
qualification check 8 (deliberate defects must fail named checks). The
production path always uses defect=None; an unknown defect id is refused.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_PIN = _HERE / "pinned_inputs"
for _p in (str(_HERE), str(_PIN)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import combine_core  # noqa: E402  (pinned byte-exact; drift-refused below)
import combine_core as _cc
import PORT_CONTRACT_V2  # noqa: E402  (pinned byte-exact)

import spec_format  # noqa: E402
import spec_lang  # noqa: E402
from spec_lang import ExprRefusal, parse, evaluate  # noqa: E402
from combine_core import (CombineRefusal, CombineScheduler, Contribution,  # noqa: E402
                          verify_pins)

# ---------- named refusal codes ---------------------------------------------------

E_PIN_DRIFT = "spec_pinned_input_drift"
E_SPEC_INVALID = "spec_validation_failed"
E_SPEC_HASH_MISSING = "spec_hash_missing"
E_CONTRACT_NOT_COVERED = "spec_contract_not_fully_covered"
E_CONTRACT_INVALID = "spec_contract_invalid"
E_UNKNOWN_INITIAL_CASE = "spec_unknown_initial_case"
E_UNKNOWN_DEFECT = "spec_unknown_defect"
E_BINDINGS_MISMATCH = "spec_bindings_mismatch"
E_BINDINGS_NOT_REFERENCE_ONLY = "spec_bindings_not_reference_only"
E_SPEC_DT_NOT_ADMISSIBLE = "spec_dt_not_admissible"
E_ANALYTIC_CLASS_UNKNOWN = "harness_analytic_reference_class_unknown"
E_STABILITY_BOUND = "harness_stability_bound_violated"
E_WINDOW_INPUTS_FORBIDDEN = "spec_window_inputs_forbidden"

# byte-exact pins of the frozen runtime this lane extends (never forked).
PINS = {
    "pinned_inputs/combine_core.py":
        "8bfe6949b6854341801106649423c100201c2ed7989c09e3aed0af3f4c860712",
    "pinned_inputs/PORT_CONTRACT_V2.py":
        "0f1b7dfec2a7335bdf99dd4e8f2f58e395fd179d1e2c2d2b88975dbceee0b29d",
    "pinned_inputs/port_contract_schema.v2.json":
        "69161d32229a69f89b30bca27c95221b1d04e485f17972e96d0ed1a905c9a623",
}

DEFECT_IDS = ("sign_flip_transfer_b", "double_apply_transfer_a",
              "exchange_constant_bias")

# the declared deliberate physics defect size (qualification check 8): a
# constant exchange bias of 1.0 W shifts the equilibrium by bias/k = 2 K and
# the nominal checkpoints by >= 0.4 K -- comfortably outside the declared
# 0.25 K linf tolerance, so the analytic gate MUST catch it while the paired
# ledger conservation stays bitwise-exact.
DEFECT_BIAS_W = 1.0

SUPPORTED_ANALYTIC_CLASSES = ("two_body_linear_newton_cooling",)


def require_pins() -> None:
    """Drift-refuse the pinned frozen runtime BEFORE anything runs."""
    verify_pins(PINS)


def canonical(value) -> str:
    return _cc.canonical(value)


def state_hash(value) -> str:
    return _cc.state_hash(value)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(t: str) -> str:
    return sha256_bytes(t.encode("utf-8"))


def _tag(membrane_id: str) -> str:
    """membrane.thermal_a.v1 -> thermal_a (deterministic id compaction)."""
    parts = membrane_id.split(".")
    if len(parts) >= 3 and parts[0] == "membrane" and parts[-1] == "v1":
        return ".".join(parts[1:-1])
    return membrane_id.replace(".", "_")


def _conn_tag(connection_id: str) -> str:
    parts = connection_id.split(".")
    if len(parts) >= 3 and parts[0] == "conn" and parts[-1] == "v1":
        return ".".join(parts[1:-1])
    return connection_id.replace(".", "_")


def resolve_ids(spec: dict) -> tuple[dict, dict, dict]:
    """The DETERMINISTIC id scheme shared by the runtime and the generator:
    state ids, owners and exchange-state ids are derived from the spec ids
    only. One authority; the generated bindings reuse these tables."""
    state_ids: dict = {}
    state_owner: dict = {}
    exchange_state_ids: dict = {}
    for m in spec.get("membranes") or []:
        mid = m["membrane_id"]
        for st in m.get("owned_state") or []:
            sid = f"state.{st['var']}.{_tag(mid)}.v1"
            state_ids[(mid, st["var"])] = sid
            state_owner[sid] = mid
    for c in spec.get("connections") or []:
        ex = c["exchange"]
        exchange_state_ids[c["connection_id"]] = \
            f"state.{ex['quantity_ref']}.{_conn_tag(c['connection_id'])}.v1"
    return state_ids, state_owner, exchange_state_ids


class Assembly:
    """A built assembly: pinned scheduler + compiled spec + resolution."""

    def __init__(self, spec: dict, spec_sha256: str, report, contract: dict,
                 decl: dict, scheduler: CombineScheduler, state_ids: dict,
                 exchange_state_ids: dict, dt: float, window_index: int = 0):
        self.spec = spec
        self.spec_sha256 = spec_sha256
        self.report = report
        self.contract = contract
        self.decl = decl
        self.scheduler = scheduler
        self.state_ids = dict(state_ids)          # (mid, var) -> state_id
        self.exchange_state_ids = dict(exchange_state_ids)  # cid -> state_id
        self.dt = dt
        self.window_index = window_index

    # -- stepping ------------------------------------------------------------------
    def step(self) -> dict:
        """One window = one declared Euler step of size dt. Window inputs are
        forbidden by construction (the assembly has no hidden inputs). The
        window-start values are snapshotted BEFORE the window so the
        applied-vs-booked energy law is auditable."""
        self.last_window_start = self.scheduler.store.values()
        result = self.scheduler.run_window({})
        self.window_index += 1
        return result

    def run_to(self, t_s: float) -> dict:
        last = None
        target = round(t_s / self.dt)
        while self.window_index < target:
            last = self.step()
        return last or {"values": self.scheduler.store.values(),
                        "state_hash": self.scheduler.store.hash()}

    def values(self) -> dict:
        return self.scheduler.store.values()

    def state_value(self, mid: str, var: str) -> float:
        return self.scheduler.store.read(self.state_ids[(mid, var)])

    def exchange_value(self, cid: str) -> float:
        return self.scheduler.store.read(self.exchange_state_ids[cid])

    def conserved_value(self) -> float:
        """The declared conserved quantity, evaluated from the CURRENT store
        through the same compiled AST (spec values + parameters only)."""
        cq = (self.spec.get("assembly") or {}).get("conserved_quantity") or {}
        scope = self._conserved_scope()
        return float(evaluate(self._conserved_ast, scope))

    @property
    def _conserved_ast(self):
        cached = getattr(self, "_conserved_ast_cache", None)
        if cached is None:
            cq = (self.spec.get("assembly") or {}
                  ).get("conserved_quantity") or {}
            cached = parse(cq.get("expr", ""))
            self._conserved_ast_cache = cached
        return cached

    def _conserved_scope(self) -> dict:
        scope = dict(self.parameters_flat)
        for (mid, var), sid in self.state_ids.items():
            scope[var] = self.scheduler.store.read(sid)
        return scope

    @property
    def parameters_flat(self) -> dict:
        cached = getattr(self, "_params_flat_cache", None)
        if cached is None:
            flat = {}
            for (owner, var), value in self.report.param_values.items():
                flat[var] = value
            cached = flat
            self._params_flat_cache = cached
        return cached


def build_assembly(spec: dict, spec_sha256: str,
                   initial_case_id: str = "nominal",
                   max_workers: int = 4, interleave_seed: int | None = None,
                   defect: str | None = None,
                   dt_override: float | None = None) -> Assembly:
    """Validate the spec, generate the v2 contract instance, compile every
    expression once, and build the pinned CombineScheduler. Refuses by name
    on ANY invalid input; never repairs. dt_override must be a value from
    the spec's DECLARED admissibility table (the harness may not invent
    timesteps)."""
    require_pins()
    if not spec_sha256:
        raise CombineRefusal(E_SPEC_HASH_MISSING,
                             {"law": "the spec bytes hash binds geometry "
                                     "and generation; it is mandatory"})
    conns = spec.get("connections") or []
    if len(conns) != 1:
        raise CombineRefusal(E_SPEC_INVALID, {
            "law": "phase 1 binds EXACTLY ONE connection (the first "
                   "supported class: two ODE membranes, one energy-transfer "
                   "port)", "declared": len(conns)})
    for m in spec.get("membranes") or []:
        if len(m.get("owned_state") or []) != 1:
            raise CombineRefusal(E_SPEC_INVALID, {
                "law": "phase 1 binds EXACTLY ONE owned state per membrane",
                "membrane_id": m.get("membrane_id"),
                "owned": len(m.get("owned_state") or [])})
    report = spec_format.validate_spec(spec)
    if not report.valid:
        raise CombineRefusal(E_SPEC_INVALID, {"errors": report.errors})

    numerics = spec.get("numerics") or {}
    dt = float(numerics["dt_s"])
    if dt_override is not None:
        admissible = [float(row["dt_s"])
                      for row in numerics.get("admissibility") or []]
        if float(dt_override) not in admissible:
            raise CombineRefusal(E_SPEC_DT_NOT_ADMISSIBLE, {
                "requested_dt": dt_override, "admissible": sorted(admissible),
                "law": "only DECLARED admissible timesteps may be run"})
        dt = float(dt_override)

    case = next((c for c in (spec.get("assembly") or {})
                 .get("initial_states") or []
                 if c.get("case_id") == initial_case_id), None)
    if case is None:
        raise CombineRefusal(E_UNKNOWN_INITIAL_CASE, {
            "case_id": initial_case_id,
            "declared": sorted(c.get("case_id")
                               for c in (spec.get("assembly") or {})
                               .get("initial_states") or [])})
    if defect is not None and defect not in DEFECT_IDS:
        raise CombineRefusal(E_UNKNOWN_DEFECT,
                             {"defect": defect, "allowed": list(DEFECT_IDS)})

    # ---- state id resolution (the ONE deterministic scheme) ----------------------
    state_ids, state_owner, exchange_state_ids = resolve_ids(spec)
    initial_values: dict = {}
    for m in spec.get("membranes") or []:
        mid = m["membrane_id"]
        for st in m.get("owned_state") or []:
            initial_values[state_ids[(mid, st["var"])]] = \
                float(case["values"][st["var"]])

    # ---- compile the connection exchange closure EXACTLY ONCE --------------------
    exchange_closures: dict = {}   # cid -> (qref, closure(view_scope))
    exchange_state_ids: dict = {}
    conn_params: dict = {}
    exchange_asts: dict = {}
    for c in spec.get("connections") or []:
        cid = c["connection_id"]
        ex = c["exchange"]
        qref = ex["quantity_ref"]
        ex_scope = {}
        for cons in c.get("consumed") or []:
            fmid, qv = cons["from_membrane"], cons["quantity_ref"]
            ex_scope[qv] = None  # value injected per window from the view
        for p in c.get("parameters") or []:
            conn_params[(cid, p["var"])] = float(p["value"])
            ex_scope[p["var"]] = float(p["value"])
        exchange_asts[cid] = parse(ex["expr"])

        def make_exchange(ast, scope_template, qref=qref):
            def exchange(view_scope: dict) -> float:
                scope = dict(scope_template)
                scope.update(view_scope)
                return float(evaluate(ast, scope))
            return exchange

        exchange_closures[cid] = (qref, make_exchange(exchange_asts[cid],
                                                      ex_scope))
        exchange_state_ids[cid] = \
            f"state.{qref}.{_conn_tag(cid)}.v1"
    assert exchange_state_ids == resolve_ids(spec)[2]

    qref0 = exchange_closures[spec["connections"][0]["connection_id"]][0]

    # one defect hook: a constant bias injected into the SHARED exchange
    # closure (defect d3: conservation stays bitwise-exact, the analytic
    # gate must catch the physics defect).
    bias = DEFECT_BIAS_W if defect == "exchange_constant_bias" else 0.0

    def q_value(cid: str, view: dict) -> float:
        qref, closure = exchange_closures[cid]
        view_scope = {}
        for cons in next(c for c in spec["connections"]
                         if c["connection_id"] == cid)["consumed"]:
            view_scope[cons["quantity_ref"]] = \
                view[state_ids[(cons["from_membrane"],
                                cons["quantity_ref"])]]
        return closure(view_scope) + bias

    # ---- contributions --------------------------------------------------------------
    contributions = []
    closure_ids = {}
    for m in spec.get("membranes") or []:
        mid = m["membrane_id"]
        own_vars = [st["var"] for st in m.get("owned_state") or []]
        params = {p["var"]: float(p["value"]) for p in
                  (m.get("parameters") or [])}
        evo = {e["target"]: parse(e["expr"]) for e in m.get("evolution") or []}

        # the transfer row of THIS membrane under each connection
        rows = []
        for c in spec["connections"]:
            cid = c["connection_id"]
            for row in c["transfer_law"]["per_membrane"]:
                if row["membrane_id"] == mid:
                    rows.append((cid, row))
        ledger_asts = [(cid, row, parse(row["ledger_entry"]["value_expr"]))
                       for cid, row in rows]

        def make_compute(mid=mid, own_vars=own_vars, params=params,
                         evo=evo, ledger_asts=ledger_asts):
            def compute(view, ctx):
                scope = dict(params)
                for var in own_vars:
                    scope[var] = view[state_ids[(mid, var)]]
                for cid, _row, _last in ledger_asts:
                    scope[qref0] = q_value(cid, view)
                scope["dt"] = dt
                states = {}
                sid = state_ids[(mid, own_vars[0])]
                old = view[sid]
                rhs = float(evaluate(evo[own_vars[0]], scope))
                new = old + dt * rhs
                if defect == "double_apply_transfer_a" and mid == \
                        spec["connections"][0]["transfer_law"][
                            "per_membrane"][0]["membrane_id"]:
                    new = new + dt * float(evaluate(evo[own_vars[0]], scope))
                states[sid] = new
                ledger = []
                for cid, row, last in ledger_asts:
                    lscope = {"dt": dt, qref0: scope[qref0]}
                    value = float(evaluate(last, lscope))
                    if defect == "sign_flip_transfer_b" and \
                            row["ledger_entry"]["entry_id"].endswith("into_b"):
                        value = -value
                    entry = dict(row["ledger_entry"])
                    entry["value"] = value
                    entry["iteration"] = ctx.iteration
                    entry.pop("value_expr", None)
                    ledger.append(entry)
                return {"states": states, "ledger": ledger}
            return compute

        closure_ids[mid] = id(make_compute)
        contributions.append(Contribution(
            f"contribution.{_tag(mid)}.integrate", mid,
            [state_ids[(mid, own_vars[0])]], make_compute()))

    for c in spec["connections"]:
        cid = c["connection_id"]
        owner = c["exchange"]["owner_membrane"]
        sid = exchange_state_ids[cid]

        def make_conn(cid=cid, owner=owner, sid=sid):
            def compute(view, ctx):
                return {"states": {sid: q_value(cid, view)}, "ledger": []}
            return compute

        contributions.append(Contribution(
            f"contribution.{_conn_tag(cid)}.exchange", owner, [sid],
            make_conn()))

    # ---- v2 contract + declaration (generated shape, pinned validator) ------------
    decl = {"membranes": [{"membrane_id": m["membrane_id"]}
                          for m in spec["membranes"]]}
    contract = build_contract_groups(spec, spec_sha256, state_ids,
                                     state_owner, exchange_state_ids, dt)
    vreport = PORT_CONTRACT_V2.validate_contract_v2(contract, decl)
    coverage = sum(1 for row in vreport["coverage"] if row["covered"])
    if not vreport["valid"] or vreport["schema_major"] != 2:
        raise CombineRefusal(E_CONTRACT_INVALID,
                             {"errors": vreport["errors"]})
    if coverage != 9:
        raise CombineRefusal(E_CONTRACT_NOT_COVERED,
                             {"law": "the runtime instance covers 9/9 v2 "
                                     "additions", "coverage": coverage})

    scheduler = CombineScheduler(contract, decl, contributions,
                                 max_workers=max_workers,
                                 interleave_seed=interleave_seed,
                                 initial_values=initial_values)
    asm = Assembly(spec, spec_sha256, report, contract, decl, scheduler,
                   state_ids, exchange_state_ids, dt)
    asm._q_value = q_value  # the ONE exchange closure path, for identity checks
    asm.exchange_closure_ids = {cid: id(exchange_closures[cid][1])
                                for cid in exchange_closures}
    return asm


# ---------- the generated-shape v2 contract groups -----------------------------------

def build_contract_groups(spec: dict, spec_sha256: str, state_ids: dict,
                          state_owner: dict, exchange_state_ids: dict,
                          dt: float) -> dict:
    """PORT_CONTRACT_SCHEMA v2 groups for the thermal connection. Generated
    from the spec (no hand math); validated 9/9 by the pinned validator."""
    asm = spec.get("assembly") or {}
    numerics = spec.get("numerics") or {}
    conn = spec["connections"][0]
    cid = conn["connection_id"]
    ex = conn["exchange"]
    qref = ex["quantity_ref"]
    members = conn["members"]
    frame_id = f"frame.{_tag(asm.get('assembly_id', 'assembly'))}.v1"
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
    quantities.append({
        "quantity_id": qref, "unit": ex["unit"], "frame_ref": frame_id,
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
            vertices.append({"vertex_id": f"v.{st['var']}.{_tag(mid)}",
                             "frame_ref": frame_id, "state_ref": sid,
                             "owner_membrane": mid})
            assertions.append({
                "assertion_id": f"oa.state.{st['var']}.{_tag(mid)}",
                "kind": "unique_state_reference",
                "subject": f"vertex:v.{st['var']}.{_tag(mid)}.state",
                "owner_membrane": mid, "scope": "state", "via": "owns"})
            assertions.append({
                "assertion_id": f"oa.energy.{st['var']}.{_tag(mid)}",
                "kind": "no_duplicate_energy",
                "subject": f"membrane:{mid}.internal_energy",
                "owner_membrane": mid, "scope": "matter", "via": "owns"})
    xsid = exchange_state_ids[cid]
    states.append({"state_id": xsid, "quantity_ref": qref,
                   "unit": ex["unit"], "owner_membrane": ex["owner_membrane"]})
    vertices.append({"vertex_id": f"v.{qref}.{_conn_tag(cid)}",
                     "frame_ref": frame_id, "state_ref": xsid,
                     "owner_membrane": ex["owner_membrane"]})
    assertions.append({
        "assertion_id": f"oa.exchange.{qref}.{_conn_tag(cid)}",
        "kind": "unique_state_reference",
        "subject": f"vertex:v.{qref}.{_conn_tag(cid)}.state",
        "owner_membrane": ex["owner_membrane"], "scope": "state",
        "via": "owns"})
    horizon = float(numerics.get("horizon_s") or 0)
    max_windows = int(math.ceil(horizon / dt)) + 1 if horizon > 0 else 1
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
            "measures": [{
                "measure_id": f"m.abs.{qref}", "quantity_ref": qref,
                "kind": "absolute", "norm": "linf", "limit": 1e-12,
                "suffices": False,
                "note": "dormant under explicit synchronization (no "
                        "iterations); declares the exchange-balance intent",
            }],
            "max_iterations": 1,
            "min_iterations": 1,
            "evaluating_membrane": ex["owner_membrane"],
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
            "heat": [
                dict(row["ledger_entry"],
                     quantity_ref=qref, time_level="t_n_plus_1",
                     balance="the paired transfer entries sum to EXACTLY "
                             "zero (equal-and-opposite, applied exactly "
                             "once); energy = power * window dt")
                for row in conn["transfer_law"]["per_membrane"]
            ],
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
            "statement": "the assembly contains both membranes (contains); "
                         f"{cid} transfers energy (connects); tooling "
                         "depends on the spec (depends_on); each membrane "
                         "owns its own temperature and the exchange record "
                         f"rides {ex['owner_membrane']} (owns); the four "
                         "stay distinct",
        },
    }
    return groups


# ---------- generated bindings (reference-only) + the bindings gate ------------------

def build_bindings(spec: dict, spec_raw_sha256: str,
                   spec_canonical_sha256: str) -> dict:
    """The RESOLVED BINDINGS table the generator emits. Reference-only by
    law: it carries IDENTIFIERS (resolved at generation time through the
    same deterministic scheme as the runtime), never formulas. Any formula
    here would be a second source of mathematical truth, so the shape
    refuses it."""
    state_ids, state_owner, exchange_state_ids = resolve_ids(spec)
    states = []
    for m in spec.get("membranes") or []:
        mid = m["membrane_id"]
        for st in m.get("owned_state") or []:
            sid = state_ids[(mid, st["var"])]
            states.append({"state_id": sid, "membrane_id": mid,
                           "var": st["var"],
                           "owner": state_owner[sid], "unit": st["unit"]})
    exchange_states = []
    for c in spec.get("connections") or []:
        cid = c["connection_id"]
        ex = c["exchange"]
        exchange_states.append({
            "connection_id": cid, "state_id": exchange_state_ids[cid],
            "quantity_ref": ex["quantity_ref"],
            "owner": ex["owner_membrane"], "unit": ex["unit"]})
    contributions = []
    ledger_entries = []
    for m in spec.get("membranes") or []:
        mid = m["membrane_id"]
        sid = state_ids[(mid, m["owned_state"][0]["var"])]
        contributions.append({
            "contribution_id": f"contribution.{_tag(mid)}.integrate",
            "owner_membrane": mid, "produces": [sid]})
    for c in spec.get("connections") or []:
        cid = c["connection_id"]
        xsid = exchange_state_ids[cid]
        contributions.append({
            "contribution_id": f"contribution.{_conn_tag(cid)}.exchange",
            "owner_membrane": c["exchange"]["owner_membrane"],
            "produces": [xsid]})
        for row in c["transfer_law"]["per_membrane"]:
            le = row["ledger_entry"]
            ledger_entries.append({"entry_id": le["entry_id"],
                                   "unit": le["unit"],
                                   "membrane_id": row["membrane_id"]})
    return {
        "schema": "chimera.mathspec.bindings.v1",
        "assembly_id": (spec.get("assembly") or {}).get("assembly_id"),
        "spec_id": spec.get("spec_id"),
        "spec_raw_sha256": spec_raw_sha256,
        "spec_canonical_sha256": spec_canonical_sha256,
        "dt_s": float((spec.get("numerics") or {})["dt_s"]),
        "states": states,
        "exchange_states": exchange_states,
        "contributions": contributions,
        "ledger_entries": ledger_entries,
        "reference_only": True,
        "formulas_embedded": False,
    }


def verify_bindings(assembly: Assembly, bindings: dict) -> None:
    """The bindings gate: the generated bindings must resolve EXACTLY to the
    runtime-built assembly (same ids, owners, outputs, dt); they must be
    reference-only. A mismatch is a hand-edit and is refused by name."""
    if not bindings.get("reference_only") or bindings.get("formulas_embedded"):
        raise CombineRefusal(E_BINDINGS_NOT_REFERENCE_ONLY, {
            "reference_only": bindings.get("reference_only"),
            "formulas_embedded": bindings.get("formulas_embedded"),
            "law": "bindings are a resolution record ONLY; formulas live "
                   "exclusively in the spec document"})
    spec = assembly.spec
    state_ids, state_owner, exchange_state_ids = resolve_ids(spec)
    expected_states = []
    for (mid, var), sid in state_ids.items():
        unit = next(st["unit"] for m in spec["membranes"]
                    if m["membrane_id"] == mid
                    for st in m["owned_state"] if st["var"] == var)
        expected_states.append({"state_id": sid, "membrane_id": mid,
                                "var": var, "owner": state_owner[sid],
                                "unit": unit})
    got_states = sorted(_as_jsonable(bindings.get("states") or []),
                        key=lambda r: r.get("state_id") or "")
    if _as_jsonable(expected_states) != got_states:
        raise CombineRefusal(E_BINDINGS_MISMATCH, {
            "field": "states", "expected": expected_states,
            "got": bindings.get("states")})
    expected_exchange = sorted(
        ({"connection_id": cid,
          "state_id": exchange_state_ids[cid],
          "quantity_ref": c["exchange"]["quantity_ref"],
          "owner": c["exchange"]["owner_membrane"],
          "unit": c["exchange"]["unit"]}
         for cid, c in ((x.get("connection_id"), x)
                        for x in spec.get("connections") or [])),
        key=lambda r: r["connection_id"])
    if _as_jsonable(expected_exchange) != sorted(
            _as_jsonable(bindings.get("exchange_states") or []),
            key=lambda r: r.get("connection_id") or ""):
        raise CombineRefusal(E_BINDINGS_MISMATCH, {
            "field": "exchange_states",
            "expected": expected_exchange,
            "got": bindings.get("exchange_states")})
    got_contrib = {c.get("contribution_id"): c
                   for c in bindings.get("contributions") or []}
    for contrib in assembly.scheduler.contributions:
        row = got_contrib.get(contrib.contribution_id)
        if row is None:
            raise CombineRefusal(E_BINDINGS_MISMATCH, {
                "field": "contributions",
                "missing": contrib.contribution_id})
        if row.get("owner_membrane") != contrib.owner_membrane:
            raise CombineRefusal(E_BINDINGS_MISMATCH, {
                "field": "contributions",
                "contribution_id": contrib.contribution_id,
                "expected_owner": contrib.owner_membrane,
                "got_owner": row.get("owner_membrane")})
        if sorted(row.get("produces") or []) != sorted(contrib.produces):
            raise CombineRefusal(E_BINDINGS_MISMATCH, {
                "field": "contributions",
                "contribution_id": contrib.contribution_id,
                "expected_produces": sorted(contrib.produces),
                "got_produces": sorted(row.get("produces") or [])})
    if len(got_contrib) != len(assembly.scheduler.contributions):
        raise CombineRefusal(E_BINDINGS_MISMATCH, {
            "field": "contributions",
            "law": "bindings declare exactly the runtime contributions",
            "expected_count": len(assembly.scheduler.contributions),
            "got_count": len(got_contrib)})
    heat_ids = sorted(e["entry_id"]
                      for e in (assembly.contract.get("accounting") or {})
                      .get("heat") or [])
    got_ledger = sorted(e.get("entry_id") or ""
                        for e in bindings.get("ledger_entries") or [])
    if heat_ids != got_ledger:
        raise CombineRefusal(E_BINDINGS_MISMATCH, {
            "field": "ledger_entries", "expected": heat_ids,
            "got": got_ledger})
    spec_dt = float((spec.get("numerics") or {})["dt_s"])
    if abs(float(bindings.get("dt_s")) - spec_dt) > 0.0:
        raise CombineRefusal(E_BINDINGS_MISMATCH, {
            "field": "dt_s", "expected": spec_dt,
            "got": bindings.get("dt_s"),
            "law": "bindings carry the spec's DECLARED default dt; an "
                   "admissible dt_override is a declared run parameter, "
                   "not a hand-edit"})


def _as_jsonable(rows) -> list:
    return json.loads(json.dumps(list(rows), sort_keys=True))


def assemble_from_bindings(spec: dict, bindings: dict, spec_sha256: str,
                           initial_case_id: str = "nominal",
                           max_workers: int = 4,
                           interleave_seed: int | None = None,
                           defect: str | None = None,
                           dt_override: float | None = None) -> Assembly:
    """The GENERATED-ARTIFACT build path: the bindings produced by
    spec_generate are verified against the runtime resolution BEFORE the
    assembly is used; the qualification harness builds ONLY through this
    gate (composition check chk.1/chk.9)."""
    asm = build_assembly(spec, spec_sha256, initial_case_id, max_workers,
                         interleave_seed, defect, dt_override)
    verify_bindings(asm, bindings)
    return asm


# ---------- the analytic reference (independent of the runtime path) -----------------
def analytic_reference(class_id: str, params: dict, initial: dict,
                       times: list) -> dict:
    """The independent numerical reference: a closed-form solution computed
    DIRECTLY from the declared parameters and initial state -- never from
    the runtime store. Unknown classes are refused by name."""
    if class_id not in SUPPORTED_ANALYTIC_CLASSES:
        raise CombineRefusal(E_ANALYTIC_CLASS_UNKNOWN,
                             {"class_id": class_id,
                              "supported": list(SUPPORTED_ANALYTIC_CLASSES)})
    k = float(params["k"])
    c_a = float(params["C_A"])
    c_b = float(params["C_B"])
    ta0 = float(initial["T_A"])
    tb0 = float(initial["T_B"])
    lam = k * (c_a + c_b) / (c_a * c_b)
    t_inf = (c_a * ta0 + c_b * tb0) / (c_a + c_b)
    out = {}
    for t in times:
        decay = math.exp(-lam * float(t))
        out[float(t)] = {"T_A": t_inf + (ta0 - t_inf) * decay,
                         "T_B": t_inf + (tb0 - t_inf) * decay}
    out["lambda_per_s"] = lam
    out["T_inf_K"] = t_inf
    return out


# ---------- the declared neighbor substitutes (two-lane dispatch) --------------------

def neighbor_substitute(spec: dict, membrane_id: str, times: list) -> dict:
    """The DECLARED neighbor substitute for the phase-2/3 membrane lanes:
    a lane implementing ONE membrane tests against the neighbor's trajectory
    taken from the DECLARED analytic reference class -- never from the
    neighbor's implementation. Unknown membranes or unknown reference
    classes are refused by name. Returns {t: {neighbor_var: value}}."""
    ref = (spec.get("qualification") or {}).get("analytic_reference") or {}
    class_id = ref.get("class_id")
    if class_id not in SUPPORTED_ANALYTIC_CLASSES:
        raise CombineRefusal(E_ANALYTIC_CLASS_UNKNOWN,
                             {"class_id": class_id,
                              "supported": list(SUPPORTED_ANALYTIC_CLASSES)})
    conn = spec["connections"][0]
    if membrane_id not in conn["members"]:
        raise CombineRefusal(E_SPEC_INVALID, {
            "membrane_id": membrane_id,
            "law": "the substitute is declared for connection members"})
    neighbor_mid = next(m for m in conn["members"] if m != membrane_id)
    neighbor_var = next(m["owned_state"][0]["var"]
                        for m in spec["membranes"]
                        if m["membrane_id"] == neighbor_mid)
    params = {}
    for p in conn.get("parameters") or []:
        params[p["var"]] = float(p["value"])
    for m in spec["membranes"]:
        for p in m.get("parameters") or []:
            params[p["var"]] = float(p["value"])
    nominal = next(c for c in spec["assembly"]["initial_states"]
                   if c["case_id"] == "nominal")
    initial = {m["owned_state"][0]["var"]:
               float(nominal["values"][m["owned_state"][0]["var"]])
               for m in spec["membranes"]}
    table = analytic_reference(class_id, params, initial,
                               [float(t) for t in times])
    return {float(t): {neighbor_var: table[float(t)][neighbor_var]}
            for t in times}


def check_stability_bound(spec: dict) -> dict:
    """The declared stability bound lambda*dt < 1 is VERIFIED against the
    declared admissible table (structural; refused, never waived)."""
    k = next(p["value"] for p in spec["connections"][0]["parameters"]
             if p["var"] == "k")
    caps = {}
    for m in spec["membranes"]:
        for p in m.get("parameters") or []:
            caps[p["var"]] = float(p["value"])
    lam = k * (caps["C_A"] + caps["C_B"]) / (caps["C_A"] * caps["C_B"])
    rows = []
    ok = True
    for row in spec["numerics"]["admissibility"]:
        bound = lam * float(row["dt_s"])
        row_ok = bound < 1.0
        ok = ok and row_ok
        rows.append({"dt_s": row["dt_s"], "lambda_dt": bound,
                     "satisfied": row_ok})
    if not ok:
        raise CombineRefusal(E_STABILITY_BOUND,
                             {"lambda_per_s": lam, "rows": rows})
    return {"lambda_per_s": lam, "rows": rows}
