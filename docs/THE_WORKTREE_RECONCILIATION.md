# Worktree reconciliation contract

This tool is a read-only inspector for a checkout whose ownership and task
authority are supplied by the controller. It does not claim a slot, change a
branch, alter the index, or make a dirty checkout safe.

## Preregistered contract

**STATEMENT:** Given a verified Git checkout, expected `HEAD`, repeated task
scopes, and an evidence root, the inspector will classify every observed
tracked or untracked path as evidence-only, source requiring revalidation,
historical evidence modification/deletion, outside-scope, or path escape.

**PREDICTION:** A temporary Git checkout with only a newly added file below the
declared evidence root will produce an evidence-only classification; a fast-
forward `HEAD` containing only that evidence remains safe to continue. A
changed source file, a changed historical evidence file, a scope escape, or a
divergent `HEAD` will produce a named refusal classification without changing
bytes.

**FALSIFIER:** Any test where the inspector mutates the index/worktree,
silently omits a status path, treats a source addition as evidence merely
because it is new, follows a symlink outside the checkout, or reports a
stable safe result when `HEAD` or the index changes during inspection.

The expected commit is the comparison baseline. A fast-forward from it is
accepted only when the committed delta is evidence-only; a divergent history
is refused. Neither result grants controller authority, proves ownership, or
approves a task. Existing staged, unstaged, untracked, and historical evidence
bytes remain untouched.

The motivating case is a worker whose slot-02 `HEAD` advanced with one commit
containing two files from an evidence run while a second evidence run had two
files staged. Reconciliation must preserve all four evidence files, classify
the committed additions as evidence-only, and leave any source change
requiring revalidation.

## Interface and classifications

```text
python tools/agent_fleet/worktree_reconcile.py \
  --repo CHECKOUT --expected-head FULL_SHA \
  --scope PATH --scope PATH \
  --evidence-root PATH
```

`--repo` must resolve through Git to the requested checkout. `--scope` may be
repeated and is compared lexically and physically inside that checkout.
`--evidence-root` is the only location where a newly added path can be
evidence-only. A pre-existing or deleted path below `docs/evidence/` is
historical evidence and requires revalidation. A source file is never promoted
to evidence by its filename or by being newly added.

The JSON result includes the observed head, all status paths, classifications,
and a stable flag. It is an observation, not a transition: controller task and
generation checks remain separate requirements.

Ignored files, including Python caches inside a task directory, are reported
as `preserved_ignored` and do not block this tracked-source comparison. They
are not validated runtime inputs: build/runtime provenance must account for
generated or ignored files that it actually consumes. The tool never deletes
caches to manufacture a clean result. `stable` compares observed HEAD and
index snapshots; it is not a lock against subsequent writes.

## Continue after a changed head

1. Refresh the live controller snapshot. Continue only the current owned task,
   generation and provisioned branch; Git author names cannot supply authority.
2. Run the inspector against the last checked revision and declared task paths.
   An evidence-only fast-forward with preserved staged work does not require
   human confirmation. Inspect the staged diff, retain both runs, commit only
   the intended evidence, push normally, and submit the resulting exact head.
3. If implementation changed, inspect it and rerun the relevant acceptance
   tests before updating the checkpoint. A named revalidation result is work
   to perform, not an instruction to ask the operator whether to continue.
4. If the read was unstable, reread the same worktree and controller. For a
   changed claim, divergent history, deleted evidence or overlapping writes,
   preserve the state and route the precise conflict to the lead through the
   controller. Continue independent owned work while it is reconciled.

Never reset, clean, force-push, discard a second run as redundant, or submit a
different head under a stale review to make the checkout match an old prompt.
An actual stop/scope instruction from Alan still takes precedence.
