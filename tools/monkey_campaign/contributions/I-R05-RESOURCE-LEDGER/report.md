# report.md — I-R05-RESOURCE-LEDGER

- **Card:** I-R05-RESOURCE-LEDGER (planning id R05)
- **Attempt:** 080ba14585ce405e9b7d0ae87632a8af
- **Branch:** branch-6 · **Pinned base:** `9afbddcd90164b5544a16fd0bc72278d985eb6e3`
- **Preregistration:** `PREREGISTRATION.md` (frozen BEFORE implementation, Rule 0)
- **This is preparatory work for R05** — parent R05 gates stay OPEN; nothing here closes them.

## What was built

`resource_ledger.py` — an ownership-scoped, generation-aware resource accounting
CHECKER for repeated session/restart teardown. Stdlib only, Python 3.11+,
headless, deterministic, bounded (`max_events`, default 10000, overflow is a loud
`ledger_full` refusal). It records `acquire`/`release` claims against a
**(SESSION GENERATION, OWNER, RESOURCE ID)** key and judges cycles; it never
touches the world.

- **Five named failure classes** (the card's vocabulary, recorded as evidence,
  never raised — a checker must keep observing):
  `ledger_duplicate_acquire`, `ledger_unknown_release`, `ledger_wrong_generation`,
  `ledger_wrong_owner`, `ledger_live_at_close`.
- **Fixed refusal precedence** for release claims: unknown-release →
  wrong-generation → wrong-owner. A refused release leaves the live record
  UNTOUCHED — a failed probe cannot half-close a resource.
- **Loud `LedgerRefusal`** (house `Refusal` shape, `code`/`detail`/identity) for
  programmer errors only: bad ids/generations/times, use-after-close, full
  ledger, bad ceilings, double generation-close.
- **Cycle summaries** with EXPLICIT CALLER-PROVIDED ceilings
  (`max_live`, `max_acquires`, `max_releases`, `max_failures`; unknown ceiling
  keys are REFUSED, never ignored — a typo must not silently disable a limit).
  Law: `passed` = no ceiling violation AND zero live_at_close in scope AND
  non-leak failures within the caller's failure budget (zero when no budget).
  **live_at_close is never launderable by any budget** — that is falsifier F3.
  **No memory probing exists anywhere** — there is no RAM input in the module at
  all, so "high free RAM" cannot be a success criterion by construction.
- **Generations:** reusing a resource id in a distinct generation is legal once
  the old record is no longer live; a still-live id re-acquired anywhere is a
  duplicate (two live things on one id is exactly what this ledger exists to
  catch). `close_generation(g)` names and ABANDONS g's leaks so later
  generations can reuse ids honestly; `close()` does this for every open
  generation and seals the ledger.
- All times are INJECTED integer milliseconds (`now_ms`) or None — never a wall
  clock (session_flow's injected-time law). Identical histories produce
  byte-identical canonical JSON (`to_json`/`canonical_json`).
- `python resource_ledger.py selftest` → `{"schema":"chimera.monkey_campaign.resource_ledger.v1","selftest":"pass"}`.

## API derivation from the pinned sources (read-only, `git show 9afbddcd:<path>`)

Existing teardown ownership APIs inspected (extracted bytes pinned in
`reference/EXTRACTION_LEDGER.json`; `reference/` is read-only after extraction):

1. `tools/monkey_campaign/product/session_flow.py` (`30e06c04d…`):
   `SessionFlow._transition` (:310-360) — `elif action == "restart":` (:327)
   calls `self._restart_scene()` (:336, declared referent `World.boot()`,
   slice_server.py:94-135) and `elif action == "exit":` (:343) calls
   `self._teardown()` (:349, declared referent `World.shutdown_engine()`,
   slice_server.py:174-181). One callable, fired exactly once (TRANSITIONS
   rows 5-7, :106-110; second exit is a named drop). **No per-resource
   ownership record exists** — the flow cannot see what its teardown should
   have closed, only that the one callable returned.
2. `tools/monkey_campaign/data/monkey_forest/forest_loader.py` (`53d7fdde…`):
   `ForestScene` is the closest existing ownership API — a NAME-keyed registry
   `self._resources` (:358-362), `attach_engine_shutdown` (:367-374),
   `live_resources()` (:376-378), and `teardown()` (:380-405) releasing in
   reverse-load order (:386) with `f08_teardown_leak` raised only when a
   release RAISES (:395). **It has no owner axis and no session generation**:
   one scene, one teardown scope; a resource nobody releases is invisible to
   `live_resources()` only until teardown nulls it; and across RESTARTS
   (new scene, new boot) there is nothing connecting generation N's leak to
   generation N+1.
3. `tools/playable_slice/slice_server.py` (`5accc730…`, reference only):
   `World.boot()` (:94-135) already shuts the old engine down first (:96) and
   counts boots (`self.boot_count += 1`, :128) — a natural generation counter
   to mirror; `World.shutdown_engine()` (:174-181) is terminate → wait(10 s) →
   kill.

**Existing-equivalent check (recorded per card):** `git grep -iE "resource_ledger|acquire|generation.*owner" 9afbddcd -- tools/monkey_campaign`
returns only unrelated prose hits (completion-map rows, G04 material-coefficient
"acquisition", HANDOFFS); `git grep -il "ledger"` over monkey_campaign `*.py`
returns NOTHING. No existing module does ownership-scoped acquire/release
accounting, so this card builds the smallest new checker instead of
duplicating — and deliberately reuses the house shapes: `Refusal(code, detail)`
(forest_loader.py:108-121), reverse-order release, the named-drop/failure-event
idiom (session_flow `_drop`), injected `now_ms`, and canonical JSON.

## Hook-up proposal (TEXT ONLY — no source edits were made)

Everything below names exact functions/lines in the pinned revision
`9afbddcd90164b5544a16fd0bc72278d985eb6e3`.

**A. `session_flow.py` — the flow owns the generation.**
`SessionFlow.__init__` (:233-258) gains one optional injected surface,
`ledger=None` (duck-typed to `ResourceLedger.acquire/release/close_generation`),
matching the module's law that the flow only gates, never builds the world.
- **Start** (`confirm` in ATTRACT, table row :104): after the state lands in
  PLAYING, the session owner calls `ledger.acquire(...)` for each resource the
  session acquired this generation, all tagged with the SAME generation
  integer. Generation source: mirror `World.boot_count` (slice_server.py:128) —
  the flow already records `restart_path` events in `last_trace` (:335), so the
  generation integer rides there.
- **Restart** (`elif action == "restart":` :327-340): after
  `self._restart_scene()` succeeds (:336) and BEFORE the state moves to PLAYING
  (:357), call `ledger.close_generation(old_gen, now_ms=now_ms)`. Its summary's
  `failure_details` (any `ledger_live_at_close`) go to
  `last_trace["restart_leaks"]` — a named receipt in the exact style of the
  existing `restart_failed` record (:338-340). Then bump the generation and
  re-acquire the new session's resources under the new generation.
- **Exit** (`elif action == "exit":` :343-350): BEFORE `self._teardown()`
  (:349) the flow releases everything it owns by name; AFTER it returns, call
  `ledger.close_generation(current_gen)` and record a nonzero
  `failures_by_code["ledger_live_at_close"]` in `last_trace["exit_leaks"]`.
  The terminal-state law is preserved: the close is idempotent-guarded, a
  second Q remains a named drop (:112-117, table :110).

**B. `forest_loader.py` — the scene publishes its names to the ledger.**
`ForestScene.__init__` (:349-365) takes an optional `ledger` + `generation`;
every entry it registers in `self._resources` (:358-362, plus
`attach_engine_shutdown` :367-374) is mirrored by
`ledger.acquire(f"forest:{name}", owner="session", generation=generation)`.
Inside `teardown()`'s reverse-load loop (:386-398), after each successful
`release()` (:390-392) the scene mirrors
`ledger.release(f"forest:{name}", "session", generation)`; on the
`f08_teardown_leak` path (:395) the ledger record simply stays live, so the
next `close_generation` names the scene's leak by resource id. The
zero-live audit (:404, `live_after`) and the ledger's `live_ids` must agree —
two independent counts of one truth, each able to catch the other's drift.

**C. `slice_server.py` — reference only, zero edits required.** `World.boot()`
(:94-135) and `shutdown_engine()` (:174-181) keep their exact bodies; the
ledger's generation mirrors `boot_count` (:128) and the engine-process slot is
just another `(generation, owner="session", "engine:<port>")` record acquired
at :99-103 and released at :174-181 — bookkeeping around the existing
machinery, never a replacement for it.

Net effect at the falsifier level: F1 — the operator's own ids
(`owner="operator"`) are unreachable by the session owner's release claims
(`ledger_wrong_owner`, resource stays live); F2 — a stale generation's claim
against a re-acquired id is refused (`ledger_wrong_generation`, current
resource untouched); F3 — a resource nobody released is named
`ledger_live_at_close` at the generation's close and FAILS that cycle's
summary, which `last_trace` now carries by name.

## Test evidence (fixtures, not runtime proof)

`python -B test_resource_ledger.py` (first invocation):
**Ran 35 tests, 1 failure + 1 error** — recorded honestly:
1. ERROR `test_leak_cannot_be_laundered_by_a_failure_budget` — real API gap:
   `close_generation`/`close` did not accept `ceilings`, though close IS the
   cycle end and must judge against caller ceilings. Fixed by adding the
   parameter (pass-through to `summary`).
2. FAIL `test_reused_resource_ids_across_generations_are_legal` — a bug in the
   TEST, not the module: the test acquired `engine:9347` in generation 1 and
   never released it before `close_generation(1)`; the ledger correctly named
   that leak (`ledger_live_at_close`) — falsifier F3's detection firing on my
   own fixture. Fixed the test to release before closing.

Second invocation: **Ran 35 tests — OK**, `runtime_seconds=0.002` (bound: 120 s).
Module selftest verb: `{"selftest":"pass"}`.

Coverage: repeated clean cycles (3 generations) · leaking cycles at
generation-close, whole-ledger scope, final close, and NOT launderable by a
failure budget · reused ids across generations legal · stale claim cannot close
a re-acquired current resource · old record releasable by its TRUE generation ·
operator-owned id NOT releasable by session owner (and still releasable by the
operator) · duplicate-acquire (same and different owner) · unknown-release
(never-acquired, after abandon, empty ledger) · wrong-generation refusal +
statelessness · wrong-owner refusal + precedence · double generation-close
refused · ceilings max_live/max_acquires/max_releases/max_failures incl.
generation-scoped summaries, unknown-key refusal, bad-value refusal · empty
ledger summary/close · use-after-close · event bound · bad ledger bound ·
determinism (identical histories → identical canonical bytes) · structural
no-probe check (no psutil/subprocess/terminate/time.time in the module source).

## Falsifier self-check (Rule 0, PREREGISTRATION.md)

- **F1 unrelated owner releasable?** NO — `OwnerTests` proves the session's
  release claim on `operator:notebook` is refused (`ledger_wrong_owner`), the
  record stays live and owned; GREEN.
- **F2 stale generation closes current resources?** NO —
  `test_stale_claim_cannot_close_a_reacquired_current_resource` proves a
  generation-0 claim against a live generation-1 record is refused and the
  current record survives; GREEN.
- **F3 a leaked resource passes a cycle?** NO — a `ledger_live_at_close`
  failure forces `passed=False` at generation scope, whole-ledger scope, and
  even under `max_failures=99`; GREEN.
- **F4 suite not green in bound / non-stdlib?** Green in 0.002 s of 120 s,
  stdlib only; GREEN. (Prediction 1 of the prereg also held: no existing
  equivalent found at the pinned revision.)

## Remaining gates (open, deliberately)

This card is PREPARATORY for parent R05: the checker exists and is proven on
fixtures, but it is NOT yet wired into `session_flow.py` / `forest_loader.py`
(section "Hook-up proposal" is a proposal, not an edit), no runtime session has
run against it, and the parent R05 gate (verifying owned-children closure of
the REAL teardown path) remains exactly where it was. Also open: operator-side
adoption (the `owner="operator"` axis is ledger-level only; no operator flow
emits those acquires yet).

## Constraints honored

Code only inside WS · no network, installs, GUI, native builds, GPU, training,
process control, unbounded fuzzing · test invocations bounded (timeout 120 s)
· source repo touched read-only (`git show`/`ls-tree`/`grep` only) ·
`reference/` frozen after extraction · total new output well under 16 MiB.

---

# CORRECTION — attempt 6487d23753e143ed941a4f4a60e55e33 (2026-09-25)

Responds to the lead's CHANGES REQUIRED on PR #122. Base adopted
byte-identical (resource_ledger.py sha256 `ef313c27…`; prior 35/35 green
pre-fix). Failing-first proof: both correction tests FAILED on base
(`failing_first_base.txt`) — the lead's exact sequence returned
`passed=true, live_now=1`, zero leak failures.

## Fixes

1. `acquire` refuses acquisitions into a CLOSED generation by name
   (`acquire_generation_closed`) — the impossible state cannot be created.
2. `close()` sweeps any still-live record in an already-closed generation
   (named `ledger_live_at_close` leak, abandoned) before sealing — the
   final close can NEVER pass with live resources (defense in depth,
   white-box regression-guarded for pre-fix ledger states).

## Verification

`python -B -m unittest test_resource_ledger test_correction` → **37/37 OK
(35 prior + 2 correction), run twice, deterministic**. The reproducer now:
late acquire REFUSES; final close with a closed-generation live record
FAILS (passed=false, live_now=0, named leak). No prior test broken.
