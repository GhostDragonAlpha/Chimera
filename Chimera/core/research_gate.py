"""
Research Gate — makes skipping the workflow's mandated research EXPLICIT and
RECORDED instead of silent and self-rationalized.

Why (2026-07-13, the human): an agent (me) built infrastructure and shipped a
SQLite concurrency bug because it skipped the workflow's mandated online research,
rationalizing that "infrastructure is exempt." The research, once actually done,
caught the defect in a single search. The Research Depth Protocol was already
documentation — and documentation is exactly what an agent skips. "Soft warnings
produce soft compliance; hard gates produce alignment" (gates.py). So this adds
teeth at the postflight chokepoint, in the project's own "bare 'blocked' is
forbidden" idiom:

  - Research WAS recorded this session (research_discovery / technical_discovery /
    research_summary / a sourced Reference)  -> the gate passes automatically.
  - Otherwise you must EITHER cite what you looked up (`--researched "..."`)
    OR record why none was needed (`--research-waiver "..."`). A reasoned waiver
    proceeds instantly — speed-run intact — but the decision is now recorded and
    auditable, and waivers feed the nightly distiller. A SILENT skip is refused.

The mandate explicitly covers TECHNICAL / INFRASTRUCTURE decisions (SQLite
semantics, a UE API's behaviour, a git internal), not just game assets — Gate 1
of the Research Depth Protocol lists **Technical Documentation** as a source type.
The gate is agent-agnostic (plain Python over the DNA graph); every harness that
runs postflight inherits it.

Toggle: `CHIMERA_RESEARCH_GATE=warn` (or off/0/false) downgrades block -> warn.
"""
import os
from datetime import datetime, timedelta, timezone

# Block a research-less session (True) vs. warn-and-proceed (False). Env overrides.
ENFORCE_DEFAULT = True

RESEARCH_TYPES = ("research_discovery", "technical_discovery", "research_summary")
RESEARCH_TEMPLATE_PREFIXES = ("research_discovery/", "technical_discovery/")

GUIDANCE = (
    "The Research Depth Protocol is mandatory and covers TECHNICAL / INFRASTRUCTURE\n"
    "decisions too (SQLite semantics, a UE API, a git internal) - not just game\n"
    "assets (Gate 1 lists Technical Documentation as a source type). Either cite\n"
    "what you looked up:\n"
    '    ... --researched "<what you researched + sources/URLs>"\n'
    "or record why none was needed (a reasoned waiver proceeds - speed-run intact):\n"
    '    ... --research-waiver "<why this change needed no external research>"\n'
    "A silent skip is the exact pattern this gate exists to stop."
)


def enforced() -> bool:
    if os.environ.get("CHIMERA_RESEARCH_GATE", "").strip().lower() in ("warn", "off", "0", "false"):
        return False
    return ENFORCE_DEFAULT


def _is_research(n: dict) -> bool:
    t = n.get("type")
    if t in RESEARCH_TYPES:
        return True
    if t == "Reference" and (n.get("url") or n.get("source") or n.get("citation")):
        return True
    return str(n.get("template_file", "")).startswith(RESEARCH_TEMPLATE_PREFIXES)


# Recipe/phase boilerplate that must NEVER carry a topic match on its own -
# "Build toward the seed: X" and "... in live build" share the word `build`, and a
# naive token match on it passed one session's research off as another's.
_STOP = {"build", "toward", "seed", "live", "remaining", "realize", "witness",
         "collapse", "verify", "verified", "observe", "observed", "session",
         "phase", "task", "update", "fix", "work", "loop", "chimera", "component",
         "toward", "into", "with", "from", "this", "that", "their", "there"}


def _topic_tokens(topic):
    """Distinctive words only: >=5 chars and not recipe boilerplate."""
    import re
    return {w for w in re.split(r"[^A-Za-z0-9]+", (topic or "").lower())
            if len(w) >= 5 and w not in _STOP}


def _about(n, toks):
    if not toks:
        return True                      # no topic given -> time-only (old behaviour)
    blob = " ".join(str(n.get(f) or "") for f in
                    ("feature", "topic", "template_file", "fix_description", "id")).lower()
    return any(t in blob for t in toks)


def _age_h(n):
    ts = str(n.get("timestamp", ""))
    try:
        when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
    except Exception:
        return None
    return (datetime.now(timezone.utc) - when).total_seconds() / 3600.0


def recent_research(nodes, hours=8, topic=""):
    """Research nodes from the last `hours` that are ABOUT `topic`.

    THE 2026-07-16 FIX. This was a bare time window over the WHOLE graph, described
    in its own docstring as "a stateless-CLI proxy for 'this session'". It was not a
    proxy; it was a hole. Proved live: a session that researched NOTHING sailed
    through on the Sky session's node from 3h earlier, because ANY research node
    anywhere satisfied it -- and the gate then TOLD the agent "1 research node(s)
    this session", so the agent reported a waiver it never made. The agent was not
    disobeying the prompt; it believed the checkpoint, which is what checkpoints are
    for. A gate that lies is worse than no gate.

    Scoping by topic mirrors coin_verifier.assemble_evidence (same bug, same fix):
    evidence must be ABOUT the claim, not merely near it in time.
    """
    toks = _topic_tokens(topic)
    out = []
    for n in nodes:
        if not _is_research(n) or not _about(n, toks):
            continue
        age = _age_h(n)
        if age is None or age <= hours:   # undated included (fail-lenient)
            out.append(n)
    return out


def check(nodes, researched="", waiver="", hours=8, topic="", run_id=""):
    """Return (status, detail). status is one of:
        provided  — --researched given (sources cited)
        evidence  — research node(s) recorded for THIS topic
        waived    — --research-waiver given (reasoned skip)
        missing   — nothing; the gate should refuse (if enforced)

    `topic` (the phase/feature) scopes the evidence; `run_id` lets the detail say
    HONESTLY whether the node is this run's own or inherited from another session.
    Never claim "this session" for a node this session did not write - that exact
    sentence is what fooled an agent into reporting a waiver it never made.
    """
    if (researched or "").strip():
        return "provided", researched.strip()
    rec = recent_research(nodes, hours=hours, topic=topic)
    if rec:
        own = [r for r in rec if run_id and r.get("run_id") == run_id]
        src = own or rec
        tags = []
        for r in src[:4]:
            name = str(r.get("feature") or r.get("topic") or r.get("template_file") or r.get("id"))[:40]
            age = _age_h(r)
            who = "THIS run" if (run_id and r.get("run_id") == run_id) else \
                  f"a DIFFERENT run: {r.get('run_id') or '?'}"
            tags.append(f"{name} [{who}" + (f", {age:.1f}h ago]" if age is not None else "]"))
        if own:
            return "evidence", f"{len(own)} research node(s) recorded by THIS run: {'; '.join(tags)}"
        # Say exactly what is known: a different RUN (postflight is its own process, so
        # even a same-session spiral_forks node lands here). Whether that was your work
        # is something this gate cannot know - so it must not imply either way.
        return "evidence", (f"{len(rec)} research node(s) match this topic but were recorded by a "
                            f"different run: {'; '.join(tags)}. If that research was not YOURS, "
                            f"this is not proof you researched - cite your own with --researched.")
    if (waiver or "").strip():
        return "waived", waiver.strip()
    return "missing", ("no research recorded for this topic; no --researched / "
                       "--research-waiver given")
