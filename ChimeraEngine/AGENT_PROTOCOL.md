# AGENT_PROTOCOL.md — the session contract for implementation agents

---

## ★ CURRENT TASK — do this (rewritten per stage by Kimi; read everything below first)

<!-- House rule: when a task completes satisfactorily, this file is updated the
     SAME day — this slot is cleared/rewritten AND any lessons the task earned
     (harness fixes, new gates, new flake patterns) are folded into the rules
     below, so the next agent inherits them instead of re-paying for them. -->

**LIVE TASK — Teddy pipeline T5 (immediately below).** Teddy-thread shipped:
T2 structure (splat pyramid + density-law ground, `2263659`), T3 rig
(voxel-muscle CA gait — no FK/IK, `e0af946`), T3.5 shape training
(`080bf4b`, COM margin −1.63 → +2.21), T4 trained gait (stride L=2,
+41.5% under the falsifier gate). **Current dual score: P = 92, V = 58** —
physics is in band, VISUAL is the deficit; T5 attacks it. Phase 11 Stage 2
(browser engine) is **PARKED at the bottom of this slot** — prompt intact,
ready for an agent when the operator returns to that thread.

---

# Teddy pipeline, T5: visual quality — make the walk READ as a teddy walking

**TASK:** Raise the V-score (58/100, rubric in rule 8) without regressing
the P-score (92/100). The physics is measured-correct; the picture is not
skeptic-proof: at canonical framing the teddy is a small dark lump, the legs
are not individually readable, and 375 raw cells is far under the
0.5–2 splats/px density law.

**STATE:** T4 (`vmStride=2, vmLift=1` in `teddymuscle.chimera`): walk 116
cells/400 t (pred 114), iters=0, conn 1, count [358,375], slips 0, airDX 0,
contactTick 53 == prediction. Fast net ALL GREEN in 7.8 s. Strip pattern:
`engine/scratch/_proof_t3.py` (headed, port 8914, 6 frames + ledger).

**Rule 0 (stated before the run):** the V deficit is dominated by THREE
measurable causes — (a) framing: the subject fills < 15% of the strip
frame; (b) density: the viewer binds the 375-cell raw lattice, not the T2
pyramid shell (`teddy_shell.json`, up to 56802 splats — the machinery
exists and is camera-driven); (c) lighting/exposure: the body renders dark
against a dark ground. Prediction: subject ≥ 40% of frame height + the
pyramid level picked by the 2.5-px footprint law + an exposure pass lifts
V into the 70s with ZERO physics edits. Falsifier: any variant that raises
the strip's readability but changes ONE wire number (bodyX, count, slips,
contactTick) is disqualified — P must not move.

**What to wire:** viewer-only (`spiace_native.html` + maybe relay frame
packing). Camera: canonical strip framing derived from the body's bounding
radius (subject ≥ 40% frame height at walk start, lagged follow stays).
Density: bind the pyramid shell to the live cells (the T2 rebinding already
keeps stable bindings byte-identical — extend it to level selection by
camera depth). Exposure: a display-space gain, never touching cell data.

**Objective:** V-score up, P-score flat. Both numbers reported with the
category breakdown, before AND after.

**FALSIFIERS:** F-T3a–d green on the untouched genome; the strip shows the
claimed improvement (a strip that can't show the claim is a FAIL, rule 7);
wire numbers bit-identical to the T4 pins above.

**CONSTRAINTS:** no git commits; `ca_core.cpp`, all genomes, and
`test_native.py` FROZEN (this is a viewer task); scratch in
`engine/scratch/` only; headed runs only for your strip captures.

**DONE MEANS:** report with (1) before/after strips + V-score category
breakdown both times, (2) P-score confirmation (fast net log path), (3)
diff summary. Then STOP.

---

# SPIACE Phase 11, Stage 2 of 3 (PARKED): ship + atmosphere + re-entry physics (wire+prove)

**PARKED 2026-08-16 — the operator pivoted to the teddy/CA thread (T2–T4).
This prompt is complete and ready to hand to an agent unchanged.**

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

## THE EIGHT RULES

**1. Green baseline BEFORE you edit; green fast net BEFORE you report.**
Run `python test_native.py` before writing a line (seconds now — the headed
browser blocks are opt-in only) and again after your last edit. If your task
touches the viewer, run ONLY the headed blocks you touched, once, via
`T_HEADED=<tag>` — never the whole browser fleet. There is no full-suite run
anymore; it was deleted 2026-08-16 after the audit showed 96% of its time
was browser waiting that decided nothing new.

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

**6. Order of construction: SHAPE before RIG before GAIT.**
A body's physical correctness is trained FIRST — `native/shape_train.py`: COM
ground projection inside the paw support hull with margin >= 1 cell (one
lattice step of discretization slack), paws coplanar, scan untouched (the
trainable DOF is support placement: grow pillars, never trim). The rig is
DERIVED from the corrected shape. Gait work runs only on a body that passes
the shape gate — F-T3a-shape recomputes it from the cells file, never trusts
the trainer. Earned 2026-08-16: the raw teddy scan's COM projected 1.63
cells OUTSIDE its paw hull — a doll that tips — and no other ground-touching
columns existed, so no re-rig or gait could have made it stand. Three grown
pillars later: margin +2.21 cells, then movement.

**7. Judge what you see — the visual-critique gate.**
Every headed deliverable requires you to capture a screenshot or frame strip,
READ it (ReadMediaFile), and write a VISUAL VERDICT in your report: what a
skeptic would see, with named deficiencies. Numbers without a visual verdict
are unverified. Earned 2026-08-16: T3's ledger said WALKS while the strip
showed an unreadable jiggling blob — the camera's perfect body lock hid the
translation, and the dense shell hid the legs. The critique, not the
assertions, produced the fixes (lagged follow, leg-zone tint, new-voxel
highlight — `engine/scratch/_proof_t3.py` is the reusable strip pattern).
Two more earned notes: check `pageerror` on every probe (a scope error threw
inside the splat builder and the suite's numeric checks never noticed), and a
strip that can't show the claim being made is a FAIL, however green the log.

**8. Two scores, every report — P and V, each /100.**
Operator directive 2026-08-16. Every deliverable ships a PHYSICS score and a
VISUAL score. 100 is theoretically impossible on both; the operator sets the
acceptable band from measured baselines (first baselines: P = 92, V = 58 at
T4). Each category is measurable — no vibes. If you cannot name the
instrument a category is measured with, the category scores 0.

P (physics), /100:
- Conservation ledgers (20): measured energy/momentum drift vs the named
  bound. Derived-but-nonzero drift (e.g. symplectic shadow) costs points.
- Analytic-law agreement (20): every closed-form prediction (drop tick,
  Kepler, thermal, cyclotron, stride rate) inside its PRE-STATED band.
- Oracle replication (15): C++ vs the independent Python oracle — bit-exact
  is full marks; every epsilon-waiver costs.
- Integrity gates (15): connectivity, count bounds, no NaN, zero slips.
- Contact & traction (15): gap, rest equilibrium, airDX, earned traction.
- Control layer (10): learner/deliberation consistent with the physics
  (an unfixed CASE B stall costs — measured and pinned, not patched).
- Falsifier discipline (5): every claim named its falsifier before the run.

V (visual), /100 — judged off the strip/screenshot YOU read (rule 7):
- Subject recognizability (25): a skeptic names the object at canonical
  framing without being told.
- Motion legibility (20): the claimed motion reads as that motion (a walk
  reads as walking, not sliding or jiggling).
- Grounding (15): contact, shadow, no floating or sinking.
- Renderer fidelity (15): no seams, flicker, or artifacts; splat pipeline.
- Scene legibility (15): framing (subject ≥ 40% of frame), lighting,
  contrast, HUD honesty.
- Density law (10): splats-per-pixel inside the 0.5–2/px capture law at
  canonical framing (T2 measured this off real 3DGS scans).

A P regression to buy V (or vice versa) is disqualified, not traded.

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
| Teddy splat pyramid (T2) | `ChimeraEngine/native/teddy_pyramid.py` → `genomes/teddy_shell.json` |
| Teddy voxel bodies (T1/T3) | `genomes/teddy.cells` (370 cells, 6 leg chains); `teddy.chimera` FK/IK · `teddymuscle.chimera` voxel-muscle |

Standard verify commands:
```bash
cd ChimeraEngine/native && g++ -O2 -std=c++17 -Wall -o ca_core.exe ca_core.cpp   # zero warnings
cd ChimeraEngine/engine && python test_native.py                                # fast net (seconds)
cd ChimeraEngine/engine && python kernel_dsl.py --verify spiace_phase6.html     # DSL gate
```

## RUN ONLY THE TESTS YOUR TASK TOUCHES (the full suite is DELETED)

`python test_native.py` with no env runs in seconds: the headless selftests
and Python oracles — the invariance net. Headed browser blocks are opt-in,
named by tag, and you run only the ones your task touches, once, before
commit:

```bash
python test_native.py                       # the fast net — ALWAYS this
T_HEADED=T1d python test_native.py          # + your headed block, ONCE
```

Rule 1 still stands in its new form: fast net green before your first edit
(baseline) and before your final report. Between those, iterate headless.

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
