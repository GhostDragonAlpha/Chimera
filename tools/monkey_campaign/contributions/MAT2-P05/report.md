# MAT2-P05 qualification report — milestone recovery and artifact identity, reconciled live

**Verdict: the done_when record classes EXIST and verify at the current
revision through the reused, merged ONT-P05 winner oracles — 4 of 5 clauses
pass outright with zero findings; run manifests verify as an existing,
working mechanism while finding F1 (fleet `MANIFEST.json` does not reproduce
against its pinned `source_base`) is re-confirmed live and stays a named,
open finding for lead disposition (the same PARTIAL-with-findings standard
the lead accepted for ONT-P05). The merged prior evidence is preserved
byte-identical in the integration branch (3/3 hashes match); the governing
crosswalk is honored with zero promotions; the dependency MAT2-P03 is DONE
with a resolvable merge. Nothing repaired, nothing fabricated, nothing
silently passed.**

- Card `MAT2-P05`, planning `P05`, kind integration, profile `records`
  (offline, nonvisual). Attempt `01ce64f40de34bcb82782d566ddfed39`, agent
  `arrival-961a6f78a19c4eb58cafb2c7e1fcbcb1`, branch `branch-6` at base
  `c525b82c7c3ce0128565424764293a3c85811ab3`, criteria
  `0fbecb6247f21492706fbfe94c2ac0af81060e26a667bb52c91e6b4d89ea4953`,
  scope `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.
- Dependency `MAT2-P03`: DONE (winner PR #194, merge `13a94391…`, read
  read-only from the live registry, revision 1185 at probe time) — its
  `reconciliation.json` carries the governing crosswalk row for this card.
- Preregistration `PREREGISTRATION.md` (sha256
  `fbf8ca6b0754cc561c0c73585b384b42c921bf4a9be7e437823380cef3a23dc9`) was
  frozen BEFORE implementation existed and BEFORE any probe ran; the
  failing-first test run predates `implementation.py` (captured in
  `tests_failing_first.log`).

## Reconcile-first: what was reused, byte-verified

The legacy card `ONT-P05` (same done_when text) was DONE via PR #174
(head `52dbc2ce…`, merge `78f3b524…`). Its delivered five-clause identity
audit is the known-good verifier for exactly this clause set. This attempt
does not re-implement it: `implementation.py` materializes (or reads
in-tree) the merged verifier bytes, refuses to import unless the raw
SHA-256 equals the winner receipt's `e45d837d…`, then calls its
parameterized clause functions with THIS attempt's identity and the CURRENT
human-pinned scope anchor. Preservation was verified from the integration
branch `origin/astra/gait-capture`:

| Merged prior artifact (at merge) | raw SHA-256 (recomputed) | winner-receipt hash | match |
|---|---|---|---|
| `contributions/ONT-P05/implementation.py` @ `78f3b524` | `e45d837d…7782db6b3cd2` | source evidence | YES |
| `contributions/ONT-P05/identity_audit.json` @ `78f3b524` | `30f33924…f846459489d9e` | numerical evidence | YES |
| `contributions/MAT2-P03/reconciliation.json` @ `13a94391` | `2ea458a2…7f7e1b205b4f` | numerical evidence | YES |

Crosswalk (from the merged MAT2-P03 artifact, extracted live):
`ONT-P05 → MAT2-P05`, `clause_relation: "unchanged"`,
`promoted_to_acceptance: false`, `historical_evidence_only: true`,
archived receipt = PR #174 / head `52dbc2ce…` / merge `78f3b524…` with 1
accepted review. The legacy DONE is historical evidence; this card
qualifies only on the live re-derivation below.

## Measured against the live records (Probe C, registry revision 1185)

| Clause | Verdict | Records and oracle results |
|---|---|---|
| Recoverable commits | **PASS** (0 findings) | 265 `chimera.startup_recovery.v1` receipts, every filename == SHA-256(arrival_id); own receipt `8daed2f6…` binds task `MAT2-P05`, attempt `01ce64f4…`, criteria `0fbecb62…`; `checkout_identity.json` head `c525b82c…` resolves as a commit on `branch-6`; MAT2 winner merges resolve 3/3 — `MAT2-P01 97993cbe…` (PR #192), `MAT2-P03 13a94391…` (PR #194), `MAT2-F01 b0108a36…` (PR #195); the reused verifier resolved its 3 legacy merges (ONT-P01/P03/X01) in the same clause |
| Run manifests | **unmet** — mechanism verified, findings preserved | Schema law records present 3/3 (`chimera.checkpoint_context.v1` in `checkpoints.py`, `chimera.visual_capture_manifest.v1` in `visual_capture.py`, candidate-manifest law in `CHECKPOINT_WORKFLOW.md`); fleet `MANIFEST.json` present (21 entries, `source_base bf0a6216…`); walk `MANIFEST_sha256.txt` present (raw `951724b6…`); generation oracle: **0/16 sampled entries match** — 7 `generation_blob_unreadable` + 1 `generation_mismatch` (THE_MASTER_LIST) + 8 `manifest_generation_mismatch` = 16 findings, the same composition the lead accepted as PARTIAL for ONT-P05 (**finding F1, re-confirmed live**); **finding F2** (FEATURE_WALK `g*.png` frames preserved nowhere reachable) remains as recorded in the merged audit, unmodified. Disposition is the lead's; this card neither repairs nor hides it |
| Training checkpoints | **PASS** (0 findings) | Store table 4/4 identical to the merged report's frozen hashes: `walk_theta_entrained.npy 8f5dd3a6…`, `walk_theta_mult.npy ad8ed9a9…`, `stand_theta.npy 684f1eaa…`, `step_theta.npy db943f46…` (108 `.npy` in store); complete-structure `.npy` load evidence via the merged module's own parser; run record `f4_walk_walk_theta_entrained.json 9cd272ea…` byte-identical at 3 preserved sites (l0-baseline-repro, lane-archive/w47-agent, pass3-integ/repo); `certified_policy_checkpoints: 0` reported VERBATIM — no checkpoint belongs to a certified walk; law tokens present (`checkpoints.py` receipt schema, CHECKPOINT_WORKFLOW table, CHECKPOINT_VERIFICATION); `test_checkpoints` battery green |
| Raw/blob/canonical hash labels | **PASS** (0 findings) | For the sealed map: raw `8fa2e140…c61543cb272`, git blob `728da4775fff8e435805702293ba215e8e3b3035`, canonical `sha256-chimera-json-v1` `cb5475f8…57996097` — three DISTINCT labeled identities; scope lock `raw_file_sha256` binds the map's bytes; `scope_sha256` == canonical == this card's scope; `verify_catalog` PASSES with the human-pinned external anchor `cb5475f8…` (`external_digest_checked: true`) |
| Retry rules | **PASS** (0 findings) | All 5 markers present (`ALREADY_COMPLETED` in kanban.py, `PUBLICATION_ALREADY_REQUESTED` in continuous_cycle.py, `exact_retry` in suggestion_box.py, retry accept-merge in MERGE_SERVICE.md, arrival-ID retry in STARTUP_RECOVERY.md); 4 merge-service `accept-*-result.json` receipts; batteries re-executed green: test_kanban, test_suggestion_box, test_merge_service, test_checkpoints |

`first_unmet_clause`: `run_manifests` — under the card falsifier ("missing
identities … fails") this card does not claim a clean 5/5: the fleet
manifest's `source_base` label does not bind the content it labels (F1),
and the walk frames F2 labels are unpreserved. Everything else about the
manifest mechanism (schema law, manifests, per-attempt
`checkout_identity.json`, dual-labeled scope lock) exists and verifies.

## Probe B — labeled refresh run of the unmodified merged verifier

The merged ONT-P05 verifier, bytes unmodified (hash-verified `e45d837d…`),
was re-executed at its own frozen identity/anchor → exit 0, output
`refresh_identity_audit.json` (raw `f4c0f23a…c7957d7`, == its stdout log).
Observed, verbatim: receipt_count 265; run_manifests **16 findings,
identical composition** to the merged official probe; training_checkpoints
satisfied (4 artifacts, 3 run identities, certified 0); retry_rules
satisfied; hash_labels reports exactly the predicted old-anchor drift
(`canonical_digest_mismatch:cb5475f8…`, `TRUST_ANCHOR_MISMATCH`) because
the verifier is frozen at scope `01ea5cdd…` while the campaign migrated to
`cb5475f8…` — the same triple-label mechanism verifies under the current
anchor (row above).

**New named finding (N1): the legacy verifier's own-receipt binding is now
stale.** Its frozen receipt stem `e253f0cc…` (= SHA-256 of arrival
`arrival-9887482e…`) NOW contains task `ONT-A01`, attempt `7fe00a83…`,
criteria `2bcf59fa…` — that arrival id was later re-used and the receipt
law overwrites on resume. Direct file read confirms it. The refresh
therefore reports 3 `own_receipt_mismatch` findings. This is a records
drift, not a defect this card can repair (the receipt is live data by
law); reported for lead disposition. THIS card's own receipt binding is
verified live and passes.

**Statement correction (honest disclosure):** preregistration statement
item (ii) expected the curriculum file's entry count to have changed
("now different"). Observed: 18 entries, all `status: pending` — unchanged
(the pre-freeze inventory read had misread the JSON key). No frozen
prediction referenced curriculum counts, so the scorecard below is
unaffected; the wrong expectation is recorded, not silently dropped.

## Preregistered predictions — observed verdicts

| # | Prediction | Verdict |
|---|---|---|
| P1 | 3/3 merged prior artifacts byte-match their winner-receipt hashes | **PASS** (3/3 exact) |
| P2 | refresh exit 0; receipt_count ≥ 200; refresh recoverable_commits satisfied; retry batteries green; training checkpoints satisfied; run_manifests not fully satisfied with F1+F2; hash_labels reports `canonical_digest_mismatch:cb5475f8…` | **PARTIAL FAIL — sub-claim 3 wrong**: exit 0 ✓, 265 ≥ 200 ✓, retry ✓, training ✓, run_manifests+F1 ✓, anchor drift string exact ✓ — but refresh recoverable_commits satisfied=**false** (3 `own_receipt_mismatch`, finding N1 above). Reported as observed; the failure is the work product, not tuned away |
| P3 | own clause probes pass (own receipt law + 6 winner merges + checkpoint store table + triple hash labels under current anchor) | **PASS** (receipt_count 265, own binding exact, 6/6 merges resolve, 4/4 store hashes, labels distinct, `verify_catalog` pass) |
| P4 | run_manifests = partial under the accepted standard: mechanism present, F1/F2 re-confirmed | **PASS** (schema 3/3 + manifests present; F1 0/16 sampled; F2 unchanged) |
| P5 | crosswalk row exact and unpromoted; MAT2-P03 DONE with resolvable merge | **PASS** (`promoted_to_acceptance: false`; merge `13a94391…` resolves; criteria match) |
| P6 | failing-first fixtures ≥ 12 | **PASS** (23 tests, all OK after implementation; pre-implementation `ModuleNotFoundError` captured) |
| P7 | registry revision recorded read-only; write boundary enforced | **PASS** (revision 1185; `ensure_within` refuses outside-workspace writes) |

## Falsifier status

"Missing identities or a claimed pass unsupported by records fails; a
screenshot is not a substitute." Exercised in both directions: fixture
tests prove forged/missing identities are NAMED (wrong filename digest,
wrong own-receipt fields, absent receipt, hash mismatch, absent artifact,
unresolvable merge/head, promotion attempt refused); the live run names
every gap found (run_manifests clause not claimed as a clean pass; N1
named; no silent gaps). Every pass above carries a recomputed hash or git
resolution; no screenshot is offered or needed.

## Exact commands and observed results

```
cd <attempt>/checkout/tools/monkey_campaign/contributions/MAT2-P05
python -B -m unittest test_implementation          # 23 tests, OK (fixtures, temp dirs/git repos)
python -B -m unittest test_implementation          # FIRST run, before implementation.py existed:
                                                   #   ModuleNotFoundError: No module named
                                                   #   'implementation' (tests_failing_first.log)
python -B implementation.py --out reconciliation.json   # official Probe C (exit 0)
```

Probe C internally: byte-verifies and imports the merged verifier,
re-executes it unmodified (`refresh_identity_audit.json`, exit 0), reads
the live registry read-only (`Registry(...).readonly()`), re-executes the
four rule batteries (all OK), and writes only inside this attempt
workspace.

## Limits

- Records and hash oracles only (profile `records`, offline): no runtime,
  engine, GPU, rollout or visual claim is made or needed.
- Live-store numbers describe registry revision 1185 / receipt store 265
  and drift as the campaign moves; preservation hashes (P1) are frozen by
  the merges and stable.
- Historical-record repair is OUT of scope: F1, F2 and N1 are reported
  verbatim for lead disposition; this card neither rewrites preserved
  evidence nor repairs live stores.
- The refresh run's stale own-receipt binding (N1) means the merged
  verifier can no longer reproduce its ORIGINAL live self-identity check;
  its clause machinery, oracles and preservation are intact, as this
  card's own binding demonstrates.

## Deliverable artifacts (raw SHA-256)

- `PREREGISTRATION.md` — `fbf8ca6b0754cc561c0c73585b384b42c921bf4a9be7e437823380cef3a23dc9`
- `implementation.py` — `cb323823904100d2011f31f515db30336ddece8148477ec13e0e4ae92952fa3b`
- `test_implementation.py` — `509f77db93d03178ec87a7a93ebff8686b6469fa5e78df94f16ce4e8cfd71880`
- `tests_failing_first.log` — `8ac357ef23472675610a7da19cea3d165b5327f2d27322e122cc7ffda1131e8d`
- `tests.log` — `3a9137ad902010092e64e692684e3f57e20b0719cd3e50d3262f8d46dfef2f28`
- `reconciliation.json` (official probe output) — `eded080636474d1c39f76c68e36394105aa285d9b35b54f9eb95550015fc2e8b`
- `refresh_stdout.log` (refresh run stdout, == refresh output JSON) — `f4c0f23a2357409ead5418ed74598244b93a141c31aeb084ec97171f8c7957d7`
- Attempt-workspace reference: `refresh_identity_audit.json` — `f4c0f23a2357409ead5418ed74598244b93a141c31aeb084ec97171f8c7957d7`

Component-complete per DELIVERY.md: retains the verified milestone
recovery/artifact-identity machinery at the current revision and unblocks
its dependents; no playable-feature claim is made.
