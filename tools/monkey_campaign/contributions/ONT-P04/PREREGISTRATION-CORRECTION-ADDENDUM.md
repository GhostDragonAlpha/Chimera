# PREREGISTRATION ADDENDUM - ONT-P04 correction: evidence fencing + restore-config law (records profile)

Attempt: 06792d79c3704ac29df519055aabbc57
Arrival: arrival-c03016e9e0c74d67b03761e5d74ac7e1
Corrects: PR #158 head 68290bec4ab84238e00e9190748402177fd55937
          (publication-a6c5aa2fbd4446dfa94852038d3fea1b)
Lead ruling: CHANGES_REQUIRED msg-5feabcb2d57f49e9a70d8e366b62095e
          (astra-codex, OPERATIONAL_LEAD), evidence
          E:/Chimera/queue-check-20260926/current/REVIEW.md + reprobe.py
Base prereg: PREREGISTRATION.md of attempt 4f4df57ef3d54c0996cf969e8a599d1b
          (sha256 124c3acfc6ae572bdfab7021c30a0802ddd6f5551b4f9c12a18e8ad72e85ecbc),
          carried forward unchanged; this addendum freezes the SECOND
          correction delta. The pinned controller stays untouched
          (tools/agent_fleet/control.py at c525b82c, sha256
          39ff01dc8a4192e04606ee9d87386780739e89c8a1774da48501a9545792f6b3);
          the pinned controller's additive-subclass property is preserved and
          `HandoffControl` remains a pure subclass with no rival authority.
Profile: records (offline), CPU-only, temporary registries only, `python -B`;
          no GPU, no live registry, no process launches beyond python -B
          tests; E:/PythonChimera and E:/Chimera receive zero writes; review
          evidence read read-only. Frozen BEFORE any post-fix probe run.

## Frozen finding (reproduced before the fix)

Reproduction (attempt reprobe/pr158_falsifier.py, reviewer Rig, source hash
pinned to 100154452bcc5db16b916743507091dc00160aa34fcdb3a1bf75c59bfa3e7030 =
the PR #158 head gpu_handoff.py, temporary registry): with the training
request live in DRAINING, the enrolled `gamer` identity - which owns the game
task and is NOT the request owner (gamer_is_request_owner == false) -
successfully called `handoff_checkpoint_preserved` (recorded
checkpoint_preserved = "foreign assertion") and `handoff_model_unload` with
restoration_config {artifact: DIFFERENT, context: 1} (recorded as the unload
config). Both mutations of the training drain evidence are accepted by the
unfixed handlers because they check phase but omit actor authorization; the
unload path also compares the config only for shape, never against the
registered identity. Before-run output preserved at
reprobe/before_run.json (+ before_run_stdout.txt). The lead's own reprobe.py
was also executed verbatim: its #158 half runs silently; its #160 half
crashes on a harness bug in the lead's quick script
(`p.stat().st_size()` is an int, not callable) before printing - unrelated to
the #158 finding; the faithful #158 reproduction is the preserved runner.

## Frozen statement (the fix)

1. EVIDENCE FENCING. Every state/evidence mutation of a live handoff request
   is fenced by a new `_fence_mutation` guard applied to
   `handoff_gate_close`, `handoff_gate_open`, `handoff_checkpoint_preserved`,
   `handoff_model_unload`, `handoff_game_release`: after request resolution
   and the corruption gate, and BEFORE any other check, the guard requires
   EITHER explicit supervisor authority (actor == SUPERVISOR) OR the live
   request owner whose own task claim is live at the validated generation:
   `require(actor == req['owner'], 'handoff_mutation_not_authorized')` then
   `Control._task(s, actor, req['task'],
   p.get('generation', req['generation']))`. Consequences, by frozen refusal
   name:
   - a foreign enrolled identity is refused `handoff_mutation_not_authorized`
     (new frozen name) and writes nothing;
   - a generation pin that is not the live claim generation, and a request
     whose recorded generation is no longer live, are refused
     `stale_or_foreign_claim` (the pinned controller's claim law);
   - the legal owner flow at the live generation is unchanged;
   - supervisor authority stays legal (supervisor recovery/delegation).
   Phase checks and evidence validation keep their existing frozen names and
   order after the fence.

2. RESTORE-CONFIG REGISTRATION. `handoff_model_unload` additionally requires
   the presented restoration_config to EQUAL the registered configuration of
   the named instance:
   `require(cfg == plane['instances'][iid], 'restoration_config_mismatch')`
   (checked after the existing `restoration_config_required` shape guard and
   `unknown_instance`). The registered configuration is therefore retained
   EXACTLY in the drain record; a different/unregistered config is refused by
   name (`restoration_config_mismatch`, the same frozen name the restore path
   already enforces), so a tampered unload can no longer propagate into
   `handoff_restore`, which keeps comparing against the drain record.

### Frozen scoping decisions (honest boundary)

- `handoff_gate_check` is a STATUS probe: it writes no request evidence; its
  internal deadline flag only ever keeps the gate CLOSED. It stays unfenced
  (the independent reviewer's probes read gate status as a foreign actor).
- `handoff_infer_wait` appends only the CALLER'S OWN waiter record and
  mutates no request evidence; it stays unfenced.
- `handoff_request`, `handoff_admit`, `handoff_ready`, `handoff_launch`,
  `handoff_cessation`, `handoff_restore` already authorize through
  `Control._task` with an explicit generation (owner + live generation +
  active state); `handoff_hold` already refuses non-owners
  (`handoff_hold_not_authorized`); `handoff_recover` and both register ops
  are already supervisor-only. They are unchanged.

## Frozen regressions (failing-first)

New suite `test_correction_fencing.py`, 11 tests:
- F1 foreign-mutation refusal (4 refusal regressions + 1 legal supervisor
  path): `handoff_mutation_not_authorized` for gamer and lead on
  checkpoint/model_unload/game_release/gate_close, drain record proven
  untouched, including the lead's exact falsifier calls.
- F2 stale-generation refusal (2 regressions): owner-pinned stale generation
  (`stale_or_foreign_claim`), and a request made stale by a real claim
  advance (supervisor `claim_abandon` + re-claim, live generation 3 vs
  request generation 1), plus the honest re-request path at the live
  generation.
- F3 restore-config law (4 tests: 2 refusal regressions + 2 legal paths):
  `restoration_config_mismatch` on unload for a different artifact, mutated
  context, mutated offload; retained-exactly registered config through a full
  chain into restore.

Frozen prediction P1 (verified before the fix): exactly the 8 refusal
regressions FAIL on the unfixed head with "Refusal not raised"; the 3
legal-path guards pass. First-run output preserved at
first_run_failures/test_correction_fencing_first_run.log.

Frozen prediction P2 (verified after the fix): the lead's falsifier lines,
re-run against the FIXED source (new hash asserted at import), raise
`Refusal: handoff_mutation_not_authorized` for the foreign checkpoint and the
foreign wrong-config unload; the drain record stays empty.

Frozen prediction P3 (verified after the fix): test_correction_fencing runs
11/11 OK, and the full frozen battery (9 suites) runs 129/129 OK
(118 prior + 11 new), exit 0, carried-forward probes byte-identical.

No live GPU action is required or performed: the defect and its correction
are fully records-profile.
