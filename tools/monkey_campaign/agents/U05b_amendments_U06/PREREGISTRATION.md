# PREREGISTRATION — M-U05b (R4's four binding amendments + U06 state feedback)

Frozen 2026-09-24, BEFORE any edit to any file outside this directory. Brief:
`brief.md` (verbatim copy in this dir). Review being landed: `agents/R4_intent_review/report.md`
(APPROVED-WITH-AMENDMENTS; AMR-1..4 BINDING inside v1, no version bump; SPEC-NOTES N1-N6
recorded for v2, NOT implemented). Baseline measured before this prereg was written:
`product/climb_intent_tests.py` GREEN 73/73, fuzz bit-identical to R4's receipt
(354 events == 354 accepted presses, let_go=185, named_drops=1089, seed 20260924).

## 0. THEORY (Rule 0)

- **STATEMENT:** R4's four measured gaps are real, reachable through the seam's declared
  surface, and fixable inside v1 with zero wire-format change and zero valid-path behavior
  change; AND an honest U06 prompt vocabulary exists that is derivable entirely from landed
  state (X02 session flow, U03 focus policy, U05 intent channel, U01 walk commands) without
  a single capability claim.
- **PREDICTION (unmeasured at freeze):** (a) exactly 4 new checks fail against today's
  `climb_intent.py` and pass after the minimal validator/reorder/docstring edits, with the
  73 original checks green in the same session (77/77 total); (b) every U06 vocabulary row
  is derivable from real module objects (no row without a source module), and a seeded
  adversarial fuzz over 20,000 state combinations finds ZERO forbidden capability-claim
  tokens in any rendered output.
- **FALSIFIERS (named before the run):**
  - **F-a (capability claim):** any rendered prompt/diagnostic implying climb, hold,
    support-contact, falling, or recovery capability that no landed module provides — the
    fuzz scans every rendered string for the frozen forbidden token list (§2.4); one hit
    kills U06.
  - **F-b (amendment not demonstrably fixed):** any of the 4 amendment checks green BEFORE
    its fix, or any of the 73 original checks regressing after the fixes.
  - **F-c (invented state):** any vocabulary row not derivable from the four declared
    sources, or any rendered state_key outside the frozen table, or a rendered prompt that
    is not the frozen line for its key.
- CPU-only, headless, injected clocks only. Numbers frozen at freeze and never tuned:
  fuzz combos = 20,000; seed = 20260924 (house seed); forbidden token list = §2.4 exactly.

## 1. PART 1 — the four amendment checks (from R4 §4's measurements, failing first)

The checks live in `product/climb_intent_amr_tests.py` (NEW file, disjoint name; the 73-check
suite `climb_intent_tests.py` is U05's file and is NOT edited — 77/77 = 73 re-run green +
4 amendment checks). Each check is R4's measurement, converted to the demanded behavior:

- **AMR-1 (validator refuses `intent_version=True`).** R4 A1.g/A1.g': `True == 1` is
  accepted today and JSON-encodes `"intent_version": true`. Check:
  `IntentEvent("climb_request", 0, 0, intent_version=True)` RAISES `IntentEventError`
  (and, in the same check, `"1"`, `1.0`, and `2` still raise; `1` still passes).
  Fix: the version check requires `isinstance(v, int) and not isinstance(v, bool)`.
- **AMR-2 (refuse forged `source`).** R4 A5.e: `source="not_the_channel"` constructs
  cleanly today; §3 says source is FIXED provenance. Check: a forged source RAISES
  `IntentEventError`; the default still constructs and stamps `SOURCE_ID`.
  Fix: `__post_init__` refuses `source != SOURCE_ID`. Wire format unchanged.
- **AMR-3 (validate-then-arm).** R4 A5.b-d: a press with a negative `now_ms` (or a raising
  `tick_source`) ARMS the edge first and raises second; the next valid press is then a
  named no-op — the physical press silently consumed. Check: after the raising press,
  `"Space" not in chan.held` AND zero events AND the next valid press DELIVERS.
  Fix: build/validate the `IntentEvent` BEFORE `self._held.add(name)` (R4's reorder).
  Behavior-identical on every valid path; suite must stay 73/73.
- **AMR-4 (press() docstring fix).** R4 A5.f: the docstring promises "returns ... if ONE
  event was emitted, else None", but the repeat (held) branch returns the bound action
  with NO event — the return value cannot distinguish delivery from no-op. Check: (i) the
  measured contract — fresh press returns the name AND delivers; repeat press returns the
  name AND delivers nothing; `repeat_press` names it in the trace; (ii) the docstring no
  longer contains the false claim. Fix: docstring states the two-case return honestly.

Failure-first evidence: the 4 checks run against the UNEDITED module first; the run is
captured at `receipts/amr_failing_first_20260924.txt` (expect 4/4 FAIL), then the fixes
land and the same file re-runs 4/4 PASS plus `climb_intent_tests.py` 73/73. R4's probe
battery (`agents/R4_intent_review/receipts/adversarial_probes_source.py`) is re-run
read-only after the fix; the four former FINDING probes (A1.g, A5.b, A5.c, A5.e — plus
A5.d, the same AMR-3 path) are expected to flip to the FIXED refusal; the other probes
must reproduce.

## 2. PART 2 — U06 display model (frozen before implementation)

Completion-map item U06 (verbatim): "Prompts distinguish available climb, unavailable
support, holding, falling and recovery without claiming nonexistent capabilities. Minimal
player language; engineering diagnostics stay optional."

**The pure display model:** `render(observation) -> Feedback` — a pure function from the
observed state of the four landed modules to ONE minimal prompt line + a structured state
record. `state_feedback.py` QUERIES NO ENGINE and reads NO WALL CLOCK: the observation is
data the harness assembled from public module attributes; the only mutables it touches are
its own frozen inputs.

### 2.1 THE STATE-SOURCE MAP (every displayed state cites its source module)

| state_key | source module (cited) | derivation from real inputs |
|---|---|---|
| `session_menu` | X02 `session_flow.py` (`ATTRACT`) | `session_flow.state == "attract"` |
| `session_paused` | X02 `session_flow.py` (`PAUSED`) | `session_flow.state == "paused"` |
| `session_exited` | X02 `session_flow.py` (`EXITED`) | `session_flow.state == "exited"` |
| `input_disconnected` | U03 `focus_policy.py` (`DISCONNECTED`) / U05 gates | focus disconnected OR `intent_channel.gates_active` contains `disconnected` |
| `input_blurred` | U03 `focus_policy.py` (`BLURRED`) / U05 gates | focus blurred OR intent gates contain `blurred` (checked after disconnect) |
| `intent_paused` | U05 `climb_intent.py` gates | intent gates contain `paused` (session claims playing — surfaced anyway: the channel WILL drop) |
| `climb_sent` | U05 `climb_intent.py` stream | the flash `IntentEvent` with `intent == "climb_request"` (delivered event only) |
| `let_go_sent` | U05 `climb_intent.py` stream | the flash `IntentEvent` with `intent == "let_go"` |
| `climb_key_held` | U05 `climb_intent.py` (`held`) | `len(intent_channel.held) > 0` (an INPUT fact: keys physically held, edge consumed) |
| `walking` | U01 `input_mapper.py` (+ its declared `is_expired` law) | walk keys held (`mapper.held`) OR a live (unexpired) walk `CommandRecord` exists — derived via `InputMapper.is_expired`, never a new staleness rule |
| `climb_ready` | U05 `climb_intent.py` (`state == "ready"`) under X02/U03 open gates | all gates open, nothing above fired — "available climb" = the channel would HEAR the key, with the no-skill disclaimer |

**NOT DERIVABLE AT v1 — NEVER RENDERED (falsifier F-a):**
- **falling** — no landed module provides a live airborne/contact fact. F04's L1 is an
  OFFLINE geometric verification of declared contact models, not a runtime state; there is
  no per-tick contact source to read.
- **recovery** — a recovery SKILL does not exist (W09 future). Gate-clearing is rendered
  only by the ladder naturally returning to `walking`/`climb_ready`; the word never appears.
- **unavailable support** — no support/contact knowledge exists (nothing beyond F04's L1,
  which is not a live source). Unavailability is rendered ONLY as input-gate facts
  ("keys dropped"), never as a claim about branches/trunk/contact.
- **climbing/holding as game states** — no climb skill exists (K-series future). `held`
  is rendered as the input fact it is ("Climb key held"), never as "climbing"/"holding on"
  (R1's fence; U05's integration note).

### 2.2 THE VOCABULARY TABLE (every line's honesty boundary; frozen strings)

| state_key | prompt (frozen) | honesty boundary |
|---|---|---|
| `session_menu` | `Menu — controls inactive` | X02 drops gameplay input off-`playing`; no capability implied |
| `session_paused` | `Paused — controls inactive` | same source, pause state |
| `session_exited` | `Exited — controls inactive` | terminal state; input off |
| `input_disconnected` | `No input device — keys dropped` | U03's named gate; states the DROP, not device repair |
| `input_blurred` | `Window lost focus — keys dropped` | U03's named gate |
| `intent_paused` | `Paused — controls inactive` | the channel's pause gate (U05); same player meaning |
| `climb_sent` | `Climb intent sent (no climb skill loaded)` | the BRIEF's example line: states the delivery FACT + disclaims the missing skill; never "climbing" |
| `let_go_sent` | `Let-go intent sent (nothing to release)` | delivery fact; nothing is held BY A SKILL (none exists) |
| `climb_key_held` | `Climb key held (ask already sent)` | the edge/input fact only; one consumed edge (no repeat) |
| `walking` | `Walking — movement input active` | walk seam IS landed (U01): states the live input stream, disclaims nothing new |
| `climb_ready` | `Climb key ready ({key}) — no climb skill loaded` | "available climb" honestly: the CHANNEL is ready; `{key}` interpolates the LIVE bindings table (data, §9 of the spec); the no-skill disclaimer is mandatory |

The word "recovery", "falling", "support", "unavailable", "climbing", "holding",
"attached", "grabbed", "hanging", "contact", "branch", "trunk", "snap" appear in NO prompt.

### 2.3 THE LADDER (deterministic priority; first match renders; every input validated)

0. validate inputs (refuse-what-you-cannot-name): unknown session/focus/gate/intent
   values, a flash event with `intent_version != 1` or a foreign intent name → raise
   `UnknownStateError` (a ValueError). The renderer NEVER guesses (it is an IntentEvent
   consumer: spec §7.1's check-the-version law is enforced here).
1. session not `playing` → the session row (X02 is the session truth; conservative).
2. disconnected (focus OR intent gates) → `input_disconnected`.
3. blurred (focus OR intent gates) → `input_blurred`.
4. paused in intent gates → `intent_paused`.
5. flash event present → `climb_sent` / `let_go_sent` (the delivery instant the harness
   surfaces; U05's note: light the flash FROM the delivered event; intents do not expire
   (R3) so no decay logic exists — a stale flash is warned about in diagnostics only).
6. `intent_held` non-empty → `climb_key_held`.
7. walk keys held OR live walk record → `walking`.
8. otherwise → `climb_ready` (gates open is exactly "available climb" at v1).

Cross-source consistency (focus vs intent channel, e.g. mis-wiring) goes to DIAGNOSTICS
ONLY, never the player line. Diagnostics default OFF (`render(obs)` → `diagnostics=""`);
`render(obs, diagnostics=True)` fills the optional engineering line (last named drop,
held sets, flash age, gate-set mismatch). Structured record: `Feedback` is a frozen
dataclass (`state_key`, `prompt`, `diagnostics`, `sources`, `observed`) — `sources` maps
every field to its module file; `record()` returns the JSON-able dict.

### 2.4 FROZEN FORBIDDEN CLAIM TOKENS (the fuzz scans prompt + diagnostics for ALL of these)

```
("climbing", "climbed", "grabbed", "grabbing", "grip", "hanging", "holding",
 "attached", "attaching", "falling", "fell", "recovered", "recovering",
 "recovery", "branch", "trunk", "contact", "support", "snap", "auto-snap",
 "climb available", "unavailable", "skill active", "skill engaged")
```

The vocabulary lines above were checked against this list at freeze (the disclaimer
"no climb skill loaded" deliberately does NOT contain any token — "skill loaded" is not
on the list because it only ever appears negated; the fuzz also asserts the disclaimer
string is present in `climb_sent` and `climb_ready`).

### 2.5 THE TESTS (product/state_feedback_tests.py, NEW disjoint file)

- **V1 DERIVABILITY (F-c):** drive REAL modules (SessionFlow, FocusPolicy +
  InputMapper, ClimbIntentChannel + MockIntentSink) through scenarios; build the
  observation from their PUBLIC attributes; every one of the 11 rows renders from real
  inputs; prompt == frozen vocabulary line; sources cite the right module.
- **V2 NO-CAPABILITY-CLAIM FUZZ (F-a):** 20,000 seeded combos (seed 20260924),
  adversarial: all gate subsets incl. INCONSISTENT cross-source combos (focus says
  focused, channel says disconnected), stale flashes, empty/full held sets, every session
  x focus x gate combination; scan prompt+diagnostics of every render for all forbidden
  tokens; also assert valid vocabulary keys and frozen prompt text; plus adversarial
  INVALID inputs (unknown enums, foreign version, foreign intent) must RAISE, never render.
- **V3 U05 INTEGRATION:** a real channel sequence (press -> delivered flash; gated
  presses -> named drops surface in diagnostics only; diagnostics OFF by default = "").
- **V4 X02/U03 GATING:** real SessionFlow pause/exit and real FocusPolicy blur/disconnect
  each take over the line; resume/focus returns the ladder to `walking`/`climb_ready`.
- **V5 HONESTY BOUNDARIES:** the map's five nouns map to the table per §2.1 (falling/
  recovery/support-unavailable have NO row and NO token ever appears); the disclaimer is
  present in `climb_sent`/`climb_ready`; `held` never renders as a game state.

## 3. WRITES (integrity, declared BEFORE the run)

1. `agents/U05b_amendments_U06/**` (this dir: prereg, brief, receipts, U07 note).
2. `product/climb_intent.py` — the four minimal amendment edits (the ONLY existing file
   edited; no version bump: wire format, event set, semantics unchanged on valid paths).
3. `product/state_feedback.py` — NEW (U06 display model).
4. `product/climb_intent_amr_tests.py` — NEW (the 4 amendment checks; disjoint name).
5. `product/state_feedback_tests.py` — NEW (U06 checks; disjoint name).
6. `agents/U05_climb_intent/INTENT_SEAM_SPEC.md` — APPEND ONLY (the R4-binding amendments
   + N1-N6 v2 notes; required by the brief's TASK 1 and ACCEPTANCE 2).

Nothing else. No engine code, no docs, no other agents' files. Pre-existing worktree
entries at session start (NOT mine, untouched): `M agents/U02_camera/receipts/latency_run.json`,
`?? agents/F07_obstacles/`, `?? agents/TIE2/`.

---

## APPENDIX A (post-freeze, append-only 2026-09-24 — a finding the frozen fuzz caught)

**A.1 — the consumer-side AMR-1 hole (found by the frozen V2.e check, fixed in
`state_feedback.py` BEFORE any green run):** the renderer's flash-event version
check originally compared `intent_version != INTENT_VERSION` only — so a stub
event carrying `intent_version=True` would have passed, exactly the `True == 1`
smuggle R4's AMR-1 closed on the PRODUCER side. The frozen check demanded the
bool refusal; the module moved to match the frozen test (type check first:
`isinstance(bool) -> refuse, not isinstance(int) -> refuse, != version ->
refuse`). No seam file was touched for this — the seam's producer-side AMR-1
fix was already landed; this is the same law applied on the consumer side.

**A.2 — measured fuzz numbers (frozen run, receipt
`receipts/state_feedback_tests_green_20260924.txt`):** 20,000 combos, seed
20260924; 30,099 rendered strings scanned; 722,376 token-level scans
(forbidden-token x string); **0 capability-claim hits**; ladder model-checked
20,000/20,000 (state_key AND prompt exact vs an independent model); all 11
vocabulary rows reachable from real module objects (no dead row, no invented
row); 10 adversarial invalid-input classes raise UnknownStateError, never render.

**A.3 — final suite verdicts (all re-run after the last edit):**
`climb_intent_tests.py` 73/73 GREEN (fuzz bit-identical to the U05/R4 receipt:
354 events, let_go=185, named_drops=1089) + `climb_intent_amr_tests.py` 4/4
GREEN (failing-first receipt on file) = **77/77**; `state_feedback_tests.py`
38/38 GREEN; neighbor baselines re-run GREEN untouched (input_mapper,
focus_policy, session_flow, stack_composition 73 checks 0 failed);
R4's probe battery post-fix: 27/27 expectations reproduce, 0 findings.
