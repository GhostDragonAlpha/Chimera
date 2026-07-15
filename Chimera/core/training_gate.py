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
    elif not enrolled:
        pass
    return "missing", "; ".join(misses) or reason
