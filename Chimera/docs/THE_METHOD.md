# THE METHOD — how anything gets proven

> The complete inquiry method, solidified 2026-07-24 from the conversation that built it.
> Companion to `docs/THE_LINE.md` (PROGRAM/TRAIN/HUMAN) and `docs/OBJECTIVE_DESIGN.md`.
> This is the one that governs *requests*: what to ask for, and what "done" means.
> **Start with the map: `docs/THE_WORKFLOW.md`** — the whole method end to end; this is its engine.

---

## The request verb is PROVE (never "build")

"Build" is the old-programming verb — press the button, trust the output. It lets the agent
*make a thing and declare it done*, which is the one failure this whole studio exists to kill.
The verb is **PROVE**, borrowed from science, and the reason is the entire value:

> **"Prove" forces the definition to be reduced.** You cannot prove what you cannot first
> state precisely. So "prove X" forces *"what exactly is X, and how would we check it?"* before
> a single line of work. "Build" never asks that.

The only other verb is **DECIDE** — for taste. The operator is THE HUMAN terminal; you don't
prove taste, you decide it. Two verbs. That reduction is itself the point.

---

## Two terminals — where proof stops

A proof is a chain of *because* that ends at a terminal. There are exactly two, and an LLM is
**never** one of them (its answer is always another claim):

- **PHYSICS** — a measured fact, true in an empty universe. Discharged by *running the code and
  reading the number.* Cannot be bluffed: it runs or it doesn't.
- **THE HUMAN** — the reference; taste, meaning, "good and evil." Discharged by the operator's
  ratification, or measured through a *model of the target human* (the taste/heritability split).

`Prove X` = build the why-chain for X until every branch reaches PHYSICS or THE HUMAN.
The two terminals are also the **floor of the recursion** — a claim that reaches one does not
recurse further. Without them it is turtles all the way down; with them the whole thing is finite.

---

## The engine — a question-tree that grows itself

The atom is the **question**. The method is one operator, applied fractally:

```
PROVE(X):
  shatter X into its terms → each term into claims
  for each claim, ask its questions; each question is a fork:
      ├─ I know it (the AI is the domain expert)        → answer it
      ├─ it is a physical claim                          → RUN the measurement → answer it
      └─ I cannot answer it honestly                     → it SPENDS A RESEARCH CALL
                                                            (research lands, and SPAWNS new questions)
  branches stop at PHYSICS (a measurement) or THE HUMAN (the operator)
  the tree stops growing when no question returns anything new  → DRY
  the operator calls ENOUGH
```

Load-bearing consequences:

- **The questions ARE the measurement.** For a meaning-claim there is no instrument — the
  structured interrogation *is* the science. Asking well and answering well is the whole act of
  proving. The questions are not scaffolding around some later "real" measurement; there is no
  later.
- **Research is demand-driven, not a ritual.** A question you cannot answer honestly *is* a
  research request wearing a question mark. Research everything = theater; research nothing =
  blind faith; **research exactly what the questions demand** — and the questions tell you.
- **Research is generative.** Answering by research hands you questions you could not have asked
  before you knew — so the tree grows where knowledge is thin and stops where it is thick.
- **Enough is the operator's one lever.** Completeness is unprovable (you cannot see the lens you
  never ground). So the operator decides *is it deep enough yet* — the single decision the method
  leaves to a human besides taste.

---

## Lenses and the optician

You do not question a loaded term with one eye. You grind **lenses** — each a discipline
(physicist, sociologist, theologian, mythologist, psychologist) that asks its own questions and
whose answers reach a terminal. The **optician** selects, for a given term and demographic, which
lenses to grind. **The AI is the expert** — it asks *and* answers each lens's questions; the
lens's questions come grounded in the discipline's real frameworks (e.g. sociology = Griswold's
cultural diamond + Bourdieu's distinction + Hall's encoding/decoding), and research is spent only
where the AI cannot answer honestly. Faith-with-a-floor: you trust the AI to ask and answer;
physics checks its own half by running; you ratify the meaning half and call enough.

---

## Stage 0 — the demographic

*Who is this for?* — asked first, because meaning is demographic (The Matrix proves itself to a
different human than a children's fable; the titles sort by audience). The demographic decides
*which* human terminal you aim at — whose archetypes land, whose taste. It is a DECIDE, the outer
membrane everything else is relative to. The sociological lens (Bourdieu + Hall) is the instrument
that turns it into a checkable claim: *does the target demographic decode the meaning I encoded?*

---

## The gates seal it

`preflight → witness / coin / why gates → postflight`. A claim is not proven because the agent
says so or shows a render (H-14: a render is not a witness). It is proven when it is run,
observed, recorded, and the chain reaches a terminal. No render-and-declare.

**This is the dyadAnalysis.** A render is not a witness *because it is one system showing itself its
own work* — a monad. It becomes proof only when a SEPARATE system reads it: the physics (the agent)
produces a NUMBER, and an independent mind — LM Studio's vision model plus the operator — reads the
render BLIND and produces a TERM; proof is their measured AGREEMENT (`ChimeraEngine/human_messenger.py`).
Two systems kept apart, converging — the shape of thought itself (`THE_FORMULA.md` §"Why a dyad at all").

---

## The honest bounds (which belong to the method, not against it)

- **Meaning is observer-completed** — it lives in the viewer, not the scene's atoms; so a meaning
  claim is checked against a *model of the viewer*, never a fact of the matter.
- **Archetypes are strong, not absolute** — a heavy near-universal core (the reason Stage 0
  matters) wrapped in real cultural variance (exactly what the heritability split measures).
- **Fiction is not the forbidden lie** — art is honest fiction, labeled and consensual; keeping
  the two terminals separate is what lets facts stay true *and* stories stay free. Collapse them
  and you kill one or the other.
- **Completeness is never certain** — the operator's "enough" is the honest stopping rule, not a
  proof of totality.

That is the method. It maps its own territory, digs only where it must, stops at two floors, and
leaves the human two levers: *decide the taste*, and *call when it is deep enough.*
