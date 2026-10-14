"""combination.py -- combination validation across mechanisms.

Validates an assembly BEFORE the integrator may run it:
  1. unresolved dependencies   -- a mechanism declares an input nobody provides
  2. incompatible formulations -- a mechanism is bound to a model absent from
     the assembly, to a different model VERSION than the one bound, or a
     contact pair names models the assembly does not carry
  3. DUPLICATE contributions   -- two records hitting the same (channel, point)
     in a flagged channel ("contact_force", "stored_energy", "heat",
     "dissipation"). Duplicates are FLAGGED and reported; the integrator
     refuses to run a combination that has them. They are NEVER silently
     summed.

Policies: "reject" (raise CombinationRefusal) or "flag" (return the report;
the caller must act on valid_for_run).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .mechanism import DUPLICATE_FLAGGED_CHANNELS, Mechanism, MechanismRefusal
from .contact import ContactModel


class CombinationRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


class CombinationReason:
    DUPLICATE = "duplicate_contribution"
    UNRESOLVED = "unresolved_dependency"
    INCOMPATIBLE = "incompatible_formulation"
    BAD_POLICY = "unknown_policy"


POLICY_REJECT = "reject"
POLICY_FLAG = "flag"


@dataclass(frozen=True)
class CombinationIssue:
    kind: str
    detail: str
    mechanisms: tuple[str, ...]
    channel: str | None = None
    point: str | None = None


@dataclass
class CombinationReport:
    issues: list[CombinationIssue] = field(default_factory=list)
    contributions_probed: int = 0

    @property
    def valid_for_run(self) -> bool:
        return not self.issues

    def duplicates(self) -> list[CombinationIssue]:
        return [i for i in self.issues if i.kind == CombinationReason.DUPLICATE]


@dataclass(frozen=True)
class Assembly:
    """What a run binds: mechanisms, the material models present, the contacts,
    and the input names provided at runtime."""
    mechanisms: tuple[Mechanism, ...]
    model_ids: tuple[str, ...]
    provided_inputs: tuple[str, ...]
    contacts: tuple[ContactModel, ...] = ()


class CombinationValidator:
    """Dry-run probe of the whole assembly against a representative state."""

    def __init__(self, policy: str = POLICY_REJECT):
        if policy not in (POLICY_REJECT, POLICY_FLAG):
            raise CombinationRefusal(CombinationReason.BAD_POLICY,
                                     f"policy {policy!r} is not "
                                     f"'reject' or 'flag'")
        self.policy = policy

    def _collect(self, issue: CombinationIssue, report: CombinationReport) -> None:
        report.issues.append(issue)
        if self.policy == POLICY_REJECT:
            raise CombinationRefusal(
                issue.kind,
                f"{issue.detail} (mechanisms: {issue.mechanisms}, "
                f"channel={issue.channel}, point={issue.point})")

    def validate(self, assembly: Assembly, probe_inputs: dict) -> CombinationReport:
        report = CombinationReport()
        model_ids = set(assembly.model_ids)

        for mech in assembly.mechanisms:
            # 1. unresolved dependencies
            missing = [name for name in mech.declares
                       if name not in probe_inputs]
            if missing:
                self._collect(CombinationIssue(
                    kind=CombinationReason.UNRESOLVED,
                    detail=(f"mechanism {mech.mechanism_id!r} declares "
                            f"input(s) {missing} that no provider supplies"),
                    mechanisms=(mech.mechanism_id,), channel=None, point=None),
                    report)
                continue  # cannot probe further without its inputs
            # 2. incompatible formulation: mechanism bound to an absent model
            if mech.model_id not in model_ids:
                self._collect(CombinationIssue(
                    kind=CombinationReason.INCOMPATIBLE,
                    detail=(f"mechanism {mech.mechanism_id!r} is bound to model "
                            f"{mech.model_id!r}, absent from the assembly "
                            f"{sorted(model_ids)}"),
                    mechanisms=(mech.mechanism_id,)), report)
            # 2b. version mismatch: mechanism declares the exact model version
            #     it adapts via adapters_model_id (when set)
            adapters = getattr(mech, "adapters_model_id", None)
            if adapters is not None and adapters != mech.model_id:
                self._collect(CombinationIssue(
                    kind=CombinationReason.INCOMPATIBLE,
                    detail=(f"mechanism {mech.mechanism_id!r} adapts "
                            f"{adapters!r} but is bound to {mech.model_id!r}"),
                    mechanisms=(mech.mechanism_id,)), report)
            # 3. probe evaluation (mechanisms are pure; probe on frozen inputs)
            try:
                records = mech.evaluate(probe_inputs)
            except MechanismRefusal:
                raise
            report.contributions_probed += len(records)

        # contact pairs must name models present in the assembly
        for contact in assembly.contacts:
            absent = [m for m in contact.pair if m not in model_ids]
            if absent:
                self._collect(CombinationIssue(
                    kind=CombinationReason.INCOMPATIBLE,
                    detail=(f"contact {contact.contact_id!r} pairs models "
                            f"{contact.pair} but the assembly lacks {absent}"),
                    mechanisms=(contact.contact_id,)), report)

        # 3. duplicate contributions across the whole assembly
        groups: dict[tuple[str, str], list[str]] = {}
        for mech in assembly.mechanisms:
            if not all(name in probe_inputs for name in mech.declares):
                continue
            try:
                records = mech.evaluate(probe_inputs)
            except MechanismRefusal:
                continue
            for rec in records:
                if not rec.applicable:
                    continue  # excluded records cannot collide
                if rec.channel not in DUPLICATE_FLAGGED_CHANNELS:
                    continue
                key = (rec.channel, rec.point)
                groups.setdefault(key, []).append(rec.mechanism_id)
        for (channel, point), mech_ids in sorted(groups.items()):
            if len(mech_ids) > 1:
                self._collect(CombinationIssue(
                    kind=CombinationReason.DUPLICATE,
                    detail=(f"{len(mech_ids)} contributions of channel "
                            f"{channel!r} at point {point!r} -- flagged, "
                            f"never silently summed"),
                    mechanisms=tuple(mech_ids), channel=channel, point=point),
                    report)
        return report
