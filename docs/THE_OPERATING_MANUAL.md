# THE OPERATING MANUAL — how any agent works in this project

Written 2026-08-28, operator decree: "set up the documentation and the workflow
so weaker agents can operate in this project." Companion to
`docs/THE_TRIANGLE_GUIDE.md` (the domain laws — read it first) and
`docs/THE_MASTER_LIST.md` §11 (the main-agent method). This manual is the
WORKFLOW: how a task arrives, what you may touch, how you prove, how you hand
back. Followed correctly, a weaker agent produces work the operator can trust
without re-checking every line. Skipped, the same agent produces stubs,
placebos, and torn legs.

---

## 1 · Who owns what (the boundaries are hard, not polite)

| Surface | Owner | You may |
|---|---|---|
| `docs/THE_MASTER_LIST.md` | the main agent (kimi) | never edit |
| `docs/THE_ARTISTS_SOLID.md` | construction agents | append membranes + measured results only, never rewrite history |
| `docs/THE_TRIANGLE_GUIDE.md`, this manual | main agent | never edit |
| `.tmp/` | you | all scratch lives here; nothing in `.tmp/` is a deliverable by itself |
| `agent_logs/<yourname>/` | you | your reports |
| git commits / pushes | main agent (unless the operator explicitly grants you commit rights) | never commit unless granted |
| the Vulkan engine, ports 8090/8088, any running process | main agent / operator | never kill, restart, or POST to unless your task says so |
| `tools/gsplat` (submodule) | nobody right now | never touch |

If a task requires crossing a boundary, STOP and say so in your report. Do not
route around a boundary because the task seems to need it.

## 2 · The loop (six steps, in order, none skippable)

1. **READ.** Your task lists the read-first files. Read them all before
   writing a line. The laws in the Triangle Guide name failures you have not
   seen yet; the membrane docs name numbers you must not re-derive or
   contradict.
2. **MEMBRANE.** Before any build, write the membrane (Rule 0): a STATEMENT
   someone could disagree with, a PREDICTION you have not measured, and
   FALSIFIERS named *before the run*, each one mechanical (a number, a count,
   a comparison) — never "looks better". Append it to the task's home doc.
   No falsifier, no build.
3. **BUILD** in `.tmp/`. Reuse the known-good machinery your task names.
   Every constant is DERIVED (show the derivation), CHOSEN-UNVERIFIED (name
   the experiment that will measure it), or forbidden. There is no fourth kind.
4. **MEASURE.** Run the falsifiers and print the table. Verify each check can
   fail: a check that can't fail is a placebo (the `hasattr` trap — see the
   Guide §6). View every render you claim about with your own eyes.
5. **REPORT** to `agent_logs/<yourname>/`: root cause, numbers, falsifier
   table with PASS/FAIL per item, and the honest negatives — what is stubbed,
   what was measured about a superseded quantity, every retracted experiment
   with its reason. A falsifier that fires is a result. Never widen a bound
   after measuring.
6. **HAND BACK** the paste-back (below). The main agent records verdicts in
   the master list and commits. Your job ends at the paste-back.

## 3 · The paste-back format (always, exactly this shape)

```
1. Falsifier table: <item> -> PASS/FAIL (<measured number>)  [one line each]
2. Files written: <paths>
3. Falsified/retracted: <what, with the number that killed it>
4. Open items: <what stays unmeasured or unbuilt>
5. Boundary hits: <anything you needed but weren't allowed to touch>
```

## 4 · Blocked is earned

Bare "blocked" is forbidden. Before reporting blocked: try at least 5
materially different approaches, record each attempt and its outcome in your
report, then report blocked WITH the cause and the evidence. If the blocker
is a boundary (§1), that is a boundary hit, not a blocker — report it
immediately instead of spending attempts.

## 5 · The task-envelope (what a legal task prompt contains)

The operator or main agent hands you a prompt with all of these. If one is
missing, ask before starting:

1. **Objective** — one sentence, measurable.
2. **Isolation boundary** — which of §1 applies, tightened for this task.
3. **Read-first list** — exact paths.
4. **The problem, measured** — the evidence that exists already, with numbers.
5. **Rule-0 frame** — the statement/prediction to test, or the instruction to
   write your own membrane first.
6. **Falsifiers** — mechanical, named before the run.
7. **Known-good machinery** — the files/values that already work (mesh paths,
   sets, axes, cameras, checkers). Never reinvent these.
8. **Deliverables** — the files and the paste-back.

## 6 · The template (copy this shape for any construction task)

```
TASK: <one measurable sentence>

You are working in E:/PythonChimera (Windows, Git Bash). Use
.venv-hy3d/Scripts/python.exe. Hard isolation: <boundaries — no commits, no
process kills, no engine, scratch in .tmp/ only, ...>.

Context you must read first: <paths>.

The problem (measured, not guessed): <evidence with numbers>.

Rule 0 first — write the membrane BEFORE code (append to <home doc>):
STATEMENT / PREDICTION / FALSIFIERS (each mechanical; include the checks this
project already trusts — the real intersection test from .tmp/tri_hinge2.py,
TORN-SHEET, the stretch metric, the dyad one-picture-per-call rule).

Known-good machinery to reuse, do not reinvent: <paths and values>.

Honesty rules: honest negatives with numbers; never widen a bound after
measuring; never claim a render you haven't viewed yourself.

Deliverables: membrane text with measured numbers; <scripts>; <renders>;
report at agent_logs/<you>/<task>.md.

When done, paste back: the falsifier table, files written, what you
falsified, what stays open, boundary hits.
```

A worked example of this envelope, filled for a real task (the ARAP knee-fold
skin), is in the session record of 2026-08-28 — the pinch-band prompt.
