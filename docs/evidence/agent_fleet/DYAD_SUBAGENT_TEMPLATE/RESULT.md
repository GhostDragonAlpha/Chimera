# dyad-subagent-template-01 result (2026-09-11, lead lane)

Task: `dyad-subagent-template-01` generation 1, slot 5, worktree
`E:\ChimeraWork\slot-05`, base `7e7d8466` (integration tip). Preregistration
commit `ea8b4fe0` precedes all results recorded here. Operator direction:
HUMAN feedback `d015187c`.

## Prediction outcomes

| # | Prediction | Outcome | Evidence |
|---|---|---|---|
| 1 | driver validates `still` request (1 capture, sha256 verified pre-spawn) | PASS | `request_spec_live-raised-gamma0-20260911.json`, plan output (capture sha256 53e994e08d8e...) |
| 2 | spawned subagent reads the capture and returns a parseable structured report | PASS (after one retained correction) | `subagent_report_live-raised-gamma0-20260911.txt` verbatim |
| 3 | provider assembles DyadResponse; verdict at most INCONCLUSIVE; numerics tagged | PASS — INCONCLUSIVE, 4 tagged mentions | `dyad_response_live-raised-gamma0-20260911.json` |
| 4 | exact prompt, raw response, capture identities, served-identity note retained verbatim + dyad log append | PASS | same JSON + `dyad_log.jsonl` |

## Falsifier events (retained, both corrected without weakening)

1. `plan` NameError (driver comprehension bug) before any review run — fixed;
   no contract path involved.
2. First `assemble` refused `subagent_callback_malformed` — the provider's
   fail-closed contract fired because the report parser accepted only bare
   section headers while the template emits `CONCLUSION: <value>` inline.
   Retained in `failed_assemble_attempt1_20260911.txt`; parser fixed to
   accept both forms; the refusal itself proves the reviewed contract
   executes on this path.

## Verdicts (kept separate)

- Provider path: **EXECUTED LIVE with retained evidence** (subagent class,
  GLM 5.3 Flash vision per harness declaration).
- Content-level visual acceptance (raised-state geometry etc.): NOT_CLAIMED —
  the reviewer's own uncertainty statement is retained; single-still height
  ambiguity is consistent with the historical record.
- Local eye / GPU / model resources: untouched; `tools/test_dyad_provider.py`
  14/14 OK at this branch (regression, unmodified).

## Timing observation (context, not a gate)

Spawn-to-report ~46 s for the single-still review, versus minutes-per-call
for the local 27B eye — consistent with the operator's expectation; not
claimed as a benchmark.

## Correction (2026-09-11, generation 2 — review finding landed on-branch)

Independent review of head `01080c5f` (APPROVE_WITH_FOLLOWUPS) found the
driver's hash verification tautological: a spec-declared capture sha256 was
ignored (always recomputed), so `capture_hash_mismatch` was unreachable and
the template doc's "verifies every capture sha256" overstated — the hash was
computed and recorded, not verified against an independent declaration. The
reviewer proved it empirically with a mutated PNG.

Fixes at generation 2 (worktree preserved by review_requeue; prior review
void per contract):
1. `_build_request` honors a declared sha256 (`declared or computed`), making
   `verify_captures` a real check. Retained falsifier proof:
   `tamper_falsifier_20260911.txt` — mutated copy + declared original hash →
   `capture_hash_mismatch`, exit 2; unmodified original still passes (plan
   replay byte-identical).
2. Parser continuation fix (LOW finding): continuation lines after an inline
   header are now APPENDED to that section (never silently dropped);
   appended prose on CONCLUSION/FINISH fails strict validation — fail-closed.
3. Doc/spec wording corrected (declared sha256 optional, verified when
   present).

Regression: `plan` and `assemble` replay of the original live run are
byte-identical to the retained evidence; `tools/test_dyad_provider.py` 14/14.
