# AMENDMENT A1 (DRAFT) — WK-LATENCY-20261002 prereg, clause L-P4

STATUS: DRAFT for Lieutenant commit. Amends the committed preregistration
`18e655824ab7c8a8a8b155eb7db129ddffee72dd54`
(`tools/monkey_campaign/contributions/WK-LATENCY-20261002/PREREGISTRATION.md`,
content sha256 `f3afb0f6084b04c546355b104dd2f6274fa04f4eaa4a1e64529b30ce73d62a7f`).
Defect source: attribution-law review, evidence file `3b7c1dcd`, section
advisories (routed by the Lieutenant, chain stop 2 defect stop).

HONESTY RECORD: NO Phase B measurement ran under the defective bytes. The
defect stop arrived before any seal, run, capture or diff existed; nothing is
discarded and no result carries in either direction.

## 1. The defect (one clause, L-P4 clock_conversion, self-contradictory as frozen)

Frozen clause 1 asserted `L_pixel_ms(n) = presented_now_ms(f*) -
input_now_ms(T_in(n))`. Under the pinned clock law
`now_ms(tick) = tick*1000//300` both terms are FLOORED integers, so clause 1
is an integer number of milliseconds. Frozen clause 2 asserted
`L_pixel_ms(n) = L_pixel_ticks(n) * 1000/300` "exactly" — a rational with
denominator 3. The two agree only when `L_pixel_ticks(n) ≡ 0 (mod 3)`;
on the frozen domain `L_pixel_ticks(n) in [1, 45]` that is 15 of 45 values,
so 30 of 45 honest outcomes would be phantom violations. Concrete: T_in =
4351, first differing frame tick 4352: clause 1 gives
`now_ms(4352) - now_ms(4351) = 14506 - 14503 = 3` ms; clause 2 gives
`1 * 1000/300 = 10/3` ms.

## 2. The amendment (replacement clause, whole)

- L-P4 `clock_conversion`: BY DEFINITION
  `L_pixel_ms(n) := L_pixel_ticks(n) * 1000/300` on the injected clock
  (`1000/300` ms per tick; the frozen per-tick constant). This definition is
  THE recorded latency in the milliseconds domain; per class (FWD/TURN) it
  is reported as min/median/max over the 5 declared repeats plus the full
  per-repeat series in the receipt.
  L-P4a `clock_crosscheck` (recorded cross-check, not a definition): for
  every pair, the floored-integer clock difference
  `presented_now_ms(f*) - input_now_ms(T_in(n))` is ALSO recorded and must
  satisfy `|recorded_difference - L_pixel_ms(n)| <= 2/3` ms. The bound 2/3 ms
  is exact and tight: with `r(t) = t*1000 mod 300 in {0, 100, 200}`,
  `now_ms(a) - now_ms(b) = (a-b)*1000/300 - (r(a)-r(b))/300`, so the
  deviation is `(r(b)-r(a))/300 in [-2/3, +2/3]` ms for every honest
  outcome. A deviation outside 2/3 ms means the presented or input timestamp
  is not the frozen function of its tick: FINDING `clock_anomaly`
  (recorded, never tuned; it would impeach the cadence denominator and
  every L-P4 number).
  The wall-clock honesty law is UNCHANGED: all milliseconds remain
  injected-clock arithmetic, verdict `unqualified` against any SLA while the
  P06 `network-latency-sla-ms` operator decision stands (prereg sections
  6 and 8 item A2).
- L-P4b `presentation_order_invariant` (advisory 3, ACCEPTED): whenever both
  exist, `presented_tick(f*_pixel) >= presented_tick(f*_state)`; a pixel
  reflection cannot precede the state frame that carries the command's
  effect. Violation = FINDING `order_invariant_violation`.

## 3. Advisories dispositions (review evidence 3b7c1dcd)

1. Cite U07 P5/P10 by name in L-P1a's determinism extension — ACCEPTED. The
   frozen L-P1a already re-executes B and requires identical state chains;
   this amendment names the heritage its frame-byte extension relies on:
   U07's sealed P5 (the repeatable-scene determinism law: byte-identical
   re-execution under the declared normalization) and U07's sealed P10
   (the render consumes records only and writes no run state), so the
   B-re-render piped-frame-sha equality, transited through the A4-proven
   lossless FFV1 codec (decode == piped, per committed video), is the P5
   law carried to the frame-byte layer. No behavior change; citations only.
2. Tighten L-P1c to `consumed+14` — ACCEPTED IN INTENT, CORRECTED FORMULA
   (the formula as stated would contradict the render contract). On this
   line the presented frame at tick p renders the run's own state AT p
   (`pose_at(row_at(p))`; U07's sealed presented-lag law is presentation
   BOOKKEEPING, not deferred-state rendering). The command's chain consumed
   at c changes the state from tick c onward, so the first presentation
   slot at which a nonzero diff is LAWFUL is the first PRESENT_TICK
   `p >= c` — which on the declared 15-tick grid with `c ≡ 1 (mod 15)` is
   exactly `c + 14`. AMENDED L-P1c: the zero-diff law binds every slot with
   `presented_tick < c`, stated WITH the explicit boundary that the first
   slot `>= c` (== `c + 14` on the declared grid) is where L-P1c hands
   jurisdiction to L-P3; requiring zero at `p = c + 14` itself would make
   L-P1c unsatisfiable whenever the command has a same-frame pixel effect,
   which is the same class of defect A1 just removed from L-P4.
3. Record the presentation-order invariant — ACCEPTED (L-P4b above).

## 4. Effect on the frozen design

Nothing else changes: N = 10 pairs (FWD/TURN x 5), T_in(n) = 4351 + (n-1),
the window and stride, the ROI law, L-P1a/L-P1b/L-P1c (as corrected in
section 3 item 2), L-P2, L-P3, L-P5, L-P6, L-P7, the probes and views, the
boundary claims (sections 0, 6, 8) and the publication mechanics (section 9)
all stand as committed. The amendment is committed ALONE first (the
M03/P04 law); the fresh review covers the amended revision; Phase B
re-releases only after the Lieutenant's pin of THESE bytes.
