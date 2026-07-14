"""
Witness Gate — no feature reaches 'verified'/'observed' on a compile alone.

Why (2026-07-13, the human): the constitution says it in many places — "a compile
is not proof" (AGENT_ONBOARDING), H-14 "verified-by-injection is not playable",
"report exact automation output verbatim BEFORE any feature is marked verified"
(CHIMERA_PROGRESS_UPDATE) — yet `record_feature(status='verified')` accepts
anything. So the proxy-vs-witness error (green unit tests read as "it flies") had
no guard. This adds one, at postflight, in the "bare 'blocked' is forbidden"
idiom: a feature can only be recorded verified/observed if there is real witness
evidence this session (a SimPlaytest / telemetry / observation node), OR you cite
what you observed (--witnessed), OR you record a reasoned waiver (--witness-waiver).

Agent-agnostic (plain Python over the DNA graph). Toggle:
CHIMERA_WITNESS_GATE=warn (or off) softens block -> warn.
"""
import os
from datetime import datetime, timedelta, timezone

ENFORCE_DEFAULT = True
# The statuses that CLAIM a feature is proven — the ones that require a witness.
VERIFIED_STATUSES = {"verified", "observed", "observed_provisional"}
EVIDENCE_TYPES = ("SimPlaytest", "CriticJudgment", "Health")

GUIDANCE = (
    "H-14: a compile is not proof; verified-by-injection is not playable. Mark a\n"
    "feature verified/observed only with a WITNESS. Either point at real evidence\n"
    "recorded this session (a SimPlaytest via `python -m core.sleepwalker ...`, or a\n"
    "telemetry soak), or:\n"
    '    ... --witnessed "<what you observed in PIE + the simtest/telemetry id>"\n'
    "or record why a witness is genuinely not applicable:\n"
    '    ... --witness-waiver "<why>"\n'
    "Green unit tests alone are not a witness."
)


def enforced():
    if os.environ.get("CHIMERA_WITNESS_GATE", "").strip().lower() in ("warn", "off", "0", "false"):
        return False
    return ENFORCE_DEFAULT


def _recent_evidence(nodes, hours=12):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out = []
    for n in nodes:
        t = n.get("type")
        is_ev = (t in EVIDENCE_TYPES
                 or str(n.get("template_file", "")).startswith("telemetry")
                 or n.get("fps") is not None
                 or (t == "FeatureUpdate" and n.get("status") in ("observed", "observed_provisional")))
        if not is_ev:
            continue
        ts = str(n.get("timestamp", ""))
        try:
            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
        except Exception:
            when = None
        if when is None or when >= cutoff:
            out.append(n)
    return out


def check(nodes, status=None, witnessed="", waiver="", hours=12):
    """(result, detail). result: n/a | provided | evidence | waived | missing.
    Only gates a verify/observe transition."""
    if status not in VERIFIED_STATUSES:
        return "n/a", "not a verify/observe transition"
    if (witnessed or "").strip():
        return "provided", witnessed.strip()
    ev = _recent_evidence(nodes, hours=hours)
    if ev:
        kinds = sorted({n.get("type", "?") for n in ev})
        return "evidence", f"{len(ev)} witness node(s) this session ({', '.join(kinds)})"
    if (waiver or "").strip():
        return "waived", waiver.strip()
    return "missing", "no SimPlaytest/telemetry/observation evidence this session (a compile is not proof, H-14)"
