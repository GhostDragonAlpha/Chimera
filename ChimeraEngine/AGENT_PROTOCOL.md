# AGENT_PROTOCOL.md — the session contract for implementation agents

---

## ★ CURRENT TASK — do this (rewritten per stage by Kimi; read everything below first)

### SPIACE T1-Stage3: teddygoal nav + PLAN.md v4.4

**TASK:** give the teddy the goal membrane and document T1. Two code deliverables
plus the PLAN.md entry, in the order written.

**STATE:** committed `7f4a85a`, full headed suite 71 PASS / 0 FAIL.
- `ChimeraEngine/native/genomes/teddy.chimera` — kind=vox genome, B4/N5 constants
  only (stand/walk proven: F-T1a/b/c green)
- `ChimeraEngine/native/ca_core.cpp` — kind=vox loader at ~line 343 accepts ONLY
  the B4/N5 fields; L5/R5/N6/N8 sections are absent from teddy.chimera
- `ChimeraEngine/engine/test_native.py` — F-T1 block after the F-N8 block (~line 2001)
- `ChimeraEngine/native/relay.py` — runtime genome switch via POST /cmd "genome:<name>"

**FILES to read first:** `native/genomes/beargoal.chimera` (the goal-membrane
declaration you're mirroring), `native/genomes/teddy.chimera`, the vox loader in
`native/ca_core.cpp` (~line 343), the F-N8 block in `engine/test_native.py`
(~line 1770-2000).

**DELIVERABLES:**
1. `native/genomes/teddygoal.chimera` — copy teddy.chimera, add the goal membrane
   EXACTLY as beargoal.chimera declares it (`goal = 1`, `goalX = 15`, plus the
   L5/R5/N6 blocks the nav path requires). If the vox loader rejects the extra
   sections, extend the LOADER ONLY (accept the fields, wire them to the existing
   nav code path). Terrain: read how bearhill/beargoal declare it and decide flat
   vs terrain block from what the nav senses actually read — DERIVE, document the
   choice in the genome's comment header.
2. `engine/test_native.py` — F-T1d after F-T1c, same shape as F-N8d/e: navigator
   drives the teddy to the flag; report learning curve (first30 vs last30),
   arrivals/N, and a headed witness. **If the N8 CASE B honest-stall repeats on
   the teddy (greedy RESTs forever while training arrives), that is a VALID
   result** — pin it like CASE B with measured Q-values.
3. `engine/SPIACE_RPG_PLAN.md` — APPEND a T1 section, N-series style: the
   shape-agnostic theory, scale derivation (s = 11.784098 cells/unit from bear
   bodyH=8), orientation (CA y(up)=model z), all measured numbers (370 cells,
   6 rig chains, drop 53==53, ledgerErr 3.06e-16, termDrift 1.8451%, gap
   2.6645e-17 m, walk 53.630579==oracle, F-T1d results), falsifiers F-T1a..d.
   Footer to `Document version: 4.4`, status adds T1. **APPEND ONLY — the file is
   891 lines at v4.3; `wc -l` after your edit must show more.** The doc-guard
   pre-commit hook refuses shrinks.

**FALSIFIERS:** F-T1d pass = navigator arrives per the F-N8d/e criteria; honest
stall = CASE B pin with Q-values. Named now, before any run.

**CONSTRAINTS:** N5/N6/N7/N8 physics logic in ca_core.cpp is FROZEN (loader
plumbing only). `kernel_dsl.py` untouched. No commits. Match existing style.

**DONE MEANS:** `cd ChimeraEngine/engine && python test_native.py` — full suite
green incl. F-T1d (or the pinned stall); report PASS/FAIL counts, all measured
numbers, and the log path under `engine/scratch/`.

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
cd ChimeraEngine/engine && python test_native.py                                # native suite (headed)
cd ChimeraEngine/engine && python kernel_dsl.py --verify spiace_phase6.html     # DSL gate
```

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
