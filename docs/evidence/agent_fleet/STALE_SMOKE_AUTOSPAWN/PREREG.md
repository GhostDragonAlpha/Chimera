# PREREG — stale-smoke-autospawn-01 (gen 1)

- Agent: subagent-worker-09 (instance subagent-worker-09-a8960d274e14). Slot 12,
  worktree E:\ChimeraWork\slot-12, branch astra/tasks/stale-smoke-autospawn-01,
  base d8e3b5f54ce95e0f9690a73c381bc5ef20d76f8b (the deployed fix tip,
  claim-restore; HEAD==base verified, clean, live provisioner).
- Scope (exact, lead-assigned): tools/agent_fleet/five_slot_coordination.py +
  docs/evidence/agent_fleet/STALE_SMOKE_AUTOSPAWN. test_control.py is
  OUT of scope; the drift-catchable hook therefore lives inside the script
  itself (guarded import under a loader-visible name), not in the suite file.
- This commit contains the prereg ONLY. No fix, no evidence.

## THE MEMBRANE (RULE 0, before any edit)

- STATEMENT: the live smoke driver's capacity scenario asserted DEAD-PLANE
  behavior — tools/agent_fleet/five_slot_coordination.py s1_capacity
  (lines 163-180) expected the sixth claim against the real control service
  to refuse `no_free_slot`, which was true only before the fleet-slot-expansion
  fix (now deployed at d8e3b5f5): on the fixed controller the sixth claim
  AUTO-SPAWNS a fresh worker slot above the registry high-water under the
  SLOT_MAX=64 fuse (control.py claim block: no free slot of the kind and no
  free slot at all -> _spawn_slot, guard slot_guard_reached; matching
  test_control.py::test_five_slots_then_auto_spawn_on_sixth, which asserts
  slot '6' and six bound slots). The script is not test-imported (the suite
  never executes it), so nothing caught the drift — the scenario now FAILS
  against the very controller it exists to smoke.
- PREDICTION (concrete, before the edit):
  P1 — after the fix, the full driver run (fresh isolated registry, real
       authenticated HTTP, never the operator's 8099 service) ends S1..S9 all
       PASS, and S1's recorded detail shows the sixth claim ACCEPTED with a
       new slot id > the pre-claim high-water (5), coord-sixth RUNNING owned
       by a2 at generation 1, the new slot bound to coord-sixth, and exactly
       six slots carrying tasks.
  P2 — the drift-catchable hook (`test_scenario_pins_are_current()`,
       loader-visible, module imports with zero side effects) PASSES on the
       fixed source and FAILS on a stale-pin fixture (the same source with the
       superseded `no_free_slot` expectation reintroduced) — proving the hook
       has teeth. The script's main() runs the hook FIRST and refuses to run
       scenarios on stale pins, so the smoke itself is drift-catching.
  P3 — the full fleet suite (`python -m unittest discover -s
       tools/agent_fleet -p 'test_*.py'`) stays at zero failures/errors: the
       edit touches only the scenario expectation, never controller semantics.
- FALSIFIER (named BEFORE the run, from the packet): any weakening of the
  five-slot coordination scenarios otherwise — concretely: S2-S9 regressing or
  being altered; the fleet suite going red; the pin hook passing on a
  stale-pin source; the s1 scenario edited to anything other than the
  auto-spawn expectation (e.g. deleting the capacity scenario to dodge the
  drift); evidence not retained verbatim.

## THRESHOLDS (fixed now)

- R1: 9/9 scenarios PASS in one retained driver run; S1 detail names the
  auto-spawn facts above (slot id > 5, RUNNING/a2/gen 1, slot bound, 6 slots).
- R2: 2/2 — hook PASSES on the fixed script; hook FAILS on the stale-pin
  fixture copy; both runs retained verbatim.
- R3: fleet suite reports 0 failures, 0 errors (retained verbatim).
Any miss = falsifier FIRED for that row; the miss is reported, not patched
around; committed check files are the single retained run (re-runs disclosed
in RESULT.md).

## METHOD

1. Prereg (this commit).
2. Edit s1_capacity to expect auto-spawn (matching the named test's
   semantics); add EXPECTED_SIXTH_AUTO_SPAWN + test_scenario_pins_are_current()
   + main()-first pin check. Nothing else in the script changes.
3. Run: driver (isolated registry, --out inside the evidence scope), pin-hook
   positive, pin-hook negative control (stale fixture in a temp copy), fleet
   suite. Retain RAW_SMOKE_RUN.txt, RAW_PIN_HOOK.txt, RAW_SUITE.txt under
   docs/evidence/agent_fleet/STALE_SMOKE_AUTOSPAWN/.
4. RESULT.md (scorecard, falsifier status, reproduction), trailer
   `Agent: subagent-worker-09`, push no-force, PR into astra/gait-capture,
   submit_review exact HEAD.
