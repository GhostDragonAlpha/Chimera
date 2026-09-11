# RESULT — stale-smoke-autospawn-01 (gen 1)

Agent: subagent-worker-09 (instance subagent-worker-09-a8960d274e14) · slot 12 ·
worktree E:\ChimeraWork\slot-12 · branch astra/tasks/stale-smoke-autospawn-01 ·
base d8e3b5f54ce95e0f9690a73c381bc5ef20d76f8b (the deployed fix tip
claim-restore; provision verified HEAD==base, clean). Scope honored exactly:
tools/agent_fleet/five_slot_coordination.py + this evidence directory;
test_control.py was never touched. Live-service hygiene: the driver brings up
its own FRESH isolated registry (temp root + free ephemeral port) running the
REAL control service over authenticated HTTP; the operator's live service at
127.0.0.1:8099 was NEVER contacted.

## THE DEFECT (packet PR #80 review LOW-1, now load-bearing)

s1_capacity (was lines 163-180) expected the sixth claim against the real
control service to refuse `no_free_slot` — the regressed PRE-fix behavior.
Post-fix (slot-expansion, deployed at d8e3b5f5) the sixth claim AUTO-SPAWNS a
fresh worker slot above the registry high-water under the SLOT_MAX=64 fuse
(control.py claim block: no free slot of the kind and no free slot at all ->
_spawn_slot; refusal names remaining: slot_guard_reached /
stale_provision_requires_recovery / integration_slot_busy). The script is not
test-imported (the unittest suite never executes it), so nothing caught the
drift: S1 now FAILed against the very controller it smokes.

## CHANGES (two, both inside scope)

1. s1_capacity rewritten to the auto-spawn expectation, semantics-matched to
   test_control.py::test_five_slots_then_auto_spawn_on_sixth: the sixth claim
   must SUCCEED, return a NEW slot id (not present pre-claim) above the
   pre-claim high-water, leave coord-sixth RUNNING owned by a2 at generation
   1, bind the new slot to coord-sixth, bump the revision, and leave exactly
   six slots carrying tasks.
2. Drift-catchable hook, in-file (test_control.py is out of this lane's write
   scope): `EXPECTED_SIXTH_AUTO_SPAWN = True` plus loader-visible
   `test_scenario_pins_are_current()` (guarded import — the module imports
   with zero side effects; unittest.FunctionTestCase binding included). It
   greps ONLY the s1_capacity source (via a scoped regex) for the stale
   refusal name — constructed by concatenation so the hook's own source never
   matches — requires the auto-spawn expectation and the semantics anchor in
   the source, and `main()` runs it FIRST, refusing (exit 3) to run scenarios
   on stale pins. The smoke itself is now drift-catching.

## PREDICTION SCOREBOARD (all thresholds fixed in PREREG 1ee78ccd, before the edit)

| row | prediction | verdict |
|-----|------------|---------|
| R1 | driver run: S1..S9 all PASS; S1 detail names auto-spawn above high-water | HOLDS 9/9 — S1 detail: "sixth claim auto-spawned slot 6 above high-water 5; coord-sixth RUNNING owned by a2 at generation 1; six slots bound" (RAW_SMOKE_RUN.txt, run-20260911T191323Z/COORDINATION.json) |
| R2 | pin hook PASSES on fixed source and FAILS on a stale-pin fixture | HOLDS 2/2 (RAW_PIN_HOOK.txt: positive accepts; negative control — the same source with the refusal re-injected into s1 — DETECTED the drift) |
| R3 | fleet suite stays green | HOLDS — `Ran 250 tests ... OK (skipped=1)`, zero failures/errors (RAW_SUITE.txt) |

FALSIFIER status: NOT TRIGGERED — no scenario other than s1 was altered
(diff is s1 + the hook + the main() pin gate only); the suite is green; the
hook demonstrably fails on stale pins; evidence retained verbatim.

## REPRODUCTION

```
git -C <checkout> rev-parse d8e3b5f5                 # base identity
cd <checkout>
python tools/agent_fleet/five_slot_coordination.py \
  --out docs/evidence/agent_fleet/STALE_SMOKE_AUTOSPAWN/run-repro
python -m unittest discover -s tools/agent_fleet -p 'test_*.py'
python -c "import sys; sys.path.insert(0,'tools/agent_fleet'); \
import five_slot_coordination as m; print(m.test_scenario_pins_are_current())"
```

## LIMITATIONS

- The hook is a source-pin check (the packet's option B): it proves the
  scenario EXPECTS auto-spawn; it does not execute the scenario. Execution
  coverage remains the driver run itself (retained) and
  test_control.py::test_five_slots_then_auto_spawn_on_sixth.
- The driver certifies scripted clients only — it does NOT claim the
  milestone "five independent agents verified" (label retained in
  COORDINATION.json).
- The negative control synthesizes the regression by text injection into a
  temp copy; it does not revert the deployed controller.
- Suite skip count (1) is pre-existing (unchanged by this lane).

## SHIP RECORD

- Commit chain: 1ee78ccd (PREREG, first, before any edit) -> artifact commit(s)
  -> pushed HEAD recorded in the controller submit_review event; PR into
  astra/gait-capture; pushed no-force.
- Files changed: tools/agent_fleet/five_slot_coordination.py +
  docs/evidence/agent_fleet/STALE_SMOKE_AUTOSPAWN/** only.
