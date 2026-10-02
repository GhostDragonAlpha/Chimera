# AMENDMENT A2 — MAT2-U07 preregistration (the R4 correction; dev-refuted,
# frozen BEFORE the sealed run; no receipt exists yet)

## What the development run refuted

Dev run (2026-10-01, attempt scratch): prereg R4 as originally frozen —
"press W at the start, NEVER release, no further input events; the consumer
expiry contract must revert the consumer to the inert path; first revert at
age 31" — is REFUTED BY THE SEAM'S OWN LAW: the pinned U01 InputMapper
RE-ISSUES the held demand at every 50 ms poll (observed: records at issued
ticks 300, 315, 330, 345, ... with no gap), so the consumer-side record age
never exceeds the expiry floor while a key is HELD. The expiry contract
guards the record stream after it goes SILENT (W08's sealed framing: "a
record older than EXPIRY_TICKS reverts the consumer") — a held key is a
continuously renewed stream, not a stale record. The original R4 would have
produced zero reverts and a red prediction against a CORRECT seam.

## The corrected R4 (the release/silence expiry law)

- R4 script: press W at tick 300, RELEASE at tick 600, no further input
  events, horizon 1200 ticks. The pinned decay lands the stream on an exact
  zero record and then SILENCE; the last record (the zero) goes stale and
  the consumer must revert to the inert path at
  `age == EXPIRY_TICKS + 1 == 31` ticks after the last record (the
  `> EXPIRY_TICKS` law).
- P7 variables (renamed explicitly): `first_revert_age_ticks == 31`;
  additionally `zero_record_is_last` (the stream's last record is the
  exact-zero record) and `no_positive_record_after_first_revert` (the
  stuck-command prevention: after the revert the applied vector stays the
  declared idle/inert projection without new records).
- The stuck-command falsifier clause is executed by R4 (silent-stream
  expiry), R3 (wrong-key script) and R5 (blur drop + decay), exactly as the
  card falsifier requires; the ARM CHANGES, the LAW does not.

## Unchanged

P1 (as amended by A1), P2-P6, P8-P12 stand. This amendment is part of the
frozen preregistration set; the sealed receipts embed all three sha256s
(`preregistration_sha256`, `amendment_a1_sha256`, `amendment_a2_sha256`)
and refuse any mismatch.
