"""
THE COIN — the two-sided verification harness (the human's design, 2026-07-14).

"Everything can be built into a verification system that uses the LM Studio
agent + pre-programmed prompts ... the left side of the coin on the one side and
the right side of the coin onto the other. The two sides work as a flipping coin."

THE COIN: every verification has exactly two faces.
    HEADS (the CLAIM)   — what the work is SUPPOSED to be: the feature, its
                          declared status, the agent's own report of what it did.
    TAILS (the EVIDENCE)— what actually IS: screenshot analyses, telemetry,
                          simtest results, test output, read-backs, recorded nodes.

THE FLIP: the judge rules BOTH directions in one pass —
    heads->tails  does the evidence actually demonstrate the claim?  (overclaim check)
    tails->heads  does the claim honestly describe the evidence?     (mislabel check)
Either direction failing = the faces are not the same coin = NOT verified.

This is the layer ABOVE the existence gates (research/witness/visual, which only
check that evidence EXISTS): the coin checks the evidence MATCHES the claim.
Prompts are PRE-PROGRAMMED (the PROMPTS registry) — not ad-hoc per call.
LM convention mirrors core/critic.py (H-3: scan content + reasoning_content for a
JSON blob, schema-validate, retry with a larger token budget; a reasoning dump is
never a verdict). ~20 tok/s local model: ONE call judges both directions.

CLI:
    python -m core.coin_verifier --claim "..." --evidence "..." [--kind feature_verify]
    python -m core.coin_verifier --feature X --status verified  (auto-assembles both faces)
Toggle: CHIMERA_COIN_GATE=warn (or off) softens the postflight block -> warn.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from core.lm_gateway import LM_MODEL as LM_STUDIO_MODEL
except Exception:
    LM_STUDIO_MODEL = ""   # blank ON PURPOSE — see lm_gateway.LM_MODEL. Naming a
                           # model here would pin one the operator never chose.

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
ENFORCE_DEFAULT = True

# ---------------------------------------------------------------------------
# PRE-PROGRAMMED PROMPTS — one per verification kind; DEFAULT covers the rest.
# Each receives the two faces in fixed slots. Kept tight (~20 tok/s model).
# ---------------------------------------------------------------------------
_COIN_CORE = (
    "You are THE COIN JUDGE for a game studio. A verification has two faces:\n"
    "HEADS = the CLAIM (what the work is supposed to be).\n"
    "TAILS = the EVIDENCE (what was actually measured/recorded).\n"
    "Rule BOTH directions:\n"
    "  heads_to_tails: does the evidence actually demonstrate the claim? "
    "(a compile alone never demonstrates gameplay; unit tests alone never "
    "demonstrate felt experience)\n"
    "  tails_to_heads: does the claim honestly describe the evidence? "
    "(no overclaiming, no relabeling partial results as complete)\n"
    "The coin is genuine only if BOTH hold. Respond with ONLY a JSON object:\n"
    '{"same_coin": true|false, '
    '"heads_to_tails": {"holds": true|false, "reason": "<one sentence>"}, '
    '"tails_to_heads": {"holds": true|false, "reason": "<one sentence>"}, '
    '"verdict": "VERIFIED"|"NEEDS_REFINEMENT", '
    '"mismatches": ["<specific gap>"], "confidence": 0.0-1.0}'
)

PROMPTS = {
    "DEFAULT": _COIN_CORE,
    "feature_verify": _COIN_CORE + (
        "\nContext: the claim marks a game FEATURE as verified/observed. Evidence "
        "must show the feature exercised for real (playtest/telemetry/screenshot "
        "analysis), not merely built."),
    "visual": _COIN_CORE + (
        "\nContext: the evidence face is an LM screenshot analysis of the live "
        "viewport. It must actually describe what the claim promises on screen."),
    "build": _COIN_CORE + (
        "\nContext: the claim reports a build/compile result. The evidence face "
        "must contain real toolchain output (UBT lines), not a summary."),
}


def enforced():
    if os.environ.get("CHIMERA_COIN_GATE", "").strip().lower() in ("warn", "off", "0", "false"):
        return False
    return ENFORCE_DEFAULT


# ---------------------------------------------------------------------------
# face assembly — build the two faces from the DNA graph for a feature
# ---------------------------------------------------------------------------
def _recent(nodes, hours=12):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    for n in nodes:
        ts = str(n.get("timestamp", ""))
        try:
            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
        except Exception:
            when = None
        if when is None or when >= cutoff:
            yield n


def assemble_evidence(nodes, feature=None, hours=12, cap=14):
    """TAILS: this session's hard evidence, compacted to text lines."""
    lines = []
    for n in _recent(nodes, hours):
        t = n.get("type", "")
        tf = str(n.get("template_file", ""))
        if t == "SimPlaytest":
            lines.append(f"[simtest] {n.get('session')} {n.get('beats_reached')}/"
                         f"{n.get('beats_total')} beats ({n.get('demo')})")
        elif tf.startswith("visual_verification"):
            lines.append(f"[visual] {str(n.get('fix_description') or n.get('analysis') or tf)[:160]}")
        elif t == "Health" or n.get("fps") is not None:
            lines.append(f"[telemetry] fps={n.get('fps')} status={n.get('status')}")
        elif t == "ProfessorGrade" and (not feature or n.get("feature") == feature):
            lines.append(f"[grade] {n.get('feature')}: {n.get('grade')}")
        elif t == "FeatureUpdate" and feature and n.get("feature_name") == feature:
            lines.append(f"[ledger] {feature} -> {n.get('status')}")
        if len(lines) >= cap:
            break
    return "\n".join(lines) or "(no evidence nodes recorded this session)"


def assemble_claim(feature, status, result="", notes=""):
    """HEADS: what is being asserted."""
    parts = [f"Feature '{feature}' is being recorded as '{status}'."]
    if result:
        parts.append(f"Agent's report: {result[:400]}")
    if notes:
        parts.append(f"Notes: {notes[:200]}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# the judgment — ONE LM call, both directions (H-3 discipline throughout)
# ---------------------------------------------------------------------------
def _validate(c):
    if not isinstance(c, dict) or not isinstance(c.get("same_coin"), bool):
        return False
    for d in ("heads_to_tails", "tails_to_heads"):
        if not isinstance(c.get(d), dict) or not isinstance(c[d].get("holds"), bool):
            return False
    return c.get("verdict") in ("VERIFIED", "NEEDS_REFINEMENT")


def judge(claim, evidence, kind="DEFAULT", max_retries=1):
    """Flip the coin: returns the validated judgment dict, or None if the LM is
    unavailable/unparseable after retries (caller decides pass-open vs block)."""
    system = PROMPTS.get(kind, PROMPTS["DEFAULT"])
    user = f"HEADS (the CLAIM):\n{claim}\n\nTAILS (the EVIDENCE):\n{evidence}"
    budget = int(os.environ.get("CHIMERA_LM_MAX_TOKENS", "32768"))  # 262k-ctx models: one generous attempt beats a retry ladder
    for _ in range(max_retries + 1):
        payload = {"model": LM_STUDIO_MODEL,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                   "max_tokens": budget, "temperature": 0.2}
        req = urllib.request.Request(LM_STUDIO_URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            from core.lm_gateway import lm_urlopen, LM_TIMEOUT
            with lm_urlopen(req, timeout=LM_TIMEOUT, agent="coin-verifier") as r:
                msg = json.load(r)["choices"][0]["message"]
        except Exception:
            return None
        for text in (msg.get("content") or "", msg.get("reasoning_content") or ""):
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                continue
            try:
                c = json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
            if _validate(c):
                c.setdefault("mismatches", [])
                c.setdefault("confidence", 0.5)
                return c
        budget *= 2             # H-3: a reasoning dump is a retry, never a verdict
    return None


def format_judgment(j):
    ok = "SAME COIN" if j.get("same_coin") else "NOT THE SAME COIN"
    lines = [f"  {ok} -> {j.get('verdict')} (confidence {j.get('confidence')})",
             f"  heads->tails (evidence proves claim): "
             f"{'holds' if j['heads_to_tails']['holds'] else 'FAILS'} - {j['heads_to_tails'].get('reason','')[:120]}",
             f"  tails->heads (claim honest to evidence): "
             f"{'holds' if j['tails_to_heads']['holds'] else 'FAILS'} - {j['tails_to_heads'].get('reason','')[:120]}"]
    for m in (j.get("mismatches") or [])[:4]:
        lines.append(f"  x {str(m)[:120]}")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(prog="coin_verifier", description="THE COIN - two-sided LM verification")
    p.add_argument("--claim", default="", help="HEADS: the claim text")
    p.add_argument("--evidence", default="", help="TAILS: the evidence text")
    p.add_argument("--feature", default="", help="auto-assemble both faces for this feature")
    p.add_argument("--status", default="verified")
    p.add_argument("--result", default="")
    p.add_argument("--kind", default="DEFAULT", choices=sorted(PROMPTS))
    a = p.parse_args(argv)

    claim, evidence = a.claim, a.evidence
    if a.feature and not (claim and evidence):
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            from core.graphify_interface import load_dna_graph
        except ImportError:
            from graphify_interface import load_dna_graph
        nodes = load_dna_graph().get("nodes", [])
        claim = claim or assemble_claim(a.feature, a.status, a.result)
        evidence = evidence or assemble_evidence(nodes, feature=a.feature)
    if not (claim and evidence):
        print("need --claim + --evidence, or --feature")
        return 2
    print(f"HEADS:\n{claim}\n\nTAILS:\n{evidence}\n\nflipping the coin (LM judging both directions)...")
    j = judge(claim, evidence, kind=a.kind)
    if j is None:
        print("coin toss failed: LM unavailable or unparseable after retries")
        return 3
    print(format_judgment(j))
    return 0 if j.get("same_coin") else 1


if __name__ == "__main__":
    sys.exit(main())
