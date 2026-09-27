# PREREGISTRATION — MAT2-P05 (milestone recovery and artifact identity reconciliation)

Card `MAT2-P05` (planning P05, group "Scope, identity, and fleet", kind=integration,
profile=records/offline). Attempt `01ce64f40de34bcb82782d566ddfed39`, agent
`arrival-961a6f78a19c4eb58cafb2c7e1fcbcb1`, criteria
`0fbecb6247f21492706fbfe94c2ac0af81060e26a667bb52c91e6b4d89ea4953`, scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`,
isolated checkout branch `branch-6` at base
`c525b82c7c3ce0128565424764293a3c85811ab3`, attempt workspace
`E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-P05\01ce64f40de34bcb82782d566ddfed39`.
This file is written and frozen BEFORE this attempt implements anything and
BEFORE any probe below is executed. Inventory reads used to design the frozen
probes are declared in the next section; no verification probe had run at
freeze time and no failing test had been executed.

## Declared inventory reads (probe design only, pre-freeze)

worker_start onboarding output (arrival, assignment, criteria, checkout identity);
`kanban_cli.py inbox --task ONT-P05` (legacy winner) and `kanban_cli.py status`
(live board); git reads in the attempt checkout of the merged integration branch
`origin/astra/gait-capture` (tip `b0108a36`) at merges `78f3b524` (ONT-P05),
`13a94391` (MAT2-P03), `97993cbe` (MAT2-P01): `git ls-tree`/`git show` of the
merged contribution files and recomputation of their raw SHA-256; read-only
hashing of live record files (startup-receipts store, `ChimeraEngine/output/ports`
store, `agent_logs/f4_walk_walk_theta_entrained.json` and its three preserved
copies, fleet/FEATURE_WALK manifests, curriculum file, completion map, scope
lock); reading of `tools/monkey_campaign/integrity.py` (`content_digest`,
`verify_catalog`) and of the merged ONT-P05 / MAT2-P03 `implementation.py`
sources. The registry was NOT probed programmatically pre-freeze (no
`Registry(...)` call); the merged ONT-P05 verifier was NOT executed pre-freeze.

## RECONCILE-FIRST DECLARATION (prior completed work reused, not re-implemented)

1. Legacy card `ONT-P05` (criteria
   `53cb0e60f447a52e9c0aca432f46d7173a3ff6cecc536cee1346d8306f715eb4`, scope
   `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`) is DONE
   via PR #174 (head `52dbc2ce35857fd442fc2b0ea20b67a58071233e`, merge
   `78f3b5248dc5503526fefb763ff3195dc769d957`, merged 2026-09-27T00:23:31Z).
   Its delivered audit tool `contributions/ONT-P05/implementation.py` and its
   official probe `contributions/ONT-P05/identity_audit.json` are merged into
   `astra/gait-capture`. Pre-freeze recomputation from the merge blobs gives
   raw SHA-256 `e45d837d8a32de28449e851b8ec3452141c861f729406177c0987782db6b3cd2`
   (implementation.py) and `30f339244dd683cd2ea9bebf0223ffccee860ad9ee3891e489cf846459489d9e`
   (identity_audit.json) — byte-identical to the source/numerical evidence
   hashes recorded in the ONT-P05 winner receipt. This attempt REUSES that
   known-good verifier: the merged module is materialized (or read in-tree),
   byte-verified against the winner-receipt hash, its component oracles are
   imported (complete-structure `.npy` parse with named refusals, receipt
   filename-digest law, winner-merge resolvability, retry markers, hash-label
   triple, battery runner), and the verifier itself is re-executed UNMODIFIED
   as a labeled live-refresh probe. Nothing it verified is re-derived.
2. Dependency `MAT2-P03` (criteria
   `67caf01f86c2ba57b8cae7ebe453d3580bfdd2c5981aee40820c431156fd6135`) is DONE
   via PR #194 (head `250d6b243947eceb0abd93c6ffadea099a612bd7`, merge
   `13a943911da711a4dd24a450055ba0d1b1fe1d04`). Its
   `contributions/MAT2-P03/reconciliation.json` (raw SHA-256
   `2ea458a294009c16ce8258e3b364af0df31a57d52468a2b9cf5d7f7e1b205b4f`,
   recomputed from the merge blob pre-freeze — byte-identical to the winner
   receipt's numerical evidence) carries the governing crosswalk row:
   `ONT-P05 -> MAT2-P05`, `clause_relation: "unchanged"`,
   `promoted_to_acceptance: false`, `historical_evidence_only: true`.
3. This card's own contribution is therefore the MAT2 reconciliation layer:
   (a) own-identity binding to THIS attempt (startup receipt
   `8daed2f64bc4d3b316da5fdd4d70e7f2de0d6da0e016ec7258b56310abbf1220.json`,
   `checkout_identity.json` head `c525b82c…` branch-6); (b) live re-derivation
   of every clause at the current revision; (c) winner-preservation
   verification for the merged prior evidence; (d) the no-promotion crosswalk
   assertion; (e) dependency verdicts; (f) F1/F2/F3 status refresh. Old DONE
   is historical evidence; this card closes only if the clause records verify
   live under THIS card's criteria.

## STATEMENT (a theory that can lose)

At the current revision the five done_when record classes — recoverable
commits, run manifests, training checkpoints, raw/blob/canonical hash labels,
retry rules — still exist and still verify through the same independent
oracles the merged ONT-P05 winner used, with exactly these expected live
drifts: (i) the shared startup-receipt store has grown (110 receipts at the
legacy correction probe; now larger); (ii) the live curriculum file has
changed entry count (18 at the legacy probe; now different — live working
data); (iii) the merged verifier, frozen at the OLD scope anchor
`01ea5cdd…`, now reports a hash-label anchor mismatch against the migrated
scope lock (`scope_sha256 cb5475f8…`, map raw `8fa2e140…`) even though the
same dual-label/canonical/external-anchor mechanism verifies under the
current human-pinned anchor; (iv) findings F1 (fleet `MANIFEST.json` not
reproducible against its pinned `source_base` `bf0a6216…`) and F2
(FEATURE_WALK raw-hash manifest labels unpreserved frames) remain live; (v)
the training-checkpoint store is unchanged (4 named `.npy` checkpoints,
hashes identical; 108 total; run record byte-identical at 3 preserved sites;
`certified_policy_checkpoints: 0` verbatim). A read-only reconciliation can
table every clause verdict with recomputed hashes, verify the merged winner
evidence is preserved byte-identical in the integration branch, crosswalk
the legacy DONE without promoting it, and name every drift — writing only
inside this attempt workspace.

## FROZEN PREDICTIONS (scorecard recorded in the report; no post-hoc edits)

- **P1 (preservation)**: recomputed from `origin/astra/gait-capture` merge
  blobs — `contributions/ONT-P05/implementation.py` = `e45d837d…`,
  `contributions/ONT-P05/identity_audit.json` = `30f33924…`,
  `contributions/MAT2-P03/reconciliation.json` = `2ea458a2…`; all three match
  their winner-receipt evidence hashes. Any mismatch = a preservation finding
  (reported, not tuned away).
- **P2 (refresh run of the unmodified merged verifier, exit 0)**:
  recoverable_commits satisfied with receipt_count ≥ 200 and own_receipt true
  (its frozen identity still binds — its receipt persists in the shared
  store); retry_rules satisfied with test_kanban, test_suggestion_box,
  test_merge_service, test_checkpoints all green; training_checkpoints
  satisfied with all four named store checkpoints loading complete and
  finite; run_manifests NOT fully satisfied and carries F1 and F2 findings;
  hash-label clause reports `canonical_digest_mismatch:cb5475f8…` (anchor
  drift predicted by statement (iii)).
- **P3 (own clause probes at current revision)**: recoverable_commits PASS —
  receipt filename == SHA-256(arrival_id) for every receipt including mine;
  my receipt binds task/attempt/criteria; checkout head `c525b82c…` resolves
  as a commit; six winner merges resolve as commits (ONT-P01, ONT-P03,
  ONT-X01, MAT2-P01 `97993cbe…`, MAT2-P03 `13a94391…`, MAT2-F01 `b0108a36…`).
  training_checkpoints PASS — 4/4 store hashes identical to the merged
  winner's table; complete-structure load evidence (exact payload,
  finite parameters) via the merged module's own parser; run record
  `9cd272ea…` byte-identical at 3 sites; verdicts reported verbatim with
  certified count 0. retry markers all present in the five named records.
  hash labels: map raw `8fa2e140…` == lock `raw_file_sha256`; map canonical
  digest `cb5475f8…` == lock `scope_sha256` == this card's scope; git blob
  label distinct from raw; `verify_catalog` passes with external anchor
  `cb5475f8…`.
- **P4 (run manifests verdict)**: PARTIAL under the lead-accepted ONT-P05
  standard — the mechanism (schema law tokens, fleet + FEATURE_WALK manifests,
  per-attempt `checkout_identity.json`) exists and its modern records verify,
  while F1 (fleet generation oracle) and F2 (walk frames) are re-confirmed
  live and remain named findings for lead disposition.
- **P5 (crosswalk + dependency)**: the governing crosswalk row is
  re-derived from the merged MAT2-P03 artifact and `promoted_to_acceptance`
  is false; dependency verdict: MAT2-P03 read from the live registry
  (read-only) as DONE with winner PR #194 whose merge `13a94391…` resolves.
- **P6 (fixtures, failing-first)**: `test_implementation.py` written and
  executed BEFORE `implementation.py` exists (observed failure captured), ≥ 12
  fixture tests covering: forged receipt filename digest, wrong own-receipt
  identity, missing own receipt, checkpoint hash mismatch, truncated `.npy`
  refusal propagated by the merged parser, run-record site disagreement,
  absent retry marker, dual-label mismatch, crosswalk rows can never emit
  `promoted_to_acceptance: true`, missing winner blob, unresolvable head,
  registry-gap naming.
- **P7 (write boundary + registry)**: `reconciliation.json` records the live
  registry revision (read-only `Registry(...).readonly()`), the exact base
  revision, and the write boundary (only attempt-workspace paths written).

## FALSIFIER (frozen, from the card)

"Missing identities or a claimed pass unsupported by records fails; a
screenshot is not a substitute." Exercised in both directions: fixture tests
prove missing/forged identities are NAMED as findings (never silently
passed), and every clause claimed as passing must carry recomputed hashes or
git resolutions in the output. A pass claimed without a records oracle, or a
silent gap, fails this card.

## FROZEN PROBES

- **Probe A (preservation)**: in the attempt checkout, `git show`
  merge `78f3b524` / `13a94391` blob contents and recompute raw SHA-256;
  compare against winner-receipt hashes (P1).
- **Probe B (refresh)**: materialize the merged ONT-P05 verifier bytes from
  merge `78f3b524` (or read them in-tree at the merge target), byte-verify
  `e45d837d…`, execute unmodified with `--out` inside this attempt workspace
  (CPU-only, `python -B`); score against P2. Its stdout JSON is captured to
  `refresh_identity_audit.json`.
- **Probe C (own reconciliation)**: `python -B implementation.py --out
  reconciliation.json` from this contribution directory; binds every clause
  to current records through independent oracles (recomputed raw SHA-256,
  canonical `sha256-chimera-json-v1` via `integrity`, read-only
  `git cat-file`/`hash-object`, merged-module `.npy` complete-structure
  parse, read-only registry read) with own-identity binding (P3–P5, P7).
- **Probe D (fixtures)**: `python -B -m unittest test_implementation -v` —
  all tests OK after implementation; the pre-implementation run (failing
  first) is captured as evidence (P6).

## Boundary

Profile `records`, offline: no runtime, engine, GPU, rollout or visual claim
is made or needed (`nonvisual_reason`: a records/contract task whose truth
requires records or numerical oracles). Read-only over the live registry and
record trees; the only writes are probe outputs and report files inside this
attempt workspace. Historical-record repair (F1/F2/F3) stays OUT of scope —
disposition is the lead's. CPU-only `python -B`; no numpy needed (the merged
parser is stdlib).
