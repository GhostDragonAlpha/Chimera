# R8 / R4 DRY-RUN RECORD — judge playbook executed by H5 (2026-09-14)

Method: executed `PLAYBOOK.md` in this directory exactly as a fresh agent —
extracted Appendix A verbatim (`judge_drive.js`, syntax-checked), ran it
headless Chrome `channel:'chrome'` 1440x900 against http://127.0.0.1:8206,
played blind from the rendered page only. 26 screenshots (`shots/`), full logs
(`session_log.txt`, `resp.jsonl`), 21 command files (`done/`). ~17 minutes
hands-on, 30 commands, zero crashes, initial load 416 ms.

**Honesty up front: I am NOT blind.** I am fleet agent H5; I know the project
exists and its vocabulary (press / lessons / heal) from commit messages. I did
not read the demo source, prior stranger-round evidence, or any product code
during the play portion. Every finding below is from what the page itself
showed. A real stranger may stall differently; the MECHANICS findings
(stalls 1, 2, 5, 6) are page behaviors, not knowledge artifacts, so they stand
regardless.

---

## THE STALL LIST (primary deliverable — what the page team should fix)

### S1 · BLOCKER — the hand sticks "pressing" forever after release
- Steps: lesson 1, press torso (mouse down 3 s, up). Immediately after `up`
  the HUD flips to **"pressing — 20000 N"**, judge line `holding=true`, and
  cell 1 jumps to 0.327 MPa (`08_released.png`, `09_recovery.png`).
- It persisted across a lesson change; clicking the visible **"let go"** chip
  did nothing (`c006`). Only **"stand at rest"** cleared it (`22_stand_at_rest.png`).
- Reproduced 3/3 times (after lesson-1 press, lesson-3 belly press, foot press).
- Buyer experience: "I let go but the world still thinks I'm squeezing it, and
  nothing I click — including the button that says *let go* — makes it stop."

### S2 · BLOCKER — the hand-strength slider cannot be operated
- Lesson 2 demands force under 8,000 N. Attempts, in order:
  1. drag from thumb at wrong y (431) — grabbed the label text instead
     (visible text-selection artifact, `11_lesson2_panel.png`) — the slider
     sits 20 px under its label;
  2. drag from thumb (1190,453) to (1140,453) — value stays **20000 N**;
  3. direct track clicks at (1140,453) and (1125,453) — unchanged;
  4. click thumb then 3x ArrowLeft — unchanged.
- The slider reads 20000 N in every screenshot for the whole session
  (`11`–`26`). Lesson 2's instructed action (a gentle <8000 N press) was
  **impossible to perform**.

### S3 · MAJOR — lessons pass without the asked action
- Lesson 2 flipped to **"PASSED — you felt the water. it was always there."**
  while I was fighting the slider — never having done a gentle foot press. The
  only ≥50 kPa event was the phantom press at 20000 N on cell 1 (not gentle,
  not a foot). Lesson 3 passed the same way: every visible cell read 0.000 MPa
  and the creature stood motionless, yet "PASSED" appeared (`20_after_pokes.png`).
- The pass copy for lessons 1, 2, 3 is the **identical sentence**, so the
  unearned passes are not even distinguishable from earned ones.
- Buyer experience: "the game grades itself, not me."

### S4 · MAJOR — after the first press, presses stop answering
- First press ever (lesson 1 torso): cell 0 spiked to **4.893 MPa** — instant
  pass. Every subsequent press delivered nothing: `lastTouchForce=0`, no cell
  moved within any read, no visual reaction — belly 2.5 s hold at 20000 N
  (`15_heal_press_hold.png`), chest poke, thigh poke, close-up foot press
  (`21_foot_press.png`), press after rest (`23_press_after_rest.png`).
- The landing promise — "touch it, and it answers" — held **exactly once**.

### S5 · MAJOR — no dent is ever visible, including on the press that worked
- `06_press_hold_3s.png` is mid-hold during the 4.893 MPa press: skin smooth,
  pose identical to rest. Zoomed presses (`15`, `21`) likewise. Lesson 3 says
  "watch the dent unwind" — there was never a visible dent to unwind.
- The body DOES move over time (by `24_after_orbit.png` it has sagged, arm
  dragged on the ground, lumpy strain patches), but the change cannot be
  attributed to any press — it reads as drift, not response.

### S6 · MAJOR — the "blood" telemetry reaches absurd numbers
- A foot cell read **87.496 MPa** while the creature merely stood
  (`12_slider_try.png`) — lesson 2's goal threshold is 0.05 MPa in the same panel.
- Later: cell 4 shows **V=0.000 m³ with P=1622.780 MPa**, and cell 2 goes
  negative (−0.009 MPa) (`23`–`26`). "conserve: -0.00 %" throughout.
- The lessons ask the buyer to steer by these numbers; they read as noise.

### S7 · MINOR — "the pose was refused." with no reason (lesson 4)
- Clicking the lesson's own "knee_L → 40°" chip was refused (`25_knee_chip.png`).
- Recovery found only by guessing: "stand at rest" FIRST, then the chip →
  PASSED, knee visibly bent (`26_knee_retry.png`). The at-rest requirement is
  never stated.

### S8 · MINOR — copy/labels
- Landing input: "your name (your camera's name)" — "camera" unexplained until
  after PLAY.
- Prominent dev telemetry in the buyer's face: `judge: wake_the_cell
  phase=goal goalMet=false passed=false touchTarget=set lastTouchForce=0
  holding=false` — internal jargon ("judge", "phase", "touchTarget") as UI.
- Ambiguous chip labels in YOUR HAND: "let go / hand open / standing at rest" —
  state display or buttons? (Both, it turns out; nothing says which.)

### S9 · INFRA — 1362 console errors in ~17 minutes
- Overwhelmingly `429 Too Many Requests` (the page's own polling exceeds its
  server's rate limit), plus one `ERR_NO_BUFFER_SPACE`. Zero page errors, no
  visible breakage — but the client hammering its own server into 429s will
  not survive ten simultaneous judges.

### What worked (credit where due)
- 416 ms load; landing copy made the first action obvious; lesson 1 teaches
  its interaction honestly and passes in seconds; lesson pager, wheel zoom,
  orbit drag, "stand at rest", the knee pose chip all function; the knee
  visibly bends and pass feedback exists (sometimes bespoke, e.g. "PASSED —
  and the body stands at rest again."); no crashes or freezes in 17 minutes.

---

## CAN A STRANGER REACH LESSON 3+ UNAIDED?

**Yes — comfortably.** Landing → name → PLAY → Begin is self-evident; lesson 1
is a clean tutorial and the pager arrows are discoverable. Reaching lesson 3
took under 5 minutes including the S1/S2 stalls. The stranger-test risk is not
navigation; it is that lessons 2+ pass without being played (S3) and the
core interaction dies after first contact (S4/S5), so a judge who plays
honestly sees a creature that stops answering and a scorecard that lies.

## PLAYBOOK VERDICT BLOCK (filled by H5 — NOT a blind judge, see honesty note)

### Buyer answers
1. **What is this?** — "A soft-body creature you press and poke, framed as a
   series of ten physics lessons — pressure cells instead of health bars. The
   first press felt genuinely alive; nothing after it did."
2. **Would you pay $15-20 for it?** — No. "The demo asks me to steer by
   numbers that hit 1622 MPa on a zero-volume cell, grades lessons I didn't
   play, and stops answering my touch after one try."
3. **What's missing?** — Visible response (dents) to presses; a strength
   slider that moves; honest telemetry; passes that reflect what I did; a
   stated rule for when poses are legal.
4. **What would you need to make it worth $25?** — "Every press answers
   visibly within half a second like the first one did, and the lessons only
   pass when I actually do them. If the creature reliably squishes and heals
   under my hand, that's a toy I'd pay for."

### Structured verdict
- PAY ($15-20): **no** (in this state)
- WOULD PAY $25: **no** (not yet — the first-press feeling is the $25 product; it currently happens once per session)
- NOVELTY: **8/10** — "I've never pressed a creature made of water before; closest thing is a stress toy, but with a physics gradebook."

### QUOTES
- "The first press felt genuinely alive; nothing after it did."
- "The game grades itself, not me."
- "1622 MPa on a zero-volume cell."

### Mechanics witnessed
- Lessons completed: 4 encountered, 4 passed (L1 genuine; L2/L3 passed
  unplayed; L4 passed after at-rest recovery guess).
- Press test: performed 6 times (torso, belly-zoomed, chest, thigh, foot,
  post-rest). First: 4.893 MPa spike + pass. Rest: `lastTouchForce=0`, no
  visible reaction. Releases left a sticky phantom press (S1).
- Stalls encountered: 9 (S1–S9 above).
- Page errors: none visible; 1362 console errors in log (429 flood).

### Honesty note
NOT blind — fleet agent H5, knows the project from commit messages; did not
read demo source or prior round evidence during play; findings are page-render
only.

## REPRODUCIBILITY VERDICT

`PLAYBOOK.md` alone was sufficient: setup, driver extraction (verbatim from
Appendix A, syntax-valid), session flow, stall definition, and verdict
template all executed without asking anyone anything. One setup gap was found
and already patched into the playbook (tooling check must run from the
scratch dir — module resolution is per-directory). Two judge-notes added
after the run: screenshots do not capture the OS cursor (touches will look
cursor-less in evidence), and judges may extend the driver's command set.
A second agent reading the playbook can run a judging session unaided.
