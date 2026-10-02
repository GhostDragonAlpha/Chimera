# AMENDMENT A1 — MAT2-U07 preregistration (the P1 correction; dev-refuted,
# frozen BEFORE the sealed run; no experiment evidence exists yet)

## What the development run refuted

Dev run (2026-10-01, attempt scratch, no receipt produced): prereg P1 as
originally frozen — "over EVERY R1 chain, `command_emitted.t_ms -
input.t_ms <= 50.0`" — is REFUTED BY THE ACCEPTED MODULE'S OWN LAW, not by
the runtime: the I-U07-TRACE-FOLLOWUP adapter (PR #145 bytes) attaches each
chain's `input` stage as "the adapter's latest observed key-state transition
at or before the emission" and records that "several re-issued commands
lawfully share one press" (`payload.transition_index`). While a key is held,
every re-issued poll chain therefore carries the ORIGINAL press as its input
stage, and `seg_input_to_command_ms` grows with the hold duration (observed:
403 chains, max 13950 ms — all sharing the W press at t=1000 ms). The
original P1 measured the wrong quantity and was REFUTED at dev time; this
amendment replaces it before the sealed run. Nothing was sealed or published
against the refuted form.

## The corrected P1 (named variables; same caller-data limit)

- P1 `first_response_ms_max`: for EVERY observed input transition
  (`payload.transition_index`), the FIRST chain re-emitted under that
  transition satisfies `command_emitted.t - input.t <= 50.0` ms (the seam
  poll INTERVAL_MS; C12 caller-data limit). Re-issued chains carry the
  shared antecedent by the accepted law; their `input->command` distance is
  the HOLD AGE — recorded informationally, never a responsiveness claim.
- The accepted-module cadence check (P11) is re-scoped to the FIRST-RESPONSE
  chains that lie in the declared render window (which exist: the A press at
  tick 4500 opens one); `seg_input_to_command_ms` over that subset carries
  the 50.0 ms caller-data limit. The wall-clock end-to-end verdict stays
  `unqualified` exactly as frozen.

## Unchanged

P2-P12 stand as frozen. The stage law, the one-clock law, the arms, the
views, the occluder box and every honest negative stand as frozen. This
amendment is part of the frozen preregistration set; the sealed receipts
embed BOTH sha256s (`preregistration_sha256`, `amendment_a1_sha256`) and
refuse any mismatch.
