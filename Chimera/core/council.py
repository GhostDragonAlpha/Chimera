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


def review(feature, status, result="", notes="", nodes=None, deep_tokens=700):
    """The DEEP brain's independent, memory-grounded second opinion on finalizing
    `feature` as `status`. Returns {up, verdict: ENDORSE|CONCERN|REJECT|UNAVAILABLE,
    reasoning}. Never raises."""
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
        "Answer starting with exactly one line:\n"
        "VERDICT: ENDORSE | CONCERN | REJECT\n"
        "then REASON: 2-4 specific sentences (name any missing proof or hallucination).")
    try:
        raw = ds4_brain.chat([{"role": "user", "content": prompt}],
                             max_tokens=deep_tokens, temperature=0.2).strip()
    except Exception as e:
        return {"up": False, "verdict": "UNAVAILABLE", "reasoning": str(e)[:160]}
    m = re.search(r"VERDICT:\s*\**\s*(ENDORSE|CONCERN|REJECT)", raw, re.IGNORECASE)
    if m:
        verdict = m.group(1).upper()
    else:  # reasoning models bury the call in their thinking — infer conservatively
        low = raw.lower()
        verdict = ("REJECT" if "reject" in low else
                   "CONCERN" if "concern" in low else "ENDORSE")
    return {"up": True, "verdict": verdict, "reasoning": raw[:1400]}


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
