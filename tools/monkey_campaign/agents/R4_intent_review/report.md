# R4 REPORT — interface review of the climb intent seam (U05)

Reviewer: R4 (interface authority, this pass). Date: 2026-09-24. Worktree
`E:/ChimeraWork/monkey-play-20260924`, reviewed commit `87c14ca5`. Preregistered
checks: `PREREGISTERED_CHECKS.md` (frozen before measurement). Receipts: `receipts/`.
Writes: this directory only (proof in §7).

## VERDICT: APPROVED-WITH-AMENDMENTS

The six interface rulings (§2) are all APPROVE — interface semantics v1 stand as the
reviewed decision the completion map demands. Four implementation-level amendments
(§4, AMR-1..AMR-4) are BINDING; none touches the wire format, the delivered event
set, or any of the six rulings, so they land inside v1 without a version bump
(AMR-1/2/3 are construction-time hardening and a pure statement reorder; AMR-4 is a
docstring correction). They must land with the 73-check suite green and the R4 probe
battery (`receipts/adversarial_probes_source.py`) re-run green. Six SPEC-NOTES (§5)
are recorded for v2; they are NOT defects and block nothing.

---

## 1. The frozen checklist, measured

| Check | Result | Evidence |
|---|---|---|
| C1 walk-contract hash proof | GREEN | §6; `receipts/walk_contract_hash_proof_20260924.txt` |
| C2 six rulings | 6 x APPROVE | §2 |
| C3 coherence spot-checks (6 done, 5 required) | 6/6 conformant; 2 validator/docstring gaps found by probe, not by clause-reading | §3 |
| C4 test suite re-run | GREEN 73/73, TWICE (independent processes); fuzz numbers bit-identical to the author receipt (354 events == 354 accepted presses, let_go=185, named_drops=1089, seed 20260924) | `receipts/climb_intent_tests_r4_rerun_20260924.txt` |
| C5 adversarial probes A1-A5 | 28/28 probes reproduced as expected; 5 found real (minor) gaps — all outside the author's falsifier set | §4; `receipts/adversarial_probes_20260924.txt` |
| C6 consumer fit | SERVES all four named consumers; nothing pre-empted | §5 |
| C7 integrity | writes ONLY `agents/R4_intent_review/` | §7 |

## 2. THE SIX RULINGS (binding interface record)

**R1 — The two-intent vocabulary (`climb_request`, `let_go`): APPROVE.**
The channel carries the player's explicit ASKS; K01's family (attach, ascend, hold,
descend, release) is skill vocabulary — decomposing a climb ask into skills is the
selector's job, not the wire's. U06's row (map:108) asks for STATES to render
(available/unavailable/holding/falling/recovery) — served by `state`/`gates_active`
plus the stream, with the integration note's prohibitions (never render `held` as
"climbing"; never infer availability from event absence) correctly fencing what the
channel does NOT know. Named now, pre-K01: **the most likely first v2 is a
directional climb intent** — the seam rightly does not invent it; K01's freeze is
where that decision belongs, and adding it is the declared version bump, not a break.

**R2 — Edge-triggered-only (no level/hold, auto-repeat a named no-op): APPROVE.**
The walk seam already owns the level/hold world (sustained demand, 20 Hz, expiry,
stall/re-issue); a level-mode climb would duplicate demand semantics and drag in
expiry/replay machinery sections 5.2/7.3 deliberately exclude. One surface, two
complementary models, zero authority overlap. The edge law is measured under full
gate churn (I1, I3.n: one physical hold = one consumed edge across 9 gate cycles x
3 gates; fuzz I8: 416 named repeat no-ops).

**R3 — No intent expiry at v1; the selector owns intent lifetime: APPROVE.**
The 100 ms walk-record expiry exists because a CommandRecord is a sustained DEMAND.
An edge FACT does not decay. Whoever owns expiry must know when a climb became
impossible — and that is engine state the pure-signal law (no engine reads, I5)
forbids the channel from having. Expiry in the channel would force exactly the
engine awareness the seam structurally lacks. §7.3 binds the K-series to own
lifetime; if K01 later needs channel-level expiry, it is a declared v2.

**R4 — No fabricated retraction on drop: APPROVE.**
I4 measures zero manufactured LET_GO under every gate, every order (a climb_request
delivered, then blur+disconnect+pause x2, five gated releases, recovery: stream
still holds exactly 1 event, no LET_GO anywhere). A fabricated let_go would assert
a fact about the player's hands that nobody pressed — the precise fabrication class
the no-fabrication laws exist to forbid, and it would BE an automatic un-snap,
which map:168 forbids K06 from doing ("no automatic snap-to-tree"). U03's
blur-releases-everything law is demand decay for the walk side and is deliberately,
declaredly NOT copied to edge facts (§6.5; prereg REVISION A records the scenario
fix that measures releases-through-the-blur). The §6.4 consequence (selector not
told to retract after a mid-climb pause) is the correct assignment of that decision
to K06.

**R5 — `C` as the let_go default: APPROVE (as data).**
No repo precedent exists (declared); the constraint space decides it: Shift is live
in U01's table (sprint) — overlap with a LIVE walk action would be a real conflict,
far worse than Space's declared-dead jump-refusal overlap; Ctrl carries OS/browser
shortcut risk; `C` collides with nothing in U01's DEFAULT_BINDINGS (input_mapper.py:99-106)
and is left-hand reachable while WASD-walking. It is a DATA default: §9's own law
makes remap a non-semantic edit. U07's actual-play lane should confirm live reach;
if the operator remaps, nothing bumps.

**R6 — Drop-naming dominance `disconnected > blurred > paused`: APPROVE.**
The first two are U03's existing, integrated law (focus_policy.py:187-194, verified);
pause appends weakest for the right reason — it is a session fact, not a claim about
the input surface. The dominance orders the NAME only: all three gates drop
identically, `gates_active` and `drops[].gates` carry the full truth (I3.k: drop
named `dropped_disconnected` with `gates == ["blurred","disconnected","paused"]`),
so naming cannot hide state. U06 gets honest diagnostics.

## 3. SPEC-IMPLEMENTATION COHERENCE (6 clauses, spec line <-> code line, executed)

1. **§3:57-59 — "the validator REFUSES any other [intent_version]"** ↔
   `climb_intent.py:149-152`. EXECUTED: v2 dict refused, `"1"` string refused
   (probes A2.a, A1.h). Gap found at the edges: `intent_version=True` accepted
   (probe A1.g) → **AMR-1**.
2. **§5.1:93-96 — exactly-once per accepted press, synchronous** ↔
   `climb_intent.py:293-295` (arm→emit, no queue, no background emitter) and
   `:354-362` (`_sink.emit(event)` inline). EXECUTED: I1.a; fuzz I8.f 354==354;
   probe A5.g (unbound/never-pressed paths emit nothing).
3. **§6.2:117-123 — named drops, strongest gate, full set recorded** ↔
   `:346-351` (`_drop`: `"dropped_" + self.state`, drop entry carries
   `gates: sorted(self.gates_active)`) + `:251-258` (`state` via
   `GATE_DOMINANCE`, `:118-119`). EXECUTED: I3.k; probe A3.b.
4. **§6.3:124-128 — gated press never arms; gated releases always pass** ↔
   `:285-287` (gate check BEFORE any `_held.add`) and `:297-304` (`release` has no
   gate branch at all; discard + return binding). EXECUTED: I3.d (fresh press after
   recovery fires once), I3.l, I3.n.
5. **§9:201-205 — bindings refused at construction by name** ↔ `:229-234`
   (value not in INTENTS → ValueError). EXECUTED: I2.m (`"J" -> "jump"` refused);
   probe A4.c (`chan.bindings` is a copy — the module default cannot be corrupted
   through an instance).
6. **§8:174-176 — exactly ONE walk-seam import, a constant, never CommandRecord** ↔
   `:81` (`from ...command_record import PHYSICS_HZ`; the only seam import;
   `__all__` carries no record type). EXECUTED: I5.d (AST import set == declared
   set), I5.e (`CI.PHYSICS_HZ is PHYSICS_HZ`), I5.b (`hasattr(CI, "CommandRecord")`
   false).

**Neighbor-code citations in the spec: all content-verified** (focus_policy.py state
dominance ~187-194, gated press ~277-281, release-always-passes ~285-288,
release-all ~262-270; input_mapper.py:105 `"Space": "jump"` exact, :115-116 jump
refusal exact, :198-199 unbound-ignored exact; command_record.py:70 `PHYSICS_HZ =
300` exact, :97-101 version law exact; session_flow.py:300-306 non-playing tick
drop exact). Cosmetic line drift of 1-4 lines on three citations; content exact.

## 4. ADVERSARIAL RESULTS (28/28 probes reproduced; 5 real findings)

Full transcript: `receipts/adversarial_probes_20260924.txt` (source:
`adversarial_probes_source.py`, run from outside the repo).

**Held the seam's claims (measured):**
- No float smuggles: float/NaN/Inf/bool stamps all refused (A1.a-e); huge ints
  accepted (spec has no upper bound — correct for a stamp); extra kwargs refused
  (dataclass, A1.i); frozen event mutation raises (A1.j).
- No version confusion: a v2/v3 wire dict refused by the v1 constructor (A2.a-b);
  the validator compares to the module constant, so a future v2 reader will refuse
  v1 events — by design, never reinterpret (A2.d).
- Gate-transition tick: press-vs-pause at the IDENTICAL `now_ms` resolves strictly
  by call order, deterministic 100/100 both ways (A3.a-b). Deterministic because
  delivery is synchronous (§5.1/5.3); see SPEC-NOTE N4.
- Second listener: the seam's API has no add_listener/attach/subscribe — a
  second-listener race cannot occur through the declared surface (A4.b). Wiring two
  channels to one sink double-delivers (A4.a) — that is harness mis-wiring outside
  the seam (SPEC-NOTE N1).

**Findings (each verified by probe; none fires the author's falsifiers I1-I8):**

- **AMR-1 (binding, validator):** `IntentEvent(..., intent_version=True)` is
  ACCEPTED (`True == 1`) and JSON-encodes as `"intent_version": true` on the wire
  (A1.g, A1.g'). The stamps explicitly exclude bool (`:159`); the version check
  (`:149`) must too: `isinstance(v, int) and not isinstance(v, bool)`.
- **AMR-2 (binding, validator):** `source` is not validated —
  `IntentEvent(..., source="not_the_channel")` constructs cleanly (A5.e), but §3
  says source is FIXED provenance. Provenance a constructor can forge is not
  provenance. Refuse `source != SOURCE_ID`. Wire format unchanged (the delivered
  field set and values are identical; consumers were already promised the fixed id).
- **AMR-3 (binding, ordering):** a press whose stamp fails validation (negative
  `now_ms`, or a raising `tick_source`) ARMS the edge first and raises second —
  measured: `held={'Space'}` with zero events, and the NEXT valid press is then a
  named-no-op, i.e. the physical press is silently consumed (A5.b-d). Fix: build/
  validate the IntentEvent BEFORE `self._held.add(name)` (`:293-294` reorder).
  Behavior-identical on every valid path; suite must stay 73/73.
- **AMR-4 (binding, docstring):** `press()`'s docstring says "Returns the intent
  name if ONE event was emitted, else None", but the repeat (held) branch returns
  the name with NO event (`:288-292` vs `:278-279`; measured A5.f) — the return
  value cannot distinguish delivery from no-op, contra the module's own contract.
  Fix the docstring to match the code (repeat returns the bound action; the trace
  names `repeat_press`). The declared consumer interface (§7, `emit` only) is
  unaffected either way.
- **NOT defect, recorded honestly:** sink-exception semantics are undeclared — a
  raising sink leaves the edge armed and the exception propagates (same class as
  AMR-3's path; AMR-3's reorder also shrinks this window to the emit call itself).
  Covered by SPEC-NOTE N5.

## 5. FUTURE-CONSUMER FIT (C6)

- **U06 (map:108):** SERVES. `state`/`gates_active`/`paused` answer "would climb
  intent be HEARD right now"; the stream answers "what did the player ask"; stamps
  share CommandRecord's `issued_tick`/ms clocks so flashes can be correlated with
  the walk timeline. The integration note correctly fences the two dishonest
  renderings (held != climbing; event-absence != unavailable). No pre-emption.
- **K-series selector (map:163,168):** SERVES the declared division of power. The
  consumer surface is one method (`emit`, §7); the selector owns meaning, lifetime,
  state machines, cancellation, and arbitration; the channel delivers climb_request
  and let_go as unrelated facts and arbitrates nothing (I4.e measured: both
  delivered, in press order). K06 can decide "no automatic snap-to-tree" freely —
  the stream never implies one.
- **X02 (map:179):** SERVES. `on_pause`/`on_resume` mirror the session flow's gate
  with one harness line; pause parity measured against the REAL `SessionFlow`
  (I7.l-n: named drops both sides, zero records/intents while paused, clean resume).
- **U03 (map:105):** SERVES. Exact policy-event names, drop naming, no-phantom
  arming, releases-always-pass — all reuse U03's integrated laws with verified
  citations; blur is measured hitting BOTH surfaces with one event (I7.f-g).
- **Nothing pre-empted:** the seam adds no intent meanings, no availability facts,
  no arbitration, no expiry. Every decision the map assigns to K01/K06/U06 remains
  theirs.

**SPEC-NOTES for v2 (not defects; no binding on v1):**
- **N1:** declare one-channel-per-sink exclusivity (two channels on one sink
  double-deliver — A4.a; a guard or a declared rule, either).
- **N2:** surface times are `int()`-truncated silently (`press`/`release`/policy,
  `:280,301,337`) — the house convention (focus_policy, session_flow do the same),
  but a named refusal would match the event validator's strictness.
- **N3:** binding KEYS are not type-checked (an int key works if pressed with an
  int); the surface contract says strings — cheap to enforce at construction.
- **N4:** state explicitly in §5 that same-`now_ms` events resolve in CALL order
  (measured deterministic; A3).
- **N5:** declare sink-exception semantics (currently: exception propagates, edge
  stays armed, event lost — the operator re-presses; §5.2's no-replay law arguably
  already implies this, but say it).
- **N6:** two presses inside the same millisecond share stamps; if K06's
  arbitration logs need total ordering beyond delivery order, v2 should say what
  the (ms, tick) pair does and does not promise.

## 6. HASH PROOF (C1, reproduced)

- Git blob sha of `tools/science_funnel/typeb_export/command_record.py`:
  `a9e0444fb495be213faf2023378fca11c43c5611` — IDENTICAL at the freeze commit
  `e028d6fb`, at the reviewed commit `87c14ca5`, at `HEAD`, and
  `git hash-object` of the working tree. Last commit touching the file: `e028d6fb`
  (the freeze itself). `git diff --stat 87c14ca5 HEAD` over the file: empty.
- Working-tree sha256: `061a2b55f2f5fd145e0fae918e8a9223b1d58be3bce78f1298cd45aa47aa8781`
  — equals the author's integration receipt AND both R4 re-runs (I6.a/I6.b green).
  `input_mapper.py` (`7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44`)
  likewise unchanged.
- Reviewer trap recorded: piping `git show <rev>:<path>` into `sha256sum` yields
  `67711759...` (LF blob bytes through the pipe) — a CRLF artifact, NOT a mismatch.
  Blob-level or file-level hashes only. Full proof:
  `receipts/walk_contract_hash_proof_20260924.txt`.

## 7. INTEGRITY

Session git status captured at `receipts/git_status_r4_session_20260924.txt`: the
only entries attributable to this review are under
`tools/monkey_campaign/agents/R4_intent_review/` (untracked, mine). The other
entries present at session start (`U02_camera/receipts/latency_run.json` modified;
`F04_contact/`, `TIE2/` untracked) belong to parallel agents — untouched by R4.
No repo file outside my directory was read-destructively, modified, or created;
adversarial probes ran from `C:/Users/allen/AppData/Local/Temp/` against read-only
imports. CPU-only throughout.

---

**R4 — 2026-09-24. Verdict: APPROVED-WITH-AMENDMENTS (AMR-1..4 binding; SPEC-NOTES
N1-N6 for v2; six rulings APPROVE; walk contract provably untouched).**
