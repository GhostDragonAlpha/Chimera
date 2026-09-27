# ONT-U05 report — candidate submission of the climb/let-go intent seam

Attempt `b60923e0331d44b1b4ac03dbd327bc01`, agent
`arrival-3c2e330f584e4c399906ec4eff127054`, 2026-09-26.
Branch `attempt/ont-u05-b60923e0`, base `56d0116a` (then-tip of
`astra/gait-capture`; contains the U01 dependency merge `048b63f4`, PR #169).
Criteria: `699696427b5c52bad16f970e88af13e5dbfb137533d8d48c890f126676d28f92`.
PREREGISTRATION.md was frozen before the first artifact write in this attempt
(all hashes in it were observed read-only beforehand).

## 1. Reconciliation — what already existed, and what this card needed

The U05 row's own observation is "Requires a reviewed interface decision, not an
invented API", and the map row is kind `decision+implementation`. Reconciliation
(read-only) found that BOTH legs already exist — in the game lineage, not in the
kanban lineage this card lives on:

* **The reviewed interface decision**: `INTENT_SEAM_SPEC.md` v1 (frozen with its
  prereg 2026-09-24 BEFORE implementation; recovered at
  `recovered/U05_climb_intent/INTENT_SEAM_SPEC.md`,
  sha256 `772d809df620bb93cce97fd41f081ba244b44edfef8d9ee4797f16cc8eac143b`),
  REVIEWED by the R4 interface review: **APPROVED-WITH-AMENDMENTS** — all six
  interface rulings APPROVE; four binding implementation amendments (AMR-1..4)
  landed inside v1
  (`recovered/R4_intent_review/report.md`,
  sha256 `e456945f568e2c7eb750cd807607152e83da2d19a28875fdc07dedafb25de418`).
* **The implementation**: `product/climb_intent.py` v1 at pinned game-lineage
  commit `9afbddcd90164b5544a16fd0bc72278d985eb6e3`, integrated by `87c14ca5`
  ("U05 integrated — climb intent seam v1 (73/73; ... spec shipped for review)")
  and amended by `272e7bda` ("U05 amendments + U06 integrated — R4's 4 binding
  fixes failing-first (77/77; R4 battery 27/27 clean)").
* **The kanban gap**: `astra/gait-capture` carries NONE of it; the ONT-U05
  card's five earlier attempt workspaces were empty bare checkouts (verified
  2026-09-26). The card therefore needed the existing verified work carried
  through this card's submission path as a hash-pinned candidate — NOT a
  rewrite ("reuse verified work. Do not repeat completed implementation").

Clause map of done_when → current evidence:

| clause | evidence |
|---|---|
| "One explicit climb/let-go intent" | the closed two-intent edge-triggered vocabulary (`climb_request`, `let_go`), I1 + I8 fuzz; spec sections 2-4 |
| "reaches the skill selector" | the channel delivers versioned `IntentEvent`s to the DECLARED consumer interface the selector implements (`emit(IntentEvent)`, spec section 7); the selector does not exist yet (K-series) by the map's own dependency layering (K01/K06 downstream), and the map's observation clause makes the interface ruling the reviewable artifact — which is R4-APPROVED |
| "with versioned semantics" | `intent_version` field, refusal of any other version, the frozen version-bump rule (spec section 4), AMR-1 bool-refusal |
| "frozen walk contract remains unchanged" | structural (imports only `PHYSICS_HZ`, never constructs `CommandRecord`) + measured (I6 seam-hash start==end in every run, original and fresh) + integration (Space stays U01's NAMED walk refusal, zero walk records) |

## 2. What this attempt wrote

Everything under `tools/monkey_campaign/contributions/ONT-U05/` only:

* `PREREGISTRATION.md` — this attempt's frozen prereg (statement, prediction,
  falsifiers F-R1..F-R5, ownership, run protocol).
* `climb_intent.py`, `climb_intent_tests.py`, `climb_intent_amr_tests.py` — the
  candidate, BYTE-EXACT from the pinned revision (hashes below; F-R1).
* `reference/` — byte-exact pinned dependencies the suites import
  (`command_record.py`, `input_mapper.py`, `focus_policy.py`,
  `session_flow.py`) + `reference/EXTRACTION_LEDGER.json`
  (sha256 `ae03fc496f5896cf373f72866694797226073a4b1161f3cd71b3b75d011d5067`,
  35 entries, `byte_exact: true` on every entry).
* `recovered/` — the pinned provenance: the reviewed spec, both original
  preregs, integration notes, the R4 review + its receipts, the original green
  receipts (33 files, all byte-exact per the ledger).
* `test_climb_intent_candidate.py` — this attempt's NEW conformance suite
  (20 unittest cases: hash binding, version law, C12 stamps, edge law, gate
  law, no-fabrication, pure signal, I7 integration, full-suite subprocess
  re-runs). The only new code in this submission; it writes no semantics.
* `evidence/` — fresh run receipts (below). `card_task.json`, `receipt.json`,
  this report.

Extraction method: `git -c safe.directory='*' -C E:/ChimeraWork/monkey-play-20260924
show 9afbddcd...:<path>` piped to files. No checkout, no branch switch, no edit
of any source repository; `E:/PythonChimera` untouched (read-only `git`
inspection only).

## 3. Verification — commands, identities, observed results

Run environment: `<workspace>/runenv/` — an uncommitted repo-shaped mirror of
the byte-exact recovered files (all seven hashes asserted equal to the pinned
hashes before running; see receipt.json). CPU-only, `python -B`, each invocation
`timeout 120`, output a few KB (budget 16 MiB). No network, no installs, no GUI,
no native build, no GPU, no training, no process control.

| # | command (cwd) | exit | observed |
|---|---|---|---|
| 1 | `python -B tools/monkey_campaign/product/climb_intent_tests.py` (runenv) | 0 | `RESULT: GREEN -- all falsifier checks passed`, 73 `[PASS]`, `seam sha256 at start:` AND `at end:` = `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` (I6 fresh) — `evidence/suite_main_20260926.txt` |
| 2 | `python -B tools/monkey_campaign/product/climb_intent_amr_tests.py` (runenv) | 0 | `RESULT: GREEN -- all 4 amendment checks passed`, 4 `[PASS]` — `evidence/suite_amr_20260926.txt` |
| 3 | fuzz reproduction check | — | I8 numbers BIT-IDENTICAL to the original author receipt (recovered, hash-pinned): `events=354, accepted=354`, `let_go=185`, `named_drops=1089`, `repeat=416, no_op=744`, seed 20260924 — third independent reproduction (author, R4, this attempt) |
| 4 | sabotage 1: scratch copy with the repeat-press guard DELETED (edge law broken) | 1 | `RESULT: FAIL (14 falsifier checks fired)` starting `FIRED: I1.b a HELD key emits ZERO further events...` — `evidence/sabotage1_edge_law_fails_20260926.txt` |
| 5 | sabotage 2: scratch copy with `_gate_open` replaced by `True` (gate law broken) | 1 | `RESULT: FAIL (11 falsifier checks fired)` starting `FIRED: I3.b press while paused: ZERO events, dropped BY NAME` (incl. I7 integration hits) — `evidence/sabotage2_gate_law_fails_20260926.txt` |
| 6 | sabotage 3: scratch copy with the version validator accepting 2 | 1 | `FIRED: I2.h a wrong intent_version is REFUSED` — `evidence/sabotage3_version_law_fails_20260926.txt` |
| 7 | pristine re-run after sabotages (mutations were confined to `runenv_sab*` scratch trees; `diff -q` confirms they differ from pristine) | 0, 0 | both suites GREEN again — `evidence/suite_main_post_sabotage_restore_20260926.txt`, `evidence/suite_amr_post_sabotage_restore_20260926.txt` |
| 8 | `python -B -m unittest test_climb_intent_candidate -v` (contribution dir) | 0 | `Ran 20 tests ... OK` — `evidence/candidate_suite_20260926.txt` |

**Failing-first honesty**: attempt run 1 of my own unittest suite FAILED
(1/20): my checker asserted the string `"CommandRecord"` absent from the module
source, but the module's docstrings NAME the separation law — the module's own
I5 note ("docstrings that NAME the separation law are not violations of it")
and the original author's REVISION A record the same checker-defect class ("the
I5 source scan read prose where it meant code"). Fixed my CHECKER (kept the AST
import-surface check and the `CommandRecord(` not-constructed regex; removed
the prose scan); the committed candidate bytes were never touched. This is the
only failure observed in this attempt; no channel semantic moved.

Falsifier self-check (prereg F-R1..F-R5):

* **F-R1 lineage drift**: NOT observed — all 35 ledger entries `byte_exact`.
* **F-R2 suite failure**: NOT observed on byte-exact trees (runs 1, 2, 7, 8).
* **F-R3 undetected sabotage**: NOT observed — each of the three sabotaged
  copies FAILED with named checks (runs 4-6). The falsifier checks are not
  vacuous.
* **F-R4 walk contract touched**: NOT observed — `command_record.py`
  `67711759...` start==end in every full run; AST: the candidate imports
  exactly `PHYSICS_HZ` from the walk seam's module and never constructs
  `CommandRecord`; walk/intent sinks never receive each other's records.
* **F-R5 invented semantics**: NOT observed — the candidate bytes are the
  pinned bytes; the only new code is the conformance suite, which introduces no
  vocabulary, trigger, drop, stamp or version behavior, and builds no selector.

C12 ("Input timing and control mapping — 20 Hz implies a 50 ms command
interval, not an end-to-end latency guarantee"): the intent channel is
edge-triggered and NOT on the 50 ms decision grid (delivery is synchronous at
the press, spec section 5); stamps ride the walk seam's convention
(`issued_tick == now_ms * 300 // 1000`, injected `tick_source` overrides) so
intents and CommandRecords correlate on ONE timeline. Measured by
`C12Stamps` in the candidate suite. No latency claim is made.

## 4. Applicability boundary (controls/motion profile — honest limits)

The profile's native/visual probes (follow-camera, obstruction views, captured
body state) do NOT apply to this clause-set yet, and claiming them would
falsify: the intent channel has NO runtime consumer (the selector is K-series;
the live wiring belongs to the harness/session-flow integration) and climbing
does not exist in any accepted build. This submission therefore claims: the
REVIEWED interface decision (R4-approved), a versioned delivery channel whose
discipline is falsifier-measured headlessly, and byte-isolation of the frozen
walk contract. NOT claimed: live key feel, any in-game climb observation, any
selector behavior, any actual-play acceptance. U07's actual-play lane and the
K-series runtime/visual gates remain the open path for those clauses; per the
packet, downstream skills are not required to accept this upstream interface
here.

## 5. Remaining gates

* Independent review of THIS candidate (the lead's review lane; review/ONT-U05).
* Publisher integration into the game lineage (production `product/` path
  remains lead-serialized; U01's contribution set the same precedent).
* K01/K06: what an intent MEANS; U06: rendering; wiring + actual-play lane.
* The six spec rulings are APPROVED; spec-notes N1-N6 are recorded v2
  candidates, NOT defects, and bind nothing at v1.

## 6. Failures and deviations

* My unittest suite's first run failed 1/20 (my checker's prose scan) — fixed
  in the checker, documented in section 3; no candidate byte changed.
* One sabotage mutation (version law) initially produced a SyntaxError instead
  of a falsifier firing; the mutation was rewritten to a balanced expression
  and re-applied before ANY receipt was recorded as a sabotage result. The
  malformed first attempt was never counted as evidence.
* Deviation from the default packet branch: the attempt branch is based on
  current `origin/astra/gait-capture` (`56d0116a`) rather than the prepared
  branch-3 checkout head (`c525b82c`), because the card's publication base IS
  `astra/gait-capture` and a branch-3-based head would drag seven unrelated
  campaign-workflow commits into the PR. branch-3 was left untouched; all work
  stayed inside this attempt's workspace.
