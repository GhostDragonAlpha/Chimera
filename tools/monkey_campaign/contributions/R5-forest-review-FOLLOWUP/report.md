# R5-forest-review-FOLLOWUP — scene-readiness smoke-test runner

**Verdict: implemented and verified (7/7 CPU tests). The runner mechanizes the
accepted R5 readiness gate: against today's engine it can only report
NOT_READY — with the missing native collision capability and the open walking
prerequisites NAMED — and a fixture READY is structurally labeled non-native.**

- Card `R5-forest-review-FOLLOWUP` (planning F01-F08/W10; parent R5 =
  PR #126 @ `7467bed2`, PASS-reviewed at the exact head by this agent).
- Attempt `cdad032e39ad4f31a6f11b95ada1791b`, agent
  `c95e1722350849bca846b237c1f60997`, criteria
  `6e10706bf24877a657ea8b4a43c9894b24fdd46b97d0d120b0573f8af0aadbcc`.
- Preregistration written before the implementation (Rule 0).

## What was implemented

`implementation.py` — `ReadinessRunner(config, transport)`, transport INJECTED
(urllib live class provided, unexercised here; CPU tests use fakes; no engine
started by this card):

- probes ONLY the documented endpoints (slice_server.py cites:
  `/api/health`, `/api/status`, `/tick_state`, `/tick_touch`,
  `/tick_gravity`); probing anything outside the configured documented set
  raises `endpoint_not_documented` (invention refused); a future collision
  route must be EXPLICITLY declared (`extra_documented_endpoints`) before it
  can be probed;
- every request bounded by the configured timeout;
- pinned scene identities carried in every verdict (R5 identity receipt:
  clearing/terrain/trunk/routes self-pins, seed 4598321, extent 20.0, trunk
  site (11.976783, 2.471766));
- NAMED findings: `engine_unavailable`, `health_unhealthy`,
  `scene_identity_mismatch` (expected vs served), 
  `native_collision_route_missing` (the accepted negative finding, preserved
  as machinery when the collision route set is empty or unanswering),
  `walking_open` (W05–W09 + in-scene acceptance prerequisite);
- verdict `READY`/`NOT_READY` + `requests` log + `transport` label; every
  verdict states `native_acceptance: false` and the note that fixture READY
  still requires a controlled native run + visual capture.

## Measured (python -B -m unittest test_implementation -v → 7/7 OK)

1. unavailable engine → NOT_READY + `engine_unavailable`, bounded;
2. mismatched scene identity → `scene_identity_mismatch` naming both values;
3. today's documented truth (collision_routes=[]) → NOT_READY +
   `native_collision_route_missing` + `walking_open`;
4. supported responses incl. a DECLARED collision route → READY, labeled
   `injected-fixture`, `native_acceptance: false`, explicit non-native note;
5. endpoint law: every probe within the configured documented set;
6. invented endpoint refused by name;
7. schema + pinned identities carried.

## Falsifier scorecard

- Fixture labeled native acceptance: NOT FIRED (label + note + flag asserted).
- Endpoint invented: NOT FIRED (refusal law + request-log test).
- Missing capability silently passed: NOT FIRED (named findings).
- Predecessor fact fabricated: NOT FIRED — endpoint set cites slice_server
  lines; negative collision finding cites the accepted PR #126/D-FOREST
  evidence; identity pins re-verified during this session's R5 review.
- Unscoped physics/threshold changes: NONE (test runner only).

## Preserved gates (not closed by this card)

An actual controlled native run + visual capture remain required for any
scene-readiness acceptance; the walking prerequisites (W05–W09, camera) stay
open per the accepted verdict. The runner is the reusable gate for when they
close: rerun with a live transport and the grown documented contract.
