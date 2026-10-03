"""membrane_abi.py -- THE VERSIONED MEMBRANE-MODULE ABI (chimera.membrane_abi.v1).

mathspec lane wk-membrane-abi, Captain's order phase 5: "Define a versioned
membrane-module ABI and an explicit implementation-binding manifest. Specify
construction, state ownership, port inputs/outputs, units, timestep
semantics, and named refusal behavior. Keep provenance attestations separately
labeled."

This module is THE ABI of record. It closes phase-4 handwritten decision #2
(the per-module adapter protocol -- gate entrypoint, membrane class name,
constructor convention, factory names, accessor names were per-module DATA in
the phase-4 manifest). Under the ABI those names are FIXED for every
conforming module, so the wiring generator needs NO per-module protocol data
and NO module-specific branches. Decision #1 (which file implements which
membrane id, at which byte identity) stays an explicit manifest --
abi_binding_manifest.thermal_pair.v1.json. Decision #3 (lane-of-record
provenance attestations) stays SEPARATELY LABELED in that manifest's
provenance section; it is never absorbed into the binding itself.

THE ABI CONTRACT (normative text; machine-checkable via ABI_CONTRACT + the
validate_* functions in this module):

1. CONSTRUCTION.
   A conforming module is ONE importable Python file declaring at module level:
     ABI_VERSION             = "chimera.membrane_abi.v1"   (exact string)
     IMPLEMENTS_MEMBRANE_ID  = "<exactly one membrane_id of the spec>"
     def build(context, dt)      -> membrane object
     def verify_frozen_inputs()  -> dict (identity table of the verified bytes)
   THE CONSTRUCTOR SIGNATURE IS build(context, dt): the ABI REPLACES the two
   delivered lanes' divergent conventions MembraneA(frozen, dt) /
   MembraneB(spec, dt). `context` is a membrane_abi.SpecContext built by the
   wiring from the byte-verified frozen spec; `dt` is ONE float.
   FROZEN-INPUT CONTRACT: every conforming module accepts the context AND
   re-verifies its own pinned bytes at build (its own gate), refusing any
   drift or context-identity mismatch BY NAME before anything is constructed.
   A conforming module never trusts an unverified context identity.

2. STATE OWNERSHIP.
   The built membrane object declares ownership() ->
     {"membrane_id": ...,
      "owned_states": [{"var", "unit", "state_id"}, ...],
      "contribution_id": ...}
   derived from the module's OWN spec section and the ONE deterministic id
   scheme (state.<var>.<membrane_tag>.v1, spec_runtime.resolve_ids). The
   ownership LAW: the module produces EXACTLY the states it declares in
   ownership() -- never the neighbor's state, never another membrane's
   exchange record. The pinned owner store enforces this at runtime
   (combine_non_owner_write / combine_unknown_state /
   combine_double_state_write); the ABI makes the declaration checkable
   BEFORE wiring (abi_ownership_contract_mismatch).

3. PORT INPUTS/OUTPUTS WITH UNITS.
   The built membrane object declares ports() -> the typed port table of its
   spec section: {"inputs": [{"port_id", "quantity_ref", "type", "unit",
   "sign_convention", "connection_ref"}...], "outputs": [...]}.
   LAW: an INPUT port carries a connection's exchange quantity (with the
   exchange's unit); an OUTPUT port carries the membrane's OWN published
   state. A module whose declared ports contradict its spec section
   (wrong unit, reversed direction, unknown quantity) is refused at
   conformance time (abi_port_contract_mismatch) -- never wired.

4. TIMESTEP SEMANTICS.
   dt admissibility: the ONLY admissible timesteps are the rows of the spec's
   numerics.admissibility table, DECLARED in the spec before any run. A
   conforming module (and the ABI wiring in front of it) refuses any other
   dt at construction with code "spec_dt_not_admissible".
   Stepping contract: ONE explicit step of size dt per window (the spec's
   declared numerics.method); the connection's exchange quantity is computed
   from the WINDOW-START state view (zero-order hold over the window); the
   ledger books ENERGY over the window (J = W * dt), never implicit power.
   The step is PURE: same window-start view -> same payload (determinism
   law). An invalid request is refused BEFORE any payload is produced, and
   the pinned scheduler restores the window-start store, so a refused window
   leaves every state bitwise unchanged.

5. NAMED REFUSAL BEHAVIOR (mandatory for every ABI-conforming module).
   BUILD-TIME (constructor):
     "spec_dt_not_admissible"   -- dt outside the declared admissibility table
     "spec_pinned_input_drift"  -- any pinned/frozen byte drifted, or the
                                   context identity does not match the
                                   module's own verified bytes
   IN-STEP (before producing any state/ledger payload):
     every DECLARED refusal condition of the module's spec section fires with
     its DECLARED refusal_code (e.g. ref.a.exchange_out_of_declared_range /
     ref.b.exchange_out_of_declared_range), and the store is restored
     bitwise by the pinned scheduler.
   WRITE-SCOPE (enforced by the pinned runtime against the ABI declaration):
     combine_non_owner_write / combine_unknown_state /
     combine_double_state_write -- any attempt to write outside the declared
     ownership is refused by the owner store; the ABI guarantees the
     declaration is honest (checked at conformance).
   ABI-LAYER REFUSALS (raised by this module's validators / the generator):
     "abi_version_mismatch"          -- module ABI_VERSION != this ABI
     "abi_module_not_conformant"     -- missing/invalid required module or
                                        membrane surface member
     "abi_identity_mismatch"         -- module identity != binding/expectation
     "abi_port_contract_mismatch"    -- declared ports contradict the spec
                                        section (unit, direction, quantity)
     "abi_ownership_contract_mismatch" -- declared ownership contradicts the
                                        spec section or the id scheme
     "abi_exchange_writer_violation" -- the ONE-writer law: only the
                                        exchange-record owner membrane exposes
                                        exchange_contribution(); a non-owner
                                        that exposes it (or the owner that
                                        lacks it) is refused

6. PROVENANCE. Lane-of-record attestations are NOT part of the ABI surface.
   They live in the binding manifest's separately-labeled provenance section
   and in the lanes' own EVIDENCE.md files (see the independence-scope note,
   mathspec EVIDENCE.md section 11: attestations are process claims, not
   machine-verified facts).

NO PHYSICS CLAIM: the ABI is an interface contract for synthetic teaching
mechanisms declared in chimera.mathspec.spec.v1 documents; it carries no
physical fidelity claim of any kind.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

# Allow sibling imports (spec_runtime for the ONE id-scheme authority) when
# this module is loaded from the lane root.
_HERE = pathlib.Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "pinned_inputs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import spec_runtime  # noqa: E402  (pinned helper; resolve_ids is THE scheme)
from spec_runtime import CombineRefusal, canonical  # noqa: E402,F401

# ---------- the versioned identity --------------------------------------------------

ABI_VERSION = "chimera.membrane_abi.v1"
ABI_SCHEMA = "chimera.membrane_abi.v1"

# ---------- named refusal codes (ABI layer) -----------------------------------------

E_ABI_VERSION_MISMATCH = "abi_version_mismatch"
E_ABI_MODULE_NOT_CONFORMANT = "abi_module_not_conformant"
E_ABI_IDENTITY_MISMATCH = "abi_identity_mismatch"
E_ABI_PORT_CONTRACT_MISMATCH = "abi_port_contract_mismatch"
E_ABI_OWNERSHIP_CONTRACT_MISMATCH = "abi_ownership_contract_mismatch"
E_ABI_EXCHANGE_WRITER_VIOLATION = "abi_exchange_writer_violation"

# ---------- the normative machine-readable contract ---------------------------------

ABI_CONTRACT = {
    "schema": ABI_SCHEMA,
    "abi_version": ABI_VERSION,
    "spec_format": "chimera.mathspec.spec.v1",
    "module_surface": {
        "ABI_VERSION": "constant == chimera.membrane_abi.v1",
        "IMPLEMENTS_MEMBRANE_ID": "constant, exactly one spec membrane_id",
        "build": "build(context: SpecContext, dt: float) -> membrane object",
        "verify_frozen_inputs": "() -> dict (verified-bytes identity table)",
    },
    "membrane_surface": {
        "membrane_id": "attribute == IMPLEMENTS_MEMBRANE_ID",
        "ownership": "() -> {membrane_id, owned_states, contribution_id}",
        "ports": "() -> {inputs: [...], outputs: [...]} (typed, with units)",
        "contribution": "() -> pinned combine_core.Contribution writing "
                         "EXACTLY ownership().owned_states",
        "exchange_quantity": "(view) -> float (the ONE shared exchange "
                             "closure at the window-start view; required on "
                             "EVERY member membrane)",
        "exchange_contribution": "() -> pinned Contribution writing the "
                                  "exchange record; REQUIRED on the "
                                  "connection's exchange-record owner and "
                                  "FORBIDDEN (absent) on every other member",
    },
    "construction": {
        "signature": "build(context, dt)",
        "context": "membrane_abi.SpecContext (byte-verified frozen spec)",
        "frozen_input_contract": "the module re-verifies its own pinned "
                                 "bytes at build and refuses drift or "
                                 "context-identity mismatch BY NAME",
    },
    "timestep_semantics": {
        "admissibility": "only numerics.admissibility rows of the spec",
        "refusal_code": "spec_dt_not_admissible",
        "stepping": "ONE explicit declared-method step of size dt per "
                    "window; exchange quantity from the WINDOW-START view "
                    "(zero-order hold); ledger books J = W * dt; pure "
                    "function of the window-start view",
    },
    "mandatory_named_refusals": {
        "build_time": ["spec_dt_not_admissible", "spec_pinned_input_drift"],
        "in_step": ["the DECLARED refusal_code of every fired declared "
                    "refusal condition of the module's spec section"],
        "write_scope_runtime": ["combine_non_owner_write",
                                "combine_unknown_state",
                                "combine_double_state_write"],
    },
    "abi_layer_refusals": [E_ABI_VERSION_MISMATCH,
                           E_ABI_MODULE_NOT_CONFORMANT,
                           E_ABI_IDENTITY_MISMATCH,
                           E_ABI_PORT_CONTRACT_MISMATCH,
                           E_ABI_OWNERSHIP_CONTRACT_MISMATCH,
                           E_ABI_EXCHANGE_WRITER_VIOLATION],
    "provenance": "SEPARATELY LABELED in the binding manifest; never part "
                  "of the ABI surface",
}


# ---------- the frozen context (THE construction context) ----------------------------

class SpecContext:
    """The ABI construction context: the parsed frozen spec + its raw-bytes
    sha256, built by the wiring from BYTE-VERIFIED spec bytes.

    It carries the attribute surface the DELIVERED membrane classes already
    expect of their context objects (spec, raw_sha256, admissible_dts,
    bindings) so the thin adapters can hand it through without translation,
    and so a legacy-class probe (e.g. the nine-check harness's
    non-admissible-dt probe) keeps refusing by name instead of raising
    AttributeError.
    """

    def __init__(self, spec: dict, spec_raw_sha256: str, bindings=None):
        if not isinstance(spec, dict):
            raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
                "law": "SpecContext.spec must be the parsed spec document"})
        if not isinstance(spec_raw_sha256, str) or len(spec_raw_sha256) != 64:
            raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
                "law": "SpecContext binds the raw spec bytes sha256 "
                       "(64 hex chars)", "got": spec_raw_sha256})
        self.spec = spec
        self.spec_raw_sha256 = spec_raw_sha256
        self.raw_sha256 = spec_raw_sha256   # legacy-context alias (Frozen.raw_sha256)
        self.bindings = bindings            # the generated bindings module (optional)

    def admissible_dts(self) -> list:
        numerics = self.spec.get("numerics") or {}
        return [float(row["dt_s"])
                for row in numerics.get("admissibility") or []]

    def section(self, membrane_id: str) -> dict:
        for m in self.spec.get("membranes") or []:
            if m.get("membrane_id") == membrane_id:
                return m
        raise CombineRefusal("spec_validation_failed", {
            "law": "the context spec does not declare this membrane",
            "membrane_id": membrane_id})

    def connection(self, connection_id: str) -> dict:
        for c in self.spec.get("connections") or []:
            if c.get("connection_id") == connection_id:
                return c
        raise CombineRefusal("spec_validation_failed", {
            "law": "the context spec does not declare this connection",
            "connection_id": connection_id})

    def require_dt_admissible(self, dt) -> float:
        dt = float(dt)
        admissible = self.admissible_dts()
        if dt not in admissible:
            raise CombineRefusal("spec_dt_not_admissible", {
                "requested_dt": dt, "admissible": sorted(admissible),
                "law": "only DECLARED admissible timesteps may be run "
                       "(ABI timestep semantics)"})
        return dt


# ---------- module-level conformance --------------------------------------------------

_MODULE_REQUIRED = ("ABI_VERSION", "IMPLEMENTS_MEMBRANE_ID", "build",
                    "verify_frozen_inputs")


def validate_module(module, expected_membrane_id: str | None = None) -> dict:
    """Validate ONE candidate module against the ABI module surface.
    Refuses by name; returns the conformance record on success."""
    missing = [name for name in _MODULE_REQUIRED if not hasattr(module, name)]
    if missing:
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "module": getattr(module, "__name__", "<unknown>"),
            "missing": missing,
            "law": "an ABI-conforming module declares " +
                   ", ".join(_MODULE_REQUIRED)})
    if module.ABI_VERSION != ABI_VERSION:
        raise CombineRefusal(E_ABI_VERSION_MISMATCH, {
            "module": getattr(module, "__name__", "<unknown>"),
            "declared": module.ABI_VERSION, "expected": ABI_VERSION})
    if (not isinstance(module.IMPLEMENTS_MEMBRANE_ID, str)
            or not module.IMPLEMENTS_MEMBRANE_ID):
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "module": getattr(module, "__name__", "<unknown>"),
            "IMPLEMENTS_MEMBRANE_ID": module.IMPLEMENTS_MEMBRANE_ID})
    if not callable(module.build) or not callable(module.verify_frozen_inputs):
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "module": getattr(module, "__name__", "<unknown>"),
            "law": "build and verify_frozen_inputs must be callable"})
    if expected_membrane_id is not None and \
            module.IMPLEMENTS_MEMBRANE_ID != expected_membrane_id:
        raise CombineRefusal(E_ABI_IDENTITY_MISMATCH, {
            "module": getattr(module, "__name__", "<unknown>"),
            "declared": module.IMPLEMENTS_MEMBRANE_ID,
            "expected": expected_membrane_id})
    return {"conformant": True, "abi_version": ABI_VERSION,
            "module": getattr(module, "__name__", "<unknown>"),
            "membrane_id": module.IMPLEMENTS_MEMBRANE_ID}


# ---------- built-membrane conformance ------------------------------------------------

def _section(spec: dict, membrane_id: str) -> dict:
    for m in spec.get("membranes") or []:
        if m.get("membrane_id") == membrane_id:
            return m
    raise CombineRefusal("spec_validation_failed", {
        "law": "the spec does not declare this membrane",
        "membrane_id": membrane_id})


def _expected_ownership(spec: dict, membrane_id: str) -> list:
    state_ids, _owner, _ex = spec_runtime.resolve_ids(spec)
    section = _section(spec, membrane_id)
    rows = []
    for st in section.get("owned_state") or []:
        rows.append({"var": st["var"], "unit": st["unit"],
                     "state_id": state_ids[(membrane_id, st["var"])]})
    return rows


def _ports_normalized(ports: dict) -> dict:
    out = {}
    for direction in ("inputs", "outputs"):
        rows = []
        for p in (ports or {}).get(direction) or []:
            rows.append({"port_id": p.get("port_id"),
                         "quantity_ref": p.get("quantity_ref"),
                         "unit": p.get("unit"),
                         "connection_ref": p.get("connection_ref")})
        rows.sort(key=lambda r: (str(r.get("port_id")),
                                 str(r.get("quantity_ref"))))
        out[direction] = rows
    return out


def validate_built(membrane, spec: dict, membrane_id: str,
                   connection_id: str) -> dict:
    """Validate ONE built membrane object against its spec section: state
    ownership, typed ports (units + direction), the exchange-writer law and
    the exchange-quantity accessor. Refuses by name; never repairs."""
    got_id = getattr(membrane, "membrane_id", None)
    if got_id != membrane_id:
        raise CombineRefusal(E_ABI_IDENTITY_MISMATCH, {
            "built": got_id, "expected": membrane_id})
    section = _section(spec, membrane_id)

    # -- ownership ------------------------------------------------------------------
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

    # -- typed ports (units + direction) ----------------------------------------------
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

    # -- exchange-quantity accessor (EVERY member) --------------------------------------
    if not callable(getattr(membrane, "exchange_quantity", None)):
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "membrane_id": membrane_id,
            "missing": "exchange_quantity(view) -- the ONE shared exchange "
                       "closure accessor is required on every member"})

    # -- the ONE-writer exchange law ------------------------------------------------------
    conn = None
    for c in spec.get("connections") or []:
        if c.get("connection_id") == connection_id:
            conn = c
            break
    if conn is None:
        raise CombineRefusal("spec_validation_failed", {
            "law": "the spec does not declare this connection",
            "connection_id": connection_id})
    owner = (conn.get("exchange") or {}).get("owner_membrane")
    has_writer = callable(getattr(membrane, "exchange_contribution", None))
    if membrane_id == owner and not has_writer:
        raise CombineRefusal(E_ABI_EXCHANGE_WRITER_VIOLATION, {
            "membrane_id": membrane_id, "connection_id": connection_id,
            "law": "the exchange-record OWNER must expose "
                   "exchange_contribution()"})
    if membrane_id != owner and has_writer:
        raise CombineRefusal(E_ABI_EXCHANGE_WRITER_VIOLATION, {
            "membrane_id": membrane_id, "connection_id": connection_id,
            "exchange_owner": owner,
            "law": "ONLY the exchange-record owner exposes "
                   "exchange_contribution(); a non-owner writer would "
                   "violate the ONE-writer law"})

    # -- contribution factory --------------------------------------------------------------
    if not callable(getattr(membrane, "contribution", None)):
        raise CombineRefusal(E_ABI_MODULE_NOT_CONFORMANT, {
            "membrane_id": membrane_id, "missing": "contribution()"})

    return {"conformant": True, "membrane_id": membrane_id,
            "connection_id": connection_id, "exchange_owner": owner,
            "owned_states": expected_rows}


# ---------- module loading helper (shared by adapters and the generator) --------------

def load_module_file(path, module_name: str):
    """Load ONE Python file as a module (no package machinery; the lane's
    flat-file convention). The caller hash-verifies the bytes first."""
    path = pathlib.Path(path)
    spec_mod = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec_mod)
    sys.modules[module_name] = module
    spec_mod.loader.exec_module(module)
    return module
