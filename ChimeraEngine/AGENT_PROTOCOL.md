# AGENT_PROTOCOL.md — the session contract for implementation agents

---

## ★ CURRENT TASK — do this (rewritten per stage by Kimi; read everything below first)

<!-- House rule: when a task completes satisfactorily, this file is updated the
     SAME day — this slot is cleared/rewritten AND any lessons the task earned
     (harness fixes, new gates, new flake patterns) are folded into the rules
     below, so the next agent inherits them instead of re-paying for them. -->

**OPERATOR WINDOW (cc1d169 → native):** the human entry point is
`python ChimeraEngine/START_VIEWER.py` (or double-click
`ChimeraEngine/native/ChimeraEngine.exe` — it self-starts the relay).
**The browser hub is RETIRED as the viewer frontend** (2026-08-16: Chromium
wedged machine-wide — every Chrome/Edge/Playwright instance hung on ALL
navigation incl. example.com while curl/Python flew; never our code, fix
attempts [WPAD off, fresh profiles] documented in this session's ledger).
The window is now `native/viewer.cpp` → ChimeraEngine.exe: Win32 +
wgpu-native (the Phase-13 API; vendored in native/viewer3rd — DLL + headers
match wgpu 0.32), the WGSL extracted from spiace_native.html at startup
(one shader, two frontends), the sim streamed from the relay over loopback
HTTP, scores live in a Win32 status bar (part 1: P/V + round + task; part 2:
the judge's current defect list), re-read from engine/score_ledger.json every
2 s so new judge rounds appear without a restart. Build:
`cd native && g++ -O2 -std=c++17 -static -static-libstdc++ -static-libgcc
viewer.cpp -I viewer3rd -o
ChimeraEngine.exe viewer3rd/wgpu_native.dll -lws2_32 -luser32 -lgdi32
-lcomctl32 && cp viewer3rd/wgpu_native.dll .` **STATIC LINKING IS MANDATORY**:
the exe otherwise loads `C:\Program Files\Git\mingw64\bin\libstdc++-6.dll`
(first on PATH) which ABI-mismatches the ProgramData g++ 15.2.0 that compiles
it — verified segfault inside the std::ifstream ctor at -O2 (-O0 masked it).
The wgpu surface lives on a CHILD render-host window (class SpiaceGL); a GPU
surface and the GDI status bar must not share one client area. **wgpu-native
v25 traps:**
`wgpuInstanceWaitAny` (WaitAnyOnly) and `wgpuShaderModuleGetCompilationInfo`
are `unimplemented.rs` PANICS — use AllowProcessEvents + a ProcessEvents
pump loop; `WGPUVertexAttribute` gained a leading nextInChain. Agents OPEN
the window themselves after a finding (never hand the operator a path) and
verify via screen capture
(`PowerShell CopyFromScreen → engine/scratch/_screen.png` — works for
native windows). New proof images land in `engine/scratch/`. v1 limits
(honest): shell rides bodyX/bodyY rigidly (limb pose binding not yet
ported), ground is the flat-plane ring march (terrain-wire not ported),
genome switch = restart with a different shell arg.

**LIVE TASK — Teddy pipeline T8 (immediately below), now on the HONEY body.**
Teddy-thread shipped: T2 structure (`2263659`), T3 voxel-muscle gait
(`e0af946`), T3.5 shape training (`080bf4b`), T4 trained gait (stride L=2,
+41.5%), T5 visual pass (V 58 → 74), T6 PART A (structure + ROM, V 74 → 80),
T7 hills (teddymusclehills.chimera, walks the bear's seed-2026 world, hills
106 vs flat 116 cells/400t, flat ledger bit-unchanged, F-T7a…d green), **T9
canonical re-import**: the T1 teddy's source was a mutated TRELLIS blob — the
physics was faithfully animating a bad statue. New pipeline: SDXL-Turbo
ambient-lit candidates (`models/imagegen/sd-cli.exe`, 4-step turbo, ambient
light only — shadows pollute shape capture) → operator pick sheet → **HONEY**
→ TRELLIS (`models/trellis/runtime/trellis-cli.exe`, cwd MUST be
models/trellis or it dies silently at [3/6] rc=127) → `voxelize_teddy.py
<ply> teddy_honey 28` (H=28 derived: head≈0.45H, eye≥2 cells ⇒ H≥26.7) →
3673 cells → `shape_train.py teddy_honey` → 3678 cells, 3 legs, connected
3678/3678 → `teddyhoneymuscle.chimera` + `teddy_pyramid.py` shell
(342k splats, levels h=56…224). F-T9a…d green in the fast net: shape gate,
drop law (contactTick 99 == pred 99, drift 0.9935%), scale-free stride
(bodyX=114 vs old 116, |Δ|≤12), integrity+airwalk (airDX 0). Turntable
(`scratch/_proof_t9.py` → `_t9_turntable.mp4`) + walk strip
(`_proof_t9_walk.py`: bodyX 24→100, contact GROUND, vy 0) read by me;
Qwen 3.8 judge (`scratch/_judge_t9.py` — reasoning model: budget 4096 tokens
and read `reasoning_content` when `content` is empty).
**Current dual score: P = 92, V = 65** (ledger round 7 — T12 anisotropic
surface splats, judge-anchored. The operator's complaint: "gaps through
giant balls" + "more splat types than just balls". Fix shipped in
`spiace_native.html` vs(): shell splats with real normals render as
EWA-projected ANISOTROPIC Gaussians — tangent-stretched (st = 1.58×size =
0.95 cell, derived: visible radius 0.82 cell ≥ the 0.707 cell grid-diagonal
gap), normal-thin (sn = 0.67×size) — plus the LOD level threshold 0.55→0.45
(3DGS law floor: ≥0.5 splats/px; picks h=224, 98.5k splats at default
framing). Measured on the RTX 4090 via wgpu-py offscreen (EXACT shader +
layout + camera port, `scratch/_render_t12.py`): torso interior dark gaps
0.0006 → 0.0000, surface grain (lum-std) 56.6 → 32.6 (−42%). Judge:
"continuous fabric, not separate balls, no through-holes" — V 60 → 65.
New defect list: patchy-scalp, lumpy-ear-rim, caterpillar-arm-rim,
flat-slab-feet, woven-lattice-texture (the tangent ridges read as 3D-print
lattice at h=224 — next lever), flat-lighting-no-AO, jagged rims, back seam.
**T12 lessons, earned the hard way:** (1) `ref` is a RESERVED WGSL keyword —
the first aniso shader failed pipeline creation silently and the canvas went
black; compile-check WGSL changes with wgpu-py BEFORE any browser run:
`.venv/Scripts/python -X utf8` + `wgpu.utils.get_default_device()` +
`create_shader_module` on the regex-extracted WGSL (this caught it in 5 s).
(2) Headed Playwright navigation to localhost BROKE mid-session on this
machine (curl instant, headless instant, headed/Playwright-launched-Chrome
hangs pre-commit — even CDP-attached real Chrome wedges; NOT our code,
repro on a static file on a plain http.server). The fallback verification
path is wgpu-py offscreen render on the real GPU — bit-exact shader/layout
check plus actual pixels. (3) dxil.dll/dxcompiler.dll were copied from
Chrome 151 into ms-playwright/chromium-1200 chasing headless WebGPU;
chromium was reinstalled (`python -m playwright install chromium`) to
restore the original dxcompiler.dll; the leftover dxil.dll is byte-identical
to chromium-1228's, harmless. (ledger round 6 — T11 standing bear, judge-anchored; the limb-distinguishability win cost face fidelity: recon dropped eyes/mouth. T10 shipped directional light + mouse orbit/zoom; the light-sweep falsifier tripped 4x and each cause is named in PLAN.md T10 — phase law exact, amplitude bound explained. The 'shadow line' was the T3 legZ debug tint on the H=28 body — now FLAT-view-only. Bodies: honey (sitting, 3678 cells) and stand (1520) both green on the voxtest drop/stride/airwalk laws. (ledger round 5 — V anchored on the
Qwen 3.8 judge's REAL verdict, `scratch/_t9_verdict.txt`: face/bow/proportions
right; see-through ghosting, floating paw pads, torso seam, lumpy hip bulge,
bow visible from behind, grainy surface = the defect list. The first judge
runs returned EMPTY content — qwen3 spends its budget on reasoning_content;
fixed in `_judge_t9.py`: max_tokens 4096 + reasoning_content fallback +
utf-8 stdout/file writes). Resolved by T9:
face-not-discernible, density-below-capture-law, limbs-stubby. Persisting:
shadow-drift, Case-B stall, terrain-ridge-lines; new (Qwen-measured):
splat-ghosting-translucency (BIGGEST — no occlusion in the renderer),
floating-paw-pads, shell-level-banding (torso seam), lumpy-asymmetric-body,
bow-misplaced-3d, fur-texture-noise, gait-motion-subtle, fps-23-at-max-shell.
Saturation completeness 0.272 (NOT saturated). **T8 runs on teddyhoneymuscle now** — the
old teddy.* / teddymuscle*.* files are FROZEN fossils pinned by T3/T7
regressions; never regenerate in place. Phase 11 Stage 2 (browser
engine) is **PARKED at the bottom of this slot** — prompt intact, ready for
an agent when the operator returns to that thread. **T10 (lighting-direction
contrast sampler) is filed after T8** — the operator's current interest.

---

# Teddy pipeline, T8: PART B stage 2 — control: walk BOTH ways on command

**TASK:** The operator's Part B has two halves; T7 shipped the environment
half ("does it respond to its environment"). Stage 2 is the CONTROL half:
"can I control the teddy bear." Today the vm gait walks +x only — the
beat machine (LIFT/SWING/PLANT/SHIFT) has no direction parameter, and the
viewer has WAVE/WALK/REST but no way to choose a heading. Give the gait a
direction and the operator the keys.

**STATE:** T7 shipped. `ca_core.cpp` vmWalkTick (~line 2065): SWING does
`paw[0] += 1`, SHIFT does `bear.body[0] += W.vmStride` and repays planted
paws by `−vmStride` — both are +x-hardcoded. The bear's N8 nav already
proved directional verbs on the FK gait (walk+/walk− bit-exact time-reverse,
F-N8). The viewer (`spiace_native.html`) maps keys 1/2/3 → wave/walk/rest
via POST /cmd; `relay.py` forwards any `cmd:` line to core stdin. The cmd
parser in `ca_core.cpp` accepts a fixed verb set — extending it is a loader
change, not an architecture change.

**Rule 0 (stated before the run):** reversing a cyclic beat machine is a
sign flip, not a redesign — SWING steps −1, SHIFT advances −vmStride, the
planted-paw repay flips sign, and the PLANT/LIFT beats are direction-free
(vertical only). Prediction: on FLAT, walk-west over 400 ticks is the
bit-exact mirror of walk-east (bodyX == −116, same conn/count/slips ledger);
on the seed-2026 hills, west-bound walks the mirror descent with the world
integer-exact the same field. Falsifier: west ≠ −(east) on flat → the
sign flip leaked an asymmetry; report, don't patch around it.

**What to wire:**
1. `cmd` verbs `walk` (east, unchanged default) + `walkw` (west) in the
   core's cmd parser; a `vmDir` (+1/−1) threaded through SWING/SHIFT.
   No new genome keys — direction is a COMMAND, not a genome fact.
2. Viewer: key 4 (or ←/→ arrows) → POST `cmd:walk` / `cmd:walkw`; the
   button row gains WALK-W. HUD shows the commanded direction.
3. `test_native.py` F-T8: flat west == −east bit-exact (bodyX, vm ledger);
   hills west-bound walks ≥ 40 cells with the same integrity gates; the
   flat east regression (F-T3/F-T7d numbers) unchanged.
4. Proof strip (rule 7): teddy walks east, reverses, walks back west —
   one strip, both directions, terrain contact visible throughout.

**FALSIFIERS:** fast net ALL GREEN (incl. F-T3/F-T6/F-T7 regressions);
west == −east bit-exact on flat; the strip (rule 7) shows a CONTROLLED
reversal, and your visual verdict says whether the turn-around reads as a
creature reversing or a tape rewinding (honest answer required — a
teleporting paw order is a deficiency, name it).

**CONSTRAINTS:** no git commits; scratch in `engine/scratch/` only;
`teddy_s1.cells` frozen; no new genome keys; the vm beat machine's phase
order (LIFT→SWING→PLANT→SHIFT) is untouchable — only signs flip.

**DONE MEANS:** (1) F-T8 numbers + all regressions, (2) the reversal strip
+ your visual verdict (rule 7), (3) ledger round + `status`, (4) diff
summary. Then STOP.

**LOOKAHEAD (not this task):** stage 3 is heading (z-axis turning) — the
honest open problem is that rotating a live lattice body leaks cells; the
CA-native answer is probably "grow the turn" (differential paw-plant columns
per side, like a tracked vehicle) rather than rotating the cell set. Stage 4
is the 2D terrain membrane (the v:terrain-ridge-lines deficiency: the world
is a 1D profile extruded along z).

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
Third earned note (T5, 2026-08-16): the strip must show the CANONICAL view —
the T4 strip's tight crop masked the framing deficiency it was meant to
judge. Full-frame capture + a measured fill probe (`__dbgFrame()`), never a
hand-picked crop.

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

The band is set by SATURATION, driven by taste (operator directive
2026-08-16): a taste judgment — the human's or the LLM's, **equally
valuable, no hierarchy** — is the discovery instrument. Each critique round
(whoever issues it) names what offends; each offense is a deficiency class
with a stable id (repeat sightings are the SAME species, whoever spotted
it). Rounds log to the ledger —
`cd ChimeraEngine/engine && python score_saturation.py add <task> <P> <V>
<def-id>...` — and `status` computes the species-accumulation curve: Chao2
completeness = S_obs/(S_obs + f1²/2f2) plus the dry tail (consecutive
rounds with zero NEW deficiency classes). SATURATED at completeness ≥ 0.9
with a 3-round dry tail — the standard stopping rule, the same math as the
engine's S1 question saturation — and the scores at that point are the
band floor, presented to the operator for the accept/reject call. Baseline
round (T4-baseline): 7 classes found, Chao2 estimates ~28, completeness
0.25 — NOT saturated; keep discovering. If the curve never humps, the
rubric's categories are wrong, not incomplete: re-frame, don't keep
scoring.

## THE METHODOLOGY IN ONE PASSAGE (2026-08-16 consolidation)

Every task runs the same loop, and the loop is the rules above:
**Rule 0 first** — statement, prediction, falsifier named BEFORE the run.
**Derive, don't tune** — a number you chose is a broken chain; train under
a falsifier gate instead (T4: the sweep found L=2 at +41.5% AND showed why
the raw-faster L≥3 were illegal). **Construction order** (rule 6): shape →
rig → gait; never train movement on an unphysical body. **Judge what you
see** (rule 7): the strip is a first-class artifact, full-frame, with the
claim measured by a probe. **Two scores** (rule 8): P and V, each /100,
every report, logged to the ledger; the band emerges from taste-driven
saturation, not from a number anyone picked. **Done is a log** (rule 2),
**docs last, append-only** (rule 3), **green before you edit and before
you report** (rule 1).

## THE WORKFLOW, STEP BY STEP (the procedural form of the passage above)

Follow these in order. Skipping a step is how every recorded failure started.

1. **READ the task.** The CURRENT TASK slot at the top of this file (or the
   staged prompt you were handed) — TASK / STATE / FILES / FALSIFIERS /
   CONSTRAINTS / DONE MEANS. Any piece missing and material: stop, ask.
2. **ORIENT green.** Run the fast net (`cd ChimeraEngine/engine && python
   test_native.py` — seconds) BEFORE writing a line. If the baseline is red,
   report that; do not build on it. Then go straight to FILES — exact paths
   and line numbers; explore only when they're wrong.
3. **RULE 0 before any run.** Write the statement, the prediction, and the
   falsifier you have not measured yet. No falsifier, no build. A number you
   cannot trace to a derivation or a citation is a broken chain — if the
   derivation sheet doesn't have it, STOP and report the gap; never tune.
4. **CONSTRUCTION ORDER.** Shape → rig → gait → control. Never train
   movement on an unphysical body; never re-rig an unbalanced one
   (rule 6 — the teddy's COM was 1.63 cells outside its paw hull; three
   grown pillars came before any gait work).
5. **BUILD the minimal diff.** Respect every CONSTRAINT. All probes, logs,
   and proof scripts go in `engine/scratch/` (gitignored). C++ core changes
   compile with zero warnings (`-Wall`); WGSL changes are compile-checked
   with wgpu-py BEFORE any window run (5 s — `ref` is a reserved keyword and
   a silent shader failure costs a black canvas and an hour).
6. **TEST only what you touched.** Fast net ALWAYS. Headed blocks: only the
   tags your task touches, once — `T_HEADED=<tag> python test_native.py`.
   The full suite is DELETED; do not resurrect it. Iterate headless between
   the two green runs.
7. **SEE it yourself.** Every headed/visual deliverable: capture the proof
   (full-frame strip or screenshot — never a hand-picked crop), then READ it
   with ReadMediaFile and write the visual verdict: what a skeptic sees,
   deficiencies named with stable ids. For the native window, screen-capture
   (`PowerShell CopyFromScreen → engine/scratch/_screen.png`). Check
   `pageerror`/stderr on every probe. Numbers without a visual verdict are
   unverified (rule 7).
8. **SCORE both axes.** P and V, each /100, per the rule-8 rubric — no
   vibes; if you can't name the instrument, the category scores 0. For V,
   the judge is the LM Studio model (`_judge_*.py` pattern: ONE image per
   call, max_tokens 4096, read `reasoning_content` when `content` is empty,
   utf-8 writes). Log the round: `cd ChimeraEngine/engine && python
   score_saturation.py add <task> <P> <V> <def-id>...`, then `status` for
   the saturation curve.
9. **SHOW the human — you open the window.** After any finding over the
   threshold, launch/raise `ChimeraEngine/native/ChimeraEngine.exe` yourself
   (it self-starts the relay; verify by screen capture). Never hand the
   operator a path or a port number. The status bar picks up your new ledger
   round within 2 s — the operator sees P/V and your defect list in the same
   window as the result.
10. **REPORT in the DONE MEANS format.** Command run, PASS/FAIL counts,
    measured numbers, log path in `engine/scratch/`, diff summary, visual
    verdict, both scores. "All green" without a log path = unverified.
11. **IF YOU'RE DYING, hand off first.** Append to
    `engine/scratch/HANDOFF.md`: done/unverified/next-command. Then stop.
12. **(Verifier only — Kimi/operator.)** Commit + push with `Agent:` trailer,
    stage only the task's files, then SAME DAY: rewrite the CURRENT TASK
    slot with the next stage and fold the task's earned lessons into these
    rules so the next agent inherits them.

## KEY PATHS (go here first; do not explore blindly)

| What | Where |
|---|---|
| **Operator window (unified human view)** | `ChimeraEngine/native/ChimeraEngine.exe` ← `viewer.cpp` (scores in the status bar) |
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
| Score ledger + saturation instrument | `ChimeraEngine/engine/score_saturation.py` → `score_ledger.json` (rule 8) |
| Proof-strip pattern (full-frame + probes) | `ChimeraEngine/engine/scratch/_proof_t5.py` (rule 7) |
| ROM strip pattern (Part A) | `ChimeraEngine/engine/scratch/_proof_rom.py` — survey + per-chain extremes |
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
