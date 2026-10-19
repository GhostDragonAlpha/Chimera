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
- 11.20 PIECE LIBRARY (first increment) — `piece_record.py` (schema
  `chimera-mechanism-factory-piece-record-v1`; the §11.20.1 record
  table: design recipe / physical definition / ports / instance state /
  representations / function card / fabrication binding; records under
  `pieces/`) + `piece_record_checks_20261016T115835.248024Z.json`
  (6/6). THREE records instantiated from the qualified alphabet, with
  MEASURED domain bounds:
  `piece.patch-equilibrium` (loads 0.4-2.0 N vertical; scales
  0.5x/0.75x/1.0x/2.0x), `law.apex-weld-seam` (apex welds only; the
  witness (g) exclusions recorded), `assembly.star-k2` (0.8 N input;
  scales 0.75x/1.0x ONLY — 1.5x/2.0x recorded over the gate).
  Laws: unknown top-level fields refused; every receipt id resolves AND
  domain claims must be covered by in-gate measured cases in the cited
  receipts (`piece_domain_unmeasured` catches domain drift, not just
  link rot); quasistatic work accounting — port work along a 9-point
  load ramp equals the stored surface-energy change to 1.99e-4 relative
  (preregistered tol 1e-3; honest finding: the ramp's INTERMEDIATE
  states stagnate over the unchanged gate); immutable shared recipes
  with per-instance state (state hashes differ); naming grants nothing
  (`function_card_required`); rejected table/learned representations
  cannot be dropped (`representations_incomplete`); freshness =
  re-verified source pins. Scope: record layer only; no engine binding
  claimed. POST-PIECE-LIBRARY SUITE RERUN (all green; no pinned-file
  edits): `adapter_faults_20261016T120042.595179Z.json` (F0-F13),
  `patch_equilibrium_receipt_20261016T120042.800680Z.json` (6/6),
  `composed_patch_receipt_20261016T120043.856152Z.json` (7/7),
  `bounded_fit_checks_20261016T120112.752908Z.json` (7/7),
  `fit_job_checks_20261016T120943.703372Z.json` (5/5),
  `gpu_fit_checks_20261016T121014.017044Z.json` (6/6) +
  `gpu_fit_dryrun_20261016T121014.836973Z.json` (clean),
  `research_cycle_checks_20261016T121143.163287Z.json` (7/7), pytest
  `test_workflow_checklist.py` 3 passed, graph `check()` clean.
- POST-PORT-SOLVE SUITE RERUN (all green; no pinned-file edits):
  `port_solve_checks_20261016T131007.892691Z.json` (6/6 + record
  amendment), `piece_record_checks_20261016T131048.000256Z.json` (6/6
  over the amended record),
  `adapter_faults_20261016T131242.752611Z.json` (F0-F13),
  `patch_equilibrium_receipt_20261016T131242.983415Z.json` (6/6),
  `composed_patch_receipt_20261016T131244.079238Z.json` (7/7),
  `bounded_fit_checks_20261016T131312.954171Z.json` (7/7),
  `fit_job_checks_20261016T132143.939485Z.json` (5/5),
  `gpu_fit_checks_20261016T132214.337220Z.json` (6/6) +
  `gpu_fit_dryrun_20261016T132215.152402Z.json` (clean),
  `research_cycle_checks_20261016T132344.487794Z.json` (7/7), pytest
  `test_workflow_checklist.py` 3 passed, graph `check()` clean.
- 11.20.5 PORT-BASED ASSEMBLY SOLVE (the LEGO composition primitive) —
  `port_solve.py` + `port_solve_checks_20261016T131007.892691Z.json`
  (6/6): two pieces coupled through their PORT RESPONSE OPERATORS ONLY
  (Newton on the interface residual; the interface DOF is the seam
  vertex's FULL 3D displacement — no reduction: the weld consumes every
  other DOF and the law's vertex forces are local to incident faces).
  AGREEMENT with the fused-mesh reference (the composed artifact):
  A rim net diff 3.17e-8 N, B rim net diff 2.14e-8 N, seam position
  diff 1.04e-8 wu (preregistered tolerances 1e-6 N / 1e-5 wu);
  3 Newton iterations to |R| = 3.45e-12 (gate 1e-10).
  (a) agreement PASS; (b) coupled global force 3.5e-12 N / moment
  8.7e-16 N·m at the unchanged 1e-6 law; (c) NOT one-shot: a single
  isolated evaluation fails the interface residual at 8.2e-1 N
  (~8e5 times the gate) — the iteration is load-bearing; (d) frames
  bit-identical, exchange closed, net joint work 5.4e-13 J (tol 1e-7),
  stored energy matches the fused reference to 8.3e-9 J; (e)
  `port_solve_out_of_domain` and `port_solve_not_converged` both
  refused by name, each with the qualified detailed fallback (the
  fused-mesh solve_equilibrium) already run and attached; (f)
  deterministic (solution hash da2d90d76f831804). The fused solve
  REMAINS the qualified reference and detailed fallback. RECORD
  AMENDMENT: `assembly.star-k2` gained the `port-based` representation
  entry (qualified, citing this receipt) via the additive-only
  amendment law; prior bytes archived under `pieces/archive/`.
- 13.1 S1 DETAILED MULTISCALE REFERENCE — `scale_resolution.py` +
  `scale_resolution_checks_20261016T145040.956432Z.json` (6/6; study
  receipt `scale_resolution_study_checks_20261016T145149.987Z.json`,
  study hash 52da3267b663350c...): the SAME mechanism (the qualified
  patch piece, piece.patch-equilibrium response) on the grid
  scales {0.5, 0.75, 1.0, 1.5, 2.0} x resolutions {n_rim 100, 150,
  200, 300} (resolution axis = fan rim vertex count; vertices =
  n_rim+1, triangles = n_rim; the physical-size axis varied
  INDEPENDENTLY). PREREGISTERED: convergence observable = apex
  displacement; tol_u = 1e-6 wu DERIVED from the packet's 1e-6 N gate
  through the law's compliance P = 1/gamma_max = 1 wu/N (never
  widened); matched regime = n_rim 300 per scale; unmatched = the
  qualification resolution n_rim 200 reused / n_rim 100 coarse. The
  rim reaction norms are EXCLUDED by preregistration with the
  measured DEFINITION law mean*n_rim ~= 6.34 N (constant to 0.06%)
  — a fixed resultant over n vertices, not a convergence error.
  (a) convergence at 1.0x: dz 4.65e-5 -> 1.63e-5 -> 1.16e-5 wu,
  monotone; noisy sub-linear order estimates 1.51/0.49; HONEST
  RESOLUTION LIMIT retained: the n_rim<=300 ladder does NOT reach
  tol_u (finest dz = 11.6x tol_u). (b) SCALE TRANSFER vs REMESHING:
  on the piece the 2.0x physics component is 6591x tol_u vs a 12x
  remeshing component (567x); on the star, refining n200->n300 at
  1.5x/2.0x moves the residual 1.3%/3.4% (1.467e-6 -> 1.448e-6,
  2.575e-6 -> 2.486e-6 N) and it STAYS over the 1e-6 gate
  (1.45x/2.49x) — the star's drift is SCALE PHYSICS under this law
  (the descent's machine-precision stagnation floor at the larger
  energy scale), NOT discretization. (c) deliberately unmatched:
  n_rim 100 misstates the apex response 7.44e-5 wu = 74x tol_u at
  both 1.0x and 2.0x (n_rim 200 reused: ~11.6x) — recorded, not
  hidden. (d) cost: mean wall 1.48/2.42/3.49/5.90 s per cell at
  n_rim 100/150/200/300, monotone (S2 throughput planning). (e)
  honesty: all 20 grid cells + 4 star cells recorded with
  status/residual/wall, none dropped (20/20 piece cells in-gate,
  including 2.0x at every resolution; all 4 star drift cells
  retained over the gate). (f) determinism: same grid twice ->
  same study hash. RECORD AMENDMENT:
  `piece.patch-equilibrium.physical_definition` gained
  `resolution_validity` (the measured (scale, resolution) in-gate
  map, 20/20; domain verdict: bounds STAND — no extension claimed;
  the resolution limit is recorded) via the NEW additive-only
  `piece_record.amend_physical_definition` law; prior bytes archived
  under `pieces/archive/piece.patch-equilibrium.7021015e482860c5.json`.
  RESEARCH LOOP: the retained `followup.star-scale-drift` record got
  its result link — allocation
  `proposal.scale-study-allocation.20261016T145403.398Z` (1 bounded
  experiment) + `experiment.star-scale-drift-verdict.20261016T145403.
  398Z` citing the study receipt, the followup and the chain receipt
  (verdict: scale physics, with the numbers above; the gate was
  never widened and 1.5x/2.0x stay honestly unqualified scales for
  the star topology). ADOPTION UPDATE (11.19 solver-v2, supersession
  with predecessors retained): the star-drift verdict above is
  REVISED to `machinery_superseded` — under the adopted
  `patch-equilibrium-solver-v2` the drift cells converge STATIONARY
  at 1.0336e-13 / 1.9962e-13 N (in-gate), so the 1.45x/2.49x
  over-gate residuals were the v1 MACHINERY's stagnation floor, not
  law-level scale physics and not discretization; the study and
  battery receipts above stand append-only and are revised by
  `scale_resolution_study_checks_20261016T184725.015Z.json` +
  `scale_resolution_checks_20261016T184614.025681Z.json` (6/6; new
  experiment `experiment.star-scale-drift-verdict.20261016T185030.358Z`)
  and by the adoption record
  `followup.adoption-solver-v2.20261016T193000.000Z`; the star
  domain was extended BY MEASUREMENT to [0.75, 1.0, 1.5, 2.0].
- POST-S1 SUITE RERUN (all green; no pinned-file edits):
  `scale_resolution_checks_20261016T145040.956432Z.json` (6/6 +
  record amendment + research records),
  `piece_record_checks_20261016T150414.003245Z.json` (6/6 over the
  amended record), `port_solve_checks_20261016T151602.441560Z.json`
  (6/6; the retained port-based entry now STANDS on materially
  identical re-runs instead of being re-amended),
  `research_cycle_checks_20261016T150443.562660Z.json` (7/7),
  `bounded_fit_checks_20261016T150450.829539Z.json` (7/7),
  `fit_job_checks_20261016T151311.744876Z.json` (5/5),
  `gpu_fit_checks_20261016T151636.950191Z.json` (6/6) +
  `gpu_fit_dryrun_20261016T151637.777479Z.json` (clean),
  `adapter_faults_20261016T151931.721440Z.json` (F0-F13),
  `patch_equilibrium_receipt_20261016T145513.861919Z.json` (6/6),
  `composed_patch_receipt_20261016T145514.964591Z.json` (7/7),
  `composed_qualification_receipt_20261016T145539.705835Z.json` +
  `composed_chain_checks_20261016T145540.007956Z.json` (6/6),
  pytest `test_workflow_checklist.py` 3 passed, graph `check()`
  clean. RETAINED FAILURES of this round: 
  `scale_resolution_checks_20261016T144603.301993Z.json` (5/6 —
  check (e) miscounted the over-gate star cells as 2 instead of 4;
  fixed, rerun green; the study numbers were identical),
  `piece_record_checks_20261016T145555.574964Z.json` and
  `piece_record_checks_20261016T150040.707626Z.json` (5/6 — the
  physical_definition merge first landed in `_record_star`, then
  was unreachable after `_record_patch`'s direct dict return; the
  honest `piece_record_conflict` refusal caught both; fixed, rerun
  green), `port_solve_checks_20261016T150444.782537Z.json` (6/6
  checks but amendment FAIL: the port-based entry embeds each run's
  receipt name, so re-amendment is a DIFFERENT same-kind entry —
  refused `piece_representation_kind_exists` by the amendment law,
  correctly; fixed by honoring the retained entry on materially
  identical re-runs),
  `scale_resolution_checks_20261016T152615.713492Z.json` (6/6 checks
  but amendment FAIL: the study hash had been computed over the star
  cells WITH their wall times — machine noise, not study content —
  so the retained validity's hash could not match; the hash now
  strips star wall times too, and the retained-stands comparison is
  material: same in-gate map, same tol_u, same finest dz; rerun
  `scale_resolution_checks_20261016T153151.197734Z.json` GREEN with
  the retained `resolution_validity` STANDING — idempotent, the
  piece record's bytes untouched). STALE study artifacts retained
  from the S1 probes:
  `scale_resolution_study_20261016T142319.584Z.json`
  (in-gate law bug: stagnated-under-gate terminations miscounted as
  out-of-gate) and `scale_resolution_study_20261016T142810.182Z.json`
  (correct 20/20 standalone run, superseded by the battery-bound
  study receipt).
- 11.19 METHOD IMPROVEMENT (candidate solver, judged the §11.19 way) —
  `solver_candidate.py` (versioned
  "patch-equilibrium-solver-v2-candidate"; convergence machinery ONLY —
  the energy law, the packet's unchanged 1e-6 N acceptance law and the
  refusal semantics untouched) +
  `solver_method_comparison_20261016T165441.030287Z.json`
  (6/6, 31-case frozen suite, matched budgets). DESIGN (from the S1
  evidence): phase 1 = the incumbent VERBATIM — on every termination
  that already satisfies the packet's law the candidate returns the
  incumbent's result to the last bit; phase 2 = Newton-by-FD-diagonal
  (Jacobi blocks of dF_free/dx_free by exact-force columns) engaged ONLY
  when the incumbent terminates OVER the law, with restart-on-stall, an
  energy guard at the incumbent's own machine-scale noise constant and
  residual-nonincrease acceptance. RESULTS: (a) REGRESSION GUARD — on
  all 27 law-passing cases the reactions are BIT-IDENTICAL (max shift
  0.0 N vs the 1e-9 bound; the candidate never moves a converged
  answer); (b) suite completeness 31/31 (13 qualification + 7 P1 + 2
  composed + 2 star + 5 S1 matched + 2 star-drift), both arms on every
  case, every case receipt-linked; (c) matched budgets enforced —
  mismatched budgets refused `budget_mismatch`, all walls within cap;
  (d) STAR VERDICT: under the unchanged 1e-6 N law the candidate DOES
  bring the star 1.5x/2.0x residuals under — 1.4477e-6 -> 1.03e-13 N
  and 2.4862e-6 -> 2.00e-13 N (ONE continuation step each, stationary
  at the incumbent's own residual scale): the drift the S1 study
  measured was the INCUMBENT SOLVER's machine-scale stagnation floor,
  not a law-level impossibility (the S1 receipt stands append-only and
  is revised by this record for the machinery question); (e) candidate
  determinism hash-verified on drift/composed/qualification cases;
  (f) the incumbent's fresh results reproduce all 30 receipt-backed
  residuals (worst relative 0.0). LADDER: does NOT reach tol_u even
  with the candidate — the qualified candidate never engages on the
  piece (all piece cells pass the law), and the forced-continuation
  DIAGNOSTIC tightens the 1.0x matched cells to ~1e-15 N shifting
  apex_z only 1.3e-8..2.9e-8 wu (three orders below the finest dz
  1.16e-5 wu = 11.6x tol_u): the ladder gap is DISCRETIZATION, not
  solver slack. NO-EQUILIBRIUM HONESTY: the overload and partial-rim
  witnesses stay honestly over the law (budget-exhausted,
  bit-identical). RESEARCH RECORD:
  `method_comparison.incumbent-vs-v2-candidate.20261016T165841.829Z`
  (kind method_comparison, citing the comparison receipt, the chain,
  the S1 study and the drift-verdict experiment). NOT ADOPTED: no
  chain regeneration, no pin changes, no piece-record edits —
  adoption is the coordinator's call. RETAINED FAILURE:
  `solver_method_comparison_20261016T165008.148041Z.json` (5/6 —
  check (e)'s pick list carried a stale case id `scale2.0` vs the
  suite's `:g`-formatted `scale2`; fixed, rerun green) and the
  registry-count refusal it followed (the imported P1 battery's 6
  tests register in the shared harness; the expectation now counts 12).
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
- POST-ADOPTION SUITE RERUN (11.19 solver-v2 adoption, coordinator
  ruling published 912f688f: the v2 candidate IS the pinned solver —
  `patch_equilibrium.solve_equilibrium` is now
  `patch-equilibrium-solver-v2`, phase 1 = the former v1 machinery
  verbatim, phase 2 = Newton-by-FD-diagonal continuation engaged only
  over the packet's unchanged 1e-6 N law; `solver_candidate.py` kept as
  the historical candidate record with an adoption pointer). The whole
  chain was regenerated in dependency order because the solver hash
  moved: `patch_equilibrium_receipt_20261016T180352.545823Z.json` (6/6,
  C6 honesty intact), genuine
  `qualification_receipt_20261016T180445.582336Z.json`, multi-point
  `qualification_receipt_20261016T180543.963553Z.json`,
  `composed_patch_receipt_20261016T180557.276658Z.json` (7/7) +
  `composed_qualification_receipt_20261016T180621.760306Z.json`,
  `composed_chain_checks_20261016T181251.019867Z.json` (6/6,
  adapter-PASS) +
  `composed_chain_qualification_receipt_20261016T180652.327348Z.json`
  (NEW star scale cases 1.5x/2.0x: STATIONARY 4.230e-14 / 1.054e-13 N —
  the pre-adoption drift was the v1 machinery's stagnation floor, not
  law-level physics), pieces `piece_record_checks_20261016T184512.602870Z.json`
  (6/6; assembly.star-k2 domain extended BY MEASUREMENT to
  valid_scales [0.75, 1.0, 1.5, 2.0] at valid_loads_N [0.8], citing the
  new chain receipt; 3.0x and out stay excluded), port
  `port_solve_checks_20261016T184557.606145Z.json` (6/6), S1
  `scale_resolution_checks_20261016T184614.025681Z.json` (6/6) +
  study `scale_resolution_study_checks_20261016T184725.015Z.json`
  (star-drift verdict now `machinery_superseded`; drift cells
  1.0336e-13 / 1.9962e-13 N in-gate),
  `bounded_fit_checks_20261016T185109.749490Z.json` (7/7) +
  `fit_receipt_20261016T190222.230347Z.json` (same table hash
  bd2876120ed65f06d175c87edcea4f65a5c90b988669309dc40df7b46c581f3d —
  the fan labels were law-passing under v1, so phase 1 reproduces them
  bit-exactly), `fit_job_receipt_20261016T191423.548554Z.json` +
  checkpoint (validation 3.3668e-02 N, unqualified, unchanged),
  `gpu_fit_manifest_20261016T190441.979869Z.json` sha256
  6e9940478cae11789f1cb477f23235448271f07ae147a512d08f278e2318c4ec +
  `gpu_manifest_receipt_20261016T190441.979933Z.json` +
  `gpu_fit_dryrun_20261016T190442.212979Z.json` (clean) +
  `gpu_fit_checks_20261016T190442.690603Z.json` (6/6),
  `adapter_faults_20261016T190509.160047Z.json` (F0-F13 green),
  solver comparison POST-adoption
  `solver_method_comparison_20261016T190912.903350Z.json` (6/6;
  incumbent = adopted v2 reproduces the REGENERATED receipts, check (f)
  worst relative 0.0; drift rows stationary in BOTH arms,
  bit-identical), `research_cycle_checks_20261016T191703.608623Z.json`
  (7/7), research records `followup.adoption-solver-v2.20261016T193000.000Z`
  (the adoption record) +
  `method_comparison.incumbent-vs-v2-candidate.20261016T191459.083Z`
  (post-adoption validation rerun). Graph:
  `verifier_inputs` re-pinned for `patch_equilibrium.py`
  (a0f4b9f9b289ef1eb76d1c903fd1e458979d7da2f8dcd5ef7683efe5898db99c)
  and the regenerated genuine qualification receipt
  (2f28df86bbd0d71c5468ebb14a68259c85b20beefdc8c7aa8494a0d9e3435e42);
  the adapter-verify-committed check now verifies the NEW receipt;
  pytest `test_workflow_checklist.py` 3 passed.

Stale (retained, do not consume):

- PRE-ADOPTION CHAIN (superseded 2026-10-16 by the 11.19 solver-v2
  adoption above: the solver hash moved, so every receipt stamped by
  the pre-adoption bytes is adapter-refused
  `solver_hash_mismatch:tools/mechanism_factory/patch_equilibrium.py`
  against current bytes, and the graph's verifier_inputs no longer pin
  them). Retained in full, predecessors intact:
  `patch_equilibrium_receipt_20261016T145513.861919Z.json`,
  `qualification_receipt_20261016T075038.618903Z.json` (genuine) and
  `qualification_receipt_20261016T075137.420787Z.json` (multi-point),
  `composed_patch_receipt_20261016T075706.009891Z.json` and
  `composed_qualification_receipt_20261016T075201.116240Z.json`,
  `composed_chain_receipt_20261016T092136.068087Z.json` +
  `composed_chain_checks_20261016T093949.650913Z.json`,
  `piece_record_checks_20261016T170142.970502Z.json`,
  `port_solve_checks_20261016T170152.531173Z.json`,
  `scale_resolution_study_checks_20261016T145149.987Z.json` +
  `scale_resolution_checks_20261016T154245.714903Z.json` (the S1
  study whose star-drift verdict `scale_physics` is REVISED by the
  adoption to `machinery_superseded` — the drift was solver machinery,
  not scale physics; the study stands append-only),
  `fit_receipt_20261016T075201.333890Z.json`,
  `bounded_fit_checks_20261016T170158.490364Z.json`,
  `fit_job_receipt_20261016T171051.412292Z.json` + checkpoint,
  `gpu_fit_manifest_20261016T171119.494497Z.json` +
  `gpu_manifest_receipt_20261016T171119.494503Z.json` +
  `gpu_fit_dryrun_20261016T171119.946387Z.json` +
  `gpu_fit_checks_20261016T171119.160073Z.json`,
  `adapter_faults_20261016T171134.289314Z.json`, the pre-adoption
  method comparison `solver_method_comparison_20261016T171921.421472Z.json`
  (the evidence the ruling adopted on; its NOT-ADOPTED verdict is
  superseded by the ruling) and research records
  `method_comparison.incumbent-vs-v2-candidate.20261016T172321.471Z.json`
  and earlier. Retained adoption-round failure receipts (each caught by
  an append-only law, then fixed):
  `composed_chain_checks_20261016T180636.034974Z.json` (5/6,
  `piece_freshness_violated` — the composed_chain.py edit staled the
  retained star record's source pins; fixed with
  `piece_record.refresh_source_pins`),
  `piece_record_checks_20261016T181419.145728Z.json`,
  `piece_record_checks_20261016T182010.558534Z.json`,
  `piece_record_checks_20261016T182516.626360Z.json` (5/6,
  `piece_record_conflict` — the canonical rebuild cited new receipt
  names / carried new exclusion text vs the retained record; fixed by
  adopting retained citation histories verbatim and by extending
  `amend_domain_measurements` with an idempotent
  excluded_phenomena replacement).

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

## Independent review round — solver v2 adoption (2026-10-16)

- `reviews/step_review_solver_v2_adoption.md` — chimera-step37's
  independent review of the v2 adoption (claims C1-C5). C1/C4/C5
  CONFIRMED; C2 UNCERTAIN as an honest limit (eight adversarial attacks
  failed to break phase 2; absence of breaks is not a soundness proof);
  C3 flagged a headline-vs-receipt number discrepancy.
- `reviews/qwen_reconciliation_step_review_c3.md` — reconciliation: the
  two number sets belong to two different fixtures (S1 n300 star-drift
  cases vs the composed-chain star assembly); both verified, both under
  the unchanged 1e-6 N law, no published evidence wrong. Lesson kept:
  method-comparison summary lines must name their fixture case IDs.

## Stage 9 first increment — piece-record to compile-transaction binding (2026-10-16)

- `tools/mechanism_factory/native_binding.py` — binding adapter (schema
  `chimera-mechanism-factory-compile-transaction-v1`): qualified piece
  record + in-domain instance parameters compile through the EXISTING
  qualified paths (`composed_chain.build_star`,
  `fixture_generator.high_degree_fan`) validated by the pinned law;
  out-of-domain scale/load refused by name from the record's measured
  domain; ids re-derived from the record, never invented; apply/restore
  transactional (hash self-check, byte-reproducibility from the record,
  instance collision, restore drift — refusals never mutate accepted
  bytes). Render/pick/inspector binding remains the recorded unset gap.
- `native_binding_checks.py` W1-W5 5/5 green; regressions
  piece_record 6/6, composed_patch 7/7, composed_chain 6/6.
- `reviews/step_review_stage9_binding_increment.md` — chimera-step37
  final review: S1-S5 CONFIRMED (tamper/stale/restore-drift attacks
  independently reproduced; cross-record domain asymmetry verified from
  the records themselves).

## Stage 9 second increment — compile-transaction to private native engine (2026-10-17)

- `tools/artificial_proteins/native_binding_engine.py` — replays the
  existing AP01 capture law (native_view: port probe, private exe+shaders
  copy, readiness poll, MD01 upload) for native_binding transactions;
  one hidden-window engine session per capture, teardown by handle.
- `native_binding_engine_receipt_20261017T051143.422076Z.json` — both
  in-domain instances compiled into the engine with
  `engine_accepted_state_id` equal to the documented accepted-hash of the
  uploaded f32 positions (independently recomputed by Qwen and
  chimera-step37); energy vs the f32-exact pinned-law reference within
  the preregistered 3e-4 J allowance; relaxation moved both accepted
  states; the existing reset control restored the uploaded initial state
  bit-exactly (restart/replay affordance). `render_state_id` 0 recorded
  honestly (the §11.20.10 rendered-byte gap stays open).
- SAVE/RESTORE GAP (recorded, nothing built): no save/restore control
  exists for the membrane-demo state class (engine ops
  reset|step|run|pause|gamma|reject only; /tick_b2_save|restore own the
  B2 scene class only; session snapshots carry no membrane_demo blob).
  A true lived-state save/restore is a future engine-side seam.
- `reviews/step_review_stage9_engine_binding.md` — chimera-step37 final
  review: T1-T6 all PASS with independent recomputation and engine
  source inspection.
- Provenance note: `tools/python_control/` and `tools/artificial_proteins/`
  (plus the AP01 evidence directory) existed only in the working tree —
  never committed on any branch — while the published chain imported
  them. Committed as-is in this increment to make the chain
  reproducible from a clean checkout; no bytes of the pre-existing
  modules were altered.

## Stage 9 third increment — first visible slice + affordance loop (2026-10-17)

- Browser path is the engine's own `GET /frame` render-PNG endpoint
  (`ChimeraEngine/engine/main.cpp:2863`, proxied by
  `tools/game_shell/server.py:186-188`); no page was authored.
- `native_binding_visible_receipt_20261017T100640.675172Z.json` +
  `visible_slice_20261017/*.png` — one managed GPU batch, visible engine:
  startup PASS (accepted_state_id == recomputed accepted_hash, |dE|
  4.5e-5 J), gamma PASS (energy ratio 2.0 at fixed geometry), reset PASS
  (bit-exact), replay PASS (identical state_id and energy on second
  boot). DEFORM FAIL recorded honestly: the step-control travel guard
  (`engine.cpp:4628`, GUARD_FRAC=1e-3) caps total travel at 0.1273 px —
  no existing demo control can visibly deform a qualified piece
  (screenshots byte-identical, sha256 d96e4440...; CPU mirror 4/4).
- `reviews/step_review_visible_slice.md` — chimera-step37 final review:
  V1-V4 CONFIRMED, including the negative deform claim.
- DECISION (Qwen): material-only gamma is NOT accepted as the visible
  physical consequence — that would move the judge. Engine-side seam
  admitted as the next increment: a physically-legitimate deform control
  and save/restore for the membrane-demo state class (both trace to the
  op set at main.cpp:1199-1213).

## Stage 9 fourth increment — engine seam: legitimate deform control + membrane save/restore (2026-10-17)

- Engine diff (Maya authored, step built/tested/minimal-fixed):
  membrane-demo op set gains ctl 6 deform (centre dead-load within the
  record's qualified domain, converged bracketed-bisection re-solve under
  the SAME surface-energy law via verified kernels, committed through the
  standard TRIAL->ACCEPTED swap — no position written outside the law)
  and save (kind 4) / restore (kind 5) following the B2 restore law
  (malformed documents leave the accepted state untouched).
- `engine_seam_test_receipt_20261017T151513Z.json` — build PASS (sha
  c1c2474c...); acceptance: baseline PASS, deform PASS (257 px visibly
  changed vs the 0.1273 px guard cap; state_id changed), CPU re-solve of
  the deformed state under the pinned law PASS (|dE| 4.5e-5 J,
  |fz-W| 3.2e-7 N), save->deform->restore bit-exact PASS, teardown PASS.
- Authorship note: worker session died mid-report (Maya CUDA stall,
  under operator repair); step completed build+test with four minimal
  fixes recorded in the receipt. Broader engine-suite regression beyond
  the membrane scene remains an open item for the next increment.

## Load-domain study for the stage 9 game loop (2026-10-17, CPU-only)

- `load_domain_study_20261017.json` — assembly.star-k2 apex equilibrium
  across loads 0.0-3.0 N at scale 1.0 (solver v2, max_steps 60000):
  monotone apex_z 0.3870 -> -0.0595 wu, every row within the unchanged
  1e-6 N law; the 0.8 N row reproduces the chain qualification receipt's
  scale-1.0 residual digit-for-digit (7.322313e-07). Measured basis for
  the additive valid_loads_N amendment and for a game objective of the
  form "set the load so the apex settles in a target band".

## Criteria freeze for the stage 9 game loop (2026-10-17, CPU-only)

- `reviews/step_review_load_domain_study.md` — chimera-step37: L1-L3
  CONFIRMED (table digit-for-digit; amendment legality per
  piece_record.amend_domain_measurements lines 419-480; all 8 studied
  loads eligible). L4 frozen game-loop criteria accepted by Qwen with
  one correction: criterion 5's evidence is the engine reset control
  (bit-exact, proven in increments 2-3), not builder seeds.

## Domain amendment: assembly.star-k2 valid_loads_N (2026-10-17, CPU-only)

- `pieces/assembly.star-k2.json` — additive domain amendment via
  `piece_record.amend_domain_measurements`: valid_loads_N [0.8] ->
  [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0], citing
  `load_domain_study_20261017.json` (all 8 rows in-gate: residual <=
  1e-6 N, valid terminal state). Prior bytes archived at
  `pieces/archive/assembly.star-k2.4d7420e49a2d1a99.json`; the
  domain_amendment_history entry (4th) records the prior claims.
- Law extension in `piece_record.py`: `measured_domain` now reads the
  load-domain-study receipt schema natively (rows with load_N,
  free_residual_N, status); in-gate is recomputed from the row residual
  against the packet gate and the terminal-state rule
  (converged/stationary/stagnated), never trusted from a self-reported
  flag. The coverage law still cannot invent domain: an uncited or
  out-of-gate receipt adds nothing.
- `piece_record_checks_20261017T163608.575037Z.json` — the append-only
  conflict law caught the fixture drift mid-round (5/6:
  piece_record_conflict on the amended bytes); the battery's canonical
  star fixture then carried the amended claims forward (the adoption
  round's precedent) and `piece_record_checks_20261017T163851.768220Z.json`
  is 6/6 PASS. native_binding_checks 5/5 green; probe: loads 0.0/1.6/3.0
  N now compile, 0.9 N still refused binding_load_out_of_domain.

## Increment 5: stage 9 game-loop engine run (2026-10-17, GPU batch)

- `native_binding_gameloop.py` (tools/artificial_proteins/) +
  `gameloop_run_receipt_20261017T180310.890170Z.json` +
  `gameloop_run_inc5/` — Maya's full-loop run on the increment-4 engine
  (sha c1c2474c), one gpu_batch invocation: objective PASS (deform 1.6 N
  -> apex_z 0.172058344 wu in the frozen band [0.147, 0.197], 810 px
  visible change), failure path PASS (0.9 N refused
  binding_load_out_of_domain at the record layer; engine admitted,
  save->restore recovered), feedback PASS (per-frame telemetry +
  screenshots), restart PASS (reset -> upload hash, 0 px), replay PASS
  (boot B: same upload hash, same terminal id, byte-identical renders).
- Centre binding (Qwen accepted, step CONFIRMED): the MD01 deform centre
  binds to the transaction's own load-port vertex (200, the record's
  free seam apex), not the demo-hardcoded pinned vertex 6, whose fz
  profile saturates at 0.999463 N and cannot reach the frozen band;
  md01 byte parity at centre 6 asserted at runtime. Resolves the
  increment-3 PIN-LAW flag for the deform path.
- AMENDMENT 1 to the frozen criteria (step_review_load_domain_study.md
  L4), per chimera-step37 ruling in
  `reviews/step_review_gameloop_increment5.md`: criterion 2's CPU
  re-solve cross-check is in FORCE/RESIDUAL units (N), threshold
  <= 1e-7 N -- measured |1.40e-7 - 6.62e-8| = 7.4e-8 N, PASS. The
  position reading (wu) is structurally inconsistent with the published
  increment-4 tolerances: the engine commit quantum 4.768e-7 wu
  (engine.cpp:4828) is 4.8x the threshold, and the kernel-vs-CPU force
  difference 4.5e-6 N (within the published 1e-4 N force allowance)
  alone shifts the true root by the observed 6.63e-7 wu. Recorded as a
  numbered amendment, not a silent adjustment.
- `reviews/step_review_gameloop_increment5.md` +
  `gameloop_run_receipt_20261017T185057.629963Z.json` +
  `gameloop_run_inc5_zcode_final/` — step's independent reproduction:
  all six claims CONFIRMED digit-for-digit, screenshots byte-identical
  across boots, both rulings issued, no driver defects. With AMENDMENT 1
  applied, the game loop meets all six frozen criteria.

## Engine-suite regression beyond the membrane scene (2026-10-17, GPU batch)

Closes the increment-4 open item. `engine_regression_smoke.py`
(tools/artificial_proteins/) +
`engine_regression_receipt_20261017T201053.035595Z.json` — Maya rebuilt
the engine from the published tree (exe sha byte-exact c1c2474c...), ran
the two tendon tests (6/6 each, ledger errors 2.5e-12 / 1.2e-12 J) and
smoke-tested all nine non-membrane route families in one gpu_batch job:
studio board default, scene defaults off, B2 admit (valid + two named
malformed refusals with state untouched), B2 pause control, science-load
refusal, graph opt-in (page bytes byte-match spec), thermal/earth
exclusivity refusals. No regression; `git show 981b805c -- main.cpp`
touches no non-membrane route line.
- `reviews/step_review_engine_regression.md` — step CONFIRMED all five
  claims (CPU tests digit-for-digit; route verdicts reproduced, state
  hashes vary run-to-run by design — the generator is not hash-pinned).
- FINDING (recorded-only per step's ruling, pre-existing, not a
  regression): scene-refusal early returns documented `return 2`
  (main.cpp:946/957/972) self-exit with fail-fast 0xC0000409 — the
  catch runs (named stderr) and the return executes; the fail-fast
  occurs in static destruction after main() returns. Pipeline harnesses
  read stderr names and HTTP bodies, not exit codes, so nothing depends
  on the documented code; a repair would touch non-membrane teardown
  code for no pipeline benefit.
- Driver limitation (step note): relative `--out` paths resolve against
  the engine CWD, not the caller's; use absolute paths (as both batches
  did).

## Live GPU learned-candidate fit batch (2026-10-17, GPU batch) — honest null

- `fit_job_receipt_20261017T211647.364397Z.json` +
  `fit_job_checkpoint_20261017T211647.364293Z.json` — the preregistered
  live batch (GPU_LIVE_BATCH.md, manifest
  gpu_fit_manifest_20261016T075313.181707Z.json, all four pinned input
  identities re-verified MATCH before running) executed on device=cuda,
  seed 1729: validation_max_error 3.3668e-2 N vs the unchanged 1e-6 gate
  -> physically_qualified=False. This reproduces the retained CPU fit
  failure digit-for-digit (CPU 0.03366755675170242 vs cuda
  0.033667556751702514, ~1e-16 agreement), a clean CPU/GPU cross-check.
  Per the preregistered law this is a valid stop result: the learned
  representation stays rejected, the detailed representation is kept.
  Wall 5.43 s, peak 0.2 MiB VRAM (budgets met).
- Harness defect (recorded, not silently patched): the batch reported
  FAIL because the manifest's expect string
  "learned-candidate receipt written" does not match what fit_job.py
  actually prints ("job receipt: {path}", fit_job.py:356); the manifest's
  output_schemas field names likewise predate fit_job.py's actual
  receipt schema (split_usage/labels_receipts/python_traced_peak_mib).
  The job exited 0 and wrote a valid receipt; the physics is unaffected.
  The pinned manifest is left byte-identical (its identity is recorded);
  a future rerun needs a corrected manifest. Qwen verified directly
  (full stdout, receipt fields, 21-receipt CPU/cuda comparison, source
  grep); step review not routed for a deterministic reproduction of an
  already-retained failure.

## S0 mechanism and scale contract (2026-10-17, CPU-only) — gate closed-except

- `S0_mechanism_scale_contract.md` — Maya's contract for the plan's open
  gate (§13.1). Verdict closed-except: the piece-record layer already
  carried the law pin (surface_energy_reference hash ee9effcf...), units
  and measured-domain refusal; the derived scale mapping is new —
  compile-path scale is rigid dilation with gamma/topology invariant,
  U ∝ s^2, f ∝ s, unique dimensionless load group Pi = F/(gamma*s*r0)
  with response eta = z_apex/(s*r0); exact similarity holds iff F ∝ s,
  so the record's fixed-load scale family is a sweep of Pi (different
  dimensionless problems) — the preregistered negative control. CPU
  check 7/7 (similarity exact to double precision; fixed-N control
  deviates 0.164 wu). Seven missing variables reported honestly.
- `reviews/step_review_s0_contract.md` — step CONFIRMED all claims
  (similarity reproduced, group uniqueness by dimensional analysis,
  owner inventory, all seven gaps real) and recorded S0 closed-except.
- GAP 2 RESOLVED by retraction (Qwen ruling, step UPHELD): the domain
  amendment 025687a2 had pushed valid_loads_N to 3.0 N, exceeding the
  preregistered packet's loads.max_force_N 2.0 (enforced by
  bounded_fit, not by native_binding — an active layer disagreement).
  The packet is quoted, never widened post-hoc; the record retracts to
  [0.0, 0.4, 0.8, 1.2, 1.6, 2.0] (5th history entry, honest reason;
  prior bytes archived). The 2.5/3.0 N measurements stay in
  load_domain_study_20261017.json as science. Game loop unaffected
  (objective 1.6 N, failure demo 0.9 N); criterion 3 strictly stronger.
  piece_record.amend_domain_measurements gained an optional reason
  parameter so retractions record honest history. piece_record_checks
  6/6, native_binding_checks 5/5; probe: 1.6/2.0 compile, 0.9/2.5/3.0
  refused binding_load_out_of_domain.

## S1 detailed multiscale reference (2026-10-17, CPU-only) — gate PASS

- `S1_multiscale_reference.md` +
  `s1_multiscale_receipt_20261017T231542.626384Z.json` — Maya's
  preregistered scale-transfer suite (S0 gap 1): matched-Pi rays
  F = s*F_ref across scales {0.75, 1.5, 2.0} collapse to
  |delta eta| <= 1.831e-07 (stagnation-noise floor, 547x inside the
  preregistered TOL_ETA = 1e-4); 15/15 deliberately-unmatched fixed-F
  controls do NOT collapse (min 1.696e-02, >169x the 1e-3 floor);
  reference cell (1.0, 0.8 N) reproduced to 0.0. Cap truncation
  recorded, never solved: (1.5, >2.0 N), (2.0, >2.0 N). Scale transfer
  is structurally distinct from remeshing (recipe pins n_rim=200;
  byte-identical topology); the resolution axis is one reported
  contrast point (patch 200 vs 300, |delta eta| 1.158e-05), honestly
  deferred, no convergence claim.
- `reviews/step_review_s1_multiscale.md` — step reproduced all 27
  in-grid solves digit-for-digit, CONFIRMED all seven claims, ruled the
  S1 gate PASS and the resolution-axis deferral honest. One prose
  correction applied at his note: the unmeasured matched-ray region at
  s=2.0 starts above 1.6 N (1.6 N is measured), not 1.0 N.
- Domain consequence: the record's Cartesian (scale x load) claim is
  measured within the packet's 2.0 N cap and overclaimed only above it
  (and for the 2.5/3.0 N rows, s=1.0 only). The similarity law
  Pi = F/(gamma*s*r0), eta = z/(s*r0) is now a MEASURED invariance of
  the star over Pi in [0.4, 2.0], not just a derivation.

## Correction to the S1 domain-read prose (2026-10-17)

The S1 report and step's review both say "the record's own
valid_loads_N rows at 2.5/3.0 N are still measured at s = 1.0 ONLY."
Stale attribution: the S0 gap-2 retraction (39b304d7, published before
the S1 run) already removed 2.5/3.0 from the record's valid_loads_N
(current claims: loads [0.0..2.0], scales [0.75,1.0,1.5,2.0]). The
underlying fact stands for the STUDY receipt
(load_domain_study_20261017.json), whose 2.5/3.0 N rows are measured at
s = 1.0 only. No record change; published artifacts left as written.

## S2 bounded GPU characterization (2026-10-18) — gate PASS

- `S2_gpu_characterization.md` +
  `s2_gpu_characterization_receipt_20261018T044604.123284Z.json` —
  Maya's characterization of the UNCHANGED kernel of record
  (`membrane.comp.spv`, sha a147901f…) through a new case driver
  (`s2_case_driver.exe`, built on the GLM-RELAX-GPU-01 `probe_core.hpp`
  extraction): characterization equipment, not a deployed production
  kernel; the three optimization patch candidates were inspected and
  left un-deployed. Receipt chain: `…T043742…` superseded (written
  before the erratum), `…T044604…` the record, `…T053901…` step's own
  reproduction run — byte-identical to the record receipt except the
  timestamp.
- Compact reusable dataset: `s2_case_set/` — 35 cases re-solved on CPU
  from the S1 record and frozen 2026-10-18T03:54:05Z (cases.json sha
  bf1cfb1f…, pinned in the batch manifest) ~14 min before the single
  managed gpu_batch; 25 S1 grid solves + 8 s=1.0 load-domain study
  rows + 2 resolution-contrast patch cells. ERRATUM (honest, disclosed
  in receipt + report §2): preregistration prose mislabeled the
  composition "27 + 6 + 2"; the frozen artifact is 25 + 8 + 2 = 35,
  no case added/removed after freezing. The two >2.0 N study rows are
  retained measurements, not a domain claim.
- Results (one exclusive batch, anchor gate PASS inside it): 35/35
  cases within every preregistered binary32-level bound (area 32u·Lmax²,
  normal 32u, corner 64u·γ·Lmax = the frozen B2 4.0e-6 N budget made
  scale-relative, complete d_v·64u·γ·Lmax + B_vj GLM-FREEZE assembly
  law, energy Higham sequential); worst ratios area 0.0078, normal
  0.651, corner 0.111, energy 1.1e-5, assembly 0.118; 35/35
  byte-identical across two passes; zero failures. Bound derivation
  PASS 6/6 on CPU pre-batch (math-tools
  results/20261017-235844-38a22dde). Honest boundary retained: worst
  complete-force deviation 1.62e-5 N at refrow_s1.0_load3 — binary32
  kernel arithmetic alone is ~16x the packet's 1e-6 N residual gate at
  the largest scales; sub-1e-5 N force claims need f64/mixed precision,
  not this kernel as-is. Throughput 314 cases/s (629 evals/s, driver
  host wall, not a qualified benchmark); peak RAM 98 MiB; VRAM sampled
  963→979 MiB (machine-wide, MiB granularity).
- `reviews/step_review_s2_gpu.md` — step PASS on every claim group
  (reproduction digit-for-digit, preregistration frozen check, bound
  physics C1–C4, gate ruling, erratum, 1.62e-5 N boundary), scoped
  exactly as the gate row reads, with named carry-forwards (loader is
  probe-grade tooling; >2.0 N rows not a domain claim; throughput is
  characterization not benchmark). CRITICAL DEFECT RETAINED (process,
  not characterization): the batch's own check job (02) exited 1
  (KeyError: 1) on a stale version of the check script; Maya fixed and
  re-ran it manually, step reproduced independently. The manifest
  pinned kernel/driver/case-set hashes but NOT the check script hash,
  so the version drift was undetectable from batch evidence.
- Qwen ruling: PUBLISH. The defect is process-level and honestly
  retained in the batch result.json and step's review; the GPU outputs
  are intact (step verified byte-identity) and the full receipt was
  reproduced digit-for-digit by step's own run. CARRY-FORWARD (binding
  on future GPU-characterization batches): manifests must hash-pin
  every script that contributes to a receipt, check scripts included;
  the fixed check script hash recorded after the fact here:
  s2_gpu_characterization_check.py sha256
  259886e882a4b9d002409ecc4e33234ea13149a7dfe47c72ea7daab814820142.

## S3 reusable reduced response (2026-10-18, CPU-only) — gate PASS

- `S3_reduced_response.md` + `s3_star_eta_pi_table_v1.json` (sha
  17b0ce54…) + `s3_reduced_response_receipt_20261018T072919.936426Z.json`
  — the similarity law made reusable: a 1-D η(Π) table (6 nodes Π ∈
  {0, 0.4, …, 2.0}, digit-for-digit from the s=1.0 rows of
  load_domain_study_20261017.json) with Fritsch–Carlson monotone cubic
  Hermite interpolation, scheme preregistered by leave-one-node-out on
  the node set only (linear rejected: worst LOO 1.676e-03 vs cubic
  2.569e-04); dependency-free implementation matches scipy PCHIP to
  1.11e-16. Π=0 tabulated but valid only at s=1.0 (F=0 dilation
  argument derived, not measured, off s=1.0).
- Explicit validity query (pure, no solve): refuses scale ∉ [0.75,
  2.0], F > 2.0 N packet cap (quoted, never widened — gap 2), Π > 2.0,
  Π ∈ (0, 0.4), γ ≠ 1.0 (gap 6), Π=0 off s=1.0; accepts with named
  flags (zero_load_measured_cell, scale_interpolated) and named
  caveats (no self-intersection refusal — gap 3, mitigated by η ≥
  0.111 over the valid window; quasistatic only — gap 7). No silent
  extrapolation.
- Held-out validation (prereg frozen 2026-10-18T07:04:46Z, sha
  2ebcdae1…, before any held-out solve): 10 fresh never-solved cells
  (Π strictly between nodes) + 7 retained S1 cells; worst fresh
  |Δη| = 2.3673e-05 at (1.0, 1.8 N) ≤ T_S3 = 1e-4 (= S1 TOL_ETA, 545×
  the stagnation floor); decomposition ≥97.5% interpolation / ≤2.5%
  stagnation (fresh matched-Π spread 1.554e-07; 2×-step re-solve moved
  η by exactly 0.0). Passivity N/A (static map, stated); monotonicity
  recorded as a consistency check, not conservation.
- Measured benefit, same 10-cell workload: 7.4318e+04× (detailed
  11.393 s incl. geometry build vs 153 µs reduced). Superseded receipt
  …T072643… retained: first run mis-implemented the ratio formula
  (printed 75.8×); corrected run changed no physics number.
- `reviews/step_review_s3_reduced.md` — step PASS, NO retained
  defects: prereg sha + import graph verified, nodes reproduced
  digit-for-digit, LOO selection reproduced, FC verified by hand
  (exact at nodes, strictly decreasing, C1), 4 held-out cells
  re-solved digit-for-digit, fresh cells confirmed absent from the S1
  receipt, all 7 refusal + 2 accept probes + edge cases (Π=2.0, F=2.0,
  negative F, NaN γ) behave, benefit formula matches prereg P9. Three
  minor observations (mean-vs-median timing wording; solver imports at
  check-script top level though validity_query is pure; scipy absent
  in review venv so PCHIP cross-check verified by hand instead).
- Qwen ruling: PUBLISH. Qwen spot-check: prereg sha 2ebcdae1…, table
  sha 17b0ce54…, ratio recomputed 74318.2 from receipt fields, record
  file and solver bytes untouched (S3 is a new CONSUMER of the record,
  not an amendment — domain claims unchanged). Carry-forwards: γ=1.0
  only; node refinement requires new measurements; scale-interpolated
  predictions flagged, not refused.

## S4 composition and state transfer (2026-10-18, CPU-only) — gate PASS

- `S4_composition_state_transfer.md` +
  `s4_composition_receipt_20261018T100039.322493Z.json` — all five
  gate columns PASS (prereg frozen 2026-10-18T09:30:46Z, sha
  2ca2a808…; three earlier prereg attempts crashed on harness
  mechanics, froze nothing, retained).
- Col1 second assembly: 19/19 battery checks (composed_patch,
  composed_chain, port_solve) re-derived FRESH at bedadbd3 via check
  functions only (mains not run — no record amendment possible);
  pieces A/B byte-identical to assembly 1 (shas 5bb740cc…, 7857974b…),
  C new. The untracked 2026-10-17 composed_* receipts provenanced
  honestly: source_commit eaf6a9e9 (post solver-v2 adoption), hashed
  sources byte-identical to HEAD — incorporated as corroborating
  evidence, not ignored.
- Col2 coupled vs detailed: port-based piece solve vs fused reference
  3.17e-08 N / 1.04e-08 wu / 8.33e-09 J against port_solve's OWN
  frozen bounds (1e-6 N / 1e-5 wu — verified preregistered, not
  invented); S3 reduced composition vs fresh detailed solves at 4
  measured scales: worst |Δη| = 5.609e-06, 56× under T_S4 = 1e-4
  (quoted from S3), node cells digit-for-digit. No silent
  extrapolation through composition: refused cells route per-cell
  through the S3 validity query (codes 4, 6, 3) with in-domain named
  fallbacks; s=3.0 refused by BOTH reduced and detailed paths.
- Col3 two-sided: hourglass closure 3.45e-12 N, net joint work
  5.4e-13 J; star welds on independently-computed films: closure
  7.32e-07 N at s=1.0 — verified to EQUAL the fused solve's own
  seam-vertex residual (the packet law's own quantity, not a new
  error) — and 1.06e-13 N at s=2.0; transfer real (|F_B| 0.922/1.572
  N, |F_C| 0.737/1.233 N).
- Col4 ownership: exact vertex/face partition (601v/600f star,
  401v/400f hourglass), unique pins, free-DOF count exactly 3 (the
  single seam vertex), duplicate probe fires loudly.
- Col5 switching IMPLEMENTED (not vacuous) for the named star-apex
  surface only: idempotent 100 repeats, reduced→detailed round trip
  |Δz| = 1.831e-07 wu = exactly the S1/S3 noise floor (bound 1e-6),
  out-of-domain switch refused by name; hourglass has no reduced
  representation (stated).
- `reviews/step_review_s4_composition.md` — step PASS, NO retained
  defects: full 48/48 re-run, worst + node cells re-solved
  digit-for-digit, port bounds verified preregistered, closure
  identity verified, duplicate probe verified loud, crashed preregs
  verified froze-nothing, provenance verified. Step's own re-run
  receipt …T105819… retained (differs from the record receipt only in
  timestamp and battery wall-clock). Note: step's review file was
  initially written to a typo'd directory (PythonChimara/); Qwen moved
  it to the correct tree and removed the stray directory.
- Qwen ruling: PUBLISH. Record file and solver bytes untouched; S4
  claims live in composition receipts only. Carry-forwards: reduced
  response is assembly-level (star apex) and γ=1.0-only — Maya
  proposes a per-piece reduced response (single-film η(Π) per piece)
  as future measurement territory, NOT attempted (beyond S3's
  published domain); s=1.0 star closure at 73% of the 1e-6 bound is
  the packet law's own seam residual.

## S5 visible authoring demonstration (2026-10-18) — gate PASS; §13.1 chain S0–S5 complete

- `S5_visible_authoring_demo.md` +
  `s5_authoring_demo_receipt_20261018T155028.861Z.json` (supersedes
  …T134559…, sha pinned in chain, original unchanged) — the existing
  viewer (GET /glass composited operator view) shows mechanism
  identity (assembly.star-k2, 601v/600f + law ids), ACTIVE
  REPRESENTATION switching on screen (DETAILED SOLVE → REDUCED TABLE
  (S3) with the S4 1e-6 wu bound evaluated live), scale (s = 1.0,
  record window), and live measurements (apex z / residual / energy /
  accepted_state_id) — closed with NO engine edits by feeding the
  engine's own Studio board file with live values. Pinned exe
  c1c2474c… verified unchanged.
- Physical/render/pick correspondence PASS: the membrane demo's only
  free DOF is the MD01 centre = record load-port vertex 200 (seam
  apex); /project (present-stage mapping (x, z+lift, −y), lift 0.5)
  places the apex at px (960.0, 426.9) inside the A-vs-B render-diff
  bbox (canonical strict byte-diff: 8326 px, bbox 857–1062 × 405–520,
  centre 959.5/462.5 — Qwen independently recomputed, matches). No
  HTTP mesh-pick endpoint exists for the membrane demo (engine gap
  named; tick_b2 only) — correspondence shown via the single-free-DOF
  deform law instead.
- Repeatable build–test–reuse PASS: two fresh-boot runs; /frame PNGs
  of A/B/C byte-identical across runs; board readouts digit-for-digit
  identical; glass dynamic pixels confined to chrome bands. On-screen
  reuse numbers: F=0.8 N table-vs-engine 1.70e-07 wu; F=1.6 N
  7.04e-07 wu (inside S4 bound 1e-6); falsifier 0.9 N refused at
  compile (binding_load_out_of_domain) shown.
- S5-AMENDMENT-1 (`s5_prereg_amendment1_20261018T155028.861Z.json`,
  step-endorsed, Qwen-ruled): the frozen predicate
  C_vs_S3_table_Pi1.6_within_quantum (CPU bisection quantum 4.77e-7
  wu) was MIS-SPECIFIED — a CPU convergence criterion applied to an
  f32-kernel landing (category error; S2 §3 f32 boundary precedent,
  AMENDMENT 1 precedent). Replaced by the force-allowance z-bound
  z_bound = force_allowance_N / dfz_dz = 1e-4 N / 7.122416 N/wu =
  1.40402e-05 wu (chord slope of seam-apex fz(z) between the S3
  table's 0.8/1.6 N cells; fz single-valued + monotone per S4).
  Measured deviation 7.044e-07 wu = 0.050× the bound, PASS both runs.
  The original FAIL is RETAINED, marked superseded, never deleted —
  the numerics check asserts both (historical + amended), PASS 26/26.
  The amended bound is the reusable law for future f32-kernel landing
  bounds.
- Erratum (step-caught, fixed): the original receipt's diff-bbox
  numbers (1218 px, 862–1052 × 405–456) used an undocumented
  per-channel threshold >8; canonical strict byte-diff numbers
  recorded with both thresholds named; functional correspondence
  unchanged (apex inside both bboxes; |cx − sx| = 0.5 px canonical).
- Engine API sharp edge RECORDED (engine untouched): POST /studio
  with omitted "on" key TOGGLES overlay visibility (main.cpp:3229,
  get_bool default = !visible) — cost two discarded runs, disclosed;
  harness now always sends explicit "on": true.
- `reviews/step_review_s5_authoring.md` — step PASS-with-carry-
  forwards on the original increment (all six requirements verified,
  amendment endorsed, bbox discrepancy caught); amendment round
  verified by Qwen directly (arithmetic, receipt diff — physics values
  untouched, independent bbox recomputation, numerics 26/26, record/
  solver/main.cpp bytes unchanged, exe sha match).
- Qwen ruling: PUBLISH. §13.1 S0–S5 chain COMPLETE: mechanism
  contract → multiscale reference → GPU characterization → reusable
  reduced response → composition → visible authoring demo. Carry-
  forwards: no HTTP mesh-pick for membrane demo (engine gap); γ=1.0
  only; per-piece reduced response (Maya's proposal) is future
  measurement territory; human usability remains separately observed
  per the gate column.

## Workshop increment 1 — persistence across sessions (2026-10-18) — PASS

- Player-sequence gap closed (plan §13.1 handoff priority: save/reuse):
  the loop previously saved/restored only WITHIN one engine boot. Now
  the save doc written to DISK by the TERMINATED boot-A engine
  restores bit-exactly in a fresh boot-B process — the player's saved
  construction survives the session.
- `workshop_increment1_persistence/` — prereg frozen before capture
  (predictions pinned digit-for-digit from the published increment-5
  receipts); two full runs, receipts
  `gameloop_run_receipt_20261018T184001.972454Z.json` +
  `…T184338.756806Z.json` at source_commit e85baca5. Persistence PASS
  both runs: state id 7177421591213043741 bit-exact, apex 0.172058344
  wu bit-equal, load 1.6 N, energy 6.4514966 J, restore 14.7/13.6 ms,
  0 changed px vs the replay terminal. Repeatability: all seven
  /frame shots byte-identical across runs; disk save doc byte-identical
  (sha d048765f… pinned in receipts); /glass differs only in chrome
  (the measured wall-time characters — disclosed prereg deviation:
  board text predicted digit-identical, restore ms varies).
- Visible readout (h-glass-persisted.png, Qwen inspected the pixels):
  WS1 "Persistence across sessions" chip green; LAW (restore is
  bit-exact by accepted-state-id), FALSIFIER (state-id/apex/load drift
  on restore; disk round-trip mismatch), VERDICT (PERSISTED RESTORE
  (fresh boot) with live values), REFEREE TOOL
  (/membrane_demo_save | /membrane_demo_restore), ARTIFACT
  (membrane_demo_save_terminal.json). 187 fps / 5.35 ms frame — no
  frame-time cost; one-shot restore cost 13.6–14.7 ms.
- Code: `native_binding_gameloop.py` additive persistence step +
  exit-code-law extension; `native_binding_visible.py` `_boot` gains
  backward-compatible board=/size= kwargs (main.cpp:974-981 argv[2]).
  Six frozen criteria reported verbatim, unchanged (c2's printed FAIL
  remains the pre-existing superseded position-units reading — under
  AMENDMENT 1 the force-units cross-check passes: balance 6.6e-8 ≤
  1e-7 N, force diff 4.5e-6 ≤ 1e-4 N allowance). §11.20.12 failed
  cross-check and separate state class untouched, not claimed.
- Qwen review (author-independent, focused): persistence block
  verified in both receipts; 7/7 cross-run PNG byte-identity
  recomputed; save-doc sha matches receipt pin; code diff additive;
  screenshot inspected. PUBLISH.
- Next player-visible capability (lead's choice, not yet scoped):
  rescue/transfer step, or loop-side S3-table instant reuse (Maya's
  bounded follow-up proposal).

## Workshop increment 2 — instant reuse via the qualified S3 table (2026-10-18) — PASS

- The loop's REUSE step now answers instantly from the qualified S3
  table (sha 17b0ce54… pinned) with the validity query gating, the
  detailed engine deform as the named fallback, and measured latency:
  table query median 2.2 µs (1000 repeats) vs live deform wall 64.9 ms
  → 29502× (run2: 4.9 µs vs 76.1 ms → 15540×), cross-referenced to the
  S3 receipt's measured benefit.
- `workshop_increment2_instant_reuse/` — prereg frozen
  2026-10-18T19:34:52Z before capture (table sha, node digits, refusal
  code, bound 1.40402e-05 wu in the S5-AMENDMENT-1 form, latency shape
  only); receipts `gameloop_run_receipt_20261018T201528.830420Z.json`
  + `…T201735.511376Z.json` at source_commit b4dbf464. Per-cell
  table-vs-engine (both runs, digit-for-digit): 1.6 N node delta
  7.044e-07 wu; 0.8 N node (live deform after fresh reset) delta
  1.700e-07 wu — both 20× inside the bound. Refusal probe: 0.2 N →
  code 6 "unmeasured gap (0, 0.4)", engine fallback admitted (apex
  0.362019569 wu). Repeatability: all 9 /frame shots byte-identical
  across runs; /glass delta 1006 px confined to chrome (union of the
  increment-1 bands and the S5-qualified mask, both counts recorded;
  timeline-clock pixels preserved as crops).
- Layering honesty (design correction by Maya, accepted): 0.9 N is
  table-VALID (Π=0.9 ∈ [0.4, 2.0]) — the 0.9 N refusal is the RECORD's
  (compile-time binding_load_out_of_domain, frozen c3 verbatim); the
  table's named refusal is demonstrated at 0.2 N instead, and a
  layering probe records query(1.0, 0.9, 1.0) = VALID code 0 beside
  the record refusal. Table validity (continuous Π window) and record
  domain (measured load list) are different layers — both kept exact.
- Implementation honesty: the published S3 check file cannot be
  imported (module-level prereg asserts + solves), so the four pure
  functions are copied verbatim with a run-start assertion that each
  function's source appears byte-for-byte in the published file
  (source_identity_vs_published: true); constants bound from the
  sha-pinned table file.
- Six frozen criteria reported verbatim, unchanged (c2's printed FAIL
  is the retained f32-landing reading, same as published increment-1
  runs); instant_reuse is additive and joins the exit-code law. WS2
  "Instant reuse (S3 table)" chip green on screen with LAW/FALSIFIER/
  VERDICT envelope (Qwen inspected the pixels).
- Qwen review (author-independent, focused): receipt blocks verified;
  9/9 cross-run /frame byte-identity recomputed; WS2 readout viewed;
  frozen constants identical to HEAD; CRLF line-ending drift in the
  working file normalized back to LF before commit (the whole-file
  git diff was an artifact — semantic diff is 498/12 additive).
  PUBLISH.
- Decision: instant reuse is now the loop's demonstrated reuse path
  (detailed re-solve remains the named fallback for refused cells).

## Workshop challenge 1 — keep the salvage load above the marked hazard (2026-10-18) — PASS (§5.1 slice minus transfer)

- First real game decision in the native scene: marked hazard (granite
  slab), kit (2 piers, deck, pillar, crate), objective law + falsifier on
  the Studio board, referee = B2 transactions. Driver
  `tools/construction_packet/workshop_challenge1.py`; runs
  `docs/evidence/mechanism_factory/workshop_challenge1/run1|run2` +
  `comparison.json`; full report `workshop_challenge1/WORKSHOP_CHALLENGE1.md`.
- Runtime: B-suite construction exe
  `.tmp/body-engine/Release/chimera_engine.exe` sha
  47bbf42a7437089264a9f830f832f7432dfc2deb48680330ce4478134b278406
  (the Oct-17 B-suite build B4/B8 already use; not the membrane pin).
- Failure→named feedback→cheap recovery: off-centre crate topples; verdict
  "LOST SUPPORT … ACTION: remove the crate and centre it over its support
  before loading."; remove+re-centre continues the same session.
- Two structurally different solutions (§6 gate
  `gate_two_solutions_different: true`): B contact tower — no connectors,
  115.03 N reaction, 79.9 mm clearance, welds []; A welded span — two piers
  + deck + live welds, 393.60 N, 304.8 mm, welds 20.25/19.39 N; mid-run
  20× stiffer re-weld cut sag 10.7→1.0 mm (B4 pattern, board verdict reads
  it). Save→clear→restore bit-exact both runs; refused edits leave the hash
  unchanged (2 probes).
- Determinism scoping (2 runs): analytic states byte-identical modulo step
  counter; settled save docs within jitter band; 8/11 frame shots
  byte-identical incl. all 3 glass shots — the 3 differing shots are
  settled-physics frames inside documented granite jitter.
- Cost: frame avg 1.142 ms (first-frame max 71.31 ms), sim/wall 1.0, RSS
  peak 200.0 MB.
- Disclosed deviation: design frozen in the committed driver before both
  runs, but no separate UTC-stamped prereg JSON (membrane-loop pattern not
  followed).
- Process: Maya authored driver + `cradle_recipe.py` extraction but timed
  out twice pre-capture; lead executed her driver directly, fixed the
  board-path bug (engine resolves argv[2] against native/ — now
  `out.resolve()`), re-captured. `test_b4_assembly.py` re-run after recipe
  extraction: 6 tests OK.
- Qwen review (author-independent, focused): receipt/comparison numbers
  re-read from JSON, glass screenshots inspected (red WS3 failure chip with
  ACTION line; green WS3 HELD verdict). PUBLISH.
- Not yet shown: saved-recipe transfer under a varied constraint
  (workshop challenge 2); human playability unobserved (scripted
  walkthrough).

## Workshop challenge 2 — saved recipe transfers; world varies; one edit recovers (2026-10-18) — PASS (§5.1 reuse promise)

- Driver `tools/construction_packet/workshop_challenge2.py` (imports the
  published challenge-1 driver); runs
  `docs/evidence/mechanism_factory/workshop_challenge2/run1|run2` +
  `comparison.json`; report `workshop_challenge2/WORKSHOP_CHALLENGE2.md`.
  B-suite exe sha 47bbf42a... (both engines, per-phase in receipts).
- Arc (both runs, `gate_pass: true`): build contact tower (79.882 mm,
  115.03 N, chain-law prediction hit to the micron) → clean shutdown →
  fresh never-admitted engine restores `save_B.json` with **restored hash ==
  engine-1 saved hash** → transfer PASS unchanged (green board chip "the
  invention is REUSABLE") → variation `/tick_b2_patch crate mass_kg` x2:
  settled margin **-8.92 mm FAIL** (doubled step load punches through the
  pillar — documented tunnel class; deterministic both runs; red chip names
  it with ACTION line) → recovery = the ACTION (second pillar beside the
  first, unrotated, crate straddling both, mass patched while paused): PASS
  79.051 mm → terminal save restore bit-exact; refused edit hash-unchanged.
- Determinism: analytic anchors byte-identical modulo steps; settled docs
  in band; frame shots 3/5 byte-identical (2 settled frames jitter-band).
  Glass shots NOT byte-identical (417-901 px, 0.02-0.04 %): board region
  incl. every verdict line byte-identical; diffs are viewport specular
  jitter + live STATUS HUD clock. Falsifier rendered "named before the run".
- Cost: frame avg 1.19/1.17 ms (first-frame max 47.6 ms), sim/wall 1.0,
  RSS peak 138 MB, 14 routes.
- New engine/API findings: patch `mass_kg` rescales mass+inertia+ground
  k/c (rest sink preserved); restore works on a never-admitted fresh engine
  (`active_ = true`); **rotated-surface contact finding** — a rotated part
  as contact surface drops vertex-resting loads (free-fall through 90°-
  yawed support at 2.4/6.7 mm, exact 1/2gt^2, zero pair force; unrotated
  control holds; yawed square-pillar control included). Probes preserved in
  `workshop_challenge2/probes/`. Challenge 1 unaffected (its support faces
  were unrotated). Workshop rule now: supports placed unrotated; engine
  ticket is a lead decision for the engine track.
- Disclosed deviation (same as challenge 1): design frozen in the committed
  driver, no separate UTC-stamped prereg JSON.
- Process: Maya authored driver + smoke in one dispatch (~2.4 h) under the
  revised brief (author + smoke only); lead ran captures + comparison. The
  post-challenge-1 process change worked.
- Qwen review (author-independent, focused): receipts/comparison re-read
  from JSON; glass-shot pixel diff localized (board byte-identical, HUD +
  viewport only); all three verdict chips read from the pixels (transfer
  green / variation red with ACTION / recovery green). PUBLISH.
- Not shown: human playability; rotated-surface defect documented, not
  fixed.
