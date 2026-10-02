# AMENDMENT A3 — MAT2-U07 preregistration (the P7 observable correction;
# dev-refuted, frozen BEFORE the sealed run; no receipt exists yet)

## What the development run refuted

Dev run (2026-10-01, attempt scratch): AMENDMENT-A2's corrected R4 (press,
release, silence) shows the seam's decay landing on an EXACT-ZERO record at
issued tick 615 and then silence — and ZERO consumer-expiry revert events.
The reason is the adapter's own declared equivalence: the zero-demand
projection IS the declared idle/inert projection (W10's sealed comment:
"the declared idle floor projection (identical to the zero-demand
projection)"). The consumer is therefore already on the inert path when the
last record goes stale; the `applied != idle` revert event has nothing to
revert. On a healthy injected clock the expiry contract is a BELT that no
healthy arm ever needs: the mapper re-issues held keys (A2) and lands
released keys on exact zero (A3). A prediction demanding a revert EVENT on a
healthy arm demands an unhealthy stream.

## The corrected P7 (the honest observable law)

- R4 arms (unchanged script): press W at tick 300, release at tick 600,
  horizon 1200.
- P7 variables:
  - `zero_record_is_last` == true (the stream's last record is the
    exact-zero record, issued within the pinned RELEASE_DECAY_MS + one poll
    of the release);
  - `no_positive_record_after_decay_deadline` == true (stuck-command
    prevention after silence);
  - `consumer_at_inert_after_last_record` == true (the applied projection
    after the last record equals the declared idle projection);
  - `first_revert_age_ticks` is recorded as `null` with the DECLARED reason
    `no_stale_noninert_record_on_healthy_clock` — the revert EVENT is not
    produced on any healthy arm;
  - the expiry LAW itself (age > EXPIRY_TICKS) is executed at the unit level
    in the named-check suite against the pinned pure law (age 30 -> False,
    age 31 -> True) — the belt's bite is proven where it exists.
- The stuck-command falsifier clause remains executed by R4 (zero-then-
  silence), R3 (wrong-key script) and R5 (blur drop + decay), plus the unit
  expiry law.

## Unchanged

P1 (as amended by A1), P2-P6, P8-P12 stand. The sealed receipts embed all
four sha256s (`preregistration_sha256`, `amendment_a1_sha256`,
`amendment_a2_sha256`, `amendment_a3_sha256`) and refuse any mismatch.
