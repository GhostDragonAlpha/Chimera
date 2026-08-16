# AGENT_PROTOCOL.md — the session contract for implementation agents

---

## ★ CURRENT TASK — do this (rewritten per stage by Kimi; read everything below first)

<!-- House rule: when a task completes satisfactorily, this file is updated the
     SAME day — this slot is cleared/rewritten AND any lessons the task earned
     (harness fixes, new gates, new flake patterns) are folded into the rules
     below, so the next agent inherits them instead of re-paying for them. -->

**LIVE TASK — Phase 11, Stage 2 of 3 (below).** Stage 1 verified complete
(baseline 96/96 green; derivation sheet `engine/scratch/_phase11_derivations.md`,
F-S1a/b/c all PASS; nothing to commit — verify-only stage, scratch is gitignored).

---

# SPIACE Phase 11, Stage 2 of 3: ship + atmosphere + re-entry physics (wire+prove)

**TASK:** Give the Phase 10 world a flyable ship with real propellant physics,
per-planet atmospheres, and re-entry heating — and prove it with F14, F15, F17.
Stage 3 (separate prompt, after this commits) flies the full arc + F16 + docs.

**STATE:** Browser engine green through Phase 10.5 (`test_phase6.py` 96/96,
Stage 1 baseline). **Every constant you need is already derived** in
`engine/scratch/_phase11_derivations.md` — constant index in its §8, with
chains. Do not re-derive; do not tune. If a number you need is missing from
that sheet, STOP and report the gap instead of inventing it.

**ARCHITECTURE (pinned — follow it):**
- The ship is an **integrated body, not a tree particle** — same precedent as
  the character (`stepCharacter`) and Phase 7 Lorentz: velocity-dependent
  forces live outside the tree. Its gravity is the **analytic 5-body sum**
  (star + 4 planet cores, positions live from the engine); the 500 tree
  particles are test-mass class and exert nothing on the ship.
- Ship state: pos/vel (f64, planet-local frames where the character uses
  them), `m_dry + m_fuel`, thrust `T = v_e·ṁ` with `v_e = 4412.992 m/s`
  (sheet §2.1). Integrator: symplectic Euler, same as the engine.
- Burn model closes the ledger (sheet §5): burning `dm` moves
  `ε_chem·dm` (20.257 MJ/kg) out of `E_chem`; `η = 0.481` becomes
  ship+exhaust mechanical KE, `(1−η)` becomes exhaust heat on the existing
  membrane heat ledger (`Σm·C_P·T` @~3427). Track exhaust KE carried away.
- Atmosphere per planet: `ρ(h) = ρ₀·exp(−h/H)` with the sheet §3 table
  (A: H=7922, ρ₀=1.3025 · B: H=11180, ρ₀=1.2695 · C: H=5051, ρ₀=1.4851 ·
  D: H=2924, ρ₀=1.6832 — heights above that planet's `heightAt` surface).
  Drag `F = ½ρv²C_dA` — `C_dA` is a stated ship constant, say so in a comment.
- Re-entry heating (sheet §4): `q̇ = 1.83e-4·√(ρ/r_nose)·v³`, r_nose = 2.0 m,
  skin temp from `T_skin = (q̇/(εσ))^¼`, ε = 0.85. Thermal limit is a stated
  TPS constant, not derived.
- HUD: fuel remaining, Δv remaining (Tsiolkovsky from current mass), T_skin,
  q̇ — four rows, minimal.

**FALSIFIERS (the deliverable's contract; bounds from PLAN.md Phase 11):**
- **F14 — Tsiolkovsky budget:** execute a commanded burn (test-driven, e.g.
  the A-ascent leg); measured Δv from the ship's own vel ledger vs the rocket
  equation's prediction from propellant consumed — agreement **< 5%**.
- **F15 — re-entry heating:** fly the sheet §4.3 reference entry state at
  planet B (test-driven trajectory through h ≈ 2·H_B at v_circ(B)); measured
  peak T_skin vs the analytic form **evaluated at the measured peak-heating
  state** (ρ(t), v(t)) — agreement **< 10%**.
- **F17 — energy with fuel:** extend `computeEnergy` (@~1781) per sheet §5
  (E_chem + exhaust KE in `total`); total-energy drift over a window
  containing a burn **< 2%**.

**CONSTRAINTS:** no git commits; `kernel_dsl.py` and the BH/tree code frozen;
existing Phase 6–10.5 / Track assertions must stay green untouched; scratch in
`engine/scratch/` only; **PLAN.md is Stage 3's, do not touch it**; new
assertions go in `test_phase6.py` as a clearly-marked Phase 11 section.

**DONE MEANS:** report with (1) `cd ChimeraEngine/engine && python test_phase6.py`
full-suite PASS/FAIL counts + log path in `engine/scratch/`; (2) F14/F15/F17
verdicts with measured numbers; (3) the diff summary (files + line counts).
Then STOP — Stage 3 (full arc + F16 + docs) lands in this slot after Kimi
verifies and commits Stage 2.

---

## THE STANDING RULES (binding on every task, this one included)

You are an implementation agent on SPIACE. Kimi K3 (or the operator) verifies your
work and commits it. **You never run git commit/push.** Every rule below was earned
by a real failure — the incident is cited so you know why it exists.

## THE FIVE RULES

**1. Green baseline BEFORE you edit; green suite BEFORE you report.**
Build and run the existing suite before writing a line (that baseline tells you the
tree was sane when you arrived), and run it again after your last edit. A refactor
that ships untested ships broken — the relay genome-switch refactor deadlocked the
whole viewer on its first request (`Lock` re-acquired → `RLock` fix) because the
session ended before one suite run.

**2. "Done" is a log file, not a claim.**
Your final report includes: the command you ran, PASS/FAIL counts, the measured
numbers, and the path to the saved output (e.g. `engine/scratch/_myrun.log`).
"All green" without a log path is treated as "unverified."

**3. Docs go LAST, append-only, and you `wc -l` after every edit.**
An agent session died mid-write on `engine/SPIACE_RPG_PLAN.md` and left it 0 lines —
recovery needed the git history. PLAN.md edits: append your section, bump the footer,
then verify line count grew. The pre-commit doc-guard refuses any PLAN.md shrink
> 50 lines unless you set `CHIMERA_ALLOW_PLAN_SHRINK=1` and say why.

**4. Running out of context? Write the handoff, then stop.**
Before you die: append to `engine/scratch/HANDOFF.md` — what's done (files touched),
what's unverified, the exact next command. Never leave uncommitted, untested work
with no note. The N8 relay refactor was found deadlocked with zero explanation.

**5. Scratch goes in `engine/scratch/` (gitignored).**
Probe scripts, logs, dumps — all of it. `git status` should show only files you
mean to ship. If you create scratch elsewhere, delete it before session end.

## KEY PATHS (go here first; do not explore blindly)

| What | Where |
|---|---|
| Native core (C++ CA/physics/rig/nav) | `ChimeraEngine/native/ca_core.cpp` |
| Genomes (data, key=value) | `ChimeraEngine/native/genomes/*.chimera` |
| Native↔viewer relay (SSE, port 8799) | `ChimeraEngine/native/relay.py` |
| Native viewer (zero sim logic) | `ChimeraEngine/engine/spiace_native.html` |
| Native test harness (headed Playwright) | `ChimeraEngine/engine/test_native.py` |
| Browser engine (WebGPU splat + BH kernels) | `ChimeraEngine/engine/spiace_phase6.html` |
| Kernel DSL (do not modify unless told) | `ChimeraEngine/engine/kernel_dsl.py` |
| Browser test harness | `ChimeraEngine/engine/test_phase6.py` |
| The plan / ledger (append-only) | `ChimeraEngine/engine/SPIACE_RPG_PLAN.md` |
| TRELLIS image→3D runtime + weights | `models/trellis/` (needs `out/` dir to exist for `--voxply`) |

Standard verify commands:
```bash
cd ChimeraEngine/native && g++ -O2 -std=c++17 -Wall -o ca_core.exe ca_core.cpp   # zero warnings
cd ChimeraEngine/engine && python test_native.py                                # full native suite (~3 min)
cd ChimeraEngine/engine && python kernel_dsl.py --verify spiace_phase6.html     # DSL gate
```

## RUN ONLY THE TESTS YOUR TASK TOUCHES (earned by the T1 harness audit)

Headed browser blocks were measured at 96% of suite time (179s of 187s). Do NOT
sit through the full suite on every iteration — gate the headed blocks:

```bash
T_HEADED=T1d python test_native.py          # only your block; selftests/oracles always run
T_HEADED=N3c,N4j python test_native.py      # comma-separated block tags
```

The selftests and Python oracles are NOT gated — they are the invariance net and
always run (they cost ~8s total). Rule 1 still stands: one FULL suite run before
your first edit (baseline) and one FULL suite run before your final report.
Between those two, iterate with `T_HEADED=<your block>` only.

Debugging a headed block? Each relay writes its own wire log —
`native/native_stream_<port>.log` (ports 8799, 8801–8806). Read that, not the
shared one; concurrent relays tear lines in a shared file (that race crashed
F-N8e with a JSONDecodeError before per-port logs existed). If a headed check
flaps, poll the wire log for the frame you need — never read `wire_anim[-1]`
and hope (the F-N5e mid-fall flake).

## HOW YOU'LL BE TASKED (the staged pattern)

Tasks over ~300 lines of diff arrive as STAGES, each < 150k tokens of context:
**Stage 1 verify-only → Stage 2 wire+prove → Stage 3 extend+docs.** Each stage ends
in a commit by Kimi, so a dead session costs at most one stage. Your prompt names
exact files and line numbers — use them; exploration is for when they're wrong.

## YOU WERE POINTED HERE BY A TASK PROMPT — START HERE

The prompt that sent you has this shape. Read it fully before touching anything:

1. **TASK** — the one outcome you own. If it's missing or ambiguous, ask before
   coding, not after.
2. **STATE** — what's already built and verified, with commit hashes. Trust it,
   but run the green-baseline check (rule 1) to confirm the tree matches.
3. **FILES** — exact paths, often line numbers. Go straight there. If a reference
   is stale (file moved, line drifted), note it and adjust — don't wander.
4. **FALSIFIERS** — the checks that decide pass/fail, named before any run. These
   are the deliverable's contract. A failing falsifier is a RESULT — document it
   with measured numbers (the CASE B model), never patch it green.
5. **CONSTRAINTS** — what you may NOT touch. Violating one invalidates the whole
   stage even if the suite is green.
6. **DONE MEANS** — the exact report format. Follow it literally.

If the prompt omits any of these and it matters, stop and ask. A prompt that says
"make it work" with no falsifier is not a task — it's a wish.

## HOW TASKS ARE WRITTEN (the template Kimi/operator fills in)

```
# SPIACE <phase>-<stage>: <one-line outcome>

Read ChimeraEngine/AGENT_PROTOCOL.md first; it is binding.

TASK: <the one outcome>
STATE: <what exists + commit hash + last suite result>
FILES: <exact paths/lines to read first>
FALSIFIERS: <named checks with numeric bounds, stated pre-run>
CONSTRAINTS: <frozen files/systems; no commits; style>
DONE MEANS: <suite green + measured numbers + log path in engine/scratch/>
```

Stages over ~300 diff lines are split: verify-only → wire+prove → extend+docs.
If your task feels bigger than one stage, say so in your report instead of
trying to swallow it — the split is the operator's call, not yours.

Rule 0 always: statement, prediction, falsifier named BEFORE the run. An honest
stall pinned with measured Q-values beats a patched pass — see the N8 CASE B entry
in PLAN.md for the model of how to document one.
