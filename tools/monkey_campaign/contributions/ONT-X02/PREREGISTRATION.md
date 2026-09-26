# PREREGISTRATION — ONT-X02 (ontology reconciliation)

Card `ONT-X02` (planning X02, profile: recovery; depends on P01's frozen
contract). Attempt `e07a08607c8b4994b3e2ce018ea4458e`, agent
`c95e1722350849bca846b237c1f60997`, criteria
`a266d16164e64af20505d4ed5d76a532ebb74f3bd0975cfd548546eaa92c71bf`.
Written BEFORE the reconciliation probe ran.

## Existing work being reconciled (identities measured)

X02 was already implemented in the M-X02 lane
(`E:/ChimeraWork/monkey-play-20260924`, HEAD `f30f2224663324e9374b076938c56672febf4082`):

- `tools/monkey_campaign/product/session_flow.py`
  (sha256 `30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf`)
  — four-state machine ATTRACT→PLAYING⇄PAUSED→EXITED, pure key-event filter
  over U01's mapper, world contact only through injected restart/teardown.
- `tools/monkey_campaign/product/session_flow_tests.py`
  (sha256 `b6ce2bba598fcb8119de82f9a06639ee6d2744c1605ac82c8d699b8df75ef49a`)
  — falsifiers F1–F5; rerun by this attempt at the pinned HEAD: exit 0,
  ALL CHECKS PASS (receipt refreshed at agents/X02_flow/receipts/, the
  suite's own designed output location).

This attempt reconciles that implementation against the ontology card; it does
not reimplement or modify it.

## PREDICTION (not yet measured by this attempt)

An independent probe driving `SessionFlow` directly (own minimal doubles —
not the suite's) confirms the card's done_when and the recovery profile:

1. **reaches play**: ATTRACT + confirm key → PLAYING (no method call exists
   that skips the key path; the module's only public mutators are
   key/mouse/tick).
2. **pause/exit without developer commands**: Escape from PLAYING → PAUSED
   with the mapper quiesced (release_all called; zero mapper events while
   paused); Q from any non-exited state → EXITED with teardown exactly once,
   recorded terminate→wait→kill.
3. **reset is an explicit user action**: R only from PAUSED → PLAYING with
   world contact exactly [release_all, boot×1]; R elsewhere is a no-op; a
   zero-event clock advance never changes state (no timer transitions).
4. **resume tail law**: resuming a mid-press pause emits at most 2 records,
   each ≤ pre-pause speed, ending exactly 0.0, then silence.
5. The existing suite passes at the pinned HEAD (F1–F5).

## FALSIFIER

Any probe outcome deviating from 1–5 fails the reconciliation and reopens the
card as missing work (reported, not smoothed). Claiming native/visual
qualification the evidence does not carry (no browser/engine session is run
here — the flow is headless by construction; the integrated playable-runtime
checkpoint V08 remains with the integration lane), editing the existing
implementation, or misstating its identity, also fails.

## BOUNDS

CPU-only, stdlib + the pinned play-worktree module imported read-only;
temporary probe state; the existing suite's receipt output is its own
designed location; no GPU, no engine launch, ≤16 MiB new output.
