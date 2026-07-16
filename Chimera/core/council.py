"""
council — FACILITATED DIALOGUE between the fast brain and the deep brain.

The human's design (2026-07-15): "Communication facilitates innovation... I don't
care if it's between two AIs, two humans, or two ants." The FAST worker (LM Studio
/ qwen, via `core.lm_gateway`) does the legwork and thinks quickly; it BOUNCES its
reasoning off the DEEP mind (DeepSeek-V4 / ds4, via `core.ds4_brain`), which is
slow but reasons further and sees non-obvious structure. They take turns seeing
each other's thinking; a SYNTHESIS step names what EMERGED that neither started
with — and (optionally) records it so the studio keeps the discovery.

  python -m core.council "<topic or problem>" [--rounds 2] [--record]
                         [--deep-tokens 600] [--fast-tokens 700]

Routing: FAST goes through lm_gateway (fair queue + model adoption, untouched).
DEEP goes through ds4_brain to localhost:8000. Both are OpenAI-compatible.
DEEP is slow (~1.6 t/s): each deep turn of N tokens ~ N/1.6 seconds — keep rounds
and --deep-tokens modest. It's a REASONING model, so it needs some room to think.
"""
import argparse
import json
import sys
import time
import urllib.request

from core.lm_gateway import lm_urlopen, resolve_model, LM_BASE
from core import ds4_brain

FAST_SYS = (
    "You are the FAST WORKER — one of two minds in a council. You do the hands-on "
    "work and think quickly. Your partner is the DEEP mind: slower, but it reasons "
    "further and sees non-obvious structure. Your job is NOT to defer to it or to "
    "defend yourself — it is to THINK TOGETHER toward an idea neither of you had "
    "alone. Be concrete, disagree when you should, and build on what is genuinely "
    "useful. Keep each turn tight (a few sharp paragraphs, not an essay).")

DEEP_SYS = (
    "You are the DEEP mind — one of two in a council. Your partner is a FAST worker "
    "who does the hands-on legwork. You are slower but you reason further. Your job "
    "is to pressure-test, reframe, and surface the non-obvious: the hidden "
    "assumption, the structural insight, the third option no one named. Do NOT "
    "merely agree or summarize — push the thinking somewhere new. Be focused; a "
    "few dense paragraphs.")


def _extract(data) -> str:
    """Reasoning models (qwen-agentworld, DeepSeek-V4) keep their real output in
    `reasoning_content` and often leave `content` EMPTY under a tight budget (the
    human's diagnosis, 2026-07-15: "where the model keeps its output is in the
    reasoning — that's what makes it great"). Prefer a clean final `content`; fall
    back to the reasoning, which IS the substance for these models."""
    msg = data["choices"][0]["message"]
    for k in ("content", "reasoning_content", "reasoning"):
        v = (msg.get(k) or "").strip()
        if v:
            return v
    return ""


def _fast(user_content, max_tokens=1200, temperature=0.6, agent="council-fast",
          system=None):
    """`system` overrides the council persona for callers that are NOT in a dialogue.

    FAST_SYS tells the model it is one of two minds talking to a partner. That is
    right for the council and WRONG for anything that just wants an answer in a fixed
    format: the expectation_violator reused this path and got drafts, "Wait,"
    asides, and its own persona handed back as a design candidate ("Role:** FAST
    WORKER - concrete, quick..." scored 7/10 and claimed an archive cell). Borrowing
    a call path silently borrows its persona."""
    body = {"model": resolve_model(), "temperature": temperature,
            "max_tokens": max_tokens, "stream": False,
            "messages": [{"role": "system", "content": system or FAST_SYS},
                         {"role": "user", "content": user_content}]}
    req = urllib.request.Request(
        LM_BASE + "/v1/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with lm_urlopen(req, agent=agent) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    return _extract(data)


def _deep(user_content, max_tokens=600, temperature=0.5):
    return ds4_brain.chat(
        [{"role": "system", "content": DEEP_SYS},
         {"role": "user", "content": user_content}],
        max_tokens=max_tokens, temperature=temperature).strip()


def _render(topic, transcript):
    lines = [f"TOPIC: {topic}", ""]
    for who, text in transcript:
        lines.append(f"--- {who} ---\n{text}\n")
    return "\n".join(lines)


def dialogue(topic, rounds=2, fast_tokens=1200, deep_tokens=700, echo=True):
    """Run the council. Returns [(speaker, text), ...] ending in SYNTHESIS."""
    transcript = []

    def _log(who, text):
        transcript.append((who, text))
        if echo:
            print(f"\n===== {who} =====\n{text}", flush=True)

    # FAST opens: a working take + the ONE thing it wants pressure-tested.
    _log("FAST", _fast(
        f"TOPIC: {topic}\n\nGive your initial working take, then state the ONE "
        f"question or assumption you most want the DEEP mind to pressure-test.",
        max_tokens=fast_tokens))

    for i in range(rounds):
        _log("DEEP", _deep(
            _render(topic, transcript) + "\n\nRespond as the DEEP mind: challenge, "
            "reframe, or extend. Surface something non-obvious the FAST mind missed.",
            max_tokens=deep_tokens))
        _log("FAST", _fast(
            _render(topic, transcript) + "\n\nRespond as the FAST mind: integrate "
            "what is useful, push back on what is not, and ADVANCE the idea toward "
            "something concrete.", max_tokens=fast_tokens))

    # SYNTHESIS — name what EMERGED (fast brain, quick).
    _log("SYNTHESIS", _fast(
        _render(topic, transcript) + "\n\nStep out of the dialogue. In 3-6 crisp "
        "bullets, name what NEW emerged here — an idea, reframe, or plan that "
        "NEITHER of you stated at the start. End with ONE concrete next action.",
        max_tokens=fast_tokens))
    return transcript


def _record(topic, transcript):
    """Keep the discovery: CAPCOM signal + a Surprise node (nightly-distiller fodder)."""
    synth = next((t for w, t in reversed(transcript) if w == "SYNTHESIS"), "")
    try:
        from core.capcom import post_safe
        post_safe("council", f"two-brain dialogue on '{topic[:60]}' -> "
                  f"{synth[:180].replace(chr(10), ' ')}", level="note", source="council")
    except Exception:
        pass
    try:
        from core.graphify_interface import record_surprise
        record_surprise(
            context=f"council dialogue (fast qwen x deep ds4) on: {topic[:120]}",
            reality=synth[:400],
            expectation="single-model reasoning; the two-brain exchange surfaced the above",
            source="agent")
    except Exception:
        pass
    return synth


# ---------------------------------------------------------------------------
# SECOND-SYSTEM REVIEW — the human's design (2026-07-15): "the fast has to consult
# with the slow before any final decisions on a feature... another person in the
# room... a reality check for hallucinating agents... an airplane flies with two
# systems for propulsion." The DEEP brain (ds4, a DIFFERENT model) reviews a
# feature finalization GROUNDED IN MEMORY. Different architecture => different
# failure modes than the fast agent, so it catches hallucinations the Coin (one
# model checking itself) structurally cannot. Fires once per feature finalization.
# ---------------------------------------------------------------------------
def gate_mode() -> str:
    """block | warn | off. Default warn (advisory): the deep brain is slow/optional,
    so it RECORDS a second opinion + shouts on REJECT, but only hard-blocks when the
    operator opts in (CHIMERA_COUNCIL_GATE=block). =off disables."""
    import os
    v = os.environ.get("CHIMERA_COUNCIL_GATE", "warn").strip().lower()
    return v if v in ("block", "warn", "off") else "warn"


# Budget for the deep review. 700 was STARVATION: ds4 is a reasoning model that thinks
# IN the output (CLAUDE.md: "give `ask` a large --max-tokens or it stops mid-think"), so
# 700 bought a truncated thinking trace and never the answer block — and the old parser
# then consumed that trace as ENDORSE. The cost is real and honest: ds4 runs ~1.6 t/s on
# CPU, so a full 2048-token review is minutes, not seconds. That is the price of a second
# opinion from a different mind; a fast fabricated one is worth nothing.
_REVIEW_BUDGET = 2048
_VERDICTS = ("ENDORSE", "CONCERN", "REJECT")


def _validate_review(c) -> bool:
    """Schema-validate before consuming (H-3). Note what this rejects for free: a model
    that merely RESTATES its output format emits verdict="ENDORSE|CONCERN|REJECT", which
    is not in _VERDICTS — the echo that used to score ENDORSE now fails the schema."""
    return (isinstance(c, dict)
            and str(c.get("verdict", "")).strip().upper() in _VERDICTS
            and isinstance(c.get("reason"), str)
            and len(c["reason"].strip()) >= 20)


def _parse_review(raw: str):
    """The LAST schema-valid JSON object in the reply, or None.

    LAST, not first: a reasoning model drafts the shape early ("I should answer
    {verdict: ...}") and commits to it at the end. Taking the first match reads its
    deliberation instead of its conclusion — the same bug that made every
    expectation_violator candidate score 3.0 off an echoed answer template.
    """
    import json as _json
    import re as _re
    blobs = [m.group(0) for m in _re.finditer(r"\{.*?\}", raw, _re.DOTALL)]
    g = _re.search(r"\{.*\}", raw, _re.DOTALL)          # outermost, in case of nesting
    if g:
        blobs.append(g.group(0))
    for blob in reversed(blobs):
        try:
            c = _json.loads(blob)
        except Exception:
            continue
        if _validate_review(c):
            return c
    return None


def review(feature, status, result="", notes="", nodes=None, deep_tokens=None,
           max_retries=1):
    """The DEEP brain's independent, memory-grounded second opinion on finalizing
    `feature` as `status`. Returns {up, verdict: ENDORSE|CONCERN|REJECT|UNAVAILABLE,
    reasoning, missing}. Never raises.

    UNAVAILABLE means the deep brain gave no schema-valid verdict — NOT approval. This
    gate exists to catch what the Coin structurally cannot (one model checking itself),
    so a gate that invents ENDORSE when it cannot read the answer is worse than no gate:
    it reports redundancy that does not exist.
    """
    import re
    # 1) The claim + evidence — reuse the Coin's assembly so both gates see the same faces.
    try:
        from core.coin_verifier import assemble_claim, assemble_evidence
        from core.graphify_interface import load_dna_graph
        if nodes is None:
            nodes = load_dna_graph().get("nodes", [])
        claim = assemble_claim(feature, status, result, notes)
        evidence = assemble_evidence(nodes, feature=feature)
    except Exception:
        claim = f"{feature} -> {status}. {result}".strip()
        evidence = notes or "(evidence unavailable)"
    # 2) MEMORY — rep status + what the studio has already learned about this feature.
    mem = []
    try:
        from core.rep_engine import rep_gate
        elig, reason = rep_gate(feature)
        mem.append(f"rep gate: {'READY' if elig else 'NOT met'} — {reason}")
    except Exception:
        pass
    try:
        from core.history_book import search as _hsearch
        hits = _hsearch(feature, limit=5) or []
        if hits:
            mem.append("history book (what the studio has learned):\n" +
                       "\n".join(f"  - {str(h)[:180]}" for h in hits[:5]))
    except Exception:
        pass
    memory = "\n".join(mem) or "(no prior memory retrieved)"
    # 3) Ask the deep brain — as the independent second system.
    prompt = (
        "You are the DEEP REVIEWER — a SECOND, INDEPENDENT system (a different model, "
        "with the studio's memory). A fast agent is about to FINALIZE a feature. This "
        "is a redundancy / reality-check: does the EVIDENCE actually support the "
        "CLAIM, or is this a hallucination or an overreach?\n\n"
        f"FEATURE: {feature}\nCLAIMED STATUS: {status}\n\n"
        f"THE CLAIM:\n{claim}\n\nTHE EVIDENCE:\n{evidence}\n\n"
        f"STUDIO MEMORY:\n{memory}\n\n"
        "Respond with ONLY a JSON object, and nothing after it:\n"
        '{"verdict": "ENDORSE" or "CONCERN" or "REJECT", '
        '"reason": "<2-4 specific sentences naming any missing proof or hallucination>", '
        '"missing": ["<specific evidence that should exist and does not>"]}')
    # H-3, THE HARD WAY (2026-07-16). This used to substring-scan the reply and, failing
    # that, "infer conservatively" -- to ENDORSE. Replayed verbatim: "" -> ENDORSE,
    # "   " -> ENDORSE, "I need more information to assess this." -> ENDORSE. The
    # airplane-redundancy check's failure mode was to APPROVE. Two more teeth in it:
    # the old regex took the FIRST match while the PROMPT ITSELF contains the line
    # "VERDICT: ENDORSE | CONCERN | REJECT", so a model merely restating its output
    # format scored ENDORSE; and deep_tokens defaulted to 700, the same starvation that
    # made every expectation_violator candidate score exactly 3.0 -- so the dump this
    # gate then consumed was one IT had caused.
    #
    # H-3 is auto-promoted constitution: "An LM response containing its own reasoning
    # dump is a RETRY with a larger token budget, never a verdict -- schema-validate
    # before consuming." coin_verifier.judge() has honoured it since it was written.
    # This function is the OTHER half of the same redundancy and did not.
    #
    # Now: schema-valid JSON or nothing. A restated format spec fails validation
    # ("ENDORSE|CONCERN|REJECT" is not a verdict). Unparseable -> retry at 2x budget ->
    # UNAVAILABLE, never a guess. UNAVAILABLE is honest and costs only the second
    # opinion; ENDORSE was a fabricated approval wearing one.
    budget = int(deep_tokens or _REVIEW_BUDGET)
    for _ in range(max_retries + 1):
        try:
            raw = ds4_brain.chat([{"role": "user", "content": prompt}],
                                 max_tokens=budget, temperature=0.2)
        except Exception as e:
            return {"up": False, "verdict": "UNAVAILABLE", "reasoning": str(e)[:160]}
        c = _parse_review(raw or "")
        if c:
            return {"up": True, "verdict": str(c["verdict"]).upper(),
                    "reasoning": str(c["reason"])[:1400],
                    "missing": list(c.get("missing") or [])}
        budget *= 2          # H-3: a dump is a retry, never a verdict
    return {"up": True, "verdict": "UNAVAILABLE", "missing": [],
            "reasoning": ("the deep brain returned no schema-valid verdict after "
                          f"{max_retries + 1} attempts (reasoning dump or truncation). "
                          "H-3: a dump is a RETRY, never a verdict — so this is "
                          "UNAVAILABLE, not ENDORSE. There is no second opinion here.")}


def main(argv=None):
    p = argparse.ArgumentParser(prog="council", description=__doc__.split("\n")[1])
    p.add_argument("topic", help="the problem/question the two brains discuss")
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--fast-tokens", type=int, default=1200, dest="fast_tokens")
    p.add_argument("--deep-tokens", type=int, default=700, dest="deep_tokens")
    p.add_argument("--record", action="store_true",
                   help="post the synthesis to CAPCOM + record a Surprise node")
    a = p.parse_args(argv)
    t0 = time.time()
    try:
        transcript = dialogue(a.topic, rounds=a.rounds,
                              fast_tokens=a.fast_tokens, deep_tokens=a.deep_tokens)
    except Exception as e:
        print(f"council failed: {e}\n"
              f"(need a model loaded in LM Studio AND ds4 up: "
              f"python -m core.ds4_brain status)", file=sys.stderr)
        return 1
    if a.record:
        _record(a.topic, transcript)
        print("\n[recorded to CAPCOM + DNA graph]")
    print(f"\n[council done in {time.time()-t0:.0f}s, {a.rounds} rounds]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
