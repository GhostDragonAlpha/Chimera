# DEV_RUN_REFUSALS — MAT2-W08 (candidate-scoped honest-failure record)

Every named refusal fired by the development runs of this card, BEFORE any
sealed run, with the derivation that was wrong and the fix. The frozen
prereg (`PREREGISTRATION.md`, sha `00a04e08411ed079aee9e0ef43f9221c69abc84612f66311e4db4822f6c8412a`)
narrates the resulting amendments and names only the P4 segment-range
refusal; THIS file is the complete coded record the submission prose refers
to. The prereg bytes were never edited after the first sealed run.

All development runs were executed from the attempt working directory
against the same pinned inputs as the sealed run (base
`8b285ee4301a8ed42be54a1924af5db019f9fb20`); each refusal stopped the
harness before any receipt existed. Five refusals across four codes (P9
fired twice, for two distinct defects).

## 1. `prediction_failed:P4_band_entry` (dev run 1)

- Wrong derivation: the first P4 draft claimed the achieved speed ENTERS the
  derived ceiling band by tick 2526, from the formula
  `t >= ln((band_hi - v0_ub)/(band_hi - band_lo))/d_lo = 2225 ticks`. The
  inequality was applied in the wrong direction: the d_lo bracket bounds how
  FAST the speed can possibly approach (an upper bound on the closed-ness of
  the gap), which upper-bounds the rise, not the crossing. The true crossing
  time depends on the warm-cache path — the achieved fixed point
  `a/d_eff(warm)` can sit arbitrarily close to the band's low edge, making
  the crossing arbitrarily late; no finite crossing bound follows from the
  declared constants alone.
- Fix: P4 was reformulated to claims that ARE derivable — monotone rise
  while below the band, onset latency <= the 15-tick hold, and the
  segment-end two-sided comparison range (see refusal 2 for the constant
  correction); the measured band-entry tick is recorded informationally.
  P7 received the same treatment.

## 2. `prediction_failed:P4_segment_range` (dev run 2)

- Wrong derivation: the first segment-range evaluation used the effective
  damping span `[DAMPING*WARM_DAMP_LO, DAMPING] = [0.3325, 0.35]`. The
  pinned scene's step law is
  `d_eff = DAMPING*(WARM_DAMP_LO + WARM_DAMP_SPAN*warm_mean)` with
  `WARM_DAMP_SPAN = 0.10`, so the true span is `[0.3325, 0.3675]` — its top
  EXCEEDS nominal damping. The mis-derived low edge (0.762517 m/s) sat above
  the measured segment-end speed (0.746082 m/s in that draft's projection)
  and the range detector refused.
- Fix: the span constants were re-read from the pinned bytes
  (`warm_damp_span` added to the derived-constant set), the projection was
  changed to the NOMINAL-damping inversion (`s = v_cmd*damping/g`; the
  declared band straddles the demand), and the tracking bound became the
  largest distance from the demand to the derived band edges
  (0.040190790 m/s). The certified velocity envelope (2.977443609 m/s) uses
  the span's LOW edge and was never affected.

## 3. `prediction_failed:P5_in_range_yaw` (dev run 3)

- Wrong derivation: the frozen input script fed +400 mouse counts per
  boundary, assuming the port's yaw is `counts*sensitivity`. The pinned
  mapper's `_yaw_demand` is a RATE law: `raw = counts*sensitivity/interval_s`
  (counts are a per-interval displacement), so 400 counts clipped at
  OMEGA_MAX (1.6 rad/s) and every "in-range" record carried 1.6, not 0.8.
- Fix: the script feeds 20 counts per 50 ms interval
  (`20*0.002/0.05 = 0.8 rad/s`); the seam-max row (key "A", 1.6 rad/s)
  remains the declared saturating case. The prereg's section 4.1 table was
  amended accordingly.

## 4. `prediction_failed:P9_physical_separation` (dev runs 4 AND 5)

- Dev run 4 — wrong injection design: the probe injected ONE wrong record at
  the stop boundary. The pinned mapper declares a CONSUMER-SIDE expiry
  contract naming this card (`is_expired`: a record older than
  EXPIRY_TICKS = 30 reverts the consumer to the seam's inert path), which
  the adapter implements — so a single injected record drove the plant for
  only 30 ticks before the revert, and the wrong/clean separation at tick
  5999 collapsed to noise (0.538097 vs 0.529942 m/s). The expiry law was
  working correctly; the probe design was not.
- Fix: the probe was re-declared as the WRONG-KEY SCRIPT (the wrong operator
  presses "W" at the stop boundary and holds it; the clean S segment never
  happens in R3), which is the operator-level falsifier the card names.
  Prefix identity through tick 5430 is preserved.
- Dev run 5 — stale bracket in code: after the script fix, the code's
  r3_lower bracket still used the draft formula anchored at the demand
  (`v_cmd - (v_cmd - v_prefix)e^{-d_hi*t}` = 0.753037 m/s), while the
  amended prereg bracket is anchored at the a/d_hi fixed point
  (`a/d_hi + (v_prefix - a/d_hi)e^{-d_hi*t}` = 0.734785 m/s). The measured
  wrong-run speed (0.747213 m/s) sat between them: the code refused on a
  formula that no longer matched the prereg. The code was aligned to the
  prereg's bracket (the valid one: the lower comparison bound against the
  a/d_hi fixed point at the fast rate holds for every d_eff path).

## Outcome

Dev run 6 onward: every frozen prediction green, first in the development
directory and then byte-identically inside the sealed runner slot
(job `b00e72c24e1e463ea06cb3bbef391890`). The prereg was amended in five
recorded editing rounds, all before the first sealed run; each amendment is
narrated in the frozen prereg itself (section 3 preamble, P4, P7, section
4.1, 4.2, 4.4).
