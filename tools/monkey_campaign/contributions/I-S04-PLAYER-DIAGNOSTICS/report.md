# REPORT — I-S04-PLAYER-DIAGNOSTICS

- Card: **I-S04-PLAYER-DIAGNOSTICS** (planning id S04)
- Attempt: `d24bd30d38234a4cae33288048cce14f`
- Branch: `branch-9`
- Base (pinned source revision): `9afbddcd90164b5544a16fd0bc72278d985eb6e3`
  ("monkey-play: F08 integrated — repeatable forest loading ... FOREST FRONT F01-F08 COMPLETE")
- Objective: a tested player-facing diagnostic translation module for existing
  named product refusals.
- Rule 0: `PREREGISTRATION.md` was frozen BEFORE any implementation edit
  (statement / prediction / falsifier, all three present).

## 1. Existing-equivalent check (measured at the pinned revision)

`git grep` over `tools/monkey_campaign/product/*.py` at the pinned revision for
message/translation helpers found exactly ONE player-facing surface:
`state_feedback.py` (M-U06 — `STATE_KEYS`/`PROMPTS`, `render()`, `Feedback`,
`FORBIDDEN_CLAIM_TOKENS`). It renders STATE prompts from the four landed
modules; it has **no** refusal-translation surface. The refusal modules carry
only developer-shaped text: `input_settings.Refusal.detail` (e.g. "required key
'bindings' is missing", input_settings.py:211) and `session_flow.last_trace`
machine records (`_drop`, session_flow.py:264-267). **No equivalent translator
existed, so this module is new — but it builds on U06's honesty conventions**
(its tests reuse the pinned `FORBIDDEN_CLAIM_TOKENS` via ast extraction of the
pinned bytes) rather than duplicating U06's prompt ladder. Nothing was edited
in the source repo; extraction was `git show` only, ledgered in
`reference/EXTRACTION_LEDGER.json` (6 files, real sha256 of actual bytes).

## 2. Named-failure inventory (exact pinned-revision citations)

### 2a. input_settings.py — `Refusal(code, detail)` codes (20; 18 literal + 2 computed)

| code | pinned line(s) | trigger |
|---|---|---|
| `root_not_object` | 201-205 | document not a JSON object |
| `key_missing` | 210-211 | required key absent |
| `key_unknown` | 212-217 | unknown top-level key (seam constants refuse here) |
| `schema_type` | 222-226 | `schema` not a string |
| `schema_unknown` | 227-232 | schema id mismatch (no silent migration) |
| `bindings_type` | 254-259 | bindings not an object |
| `binding_name_invalid` | 263-267 | non-string/empty physical name |
| `binding_type` | 269-273 | binding value not a non-empty string |
| `action_unknown` | 275-280 | action outside `KNOWN_ACTIONS` (incl. sprint/jump) |
| `action_unbound` | 283-291 | coverage law: a selected control has no key |
| `sensitivity_type` | 295-325 (f-string at 299) | sensitivity.yaw not a number (bools refuse) |
| `invert_type` | 344-366 (f-string at 364) | invert.yaw not a boolean |
| `axis_unknown` | 303-308, 351-355 | unknown axis name |
| `axis_missing` | 309-314, 356-360 | `yaw` axis absent |
| `value_not_finite` | 328-332 | non-finite sensitivity |
| `value_out_of_range` | 333-338 | outside (0, 0.08] rad/count (derived ceiling) |
| `io_error` | 396-405 | path is a directory / unreadable |
| `json_corrupt` | 409-413, 429-433 | not valid UTF-8 / not valid JSON |
| `key_duplicate` | 417-422 | duplicate JSON key (refuse-whole law) |
| `not_finite_json` | 423-428 | NaN/Infinity literal |

Measured consequence at the pinned revision: EVERY refusal loads U01's default
settings (input_settings.py:145-151, 248-249, 384-389) — so every settings
message says "Default controls are active" and never more. `LoadResult.status`
is `"loaded" | "first_run" | "refused"` (:375); the first two are NOT failures
and are deliberately NOT translated (they fall to the honest unknown fallback
if routed here).

### 2b. session_flow.py — named drops + failed transitions (7)

| identity | pinned line(s) | trigger |
|---|---|---|
| `key_press` | 279-282 | unbound key press while not playing |
| `key_release` | 284-288 | key release while not playing |
| `mouse` | 290-296 | mouse counts while not playing |
| `decision_tick` | 298-307 | decision boundary while not playing (emits nothing) |
| `flow_action` | 313-317 | `"action@state"` named no-op (explicit-user-action-only law) |
| `restart_failed` | 335-342 | boot raised → transition NOWHERE, old scene stays |
| `exit_failed` | 343-353 | teardown raised → no transition, still running |

Drops happen ONLY while not playing (session_flow.py:279-306); the four-state
frozen table (`DEFAULT_FLOW_BINDINGS` :94-101, `TRANSITIONS` :102-110, terminal
`exited` :111-117) is the complete action vocabulary. `FlowError` (:120) is a
construction-time developer error → honest unknown fallback, out of player
scope.

### 2c. state_feedback.py (U06 vocabulary, inherited not duplicated)

`STATE_KEYS`/`PROMPTS` (11 states), the render ladder, and
`FORBIDDEN_CLAIM_TOKENS` (falling/recovery/support/... are NEVER claimed —
falling and recovery are deliberately absent from the product). The card's
five prompt states map honestly: available climb → `climb_ready`;
unavailable support → `input_disconnected`/`input_blurred` ("keys dropped");
holding → `climb_key_held` (an INPUT fact); falling → unrendered; recovery →
unrendered. This module claims none of the forbidden tokens (test-enforced).

## 3. What was built

`player_diagnostics.py` — stdlib-only, deterministic, headless, Python 3.11+:

- `explain_settings_refusal(code, detail, nonce)` — 20 codes → player records.
- `explain_flow_drop(kind, detail, state, nonce)` — 7 identities; parses the
  pinned `"action@state"` format; refuses identities the pinned source cannot
  produce (a drop while playing, a state outside `STATES`) to the unknown
  fallback instead of fabricating.
- `explain_exception(exc, nonce)` — Refusal-shaped objects (.code) translate;
  everything else → fallback.
- `explain(name, detail, state, nonce)` — name dispatch; anything unknown
  (typos, `"loaded"`, trace keys like `"quiesced"`) → fallback, never success.
- `PlayerDiagnostic` — frozen record: `name`, `status`
  (`refused|dropped|failed|unknown`), `ok` (**always False** — a diagnostic is
  never a success), player `message`, player `actions` (grounded imperative
  sentences only), `correlation_id`, and a SEPARATE developer `diagnostic`
  field (raw detail verbatim, origin citation, grounding pairs).
- `scrub()` — drive-letter/UNC/backslash/POSIX-home/file-URI paths and
  `%ENV%`/`${ENV}`/`$ENV` references → `[removed]`; applied to all player text
  and to offense tokens as a final pass.
- `correlation_id()` — sha256(name+detail+caller nonce), 16 hex chars; no wall
  clock, no randomness.
- 39 supported identities total (`supported_identities()`).

`test_player_diagnostics.py` — stdlib unittest, 22 tests, reads the pinned
source BYTES in `reference/` with `ast` so the inventory, the transitions and
the forbidden vocabulary are checked against the real source, not a
transcription.

**Test result (final): `Ran 22 tests in 0.032s — OK`** under
`timeout 120 python -B test_player_diagnostics.py` (0.34 s wall).

First-run failures, recorded honestly (the run was NOT green first):
1. Run 1 — FAILED (4 failures, 25 errors). Real module bugs: (a)
   `value_out_of_range` message said "supported range", which contains U06's
   forbidden token substring "support" → reworded to "allowed range"; (b)
   `actions` carried raw `(state, action)` tuples instead of player-readable
   sentences → rewritten as grounded imperatives ("Press Return to start.")
   with the grounding pairs moved into the developer field. Test bugs: pinned
   `TRANSITIONS` keys are name tuples so `ast.literal_eval` fails → replaced
   with name-aware evaluation; scrub assertion double-prefixed "ENOENT";
   repr-escaped backslashes broke a raw-detail assertion.
2. Run 2 — FAILED (1 failure, 19 errors): state/action argument order swapped
   in `_action_sentence` (`KeyError: 'attract'`), plus a key-order assertion
   that ignored `sort_keys`.
3. Run 3 — **22/22 OK in 0.032 s.**

## 4. Connection proposal (TEXT ONLY — no product code was edited)

The module is a pure library; connecting it is a product decision. The
existing surfaces, at the pinned revision:

1. **Settings load (input_settings.load_settings, input_settings.py:384-437).**
   Wherever the UI surfaces a `LoadResult`, translate each refusal:
   `pd.explain_settings_refusal(r.code, r.detail)` → show `message`, list
   `actions`; keep `r.detail` out of player text (it is already preserved in
   the record's diagnostic field). Statuses `"loaded"`/`"first_run"` stay with
   state_feedback's prompts — they are not diagnostics.
2. **Named drops (SessionFlow.last_trace, session_flow.py:264-267).** A UI
   poller reading `flow.last_trace["dropped"]` translates the newest entry:
   `pd.explain_flow_drop(entry["kind"], entry["detail"], state=flow.state)`.
   The `state` argument comes free — `_drop` already records it.
3. **Failed transitions (session_flow.py:335-342, 343-353).** The trace keys
   `restart_failed`/`exit_failed` carry `repr(exc)`; translate with
   `pd.explain_flow_drop("restart_failed", repr_text)` — the repr (paths,
   exception details) stays in the diagnostic field only.
4. **Sibling, not merge, with state_feedback.render.** U06 renders the STATE
   line; this module renders FAILURE events. A surface can show one state line
   (state_feedback) plus the latest failure line (this module). The shared
   honesty vocabulary (`FORBIDDEN_CLAIM_TOKENS`) is reused by the tests via
   the pinned bytes, so a divergence in U06's token list will fail this
   module's tests and force a conscious re-read.

## 5. Falsifier self-check (card's authority, verbatim)

- **F1 — the player receives raw local paths: NOT OBSERVED.** Path-bearing
  sweep (`ENOENT E:\repo\secret\forest.bin` and friends) across all 39
  identities: banned-shape regex (`[A-Za-z]:\\`, `\\\\`, `%ENV%`, `${ENV}`)
  finds 0 matches in any player message or action; the card's exact example
  keeps `E:`/`repo`/`secret`/`forest.bin` out of player text while the
  diagnostic field retains the original (`PlayerTextNeverContainsPathsOrSecrets`).
- **F2 — a message claims an unsupported action: NOT OBSERVED.** Every
  grounding pair is a row of the pinned `TRANSITIONS` (ast-extracted); every
  key token in messages+actions equals the pinned `DEFAULT_FLOW_BINDINGS` keys
  for exactly the offered actions; settings messages offer no session key and
  no settings menu; `key_press@playing` (impossible at the pinned revision)
  returns the unknown fallback, not a fabricated message
  (`ActionsAreSupportedByPinnedStates`).
- **F3 — unknown errors silently report success: NOT OBSERVED.** 8 unknown
  identities (typos, `"loaded"`, `"first_run"`, trace keys `"quiesced"`,
  `"transitions"`, `"restart_path"`, `"dropped"`, empty name, case mismatch)
  plus an arbitrary `ValueError` all return `status="unknown"`, `ok=False`,
  `actions=()`, with a deterministic correlation ID in the player text
  (`UnknownIsHonest`).
- Determinism: full 39-identity sweep byte-identical across runs; nonce
  perturbs correlation IDs deterministically (`Determinism`).

## 6. Remaining gates (open, none closed by this card)

- **Human readability / playthrough acceptance: PENDING** — the messages are
  minimal player language by construction, but acceptance is the operator's
  call, not mine. Label: awaiting human reference.
- **Parent gates stay open** — this card is preparatory only: no engine port
  was tested (S-1 `port_test()` does not apply to a standalone stdlib module),
  no training, no calibration. Connecting the module (§4) is the next card's
  work and would go through its own preregistration.

## 7. Constraints honored

Stdlib only · no network · no package installs · no GUI · no native builds ·
no GPU · no training · no process control · no fuzzing beyond the fixed
sweeps · every test invocation under `timeout 120` (actual 0.03-0.34 s) ·
total new output ~55 KB (far under 16 MiB) · source repo touched only via
read-only `git show` · no push, no new branches beyond the given `branch-9`
checkout.
