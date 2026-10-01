# H7 judge-doctor — mechanism notes (before-repro → fix → after-gone)

Inputs: `R8_R4_PLAYBOOK/DRYRUN_H5.md` (hand-play stalls S1–S9) and
`R4_TEN_WALK/walk10_attempt2_summary.txt` (walker attempt 2). Two probes agree;
every fix below was driven by a measured before-repro (`probes/probe_before.js`,
`probes/probe_before2.js` → `before_repro.json`, `before_repro2.json`) and closed
by an after-verify (`probes/probe_after.js` → `after_verify.json`).
Screenshots in `shots/`. Acceptance runs: `accept_a_e.json` (a+e), the
ten-lesson diagnostic walk (f) recorded separately in `diagnostic_walk/`.

## D1 — lesson state latches across lessons

- **Before-repro (probe_before D1):** pressing SPACE in L1 and advancing with
  `]` WITHOUT releasing left lesson 2 starting with the hand still
  "pressing — 11500 N (space)" and torso cells carrying 482 624 Pa of the
  previous lesson's press; revisiting L1 kept `goalMet=true` from the earlier
  visit. Also measured: `lastTouchForce` is global and never reset per lesson
  (a stale 50 000 N blocked a later capped lesson in probe_before2 §4).
- **Mechanism (three latches):**
  1. `lessonState[id]` (goalMet/phase/pairOk/wokenSet/wokeMemo/…) was created
     once and NEVER reset at lesson start;
  2. `showLesson()` neither cleared a live engine touch nor reset
     `lastTouchForce` — the WORLD's press state leaked across lessons;
  3. the release-phase calm check counted the engine's broken zero-volume
     cell4 (measured V=4.65502e-9 m³ pinned at up to 1 622 780 000 Pa) as
     unhealed water, so `the_heavy_hand` and `the_graduation` sat at
     `phase=release goalMet=true` forever — the walker's FAIL rows.
- **Fix:** `showLesson()` now (a) `clearTouch()` + cancels the tap pulse,
  (b) zeroes `lastTouchForce`/`lastTouchAt`, (c) resets the target lesson's
  runtime state (goalMet→false, phase→'goal', all memos/latches cleared) while
  preserving only the earned `passed` latch (progress semantics). The judge's
  calm/wake/quiet checks skip broken cells (`brokenCell()`: finite V ≤ 1e-6 m³
  = 1 cm³; real compartments are 0.28–12.5 m³).
- **After-gone:** probe_after D1 → `the_gentle_hand phase=goal goalMet=false`
  with `hand open` at start; L1 revisit shows `phase=goal goalMet=false,
  passed=true`. 5-cycle press-release clean (see D3).

## D2 — presses die after the first

- **Before-repro:** SPACE path 5/5 answered; mouse path 0/5 at (720,500).
  probe_before2: a deliberate 52×429 burst ATE the next SPACE press silently —
  `lastTouchForce=50000` set, `holding=false`, no retry, no report, hand said
  nothing. The engine double-touch probe also showed refusals return
  `200 {"ok":false,"error":"the point is not on the body"}`.
- **Mechanism:** three stacked causes.
  1. The page read only the HTTP `res.ok` flag of the touch POST, never the
     body's `ok` — an engine refusal still set `holding=true` (a press that
     never was), and a 429/network failure silently dropped the press;
  2. the mouse path pressed only at pointerUP and any later pointerup ended
     the press — clicks alternated press/release, so half of a player's
     clicks did nothing;
  3. under the rate storm (D6) touch POSTs 429'd and vanished.
- **Fix:** one retrying sender (`postTouchRetry`: 3 attempts, backoff
  400/800 ms × jitter ±30%, retries only on 429/5xx/network); the response
  BODY decides (`ok:true` → press; `ok:false` → the engine's own error text
  goes to the hand line, e.g. "the point is not on the body"); retries spent →
  "the world is busy — the press did not land. try again." The mouse path now
  sets `lastTouchForce`/`lastTouchAt` like SPACE (judge force-cap honesty).
- **After-gone:** probe_after D2 → mouse 5/5, SPACE 5/5, taps 3/3.

## D3 — the phantom press (mouseup ends nothing)

- **Before-repro (probe_before D3):** mouse down 2 s, up → HUD stuck at
  "pressing — 20000 N" with `holding=true` (3/3 in the H5 dry-run, 1/1 here).
- **Mechanism:** the press STARTED at pointerup (`endPress → tryTouch`) and
  `holding` flipped true asynchronously AFTER the up — so the very up that
  started a press could never end it; there was no keyup/blur/visibilitychange
  handling at all, so a scripted SPACE held the world's hand forever.
- **Fix (the new hand model):** pointerdown (still ≥130 ms) starts the press;
  moving >6 px turns the gesture into an orbit and ends the press; pointerup
  ends a HELD press immediately; a TAP (<250 ms) lets its press pulse ~900 ms
  so the engine and judge see it, then the hand opens by itself; SPACE keyup
  ends a SPACE press; pointercancel / window blur / visibilitychange-hidden
  all end the press. In-flight POST races are closed: if the pointer/keyup
  ends while the press POST is still in the air, the press ends the moment it
  lands (`mouseClearOnLand` / `spaceClearOnLand`) — that was the last path a
  phantom could survive through.
- **After-gone:** probe_after D3 → 5/5 hold-release cycles clean, drag-out
  clean, blur (alt-tab) clean.

## D4 — the unusable slider

- **Before-repro (probe_before D4):** `elementFromPoint(1190,453)` — H5's
  thumb-drag and track-click coordinates — returned **`force-meter-fill`**:
  the decorative meter bar (y 451–456) sits under the input and INTERCEPTED
  the pointer. The slider never got focus (focus landed on BODY — measured),
  which is why even the arrow keys "did nothing". Aimed AT the input, all
  three modes worked — the binding was never broken; the meter was stealing.
- **Fix:** `pointer-events:none` on `#force-meter` and `#force-meter-note`;
  the input grew to a 28 px hit area; `user-select:none` on the sidebar (H5's
  label text-selection artifact); the keyboard guard now skips only TEXT
  inputs, so SPACE / - / = work even when the slider has focus (arrows stay
  native for the focused slider).
- **After-gone:** probe_after D4 → drag 50000→5600, track click →5600,
  arrows →6000; label "6000 N", meter 11.11%, and the next press actually
  SENT `force_n=6000` (captured on the wire). ×3 modes agree with sent force.

## D5 — judge integrity

- **Before-repro:** code + injected-frame probe. `forceOk` used to be
  `!cap || !lastTouchForce || lastTouchForce <= cap` — a lesson whose
  qualifying press NEVER happened passed (0 counts as force-ok, and the mouse
  path never set `lastTouchForce` at all). L1–L3 all passed with the one
  shared sentence "PASSED — you felt the water. it was always there."
  (`lessons.json` never carried per-lesson pass copy).
- **Fix:** `forceOk = !cap || (lastTouchForce > 0 && lastTouchForce <= cap)`;
  pressure latches (pressure_above incl. `also`, pressure_isolation target,
  cells_woken) require `pressFresh()` — the crossing must land within 2.5 s
  of a hand-accepted touch post, so residual/injected/phantom pressure can
  never latch a goal; `lessons.json` now carries a distinct `pass_line` per
  lesson and the page speaks `PASSED — <pass_line>` (pose lessons keep their
  bespoke lines as fallbacks).
- **After-gone:** probe_after D5 → injected cell0=60 kPa with NO press:
  "the creature waits.", goalMet=false; then a real recorded 6000 N press:
  `PASSED — a gentle hand: the small water answered a small touch.`
  (acceptance (b) evidence, `recordedPress: 6000`).

## D6 — the 429 storm

- **Before-repro:** with every API answer poisoned, the page made 59 requests
  in 8 s = **443 req/min forever** (333 ms verts timer + an IMMEDIATE
  `?delta=key` resync on every failure — two requests per failed beat), until
  the shell's own budget 429'd it (H5: 1362 errors / 17 min).
- **Mechanism:** fixed-interval timers never back off; the catch block added
  an unthrottled second request.
- **Fix (page):** self-scheduling poll loops — any failed beat backs off
  exponentially (2^n beats, capped 15 s verts / 10 s state) with ±20% jitter;
  success restores the base pace; the immediate pullKey-on-failure is gone
  (a torn-but-200 frame resyncs through the normal in-try seq-gap path on the
  next beat). While starved the page says so honestly:
  `the world is unreachable — the lesson holds for the world, not for you.
  nothing is being asked; this line clears on its own.` (verdict line, warn
  tone; restored verbatim on recovery; a partial outage shows a link-line
  note instead). The judge never demands a player action while starved.
- **Fix (server):** engine URL is `CHIMERA_ENGINE_URL` or `--engine`
  (default unchanged `http://127.0.0.1:8107`) so scratch shells point at
  private engines; the stream budget is raised 600→**1200 req/min, burst 480**
  — the shared-NAT tradeoff, documented in server.py: the bucket stays keyed
  per IP (NOT per session — session minting must not bypass it), 1200/min
  serves ~4 honest players (4×264=1056) behind one router, and a hammering
  client can only reach the PROXY at that rate, with the page's own backoff
  making hammering self-defeating. 429 answers carry `Retry-After: 1`.
- **Verified on a scratch port** (8293/8294, live shell untouched): env var
  startup line, `--engine` override, 429 burst → 8×429 each carrying
  Retry-After.
- **After-gone:** probe_after D6 → 7 requests in 10 s = 42/min and falling,
  with the honest hold line up.

## D7 — display guards + telemetry

- **Before-repro:** injected/live frames rendered `cell 4: V=0.000 m3
  P=1622.780 MPa` as if it were blood pressure; "the pose was refused." gave
  no reason; the internal `judge: … phase=… touchTarget=…` line rendered for
  every buyer.
- **Fix:** zero-volume cells render as
  `cell 4: V=0.000 m3  P=---  sealed solid (no water)` (threshold 1e-6 m³;
  measured live value 4.65502e-9) and non-finite P renders dashes; pose
  refusals surface the engine's error (`the pose was refused — <reason>`),
  touch refusals already did; `renderJudgeDebug` renders ONLY with
  `?debug=1` (format unchanged — the walker now passes the flag).
- **After-gone:** probe_after D7 → sealed-solid shown, no 1622 garbage,
  line empty without the flag and present with it.

## THE WALKER RECONCILIATION (defect 1's second half: who lied?)

**Answer: neither the walker's pass rule nor the page's phase reporting lied —
the ENGINE's cell4 lied, and the page's guilty part was believing it.**
Walk-through of attempt 2's rows:

- `the_heavy_hand` / `the_graduation`: `FAIL phase=release goalMet=true` —
  goalMet was EARNED (the torso press reached 11.9 MPa ≥ 3 MPa; three cells
  woke), the phase advanced to release honestly, and then the calm check
  demanded ALL cells < 1000 Pa — including cell4, pinned at 1 622 780 000 Pa
  by the engine's zero-volume defect. `passed` never arrived; the walker's
  rule (`v.passed`) reported the truth. Fixed page-side: broken cells are
  skipped by every judge check and shown as "sealed solid"; the walker's own
  `waitCalm` now skips them too. **Engine-side root cause (belongs to engine
  agents, NOT fixed here): a seal/damage cell can sit at V≈4.7e-9 m³ while
  reporting pressures up to 1.62 GPa; a cell with no water should report no
  pressure (or the shell's guard will keep hiding it).**
- `the_balance`: `PASS` while the cells sat at rest with garbage cell4 —
  no lie: pose_pair is judged on POSTED INTENT per LESSON_JUDGE_SPEC (the
  accepted /api/pose wishes), not on pressures. The garbage display next to
  the pass was D7's problem, now guarded.
- `the_gentle_hand` FAIL (all cells 0 Pa) — that was D2 (the eaten press),
  not the judge.

## What belongs to engine-side agents (not fixed here)

1. **Zero-volume cell garbage**: cell4 (the seal/damage bookkeeping cell?)
   holds V=4.65502e-9 m³ and reports P up to 1 622 780 000 Pa (and negative
   −0.009 MPa elsewhere). The page now guards, but the root fix is the
   engine's: a zero-volume cell must report zero pressure.
2. **S5 (no visible dent)**: dents exist in the numbers (cell spikes measured)
   but were not visible to H5 at the default zoom; the mesh response to a
   3 cm Gaussian is engine-side. The page now guarantees every press ANSWERS;
   making it LOOK like an answer is an engine/render task.
3. **Touch apply latency**: /api/state can lag a touch_hit by up to ~1 s
   (probe_before2 §1: torso still 0 mid-hold, 89 829 Pa after release) — the
   tap pulse (900 ms) covers it, but tightening engine latency would let the
   page shrink the pulse.

## Files changed

- `tools/game_shell/index.html` — input model, judge gates, display guards,
  backoff loops, pass sentences, telemetry gate (sound rails unchanged:
  press/passed/wakeWhoosh/cellWake/healShimmer/saved/init/ambient all live).
- `tools/game_shell/lessons.json` — `pass_line` per lesson (10/10 distinct).
- `tools/game_shell/server.py` — env/--engine world URL, 1200/min stream
  budget + documented tradeoff, Retry-After on rejections.
- `tools/game_shell/walk_lessons10.js` — `?debug=1` rides the URL;
  `waitCalm` skips sealed-solid cells.
- Evidence: this directory (`probes/`, `shots/`, JSON results,
  `diagnostic_walk/`).

---

# FINISH — H7r "page-finisher" (2026-09-14)

H7's tree landed D1-D7 but got stuck before committing; three audits arrived while it
worked. This finisher audited that diff against all three lists, found SIX defects still
live in the tree, fixed them with before-repros, and ran the full acceptance.

## What H7's tree already covered (verified fresh, not re-fixed)

D1 lesson-state latches, D2 unanswered presses, D3 the phantom press, D4 the dead slider,
D5 judge integrity (force cap + pressFresh), D6 the 429 storm (page backoff + server
budget), D7 display guards + telemetry gate. Re-run of H7's own after-probe against the
fixed page: D1-D6 all CLEAN again (`after_verify.json`; H7's original kept as
`after_verify_h7_original.json`; console "errors" in both are only the browser's own logs
of the probe's INJECTED 500s).

## The six defects H7's tree did NOT cover — mechanism, before, fix, after

All six before-repros: `probes/probe_h7r_before.js` -> `probe_h7r_before.json` (all
DEFECT LIVE). All six after-verifications: `probes/probe_h7r_after.js` ->
`probe_h7r_after.json` (all CLEAN). Failure injection is page-level only (route
interception / synth wrapping); the engine saw ordinary traffic.

| # | defect (source) | before (measured) | fix | after (measured) |
|---|---|---|---|---|
| 1 | gravity false-arm (H10 fix-1) | a 429'd /api/gravity enable still armed the judge: 1x429 -> `armed=true` while root_y stayed exactly 0 (fetch resolves on ANY status; body never read) | `enableGravity()`: parse the body, arm ONLY on `ok:true`, 3 gentle retries, honest unarmed + link line on refusal | `armed=false` under 429; honest enable arms and the root settles 9.507 mm (A1) |
| 2 | touch_clear fire-and-forget (H10 fix-2) | a 429'd release POST was dropped forever: exactly 1 clear call, no retry, no report -> the engine keeps pressing (the sticky phantom's last path) | `clearTouchSend()`: 3 attempts, 400/800 ms backoff x jitter; idempotent server-side; retries spent -> honest link line | 2 calls under the same one-shot 429 -> retried and landed (A2) |
| 3 | pressEnd never wired — SHIP-BLOCKER (H9-1) | 4 page-driven presses, 0 pressEnd calls: the first press started a tone that never stopped; releases mute | `snd('pressEnd')` in `clearTouch()` — the single release funnel (ESC, let-go, rest, pointerup, cancel, blur, tab-hide, tap pulse, lesson switch) | 1 pressEnd per release through BOTH the keyup and ESC funnels (2 presses -> 2 ends) (A3) |
| 4 | showLesson doesn't await resetPose (H10 fix-3) | next lesson's judge window opened 8 ms after `]` while the cells still carried the held ankle pose (6.0 MPa / -8.8 kPa / 715 kPa signature) | `showLesson` is async and AWAITS `resetPose()`, whose six joint posts each retry until the engine takes them | flip at 4315 ms with the delayed-route load, cells `[0,0,0,0]` at the flip (A4) |
| 5 | lesson-switch whoosh re-fire (H9-3) | an already-awake cell whooshed AGAIN on lesson switch (memo was per-LESSON and showLesson reset it): 1 -> 2 | the wake memo is WORLD-scoped (`worldWokeMemo`); per-lesson `wokeMemo` removed | 1 whoosh on L1, 0 additional after the switch; the memo still clears when the cell falls asleep (A5) |
| 6 | snd() failure invisibility (H9-4) | an injected throwing synth left NO trace: 0 console output, no counter, no state (silence undiagnosable) | failures count per method into `window.__sndFailures`; the ?debug=1 judge line carries a `snd-fail:` tally; still ZERO console output ever | thrower counted 1x, `snd-fail: press` in the debug line, 0 console errors (A6) |

## PER-DEFECT VERDICT TABLE — every defect in the three lists, classified

H5 `R8_R4_PLAYBOOK/DRYRUN_H5.md` (page-team stalls):
| stall | verdict | evidence |
|---|---|---|
| S1 phantom press after release | FIXED by H7, verified | after_verify D3: 5/5 cycles clean, drag-out clean, blur clean |
| S2 slider stuck at 20000 N, all 3 modes | FIXED by H7, verified | after_verify D4: drag 5600 / track 5600 / arrows 6000, label+meter agree, wire-captured force_n=6000 |
| S3 lessons pass without the asked action | FIXED by H7, verified | after_verify D5: injected 60 kPa with NO press does not pass; a real recorded 6000 N press passes |
| S3 identical pass sentences | FIXED by H7, verified | accept_h7r_b_e.json: L1/L2/L3 pass on real input with three DISTINCT sentences |
| S4 presses die after the first | FIXED by H7, verified | after_verify D2: mouse 5/5, SPACE 5/5, taps 3/3 |
| S5 no visible dent | ENGINE-SIDE (named, not page) | presses ANSWER page-side (D2); making the 3 cm Gaussian LOOK like an answer is engine/render work — H7's MECHANISM_NOTES named it for engine agents |
| S6 absurd telemetry (V=0.000, P=1622 MPa) | FIXED by H7 + engine root FIXED by H8 | page renders `sealed solid (no water)`; engine now boots the guarded clean 4-cell world (seal_refusal by name); page guard re-verified as defense: probe_h7r_d7defense.json (injected sliver renders sealed-solid, 1622 hidden) |
| S7 pose refused without reason | FIXED by H7 | `poseRefused()` surfaces the engine's own error text |
| S8 judge: telemetry in buyer's face | FIXED by H7, verified | renders only with ?debug=1 (after_verify D7); walkers pass the flag, players never see it |
| S9 429 flood (1362 / 17 min) | FIXED by H7, verified | after_verify D6: 54 req/min while starved (was 443/min) + honest hold line; soak: zero 429s in 10 min |

H10 `H10_WALKER/H10_WALKER_AUDIT.md` (page fix list):
| item | verdict | evidence |
|---|---|---|
| 1 gravity res.ok check | FIXED by H7r | A1 above |
| 2 clearTouch res.ok + retry | FIXED by H7r | A2 above |
| 3 showLesson await resetPose | FIXED by H7r | A4 above |
| 4 judge degenerate-cell guard | FIXED by H7 (brokenCell in calm/woken/whoosh/display + walker waitCalm), defense re-verified | probe_h7r_d7defense.json; the live world no longer contains a degenerate cell (H8's guard) |
| walker PASS rule | SOUND, no changes (as H10 concluded) | formal walk 10/10 |
| H10 item 5 (engine cell4) | FIXED engine-side by H8 | n_cells=4, seal_refusal fields, no cell4 in the walk table |
| H10 item 6 (per-IP bucket co-tenants) | server budget raised 600->1200/min by H7 + page self-backoff; fleet staggering still advised | server.py comments; D6 |

H9 `H9_AUDIO/AUDIT.md` (sound debt):
| item | verdict | evidence |
|---|---|---|
| 1 pressEnd unwired (SHIP-BLOCKER) | FIXED by H7r | A3 above |
| 2 canvas-click payload never parsed (SHIP-BLOCKER) | FIXED by H7 (postTouchRetry parses; applyTouch carries body.hit), verified | accept_h7r_e4.json: foot click -> engine hit y=0.211 -> FOOT band; torso click -> hit y=4.479 -> BODY band; hits distinct |
| 3 lesson-switch wokeMemo re-fire | FIXED by H7r | A5 above |
| 4 snd() zero failure visibility | FIXED by H7r | A6 above |
| (5) 5-cell world vs 4-entry region map | MOOT | the world is the clean 4-cell creature now |
| (6) inherited-world start sounds | LEFT (minor polish, not in this lane's list) | named for the sound lane |

## ACCEPTANCE RESULTS

- (a) every defect classified: table above. NONE left unclassified.
- (b) `accept_h7r_b_e.json`: L1 "you pressed, the cell woke..." / L2 "a gentle hand..." /
  L3 "you let go..." — 3/3 PASSED on real SPACE-rail input, all distinct.
- (c) after_verify D4 + D5: drag/track/arrows all reach ~6000, label `6000 N`, meter
  11.11%, wire-captured force_n=6000; the_gentle_hand PASSED on that recorded press.
- (d) after_verify D3 (5 cycles, drag-out, alt-tab: zero sticks) + A3 (the press voice
  ENDS on release through every funnel).
- (e) accept_h7r_e4.json (see H9-2 row).
- (f) `soak_h7r_10min.json`: 10.10 min, 85 gentle interaction beats, 0 console errors,
  0 page errors, 0 429/5xx.
- (g) THE FORMAL WALK (`formal_walk/verdicts_walker.json` +
  `formal_walk/walk10_formal_console.txt`): **FRESH PASSES 10 of 10, PAGE ERRORS: 0 (zero)** — every row honest: the_heavy_hand/the_cascade/the_graduation passed
  their release-calms (calm after 8.1 s, final |P| all 0), the_stand armed=true with the
  root settled at 9.5 mm, no cell4 anywhere in the table.

## Engine-side findings (for the record; engine never restarted, never touched directly)

1. The clean guarded 4-cell world holds under the whole lane: n_cells=4, all P=0 at rest
   through every probe; the 1.62 GPa cell4 never appeared.
2. The engine's touch picker resolves canvas clicks in ITS OWN camera — `/api/cam`'s
   echo reports pan-relative zeros, so pixel-aiming from that echo needs a measured
   +4.65 world-Y offset (documented in accept_h7r_e3/e4). Calibration note, not a defect.
3. `/tick_state`'s force_l/force_r stay 0 during an active page press — if a future agent
   wants an engine-side phantom-press indicator, that field is not it.

Shell 8206 was restarted ONCE after all tests (kill BY PID 20260 only), loading server.py's
budget/env hardening; post-restart smoke: fixed page served, judge line live, world
[0,0,0,0] n_cells=4, zero errors (probes/smoke_after_restart.js).
