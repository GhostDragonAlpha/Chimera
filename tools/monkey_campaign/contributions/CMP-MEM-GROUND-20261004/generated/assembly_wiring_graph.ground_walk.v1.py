"""GENERATED FILE -- mathspec lane, graph_wiring_generate.generate_graph_wiring. DO NOT HAND-EDIT.

GENERATED ASSEMBLY WIRING (GRAPH PATH) for assembly.ground_walk.v1 -- the
N-membranes/M-connections assembly (the 2-membrane/1-connection graph), stage-general.
Generated from the frozen spec bytes + the GENERATED bindings table + the
VERSIONED ABI chimera.membrane_abi.v1 + graph_runtime (the graph-class
validation/contract layer) + the DECLARED implementation-binding manifest.
Every member module is constructed and wired through THE SAME ABI code path
(build(context, dt), graph_runtime.validate_built_graph with per-connection
writer scoping, contribution() on every member, exchange_contribution() on
each connection's owner only): there is NO module-specific branch and NO
per-module adapter-protocol table.

Generation inputs (byte identities of record):
  spec        spec/ground_walk_contact.spec.v1.json sha256=abe378ab56e418778ab1fa4fc0c7c52ea7bb8e66029726df6f847c40b0cc69ea
  bindings    generated/bindings.ground_walk.v1.py sha256=f5a6bc3ae70f94ecc52dbc08b967b54f4796dcbff3598850d34fbd638b08b91f
  abi         membrane_abi.py sha256=80c5b36574a442fa829f0fa3bea52f088f32c6db5bc316e2e77c54ee03811665
  graph       graph_runtime.py sha256=c7a96b07dfe4da5056a5c9b39aefa3f3d178c3be01084c823dbd4a9084fc3860
  manifest    abi_binding_manifest.ground_walk.v1.json canonical sha256=8f9e7988cfe0302408c509ec2c9d1eacd04a3ba6ec99b542bb594ea354af0533
  generator   graph_wiring_generate.py sha256=8637058fe459b7a29c9582f604d494e7d37385b34fc71557846b59cd77dbd723

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
ASSEMBLY_ID = "assembly.ground_walk.v1"
MEMBERS = json.loads(r'''["membrane.ground.v1", "membrane.hand_fixture_stub.v1"]''')      # bindings states order
CONNECTIONS = json.loads(r'''[
  {
    "connection_id": "conn.hand_ground_contact.v1",
    "exchange_state_id": "state.q_jn.hand_ground_contact.v1",
    "exchange_writer_id": "contribution.hand_ground_contact.exchange",
    "ledger_entries": {
      "membrane.ground.v1": "ground_seam.jn.into_ground",
      "membrane.hand_fixture_stub.v1": "ground_seam.jn.into_hand_fixture"
    },
    "members": [
      "membrane.hand_fixture_stub.v1",
      "membrane.ground.v1"
    ],
    "owner": "membrane.ground.v1",
    "qref": "q_jn"
  }
]''')
SPEC_RAW_SHA256 = "abe378ab56e418778ab1fa4fc0c7c52ea7bb8e66029726df6f847c40b0cc69ea"
SPEC_RELPATH = "spec/ground_walk_contact.spec.v1.json"
BINDINGS_RELPATH = "generated/bindings.ground_walk.v1.py"
BINDINGS_SHA256 = "f5a6bc3ae70f94ecc52dbc08b967b54f4796dcbff3598850d34fbd638b08b91f"
MANIFEST_RELPATH = "abi_binding_manifest.ground_walk.v1.json"
ABI_VERSION = "chimera.membrane_abi.v1"
ABI_MODULE_RELPATH = "membrane_abi.py"
GRAPH_RELPATH = "graph_runtime.py"

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
LANDED_MODULES = json.loads(r'''{
  "membrane_ground.py": "1684d3b23d7461274b39626b3b4dabcaa1b6b26968b3ccf21e906ceb39d4dbfe",
  "membrane_hand_fixture_stub.py": "6b9218c5aed7348f50a966697680ce12530a0ae0ea03daa8d49e8e67d0e463b2"
}''')

LANE_OF_RECORD = json.loads(r'''{
  "membrane_ground.py": "E:/ChimeraWork/monkey-coordination/membrane-ground (wk-membrane-ground, packet PKT-G3-MEMBRANE-GROUND)",
  "membrane_hand_fixture_stub.py": "E:/ChimeraWork/monkey-coordination/membrane-ground (wk-membrane-ground, the DECLARED FIXTURE EXTERIOR of the hand side; NOT membrane.hand.v1's interior - interior law)"
}''')

WRAPS_OF = json.loads(r'''{
  "membrane.ground.v1": "membrane_ground.py",
  "membrane.hand_fixture_stub.v1": "membrane_hand_fixture_stub.py"
}''')

# the manifest-bound member modules; the ABI fixes their surface, so only
# files + byte identities are declared
ADAPTER_FILES = json.loads(r'''{
  "membrane.ground.v1": {
    "file": "membrane_ground.py",
    "sha256": "1684d3b23d7461274b39626b3b4dabcaa1b6b26968b3ccf21e906ceb39d4dbfe"
  },
  "membrane.hand_fixture_stub.v1": {
    "file": "membrane_hand_fixture_stub.py",
    "sha256": "6b9218c5aed7348f50a966697680ce12530a0ae0ea03daa8d49e8e67d0e463b2"
  }
}''')

# the frozen interface the assembly consumes (drift-refused BEFORE anything
# runs): the landed modules, the member modules, the ABI, the graph layer,
# this generator stage, the manifest, the pinned runtime, the spec and the
# bindings artifact
FROZEN_INTERFACE = json.loads(r'''{
  "abi_binding_manifest.ground_walk.v1.json": "e039e9820fa2eb618c704412bf100d16e6c2edd6e7eeaee9618ea58e869e1391",
  "generated/bindings.ground_walk.v1.py": "f5a6bc3ae70f94ecc52dbc08b967b54f4796dcbff3598850d34fbd638b08b91f",
  "graph_runtime.py": "c7a96b07dfe4da5056a5c9b39aefa3f3d178c3be01084c823dbd4a9084fc3860",
  "graph_wiring_generate.py": "8637058fe459b7a29c9582f604d494e7d37385b34fc71557846b59cd77dbd723",
  "membrane_abi.py": "80c5b36574a442fa829f0fa3bea52f088f32c6db5bc316e2e77c54ee03811665",
  "membrane_ground.py": "1684d3b23d7461274b39626b3b4dabcaa1b6b26968b3ccf21e906ceb39d4dbfe",
  "membrane_hand_fixture_stub.py": "6b9218c5aed7348f50a966697680ce12530a0ae0ea03daa8d49e8e67d0e463b2",
  "pinned_inputs/PORT_CONTRACT_V2.py": "0f1b7dfec2a7335bdf99dd4e8f2f58e395fd179d1e2c2d2b88975dbceee0b29d",
  "pinned_inputs/combine_core.py": "8bfe6949b6854341801106649423c100201c2ed7989c09e3aed0af3f4c860712",
  "pinned_inputs/port_contract_schema.v2.json": "69161d32229a69f89b30bca27c95221b1d04e485f17972e96d0ed1a905c9a623",
  "spec/ground_walk_contact.spec.v1.json": "abe378ab56e418778ab1fa4fc0c7c52ea7bb8e66029726df6f847c40b0cc69ea"
}''')

# the full manifest (implementation binding + separately-labeled provenance)
MANIFEST = json.loads(r'''{
  "abi_version": "chimera.membrane_abi.v1",
  "assembly_id": "assembly.ground_walk.v1",
  "generated_bindings_relative_path": "generated/bindings.ground_walk.v1.py",
  "implementations": [
    {
      "membrane_id": "membrane.ground.v1",
      "module_file": "membrane_ground.py",
      "module_sha256": "1684d3b23d7461274b39626b3b4dabcaa1b6b26968b3ccf21e906ceb39d4dbfe",
      "wraps": {
        "file": "membrane_ground.py",
        "lane_of_record": "E:/ChimeraWork/monkey-coordination/membrane-ground (wk-membrane-ground, packet PKT-G3-MEMBRANE-GROUND)",
        "sha256": "1684d3b23d7461274b39626b3b4dabcaa1b6b26968b3ccf21e906ceb39d4dbfe"
      }
    },
    {
      "membrane_id": "membrane.hand_fixture_stub.v1",
      "module_file": "membrane_hand_fixture_stub.py",
      "module_sha256": "6b9218c5aed7348f50a966697680ce12530a0ae0ea03daa8d49e8e67d0e463b2",
      "wraps": {
        "file": "membrane_hand_fixture_stub.py",
        "lane_of_record": "E:/ChimeraWork/monkey-coordination/membrane-ground (wk-membrane-ground, the DECLARED FIXTURE EXTERIOR of the hand side; NOT membrane.hand.v1's interior - interior law)",
        "sha256": "6b9218c5aed7348f50a966697680ce12530a0ae0ea03daa8d49e8e67d0e463b2"
      }
    }
  ],
  "manifest_id": "abi_binding_manifest.ground_walk.v1",
  "provenance_labels": {
    "abi_role": "the ABI surface (chimera.membrane_abi.v1) carries NO provenance fields by design",
    "law": "lane_of_record strings are lane-process attestations of record, NOT derivable facts; the interior law means membrane.hand.v1's implementation was never read, listed or referenced - that absence is a process attestation, not a machine-verified fact",
    "status": "SEPARATELY LABELED -- provenance attestations are process claims, never part of the ABI surface (ABI section 6)"
  },
  "schema": "chimera.membrane_abi.binding_manifest.v1",
  "spec_relative_path": "spec/ground_walk_contact.spec.v1.json"
}''')


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

      contribution.ground.integrate   (owner membrane.ground.v1)
      contribution.hand_fixture_stub.integrate   (owner membrane.hand_fixture_stub.v1)
      contribution.hand_ground_contact.exchange   (owner membrane.ground.v1)
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
        if not vreport["valid"] or vreport["schema_major"] != 2 \
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
            if row["owner_membrane"] != c.owner_membrane \
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
