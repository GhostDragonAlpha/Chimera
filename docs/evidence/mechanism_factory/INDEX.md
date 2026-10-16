# Mechanism factory evidence index (11.18)

Current (adapter-verifiable in a clean checkout of HEAD):

Coordinated doc bump #2 — drift-proof verifier_identity (2026-10-16): the
packet's `verifier_identity.receipt_adapter` no longer ENUMERATES accepted
schemas (that enumeration was the design flaw: it drifted on every schema
addition); it now names `tools/mechanism_factory/receipt_adapter.py` and
states the accepted schema set is defined by that file AS PINNED by its
`verifier_inputs` hash. `README.md`'s adapter section got the same
one-sentence treatment (accepted schemas = what the pinned adapter
accepts; nothing enumerated). No code bytes changed this round, so every
non-document verifier_inputs pin still matches disk. Both files are
graph-pinned, so the whole receipt chain was regenerated in dependency
order and the graph re-pinned (read_first oids re-absorbed for the two
documents, packet pin 3a0375ef9a81... -> 75e24523dc1c..., committed-
receipt pin moved to the new genuine stamp, adapter-verify-committed
argv repointed, old document versions retained as immutable graph nodes,
`check()` clean). Every pre-bump-2 artifact is superseded under Stale:
the packet digest moved again, so old packet-derived receipts are now
adapter-refused (`packet_digest_mismatch`) and the old manifest's
sha-pinned identities no longer match. Measured numbers are unchanged
(same fixtures, same seeds, deterministic fits); only the packet
identity moved.

- `qualification_receipt_20261016T075038.618903Z.json` — genuine
  qualification receipt (schema
  `chimera-mechanism-factory-qualification-receipt-v2`), regenerated
  against the reworded packet via the pinned writer; three CPU cases,
  stagnated at the machine-scale floor, all residuals under the packet
  thresholds. Adapter verdict PASS (recomputed + declared).
- `qualification_receipt_20261016T075137.420787Z.json` — multi-point
  qualification-case receipt (5 vertical load magnitudes per
  train/validation family, each case recording its own
  `load_magnitude_N`; holdout family never run), same writer. Adapter
  verdict PASS (recomputed + declared).
- `composed_qualification_receipt_20261016T075201.116240Z.json` — P5
  composition receipt, schema
  `chimera-mechanism-factory-composed-qualification-v1`
  (`composed_patch.py`): the apex-weld hourglass assembly (piece A rim
  pinned, apex = seam, 0.8 N input load; piece B inverted, far rim
  pinned = output port; seam owned by A, referenced by B), reference =
  ONE `solve_equilibrium` on the joined mesh. Scale 1.0: stagnated,
  free residual 5.3e-8, force balance 5.3e-8 N, moment 3.4e-16, block
  margin 0.170; scales 0.5/2.0 within the 1e-6 law (margins 0.142 /
  0.183). Adapter verdict PASS (recomputed + declared); the battery's
  internal stamp `composed_qualification_receipt_20261016T075746.134714Z.json`
  is likewise adapter-PASS. Topology witnesses (free seam ring: no
  equilibrium, residual 1.08; grounded ring: zero transfer,
  bit-for-bit) recorded in the battery receipt.
- P5 REUSE — `composed_chain_receipt_20261016T092136.068087Z.json` +
  `composed_chain_checks_20261016T093949.650913Z.json` (6/6; its internal
  stamp `composed_chain_qualification_receipt_20261016T094004.837261Z.json`
  is adapter-PASS) (`composed_chain.py` / `composed_chain_checks.py`):
  the SAME piece artifacts A and B (vertex/face blocks hashed
  byte-identical to assembly 1's) plus new piece C reassembled into the
  k=2 fan-out STAR (A = grounded owner at the single seam vertex, both
  welds at apexes only; the seam law's generalized hanger placement
  z -> (hA + h) - z reduces to assembly 1's transform for B, preserving
  byte-identical reuse). Minimal-legal-topology witness under check (g):
  free seam rings have no equilibrium and grounded rings transfer
  nothing, so connected assemblies are single-seam stars; a two-seam
  chain through rim vertices is impossible. Reference = ONE
  `solve_equilibrium`: scale 1.0 stagnated at free residual 7.32e-7
  (<= the packet's 1e-6 law), block margin 0.488, port nets
  B 0.922 N / C 0.737 N (transfer margin >= the C4 precedent 0.1
  through BOTH welds); new scale point 0.75 stagnated at 3.36e-7 with
  resolution untouched; stripping C reproduces assembly 1's mesh
  byte-for-byte (energy within 1e-9). Adapter verdict PASS on the
  standalone receipt under the unchanged composed-v1 schema (no adapter
  edit; F13 already refuses unknown variants).
- 11.19 RESEARCH-LOOP RECORD LAYER — `research_record.py` (schema
  `chimera-mechanism-factory-research-record-v1`; append-only JSON under
  `research/`) + `research_cycle_checks_20261016T103302.207984Z.json`
  (7/7): the demonstrated cycle over the REAL retained evidence —
  (a) retained bounded-table rejection -> PCHIP hypothesis proposal
  (dangling parents refused `research_parent_evidence_dangling`);
  (b) method_comparison: piecewise-linear LOO 3.9417e-4 N vs PCHIP
  1.4423e-4 N on the SAME frozen suite, BOTH rejected at the unchanged
  1e-6 gate — improvement measured, adoption REFUSED; (c) the qualified
  apex-weld seam law + byte-identical pieces A/B reused by the star
  assembly (both receipts cited, adapter-PASS); (d) evidence-linked
  followup on the 1.5x/2.0x scale drift (honestly over the gate);
  (e) learned candidate STOPPED without success (`successful: false`
  explicit; a stop claiming success is refused);
  (f) gate-widening refused three ways (`research_gate_override_forbidden`
  on the forged record; the adapter's threshold law and
  `packet_digest_mismatch` on forged receipts — the record layer cannot
  touch any pinned file); (g) finite exploration allocation (second
  experiment refused `budget_exhausted` until a NEW allocation record).
  24 records retained. GRAPH ATTACHMENT via the EXISTING mechanisms
  only: the proposal and followup records attached to
  `work.mechanism-factory-patch-equilibrium` as kind=work objects
  through the workflow's graph_apply intake-proposal law (derived_from
  provenance edges only; `check()` CLEAN); the store admits NO
  evidence-kind proposal (graph_apply refuses
  `workflow_evidence_requires_measurement_api`), so outcome records
  (experiment/method_comparison/stop) honestly stay file-level.
  Scope: this demonstrated cycle only.
- `fit_receipt_20261016T075201.333890Z.json` — bounded-table fit+eval
  receipt (`bounded_fit.py`, P3), regenerated against the reworded
  packet. Same physics as before: bounded PCHIP interpolant, knot-point
  validation error 0.0/0.0 N, **TABLE REJECTED at the preregistered
  1e-6 interpolation gate** (leave-one-out max 1.44e-4 N; measured
  curve recorded), learned-candidate hook
  `learned_candidate_deferred_gpu_seam`; shadow latency 23.5 us vs
  reference solve 15.16 s mean.
- `patch_equilibrium_receipt_20261015T123339.081217Z.json` — P1
  boundary/load solve falsifier battery, 6/6 (schema
  chimera-mechanism-factory-patch-equilibrium-v1). Packet-independent
  (own allowances), so it survives both doc bumps; latest rerun
  `patch_equilibrium_receipt_20261016T080659.004429Z.json` 6/6 green.
- `gpu_fit_manifest_20261016T075313.181707Z.json` +
  `gpu_manifest_receipt_20261016T075313.181768Z.json` — §11.18 GPU
  learned-candidate batch manifest, schema
  `chimera-mechanism-factory-gpu-manifest-v1`, manifest sha256
  e4d839794e9781c0136e15383b89633c4299e5894fa7f4a8b1ccc90459295569,
  `pending_inputs: []`, `eligible_for_live_batch: true` (one job:
  `fit_job.py --device cuda --seed 1729`, timeout 600 s, packet budgets
  verbatim, no-LLM-call law, release-in-cleanup; packet, label receipts
  and `fit_job.py` bytes sha-pinned in `identities`). The live command
  is documented in `tools/mechanism_factory/GPU_LIVE_BATCH.md` (now
  pointing at this manifest) as NOT YET RUN.
- `fit_job_receipt_20261016T075339.472945Z.json` +
  `fit_job_checkpoint_20261016T075339.472851Z.json` — P3 fit stage
  (`fit_job.py`, CPU): deterministic (repeat runs identical; a second
  post-bump rerun `fit_job_receipt_20261016T075308.934569Z.json` +
  checkpoint 075308.934467Z reproduces the same numbers), checkpoint
  sha256 db6525b61d992112..., **VALIDATION MAX ERROR 3.3668e-02 N vs the
  preregistered 1e-6 N gate -> `physically_qualified: false`** (gate
  not lowered; next decision referred back).
- POST-BUMP-2 SUITE RERUN:
  `adapter_faults_20261016T075705.701482Z.json` (F0-F13 green),
  `composed_patch_receipt_20261016T075706.009891Z.json` (7/7),
  `bounded_fit_checks_20261016T075746.397805Z.json` (7/7),
  `fit_job_checks_20261016T080627.624407Z.json` (5/5),
  `gpu_fit_checks_20261016T080657.819895Z.json` (6/6, including its
  internal dry run `gpu_fit_dryrun_20261016T080658.133156Z.json`),
  `gpu_fit_dryrun_20261016T080658.581626Z.json` (clean,
  `reservation_available_not_taken`), and pytest
  `test_workflow_checklist.py` 3 passed over the refreshed graph.
- POST-REUSE SUITE RERUN (P5 reuse round): all suites re-greened —
  `adapter_faults_20261016T092258.859987Z.json` (F0-F13 green),
  `patch_equilibrium_receipt_20261016T092259.068491Z.json` (6/6),
  `composed_patch_receipt_20261016T092303.625898Z.json` (7/7),
  `bounded_fit_checks_20261016T092328.431715Z.json` (7/7),
  `fit_job_checks_20261016T093154.134037Z.json` (5/5),
  `gpu_fit_checks_20261016T093305.360305Z.json` (6/6) +
  `gpu_fit_dryrun_20261016T093306.144822Z.json` (clean), pytest
  `test_workflow_checklist.py` 3 passed. No pinned-file edits this
  round, so all graph `verifier_inputs` pins still match disk.
- POST-11.19 SUITE RERUN (research-record round; graph file edited for
  the two research attachments, `check()` clean, pytest re-greened):
  `research_cycle_checks_20261016T103302.207984Z.json` (7/7),
  `adapter_faults_20261016T104122.353469Z.json` (F0-F13 green),
  `patch_equilibrium_receipt_20261016T104122.562226Z.json` (6/6),
  `composed_patch_receipt_20261016T104123.596029Z.json` (7/7),
  `bounded_fit_checks_20261016T104151.392925Z.json` (7/7),
  `fit_job_checks_20261016T105021.398774Z.json` (5/5),
  `gpu_fit_checks_20261016T105051.453131Z.json` (6/6) +
  `gpu_fit_dryrun_20261016T105052.212501Z.json` (clean), pytest
  `test_workflow_checklist.py` 3 passed over the edited graph.

Stale (retained, do not consume):

- PRE-BUMP-2 CHAIN (superseded 2026-10-16 by the drift-proof
  verifier_identity doc bump above; the packet digest moved again, so
  these are adapter-refused `packet_digest_mismatch` or pin inputs whose
  hashes no longer match). Retained in full, with their full physics
  records intact: composed receipts
  `composed_qualification_receipt_20261016T071312.835237Z.json`,
  `composed_qualification_receipt_20261016T071604.131817Z.json`
  (battery-internal) and the malformed-scale predecessor
  `composed_qualification_receipt_20261016T071144.424155Z.json`,
  composed batteries `composed_patch_receipt_20261016T071539.282973Z.json`
  and `composed_patch_receipt_20261016T074217.266090Z.json`,
  `adapter_faults_20261016T071909.735094Z.json` and
  `adapter_faults_20261016T074256.750508Z.json` (F0-F13),
  `bounded_fit_checks_20261016T071909.944298Z.json` (7/7),
  `fit_job_checks_20261016T072736.582791Z.json` (5/5),
  `gpu_fit_checks_20261016T072806.716918Z.json` (6/6),
  `gpu_fit_dryrun_20261016T072807.462506Z.json` (clean),
  `patch_equilibrium_receipt_20261016T072807.881870Z.json` (6/6),
  qualification receipts `qualification_receipt_20261016T043801.479415Z.json`
  (genuine) and `qualification_receipt_20261016T043900.489112Z.json`
  (multi-point), `fit_receipt_20261016T043900.694301Z.json` (PCHIP
  rejection record), `gpu_fit_manifest_20261016T044124.832275Z.json` +
  `gpu_manifest_receipt_20261016T044124.832337Z.json` (manifest sha
  b20e0589574e5de9751abe3831ffea7adeb3eb3f1c2bc10913de1c13c0318e83),
  `fit_job_receipt_20261016T044141.958228Z.json` +
  `fit_job_checkpoint_20261016T044141.958119Z.json` (validation
  3.3668e-02 N, unqualified). Measured numbers are identical in the
  post-bump-2 chain; only the packet identity moved.


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
