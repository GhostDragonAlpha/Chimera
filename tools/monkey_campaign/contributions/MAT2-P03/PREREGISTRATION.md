# PREREGISTRATION — MAT2-P03 (ledger reconciliation, material-first crosswalk)

Card `MAT2-P03` (planning P03, group "Scope, identity, and fleet", kind=reconcile,
profile=records/offline). Attempt `fdc55a400ba64ff4b9795ff3d6b753f4`, agent
`arrival-ad31c256f02840e48b99ebbeb12fd3b6`, criteria
`67caf01f86c2ba57b8cae7ebe453d3580bfdd2c5981aee40820c431156fd6135`.
Written and frozen BEFORE the reconciliation tool ran against the live registry
and BEFORE the test suite was executed. Inventory reads used to design the
frozen probes (kanban_cli inbox reads, read-only Registry reads) are declared
above; no verification had run at freeze time.

## RECONCILE-FIRST DECLARATION (prior completed work reused)

The prior-scope card `ONT-P03` (criteria
`1fcf0eea7c11d4d6346a27b09c88bf7144dff9219ff1c0de7f77505e27b5f391`, old scope
`01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`) was DONE via
PR #140 (head `e1443d452ad9e4869e7bc3df20b2e4b98819a34f`, merge `736d12cc…`,
lead ACCEPTED, independent worker review PASS at the same head). Its delivered
tool `tools/monkey_campaign/contributions/ONT-P03/implementation.py`
(raw sha256 at that head:
`fa352857d216df26bd7a55d5fa7b752647f93387d00db282be14800aa0de1a7a`, per the
lead acceptance record in the ONT-P03 card) already tables every live card with
the four ledger identities. This attempt REUSES that design (read-only
`Registry(...).readonly()` access, four-identity per-card row, gap naming,
fixture test shapes) and extends it with the material-first additions the
revised clause demands: (a) crosswalk of archived old-scope receipts to MAT2
requirements WITHOUT promoting old DONE to new acceptance, and (b) a bounded,
frozen search of the existing material graph and code before adding work.
Nothing that ONT-P03 delivered is re-derived or re-implemented from scratch.

## STATEMENT (a theory that can lose)

The live astra-0031 registry (`E:/ChimeraWork/monkey-coordination`, opened
read-only) already carries the four ledger identities (owner, source revision,
scoped verdict, receipt) for every active MAT2 card; the archived pre-adoption
board preserved in the same registry under `scope_archives` (scope
`01ea5cdd…`, frozen) holds 43 cards whose accepted receipts (PR heads, merge
commits, recorded review verdicts) crosswalk deterministically to MAT2 planning
ids as HISTORICAL EVIDENCE ONLY; and the existing repository already contains a
bounded, enumerable set of material-graph/code artifacts relevant to the M01–M12
foundation, discoverable with the frozen path list below. A deterministic
read-only reconciliation can therefore table every live card, crosswalk every
archived card, name every missing identity, and record every absent probe path
explicitly — without writing anything and without promoting a single old DONE
verdict into MAT2 acceptance.

## FROZEN PROBES (exact, before execution)

Probe A (live ledger): `implementation.py reconcile` over registry
`E:/ChimeraWork/monkey-coordination`, output `reconciliation.json`.
Probe B (crosswalk): same run, section `crosswalk`, over
`scope_archives["01ea5cdd…"]["board"]` (archived board sha
`0fca6e61f89a56492ff5b36ab3b78298a1d879c61c0ad50ce26a6accd1be6ab5`).
Probe C (material search): frozen relative-path list against repo root
`E:/PythonChimera`:
  1.  tools/monkey_campaign/monkey_completion_map.json   (canonical catalog)
  2.  tools/monkey_campaign/APPROVED_SCOPE.json           (approved scope)
  3.  docs/MONKEY_RUN.md                                  (current directive)
  4.  docs/THE_MASTER_LIST.md                             (planning)
  5.  docs/THE_HOLODECK_BLUEPRINT.md                      (planning)
  6.  docs/roadmap/holodeck_tasks.json                    (planning)
  7.  docs/architecture/CREATURE_ARCHITECTURE_REBASE_2026-09-15.md (planning)
  8.  agent_logs/local_buffy_qwen/assembly_handoff_02.md  (disk report)
  9.  forearm_package/ANATOMICAL_DECISION_TABLE.md        (disk report)
  10. planning_inventory.json                             (graph inspection)
  11. plans/material-first-v2/                            (historical proposal dir)
  12. Chimera/core/membranes.py                           (existing membrane concept code)
  13. Chimera/core/membrane_shapes.py                     (existing membrane code)
  14. Chimera/core/matter_derive.py                       (existing matter derivation code)
Probe D (tests): `test_implementation.py` fixture tests in isolated temp
registries plus live-structure checks, CPU-only, stdlib-only.
Probe E (identity): sha256 over each delivered artifact, reported in
`report.md`.

## PREDICTIONS (not yet verified at freeze time)

1. Live board: >=6 cards; every card has non-empty `id` and
   `criteria_sha256`; `MAT2-P01` is DONE with winner PR #192, head
   `e61838b9fb058b19631717fc5d15be8c31681954`, merge
   `97993cbefaf00380803d8e67652ac51d50c37d06`; every non-DONE live card has
   at least one attempt carrying all five required identity fields
   (id, agent_id, state, workspace, criteria_sha256).
2. Archived board: exactly 43 cards; state multiset DONE=36, REVIEW=6,
   CHANGES_REQUESTED=1; exactly 36 cards carry an accepted winner receipt
   (winner pr_url + head_sha + merge_commit_sha with an ACCEPTED recorded
   review); `board_sha256` equals
   `0fca6e61f89a56492ff5b36ab3b78298a1d879c61c0ad50ce26a6accd1be6ab5`.
3. Crosswalk: the 22 `ONT-<XX>` cards (A01–A05, F01, P01–P06, S01, U01–U05,
   W01–W02, X01–X02) each map to exactly one MAT2 requirement id `MAT2-<XX>`
   that exists in the live board or backlog; the 21 non-ONT cards (D-*, I-*,
   R5-*) are classified `workflow` and map to no catalog requirement; every
   crosswalk row records `promoted_to_acceptance: false` and
   `historical_evidence_only: true`; old DONE never satisfies a MAT2 clause.
4. Material search: probes 1–8 and 12–14 are FOUND with recorded sha256;
   probes 9, 10, 11 are UNAVAILABLE (absent from the current tree at inventory
   time) and are recorded as explicit UNAVAILABLE entries, never fabricated.
5. Gap honesty: any live card missing one of the four identities appears in
   `missing_detail` (count == `cards_with_missing_identities`); the tool opens
   the registry read-only only (`readonly()`), never transacts.

## FALSIFIER

A claimed pass unsupported by records; a silent gap (missing identity not
named); any crosswalk row marked as satisfying/promoting a MAT2 acceptance from
old DONE; any fabricated hash or invented artifact (including a FOUND probe
whose file does not exist or whose recorded sha256 mismatches); any write to
the live registry; a claimed identity the registry does not contain. If a
prediction fails, the failure is REPORTED verbatim as a finding — it is the
card's work product, not a reason to adjust the probe.

## BOUNDS

Read-only over the live registry; CPU-only; stdlib-only; fixture tests in temp
directories; no production edits; attempt-workspace writes only; total
artifact budget <= 16 MiB (publication handoff cap).
