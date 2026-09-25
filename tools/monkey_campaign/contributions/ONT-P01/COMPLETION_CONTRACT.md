# Playable-monkey completion contract — FROZEN v1.0.0

**Card:** ONT-P01 (planning task P01) · **Frozen:** 2026-09-25 ·
**Status:** FROZEN · **Machine record:** [completion_contract.json](completion_contract.json)

This artifact freezes the completion contract for the playable-monkey game. It binds
the contract's meaning to the sealed records by recomputable identities and adds an
executable oracle ([verify_completion_contract.py](verify_completion_contract.py)).
It changes no task status, adds no requirement, and completes nothing. A freeze is
not a pass.

## RULE 0 — this contract is a theory

- **STATEMENT:** Completion is exactly the sealed 83-item map's 76 selected items with
  item-scoped integrated evidence, plus the integrated ground-tree-ground playthrough
  (K08) on the native runtime and the operator's explicit acceptance of actual play
  (S05). Nothing outside the sealed list gates completion.
- **PREDICTION:** At freeze time no record establishes game completion; the integrated
  playthrough and operator acceptance remain open. Freezing this contract changes no
  task acceptance status.
- **FALSIFIER:** Any completion claim lacking item-scoped evidence, the native-runtime
  playthrough record, or explicit operator acceptance is false. Any identity below that
  cannot be recomputed from the actual records invalidates this contract.

## The finish line (verbatim from the sealed map)

> Playable monkey game first; broader Chimera vision later.

The player controls one physically simulated monkey in one finite forest clearing:
walk on all fours, steer, stop, approach one rigid trunk, attach, climb, hold,
descend, release, resume walking — with a usable camera and complete player flow.

## Success conditions

| ID | Condition | Evidence-bound tasks |
|----|-----------|---------------------|
| SC-GROUND | Player-controlled all-fours walking that steers and stops, produced only by approved physical actuation on the declared terrain envelope | W07, F06, U04, P06 |
| SC-TRUNK | One rigid climbable trunk; grip, support and release through the physical solver — no invisible anchors, no kinematic substitutes | F03, G04, G07 |
| SC-LOOP | The complete ground→tree→ground loop in one session on the native runtime, with explicit walk/climb arbitration and boundary/failure behavior | K06, K07, K08 |
| SC-FAILURE-BEHAVIOR | Failures remain physical and visible (falls, rejected grips, lost contact); no silent teleport or hidden support; the player has an explicit way to continue | G07, K07, R06 |
| SC-PLAYER-FLOW | Launch, settings, pause/restart, persistence, follow camera and command mapping meet the frozen P06 limits; package identity matches the accepted game | P06, U01–U07, R01–R07, S01 |
| SC-ACCEPTANCE | All selected core/product behaviors pass; remaining issues triaged explicitly; the operator accepts actual play | S05 |

Terminal clauses, verbatim:

- **K08:** "Player approaches, attaches, ascends, holds, descends, releases and resumes
  all-fours walking in one session"
- **S05:** "All selected core/product behaviors pass; remaining issues are triaged
  explicitly; operator accepts actual play"

## Explicit failure behavior (what the game must do when things go wrong)

1. Loss of support produces accounted falls — the support's forces vanish and the
   monkey's motion and energy are accounted (G07); never a frozen mid-air rescue.
2. Out-of-reach grips, rejected grips and excessive loads terminate or transition
   according to the frozen climbing specification (K07); visible to the player.
3. Focus loss, held input across pause/resume/restart and repeated close preserve the
   invariants: released input never stays latched, paused flow emits no locomotion,
   owned teardown happens exactly once (R06).
4. Every failure state leaves the player an explicit, in-game way to continue
   (restart/respawn path, R-cards). No failure requires killing a process.

## Exclusions (broader features are OUT of this contract)

- **Conditional items B01–B07** (material/assembly modernization): required only if the
  selected playable build actually consumes them; never auto-activated; activation
  requires a lead scope amendment with operator authorization.
- **Deferred families** (post-completion backlog, verbatim titles): multiple tree forms
  and branch traversal; jumping/swinging/brachiation/get-up/carrying; more species;
  multiplayer and networked persistence; large streamed worlds; water/weather/thermal/
  chemical; deformable trees and tissue surgery; creator tools/UGC; space/vehicles/
  economies/social; XR/haptics/advanced research.
- **Forbidden substitutes:** kinematic locomotion; invisible support forces or hidden
  anchors; invented anatomy/constants/thresholds/supersessions; percent-complete or
  calendar forecasts; reports, screenshots or PRs counted as completion; a merged
  diagnostic qualifying its parent gameplay task.

## Acceptance oracle

Per item: sealed verification profile at the reviewed exact head — a diagnostic or
scaffold never qualifies its parent. Integration: checkpoints collect contributors and
never gate them; K08 and R07 are measured on the native runtime. Human terminal: only
the operator's explicit acceptance of actual play (S05) completes the game — no agent
self-acceptance, no automatic completion, no synthetic pass.

## Frozen identities (recomputed, not trusted)

| Identity | Value |
|----------|-------|
| Scope content digest (sha256-chimera-json-v1) | `01ea5cdd…ef6` — full value in the JSON |
| Map raw SHA-256 | `010311bb…161` |
| Lock (APPROVED_SCOPE.json) raw SHA-256 | `92d0c33f…397` |
| Ontology definition raw SHA-256 | `57ded6eb…5c1` |
| Task inventory | 83 = 76 selected + 7 conditional (B01–B07) |
| Calculation contracts | 28 |
| Amendment chain | `33a8fb72…` → `5b07ce0c…` → `01ea5cdd…` (P04 correction, then ontology alignment; both operator-authorized) |

The amendment chain is the reconstruction path: each amendment records its previous and
resulting scope digest, ending at the human-pinned value. The trust anchor is the
operator's pinned fingerprint, never a newly computed digest.

## Verification

```bash
python verify_completion_contract.py \
  --map E:/PythonChimera/tools/monkey_campaign/monkey_completion_map.json \
  --lock E:/PythonChimera/tools/monkey_campaign/APPROVED_SCOPE.json \
  --ontology E:/PythonChimera/tools/membrane_ontology/ontology.json
```

Exit 0 with `outcome: PASS` = every identity recomputed from the records agrees.
Any drift refuses with a named failure (`P1…`, `P2…`, `P3…`, `P4…`, `contract_*`).
Tests: `python test_verify_completion_contract.py` (bounded; includes live-records
integration when the campaign records are present).

## Authority and limits

- Sealed scope and acceptance bar remain governed by the operator's pin and the lead;
  this contract binds completion **semantics** only and cannot add, remove, weaken or
  reinterpret any sealed item, criterion or dependency (that requires a scope amendment).
- This card (P01) closes when the lead reviews and merges this freeze; it does not mark
  any planning task accepted and does not complete the game.
