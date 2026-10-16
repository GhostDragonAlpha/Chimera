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
- `gpu_fit_manifest_20261016T040553.303266Z.json` +
  `gpu_manifest_receipt_20261016T040553.303324Z.json` — §11.18 GPU
  learned-candidate batch manifest, schema
  `chimera-mechanism-factory-gpu-manifest-v1`, manifest sha256
  874ec7031242a5877d66a58926f9956b6baaef1d450ece9de518c83ec6cca96d,
  `eligible_for_live_batch: true`. One job (learned_candidate_fit:
  `fit_job.py --device cuda --seed 1729 --packet ...`, timeout 600 s,
  seed 1729 per the reference bounded fit), packet budgets verbatim
  (time_s 300, ram_mb 512) plus preregistered VRAM/disk headroom,
  packet checkpoint policy and stopping conditions verbatim (OOM
  fails the job — no silent precision/step/case changes), the
  release-in-cleanup contract, and the no-LLM-call law. Fixtures: 5
  knots per train/validation family derived from the adapter-PASSed
  receipts (holdout excluded structurally); packet, label receipts and
  `fit_job.py`'s exact bytes are sha-pinned in `identities` so
  gpu_batch refuses the batch if any input changes. The live command
  is documented in `tools/mechanism_factory/GPU_LIVE_BATCH.md` as NOT
  YET RUN.
- `fit_job_receipt_20261016T035302.105613Z.json` +
  `fit_job_checkpoint_20261016T035302.105509Z.json` — P3 fit stage
  proper, schema `chimera-mechanism-factory-fit-job-v1`
  (`tools/mechanism_factory/fit_job.py`, CPU smoke fit): small torch
  MLP response operator (pin angle, load magnitude, fixture geometry
  -> pin reaction components), seed 1729, labels only from the
  adapter-PASSed receipts through the SAME split gate the sentinel
  check proved. Deterministic: repeat runs give the identical
  checkpoint sha256 db6525b61d992112...; stopping max_epochs (3000);
  wall 3.5 s, traced peak 0.2 MiB (packet budgets enforced; breach
  fails the job cleanly). **VALIDATION MAX ERROR 3.3668e-02 N vs the
  preregistered 1e-6 N gate -> `physically_qualified: false`** (the
  gate was not lowered; the learned candidate — like the bounded
  table — does not reach the reference's own error scale; the next
  decision, more data via GPU characterization batch vs accepting the
  reference, is referred back). Receipt carries
  `no_llm_calls: true` and is verified by `fit_job.py`'s own
  verifier (forge -> named refusal).
- `fit_job_checks_20261016T040453.179798Z.json` — fit-stage falsifier
  battery, 5/5 green: (a) determinism (two runs, identical checkpoint
  hash + validation error), (b) holdout sentinel never read (merged
  adapter-PASSable sentinel receipt -> identical checkpoint hash,
  holdout_cases_read 0, no sentinel value in either artifact),
  (c) budget breach -> clean failure (exit 1, receipt records
  budget_breach, physically_qualified false), (d) receipt honesty
  (clean verifies; forged flag/seed/holdout-read/no-LLM/checkpoint
  hash each refused by name), (e) manifest regeneration pins
  fit_job.py and flips eligibility.
- `gpu_fit_checks_20261016T040612.400941Z.json` — manifest/dry-run
  battery rerun after the regeneration, 6/6 green (determinism now
  reproduces the NEW manifest's sha256).
- `gpu_fit_dryrun_20261016T040553.519171Z.json` — dry run on the
  regenerated manifest, clean; reservation verdict
  `reservation_available_not_taken` (read-only probe).
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

- `gpu_fit_manifest_20261016T030615.852906Z.json` (+ manifest receipt)
  — STALE: first manifest, sha256 7a9a23587eb955ac..., which carried
  `fit_job.py` as a PENDING input (`eligible_for_live_batch: false`)
  and pointed the job at the old planned script name. Superseded by
  `gpu_fit_manifest_20261016T040553.303266Z.json` (script authored and
  pinned; job executable moved to the torch-bearing local Python).
- `gpu_fit_dryrun_20261016T032645.207808Z.json` and
  `gpu_fit_checks_20261016T032644.947848Z.json` — STALE: validated the
  superseded manifest; rerun clean against the regenerated one
  (`gpu_fit_dryrun_20261016T040553.519171Z.json`,
  `gpu_fit_checks_20261016T040612.400941Z.json`).
- `fit_job_receipt_20261016T034921.208926Z.json` (+ checkpoint) —
  STALE: first stamped CPU fit run; its checkpoint was raw float64
  bytes (nondeterministic archive formats avoided, but the opaque
  artifact was replaced by a deterministic JSON checkpoint). Same
  training data and validation error as
  `fit_job_receipt_20261016T035302.105613Z.json`.
- `fit_job_receipt_20261016T040208.820815Z.json` and
  `fit_job_receipt_20261016T040521.852816Z.json` — the T3 battery's
  budget-breach failure records (kept: evidence the breach path writes
  an honest failure receipt and never a partial success).
- `fit_job_checks_20261016T040139.919918Z.json` — STALE: first battery
  run, 2/5 (T3's receipt parse missed the failure-receipt line, T4
  picked a breach record as latest, T5 ran before the manifest pointed
  at `fit_job.py`); all three fixed, rerun 5/5 green (above).
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
