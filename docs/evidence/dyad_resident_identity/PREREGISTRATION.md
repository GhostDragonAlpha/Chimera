# PREREGISTRATION — dyad-resident-identity-01 (fresh-system re-verification)

- Task: `dyad-resident-identity-01`, generation 5, slot 4, worktree `E:\ChimeraWork\slot-04`
- Task branch: `astra/tasks/dyad-resident-identity-01`, recorded base `accd15b61d7ac3805edfc36535ef99de121baf65`
- Stale-base reconciliation: merge of `origin/astra/gait-capture` (tip `4604de40bd6cdd02d3cc277019f8bac5030c2dbe`) — a fast-forward, no new commit
- Written BEFORE any new run or result of this task. No measured actual of this
  task's runs appears below; only the packet's prior observation is cited.

## STATEMENT

Reported resident identity (`ChimeraEngine.senses.resident_model()`) comes only
from explicit loaded-state metadata in LM Studio's `/api/v0/models` records
(`state == "loaded"` or `status == "loaded"`); a model id that is merely present
on disk is NEVER reported as resident. Inference served identity remains
response-derived (recorded only from actual `/v1/chat/completions` response
bodies), never from the metadata read.

## PRIOR OBSERVATION BEING RE-VERIFIED (packet, at base accd15b6)

`senses.resident_model()` fell back to the first on-disk model id when every
`/api/v0/models` item was not-loaded. A read-only synthetic urlopen test
returned a fixture-on-disk-only id. This task re-verifies that counterexample
FRESH on this system and pins the corrected contract with CPU regressions.

## PREREGISTERED FALLBACK / AMBIGUITY SEMANTICS (exact, declared before any run)

`resident_model()` must return, for a mocked `/api/v0/models` response:

| # | Case | Response shape | Required result |
|---|------|----------------|-----------------|
| 1 | no-model | `{"data": []}` | `None` |
| 2 | on-disk-only | records present, every `state`/`status` != `"loaded"` | `None` — never any on-disk id |
| 3 | loaded (unambiguous) | exactly one record explicitly `loaded` (non-empty string id) | that id |
| 4 | multiple-loaded | two or more explicitly `loaded` records | `None` — named ambiguity; never first-selected, never hidden selection |
| 5 | malformed | payload not an object, or `data` not a list; non-object records are skipped | `None`, no exception escapes |
| 6 | transport-failure | `urlopen` raises (URLError/timeouts) | `None` |

Side-effect laws, binding for every case above:

- No load, pick, evict, or reconfigure call occurs: the only network surface
  touched is a data-less (GET) request to `/api/v0/models`; no
  `/v1/chat/completions` inference call, no `eye_control.load`, nothing that
  could evict an operator-loaded model.
- Inference served identity stays response-derived: the metadata read does not
  write any served-identity record; `_SERVED` moves only on an actual response.

## FALSIFIER (named before the run)

The preregistration FAILS if any of these is measured:

1. An on-disk (not-loaded) model id is reported resident (case 2 returns a
   non-None id) — the original counterexample.
2. A guessed served model: resident_model() returns an id the mocked metadata
   never explicitly marked loaded, or the metadata read mutates any
   served-identity record.
3. Hidden model selection: with multiple loaded records, an arbitrary
   (e.g. first-listed) id is returned instead of named ambiguity.
4. Real inference, model load, or eviction occurs during the CPU tests
   (any non-`/api/v0/models` network surface, any POST, any `eye_control.load`).
5. Old failed evidence is overwritten: this task's evidence directory
   (`docs/evidence/dyad_resident_identity/`) gains only append/new files; the
   retained base counterexample artifacts are preserved verbatim.

Cases 1 and 3 are additionally PREDICTED to fire the falsifier against the
BASE `accd15b6` snapshot (retained counterexample run): base `resident_model()`
returns `ids[0]` of all listed ids when nothing is loaded, and returns the
FIRST loaded id when several are loaded. If the base snapshot instead passes
all six cases, the prior observation fails to reproduce and that result is
recorded verbatim.

## METHOD (declared before any run)

- CPU-only, synthetic: `urllib.request.urlopen` is monkeypatched; no network,
  no model load, no GPU, no inference. `python -m unittest` from repo root.
- Fresh defect demonstration: `git show accd15b6:ChimeraEngine/senses.py`
  extracted verbatim into this evidence directory and loaded by module path
  (env-var override in the test harness), so the preregistered cases run
  against the exact base code without modifying the merged tree.
- Consumers inspected before choosing the correction scope: at base accd15b6
  `resident_model()` had no production caller; at the merged tip the canonical
  history (dyad model policy work) already supplies the stricter contract
  (single unambiguous loaded id, `None` otherwise) plus
  `tools/test_dyad_model_policy.py` covering four identity cases. The smallest
  coherent correction on this branch is therefore: keep the canonical merged
  `senses.py` unmodified (no competing re-fix) and add the missing
  preregistered regressions: no-model, malformed, transport-failure, the
  side-effect laws, and the retained base counterexample run.
- Related test module that also imports `ChimeraEngine.senses`
  (`tools/test_dyad_model_policy.py`) is run alongside the new suite.

## NOT_CLAIMED

- No live model load, inference, eviction, or GPU operation is performed or claimed.
- DYAD visual acceptance is NOT_CLAIMED; acceptance of this task stays
  NOT_CLAIMED pending lead review.
