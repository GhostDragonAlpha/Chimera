"""
Visual Gate — no feature reaches 'verified'/'observed' without an LM-Studio
screenshot analysis on record.

Why (2026-07-14, the human): the studio already HAS the machinery to capture the
viewport (MCP control_editor screenshot mode=editor_viewport) and have the local
model LOOK at it (core/visual_verifier.py: capture_screenshot + analyze_screenshot),
but NOTHING required it -- the LM screenshot analysis was "tertiary, when
requested", so it got skipped. This makes it a hard requirement, in the same
"bare 'blocked' is forbidden" idiom as the research and witness gates:

to mark a feature verified/observed you must EITHER have a recorded visual
verification this session, OR cite the analysis (--visual-analysis), OR record a
reasoned waiver (--visual-waiver, e.g. a non-visual feature, or the editor / MCP
bridge is down and a shot genuinely can't be taken).

The recorded evidence is a visual-verification node (template_file
"visual_verification/...") written by core/visual_verifier.py after it captures a
viewport screenshot and sends it to LM Studio for a VERIFIED / NEEDS_REFINEMENT
judgment. Agent-agnostic (plain Python over the DNA graph).
Toggle: CHIMERA_VISUAL_GATE=warn (or off) softens block -> warn.
"""
import os
from datetime import datetime, timedelta, timezone

ENFORCE_DEFAULT = True
VERIFIED_STATUSES = {"verified", "observed", "observed_provisional"}

GUIDANCE = (
    "A feature marked verified/observed needs the local model to have LOOKED at it.\n"
    "Either run the visual verification (captures the viewport + LM judges it):\n"
    "    python -m core.visual_verifier --feature <X>\n"
    "or cite an analysis you already have:\n"
    '    ... --visual-analysis "<what the LM saw + VERIFIED/NEEDS_REFINEMENT + shot path>"\n'
    "or record why a screenshot analysis does not apply (non-visual feature, or the\n"
    "editor / MCP bridge is down so a shot genuinely cannot be taken):\n"
    '    ... --visual-waiver "<why>"'
)


def enforced():
    if os.environ.get("CHIMERA_VISUAL_GATE", "").strip().lower() in ("warn", "off", "0", "false"):
        return False
    return ENFORCE_DEFAULT


def _is_visual(n):
    tf = str(n.get("template_file", ""))
    if tf.startswith("visual_verification"):
        return True
    return n.get("type") in ("VisualVerification", "ScreenshotAnalysis")


def recent_visual(nodes, hours=12):
    """Visual-verification (LM screenshot analysis) nodes recorded this session."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out = []
    for n in nodes:
        if not _is_visual(n):
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


def check(nodes, status=None, analysis="", waiver="", hours=12):
    """(result, detail). result: n/a | provided | evidence | waived | missing.
    Only gates a verify/observe transition."""
    if status not in VERIFIED_STATUSES:
        return "n/a", "not a verify/observe transition"
    if (analysis or "").strip():
        return "provided", analysis.strip()
    ev = recent_visual(nodes, hours=hours)
    if ev:
        return "evidence", f"{len(ev)} LM screenshot-analysis node(s) this session"
    if (waiver or "").strip():
        return "waived", waiver.strip()
    return "missing", ("no LM screenshot analysis on record this session "
                       "(a visual_verification node) — the local model never looked at it")
