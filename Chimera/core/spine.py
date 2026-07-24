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


    # --- CLOSING THE ASSERTIONS (2026-07-23, operator: "close the 42 assertions") -------
    # Every term the audit named as having no reason. Authored, each citing something
    # already in the spine or a terminal, each carrying its number where one exists. An
    # audit that names gaps and is never acted on is just a longer way of ignoring them.

    'splat': (
        "it is simultaneously a RENDERING primitive and a STATISTICAL one, so the same "
        "object can be drawn and measured without converting between two representations. "
        "A triangle can be drawn but not distributed; a sample can be distributed but not "
        "drawn.",
        PHYSICS, ''),

    'gaussian splatting / 3dgs': (
        "fitting splats to photographs is how matter gets MEASURED from reality instead of "
        "authored, which is the only way a genome can carry reality's own numbers.",
        'splat', ''),

    'anisotropy': (
        "a splat's shape has to be ONE bounded, scale-free number (1 - min/max) or it "
        "cannot be compared between scans taken at different sizes. Bounded [0,1] by "
        "construction, which is exactly why it must be sampled on the liability scale.",
        'splat', ''),

    'feature': (
        "one axis of a genome stored as mean plus p10..p90 IS the range -- the storage "
        "shape is what makes it a distribution rather than a value.",
        'material-DNA', ''),

    'morphology-DNA': (
        "shape and appearance are independently measurable, so they are independently "
        "trainable. Fusing them would mean a change of colour could not be made without "
        "redescribing the form.",
        'genome', ''),

    'genotype': (
        "you must be able to name the stored description separately from the expressed "
        "thing, or you cannot say what was INHERITED as opposed to what was grown.",
        'genome', ''),

    'plasticity': (
        "the same genotype expressed differently by its environment is the VERB, and it is "
        "not inherited -- which is why environment belongs in the membrane and never in "
        "the genome.",
        'genotype', ''),

    'linkage group': (
        "traits that covary in real material have to be inherited TOGETHER, or a child gets "
        "a coherent value on one axis and a contradictory one on the next.",
        'pleiotropy', ''),

    'mutation': (
        "a low-rate perturbation is a DIFFERENT process from parental variance, and "
        "conflating the two is why sampling from one parent looked like noise instead of "
        "like a family.",
        'recombination', ''),

    'progeny / children': (
        "you do not paint a material onto a surface -- that is texturing, and it gives you "
        "surfaces instead of game content. You isolate ONE object, vary it inside its "
        "measured range, and place instances.",
        'material-DNA', ''),

    'serial number': (
        "once a material is recognised you can store its index instead of its splats, which "
        "is compression made literal -- the same reason a genome is worth recovering at all.",
        'genome', ''),

    'intake method': (
        "a genome does not have to come from a scan: PBR maps are already light-separated, "
        "so an authored asset is easier to read than a measured one. Both feed ONE codebook, "
        "which is the whole reason calibration matters.",
        'serial number', ''),

    'format calibration': (
        "because both intakes feed one codebook, an uncalibrated container FORKS the same "
        "material into two serial numbers. Proven: applying sigmoid() where INRIA stores an "
        "SH DC coefficient gave p10 0.143 against a true 0.000.",
        'intake method', 'MEASURED'),

    'brick': (
        "a genome has to become something PLACEABLE or it stays a description. Attaching it "
        "to a membrane with a mating stud is what turns a measurement into matter you can "
        "build with -- 6,037 bricks/sec, deterministic.",
        'genome', 'MEASURED'),

    'mate': (
        "occupancy has to be RECORDED, not inferred from geometry: open_ports() inferred it "
        "and reported \"filled 0\" while six bricks were attached.",
        'port / stud', 'MEASURED'),

    'saturated': (
        "a membrane with no open ports has nothing left to build, so it stops being work and "
        "becomes something to move on from.",
        'work queue', ''),

    'negative space': (
        "an object has to grow AROUND its environment, so the environment must enter the "
        "growth as frozen cells rather than as a collision test applied afterwards. The "
        "regolith is not the absence of the object; it is what the object must fit into.",
        'membrane', ''),

    'time as the outermost membrane': (
        "anything with a beginning and an end is a boundary, so time is a membrane like any "
        "other -- past inside, future outside, present the surface. The story is then just "
        "the outermost dial, with gates on it.",
        'membrane', ''),

    'arrangement': (
        "a material and its PLACEMENT are separately measurable, and placement is what makes "
        "an object rather than a texture. What must be learned is how the pieces fit.",
        'morphology-DNA', ''),

    'clustering': (
        "it is a RATIO (mean pairwise distance over nearest-neighbour distance), so it is "
        "scale-free and comparable between a scan and an emitter of different sizes. It is "
        "the fact that exposed the gap: real regions 4.679-8.172, hand-written forms "
        "1.277-1.497.",
        'arrangement', 'MEASURED'),

    'verticality': (
        "how much matter stands up versus lies flat is set by GRAVITY, which acts the same "
        "on a scan and on an emitted arrangement -- so the number transfers between them.",
        'arrangement', 'MEASURED'),

    'alignment': (
        "real material sits at PARTIAL coherence (0.516-0.576) -- neither combed nor random "
        "-- so it discriminates real arrangement from both idealised failure modes at once.",
        'arrangement', 'MEASURED'),

    'aspect': (
        "the overall proportion of an arrangement is scale-free, so it constrains the shape "
        "of the whole without constraining its size.",
        'arrangement', ''),

    'band error': (
        "distance to a band must be normalised by that band's own width, because clustering "
        "spans 3.49 and alignment spans 0.06 -- a raw sum would weight clustering 58x for no "
        "physical reason and the winner would match density while getting orientation wrong.",
        'band', 'MEASURED'),

    'form': (
        "an arrangement has to be selectable by name at the emitter, or a trained genome "
        "cannot replace a hand-written one without rewriting every caller.",
        'arrangement', ''),

    'domain': (
        "the trainer has to stay generic -- it cannot know what an economy or a creature IS "
        "-- so the facts come from a separate module that reports them and never judges them.",
        "train, don't hand-tune", ''),

    'measure': (
        "the domain reports FACTS and the objective decides which are good. Mixing them puts "
        "taste inside the crank, where nobody can see it and the optimiser cannot audit it.",
        'domain', ''),

    'self-loading reference': (
        "a domain with no reference optimises nothing while looking identical to one that "
        "works: material_appearance trained against None until somebody finally checked.",
        'domain', 'MEASURED'),

    'hard gate': (
        "a constraint that scores ZERO removes the gradient wherever the population cannot "
        "satisfy it, so it is only safe where nothing is near it yet -- an overshoot guard, "
        "not a standard.",
        'reachability probe', ''),

    'the LLM sits at the top and the bottom, never the middle': (
        "the LLM writes the constraints and reads the walls, because those are judgements; "
        "it never turns the crank, because that is 20 edits an hour against 30,000 "
        "evaluations a second.",
        "train, don't hand-tune", 'MEASURED'),

    'the GPU is mandatory': (
        "scoring N randomised restarts and keeping the worst costs N times the compute, and "
        "that honesty is unaffordable on a CPU: 2,358 evals/sec at 16,384 worlds against "
        "pybullet's 70 with eight P-cores pinned at thermal limit.",
        'robustness', 'MEASURED'),

    'the one rule': (
        "a read-back inside the rollout loop destroys the entire advantage: 1,575 CPU-GPU "
        "syncs per batch ran 300x SLOWER than the CPU it was meant to replace.",
        'the GPU is mandatory', 'MEASURED'),

    'capacity': (
        "how much a program can express caps what it can reach, independently of how well "
        "you search: 2-state machines top out at 0.151 against each other, while 3-state "
        "machines reach 0.593 against them.",
        'ruliology', 'MEASURED'),

    'pocket of computational reducibility': (
        "if everything were irreducible nothing could be trained at all, so a trainable "
        "feature is precisely one where a measurable objective has a searchable gradient "
        "into a predictable region.",
        'computational irreducibility', ''),

    'rung': (
        "each level's averages are the next level's data, so the levels must be settled "
        "separately -- assembling one while settling another is the named failure mode.",
        'LOD of meaning', ''),

    'research gate': (
        "a session that inherits its answer from nowhere is guessing, and a guess is "
        "cheapest to catch before the work rather than after it.",
        'witness gate', ''),

    'visual gate': (
        "a recorded number is not a look. Something has to have SEEN it, or \"verified\" "
        "means the measurement ran and not that the thing appeared.",
        'witness gate', ''),

    'training gate': (
        "verifying a piece that was never trained means it was never evaluated, only "
        "observed once -- which is the coin-toss problem wearing a checkmark.",
        'witness gate', ''),

    'membrane vs Faraday cage': (
        "the seal covers the filesystem and the studio's own state, NOT the network. Stating "
        "the limit is what keeps the containment a measurement instead of a claim.",
        'membrane (verification sense)', ''),

    'A field can lie; an edge cannot': (
        "a string field can name anything, including something that does not exist, but a "
        "graph knows its own ids -- so the STORAGE SHAPE is the integrity check. Measured: "
        "16 live references named nothing at all, two of them English sentences sitting in "
        "an id field.",
        PHYSICS, 'MEASURED'),

    'why it is the primitive': (
        "the same reason the membrane exists at all: attribution. Kept as its own term "
        "because it is the sentence people quote, and a quoted sentence still needs a why.",
        'membrane', ''),

    'rung conflation': (
        'settling a higher rung\'s dynamics while still assembling a lower rung\'s parts '
        'fails. Five trained rounds and a granularity probe all failed until the rungs were '
        'split; then the UNTRAINED smoke test succeeded.',
        'LOD of meaning', 'MEASURED'),
    # --- THE HUMAN TERMINAL (2026-07-23) -----------------------------------------------
    # The closed spine reported all 80 chains landing on PHYSICS and none on THE HUMAN,
    # and run through its own span test the vocabulary scored CUTSCENE. The cause was not
    # an oversight: every -ology recruited so far (physics, geology, astronomy,
    # climatology, optics, genetics, statistics, ruliology) is a physics-side science.
    # The operator's correction -- "we'll need all the ologies, well this is one of them"
    # -- names the fix: sociology is the first hire on the other side.
    #
    # THE RULE THAT KEEPS THE COLUMNS HONEST: does it hold with NOBODY THERE?
    # Gravity does -> PHYSICS. A just-noticeable-difference does not, and neither does a
    # group's preference -> THE HUMAN, even though both are rigorously measured. Without
    # this rule "we measured it" launders every human fact into the physics column and the
    # terminal stays empty while looking full.

    'the column rule': (
        "without it, 'we measured it' absorbs every human fact into the physics column and "
        "the human terminal stays empty while looking full -- a JND and a group's preference "
        "are both rigorously measured and neither holds with nobody there.",
        'taste', ''),

    'taste': (
        "no measurement can settle whether a thing is worth WANTING. You can measure what "
        "something is and what it does; whether it should exist bottoms out in a person, "
        "and there is nowhere further to go.",
        HUMAN, 'HUMAN'),

    'the physics measure vector': (
        "taste is learned over a handful of honest physical axes rather than over pixels, "
        "which is what makes it cheap: a reward model over raw artifacts needs thousands of "
        "labels, and ~6 interpretable axes need a DOZEN comparisons.",
        'measure', 'MEASURED'),

    'the preference loop': (
        "taste has to be ELICITED as comparisons rather than declared as numbers, because a "
        "person can reliably say which of two things they prefer and cannot reliably say "
        "what weight they put on an axis.",
        'taste', 'HUMAN'),

    'fun': (
        "it is subjective for one person and STRUCTURED across a group, so it is measurable "
        "as a distribution even though it is not measurable as a value -- the same reason a "
        "material is stored as a range and not an average. This is the operator's point, and "
        "it is what makes the human terminal reachable at all.",
        'taste', 'HUMAN'),

    'cultural heritability': (
        "the heritability formula applies literally with cultures in place of specimens: "
        "V_between / (V_between + V_within) says which parts of fun are REGIONAL (predictable "
        "from where a person is) and which are PERSONAL (varying as much inside a country as "
        "between countries, so no amount of sociology will predict them and you must ask the "
        "individual). Most arguments about what players want are that distinction, unmade.",
        'fun', 'HUMAN'),

    'psychophysics': (
        "the span between a physical stimulus and a human sensation is itself measurable -- "
        "just-noticeable-difference, Weber's law, measured since the 1860s -- so 'how precise "
        "does this have to be' has an answer instead of an opinion: whatever a person can "
        "actually tell apart at that distance.",
        HUMAN, 'HUMAN'),

    'the player is the second terminal': (
        "in development THE HUMAN is the operator's taste and in the shipped game it is the "
        "player. It is the same slot, not an analogy -- which is why the rule that keeps the "
        "engineering honest (nothing may be its own reason) is the rule that makes a story "
        "feel real.",
        'taste', 'HUMAN'),

    'a choice that costs something': (
        "a choice with no cost is a menu, not a choice. The cost is what makes the player the "
        "CAUSE of what follows rather than the witness of it, and only a cause can be a "
        "terminal.",
        'the player is the second terminal', 'HUMAN'),

    'the span': (
        "emotion is neither terminal but the DISTANCE between them: a real law reaching a "
        "real person. Physics alone is a cutscene (lawful, nothing felt); the human alone is "
        "asserted (no physics under it, and it reads as manipulation). Only a chain that "
        "spans both was actually felt.",
        'psychophysics', 'HUMAN'),

    # --- TIMELINES ARE MEMBRANES (2026-07-23) ------------------------------------------
    # Operator: "timelines control everything, they are the mega membrane", and the
    # demographic target "is another timeline that controls everything".
    #
    # Time being the outermost membrane does NOT mean there is one clock. It means
    # anything with a beginning and an end is a boundary -- so every timeline is a
    # membrane at its own scale, nesting exactly like universe > planet > section > cell.
    # The correction that matters: a demographic is a TRAJECTORY, not a snapshot, which is
    # the same error as storing a material as an average instead of a range.

    'timeline': (
        "anything with a beginning and an end is a boundary, so a timeline is a membrane "
        "like any other -- and there is no single clock, only nested ones: cultural time "
        "contains development time contains story time contains a session contains a beat.",
        'time as the outermost membrane', ''),

    'cultural time': (
        "a demographic is a TRAJECTORY and not a snapshot: what is fun in a place in 2026 "
        "is not what was fun there in 2016. Treating an audience as fixed is the same "
        "mistake as storing a material as an average instead of a range. It cites the human "
        "terminal and not `timeline`: that a timeline is a membrane is structurally true but "
        "it is not WHY this one matters, and citing it routed the branch back into physics.",
        HUMAN, 'HUMAN'),

    'development time': (
        "the project's own history is a boundary with an inside and an outside, which is "
        "why THE_WORKFLOW.md could only be written by reading the git chronology IN ORDER "
        "-- the sequence is the structure, not a presentation choice.",
        'timeline', ''),

    'story time': (
        "the player's journey is the dial between two states of the world, so the story is "
        "just the outermost dial the player can actually reach, with gates along it.",
        'timeline', ''),

    'a release is a gate': (
        "a gate is a dial held until a MEASURED condition holds, and a release condition is "
        "measured on the CULTURAL timeline -- so when to ship stops being a calendar guess "
        "and becomes a reading of whether the audience's trajectory has crossed the bar.",
        'cultural time', 'HUMAN'),

    'the human stands at the boundary': (
        "cultural time and development time are two membranes, and a person is the only "
        "thing that can look across the seam between them and decide what to build. That is "
        "not a management role, it is a PORT -- the one place those two membranes touch.",
        'cultural time', 'HUMAN'),

    # --- ADAPTIVE-PROCESS THEORY (2026-07-23) ------------------------------------------
    # From Wolfram, "Why Does Biological Evolution Work? A Minimal Model for Biological
    # Evolution and Other Adaptive Processes" (2024-05-03). Read at the operator's
    # instruction. Three of its findings were TESTED against this studio's own trainer
    # rather than admired, and one of them reversed a cleanup I was about to do.

    'neutral mutation': (
        "a mutation that changes nothing measurable is not waste -- it is what lets single "
        "point changes ACCUMULATE until together they unlock a jump no one of them could "
        "reach. Wolfram accepts any mutation that does not DECREASE fitness for exactly "
        "this reason.",
        'mutation', ''),

    'noncoding gene': (
        "part of a genome that is never expressed in the phenotype, so many genotypes give "
        "one result -- Wolfram measured 18 of 26 rule cases sampled, leaving 6,561 genomes "
        "with identical behaviour. MEASURED HERE: sweeping `align_up` across its whole range "
        "moves the arrangement facts by 0.009, and `taper` by 0.056. They are noncoding.",
        'neutral mutation', 'MEASURED'),

    'the neutral network': (
        "a continuous weighted-sum fitness has almost no exact ties, so it has no plateaus "
        "to drift along -- which means a NONCODING gene is the only genuinely neutral "
        "dimension such a search has. `align_up` was about to be deleted as dead weight; it "
        "is in fact this domain's entire drift capacity.",
        'noncoding gene', 'MEASURED'),

    'computational necessity': (
        "when an evolved answer looks ornate, the ornateness is usually FORCED rather than "
        "chosen: exhaustive search showed the only rules reaching long lifetimes are the "
        "elaborate ones. Weaker evidence of the same kind here -- five independent seeds "
        "converge to 0.9125-0.9152, a 0.3% spread, so the trained arrangement is closer to "
        "what the four bands REQUIRE than to what our search happened to find.",
        'computational irreducibility', 'MEASURED'),

    'adaptive evolution finds a way': (
        "the encouraging half of the same result: these searches do not get stuck. Wolfram "
        "found progress possible in almost all mutation sequences, and five seeds here land "
        "within 0.3% of each other -- so a poor result is evidence about the OBJECTIVE, not "
        "about the optimiser having been unlucky.",
        'computational necessity', 'MEASURED'),

    'punctuated equilibrium': (
        "long plateaus broken by sudden jumps, emerging from plain hill-climbing with no "
        "mechanism put in to produce it. Visible in this studio's own fitness curves: "
        "0.7152 -> 0.9323 -> 0.9676, then flat for 200 generations.",
        'adaptive evolution finds a way', 'MEASURED'),

}


# Keys are matched case-insensitively everywhere, so normalise ONCE here rather than at
# each lookup -- the first walk dead-ended on 'material-DNA' vs 'material-dna' and reported
# an honest-looking "this is an ASSERTION" for a term that had a perfectly good because.
SPINE = {k.lower(): v for k, v in SPINE.items()}




# ---------------------------------------------------------------------------
# THE TIMELINE LADDER
#
# Outermost first. Each contains the next, and each GATES the one inside it: a condition
# measured on the outer timeline is what releases the inner one's dial. This is the same
# containment as universe > planet > section > cell -- a timeline is not a special kind of
# thing, it is a membrane whose axis happens to be time.
#
# The operator sits on the seam between CULTURAL and DEVELOPMENT: the only port where a
# person can read one membrane and act on the other.
# ---------------------------------------------------------------------------

TIMELINES = [
    ('cultural',    'a demographic\'s own trajectory; generations', HUMAN),
    ('development', 'this project\'s history, recorded in the git chronology', ''),
    ('story',       'the player\'s journey through the world, 0 -> 1', ''),
    ('session',     'one sitting at the game', ''),
    ('beat',        'one moment, where a span is either felt or not', HUMAN),
]


def gates(inner: str) -> str | None:
    """Which timeline gates this one -- the membrane immediately outside it."""
    names = [t[0] for t in TIMELINES]
    if inner not in names:
        raise KeyError(f'no timeline {inner!r}; have {names}')
    i = names.index(inner)
    return names[i - 1] if i else None


def ladder() -> str:
    out = []
    for d, (name, what, term) in enumerate(TIMELINES):
        tag = f'   -> {term}' if term else ''
        out.append('  ' * d + f'{name}{tag}')
        out.append('  ' * d + f'    {what}')
    return '\n'.join(out)

# ---------------------------------------------------------------------------
# THE -OLOGIES (operator: "we'll need all the ologies")
#
# Not a slogan -- the STAFFING PLAN for the two terminals. Each science is where one
# terminal's numbers come from, and a terminal with no science behind it stays empty no
# matter how much is built on the other side. The vocabulary scoring CUTSCENE against its
# own span test was this table having one column filled and two blank.
#
# COLUMN RULE: does the fact hold with NOBODY THERE?
#   yes -> PHYSICS       no -> THE HUMAN       the measurable gap between -> THE SPAN
# ---------------------------------------------------------------------------

OLOGIES = {
    # physics-side: true in an empty universe
    'physics':        (PHYSICS, 'gravity, contact, torque limits', 'recruited'),
    'astronomy':      (PHYSICS, 'N-body accretion, Kepler slope 1.50 at r2 1.000', 'recruited'),
    'geology':        (PHYSICS, 'regolith repose 40.03 deg, mineral spectra', 'recruited'),
    'climatology':    (PHYSICS, 'moist-greenhouse limit, Jeans escape', 'recruited'),
    'optics':         (PHYSICS, 'Rayleigh/Mie scattering, SH coefficients', 'recruited'),
    'genetics':       (PHYSICS, 'heritability, linkage, liability scale', 'recruited'),
    'statistics':     (PHYSICS, 'bands, range-bias d2 constants, Bradley-Terry', 'recruited'),
    'ruliology':      (PHYSICS, 'irreducibility, capacity, the Axelrod error', 'recruited'),

    # the span: a measurable gap that needs both a stimulus and an observer
    'psychophysics':  ('THE SPAN', 'just-noticeable-difference, Weber law; sets how precise '
                                   'a band must actually be', 'NAMED, NOT YET USED'),
    'perceptual psychology': ('THE SPAN', 'attention, salience, what a player notices at all',
                              'NOT RECRUITED'),

    # human-side: needs a person to be true
    'sociology':      (HUMAN, 'group preference structure; which parts of fun are cultural '
                              'vs personal', 'FIRST HIRE, 2026-07-23'),
    'anthropology':   (HUMAN, 'ritual, meaning, what a place signifies', 'NOT RECRUITED'),
    'psychology':     (HUMAN, 'motivation, flow, frustration tolerance', 'NOT RECRUITED'),
    'linguistics':    (HUMAN, 'naming, story grammar, what reads as a sentence', 'NOT RECRUITED'),
}


def staffing() -> dict:
    """Which terminals have a science behind them, and which are still empty."""
    out = {}
    for name, (col, supplies, status) in OLOGIES.items():
        out.setdefault(col, {'recruited': [], 'open': []})
        key = 'recruited' if status.startswith(('recruited', 'FIRST')) else 'open'
        out[col][key].append(name)
    return out

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
    # BOTH directions. The first version only asked "does every term have a because?" and
    # happily printed "95 of 80" once the spine grew past the doc -- a term that exists as
    # a reason but was never written down is just as unfindable as one with no reason.
    undocumented = sorted(k for k in spined if k not in terms)
    dead = []
    for k in spined:
        try:
            if terminal_of(k) is None:
                dead.append(k)
        except KeyError:
            dead.append(k)
    # A `proves` class and a citation can DISAGREE, and nothing noticed until the human
    # branch was labelled HUMAN throughout and still terminated at PHYSICS. An edge that
    # claims to rest on a person must actually reach one.
    mislabelled = []
    for k, (_, _, proves) in SPINE.items():
        if proves == 'HUMAN' and terminal_of(k) != HUMAN:
            mislabelled.append(k)

    return {'terms': len(terms), 'with_because': len(spined),
            'without_because': missing, 'undocumented': undocumented,
            'dead_ends': sorted(dead),
            'mislabelled': sorted(mislabelled)}


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
        print(f'  {r["terms"]} terms documented, {r["with_because"]} reasons recorded')
        if r.get('undocumented'):
            print(f'  IN THE SPINE BUT NOT IN THE DOC ({len(r["undocumented"])}): '
                  + ', '.join(r['undocumented']))
        if r.get('mislabelled'):
            print(f'  CLAIMS HUMAN BUT REACHES PHYSICS ({len(r["mislabelled"])}): '
                  + ', '.join(r['mislabelled']))
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
