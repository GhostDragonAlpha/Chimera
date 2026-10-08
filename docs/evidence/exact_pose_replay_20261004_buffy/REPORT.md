# Proposal-only handoff to hand-remediation

**Disposition: PROPOSAL-ONLY. Do not create or run a competing replay attempt.**

The Captain's latest instruction confirms that the hand-remediation lane owns the
exact **314 q_c_PRIMARY + 40 q_zero_CONTROL** poses. A fresh read at
2026-10-04T02:22:32Z corroborated its package metadata:

- Owner: `wk-hand-remediation` (previous roster identity `agent_12f307d7`).
- Task: `HAND-REMEDIATION-20261003-R1-COLLISION-ADJ`.
- Base: `adc410451951b9057a9c749e7af84cdb9a063b3a`.
- Authority evidence: Captain's current message and the read-only existing
  `E:/ChimeraWork/monkey-coordination/hand-remediation/package/package.json`.

The initial absence of a separate assignment in older records did NOT prove that
this work was unclaimed. The earlier R1-STAGE4/unclaimed premise and request for
a separate admission are superseded. No owner files or claims were taken over.
The original mailbox request/old seals/failed logs remain historical evidence;
they must not be used to release this proposal. No one-hour completion is claimed:
the Captain interrupted and redirected the work to these bounded corrections.

## Corrected scientific scope

Stage 1 **already adjudicated the anchor VTP against the trunk** and recorded that
result; it **did not gate the survivor predicate**. The omitted check is the
**pad-substituted rigid bone**, not anchor adjudication. Proposed code retains
both raw records and separate bone/anchor-inclusive diagnostics. No geometry,
anatomy, measured parameter, threshold, exemption or playable goal was altered.
This is the exact stored Stage 1/2 pose set, NOT a separate R2 construction/sweep.

## Smallest pose-hash correction

The preregistration now matches the existing `join_rows()` implementation:

```text
pose_sha256 = SHA256(canonical({
  "key": pose_key,
  "stage1": complete_stage1_row,
  "stage2": joined_stage2_row
}))
```

`canonical()` uses sorted JSON keys, compact separators, UTF-8 and a trailing
newline. Posture NAME is part of the key. Rebuilt posture VALUES and inherited
file pins are not additionally included in `pose_sha256`. They remain separately
recorded/validated through `posture_q`, pinned inputs and `inputs_sha256`.
The runtime implementation/hash algorithm was not expanded or changed.

Two new fixture tests independently encode that exact payload, prove sensitivity
to each included component, and verify that posture/pin/identity providers are
not consulted by `join_rows()`. Existing posture and pin validation tests remain.

## Files changed in this correction

- [PREREGISTRATION.md](../../../tools/monkey_campaign/contributions/EXACT-POSE-REPLAY-20261004-BUFFY/PREREGISTRATION.md): proposal-only ownership, anchor scope and exact hash wording.
- [RUNBOOK.md](../../../tools/monkey_campaign/contributions/EXACT-POSE-REPLAY-20261004-BUFFY/RUNBOOK.md): owner-review reference, not a competing launch plan; corrected anchor/hash description.
- [test_replay.py](../../../tools/monkey_campaign/contributions/EXACT-POSE-REPLAY-20261004-BUFFY/test_replay.py): two focused hash-scope regressions.
- [replay.py](../../../tools/monkey_campaign/contributions/EXACT-POSE-REPLAY-20261004-BUFFY/replay.py): unchanged in this correction; proposed safeguards offered for review only.
- [INPUTS.json](../../../tools/monkey_campaign/contributions/EXACT-POSE-REPLAY-20261004-BUFFY/INPUTS.json): unchanged pinned input ledger.
- Updated editing-package copies of those proposal files; old seals remain untouched.
- Added this report, correction handoff request/receipt, fixture-only seal/run receipt,
  and hash-verified local copies of the new runner log/test artifact.

No commit, push, PR, controller claim, scientific execution or independent approval.

## Verification — actual fixture run, not collision evidence

Approved runner, synchronous, slot 2; timeout 120 s; 2 GiB scratch ceiling;
16 GiB aggregate committed-memory limit; 24 GiB reserve; <=4 threads/job;
`--keep outputs/replay`; runner-owned cleanup. No detached process.

- Prereg proposal ID: `EXACT-POSE-REPLAY-20261004-BUFFY-PRE-1` (unpublished).
- Current prereg SHA256: `9eddb18a5ff64ed1b67e150710d8a77451f86607d3bfac67d3b95be35cc97d62`.
- Unchanged implementation SHA256: `dd183e61c767b84fdcf9667957672d35528aa1834264e40b628416e6d57293c5`.
- Unchanged input-ledger SHA256: `50ee2f4757d062ff1e36ab7a0940165284decd947e82b95c5d4ea4fa85d47ecc`.
- Fixture-test seal SHA256: `e4f973195e9228529bdc689620a7224101e9fa7a8cc65e8ae324ab05de15befe`.
- Runner job: `8553c6c9116542ecb1e3c4bb19ed8037`.
- Result: **41 tests, 0 failures/errors/skips**, runner `PASSED`, exit 0,
  `cleanup_verified=true`. Syntax/AST checks included; no configured static
  typechecker exists for this stdlib contribution.
- Test artifact SHA256: `130b94115d8353dad8d72c20acd4e29966dc6882f149e2430d7acb72f35dd400`.
- Runner log SHA256: `c39f1c61bf8397eabc99b786e2b8855271b0f3a4cc5497820d81922adde64e75`.

Receipts: [fixture run](proposal_correction_test_run.json),
[fixture seal](proposal_correction_seal.json),
[test artifact](runs/8553c6c9116542ecb1e3c4bb19ed8037/artifacts/outputs/replay/tests.json),
[runner log](runs/8553c6c9116542ecb1e3c4bb19ed8037/runner.log).

No new metadata preflight, scientific serial control slice or actual collision
replay ran in this correction. The fixture-test seal is not a scientific
preregistration pin, competing campaign attempt, launch or release.

## Offer to the owning lane — review before adoption

Please review and reuse whichever safeguards suit the existing collision-adjudication
lane, without importing this proposal's task identity or creating another attempt:

1. Exact one-to-one Stage 1/2 key join; canonical pose/body order; stored o/u/s_star,
   no placement solver; signed-zero preservation.
2. Complete raw 20-body collision records, including the omitted rigid bone;
   already-adjudicated anchor record kept distinct from predicate interpretation.
3. Atomic per-body/pose checkpoints, nonzero refusal propagation including the
   inherited SystemExit-derived GateRefusal, bounded Windows sharing retry.
4. Detached payload copies so evidence cannot mutate its comparison oracle.
5. Duplicate/missing/foreign/tampered unit refusal; retained runner artifact,
   candidate and seal identity checks; no partial-as-full result promotion.
6. Serial-control-before-scaling and deterministic canonical combination; labeled
   20 mm inherited depth-bracket edge, not an unbounded exact-depth claim.
7. Explicit separation of fixture validation, runtime evidence and independent
   approval; no changed anatomy, tolerance, exemption or measurement to pass.

These are author-verified proposal features, NOT independently approved or
science-qualified functionality. The owner decides whether/how to adopt them
under its own preregistration, publication, runner and reviewer process.

The append-only correction/offer was submitted through the existing suggestion
box as `Q-d20c7f15b8934f949f17feb6bd9b12af` (question SHA256
`93f40e24b045f79278bfc67f42248fcc440ded3e031e5cbe17e5caf43fe862cd`).
See [offer](owner_review_offer.json) and
[submission receipt](owner_review_offer_submission.json). It explicitly withdraws
the earlier separate-admission request. This is queued for authority/owner review;
no delivery acknowledgement, adoption, approval or launch is claimed.

## Remaining work and next independent task

Completed here: proposal scope/ownership correction, narrowed hash wording,
regression tests, retained evidence and offer for owner review.

Pending with the EXISTING lane: any adoption, scientific preregistration/release,
serial control parity, exact full replay, interpretation ruling if needed,
independent review and physically supported player runtime. None is assigned to
this proposal; no admission/launch request for a competing Buffy lane remains.

Next independent action: the existing lane's non-author reviewer can assess this
hash-scope correction and safeguards without launching another collision replay.
Player-intent-to-physical-body integration remains a separate possible direction,
but its live ownership must be checked before any assignment; no unclaimed status
is asserted here.
