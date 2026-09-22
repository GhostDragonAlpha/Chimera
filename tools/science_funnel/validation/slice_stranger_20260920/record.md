# Rule 0 record — THE STRANGER PASS, lane slice-stranger-20260920

Lane: `lane/slice-stranger-20260920`, branched from `lane/mesh-parse-20260920`
@ `7d7868d3b80d3ef3bf514eabbfd035dc8b741b46` (verified: the commit was fetched
from the canonical origin and `git branch` points the worktree at exactly that
hash; the lane carries the real-body slice WITH the 2-second cached boot).
Worktree: `E:/ChimeraWork/buffy-stranger-20260920` (a NEW worktree of
`E:/PythonChimera`; no other worktree touched). Engine port law 8127 is the
slice server's own refusal-by-code; only this lane branch will be pushed.
Git trailer on this lane's commits: `Agent: stranger`.

## THE THEORY

**STATEMENT** (someone could disagree): the playable slice as it stands is a
developer instrument, not a place a stranger can land in; the missing piece is
NOT more engine, more mock retirement, or any physics work — it is an ON-PAGE
stranger layer (plain-words guidance naming what this is, what it does, and
every key, written into the page itself), a keyboard path for every control
(the mouse-through-automation is unreliable law; every control needs its key
path), and a clean restart path — and with only that, plus the error-beacon
pattern the repo's web work already uses, a person who has never seen this
project can go from launch to a deliberate action unaided, and a scripted
headless stranger (Playwright, channel 'chrome', never the shared desktop)
measures it: boot, first understood control, first action, restart, zero
console errors.

**PREDICTIONS** (not yet measured by anyone):

- P-GUIDE: a stranger's first minute is spent on the page, not in a manual.
  Concretely: the page carries (1) a plain-words WHAT-IS (what the creature
  is, what is real, what is named mock), (2) a WHAT-TO-DO line for the one
  objective, and (3) a CONTROLS block naming EVERY key with its effect — and
  the scripted stranger's first deliberate action can be driven purely from
  what the page says (the walkthrough reads only what the page shows).
- P-KEYS: every control the page names is reachable by a KEY alone: action
  keys 1/2/3, the objective key G, restart R, save S, camera orbit
  ARROWS, zoom +/-. A key path exercises the SAME handler the button path
  exercises (no parallel logic), and a keydown that reaches no handler is a
  recorded finding, not a silent swallow.
- P-TIME: on the cached-boot base (the lane's own measured 2.08-2.10 s
  t_first_verts), a stranger crossing the page lands: first rendered motion
  quickly after page load, first UNDERSTOOD control (the page has told them
  what to press) shortly after, first deliberate action within the mission's
  60-second bar from launch. Any step over its budget is a FINDING, recorded
  and reported — not tuned away.
- P-RESTART: restart is clean: one key, the page tells the stranger what is
  happening, and the world comes back to the standing start with the same
  determinism the bank already holds (scene sha == the payload pin).
- P-CLEAN: zero console errors for the WHOLE scripted session — the repo's
  own error-beacon pattern (Playwright console+pageerror capture with a
  zero-error assertion, as the game-shell probes use) applied across boot,
  action, fall, and restart.

**FALSIFIERS** (named before any code; any one failing = the theory loses,
the RED is recorded and reported, not tuned):

| id | class | pass condition |
|----|-------|----------------|
| F-STRANGER-60S | the mission's own bar | the scripted stranger reaches a deliberate action with no external help in under 60 s from launch (launch = the slice server answers /api/health; the walkthrough script reads ONLY what the page shows it) |
| F-KEYS-NAMED-WORK | every control has a key path that works | every key named on the page is pressed by the walkthrough; each press reaches its handler (server/endpoint effect observed) within 2 s; the key list on the page and the key list the walkthrough exercises are the same list (compared mechanically) |
| F-BEACON-SILENT | zero console errors, whole session | the error beacon (console 'error' + pageerror, repo probe pattern) records zero entries across boot, understanding, actions, fall, and restart |
| F-RESTART-CLEAN | one-key restart, world returns | after R: page shows the restart notice; the world returns to the standing start (engine answers; carry state cleared; scene sha == the payload pin bc9033bf… recorded in the boot record) |
| F-TIMELINE-HONEST | the timestamps exist and are reported, whatever they say | the walkthrough artifact records wall-clock timestamps for t_server_up, t_page_load, t_first_motion (first /api/verts payload rendered — measured as the first successful verts render, the bank's own definition), t_understood (guidance visible + controls named), t_first_action, t_restart_done; over-budget steps are reported as FINDINGS, not tuned |

3-run determinism: the walkthrough runs 3x; per-run timestamps are
wall-clock (real time, honestly reported, expected to vary); verdicts and the
key-list comparison must be identical across runs.

## DERIVED, NOT TUNED (Rule 1)

- The 60-second bar is the MISSION's named bar, not this lane's taste.
- The 2-second key-press effect bar is this lane's instrumentation of
  "the visitor can act" (a key whose effect takes longer than that is not
  experienced as the key doing anything); it is recorded as a named bar in
  this prereg, before any measurement.
- The key scheme (1/2/3, G, R, S, ARROWS, +/-) derives from the slice's OWN
  five controls (send, stop, fall, restart, save) — one key each, plus the
  camera/press paths the page already owns. No new gameplay is invented; no
  engine route is added; no mock is renamed or retired (that is other lanes'
  law — this lane only NAMES what the registry already declares).
- The beacon is the repo's own pattern (playwright console+pageerror capture,
  zero-error assertion) pointed at this page; no new telemetry scheme.

## RUN PLAN

Prereg (this file, committed FIRST) -> implement the on-page stranger layer +
key paths + beacon + restart polish in tools/playable_slice/index.html and
one small server addition (no-console-error restart gap) -> the scripted
stranger walkthrough (Node + playwright-core, channel 'chrome', private
headless) -> 3 runs -> artifacts in THIS directory -> receipt.json with
per-falsifier verdicts -> push ONLY lane/slice-stranger-20260920.

Receipt: `tools/science_funnel/validation/slice_stranger_20260920/receipt.json`.

Agent: stranger
