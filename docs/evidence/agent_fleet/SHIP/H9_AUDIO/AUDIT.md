# H9 AUDIO-AUDIT — W4 sound wiring (commit ee249856) at HEAD 569083bb

Auditor: fleet agent H9 "audio-auditor". READ-ONLY lane: no tracked file edited.
Served files verified byte-identical to the worktree (`servedMatchesWorktree: true`);
the instrumented sound.js copy was delivered by Playwright route interception only.

Method: static read of `tools/game_shell/sound.js` (458 lines) and every
`snd(`/`ChimeraSound` call site in `tools/game_shell/index.html` (1809 lines), then a
headless live run (channel:'chrome') against the LIVE stack (site 8206 -> engine 8107)
with the instrumented local copy wrapping every public ChimeraSound method from inside
the module IIFE (logging only). World interaction kept light: one scripted SPACE
press-hold (~2.5 s, 20 kN -> 34 kN) on lesson 1, one mid-hold lesson switch, one
release + rest, one second press cycle, one canvas-click probe. Zero 429s incurred,
zero console errors caused.

---

## 1. STATIC AUDIT — event source -> code path -> data carried -> failure visibility

| # | Site (index.html) | Event source | Data carried | Failure visibility |
|---|---|---|---|---|
| 1 | SPACE press (line 1341) | keydown ' ', guarded `e.repeat`, inside `postJSON(/api/touch_hit).then` | `Number(force) + touchTarget` — the lesson target SNAPPED to the nearest mesh vertex (`snapToVertex`, line 1292). Real world point. | ZERO — `snd()` try/catch (line 398); also `res.ok` here is the fetch Response's ok, and the engine answers HTTP 200 even for `{ok:false}` payloads (http_server.cpp:202), so a REFUSED press still sounds |
| 2 | Gamepad A press (line 1375) | pollGamepad rAF poll, A-held edge | `f (RT analog) + touchTarget` — same real snapped point | ZERO — worse: no response check at all; press sound + `holding=true` fire unconditionally |
| 3 | Canvas click (tryTouch, line 1465) | pointerup after a still click; engine-resolved hit from the cam-form /tick_touch response | `res.hit` — **ALWAYS `undefined`**: `postJSON` returns the raw fetch Response (line 595), the payload is never parsed, and a Response has no `.hit`. The engine's real hit `{"ok":true,"hit":[x,y,z]}` (main.cpp:1240) never reaches the synth | ZERO — plus `res.ok`/`res.error` read off the Response, so even a "the ray misses the body" refusal (HTTP 200) sets `holding=true` and plays the press voice |
| 4 | Force slider mid-hold (line 1530) | `#force` 'input' event while `holding` | `Number(force)` only; `press()` keeps the held region and retargets with an 80 ms glide (sound.js:322-331). Never stacks | ZERO |
| 5 | Wake whoosh (judgeState, lines 1149-1159) | /api/state poll (700 ms), per-cell false->true crossing of `signedP >= WOKEN_PA` (20 kPa), memo `st.wokeMemo['cell'+i]` | none (non-spatial swell by design) | ZERO; memo is per-LESSON state, so a lesson switch re-whooshes an already-awake cell (live-confirmed) |
| 6 | Heal shimmer (line 1235) | judgeState release phase, first poll where EVERY cell `|P| < 1000` Pa (line 1232), just before `passed()` | none (quiet reward by design) | ZERO; starves whenever the world never goes calm — exactly the phantom-press state |
| 7 | init + ambient (enterPlay, lines 1572-1573) | PLAY click / Enter on name field — a real user gesture | none | ZERO — and if sound.js never loaded, `window.ChimeraSound` is absent and everything above is a silent no-op |

Non-W4 sites (pre-existing W1 wiring, all through `snd()` now): `cellWake` at goal latch
(line 1217), `passed()` (lines 508/528/1223/1236), `saved()` on manual save (line 1554).
`pressEnd` — **no call site anywhere** (`grep -c pressEnd index.html` = 0;
`git log -S pressEnd -- index.html` = empty): the only synth method with no caller.
sound.js's own contract (sound.js line 11: "touch released : ChimeraSound.pressEnd()")
is not honored by the page.

The guard: `snd()` (index.html:398) = window guard + try/catch, comment says the
failure mode is "silence, never a dead page". That is exactly what the live run
measured — and it means a permanently broken synth has NO visibility at all: no
console output, no telemetry, no state anywhere.

---

## 2. LIVE AUDIT — instrumented run (h9_live_audit.json, h9_click_probe.json)

World state at start: `[0, 0, 0, 0, 0]` Pa (clean). AudioContext count: **0 at load
-> exactly 1 after the PLAY gesture -> still 1 at session end**; ctx.state
`running` at every synth call. Served sound.js == worktree == HEAD.

Event log (t relative to first sound; full log in h9_live_audit.json):

```
    0 ms  init          ctx=running
    1 ms  ambient(true) ctx=running                        <- bed fades in under the greeting
10103 ms  press   [20000, [0, 4.444, 0.7]]  region=body   <- SPACE: real snapped torso vertex
10676 ms  wakeWhoosh  (exactly 1 across ~3 held polls)  <- crossing memo holds
10676 ms  cellWake                                  <- latch chime (same poll)
10802 ms  press   [34000]                   region=body   <- slider mid-hold retarget, no stack
12076 ms  wakeWhoosh + cellWake                     <- SPURIOUS: lesson switch ('3') while cell still awake
18392 ms  healShimmer                               <- release-phase calm after ESC + rest
18393 ms  passed
18576 ms  press   [34000, [0, 4.516, 0.309]]            <- 2nd press cycle still fires page-side
```

- pressEnd: **never called**; internal state after ESC release: `pressVActive: true,
  region: "body"` — the press voice (looping noise + oscillator) is still alive after
  the hand opened. The press tone is a monotone-on: once the first press lands it
  drones for the rest of the session; every later press merely retunes it.
- Canvas click (h9_click_probe.json): press fired, `args[1] = "undefined"`, region
  fell back to default `body` — the claimed engine-resolved hit is never carried.
- Broken-synth context: `ChimeraSound.press` replaced by a thrower -> `press-THREW`
  logged, game path unharmed (`holding=true`), **zero console errors, zero page
  errors**. A dead synth is indistinguishable from a healthy one without
  instrumentation.
- Run 1 also serendipitously demonstrated inherited-world audio: a second fresh page
  over an still-squeezed world latched `goalMet=true phase=release` on its first poll
  — latch sounds fire without the new player touching anything (lessons load at PLAY,
  so the memo can only latch post-gesture: the new player gets instant, unearned
  chimes, and never hears the crossing whoosh that was skipped before they arrived).
- Not audible-tested: headless Chrome has no listening device; what is proven is
  wiring, counts, real-time graph state (`running`), and data carried.

---

## 3. VERDICT PER CALL SITE

| Site | Verdict | Evidence |
|---|---|---|
| 1 SPACE press + region hint | **LIVE-OK** | fired with real snapped world point `[0,4.444,0.7]`, region `body` correct for torso; caveat: refusal-invisible (Response.ok, engine 200-always) |
| 2 Gamepad press + region hint | **LIVE-OK** (static; no gamepad headless) | real hint, but fires unconditionally — lies on refusal |
| 3 Canvas click + engine hit | **FIRES-BUT-WRONG-DATA** | `res.hit` always undefined (fetch Response, payload never parsed); every click sounds `body`; water clicks sound as presses and hold |
| 4 Force-follow mid-hold | **LIVE-OK** | retarget entry `[34000]`, region kept, no voice stack |
| 5 Wake whoosh memo | **FIRES-BUT-WRONG-DATA** (over-fires) | core crossing memo WORKS (1 per crossing across polls); but lesson-scoped memo re-fires whoosh+cellWake for an already-awake cell on lesson switch (1->2, live), and the loop spans 5 cells while the world's 5th is a degenerate zero-volume sliver (ylo=yhi=0.338, V=4.7e-9) whose P spikes (1.62 GPa in walk10) would whoosh untouched |
| 6 Heal shimmer on release heal | **LIVE-OK** | fired on first all-calm poll; but starves whenever the world never calms (press-pipeline defect) |
| 7 init + ambient in PLAY gesture | **LIVE-OK** | 0 -> exactly 1 AudioContext, created inside the gesture, running; ambient call verified |
| (unclaimed) `pressEnd` | **DEAD-CODE** | zero call sites, never wired in any revision; release is silent AND the voice never stops |

---

## 4. THE REAL QUESTION — what the broken press pipeline silences vs what remains

**Goes silent (or lies) under the CURRENT press-pipeline defect, and VANISHES with
H7's fix:**
- The shimmer/passed arc of every `then_release` lesson (7 of 10) — release-phase
  calm is unreachable while a phantom press holds GPa residuals; walk10 starved
  lessons 7 and 10 exactly this way. Live run proves the arc fires the moment the
  world actually calms.
- Latch chimes (`cellWake`/`passed`) for any lesson whose target press never lands
  because the pipeline stuck after the first press — the world never crosses the
  bar, so the judge never sounds it.
- The press voice's HONESTY: while the pipeline sticks, audio keeps claiming
  "pressing" (page-side events keep firing — live-confirmed 2nd press fires) over a
  world that stopped answering. Sound actively lies during the defect rather than
  going silent.

**Remaining after H7's fix — the sound lane's own debt (NOT fixed by H7):**
1. **pressEnd never wired (major).** `clearTouch()` — the single funnel for every
   release (ESC, letgo button, rest button, mouseup, pointercancel, gamepad release,
   payoff ceremony) — never calls it. First press starts a voice that never stops;
   releases are mute; the "150 ms natural release decay" (sound.js:364) is dead code.
   The smoke missed it because probe_sound_w4.js line 77 calls `S.pressEnd()`
   directly instead of releasing through the page.
2. **Canvas-click hint is always undefined (major).** `tryTouch` reads `res.hit`
   off a fetch Response; the payload is never parsed and the engine always answers
   HTTP 200, so refusals are indistinguishable and every click press sounds `body`.
   Fix shape: `res = await postJSON(...).then(r => r.json())` (or parse), then use
   `res.ok`/`res.hit` — this also stops water clicks from sounding and holding.
3. **Lesson-switch double-fire (minor).** Per-lesson `wokeMemo` re-whooshes (and
   re-chimes) an already-awake cell on lesson switch; make the memo world-scoped
   (or suppress the latch chime when `goalMet` latches on the first poll of a
   lesson with no fresh crossing).
4. **5-cell world vs 4-entry region map (minor).** sound.js CELL_REGION/FALLBACK_BANDS
   assume 4 cells; live /api/state reports 5, cell 4 a zero-volume degenerate band
   that can spike the whoosh loop. Either filter zero-volume cells or extend the map.
5. **Inherited-world start sounds (minor).** Entering a world that is already awake
   yields instant unearned latch chimes and a permanently missed crossing whoosh;
   the crossing memo has no pre-gesture baseline concept.
6. **Zero failure visibility (by design, still a gap).** `snd()` swallows everything;
   a synth that throws or a sound.js 404 is undetectable without instrumenting
   internals (proven live). One dev-mode `console.warn` per distinct failing method
   would keep the guarantee while making silence diagnosable.

## 5. IS SOUND PRODUCT-READY?

Not yet. The W4 wiring is real and its six claims are individually honest — every
claimed call site exists, fires on the real event, and the AudioContext discipline
is exactly as claimed (0 -> 1, lazy, in-gesture). But a player's first press begins
a tone that never stops for the session (pressEnd unwired), canvas presses always
sound "torso" no matter where they click and cannot hear a refusal, and lesson
switches can chime for cells nothing new woke. Items 1-2 are ship-blockers for a
sound lane claiming "the creature has four voices"; 3-6 are polish. Items marked
"vanishes with H7" should be re-audited after the press-pipeline fix lands — this
audit's live-run machinery (h9_audit.js) is reusable for that pass as-is.

## FILES
- `h9_audit.js` — main instrumented live run (route-intercepted sound.js copy)
- `harness_snippet.js` — the in-IIFE wrapper injected at the module export block
- `sound_instrumented.js` — the exact instrumented copy served during the run
- `h9_live_audit.json` — full results: verdicts, event log, timeline, judge lines
- `h9_click_probe.js` / `h9_click_probe.json` / `05_canvas_click.png` — call-site-3 probe
- `01_boot.png` .. `04_lesson_switch.png` — run screenshots
