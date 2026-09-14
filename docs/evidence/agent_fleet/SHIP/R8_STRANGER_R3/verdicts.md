# R8 STRANGER TEST — ROUND 3 — Blind Judge Verdicts

Date: 2026-09-13/14 (~23:52-23:54). Branch: astra/tasks/matter-kernel-format-01.
Agent: R8-rerun, fleet 3.

Round 3 re-runs the stranger test after round 2 named the remaining gap: "I
know what it is, but the playable demo isn't there yet." Since round 2 the
named fixes were already in the pack (trailer, blood-panel pair, beauty shots,
ten-lesson arc live) — this round's change is the CONDITION: the judges were
given the actual 28 s trailer MP4 in their media folder, not just a storyboard
of it, and both extracted and examined frames from it themselves.

Prior rounds: `../R8_STRANGER/verdicts.md` (round 1: FAIL, no/no, 3/10, 3/10)
and `../R8_STRANGER_RERUN/verdicts.md` (round 2: FAIL, no/no, 5/10, 4/10).

## Method

Same protocol as rounds 1-2. Two blind judge sessions, neither had ever seen
this project: fresh headless `codex exec` sessions (gpt-6-astra, ChatGPT auth,
codex-cli 0.154.0, sandbox workspace-write, approval never), each started in an
isolated temp workspace OUTSIDE the repo (`C:/Users/allen/AppData/Local/Temp/
r8_r3_judge1|2/`), containing only neutral-named media + the pitch + the same
4 questions as every round. No project files, no manifest, no descriptive
filenames, no web. Both judges ran in parallel; neither saw the other's
answers. Prompt text preserved at `prompt_judge1.txt` / `prompt_judge2.txt`
and `<temp workspace>/prompt.txt`; console logs at `judge1_session.log` /
`judge2_session.log`.

The media shown (composition recorded for reproducibility; names shown to
judges were neutral):

- img_01..03 — beauty shots (hero front 3/4, mirrored, wide)
- img_04..05 — the blood-panel PAIR: rest (all cells 0.000 MPa), then
  mid-press (torso P=1.270 MPa), same camera, 1 s apart
- img_06..08 — trailer keyframes (press peak / healing / end card)
- img_09 — lesson 2/5 "THE GENTLE HAND" PASSED moment
- clip_01.mp4 — the full 28.04 s trailer (`chimera_trailer.mp4`, 1920x1080)

The prompt said the video was part of the media and to examine it if their
tools allowed. BOTH judges independently found cv2 available and extracted
12 frames each spanning the full 0-28 s (`video_frames/frame_00..11.jpg` in
their workspaces) and viewed them. This is a first for the stranger test:
rounds 1-2 judged stills only.

Integrity check: codex persisted transcripts
(`C:/Users/allen/.codex/sessions/2026/09/13/rollout-2026-09-13T23-52-35-01a09e42-*.jsonl`)
contain exactly 21 `input_image` entries per judge (9 stills + 12
self-extracted trailer frames) — both judges verifiably viewed all 21 before
answering.

One anomaly, recorded honestly: judge 2's answer cites `the "~1 fps" capture
note`. That string appears NOWHERE in its inputs — not in the prompt, the
media filenames, the JPG metadata, or the MP4 tags (checked: ffprobe shows
only generic Lavf encoder tags). The judge apparently INFERRED the ~1 fps
source capture from the stepwise held-frame motion visible across its
extracted frames and misattributed it to a "note" — a hallucinated citation.
The inference itself is factually correct (the trailer was captured at ~1 fps
and time-remapped to 24 fps, per D2's manifest, preserved at
`media/PROVENANCE_manifest_agent_D2_NOT_shown_to_judges.md`), but the citation
is not evidence-backed and is discounted as such.

Pitch shown (verbatim, `pitch.txt`, identical all three rounds):

> CHIMERA — a creature of water and skin. Press it, and the physics answers.
> $14.99
> physics sandbox / teaching game

## Judge 1 — VERBATIM (`judge1_final.txt`)

1) What do you THINK this game is?

> A guided physics toy where you press a monkey-shaped, fluid-filled body, watch pressure readings change, and complete lessons about deformation and recovery. It looks like an early technical prototype.

2) Would you pay $14.99? (yes/no/maybe + one sentence why)

> **No.** The media shows too little variety or satisfying visible interaction to convince me I'd stay interested.

3) What is missing that would make it a yes?

> A playable demo showing responsive deformation, varied experiments and meaningful challenges beyond pressure thresholds, plus cleaner character geometry and more readable UI.

4) Rate 1-10 how novel it looks.

> **4/10.** The fluid-pressure teaching angle is distinctive, but the visible experience mostly looks like poking a model while numbers change.

(Preceded by: "Viewed all nine images and 12 extracted frames spanning the video.")

## Judge 2 — VERBATIM (`judge2_final.txt`)

1) What do you THINK this game is?

> A guided physics experiment where I press a monkey-shaped, fluid-filled body, watch pressure readings change, and let it recover. It looks like an early simulation demo with lessons.

2) Would you pay $14.99? (yes/no/maybe + one sentence why)

> **No.** The media shows too little variety or satisfying interaction to convince me I'd stay interested beyond briefly poking it.

3) What is missing that would make it a yes?

> A playable demo showing responsive deformation, varied experiments and meaningful challenges beyond reaching pressure thresholds. Cleaner character joints and more readable UI would help; the "~1 fps" capture note also leaves responsiveness unproven.

4) Rate 1-10 how novel it looks.

> **5/10.** The fluid-pressure teaching angle feels unusual, but the visible experience—pressing a mostly stationary model and watching numbers—doesn't yet look especially distinctive.

(Preceded by: "Viewed all nine images and 12 extracted frames spanning the video.")

## Summary

STRANGER TEST ROUND 3: FAIL — both judges say NO at $14.99 (Judge 1: no,
novelty 4/10; Judge 2: no, novelty 5/10). PASS required both yes/maybe AND
novelty >= 6.

Honest read, no spin:
- 0 of 2 judges would pay, for the third round running. Novelty 4 and 5
  against a bar of 6 — the same as round 2's 5 and 4 (swapped), i.e. FLAT.
- The round-2 diagnosis is confirmed, not moved. Both judges again correctly
  identify the product (no confusion remains — that was round 1's defect and
  it is fixed), and both again refuse on the same three grounds: no playable
  demo with satisfying responsive deformation, no variety beyond pressing
  body parts to pressure thresholds, and unpolished geometry/UI.
- The new condition (judges handled the actual MP4 and pulled 12 frames from
  it themselves) did NOT help. Judge 2 examined the trailer knowing it was a
  video and still concluded responsiveness is "unproven" — and its inferred
  ~1 fps attribution is, per the real capture method, TRUE. A ~1 fps
  time-remapped trailer answers "the creature never moves" for a STILL judge
  but cannot prove satisfying motion to a judge who looks at the frames'
  stepwise motion. The motion evidence as shipped does not clear the bar it
  was built for.
- Convergence check: the two judges' answers are near-identical in structure
  and wording again (as in rounds 1-2) — independent sessions reaching the
  same three demands is the pattern's strongest signal. The gap is the game,
  not the explanation, and no amount of stills or remapped footage has moved
  it in two rounds.
- Condition caveat: both judges judged via extracted frames, not fluid
  playback; no judge in three rounds has seen smooth real-time motion. But
  round 3's result bounds the value of that fix alone: a judge who KNOWS it
  is video and reads its true capture rate discounts it. The next lever named
  by both judges is a PLAYABLE DEMO (or footage at real frame rate showing
  responsive deformation), not more packaging.

## Delta vs rounds 1 and 2

| Defect | Round 1 (stills only) | Round 2 (+ media pack, storyboard) | Round 3 (+ actual MP4, judges extracted frames) | Moved? |
|---|---|---|---|---|
| knows what it is | NO — "what even is this" | YES — correct full identification | YES — correct full identification, unchanged | moved in R2, held in R3 |
| motion | "basic model viewer with a denting effect" | arc reads, "subtle" / "poking while numbers change" | "pressing a mostly stationary model"; trailer examined and discounted, responsiveness "unproven" (~1 fps inferred) | NO — flat R2→R3, trailer did not clear it |
| variety | "varied experiments or challenges" | "varied experiments beyond pressing body parts" | "varied experiments and meaningful challenges beyond pressure thresholds" (both) | NO — same demand, third round |
| polish | "joint seams", "early prototype" | "rough-looking joints" | "cleaner character geometry/joints and more readable UI" (both) | NO — same demand, third round |
| teaching payoff | missing | "lessons" identified; angle "intriguing" | "lessons" identified by both; not enough to buy | held at R2 level |
| novelty | 3/10, 3/10 | 5/10, 4/10 | 4/10, 5/10 | FLAT R2→R3 (mean 4.5 both rounds) |
| pay at $14.99 | no, no | no, no | no, no | unchanged, three rounds |

Single-sentence delta: round 3 gave the judges the trailer itself and they
used it — and the verdict did not move — so the evidence pack is now formally
exhausted as a lever: what remains is exactly what both judges and both prior
rounds name, a playable demo (or genuinely real-time footage) with satisfying
responsive deformation, variety beyond pressure thresholds, and polish.
