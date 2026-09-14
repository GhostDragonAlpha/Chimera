# R8 — THE STRANGER TEST — Blind Judge Verdicts

Date: 2026-09-13. Branch: astra/tasks/matter-kernel-format-01.

## Method

Two blind judge sessions, run so that neither judge had ever seen this project:
each was a fresh headless `codex exec` session (ChatGPT auth) started in an
isolated temp workspace OUTSIDE the repo, with only a copy of the six screenshot
previews (`media/previews/*.jpg`) and the pitch text below. No project files, no
context, no web. Each judge was told to view every image before answering.

Pitch shown (verbatim, from `pitch.txt`):

> CHIMERA — a creature of water and skin. Press it, and the physics answers.
> $14.99
> physics sandbox / teaching game

Screenshots: 6 live captures from the running engine (127.0.0.1:8107) —
default view, high front, close side, back three-quarter, mid-press
(3x `tick_touch` at 30000 N on [0,4.5,0.35], captured before
`tick_touch_clear`), and level side. Full-res PNGs in `media/`, judge-size
JPEGs in `media/previews/`.

The trailer (`CHIMERA_PROOF/TRAILER/chimera_trailer.mp4`) did NOT exist after a
10-minute poll (30 checks x 20 s), so the judges saw stills only.

Note on mechanism: the first attempt used `claude -p` fresh sessions for both
judges; both failed with an expired OAuth token (see `judge1_claude_401.log`,
`judge2_claude_401.log`) and were replaced by the codex sessions above. One
screenshot (shot4) was retaken with a corrected camera angle during judging —
the first attempt had the camera below the floor plane and misrepresented the
renderer.

## Judge 1 — VERBATIM

1) What do you THINK this game is?

> A physics toy where you poke a clay-looking monkey and watch its body deform. The bare grid and visible joint seams make it look like an early prototype; the water simulation and teaching aspect aren't apparent.

2) Would you pay $14.99? (yes/no/maybe + one sentence)

> No — these screenshots don't show enough interaction, polish, or lasting appeal to justify $14.99 for me.

3) What is missing that would make it a yes?

> Gameplay footage showing satisfying deformation and fluid movement, varied experiments or challenges, a clear example of what I'd learn, and cleaner character visuals.

4) Rate 1-10 how novel it looks.

> 3/10 — the water-and-skin idea sounds unusual, but the images mostly look like a basic 3D model viewer with a denting effect.

## Judge 2 — VERBATIM

1) What do you THINK this game is?

> I think it's a soft-body physics toy where you press a monkey-like creature and watch it deform. The screenshots look like an early prototype; the water simulation and teaching aspects aren't apparent.

2) Would you pay $14.99? (yes/no/maybe + one sentence)

> **No.** $14.99 feels too high for what currently looks like one model on a grid with a small visible dent.

3) What is missing that would make it a yes?

> A gameplay video showing satisfying deformation and fluid movement, varied experiments or challenges, clear examples of what it teaches, and more polished visuals without the apparent gaps around joints.

4) Rate 1-10 how novel it looks.

> **3/10.** The water-and-skin premise sounds unusual, but the screenshots make it look like a fairly ordinary model-deformation demo.

## Summary

STRANGER TEST: FAIL — both judges say NO at $14.99 (Judge 1: no, novelty 3/10; Judge 2: no, novelty 3/10).

Honest read, no spin:
- 0 of 2 judges would pay; PASS required both yes/maybe with novelty >= 6. Novelty was 3/10 from both.
- Both judges converged on the same diagnosis independently: the stills read as a prototype model viewer with a dent effect; the "water" and "teaching game" halves of the pitch are not visible at all; joint seams and the bare grid read as unfinished.
- Both named the same missing pieces: motion/gameplay footage (satisfying deformation and fluid movement in a video — exactly what the missing trailer would have supplied), varied experiments/challenges, a clear teaching payoff, and cleaner visuals.
- Condition of the test: judges saw stills only because the trailer never landed within the 10-minute poll window. The convergence of both judges on "no gameplay footage" as the gap suggests the trailer is the single highest-leverage piece before any real store exposure, but this verdict is recorded as FAIL because that is what the evidence pack as shipped earned.
