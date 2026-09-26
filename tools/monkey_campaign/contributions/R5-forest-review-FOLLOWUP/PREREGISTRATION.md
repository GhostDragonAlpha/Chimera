# PREREGISTRATION — R5-forest-review-FOLLOWUP

Card `R5-forest-review-FOLLOWUP` (planning F01-F08/W10; parent R5-forest-review
= PR #126 @ `7467bed2` — reviewed PASS by this same agent earlier today at the
exact head). Attempt `cdad032e39ad4f31a6f11b95ada1791b`, agent
`c95e1722350849bca846b237c1f60997`, criteria
`6e10706bf24877a657ea8b4a43c9894b24fdd46b97d0d120b0573f8af0aadbcc`.
Written BEFORE the implementation.

## Predecessor facts (from the accepted R5 correction, none fabricated)

- The corrected R5 verdict (PR #126, verified this session): F01/F02/F03/F04/
  F07/F08 verified STATIC only; F05/F06 never started; W10 NOT ready — missing
  native heightfield/trunk contact, trained walking (W05–W09), in-scene
  walking/camera acceptance.
- Documented runtime endpoints (slice_server.py, play HEAD `f30f2224`):
  GET `/api/health` → `{ok, world_booted}` (`:460`), GET `/api/status` →
  `WORLD.status()` (`:458`), GET `/tick_state` (`:153,220,264`), POST
  `/tick_touch` (`:269`), POST `/tick_gravity` (`:324,327`). The D-FOREST
  parent brief's negative evidence (§2.4): the HTTP contract has NO collision
  query route.
- The F01–F03 identity pins (from R5's identity receipt, re-verified by this
  agent during the R5 review with the PR's own tools 13/13 + 30/30): terrain
  file sha `446ed3fb…`/self-pin `8c7d60c8…`, trunk `94ff906e…`/`b7089e78…`,
  clearing `18dd2ff6…`/`aa2607df…`, seed 4598321, extent 20.0.

## STATEMENT (a theory that can lose)

A configurable smoke-test runner over ONLY the documented endpoints, with an
injected transport, bounded timeouts and pinned expected identities, can
mechanize the R5 scene-readiness gate: it reports READY only when the live
runtime answers every documented check AND the native collision capability
exists; against today's engine it must report NOT_READY with the collision
route NAMED missing — the runner can never turn the static front into native
readiness, and a fixture transport can never be labeled native acceptance.

## PREDICTION (not yet measured)

With a FakeTransport in CPU tests:

1. Engine unavailable (transport raises / times out) → verdict NOT_READY,
   finding `engine_unavailable`, bounded runtime (< timeout).
2. Health/status answered but a configured expected field mismatches (e.g.
   scene/world identity) → finding `scene_identity_mismatch` naming expected
   vs served values.
3. Supported responses with collision_routes=[] (today's documented truth) →
   verdict NOT_READY with finding `native_collision_route_missing` (the
   accepted negative finding, preserved as machinery) and `walking_open`
   (W05–W09 prerequisite, from the accepted verdict).
4. A hypothetical transport serving a documented collision route + all checks
   → verdict READY, with output labeled `transport: injected-fixture` and an
   explicit note that fixture READY is NOT native acceptance (controlled
   native run + visual capture still required).
5. No endpoint outside the documented set is ever probed (the request log of
   every scenario contains only configured documented paths).

## FALSIFIER

Any fixture output labeled native acceptance; any endpoint invented; any
missing capability silently passed; any predecessor fact above not traceable
to the accepted PR #126 evidence or the cited source lines; unscoped
physics/threshold edits (there are none — this is a test runner). Fails the
card if any prediction 1–5 does not hold.

## BOUNDS

CPU-only, stdlib-only; injected transport in tests (urllib transport provided
but not exercised against a live engine — no engine is started by this card);
bounded timeouts; own attempt workspace; ≤16 MiB output.

## AMENDMENT (2026-09-26, correction attempt `165ca25f52df48fd9de4cb24d42c68d6`,
arrival `arrival-773e9bcac941425c9a55d02b447db9a1`)

The operational lead's pre-publication verification (lead-verify-20260926)
found two transcription corruptions in the predecessor identity pins above;
the corrupted forms exist in no accepted record. Corrected to the accepted
receipt values at pinned play revision `dc7ea811`:

- trunk self-pin `b7099e78…` → `b7089e78…` (R5 identity receipt
  `A1_recompile_trunk`; F03 validate_receipt `declaration_sha256
  b7089e7826a221a5…`);
- routes self-pin `c3a7d6e8…` → `7c3ad6e8…` (R5 identity receipt
  `A1_recompile_routes`; F07 run.json).

Both are pass-through fixture values in the runner config (never validated
against served data), so no behavioral change and all original predictions
above are preserved unchanged.
