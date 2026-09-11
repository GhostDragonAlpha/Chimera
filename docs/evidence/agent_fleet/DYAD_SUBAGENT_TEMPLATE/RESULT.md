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
