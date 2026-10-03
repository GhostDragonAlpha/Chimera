"""graph_wiring_generate.py -- THE GRAPH-DRIVEN ASSEMBLY-WIRING GENERATOR
(the packetgen law, the graph stage; the Order-17 lift).

mathspec lane wk-membrane-abi. This stage GENERALIZES the ABI wiring
generator's class law from (two membranes, one connection) to the DECLARED
GRAPH -- N membranes, M two-member connections, everything from the frozen
declarations -- with NO module-name-specific branches:

  inputs:  the frozen spec bytes (validated) + the bindings table (loaded
           from its pinned artifact, cross-checked against a fresh
           derivation -- or EMITTED when the manifest declares a bindings
           artifact that does not exist yet, the chain case) + the VERSIONED
           ABI + graph_runtime (the graph-class validation/contract layer) +
           the implementation-binding manifest (the SAME manifest schema,
           chimera.membrane_abi.binding_manifest.v1: membrane_id -> module
           file + byte identity + the wrapped delivered bytes).
  outputs: generated/bindings.<tag>.v1.py (when freshly emitted) +
           generated/assembly_wiring_graph.<tag>.v1.py -- the GENERATED
           wiring that constructs and wires EVERY member through the SAME
           ABI code path, places the contributions in the GENERATED
           bindings-row order, validates 9/9 coverage under the pinned
           validator, and proves PER CONNECTION the ONE-quantity law
           bitwise every window.

Every member module is constructed with the SAME call adapter.build(context,
dt), validated by graph_runtime.validate_built_graph (per-connection writer
scoping), and wired through the SAME ABI factories (contribution() on every
member; exchange_contribution() on each connection's owner only). The
manifest carries ONLY files and byte identities; the ABI fixes every name.

Determinism law: identical inputs -> byte-identical artifacts; from-scratch
regeneration must equal the shipped artifacts byte-for-byte.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_PIN = _HERE / "pinned_inputs"
for _p in (str(_HERE), str(_PIN)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import membrane_abi  # noqa: E402  (THE ABI; version-checked below)
import graph_runtime  # noqa: E402  (the graph-class layer)
import spec_format  # noqa: E402
import spec_runtime  # noqa: E402  (pinned bytes: 423fca70...)
from spec_runtime import (CombineRefusal, PINS, build_bindings,  # noqa: E402,F401
                          canonical, sha256_bytes, sha256_text)

E_SPEC_UNPARSEABLE = "wiring_spec_unparseable"
E_SPEC_INVALID = "wiring_spec_invalid"
E_CLASS_UNSUPPORTED = "wiring_class_unsupported"
E_BINDINGS_MISMATCH = "wiring_bindings_mismatch"
E_MANIFEST_UNPARSEABLE = "abi_binding_manifest_unparseable"
E_MANIFEST_INVALID = "abi_binding_manifest_invalid"
E_LANDED_DRIFT = "wiring_landed_module_drift"
E_FROZEN_MISSING = "wiring_frozen_interface_missing"
E_RENDER_ERROR = "wiring_render_error"

GRAPH_RECEIPT_SCHEMA = "chimera.mathspec.graph_wiring_generation_receipt.v1"
MANIFEST_SCHEMA = "chimera.membrane_abi.binding_manifest.v1"
ARTIFACT_PREFIX = "assembly_wiring_graph"
BINDINGS_PREFIX = "bindings"

_IMPL_KEYS = ["membrane_id", "module_file", "module_sha256", "wraps"]
_WRAPS_KEYS = ["file", "sha256", "lane_of_record"]

_BINDINGS_MODULE_TEMPLATE = '''"""GENERATED FILE -- mathspec lane, graph_wiring_generate.generate_graph_wiring. DO NOT HAND-EDIT.

Interface bindings for @@ASSEMBLY_ID@@ (the @@GRAPH_DESC@@), generated from
the frozen spec bytes of @@SPEC_ID@@. This module is a REFERENCE-ONLY
resolution record: identifiers resolved at generation time through the ONE
deterministic scheme; formulas live ONLY in the embedded spec. Any formula
here would be refused by the bindings gate.

Regeneration from the same spec bytes must be byte-identical.

NOTE: the frozen spec_runtime.build_assembly binds the ONE-connection class
and refuses this assembly by name (spec_validation_failed); the assembly
build path for this graph is the GENERATED graph wiring artifact beside
which this bindings module lives.
"""
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "pinned_inputs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SPEC_RAW_SHA256 = "@@SPEC_SHA@@"
SPEC_CANONICAL_SHA256 = "@@SPEC_CANON_SHA@@"
SPEC = json.loads(r\'\'\'@@SPEC_JSON@@\'\'\')
BINDINGS = json.loads(r\'\'\'@@BINDINGS_JSON@@\'\'\')
'''

_WIRING_TEMPLATE = '''"""GENERATED FILE -- mathspec lane, graph_wiring_generate.generate_graph_wiring. DO NOT HAND-EDIT.

GENERATED ASSEMBLY WIRING (GRAPH PATH) for @@ASSEMBLY_ID@@ -- the
N-membranes/M-connections assembly (the @@GRAPH_DESC@@), stage-general.
Generated from the frozen spec bytes + the GENERATED bindings table + the
VERSIONED ABI chimera.membrane_abi.v1 + graph_runtime (the graph-class
validation/contract layer) + the DECLARED implementation-binding manifest.
Every member module is constructed and wired through THE SAME ABI code path
(build(context, dt), graph_runtime.validate_built_graph with per-connection
writer scoping, contribution() on every member, exchange_contribution() on
each connection's owner only): there is NO module-specific branch and NO
per-module adapter-protocol table.

Generation inputs (byte identities of record):
  spec        @@SPEC_RELPATH@@ sha256=@@SPEC_SHA@@
  bindings    @@BINDINGS_RELPATH@@ sha256=@@BINDINGS_SHA@@
  abi         @@ABI_RELPATH@@ sha256=@@ABI_SHA@@
  graph       @@GRAPH_RELPATH@@ sha256=@@GRAPH_SHA@@
  manifest    @@MANIFEST_RELPATH@@ canonical sha256=@@MANIFEST_SHA@@
  generator   graph_wiring_generate.py sha256=@@GEN_SHA@@

Determinism law: identical inputs -> byte-identical artifact; from-scratch
regeneration MUST equal this file byte-for-byte.

Provenance attestations are SEPARATELY LABELED in the manifest
(provenance_labels); they are not part of the wiring path.
"""
import hashlib
import importlib.util
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "pinned_inputs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import combine_core  # noqa: E402  (pinned byte-exact)
import graph_runtime  # noqa: E402  (the graph-class layer; pinned below)
import membrane_abi  # noqa: E402  (THE versioned ABI; pinned below)
import spec_lang  # noqa: E402
import spec_runtime  # noqa: E402  (frozen helper; bytes pinned below)
import PORT_CONTRACT_V2  # noqa: E402  (the pinned v2 validator)
from combine_core import CombineRefusal, CombineScheduler, verify_pins  # noqa: E402,F401
from spec_lang import evaluate, parse  # noqa: E402,F401

# ---------- generation-time resolution (re-verified at every build) -----------------
ASSEMBLY_ID = "@@ASSEMBLY_ID@@"
MEMBERS = json.loads(r\'\'\'@@MEMBERS_JSON@@\'\'\')      # bindings states order
CONNECTIONS = json.loads(r\'\'\'@@CONNECTIONS_JSON@@\'\'\')
SPEC_RAW_SHA256 = "@@SPEC_SHA@@"
SPEC_RELPATH = "@@SPEC_RELPATH@@"
BINDINGS_RELPATH = "@@BINDINGS_RELPATH@@"
BINDINGS_SHA256 = "@@BINDINGS_SHA@@"
MANIFEST_RELPATH = "@@MANIFEST_RELPATH@@"
ABI_VERSION = "@@ABI_VERSION@@"
ABI_MODULE_RELPATH = "@@ABI_RELPATH@@"
GRAPH_RELPATH = "@@GRAPH_RELPATH@@"

# pair-compatibility aliases (the FIRST two members and the FIRST
# connection) -- the preserved pair harness reads these names; they are
# derived aliases, not wiring decisions
MEMBRANE_A = MEMBERS[0]
MEMBRANE_B = MEMBERS[1]
CONNECTION_ID = CONNECTIONS[0]["connection_id"]
EXCHANGE_STATE_ID = CONNECTIONS[0]["exchange_state_id"]
ENTRY_FROM_A = CONNECTIONS[0]["ledger_entries"][MEMBERS[0]]
ENTRY_INTO_B = CONNECTIONS[0]["ledger_entries"][MEMBERS[1]]

# the landed DELIVERED modules (the manifest's wrapped implementations;
# consumed BYTE-EXACT as delivered -- hash equality IS the no-edit proof)
LANDED_MODULES = json.loads(r\'\'\'@@LANDED_JSON@@\'\'\')

LANE_OF_RECORD = json.loads(r\'\'\'@@LANE_JSON@@\'\'\')

WRAPS_OF = json.loads(r\'\'\'@@WRAPS_OF_JSON@@\'\'\')

# the manifest-bound member modules; the ABI fixes their surface, so only
# files + byte identities are declared
ADAPTER_FILES = json.loads(r\'\'\'@@ADAPTERS_JSON@@\'\'\')

# the frozen interface the assembly consumes (drift-refused BEFORE anything
# runs): the landed modules, the member modules, the ABI, the graph layer,
# this generator stage, the manifest, the pinned runtime, the spec and the
# bindings artifact
FROZEN_INTERFACE = json.loads(r\'\'\'@@FROZEN_JSON@@\'\'\')

# the full manifest (implementation binding + separately-labeled provenance)
MANIFEST = json.loads(r\'\'\'@@MANIFEST_JSON@@\'\'\')


def sha256_file(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


_BINDINGS_MODULE_NAME = "graph_assembly_wiring_generated_bindings"


def _load_bindings_module():
    path = _HERE.parent / BINDINGS_RELPATH
    if sha256_file(path) != BINDINGS_SHA256:
        raise CombineRefusal("spec_pinned_input_drift", {
            "path": BINDINGS_RELPATH, "expected": BINDINGS_SHA256,
            "observed": sha256_file(path),
            "law": "the generated bindings are a frozen interface identity; "
                   "a drifted bindings module is never loaded"})
    spec_mod = importlib.util.spec_from_file_location(
        _BINDINGS_MODULE_NAME, path)
    module = importlib.util.module_from_spec(spec_mod)
    sys.modules[_BINDINGS_MODULE_NAME] = module
    spec_mod.loader.exec_module(module)
    return module


def _load(name: str, filename: str):
    path = _HERE.parent / filename
    spec_mod = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec_mod)
    sys.modules[name] = module
    spec_mod.loader.exec_module(module)
    return module


def require_assembly_inputs() -> dict:
    """THE assemble-without-hand-editing gate (GENERATED): every landed
    byte, every member-module byte and every frozen-interface byte is
    hash-verified BEFORE anything runs."""
    verify_pins(spec_runtime.PINS)
    identities = {"landed_modules": {}, "frozen_interface": {}}
    for rel, want in sorted(LANDED_MODULES.items()):
        got = sha256_file(_HERE.parent / rel)
        if got != want:
            raise CombineRefusal("assemble_landed_module_drift", {
                "path": rel, "expected": want, "observed": got,
                "lane_of_record": LANE_OF_RECORD.get(rel),
                "law": "the independently produced modules are consumed "
                       "BYTE-EXACT as delivered; any hand edit is refused "
                       "here (assemble-without-hand-editing)"})
        identities["landed_modules"][rel] = got
    for rel, want in sorted(FROZEN_INTERFACE.items()):
        got = sha256_file(_HERE.parent / rel)
        if got != want:
            raise CombineRefusal("spec_pinned_input_drift", {
                "path": rel, "expected": want, "observed": got})
        identities["frozen_interface"][rel] = got
    return identities


def _load_adapters():
    """Load the manifest-bound member modules and validate each against the
    ABI (module surface + identity). THE SAME code path for every member."""
    adapters = {}
    for mid in MEMBERS:
        decl = ADAPTER_FILES[mid]
        adapter = _load("graph_assembly_wiring_adapter_"
                        + decl["file"][:-3], decl["file"])
        conformance = membrane_abi.validate_module(adapter, mid)
        adapters[mid] = adapter
    return adapters


def _build_context():
    """The ABI construction context from the PINNED spec bytes: read, hash,
    parse, bindings cross-check (loaded table == fresh derivation), wrap in
    membrane_abi.SpecContext."""
    raw = (_HERE.parent / SPEC_RELPATH).read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != SPEC_RAW_SHA256:
        raise CombineRefusal("spec_pinned_input_drift", {
            "path": SPEC_RELPATH, "expected": SPEC_RAW_SHA256,
            "observed": got})
    spec = json.loads(raw.decode("utf-8"))
    module = _load_bindings_module()
    if module.SPEC_RAW_SHA256 != SPEC_RAW_SHA256:
        raise CombineRefusal("spec_bindings_mismatch", {
            "field": "SPEC_RAW_SHA256", "expected": SPEC_RAW_SHA256,
            "got": module.SPEC_RAW_SHA256})
    bindings = module.BINDINGS
    canon = spec_runtime.sha256_text(spec_runtime.canonical(spec))
    expected = spec_runtime.build_bindings(spec, SPEC_RAW_SHA256, canon)
    if bindings != expected:
        raise CombineRefusal("spec_bindings_mismatch", {
            "field": "table",
            "law": "the GENERATED wiring cross-checks the loaded bindings "
                   "table against a fresh derivation from the frozen spec "
                   "bytes; a mismatch is a hand edit",
            "loaded": bindings, "derived": expected})
    return membrane_abi.SpecContext(spec, SPEC_RAW_SHA256, module)


def load_members():
    """Verify every byte; load the landed modules, the manifest-bound
    member modules (ABI-validated), the context and each member's OWN
    frozen-input gate. Returns (landed_mods, adapters, context, gates)."""
    require_assembly_inputs()
    adapters = _load_adapters()
    mods = {}
    gates = {}
    for mid in MEMBERS:
        mods[mid] = _load("graph_assembly_wiring_membrane_"
                          + WRAPS_OF[mid][:-3], WRAPS_OF[mid])
        gates[mid] = adapters[mid].verify_frozen_inputs()
    context = _build_context()
    if context.spec_raw_sha256 != SPEC_RAW_SHA256:
        raise CombineRefusal("spec_pinned_input_drift", {
            "law": "the context must bind THIS assembly's spec bytes"})
    return mods, adapters, context, gates


def load_membranes():
    """The pair-harness-facing signature (the preserved pair harness reads
    exactly four names). Refuses by name for any assembly whose member
    count is not two -- the generic accessor is load_members()."""
    if len(MEMBERS) != 2:
        raise CombineRefusal("wiring_class_unsupported", {
            "members": MEMBERS,
            "law": "the pair-compatibility accessor binds exactly two "
                   "members; use load_members() for the graph"})
    mods, adapters, context, gates = load_members()
    return mods[MEMBERS[0]], mods[MEMBERS[1]], context, gates[MEMBERS[1]]


# ---------- the GENERATED mechanical assembly (the graph code path) ------------------

class AssemblyRun:
    """The completed assembly on the pinned scheduler, wired ENTIRELY by
    this generated module through the ABI + the graph-class layer. Every
    member is constructed with the SAME call adapter.build(context, dt),
    validated by graph_runtime.validate_built_graph (ownership, typed ports
    with units, PER-CONNECTION writer scoping), and wired in the GENERATED
    bindings-row order:

@@PLACE_ROWS@@
    under the graph v2 contract groups (validated 9/9 by the pinned
    validator). Every window the generated step proves, PER CONNECTION, the
    ONE-exchange law: each member's accessor, the owner's accessor and the
    stored record agree BITWISE.
    """

    def __init__(self, context, adapters, gates, dt: float,
                 initial_case_id: str = "nominal", max_workers: int = 4,
                 interleave_seed: int | None = None):
        spec = context.spec
        self.spec = spec
        self.raw_sha256 = context.spec_raw_sha256
        self.dt = context.require_dt_admissible(dt)
        self.gates = gates
        # -- ABI construction: THE SAME path for every member --------------
        self.membranes = {}
        self.conformance = {}
        for mid in MEMBERS:
            obj = adapters[mid].build(context, self.dt)
            self.conformance[mid] = graph_runtime.validate_built_graph(
                obj, spec, mid)
            self.membranes[mid] = obj
        # -- resolution from the GENERATED bindings table (cross-checked) --
        bindings = self._load_and_verify_bindings(spec)
        self.bindings = bindings
        self.state_ids = {(r["membrane_id"], r["var"]): r["state_id"]
                          for r in bindings["states"]}
        self.state_owner = {r["state_id"]: r["owner"]
                            for r in bindings["states"]}
        self.exchange_state_ids = {r["connection_id"]: r["state_id"]
                                   for r in bindings["exchange_states"]}
        contract = graph_runtime.build_contract_groups_graph(
            spec, self.raw_sha256, self.state_ids, self.state_owner,
            self.exchange_state_ids, self.dt)
        decl = {"membranes": [{"membrane_id": m["membrane_id"]}
                              for m in spec["membranes"]]}
        vreport = PORT_CONTRACT_V2.validate_contract_v2(contract, decl)
        coverage = sum(1 for row in vreport["coverage"] if row["covered"])
        if not vreport["valid"] or vreport["schema_major"] != 2 \\
                or coverage != 9:
            raise CombineRefusal("combine_contract_invalid", {
                "law": "the graph v2 contract must be valid with 9/9 "
                       "coverage under the pinned validator",
                "errors": vreport["errors"], "coverage": coverage})
        case = next((c for c in spec["assembly"]["initial_states"]
                     if c["case_id"] == initial_case_id), None)
        if case is None:
            raise CombineRefusal("spec_unknown_initial_case", {
                "case_id": initial_case_id,
                "declared": sorted(c["case_id"] for c in
                                   spec["assembly"]["initial_states"])})
        self.initial = {k: float(v) for k, v in case["values"].items()}
        initial_values = {sid: self.initial[var]
                          for (mid, var), sid in self.state_ids.items()}
        # -- the Contribution placement (GENERATED from the bindings rows,
        #    built through the ABI factories) -------------------------------
        exchange_state_set = set(self.exchange_state_ids.values())
        contributions = []
        for row in bindings["contributions"]:
            mid = row["owner_membrane"]
            if exchange_state_set & set(row["produces"]):
                contributions.append(
                    self.membranes[mid].exchange_contribution())
            else:
                contributions.append(self.membranes[mid].contribution())
        self._verify_wiring(contributions, bindings)
        self.contract = contract
        self.decl = decl
        self.scheduler = CombineScheduler(
            contract, decl, contributions, max_workers=max_workers,
            interleave_seed=interleave_seed,
            initial_values=initial_values)
        self.window_index = 0
        self.last_window_start = None
        self.q_proofs = []   # per-window, per-connection bitwise proofs

    def _load_and_verify_bindings(self, spec) -> dict:
        module = _load_bindings_module()
        bindings = module.BINDINGS
        if module.SPEC_RAW_SHA256 != SPEC_RAW_SHA256:
            raise CombineRefusal("spec_bindings_mismatch", {
                "field": "SPEC_RAW_SHA256",
                "expected": SPEC_RAW_SHA256,
                "got": module.SPEC_RAW_SHA256})
        canon = spec_runtime.sha256_text(spec_runtime.canonical(spec))
        expected = spec_runtime.build_bindings(spec, SPEC_RAW_SHA256, canon)
        if bindings != expected:
            raise CombineRefusal("spec_bindings_mismatch", {
                "field": "table",
                "law": "the GENERATED wiring cross-checks the loaded "
                       "bindings table against a fresh derivation from the "
                       "frozen spec bytes; a mismatch is a hand edit",
                "loaded": bindings, "derived": expected})
        return bindings

    def _verify_wiring(self, contributions, bindings) -> None:
        rows = {r["contribution_id"]: r
                for r in bindings.get("contributions") or []}
        for c in contributions:
            row = rows.get(c.contribution_id)
            if row is None:
                raise CombineRefusal("assemble_wiring_mismatch", {
                    "contribution_id": c.contribution_id,
                    "law": "the assembly wires EXACTLY the generated "
                           "bindings rows; nothing else"})
            if row["owner_membrane"] != c.owner_membrane \\
                    or sorted(row["produces"]) != sorted(c.produces):
                raise CombineRefusal("assemble_wiring_mismatch", {
                    "contribution_id": c.contribution_id,
                    "bindings": row,
                    "wired": {"owner": c.owner_membrane,
                              "produces": sorted(c.produces)}})
        if len(rows) != len(contributions):
            raise CombineRefusal("assemble_wiring_mismatch", {
                "law": "every bindings row is wired exactly once",
                "bindings_rows": sorted(rows), "wired":
                    sorted(c.contribution_id for c in contributions)})
        self.exchange_writer_id = CONNECTIONS[0]["exchange_writer_id"]

    # -- stepping ------------------------------------------------------------------
    def step(self) -> dict:
        self.last_window_start = self.scheduler.store.values()
        result = self.scheduler.run_window({})
        self.window_index += 1
        # PER CONNECTION: the ONE signed exchange quantity, proven bitwise
        # (every member's accessor == the owner's accessor == the record):
        start = self.last_window_start
        window_proofs = []
        for conn in CONNECTIONS:
            owner = conn["owner"]
            q_owner = graph_runtime.exchange_accessor(
                self.membranes[owner], conn["connection_id"])(start)
            q_values = {"owner:" + owner: q_owner}
            for mid in conn["members"]:
                if mid == owner:
                    continue
                q_m = graph_runtime.exchange_accessor(
                    self.membranes[mid], conn["connection_id"])(start)
                q_values["member:" + mid] = q_m
            q_record = self.scheduler.store.read(conn["exchange_state_id"])
            q_values["record"] = q_record
            bitwise = len(set(q_values.values())) == 1
            if not bitwise:
                raise CombineRefusal("assemble_exchange_not_one_quantity", {
                    "window": self.window_index,
                    "connection_id": conn["connection_id"],
                    "q_values": q_values,
                    "law": "ONE signed exchange quantity per connection: "
                           "every member's independently compiled accessor "
                           "and the stored record must agree BITWISE every "
                           "window"})
            window_proofs.append({
                "window": self.window_index,
                "connection_id": conn["connection_id"],
                "q_values": q_values, "bitwise_equal": True})
        self.q_proofs.extend(window_proofs)
        return result

    def run_to(self, t_s: float) -> dict:
        last = None
        target = round(t_s / self.dt)
        while self.window_index < target:
            last = self.step()
        return last or {"values": self.scheduler.store.values(),
                        "state_hash": self.scheduler.store.hash()}

    # -- queries -----------------------------------------------------------------
    def values(self) -> dict:
        return self.scheduler.store.values()

    def state_value(self, mid: str, var: str) -> float:
        return self.scheduler.store.read(self.state_ids[(mid, var)])

    def exchange_record(self, connection_id: str | None = None) -> float:
        cid = connection_id or CONNECTIONS[0]["connection_id"]
        return self.scheduler.store.read(
            self.exchange_state_ids[cid])

    @property
    def parameters_flat(self) -> dict:
        cached = getattr(self, "_params_flat", None)
        if cached is None:
            flat = {}
            for m in self.spec["membranes"]:
                for p in m.get("parameters") or []:
                    flat[p["var"]] = float(p["value"])
            for conn in self.spec["connections"]:
                for p in conn.get("parameters") or []:
                    flat[p["var"]] = float(p["value"])
            for p in self.spec.get("global_parameters") or []:
                flat[p["var"]] = float(p["value"])
            cached = flat
            self._params_flat = cached
        return cached

    def conserved_value(self) -> float:
        cq = self.spec["assembly"]["conserved_quantity"]
        scope = dict(self.parameters_flat)
        for (mid, var), sid in self.state_ids.items():
            scope[var] = self.scheduler.store.read(sid)
        return float(evaluate(parse(cq["expr"]), scope))


def build(dt: float, initial_case_id: str = "nominal", max_workers: int = 4,
          interleave_seed: int | None = None) -> AssemblyRun:
    """The GENERATED graph assembly: verify inputs, load the manifest-bound
    member modules, validate them against the ABI + the graph layer, build
    the context, wire per the GENERATED bindings table through the ABI
    factories, cross-check, schedule."""
    require_assembly_inputs()
    mods, adapters, context, gates = load_members()
    return AssemblyRun(context, adapters, gates, dt, initial_case_id,
                       max_workers, interleave_seed)
'''


# ---------- generation ----------------------------------------------------------------

def _canon_json(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _a_tag(assembly_id: str) -> str:
    parts = assembly_id.split(".")
    if len(parts) >= 3 and parts[-1] == "v1":
        return ".".join(parts[1:-1])
    return assembly_id.replace(".", "_")


def _sha_file_or_refuse(lane_root: pathlib.Path, rel: str, want: str,
                        lane_of_record=None) -> str:
    path = lane_root / rel
    if not path.is_file():
        raise CombineRefusal(E_LANDED_DRIFT, {
            "path": rel, "law": "the declared module file is missing",
            "lane_of_record": lane_of_record})
    got = sha256_bytes(path.read_bytes())
    if got != want:
        raise CombineRefusal(E_LANDED_DRIFT, {
            "path": rel, "expected": want, "observed": got,
            "lane_of_record": lane_of_record,
            "law": "the manifest pins the bytes; a drifted module is never "
                   "wired"})
    return got


def _render_bindings_module(spec: dict, spec_sha: str, canon_sha: str,
                            bindings: dict, graph_desc: str) -> str:
    text = _BINDINGS_MODULE_TEMPLATE
    replacements = {
        "@@ASSEMBLY_ID@@": bindings["assembly_id"],
        "@@GRAPH_DESC@@": graph_desc,
        "@@SPEC_ID@@": spec["spec_id"],
        "@@SPEC_SHA@@": spec_sha,
        "@@SPEC_CANON_SHA@@": canon_sha,
        "@@SPEC_JSON@@": json.dumps(spec, sort_keys=True),
        "@@BINDINGS_JSON@@": json.dumps(bindings, indent=2, sort_keys=True),
    }
    for token, value in replacements.items():
        text = text.replace(token, value)
    if "@@" in text:
        raise CombineRefusal(E_RENDER_ERROR, {
            "law": "an @@ token survived the bindings rendering"})
    return text


def _check_manifest(manifest: dict, member_ids: list, assembly_id: str,
                    spec_relative_path: str, bindings_relpath: str,
                    lane_root: pathlib.Path) -> dict:
    if not isinstance(manifest, dict) or \
            manifest.get("schema") != MANIFEST_SCHEMA:
        raise CombineRefusal(E_MANIFEST_INVALID, {
            "schema": manifest.get("schema") if isinstance(manifest, dict)
            else None, "expected": MANIFEST_SCHEMA})
    if manifest.get("abi_version") != membrane_abi.ABI_VERSION:
        raise CombineRefusal("abi_version_mismatch", {
            "manifest": manifest.get("abi_version"),
            "expected": membrane_abi.ABI_VERSION})
    if manifest.get("assembly_id") != assembly_id:
        raise CombineRefusal(E_MANIFEST_INVALID, {
            "assembly_id": manifest.get("assembly_id"),
            "expected": assembly_id})
    if manifest.get("spec_relative_path") != spec_relative_path:
        raise CombineRefusal(E_MANIFEST_INVALID, {
            "spec_relative_path": manifest.get("spec_relative_path"),
            "expected": spec_relative_path})
    if manifest.get("generated_bindings_relative_path") != bindings_relpath:
        raise CombineRefusal(E_MANIFEST_INVALID, {
            "generated_bindings_relative_path":
                manifest.get("generated_bindings_relative_path"),
            "expected": bindings_relpath})
    impls = manifest.get("implementations")
    if not isinstance(impls, list) or not impls:
        raise CombineRefusal(E_MANIFEST_INVALID, {
            "law": "implementations must be a nonempty list"})
    file_of = {}
    landed = {}
    lanes = {}
    adapters = {}
    wraps_of = {}
    bound_ids = []
    for entry in impls:
        if not isinstance(entry, dict) or sorted(entry) != sorted(_IMPL_KEYS):
            raise CombineRefusal(E_MANIFEST_INVALID, {
                "entry_keys": sorted(entry) if isinstance(entry, dict)
                else None, "expected": sorted(_IMPL_KEYS)})
        mid = entry["membrane_id"]
        if mid not in member_ids:
            raise CombineRefusal(E_MANIFEST_INVALID, {
                "membrane_id": mid, "members": sorted(member_ids),
                "law": "the manifest binds exactly the spec's member "
                       "membranes; an unknown id is a mismatch"})
        if mid in bound_ids:
            raise CombineRefusal(E_MANIFEST_INVALID, {
                "membrane_id": mid,
                "law": "EXACTLY ONE implementation per member membrane"})
        bound_ids.append(mid)
        sha = entry["module_sha256"]
        if (not isinstance(sha, str) or len(sha) != 64
                or any(c not in "0123456789abcdef" for c in sha)):
            raise CombineRefusal(E_MANIFEST_INVALID, {
                "membrane_id": mid, "module_sha256": sha})
        adapter_file = entry["module_file"]
        _sha_file_or_refuse(lane_root, adapter_file, sha)
        wraps = entry["wraps"]
        if not isinstance(wraps, dict) or sorted(wraps) != sorted(
                _WRAPS_KEYS):
            raise CombineRefusal(E_MANIFEST_INVALID, {
                "membrane_id": mid, "wraps_keys":
                    sorted(wraps) if isinstance(wraps, dict) else None,
                "expected": sorted(_WRAPS_KEYS)})
        _sha_file_or_refuse(lane_root, wraps["file"], wraps["sha256"],
                            wraps["lane_of_record"])
        file_of[mid] = adapter_file
        adapters[mid] = {"file": adapter_file, "sha256": sha}
        landed[wraps["file"]] = wraps["sha256"]
        lanes[wraps["file"]] = wraps["lane_of_record"]
        wraps_of[mid] = wraps["file"]
    if sorted(bound_ids) != sorted(member_ids):
        raise CombineRefusal(E_MANIFEST_INVALID, {
            "bound": sorted(bound_ids), "members": sorted(member_ids),
            "law": "EVERY member membrane needs exactly one implementation "
                   "binding"})
    if not isinstance(manifest.get("provenance_labels"), dict) or \
            not manifest["provenance_labels"].get("status"):
        raise CombineRefusal(E_MANIFEST_INVALID, {
            "law": "provenance attestations stay SEPARATELY LABELED; the "
                   "manifest must carry the labeled provenance section"})
    return {"file_of": file_of, "adapters": adapters, "landed": landed,
            "lanes": lanes, "wraps_of": wraps_of}


def generate_graph_wiring(lane_root, spec_relative_path: str,
                          manifest_relative_path: str, out_dir=None) -> dict:
    """Generate the graph assembly-wiring artifacts from the frozen spec
    bytes, the bindings table (loaded or freshly emitted), the versioned
    ABI + graph layer, and the declared implementation-binding manifest.
    Deterministic; refuses by name on any invalid or drifted input."""
    if membrane_abi.ABI_VERSION != "chimera.membrane_abi.v1":
        raise CombineRefusal("abi_version_mismatch", {
            "law": "the generator is bound to chimera.membrane_abi.v1"})
    lane_root = pathlib.Path(lane_root)
    raw = (lane_root / spec_relative_path).read_bytes()
    try:
        spec = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise CombineRefusal(E_SPEC_UNPARSEABLE, {"error": str(exc)})
    report = spec_format.validate_spec(spec)
    if not report.valid:
        raise CombineRefusal(E_SPEC_INVALID, {"errors": report.errors})
    raw_sha = sha256_bytes(raw)
    canon_sha = sha256_text(canonical(spec))

    # ---- the graph class law (from the declarations) ------------------------
    members = [m["membrane_id"] for m in spec["membranes"]]
    conns = spec["connections"]
    if len(members) < 2 or len(conns) < 1:
        raise CombineRefusal(E_CLASS_UNSUPPORTED, {
            "members": len(members), "connections": len(conns),
            "law": "the graph class wires N >= 2 membranes and M >= 1 "
                   "two-member connections"})
    for conn in conns:
        if len(conn.get("members") or []) != 2:
            raise CombineRefusal(E_CLASS_UNSUPPORTED, {
                "connection_id": conn.get("connection_id"),
                "law": "every connection is a two-member connection "
                       "(the frozen format law)"})
        owner = (conn.get("exchange") or {}).get("owner_membrane")
        if owner not in (conn.get("members") or []):
            raise CombineRefusal(E_CLASS_UNSUPPORTED, {
                "connection_id": conn.get("connection_id"),
                "law": "the exchange-record owner must be a member"})

    assembly_id = spec["assembly"]["assembly_id"]
    a_tag = _a_tag(assembly_id)
    # the manifest is parsed early for its DECLARED bindings path (the
    # artifact pins it); the full manifest validation runs below
    manifest_path = lane_root / manifest_relative_path
    try:
        manifest = json.loads(manifest_path.read_bytes().decode("utf-8"))
    except Exception as exc:
        raise CombineRefusal(E_MANIFEST_UNPARSEABLE, {"error": str(exc)})
    # the bindings artifact path is the MANIFEST'S DECLARED input (the
    # artifact pins it); the graph stage does NOT force a filename prefix --
    # the delivered pair modules' single-bindings glob law constrains where
    # graph bindings may live, and the manifest records that choice
    bindings_relpath = manifest.get("generated_bindings_relative_path")
    if not isinstance(bindings_relpath, str) or not bindings_relpath:
        raise CombineRefusal(E_MANIFEST_INVALID, {
            "law": "the manifest must declare the bindings artifact path",
            "got": bindings_relpath})
    artifact_name = f"{ARTIFACT_PREFIX}.{a_tag}.v1.py"
    graph_desc = f"{len(members)}-membrane/{len(conns)}-connection graph"

    # ---- the bindings table (loaded from its pinned artifact, or emitted) ---
    bindings_path = lane_root / bindings_relpath
    emitted_bindings = False
    if bindings_path.is_file():
        bindings_sha = sha256_bytes(bindings_path.read_bytes())
        spec_mod = importlib.util.spec_from_file_location(
            "graph_generation_bindings", bindings_path)
        bindings_module = importlib.util.module_from_spec(spec_mod)
        sys.modules["graph_generation_bindings"] = bindings_module
        spec_mod.loader.exec_module(bindings_module)
        if bindings_module.SPEC_RAW_SHA256 != raw_sha:
            raise CombineRefusal(E_BINDINGS_MISMATCH, {
                "path": bindings_relpath, "spec": raw_sha,
                "bindings": bindings_module.SPEC_RAW_SHA256})
        bindings = bindings_module.BINDINGS
    else:
        # the lift's declared emission: the deterministic bindings artifact
        # from the SAME generic derivation (the manifest pre-declared this
        # path; the frozen stage-1 generator does not emit it for graphs)
        bindings = build_bindings(spec, raw_sha, canon_sha)
        bindings_text = _render_bindings_module(spec, raw_sha, canon_sha,
                                                bindings, graph_desc)
        bindings_sha = sha256_text(bindings_text)
        emitted_bindings = True

    expected_table = build_bindings(spec, raw_sha, canon_sha)
    if bindings != expected_table:
        raise CombineRefusal(E_BINDINGS_MISMATCH, {
            "path": bindings_relpath,
            "law": "the bindings table must equal a fresh derivation from "
                   "the frozen spec bytes",
            "loaded": bindings, "derived": expected_table})

    # ---- the declared implementation-binding manifest -----------------------
    # (parsed above for its declared bindings path; validated here)
    tables = _check_manifest(manifest, members, assembly_id,
                             spec_relative_path, bindings_relpath,
                             lane_root)
    file_of = tables["file_of"]

    # ---- generation-time ABI conformance of every bound module --------------
    conformance = {}
    for mid in sorted(file_of):
        adapter = membrane_abi.load_module_file(
            lane_root / file_of[mid],
            "graph_generation_adapter_" + pathlib.Path(file_of[mid]).stem)
        conformance[mid] = membrane_abi.validate_module(adapter, mid)

    # ---- the per-connection plan (deterministic, from the declarations) -----
    state_ids, state_owner, exchange_state_ids = \
        spec_runtime.resolve_ids(spec)
    connections_plan = []
    for conn in conns:
        cid = conn["connection_id"]
        ex = conn["exchange"]
        xsid = exchange_state_ids[cid]
        ex_rows = [r for r in expected_table["contributions"]
                   if r["produces"] == [xsid]]
        if len(ex_rows) != 1:
            raise CombineRefusal(E_CLASS_UNSUPPORTED, {
                "connection_id": cid,
                "law": "exactly ONE bindings row produces each connection's "
                       "exchange record"})
        ledger_entries = {}
        for row in conn["transfer_law"]["per_membrane"]:
            ledger_entries[row["membrane_id"]] = \
                row["ledger_entry"]["entry_id"]
        connections_plan.append({
            "connection_id": cid,
            "exchange_state_id": xsid,
            "exchange_writer_id": ex_rows[0]["contribution_id"],
            "owner": ex["owner_membrane"],
            "qref": ex["quantity_ref"],
            "members": list(conn["members"]),
            "ledger_entries": ledger_entries,
        })

    # ---- the frozen interface pins (observed from the lane bytes) ----------
    frozen_interface = dict(PINS)
    frozen_interface[spec_relative_path] = raw_sha
    frozen_interface[bindings_relpath] = bindings_sha
    frozen_interface["membrane_abi.py"] = None
    frozen_interface["graph_runtime.py"] = None
    frozen_interface["graph_wiring_generate.py"] = None
    frozen_interface[manifest_relative_path] = None
    for mid in sorted(file_of):
        frozen_interface[file_of[mid]] = None
    # a freshly-EMITTED bindings artifact does not exist on disk yet; its
    # byte identity is already computed from the deterministic rendering
    for rel in sorted(frozen_interface):
        if rel == bindings_relpath and emitted_bindings:
            continue
        path = lane_root / rel
        if not path.is_file():
            raise CombineRefusal(E_FROZEN_MISSING, {"path": rel})
        frozen_interface[rel] = sha256_bytes(path.read_bytes())

    gen_sha = sha256_bytes(pathlib.Path(__file__).read_bytes())
    abi_sha = sha256_bytes((lane_root / "membrane_abi.py").read_bytes())
    graph_sha = sha256_bytes((lane_root / "graph_runtime.py").read_bytes())

    place_rows = "\n".join(
        "      " + r["contribution_id"] + "   (owner "
        + r["owner_membrane"] + ")"
        for r in expected_table["contributions"])

    text = _WIRING_TEMPLATE
    replacements = {
        "@@ASSEMBLY_ID@@": assembly_id,
        "@@GRAPH_DESC@@": graph_desc,
        "@@MEMBERS_JSON@@": json.dumps(members),
        "@@CONNECTIONS_JSON@@": json.dumps(
            connections_plan, indent=2, sort_keys=True),
        "@@PLACE_ROWS@@": place_rows,
        "@@SPEC_SHA@@": raw_sha,
        "@@SPEC_RELPATH@@": spec_relative_path,
        "@@BINDINGS_RELPATH@@": bindings_relpath,
        "@@BINDINGS_SHA@@": bindings_sha,
        "@@MANIFEST_RELPATH@@": manifest_relative_path,
        "@@MANIFEST_SHA@@": sha256_text(_canon_json(manifest)),
        "@@ABI_VERSION@@": membrane_abi.ABI_VERSION,
        "@@ABI_RELPATH@@": "membrane_abi.py",
        "@@ABI_SHA@@": abi_sha,
        "@@GRAPH_RELPATH@@": "graph_runtime.py",
        "@@GRAPH_SHA@@": graph_sha,
        "@@GEN_SHA@@": gen_sha,
        "@@LANDED_JSON@@": _canon_json(tables["landed"]).rstrip("\n"),
        "@@LANE_JSON@@": _canon_json(tables["lanes"]).rstrip("\n"),
        "@@WRAPS_OF_JSON@@": _canon_json(tables["wraps_of"]).rstrip("\n"),
        "@@ADAPTERS_JSON@@": _canon_json(tables["adapters"]).rstrip("\n"),
        "@@FROZEN_JSON@@": _canon_json(frozen_interface).rstrip("\n"),
        "@@MANIFEST_JSON@@": _canon_json(manifest).rstrip("\n"),
    }
    for token, value in replacements.items():
        text = text.replace(token, value)
    if "@@" in text:
        raise CombineRefusal(E_RENDER_ERROR, {
            "law": "an @@ token survived rendering", "artifact": artifact_name})

    outputs = []
    if out_dir is not None:
        out_dir = pathlib.Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if emitted_bindings:
            bpath = out_dir / pathlib.Path(bindings_relpath).name
            bpath.write_bytes(bindings_text.encode("utf-8"))
            outputs.append({"path": str(bpath).replace("\\", "/"),
                            "sha256": bindings_sha,
                            "bytes": len(bindings_text),
                            "kind": "bindings_emitted"})
        path = out_dir / artifact_name
        path.write_bytes(text.encode("utf-8"))
        outputs.append({"path": str(path).replace("\\", "/"),
                        "sha256": sha256_text(text), "bytes": len(text),
                        "kind": "assembly_wiring"})
    else:
        if emitted_bindings:
            outputs.append({"path": bindings_relpath,
                            "sha256": bindings_sha,
                            "bytes": len(bindings_text),
                            "kind": "bindings_emitted"})
        outputs.append({"path": artifact_name, "sha256": sha256_text(text),
                        "bytes": len(text), "kind": "assembly_wiring"})

    receipt = {
        "schema": GRAPH_RECEIPT_SCHEMA,
        "generator": "graph_wiring_generate.py (mathspec lane, the graph "
                     "stage; the Order-17 lift)",
        "generator_sha256": gen_sha,
        "abi": {"version": membrane_abi.ABI_VERSION,
                "module": "membrane_abi.py", "sha256": abi_sha,
                "graph_layer": {"module": "graph_runtime.py",
                                "sha256": graph_sha},
                "module_specific_branches": 0},
        "inputs": {
            "spec": {"path": spec_relative_path, "sha256": raw_sha},
            "bindings": {"path": bindings_relpath, "sha256": bindings_sha,
                         "freshly_emitted": emitted_bindings},
            "manifest": {"path": manifest_relative_path,
                         "canonical_sha256":
                             sha256_text(_canon_json(manifest))},
        },
        "bindings_gate": {
            "reference_only": bindings.get("reference_only"),
            "formulas_embedded": bindings.get("formulas_embedded"),
            "table_equals_fresh_derivation": True,
        },
        "abi_conformance_at_generation": conformance,
        "plan": {
            "assembly_id": assembly_id,
            "graph": graph_desc,
            "member_order": members,
            "connections": connections_plan,
            "contribution_placement":
                [r["contribution_id"] for r in expected_table["contributions"]],
            "implementation_bindings": {mid: file_of[mid]
                                        for mid in sorted(file_of)},
            "provenance": "SEPARATELY LABELED in the manifest "
                          "(provenance_labels); not part of the wiring path",
        },
        "outputs": outputs,
        "remaining_handwritten_decisions": "NONE on the wiring path: the "
            "implementation binding is the versioned manifest, the adapter "
            "protocol is superseded by the ABI, provenance stays separately "
            "labeled; the graph class law comes from the declarations",
        "law": "identical inputs -> byte-identical artifacts; from-scratch "
               "regeneration must equal the shipped artifacts byte-for-byte",
    }
    return receipt
