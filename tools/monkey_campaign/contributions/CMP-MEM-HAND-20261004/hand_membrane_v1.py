"""hand_membrane_v1.py -- THE HAND MEMBRANE MODULE (chimera.membrane_abi.v1).

Packet PKT-G3-MEMBRANE-HAND (criteria f3dbf093...), lane CMP-MEM-HAND-20261004,
worker wk-membrane-hand. Implements the HAND side of
conn.hand_ground_contact.v1 against the EXTERNAL contract only:

  - the press channel state (armed/released; owned by membrane.hand.v1;
    the ground side never writes it -- G07 X1 release account),
  - the press release latch (contract timing.latches.press_release_latch:
    once released, stays released until an EXPLICIT re-arm; every release
    tick records jn/jt at the share-scaled noise bars, never a partial press),
  - the 32-slot float32 observation seam delivery through the pinned G05
    seam implementation and its named delivery gates.

jn/jt are consumed READ-ONLY as seam records (single writer: the pinned
M06 solver at the contact; owner membrane.ground.v1). The neighbor's
interior stays HIDDEN (interior law): this module pins the neighbor's
CONTRACT-SIDE rows only (the byte-verified port contract), never any
ground-lane workspace.

SUBSTRATE (imported-not-forked; every byte re-verified at build; any drift
refuses BY NAME before anything is constructed):
  chimera.membrane_abi.v1 (mathspec/membrane_abi.py, sha 80c5b365...) and its
  pinned spec grammar/runtime; the pinned MAT2-M06/G04/G05/G07 modules and the
  F03 trunk mesh at their sealed hashes; the sealed G04/G05/G07 receipts; the
  pinned preregistration (commit 069c6857, blob sha e573d55d...).

NO PHYSICS CLAIM: press_channel_jn_ns_per_tick = 0.3 N*s is the DECLARED
fixture operating point (actuator_qualified false; x_press ABSENT, blocker
NB-03). Results produced with the declared fixtures are FIXTURE-BASED and
never discharge an integrated-qualification gate.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_CONTRIB = _HERE.parent

# --------------------------------------------------------------------------
# pinned bytes (the frozen-input contract): full sha256 identities
# --------------------------------------------------------------------------

ABI_VERSION = "chimera.membrane_abi.v1"
IMPLEMENTS_MEMBRANE_ID = "membrane.hand.v1"
CONNECTION_ID = "conn.hand_ground_contact.v1"

MATHSPEC_DIR = pathlib.Path("E:/ChimeraWork/monkey-coordination/mathspec")

SPEC_REL = "spec/hand_press_seam.spec.v1.json"

# absolute external pins (sealed evidence + the proven ABI/grammar substrate)
_EXTERNAL_PINS = {
    "E:/ChimeraWork/monkey-coordination/compiler-compile/PORT_CONTRACT.hand_ground_contact.v1.json":
        "a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104",
    "E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/numerical/experiment_receipt.json":
        "0d622f3610a4d23f52655908effe474694867a20e639747dc48535a419319ce8",
    "E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/report/REPORT.md":
        "dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8",
    "E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/numerical/falsifier_receipt.json":
        "04ef594cb7aa856e3afcd9b767e75c5c0dc44206f4c3db16ce678a35886f7fb2",
    "E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G05/numerical/experiment_receipt.json":
        "468185796db949ffd97b7e390de4adbc80aef74d1021445a8cfa28a74ef3dfbe",
    "E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G05/report/REPORT.md":
        "1e5fcc7f81b5bd7b0ae3b460c72d5ed190510f66db4793c6b2e99756da8c8524",
    "E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G07/report/REPORT.md":
        "34a4a095e1f4b3e5c87160a77e399c5c27a38202c1ad3675b0bcbf70d4b956a1",
    str(MATHSPEC_DIR / "membrane_abi.py"):
        "80c5b36574a442fa829f0fa3bea52f088f32c6db5bc316e2e77c54ee03811665",
    str(MATHSPEC_DIR / "spec_format.py"):
        "7e0377929cd0acee2068c5ad75e9d73e95a985e77cfde072be41e09897b07059",
    str(MATHSPEC_DIR / "spec_lang.py"):
        "6ac52e650ae6024faaa4b6f9245eeb3421a1c793cb92ecd89c3e373e83dc8e52",
    str(MATHSPEC_DIR / "spec_runtime.py"):
        "423fca7089fc28a39825c50eaee8b4968b4beebd778807cb32eaf2e95e2cbd31",
}

# in-package pins (materialized reads at the pinned base; sealed hashes)
_PACKAGE_PINS = {
    "PREREGISTRATION.md":
        "e573d55df48fb1ced37c241057ec7c5dd1cec592c7e8393d1def04c28429cfc0",
    "../MAT2-M06/local_contact.py":
        "1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc",
    "../MAT2-M06/contact_law.json":
        "583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b",
    "../MAT2-G04/grip_contact.py":
        "0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245",
    "../MAT2-G05/contact_support_obs.py":
        "3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3",
    "../MAT2-G07/release_fall_account.py":
        "78b5cc66f7019fa181765eb0366fe6c98525941840f57723d0ae99cb55b2a8c5",
    "../MAT2-F03/assets/trunk_01_mesh.json":
        "3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7",
}


class PinRefusal(Exception):
    """Pre-import stand-in for the pinned CombineRefusal: a drifted or
    missing pinned byte refuses BY NAME before anything is constructed."""

    def __init__(self, code, detail):
        super().__init__(code + ": " + json.dumps(detail, sort_keys=True))
        self.code = code
        self.detail = detail


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_inputs() -> dict:
    """The ABI frozen-input gate: re-verify EVERY pinned byte; refuse any
    drift or absence by name (spec_pinned_input_drift) BEFORE construction.
    Returns the verified identity table."""
    verified = {}
    for rel, expected in _PACKAGE_PINS.items():
        path = (_HERE / rel).resolve()
        if not path.exists():
            raise PinRefusal("spec_pinned_input_drift",
                             {"pin": rel, "error": "input_pin_missing",
                              "path": str(path)})
        got = _sha256_file(path)
        if got != expected:
            raise PinRefusal("spec_pinned_input_drift",
                             {"pin": rel, "error": "input_pin_drift",
                              "expected": expected, "observed": got})
        verified[rel] = got
    for raw_path, expected in _EXTERNAL_PINS.items():
        path = pathlib.Path(raw_path)
        if not path.exists():
            raise PinRefusal("spec_pinned_input_drift",
                             {"pin": raw_path, "error": "input_pin_missing"})
        got = _sha256_file(path)
        if got != expected:
            raise PinRefusal("spec_pinned_input_drift",
                             {"pin": raw_path, "error": "input_pin_drift",
                              "expected": expected, "observed": got})
        verified[raw_path] = got
    spec_path = _HERE / SPEC_REL
    if not spec_path.exists():
        raise PinRefusal("spec_pinned_input_drift",
                         {"pin": SPEC_REL, "error": "spec_missing"})
    verified[SPEC_REL] = _sha256_file(spec_path)
    return {
        "abi_version": ABI_VERSION,
        "membrane_id": IMPLEMENTS_MEMBRANE_ID,
        "gate": "hand_membrane_v1.verify_frozen_inputs (this module's own "
                "pinned-byte table)",
        "verified": verified,
    }


def _load_mathspec():
    """Hash-assert then import the pinned ABI + spec runtime (never forked)."""
    verify_frozen_inputs()
    if str(MATHSPEC_DIR) not in sys.path:
        sys.path.insert(0, str(MATHSPEC_DIR))
    import membrane_abi  # noqa: E402
    import spec_format   # noqa: E402
    import spec_runtime  # noqa: E402  (self-verifies its pinned_inputs pins)
    return membrane_abi, spec_format, spec_runtime


def _load_pinned(rel, expected, name):
    path = (_HERE / rel).resolve()
    got = _sha256_file(path)
    if got != expected:
        raise PinRefusal("spec_pinned_input_drift",
                         {"pin": rel, "error": "input_pin_drift",
                          "expected": expected, "observed": got})
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def build(context, dt):
    """THE ABI constructor: build(context, dt) -> membrane object.

    Refuses by name on any drifted pinned byte, context-identity mismatch,
    or non-admissible dt -- all BEFORE any payload is produced."""
    membrane_abi, spec_format, spec_runtime = _load_mathspec()
    if not isinstance(context, membrane_abi.SpecContext):
        raise membrane_abi.CombineRefusal(
            membrane_abi.E_ABI_MODULE_NOT_CONFORMANT,
            {"module": __name__,
             "law": "build(context, dt) requires a membrane_abi.SpecContext"})
    verify_frozen_inputs()
    spec_path = _HERE / SPEC_REL
    own_spec_sha = _sha256_file(spec_path)
    if context.spec_raw_sha256 != own_spec_sha:
        raise membrane_abi.CombineRefusal(
            "spec_pinned_input_drift",
            {"law": "the wiring context binds different spec bytes than this "
                    "module's verified frozen spec document",
             "context": context.spec_raw_sha256,
             "module_verified": own_spec_sha})
    dt = context.require_dt_admissible(dt)   # spec_dt_not_admissible gate
    section = context.section(IMPLEMENTS_MEMBRANE_ID)
    gc = _load_pinned("../MAT2-G04/grip_contact.py",
                      "0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245",
                      "hand_pinned_g04_grip")
    cso = _load_pinned("../MAT2-G05/contact_support_obs.py",
                       "3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3",
                       "hand_pinned_g05_obs")
    rfa = _load_pinned("../MAT2-G07/release_fall_account.py",
                       "78b5cc66f7019fa181765eb0366fe6c98525941840f57723d0ae99cb55b2a8c5",
                       "hand_pinned_g07_account")
    lc = gc.load_interface()   # the G04 module's own hash-asserted M06 import
    return _HandMembrane(context, dt, section, membrane_abi, spec_format,
                         spec_runtime, gc, cso, rfa, lc)


# --------------------------------------------------------------------------
# the built membrane
# --------------------------------------------------------------------------

class PressChannel:
    """The hand's press channel + release latch (contract
    timing.latches.press_release_latch).

    Declared behavior:
      hold tick    -> channel state = P (the declared per-channel impulse)
      release tick -> channel state = 0.0 EXACTLY; the latch SETS
      any later hold tick without an explicit re_arm() ->
        refusal ref.hand.latch_silent_rearm (never a partial press,
        never a silent re-arm)
      an applied value outside {0.0, P} -> structural fault refusal
        ref.hand.press_state_not_armed_nor_released (contract
        valid_input_ranges: no third state exists)
    """

    def __init__(self, p_ns):
        self.p_ns = float(p_ns)
        self.latched = False
        self.value = None
        self.decisions = []

    def step(self, tick, phase, applied=None):
        if phase == "hold":
            if self.latched:
                raise CombineRefusalProxy(
                    "ref.hand.latch_silent_rearm",
                    {"tick": tick,
                     "law": "once released the press channel stays released "
                            "until an explicit re-arm (contract "
                            "timing.latches.press_release_latch)"})
            value = self.p_ns if applied is None else float(applied)
        elif phase == "release":
            if applied is not None and float(applied) != 0.0:
                raise CombineRefusalProxy(
                    "ref.hand.press_state_not_armed_nor_released",
                    {"tick": tick, "value": applied,
                     "law": "a release tick records the channel at exactly "
                            "0 N*s (G07 X1), never a partial press"})
            value = 0.0
            self.latched = True
        else:
            raise CombineRefusalProxy(
                "ref.hand.press_state_not_armed_nor_released",
                {"tick": tick, "phase": phase,
                 "law": "a record outside {armed, released} is a structural "
                        "fault, not a value (contract valid_input_ranges)"})
        if value != 0.0 and value != self.p_ns:
            raise CombineRefusalProxy(
                "ref.hand.press_state_not_armed_nor_released",
                {"tick": tick, "value": value,
                 "law": "a record outside {armed, released} is a structural "
                        "fault, not a value (contract valid_input_ranges)"})
        self.value = value
        self.decisions.append({"tick": tick, "phase": phase,
                               "press_channel_state": value})
        return value

    def re_arm(self):
        """The EXPLICIT re-arm (the only way the latch clears)."""
        if not self.latched:
            raise CombineRefusalProxy(
                "ref.hand.rearm_without_release",
                {"law": "an explicit re-arm is defined only on a released "
                        "channel"})
        self.latched = False
        return True


class CombineRefusalProxy(Exception):
    """In-step refusal raised before any payload is produced when the
    pinned CombineRefusal type is not the import context (the code string
    is the named contract; the battery asserts the codes)."""

    def __init__(self, code, detail):
        super().__init__(code + ": " + json.dumps(detail, sort_keys=True))
        self.code = code
        self.detail = detail


class HandObservationSeam:
    """The hand's observation seam delivery component: composition of the
    pinned G05 seam implementation (imported-not-forked). The delivery
    gates are the pinned named refusals (undeclared_field, timing_unbound,
    timing_drift, named_absent_occupied, privileged_source, nonfinite_value,
    dim_mismatch); the x_* namespace and the privileged registry stay
    refused. This component never widens the declared key universe."""

    def __init__(self, cso):
        self._cso = cso
        self._censuses = []

    def observe_and_deliver(self, gc, lc, geom, reading_kg, n_channels,
                            scenario_id, **kwargs):
        """One observed scenario owned by THIS component, composed of the
        pinned pieces in the sealed G05 order: the pinned G05 loop
        (bit-identical G04 per-tick operations), the pinned-runner
        cross-check (refusal observer_drift), then one delivered sample
        per tick through a fresh pinned seam (this component never
        widens the declared key universe). Returns
        (header, rows, samples, census, z0)."""
        header, rows, centroids = self._cso.observe_scenario(
            gc, lc, geom, reading_kg, n_channels, scenario_id=scenario_id,
            **kwargs)
        header_ref, rows_ref = gc.run_scenario(
            lc, geom, reading_kg, n_channels, scenario_id=scenario_id,
            **kwargs)
        if header != header_ref:
            raise ValueError("observer_drift:header:" + str(scenario_id))
        for r_obs, r_ref in zip(rows, rows_ref):
            if (r_obs["tick"] != r_ref["tick"]
                    or r_obs["phase"] != r_ref["phase"]):
                raise ValueError("observer_drift:row:%d" % r_obs["tick"])
            if r_obs["ledger"] != r_ref["ledger"]:
                raise ValueError("observer_drift:ledger:%d" % r_obs["tick"])
            for p_obs, p_ref in zip(r_obs["pads"], r_ref["pads"]):
                for key in ("jn_sum_Ns", "jt_sum_Ns", "mode", "disp_tick_m",
                            "surfaces", "vt_post_mps", "pad"):
                    if p_obs[key] != p_ref[key]:
                        raise ValueError("observer_drift:pads:%s:%d"
                                         % (key, r_obs["tick"]))
        z0 = self._cso.initial_centroid_z(gc, geom, n_channels)
        samples = [self._cso.project_sample(
            gc, lc, row, [c[2] for c in centroids[i]], n_channels, lc.DT)
            for i, row in enumerate(rows)]
        census = self.deliver_scenario(scenario_id, lc.DT, samples)
        return header, rows, samples, census, z0

    def deliver_scenario(self, scenario_id, dt_s, samples):
        """Deliver a scenario's samples in tick order through ONE pinned
        seam gate set (the monotonicity law is per scenario tick axis)."""
        seam = self._cso.ObservationSeam(scenario_id, dt_s)
        for sample in samples:
            seam.deliver(sample)
        census = seam.census()
        self._censuses.append(census)
        return census

    def deliver_one(self, scenario_id, dt_s, sample):
        """Deliver ONE sample through a fresh pinned seam gate set
        (single-sample delivery controls). Raises the pinned refusal."""
        seam = self._cso.ObservationSeam(scenario_id, dt_s)
        seam.deliver(sample)
        return seam.census()

    def census(self):
        accepted = sum(c["accepted"] for c in self._censuses)
        refusals = [dict(r, scenario_id=c["scenario_id"])
                    for c in self._censuses for r in c["refusals"]]
        return {"scenarios": len(self._censuses), "accepted": accepted,
                "refusals": refusals}


class _HandMembrane:
    """The built hand membrane (ABI surface)."""

    membrane_id = IMPLEMENTS_MEMBRANE_ID

    def __init__(self, context, dt, section, membrane_abi, spec_format,
                 spec_runtime, gc, cso, rfa, lc):
        self._ctx = context
        self._spec = context.spec
        self._dt = float(dt)
        self._section = section
        self._abi = membrane_abi
        self._spec_format = spec_format
        self._spec_runtime = spec_runtime
        self._gc, self._cso, self._rfa, self._lc = gc, cso, rfa, lc
        params = {p["var"]: p["value"] for p in section.get("parameters") or []}
        self.press_point_ns = float(params["press_channel_jn_ns_per_tick"])
        self.press_dt_s = float(params["press_dt_s"])
        self.release_bar_jn_ns = float(params["release_bar_jn_ns"])
        self.release_bar_jt_ns = float(params["release_bar_jt_ns"])
        self.press_channel = PressChannel(self.press_point_ns)
        self.observation_seam = HandObservationSeam(cso)
        # the pinned substrate (imported, hash-asserted, never forked),
        # exposed read-only for the acceptance battery
        self.pinned = {"gc": gc, "lc": lc, "cso": cso, "rfa": rfa}

    # -- ownership (the ONE deterministic id scheme) --------------------------------
    def ownership(self):
        state_ids, _owner, _ex = self._spec_runtime.resolve_ids(self._spec)
        rows = [{"var": st["var"], "unit": st["unit"],
                 "state_id": state_ids[(self.membrane_id, st["var"])]}
                for st in self._section.get("owned_state") or []]
        return {"membrane_id": self.membrane_id,
                "owned_states": rows,
                "contribution_id": "CMP-MEM-HAND-20261004.hand_membrane_v1"}

    # -- typed ports (equal to the spec section's table) -----------------------------
    def ports(self):
        return self._section.get("ports") or {}

    # -- the ONE shared exchange accessor (read-only seam records) --------------------
    def exchange_quantity(self, view):
        """jn at the window-start view. READ-ONLY: the record is written
        once by the ground side; this accessor never writes."""
        return view["jn"]

    def seam_records(self, view):
        """Both READ-ONLY seam records of the window view (jn and jt)."""
        return {"jn": view["jn"], "jt": view["jt"]}

    # -- the integrate contribution (writes EXACTLY the owned states) -----------------
    def contribution(self):
        state_ids, _owner, _ex = self._spec_runtime.resolve_ids(self._spec)
        press_id = state_ids[(self.membrane_id, "press_channel_state")]
        obs_id = state_ids[(self.membrane_id, "grasp_observation_table")]
        Contribution = self._spec_runtime.Contribution   # pinned class

        def compute(view, ctx):
            channel_value = self.press_channel.value
            if channel_value is None:
                channel_value = 0.0   # pre-first-step view: channel not armed
            return {"states": {press_id: float(channel_value),
                               obs_id: 0.0},
                    "ledger": []}

        return Contribution(
            "CMP-MEM-HAND-20261004.hand_membrane_v1.press_channel",
            self.membrane_id, [press_id, obs_id], compute)

    # -- the ABI ONE-writer law: NO exchange_contribution on the hand -----------------
    # (the connection's exchange-record owner is membrane.ground.v1; a
    # non-owner exposing exchange_contribution() is refused
    # abi_exchange_writer_violation at conformance time. The attribute is
    # deliberately ABSENT; the battery asserts its absence positively.)

    # -- the press channel driving helper ------------------------------------------------
    def drive_tick(self, tick, phase):
        """One channel decision for tick/phase; returns the channel state
        value written to press_channel_state (P on armed hold, 0.0 on
        release). Refuses by name on latch/state faults."""
        return self.press_channel.step(tick, phase)

    def observe_and_deliver(self, geom, reading_kg, n_channels, scenario_id,
                            **kwargs):
        """The observation seam delivery through this membrane's component
        (pinned G05 loop + gates; refusal observer_drift on any drift)."""
        return self.observation_seam.observe_and_deliver(
            self._gc, self._lc, geom, reading_kg, n_channels, scenario_id,
            **kwargs)

    def load_fixture_geometry(self):
        """The pinned trunk fixture geometry (hash-asserted by the G04
        module's own loader)."""
        return self._gc.load_trunk_geometry()
