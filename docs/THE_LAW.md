# THE LAW — read this before you do anything

> Every document in this repository carries a banner pointing here. There is one reason for that:
> the rule below was written as *rule 24*, at the back of a file, and was therefore read last and
> applied never — and the one document guaranteed to be read first, `story/README.md`, was the one
> document that did not carry it at all.

---

## RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.

The operator, 2026-08-02: *"Every membrane is a theory. Every port is a theory. Every connection is
a theory. The game itself is a theory."*

**A membrane is not a thing you build and then check. It is a CLAIM about how the world works, and
building it is the experiment.** Three parts, and all three are required before a line is written:

| part | what it is | the test that it is real |
|---|---|---|
| **STATEMENT** | what it claims, one sentence, plain words | someone could disagree with it |
| **PREDICTION** | a number it implies **that you have not measured** | it could come out otherwise |
| **FALSIFIER** | what would kill it, named **before** the run | you would accept that as a loss |

    A DESCRIPTION SURVIVES ANY RESULT. A THEORY CAN LOSE.

**The falsifier is the part that gets skipped**, and skipping it is how work becomes unfalsifiable.
If you cannot say in advance what would prove you wrong, you will not notice when it happens — you
will find a reason the result still fits, and every reason will be individually reasonable. Four
confident diagnoses were reversed on the day this rule was written, and every one of them had been
stated without a falsifier.

**It is fractal, and that is what makes the game one object:** the game is a theory, a membrane is
a theory, a port is a theory, a number is a theory. Each level's PREDICTION is the level below's
TEST — `theCooling` predicted **3760 K** and the literature said ~3700, so the membrane *was* the
experiment and the number *was* the result.

**Rule 0 comes before Rule 1** because you cannot derive your way to something you have not claimed.
Full method, with the worked example: `docs/THE_WORKFLOW.md` §0.

---

## RULE 1 — A PARAMETER SWEEP IS AN ADMISSION THE DERIVATION WAS NOT DONE

The operator's words, from 2026-07-28 and again on 2026-08-02:

> *"You have to know it works because it's proven mathematically first before you start training."*

**What it looked like when it was violated the second time.** A walker would not walk. The response
was a four-variant parameter sweep — alive bonus, stagnation floor, penalty weight, effort cost —
run in parallel. One variable per variant. Controls. A fair comparison. Honest reporting. It wore
this project's own method as a costume, and that is exactly why it felt like work.

**Every variant was asking the body for a speed it physically cannot walk at.**

    this world     g = 7.076 m/s^2 (0.722 Earth),  leg 0.9201 m
    theHuman derives its own comfortable speed:    0.9924 m/s
    the trainer targeted:                          1.285  m/s   <- MEASURED ON EARTH

Froude settles it in one line. `Fr = v^2/(gL)`, and equal Fr means a dynamically similar gait:
1.285 m/s is **Fr 0.183** on Earth and **Fr 0.254** here — 39% higher, heading toward the walk→run
transition. So the velocity term demanded a running-ward gait while the tracking term demanded
Earth *walking* envelopes. The body could satisfy neither, so it satisfied neither and collected
the alive bonus instead.

> ### THE CROUCH WAS THE ONLY STABLE POINT IN A CONTRADICTORY REWARD.

The stride clock was wrong too, but by **3.9%, not the 18%** first published here: `theHuman`
derives its own stride of **1.1730 s** from the leg as a compound pendulum, and the 1.3267 s once
quoted was Earth's 1.127 s Froude-transported -- the forbidden move, made by the gate meant to
forbid it. Read the body's published cadence, never a transported one.

**No sweep can find that.** Four variants asking an impossible question rank four failures, and the
winner is whichever fails most gracefully — which then gets believed and reported as progress.

---

## Why this is RULE 1 and not rule 24

It is the only rule that decides whether the other twenty-three are being applied to a real
question. Rules about controls, scale, self-normalisation and instruments all assume you are
measuring something worth measuring. A sweep over a reward whose targets belong to another planet
satisfies every one of them and is still worthless.

    THE TELL: before running variants, ask what QUESTION each one answers.
    If the answer is "which number is best", STOP. That is a search where a derivation belongs.

Sweeping is legitimate only for numbers that are genuinely **free**. A target speed Froude-derived
from measured gravity is not free — the membrane already published it.

---

## It is enforced, not merely written down

    python tools/training_gate.py --target-speed 1.285 --stride-s 1.127

Refuses a run whose speeds are not scaled by `sqrt(g/g_E)`, whose strides are not scaled by
`sqrt(g_E/g)`, or which disagrees with what the body publishes about itself. Run against the
trainer as it stood on 2026-08-02, it refuses and names both defects with the corrected numbers.

---

## The rest of the method

The full set — **27 rules**, each with the failure that earned it — is
**`Chimera/docs/EXPERIMENTAL_METHOD.md`**. Rules 2–11 are about not fooling yourself while
*debugging*; 12–17 while *reporting*; 18–21 about *direction* (where to look when everything you
can see is already correct); 22–26 about *order*, about instruments that need instruments, about
the difference between a number you transported and one you derived, and about the fact that a
claim without a falsifier is a description.

**Rule 0 is applied at the smallest scale by `S-1 VALIDATE`** — every port tested alone against a
known answer, with `port_test()` *refusing to register* a test that names no falsifier. That is
Rule 0 as code rather than as a paragraph, and it is the cheapest place it can possibly be applied.
The layer it feeds is specified in **[`docs/THE_COMPILER.md`](THE_COMPILER.md)**: ports → primitives
→ programs → parser → runtime → calibration.

Two other gates run beside this one:

    python story/folding.py audit          # units: what a law may connect to
    python tools/methodology_gate.py       # every membrane against the workflow
    python tools/slider.py                 # move a free number; whatever does not move is typed

---

## THE INDEX OF EVERY RULE (added 2026-08-03, operator delegation)

One fact, one home: every rule's FULL text lives in exactly one file (the pointer), and this
index is the map — organized by what each rule protects. Numbers are stable forever: rules
are appended, never renumbered, and a new rule is added to this index in the same commit.
LAW 0 and LAW 1 above ARE EM-26 and EM-01, kept at the front because they decide whether the
other twenty-four are being applied to a real question at all.

**Truth of claims**

| rule | one line | enforced by | full text |
|---|---|---|---|
| LAW 0 ≡ EM-26 | a claim without a falsifier is a description, and a description cannot be wrong | `port_test()` at S-1 VALIDATE | EM-26 |
| EM-8 | record the negative results; a ledger of wins is a lie of omission | prose | EM-8 |
| EM-16 | matching names is not matching definitions — joining a codebook, THEIR file is the authority | prose | EM-16 |

**Derivation — Law 1's family**

| rule | one line | enforced by | full text |
|---|---|---|---|
| LAW 1 ≡ EM-1 | a parameter sweep is an admission the derivation was not done | `tools/training_gate.py` | EM-1 |
| EM-25 | a transported number is not a derived number | `tools/training_gate.py` | EM-25 |
| EM-9 | arithmetic before action — but verify the model behind the arithmetic | prose | EM-9 |
| EM-17 | derive the shape, let physics set the level; when they disagree, the disagreement IS the finding | prose | EM-17 |
| EM-27 | the interface membrane is derived first — grow from the connection, not from the average | prose | EM-27 |

**Measurement hygiene (not fooling yourself)**

| rule | one line | enforced by | full text |
|---|---|---|---|
| EM-2 | measure the thing, not a proxy for the thing | prose | EM-2 |
| EM-3 | benchmark in the state the system will actually be in | prose | EM-3 |
| EM-4 | distrust any probe that can read a cache | prose | EM-4 |
| EM-5 | watch what the machine is doing, not what it reports | prose | EM-5 |
| EM-6 | capture stderr before you diagnose | prose | EM-6 |
| EM-7 | one variable at a time, and keep the control | prose | EM-7 |
| EM-10 | read the tool's own source and changelog | prose | EM-10 |
| EM-12 | run the instrument on something whose answer you already know | the clay control; `emit()` is a free known subject | EM-12 |
| EM-13 | measure at the scale the thing lives at — count the pixels the effect occupies | prose | EM-13 |
| EM-14 | a threshold defined in terms of the population it measures reports nothing | prose | EM-14 |
| EM-15 | suspect the instrument's construction, not only its reading | prose | EM-15 |
| EM-24 | an instrument needs an instrument | the contrast proofs (`parity_report`, differential-vs-uniform) | EM-24 |

**Direction — where to look when everything you can see is correct**

| rule | one line | enforced by | full text |
|---|---|---|---|
| EM-18 | backtrace: debug UP the chain, not forward from the symptom | prose | EM-18 |
| EM-19 | one quantity, one landmark | prose | EM-19 |
| EM-20 | the instrument must move with the membrane, and must not keep its own copy | the witness gates | EM-20 |
| EM-23 | check the generator before you believe the witness | CHECK order: `grow.py` before `chain_witness.py` | EM-23 |

**Grown-world doctrine**

| rule | one line | enforced by | full text |
|---|---|---|---|
| EM-21 | in a grown world, an authored phenotype is the defect | prose | EM-21 |
| EM-22 | the serial is the place in time, not the place in the tree | `story/timeline.py` | EM-22 |

**The human terminal**

| rule | one line | enforced by | full text |
|---|---|---|---|
| EM-11 | the operator's observations outrank your model | the operator | EM-11 |
| THE DYAD | physics produces a NUMBER, the human a TERM; an LLM is never a terminal | `ChimeraEngine/human_messenger.py`, the engine's `prove` gate | `ChimeraEngine/ONBOARDING.md` |

**The operator's rulings** — `Chimera/docs/THE_GROWTH.md` (2026-07-31, + the 2026-08-01
control ruling): everything is a sample you train · research connects physics to training
data (download the measured data FIRST) · the physics is the code · the natural world is all
of the known · the standard of definition is measured capture (D0–D4) · nothing is true
until the instrument has been run on a known subject.
