# AMENDMENT A1 — MAT2-W10 preregistration (pinned-authority addition)

Disclosed BEFORE any implementation commit and BEFORE any experiment
(the amendment law: separate commit, before the runs, disclosing what changed
and why). PREREGISTRATION.md itself is untouched; its live bytes stay the
seal authority. This amendment adds ONE input pin and declares its role.

## What changed

Section 1 (Input pins) gains one base-blob pin, verified at freeze:

- `tools/monkey_campaign/contributions/MAT2-W09/out_of_envelope.py`
  `7245739a746aaeb259a2720c97dbdfec4a88b77aed997cd0c9f961f5ca89d782`

## Why

Prereg section 2 step 8 replays W09's declared unsupported probe (arm R4)
and prereg section 0/7 attach the sealed W09 supervisor in its declared role
(observation monitor on the clean arms; the R1/R2 response owner on R4).
The supervisor's bytes are the sealed W09 card module in the shared object
database at this card's base — the same read-only import-identity pattern
the prereg already declares for the machinery and seam. Freezing the plan
without pinning the instrument that executes a frozen response table would
leave a replay arm unbound to its sealed authority; the pin closes that gap
before anything runs. Every detector the prereg names (velocity recursion,
phase recursion, micro draw chain, support-force removal, warm force
crosscheck, energy account) is consumed from these pinned bytes, never
re-implemented.

## Receipt binding

Every W10 receipt records BOTH `preregistration_sha256` (the live
PREREGISTRATION.md bytes) and `amendment_a1_sha256` (the live AMENDMENT-A1.md
bytes) and refuses any document whose recorded values do not match.
