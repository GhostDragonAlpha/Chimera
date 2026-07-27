"""
why_gate — the system asks WHY, automatically, before a claim is allowed to finalize.

THE HUMAN (2026-07-16): "you need to get the system to guide the agent to be able to ask
these questions automatically, even if we just have to ask one question with one word:
WHY." And: "the why connects the node edges."

Both halves are built (3655259, 3e3e58e, 5a0bb8f, a241b94): the why IS an edge, and
`why.walk()` recurses claim -> Observation -> SimPlaytest until it reaches something that
needs no observer. But NOTHING RAN IT. `python -m core.why` was a tool an agent had to
remember, and an agent that remembers to interrogate its own work is not the agent this
gate exists for. That is exactly how the studio accumulated 150 finalized claims with
ZERO recorded whys: nothing asked, so nobody answered.

WHAT IT CHECKS, AND WHY THAT IS NOT A VERDICT. core/why.py's own docstring says this
must never become a gate that judges: "It renders no verdict and blocks nothing... A
question has no failure mode — a bad one costs an afternoon, a bad verdict costs the
record." That constraint is kept, exactly, by checking a STRUCTURAL FACT:

    NOT  "is your evidence good?"          <- a verdict. An opinion. Fabricable.
    BUT  "did the chain reach a terminal?"  <- a fact. A traversal over typed edges.

`proves` on each edge comes from the CITED NODE'S TYPE (a SimPlaytest is the engine
answering; an Observation is an agent writing), so nothing here has an opinion about
quality. The gate walks and reports where the chain stopped. A dead end is not a
judgement that the work is bad — it is the observation that nothing in the record needed
the world to be a certain way.

HOW IT DIFFERS FROM THE WITNESS GATE, which is not redundant with it:
    witness_gate  "does an evidence NODE exist?"        -> System_Economy PASSES
    why_gate      "does the CHAIN reach a terminal?"    -> System_Economy REFUSED
System_Economy has an Observation. That Observation cites
`session_continuous_workflow_20260708`, which does not exist. One checks for a node; the
other follows it. The second is strictly stronger, and it is the one that catches a
citation nothing can follow.

THE TWO LEGAL TERMINALS are the trinity's: PHYSICS settles a FACT (true in an empty
universe), THE HUMAN settles TASTE (the reference). AN LLM IS NEVER A TERMINAL — its
answer is always another claim, so the walk recurses past it or does not end.

    CHIMERA_WHY_GATE=warn   softens block -> warn
    CHIMERA_WHY_GATE=off    disables
"""
import os

GUIDANCE = """
   The claim has no why-chain that reaches a terminal. That is not a verdict on the
   work — it is the record saying nothing here needed the world to be a certain way.

   Look at where it stopped:
       python -m core.why --feature <name> --loop

   There are exactly two ways to end a why-chain honestly:
     PHYSICS    the engine ran it and something read the world back. Lint the beat
                first (a typo'd beat indicts the FEATURE), then run it:
                    python -m core.beat_lint --beats docs/beats/<x>.beats.json
                    python -m core.sleepwalker --beats docs/beats/<x>.beats.json --session <s>
                    python -m core.collapse_proxy --from-simtest <simtest_id> --valence accepted
     THE HUMAN  a person played it and said so. EARNED, never requested
                (core/trainables/attunement.py: HUMAN_TEST_BAR).

   A compile is not proof (H-14). A file existing is not proof — you wrote the file.
   An LLM's opinion is not proof; it is another claim, and the walk recurses past it.

   If the chain SHOULD reach evidence that exists, the link was probably never
   recorded (record_feature() cites no observation — that is the fifth dangling wire):
       python -m core.why --backfill --apply

   Honest exception: --why-waiver "<reason>". It is recorded and it is read.
"""


def enforced():
    """block (default) | warn | off — matches every other gate's contract."""
    return os.environ.get("CHIMERA_WHY_GATE", "block").strip().lower() == "block"


def disabled():
    return os.environ.get("CHIMERA_WHY_GATE", "block").strip().lower() == "off"


def check(feature, status=None, waiver="", graph=None):
    """(state, detail). state: 'terminal' | 'dead_end' | 'unasked' | 'waived' | 'n/a'.

    Renders NO verdict about quality. It walks typed edges and reports where the chain
    stopped — a fact, reproducible by anyone, with no LM anywhere in it.
    """
    if disabled():
        return "n/a", "CHIMERA_WHY_GATE=off"
    if status not in ("verified", "accepted", "observed", "observed_provisional"):
        return "n/a", f"status {status!r} is not a finalization"
    if not feature:
        return "n/a", "no feature named"

    from core.graphify_interface import load_dna_graph
    from core.why import walk

    g = graph if graph is not None else load_dna_graph()

    # A WAIVER THAT CLAIMS THE GATE WOULD PASS IS A TESTABLE LIE (2026-07-17, the
    # human's security reframe, caught live). `if waiver: return "waived"` accepted ANY
    # non-empty string — the truthiness hole, in the gate meant to be the strongest.
    # A real agent used it: postflighting Shelter_Habitat_Materials it passed
    #     --why-waiver "the why loop shows YES with PHYSICS terminal via witness run
    #                   simtest_f2856885f26a021f"
    # while the walk reached ZERO terminals. It waived the WHY gate by ASSERTING the
    # WHY gate would pass — the deepest form of the week's one bug: a credential
    # (the waiver) nobody authenticated, asserting the very thing the gate computes.
    #
    # A waiver is for when the check legitimately CANNOT apply ("nothing measures the
    # economy yet; back-burnered by the human"). It is NOT for asserting the check's
    # own result. So: if the waiver text makes a PASSING CLAIM — that the chain reaches
    # a terminal, shows YES, is proven/measured/witnessed — the gate RUNS THE WALK and
    # REFUSES the waiver when the walk disagrees. You may say "this cannot be
    # measured"; you may not say "the measurement you are about to take would pass",
    # because it can be taken.
    if waiver:
        _claims_pass = any(w in waiver.lower() for w in (
            "shows yes", "reaches physics", "physics terminal", "reaches the human",
            "terminal via", "chain reaches", "why loop shows", "already verified",
            "proven", "witnessed", "measured", "walk shows", "gate passes",
            "gate would pass", "reaches a terminal"))
        if _claims_pass:
            _claim_nodes = [n for n in g.get("nodes", [])
                            if n.get("type") == "FeatureUpdate"
                            and n.get("feature_name") == feature
                            and n.get("status") in ("verified", "accepted", "observed",
                                                    "observed_provisional")]
            _reaches = any(
                any(s.get("terminal") for s in walk(c["id"], g)) for c in _claim_nodes)
            if not _reaches:
                return "refused_waiver", (
                    "the waiver CLAIMS the why-chain passes (\"" + waiver[:80] + "…\"), "
                    "but the walk reaches NO terminal. A waiver is for when the check "
                    "cannot apply, never for asserting its result — that is checkable, "
                    "and it is false. Run the real evidence, or waive with an honest "
                    "reason the chain genuinely cannot reach PHYSICS/THE HUMAN.")
        return "waived", waiver
    claims = [n for n in g.get("nodes", [])
              if n.get("type") == "FeatureUpdate" and n.get("feature_name") == feature
              and n.get("status") in ("verified", "accepted", "observed",
                                      "observed_provisional")]
    if not claims:
        # Nothing recorded yet — postflight runs BEFORE the ledger write in some flows.
        # Refusing here would block a claim that does not exist. Not this gate's job.
        return "n/a", f"no finalized claim recorded for {feature!r} yet"

    best, deepest = None, []
    for c in sorted(claims, key=lambda n: n.get("timestamp", ""), reverse=True):
        chain = walk(c["id"], g)
        if not deepest:
            deepest = chain
        term = [s for s in chain if s.get("terminal")]
        if term:
            best = (c, chain, term[0])
            break

    if best:
        c, chain, term = best
        hops = " -> ".join(s["type"] for s in chain)
        derived = " (via a DERIVED link — inferred from a name match, not cited)" \
            if any(s.get("derived") for s in chain) else ""
        return "terminal", (f"the why-chain reaches {term['terminal']}: {hops}"
                            f" [{len(chain)} hop(s)]{derived}")

    if not deepest:
        return "unasked", ("no because-edge at all — NOBODY EVER ASKED why this is "
                           f"{status}. (The evidence may exist and simply never have been "
                           f"wired: try `python -m core.why --backfill`.)")

    stops = "; ".join(f"{s['type']} proves {s['proves']}" for s in deepest[:3])
    return "dead_end", (f"the why-chain runs {len(deepest)} hop(s) and never reaches "
                        f"PHYSICS or THE HUMAN — it stops at: {stops}")
