# ONT-U03 report — focus-loss/input-release controls qualification candidate

Card `ONT-U03` (U03, profile `controls`, kind motion), attempt
`593b5ff8b920461581bb715826613ad7`, agent
`arrival-b249a6084f3c4525afde7644b08ead4f`, criteria
`a161edd6e1bb2aaf7f55c96503992b17a008f5ebe111032be01d717846aef625`.

## 1. Reconciliation (what existed; what this candidate adds)

U03's implementation ALREADY EXISTS and is integrated in the play lineage:

- `8fc072f3` — "U03 integrated — focus-loss/disconnect policy (41/41;
  consistency-with-U01 held byte-identically; expiry floor; no-stuck fuzz
  clean; honest REVISION A trail)".
- `d2a0e593` — R3 stack review: the one-line `release_all` passthrough on
  `FocusPolicy`, adopted with `product/stack_composition_tests.py` (73/73).
- X02's SessionFlow drives pause/restart through the policy's mapper slot.

The board's card has NO prior PR and no prior attempt advanced past a clean
checkout (all five earlier attempt dirs are unadvanced `branch-1` checkouts;
nothing was discarded). What the card was missing is exactly its completion
clause: **full ontology qualification evidence** (numerical + runtime +
visual/camera under the `controls` motion profile), which the original U03
records (a headless 41/41 falsifier receipt) do not provide.

Evidence source pin: play revision `9afbddcd90164b5544a16fd0bc72278d985eb6e3`
(the live campaign board's pinned base). All 12 source/record files recovered
READ-ONLY via `git show` into this attempt's `reference/` (no checkout, no
branch switch, play worktree untouched at HEAD `8d16d3c1`); hashes in
`reference/EXTRACTION.json`, asserted at probe import:

- SUBJECT `focus_policy.py` = `e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0`
- mapper `input_mapper.py` = `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44`
  (byte-identical to the qualified ONT-U01 subject in merged PR #152)
- seam `command_record.py` = `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e`
- camera referent `follow_camera.py` = `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7`
- preserved U03 falsifier + GREEN receipt: `f1d7a2fd…` / `3e31524f…` (41/41)
- preserved U01 falsifier + GREEN receipt: `95f44e90…` / `00c73e34…` (26/26)

## 2. What ran (exact commands, bounded)

```
python -B tools/monkey_campaign/contributions/ONT-U03/extract_reference.py
python -B tools/monkey_campaign/contributions/ONT-U03/focus_policy_probe.py
python -B tools/monkey_campaign/contributions/ONT-U03/capture_build.py
python -B -m unittest test_focus_policy_probe -v
```

All inside this attempt checkout; CPU-only; each invocation bounded (<120 s
probe/tests, <5 min capture); no GPU, no engine, no browser, no network; the
operator's desktop focus and processes untouched (the "alt-tab" of the
profile is the policy's DECLARED `on_blur` event — synthetic events only).

## 3. Results

### Probe (focus_policy_probe.py) — ALL 10 CHECKS PASS

- `C1_policy_no_stuck_fuzz` — 5000 seeded schedules (seed 20260926),
  43,046 delivered records: every clearing event's positive-speed deadline
  holds, every record in bounds, sink calls emit-only, no phantom key,
  zero forbidden markers. 1 predeclared FIRED deviation (see §4).
- `C2_blur_clears_no_stuck_command` — blur@1600 with W held: held empty at
  once, tail [1600: 0.763625, 1650: 0.0], silence to the 1900 recovery
  press; double blur@1620 a NAMED no-op that does NOT restart the tail;
  scripted-timeline silence holds (no post-zero record at all).
- `C3_disconnect_clears_named_state` — disconnect@2550: same decay law,
  state names `disconnected`, the 2650 S press dropped by name, reconnect
  restores `focused`.
- `C4_press_mouse_dropped_while_unfocused` — press+mouse@1700 dropped by
  name, zero records, held empty.
- `C5_recovery_clean_rearm` — rearmed receipts with EMPTY held sets at
  1800/2700; fresh grid at full demand at 1900; idle blur@2200 emits nothing.
- `C6_age_floor_expiry_gate` — stalled-clock sub-probe: delivered ages
  [0,15,30] ticks kept, [45,60,90] dropped NAMED with issued tick 300; the
  healthy clock drops 0; all 7 frozen-number object identities hold
  (MAX_AGE_MS is VALID_MS); no duplicated frozen literal.
- `C7_consistency_with_u01_release_all` — the policy blur stream is
  byte-identical to U01's own `release_all` (5 records, all fields, source
  `u01_input_mapper`).
- `C8_no_camera_induced_body_movement` — camera-only window [3100,3400]:
  0 events, 0 records, body bit-identical; every camera write on the single
  declared route with exactly the 8 camera fields; body == exact integral of
  delivered records (residual 0.0); max step <= v_max*dt. 1 predeclared FIRED
  deviation (deadband-honest camera wrote 0 inside the window; the U01
  precedent deviation, recorded the same way).
- `C9_obstruction_declared_target_readable` — measured occlusion ray blocked
  at every one of the 69 ticks; close-target distances in [1.5, 3.0] m;
  target center inside the frustum every tick.
- `C10_timing_chain_bound` — issued_tick == t_ms*300//1000 for all 69
  boundaries' records; accepted-press gaps in [0, 50] ms; the two unfocused
  presses reported as named drops (no record by law), not timing failures.

### Capture (capture_build.py) — GATE-VALID

- `evidence/capture.mp4` = `adae7561713afd235c6140ea4ef4bb99496e25e5916a35bcade9a6280c536b1f`
  (242,450 bytes; 414 frames = 6 segments x 69 ticks; 640x360; 20 fps;
  ffmpeg libx264 yuv420p crf23 bitexact threads=1). REBUILD REPRODUCED THE
  IDENTICAL FILE (bitexact verified with cmp).
- `evidence/capture_manifest.json` — chimera.visual_capture_manifest.v1,
  profile `controls`, 3 views x diagnostic+clean pairs, state-bound to the
  trace, all 16 profile camera fields; `visual_gate.verify` against
  `card_task.json` returned `structurally_valid: true` (visual_acceptance
  false by law — independent review remains required).
- trace `evidence/trace.jsonl` = `2dd6f2995d0d2987e0f9054346688bdcfdb27962b3cd9ed876619e386d17192f`
  (117,307 bytes; 69 rows; byte-identical across reruns).

### Tests (test_focus_policy_probe.py) — 16/16 OK in 0.066 s

Reduced-workload suite: pinned hashes, scripted laws (blur/disconnect/
drops/re-arm/camera-window/body-integral/obstruction), reduced fuzz (25
schedules), expiry floor + is_expired boundary, release_all consistency,
mini-manifest structure + clean-view refusal.

## 4. Honest deviations (recorded, never smoothed)

1. `C1` (FIRED, prereg REVISION B): on generated schedule 1774 a live `S`
   press overrode the decaying `W` tail; the mapper's own precedence law
   emitted a SECOND exact-zero record (a live zero-advance target), which
   the gate honestly delivered. The strict two-zeros clause of the preserved
   P6 therefore cannot hold universally on generated schedules; it HOLDS on
   the scripted timeline (C2/C3). No positive speed ever survived its
   deadline; no emission occurs without a live demand. The generated-
   schedule behavior is now a measured observation
   (`second_zero_observations`), and the deviation is recorded in
   `numerical_receipt.prediction_deviations`.
2. `C8a` (FIRED, predeclared): the deadband-honest camera wrote 0 times
   inside the camera-only window (the solution had already settled), so the
   frozen "while camera writes are observed" clause is satisfied by the
   run-level write surface (25 writes, all on the declared 8-field route)
   rather than in-window writes. Identical to the deviation the lead
   accepted on the merged ONT-U01 candidate.

## 5. Artifact identities

| artifact | sha256 |
|---|---|
| evidence/trace.jsonl | `2dd6f2995d0d2987e0f9054346688bdcfdb27962b3cd9ed876619e386d17192f` |
| evidence/capture.mp4 | `adae7561713afd235c6140ea4ef4bb99496e25e5916a35bcade9a6280c536b1f` |
| evidence/runtime_receipt.json | (hashed in the publication request) |
| evidence/numerical_receipt.json | (hashed in the publication request) |
| evidence/capture_manifest.json | (hashed in the publication request) |
| evidence/capture_receipt.json | (hashed in the publication request) |
| reference/EXTRACTION.json | (hashed in the publication request) |
| qualification_receipt.json | (hashed in the publication request) |

The head-bound `qualification_receipt.json` (schema
`chimera.ontology_qualification_receipt.v1`) carries `head_sha: null` with
its binding note: it must be pinned to the EXACT reviewed PR head at
ACCEPTED time (the in-tree copy cannot know its own commit hash).

## 6. Remaining gates (not claimed by this candidate)

- Independent worker review of this exact head (queued automatically by the
  publication request).
- Lead ACCEPTED review pinning `head_sha`, then GitHub merge to
  `astra/gait-capture` via `review/ONT-U03`, then `accept-merge` verification.
- The native playable-runtime checkpoint and the human player-acceptance
  gate stay with the integration lane; a component qualification does not
  satisfy parent gameplay/runtime/human gates.

## 7. Failures encountered and fixed during the candidate's own development

(kept for provenance; all resolved, final state green)
- Policy `__init__` surface check required an `is_expired` passthrough on the
  probe's logging mapper wrapper (the policy drives U01's mapper surface).
- `build_policy` originally returned the inner mapper instead of the logged
  wrapper.
- The double-blur no-op receipt lives in the enclosing tick's trace snapshot
  (t=1650), not a nonexistent t=1620 row.
- C2's original predicate contained a tautological clause; replaced with the
  explicit post-zero scan (and the window now ends before the 1900 recovery
  press).
- C10 originally counted the two NAMED-drop presses as timing gaps; they are
  reported as named drops (C4's law) and excluded from the gap bound.
- Frozen-constant object identity required importing the mapper module the
  same way the pinned policy does (top-level `import input_mapper` against
  the reference path), not via the package path (which had instantiated a
  second module and duplicated the constants).
