# Mechanism factory evidence index (11.18)

Current (adapter-verifiable in a clean checkout of HEAD):

Coordinated doc bump (2026-10-16): `example_packet.json`'s
`verifier_identity` and `README.md` were updated from the schema-v1
wording to the v2 reality (adapter = `receipt_adapter.py`; v1 receipts
refused as `receipt_schema_unsupported`; balance-residual recomputation;
F12 verdict forgery; a new bounded-fit / learned-candidate / GPU-batch
section). Both files are graph-pinned, so the whole receipt chain was
regenerated in dependency order and the graph re-pinned
(`creature_graph.json`: read_first document oids re-absorbed,
verifier_inputs packet pin and committed-receipt pin moved to the new
stamps, old document versions retained as immutable graph nodes,
`check()` clean). Every pre-bump artifact is listed under Stale below:
the packet digest moved, so old qualification receipts are now
adapter-refused (`packet_digest_mismatch`) and old manifests' sha-pinned
`identities` no longer match. Measured numbers did not change (same
fixtures, same seed); only the packet identity moved.

- `composed_qualification_receipt_20261016T071604.131817Z.json` and
  `composed_qualification_receipt_20261016T071312.835237Z.json` — P5
  COMPOSITION receipts, schema
  `chimera-mechanism-factory-composed-qualification-v1`
  (`tools/mechanism_factory/composed_patch.py`): two qualified
  `high_degree_fan` patches joined into ONE apex-weld hourglass assembly —
  piece A (rim at z=0 pinned, apex UP = the SEAM, free, carrying the 0.8 N
  input load) and piece B INVERTED (apex welded down onto the seam, far
  rim at z=0.6 pinned = the OUTPUT port). SEAM OWNERSHIP recorded in the
  receipt: A owns the seam vertex, B references it (deduplicated;
  `seam_vertex_coordinate_mismatch` / `seam_owner_conflict` refused
  before any solve). The reference is ONE `solve_equilibrium` on the
  joined mesh (connectivity union, seam deduplicated) — no new physics.
  The adapter accepted the composed schema explicitly (versioned; the
  composed path reuses the packet's preregistered 1e-6 law and the same
  convergence/verdict-forgery machinery; F13 in the faults suite refuses
  a v0/unknown composed schema). Measured (scale 1.0): stagnated at the
  machine floor, free residual 5.3e-8, force balance 5.3e-8 N, moment
  balance 3.4e-16; per-block mean reaction norms A 0.0315 / B 0.0261
  (margin 0.170 > the C4 precedent 0.1); B-port net reaction 1.25 N vs
  ~1e-7 N for B alone unloaded (transfer real). Supported scale: the
  SAME assembly at 0.5x and 2.0x (packet size axis, n_rim untouched,
  load unchanged) — residuals 4.6e-8 / 1.0e-7, balances within the 1e-6
  law, margins 0.142 / 0.183. Adapter verdict (CLI, on 071312): **PASS**
  (recomputed + declared). The battery
  `composed_patch_receipt_20261016T071539.282973Z.json` is 7/7 green:
  (a) seam single-valued (no duplicate coordinates; one seam index with
  2x200 incident faces; free; seam force 5.3e-8 N), (b) coupled balance
  across both pin sets, (c) reduction — B alone unloaded flattens onto
  its pinned rim with dE = 0.0 vs the same fan without the placement,
  (d) transfer real (block margin 0.170; B-port delta 1.25 N), (e)
  seam/scale refusals by name, (f) supported scale, (g) TOPOLOGY
  WITNESSES (physics findings, reported not tuned away): a rim-to-rim
  weld with a FREE seam ring has NO equilibrium under this law
  (step_limit, residual 1.08 — the packet's own free-boundary exclusion
  at assembly scale) and a rim-to-rim weld onto a GROUNDED ring
  transmits NOTHING (B-port delta 0.0 bit-for-bit); hence the apex weld,
  the one topology with both equilibrium and real transfer.
- POST-P5 RERUN of every existing suite after the adapter gained the
  composed schema and the graph's adapter-file pins moved:
  `adapter_faults_20261016T071909.735094Z.json` (F0-F13 green; F13 new:
  a `composed-qualification-v0`/unknown schema is refused as
  `receipt_schema_unsupported`), `bounded_fit_checks_20261016T071909.944298Z.json`
  (7/7), `fit_job_checks_20261016T072736.582791Z.json` (5/5),
  `gpu_fit_checks_20261016T072806.716918Z.json` (6/6),
  `gpu_fit_dryrun_20261016T072807.462506Z.json` (clean,
  `reservation_available_not_taken`),
  `patch_equilibrium_receipt_20261016T072807.881870Z.json` (6/6), and
  pytest `test_workflow_checklist.py` 3 passed (`creature_graph.json`
  verifier_inputs pins for `receipt_adapter.py` and
  `receipt_adapter_faults.py` refreshed to the new bytes; `check()`
  clean). The pre-P5 suite stamps are superseded by these reruns and
  retained under Stale.
- `qualification_receipt_20261016T043801.479415Z.json` — genuine
  qualification receipt for the asymmetric constant-tension patch
  mechanism, regenerated against the bumped packet via the pinned
  writer; schema
  `chimera-mechanism-factory-qualification-receipt-v2`; three CPU
  cases (stagnated at the machine-scale floor, all residuals under the
  packet thresholds). Adapter verdict PASS (recomputed + declared;
  `receipt_adapter.py` recomputes the packet's balance thresholds
  through the same verdict-forgery path as the other thresholds).
- `qualification_receipt_20261016T043900.489112Z.json` — multi-point
  qualification-case receipt (same schema), written by
  `tools/mechanism_factory/qualification_cases.py`: 5 vertical load
  magnitudes per train/validation family across the admitted domain
  (train 0.4-2.0 N, validation 0.2-1.8 N; frozen fixtures; the pinned
  writer's `run_case` solve path and negative controls; each case
  records its own `load_magnitude_N`). Adapter verdict PASS
  (recomputed + declared). The holdout family is never run.
- `fit_receipt_20261016T043900.694301Z.json` — bounded-table fit+eval
  receipt, schema `chimera-mechanism-factory-fit-eval-v1`
  (`tools/mechanism_factory/bounded_fit.py`, P3), regenerated against
  the bumped packet. Labels only from adapter-PASSed receipts (3
  receipts refused and recorded); 5 knots per family after
  cross-writer deduplication (identical reactions at the shared
  magnitudes — consistency witness passed). Bounded PCHIP interpolant
  (monotone cubic in |f|, method config #1; no overshoot, no
  extrapolation past knots; out-of-domain refused by name). Validation
  max/mean reaction error at the knots 0.0/0.0 N (tolerance 1e-6 N).
  Shadow latency: table query 36.6 us vs reference solve 15.11 s mean.
  Holdout: seen, 0 read, `no_final_test_access: true`. **TABLE
  REJECTED at the preregistered interpolation gate**: leave-one-out
  max error 1.44e-4 N vs the 1e-6 N gate (PCHIP improved on the
  linear table's 3.94e-4 N but does not reach the reference's own
  error scale; measured curve recorded per knot: train 9.7e-6 @0.8,
  2.2e-5 @1.2, 7.1e-5 @1.6; validation 1.2e-5 @0.6, 3.3e-5 @1.0,
  1.4e-4 @1.4). The learned-candidate hook is therefore flipped:
  `learned_candidate_deferred_gpu_seam`. The PCHIP implementation was
  CPU-verified against scipy's `PchipInterpolator` (5/5: slopes,
  values, knot reproduction, monotone/no-overshoot, real-table LOO
  agreement to 1e-12 N; math-tools evidence
  `Runtime/local-ai/math-tools/results/20261015-211510-d9656b3c`).
- `patch_equilibrium_receipt_20261015T123339.081217Z.json` — P1
  boundary/load solve falsifier battery, 6/6 (schema
  chimera-mechanism-factory-patch-equilibrium-v1). Its inputs do not
  touch the bumped documents; the post-bump rerun
  `patch_equilibrium_receipt_20261016T044911.994703Z.json` is 6/6
  green with the recorded results unchanged.
- `gpu_fit_manifest_20261016T044124.832275Z.json` +
  `gpu_manifest_receipt_20261016T044124.832337Z.json` — §11.18 GPU
  learned-candidate batch manifest, schema
  `chimera-mechanism-factory-gpu-manifest-v1`, manifest sha256
  b20e0589574e5de9751abe3831ffea7adeb3eb3f1c2bc10913de1c13c0318e83,
  `pending_inputs: []`, `eligible_for_live_batch: true`. One job
  (learned_candidate_fit: `fit_job.py --device cuda --seed 1729
  --packet ...`, timeout 600 s, seed 1729 per the reference bounded
  fit), packet budgets verbatim (time_s 300, ram_mb 512) plus
  preregistered VRAM/disk headroom, packet checkpoint policy and
  stopping conditions verbatim (OOM fails the job — no silent
  precision/step/case changes), the release-in-cleanup contract, and
  the no-LLM-call law. Fixtures: 5 knots per train/validation family
  derived from the adapter-PASSed receipts (holdout excluded
  structurally); packet, label receipts and `fit_job.py`'s exact
  bytes are sha-pinned in `identities` so gpu_batch refuses the batch
  if any input changes. The live command is documented in
  `tools/mechanism_factory/GPU_LIVE_BATCH.md` as NOT YET RUN.
- `fit_job_receipt_20261016T044141.958228Z.json` +
  `fit_job_checkpoint_20261016T044141.958119Z.json` — P3 fit stage
  proper, schema `chimera-mechanism-factory-fit-job-v1`
  (`tools/mechanism_factory/fit_job.py`, CPU smoke fit): small torch
  MLP response operator (pin angle, load magnitude, fixture geometry
  -> pin reaction components), seed 1729, labels only from the
  adapter-PASSed receipts through the SAME split gate the sentinel
  check proved. Deterministic: repeat runs give the identical
  checkpoint sha256 db6525b61d992112...; stopping max_epochs (3000);
  packet budgets enforced (breach fails the job cleanly). **VALIDATION
  MAX ERROR 3.3668e-02 N vs the preregistered 1e-6 N gate ->
  `physically_qualified: false`** (the gate was not lowered; the
  learned candidate — like the bounded table — does not reach the
  reference's own error scale; the next decision, more data via GPU
  characterization batch vs accepting the reference, is referred
  back). Receipt carries `no_llm_calls: true` and is verified by
  `fit_job.py`'s own verifier (forge -> named refusal).
- `adapter_faults_20261016T044810.797759Z.json` — fault-injection
  suite rerun against the bumped packet, F0-F12 green (F12: a v2
  receipt with a recorded balance residual above the packet threshold
  under a declared PASS is `verdict_forgery`).
- `bounded_fit_checks_20261016T045355.854421Z.json` — fit falsifier
  battery rerun after the doc bump, **7/7 green**: T1 determinism,
  T2 unqualified receipts refused as label sources, T3 structural
  holdout sentinel untouched, T4 out-of-domain refused by name, T5
  knot-point error within the preregistered packet tolerance, T6
  fit-receipt honesty, T7 GATE CONSISTENCY (the table is either
  qualified at the preregistered leave-one-out gate or explicitly
  rejected with the hook flipped). Current run: the rejection branch
  is active and internally consistent.
- `fit_job_checks_20261016T045306.970480Z.json` — fit-stage falsifier
  battery rerun, 5/5 green: (a) determinism (two runs, identical
  checkpoint hash + validation error), (b) holdout sentinel never
  read (merged adapter-PASSable sentinel receipt -> identical
  checkpoint hash, holdout_cases_read 0, no sentinel value in either
  artifact), (c) budget breach -> clean failure (exit 1, receipt
  records budget_breach, physically_qualified false), (d) receipt
  honesty (clean verifies; forged flag/seed/holdout-read/no-LLM/
  checkpoint hash each refused by name), (e) manifest regeneration
  pins fit_job.py and flips eligibility.
- `gpu_fit_checks_20261016T044911.264376Z.json` — manifest/dry-run
  battery rerun against the regenerated manifest, 6/6 green
  (determinism reproduces the new manifest's sha256).
- `gpu_fit_dryrun_20261016T044811.006952Z.json` — dry run on the
  regenerated manifest, clean; reservation verdict
  `reservation_available_not_taken` (read-only probe).

Stale (retained, do not consume):

- `composed_qualification_receipt_20261016T071144.424155Z.json` — STALE:
  first composed receipt run; a build bug applied NO rigid scale (all
  three scale cases returned the unit-scale numbers verbatim). Fixed in
  `composed_patch.py`; superseded by the 071312 / 071604 receipts above.
  Retained as the bug record; never adapter-verified.
- PRE-P5 SUITE STAMPS (superseded 2026-10-16 by the post-P5 reruns
  above, because the adapter's accepted-schema set changed — composed-v1
  added explicitly, versioned — and the graph's verifier_inputs pins for
  `receipt_adapter.py` / `receipt_adapter_faults.py` moved):
  `adapter_faults_20261016T044810.797759Z.json` (F0-F12),
  `bounded_fit_checks_20261016T045355.854421Z.json` (7/7),
  `fit_job_checks_20261016T045306.970480Z.json` (5/5),
  `gpu_fit_checks_20261016T044911.264376Z.json` (6/6),
  `gpu_fit_dryrun_20261016T044811.006952Z.json` (clean),
  `patch_equilibrium_receipt_20261016T044911.994703Z.json` (6/6). All
  were green at their time; retained.

- PRE-DOC-BUMP CHAIN (superseded 2026-10-16 by the coordinated packet/
  README doc bump above): the packet digest changed, so these are
  refused by the current adapter (`packet_digest_mismatch`) or pin
  inputs whose hashes no longer match. Retained in full:
  `qualification_receipt_20261015T205346.498645Z.json` (the pre-bump
  genuine receipt), `qualification_receipt_20261016T011306.154827Z.json`
  (the pre-bump multi-point receipt), `fit_receipt_20261016T022858.761939Z.json`
  (PCHIP fit), `gpu_fit_manifest_20261016T040553.303266Z.json` +
  `gpu_manifest_receipt_20261016T040553.303324Z.json` (manifest sha
  874ec7031242a587...), `fit_job_receipt_20261016T035302.105613Z.json`
  (+ `fit_job_checkpoint_20261016T035302.105509Z.json`),
  `adapter_faults_20261016T022755.396222Z.json`,
  `bounded_fit_checks_20261016T021808.526204Z.json`,
  `fit_job_checks_20261016T040453.179798Z.json`,
  `gpu_fit_checks_20261016T040612.400941Z.json`,
  `gpu_fit_dryrun_20261016T040553.519171Z.json`. Measured numbers
  (rejection curve, validation errors, checkpoint hash) are identical
  in the post-bump chain; only the packet identity moved.


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
