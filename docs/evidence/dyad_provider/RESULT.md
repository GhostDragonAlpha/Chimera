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

- Fail-closed refusals by name: PASS (T1-T4, T8).
- Full evidence retention incl. exact prompt + raw response: PASS (T5).
- No numeric facts from visual text: PASS (T5/T6/T7: tagged only; verdict
  statuses FAIL/NOT_CLAIMED/INCONCLUSIVE).
- Provider selection by configuration, no fallback: PASS (T8).
- Local adapter retained, not bypassed: PASS (T9 — boundary explicitly named;
  live wiring remains in ChimeraEngine/senses.py under the protocol).

## Explicitly NOT claimed

- Actual visual capability of any provider (no live vision run in this task).
- Remote transport execution (contract + refusals defined; HTTP wiring is
  deployment-lane work with its own evidence).
- Changes to ChimeraEngine/senses.py (separate READY task
  dyad-resident-identity-01 owns that scope).

## Commands

- `python -m unittest tools.test_dyad_provider` (slot-05 worktree) → 11/11 OK.
