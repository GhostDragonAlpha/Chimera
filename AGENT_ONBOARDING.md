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

## FIRST ACTIONS (every session)

```powershell
cd E:\PythonChimera\Chimera
python -m core.preflight          # Live state: GPA, loops, CAPCOM, Will, pains
python -m core.capcom brief       # Operator signals
python -m core.helm targets       # Seed-vs-reality gaps
```

Read `task_progress.md` for the handoff from the last session.

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
- **Never take screenshots without foregrounding the editor first**:
  ```powershell
  powershell -NoProfile -Command '$ws = New-Object -ComObject WScript.Shell; $p = Get-Process UnrealEditor | Where-Object {$_.MainWindowTitle} | Select-Object -First 1; if ($p) { $ws.AppActivate($p.Id) | Out-Null }'
  ```
- **Never use W-key walks in beats** — `simulate_input` doesn't drive axis bindings in PIE. Use `reset_position` to place the pawn directly.
- **Never use `_C` suffix for Blueprint paths** — use asset form: `/Game/X/BP_Y.BP_Y`
- **Never fabricate simtest IDs** — real IDs are `<type>_<sha256[:16]>`, minted by sleepwalker/record helpers
- **Never stop at "task done"** — ask the next question

## CURRENT GAME STATE (2026-07-20)

- **Player**: BP_Astronaut_Character with 6 working verbs (look, crouch, pickup, drop, shovel, interact)
- **NPCs**: 36 in the yard with Tab-gesture interaction
- **Erisaid**: AErisaidActor at center (0,0,150) — the moral core, Environmental Catalyst
- **Core loop**: Pick up item → drop at Erisaid → sacrifice recorded → sun brightens → NPCs react → auto-transition
- **Sacrifice**: USacrificeLogComponent records GAVE_CARGO on drop near Erisaid (2000uu radius)
- **Generation**: Auto-transition wired in DemoPlayerController DropItem
- **Education**: LEARN messages on pickup (Multitool, Basalt, Granite). 64+ labeled specimens.
- **Level**: 229 actors saved in chimeradefaultlevel.umap
- **Loops done**: 0 (Player), 1 (Ground), 2 (Verbs), 3 (Sky), 4 (Tools), 5 (Dots), 9 (Universe)
- **Loops open**: 6 (Shelter: 4/7), 7 (Travel: 2/7)
- **Catalog**: 69,749 elements across 10 sources
- **Domains**: 21 trainable, all 0% stuck, objectives written
- **Framework**: State machine physics (docs/THE_STATE_MACHINE_PHYSICS.md)
- **Model routing**: Edit docs/season_models.json to switch models per season
- **Launcher**: python core/farm_launcher.py SPRING|SUMMER|FALL|WINTER

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
| `CHIMERA_VISION.py` | The seed — 4560 lines, complete game architecture |
| `task_progress.md` | Session handoff log |
| `docs/FARMING_SEASONS.md` | Seasons workflow — discrete batch processes any agent can run |
| `docs/THE_STATE_MACHINE_PHYSICS.md` | Elements + principles + AI trainer framework |
| `docs/THE_EVOLUTION_ENGINE.md` | The trainer: 30,000 evals/sec, proven at every scale |

## THE ULTIMATE GOAL

The most famous educational RPG on Steam. Deep Space Trader. Every finished life becomes a star whose brightness equals what that life sacrificed. The bad ending is not death — it is a costless life. The Erisaid mirror shows your desire, and an empty life reflects nothing.

Build toward this. Ask questions. Never stop.
