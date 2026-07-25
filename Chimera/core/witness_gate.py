"""
Witness Gate — no feature reaches 'verified'/'observed' on a compile alone.

Why (2026-07-13, the human): the constitution says it in many places — "a compile
is not proof" (the onboarding), H-14 "verified-by-injection is not playable",
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


# Recipe/phase boilerplate that must never carry a topic match on its own — the same
# stop-list research_gate needs, for the same reason ("Build toward the seed: X" and
# "...in live build" share the word `build`).
# `feature`/`update`/`model` etc. are NODE VOCABULARY, not feature names. They must never
# carry a match: every DNA node id is auto-generated with its type as a prefix
# (feature_ccd59957..., phase_8ebd..., observation_4085...), so a token like "feature"
# matches the id of every FeatureUpdate in the graph. My first cut of this fix included
# `id` in the searchable blob and did exactly that -- "Totally_Nonexistent_Feature_XYZ"
# passed on 6 nodes, because the word "Feature" in its NAME matched "feature_" in their
# IDs. A scoping filter that matches on the scaffolding is worse than none: it looks
# scoped and is not.
_STOP = {"build", "toward", "seed", "live", "remaining", "realize", "witness",
         "collapse", "verify", "verified", "observe", "observed", "session",
         "phase", "task", "update", "fix", "work", "loop", "chimera", "component",
         "feature", "system", "model", "material", "surface", "simtest", "playtest",
         "telemetry", "record", "graph", "node"}
# NB: every entry above is NODE VOCABULARY — words the graph uses to describe itself.
# Nothing here is a word from a test case. (I briefly added "totally"/"nonexistent" to
# make my own probe pass, which is tuning the instrument to the fixture — the exact
# fraud this file now exists to prevent. Removed.)


def _topic_tokens(topic):
    import re
    return {w for w in re.split(r"[^A-Za-z0-9]+", (topic or "").lower())
            if len(w) >= 5 and w not in _STOP}


def _about(n, toks):
    """Is this evidence ABOUT the feature, or merely NEAR it in time?

    Deliberately does NOT read `id`: ids are scaffolding (type-prefixed and auto-
    generated), so matching them measures the graph's own naming scheme, not the
    feature. Only fields an agent actually WROTE about the work are searched.
    """
    if not toks:
        return True                      # no feature given -> time-only (old behaviour)
    blob = " ".join(str(n.get(f) or "") for f in
                    ("feature", "feature_name", "session", "demo", "notes",
                     "template_file", "fix_description")).lower()
    return any(t in blob for t in toks)


def _recent_evidence(nodes, hours=12, feature=""):
    """Evidence from the last `hours` that is ABOUT `feature`.

    THE RESEARCH-GATE BUG, VERBATIM, IN THE MORE LOAD-BEARING GATE (fixed 2026-07-16).
    This was a bare 12h window over the WHOLE graph with no feature filter — and check()
    had no `feature` parameter at all, so it was structurally incapable of scoping even
    if a caller wanted to. Proven live: asking about a feature that has NEVER EXISTED
    returned "17 witness node(s) this session" — 11 Sky SimPlaytests and 6 Sky
    FeatureUpdates that would satisfy the gate for System_Economy identically. H-14's
    gate ("a compile is not proof") was a 12h no-op that any recent activity satisfied.

    Same fix as research_gate: evidence must be ABOUT the claim, not merely near it in
    time. Time is not identity, and recency is not relevance.
    """
    toks = _topic_tokens(feature)
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
        if not _about(n, toks):
            continue
        if when is None or when >= cutoff:
            out.append(n)
    return out


def check(nodes, status=None, witnessed="", waiver="", hours=12, feature=""):
    """(result, detail). result: n/a | provided | evidence | waived | missing.
    Only gates a verify/observe transition.

    `feature` scopes the evidence (added 2026-07-16). Without it this gate accepted ANY
    witness node from the last 12h anywhere in the graph — a feature that never existed
    drew "17 witness node(s) this session" off unrelated Sky playtests. Passing no
    feature preserves the old time-only behaviour, so callers that cannot name one are
    not broken; postflight names one.
    """
    if status not in VERIFIED_STATUSES:
        return "n/a", "not a verify/observe transition"
    if (witnessed or "").strip():
        return "provided", witnessed.strip()
    ev = _recent_evidence(nodes, hours=hours, feature=feature)
    if ev:
        kinds = sorted({n.get("type", "?") for n in ev})
        # Never "this session" — this gate cannot know a session (see research_gate: that
        # exact word is what fooled an agent into reporting a waiver it never made).
        scope = f"for '{feature}'" if feature else "in the last 12h (UNSCOPED — no feature given)"
        return "evidence", (f"ACCEPTED on {len(ev)} witness node(s) {scope} "
                            f"({', '.join(kinds)})")
    if (waiver or "").strip():
        return "waived", waiver.strip()
    return "missing", (f"no SimPlaytest/telemetry/observation evidence"
                       + (f" for '{feature}'" if feature else "")
                       + " in the last 12h (a compile is not proof, H-14)")
