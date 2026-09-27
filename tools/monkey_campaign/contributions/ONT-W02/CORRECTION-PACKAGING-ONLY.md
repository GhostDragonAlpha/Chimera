# ONT-W02 — PACKAGING-ONLY CORRECTION NOTE

Lead finding: msg-2ed37cf7327548b6b957fe366d25af40 (CHANGES_REQUIRED, PR #168).
Scope: packaging of the qualification receipt at PR head and in the publication
artifact set. **No parity evidence, no pins, no frozen sites, and no done_when
material was changed.** Every file that appeared in PR #168 is committed here
byte-identical to the reviewed candidate at attempt
681e63e9e5d84eaa9702379faf347ac5.

## The defect

The evidence run itself fully reproduced under independent lead-side dossier
verification (EI verification.json 7b668328: PINS 10/10, FROZEN125 125/125,
DENSE 55392/55392 bit-exact, deterministic stdout sha256 517096e5…). The only
defect was packaging:

1. `qualification_receipt.json` (sha256
   `1ece68a480f3f8cc58a44e57a97f99148a3ac3672252f682f92fdd908606bb3f`, the
   "current" revision per the lead) was built and is listed as an artifact in
   `report.md`, but was **absent from PR #168's head tree** and absent from the
   original 17-artifact publication request (publication-4524676b).
2. `candidate.diff` embeds a superseded receipt revision (embedded sha256
   `6271cba6…`; lead also cites git index `89ee7ff3…` for that revision). The
   current revision on disk adds the `artifacts` array (45 differing paths)
   whose 17 artifact hashes all verify against the attempt files.

## Fix applied (minimal, per lead)

- The current `qualification_receipt.json` (sha256 above) is committed at this
  PR's head and included in the publication artifact set.
- This file (new, not referenced by any receipt pin) carries the required
  annotation of the known staleness inside `candidate.diff`.

## Why candidate.diff was annotated rather than regenerated

The current receipt pins all 17 contribution files byte-exact, including
`candidate.diff` itself (`b47f1a2cddbdeb3b…`) and `report.md`
(`786312256d84…`). Regenerating the diff (or editing the report) would change
those bytes and invalidate the receipt the lead directed us to commit.
Therefore candidate.diff is committed unchanged, with this annotation:

- The receipt embedded in `candidate.diff` (6271cba6…) is a **superseded
  revision**; the authoritative receipt for this candidate is the committed
  `qualification_receipt.json` at 1ece68a4…, which additionally carries the
  `artifacts` array (17 entries, all verified).
- All other embedded files in candidate.diff are byte-identical to the files
  at this head (verified via `git apply` into an empty repo with EOL
  normalization; 15/17 byte-identical, and the two remaining deltas are exactly
  the two JSON serializations described below).
- The embedded `parity_gate_result.json` differs from the committed file only
  in JSON serialization; key-sorted JSON comparison proves semantic identity.
- The embedded `qualification_receipt.json` differs from the committed file
  only by the superseded-revision delta described above; no parity claim
  changes between the revisions.

The applies-with property of the diff is unchanged: `git -c
core.autocrlf=false apply --check --cached` passes against an empty base for
all 16 new-file additions plus the receipt (verified by the lead on PR #168
and re-verified here into a scratch repo).

## Verification performed for this correction

- Receipt artifact list: 17/17 sha256 entries re-verified against the files at
  this head.
- Receipt content spot-checks: `fresh_evidence.frozen125` 125/125 with
  tolerance NONE; dense 55392/55392; `gate_stdout_sha256`
  517096e569b6bc7b…; `parity_gate_result.json` on disk confirms frozen125
  `p1_pass: true` and identical dense totals.
- No file listed in the original 17-artifact request changed (all sha256
  values match the original request_pr.json entries).
