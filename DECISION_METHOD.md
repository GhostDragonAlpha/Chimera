# Decision Method — The agent drives itself

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
> **[docs/THE_LAW.md](docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> No questions. No reports. The method is the lever.
> When in doubt, run the decision tree. When the tree terminates, the session ends.

## The Decision Tree

This is a hard fallthrough. Start at 1. If it produces work, execute it. If it doesn't, fall through to the next. If all fall through, the session is complete.

### 0. Check the 40-question depth

Before touching any feature, check its 40-question document:

```
python -m core.forty_questions show <feature_name>
```

- If **unexplored** (0-9 answered): the feature needs investigation. Run the 40 questions, fill answers, train.
- If **explored** (10-19): basic understanding exists. Decide whether to go deeper or start building.
- If **adequate** (20-29): well-understood. Decompose into sub-rungs if needed.
- If **deep** (30-40): fully understood. Feature is complete. Do not retrain.
- If **no document exists**: the feature hasn't been created yet. Generate one first.

The 40-question document is stored in `docs/forty_questions/<name>.json` and the DNA graph. Query it:

```python
from core.forty_questions import check_depth
depth = check_depth('feature_name')
```

### 1. Read the roadmap

Open EMERGENCE_ROADMAP.md. Find the first item whose status is not DONE and not BLOCKED.

- **DONE** → mark it, move to the next.
- **BLOCKED** → note the blocker, move to the next.
- **Not started or in progress** → execute it using the formula (CONSTRAINT → EXISTING → WALLS → WORK → JUDGE).
- **No items found** → fall through to 2.

### 1.5 Query the graph for Mirror-weighted gaps

Before starting new work, query the DNA graph for the highest-Mirror-weighted gap:

```python
from core.forty_questions import graph_context
ctx = graph_context()
print(f'{ctx["n_gaps"]} gaps, {ctx["n_mirror"]} Mirror connections')
```

Prioritize gaps by Mirror weight: direct Mirror features > enabling features > orthogonal features.

The auto-decomposer can do this automatically:
```
python -m core.auto_decomposer
```

If the graph shows no gaps, the current rung is complete at its resolution level.

### 2. Re-approach blocked items

For each blocked item, try ONE alternative approach to satisfy the same CONSTRAINT. The formula says test the rule, not the object. If the object can't be MCP-spawned, test the rule a different way.

- If the constraint is "player can collect resources" and APickupActor can't be spawned, implement proximity-based collection in C++ (like the shelter fix).
- If the constraint is "shelter refills O2" and the collision trigger doesn't work, implement distance-based checking in Tick (already done).
- Each item gets ONE alternative attempt. If that also fails, mark it BLOCKED and fall through.

### 3. Move to the next ladder rung

Items are ordered by the compositional ladder. If Item N is blocked, work Item N+1. The ladder is:

```
body (survival) → biome (resources) → shelter (threshold) → form (geometry)
→ social (NPC needs) → economy (fabricator) → narrative (beacon)
```

- Each item that is not blocked gets one full formula pass.
- After the pass, re-check Item N to see if the blocker has resolved.
- If no items are available (all blocked or done), fall through to 4.

### 4. Work the audit backlog

Open EMERGENCE_ROADMAP.md's audit backlog section. Every feature previously built with the old method (maximize/minimize, authored forms, placed objects) that has a recorded human judgment of failure:

- Pick the oldest unaddressed audit item.
- Apply the formula: retrain with walls-only constraints at the right definition level.
- Record the new result. Mark the audit item as addressed.
- If no audit items remain, fall through to 5.

### 5. Train the next untrained rung

The compositional ladder has rungs that are not yet in EMERGENCE_ROADMAP.md. Check what's been trained vs what's pending:

- Check core/trainables/ for existing domains.
- Check docs/objectives/ for existing objectives.
- If a domain exists but was trained with maximize/minimize (old method), it's an audit item (go to 4).
- If a domain has never been trained (e.g., habitat_form, npc_needs, economy_exchange), train it:
  1. Write the domain (seed/mutate/measure) with walls-only constraints
  2. Write the objective (no maximize/minimize — only walls)
  3. Train
  4. Decode to game artifact
  5. Write beat to verify
- If no untrained rungs remain, fall through to 6.

### 6. Run the rehearsal engine

```powershell
python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json --decide
```

- Execute the decision it produces.
- If rehearsal produces nothing or only `capable_only` items, fall through to 7.

### 7. The season is complete

- Run `python -m core.dream_loop` to distill lessons.
- Run `python -m core.history_book search --query "<anything>"` to update the book.
- Commit everything.
- The session ends. No questions. No reports. The user sees the commit log and the updated roadmap.

---

## The Fallthrough Invariant

The decision tree ALWAYS terminates. Every branch either produces work or falls through.
When all branches have fallen through, there is nothing left to do in this session.
The session ends. No questions.

---

## Ties and Ambiguity

When the tree could send you to multiple equal branches:

- **Item vs item** → lower rung wins (closer to the body).
- **Fix blocker vs train new** → fix blocker wins (completes work already started).
- **Audit vs train** → audit wins (fixes old method before building new).
- **Rehearsal vs anything** → rehearsal wins (it's the widest look at the graph).
- **Same priority** → alphabetical by feature name.
- **Cannot decide** → pick the one with the shortest expected work time. If still tied, pick the first in the file.
