# GPU validation gap - recorded separately (elastic-ref-publish, gen 6)

Per the lead's generation-6 review of `7d9e6949`: this repair task closes the
two false-pass defect classes in the CPU fixture verifier. It does **not**
implement GPU validation, and the original law and tolerances are not expanded
by this repair.

**Unimplemented and NOT_TESTED:**

1. **GPU upload-path validation** - `verify_fixtures` emits the
   truncated-to-float32 reference answers for the GPU acceptance workflow
   (`GPU_HANDOFF.md` stage C), but no check yet verifies that a GPU stage-A
   output derived from an actual `/mesh_bin`/upload path matches them. The
   fixture verifier validates stored arrays only; it cannot see the engine's
   upload pipeline.
2. **Corner-oracle validation** - the handoff's corner/oracle comparisons
   (per-corner force and energy checks against independent oracles on the GPU
   result) are not implemented here and remain separate runtime gates.

Both require the engine runtime and GPU resources (`rtx4090`, possibly
`engine_demo`), which this task's packet forbids claiming (CPU-only repair
task; "No GPU, engine, runtime, window or DYAD reservation"). They are
therefore recorded as explicitly NOT_TESTED rather than approximated by a
CPU-side proxy.

**Original law and tolerances preserved:** the CPU law, the declared relative
L-infinity comparison norm, the 512*eps budget and all frozen fixture arrays
are unchanged by the gen-5 and gen-6 corrections; only the verifier's
comparison mechanics and refusal behavior were repaired, plus the test's
isolation of the tracked fixture root.

**Evidence-hygiene note (2026-09-10):** while this task was RUNNING, an actor
other than buffy-02 amended the local branch (rewriting gen-5 commit
7d9e6949 into 1896c721 with this task's then-staged gen-6 files), and
untracked evidence files were deleted twice from this worktree within
seconds of creation. No buffy-02 command performs either action. Recovery:
the local branch was reset to the remote's true lineage (7d9e6949, preserved
on the remote and in PR #14), and the gen-6 content was recommitted on top
as a normal child commit. The amended commit remains in reflog as incident
evidence; this note is committed to make the incident durable.

Recorded by buffy-02, 2026-09-10.
