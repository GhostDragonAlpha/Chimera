# Native membrane demo: execution and evidence

The interactive entry point is `python tools/engine_demo.py --help`. Use a
provisioned slot's private executable, runtime directory and endpoint; obtain
the engine/GPU reservation before launch. The launcher was integrated through
PR #15 at `82f8623c688191d3ddcf32c5e3282bde8e350d4b`.

This demonstrates the frozen B2 constant-gamma surface-energy law. Relaxation
iterations minimize energy; they are not physical time. It does not certify
elasticity, a cup of water, creature locomotion or performance.

## Executed evidence

Evidence lives in `docs/evidence/engine_demo01/`. The initial private native
build and the first reset repair both passed the unchanged frozen runtime
gate: **20 PASS and 1 INFO**, not 21 PASS. The complete records are respectively
`../membrane_gpu_demo_runtime/20260910T153744.673179Z/` and
`../membrane_gpu_demo_runtime/20260910T162129.484823Z/`, relative to that evidence
directory. Source, executable and shader hashes are in the build identities.

The reset defect mixed restored geometry and energy with cached force from a
preceding state. `reset_before/result.json` retains two failing comparisons;
`reset_after/result.json` retains their passing counterparts after the force
cache refresh. Independent review additionally required the gate to prove
that each preceding control actually changed state and to reject malformed
vectors. Final review evidence must be read separately from those earlier
runs; historical outputs are not overwritten.

The final review build also passes the unchanged gate in
`../membrane_gpu_demo_runtime/20260910T163442.349383Z/`. The strengthened reset
gate passes both controls in `reset_review_after/result.json`; five independent
fake-request regression tests pass in `reset_gate_unit.txt`, including ignored
controls and malformed status. `reset_review_identity.json` identifies the
final executable and exact then-dirty C++ source bytes. A failed reset now
deactivates the demo, requiring initialization before later controls. That
failure branch was reviewed and built, but GPU evaluation failure was not
injected; the successful runtime checks do not establish that failure path.

`scheduler_after/result.json` records three actual native/session checks:
refused Run halts scheduling, Reset stays reset, and terminal state halts
future steps. The final launcher source was `eb408d174742ab6daac30f580acd718ef558c336`.
Earlier six-control pointer observations and their later scheduler failures
are retained under `panel_controls/`; they do not certify the corrected source.

## Visual observations and remaining requirements

`dyad_round1/` retains two complete, one-image responses from served model
`qwen3.8-27b-nvfp4-mtp`, with image hashes, prompts and finish reasons. The eye
recognized the polygon and triangle edges, but center-height interpretation
remained **INCONCLUSIVE**. No human acceptance is inferred. Profile-view
experiments have their own preregistration; an edge-on flat surface can become
almost invisible and is not stronger evidence merely because its view changed.

The final `profile_review/` captures have unchanged before/after state fields
and pass the PR #16 bounded snapshot validator. Both additional eye responses
completed with finish reason `stop` on the same served model. The raised view
shows a shallow central peak. The relaxed view supplies no visible center cue;
the eye attributed the dark hexagonal region to surface geometry, but this
image does not establish that attribution. Retain that response as an
observation, not a topology or physical-state verdict. Use the numerical gate
for the relaxed state and retain the oblique view for visible triangle layout.

`native_window_gen4.png` shows the native renderer displaying the membrane
while Studio labels report no mesh. The new `demo-studio-state-01` requirement
tracks this discrepancy and the distinction between an absent local eye log
and tested eye failure. It supplements the Master list rather than replacing
unfinished work.

The original `panel_initial.png` captured a minimized title bar. Files named
`panel_gen7_refusal*.png` belong to refused input attempts, despite the word
"verified" in one filename. An unrelated Windows Security window occluded
the panel; the input guard refused clicks. Subsequent checks used the owned
native endpoint and session class. No Security dialog was operated.

Capture hashes and equal before/after accepted-state fields support only a
bounded snapshot correspondence claim. They do not bind a frame to a GPU
submission/completion identity. Render identity remains unbound.

Run-specific helper scripts retain historical paths and process identities;
inspect them before reuse. Never replay old window handles or assume a reused
slot still contains the recorded revision. Protected build artifacts and the
operator's running engine were not modified.
