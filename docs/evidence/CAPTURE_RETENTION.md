# Capture retention policy — pictures are transient, calculations are evidence

Standing directive (owner, 2026-10-12): this project's development loop
collects many screenshots; raw images must not accumulate on disk. The
durable form of a visual test result is **the calculation it demonstrated**
— the measured quantities, the law, the tolerances, the hashes — recorded
compactly. The picture itself is deleted after that extraction.

## Rule

After any battery, receipt run, or visual probe produces image captures:

1. **Extract before deleting.** Write a `CAPTURE_DIGEST*.json` beside the
   run's other evidence containing, per image: SHA-256 of the exact bytes
   deleted, pixel dimensions, a coarse content check (64×36 non-background
   fraction — proves the frame rendered the scene, not a black window), and
   a `physics` field binding the image to the numbers it demonstrated
   (settled COM, forces, reactions, energy drift, hue-probe coordinates,
   state hashes — with a pointer to the evidence section that carries the
   full account).
2. **Then delete the raw image.** Never commit a multi-megabyte capture;
   the digest + the run's JSON evidence are the committed record. The
   SHA-256 row is what makes the deletion auditable: anyone with a retained
   copy can prove byte-identity, and nobody can quietly swap content.
3. **Update references in place.** Evidence documents that named the image
   keep their sentences, re-anchored to the digest ("raw capture deleted
   per this policy; digest + SHA-256 in …").
4. **A claim that only a picture can support is a gap**, not a reason to
   keep the picture: add the missing measurement to the numeric evidence
   (hue probes, projected-pixel checks, telemetry-at-capture) so the
   calculation stands alone.

## Applied so far

- `construction_packet_20261012/CAPTURE_DIGEST_b4b5.json` — B4/B5 gate
  frames (2 × 7.4 MB deleted; hue probes + telemetry preserved in the B5
  "Frame" passage).
- `recipe_comparison_rc1_def4d82d/CAPTURE_DIGEST.json` — recipe-comparison
  captures (5 × 7.4 MB + 3.3 MB native payload deleted; per-trial settled
  COM/force/extension/final-hash preserved).
- ~57.6 MB freed by these two sweeps.

## Not yet applied (needs owner coordination)

Other agents' captures in the shared checkout (e.g.
`ChimeraEngine/engine/spiace_*.png`, fleet-evidence images) predate this
policy and belong to their authors' uncommitted work — a sweep of those,
and of historical committed images repo-wide, should be run as its own
digest-and-delete pass with their owners, not folded into an unrelated
commit.

## For the tooling (proposed, not implemented)

The recipe runner and batteries should write digests and delete captures
as their final step (the runner's `artifacts_sha256` already hashes the
images before deletion would occur, so the audit chain survives). The
runner is another agent's uncommitted file — proposed change, not applied.
