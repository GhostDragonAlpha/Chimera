# ARCHIVE — documents that were superseded, kept because deleting them loses the record

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **Archived 2026-08-02, during the documentation consolidation.** Nothing here was thrown away for
> being wrong. Each was either a description of a retired pipeline, or a *copy* of rules that live
> somewhere else — and a copy is exactly how three documents drift into three different truths.
>
> **The repo's own rule, from `THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md`:** *"THE CONTRACT's rules
> were duplicated here, in `AGENTS.md`, and in `CLAUDE.md`. **CLAUDE.md owns them. Three copies is
> why all three drifted; the copies are gone.**"* One copy survived that cleanup and is now here.
>
> **And from `docs/THE_ORDER.md` §E, on why this repo drifts at all:** *"a new thing was added
> BESIDE the old thing instead of replacing it… The remedy is not more documentation — it is
> deleting the losers once a winner exists."*

**Everything load-bearing in these files was read out first and placed in `docs/THE_PIECES.md`
(the 124-piece inventory) before anything moved.** Where a piece is still live, it is in
`docs/THE_WORKFLOW.md`.

| file | what it was | why it moved | what was rescued from it |
|---|---|---|---|
| `FOUNDRY_WORKFLOW.md` | the repo-root `WORKFLOW.md` — the Foundry design engine, over UE5 MCP plumbing | its build half drives `UnrealEditor.exe` through MCP port 3000; the Unreal pipeline was retired 2026-07-23 | **its design half was the best find of the consolidation** — the 22 question categories (NODE/EDGE/MIRROR/META), the council's seven gates, and THE RHYTHM. All extracted into `THE_WORKFLOW.md` §S1, which had been orphaned for exactly the want of them. See `THE_PIECES.md` §15 |
| `WORKFLOW_RULES.md` | "every rule of the project workflow in one place" | it names its own source of truth in its second line: *"Source of truth is CLAUDE.md + the enforcement code."* A fourth copy of the contract | its live rules are in `CLAUDE.md` and `THE_WORKFLOW.md`; the gate table is `THE_WORKFLOW.md` §8 of `THE_PIECES.md` |
| `WORKFLOW_SPEC.md` | the full UE 5.8 / C++20 / Win64 system specification | describes the generator, the DSL→C++ pipeline and the editor bridge, all retired | nothing live — the DSL survives and is documented in `tests/dsl_grammar/` |
| `UE_UNTANGLING_SCOPE.md` | the scope that guided removing the UE backend | its own banner: *"BACKEND REMOVED 2026-07-24… kept as the record"* — a record of a finished job | the record itself, which is why it is archived and not deleted |
| `HANDOFF.md` | a handoff for the Gaussian Foundry's educational-canyon UE5 demo | a completed deliverable in a retired engine | nothing live |

---

## The rule that governs this folder

**A claim about INTENT does not rot. A claim about STATE rots by construction.**

Every file here is mostly *state* — what existed, what was wired to what, which port the editor
listened on. That is why they went stale rather than staying useful, and why the surviving
documents point at commands instead of copying their output.

Nothing here should be built against. Read it to understand how something came to be, never to
learn how something works now.
