"""THE VERSIONED COMMAND RECORD v1 + THE FAMILY-ADAPTER PROJECTION LAW
(lane/policy-interface-freeze-20260920; preregistered BEFORE this build).

Astra round 5 (settled): hierarchical control -- derived reflexes fixed below,
command-conditioned policies WITHIN behavior families at 20 Hz over 300 Hz
physics (15-tick holds), certified option-transitions between families, a
planner on top. The PLANNER's only downward currency is a COMMAND RECORD. This
module freezes that currency's v1 shape and its PROJECTION LAW:

    versioned command record -> family adapter (versioned) -> fixed actor input

THE LAW (what makes the freeze irreversible-safe):
  1. A record carries its `record_version`. An adapter carries its
     `adapter_version`. An adapter of version N reads ONLY the fields declared
     by version N -- a later record version may ADD fields, and they can never
     leak into an older adapter's projection (the v2-record-through-v1-adapter
     bit-identity test).
  2. The v1 deployment's actor is UNCONDITIONED: the old actor's fixed input is
     its old projection (the frozen 80-field observation; the actor's own
     8-channel walk-interface output path untouched). The v1 adapter's actor
     conditioning is therefore the EMPTY vector -- the old actor gets exactly
     its old projection, byte for byte.
  3. The v1 adapter's machinery projection routes EXACTLY ONE field to the
     walk's command channel: `commanded_target_velocity_x = v_forward` (the
     typea-command-adapter receipt's channel: GaitWalker::configure() between
     ticks, zero-order hold at the tick boundary, 20 Hz re-issue legal -- F-ZOH-
     CLOCK GREEN). `yaw_rate` is CARRIED but routed NOWHERE: the typea receipt
     reserved commanded_heading for a later lane and this lane does not invent
     authority it has not measured.

THE NUMBERS (all measured, none tuned; the typea receipt is the source):
  - domain: v_forward >= 0 (the plant law's own max(0, .) domain).
  - supported range: [0.0, 0.763625] m/s -- the scene seed's band, measured
    veto-free horizons 137-222 ticks (R1-R4 GREEN clause (b)).
  - out-of-band: LEGAL up to the declared envelope; the MACHINERY absorbs the
    excess through its own reach annulus (R5: 1.30 m/s demanded, clamped to
    xoff 0.258747 m by the existing fore clamp; refused by the existing budget
    at the M2 class -- F_COMMAND_ENVELOPE GREEN). The adapter never pre-clamps.
  - rate limits: DECLARED UNLIMITED at v1 (rate_limit_v_per_s = None,
    rate_limit_yaw_per_s = None). Step changes are measured-legal: R1-R3 step
    commands onset latency 7 ticks <= the 15-tick hold. No rate number is
    invented; the schema fields exist so a v2 record can fill them from a
    derivation.
  - zero-speed semantics: v_forward = 0.0 is the plant law's own
    x_off = 0*(DUTY_SAMPLED*T_CYCLE)/2 = 0 -- a legal command that targets the
    walk's own zero advance. It is NOT a stop bar: stopping bars are a
    DIFFERENT lane's job (declared; this module only carries the note).
  - the R4 lesson (carried as a SEMANTIC constraint, enforced by the planner,
    not by this module): never feed a constant seed pinned from entry -- a held
    command must TRACK the measured relation (R4 refused at 282 of
    gait_impact_event_budget, a class flip, when the law's v was frozen while
    measured v dipped).
"""
from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass, field
from typing import Optional

COMMAND_RECORD_VERSION = 1
ADAPTER_VERSION = 1

# the measured envelope (the typea receipt's authority table; nothing tuned)
V_MAX_IN_BAND_M_S = 0.763625   # the scene seed: measured veto-free 137-222 ticks
V_ENVELOPE_DEMO_M_S = 1.30     # R5: legal out-of-band demand, machinery-absorbed
HOLD_TICKS = 15                # the 20 Hz decision clock over 300 Hz physics
POLICY_HZ = 20
PHYSICS_HZ = 300


class CommandRecordError(ValueError):
    """A record violates the v1 law (validator message says which)."""


@dataclass(frozen=True)
class CommandRecord:
    """The planner's downward currency, version 1.

    Fields (v1 -- the ONLY fields a v1 adapter may read):
      v_forward : float, m/s, >= 0. The walk-interface forward-speed demand.
      yaw_rate  : float, rad/s. CARRIED, NO AUTHORITY (commanded_heading is
                  reserved for a later lane per the typea receipt); present so
                  the wire format never changes when the authority is derived.
      issued_tick : int, the physics tick at which the planner issued (the ZOH
                  applies it at the next step() and holds >= HOLD_TICKS).
    Semantic (planner-owned, carried for provenance):
      source : the issuing planner's id (a string; the R4 discipline lives here).
    """
    v_forward: float
    yaw_rate: float = 0.0
    issued_tick: int = 0
    source: str = "planner"
    record_version: int = COMMAND_RECORD_VERSION

    def __post_init__(self):
        if self.record_version != COMMAND_RECORD_VERSION:
            raise CommandRecordError(
                f"record_version {self.record_version} != {COMMAND_RECORD_VERSION} "
                "(a new version is a NEW declared wire format, not a free field)")
        vf = float(self.v_forward)
        if vf != vf or vf in (float("inf"), float("-inf")):
            raise CommandRecordError("v_forward must be finite")
        if vf < 0.0:
            raise CommandRecordError(
                "v_forward < 0 is outside the plant law's own max(0, .) domain")
        yr = float(self.yaw_rate)
        if yr != yr or yr in (float("inf"), float("-inf")):
            raise CommandRecordError("yaw_rate must be finite")
        object.__setattr__(self, "v_forward", vf)
        object.__setattr__(self, "yaw_rate", yr)

    # ---- the wire format (canonical bytes; the F2 pin) ----------------------
    def canonical_fields(self) -> dict:
        return {
            "record_version": self.record_version,
            "v_forward": self.v_forward,
            "yaw_rate": self.yaw_rate,
            "issued_tick": int(self.issued_tick),
            "source": self.source,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.canonical_fields(), sort_keys=True,
                          separators=(",", ":")).encode("utf-8")

    def canonical_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    # ---- the float-bit identity (the projection law's test surface) ---------
    def v1_field_bits(self) -> bytes:
        """The exact float64 bits of the v1-readable fields, in declared order
        (v_forward, yaw_rate). The bit-identity test compares THESE: a v2
        record carrying the same v1 values must produce these exact bits."""
        return (struct.pack("<d", float(self.v_forward))
                + struct.pack("<d", float(self.yaw_rate)))


# ---- the family adapter (versioned) ----------------------------------------

@dataclass(frozen=True)
class V1FamilyAdapter:
    """The v1 walk-family adapter: the fixed projection law.

    project_to_machinery : routes v_forward to the typea command channel
        (commanded_target_velocity_x) EXACTLY, as a float64 pass-through -- the
        machinery owns every clamp (the reach annulus) and every budget; the
        adapter pre-clamps nothing (R5/F_COMMAND_ENVELOPE measured).
    project_to_actor_conditioning : the EMPTY vector. The v1 actor is
        unconditioned -- its fixed input is its old projection (the frozen
        80-field observation); this adapter adds no bits to it.
    """
    adapter_version: int = ADAPTER_VERSION

    def project(self, rec: CommandRecord) -> dict:
        """The machinery projection (validate + route). Reads ONLY the v1
        field set: v_forward, yaw_rate(carry-only). A record with ANY extra
        fields (a v2 wire format) produces bit-identical output here."""
        if not isinstance(rec, CommandRecord):
            raise CommandRecordError("adapter v1 consumes CommandRecord instances")
        return {
            "adapter_version": self.adapter_version,
            "commanded_target_velocity_x": float(rec.v_forward),  # float64 passthrough
            # yaw_rate: carried, NO ROUTE (authority not derived; declared above)
            "routed_yaw_rate": False,
        }

    def project_to_actor_conditioning(self, rec: CommandRecord) -> bytes:
        """The actor-conditioning projection: EMPTY at v1 (the law's clause 2).
        Bit-for-bit identical for every record, of any version the caller
        claims: the old actor gets exactly its old projection."""
        return b""

    def projection_bytes(self, rec: CommandRecord) -> bytes:
        """Canonical byte serialization of the full projection (the F2 pin and
        the bit-identity test's surface)."""
        p = self.project(rec)
        return json.dumps(p, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("utf-8") + b"|cond=" \
            + self.project_to_actor_conditioning(rec)


def project_v1(rec: CommandRecord, adapter: Optional[V1FamilyAdapter] = None) -> dict:
    """The v1 projection law, functional form (the unittest's stable entry)."""
    return (adapter or V1FamilyAdapter()).project(rec)


# ---- the declared v1 WIRE decoder -------------------------------------------

def decode_v1(wire: dict) -> CommandRecord:
    """The DECLARED v1 decoder: reads ONLY the v1 field set from a wire dict.

    THIS is the law's enforcement point for forward compatibility: a v2 (or
    any later) wire carries extra keys and a possibly-bumped record_version;
    decode_v1 ignores every key it does not know. A v2 wire with the same v1
    values therefore decodes to a record whose projection is BIT-IDENTICAL to
    the v1 wire's (the unittest pins this with float64 bits)."""
    return CommandRecord(
        v_forward=float(wire["v_forward"]),
        yaw_rate=float(wire.get("yaw_rate", 0.0)),
        issued_tick=int(wire.get("issued_tick", 0)),
        source=str(wire.get("source", "planner")),
        record_version=COMMAND_RECORD_VERSION,   # the DECODER's version, not the wire's
    )


def wire_version(wire: dict) -> int:
    """The wire's DECLARED record version (the runtime dispatches decoders on
    this; an unversioned wire is v1)."""
    return int(wire.get("record_version", 1))


# ---- declared semantics (read-only tables for the certificate lane) ---------

ZERO_SPEED_SEMANTICS = (
    "v_forward = 0.0 is the plant law's own x_off = 0 (a legal command, the "
    "walk's own zero-advance target). It is NOT a stop bar: the stopping "
    "criterion is a DIFFERENT lane's job and is not declared here.")

R4_SEMANTIC_CONSTRAINT = (
    "never feed a constant seed pinned from entry (R4: refusal 282, "
    "gait_impact_event_budget, a class flip -- the frozen v removed the walk's "
    "own speed feedback). A held command must TRACK the measured relation. "
    "Enforced by the planner; this module carries the note on every record's "
    "consumer path.")

RANGES = {
    "v_forward": {
        "domain_lo": 0.0,
        "domain_hi": None,             # the plant law's own domain is [0, inf)
        "in_band_hi": V_MAX_IN_BAND_M_S,   # measured veto-free band
        "envelope_demo": V_ENVELOPE_DEMO_M_S,  # measured machinery-absorbed demand
        "out_of_band_semantics": "legal; the machinery's own reach annulus "
                                 "absorbs the excess (R5 measured), the "
                                 "existing budgets own the refusal",
    },
    "yaw_rate": {
        "authority": "NONE (reserved: commanded_heading is a later lane's)",
        "carried": True,
    },
}

RATE_LIMITS = {
    "v_forward_per_s": None,   # DECLARED UNLIMITED at v1: step changes measured
                               # legal (R1-R3: onset 7 ticks <= hold 15)
    "yaw_rate_per_s": None,    # no authority to rate-limit
    "derivation_status": "no rate number is invented; the fields exist so a v2 "
                         "record can fill them from a derivation",
}
