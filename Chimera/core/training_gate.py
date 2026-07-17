"""
Training Gate — every feature is FORCED through training, one piece at a time.

Why (2026-07-14, the human): "my goal is to train everything, just one piece at
a time." The training machinery existed — the Curriculum (features go to school,
K->PhD checkpoint bands) and the Rep Engine (resolution by accumulated reps,
>=200 + a >=95% 8-run streak) — but BOTH were optional in practice: CLAUDE.md
said features "should" enroll (exactly ONE feature was enrolled), and the rep
gate was advisory unless CHIMERA_ENFORCE_REP_GATE=1. A feature could reach
'verified' having never attended school and never earned a rep.

This gate makes training non-skippable at the ledger transition, tiered to match
the constitution's own ladder:

  verified              -> the feature must be ENROLLED in the curriculum AND
                           have a rep battery with at least one recorded rep
                           (training has genuinely begun).
  observed / observed_provisional (the true collapse)
                        -> ENROLLED + the FULL rep gate (rep_engine.rep_gate:
                           threshold reps + streak) must be eligible.

A reasoned --training-waiver proceeds (recorded + CAPCOM-posted); a silent skip
is refused, in the same "bare 'blocked' is forbidden" idiom as the research /
witness / visual gates. CHIMERA_TRAINING_GATE=warn softens block -> warn.
Agent-agnostic: plain Python over the curriculum transcripts + rep ledger.
"""
import os

ENFORCE_DEFAULT = True
VERIFIED_STATUSES = {"verified", "observed", "observed_provisional"}
COLLAPSE_STATUSES = {"observed", "observed_provisional"}


def enforced():
    if os.environ.get("CHIMERA_TRAINING_GATE", "").strip().lower() in ("warn", "off", "0", "false"):
        return False
    return ENFORCE_DEFAULT


def guidance(feature):
    f = feature or "<feature>"
    return (
        f"Training is mandatory — every feature goes through school, one piece at a time:\n"
        f"  enroll it:        python -m core.curriculum enroll --feature {f}\n"
        f"  build its battery: python -m core.rep_engine build   (atoms are auto-generated)\n"
        f"  earn reps:        python -m core.rep_engine tend     (runs every battery)\n"
        f"  check the gate:   python -m core.rep_engine gate --feature {f}\n"
        f"or record why training genuinely doesn't apply:\n"
        f'  ... --training-waiver "<why>"'
    )


def check(feature, status=None, waiver="", ):
    """(result, detail). result: n/a | evidence | waived | missing."""
    if status not in VERIFIED_STATUSES or not feature:
        return "n/a", "not a feature verify/observe transition"

    # Enrollment — the curriculum transcript IS the school record.
    try:
        from core.curriculum import _transcript_path
        enrolled = _transcript_path(feature).exists()
    except Exception:
        enrolled = False

    # Rep training state.
    eligible, reason = False, "rep engine unavailable"
    try:
        from core.rep_engine import rep_gate
        eligible, reason = rep_gate(feature)
    except Exception as e:
        reason = f"rep engine unavailable ({e})"
    never_trained = str(reason).startswith("no reps recorded")

    if status in COLLAPSE_STATUSES:
        if enrolled and eligible:
            return "evidence", f"enrolled + rep gate READY ({reason if reason else 'threshold met'})"
        if (waiver or "").strip():
            return "waived", waiver.strip()
        misses = []
        if not enrolled:
            misses.append("NOT ENROLLED in the curriculum")
        if not eligible:
            misses.append(f"rep gate not met: {reason}")
        return "missing", "; ".join(misses)

    # status == verified: training must have BEGUN (enrolled + >=1 rep recorded).
    if enrolled and not never_trained:
        return "evidence", ("enrolled + training underway "
                            + ("(rep gate READY)" if eligible else f"({reason})"))
    if (waiver or "").strip():
        return "waived", waiver.strip()
    misses = []
    if not enrolled:
        misses.append("NOT ENROLLED in the curriculum")
    if never_trained:
        misses.append("zero reps recorded (training never began)")
    return "missing", "; ".join(misses) or reason


# ---------------------------------------------------------------------------
# Training at TASK CLOSURE (2026-07-15) — the unit of training is the PIECE the
# agent is working on: the claimed TASK, at ANY granularity (a period to a whole
# system). The old feature-verify gate sat on a path task-closure never took, so
# real work escaped training (all 4 stress-test agents closed tasks untrained).
# DOMAIN-APPROPRIATE policy (the human's choice): every task IS trained, by the
# mechanism that logically fits its KIND. Only a GAME task must show curriculum+
# reps; the others each have a stated reason they train differently.
GAME_MARKERS = ("source/chimera", "tests/dsl_grammar", "content/", ".chimera",
                "game_code_generator")
_KIND_TRAINING = {
    "infra": "proof-of-work: passing tests + the exit's verbatim evidence "
             "(no game artifact exists to mint rep atoms from)",
    "research": "the research gate (sources/waiver) — the deliverable is knowledge",
    "witness": "it RUNS the training-evaluation (collapse), it is not a new trainable",
}


def _task_subject(task) -> str:
    """The game feature a task is ABOUT, with the recipe verb stripped."""
    import re
    s = str((task or {}).get("feature") or (task or {}).get("title") or "").strip()
    for pat in (r"^Fix\s+\d+\s+red\s+rep\s+atom\(s\):\s*", r"^Build toward the seed:\s*",
                r"^Witness & collapse:\s*", r"^Witness:\s*", r"^Collapse:\s*",
                r"^Research:\s*"):
        s = re.sub(pat, "", s, flags=re.IGNORECASE)
    return s.strip()


def classify_task(task) -> str:
    """game | infra | research | witness — the domain that decides HOW it trains."""
    import re
    title = str((task or {}).get("title") or "").lower()
    if title.startswith("research:") or re.match(r"^\s*research\b", title):
        return "research"
    if "witness" in title or "collapse" in title or title.startswith("observe"):
        return "witness"
    files = " ".join((task or {}).get("resources", {}).get("files", []) or []).lower()
    if any(m in files for m in GAME_MARKERS):
        return "game"
    if files and ("core/" in files or "docs/" in files):
        return "infra"
    return "game"  # default: an unclassified named piece is treated as game work


def check_task(task, waiver: str = ""):
    """(status, detail). status: n/a | evidence | waived | missing. Only a GAME
    task requires curriculum+reps; the rest are trained by their domain mechanism."""
    kind = classify_task(task)
    if kind != "game":
        return "n/a", f"{kind} task — trained by {_KIND_TRAINING[kind]}"
    subject = _task_subject(task)
    if not subject:
        return "n/a", "no identifiable game subject"
    try:
        from core.curriculum import _transcript_path
        enrolled = _transcript_path(subject).exists()
    except Exception:
        enrolled = False
    reps_begun, reason = False, "rep engine unavailable"
    try:
        from core.rep_engine import rep_gate
        _elig, reason = rep_gate(subject)
        reps_begun = not str(reason).startswith("no reps recorded")
    except Exception:
        pass
    if enrolled and reps_begun:
        return "evidence", f"'{subject}' enrolled + reps begun"
    if (waiver or "").strip():
        return "waived", waiver.strip()
    misses = []
    if not enrolled:
        misses.append("NOT ENROLLED in the curriculum")
    if not reps_begun:
        misses.append("no reps begun on its battery")
    return "missing", f"'{subject}': " + "; ".join(misses)


def task_guidance(task) -> str:
    s = _task_subject(task) or "<subject>"
    return ("This PIECE must go to school before it closes — train the one thing you "
            "worked, one at a time:\n"
            f'  python -m core.curriculum enroll --feature "{s}"\n'
            "  python -m core.rep_engine tend      (earn reps on its battery)\n"
            'or record an honest exception:  --training-waiver "<why>"')


def enforce_task_or_raise(task, waiver: str = "", agent: str = ""):
    """Raise ValueError (surfaced as REFUSED) when a GAME task closes untrained and
    the gate is enforced. n/a / evidence / waived pass through. Returns (status,
    detail) so the caller can log the domain-appropriate mechanism.

    Also PUSHES the notable outcome onto CAPCOM (the human's design, 2026-07-15):
    the LEAD agent runs CAPCOM and dispatches FOCUSED subagents, one per task, so
    each focused piece's training status must flow back UP to the operator channel
    the lead reads. A blocked/waived closure the lead didn't do itself is exactly
    the kind of signal CAPCOM exists to surface."""
    status, detail = check_task(task, waiver=waiver)
    tid = str((task or {}).get("id", "?"))
    who = agent or "subagent"
    try:
        from core.capcom import post_safe
        if status == "missing" and enforced():
            post_safe("training", f"BLOCKED closure: {who} on {tid} untrained — {detail[:64]}",
                      level="warn", source="training-gate")
        elif status == "waived":
            post_safe("training", f"WAIVED: {who} closed {tid} untrained — {detail[:58]}",
                      level="note", source="training-gate")
    except Exception:
        pass
    if status == "missing" and enforced():
        raise ValueError(f"TRAINING GATE (task closure) — {detail}. The piece you "
                         f"worked must be trained before it can close.\n{task_guidance(task)}")
    return status, detail
