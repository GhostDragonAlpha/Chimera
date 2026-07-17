"""
why — the system asks the agent one word, mechanically.

THE HUMAN (2026-07-16): "you need to get the system to guide the agent to be able to ask
these questions automatically, even if we just have to ask one question with one word:
WHY."

They are right, and the proof is the audit that prompted it. Every question that caught
sub-04's hollow feature was the same word:

    "0 red atoms, promoted to tier 1"   -> WHY? -> the atom checks that the file it just
                                                   wrote exists. It is circular.
    "generator loads successfully"      -> WHY? -> loading a module says nothing about
                                                   the C++ it emits.
    "int32 MassCount"                   -> WHY is that a Mass crowd entity? -> it is not.
                                                   Zero Mass framework symbols. (H-21:
                                                   "a verb needs behavior, not metadata"
                                                   — ATool_Shovel had DigRadius and no
                                                   Dig(); ADotCharacter has MassCount and
                                                   no Mass.)

The agent never asked. NOTHING ASKED IT. Not because the answer was hidden — the atom's
probe type is DATA, sitting in the battery file — but because the system reported
"0 red atoms" and stopped, and a green number reads as a proof.

WHY THIS IS NOT ANOTHER GATE, AND MUST NOT BE. It renders no verdict and blocks nothing.
It states what the evidence PROBES and asks what the evidence CANNOT answer. That is the
Paraclete (core/council.py) made deterministic: it convicts, it does not judge, and there
is no LLM in it to fabricate anything. A question has no failure mode — a bad one costs
an afternoon, a bad verdict costs the record.

THE CLASSIFICATION IS THE WHOLE TRICK. Six of the ten probe types prove only that a FILE
OR STRING EXISTS. An agent that writes a file and then runs a probe asking whether the
file exists has measured its own hand. That is not a bug in the probe — a
`tree_contains` atom is a perfectly good regression guard — it is a bug in calling it
PROOF OF BEHAVIOUR.

    python -m core.why --feature ADotCharacter
    python -m core.why --feature X --claim "it is verified"
"""
import argparse
import glob
import io
import json
import os
import re                       # _MINTED. The FOURTH missing-stdlib-import I have
                                # written today (critic.py: os, days; council.py: re,
                                # shipped; regression.py: os, caught). This one could
                                # not ship: `_MINTED = re.compile(...)` runs at MODULE
                                # level, so the import fails LOUD and IMMEDIATELY. The
                                # other three hid in branches nobody took. That is an
                                # argument for module-level constants over lazy locals.
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# What each probe type ACTUALLY establishes. Not what it is named; what it PROVES.
# EXISTENCE  — a file or a string is on disk. An agent that just wrote the file has
#              proved nothing but its own typing.
# RECORDED   — something was written to the graph. Also a thing an agent can just do.
# DISPATCH   — a beat could run (not that it did, and not that it passed).
# MEASURED   — the world was observed. THIS is the only kind that can prove behaviour.
_PROVES = {
    "glob_nonempty":   ("EXISTENCE", "a file exists"),
    "file_contains":   ("EXISTENCE", "a string exists in a file"),
    "tree_contains":   ("EXISTENCE", "a string exists somewhere in the tree"),
    "tree_lacks":      ("EXISTENCE", "a string does NOT exist (a real negative — but still text)"),
    "json_valid":      ("EXISTENCE", "a file parses as JSON"),
    "file_md5_not":    ("EXISTENCE", "a file differs from a known hash"),
    "beats_registered": ("DISPATCH", "a beat COULD run — not that it did, nor that it passed"),
    "graph_status":    ("RECORDED", "a node carries a status — which an agent wrote"),
    "envelope_axis":   ("MEASURED", "a measured value sits inside a wall"),
    "feel_metric":     ("MEASURED", "a metric was measured from the running game"),
}

_QUESTIONS = {
    "EXISTENCE": "WHY does a file/string existing prove {feature} WORKS? "
                 "You wrote that file. (H-14: a compile is not proof. H-21: a verb needs "
                 "behavior, not metadata.)",
    "RECORDED":  "WHY does a status you recorded prove {feature} works? "
                 "Recording is not measuring.",
    "DISPATCH":  "WHY does a beat being runnable prove {feature} works? "
                 "It has not run here.",
}


def _battery(feature):
    p = os.path.join(ROOT, "docs", "rep_batteries", f"{feature}.json")
    if not os.path.exists(p):
        return None
    d = json.loads(io.open(p, encoding="utf-8").read())
    return d if isinstance(d, list) else (d.get("atoms") or [])


def audit(feature):
    """What does this feature's evidence actually PROBE? Deterministic; no LLM."""
    atoms = _battery(feature)
    if atoms is None:
        return None
    rows, kinds = [], {}
    for a in atoms:
        t = str((a.get("probe") or {}).get("type", "?"))
        kind, means = _PROVES.get(t, ("UNKNOWN", "an unrecognised probe"))
        kinds[kind] = kinds.get(kind, 0) + 1
        rows.append({"id": str(a.get("id"))[:20], "type": t, "kind": kind, "means": means,
                     "desc": str(a.get("desc") or "")[:60]})
    return {"feature": feature, "atoms": rows, "kinds": kinds,
            "measured": kinds.get("MEASURED", 0), "total": len(rows)}


def run(feature, claim=""):
    a = audit(feature)
    if a is None:
        print(f"no rep battery for '{feature}' — nothing to ask about "
              f"(docs/rep_batteries/{feature}.json)")
        return 0
    print("=" * 76)
    print(f"WHY  —  {feature}" + (f"   claim: \"{claim}\"" if claim else ""))
    print("  What your evidence PROBES. Not a verdict; a question.")
    print("=" * 76)
    for r in a["atoms"]:
        print(f"  {r['id']:20} {r['type']:16} {r['kind']:9} -> {r['means']}")
    print()
    tally = ", ".join(f"{v} {k}" for k, v in sorted(a["kinds"].items()))
    print(f"  {a['total']} atom(s): {tally}")
    print(f"  probes that MEASURE the running game: {a['measured']}")
    print()
    if a["measured"] == 0:
        asked = set()
        for kind in a["kinds"]:
            q = _QUESTIONS.get(kind)
            if q and kind not in asked:
                asked.add(kind)
                print(f"  ?  {q.format(feature=feature)}")
        print()
        print("  NOTHING HERE OBSERVED THE GAME. Every green atom above is compatible with")
        print("  a feature that does not work — including one that is only its own name.")
        print("  If you cannot answer the question, the honest evidence is a WITNESS RUN:")
        print(f"     python -m core.beat_lint --beats docs/beats/<x>.beats.json   (lint FIRST)")
        print(f"     python -m core.witness_runner --beats docs/beats/<x>.beats.json "
              f"--session obs_{feature[:20]}")
    else:
        print(f"  {a['measured']} probe(s) measured the running game. Ask of each: does it")
        print(f"  measure what {feature} is FOR, or only that something moved?")
    print("=" * 76)
    return 0


# ---------------------------------------------------------------------------
# THE WHY LOOP — and the invention: what YES is
# ---------------------------------------------------------------------------
# The human (2026-07-16): "if we just keep asking why, it's the universal
# build-it-autonomously type question... and YES is not a thing yet, we have to invent
# it."
#
# THEY ARE RIGHT THAT IT DOES NOT EXIST. Look at what this studio is made of: gates
# REFUSE, the Paraclete ASKS, `why` says "this proves nothing", Elimination nodes record
# PROVEN NEGATIVES, pinned() reports where you are TRAPPED, and the councils it was named
# after produced ANATHEMAS — negative space. Every mechanism here can only say NO. You can
# ask why forever and never arrive.
#
# SO WHAT STOPS THE LOOP? A why-chain terminates when the answer NEEDS NO OBSERVER.
#
#   "attunement has skill"  -> skill_gap 83.7  -> a listener beats a flailer, worst of N
#                           -> E = mean(field^2), sin(x)+sin(x)=2sin(x)
#                           -> arithmetic. NOTHING LEFT TO ASK.          => YES
#
#   "ADotCharacter is built" -> 2 atoms green  -> they probe file-exists
#                            -> WHY does a file existing prove behaviour?
#                            -> no answer exists.                        => DEAD END
#
# THERE ARE EXACTLY TWO LEGAL TERMINALS, and they are the trinity:
#   PHYSICS  settles a FACT  — no observer needed. `punishes_naive = 4.00x` is true in an
#            empty universe.
#   THE HUMAN settles TASTE  — the reference. "Is it fun?" bottoms out in you and nowhere
#            else (core/trainables/attunement.py: HUMAN_TEST_BAR).
#
# AN LLM IS NEVER A TERMINAL. An LLM's answer is ALWAYS ANOTHER CLAIM — recurse on it.
# That is the whole reason council.review returns questions instead of ENDORSE, and the
# reason the deleted AAA grader was fraud: it terminated the chain at a model's adjective.
#
# YES = the chain reached a terminal.   NO = it dead-ended.   Everything else = keep asking.
_TERMINAL_PROBES = {"feel_metric", "envelope_axis"}      # measured from the running game


#: What each `proves` class on a because-edge can settle. Mirrors _PROVES above — the
#: edge stores the CLASS, so a walk never has to re-derive it from the probe type.
_EDGE_TERMINAL = {"MEASURED": "PHYSICS", "HUMAN": "THE HUMAN"}

# ---------------------------------------------------------------------------
# PROMOTION — the whys the studio already wrote, in the wrong place
# ---------------------------------------------------------------------------
# Measured 2026-07-16: 335 node-to-node references are stored as FIELDS INSIDE
# NODES — .derived_from (67), .evidence_ids (133), .links (133), .evidence (2) —
# and zero as because-edges. The studio HAS been recording why. It wrote each one
# as a string in a node, where nothing can traverse it.
#
# That costs two things. The reverse question is unanswerable: "this simtest was
# bogus — WHAT DID IT CONVICT?" needs a scan of all 2,546 nodes, so when a typo'd
# beat indicts a working feature (the exact scenario core/beat_lint.py exists for)
# nothing can find the wreckage. And each reader re-implements the walk, which is
# why coin_verifier, collapse_proxy, witness_gate and why.py each hand-roll a
# `derived_from` traversal.
#
# AND THE FIELD CANNOT BE CHECKED. 50 of those references NAME NODES THAT DO NOT
# EXIST — 14 of them `derived_from` on Observations with verdict=accepted, over
# System_Economy, System_SaveLoad, System_Factions, System_Missions,
# Player_Character_Animation, Demo_RegolithYard_L1, Verb_PickUp. Their targets are
# `pie_dropactor_20260708` and `session_continuous_workflow_202607…`: zero exact
# matches, zero fuzzy, zero sessions. Every real one is `simtest_<hex>` minted by a
# record helper — these do not even match the naming scheme. They were TYPED.
#
# Nothing caught it because every consumer tests TRUTHINESS, not resolution
# (coin_verifier.py:124: `and n.get("derived_from")`). `derived_from="x"` passes.
# So does "because I said so". THAT is the difference between a field and an edge:
# a graph knows its own node ids and can refuse an edge to nowhere; a string can
# say anything, and a lie costs exactly as many keystrokes as the truth.
#
# So promote them. `proves` comes from the TARGET'S TYPE — what the cited thing IS
# decides what it can settle, never the field's name and never the citer's opinion.
# A dangling field gets NO EDGE, and that absence is the report: the claims that
# cannot be promoted are exactly the claims resting on nothing.
# ---------------------------------------------------------------------------

#: Node type -> what CITING it can establish. Conservative on purpose: when a type
#: could be argued either way it gets the weaker class, because the whole value of
#: this classification is that it is not flattering.
_CITED_PROVES = {
    "SimPlaytest":         "MEASURED",   # the engine ran; beats reached or not
    "PlaytestObservation": "HUMAN",      # a person played it — the taste terminal
    "Elimination":         "MEASURED",   # a proven negative: a boundary that held
    "pathway_attempt":     "MEASURED",   # an MCP call; the editor answered or did not
    "Observation":         "RECORDED",   # a WRITTEN verdict. Its own derived_from
                                         # continues the chain — that is the point of
                                         # a graph: this link need not be the last.
    "ProfessorGrade":      "RECORDED",   # an agent graded it. Recording is not measuring.
    "SurpriseMoment":      "RECORDED",   # a written note
    "VisualVerification":  "RECORDED",   # AN LM LOOKED AT A SCREENSHOT. The screenshot
                                         # is a measurement; the LM's read of it is a
                                         # CLAIM. "An LLM is never a terminal" is the
                                         # doctrine of this file and it does not get an
                                         # exception for being the gate we like. The
                                         # chain continues past it or it does not end.
}

#: Fields that are edges in disguise -> the question each was silently answering.
_WHY_FIELDS = {
    "derived_from": "WHY is this observation held?",
    "evidence_ids": "WHY is this heuristic held?",
    "evidence":     "WHY was this decomposed?",
    # .links is not here: measured identical to .evidence_ids on every Heuristic that
    # has both (133/133). Promoting both would double every edge and inflate the very
    # count this exists to make honest.
}

#: The hex tail of a minted id: `hashlib.sha256(...).hexdigest()[:16]`.
#: NOT `[0-9a-f]{8,}` — my first cut was, and it is wrong because A DATE IS VALID HEX.
#: `pie_dropactor_20260708` matched (20260708 is eight hex chars) and got filed as a
#: minted id that was LOST, when it is a hand-typed string that never existed. The
#: minimum is 12: every id in this graph is a sha256 slice, and no date reaches 12.
_MINTED_TAIL = re.compile(r"^[0-9a-f]{12,}$")


def _minted_prefixes(nodes):
    """The id prefixes this graph ACTUALLY mints — derived, never hand-listed.

    Same lesson as core/beat_lint.py's vocabulary: a hand-copied list is a second
    source of truth that drifts. Here it also cannot be written down honestly — the
    prefixes are whatever the record_* helpers happen to emit, and they have changed.
    So read them off the real ids.
    """
    return {i.rsplit("_", 1)[0] for i in (str(n.get("id", "")) for n in nodes)
            if "_" in i and _MINTED_TAIL.match(i.rsplit("_", 1)[-1])}


def _is_minted(target, prefixes):
    """A minted id = a prefix this graph mints + a sha256 tail. BOTH halves.

    `simtest_audio_visual_sync_verify` is why both are needed: a REAL prefix with a
    TYPED suffix. Checking the prefix alone calls it lost evidence; checking the tail
    alone calls `pie_dropactor_20260708` minted. It is the same shape as every false
    positive my instruments produced today — checking something adjacent to the truth
    and calling it the truth.
    """
    if "_" not in target:
        return False
    head, tail = target.rsplit("_", 1)
    return head in prefixes and bool(_MINTED_TAIL.match(tail))


def _archived_ids():
    """Every node id the archives hold. archive-never-delete means the ARCHIVE IS
    PART OF THE TRUTH — a reference the compactor archived out of the live graph is
    STALE, NOT FALSE, and reporting it as "does not exist" would be a lie about a lie.

    I nearly shipped exactly that: the first cut of this report bucketed 12 archived
    mutation ids together with hand-typed session names under one heading. That is the
    same sloppy accusation I made against a subagent this morning — checking something
    adjacent to the truth and calling it the truth.
    """
    ids = set()
    for f in glob.glob(os.path.join(ROOT, "docs", "**", "*archive*.json"), recursive=True):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="ignore").read())
        except Exception:
            continue
        for n in (d.get("nodes", []) if isinstance(d, dict) else d):
            if isinstance(n, dict) and n.get("id"):
                ids.add(n["id"])
    return ids


def _classify_dangler(target, archived, prefixes):
    """ARCHIVED (stale) | LOST (minted, gone) | NEVER MINTED (typed). Three stories,
    and collapsing them would be a lie about a lie."""
    if target in archived:
        return "ARCHIVED"
    return "LOST" if _is_minted(target, prefixes) else "NEVER MINTED"


def backfill(apply=False):
    """Wire each finalized CLAIM to the Observation that already carries its evidence.

    THE FIFTH DANGLING WIRE, and the widest (measured 2026-07-16):

        CLAIM  Sky_Earth_Model  status=verified   because_of -> NOTHING
        OBS    Sky_Earth_Model  verdict=accepted  because_of -> MEASURED simtest_03a16…

    The evidence is REAL and it REACHES PHYSICS. Nothing connects the claim to it.
    The only thing relating those two nodes is a matching feature_name STRING — which
    is why coin_verifier, collapse_proxy, witness_gate and _mutate_feature_complete
    each hand-roll that match, slightly differently, and why 150 finalized claims read
    as assertions while their evidence sits one string-compare away.

    MARKED `derived: true`, AND THAT MATTERS. record_feature() never said "this rests
    on that observation" — the caller never passed one. Inferring the link from a name
    match is exactly the reasoning I have spent today criticising, so it must be
    labelled as inference. The underlying evidence is identical either way; what is
    weaker is the INTENT. A recorded edge means someone cited it. A derived edge means
    I matched a string and guessed they meant to.

    proves=RECORDED, never MEASURED: an Observation is a WRITTEN verdict. The claim
    does not reach physics by citing it — the Observation's own edge does that, on the
    next hop. The chain walks; this link is not allowed to pretend it is the end of it.
    """
    from core.graphify_interface import load_dna_graph, save_dna_graph, because_edge
    g = load_dna_graph()
    nodes, edges = g.get("nodes", []), g.get("edges", [])
    have = {e.get("src") for e in edges if e.get("rel") == "because"}
    by_id = {n.get("id"): n for n in nodes}

    # An Observation is only usable as a why if its OWN why resolves. An Observation
    # citing `session_continuous_workflow_202607…` (typed, never minted) is exactly the
    # thing that must not be laundered into a claim's evidence by this backfill.
    obs_by_feature = {}
    for n in nodes:
        if n.get("type") != "Observation":
            continue
        src = n.get("derived_from")
        if not src or src not in by_id:
            continue
        obs_by_feature.setdefault(n.get("feature_name"), []).append(n)

    new, unbacked = [], []
    for n in nodes:
        if n.get("type") != "FeatureUpdate":
            continue
        if n.get("status") not in ("verified", "accepted", "observed", "observed_provisional"):
            continue
        if n["id"] in have:
            continue
        cands = obs_by_feature.get(n.get("feature_name")) or []
        if not cands:
            unbacked.append(n)
            continue
        best = max(cands, key=lambda o: o.get("timestamp", ""))   # freshest (H-19)
        e = because_edge(n["id"], best["id"],
                         f"WHY is {n.get('feature_name')} '{n.get('status')}'?", "RECORDED")
        e["derived"] = True
        e["derived_how"] = "feature_name match — record_feature() never cited evidence"
        new.append(e)

    print("=" * 76)
    print("BACKFILL — wire each CLAIM to the evidence that already exists beneath it")
    print("=" * 76)
    print(f"  {len(new):>4}  claim(s) can be wired to an Observation whose own why RESOLVES")
    print(f"        (proves=RECORDED — the claim does not reach physics by citing a")
    print(f"         written verdict; the Observation's next hop does. The chain walks.)")
    print(f"  {len(unbacked):>4}  claim(s) have NO observation with a resolvable why — these stay")
    print(f"        ASSERTIONS, and that is the honest answer, not a gap in this tool.")
    for n in unbacked[:8]:
        print(f"          {str(n.get('feature_name'))[:44]:<44} [{n.get('status')}]")
    if len(unbacked) > 8:
        print(f"          ... and {len(unbacked) - 8} more")
    print()
    print("  Every edge is marked derived=true: record_feature() never cited an")
    print("  observation, so this link is INFERRED from a name match — the same")
    print("  reasoning this file spends its length criticising. Labelled, not hidden.")
    print()
    if apply and new:
        save_dna_graph({"nodes": nodes, "edges": edges + new})
        print(f"  APPLIED: {len(new)} derived because-edge(s) written.")
    elif new:
        print("  DRY RUN. Re-run with --apply to write them.")
    else:
        print("  Nothing to backfill.")
    print("=" * 76)
    return 0


def walk(node_id, graph=None, _seen=None, depth=0):
    """Ask WHY, follow the edge, ASK AGAIN. Recurse until a terminal or a dead end.

    THIS IS THE LOOP. The human's whole theory in one function: "if we just keep
    asking why it's the universal build-it-autonomously type question." One word,
    applied until the answer needs no observer.

    It only works because `proves` sits on the EDGE. A claim citing an Observation
    proves RECORDED — an agent wrote that verdict, so KEEP ASKING — and the
    Observation's OWN edge is what reaches MEASURED. Two hops:

        claim --because(RECORDED)--> observation --because(MEASURED)--> simtest
                                                                        => PHYSICS

    Neither hop alone is YES. The chain is. That is what a graph is FOR, and it is
    what a field could never do: `derived_from` bottoms out in one string lookup, so
    every consumer that read it saw one hop and stopped. The studio has been asking
    why exactly once, for months, and calling the answer proof.

    Cycle-safe (_seen): a why-chain that loops is a claim resting on itself, which is
    the circularity this file was written to catch — "0 red atoms" resting on a probe
    that checks the file the agent just wrote.

    Returns [{depth, question, proves, node, type, terminal}] — the chain, in order.
    """
    from core.graphify_interface import load_dna_graph, because_of
    graph = graph if graph is not None else load_dna_graph()
    _seen = _seen if _seen is not None else set()
    if node_id in _seen or depth > 12:      # 12: no honest chain is deeper; a runaway
        return []                           # is a cycle the _seen guard already caught
    _seen.add(node_id)

    by_id = {n.get("id"): n for n in graph.get("nodes", [])}
    out = []
    for e in because_of(node_id, graph):
        dst = by_id.get(e["dst"], {})
        proves = e.get("proves", "?")
        out.append({
            "depth": depth,
            "question": e.get("question", "why?"),
            "proves": proves,
            "node": e["dst"],
            "type": dst.get("type", "?"),
            "terminal": _EDGE_TERMINAL.get(proves),
            "derived": bool(e.get("derived")),
        })
        if proves not in _EDGE_TERMINAL:    # not a terminal -> KEEP ASKING
            out.extend(walk(e["dst"], graph, _seen, depth + 1))
    return out


def promote(apply=False):
    """Turn why-shaped FIELDS into because-edges. Reports what will not promote.

    The fields were always edges; they were written into nodes because no edge
    existed to write. This does not invent a single why — every one already sits in
    the graph as data. It moves them where they can be walked, counted, and
    REVERSED, and it refuses the ones that point at nothing.

    Idempotent. Read-only unless apply=True.
    """
    from core.graphify_interface import load_dna_graph, save_dna_graph, because_edge
    g = load_dna_graph()
    nodes, edges = g.get("nodes", []), g.get("edges", [])
    by_id = {n.get("id"): n for n in nodes}
    have = {(e.get("src"), e.get("dst")) for e in edges if e.get("rel") == "because"}
    archived = _archived_ids()
    prefixes = _minted_prefixes(nodes)

    new, dangling, unclassified = [], {"ARCHIVED": [], "LOST": [], "NEVER MINTED": []}, []
    for n in nodes:
        for field, question in _WHY_FIELDS.items():
            v = n.get(field)
            for tgt in (v if isinstance(v, list) else [v]):
                if not isinstance(tgt, str) or not tgt:
                    continue
                if tgt not in by_id:
                    dangling[_classify_dangler(tgt, archived, prefixes)].append((n, field, tgt))
                    continue
                ttype = by_id[tgt].get("type", "?")
                proves = _CITED_PROVES.get(ttype)
                if proves is None:
                    unclassified.append((n, field, tgt, ttype))
                    continue
                if (n["id"], tgt) in have:
                    continue
                have.add((n["id"], tgt))
                new.append(because_edge(n["id"], tgt, question, proves))

    print("=" * 76)
    print("PROMOTE — the whys the studio already wrote, moved where they can be walked")
    print("=" * 76)
    kinds = {}
    for e in new:
        kinds[e["proves"]] = kinds.get(e["proves"], 0) + 1
    for k in ("HUMAN", "MEASURED", "RECORDED", "DISPATCH", "EXISTENCE"):
        if kinds.get(k):
            term = _EDGE_TERMINAL.get(k)
            print(f"  {kinds[k]:>4}  proves {k:<10} "
                  + (f"-> terminates at {term}" if term else "-> NOT a terminal; keep asking"))
    print(f"  {len(new):>4}  edge(s) to write")

    _GLOSS = {
        "ARCHIVED": ("the compactor moved these out of the live graph. archive-never-delete "
                     "means\n     the evidence EXISTS — the reference is STALE, NOT FALSE. No "
                     "edge yet: an edge\n     must point at a node this graph holds."),
        "LOST": ("minted ids (<type>_<hex>) in neither the graph nor any archive. The "
                 "evidence\n     is gone. The claim may once have rested on something; "
                 "nothing can tell now."),
        "NEVER MINTED": ("these do not match ANY minting scheme — every id in this graph is\n"
                         "     sha256()[:16]. These were TYPED. This is the only class that "
                         "is suspicious,\n     and it is the one an edge makes impossible: a "
                         "graph knows its own ids."),
    }
    for kind in ("ARCHIVED", "LOST", "NEVER MINTED"):
        items = dangling[kind]
        if not items:
            continue
        print()
        print(f"  {kind}: {len(items)} reference(s) — no edge.")
        print(f"     {_GLOSS[kind]}")
        for n, field, tgt in items[:8]:
            who = str(n.get("feature_name", n.get("type", "?")))[:30]
            print(f"       {who:<30} .{field:<13} -> {tgt[:32]:<32} "
                  f"[{n.get('verdict', n.get('status', '?'))}]")
        if len(items) > 8:
            print(f"       ... and {len(items) - 8} more")
    if unclassified:
        seen = sorted({t for _, _, _, t in unclassified})
        print(f"\n  {len(unclassified)} cite an unclassified node type ({', '.join(seen)}) — "
              f"no edge until _CITED_PROVES says what citing one can settle.")

    print()
    if apply and new:
        save_dna_graph({"nodes": nodes, "edges": edges + new})
        print(f"  APPLIED: {len(new)} because-edge(s) written.")
    elif new:
        print("  DRY RUN. Re-run with --apply to write them.")
    else:
        print("  Nothing to promote — every resolvable why is already an edge.")
    print("=" * 76)
    return 0


def recorded_chain(feature, graph=None):
    """Walk the REAL because-edges out of this feature's claims. A TRAVERSAL.

    THE HUMAN (2026-07-16): "the why connects the node edges." This is that, and
    everything below it in this file is the bootstrap that exists because these
    edges mostly do not yet.

    The difference is not style. chain() RE-DERIVES a why from the file tree on every
    call, by rules I wrote — so its ceiling is my imagination, it cannot see a why
    nobody hard-coded, and it forgets. An edge is the answer KEPT: asked once, true
    for whoever reads next, and walkable by a machine that knows nothing about rep
    atoms or beats. The studio has been paying the re-derivation cost forever —
    _mutate_feature_complete scanned 2,546 nodes to rebuild one of these and then
    printed a warning and dropped it.
    """
    from core.graphify_interface import load_dna_graph, because_of
    graph = graph if graph is not None else load_dna_graph()
    nodes = graph.get("nodes", [])
    by_id = {n.get("id"): n for n in nodes}

    claims = [n for n in nodes
              if n.get("type") == "FeatureUpdate" and n.get("feature_name") == feature]
    out = []
    for c in claims:
        for e in because_of(c["id"], graph):
            dst = by_id.get(e["dst"], {})
            proves = e.get("proves", "?")
            out.append({
                "chain": "recorded why", "step": e.get("question", "why?"),
                "why": f"{dst.get('type', 'node')} {e['dst'][:16]} ({proves})",
                "terminal": _EDGE_TERMINAL.get(proves),
                "stop": ("the answer was RECORDED, not re-derived — this is the graph's "
                         "own why" if proves in _EDGE_TERMINAL else
                         f"the recorded reason only proves {proves} — keep asking"),
            })
    return out


def chain(feature):
    """Walk every evidence chain for `feature` and report WHERE EACH STOPS.

    Deterministic. No LLM — an LLM here would be a non-terminal pretending to be one.

    Reads RECORDED because-edges first (the graph's own answer), then falls back to
    re-deriving from the file tree. The fallback is a BOOTSTRAP: 81 of 82
    verified/accepted claims had no because-edge the day this was written, so with
    only the traversal there would be nothing to walk. As the edges accumulate the
    derivation matters less, and the day it matters not at all is the day the graph
    can answer "why?" about itself without consulting me.
    """
    from core.graphify_interface import load_dna_graph
    graph = load_dna_graph()
    links = list(recorded_chain(feature, graph))
    nodes = graph.get("nodes", [])

    # chain 1: rep atoms -> probe types
    a = audit(feature)
    if a:
        term = [r for r in a["atoms"] if r["type"] in _TERMINAL_PROBES]
        links.append({
            "chain": "rep atoms", "step": f"{a['total']} atom(s) green",
            "why": ", ".join(sorted({r["type"] for r in a["atoms"]})),
            "terminal": "PHYSICS" if term else None,
            "stop": (f"{len(term)} probe(s) measured the running game" if term else
                     "every probe reads the file tree — it measures YOUR HAND, not the world"),
        })

    # chain 2: a SimPlaytest that REACHED its beats -> the engine observed it
    from core.witness_gate import _about, _topic_tokens
    toks = _topic_tokens(feature)
    sims = [n for n in nodes if n.get("type") == "SimPlaytest" and _about(n, toks)]
    reached = [s for s in sims
               if any(o.get("outcome") == "reached" and feature in (o.get("features") or [])
                      for o in (s.get("outcomes") or []))]
    if sims:
        links.append({
            "chain": "witness run", "step": f"{len(sims)} SimPlaytest(s)",
            "why": f"{len(reached)} reached a beat naming {feature}",
            "terminal": "PHYSICS" if reached else None,
            "stop": ("the engine ran it and the beat was reached — the world answered"
                     if reached else "no beat naming this feature was ever reached"),
        })

    # chain 3: a HUMAN playtest -> the taste terminal
    plays = [n for n in nodes if n.get("type") == "PlaytestObservation" and _about(n, toks)]
    if plays:
        links.append({"chain": "human playtest", "step": f"{len(plays)} observation(s)",
                      "why": "a person played it", "terminal": "THE HUMAN",
                      "stop": "taste bottoms out here and nowhere else"})
    return links


def _deep_questions(feature, claim, status="verified"):
    """THE BRAIN ASKS THE WHYS I DID NOT HARD-CODE.

    chain() walks three chains — rep atoms, witness runs, human playtests — and those are
    the only questions I thought of. MY IMAGINATION IS THE CEILING. The deep brain's whole
    value at the torque fork was asking "what about armature?", a question nobody had
    hard-coded, and physics then answered it in four minutes and refuted my own commit.

    So the brain belongs IN the loop, and in exactly one seat: it ASKS. Its answers are
    never terminals — an LLM's answer is always another claim, and terminating a chain at
    a model's opinion is precisely what the deleted AAA grader did. council.review()
    already returns questions and lets the GRAPH answer them; this is that, pointed at the
    why-loop instead of at postflight.
    """
    try:
        from core import council
        r = council.review(feature, status, result=claim or f"{feature} is done")
        if not r.get("up"):
            return None, "deep brain down — the loop can only ask what I hard-coded"
        return r, None
    except Exception as e:
        return None, f"deep brain unavailable ({type(e).__name__})"


def loop(feature, claim="", deep=False):
    print("=" * 76)
    print(f"WHY LOOP  —  {feature}" + (f'   claim: "{claim}"' if claim else ""))
    print("  Keep asking why. YES = the chain reached a terminal (PHYSICS or THE HUMAN).")
    print("  An LLM is never a terminal — its answer is always another claim.")
    if deep:
        print("  --deep: the BRAIN asks the whys I did not hard-code; the GRAPH answers them.")
    print("=" * 76)
    links = chain(feature)
    if not links:
        print(f"\n  NO EVIDENCE OF ANY KIND for '{feature}'. The loop has nothing to walk.")
        print("  => NOT YES (there is not even a chain to dead-end).")
        print("=" * 76)
        return 0
    hit = []
    for L in links:
        mark = f"TERMINAL: {L['terminal']}" if L["terminal"] else "DEAD END"
        print(f"\n  [{L['chain']}]  {L['step']}")
        print(f"     WHY does that prove it? -> {L['why']}")
        print(f"     WHY does THAT settle anything? -> {L['stop']}")
        print(f"     => {mark}")
        if L["terminal"]:
            hit.append(L)
    # THE BRAIN'S TURN: the whys I did not hard-code.
    if deep:
        print("\n" + "-" * 76)
        print("  [the brain] asking what ELSE would have to be true (slow — ds4 ~1.6 t/s)...")
        r, err = _deep_questions(feature, claim)
        if err:
            print(f"     {err}")
        else:
            for a in (r.get("questions") or []):
                mark = {True: "yes ", False: "NO  ", None: "open"}[a["answered"]]
                print(f"     [{mark}] {str(a['q'])[:78]}")
                if a["answered"] is False:
                    print(f"             -> the GRAPH says: {a['evidence']} ({a['check']})")
            ref, opn = r.get("refuted") or [], r.get("open") or []
            if ref:
                print(f"\n     {len(ref)} question(s) the GRAPH REFUTES — facts, not opinions.")
                print("     A chain cannot terminate through a refuted link.")
            if opn:
                print(f"     {len(opn)} question(s) no check can answer — THE HUMAN'S "
                      f"terminal, and they arrive earned.")

    print("\n" + "-" * 76)
    if hit:
        print(f"  YES — {len(hit)} chain(s) reached a terminal: "
              f"{', '.join(sorted({L['terminal'] for L in hit}))}.")
        print("  The remaining question is not WHY, it is WHETHER IT MEASURES WHAT THE")
        print("  FEATURE IS FOR — and that one is the objective's, or the human's.")
    else:
        print("  NOT YES. Every chain dead-ends before reaching a terminal.")
        print("  Nothing here needed the world to be a certain way. Go get a measurement:")
        print(f"     python -m core.beat_lint --beats docs/beats/<x>.beats.json   (lint FIRST)")
        print(f"     python -m core.witness_runner --beats docs/beats/<x>.beats.json "
              f"--session obs_{feature[:20]}")
    print("=" * 76)
    return 0


def assertions():
    """Every claim in the graph that nobody ever asked WHY about.

    A claim with no outgoing because-edge is not "unverified" — the studio has six
    gates for that. It is something narrower and worse: NOTHING EVER ASKED. The
    status was written and read, and the question of what made it true was never
    put, so there is no answer to have been wrong.

    This is a STRUCTURAL fact — a set difference over edges. No scan, no
    string-matching on feature_name, no heuristic about what evidence "counts". The
    graph is finally able to answer a question about itself.
    """
    from core.graphify_interface import load_dna_graph
    g = load_dna_graph()
    claims = [n for n in g.get("nodes", [])
              if n.get("type") == "FeatureUpdate"
              and n.get("status") in ("verified", "accepted", "observed",
                                      "observed_provisional")]
    answered = {e.get("src") for e in g.get("edges", []) if e.get("rel") == "because"}
    hollow = [n for n in claims if n.get("id") not in answered]

    print("=" * 76)
    print("ASSERTIONS — claims nobody ever asked WHY about")
    print("  A because-edge is the answer to 'why is this true?'. No edge = never asked.")
    print("=" * 76)
    by_feature = {}
    for n in hollow:
        by_feature.setdefault(n.get("feature_name", "?"), []).append(n)
    for f in sorted(by_feature):
        ns = by_feature[f]
        st = sorted({x.get("status", "?") for x in ns})
        print(f"  {f:<44} {len(ns):>2} claim(s)  [{', '.join(st)}]")
    print("=" * 76)
    print(f"  {len(claims)} finalized claim(s); {len(claims) - len(hollow)} carry a why; "
          f"{len(hollow)} are ASSERTIONS.")
    if hollow:
        print("  These are not 'unverified' — the gates cover that. NOTHING EVER ASKED.")
        print("  Ask:  python -m core.why --feature <name> --loop")
    print("=" * 76)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="why", description=__doc__.split("\n")[1])
    p.add_argument("--feature", help="the feature to ask about")
    p.add_argument("--claim", default="", help="what you are about to assert")
    p.add_argument("--loop", action="store_true",
                   help="walk every evidence chain and report where each STOPS (YES = "
                        "it reached PHYSICS or THE HUMAN)")
    p.add_argument("--deep", action="store_true",
                   help="let the BRAIN ask the whys that are not hard-coded (slow: ds4 "
                        "~1.6 t/s). It asks; the graph answers; it is never a terminal.")
    p.add_argument("--assertions", action="store_true",
                   help="every finalized claim with NO because-edge — i.e. nobody ever asked")
    p.add_argument("--promote", action="store_true",
                   help="turn why-shaped FIELDS (.derived_from/.evidence_ids/.evidence) "
                        "into because-edges; reports every reference naming a node that "
                        "does not exist. Read-only without --apply.")
    p.add_argument("--backfill", action="store_true",
                   help="wire each finalized CLAIM to the Observation already carrying "
                        "its evidence (marked derived=true — it is a name match, not a "
                        "citation). Read-only without --apply.")
    p.add_argument("--apply", action="store_true",
                   help="with --promote/--backfill: actually write the edges")
    a = p.parse_args(argv)
    if a.promote:
        return promote(apply=a.apply)
    if a.backfill:
        return backfill(apply=a.apply)
    if a.assertions:
        return assertions()
    if not a.feature:
        p.error("--feature is required (or use --assertions)")
    return loop(a.feature, a.claim, deep=a.deep) if a.loop else run(a.feature, a.claim)


if __name__ == "__main__":
    sys.exit(main())
