# HANDOFF — Fork 2 (evolved control), after RUN 35 FAIL

> Paste this into the next session. It is your orientation. **Verify every claim against
> disk before acting** — context restarts have already happened twice; disk is ground truth,
> not this prose.

## WHO YOU ARE / HOW TO ORIENT (do this first, in order)

1. Read `E:/PythonChimera/AGENTS.md` top to bottom. RULE 0 (state a theory before you build:
   STATEMENT + PREDICTION + FALSIFIER) and RULE 1 (derive it before you train it; no sweeps) are
   load-bearing. The rule index is the last section of `docs/THE_LAW.md`.
2. Run the live read, every time:
   ```bash
   python tools/orient.py            # engine tree + verdict ledger + git HEAD
   python tools/verdict.py status    # Rule-0 membranes, open + closed
   git log --oneline -8 && git status --short
   ```
3. You are the PHYSICS (rendering + workflow). The HUMAN side is operator + LM Studio vision. A
   proof is a dyadAnalysis: a number and a term, aligned. Build THROUGH the engine.

## WHERE WE ARE (as of HEAD `b6d000a`, 2026-08-23)

Goal chain (operator-approved): **translated → standing → walking → dressed**, one dyad per
milestone. M1/M2 were done in earlier runs (operator's eyes still pending on the images).
**M3 = walking is the active milestone, and it just FAILED.**

Fork 2 status:
- **F2-a — batched dynamics port: PASS** (RUN 32). Port matches reference.
- **F2-b — policy training harness + RUN 33 train**: built; RUN 33 label was wrong and is
  erratum'd in `docs/SESSION_LOG_2026-08-22.md` (true gen‑39 mean reward +0.5427, not +0.7076).
- **F2-c — official proof (policy as command source through the reference harness)**:
  - Harness equivalence is **PROVEN to sub-mm** after the Fn-lag fix (`tools/kernel_walk.py`
    'gait policy' mode): reference tracks port over the sweep, min gap 0.0 mm vs port 0.0068 mm,
    corridor-breach tick t=0.55 s on both. This part is SOLID — do not re-litigate it.
  - **But the bear FELL.** RUN 35 honest retrain: tilt maxed 63.4°, fell at t=0.72 s. The
    pre-registered no-fall bound was miscalibrated: the best policy is a *knife-edge sweep that
    passes X_R exactly as it breaches the corridor*. FALSIFIER FIRED AS WRITTEN.
- **OPERATOR VERDICT (2026-08-23): M3 = FAIL.** "I believe you that it fell … that's a fail."
  The walking milestone does NOT advance on this evidence.

### The diagnosis you must inherit (this is the important part)

Two distinct problems are now visible, and they are not the same:

1. **The reward is gameable.** `r = (BASE_GAP - min_gap)/BASE_GAP`, freeze on corridor
   violation — but min-gap is recorded *before* freeze, so a sweep-then-fall scores +1. The
   policy found exactly that exploit. Falling does not cost anything in the objective.
2. **Upright transfer is NOT yet proven physically achievable.** The hand-designed FSM gait
   (RUN 30/31) *also fell* — see `.tmp/run30_gait.log` and `.tmp/run31_gait.log`: both end with
   `M3-STEP-2: FALSIFIER FIRED -- gait wrong`, fallen=True, tilt max ~44.7° / ~50.5°. So we do not
   yet have evidence that ANY control (hand or learned) keeps the bear upright through a transfer
   with this physics + geometry.

Consequence: **the next step is NOT "retrain harder."** That would be retraining-to-fit, which is
forbidden. The honest successor is to fix what makes falling unprofitable AND establish that an
upright transfer is physically possible — in that order.

## WHAT TO DO NEXT (in this order; stop and report at each gate)

1. **Record the operator verdict** (append-only, do not rewrite): append to
   `docs/SESSION_LOG_2026-08-23.md` a short entry: M3 dyad presented 2026-08-23; operator verdict
   = FAIL (bear fell; walking milestone not advanced). Commit ONLY that file with the Agent trailer.
2. **Reconcile the live state.** `tools/orient.py` currently reports CURRENT TERM `theSeed` →
   next `theDeterminism`, and an OPEN membrane V62 (dirty-set grain sweep, a *rendering* concern)
   while HEAD is the RUN 35 walking commit. The engine-state store and the git narrative are
   tracking different workstreams. Figure out which term the walking work actually lives under
   (`theGait`/`theStand`/`theWalk` are all unchecked in the hierarchy) and reconcile — do not trust
   either source blindly, and do not silently "fix" V62; it is someone else's open membrane.
3. **Diagnose achievability (Rule 0 membrane, before any training).** Read RUN 30/31 gait logs in
   full and the physics params. State as ONE claim: *can an upright transfer be done at all with
   this physics + geometry?* Name a falsifier. If hand control cannot hold upright, the next fix is
   gait design / physics params — NOT policy retraining. Report to operator before spending a run.
4. **Pre-register reward v2 (Rule 0), then RUN 36 — conditional on operator sign-off.** The bar
   changes what "walking" means for the official proof, so it needs the operator's call. Candidate
   fix: make falling unprofitable — e.g. zero/negative reward if a corridor violation occurs ANYWHERE
   in the horizon (survival gate), so +1 requires pass X_R AND stay upright. Write the pre-registration
   block into `tools/kernel_walk.py` docstring AND a session-log entry BEFORE running, with the
   falsifier named up front. Same procedure as RUN 33/35 (E/mu/budget from that template — do not
   sweep; if you want to change a number, derive why first).
5. **Replay through the reference harness** once RUN 36 produces an honest best sample
   (`python tools/kernel_policy.py evaluate [npz]`), then filmstrip + referee. Equivalence is already
   proven to sub-mm, so transfer risk is low — this step is about the BEHAVIOR (does it walk upright),
   not about port-vs-reference drift.

## KEY ARTIFACTS & PATHS

- Harness: `tools/kernel_walk.py` — 'gait policy' mode (policy as ONLY command source; FSM/PD/brake
  bypassed; H=2.0 s, 50 ms ZOH), referee branch, pre-registration + RESULT blocks in the docstring.
- Trainer: `tools/kernel_policy.py` — `train()` now saves the ACTUAL best sample (old bug fixed);
  new `evaluate [npz]` mode measures a saved theta's true reward through a port episode.
- RUN 35 referee log: `.tmp/run35b_f2c.log`. FSM gait logs: `.tmp/run30_gait.log`, `.tmp/run31_gait.log`.
- Session logs (append-only): `docs/SESSION_LOG_2026-08-22.md`, `docs/SESSION_LOG_2026-08-23.md`.
- Trained policy npz: wherever `train()` writes it — check the save path in `tools/kernel_policy.py`
  (npz is gitignored; find the newest by mtime under `.tmp/`). RUN 35's honest best sample is the one
  to evaluate.
- Renderer (settled): C++ Vulkan engine, `ChimeraEngine/engine/engine.cpp`; render a rotation with
  `ChimeraEngine/cpp_bridge.py::render_teddy_movie`, encode MP4, judge with `senses.watch()` (Ollama
  qwen3.8, think:false). The dyad watches a MOVIE, not a still.

## WHAT NOT TO DO

- **Do not retrain to fit the reference.** Equivalence is already proven; changing the objective to
  make the port match the reference is forbidden and pointless here.
- **Do not touch the uncommitted UV/gsplat lane.** `git status` shows modified: `Chimera/docs/DREAM_REPORT.md`,
  `Chimera/docs/HERALD.md`, `Chimera/docs/HISTORY_BOOK.md`, `Chimera/docs/chimera_dna_graph.json`,
  `docs/THE_UV_METHOD.md`, `tools/gsplat` (submodule), `tools/uv_sheet.py`, and untracked
  `Chimera/docs/chimera_dna_graph.json.tmp`. Those are another lane's work. **Commit ONLY the files
  you actually changed for your task.** Never `git add -A`; never revert what you didn't change.
- **Docs are append-only** (session logs, THE_* docs). Append; do not rewrite history. A file existing
  is not proof — a compile is not proof (H-14); a verb needs behavior, not metadata (H-21).
- **Commit conventions:** pre-commit hook runs; include the `Agent:` trailer; commit exactly the files
  you touched. No force-push, no amend, no history rewrite.

## DOCTRINE REMINDERS (the part that keeps this honest)

- RULE 0: every new membrane gets STATEMENT + PREDICTION + FALSIFIER *before* the run. `port_test()`
  refuses to register a test with no falsifier. No falsifier, no build.
- RULE 1: derive before you train. A parameter sweep is an admission the derivation wasn't done. If a
  variant's only answer is "which number is best," STOP.
- `blocked` must be EARNED — give cause + evidence or run `core/solver.py`; bare `blocked` is forbidden.
- The human is one of the two legal terminals (the other is PHYSICS). An LLM is never a terminal.
  Refusing to ask about FUN is just guessing; refusing to ask about a MEASURABLE thing is right.
