# Mechanism factory evidence index (11.18)

Current (adapter-verifiable in a clean checkout of HEAD):

- `qualification_receipt_20261015T205346.498645Z.json` — genuine
  qualification receipt for the asymmetric constant-tension patch
  mechanism, schema
  `chimera-mechanism-factory-qualification-receipt-v2`; three CPU
  cases (stagnated at the machine-scale floor, all residuals under the
  packet thresholds). v2 records each case's
  `max_force_balance_residual` and `max_moment_balance_residual`, so
  `receipt_adapter.py` recomputes the packet's two balance thresholds
  through the same verdict-forgery path as the other thresholds.
  Verified by `tools/mechanism_factory/receipt_adapter.py`
  against `tools/mechanism_factory/example_packet.json` (PASS).
- `patch_equilibrium_receipt_20261015T123339.081217Z.json` — P1
  boundary/load solve falsifier battery, 6/6 (schema
  chimera-mechanism-factory-patch-equilibrium-v1).
- `adapter_faults_20261015T210124.045050Z.json` — fault-injection suite
  against the schema-v2 adapter, F0-F12 green (F12: a v2 receipt with a
  recorded balance residual above the packet threshold under a declared
  PASS is `verdict_forgery`). The earlier
  `adapter_faults_20261015T154126.354864Z.json` (worker run) and
  `adapter_faults_20261015T155352.835286Z.json` (independent verifier
  rerun) cover F0-F11 against the schema-v1 adapter and are retained.
- `fit_receipt_20261016T002559.959110Z.json` — bounded table fit+eval
  receipt, schema `chimera-mechanism-factory-fit-eval-v1`
  (`tools/mechanism_factory/bounded_fit.py`, P3). Labels come only from
  adapter-PASSed qualification receipts; the two stale receipts are
  recorded as `receipt_unqualified` /
  `receipt_schema_unsupported` and contribute nothing. Bounded
  nearest-neighbour table over train+validation families
  (fan-full-rim-pin, fan-full-rim-pin-alt-geometry), table hash
  e702b38438bedc16...; seed 0 (deterministic pipeline, no RNG);
  normalization from the packet; cost wall 49.0 s, traced peak 8.3 MiB.
  Validation max/mean reaction error 0.0/0.0 N vs the packet
  `max_force_balance_residual` tolerance 1e-6 N. Shadow latency:
  table query 59.6 us vs reference solve 15.12 s mean (~2.5e5x).
  Holdout: 1 case seen, 0 read, `no_final_test_access: true`. The
  learned-candidate hook refuses as `learned_candidate_not_justified`
  (later GPU-batch seam). Degenerate one-point-per-family
  interpolation is disclosed by the recorded off-point probe
  (0.9x load, error 2.7e-4 N, diagnostic, not gated).
- `bounded_fit_checks_20261015T214016.502526Z.json` and
  `bounded_fit_checks_20261015T215807.597345Z.json` — retained
  FAILING runs of the fit falsifier battery: T3's sentinel probe
  searched raw canonical bytes for "777", which a genuine reaction
  value (0.00889664220777553) contains; kept as the record of why the
  probe was made structural.
- `bounded_fit_checks_20261016T001508.538640Z.json` — fit falsifier
  battery, 6/6 green (T1 determinism, T2 unqualified receipt refused
  as label source, T3 structural holdout sentinel untouched, T4
  out-of-domain refused by name, T5 validation error within the
  preregistered packet tolerance, T6 fit-receipt honesty incl. seed,
  cost, recomputed table hash, `no_final_test_access` true).

Stale (retained, do not consume):

- `qualification_receipt_20261015T151456.178807Z.json` — STALE:
  generated 2026-10-15T15:14Z, but `qualification_receipt.py` was
  revised during seam 2b (adapter fault harness needed an importable
  writer) after generation, so its `source_file_hashes` no longer match
  any committed bytes. Superseded by
  `qualification_receipt_20261015T160534.073121Z.json`. Solver-change
  reason: writer refactor only; the three case numbers are identical.
- `qualification_receipt_20261015T160534.073121Z.json` — STALE:
  superseded by schema
  `chimera-mechanism-factory-qualification-receipt-v2`
  (`qualification_receipt_20261015T205346.498645Z.json`). Reason: v1
  receipts record only `energy_J`, `max_free_residual_N` and
  `reactions_N`, so the packet's force/moment balance thresholds were
  enforced at qualification time but not recomputable by the adapter
  alone; v2 adds the two balance-residual outputs, and the adapter now
  refuses v1 explicitly as `receipt_schema_unsupported`. The three case
  numbers are unchanged; only the outputs block was extended.

Line-ending note: the lab files `surface_energy_reference.py`,
`overdamped_descent.py`, `evidence_output.py` were CRLF in the lab
working copy when hashed; `text=auto` had normalized committed blobs to
LF, breaking receipt verification in clean checkouts. Blobs now hold the
hashed bytes and `.gitattributes` marks `tools/membrane_scale_lab/**`
and `tools/mechanism_factory/**` `-text` (checkout-invariant, per the
`docs/evidence/** -text` doctrine).
