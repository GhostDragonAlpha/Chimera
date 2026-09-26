# R4 PREREGISTERED REVIEW CHECKS — frozen before measurement

Reviewer: R4 (interface authority, this pass). Written 2026-09-24, before reading the
spec body, the implementation, or running any check. The brief enumerates the review
dimensions; this file freezes HOW each will be judged and what would falsify approval.

## Frozen checklist (executed in this order, results reported even when red)

- **C1 — Hash proof (walk contract untouched).** Recompute a content hash of the frozen
  walk-contract module (CommandRecord v1) at the reviewed commit 87c14ca5 and compare
  against the hash the U05 integration artifacts claim for it, AND against the same
  module's hash at the parent commit of the U05 work (provenance anchor recorded in the
  prereg/spec). FALSIFIER: any hash mismatch, or an unverifiable claim of identity.
- **C2 — Six rulings.** Rule APPROVE / AMEND-WITH-REASONING / REJECT on each of the six
  ruling points that terminate INTENT_SEAM_SPEC.md. A ruling requires a reason tied to a
  consumer need (U06/K/X02/U03) or a law (no-fabrication, no-invented-API), not taste.
  FALSIFIER: a ruling with no reason, or a ruling that pre-empts a consumer's own
  decision (e.g., dictating K-series arbitration policy).
- **C3 — Spec-implementation coherence, >=5 clauses with line citations.** Pick five
  normative clauses ("MUST"/"SHALL"/numbered guarantees) from the spec, cite spec line
  and code line, and verify by reading AND by execution where cheap. FALSIFIER: any
  clause the code contradicts, or a clause with no corresponding code at all.
- **C4 — Test suite re-run.** Re-run the author-claimed 73/73 suite from a clean process.
  Report the counted total. FALSIFIER: count differs from claim, or any red.
- **C5 — Adversarial probes (declared in advance):**
  - A1: smuggle a float (and a bool, and a NaN) into IntentEvent's integer fields —
    expect rejection, not silent coercion. FALSIFIER: acceptance or silent cast.
  - A2: version confusion — present a v1-shaped record to a v2 reader (and vice versa);
    expect a named refusal, not a reinterpretation. FALSIFIER: acceptance-as-other-version.
  - A3: press arriving on the exact gate-transition tick (intent pressed in the same
    update the gate flips) — behavior must be SPECIFIED and deterministic, not accidental.
    FALSIFIER: unspecified/OrderMap-dependent behavior.
  - A4: two listeners, two sinks, same tick — double-count or sink-order-dependent state
    is the failure. FALSIFIER: delivery count differs from spec, or order changes state.
  - A5: oversized/negative/absent fields at the boundary (magnitude > bound, negative
    duration, missing key) — expect the documented refusal names. FALSIFIER: silent clip
    or default other than spec'd.
- **C6 — Future-consumer fit.** Read U06's completion-map row + K-series needs (selector
  receives intents, decides; K06 arbitration) + X02 + U03 rows. Output: SERVES / GAPS list.
  Gaps are SPEC-NOTES for v2, not defects. FALSIFIER: a consumer need the interface makes
  IMPOSSIBLE (that one is a defect, not a note).
- **C7 — Integrity.** `git status` diff-scoped proof that my only writes are inside
  agents/R4_intent_review/. FALSIFIER: any write outside my dir.

## Honesty constraints

- Re-run what is re-runnable (tests, hashes, probes). CPU-only; nothing here needs GPU.
- Everything outside my dir is READ-ONLY. Adversarial probes run against in-memory
  copies / temp files outside the repo (system temp), never against repo files.
- Report greens AND reds with numbers. A red on C4 or C5 is not tuned away; it is either
  an amendment (binding) or a rejection reason.

## Verdict rule (frozen)

- Any C1 mismatch, any C3 contradiction, any C4 red, any C5 falsifier fired => REJECTED
  or APPROVED-WITH-AMENDMENTS, never silent INTERFACE-APPROVED.
- Six rulings all APPROVE and everything else green => INTERFACE-APPROVED.
- Rulings with amendments, or fixable coherence/notes => APPROVED-WITH-AMENDMENTS with
  the amendment list stated as binding.
