"""THE CERTIFIED OPTION-TRANSITION SCHEMA v1 + VALIDATOR + THREE DECLARED
EXAMPLES (lane/policy-interface-freeze-20260920; preregistered BEFORE this
build).

Astra round 5 (settled): command-conditioned policies live WITHIN behavior
families; movement BETWEEN families happens only through a CERTIFIED
option-transition. This module freezes the certificate's v1 wire format and
the registry/validator machinery. It makes ZERO behavior claims: the three
declared examples (walk_v1, recovery_v1, rear_up_v1) are SCHEMA EXAMPLES --
rear-up does not exist yet; their guards are declared over the FROZEN
80-field vocabulary exactly so that a later lane can evaluate them against
real traces without touching this format (the dummy-weights convention).

A certificate v1 binds, per option:
  entry_guard          predicates over the FROZEN observation vocabulary
                       (field NAME + op + threshold in RAW units + the
                       availability requirement: a guard may REQUIRE a field
                       be available, or evaluate on its value)
  command_payload      the record version + adapter version the option consumes
                       (from command_record.py's versions)
  termination          named conditions under which the option MUST exit --
                       each either a guard predicate over the same vocabulary
                       or the declared machinery-refusal acceptance
  registered_timeout   ticks + the exit taken on expiry (timeout discipline:
                       an option can never outlive its registration)
  named_fallback       the option to enter on termination/timeout -- must be a
                       REGISTERED option (the validator closes the graph; a
                       fallback to an unregistered option is invalid)

Rule 0: the falsifier for THIS module is F2 FREEZE-DRIFT (the schema's required
keys and the three declared examples are pinned; any change without a version
bump fails a unittest). The certificates themselves are judged when a lane
certifies a real behavior against traces -- not here.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field as dc_field
from typing import Optional

from command_record import ADAPTER_VERSION, COMMAND_RECORD_VERSION

CERTIFICATE_VERSION = 1

_OPS = {
    ">=": lambda v, t: v >= t,
    "<=": lambda v, t: v <= t,
    ">": lambda v, t: v > t,
    "<": lambda v, t: v < t,
    "==": lambda v, t: v == t,
    "!=": lambda v, t: v != t,
}

_REQUIRED_TOP = ["certificate_version", "option", "entry_guard", "command_payload",
                 "termination", "registered_timeout", "named_fallback"]
_REQUIRED_GUARD = ["field", "op", "threshold"]
_REQUIRED_TIMEOUT = ["ticks", "on_expiry"]


class CertificateError(ValueError):
    """A certificate violates the v1 schema (message says which)."""


def validate_certificate(cert: dict, field_names: list[str],
                         registered_options: set[str],
                         registered_fallbacks: Optional[set[str]] = None) -> list[str]:
    """Return a list of violations (empty == valid). Pure: no mutation.

    field_names: the FROZEN vocabulary (observation_schema.FIELD_NAMES).
    registered_options: every option name a fallback may name (the registry;
    an option's own name may appear -- self-fallback == hold/stand-fast).
    registered_fallbacks: optional stricter set; if given, fallbacks must be in it.
    """
    errs = []
    for k in _REQUIRED_TOP:
        if k not in cert:
            errs.append(f"missing key: {k}")
    if errs:
        return errs
    if cert["certificate_version"] != CERTIFICATE_VERSION:
        errs.append(f"certificate_version != {CERTIFICATE_VERSION}")
    if not isinstance(cert["option"], str) or not cert["option"]:
        errs.append("option must be a non-empty string")

    # ---- entry guard: every predicate names a frozen vocabulary field
    guard = cert["entry_guard"]
    if not isinstance(guard, list) or not guard:
        errs.append("entry_guard must be a non-empty list of predicates")
    else:
        for i, pred in enumerate(guard):
            errs += _check_predicate(f"entry_guard[{i}]", pred, field_names)

    # ---- command payload: the record/adapter versions this option consumes
    pay = cert["command_payload"]
    if not isinstance(pay, dict):
        errs.append("command_payload must be an object")
    else:
        if pay.get("command_record_version") != COMMAND_RECORD_VERSION:
            errs.append(f"command_payload.command_record_version must be "
                        f"{COMMAND_RECORD_VERSION}")
        if pay.get("family_adapter_version") != ADAPTER_VERSION:
            errs.append(f"command_payload.family_adapter_version must be "
                        f"{ADAPTER_VERSION}")

    # ---- termination: at least one named condition; each a predicate or the
    #      declared machinery-refusal acceptance
    term = cert["termination"]
    if not isinstance(term, list) or not term:
        errs.append("termination must be a non-empty list of named conditions")
    else:
        for i, cond in enumerate(term):
            if not isinstance(cond, dict) or "name" not in cond:
                errs.append(f"termination[{i}] missing name")
                continue
            if "on_machinery_refusal" in cond:
                if not isinstance(cond["on_machinery_refusal"], (str, list)):
                    errs.append(f"termination[{i}].on_machinery_refusal must be a "
                                "refusal class name or list of names")
                continue
            errs += _check_predicate(f"termination[{i}]", cond, field_names)

    # ---- registered timeout: positive ticks + a declared exit
    to = cert["registered_timeout"]
    if not isinstance(to, dict):
        errs.append("registered_timeout must be an object")
    else:
        for k in _REQUIRED_TIMEOUT:
            if k not in to:
                errs.append(f"registered_timeout missing: {k}")
        if "ticks" in to:
            t = to["ticks"]
            if not isinstance(t, int) or isinstance(t, bool) or t <= 0:
                errs.append("registered_timeout.ticks must be a positive int")
        if "on_expiry" in to and not isinstance(to["on_expiry"], str):
            errs.append("registered_timeout.on_expiry must be a string "
                        "(the exit's name)")

    # ---- named fallback: must be a REGISTERED option
    fb = cert["named_fallback"]
    if not isinstance(fb, str) or not fb:
        errs.append("named_fallback must be a non-empty string")
    else:
        reg = registered_fallbacks if registered_fallbacks is not None else registered_options
        if fb not in reg:
            errs.append(f"named_fallback '{fb}' is not a registered option")
    return errs


def _check_predicate(where: str, pred, field_names: list[str]) -> list[str]:
    errs = []
    if not isinstance(pred, dict):
        return [f"{where} must be an object"]
    for k in _REQUIRED_GUARD:
        if k not in pred:
            errs.append(f"{where} missing: {k}")
    if "field" in pred:
        if pred["field"] not in field_names:
            errs.append(f"{where}.field '{pred['field']}' is not in the frozen "
                        "observation vocabulary")
        if pred.get("require_available") is not None and \
                not isinstance(pred.get("require_available"), bool):
            errs.append(f"{where}.require_available must be a bool")
    if "op" in pred and pred["op"] not in _OPS:
        errs.append(f"{where}.op '{pred['op']}' not in {sorted(_OPS)}")
    if "threshold" in pred:
        t = pred["threshold"]
        if not isinstance(t, (int, float)) or isinstance(t, bool):
            errs.append(f"{where}.threshold must be a number (raw units)")
        elif t != t or t in (float("inf"), float("-inf")):
            errs.append(f"{where}.threshold must be finite")
    return errs


def evaluate_predicate(pred: dict, read_field, rec: dict, prev_state: dict) -> Optional[bool]:
    """Evaluate one predicate against a trace record. read_field is the FROZEN
    schema's own reader (observation_schema.read_field) so the guard semantics
    are exactly the projector's. Returns None when the field is unavailable
    (an unavailable predicate never silently passes; the caller's policy owns
    the None case -- a certificate MAY declare require_available: true to make
    unavailability itself an entry failure)."""
    v = read_field(pred["field"], rec, prev_state)
    if v is None:
        if pred.get("require_available"):
            return False
        return None
    return _OPS[pred["op"]](float(v), float(pred["threshold"]))


# ---- the registry -----------------------------------------------------------

@dataclass
class OptionRegistry:
    """The certified-option registry: certificates live here; fallback edges
    must close over registered (or pre-declared) names. `known` pre-declares
    the option names of the declared family graph so a registration order
    cannot manufacture a dangling fallback; every certificate is still
    re-validated against the FULL registry by revalidate_all."""
    field_names: list[str]
    known: set = dc_field(default_factory=set)
    certs: dict = dc_field(default_factory=dict)

    def register(self, cert: dict) -> list[str]:
        errs = validate_certificate(cert, self.field_names,
                                    set(self.certs) | set(self.known) | {cert["option"]})
        if errs:
            return errs
        self.certs[cert["option"]] = cert
        return []

    def revalidate_all(self) -> dict[str, list[str]]:
        """Re-validate every certificate against the registry as it NOW stands
        (closure: every fallback must be a registered option)."""
        reg = set(self.certs) | set(self.known)
        return {name: validate_certificate(cert, self.field_names, reg)
                for name, cert in self.certs.items()}

    def get(self, name: str) -> dict:
        return self.certs[name]


# ---- the THREE DECLARED EXAMPLES (schema examples; ZERO behavior claims) ----

def declared_examples() -> list[dict]:
    """The three declared certificates. HONESTY: walk_v1's guard is expressed
    in the frozen vocabulary and is evaluable against real trace records TODAY
    (the audit's records); recovery_v1 and rear_up_v1 are declared to close the
    fallback graph and to pin the wire format -- their families have NO trained
    policies and NO measured dynamics yet (the dummy-weights convention)."""
    return [
        {
            "certificate_version": 1,
            "option": "walk_v1",
            "option_kind": "declared_example (schema pin; the walk family exists "
                           "as the shipped reflex layer + the frozen walk interface)",
            "entry_guard": [
                {"field": "support_ge3_flag", "op": "==", "threshold": 1.0,
                 "require_available": True, "meaning": "the support census forms a polygon"},
                {"field": "intv_refusal", "op": "==", "threshold": 0.0,
                 "require_available": True, "meaning": "no live refusal"},
                {"field": "ticks_since_intv", "op": ">=", "threshold": 45.0,
                 "require_available": True,
                 "meaning": "the last intervention is >= 3 holds old (45 ticks)"},
            ],
            "command_payload": {
                "command_record_version": 1,
                "family_adapter_version": 1,
                "semantics": "v_forward per command_record.RANGES; zero-speed is "
                             "the plant law's own x_off=0, NOT a stop bar; the R4 "
                             "no-constant-seed constraint is planner-owned",
            },
            "termination": [
                {"name": "machinery_refusal", "on_machinery_refusal": [
                    "gait_positional_correction_budget",
                    "gait_impact_event_budget"]},
                {"name": "support_lost", "field": "support_ge3_flag", "op": "==",
                 "threshold": 0.0, "require_available": True},
                {"name": "live_refusal_flag", "field": "intv_refusal", "op": "==",
                 "threshold": 1.0, "require_available": True},
            ],
            "registered_timeout": {"ticks": 300, "on_expiry": "settle_guard_expiry"},
            "named_fallback": "recovery_v1",
        },
        {
            "certificate_version": 1,
            "option": "recovery_v1",
            "option_kind": "declared_example (wire-format pin; NO trained policy, "
                           "NO measured recovery dynamics -- nothing is claimed)",
            "entry_guard": [
                {"field": "intv_refusal", "op": "==", "threshold": 1.0,
                 "require_available": True,
                 "meaning": "entered from a live refusal (or the walk option's "
                            "termination paths); the guard is deliberately "
                            "redundant with the fallback edge's origin"},
            ],
            "command_payload": {
                "command_record_version": 1,
                "family_adapter_version": 1,
                "semantics": "v_forward=0 (the plant law's own zero advance; the "
                             "stopping criterion remains the stopping lane's job)",
            },
            "termination": [
                {"name": "support_restored", "field": "support_ge3_flag", "op": "==",
                 "threshold": 1.0, "require_available": True},
            ],
            "registered_timeout": {"ticks": 450, "on_expiry": "recovery_window_expiry"},
            "named_fallback": "rear_up_v1",
        },
        {
            "certificate_version": 1,
            "option": "rear_up_v1",
            "option_kind": "declared_example (wire-format pin; the rear-up behavior "
                           "DOES NOT EXIST yet -- zero claims)",
            "entry_guard": [
                {"field": "support_ge3_flag", "op": "==", "threshold": 0.0,
                 "require_available": True,
                 "meaning": "entered from a lost support census; placeholders are "
                            "honest placeholders -- a later lane re-declares the "
                            "real guard from measured rear-up traces"},
            ],
            "command_payload": {
                "command_record_version": 1,
                "family_adapter_version": 1,
                "semantics": "undeclared (the family has no measured command "
                             "surface; the record version is pinned so the wire "
                             "never changes when it is derived)",
            },
            "termination": [
                {"name": "support_restored", "field": "support_ge3_flag", "op": "==",
                 "threshold": 1.0, "require_available": True},
            ],
            "registered_timeout": {"ticks": 600, "on_expiry": "rear_up_window_expiry"},
            "named_fallback": "recovery_v1",   # self-graph closure: recovery -> rear_up -> recovery
        },
    ]


def declared_registry(field_names: list[str]) -> OptionRegistry:
    reg = OptionRegistry(field_names=field_names,
                         known={"walk_v1", "recovery_v1", "rear_up_v1"})
    for cert in declared_examples():
        errs = reg.register(cert)
        if errs:  # pragma: no cover -- the examples must always be valid
            raise CertificateError(f"declared example invalid: {errs}")
    return reg


def canonical_certificate_bytes(cert: dict) -> bytes:
    return json.dumps(cert, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
