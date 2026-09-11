# PREREGISTRATION — dyad-retained-reviews-01

- agent: subagent-worker-06 (vision-capable host subagent; harness-declared by lead 2026-09-11)
- task: dyad-retained-reviews-01, generation 1, slot 5
- base: 5199d9c3015f6840b12186f34c3e0c2fd5d7b0a4 (merge of PR #60; contains the integrated
  DYAD subagent template, PR #52 merge f3e7b51d)
- branch: astra/tasks/dyad-retained-reviews-01
- written: 2026-09-11, BEFORE any review run of this task (no actuals below)

## What runs

Systematic DYAD review of retained engine captures through the LIVE subagent template
(`docs/THE_DYAD_SUBAGENT_TEMPLATE.md` + `tools/dyad_subagent_template.py`). The host
subagent performs the DYAD reviewer role itself (it spawns nothing): for each case below
it (1) validates the request + hash-verifies captures + retains the exact prompt via
`plan`, (2) reads ONLY the listed image file(s) with its own Read tool, (3) answers the
numbered non-leading questions as RAW_RESPONSE inside the template's `===DYAD_REPORT===`
block, saved verbatim, and (4) runs `assemble` through `SubagentDyadProvider` with
`--served "subagent-worker-06 (vision-capable host subagent) [harness-declared by lead 2026-09-11]"`.

## Review set (captures read-only; sha256 declared from each capture's retained sidecar)

| case (attempt) | review_type | captures (declared sha256 from sidecar) | retained source |
|---|---|---|---|
| rr01-edge01-pair | ordered_frames (2) | raised_gamma0.png 53e994e0..., final_relaxed.png 20021e78... | docs/evidence/membrane_gpu_demo_runtime/20260909T143821.177952Z/ (EDGE-01 phi-0.35 pair) |
| rr01-edge01-relaxed-still | still (1) | final_relaxed.png 20021e78... | same directory (relaxed side; the raised side was the template lane's live run live-raised-gamma0-20260911) |
| rr01-dyad02-oblique-pair | ordered_frames (2) | raised_gamma0_oblique.png f7a6e595..., relaxed_gamma1_oblique.png 39b861a8... | docs/evidence/membrane_window_demo/20260908T192702.077867Z/ + 20260908T192708.250952Z/ (GLM-DYAD-02 oblique pair, dyad round-5 images) |
| rr01-contrast-oblique-pair | ordered_frames (2) | raised_contrast_oblique.png a1c24291..., relaxed_contrast_oblique.png 8da47c82... | docs/evidence/membrane_window_demo/20260908T203620.679992Z/ + 20260908T203626.782212Z/ (GPU-demo edge-contrast finals, dyad round-6 images) |

Full 64-hex sha256 values are in each case's request spec; `plan` verifies each file
against its sidecar-declared declaration fail-closed (`capture_hash_mismatch` on tamper).

## STATEMENT (theory, per task packet)

Each retained capture above carries an open visual question that a prior dyad round left
open or INCONCLUSIVE (height resolvability in single stills; raised-vs-flat separability
in the oblique pairs; the edge-contrast finals). A fresh structured review through the
live subagent template — one image per still, ordered_frames only where the pair is the
question, non-leading questions, verdict ceiling INCONCLUSIVE — is a legal, auditable way
to put these retained items through the reviewed provider path and record honest
uncertainty verbatim.

## PREDICTION (stated before any run)

1. Every request validates against the reviewed contract; all seven capture files match
   their sidecar-declared sha256 (no tamper; no re-render).
2. The assembled responses record visible structure where it is visible and name
   uncertainty wherever single-view geometry cannot resolve it (e.g. exact heights from
   oblique stills).
3. `dyad_log.jsonl` accumulates exactly one entry per review (four entries total, plus
   any fail-closed refusals, which are retained as evidence, not hidden).
4. No content-level acceptance is claimed anywhere by this task.

## FALSIFIER (named before the run)

- A leading question appears in any retained request (r7 law).
- Any verdict above INCONCLUSIVE is claimed for a review.
- Evidence not retained verbatim (exact prompt, raw report, assembled response, log line).
- A capture is re-rendered, modified, or its hash fails verification.
- The local eye / LM Studio / any local model load or GPU resource is used
  (subagent provider class only; no resource chain needed).

## NOT_CLAIMED

- Any content-level physics acceptance (the reviewed lane certifies the provider path
  only; shape claims stay with the owning lanes' gates).
- Equivalence between this host-subagent reviewer and the local eye.
- Human acceptance (reserved to Alan).

## Method notes

- Verdict mapping (reviewed contract): reviewer conclusion `supports` records
  INCONCLUSIVE at most (agreement is never acceptance); `contradicts` records FAIL;
  `unclear` records NOT_CLAIMED.
- Numbers mentioned in any report are observations to verify, never measurements.
- One image per still review; ordered_frames (exactly 2) only for the three pair cases
  where the pair itself is the question.
- All work committed under docs/evidence/agent_fleet/DYAD_RETAINED_REVIEWS with trailer
  `Agent: subagent-worker-06`.
