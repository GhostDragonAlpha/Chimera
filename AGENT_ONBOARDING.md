# CHIMERA — AGENT ONBOARDING

> Paste this as an agent's first instruction, **or** just tell the agent:
> "Read `E:\PythonChimera\AGENT_ONBOARDING.md` and follow it." (lowest context cost.)

**TL;DR if you read nothing else:** `cd E:\PythonChimera\Chimera` → `python -m core.preflight` → `python -m core.helm targets` → `python -m core.task_board claim --agent <your-handle>`. The claim **prints your task packet — that packet is your instructions.** Do the work, prove it with real evidence (a compile is not proof), close with `task_board done` + `postflight`, prepend a note to `task_progress.md`. Don't explore the tree; the tools tell you what to do.

---

You're joining **Chimera**: an autonomous studio that generates a AAA-quality Unreal Engine 5.8 game from a formal seed (`CHIMERA_VISION.py`) through a hard-gated pipeline. Your job: advance the game toward that seed by completing **one well-scoped lane of work**, proving it, recording it, and handing off cleanly. **The system tells you what to do — you run its tools and follow their output.**

## 0. Which agent are you? (pick your authority, ignore the other)
- **Capable / confident model** → skim `E:\PythonChimera\CLAUDE.md` ("NEW AGENT? START HERE" + "Key Paths") and think.
- **Smaller model, or unsure** → open `E:\PythonChimera\SUCCESSOR_RUNBOOK.md` and follow it **EXACTLY. Improvise nothing.** Every recipe there was paid for in failures.

The boot, laws, and exit below are **universal** — do them regardless.

## 1. Boot (run from `E:\PythonChimera\Chimera`, in order — each prints what you need)
```powershell
cd E:\PythonChimera\Chimera
python -m core.preflight       # live state: health, GPA, loop board, last run, + [4.5] prior Will & open pains
python -m core.helm            # recommended FOCUS: Contain / Fix / Graduate / Build / Verify / Polish / Consolidate
python -m core.helm targets    # the ranked gap between the seed and the live project
```
Then read the **top** of `E:\PythonChimera\task_progress.md` — the last agent's handoff and NEXT items. (Read the top few blocks, not the whole file.)

## 2. Claim your lane — this IS your assignment (don't hand-pick work by searching)
```powershell
python -m core.task_board list                          # see the board
python -m core.task_board claim --agent <your-handle>   # add --capable ONLY if you earned it (see Gauntlet)
```
- Use a **unique handle** so you don't collide with other agents: e.g. `opus-47`, `haiku-k9`, `sonnet-3b`.
- `claim` opens your tunnel, reserves your editor mode, and **prints your WORK PACKET: recipe, matching H-heuristics, study guide, open pains. The packet is your instructions — follow it.**
- The board only grants lanes whose files **don't collide** with other active agents. **Stay inside your footprint** (the files/systems your packet names). Don't wander.
- `capable_only` lane? Earn the credential first: `python -m core.gauntlet enter --agent <handle>` (`docs/GAUNTLET.md`).
- Long task? Keep your claim + editor alive: `python -m core.agent_tunnel heartbeat --agent <handle>`.

## 3. Work (the Contract)
- **Flow top-down:** game *content* → the DSL spec (`tests/dsl_grammar/deep_space_trader.chimera`); code *shape* → the generator (`core/game_code_generator.py`); the pipeline regenerates the C++.
- **Never hand-edit generated code** under `Source/Chimera/ProceduralGenerated/` that a template owns (Flight, Ship, GameMode, Economy, Combat, Missions, Save, Docking, Factions, Weapons… — CLAUDE.md lists them). Fix the **generator template** instead; hand-edits are clobbered on the next pipeline run. **Unsure whether a file is generator-owned? Treat it as owned** — fix the generator, or don't fix it.
- **Build must return 0** (record success AND failure to the graph):
  ```powershell
  & "C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" ChimeraEditor Win64 Development "E:\PythonChimera\Chimera\Chimera.uproject" -waitmutex
  ```
- **Record only through typed helpers:** `python -m core.graphify_record <feature|grade|surprise|...>` or the `record_*` functions. **Never hand-write graph mutation dicts** — wrong keys silently poison the graph.
- **Unknown blocker?** Never write a bare "blocked." Run `python -m core.solver --blocker "<one line>" --context "<verbatim error>"` — its output is a concrete fix plan.

## 4. The Laws (breaking these destroys paid-for work)
1. **Verify, don't assert.** A compile is not a behavior; an event firing is not a state change; `success: true` is not proof. **Read the result back** (engine query, telemetry run foregrounded, a passing test). If you can't read it back, it's NOT done — say so plainly.
2. **`verified` is AUTOMATED-ONLY.** Only sleepwalker/telemetry/result-grading observation collapses a feature to `verified`. Your built + compiled + unit-tested work is `implemented`, never `verified`.
3. **Answer the Frame Audit before "done"** (`docs/RESULT_GRADING_RUBRIC.md`): Are you optimizing the *target* or a *proxy*? Judging the *result* or your own *effort/artifact*? Grade the result.
4. **No fallback ladders, no silent continuation.** A failed gate = stop and fix. Exit code 1 halts the pipeline on purpose — don't route around it.
5. **Multi-agent hygiene.** Work only inside your footprint. **Never `git add -A`** — you'll commit other agents' in-flight files. Stage **your own files by path**, commit, push. Never touch another agent's files or `Chimera/Config/DefaultEngine.ini` unless it is explicitly your lane.

## 5. Exit (always, before you finish)
```powershell
python -m core.task_board done --agent <handle> --id <tb-N> --result "<verbatim evidence>"
python -m core.postflight --phase "<what you did>" --result "<UBT / command output, verbatim>" `
  --inheritance "<=3 sentences: what this session learned>" `
  --phantom-pain "<a specific failure the next agent should confirm or refute>"
```
(If you must stop without finishing: `task_board block --agent <handle> --id <tb-N> --reason "<why + next step>"` — a bare "blocked" is forbidden.)
Then **prepend** a short block to `task_progress.md`: *what you did · the evidence · the NEXT step.* If you used git, commit **only your files** and push.

## Stuck? The answer is in ONE of these — not the whole tree:
`preflight` output · your **task packet** · CLAUDE.md **"Key Paths"** table · `SUCCESSOR_RUNBOOK.md` · `docs/MCP_PATHWAYS.md` (proven MCP calls + traps).
