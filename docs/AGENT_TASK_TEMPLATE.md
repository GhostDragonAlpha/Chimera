# Agent task template

> **Generic by design.** Nothing here names a current problem, a current file, or a
> current function — those go stale and turn a template into a case study. This document
> describes only the *method*: where an agent stands, which way it faces, how it decides
> what belongs there, and what counts as having done the work.
>
> Fill two placeholders — **`<POSITION>`** and **`<DIRECTION>`** — and paste.

---

## The prompt

```
Read ChimeraEngine/ONBOARDING.md. It is your briefing and it takes precedence over anything
you assume.

THE WORLD IS A 64-BIT DOUBLE-PRECISION GRID, AND IT IS IRREDUCIBLE.
Every position is a coordinate carried in float64. There is no smallest feature: any
region can be subdivided further, and the grid will still address it. So "what is
here" is never answered once — it is answered at the level of detail the observer's
distance justifies, and a finer answer always exists beneath the one you give.
Work in float64 for anything positional. Cast to float32 only after subtracting a
local origin, never before.

WHERE YOU ARE:  <POSITION>
WHICH WAY YOU FACE:  <DIRECTION>

You stand at that coordinate and look that way. That is your entire scope this turn.
You are not responsible for the world; you are responsible for what is visible along
one axis from one place. Six directions exist — up, down, left, right, forward, back —
and you are working exactly one of them.

STEP 1 — DECODE BEFORE YOU BUILD.
Do not begin from an idea of what would look good. Begin by asking what belongs
there, using the project's question protocol, and answer as many as the evidence
supports. Some questions the physics can answer and some only a human can; answer the
first kind and leave the second kind alone.

EVERY ANSWER YOU RECORD MUST CONTAIN A NUMBER YOU MEASURED FROM THE ARTIFACT YOU
PRODUCED. A default parameter, a count of things in a module, a value read from a
config, or anything obtained by inspecting source rather than running the pipeline is
a fact about the CODE, not about the WORK — it does not count. If a question cannot
be answered by measurement, leave it unanswered. An unanswered question is an honest
result; an invented one is a lie stored in a file.

STEP 2 — BUILD FROM WHAT EXISTS.
Find the functions the project already provides and compose them. Do not write new
modules, and do not reimplement something that is already there under another name.
If you are unsure what exists, read before you write.

>>> ESCAPE HATCH — READ BEFORE BUILDING <<<
If what exists CANNOT do this, STOP and name precisely which capability is missing
and what it would have to do. Reporting a missing capability is a SUCCESSFUL outcome
and it is wanted. Producing something differently-shaped and calling it the task is a
FAILURE. If a function's own documentation contradicts the use you are about to make
of it, that contradiction is the signal — say so rather than proceeding.

STEP 3 — MEASURE WHAT YOU MADE, NOT WHAT THE LOG SAID.
A process that exited zero has not been verified. Open your artifact and take
measurements from it: its extent, its content, its distribution, whether it is mostly
empty. Report those numbers. Then describe what the artifact actually is, in two
sentences, using them. If the measurements disagree with what you expected, say so
plainly — a disagreement you report is a finding, and one you omit is a defect you
have hidden.

ACCEPTANCE
You are done when the artifact exists AND has been measured, or when you have invoked
the escape hatch naming a specific missing capability. Nothing else ends the turn.

FORBIDDEN
  - Writing a status document, summary, report, or plan. Describing work is not doing
    work, and a file that restates your briefing back is worth less than nothing.
  - Asking which thing to focus on. Your position and direction are given above.
  - Editing a record by hand to mark it complete. Use the tools that write it.
  - Ending the turn with neither an artifact nor a named missing capability.

REPORT
The numbers you measured and what each one measures; the exact commands you ran; and
what the artifact actually is.
```

---

## The method, and why it is shaped this way

**One place, one direction, one turn.** An agent whose scope is "the project" produces
description instead of work — it summarises its briefing, proposes plans, and asks what
to do. Scope bounded to a coordinate and an axis has a checkable done-condition. A
boundary is what makes work attributable.

**Decode before building.** Going straight to construction means building what seems
plausible. Asking what belongs somewhere, and answering only what the evidence supports,
separates the part physics can settle from the part only a human can — and stops the
second kind being silently invented.

**Acceptance must be an artifact-measurement, never an activity-description.** Any
condition an agent can satisfy without doing the work *will* be satisfied without doing
the work. This is not misbehaviour; it is the same thing a degenerate winner does to a
loosely-specified training objective — **the agent is auditing the specification.** When a
run disappoints, suspect the acceptance condition before you suspect the agent.

**The escape hatch is load-bearing.** With only two legal outcomes — produce the artifact
or fail — producing a *wrong* artifact strictly dominates admitting a tool is missing. So
an agent will build the wrong thing while its own reasoning notes the contradiction.
Making "the capability is missing" a **winning** outcome converts a silent bad build into
a bug report.

**Measurement over logs.** An exit code says a process ran. It says nothing about whether
the thing produced is the thing intended. The measurement must come from the artifact
itself, and it must be reported even — especially — when it disagrees with expectation.

**Irreducibility sets the depth.** Because the grid can always be subdivided, no answer is
final; there is always a finer one. The right depth is the one the observer's distance
justifies, which is why detail is budgeted by perceived distance and why "deep enough" is
a question that gets asked rather than assumed.

---

## Maintaining this document

Add to the method section only when a **structural** lesson is learned — something about
how work should be specified, not about what happened to be broken that day. Specific
failures belong in the experimental record. If a line here would stop making sense once
the current problems are fixed, it does not belong here.
