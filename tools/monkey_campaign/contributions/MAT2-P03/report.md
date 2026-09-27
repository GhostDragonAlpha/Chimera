# MAT2-P03 qualification report — ledger reconciliation with material-first crosswalk

Task `MAT2-P03` (planning P03, kind=reconcile, profile=records/offline).
Attempt `fdc55a400ba64ff4b9795ff3d6b753f4`, agent
`arrival-ad31c256f02840e48b99ebbeb12fd3b6`, criteria
`67caf01f86c2ba57b8cae7ebe453d3580bfdd2c5981aee40820c431156fd6135`,
attempt workspace `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-P03\fdc55a400ba64ff4b9795ff3d6b753f4`,
isolated checkout branch `branch-3` at base `c525b82c7c3ce0128565424764293a3c85811ab3`.
Preregistration was frozen before any verification run (see
`PREREGISTRATION.md`, sha256 `4f23f03dea1d99be61e15c500e574ce35235cc1dcf52d912ef92fdd458b0672e`).

## done_when, clause by clause

Clause: "Every active task has one owner, source revision, scoped verdict, and
receipt; prior completed work is reused. Material-first addition: Crosswalk old
receipts to revised requirements without promoting old DONE to new acceptance.
Search the existing material graph and code before adding work."

1. Owner / source revision / scoped verdict / receipt for every active task —
   `implementation.py` (ON-P03 accepted design reused, read-only
   `Registry(...).readonly()`, no `transaction` call anywhere in the file)
   tables every live card with the four identities and names any missing
   identity. Live snapshot at registry revision 1148: 7 cards; 6 non-DONE
   (5 OPEN + 1 PUBLICATION_PENDING) each with a complete attempt identity
   (all five required fields); 1 DONE (MAT2-P01) with winner receipt
   (PR #192, head `e61838b9…`, merge `97993cbefaf0…`); **0 cards with missing
   identities; zero silent gaps** (`all_identities_present: true`).
2. Prior completed work reused — the accepted ONT-P03 tool (PR #140 head
   `e1443d452ad9e4869e7bc3df20b2e4b98819a34f`, raw implementation.py sha256
   `fa352857d216df26bd7a55d5fa7b752647f93387d00db282be14800aa0de1a7a`) is
   reused as the ledger design; its fixture patterns are reused in tests;
   nothing verified was re-derived or re-implemented.
3. Crosswalk without promotion — archived board
   `scope_archives[01ea5cdd…].board` (board sha256
   `0fca6e61f89a56492ff5b36ab3b78298a1d879c61c0ad50ce26a6accd1be6ab5`,
   reason "Captain stopped all workers and authorized material-first scope
   migration"): **43 archived cards = 22 mapped to MAT2 requirements + 21
   campaign-workflow receipts (D-*/I-*/R5-*)**; 36 archived cards carry an
   accepted winner receipt (winner pr/head/merge + ≥1 ACCEPTED review);
   archived state multiset DONE=36, REVIEW=6, CHANGES_REQUESTED=1. All 22
   mapped targets exist in the live board/backlog; clause relations:
   18 `unchanged`, 4 `extended_material_first` (P01, P02, P03, P06);
   **`promoted_to_acceptance` is false on all 43 rows (count 0)** — old DONE
   is recorded as historical evidence only. This card's own row: ONT-P03
   (criteria `1fcf0eea…`, merged PR #140) → MAT2-P03 (criteria `67caf01f…`,
   this card), `extended_material_first`, not promoted.
   73 of 95 catalog ids have no archived counterpart and are enumerated as
   fresh work in `reconciliation.json`
   (`catalog_ids_without_archived_counterpart`).
4. Material graph/code searched before adding work — frozen 14-path probe:
   **11 FOUND with true sha256** (canonical catalog + approved scope + current
   directive + 4 planning docs + assembly handoff disk report +
   `Chimera/core/membranes.py`, `membrane_shapes.py`, `matter_derive.py` as
   existing membrane/matter concept modules to reconcile against) and **3
   explicit UNAVAILABLE** (absent from the current tree at snapshot time):
   `forearm_package/ANATOMICAL_DECISION_TABLE.md`,
   `planning_inventory.json`, `plans/material-first-v2`. Absence is recorded,
   never fabricated.

## Exact commands and observed results

Working dir: `…\kanban-attempts\MAT2-P03\fdc55a400ba64ff4b9795ff3d6b753f4\checkout\tools\monkey_campaign\contributions\MAT2-P03`

1. Failing-first: wrote `test_implementation.py` before
   `implementation.py`; `python -B test_implementation.py` →
   `ModuleNotFoundError: No module named 'implementation'` (observed,
   expected). Then implemented.
2. `python -B test_implementation.py` → exit 0, **Ran 11 tests … OK**
   (8 fixture tests in isolated temp registries/dirs + 3 live-structure
   tests; live tests skip honestly if the registry is absent). Final clean
   run captured in `tests.log` (sha256
   `be74be6015bdcac0a5b4dc214b0ae2f045ff0179c333c69229ba774be872eeea`).
3. `python -B implementation.py --registry E:/ChimeraWork/monkey-coordination
   --repo-root E:/PythonChimera --out reconciliation.json` → exit 0,
   summary: card_count 7, done_with_winner 1, cards_awaiting_lead_publication
   1 (MAT2-X01, a sibling card's own criteria — not this card), cards with
   missing identities 0, crosswalk 43 = 22 + 21, promoted 0, material 11
   found / 3 unavailable, registry_revision 1148.
4. `sha256sum` over each deliverable (below).

## Preregistered predictions — observed verdicts

| # | Prediction | Verdict |
|---|---|---|
| 1 | ≥6 live cards; ids+criteria everywhere; P01 DONE w/ winner #192/e61838b9/97993cbe; every non-DONE card has complete attempt identity | PASS (7 cards; 0 missing identities) |
| 2 | 43 archived cards; DONE=36/REVIEW=6/CHANGES=1; 36 accepted winner receipts; board sha 0fca6e61… | PASS (exact) |
| 3 | 22 ONT→MAT2 mappings all targeting existing catalog ids; 21 workflow rows; zero promoted rows | PASS (22+21=43; promoted 0) |
| 4 | Probes 1–8, 12–14 FOUND with sha256; 9, 10, 11 UNAVAILABLE | PASS (11 FOUND / 3 UNAVAILABLE) |
| 5 | No silent gaps; read-only access only | PASS (`missing_detail` == gap count; only `readonly()` used) |

No prediction failed; no probe was adjusted after freezing.

## Falsifier status

The falsifier ("missing identities or a claimed pass unsupported by records
fails") was exercised in both directions: fixture tests prove an unclaimed
card is REPORTED as `owner:no_active_attempt` (gap surfaced, not hidden), and
the live run found zero gaps to report. `reconciliation.json` is a
point-in-time snapshot; it records `registry_revision` 1148 and the snapshot
moment (2026-09-26/27 session, immediate pre-submission) per the ONT-P03
reviewer's non-gating suggestion. A screenshot-free records artifact; every
hash above was recomputed from the actual bytes.

## Limits

- Live-board numbers describe revision 1148 and will drift as the campaign
  moves; the crosswalk counts (43/22/21/0) are stable because the archive is
  frozen.
- Material-search annotations identify existing concept modules; they do NOT
  claim any M01–M12 acceptance — that is fresh work (73 catalog ids with no
  archived counterpart).
- Scope: `records` profile, offline; no runtime or visual claim is made.

## Deliverable artifacts (absolute path, sha256)

- `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-P03\fdc55a400ba64ff4b9795ff3d6b753f4\checkout\tools\monkey_campaign\contributions\MAT2-P03\PREREGISTRATION.md` — `4f23f03dea1d99be61e15c500e574ce35235cc1dcf52d912ef92fdd458b0672e`
- `…\MAT2-P03\implementation.py` — `2dca56fec5a622922988f01e06b12671990d1cd3a8df18cb0c1a62287cee6639`
- `…\MAT2-P03\test_implementation.py` — `3e5adbd199fad7d7b7938fb9f9f5f0ec8023a77d54673823d95e2ff934b25076`
- `…\MAT2-P03\reconciliation.json` — `2ea458a294009c16ce8258e3b364af0df31a57d52468a2b9cf5d7f7e1b205b4f`
- `…\MAT2-P03\tests.log` — `be74be6015bdcac0a5b4dc214b0ae2f045ff0179c333c69229ba774be872eeea`
- `…\MAT2-P03\report.md` — this file.

Component-complete per DELIVERY.md: unblocks P04/P05 and M01 (dependency
P03) with a verified ledger + crosswalk; no playable-feature claim.
