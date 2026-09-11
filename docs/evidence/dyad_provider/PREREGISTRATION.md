# DYAD_PROVIDER — Preregistration (before implementation)

Task: `dyad-provider-interface-01` gen 1, slot 5, owner glm53-lead-02 (epoch 5).
Base: `d012b4b1`. Recorded before any code.

## Statement / Prediction / Falsifier (task packet, restated)

STATEMENT: the interface separates the review CONTRACT from the vision PROVIDER
so a dedicated reviewer can run via subagent callback, remote service or the
existing local eye without protocol change.

PREDICTION: synthetic provider tests show fail-closed refusals (`no_vision`,
`capture_missing`, `capture_hash_mismatch`,
`provider_cannot_verify_temporal_claim`), full evidence retention including the
exact prompt and raw response, verdict parsing that never emits numeric facts
from visual text, and provider selection by configuration with no silent
fallback.

FALSIFIER: a temporal claim accepted from a still-only provider; a numeric fact
asserted from a visual response; a missing/corrupt capture passed through; the
prompt or raw response not retained; or the local adapter removed/bypassed.

## Derived contract (from docs/THE_DYAD_PROTOCOL.md, additive)

- One image per provider CALL remains the law for the local eye; the interface
  expresses ordered/multi-capture reviews as ordered call sequences and never
  collapses them silently.
- Non-leading questions only; the prompt builder never embeds expected defect
  strings (r7 lesson).
- Served identity is a separate fact from configured identity; missing
  response identity is recorded as named uncertainty, never substituted.
- Numeric mentions in visual prose are tagged `unverified_numeric_mention`;
  numbers become facts only through measurement, never through the eye.
- The local senses/LM Studio adapter is retained and lazily imported (CPU
  tests must not require the engine or a loaded model).

## Review types and capability ladder

- `still` — exactly one capture.
- `ordered_frames` — at least two captures, reviewed in order.
- `movie` — at least two captures plus a movie artifact reference in runtime
  metadata; ONLY providers declaring `temporal='movie'` may accept.

Provider temporal capability: `'none'` (still only), `'frames'`, `'movie'`.
Requesting above capability → `provider_cannot_verify_temporal_claim`.

## Test plan (tools/test_dyad_provider.py)

T1 request validation (bad type, zero captures, bad hash format, still with 2
captures, movie without artifact ref); T2 hash/missing fail-closed; T3
still-only provider refuses frames and movie by name; T4 frames provider
refuses movie; T5 subagent adapter happy path retains prompt+raw+identity;
T6 numeric mentions tagged, never asserted; T7 missing served identity is
named uncertainty; T8 selection by config, unknown kind refused, no fallback;
T9 local adapter class exists, lazy import, one-image-per-call loop for frames;
T10 prompt determinism and no expected-defect priming fields.
