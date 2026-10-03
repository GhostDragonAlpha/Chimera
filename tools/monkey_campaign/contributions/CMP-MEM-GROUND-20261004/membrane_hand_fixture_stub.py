"""membrane_hand_fixture_stub.py -- the DECLARED FIXTURE EXTERIOR of the
hand side (membrane.hand_fixture_stub.v1) under chimera.membrane_abi.v1
(packet PKT-G3-MEMBRANE-GROUND; worker wk-membrane-ground).

INTERIOR LAW (read this first): membrane.hand.v1's interior stays hidden
(packet owned_scope read_only + the Captain's parallel-membrane order). THIS
MODULE IS NOT membrane.hand.v1. It carries exactly the hand side's seam
EXTERIOR as the packet's DECLARED FIXTURES state it while the hand side is
UNFINISHED (packet explicit_assumptions: "the hand side is UNFINISHED: its
press channel runs at the declared fixture impulse; the ground membrane
never writes press_channel_state"):

  - OWNED STATE  state.press_channel_state.hand_fixture_stub.v1 (contract
                 press_channel_state: owned by the hand side, direction out;
                 armed carries the fixture impulse magnitude 0.3 N*s,
                 released is exactly 0.0; no third state exists).
  - CONSUMER    the seam's contact records (q_jn, and the declared derived
                jt) are CONSUMED READ-ONLY: this member's ledgers re-read,
                never re-write. It exposes NO exchange_contribution -- the
                per-connection ONE-writer law gives the record to
                membrane.ground.v1 alone (contract state_ownership jn/jt;
                enforced by graph_runtime.validate_built_graph, and the
                mutant fixture that adds a writer is refused
                abi_exchange_writer_violation).
  - LEDGER      the pad-side bookings ground_seam.jn.into_hand_fixture (+q)
                and ground_seam.jt.into_hand_fixture (+jt), each written
                once per window (S1 counted-once).

Fixture class: fx.hand_press_impulse (jn 0.3 N*s per channel per tick at
dt 0.005 s; AUTHORED_DECLARED; actuator_qualified false; x_press ABSENT,
blocker NB-03). FIXTURE-BASED RESULTS ONLY: nothing here claims integrated
qualification, an actuator qualification, or the pair RUN with the real
membrane.hand.v1 (declared_pending, owed by the assembly task).

All math is compiled from the frozen spec bytes
(spec/ground_walk_contact.spec.v1.json, sha256 7e6700dd...) through the
frozen closed evaluator; the frozen-input gate re-verifies every pinned byte
at every build and refuses drift BY NAME. Stdlib-only, deterministic.
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "pinned_inputs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from combine_core import CombineRefusal, Contribution  # noqa: E402
import spec_lang  # noqa: E402
import spec_runtime  # noqa: E402
from spec_lang import evaluate, parse  # noqa: E402

# ---------- the versioned identity --------------------------------------------------

ABI_VERSION = "chimera.membrane_abi.v1"
IMPLEMENTS_MEMBRANE_ID = "membrane.hand_fixture_stub.v1"

CONNECTION_ID = "conn.hand_ground_contact.v1"
CONTRIBUTION_ID = "contribution.hand_fixture_stub.integrate"
JT_RECORD_ID = "jt"

# ---------- the frozen-input pin table (drift-refused at EVERY build) ---------------

PINNED_INPUTS = {
    "spec/ground_walk_contact.spec.v1.json":
        "abe378ab56e418778ab1fa4fc0c7c52ea7bb8e66029726df6f847c40b0cc69ea",
    "pinned_inputs/pc.hand_ground_contact.v1.json":
        "a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104",
    "pinned_inputs/g04_experiment_receipt.json":
        "0d622f3610a4d23f52655908effe474694867a20e639747dc48535a419319ce8",
    "pinned_inputs/hand_ground_declaration.v1.json":
        "a5a82d526f160be671837307419abc0f1c33a0f0636bd13220fb9b1797c3d773",
    "membrane_abi.py":
        "80c5b36574a442fa829f0fa3bea52f088f32c6db5bc316e2e77c54ee03811665",
    "spec_lang.py":
        "6ac52e650ae6024faaa4b6f9245eeb3421a1c793cb92ecd89c3e373e83dc8e52",
    "spec_format.py":
        "7e0377929cd0acee2068c5ad75e9d73e95a985e77cfde072be41e09897b07059",
    "spec_runtime.py":
        "423fca7089fc28a39825c50eaee8b4968b4beebd778807cb32eaf2e95e2cbd31",
    "graph_runtime.py":
        "c7a96b07dfe4da5056a5c9b39aefa3f3d178c3be01084c823dbd4a9084fc3860",
    "pinned_inputs/combine_core.py":
        "8bfe6949b6854341801106649423c100201c2ed7989c09e3aed0af3f4c860712",
    "pinned_inputs/PORT_CONTRACT_V2.py":
        "0f1b7dfec2a7335bdf99dd4e8f2f58e395fd179d1e2c2d2b88975dbceee0b29d",
    "pinned_inputs/port_contract_schema.v2.json":
        "69161d32229a69f89b30bca27c95221b1d04e485f17972e96d0ed1a905c9a623",
}


def _sha256_file(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def verify_frozen_inputs() -> dict:
    identities = {}
    for rel, want in sorted(PINNED_INPUTS.items()):
        path = _HERE / rel
        if not path.is_file():
            raise CombineRefusal("spec_pinned_input_drift", {
                "path": rel, "expected": want,
                "law": "a pinned input of " + IMPLEMENTS_MEMBRANE_ID +
                       " is missing; the frozen-input contract refuses"})
        got = _sha256_file(path)
        if got != want:
            raise CombineRefusal("spec_pinned_input_drift", {
                "path": rel, "expected": want, "observed": got,
                "law": "pinned bytes drifted; " + IMPLEMENTS_MEMBRANE_ID +
                       " never builds on drifted bytes"})
        identities[rel] = got
    return identities


def build(context, dt):
    identities = verify_frozen_inputs()
    if not hasattr(context, "spec_raw_sha256") or not hasattr(context, "spec"):
        raise CombineRefusal("spec_pinned_input_drift", {
            "law": "the context must be a membrane_abi.SpecContext binding "
                   "the verified spec bytes"})
    spec_sha = identities["spec/ground_walk_contact.spec.v1.json"]
    if context.spec_raw_sha256 != spec_sha:
        raise CombineRefusal("spec_pinned_input_drift", {
            "law": "the context identity does not match this module's "
                   "verified spec bytes",
            "context": context.spec_raw_sha256, "pinned": spec_sha})
    spec = context.spec
    if spec.get("spec_id") != "spec.ground_walk_contact.v1":
        raise CombineRefusal("spec_pinned_input_drift", {
            "law": "the context spec is not this module's spec of record",
            "spec_id": spec.get("spec_id")})
    dt = context.require_dt_admissible(dt)

    section = context.section(IMPLEMENTS_MEMBRANE_ID)
    conn = context.connection(CONNECTION_ID)
    state_ids, _owner, exchange_state_ids = spec_runtime.resolve_ids(spec)
    q_jn_id = exchange_state_ids[CONNECTION_ID]
    press_id = state_ids[(IMPLEMENTS_MEMBRANE_ID, "press_channel_state")]

    ex_scope_template = {}
    for cons in conn.get("consumed") or []:
        ex_scope_template[cons["quantity_ref"]] = None
    exchange_ast = parse(conn["exchange"]["expr"])
    conn_params = {p["var"]: float(p["value"]) for p in conn.get("parameters") or []}
    params = {p["var"]: float(p["value"]) for p in section.get("parameters") or []}

    records = {r["record_id"]: r for r in
               (spec.get("declared_records") or {}).get("records") or []}
    jt_ast = parse(records[JT_RECORD_ID]["expr"])
    jt_entry_ids = list(records[JT_RECORD_ID]["ledger_entry_ids"])

    class _HandFixtureStub:
        """The built declared-fixture-exterior object (ABI surface). A
        non-owner of the seam's contact record: NO exchange_contribution,
        by the ABI's ONE-writer law."""

        membrane_id = IMPLEMENTS_MEMBRANE_ID

        def ownership(self):
            return {
                "membrane_id": IMPLEMENTS_MEMBRANE_ID,
                "owned_states": [
                    {"var": "press_channel_state", "unit": "N*s",
                     "state_id": press_id},
                ],
                "contribution_id": CONTRIBUTION_ID,
                "single_writer_law":
                    "press_channel_state: owned by the hand side (here its "
                    "declared fixture exterior; contract state_ownership "
                    "press_channel_state direction out); written ONCE by the "
                    "declared initial case (armed_hold 0.3 / released 0.0) "
                    "and never re-written at runtime. The seam's contact "
                    "records are NOT owned here: they are consumed "
                    "read-only (ledgers re-read, never re-write).",
            }

        def ports(self):
            return section.get("ports") or {}

        # -- the ONE shared exchange closure (consumer accessor) --------------
        def exchange_quantity(self, view) -> float:
            scope = dict(conn_params)
            for cons in conn.get("consumed") or []:
                qv = cons["quantity_ref"]
                sid = state_ids[(cons["from_membrane"], qv)]
                scope[qv] = view[sid]
            return float(evaluate(exchange_ast, scope))

        # -- the declared derived jt record (consumer accessor) ---------------
        def jt_record(self, view) -> float:
            scope = dict(conn_params)
            scope["q_jn"] = self.exchange_quantity(view)
            return float(evaluate(jt_ast, scope))

        # -- contributions -----------------------------------------------------
        def contribution(self):
            """The fixture integrate contribution: holds the press state's
            declared law in-step (armed fixture bound; no third state) and
            NEVER writes it at runtime (the declared case is its writer);
            emits the pad-side seam ledger bookings (re-read, counted once)."""
            def compute(view, ctx):
                press = view[press_id]
                if press < 0.0:
                    raise CombineRefusal("ref.stub.press_state_negative", {
                        "state_id": press_id, "observed": press,
                        "law": "ref.stub.press_state_negative"})
                if press > params["press_channel_jn_ns_per_tick"]:
                    raise CombineRefusal("ref.stub.press_state_above_fixture", {
                        "state_id": press_id, "observed": press,
                        "bound": params["press_channel_jn_ns_per_tick"],
                        "law": "pre.stub.fixture_bound: the declared fixture "
                               "bound (x_press is ABSENT, NB-03; a value "
                               "above the fixture point is inadmissible for "
                               "qualification claims)"})
                q_jn = self.exchange_quantity(view)
                jt = self.jt_record(view)
                ledger = [
                    {"entry_id": "ground_seam.jn.into_hand_fixture",
                     "unit": "N*s", "value": q_jn,
                     "sign_convention": "+: the pad-side ledger books the "
                                        "record once per tick (S2, own "
                                        "surface normal)"},
                    {"entry_id": jt_entry_ids[0], "unit": "N*s", "value": jt,
                     "sign_convention": "+: the forward push-off booking on "
                                        "the pad side (S2)"},
                ]
                # ZERO states written: the declared case is the writer.
                return {"states": {}, "ledger": ledger}
            return Contribution(CONTRIBUTION_ID, IMPLEMENTS_MEMBRANE_ID,
                                [press_id], compute)

    return _HandFixtureStub()
