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


def recent_research(nodes, hours=8):
    """Research nodes recorded within the last `hours` — a stateless-CLI proxy
    for 'this session'. Undated nodes are included (fail-lenient)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out = []
    for n in nodes:
        if not _is_research(n):
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


def check(nodes, researched="", waiver="", hours=8):
    """Return (status, detail). status is one of:
        provided  — --researched given (sources cited)
        evidence  — research nodes recorded this session
        waived    — --research-waiver given (reasoned skip)
        missing   — nothing; the gate should refuse (if enforced)
    """
    if (researched or "").strip():
        return "provided", researched.strip()
    rec = recent_research(nodes, hours=hours)
    if rec:
        tags = [str(r.get("feature") or r.get("topic")
                    or r.get("template_file") or r.get("id"))[:44] for r in rec[:5]]
        return "evidence", f"{len(rec)} research node(s) this session: {', '.join(tags)}"
    if (waiver or "").strip():
        return "waived", waiver.strip()
    return "missing", "no research recorded this session; no --researched / --research-waiver given"
