"""membrane_ground.py -- membrane.ground.v1 UNDER chimera.membrane_abi.v1
(the packet PKT-G3-MEMBRANE-GROUND implementation; worker wk-membrane-ground).

This module implements the GROUND side of external contract
pc.hand_ground_contact.v1 (sha256 a5431376..., pinned byte-exact at
pinned_inputs/pc.hand_ground_contact.v1.json): the authored walk surface,
the declared slope envelope with the walk-class verdict law, and the SEAM'S
CONTACT-RECORD OWNERSHIP. Derived ONLY from:

  1. the frozen ABI of record: membrane_abi.py (chimera.membrane_abi.v1,
     sha256 80c5b36574a442fa829f0fa3bea52f088f32c6db5bc316e2e77c54ee03811665),
  2. the frozen spec bytes of THIS lane:
     spec/ground_walk_contact.spec.v1.json (spec.ground_walk_contact.v1,
     sha256 7e6700dde3fc150a60a263dff13c8211f3d131cce5c2026538b6f69b95b83ae5),
  3. the pinned evidence inputs listed in PINNED_INPUTS below (contract,
     declaration, F05 composed/terrain metadata, FRICTION_SOURCES, the G04
     receipt), each byte-verified at every build and drift-refused BY NAME.

WHAT THIS MODULE OWNS (exactly the contract's state_ownership rows):
  - OWNED STATE  state.walk_plane_height.ground.v1 (var walk_plane_height,
                 unit m; +0.004 m authored plateau). SINGLE WRITER: the
                 composition flatten -- represented by the declared initial
                 case. THIS MODULE'S CONTRIBUTIONS NEVER WRITE IT: the store
                 log shows zero applies after the initial case, so "written
                 ONCE, no second writer" is provable from the runtime log
                 (packet T.GROUND_plane_identity).
  - EXCHANGE RECORD  state.q_jn.hand_ground_contact.v1 (contract jn, the
                 connection's primary transferred quantity): THE GROUND IS
                 THE SEAM'S CONTACT-RECORD OWNER (contract state_ownership
                 jn/jt owner membrane.ground.v1; bind B01/B02). The exchange
                 contribution writes the record EXACTLY ONCE per window (the
                 contact stage) and emits the ground-side ledger bookings
                 (S2: bitwise opposite of the pad-side bookings).
  - DERIVED RECORD jt (contract jt): the Coulomb elementwise_min pair cone
                 record jt = min(mu_hand, mu_surface) * q_jn, compiled from
                 the spec's declared_records AST (no private formula), booked
                 as the per-window ledger entry pair ground_seam.jt.*.
  - WALK SURFACE  walk_surface_verdict(): the declared class table (F05
                 walk_core rules) against the declared envelope 0.05 m/m
                 INCLUSIVE; OUTSIDE is reported with the TRUE slope, never
                 clamped (contract valid_input_ranges outside_behavior).

THE GROUND NEVER WRITES press_channel_state: that state is owned by the
hand side (here its declared fixture exterior, fx.hand_press_impulse,
blocker NB-03); this module exposes no writer for it and the pinned owner
store refuses any such attempt as combine_non_owner_write (verified by the
harness probe).

NAMED REFUSALS (never repaired, never silenced):
  build-time:  "spec_pinned_input_drift" (the pinned bytes or the context
               identity drifted), "spec_dt_not_admissible" (dt outside the
               DECLARED admissibility rows)
  in-step:     "ref.ground.jn_negative_press_record" (sign law jn >= 0) and
               the declared invariant inv.ground.plane_authored (the plane
               stays bitwise 0.004) fire BEFORE any payload is produced; the
               pinned scheduler restores the window-start snapshot.

INTERIOR LAW: membrane.hand.v1's interior stays hidden; this module reads
ONLY the contract's hand-side exterior declarations (never another lane's
implementation).

NO PHYSICS CLAIM: fixture-based membrane implementation; mu_s/mu_k stay
NAMED placeholders (fx.mu_placeholders, blockers NB-01/NB-02, REPIN ORDER 2);
no integrated qualification and no pair RUN is claimed.

All CPU execution goes through the campaign runner (NO_WORKTREES.md);
this file is stdlib-only and deterministic (no wall clock, no randomness).
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "pinned_inputs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from combine_core import CombineRefusal, Contribution  # noqa: E402
import spec_lang  # noqa: E402  (the frozen closed expression evaluator)
import spec_runtime  # noqa: E402  (resolve_ids -- THE ONE id scheme)
from spec_lang import evaluate, parse  # noqa: E402

# ---------- the versioned identity --------------------------------------------------

ABI_VERSION = "chimera.membrane_abi.v1"
IMPLEMENTS_MEMBRANE_ID = "membrane.ground.v1"

CONNECTION_ID = "conn.hand_ground_contact.v1"
CONTRIBUTION_ID = "contribution.ground.integrate"
EXCHANGE_CONTRIBUTION_ID = "contribution.hand_ground_contact.exchange"
JT_RECORD_ID = "jt"
WALK_CLASS_RECORD_ID = "walk_class"

# ---------- the frozen-input pin table (drift-refused at EVERY build) ---------------

PINNED_INPUTS = {
    "spec/ground_walk_contact.spec.v1.json":
        "abe378ab56e418778ab1fa4fc0c7c52ea7bb8e66029726df6f847c40b0cc69ea",
    "pinned_inputs/pc.hand_ground_contact.v1.json":
        "a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104",
    "pinned_inputs/hand_ground_declaration.v1.json":
        "a5a82d526f160be671837307419abc0f1c33a0f0636bd13220fb9b1797c3d773",
    "pinned_inputs/f05_composed_meta.json":
        "8168382ff2c852b9fbf2c49831ec2021c8c3f5178af95d6ffba0ce55fa3a42f7",
    "pinned_inputs/f05_terrain_meta.json":
        "ff15fb1db3dcc128a531d21ef64d3ab62ae78190b64db36f70b5d273c1425681",
    "pinned_inputs/FRICTION_SOURCES.md":
        "336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b",
    "pinned_inputs/g04_experiment_receipt.json":
        "0d622f3610a4d23f52655908effe474694867a20e639747dc48535a419319ce8",
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
    "graph_wiring_generate.py":
        "8637058fe459b7a29c9582f604d494e7d37385b34fc71557846b59cd77dbd723",
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
    """The frozen-input gate: hash-verify every pinned byte and return the
    identity table. Any drift (or missing pin) is refused BY NAME before
    anything is constructed."""
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


# ---------- construction -------------------------------------------------------------

def build(context, dt):
    """THE ABI constructor: build(context: membrane_abi.SpecContext, dt: float).
    Re-verifies the pinned bytes and the context identity, refuses a
    non-admissible dt, then compiles the module's whole math from the CONTEXT
    spec bytes (the ONE source of truth; no private formulas)."""
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
    plane_id = state_ids[(IMPLEMENTS_MEMBRANE_ID, "walk_plane_height")]

    # -- the ONE shared exchange closure (compiled from the spec AST) ---------
    ex_scope_template = {}
    for cons in conn.get("consumed") or []:
        ex_scope_template[cons["quantity_ref"]] = None
    exchange_ast = parse(conn["exchange"]["expr"])
    conn_params = {p["var"]: float(p["value"]) for p in conn.get("parameters") or []}

    # -- the declared derived records (declared_records section) --------------
    records = {r["record_id"]: r for r in
               (spec.get("declared_records") or {}).get("records") or []}
    if JT_RECORD_ID not in records or WALK_CLASS_RECORD_ID not in records:
        raise CombineRefusal("spec_validation_failed", {
            "law": "the spec's declared_records section must carry the jt "
                   "record and the walk-class record"})
    if records[JT_RECORD_ID].get("owner_membrane") != IMPLEMENTS_MEMBRANE_ID:
        raise CombineRefusal("spec_validation_failed", {
            "law": "the jt record's owner must be the ground membrane "
                   "(contract state_ownership jt)"})
    jt_ast = parse(records[JT_RECORD_ID]["expr"])
    jt_entry_ids = list(records[JT_RECORD_ID]["ledger_entry_ids"])

    # -- own parameters (the verdict thresholds + the envelope) ---------------
    params = {p["var"]: float(p["value"]) for p in section.get("parameters") or []}

    class _GroundMembrane:
        """The built membrane.ground.v1 object (ABI surface)."""

        membrane_id = IMPLEMENTS_MEMBRANE_ID

        def ownership(self):
            return {
                "membrane_id": IMPLEMENTS_MEMBRANE_ID,
                "owned_states": [
                    {"var": "walk_plane_height", "unit": "m",
                     "state_id": plane_id},
                ],
                "contribution_id": CONTRIBUTION_ID,
                "single_writer_law":
                    "walk_plane_height: written ONCE by the composition "
                    "flatten (the declared initial case); this membrane's "
                    "contributions never re-write it and any second writer "
                    "is refused by the pinned owner store. q_jn/jt: the "
                    "seam's contact records, owned HERE (contract "
                    "state_ownership); the hand side only consumes.",
            }

        def ports(self):
            return section.get("ports") or {}

        # -- the ONE shared exchange closure ---------------------------------
        def exchange_quantity(self, view) -> float:
            scope = dict(conn_params)
            for cons in conn.get("consumed") or []:
                qv = cons["quantity_ref"]
                sid = state_ids[(cons["from_membrane"], qv)]
                scope[qv] = view[sid]
            return float(evaluate(exchange_ast, scope))

        def exchange_quantity_for(self, view, connection_id) -> float:
            if connection_id != CONNECTION_ID:
                raise CombineRefusal("spec_validation_failed", {
                    "law": "unknown connection", "connection_id": connection_id})
            return self.exchange_quantity(view)

        # -- the declared derived jt record (the pair cone) -------------------
        def jt_record(self, view) -> float:
            scope = dict(conn_params)
            scope["q_jn"] = self.exchange_quantity(view)
            return float(evaluate(jt_ast, scope))

        def pair_mu(self) -> float:
            return min(conn_params["mu_hand"], conn_params["mu_surface"])

        # -- the walk surface verdict (declared_records walk_class) -----------
        def walk_surface_verdict(self, slope_m_per_m: float,
                                 surface_kind: str = "ground") -> dict:
            """TWO declared layers, exactly as F05 declares them: (1) the
            terrain difficulty CLASS of the slope (the walk_core degree
            thresholds; vocabulary, not a walker qualification), and (2) the
            WALK verdict against the declared envelope (inclusive at 0.05
            m/m; OUTSIDE reported with the TRUE slope, never clamped)."""
            envelope = params["slope_envelope_m_per_m"]
            row = {
                "slope_m_per_m": float(slope_m_per_m),
                "envelope_m_per_m": envelope,
                "surface_kind": surface_kind,
                "reported_slope_m_per_m": float(slope_m_per_m),
            }
            if surface_kind == "water":
                row.update({"verdict": "WATER", "class": "water",
                            "outside": False, "slope_deg": None})
                return row
            slope_deg = math.degrees(math.atan(float(slope_m_per_m)))
            row["slope_deg"] = slope_deg
            if slope_deg < params["walk_class_easy_lt_deg"]:
                row["class"] = "easy_lt10deg"
            elif slope_deg < params["walk_class_moderate_lt_deg"]:
                row["class"] = "moderate_10_20deg"
            elif slope_deg < params["walk_class_steep_lt_deg"]:
                row["class"] = "steep_20_30deg"
            else:
                row["class"] = "impassable_ge30deg"
            if float(slope_m_per_m) > envelope:
                # OUTSIDE reported with the TRUE slope; NEVER clamped
                # (contract valid_input_ranges outside_behavior verbatim).
                row.update({"verdict": "OUTSIDE", "outside": True,
                            "clamped": False})
            else:
                row.update({"verdict": "INSIDE", "outside": False})
            return row

        # -- contributions -----------------------------------------------------
        def contribution(self):
            """The ground integrate contribution: holds the plane's law
            in-step (the authored-plane invariant) and NEVER writes it (the
            composition flatten is the plane's single writer; the runtime
            store log must show zero applies after the initial case)."""
            def compute(view, ctx):
                plane = view[plane_id]
                if plane != 0.004:
                    raise CombineRefusal("inv.ground.plane_authored_violated", {
                        "state_id": plane_id, "observed": plane,
                        "law": "the authored walk plane is +0.004 m exactly "
                               "(inv.ground.plane_authored; a drifted plane "
                               "is a structural fault, never repaired)"})
                # ZERO states written: the single-writer law. Zero ledger:
                # the ground's seam bookings ride the exchange (contact)
                # stage contribution below.
                return {"states": {}, "ledger": []}
            return Contribution(CONTRIBUTION_ID, IMPLEMENTS_MEMBRANE_ID,
                                [plane_id], compute)

        def exchange_contribution(self):
            """THE CONTACT STAGE: the ground writes the seam's contact record
            EXACTLY ONCE per window and books the ground-side ledger entries
            (the reaction rows, bitwise opposite the pad side)."""
            def compute(view, ctx):
                q_jn = self.exchange_quantity(view)
                if q_jn < 0.0:
                    raise CombineRefusal("ref.ground.jn_negative_press_record", {
                        "record": q_jn_id, "observed": q_jn,
                        "law": "sign convention: jn >= 0 presses the two "
                               "surfaces together (ref.ground.jn_negative)"})
                jt = self.jt_record(view)
                plane = view[plane_id]
                if plane != 0.004:
                    raise CombineRefusal("inv.ground.plane_authored_violated", {
                        "state_id": plane_id, "observed": plane,
                        "law": "inv.ground.plane_authored: the record lives "
                               "at the authored +0.004 m plane only"})
                ledger = [
                    {"entry_id": "ground_seam.jn.into_ground", "unit": "N*s",
                     "value": -q_jn,
                     "sign_convention": "-: the world-anchor reaction books "
                                        "bitwise opposite the pad side (S2)"},
                    {"entry_id": jt_entry_ids[1], "unit": "N*s",
                     "value": -jt,
                     "sign_convention": "-: bitwise opposite the pad-side jt "
                                        "entry (S2 reciprocity)"},
                ]
                return {"states": {q_jn_id: q_jn}, "ledger": ledger}
            return Contribution(EXCHANGE_CONTRIBUTION_ID,
                                IMPLEMENTS_MEMBRANE_ID, [q_jn_id], compute)

    return _GroundMembrane()
