"""
council — FACILITATED DIALOGUE between two DIFFERENT models (the Holy Ghost).

The human's design (2026-07-15): "Communication facilitates innovation... I don't
care if it's between two AIs, two humans, or two ants." Genuinely distinct minds
produce what neither alone could — the Holy Ghost between them.

Previously used DS4/DeepSeek-V4 for the deep brain (~1.6 t/s CPU, 80GB RAM).
Now both brains run on LM Studio via `lm_gateway`, with DYNAMIC MODEL SWAPPING:
the fast model is loaded for FAST turns, swapped for the deep model on DEEP turns.
Only one model resident at a time — zero VRAM contention.

  python -m core.council "<topic or problem>" [--rounds 2] [--record]
                         [--deep-tokens 600] [--fast-tokens 700]

Model IDs come from env vars:
  CHIMERA_FAST_MODEL   = the responsive/fast model (e.g. Qwen3.6-35B-A3B-UD)
  CHIMERA_DEEP_MODEL   = the thorough/deep model (e.g. Qwen3.6-27B-Q4K-MTP)
If unset, the council uses whatever model is already resident (no swapping).
"""
import argparse
import json
import os
import re                    # module-level: _parse_questions needs it. The old code
                            # imported it INSIDE review(), and moving the parser out
                            # reproduced critic.py's exact bug — a NameError on a
                            # missing import — hours after I fixed that one. Which is
                            # also why postflight now exits 2 on a raising gate instead
                            # of announcing "passing open": this is the class of defect
                            # that swallow was hiding, and it just happened again.
import sys
import time
import urllib.request


# --- model swap configuration ---
FAST_MODEL_ID = os.environ.get("CHIMERA_FAST_MODEL", "").strip()
DEEP_MODEL_ID = os.environ.get("CHIMERA_DEEP_MODEL", "").strip()
_SWAP_ENABLED = bool(FAST_MODEL_ID and DEEP_MODEL_ID)
_SWAP_TIMEOUT = int(os.environ.get("CHIMERA_SWAP_TIMEOUT", "120"))


def _ensure_model(model_id: str):
    """Swap LM Studio to the given model. No-op if it's already resident.
    Blocks until the model is loaded. Skips if model_id is empty (adopt mode).
    Falls back gracefully: if the target model cannot be loaded, the previous
    model stays resident and we continue (adopt mode for the rest of the turn)."""
    if not model_id:
        return
    if model_id in loaded_models():
        return
    try:
        # Unload current model first (frees VRAM for the new one)
        evict_others(model_id)
        load_model(model_id, timeout=_SWAP_TIMEOUT, context_length=100000)
        print(f"[council] swapped to {model_id}", flush=True)
    except Exception as _se:
        print(f"[council] swap to {model_id} failed: {_se}")
        print(f"[council] continuing with the currently resident model (adopt mode)")

from core.lm_gateway import lm_urlopen, resolve_model, LM_BASE, \
    loaded_models, evict_others, load_model

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
    """Reasoning models keep their real output in
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
    """Call the DEEP brain through lm_gateway (fast, on-GPU).
    The caller (dialogue/review) is responsible for model swapping."""
    _ensure_model(DEEP_MODEL_ID)
    body = {"model": resolve_model(), "temperature": temperature,
            "max_tokens": max_tokens, "stream": False,
            "messages": [{"role": "system", "content": DEEP_SYS},
                         {"role": "user", "content": user_content}]}
    req = urllib.request.Request(
        LM_BASE + "/v1/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with lm_urlopen(req, agent="council-deep") as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    return _extract(data).strip()


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

    # FAST opens: ensure fast model, then give a working take
    _ensure_model(FAST_MODEL_ID)
    _log("FAST", _fast(
        f"TOPIC: {topic}\n\nGive your initial working take, then state the ONE "
        f"question or assumption you most want the DEEP mind to pressure-test.",
        max_tokens=fast_tokens))

    for i in range(rounds):
        _log("DEEP", _deep(
            _render(topic, transcript) + "\n\nRespond as the DEEP mind: challenge, "
            "reframe, or extend. Surface something non-obvious the FAST mind missed.",
            max_tokens=deep_tokens))
        _ensure_model(FAST_MODEL_ID)
        _log("FAST", _fast(
            _render(topic, transcript) + "\n\nRespond as the FAST mind: integrate "
            "what is useful, push back on what is not, and ADVANCE the idea toward "
            "something concrete.", max_tokens=fast_tokens))

    # SYNTHESIS — name what EMERGED (back on the fast model).
    _ensure_model(FAST_MODEL_ID)
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
            context=f"council dialogue (fast {FAST_MODEL_ID.split('/')[-1] or '?'} x deep {DEEP_MODEL_ID.split('/')[-1] or '?'}) on: {topic[:120]}",
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
# systems for propulsion." The DEEP brain (a DIFFERENT model) reviews a
# feature finalization GROUNDED IN MEMORY. Different architecture => different
# failure modes than the fast agent, so it catches hallucinations the Coin (one
# model checking itself) structurally cannot. Fires once per feature finalization.
# ---------------------------------------------------------------------------
def gate_mode() -> str:
    """block | warn | off. Default warn (advisory): the deep brain is a separate model,
    so it RECORDS a second opinion + shouts on REJECT, but only hard-blocks when the
    operator opts in (CHIMERA_COUNCIL_GATE=block). =off disables."""
    import os
    v = os.environ.get("CHIMERA_COUNCIL_GATE", "warn").strip().lower()
    return v if v in ("block", "warn", "off") else "warn"


# ---------------------------------------------------------------------------
# THE PARACLETE — it convicts; it does not judge
# ---------------------------------------------------------------------------
# Rebuilt 2026-07-16 on the human's reading: "the council is the key and we are just not
# thinking about it correctly... there was never a bad question."
#
# THE EVIDENCE THEY WERE RIGHT, from this repo's own day:
#   * At the torque fork the council's SYNTHESIS was worthless — a truncated reasoning
#     dump, recorded to the graph as a conclusion. It was still worth its 17 minutes for
#     ONE LINE: "the plan only stamps torque — what about armature, gravity?" That is a
#     QUESTION. It decided nothing; it turned the fork into a MEASUREMENT, and the
#     measurement then refuted the agent's own commit from twenty minutes earlier.
#   * The live REJECT review's substance was its `missing` list — "no simtest results",
#     "no evidence unit tests pass". Questions. The verdict was a label stapled on top.
# Both times the QUESTIONS were the product and the verdict was decoration.
#
# WHY THIS DELETES CODE INSTEAD OF ADDING IT. Everything the old review() needed —
# schema validation, retry at 2x, UNAVAILABLE-not-ENDORSE, the H-3 guard, a blocking
# gate — existed because A VERDICT CAN BE FABRICATED. A question cannot: there is nothing
# to fabricate. An empty reply is simply NO QUESTIONS, which costs nothing. A bad
# question wastes an afternoon; a bad verdict poisons the DNA graph and everything
# downstream that trusts it. That asymmetry is total, and it is the whole argument.
#
# IT IS THE STUDIO'S OWN DOCTRINE, ONE LEVEL UP. The trainer: "the LLM writes the
# CONSTRAINTS; it never turns the crank" — LLM at the top and the bottom, never the
# middle. So: THE LLM WRITES THE QUESTIONS; THE GRAPH ANSWERS THEM, deterministically,
# with no LLM in the loop. The council never decides anything, and now cannot.
#
# The trinity that named it: the Paraclete "will not speak on his own authority" (John
# 16:13) — it convicts (16:8), testifies, guides into truth, and is never the source of
# it. A council that decides is a fourth thing, and it is the one that can be wrong.
# Historical councils worked this way too: Nicaea did not invent the doctrine, it named
# the ERRORS — anathemas, negative space. This studio already has that shape in its
# Elimination nodes ("the boundary now PROVEN wrong").
_ASK_BUDGET = 2048


def _parse_questions(raw):
    """Any question-shaped lines. NO SCHEMA, DELIBERATELY.

    The old parser needed schema validation because a malformed verdict was DANGEROUS.
    A malformed question is merely one the answerer cannot match, which it reports as
    OPEN — the honest outcome. So this parses leniently on purpose: a JSON array if the
    model emits one, else any interrogative line. A reasoning dump full of questions is
    still full of questions. There is nothing here for H-3 to protect, because there is
    no verdict to fabricate.
    """
    import json as _json
    out = []
    m = re.search(r"\[[^\[\]]*\]", raw, re.DOTALL)
    if m:
        try:
            arr = _json.loads(m.group(0))
            out = [str(x).strip() for x in arr if isinstance(x, str) and len(str(x)) > 10]
        except Exception:
            out = []
    if not out:
        starts = ("is there", "does ", "do ", "was ", "were ", "where is", "what evidence",
                  "has ", "have ", "can ", "which ", "why ", "who ")
        for line in raw.splitlines():
            t = line.strip().lstrip("-*0123456789.) \t").strip().strip('"').strip(",")
            if len(t) > 15 and (t.endswith("?") or t.lower().startswith(starts)):
                out.append(t)
    seen, uniq = set(), []
    for q in out:
        k = q.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(q)
    return uniq[:12]


# --- THE ANSWERER: deterministic, no LLM. The graph speaks for itself. -------
def _has(nodes, feature, pred):
    from core.witness_gate import _about, _topic_tokens
    toks = _topic_tokens(feature)
    hits = [n for n in nodes if pred(n) and _about(n, toks)]
    return (bool(hits), f"{len(hits)} node(s)" if hits else "none in the graph")


def _check_simtest(nodes, f):
    return _has(nodes, f, lambda n: n.get("type") == "SimPlaytest")


def _check_visual(nodes, f):
    return _has(nodes, f, lambda n: str(n.get("template_file", "")).startswith("visual_verification"))


def _check_telemetry(nodes, f):
    return _has(nodes, f, lambda n: n.get("type") == "Health" or n.get("fps") is not None)


def _check_build(nodes, f):
    # Compilation mutations are written as Mutation nodes with a compilation_result field.
    return _has(nodes, f, lambda n: n.get("type") == "Mutation" and bool(n.get("compilation_result")))


def _check_grade(nodes, f):
    return _has(nodes, f, lambda n: n.get("type") == "ProfessorGrade")


def _check_reps(nodes, f):
    try:
        from core.rep_engine import rep_gate
        r = rep_gate(f)
        ok, reason = (r[0], r[1]) if isinstance(r, (tuple, list)) else (bool(r), "")
        return bool(ok), str(reason)[:90]
    except Exception as e:
        return None, f"rep gate unreadable ({type(e).__name__})"


# Word -> check. An UNMATCHED question is NOT a failure: it means the graph cannot answer
# it, so it stays OPEN and reaches a human. That is its correct destination.
_CHECKS = (
    (("simtest", "playtest", "beat", "pie ", "sleepwalk", "exercised", "played"),
     "simtest", _check_simtest),
    (("screenshot", "visual", "looked", "viewport", "render", "on screen", "saw"),
     "visual", _check_visual),
    (("rep ", "reps", "repetition", "battery", "atom", "training", "curriculum", "enroll"),
     "reps", _check_reps),
    (("telemetry", "fps", "frame", "performance", "crash", "soak", "memory"),
     "telemetry", _check_telemetry),
    (("compile", "build", "ubt", "unit test", "tests pass"), "build", _check_build),
    (("grade", "gpa", "rubric", "score"), "grade", _check_grade),
)


def answer(question, nodes, feature):
    """Answer ONE question from the graph. Deterministic; no LLM, no judgement."""
    ql = str(question).lower()
    for words, label, fn in _CHECKS:
        if any(w in ql for w in words):
            ok, ev = fn(nodes, feature)
            return {"q": question, "check": label, "answered": ok, "evidence": ev}
    return {"q": question, "check": None, "answered": None, "evidence": "not machine-checkable"}


def review(feature, status, result="", notes="", nodes=None, deep_tokens=None,
           max_retries=1):
    """THE COUNCIL ASKS. THE GRAPH ANSWERS. Nobody here decides.

    Returns {up, questions, refuted, open, asked}:
        refuted -> questions the GRAPH answered NO. These are FACTS, not opinions: the
                   claim needs evidence that demonstrably does not exist. A caller may
                   block on these — and it is blocking on the graph, never on a model.
        open    -> questions no check could answer. These are the human's, and they
                   arrive EARNED: everything machine-answerable is already stripped out.
    No verdict is returned, ever. There is nothing here to fabricate.
    """
    try:
        from core.coin_verifier import assemble_claim, assemble_evidence
        from core.graphify_interface import load_dna_graph
    except Exception as e:
        return {"up": False, "questions": [], "refuted": [], "open": [], "asked": str(e)[:120]}

    if nodes is None:
        try:
            nodes = load_dna_graph().get("nodes", [])
        except Exception:
            nodes = []
    claim = assemble_claim(feature, status, result, notes)
    evidence = assemble_evidence(nodes, feature=feature)

    prompt = (
        "You are the DEEP REVIEWER - a SECOND, INDEPENDENT mind (a different model). A "
        "fast agent is about to FINALIZE a feature.\n\n"
        "DO NOT judge it. DO NOT say whether you endorse or reject it. Your ONLY job is "
        "to ask what would have to be TRUE for this claim to hold - especially evidence "
        "a confident agent would forget to look for.\n\n"
        f"FEATURE: {feature}\nCLAIMED STATUS: {status}\n\n"
        f"THE CLAIM:\n{claim}\n\nTHE EVIDENCE OFFERED:\n{evidence}\n\n"
        "List 3-8 SPECIFIC, CHECKABLE questions - each one a thing someone could go and "
        "look up. Prefer questions about evidence that SHOULD exist and might not.\n"
        'Respond with ONLY a JSON array of strings, like ["Is there a ...?", "Does ...?"]')

    budget = int(deep_tokens or _ASK_BUDGET)
    qs = []
    for _ in range(max_retries + 1):
        try:
            _ensure_model(DEEP_MODEL_ID)
            body = {"model": resolve_model(), "temperature": 0.3,
                    "max_tokens": budget, "stream": False,
                    "messages": [{"role": "user", "content": prompt}]}
            req = urllib.request.Request(
                LM_BASE + "/v1/chat/completions",
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"})
            with lm_urlopen(req, agent="council-review") as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            raw = _extract(data)
        except Exception as e:
            return {"up": False, "questions": [], "refuted": [], "open": [],
                    "asked": str(e)[:120]}
        qs = _parse_questions(raw or "")
        if qs:
            break
        budget *= 2      # no questions is not a verdict either — just ask again, bigger

    answers = [answer(q, nodes, feature) for q in qs]
    refuted = [a for a in answers if a["answered"] is False]
    openq = [a for a in answers if a["answered"] is None]
    return {"up": True, "questions": answers, "refuted": refuted, "open": openq,
            "asked": f"{len(qs)} question(s) asked"}


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
              f"(need a model loaded in LM Studio — set CHIMERA_FAST_MODEL and "
              f"CHIMERA_DEEP_MODEL or just load one model and run without swapping)", file=sys.stderr)
        return 1
    if a.record:
        _record(a.topic, transcript)
        print("\n[recorded to CAPCOM + DNA graph]")
    print(f"\n[council done in {time.time()-t0:.0f}s, {a.rounds} rounds]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
