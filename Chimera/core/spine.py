"""spine — the because-chain under the vocabulary, and the story it tells.

THE OPERATOR'S CORRECTION (2026-07-23): "all these custom terms in itself must make a
story." docs/TERMINOLOGY.md was built as a DICTIONARY -- 81 entries, alphabetical, each
true and none of them explaining why the next one has to exist. You can read every entry
and still not know why any of it is there.

AND IT REBUILT A FLAW THE STUDIO ALREADY FIXED. core/why.py exists because the graph had
1,448 edges and NOT ONE meant BECAUSE -- only association. The terminology graph shipped
with edges called `references`, which is that same empty association wearing a new name.
A term mentioning another term is not a reason.

    A STORY IS A BECAUSE-CHAIN. That is the whole definition.

So the edges here are AUTHORED, never inferred from word overlap, and they carry the same
`proves` vocabulary as core/why.py rather than a parallel one:

    MEASURED -> PHYSICS      a fact; true in an empty universe
    HUMAN    -> THE HUMAN    taste; the reference, and it is earned

EXACTLY TWO TERMINALS, and in a shipped game the second one is THE PLAYER. That is not an
analogy -- it is the same slot. The rule that keeps the engineering honest ("nothing may
be its own reason") is the rule that makes a story feel real: every event bottoms out in
the world's laws or in a person's choice, and never in "an author said so".

    AND BETWEEN THE TWO TERMINALS LIES EMOTION (the operator, same session).

Everything is two ends and a dial. Physics is one end, the human is the other, and the
feeling is the SPAN -- the traversal, not either endpoint. Which gives a test most games
cannot run: a beat whose chain reaches physics but never the player is a cutscene; one
that reaches the player but never physics is asserted, and reads as manipulation. Only a
chain that spans both was actually felt. The walker that audits an engineering claim is
the walker that audits that.

    python -m core.spine --story membrane      # how this term came to be, to a terminal
    python -m core.spine --tell                # the whole spine, read as one narrative
    python -m core.spine --audit               # every term with no because (an assertion)
    python -m core.spine --graph               # write because-edges into the term graph
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Terminals, named exactly as core/why.py names them.
PHYSICS = 'PHYSICS'
HUMAN = 'THE HUMAN'
TERMINALS = (PHYSICS, HUMAN)

# ---------------------------------------------------------------------------
# THE SPINE
#
# Each entry:  term -> (because, cites, proves)
#   because  the reason, in one sentence, in plain words
#   cites    the term this rests on, or a TERMINAL
#   proves   MEASURED (a fact, with its number) or HUMAN (taste), or '' when the edge is
#            structural and its own citation carries the class
#
# A NUMBER WHEREVER ONE EXISTS. A because without a number is an opinion, and this file
# is not allowed to contain opinions -- that is the same rule as docs/EXPERIMENTAL_METHOD.
# ---------------------------------------------------------------------------

SPINE: dict = {

    # --- the root: why there is a boundary at all -------------------------------------
    'membrane': (
        'a boundary is what makes a cause ATTRIBUTABLE. Without an inside and an outside '
        'there is no individual, so there is nothing an outcome can be attributed to -- '
        'in biology no vesicle means nothing for selection to act on, and in engineering '
        'it means you cannot tell a change from the world.',
        PHYSICS, 'MEASURED'),

    'membrane (verification sense)': (
        'THE SAME REASON, one level up. Sealing a command in a copy and proving it touched '
        'nothing live is attribution applied to your own work. It is one idea, not two: it '
        'caught pi writing to the live graph on its first run.',
        'membrane', 'MEASURED'),

    'skin': (
        'a boundary needs an absolute thickness, because a RELATIVE one scales with the '
        'membrane: 1e-6 of a planet radius made "on the surface" mean plus or minus 6.4 '
        'metres, and side() returned "on" for everything.',
        'membrane', 'MEASURED'),

    'port / stud': (
        'a boundary that nothing crosses is a wall, not an interface. Ports are typed by '
        'WHAT FLOWS -- structural, gravitational, energy, fluid, atmospheric, substrate -- '
        'which is a physical claim about what can pass, not a category.',
        'membrane', ''),

    'the six directions': (
        'a cell has six faces, so its ports ARE the six directions. Picking one and '
        'building it out is a development-focus mechanism that works at every scale, '
        'because the six faces exist at every scale.',
        'port / stud', ''),

    'work queue': (
        'an unfilled port is exactly WHERE THE WORLD IS UNFINISHED, so the to-do list is '
        'enumerated from the world rather than authored by a person.',
        'port / stud', ''),

    'deterministic by coordinate': (
        'neighbouring tiles must agree without negotiating, so content has to be a pure '
        'function of position. Measured seam continuity: 5.8e-10.',
        PHYSICS, 'MEASURED'),

    'section': (
        'determinism by coordinate is what lets a tile ignore its neighbours entirely, so '
        'a section can be addressed by position alone (S+00384+00896) and generated alone.',
        'deterministic by coordinate', ''),

    'cell': (
        'the unit is 1.83 m because that is a person. Earth\'s surface is then 1.52e14 '
        'cells, and a coordinate never has to exceed its own membrane\'s extent.',
        PHYSICS, 'MEASURED'),

    # --- what fills the boundary ------------------------------------------------------
    'genome': (
        'a membrane holds matter, and matter has to be described compactly enough to '
        'regenerate rather than store. Compression IS the description.',
        'membrane', ''),

    'material-DNA': (
        'a genome must be a RANGE and not an average, because a range is the only thing you '
        'can draw new members of a kind from. An average gives you one object forever.',
        'genome', ''),

    'band': (
        'real material varies from region to region, so the target measured off reality is '
        'a min..max and not a value. Demanding a single number is fitting noise.',
        'material-DNA', 'MEASURED'),

    'band margin': (
        'a genome sitting ON a band edge is inside reality by exactly nothing, so its '
        'children fall out. Measured: child survival 38% -> 81% once margin was maximized.',
        'band', 'MEASURED'),

    'liability scale': (
        'a Gaussian drawn on a bounded trait piles probability onto the boundary -- mean '
        '0.95 on [0,1] produced saturated-white children and negative sizes. Modelling on '
        'an unbounded scale and transforming back cannot leave the domain. 0/10 saturated '
        'after.',
        PHYSICS, 'MEASURED'),

    'pleiotropy': (
        'sampling R, G and B independently produced RAINBOW CONFETTI children, because in '
        'real material one luminance factor drives all three.',
        PHYSICS, 'MEASURED'),

    'heritability': (
        'you cannot tell what breeds true from one specimen, because between-specimen '
        'variance is undefined with a sample of one. Two scans of a kind is the minimum.',
        PHYSICS, 'MEASURED'),

    'recombination': (
        'siblings must differ in whole BLOCKS rather than in noise, which is what drawing '
        'each linkage group from one of two parents gives you.',
        'heritability', ''),

    # --- why you train rather than author ---------------------------------------------
    'train, don\'t hand-tune': (
        'an LLM manages about 20 edits an hour and the trainer does about 30,000 '
        'evaluations a second. Six orders of magnitude is not a preference.',
        PHYSICS, 'MEASURED'),

    'computational irreducibility': (
        'there is no shortcut to how something turns out; you have to run it. That is why '
        'the crank cannot be reasoned through, only turned.',
        'train, don\'t hand-tune', ''),

    'objective': (
        'the trainer measures facts and cannot know which are GOOD, so a person writes that '
        'down separately. The LLM sits at the top and the bottom, never in the middle.',
        'train, don\'t hand-tune', ''),

    'satisficer': (
        'an objective with no maximize stops the moment its constraints are met, which is '
        'almost never where you wanted it.',
        'objective', ''),

    'pinned': (
        'a winner rests against some walls, and naming them is how you find where the next '
        'exploit lives.',
        'objective', ''),

    'the exploit is the product': (
        'a degenerate winner is the optimiser auditing your specification at 35 kHz and '
        'finding the hole you would have defended in review.',
        'pinned', ''),

    'iterate the objective, never the artifact': (
        'if the winner is wrong the SPEC is wrong. Proven here: round 1 of arrangement '
        'scored 0.9680, landed inside all four measured bands, and was unusable because '
        'nothing had asked for margin.',
        'the exploit is the product', 'MEASURED'),

    'reachability probe': (
        'a hard gate the population cannot reach scores everything zero, so there is no '
        'gradient and the trainer random-walks at full speed while looking like training. '
        'Measured: 0 of 140 random genomes reached clustering 4.5.',
        'objective', 'MEASURED'),

    'robustness': (
        'one rollout from one starting condition is a coin toss, not a measurement. A '
        'one-micron nudge cost the celebrated walker 5.5 body lengths, and under honest '
        'physics it scored worse than an untrained brain after 80,000 evaluations.',
        PHYSICS, 'MEASURED'),

    'a pinned gene is not a binding constraint': (
        'pinned() reports where a winner RESTS, which is not where it is HELD BACK. '
        'Widening the pinned gene moved the score 0.8238 -> 0.8240, and clustering turned '
        'out to have the largest margin of any fact.',
        'pinned', 'MEASURED'),

    # --- why you enumerate rather than pick --------------------------------------------
    'the Axelrod error': (
        'a hand-authored vocabulary is not a sample of what is possible, it is a sample of '
        'what somebody thought of. Enumerating all 22 two-state machines ranks the famous '
        'tit-for-tat far down; our three hand-written forms landed inside ZERO of reality\'s '
        'four bands.',
        PHYSICS, 'MEASURED'),

    'ruliology': (
        'if hand-picked examples mislead, the remedy is to enumerate all of them '
        'systematically and look.',
        'the Axelrod error', ''),

    'capacity is not monotone under sampling': (
        'more room only helps a search that can exploit it. Lowering one gene\'s floor '
        'raised reachable clustering 4.736 -> 6.588, but adding two more capacity '
        'dimensions LOWERED it to 4.780 and 5.312 -- a sampled space dilutes faster than '
        'it opens.',
        'ruliology', 'MEASURED'),

    # --- why proof works the way it does ----------------------------------------------
    'witness gate': (
        'a compile is not proof. Something has to have been OBSERVED, or the claim is that '
        'the code exists rather than that it works.',
        PHYSICS, 'MEASURED'),

    'the coin': (
        'a claim and its evidence have to match in BOTH directions -- the evidence must '
        'prove the claim, and the claim must be honest to the evidence. Compile plus unit '
        'tests is not "playtested and seen".',
        'witness gate', ''),

    'the why loop': (
        'a FIELD can say anything, but an EDGE cannot, because a graph knows its own ids. '
        'The storage shape IS the integrity check. Measured: 1,448 edges and not one meant '
        'because; 150 finalized claims carried zero recorded whys; 16 live references named '
        'nothing at all.',
        'the coin', 'MEASURED'),

    # --- what a game is made of --------------------------------------------------------
    'two ends and a dial': (
        'a verb needs a noun that has two states and something that moves between them. '
        'Once you have that, morphs, heritability, LOD, growth and the story are all the '
        'same mechanism at different sizes.',
        'membrane', ''),

    'verb': (
        'an action IS the span between two states, so a verb is a dial and not a noun.',
        'two ends and a dial', ''),

    'gate': (
        'progression has to be a dial held until a MEASURED condition holds, or the story '
        'is scripted and the world is not really deciding anything.',
        'verb', ''),

    'LOD of meaning': (
        'each level of detail is the rung below\'s AVERAGE, so approaching is decompression '
        'and retreating is coalescing. Appearance derives from the matter model at every '
        'scale, or the model is incomplete -- which is why there is no aesthetic pass.',
        'two ends and a dial', ''),

    'emergence': (
        'you cannot call for a macro-behaviour, you select for it: the local rule is the '
        'genome, the emergent numbers are the measure, and researched reality is the '
        'objective. Measured: a 40.03 degree repose angle nobody coded, and Kepler\'s third '
        'law at r-squared 1.000 from grown orbits\' own periods.',
        'train, don\'t hand-tune', 'MEASURED'),

    'rung conflation': (
        'settling a higher rung\'s dynamics while still assembling a lower rung\'s parts '
        'fails. Five trained rounds and a granularity probe all failed until the rungs were '
        'split; then the UNTRAINED smoke test succeeded.',
        'LOD of meaning', 'MEASURED'),
}


# Keys are matched case-insensitively everywhere, so normalise ONCE here rather than at
# each lookup -- the first walk dead-ended on 'material-DNA' vs 'material-dna' and reported
# an honest-looking "this is an ASSERTION" for a term that had a perfectly good because.
SPINE = {k.lower(): v for k, v in SPINE.items()}


# The player is the second terminal. Stated here because it is a DESIGN LAW, not a remark:
# during development THE HUMAN is the operator's taste; in the shipped game it is the
# player. Same slot, same rule -- every event bottoms out in the world's laws or in a
# person's choice, and never in "an author said so".
#
# AND BETWEEN THEM LIES EMOTION. Physics is one end, the human is the other, and the
# feeling is the SPAN. So a beat can be audited the way a claim is:
SPAN_VERDICTS = {
    (True, False): ('CUTSCENE', 'lawful world, no player cause -- impressive, not felt'),
    (False, True): ('ASSERTED', 'player named but no physics under it -- reads as '
                                'manipulation, the taste of a bad game'),
    (True, True):  ('FELT', 'a real law reached a real person -- the span was travelled'),
    (False, False): ('INERT', 'neither end reached; nothing is happening'),
}


def span(reaches_physics: bool, reaches_human: bool) -> tuple:
    """Classify a beat by which terminals its chain reaches. Emotion is the SPAN."""
    return SPAN_VERDICTS[(bool(reaches_physics), bool(reaches_human))]


def chain(term: str, max_depth: int = 24) -> list:
    """Walk the because-chain from a term to a terminal. Returns the hops."""
    from core.terms import get

    hops, seen, cur = [], set(), term.lower().strip()
    if cur not in SPINE:
        t = get(cur)
        if t is None:
            raise KeyError(f'no term {term!r}')
        cur = t['term'].lower()
    for _ in range(max_depth):
        if cur in TERMINALS:
            break
        if cur in seen:
            hops.append({'term': cur, 'because': 'CYCLE -- this chain does not terminate',
                         'cites': None, 'proves': ''})
            break
        seen.add(cur)
        e = SPINE.get(cur)
        if e is None:
            hops.append({'term': cur, 'because': None, 'cites': None, 'proves': ''})
            break
        because, cites, proves = e
        hops.append({'term': cur, 'because': because, 'cites': cites, 'proves': proves})
        cur = cites.lower() if cites not in TERMINALS else cites
    return hops


def terminal_of(term: str) -> str | None:
    """Which terminal a term's chain reaches, or None if it dead-ends."""
    hops = chain(term)
    if not hops:
        return None
    last = hops[-1]
    if last['because'] is None or last['cites'] is None:
        return None
    return last['cites'] if last['cites'] in TERMINALS else None


def audit() -> dict:
    """Every term with no because. An unexplained term is an ASSERTION.

    This is the terminology's version of `why --assertions`: not "is your reason good?"
    (nobody here can judge that) but "is there a reason at all?", which is a fact.
    """
    from core.terms import load

    terms = load()
    spined = set(SPINE)
    missing = sorted(t['term'] for k, t in terms.items() if k not in spined)
    dead = []
    for k in spined:
        try:
            if terminal_of(k) is None:
                dead.append(k)
        except KeyError:
            dead.append(k)
    return {'terms': len(terms), 'with_because': len(spined),
            'without_because': missing, 'dead_ends': sorted(dead)}


def tell(root: str = 'membrane') -> str:
    """The spine read as one narrative, breadth-first from a root."""
    kids: dict = {}
    for k, (_, cites, _) in SPINE.items():
        kids.setdefault(cites.lower() if cites not in TERMINALS else cites, []).append(k)

    out, seen = [], set()

    def walk(node, depth):
        for k in sorted(kids.get(node, [])):
            if k in seen:
                continue
            seen.add(k)
            because, cites, proves = SPINE[k]
            tag = ''
            if proves == 'MEASURED':
                tag = '   [PHYSICS]'
            elif proves == 'HUMAN':
                tag = '   [THE HUMAN]'
            out.append((depth, k, because, tag))
            walk(k, depth + 1)

    for t in TERMINALS:
        if kids.get(t):
            out.append((-1, t, None, ''))
            walk(t, 0)
    walk(root.lower(), 0)

    import textwrap
    lines = []
    for depth, k, because, tag in out:
        if because is None:
            lines.append(f'\n=== everything below rests on {k} ===')
            continue
        ind = '  ' * (depth + 1)
        lines.append(f'\n{ind}{k}{tag}')
        lines += [ind + '  ' + l for l in textwrap.wrap(because, 84 - len(ind))]
    return '\n'.join(lines)


def to_graph() -> dict:
    """Write the because-edges into the terminology graph, beside the reference edges.

    `references` stays -- it is honest about being association. `because` is added as a
    SEPARATE relation so a walker can ask for reasons and never be handed a mention.
    """
    from core import world_store as ws
    from core.terms import GRAPH_DB

    con = ws.connect(str(GRAPH_DB))
    ws.add_nodes(con, [(t, 'terminal', t, None, None, None,
                        {'note': 'a legal end of a because-chain'}) for t in TERMINALS])
    rows = []
    for k, (because, cites, proves) in SPINE.items():
        dst = cites if cites in TERMINALS else f'term:{cites.lower()}'
        rows.append((f'term:{k}', dst, 'because',
                     __import__('json').dumps({'because': because, 'proves': proves})))
    ws.add_edges(con, rows)
    con.close()
    return {'because_edges': len(rows), 'terminals': len(TERMINALS)}


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    ap = argparse.ArgumentParser(description='the because-chain under the vocabulary')
    ap.add_argument('--story', help='walk one term to its terminal')
    ap.add_argument('--tell', action='store_true', help='the whole spine as a narrative')
    ap.add_argument('--audit', action='store_true', help='terms with no because')
    ap.add_argument('--graph', action='store_true', help='write because-edges to the graph')
    a = ap.parse_args()

    if a.story:
        import textwrap
        hops = chain(a.story)
        print(f'\nWHY {a.story.upper()}?\n')
        for i, h in enumerate(hops):
            if h['because'] is None:
                print(f'  {h["term"]}\n    (no because recorded -- this is an ASSERTION)')
                break
            for l in textwrap.wrap(f'{h["term"]} -- because {h["because"]}', 86):
                print('  ' + l)
            nxt = h['cites']
            arrow = f'  |  because of: {nxt}'
            if nxt in TERMINALS:
                arrow = f'  |\n  +--> {nxt}'
            print(arrow if nxt not in TERMINALS else arrow)
            print()
        t = terminal_of(a.story)
        print(f'  CHAIN REACHES: {t if t else "NOTHING -- it dead-ends"}')
        return 0 if t else 1

    if a.tell:
        print(tell())
        return 0

    if a.audit:
        r = audit()
        print(f'  {r["with_because"]} of {r["terms"]} terms have a recorded because')
        if r['dead_ends']:
            print(f'  DEAD ENDS ({len(r["dead_ends"])}): ' + ', '.join(r['dead_ends']))
        print(f'  no because yet ({len(r["without_because"])}): '
              + ', '.join(r['without_because'][:14]) + ' ...')
        return 0

    if a.graph:
        r = to_graph()
        print(f'  {r["because_edges"]} because-edges + {r["terminals"]} terminals')
        return 0

    ap.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(_main())
