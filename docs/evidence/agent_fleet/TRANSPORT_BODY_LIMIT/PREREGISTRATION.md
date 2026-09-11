# fleet-transport-body-limit-01 preregistration (2026-09-11, lead lane)

Task: `fleet-transport-body-limit-01` generation 1, slot 2, worktree
`E:\ChimeraWork\slot-02`, base `95f25b33aff1cc4d03e6c9a0d9cf10005ca085a2`
(integration tip; all wave-2 PRs #49-#54 merged).

**Discovered live (retained context):** the first full catalogue import —
the GOV-01 clause-4 named milestone — was refused by the HTTP transport:
`service.py` `MAX_BODY=65536` (64 KB) versus the canonical payload measured
at this tip at **1,518,593 bytes** (envelope digest `dc1b860f...`; local
`validate_payload` returns no errors, `payload_digest` matches the builder
envelope). The refusal was `request_size` (409); the existing tests import
only in-process, so the gap was never exercised. No store write occurred.

- **STATEMENT**: the live transport admits the canonical full catalogue
  payload when the body cap is raised to a derived bound; the cap is
  transport policy, not physics (its own source comment says so).
- **DERIVATION (Rule 1, not taste)**: measured payload 1,518,593 B; the
  payload scales with the Master list + holodeck corpus, which can
  realistically double; headroom factor 8 → 12,148,744 B; rounded to the
  power-of-two transport convention → 16,777,216 B = 2²⁴ (16 MiB).
- **PREDICTION**: with `MAX_BODY = 2**24`, the deployed service accepts the
  exact canonical payload through `catalogue_import` (validated,
  digest-recorded); a body above the limit still refuses `request_size`
  (regression with a synthetic oversized body); bearer/envelope refusals
  unchanged; the full fleet suite stays green including the new regression.
- **FALSIFIER**: any body above the limit accepted; payload validation
  weakened; direct DB writes used instead of the reviewed transport; or the
  change deployed without the documented controlled transition (rehearsal,
  backup, quiescence, authorized stop/start, post-comparison).

Deployment happens ONLY through the documented controlled transition
executed by the lead after review + merge; nothing live is mutated by this
branch. The import retry itself is post-transition and recorded separately.
