# TRUST-TOOLING 20260918 — Rule-0 work record (filed BEFORE code)

Lane: `lane/trust-tooling-20260918`. Base: `origin/master` tip `4b047609c8f51782da10c9d63726f10ddb525cbc`.
Date: 2026-09-18. Python: `E:\PythonChimera\.venv-hy3d\Scripts\python.exe`.

## 1. THE REVIEW HARNESS (primary)

**STATEMENT.** The six static checklist items that have actually caught real
bugs in this repo's history — (a) frozen-reference bit-exactness presence,
(b) falsifier-as-test presence, (c) receipt-schema conformance,
(d) scope-honesty vs not_qualified/limits, (e) evidence-count invariance
(11), (f) graph-JSON merge replay traces — can be mechanized as deterministic
`git diff` + `grep` + `json.load` checks in
`tools/science_funnel/review_candidate.py` that reproduce the statically
visible part of the already-reviewed Coulomb-friction findings without
inventing findings on clean diffs.

Someone could disagree: a reviewer could hold that F1 (inverted exact-rest
sign), F2 (unexercised critical-mu falsifier), F3 (missing cone/J^T guard
assertions) and F4 (stale live scope string) are judgement calls no static
grep can reproduce, or that any static harness necessarily false-positives on
docs-only diffs.

**PREDICTION (not yet measured).** Running the harness with
`--base a6e6acf2 --candidate e9c7bd5e` (the exact independently-reviewed
friction range recorded in
`tools/science_funnel/validation/coupled_friction_20260917/receipt.json`
`independent_review.method`) reproduces the statically detectable subset of
the known findings F1–F4 (receipt contains F1–F4 only; the briefing's "F1–F6"
is recorded here as a scope discrepancy — F5/F6 do not exist in that receipt;
the fixes receipt `coupled_friction_fixes_20260917` confirms "findings
F1-F4"): at minimum F2-shape (critical-mu falsifier declared but trial pair
{0.05,0.8} both stick+slide), F3-shape (cone/J^T consistency without guard
assertion), F4-shape (live scope string still frictionless-era). F1-shape
(exact-rest sign) is a semantic inversion only a solver-seam test can bite;
the harness predicts at most CANNOT-VERIFY for it, never a false PASS claim
beyond its static scope.

**FALSIFIER (named before the run).** The theory LOSES if either:
(1) on the friction range the harness returns all-PASS (it saw nothing it
should have seen statically), or
(2) on a trivial docs-only diff (e.g. a one-line README/comment change with
no engine, test, receipt or graph-JSON touches) it returns any FINDING
(false positive). Both runs are recorded with verdict.json artifacts. A clean
PASS on the docs-only diff with zero findings is required; any invented
finding kills the harness design.

Scope-honesty note: the harness never claims beyond static visibility. Semantic
correctness (does the sign fix oppose impending slip, does mu=0 stay
bit-exact) stays with the native suite + independent review. The harness only
checks presence/traces: frozen references present, falsifier-shaped tests
present, receipt schema valid, scope bounded by limits, evidence count
pinned, merges replayed.

## 2. THE STORE WATCH (secondary)

**STATEMENT.** The single unreproduced `TypeError: 'set' object is not
subscriptable` death at `tools/creature_graph/store.py` in `relate()` is a
corrupt edge — a `set` object sitting in `self.relations` where a dict was
expected — entering via an unguarded path (direct `g.relations = ...`
assignment in `store.load`, `graph.graph_from`, `agent_fleet/graph_workflow`,
or a text-merged graph JSON reloaded without validation), not a flaw in the
`stem_ordinal` rid logic itself; a defensive type guard raising a named
Refusal plus a bounded stress will either reproduce the shape or bound it.

Someone could disagree: the failure could be a transient interpreter/race
artifact, or the rid-ordinal set logic itself (`used = {r["rid"] ...}`)
subscripting a set, with no corrupt edge at all.

**PREDICTION (not yet measured).** A stress harness of >=200 rapid
in-memory + file-roundtrip builds with varied record sets (including
adversarial injection of a set edge, list edge, and string edge) will:
(a) NOT reproduce the failure under honest API use (all-green), but
(b) WILL reproduce the exact `TypeError: 'set' object is not subscriptable`
at the `used = {r["rid"] ...}` line when a set is injected into
`self.relations`, proving the failure shape and the guard's trigger.

**FALSIFIER / EXIT.** The anomaly is NEVER silently closed:
- If honest-use stress reproduces it, the theory's mechanism is wrong — fix
  minimally at the true site + regression test, record the measured trigger.
- If honest-use stress does NOT reproduce after the bounded, recorded effort
  (attempt count + coverage logged), harden `relate()` defensively with a
  guard raising a named Refusal (`store_corrupt_relation_edge` naming the
  offending index/type/keys) + a unit test for that guard, and record
  UNREPRODUCED-WITH-CAUSE in this record and the commit message. The guard
  must not change honest-path behavior (all existing suites green,
  graphify HONEST, evidence 11 unchanged).

## Evidence-count / qualify pins (pre-run)

- Funnel suite: `python -B -m unittest discover -s tools/science_funnel/tests` must be green.
- Graphify: HONEST.
- Evidence count: 11 unchanged.
- Publish: push ONLY `lane/trust-tooling-20260918`, verify remote tip, `Agent: GLM 5.3` trailer, NEVER master.
- Collisions: if `origin/master` moved, rebase, take upstream on graph JSONs, re-run idempotent scripts; never rebase under a live suite.
