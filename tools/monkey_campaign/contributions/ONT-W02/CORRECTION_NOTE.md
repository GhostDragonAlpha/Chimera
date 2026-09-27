# ONT-W02 packaging correction note (CHANGES_REQUIRED on PR #168)

Correction attempt `20cd4096b9f24edd882c8adf4c375077`, arrival
`arrival-12cea78a1bf540ef9b4c65733c035f74`, criteria_sha256
`bf9f89874ee4a7d0606c46215e843474331482444af556ac4f199a6bfcd087f2`.

This is a PACKAGING-ONLY correction responding to the lead CHANGES_REQUIRED review of
PR #168 @ `47ee139f2256982eed6720aa3d4ce8ac56011d0e`. The zero-tolerance parity
evidence itself is untouched: no pinned file, probe source, gate output, math,
prediction or verdict byte is changed by this correction.

## What was wrong

1. `qualification_receipt.json` was absent from the PR #168 head and from the
   17-artifact publication request `publication-4524676b94c2416fa9fc482865f46813`
   (the prior worker's `request_pr.json` omitted it), although report.md section 1
   lists it as built and card step 5 requires a source-bound qualification receipt
   for independent review.
2. `candidate.diff` (sha256 `b47f1a2cddbdeb3b5447a4be1275830966a28e167c2a97a2298611b3bdae1923`)
   embeds a SUPERSEDED revision of the receipt (git blob `89ee7ff3`, file sha256
   prefix `468af1f5`) in its `qualification_receipt.json` section: that superseded
   revision carries per-artifact `bytes` fields and does not yet pin `candidate.diff`.
3. The `candidate.diff` section for `parity_gate_result.json` embeds an LF-line-ending
   copy of the CRLF published ledger file (sha256
   `e1d6a5096ca5e50f6907e5d68f9c57fe2d4e6141902badb23ecc454b18e105fa`). The copy is
   byte-different but content-identical after newline normalization (verified: zero
   unified-diff lines). Semantically identical; recorded here rather than silently
   regenerated.

## What this correction changes

1. `qualification_receipt.json` is now present at head and in the publication
   artifact list, byte-identical to the current revision authored by the prior
   evidence attempt `681e63e9e5d84eaa9702379faf347ac5` (arrival
   `arrival-535a6d99aaf94c78b3aed6a239885498`), sha256
   `1ece68a480f3f8cc58a44e57a97f99148a3ac3672252f682f92fdd908606bb3f`.
   It was verified against that revision and reused verbatim; its artifact pins
   (17 entries, including `candidate.diff` `b47f1a2c`) were re-verified against the
   actual PR #168 head files.
2. `candidate.diff` is intentionally NOT regenerated: the current receipt pins
   `candidate.diff` at `b47f1a2c`, so regenerating the diff would invalidate the
   receipt's pin (and re-embedding the current receipt in the diff would make the
   receipt's diff pin self-referential). This note is the annotation of record for
   the two stale-within-the-diff sections listed above. Re-verified for this
   correction: `git -c core.autocrlf=false apply` of `candidate.diff` onto base
   `155a0f5c6ed14d6ce0c95572676eb03f14bc8a50` succeeds cleanly and yields the
   15 other evidence files byte-identical to this candidate, plus exactly the two
   annotated sections: `parity_gate_result.json` as the LF copy, and
   `qualification_receipt.json` at the superseded revision (sha256
   `468af1f595f8f0da11c6aa98870e1c27709a7b456ebf8906f80bba04b1e1f3fc`), which the
   separately published receipt file at head (sha256 `1ece68a4...`) replaces.
   The diff, by construction, does not contain itself or this note.
3. Nothing else changed. All other files are byte-identical to PR #168 head
   `47ee139f2256982eed6720aa3d4ce8ac56011d0e` (verified by sha256 comparison).

## Verification re-run for this correction (CPU-only)

- Fresh `python -B run_gate.py` rerun of the pinned driver in an isolated scratch
  copy: PINS 10/10, FROZEN125 125/125, DENSE 55392/55392, RESULT
  PASS_NO_TOLERANCE, probe stdout sha256
  `517096e569b6bc7bbeb3e581ab590c5f84fa8e1da9e97962ab2d34f61291d935`
  (first and deterministic second run bit-identical). The freshly regenerated
  `parity_gate_result.json` differs from the pinned ledger only in its
  `started_utc`/`finished_utc` timestamps and the run's own `gate_run_output`
  path; every evidence field (pins, per-site bits, dense census, preserved-record
  recounts, predictions, verdict) is identical.
- Failing-first spot checks (scratch copies only, never the candidate):
  corrupted pin -> `PIN-MISMATCH trig_inputs.txt` -> `GATE FAIL: pin identity
  mismatch`, exit 1; 1-ulp deviation injected into the reconstruction at the
  25 SIN sites -> `FROZEN125 100/125`, `P1=FAIL`, `RESULT FAIL`, exit 1.
- `candidate.diff` re-applied to the base in a detached scratch worktree (see
  above for the exact result).
