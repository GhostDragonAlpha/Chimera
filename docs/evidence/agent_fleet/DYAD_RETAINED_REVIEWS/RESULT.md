# RESULT — dyad-retained-reviews-01

Agent: subagent-worker-06 (vision-capable host subagent; served identity harness-declared,
never self-reported) · base 5199d9c3 · generation 1 · 2026-09-11.

## What ran

Systematic DYAD review of retained engine captures through the LIVE subagent template
(`docs/THE_DYAD_SUBAGENT_TEMPLATE.md` + `tools/dyad_subagent_template.py`, PR #52).
The host subagent performed the DYAD reviewer role itself (spawned nothing): for each case
it validated the request + hash-verified every capture fail-closed against its retained
sidecar sha256 (`plan`), read ONLY the listed image file(s) with its own Read tool, answered
the numbered non-leading questions as RAW_RESPONSE in the template's `===DYAD_REPORT===`
block (saved verbatim), and ran `assemble` through `SubagentDyadProvider`. Four reviews,
four `dyad_log.jsonl` entries, zero refusals, zero fail-closed events. No local eye, no
local model, no GPU, no engine process. Captures untouched (read-only; hashes verified).

## Per-capture review table

| attempt | type | captures (sidecar sha256, verified) | source dir | finish | verdict | supports | reviewer gist |
|---|---|---|---|---|---|---|---|
| rr01-edge01-pair | ordered_frames | raised_gamma0.png `53e994e0…`, final_relaxed.png `20021e78…` | membrane_gpu_demo_runtime/20260909T143821.177952Z (EDGE-01 phi-0.35 pair) | complete | INCONCLUSIVE | true | Pair distinguishable: spokes converge near the upper (far) edge in frame 1 vs near the outline centroid in frame 2; outline/background/lighting identical; magnitude not determinable |
| rr01-edge01-relaxed-still | still | final_relaxed.png `20021e78…` | same dir (relaxed side; raised side was the lane's live run live-raised-gamma0-20260911) | complete | INCONCLUSIVE | true | Fan structure resolvable (six spokes, centroid convergence); height not resolvable; no large far-edge offset apparent; small curvature not excludable |
| rr01-dyad02-oblique-pair | ordered_frames | raised_gamma0_oblique.png `f7a6e595…`, relaxed_gamma1_oblique.png `39b861a8…` | membrane_window_demo/20260908T192702.077867Z + 20260908T192708.250952Z (GLM-DYAD-02 oblique pair) | complete | NOT_CLAIMED | — (unclear) | Fill-only pair reads nearly identical; interior spokes not resolvable at this presentation; centre vertex not locatable; only a subtle fill-shading difference apparent |
| rr01-contrast-oblique-pair | ordered_frames | raised_contrast_oblique.png `a1c24291…`, relaxed_contrast_oblique.png `8da47c82…` | membrane_window_demo/20260908T203620.679992Z + 20260908T203626.782212Z (edge-contrast finals) | complete | INCONCLUSIVE | true | Edge-contrast pair distinguishable: convergence in the upper part of the outline (frame 1) vs at the centroid (frame 2); direction visible, magnitude not |

## Findings (observations only — no acceptance)

1. **The verdict ceiling held everywhere.** Three reviews recorded INCONCLUSIVE (reviewer
   agreement is never acceptance — the provider maps `supports` to INCONCLUSIVE, never PASS);
   the honest `unclear` mapped to NOT_CLAIMED. No verdict above INCONCLUSIVE was claimed.
2. **Presentation decides legibility, not the states.** The same state pair that is
   indistinguishable in the fill-only oblique presentation (rr01-dyad02-oblique-pair: the
   reviewer could not locate the centre vertex at all) is distinguishable once the
   edge-contrast wire presentation is active (rr01-contrast-oblique-pair: convergence-point
   displacement clearly visible in direction). This reproduces, through the subagent class,
   the same open question the historical rounds hit: height resolvability in single stills
   and fill-only pairs remains unresolved, and the images alone never yield magnitudes.
3. **The EDGE-01 phi-0.35 GPU-demo pair is visually distinguishable** by the spoke
   convergence position alone, with all other scene elements reading identical — consistent
   with the recorded states differing only in centre height, but the images do not measure
   that height, and this review does not certify it.
4. **Honest uncertainty retained verbatim.** Every report names its limits: no scale
   reference, foreshortened oblique views, thin low-contrast lines, lighting-dominated
   shading, unexplained background silhouettes. All numeric mentions in prose are tagged
   `unverified_numeric_mention` by the provider (20/5/16/19 per case).

## Prediction scorecard (preregistered 2a45587d)

| # | prediction | outcome |
|---|---|---|
| 1 | all requests validate; all captures match sidecar sha256 | HELD — 7 capture slots verified fail-closed, 0 mismatches, 0 refusals |
| 2 | responses record visible structure and name uncertainty where single-view geometry cannot resolve | HELD — uncertainty sections retained verbatim in all four reports |
| 3 | dyad_log accumulates exactly one entry per review | HELD — 4 entries, one per case |
| 4 | no content-level acceptance claimed | HELD — verdicts capped; NOT_CLAIMED recorded for content acceptance, local-eye equivalence, human acceptance |

Falsifier check: no leading question in any retained request (questions are descriptive
"what/where do you see" form); no verdict above INCONCLUSIVE; evidence retained verbatim
(exact prompts, raw reports, response JSONs, log); captures unmodified; local eye/GPU
untouched. **No falsifier fired.**

## NOT CLAIMED

Content-level physics acceptance (shape/height claims stay with the owning lanes' gates) ·
equivalence between this host-subagent reviewer and the local eye · human acceptance
(reserved to Alan).

## Files

PREREGISTRATION.md (commit 2a45587d, before any run) · request_spec_rr01-*.json (4) ·
exact_prompt_rr01-*.txt (4) · subagent_report_rr01-*.txt (4, verbatim) ·
dyad_response_rr01-*.json (4, assembled provider responses) · dyad_log.jsonl (4 entries) ·
MEASUREMENT.json · RESULT.md (this file).
