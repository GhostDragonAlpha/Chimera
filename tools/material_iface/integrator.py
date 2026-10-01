"""integrator.py -- the SOLE authority that advances owned physical state.

Ownership law of this lane:

  - The Integrator owns positions, velocities, the internal-state variables of
    every model with a state_spec, and their HISTORY.
  - Mechanisms never touch owned state. They receive frozen snapshots and may
    only PROPOSE internal-state updates (StateProposal records); the
    Integrator's single gate `_apply_proposal` is the only writer.
  - Ordering is declared and deterministic: snapshot -> collect contributions
    (assembly order) -> duplicate refusal -> applicability filter -> force sum
    -> semi-implicit Euler (v then x) -> state proposals -> energy ledger.
  - Flagged-channel duplicates at one (channel, point) are a named refusal:
    never silently summed.
  - Runtime parameter changes go through change_parameter(): the stored-energy
    difference is computed at the FROZEN current state under old vs new
    parameters, attributed to the change in a ParameterChangeRecord, and
    reported in the ledger. It is never absorbed into the running energy.

Physics note: this is an interface/ownership lane, not a new solver. The
integrator advances whatever the adapted existing laws contribute.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from types import MappingProxyType

from .combination import (Assembly, CombinationRefusal, CombinationValidator,
                          POLICY_REJECT)
from .geometry import Geometry
from .mechanism import (DUPLICATE_FLAGGED_CHANNELS, MechanismContribution,
                        MechanismRefusal, StateProposal)
from .model import MaterialModel
from .presets import MaterialPreset
from .units import Quantity, family_of


class IntegratorRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


class IntegratorReason:
    DUPLICATE = "duplicate_contribution"
    NOT_OWNER = "state_update_not_owned"
    UNKNOWN_STATE_VAR = "unknown_state_variable"
    BAD_PROPOSAL = "bad_state_proposal"
    MODEL_ABSENT = "model_not_in_assembly"
    UNKNOWN_PARAMETER = "unknown_parameter"
    NONFINITE_STATE = "nonfinite_owned_state"


@dataclass(frozen=True)
class Snapshot:
    """Frozen view handed to mechanisms. Mutation attempts raise."""
    positions: tuple[tuple[float, float, float], ...]
    velocities: tuple[tuple[float, float, float], ...]
    time_s: float
    temperature_K: float
    geometry: Geometry
    presets: dict
    model_state: dict

    def as_inputs(self) -> dict:
        return {"positions": self.positions, "velocities": self.velocities,
                "time_s": self.time_s, "temperature_K": self.temperature_K,
                "geometry": self.geometry,
                "presets": MappingProxyType(dict(self.presets)),
                "model_state": MappingProxyType(
                    {k: tuple(v) for k, v in self.model_state.items()})}


@dataclass(frozen=True)
class ParameterChangeRecord:
    step: int
    parameter: str
    old: Quantity
    new: Quantity
    stored_energy_before_j: float
    stored_energy_after_j: float
    delta_stored_energy_j: float
    preset_before: str
    preset_after: str
    note: str


@dataclass(frozen=True)
class LedgerEntry:
    step: int
    dt_s: float
    stored_energy_j: float
    dissipated_energy_j: float
    heat_energy_j: float
    external_work_j: float
    excluded_contributions: int
    parameter_changes: tuple[ParameterChangeRecord, ...]


class Integrator:
    """Advances owned physical state. Nothing else in this lane may."""

    DECLARED_ORDERING = (
        "snapshot -> collect contributions (assembly order) -> duplicate "
        "refusal -> applicability filter -> force sum -> semi-implicit Euler "
        "(v += dt*f/m; x += dt*v) -> apply state proposals -> energy ledger")

    def __init__(self, models: dict, geometry: Geometry, presets: dict,
                 mechanisms: tuple, dt_s: float, seed: int = 0,
                 policy: str = POLICY_REJECT,
                 initial_positions: tuple | None = None):
        self._models = dict(models)
        self._geometry = geometry
        self._dt_s = float(dt_s)
        if not (self._dt_s > 0.0 and math.isfinite(self._dt_s)):
            raise IntegratorRefusal("bad_dt", "dt_s must be finite and > 0")
        self._seed = int(seed)
        rest = geometry.binding["rest_positions"]
        if initial_positions is None:
            self._positions = [tuple(float(c) for c in p) for p in rest]
        else:
            if len(initial_positions) != len(rest):
                raise IntegratorRefusal(
                    "bad_initial_state",
                    "initial_positions must supply exactly "
                    f"{len(rest)} points")
            self._positions = []
            for i, p in enumerate(initial_positions):
                if len(p) != 3 or not all(math.isfinite(float(c)) for c in p):
                    raise IntegratorRefusal(
                        IntegratorReason.NONFINITE_STATE,
                        f"initial_positions[{i}] must be a finite (x, y, z)")
                self._positions.append(tuple(float(c) for c in p))
        n = len(self._positions)
        if n != geometry.n_points:
            raise IntegratorRefusal("bad_geometry",
                                    "rest positions do not match point ids")
        self._velocities = [(0.0, 0.0, 0.0)] * n
        self._masses = tuple(float(m) for m in geometry.masses)
        self._time_s = 0.0
        self._temperature_k = 293.15
        self._presets = dict(presets)
        self._state = {mid: {v.name: 0.0 for v in m.state_spec}
                       for mid, m in self._models.items()}
        self._history: dict[str, list] = {
            mid: [] for mid, m in self._models.items() if m.history}
        self._mechanisms = tuple(mechanisms)
        self._step = 0
        self._pending_changes: list[ParameterChangeRecord] = []
        self._ledger: list[LedgerEntry] = []
        self._validator = CombinationValidator(policy=policy)
        assembly = Assembly(mechanisms=self._mechanisms,
                            model_ids=tuple(self._models),
                            provided_inputs=(), contacts=())
        try:
            report = self._validator.validate(assembly,
                                              self.snapshot().as_inputs())
        except CombinationRefusal as exc:
            raise IntegratorRefusal(
                "invalid_combination",
                f"assembly rejected at construction: {exc}") from None
        if not report.valid_for_run:
            raise IntegratorRefusal(
                "invalid_combination",
                f"assembly rejected at construction: "
                f"{[i.detail for i in report.issues]}")

    # -- frozen views ---------------------------------------------------------

    def snapshot(self) -> Snapshot:
        return Snapshot(
            positions=tuple(self._positions),
            velocities=tuple(self._velocities),
            time_s=self._time_s,
            temperature_K=self._temperature_k,
            geometry=self._geometry,
            presets=dict(self._presets),
            model_state={mid: tuple(sorted(vars_.items()))
                         for mid, vars_ in self._state.items()})

    def read_only_history(self, model_id: str) -> tuple:
        return tuple(self._history.get(model_id, ()))

    @property
    def ledger(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._ledger)

    @property
    def step(self) -> int:
        return self._step

    # -- the single ownership gate -------------------------------------------

    def _apply_proposal(self, proposal: StateProposal) -> None:
        model = self._models.get(proposal.model_id)
        if model is None:
            raise IntegratorRefusal(
                IntegratorReason.MODEL_ABSENT,
                f"state proposal for {proposal.model_id!r}: model absent")
        spec = {v.name: v for v in model.state_spec}
        if proposal.var not in spec:
            raise IntegratorRefusal(
                IntegratorReason.UNKNOWN_STATE_VAR,
                f"model {proposal.model_id!r} owns no state variable "
                f"{proposal.var!r}; refusing to store undeclared state")
        if proposal.mode not in ("set", "add"):
            raise IntegratorRefusal(IntegratorReason.BAD_PROPOSAL,
                                    f"mode {proposal.mode!r} invalid")
        if not math.isfinite(proposal.value):
            raise IntegratorRefusal(IntegratorReason.NONFINITE_STATE,
                                    "proposal value non-finite")
        expected_family = family_of(spec[proposal.var].unit)
        if family_of(proposal.unit) != expected_family:
            raise IntegratorRefusal(
                IntegratorReason.NOT_OWNER,
                f"state var {proposal.var!r} is {expected_family!r}, proposal "
                f"unit is {proposal.unit!r}")
        value = Quantity(proposal.value, proposal.unit).in_unit(
            spec[proposal.var].unit)
        current = self._state[proposal.model_id][proposal.var]
        self._state[proposal.model_id][proposal.var] = (
            value if proposal.mode == "set" else current + value)

    # -- energy evaluation at a frozen state ----------------------------------

    def stored_energy_now(self, preset_overrides: dict | None = None) -> float:
        """Sum applicable stored-energy contributions at the CURRENT frozen
        state, without advancing anything. `preset_overrides` REPLACES the
        preset of specific models while keeping every other model's preset."""
        inputs = self.snapshot().as_inputs()
        if preset_overrides:
            merged = dict(self._presets)
            merged.update(preset_overrides)
            inputs["presets"] = MappingProxyType(merged)
        total = 0.0
        for mech in self._mechanisms:
            for rec in mech.evaluate(inputs):
                if rec.applicable and rec.channel == "stored_energy":
                    total += rec.stored_energy_j
        return total

    def _collect(self, presets: dict | None = None):
        inputs = self.snapshot().as_inputs()
        if presets is not None:
            inputs["presets"] = dict(presets)
        records: list[MechanismContribution] = []
        for mech in self._mechanisms:
            records.extend(mech.evaluate(inputs))
        # duplicate refusal (flagged channels only; never silently summed)
        groups: dict[tuple[str, str], list[str]] = {}
        for rec in records:
            if rec.applicable and rec.channel in DUPLICATE_FLAGGED_CHANNELS:
                groups.setdefault((rec.channel, rec.point), []).append(
                    rec.mechanism_id)
        dupes = {k: v for k, v in groups.items() if len(v) > 1}
        if dupes:
            (channel, point), mech_ids = sorted(dupes.items())[0]
            raise IntegratorRefusal(
                IntegratorReason.DUPLICATE,
                f"{len(mech_ids)} mechanisms contribute {channel} at {point} "
                f"({mech_ids}); duplicates are flagged and refused, never "
                f"summed")
        return records

    # -- the step --------------------------------------------------------------

    def step(self, temperature_k: float | None = None) -> LedgerEntry:
        if temperature_k is not None:
            self._temperature_k = float(temperature_k)
        records = self._collect()
        excluded = 0
        net = {i: [0.0, 0.0, 0.0] for i in range(len(self._positions))}
        stored = dissipated = heat = 0.0
        proposals: list[StateProposal] = []
        for rec in records:
            if not rec.applicable:
                excluded += 1
                continue
            stored += rec.stored_energy_j
            dissipated += rec.dissipated_power_w * self._dt_s
            heat += rec.heat_flux_w_per_m2 * self._dt_s
            if rec.force is not None:
                idx = _point_index(rec.point)
                for k in range(3):
                    net[idx][k] += rec.force[k]
            if rec.state_proposal is not None:
                proposals.append(rec.state_proposal)
        # semi-implicit Euler on OWNED state
        new_positions = []
        for i, mass in enumerate(self._masses):
            v = self._velocities[i]
            a = net[i]
            v_new = (v[0] + self._dt_s * a[0] / mass,
                     v[1] + self._dt_s * a[1] / mass,
                     v[2] + self._dt_s * a[2] / mass)
            p = self._positions[i]
            new_positions.append((p[0] + self._dt_s * v_new[0],
                                  p[1] + self._dt_s * v_new[1],
                                  p[2] + self._dt_s * v_new[2]))
            self._velocities[i] = v_new
        self._positions = new_positions
        self._time_s += self._dt_s
        for proposal in proposals:
            self._apply_proposal(proposal)
        for mid, model in self._models.items():
            if model.history:
                self._history[mid].append(
                    tuple(sorted(self._state[mid].items())) +
                    ((self._time_s,),))
        entry = LedgerEntry(step=self._step, dt_s=self._dt_s,
                            stored_energy_j=stored,
                            dissipated_energy_j=dissipated,
                            heat_energy_j=heat, external_work_j=0.0,
                            excluded_contributions=excluded,
                            parameter_changes=tuple(self._pending_changes))
        self._pending_changes = []
        self._ledger.append(entry)
        self._step += 1
        return entry

    # -- runtime parameter change hook -----------------------------------------

    def change_parameter(self, model_id: str, parameter: str,
                         quantity: Quantity) -> ParameterChangeRecord:
        """Re-price stored energy at the FROZEN current state under the old and
        new parameter values; attribute the difference to the change and
        report it. The owned state itself does not move here: attribution,
        not absorption."""
        if model_id not in self._models:
            raise IntegratorRefusal(IntegratorReason.MODEL_ABSENT,
                                    f"model {model_id!r} absent from assembly")
        model = self._models[model_id]
        if parameter not in {m.name for m in model.parameters}:
            raise IntegratorRefusal(
                IntegratorReason.UNKNOWN_PARAMETER,
                f"model {model_id!r} declares no parameter {parameter!r}; "
                f"an undefined parameter is never silently inferred")
        old_preset = self._presets[model_id]
        before = self.stored_energy_now()
        new_preset = old_preset.runtime_adjusted(parameter, quantity, self._step)
        after = self.stored_energy_now({model_id: new_preset})
        record = ParameterChangeRecord(
            step=self._step, parameter=parameter,
            old=old_preset.values.quantity(parameter),
            new=new_preset.values.quantity(parameter),
            stored_energy_before_j=before, stored_energy_after_j=after,
            delta_stored_energy_j=after - before,
            preset_before=old_preset.preset_id,
            preset_after=new_preset.preset_id,
            note=new_preset.provenance.note)
        self._presets[model_id] = new_preset
        self._pending_changes.append(record)
        return record

    # -- determinism -------------------------------------------------------------

    def state_hash(self) -> str:
        snap = self.snapshot()
        payload = {
            "positions": snap.positions, "velocities": snap.velocities,
            "time_s": snap.time_s, "temperature_K": snap.temperature_K,
            "model_state": {k: list(v) for k, v in snap.model_state.items()},
            "presets": {mid: p.values.canonical_signature()
                        for mid, p in snap.presets.items()},
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _point_index(point: str) -> int:
    try:
        return int(point[1:])
    except (ValueError, IndexError):
        raise IntegratorRefusal(
            "unknown_point", f"point key {point!r} is not a v<i>/p<i> key") from None
