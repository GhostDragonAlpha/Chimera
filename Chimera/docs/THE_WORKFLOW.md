# THE WORKFLOW — moved

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> # → **[`docs/THE_WORKFLOW.md`](../../docs/THE_WORKFLOW.md)**

**There were two files with this name and they described two different methods.** This one held the
FORMULA (2026-07-24, `PROVE(X)` through S0–S7, sealed); the other held the CHAPTER (2026-07-28,
membranes in `story/`). The second superseded the first in practice while this one stayed labelled
canonical — which is this repo's own named drift pattern: *a new thing added beside the old thing
instead of replacing it.*

They are now **one sequence**, with the join that was missing between them: the formula's S4 read
`MEASURE(TRAIN(PROGRAM(V)))` and contained **no DERIVE**, which is the hole a four-variant parameter
sweep fell through on 2026-08-02. DERIVE is now S4 and everything after it moved down one.

Every idea from this file was read out and placed on the inventory before it was replaced —
**`docs/THE_PIECES.md`**, which also marks the nine pieces that were written down here and are done
by nothing.

## Where each part of this file went

| what was here | where it is now |
|---|---|
| the one-page loop, the two roles | `docs/THE_WORKFLOW.md` — the one page, and §0 |
| §1 the verb is PROVE | `docs/THE_WORKFLOW.md` §3 |
| §2 one camelCase term, setting-first | §2 (and the six directions that decide *which*) |
| §3 the equation S0–S7 | §3, restaged as **S0…S8 with DERIVE inserted at S4** |
| §4 saturation is measured | §3 · S2 — still orphaned, and now listed as such |
| §5 PROGRAM / TRAIN / DECIDE | §3 · S3 and S5 |
| §6 the black-hole shape | `Chimera/docs/THE_FORMULA.md`, which owns it in full |
| §7 the gates | `docs/THE_PIECES.md` §8 — the full gate table with wiring status |
| §7b the six rules that decide whether a result is real | `Chimera/docs/EXPERIMENTAL_METHOD.md` rules 12–17 |
| §8 the reading order | `docs/THE_WORKFLOW.md` §8 — the map |
| §9 the build as it stands | **deleted deliberately.** It was STATE in prose, and it had gone stale: it drew `theStory → theSolarSystem → theStation → theGoal`, a tree that does not exist on disk. Run `python Chimera/core/grow.py --read` and `python tools/methodology_gate.py` |
| §10 the honest bounds | `docs/THE_WORKFLOW.md` §9 |

**The deep docs this file used to introduce are unchanged and still worth reading:**
[`THE_METHOD.md`](THE_METHOD.md) (the question-tree, the terminals, the lenses) ·
[`THE_FORMULA.md`](THE_FORMULA.md) (the equation, the dyad, the black hole) ·
[`THE_LINE.md`](THE_LINE.md) (program / train / decide).
