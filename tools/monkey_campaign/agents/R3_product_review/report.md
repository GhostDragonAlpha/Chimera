# R3 REPORT — INDEPENDENT NON-AUTHOR REVIEW OF THE INTEGRATED PRODUCT STACK

Reviewer: R3 (non-author of every reviewed file). Date: 2026-09-24.
Worktree: `E:/ChimeraWork/monkey-play-20260924`, branch `monkey-play-20260924`,
HEAD `42f7cdc4`. Scope: U01 `product/input_mapper.py` (8550b634) + U03
`product/focus_policy.py` (8fc072f3) + X02 `product/session_flow.py` (42f7cdc4)
as ONE STACK. U04/U05 in-flight files excluded (see §7). Prereg:
`prereg.md` (frozen before module deep-read). Harness: `work/integrated_scenario.py`.
Receipt: `receipts/integrated_scenario_20260924.txt` (73 checks, 3 byte-identical runs).

## 0. VERDICTS

| Scope | Verdict | One-line reason |
|---|---|---|
| U01 input_mapper | **APPROVE** | Suite re-run green (26/26); every frozen number verified against the seam; no teleport surface; integration claims held |
| U03 focus_policy | **APPROVE** | Suite re-run green (41/41); blur==release_all byte-identity, gate topology, named state, no-stuck all reproduced under composition |
| X02 session_flow | **APPROVE** | Suite re-run green (74/74); table, quiesce, teardown-once, named no-ops all reproduced; but its §7 composition CLAIM is false (B1 belongs to the claim, not the module's own behavior) |
| **STACK** | **REJECT** (one blocking finding, B1) | The documented composition `SessionFlow(FocusPolicy(sink), ...)` DOES NOT CONSTRUCT as committed. Every other stack invariant passed (73/73) through a 2-line review shim, so the post-fix re-review is mechanical |

### B1 (BLOCKING) — the declared composition does not exist as committed
- **Claim under review**: X02 `DISCOVERY.md` §7: "when U03 lands, the flow's mapper slot
  accepts the FocusPolicy wrapper unchanged (it presents the mapper surface plus the policy
  events)". U03's `INTEGRATION_U07_X02.md` promises the same interplay.
- **Reality**: `session_flow.py:234-240` requires the surface
  `press/release/mouse/tick/release_all/held`. `focus_policy.py` exposes all of these
  EXCEPT `release_all` (it has only the private `_release_everything`).
- **Reproduction** (also `receipts/integrated_scenario_20260924.txt`, checks B1):
  ```python
  from tools.monkey_campaign.product.session_flow import SessionFlow
  from tools.monkey_campaign.product.focus_policy import FocusPolicy
  SessionFlow(FocusPolicy(MockSink()), restart_scene=..., teardown=...)
  # FlowError: mapper must provide the declared U01 surface
  # (press/release/mouse/tick/release_all/held); missing 'release_all'
  ```
- **Why blocking**: no legal composition of the three committed modules exists. The only
  alternative (flow over the bare mapper + policy elsewhere) either bypasses the policy's
  intent gate or cannot wire the expiry gate (the policy OWNS the mapper's sink via
  `mapper_factory`). Neither author's suite ever constructed the composition —
  `grep FocusPolicy session_flow_tests.py` = 0 hits; `grep SessionFlow focus_policy_tests.py`
  = 0 hits. Each layer's "interplay" was tested against doubles only. This is exactly the
  preregistered falsifier class: "a module assuming another module's internal behavior that
  the other does not actually provide".
- **The fix is one line** (owner: U03, its file; must go through U03's amendment trail, not
  a silent edit): expose the passthrough with the policy's own trace discipline, e.g.
  `def release_all(self, now_ms): return self._mapper.release_all(int(now_ms))`.
  Alternatively X02 could prereg an amendment routing pause/restart through
  `on_blur`-style policy events — but that changes pause semantics (decay-under-menu vs
  suspension) and U03's own note warns against faking blur for pause. The passthrough is
  the minimal, semantics-preserving fix. The failure is loud (construction-time FlowError),
  not a silent corruption — severity is availability of the documented composition, not
  correctness of behavior.
- **Conditional green**: with the shim ONLY (`class ComposedFocus(FocusPolicy)` adding that
  passthrough, in my dir), the full integrated stack passes 73/73 (§2-§3). After the real
  fix lands, re-run `work/integrated_scenario.py` with `ComposedFocus = FocusPolicy`.

## 1. CONTRACT COHERENCE (check 1) — the interplay contracts read, then measured

| Contract | U01 says | U03 says | X02 says | Coherent? |
|---|---|---|---|---|
| `release_all` semantics | physical releases; decay to exact 0.0 within 100 ms, then silence (module :225-228, :293-313) | clause 1/2/5: blur & disconnect are exactly that; a repeated release_all never restarts a tail | pause/restart quiesce is exactly that primitive (:324, :332) | YES — and measured: quiesce sequence `[release_all]` only (S1); idempotence held (S2a) |
| pause = suspension via release_all | — (consumer duty only) | ticks must pass "so the decay reaches the sink" — the flow DELIBERATELY VIOLATES this while paused (no boundaries at all) | prereg rule 2: suspension, not suppression; the tail finishes on resume | YES with one nuance: U03's no-stuck clause (ii) expects the exact-0.0 landing shortly after E; under flow-pause it arrives at RESUME. The invariants that actually matter (no v>0 past E+100 ms; exact-0.0 landing; silence) all held in both orders (S1, S2c) |
| bounded resume tail | `_apply_tail` samples ≤ 2 boundaries, `_apply_tail can only decay` | clause 4: re-arm on an empty held set; no replayed tail | prereg rule 3: ≤ 2 records, ≤ pre-pause speed, exact 0.0, then silence | YES — measured: `[0.0]` (pause outlived the window), `[0.458175, 0.0]` (interrupted mid-window), never more, never above pre-pause v |
| expiry floor in the emission path | `is_expired`, age > 30 ticks strictly | gate IS the mapper's sink; drops named `expired_at_gate`; healthy clock drops zero | leans on it for the pre-pause record | YES — S2f: 9 fresh-at-delivery passed, 3 stale dropped+named, 0 stale in sink, one emission path (no double-delivery — U03's REVISION A defect did not re-emerge under composition) |
| two-state seam (inert vs live-zero) | preserved; idle emits NOTHING | refuses hard-clear for exactly this reason | adds no seam-affecting primitive | YES — but note the emergent case in §5-F5: resume after a long pause emits ONE live-zero 0.0 record (declared-legal, ages out) |

**The one place two modules assume different things about the third**: X02's resume-tail
rule vs U01's decay is coherent; U03's reconnect re-arm vs U01's decay is coherent; the
REAL divergence found is X02's restart rule vs U01's decay — see B2 below (non-blocking).
The second divergence is documentation-level: U03's note recommends routing pause through
`on_blur`/`on_focus` ("pause is NOT blur... do not route pause through this module
silently"), while X02 as-built calls `release_all` directly and claims the wrapper slots in
"unchanged" — the notes disagree about WHERE the composition lives, and the claimed wiring
is the one that does not construct (B1).

## 2. INTEGRATED SCENARIO (check 1, the spine) — 73/73 PASS, 3 byte-identical runs

`play → hold W → blur → refocus → pause → resume → restart → exit`, driven through
`SessionFlow → (shim)FocusPolicy → InputMapper → gate → FaithfulConsumer`, injected clock,
headless. Asserted cross-module invariants, all green:
- zero emissions on non-playing ticks (attract span; 38 paused ticks with concurrent
  key/mouse mashing — 100+ named drops, zero records);
- the policy slot received NOTHING while the flow was suspended (the flow is the sole
  clock authority; U03's "ticks always pass" is correctly overridden by the flow's gate);
- the resume tail: ≤ 2 records, each ≤ pre-pause speed, landing EXACTLY 0.0, then silence,
  grid dissolved;
- teardown exactly once, `world_log == ["boot", "teardown"]`; second Q a named drop;
  boot exactly once per restart; mid-play R never boots (S2e);
- no stuck movement anywhere: every record `0 ≤ v ≤ 0.763625`, `|yaw| ≤ 1.6`,
  `source="u01_input_mapper"`, issued_ticks monotone; blur decay
  landed `(620, 0.687), (670, 0.0)` — no v>0 past blur+100 ms;
- no press reached the mapper while blurred (the policy held the gate the flow cannot see).

## 3. ADVERSARIAL COMPOSITION (check 2) — events no individual suite tried together

| Probe | Result | Numbers |
|---|---|---|
| S2a blur DURING the resume tail | PASS — blur did not restart the tail (idempotent release_all); tail completed under blur; fresh press after focus arms a fresh grid | tail `[0.458175, 0.0]`; post-focus record at its own boundary |
| S2b restart DURING the decay window | **FINDING B2** — the stale tail CROSSES the boot: a positive record (0.458175 m/s) reaches the FRESH scene post-boot | bounded: exactly `[0.458175, 0.0]`; no positive past 120+100 ms; bounds held |
| S2c disconnect + pause race, both orders | PASS both — decay completes pre-pause (disconnect-first → resume silence) or completes on resume (pause-first → `[0.0]`); no new demand while disconnected; reconnect re-arm clean | both orders: reconnect → fresh press → `[0.763625]` at its own boundary |
| S2d key held across the ENTIRE restart | PASS — the post-restart mapper sees NO stale held key (`held == ∅`); restart outside the decay window yields only the exact-0.0 landing `[0.0]`; zero movement without a genuine re-press; a re-press walks again. (A restart INSIDE the window imports the stale sample — that is B2, corroborated twice: `[0.076, 0.0]`) | `held=0`, vals `[0.0]` |
| S2e R during play | PASS — named no-op, zero boots (the table's deliberate absence holds) | — |
| S2f expiry floor inside the composition (stalled physics clock) | PASS — 9 fresh-at-delivery passed, 3 stale dropped+named, 0 stale reached the sink | `{'passed': 9, 'expired_at_gate': 3}` |

**B2 (non-blocking, named finding)**: X02's prereg table row 4 claims the quiesce means
"no stale held keys cross the boot" — literally true (held is always empty), but the
pending DECAY TAIL does cross the boot: any restart executed within 100 ms of a released
positive demand injects up to 2 records (first one POSITIVE, ≤ pre-pause speed) into the
freshly booted scene. Measured twice (S2b `[0.458175, 0.0]` at V_MAX*0.6; S2d-corroboration
`[0.07636, 0.0]` at V_MAX*0.1). Not stuck movement (bounded, monotone, lands exact 0.0
within the frozen deadline), so it does not fire the row's own falsifier — but "reset is an
explicit user action" arguably implies the fresh scene starts command-silent. If that
ruling is wanted, the fix belongs in a prereg'd amendment (e.g. the restart transition also
dissolving a non-exhausted tail is a NEW seam-affecting primitive and must not be done
silently — it would need the same care U03's clause 1 got). Recorded as APPROVE-with-notes
material for the stack owner; X02's NOTES_X03_R01.md item 2 ("a recovery action can never
race an in-flight walk command") should be read with this caveat.

## 4. CLAIM SPOT-CHECKS (check 3) — 3+ citations per report, verified against the tree

Hash-proofs: X02's receipt (`session_flow_tests_receipt.json`) pins sha256 for
`session_flow.py`, `input_mapper.py`, `session_flow_tests.py` — **all three MATCH the
current tree** (U01 and U03 receipts are prose logs without hashes — minor: only X02's
receipt is hash-pinned). Git provenance: each module last touched by exactly the commit the
brief names (8550b634 / 8fc072f3 / 42f7cdc4); `git diff HEAD -- product/` empty.

**U01 (`discovery_note.md` + `INTEGRATION_U03_U04_U07_W08.md`)**:
1. `gait_controller.hpp:2252-2255` configure intake, domain ≥ 0 — VERIFIED exactly
   (`require(a>=0.,"gait_command_domain"); cmd_vx_live_=true;...`); `:108-111` (20 Hz ZOH),
   `:1116-1117` (the fire), `:121-123` (inert), `:2772-2775` (echo) — all exact.
2. `command_record.py:66-70` V_MAX=0.763625 / HOLD_TICKS=15 / POLICY_HZ=20 / PHYSICS_HZ=300
   — VERIFIED exactly; `controller.py:45` TURN_RATE=1.6 VERIFIED.
3. `input_mapper.py:225-228 release_all`, `:341-347 is_expired`, `:77 VALID_MS=100`,
   `:94 EXPIRY_TICKS` — VERIFIED.
   **DRIFT**: `command_record.py:81-83` ("live zero... NOT a stop bar") and `:84-87` (R4)
   and `:180-181` (`routed_yaw_rate: False`) — the cited lines do NOT contain the cited
   content; actual locations `:44-47`/`:218`, `:48-51`/`:221-224`, `:166`. The file is
   unchanged since its freeze (e028d6fb, sole commit), so the drift is in the reports (and
   it propagated into `input_mapper.py`'s own docstring and U03's prereg). Content exists;
   line numbers wrong. Citation-hygiene defect, non-blocking.

**U03 (`INTEGRATION_U07_X02.md` + prereg)**:
1. "blur byte-identical to the mapper's own release_all (P2.a, 5 vs 5 records, 0 field
   mismatches)" — the test exists at `focus_policy_tests.py:185-220` comparing all five
   fields; suite re-run green (41/41) — VERIFIED.
2. `input_mapper.py:293-313` (`_apply_tail`), `:262-267` (grid dissolve) — VERIFIED exact.
3. "both named hooks existed (`release_all`, `is_expired`)... no amendment needed" —
   VERIFIED the hooks exist; BUT the note's own composition promise ("the flow's mapper
   slot accepts the FocusPolicy wrapper") is the FALSE claim B1.
   Same `command_record.py:81-83` line drift as U01 (shared lineage).

**X02 (`DISCOVERY.md` + prereg)**:
1. `slice_server.py:94-135` `World.boot` with inner steps (`:96` shutdown, `:97`
   free_port, `:98-103` Popen `--no-restore --hidden`, `:105` wait_engine, `:108`
   boot_standing_start, `:126-131` resets, `:128` boot_count) — VERIFIED exactly.
2. `slice_server.py:174-181` `shutdown_engine` terminate → wait(10) → kill — VERIFIED
   exactly; `:38` NEVER_PORT=8127 VERIFIED; `:543-547` /api/restart VERIFIED.
3. `index.html:1070-1073` dev keys c/x/r/s, `r`→`/api/restart` at `:1072` — VERIFIED.
   **FALSIFIED**: §7 "the flow's mapper slot accepts the FocusPolicy wrapper unchanged" —
   B1 above. Fair context: at discovery time `focus_policy.py` did not exist, so §7 was a
   prediction about a surface not yet written; it lost, which is what reviews are for.

## 5. FALSIFIER MINING (check 4) — gaps I could NOT break but suspect (notes, not defects)

- **F-1 (the biggest one): pause's instant-stop leans on a consumer that does not exist
  in-tree.** All three docs assign the pre-pause record to the "consumer-side expiry
  contract" (revert to inert past VALID_MS). `grep is_expired` in-tree: only the three
  modules and their tests. Measured (S3): a naive ZOH consumer sees FULL-SPEED demand for
  the ENTIRE pause; the declared consumer coasts ≤ 100 ms then goes inert. The modules are
  internally consistent and honestly declared — but today nothing in the tree enforces the
  contract on the sink side, and the live harness (U07) must implement it or the animal
  walks through the pause menu. Flagged for U07/W08 acceptance.
- **F-2**: OS/browser key-repeat re-sends keydown while a key is physically held; after a
  restart-with-key-down the page would re-press W without an explicit user act. The flow
  cannot distinguish repeats from presses; X04 owns the page wiring. Not measurable
  headless; flag to X04.
- **F-3**: exit does NOT quiesce — the terminal object keeps `held={'W'}` (S4). Harmless
  while terminal (nothing forwards), a phantom-key hazard only if a future feature
  resurrects or serializes the flow object. A one-line `release_all` in the exit transition
  (a prereg'd amendment) would make the terminal state total.
- **F-4**: flow keys are consumed absolutely, in every state, before the mapper sees them:
  a U04 settings remap that binds gameplay to `Return/Escape/R/Q` is silently stolen by the
  flow layer (bindings-are-data has no cross-layer namespace check). U04's loader should
  refuse flow-key collisions by name.
- **F-5**: resume after a pause that outlived the decay window emits exactly ONE
  live-zero record (`[0.0]`, measured) — the declared "landing". Legal (not a stop bar) and
  it ages out via the consumer contract, but U07's traces should expect a zero-advance
  target after every long pause; the seam is live-zero, not inert, until expiry.
- **F-6 (pending integration)**: U04/U05 files appeared mid-review (untracked:
  `product/input_settings.py`, `input_settings_tests.py`, `product/climb_intent.py`) —
  excluded per brief. When U04 lands: U01's note (lines 53-56) already rules that the
  bounds (`V_MAX_IN_BAND_M_S`, `INTERVAL_MS`, `EXPIRY_TICKS`) must NOT become settings; the
  F-4 collision rule and the B1 passthrough both touch U04's wiring surface.

## 6. ACCEPTANCE MAPPING

1. Frozen checklist — `prereg.md` (frozen before the module deep-read; falsifier named
   there is exactly the one that fired: cross-module assumption mismatch → blocking).
2. Integrated scenario — GREEN: 73/73 checks, 3 byte-identical runs, via the declared
   review shim; AS COMMITTED the composition does not construct (B1, reproduction in §0).
3. Adversarial-composition results — §3: blur-in-tail PASS; restart-in-decay FINDING B2
   (bounded, non-blocking, twice corroborated); disconnect+pause race PASS both orders;
   key-held-across-restart PASS (no stale held key).
4. Citation spot-checks — §4: hash-proofs 3/3 MATCH; 9+ line citations verified exact;
   one systematic line-number drift found (command_record.py :81-83/:84-87/:180-181 →
   actual :44-47/:48-51/:166); X02 §7 composition claim falsified (B1).
5. Verdicts — §0: U01 APPROVE, U03 APPROVE, X02 APPROVE, STACK REJECT on B1 alone (with
   the one-line fix named; post-fix re-review = re-run the harness with the shim removed).
6. Integrity — writes ONLY under `agents/R3_product_review/` (brief.md, prereg.md,
   work/integrated_scenario.py, work/run2.txt, work/run3.txt, receipts/). The three
   committed suites were re-run in place with `PYTHONDONTWRITEBYTECODE=1`; X02's suite
   rewrites its own receipt path but the tree stayed byte-clean (`git status`). The
   `?? agents/TIE2/` entry in final git status appeared from a concurrent fleet agent
   mid-review and is not R3's. No commit made (not requested; verdict-only stop).

## 7. OUT-OF-SCOPE NOTES
U04/U05 in-flight (untracked) files were excluded; S01/F04/W7/TIE2 dirs likewise. Nothing
outside my dir was modified by this review.
