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

The full set — 25 rules, each with the failure that earned it — is
**`Chimera/docs/EXPERIMENTAL_METHOD.md`**. Rules 2–11 are about not fooling yourself while
*debugging*; 12–17 while *reporting*; 18–21 about *direction* (where to look when everything you
can see is already correct); 22–25 about *order*, about instruments that need instruments, and about the difference between a number you transported and one you derived.

Two other gates run beside this one:

    python story/folding.py audit          # units: what a law may connect to
    python tools/methodology_gate.py       # every membrane against the workflow
    python tools/slider.py                 # move a free number; whatever does not move is typed
