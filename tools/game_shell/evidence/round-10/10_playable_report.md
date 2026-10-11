# Round 10 — FEEL THE MUSCLE on the rebuilt engine: playable acceptance

Date 2026-10-10. Stack: engine :8110 (rebuilt binary, tendon endpoints
live) + shell :8210, both launched by tools/science_funnel/run_creature.ps1
and LEFT RUNNING. Foreign PID 71636 :8117 untouched. All browser evidence
from a VISIBLE Chromium (Playwright, headless=False) driven by
_drive_r10_playable.py; numeric probe by _probe_r10_proxy.py.

## 1. Stack — PASS
- GET :8110/state live (particles); GET :8110/tick_state exposes
  tendon_armed/severed/q_deg/F_n/battery_J (+work/heat/elastic) — the new
  binary is live (the old one had no tendon fields).
- GET :8210/ → 200. Shell proxies /api/state→/tick_state,
  /api/effort→/tick_effort, /api/sever→/tick_sever (server.py:178,286-294).

## 2. Numeric probe THROUGH THE SHELL PROXY (:8210) — PASS (a–e)
Full numbers: 10_probe_proxy.json (fresh run this session).
- a PASS: /api/state carries all 10 tendon_* keys.
- b PASS: /api/effort u=1 → q crossed 40° at t=0.207 s, qmax=117.68°,
  battery min 987.19 J (< 1000).
- c PASS: /api/sever → tendon_severed true; q 120.87° → −44.99° (< 5).
- d PASS: u=−1 → armed false; /api/pose knee_L 40 → ok:true.
- e PASS: 100 rapid /api/effort ramp posts → all HTTP 200, zero 429s.

## 3. Browser gameplay, lesson 6 — PASS
Real UI only (mouse drag, clicks, keyboard). Screenshots:
10_before_contract.png / 10_contracted.png / 10_severed_passed.png.
- PLAY → gameplay started (#screen-play.on true).
- Lesson 6 reached by 'q' AND by the lesson list (next ×5): both show
  'FEEL THE MUSCLE' 6/12.
- Before: effort 0%, readout 'battery 999.9 J · knee 10.3°', verdict
  'the creature waits.'
- Slider dragged to 100% (value=100): q=134.1° (>40), battery
  999.9→978.0 J, readout 'knee 132.6° · armed'.
- SEVER button: readout 'knee −0.1° · SEVERED' (settled limp, q<5),
  verdict 'PASSED — you pulled the tendon with real energy, and watched
  the wish die when you cut it.' = the lesson's own pass_line.
- Disarm-on-switch: after switching to BEND THE KNEE, tendon_armed=false
  and its slider posted knee_L 40 (slider value 40) → PASSED.

## 4. 12-lesson regression — PASS (details 10_regression.txt)
- Every lesson card rendered title+body(>240 ch)+hint via keyboard:
  1-9 → lessons 1-9, 0 → 10, ']' (next) → 11 THE STAND, '`' → 12 THE
  GRADUATION, 'q' → 6 FEEL THE MUSCLE. 13/13 card checks ok, pageErrors=0.
  (Lesson 11 has no dedicated key by design; ']' is the keyboard next.)
- wake_the_cell e2e: belly pressed to 0.478 MPa (> 0.02), let go, calm →
  PASSED. bend_the_knee e2e: 40° posted → PASSED. Classic loop intact.

## 5. Defect found + fixed during acceptance (index.html)
- Sever-verdict race: the SEVER handler set its 'the tendon is cut' banner
  when the POST resolved; if the judge PASSED while that POST was in
  flight, the banner talked OVER the PASSED line (reproduced: verdict
  stuck at 'the tendon is cut' with st.passed true). Fix: handler
  re-reads curState() after the await and returns if already passed
  (index.html, effort-sever-btn click, RACE FIX comment). Verified by
  three subsequent full driver runs: PASSED banner always survived.
- Physics note (not a defect): after sever q OSCILLATES (dips < 5,
  swings to ~±70°, settles ~0° within ~3 s while armed+severed). The
  judge's q<5 window is transient by design; the limp screenshot waits
  for the settled frame (knee −0.1°).
- Harness repairs (this round's scripts): drag_slider signature crash;
  pose slider now pinned to exactly 40 (POSE_TOL_DEG honest-refusal);
  effort slider pinned to exactly 100 via native End; tendon preset runs
  under lesson 1 before any lesson-6 exposure so housekeeping can never
  pass lesson 6 by accident.

## 6. Evidence files
- 10_probe_proxy.json — probe a–e numbers (fresh run).
- 10_before_contract.png / 10_contracted.png / 10_severed_passed.png —
  visible-browser frames, verified by eye against the readout/verdict.
- 10_regression.txt — per-card results, readouts, flex/limp states,
  page_errors=0, full session log.
- _drive_r10_playable.py / _probe_r10_proxy.py — the drivers;
  _diag_sever_window.py / _diag_lesson6_trace.py — diagnostics used to
  pin the race.

OVERALL: PASS (items 1-4). Stack left running: engine :8110, shell :8210.

