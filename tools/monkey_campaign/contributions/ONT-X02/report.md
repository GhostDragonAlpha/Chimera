# ONT-X02 — motion-profile qualification (correction, lead msg-f4584623)

**Verdict: the card's done_when is MEASURED GREEN on the pinned M-X02 lineage
with the full motion-profile evidence the lead required: 9/9 frozen runtime
checks, byte-deterministic trace, camera manifest per visual_gate (2 views x
diagnostic+clean, motion-kind trace bindings, video capture) validated with
the campaign's own gate, and the preserved reconciliation reused as the
records leg. Two frozen sub-clause mispredictions FIRED and are recorded as
deviations — not smoothed.**

- Card `ONT-X02` (X02, verification profile `recovery`, kind motion), attempt
  `c3f7e9025d5645248f7a7a21f3b47f8a`, agent
  `arrival-2350ac01b46a42cc8c3b3aae3d545862`, criteria
  `a266d16164e64af20505d4ed5d76a532ebb74f3bd0975cfd548546eaa92c71bf`.
- Correction scope (lead, inbox): add motion-profile qualification over the
  ALREADY-IMPLEMENTED session_flow — before/after pinned state through reload,
  pause/resume, reconnect/focus loss, safe teardown, camera manifest per
  visual_gate, runtime evidence; reconciliation reused as the records leg.
- `PREREGISTRATION.md` frozen before the probe ran (first probe run is later
  than the file; both committed in this candidate in that order).

## Subject identity (nothing edited, nothing reimplemented)

Pinned play commit `f30f2224663324e9374b076938c56672febf4082` recovered
READ-ONLY (`git -C E:/ChimeraWork/monkey-play-20260924 show …`) into
`reference/` and hash-asserted at every import (probe + suite):

| source | sha256 |
|---|---|
| product/session_flow.py (the subject) | `30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf` |
| product/input_mapper.py | `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` |
| science_funnel/typeb_export/command_record.py | `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` |
| product/follow_camera.py | `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7` |

This also resolves the reviewer's non-gating observation on PR #135: the
candidate imports the pinned bytes from `reference/` (the D-W03 TIE2-guard
pattern), so it no longer depends on the live play worktree (HEAD `8d16d3c1`,
untouched; play repo left read-only).

## Runtime evidence (done_when, measured)

One deterministic headless run (ticks 0..3300 ms, 50 ms grid) drives the REAL
`SessionFlow` + REAL `InputMapper` + recording world doubles + REAL
`FollowCamera` (deterministic session-derived anchor provider; the reload
resets the provider per the DECLARED boot semantics). 9/9 checks green
(`evidence/numerical_receipt.json`, trace
`5e15d57d71a8f1b638584e2af9e6680d735da3fc77fcce45b56da99471f998e0`):

- P1 reaches play key-only (public mutators exactly key/mouse/tick);
- P2 pause key-only, quiesce, zero mapper events + zero records while paused;
- P3 focus-loss decay-tail law (<=2 records, <= pre-loss speed, exact 0.0,
  then silence);
- P4 reconnect fresh grid at the pre-loss rate, no phantom keys;
- P5 reset is an explicit user action (R from PAUSED: world contact exactly
  release_all+boot x1; R while playing: named no-op, zero world calls; 6
  zero-event ticks transition nothing);
- P6 before/after pinned state through reload (pinned boot state restored
  exactly: origin anchor, held empty, identical bookmark pose, boot delta 1,
  no stale records, fresh press resumes at 0.763625);
- P7 safe teardown exactly once, terminate->wait->kill, terminal exit, mapper
  frozen after exit;
- P8 resource containment (world contacts exactly boot x1 + the teardown
  triple; zero undeclared world attribute attempts; zero records attributed
  to non-playing ticks);
- P9 camera/state binding (bookmark constant across all 67 ticks; follow
  quaternions unit, distances consistent).

Reruns are byte-identical (trace + receipts; the video rebuilds bit-exact).

## Falsifier scorecard (honest)

- **P3 sub-clause FIRED**: the frozen prediction named t=850/900 for the
  focus-loss tail; measurement shows U01's own law samples the first tail
  record AT t=800 (release_all coincides with the boundary; elapsed=0 ->
  full v0) and exactly 0.0 at 850. The frozen LAW holds; the named-boundary
  misprediction is recorded in `numerical_receipt.prediction_deviations`.
- **P6 sub-clause FIRED**: the frozen prediction said "anchor at the boot
  origin both sides"; the pre-reload paused session had walked
  ([0.049, 0, 0.8] at t=1850) — continuity, not the pin. The measured law:
  the pinned BOOT state (attract t=200) is restored EXACTLY by the reload
  (t=1900/1950, scene_epoch 1). Recorded in `prediction_deviations`.
- No other falsifier fired: no stale/replayed commands after reload, no
  second boot, no teardown deviation, no mapper event after exit, no
  non-playing record attribution, no pinned-source drift.

## Visual + camera evidence (per visual_gate, honest boundary stated)

`evidence/capture.mp4` (sha `593c3438b6e186a742d48c7b3495c9f5bec33a6e1dfb9ff2db226fd61111b23e`,
70,300 bytes, 640x360, 134 frames @ 20 fps, h264 bitexact) rendered from the
SAME trace by `capture_build.py`:

- `matched before/after camera bookmark` — fixed_bookmark camera at the
  engine's DEFAULT bookmark (radius 12, theta 0, phi 0.3, target origin; eye
  (0, 3.5462, -11.4640), distance 12.0), seconds [0.0, 3.35];
- `normal follow view during recovery` — sampled_trajectory,
  `recorded_each_tick`, the REAL pinned FollowCamera's applied solution per
  tick, seconds [3.35, 6.7];
- each view: diagnostic+clean pair, same trace binding
  (`state_binding.kind=trace`, sha = the trace above), camera fields complete
  (frame `monkey_session_world_yup_m`, right-handed metres, quaternion wxyz
  camera->frame, forward +Z / up +Y, near/far 0.1/200, 640x360, aspect 16:9,
  perspective 45 deg fov, 67 samples covering tick_interval [0,66] exactly);
- diagnostic rows carry exactly the three profile layers with stable tag
  bindings; clean rows are scene-only (depth-tested, no diagnostics — the
  boot-flash callout is drawn ONLY in diagnostic rows).

`evidence/capture_manifest.json`
(sha `791d1e6edc91be555e9a68b240ebb7c3885428acc685942e9cd5f99550d6e207`)
validates in-process through the campaign's own `visual_capture.
validate_manifest` AND `visual_gate.verify` against `card_task.json`
(structurally_valid: true, profile recovery, 4 views, video). The exact
receipt-as-submitted (`qualification_receipt.json`) also re-validates through
`visual_gate.verify` — verified before submission.

**HONEST BOUNDARY (unchanged from the frozen preregistration)**: the pixels
are a deterministic CPU visualization of the recorded headless session trace —
the flow is headless by construction. They are NOT native engine frames. The
integrated native playable-runtime/visual checkpoint **V08 remains with the
integration lane**; nothing here claims native rendering, only the
task-owned session subset the lead's correction scoped.

## Records leg (reused, preserved)

- Reconciliation publication `publication-3d8c97cffe20430394ef238a62e7cff5`,
  PR #135 head `441582bf16e0520e8f13235826f5ad94b6e603de` — untouched.
- Independent worker review `769540e4a2954868b37de6ce230a504c` — verdict PASS
  (preserved at kanban-reviews/ONT-X02/769540e4…/evidence/review_result.json,
  sha `8dfef590aa8e5041270819f97996beb997b64de6a1b5038f0936dfedd479a760`).
- Reconciliation receipt preserved copy sha
  `cf0475d80f4653e2063ed08ffbf699db2e361201500c3c6d604c2dfa4458f188` (cited
  as `evidence.source`).

## Qualification receipt

`qualification_receipt.json` carries the gate schema exactly
(`ontology_queue.qualification`): identity (scope/task/criteria),
`done_when_verified: true`, `profile_verified: true`, evidence
`source/numerical/independent_review/visual/camera/runtime` with raw sha256,
and `capture_context` (task, subject, run, capture sha, tick_interval).
`head_sha` is `null` IN THE TREE with an explicit binding note: the ACCEPTED
review must pass this receipt with `head_sha` set to the exact reviewed head
(an in-tree file cannot contain its own commit hash; same pattern as the
ONT-P01 winner record).

## Candidate suite and how to reproduce

```
python -B tools/monkey_campaign/contributions/ONT-X02/motion_profile_probe.py
python -B tools/monkey_campaign/contributions/ONT-X02/capture_build.py
python -B -m unittest test_motion_profile_probe -v     # 5/5 OK (0.016s)
```
CPU-only (stdlib + Pillow + ffmpeg for the frames), no GPU, no engine, no
browser, no network. Total new output < 0.5 MiB.

## Submission note (path supersession, for the lead)

This correction adds `PREREGISTRATION.md` and `report.md` under
contributions/ONT-X02/ with NEW content (motion correction), superseding the
reconciliation attempt's files at the same paths on PR #135 (head 441582bf).
The prior bytes are PRESERVED VERBATIM in git history (441582bf) and in the
review workspace; if both branches merge, the mechanical resolution is
"take the correction's file" — nothing of record is lost.

## Open questions (recorded, not invented)

1. The gate reads `q.head_sha` from the review action; the in-tree receipt
   ships `head_sha: null` + binding note. If the lead prefers a different
   convention (e.g. receipt copied into the review workspace with head filled
   before review), the evidence references are absolute and stable.
2. `artifact_locator.seconds` are declared per view over the ONE capture
   video ([0,3.35] bookmark, [3.35,6.7] follow). visual_capture does not
   check the mapping between ticks and seconds; the mapping is documented in
   `capture_receipt.json` (frame = half*67 + tick, 20 fps) for the lead's
   independent inspection.
