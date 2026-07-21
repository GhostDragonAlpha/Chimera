# Chimera Agent Onboarding Prompt

> Paste this into a new agent session. It gets you into the rhythm in under 2 minutes.

## THE RHYTHM

This is not a task-list project. It is a continuous question loop:

**ask → answer → ask → answer → ask**

1. Ask a concrete question about the current state
2. Answer it with evidence (read code, run beats, query MCP, spawn actors)
3. Ask the NEXT question based on what you learned
4. Repeat until the human stops you — never stop yourself

A task is one answer, not the destination. The session ends when the human ends it.

## THE FORMULA — every item, always

The old way (place a cube, verify it exists) is muscle memory. It creeps back when tooling gets hard.
**The formula is the crutch while the new muscle grows.** Every item on your TODO list follows this:

```
CONSTRAINT: <what must be true, stated as physics — never the form>
MEASURE:    <one number that proves the constraint holds>
EXISTING:   <what's already compiled/wired that serves this>
WORK:       <train / wire / decode — never author a form>
VERIFY:     <the beat that tests the rule, not the thing>
```

**Examples:**

| ❌ Old way | ✅ Constraint-first |
|---|---|
| "Place a habitat at 0,-800,0" | "A player must be able to refill O2 by returning to shelter within 5 minutes" |
| "Spawn a resource pickup" | "Different biomes contain different collectible resources. 8 inventory slots force choice." |
| "Create NPC trader" | "At least 3 NPCs must have a visible resource need. Giving the right resource unlocks a blueprint." |

**Test the rule, never the object.** A beat that checks "does Habitat exist?" tests nothing about survival.
A beat that checks "does O2 refill when the player returns?" tests the constraint.

## THE SUB-FEATURE DECISION RULE

Detail enters at the right level. A feature needs sub-features when ANY of these is true:

1. **The CONSTRAINT contains "AND" between independent systems.**
   → "O2 refills AND habitat is visible from 50m" is two constraints. Split them.

2. **The VERIFY beat needs multiple independent assertions.**
   → A compound beat fails for ambiguous reasons. Each assertion should collapse one box.

3. **A season fails at the feature level.**
   → Trainer produces a degenerate winner? The search space is too large. Decompose.

4. **The WORK says "AND" instead of "/".**
   → "Create a Blueprint AND train a domain" is two agent lanes. Split them.

**Decomposition is NOT pre-planned.** It emerges when an item hits a season boundary and can't pass.
The decomposer (`core/decomposer.py`) breaks it into parts; each part rides the normal conveyor.

## THE FARMING METHOD — execution rhythm

Every item runs through 4 seasons. Each season is a discrete batch process with explicit inputs,
procedure, and outputs. Any agent can run any batch. Nothing lives in memory.

```
SPRING (design)   → Saturate with questions → Spec
  Catalog elements, council debate, write spec.  docs/FARMING_SEASONS.md

SUMMER (build)    → Train / wire / compile   → Artifact
  Train domain, decode genome, compile, spawn.  docs/FARMING_SEASONS.md

FALL (verify)     → Beat / observe / collapse → Evidence
  Lint beats, run sleepwalker, record evidence. docs/FARMING_SEASONS.md

WINTER (reflect)  → Audit / distill / compact → Lesson
  Audit models, dream loop, gardener, hygiene. docs/FARMING_SEASONS.md
```

Full season recipes with exact commands: `docs/FARMING_SEASONS.md`

## FIRST ACTIONS (every session)

```powershell
cd E:\PythonChimera\Chimera
python -m core.preflight          # Live state: GPA, loops, CAPCOM, Will, pains
python -m core.capcom brief       # Operator signals
python -m core.helm targets       # Seed-vs-reality gaps
```

Read `task_progress.md` for the handoff from the last session.
Read `EMERGENCE_ROADMAP.md` for the current build sequence (7 items, in order).

## YOUR TOOLS (in order of power)

1. **Sleepwalker beats** — verify ANYTHING. Create a beat, run it, record evidence.
   ```powershell
   python -m core.beat_lint --beats docs/beats/<file>.beats.json  # lint first
   python -m core.sleepwalker --beats docs/beats/<file>.beats.json --session <name>
   ```

2. **MCP bridge** — query/spawn/move/screenshot in UE5:
   ```python
   from core.telemetry_probe import MCPStdioClient
   c = MCPStdioClient()
   c.call('control_actor', {'action': 'find_by_name', 'name': 'Player'})
   ```

3. **DNA graph** — query feature state, record observations:
   ```powershell
   python -m core.graphify_record observe --feature X --verdict accepted --derived-from <simtest_id> --tacit --loop N
   ```

4. **Council** — two-model dialectical design (needs LM Studio with model loaded):
   ```powershell
   python -m core.council "<design problem>" --rounds 2 --record
   ```

5. **Foundry pipeline** — council → bridge → forge → proving ground:
   ```powershell
   cd E:\PythonChimera\worker_bridge
   python run.py --topic "<problem>" --turns 2
   ```

6. **Training loop** — train any domain with automatic model audit:
   ```powershell
   python -m core.train_loop erisaid_mirror       # train + audit any domain
   python -m core.train_loop npc_behavior
   python -m core.train_loop economy_engine
   ```

7. **Element catalog** — 69,718 trainable variables from UE5.8:
   ```powershell
   python core/element_catalog.py                  # rebuild/expand the catalog
   python -c "import json; c=json.load(open('docs/element_catalog.json')); print(c['total_elements'])"
   ```

8. **Decoder** — convert trained genomes to game artifacts:
   ```python
   from core.decoder import apply_genome, decode_to_beat
   result = apply_genome(trained_genome, 'erisaid_mirror')  # genome -> MCP commands
   beat = decode_to_beat(trained_genome, 'erisaid_mirror')   # genome -> beat script
   ```

9. **Farm launcher** — dispatch sub-agents with correct model per season:
   ```powershell
   python core/farm_launcher.py SPRING "<design topic>"  # deepseek-v4-pro (smart)
   python core/farm_launcher.py SUMMER                   # local LM Studio (free)
   python core/farm_launcher.py FALL                     # local LM Studio (free)
   python core/farm_launcher.py WINTER                   # local DS4 (free)
   ```
   Edit `docs/season_models.json` to switch models per season.

## NEVER DO

- **Never edit** `Source/Chimera/ProceduralGenerated/` — fix the generator instead (but DemoPlayerController.cpp is the pragmatic exception)
- **Never trust `success: true`** — read the value back. No read-back = not done.
- **Never place a cube.** If you find yourself authoring a form (mesh, actor, level placement) instead of writing a constraint, stop. You are doing the old way. The form should emerge from a trained constraint, not your MCP call.
- **Never skip the formula.** Every item gets CONSTRAINT → MEASURE → EXISTING → WORK → VERIFY. Items without a constraint are wishes.
- **Never decompose in advance.** Sub-features emerge when a season fails. Pre-splitting is guessing.
- **Never declare something "MCP can't do" without FIRST checking available actions.**
  ```python
  from core.telemetry_probe import MCPStdioClient; c = MCPStdioClient()
  # Try the action. If it fails, try variants. If all fail, THEN it's blocked.
  # Never assume. Always verify.
  ```
- **Never run MCP without the editor running.** If you just built, relaunch: `chimera_unblock(ensure="editor")`
- **After editor crash/restart, always verify MCP is responsive before running sleepwalker:**
  ```python
  from core.telemetry_probe import MCPStdioClient; c = MCPStdioClient()
  c.call('inspect', {'action': 'get_scene_stats'})  # must return True
  ```
- **Check for editor crash reports after every build/restart.**
  ```powershell
  dir "C:\Program Files\Epic Games\UE_5.8\Engine\Saved\Crashes\" | Sort-Object LastWriteTime -Descending | Select-Object -First 5
  ```
  If the editor crashed during your session, the MCP bridge may be in a bad state.
  Kill the editor, restart, and verify before proceeding.
- **Never take screenshots without foregrounding the editor first**:
  ```powershell
  powershell -NoProfile -Command '$ws = New-Object -ComObject WScript.Shell; $p = Get-Process UnrealEditor | Where-Object {$_.MainWindowTitle} | Select-Object -First 1; if ($p) { $ws.AppActivate($p.Id) | Out-Null }'
  ```
- **Never use W-key walks in beats** — `simulate_input` doesn't drive axis bindings in PIE. Use `reset_position` to place the pawn directly.
- **Never use `_C` suffix for Blueprint paths** — use asset form: `/Game/X/BP_Y.BP_Y`
- **Never fabricate simtest IDs** — real IDs are `<type>_<sha256[:16]>`, minted by sleepwalker/record helpers
- **Never stop at "task done"** — ask the next question

## CURRENT GAME STATE (2026-07-21)

- **Player**: BP_Astronaut_Character with 22 components: SuitLifeSupportComponent (O2/battery/dust ticking), PickupComp (E to pickup), SacrificeLogComponent, FootprintComponent, WeatherComponent, and more
- **Survival loop**: Compiled and verified. O2 drains at exertion rates (idle 6/min, walk 15/min, sprint 40/min). Refill via bAtOxygenGarden flag. WID_O2HUD created on possession.
- **Habitat**: UShelterHabitatComponent compiled. Creates sphere trigger, sets refill flags on overlap. Not yet placed in level (blocked by MCP CLASS_NOT_FOUND for C++ classes — needs Blueprint child).
- **NPCs**: 41 BP_NPC_Basic in the level with Tab-gesture interaction
- **Erisaid**: 3 AErisaidActor at center (0,0,150) — the moral core, Environmental Catalyst
- **Pickups**: 66 BP_Verb_PickUp actors in the level. Need to verify they function as collectible resources.
- **Sacrifice**: USacrificeLogComponent records GAVE_CARGO on drop near Erisaid (2000uu radius). 8 trained SACRIFICE_WEIGHTS loaded.
- **Level**: 230 actors saved in chimeradefaultlevel.umap
- **Loops done**: 0 (Player), 1 (Ground), 2 (Verbs), 3 (Sky), 4 (Tools), 5 (Dots), 9 (Universe)
- **Loops open**: 6 (Shelter: 4/7), 7 (Travel: 2/7)
- **Catalog**: 69,749 elements across 10 sources
- **Domains**: 21 trainable, all 0% stuck, objectives written
- **Roadmap**: EMERGENCE_ROADMAP.md — 7 items in order: survival → resources → habitat → emergent form → NPC needs → fabricator → beacon

## QUICK VERIFICATION

Before claiming anything works, run a beat:
```json
{
  "demo": "my_test", "loop": 0, "settle_s": 4,
  "beats": [{
    "name": "test", "features": ["Feature_X"],
    "actions": [{"reset_position": {"x": 0, "y": 0, "z": 130}}, {"wait": 1.0}],
    "expects": [{"is_pie": true}, {"actor_exists": "ActorName"}]
  }]
}
```

Record evidence: `python -m core.graphify_record observe --feature X --verdict accepted --derived-from <simtest_id> --tacit --loop N`

Level must be saved after spawning: `c.call('manage_level', {'action': 'save'})`

## DOCS TO KNOW

| File | What it is |
|---|---|
| `CLAUDE.md` | Constitution, gates, all systems |
| `SUCCESSOR_RUNBOOK.md` | Recipes, traps, proven commands |
| `WORKFLOW.md` | Foundry design methodology + rhythm |
| `EMERGENCE_ROADMAP.md` | **The build sequence** — 7 constraint-first items in order. Read this first after preflight. |
| `CHIMERA_VISION.py` | The seed — 4560 lines, complete game architecture |
| `task_progress.md` | Session handoff log |
| `docs/FARMING_SEASONS.md` | Seasons workflow — discrete batch processes any agent can run |
| `docs/GENERATION_PROTOCOL.md` | Circadian rhythm, automated Gardener, observation loop |
| `docs/THE_STATE_MACHINE_PHYSICS.md` | Elements + principles + AI trainer framework |
| `docs/THE_EVOLUTION_ENGINE.md` | The trainer: 30,000 evals/sec, proven at every scale |
| `docs/TRAINING_PROTOCOL.md` | Three-part split, honest evaluation, the exploits |
| `AGENTS.md` | Research agent, subagent delegation, session recipe |

## THE ULTIMATE GOAL

A space survival game where the mechanics produce the meaning.

You are an astronaut on an alien world. Your suit has O2, battery, and dust filters. All of them drain. You must leave the habitat to find resources. Different biomes contain different resources. You can help other stranded astronauts by giving them resources from your inventory. They have nothing to give in return — but helping them unlocks blueprints you cannot get any other way.

The beacon on the highest peak needs components from those blueprints. A costless playthrough produces a dim signal. A generous one produces a strong signal.

**Build toward this. Test the rule, never the object. Never place a cube.**
