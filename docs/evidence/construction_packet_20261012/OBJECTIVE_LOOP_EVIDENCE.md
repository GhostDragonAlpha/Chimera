# Objective-loop falsifiers — req.engine_game_release, engineering layer

Date: 2026-10-15. Battery: `tools/construction_packet/test_objective_loop.py`
(port 8796 + 8794/8795 for the agent-less pair; own engines). Result:
**4/4 green twice consecutively; full B0–B9 + objective regression
88 passed** (186.79 s). Engine: the rc.1 candidate line (pin `27314746`);
the battery is test-only — the candidate binary and its receipt are
unchanged.

## What the gate demands and what this falsifies

`req.engine_game_release` requires an objective with success/failure/
recovery and operation without an agent, plus operator/player confirmation.
The confirmation clause is human and stays a documented blocker; everything
mechanically checkable under it is falsified here, on the frozen route
surface, by a client with no engine-external knowledge:

| Gate element | Falsifier | Measured anchor |
|---|---|---|
| Objective is WINNABLE | `test_success_path`: plate + welded pillar + payload holds COM y ≥ 165 mm for 10 000 substeps; reaction == weight within 1.5 %; settled speed < 5e-3 m/s | settled payload COM 0.16868 m; reaction 11.4191 N vs weight 11.4188 N |
| Objective is LOSEABLE, loss detected named | `test_failure_path_named`: payload COM 30 mm past the pillar support edge topples; predicate records min COM | min COM 0.0373 m, lands 0.040 m |
| RECOVERY through the frozen verbs | `test_recovery_after_failure`: remove the wreck (parts back to `[plate]`), rebuild centered, the same scene then passes the predicate | recovered settle 0.17425 m, speed 3.9e-4 |
| OPERATION WITHOUT AN AGENT | `test_agentless_operation`: two fresh `--no-restore` instances driven by the same deterministic client, whitelist-asserted to the frozen route surface, reach physically-equivalent final states | agreement 9e-7 pose, 1.6e-5 quaternion, 8e-5 velocity at EQUIV_TOL 1e-3 |

The objective itself (hold the payload clear of the ground for 2.5 s of
physical time with ≤ 3 parts and 1 weld) is declared operator-side; the
encounter packets remain proposals per the plan.

## Calibration honesty (the bands are measured, not authored)

The penalty rungs hold a ~10 mm rest sink at EVERY contact, ground and
part-part alike: the pillar sinks 10 mm into the plate (settled top 0.140,
not the authored 0.150), so the payload is placed pre-sunk (B3 stack
convention) and the thresholds sit relative to MEASURED settles — success
3.7 mm below the measured 0.16868, failure 80 mm above the topple landing.
Admitting all three touching in one transaction was tried and rejected: the
payload tunnels during the coupled transient (lands 0.040), the exact failure
mode `b2_scene_gen.stack_rest_offsets` documents.

## The limit-cycle finding (recorded, not papered over)

The agent-less equivalence test exposed a real engine property: the
payload/pillar pair contact keeps a **persistent limit cycle** — payload
|omega| ~1.2e-2 rad/s (~0.6 mm/s surface speed), constant to 7 digits from
40k to 60k steps. It is the engine's own documented rest jitter (b2_scene.cpp
B8 comment "rest jitter ~0.5 mm/s"; release doc §6 "transient comparisons
are unqualified"), not a decay tail: plate+pillar alone settles to 5e-13, so
the floor is the payload interface specifically. Placement depth, yaw, and a
payload weld were probed and do not remove it (weld/yaw destabilize the
stack). Consequences recorded:

- Cross-instance physical equivalence is achievable at ~1e-5..1e-4 with the
  jitter-phase fields (`steps`, `omega_rad_s`) excluded — the same
  format-vs-physical law the rc.1 receipt established (the state hash is a
  serialization identity, not a physical comparator).
- Any future claim of exact transient comparison must first solve or bound
  this floor; it is now measured and named.

## Boundary of what this closes

This is the engineering falsifier layer under `req.engine_game_release`:
objective, success, failure, recovery, and agent-less operation are now
mechanically evidenced on the qualified runtime. It does NOT close the
operator/player-confirmation clause — that needs actual participants and
remains the release blocker in the release doc §6.
