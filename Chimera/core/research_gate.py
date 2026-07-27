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
import re                       # _SEED_BUILD
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


#: A task whose PREMISE is that the thing does not exist yet. the build-toward-seed rule:
#: "A 'Build toward the seed' task's PREMISE is that the thing does NOT exist — absence
#: is the WORK." These are minted by the helm/wellspring with this exact phrasing, so the
#: match is on the string the machine writes, not on an agent's free prose.
#: Module-level on purpose: `re` was missing from this file (the SIXTH missing stdlib
#: import I have written today), and a module-level compile fails LOUD on load. The same
#: bug inside a branch waits for the one moment the gate matters — which is how a
#: `glob` I forgot would have crashed the evidence gate only when someone cited a fake id.
_SEED_BUILD = re.compile(r"build\s+toward\s+the\s+seed", re.I)

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


def check(nodes, researched="", waiver="", hours=8, topic=""):
    """Return (status, detail). status is one of:
        provided  — --researched given (sources cited)
        evidence  — research node(s) recorded for THIS topic
        waived    — --research-waiver given (reasoned skip)
        missing   — nothing; the gate should refuse (if enforced)

    `topic` (the phase/feature) scopes the evidence: it must be ABOUT the claim, not
    merely near it in time. Never claim "this session" for a node this session did not
    write — that exact sentence is what fooled an agent into reporting a waiver it
    never made, and this gate is where it happened.

    There is no `run_id` parameter, deliberately: I added one and it was unreachable
    (postflight is its own process, RUN_ID is per-process, nothing exports
    CHIMERA_RUN_ID, and --researched returns "provided" before the node scan). A
    parameter that cannot do what its docstring promises is the same defect as a
    message that lies — so it is gone rather than kept as decoration.
    """
    if (researched or "").strip():
        return "provided", researched.strip()
    rec = recent_research(nodes, hours=hours, topic=topic)
    if rec:
        # `run_id` was DEAD CODE and is gone (2026-07-16, same day I added it). I wired a
        # "recorded by THIS run" branch that could never fire: postflight is its own
        # process, RUN_ID is per-process, nothing exports CHIMERA_RUN_ID -- and when
        # --researched IS given this function returns "provided" above without ever
        # reaching here. So the branch was unreachable by construction. A parameter that
        # cannot do what its docstring claims is the defect this gate exists to stop; I
        # shipped one into the gate itself, hours after fixing the same class of bug here.
        #
        # What is left is honest and does not pretend to identify a session: a research
        # node ABOUT this topic, from some run, recently. That legitimately passes -- a
        # subagent researches and the lead closes -- so the message says PASSED and why,
        # rather than the old text which said "this is not proof you researched" and then
        # passed anyway. A gate whose words fight its return value is the original sin.
        tags = []
        for r in rec[:4]:
            name = str(r.get("feature") or r.get("topic") or r.get("template_file") or r.get("id"))[:40]
            age = _age_h(r)
            tags.append(f"{name} [run {r.get('run_id') or '?'}"
                        + (f", {age:.1f}h ago]" if age is not None else "]"))
        return "evidence", (f"ACCEPTED on {len(rec)} research node(s) recorded for THIS TOPIC: "
                            f"{'; '.join(tags)}. This gate cannot tell whose research that was — "
                            f"if it was not yours, cite your own with --researched.")
    if (waiver or "").strip():
        # A SEED-BUILD TASK CANNOT WAIVE RESEARCH (2026-07-16, the human's call).
        #
        # the build-toward-seed rule already states the premise: "A 'Build toward the
        # seed' task's PREMISE is that the thing does NOT exist — absence is the WORK."
        # A task whose premise is that the thing does not exist is EXACTLY the task
        # that cannot inherit its answer from this repo. There is nothing here to copy;
        # that is why the task exists.
        #
        # THE WAIVER THAT PROMPTED THIS, verbatim from CAPCOM: an agent building
        # ADotCharacter waived with "ADotCharacter implementation was based on helm
        # target and existing patterns". Read it again — "based on existing patterns"
        # is not a reason research was unnecessary, it is a description of NOT DOING
        # research, offered as the excuse for not doing it. And it shipped an
        # `int32 MassCount` with zero Mass framework symbols, which is what "existing
        # patterns" gets you when the pattern for the thing does not exist yet (H-21:
        # a verb needs behavior, not metadata).
        #
        # Every other waiver still passes: this refuses ONE class, where the task's own
        # premise contradicts the excuse. That is a FACT about the task, not a judgement
        # about the reason — the gate is not reading the waiver's quality, it is noticing
        # that no waiver can be true here.
        if _SEED_BUILD.search(topic or ""):
            return "unwaivable", (
                f"a seed-build task cannot waive research: {waiver.strip()[:120]!r}. "
                f"This task's PREMISE is that the thing does NOT exist (the build-toward-seed "
                f"rule: absence is the WORK) — so there is nothing in this repo to "
                f"inherit the answer from, which is exactly why the task exists. Cite "
                f"real sources with --researched: UE5.8 documentation for the systems you "
                f"are about to name, a shipped game that solved it, the DSL bible. "
                f"('based on existing patterns' is not a reason research was unnecessary; "
                f"it is a description of not doing research.)")
        return "waived", waiver.strip()
    return "missing", ("no research recorded for this topic; no --researched / "
                       "--research-waiver given")
