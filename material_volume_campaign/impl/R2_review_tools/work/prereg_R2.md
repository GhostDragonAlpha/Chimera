# R2 PREREGISTRATION — frozen BEFORE any check runs

Reviewer: R2 (non-author). Date: 2026-09-24. Worktree `E:/ChimeraWork/mvc-20260924`
(HEAD a00146f3 — note: two commits AFTER the reviewed fe031402/af735b7f exist; both
verified by `git log --follow` to NOT touch the two tools/ files under review).

## STATEMENT
The W1 verifier + battery append and the W3 reader repair do what their claims say,
catch what they claim to catch, change nothing they claim not to change, and fail
honestly (named refusals / non-pass verdicts) on inputs outside their claims.

## PREDICTIONS (before measurement)
P1. A genuine example report VERIFIES (exit 0) with the caveat string present.
P2. Three R2-authored mutations of the genuine report (1-ULP tensor edit; swapped
    provenance hash fields; subtle mass change via nextafter) each verdict MISMATCH
    (exit 1) with an itemized path.
P3. A missing source file verdicts UNAVAILABLE-SOURCE (exit 2), never a pass.
P4. A tampered report + tampered source that agree (mutated groups + regenerated
    report from those groups) VERIFIES — and this is the documented producer-
    agreement caveat (caveat + independent_checks_note present, statuses surfaced),
    not a hidden failure.
P5. The pinned materialization OIDs hash-object-match the `git ls-tree` OIDs of the
    three producer modules at 1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56; a pin to a
    rev lacking the modules refuses (UNAVAILABLE-SOURCE).
P6. Battery diff af735b7f→fe031402 is +61/−0, append-only; both identity labels
    present; the original test's executable lines are unchanged (comment-only
    insertion); the full battery passes at HEAD.
P7. All 13 W3 T-fixtures + B7 corrupt_M13 exit 2 on a scratch copy of the CURRENT
    reader with the frozen refusal lines (no traceback).
P8. Three R2-authored hostile reader inputs get named located refusals, except any
    genuinely-expected crash class found by the generality probe (see F-R2-3).
P9. Reader stdout hashes on valid reports are byte-identical between the pre-W3
    reader (d2c23741) and the current reader; existing refusals (K1–K6 + corrupt_M13)
    produce identical stderr+exit on both.
P10. An injected RuntimeError at a coercion site propagates (not converted).
P11. Full battery + W1 suite + W3 suite all green when run together.

## FALSIFIERS (named now; a hit is reported, never tuned)
F-R2-1: any P1–P4, P7, P9, P10, P11 fails as stated (e.g., a mutation VERIFIES; a
  valid-output byte changes; a crash shape exits non-2 or with a traceback).
F-R2-2: pin integrity fails — materialized code OIDs differ from 1af0bbde's tree, or
  the W1 suite PIN constant no longer resolves to the exporter commit.
F-R2-3: generality probe — a coercion-class input OUTSIDE W3's 14 shapes still crashes
  uncaught (candidate predicted now: huge integer literals, e.g. a 400-digit int mass
  or tensor entry, float()-coerce to OverflowError which is neither TypeError nor
  ValueError). Recorded as a NOTE (pre-existing class, not a regression) unless it is
  a regression vs d2c23741, in which case it is BLOCKING.
F-R2-4: the battery append is NOT purely additive (any original line deleted/modified),
  or the blob-form test can silently skip as a pass in a normal run.

## CHECKS (executed in this order; receipts under receipts/, scratch under work/)
1. W1 re-run on R2-authored corpus (P1–P4), verifier run with --work-dir and
   --output-json inside R2 dir (impl/ write-law respected).
2. Pin integrity (P5, F-R2-2): hash-object the materialized files; ls-tree 1af0bbde;
   cat-file -t the PIN; bad-pin negative run.
3. Battery append audit (P6, F-R2-4): git diff; executable-line subset check of the
   original test; run battery at HEAD.
4. W3 re-run (P7–P10): scratch reader copy + pre-W3 reader materialized from
   d2c23741; A/B stdout/stderr/exit on valid + refusal inputs; R2 variants; injected
   RuntimeError; generality probes (huge int, numeric strings, extra columns).
5. Joint run (P11): battery + W1 suite + W3 suite, one after the other in one shell.

CPU-only, no network. All R2 writes confined to impl/R2_review_tools/.
