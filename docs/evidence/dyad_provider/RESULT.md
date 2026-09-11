# DYAD_PROVIDER — Result record (dyad-provider-interface-01, gen 1, slot 5)

## Implemented

- `tools/dyad_provider.py`: request/response contract, capability ladder
  (`no_vision` / `none` < `frames` < `movie`), fail-closed capture integrity
  (`capture_missing`, `capture_hash_mismatch`), deterministic non-leading
  prompt builder, evidence-retaining response (exact prompt, raw response,
  served identity or named uncertainty, capture identities, finish status),
  verdict mapping (model agreement = INCONCLUSIVE, never acceptance; numeric
  mentions tagged `unverified_numeric_mention`), provider adapters
  (subagent callback / remote HTTPS with env-var auth / local senses retained
  and lazily imported), configuration-based selection with no fallback.
- `tools/test_dyad_provider.py`: 11 synthetic contract tests covering every
  preregistered falsifier.
- `docs/THE_DYAD_PROTOCOL.md`: dated append-only section declaring the
  interface (history untouched).

## Prediction check

- Fail-closed refusals by name: PASS (validation, integrity, capability
  ladder, provider-kind selection, malformed-subagent-callback refusals).
- Evidence retention incl. exact prompt AND raw response verbatim: PASS
  (asserted: `exact_prompt == seen prompt`, `raw_response == callback raw`).
- No numeric facts from visual text: PASS (mentions tagged only; verdict
  statuses FAIL/NOT_CLAIMED/INCONCLUSIVE; PASS unreachable).
- Provider selection by configuration, no fallback: PASS (unknown kind and
  non-HTTPS endpoint refused by name; bogus temporal capability refused at
  construction).
- Local adapter retained, not bypassed: PASS (boundary explicitly named; live
  wiring remains in ChimeraEngine/senses.py under the protocol).

## Independent review (REQUEST_CHANGES -> addressed on-branch)

First independent pass returned REQUEST_CHANGES with two MAJORs (malformed
subagent callback crashed unnamed with no retained evidence; RESULT.md
overstated coverage: raw_response unasserted, one-image-loop claimed without
test) and four MINORs. All addressed on this branch: callback result shape
validated with named `subagent_callback_malformed:*` refusals; `raw_response`
retention asserted; capture index set must be exactly 1..n; temporal
capability constructor-validated (`invalid_temporal_capability:*`), with
constructor-only semantics documented (the ladder test's explicit `none` pin
is the single documented mutation for testing); Remote temporal validated;
frozen-dataclass dict fields documented as read-only construction inputs;
"lazily imported" wording corrected (nothing imports senses — the boundary is
the named NotImplementedError). The one-image-per-call LAW is unchanged prose
of the local eye's own protocol; this interface never loops on the local
adapter (its `_review` is a named boundary), so no untested loop is claimed.

## Explicitly NOT claimed

- Actual visual capability of any provider (no live vision run in this task).
- Remote transport execution (contract + refusals defined; HTTP wiring is
  deployment-lane work with its own evidence).
- Changes to ChimeraEngine/senses.py (separate READY task
  dyad-resident-identity-01 owns that scope).

## Commands

- `python -m unittest tools.test_dyad_provider` (slot-05 worktree) → 14/14 OK
  (after review-pass-2 amendments: index-set validation, malformed-callback
  named refusals, raw-response retention assertion, constructor capability
  validation, remote-unwired boundary).
