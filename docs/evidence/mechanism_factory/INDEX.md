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
- `qualification_receipt_20261016T011306.154827Z.json` — multi-point
  qualification-case receipt (schema
  `chimera-mechanism-factory-qualification-receipt-v2`), written by
  `tools/mechanism_factory/qualification_cases.py`: 5 vertical load
  magnitudes per train/validation family across the admitted domain
  (train 0.4-2.0 N, validation 0.2-1.8 N; frozen fixtures; the pinned
  writer's `run_case` solve path and negative controls; each case
  records its own `load_magnitude_N`). Adapter verdict: PASS
  (recomputed + declared). Provenance (writer file hash, solve
  parameters) recorded in the receipt's `provenance` block; the
  holdout family is never run.
- `fit_receipt_20261016T022858.761939Z.json` — bounded-table fit+eval
  receipt, schema `chimera-mechanism-factory-fit-eval-v1`
  (`tools/mechanism_factory/bounded_fit.py`, P3). Labels only from
  adapter-PASSed receipts (3 receipts refused and recorded); 5 knots
  per family after cross-writer deduplication (identical reactions at
  the shared magnitudes — consistency witness passed). Bounded PCHIP
  interpolant (monotone cubic in |f|, method config #1; no overshoot,
  no extrapolation past knots; out-of-domain refused by name). Table
  hash bd2876120ed65f06...; seed 0; cost wall 48.7 s, traced peak
  8.6 MiB. Validation max/mean reaction error at the knots 0.0/0.0 N
  (tolerance 1e-6 N). Shadow latency: table query 24.8 us vs
  reference solve 15.29 s mean. Holdout: seen, 0 read,
  `no_final_test_access: true`. **TABLE REJECTED at the preregistered
  interpolation gate**: leave-one-out max error 1.44e-4 N vs the
  1e-6 N gate (PCHIP improved on the linear table's 3.94e-4 N but
  does not reach the reference's own error scale; measured curve
  recorded per knot: train 9.7e-6 @0.8, 2.2e-5 @1.2, 7.1e-5 @1.6;
  validation 1.2e-5 @0.6, 3.3e-5 @1.0, 1.4e-4 @1.4). The
  learned-candidate hook is therefore flipped:
  `learned_candidate_deferred_gpu_seam` — the learned candidate is
  justified. The PCHIP implementation was CPU-verified against
  scipy's `PchipInterpolator` (5/5: slopes, values, knot
  reproduction, monotone/no-overshoot, real-table LOO agreement to
  1e-12 N; math-tools evidence
  `Runtime/local-ai/math-tools/results/20261015-211510-d9656b3c`).
- `gpu_fit_manifest_20261016T030615.852906Z.json` +
  `gpu_manifest_receipt_20261016T030615.852976Z.json` — §11.18 GPU
  learned-candidate batch manifest (implementation-only seam; no live
  reservation taken), schema
  `chimera-mechanism-factory-gpu-manifest-v1`, manifest sha256
  7a9a23587eb955ac29b8d0d1eefc58df4fbdbd967a94c6a1716e50b3de89276d.
  One job (learned_candidate_fit, Strata venv python, timeout 600 s,
  seed 1729 per the reference bounded fit), packet budgets verbatim
  (time_s 300, ram_mb 512) plus preregistered VRAM/disk headroom,
  packet checkpoint policy and stopping conditions verbatim
  (OOM fails the job — no silent precision/step/case changes), the
  release-in-cleanup contract, and the no-LLM-call law (no
  router/HTTP marker in any command; build-time and dry-run
  enforcement). Fixtures: 5 knots per train/validation family derived
  from the adapter-PASSed receipts (holdout excluded structurally);
  label receipts + packet sha-pinned in `identities` so gpu_batch
  refuses the batch if any input changes. The fit job script is
  authored in the next seam, so the manifest carries it as a pending
  input and `eligible_for_live_batch` is false — the live command is
  documented in `tools/mechanism_factory/GPU_LIVE_BATCH.md` as NOT
  YET RUN.
- `gpu_fit_dryrun_20261016T032645.207808Z.json` — dry run, schema
  `chimera-mechanism-factory-gpu-dryrun-v1`, clean (all structural
  validations PASS through gpu_batch.load_plan's own law). Reservation
  verdict: `reservation_available_not_taken` — the read-only
  `run_gpu_job.py --check` probe (no HTTP call, no model touch) found
  the lock free and released it immediately; a refused probe (exit 75)
  would have recorded `reservation_unavailable` as an expected dry-run
  outcome.
- `gpu_fit_checks_20261016T032644.947848Z.json` — manifest/dry-run
  falsifier battery, 6/6 green: (a) manifest determinism (in-memory
  build reproduces the stamped artifact's sha256 exactly), (b) holdout
  absent from operative sections + split gate reads 0 holdout cases +
  `refusal_holdout_fixture` fires, (c) timeout > 600 s and
  missing-budget builds refused by name, (d) LLM/router invocation in
  a job command refused (`llm_call_in_job_command`), (e) build with
  no qualified receipt refused (`no_qualified_receipt`), (f) real
  dry run exits 0 without a reservation and records its verdict.
- `bounded_fit_checks_20261016T021808.526204Z.json` — fit falsifier
  battery, **7/7 green**: T1 determinism, T2 unqualified receipts
  refused as label sources, T3 structural holdout sentinel untouched,
  T4 out-of-domain refused by name, T5 knot-point error within the
  preregistered packet tolerance, T6 fit-receipt honesty, T7 GATE
  CONSISTENCY (the table is either qualified at the preregistered
  leave-one-out gate or explicitly rejected with the hook flipped —
  a silently-passed over-gate table trips it). Current run: the
  rejection branch is active and internally consistent.
- `adapter_faults_20261016T022755.396222Z.json` — fault-injection
  suite rerun after the PCHIP work, F0-F12 green.

Stale (retained, do not consume):

- `fit_receipt_20261016T013441.544043Z.json` — STALE: fit receipt for
  the LINEAR interpolant, superseded by
  `fit_receipt_20261016T022858.761939Z.json` (PCHIP, method config
  #1). Its recorded 6/7 battery run
  `bounded_fit_checks_20261016T012234.469338Z.json` is likewise
  superseded: T7 then asserted that the table WINS the gate and
  failed on the real finding (LOO max 3.94e-4 N, curve recorded
  there); T7 now asserts gate consistency instead. Retained as the
  measured points-vs-error record for the linear method.
- `bounded_fit_checks_20261016T001508.538640Z.json` — STALE: 6/6
  green run against the SINGLE-POINT table (before multi-point knots
  existed; T7 not yet defined).
- `adapter_faults_20261016T013305.431120Z.json` — STALE: green
  F0-F12 run superseded by
  `adapter_faults_20261016T022755.396222Z.json` (rerun after the
  PCHIP work).
- `fit_receipt_20261016T002559.959110Z.json` — STALE: single-point
  fit receipt, superseded by `fit_receipt_20261016T022858.761939Z.json`.
  Retained as the degenerate-interpolant record.
- `qualification_receipt_20261016T005949.067106Z.json` — STALE:
  first multi-point draft; `qualification_cases.py` was edited
  immediately after generation (cases must record their own
  `load_magnitude_N`), so its `solver_hash_mismatch:
  tools/mechanism_factory/qualification_cases.py` refusal is
  genuine and permanent. Superseded by
  `qualification_receipt_20261016T011306.154827Z.json`; case numbers
  are identical.
- `bounded_fit_checks_20261015T214016.502526Z.json` and
  `bounded_fit_checks_20261015T215807.597345Z.json` — STALE:
  retained FAILING runs in which T3's sentinel probe searched raw
  canonical bytes for "777", which a genuine reaction value
  (0.00889664220777553) contains; kept as the record of why the
  probe was made structural.
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
