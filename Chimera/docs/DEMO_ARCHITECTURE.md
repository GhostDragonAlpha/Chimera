# Demo Architecture — Regolith Yard (Demo 1) + Titan Run (Demo 2)

> **STATUS 2026-07-07**: Phase 1 EXECUTED (grade A 98.5) — the yard is built, saved
> (umap md5 BF835B43...), and walkable; Session A awaits the human. An input hotfix added
> `Source/Chimera/ProceduralGenerated/Demo/DemoPlayerController + DemoOnFootGameMode`
> (the astronaut BP had ZERO input wiring — surprise_2b3d79676e3d4206); WorldSettings
> currently points at DemoOnFootGameMode, so Phase 2's GameMode surgery must either fold
> these bindings into the generated GameMode or keep the demo mode for on-foot play.
> Phase 1 item 2's WorldSettings write is PROVEN (MCP pathway 22). `core/witness.py`
> (Phase 2 item 4) is SUPERSEDED by `core/witness.py`; the Sleepwalker
> (`core/sleepwalker.py` + docs/beats/regolith_yard.beats.json) now walks these beats
> automatically — 5/5 clean on 2026-07-07.
>
> **UPDATE 2026-07-07 (late)**: Phase 2 generator work LANDED via duty session (DemoTerminal.h/cpp,
> GameMode astronaut DefaultPawnClass + double-spawn deletion + terminal self-spawn, MissionComponent
> payout — commit c1be3cd; ke-verification suite still pending -> Phase 3). CORRECTION to the risk
> table: the original walkabout was NOT lost to unsaved editor state — build_orchestrator template-
> stamped the level on every build (fixed seed-only; see MCP_PATHWAYS #27). Protected copy:
> L_RegolithYard.umap. Yard restored and sleepwalk-verified 5/5 after tonight's clobber.

## 1. Purpose

Features finish only under human eyes. Twenty sit in the Observation queue as `[DONE*]`; the protocol closes them when the Gardener plays a build and gives a few-sentence holistic temperature, which the agent then attributes across the queue with provenance (direct quote / tacit / untouched — reversible by one human sentence). No demo, no verdicts: the demo is the collapse instrument.

This is a two-demo program. **Demo 1 — Regolith Yard** closes all 20 queue features in two ~10-minute sessions, with the first playtest after ONE duty cycle and zero compiles. **Demo 2 — Titan Run** (named, scheduled, cycles 4–6) is the fly–dock–trade–deliver loop the user's directive asks for (flight + economy + missions), built on the GameMode and mission-payout fixes Demo 1's Phase 2 lands. No combat anywhere.

## 2. The Demo (Regolith Yard)

The human spawns as the finished astronaut (suit, gold visor) on a 60m tri-pad yard assembled into the open `chimeradefaultlevel` and **saved this time**: metal apron, rock field, sand basin with drifting particulate, floored with the real-but-never-placed `MAT_MetalSurface` / `MAT_RockSurface` / `MAT_GroundSand`. A pedestal "display suit" (second, unpossessed `BP_Astronaut_Character`) guarantees close inspection of model/suit/visor regardless of the possessed pawn's camera. Props: weapon tool on a crate, shovel targets on all three surfaces. Session B adds one kiosk — `ADemoTerminal` — running the *real* generated systems unmodified: `UEconomyManager` DSL prices with live fluctuation, `UInventoryTradeComponent` buy/sell, `UFactionComponent` standing, `USaveGameComponent` slot round-trip, `UMissionComponent` accept→deliver→payout. `core/witness.py` records `[DEMOBEAT]` log lines during both sessions.

**Script (~10 min; Session A = beats 1–8 after Phase 1; Session B = beats 9–10 after Phase 3):**

| # | Beat | Direct features | Tacit |
|---|---|---|---|
| 1 | Spawn on metal apron; 360° look; walk 10 steps | Verb_Look, Verb_Step, Ground_Metal_Surface | Player_Character_Animation, _Lighting |
| 2 | Orbit pedestal display suit; inspect helmet/visor/seams | Player_Character_Model, _Suit, _Model_Visor_Apply, _Lighting | — |
| 3 | Walk metal → rock → sand, watching feet/gait per surface | Verb_Step, Player_Character_Animation, Ground_Rock_Surface, Ground_Sand_Surface | — |
| 4 | Stand in sand basin; watch drift emitter | Ground_Sand_Particles | — |
| 5 | Bend (key from recipe brief) | Verb_Bend | — |
| 6 | Pick up weapon tool from crate; examine in hand | Verb_PickUp, Tool_Weapon_Model | — |
| 7 | Carry to rock pad; drop | Verb_Drop | — |
| 8 | Shovel once per surface; **give temperature #1** | Verb_Shovel | all 3 surfaces |
| 9 | (B) Kiosk: watch prices fluctuate; E buys 100 Titanium (credits drop by 100×live price); standing rises; F5 save; sell all, buy junk; F9 → snap-back | System_Economy, System_Factions, System_SaveLoad | — |
| 10 | (B) Kiosk mission key: accept `Delivery_Titanium_Batch_1`, deliver 500 Titanium, dock objective completes, **+25,000cr payout lands in credits**; **temperature #2** | System_Missions | System_Economy |

Pre-brief (read to the Gardener before each session): "Audio is silent — footsteps BLOCKED-ON-ASSETS, out of scope. The kiosk is a systems test bench, not the shipped trade UI."

## 3. Queue Coverage (20/20)

| Feature | How exercised | Tier |
|---|---|---|
| Player_Character_Model | Beat 2 pedestal inspection | direct |
| Player_Character_Suit | Beat 2 | direct |
| Player_Character_Model_Visor_Apply | Beat 2 | direct |
| Player_Character_Lighting | Beats 1–2 | direct |
| Player_Character_Animation | Beat 3 gait | direct |
| Ground_Metal_Surface | Beats 1, 8 | direct |
| Ground_Rock_Surface | Beats 3, 8 | direct |
| Ground_Sand_Surface | Beats 3, 8 | direct |
| Ground_Sand_Particles | Beat 4 | direct |
| Verb_Look | Beat 1 | direct |
| Verb_Step | Beats 1, 3 | direct |
| Verb_Bend | Beat 5 | direct |
| Verb_PickUp | Beat 6 | direct |
| Verb_Drop | Beat 7 | direct |
| Verb_Shovel | Beat 8 | direct |
| Tool_Weapon_Model | Beat 6 | direct |
| System_Economy | Beat 9 live prices/buy/sell | direct |
| System_Factions | Beat 9 standing rise | direct |
| System_SaveLoad | Beat 9 F5/F9 round-trip | direct |
| System_Missions | Beat 10 accept→deliver→payout | direct |

Tacit claims are made only if the witness timeline or a quote can timestamp the exercise (honest-tacit rule). Untouched stays untouched.

## 4. Technical Architecture

**Real today (recon-verified):** system logic is real and unit-tested; wiring is absent. Every initializer (`BuildEconomy`, `InitializeMissionBoardFromDSL`, factions `InitializeFromDSL`, save calls, `UInventoryTradeComponent` instantiation) lives only in Tests/ — PIE constructs none of it. GameMode double-spawns invisible ships at permanent full throttle (cpp:72–86), spawns stations as empty `AActor::StaticClass()` (:99/:115/:131); zero input bindings project-wide; no mission payout path exists. Assets: astronaut BP is real and finished; ground materials exist unused; EnhancedInput exists for on-foot only (`IMC_Default`); no ship/station meshes; all prior walkabout level content was lost unsaved.

**What gets built, by ownership lane:**

| Lane | Item |
|---|---|
| Level content (MCP, cosmetic-only) | Pads, pedestal, display suit, crate, props, Niagara drift — spawned via proven pathways, then save-proof ritual. Loseable without killing the demo. |
| Manual file (Interactions/ = hand-editable) | `Source/Chimera/ProceduralGenerated/Interactions/DemoTerminal.h/.cpp` — *uses* generator-owned classes, edits none. |
| Generator (`core/game_code_generator.py`) | GameMode template: astronaut `DefaultPawnClass` via `FClassFinder` (ship fallback), delete double-spawn block, `AStationActor` spawns, guarded BeginPlay self-spawn of `ADemoTerminal`. MissionComponent template: payout branch → `AddCredits(RewardCredits)`. Tests emitted in the same change (H-1/H-12). |
| New tooling | `core/witness.py` (reuses `MCPStdioClient` from `core/telemetry_probe.py`). |
| DSL | No changes for Demo 1. Demo 2 requires one content decision (mission destination, §5). |

**Self-assembly principle (D1):** every demo-CRITICAL actor is constructed at BeginPlay by the generated GameMode (astronaut pawn via DefaultPawnClass; DemoTerminal via guarded spawn). A lost level costs dressing, never the demo — the exact failure that erased the walkabout.

**Input-from-zero:** Demo 1 needs no new input. The possessed astronaut uses its existing EnhancedInput (`IMC_Default`); the kiosk uses `EnableInput(PC)` + `BindKey` (E/Q/F5/F9/M) on the terminal actor for the human, and `UFUNCTION(Exec)` wrappers invoked via `ke <ActorName> <Func>` for agent verification — plain `DemoBuy` in console will NOT route to a world actor (verified exec-chain flaw; `ke` is the fix). Demo 2 binds ship input via generator-emitted legacy `BindAxis` + `Config/DefaultInput.ini` appends (primary, weak-debuggable); runtime EnhancedInput is the experiment slot only.

## 5. Build Plan (one duty cycle per phase; every item executable without searching)

### PHASE 1 — Yard assembly, zero build (weak-model OK) → **FIRST PLAYTESTABLE**

1. Fetch recipes/trigger keys into the session brief. For each of `Ground_Sand_Particles`, `Tool_Weapon_Model`, `Verb_Step`, `Verb_Bend`, `Verb_PickUp`, `Verb_Drop`, `Verb_Shovel`:
   `python -c "from core.graphify_interface import graphify_query; import json; print(json.dumps(graphify_query('feature','Ground_Sand_Particles'), default=str, indent=1))"` (swap identifier; use `'pathway'` query for placement recipes).
2. Neutralize buggy GameMode: `control_actor set_property` on WorldSettings, `DefaultGameMode=/Script/Engine.GameModeBase`; **read back**. Skip-condition: property not settable → record surprise (`python -m core.graphify_record surprise --context "WorldSettings DefaultGameMode via bridge" --reality "<error field>" --source agent`), pull Phase 2 forward, first playtest slips one cycle.
3. Spawn 3 pads: `control_actor spawn_actor actorName=Pad_Metal classPath=/Engine/BasicShapes/Plane.Plane location=(0,0,0)` (then `Pad_Rock` at (2000,0,0), `Pad_Sand` at (4000,0,0)); `set_property RelativeScale3D=(20,20,1)`; `control_actor set_material` with `/Game/Chimera/Materials/MAT_MetalSurface|MAT_RockSurface|MAT_GroundSand`; **read back material paths**. Skip-condition: BasicShapes path fails → `manage_asset search_assets directory=/Game/ classNames=["StaticMesh"]`, use `SM_Track_10M` (proven pathway 1) scaled flat.
4. Spawn possessed astronaut: `control_actor spawn_actor actorName=Player_Astronaut classPath=/Game/Characters/Astronaut/BP_Astronaut_Character location=(0,0,120)`; `set_property AutoPossessPlayer=Player0`; read back. **Never `control_editor possess`** (trap, re-confirmed 2026-07-06).
5. Spawn pedestal cube at (600,600,0) + display suit: second `BP_Astronaut_Character`, `AutoPossessPlayer=Disabled`, on top; read back.
6. Sand drift: spawn stock Niagara template over Pad_Sand exactly per the `Ground_Sand_Particles` node recipe — **spawn-only, never author** (authoring facade trap).
7. Weapon tool on crate cube at (400,−400,50); stage PickUp/Drop/Shovel targets exactly per verb node recipes.
8. **Save-proof ritual**: `control_editor save_all` → savedCount≥1; then `Get-FileHash -Algorithm MD5 E:\PythonChimera\Chimera\Content\Levels\chimeradefaultlevel.umap` → hash ≠ `B734CFF5B6D6343B7A2BCCA43A1CB756`, mtime today; then reopen the level and `inspect get_scene_stats` → actor count matches pre-save count.
9. PIE smoke: `inspect runtime_report` → exactly one pawn, class `BP_Astronaut_Character_C`, isPIE true; `python -m core.telemetry_probe --out t.json --soak 30` **FOREGROUNDED**; ≤1 `control_editor screenshot mode=editor_viewport filename=regolith_yard_p1`.
10. Grade + close: ev.json with `criteria_total:8` (3 material read-backs, pawn possession, display suit present, Niagara actor exists, umap hash delta + recount, single-pawn PIE), `ran_in_editor:true`, telemetry from t.json, 5 checklist bools, spec_fidelity = recipe-conformance fraction. `python -m core.result_grader --feature Demo_RegolithYard_L1 --evidence ev.json`; postflight. → **HUMAN SESSION A (16/20).**

### PHASE 2 — Terminal C++, generator surgery, witness (items 1–4 **capable sessions only**; 5 weak-OK)

1. Write `Interactions/DemoTerminal.h/.cpp` (manual lane). `ADemoTerminal : AActor`: kiosk StaticMesh + subobjects `UEconomyManager`, `UInventoryTradeComponent`, `UFactionComponent`, `USaveGameComponent`, `UMissionComponent`. BeginPlay: `UEconomyInitializer::BuildEconomy(Econ); Trade->SetCredits(10000.f); Factions->InitializeFromDSL(); Missions->InitializeMissionBoardFromDSL(); EnableInput(PC)` + BindKey E/Q/F5/F9/M. `UFUNCTION(Exec)` `DemoStatus/DemoBuy(int32)/DemoSell(int32)/DemoSave/DemoLoad/DemoMission` wrapping verified APIs: `BuyCommodity(FName("Titanium"), Qty, Econ->GetCommodityPrice("Titanium"))`, `Factions->NotifyTradeCompleted(FName("faction_orbital_council"), Cost)` (FName verified at FactionComponent.cpp:28), `Save->SaveGame("DemoSlot")/LoadGame("DemoSlot")`; `DemoMission`: `AcceptMission(FName("Delivery_Titanium_Batch_1")); UpdateObjective(TEXT("Deliver"), TEXT("Titanium")); UpdateObjective(TEXT("Dock"), TEXT("Orbital_Hub_7"))` (signatures verified MissionComponent.h:27–33; objective types verified cpp:25/:33). Every state change emits `UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] ..."))` with values; Tick draws debug lines (price/credits/cargo/standing/mission) when pawn <800uu. Grep-first discipline: match all signatures verbatim before writing. No Build.cs edit.
2. Generator — GameMode template: `FClassFinder` on `/Game/Characters/Astronaut/BP_Astronaut_Character` → `DefaultPawnClass` (ship fallback if null); **delete** second-ship spawn/re-possess block (generated cpp:72–86); station spawns → `AStationActor::StaticClass()` (:99/:115/:131); guarded self-spawn `if (!UGameplayStatics::GetActorOfClass(GetWorld(), ADemoTerminal::StaticClass())) SpawnActor<ADemoTerminal>` at (500,−500,20). Emit matching test in the same change.
3. Generator — MissionComponent template: in the completion path, `if (auto* Inv = GetOwner()->FindComponentByClass<UInventoryTradeComponent>()) Inv->AddCredits(M.RewardCredits);` (`AddCredits(float)` verified InventoryTradeComponent.h:67; faction hook already exists). Emit test. Record any C2039 as template drift with UBT file:line verbatim (H-1/H-12).
4. Write `core/witness.py`: reuse `MCPStdioClient` from `core/telemetry_probe.py`; tail `Saved/Logs/Chimera.log` for `[DEMOBEAT]`, poll `inspect runtime_report` every 10s; emit beat-timeline JSON. CLI: `python -m core.witness --session A --out beats_A.json`.
5. Regenerate; build: `& "C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" ChimeraEditor Win64 Development "E:\PythonChimera\Chimera\Chimera.uproject" -waitmutex` → UBT 0 gate; `record_build` with verbatim output; postflight.

### PHASE 3 — Wire, verify, Session B (weak-OK; recipes inline)

1. Restore fixed GameMode: `control_actor set_property` WorldSettings `DefaultGameMode=/Script/Chimera.DeepSpaceTraderGameMode`; read back. PIE → `inspect runtime_report`: pawn class `BP_Astronaut_Character_C`, exactly one pawn (contingency: if the placed AutoPossess pawn duplicates the default pawn, delete the placed one — DefaultPawnClass now covers spawning); `control_actor find_by_class` → `ADemoTerminal` present (self-spawned); **record exact actor name `<T>`**.
2. Console verification — **route via `ke`, never bare exec** (verified: Exec on a world actor is unreachable through the console chain): `ke <T> DemoStatus` → parse price P and credits 10000 from `[DEMOBEAT]` log lines; `ke <T> DemoBuy 100` → credits==10000−100P, cargo==100, standing>0; `ke <T> DemoSave` → `Test-Path E:\PythonChimera\Chimera\Saved\SaveGames\DemoSlot.sav` is true; `ke <T> DemoSell 100` then `ke <T> DemoBuy 40` then `ke <T> DemoLoad` → credits/cargo/standing == saved snapshot (sibling-component serialization verified SaveGameComponent.cpp:24–55); `ke <T> DemoMission` → `[DEMOBEAT] MISSION_COMPLETE` + credits +25000. **criteria_total:7, all measured** (H-13: every declared criterion tested, no partial coverage).
3. `control_editor save_all` + hash/recount recheck; PIE + `python -m core.telemetry_probe --out t2.json --soak 30` foregrounded; ev.json → `python -m core.result_grader --feature Demo_RegolithYard_Systems --evidence ev.json`; regenerate Session B handoff card (attribution skeleton, §6); postflight. → **HUMAN SESSION B (20/20).**

### DEMO 2 — "Titan Run" (scheduled, cycles 4–6; recipes written at each cycle's start per handoff invariant)

Prerequisite (capable): add `generate_station_actor` and `generate_inventory_trade` methods to `core/game_code_generator.py` **before** substantively touching StationActor or attaching `UInventoryTradeComponent` to the ship template (migration discipline). Content decision first: both `Delivery_Titanium_Batch_1` objectives target Orbital_Hub_7 and `UpdateObjective` ignores the station field — script becomes buy-at-Ares → deliver-to-Orbital_Hub_7, or the DockingComponent template passes the docked station name and the objective match checks `Obj.Station` (DSL/template decision, capable-only).
- **Cycle 4 — Flight input** (capable): FlightComponent input API via generator (replace hardcoded inputs cpp:27–30, apply the computed-but-discarded rotation :50–53, route DSL params through `InitializeFromShip`, add fuel burn); ship `SetupPlayerInputComponent` via generator; legacy `BindAxis` + `Config/DefaultInput.ini` appends; **bind ALL Demo 2 keys in this one cycle**; assign ShipMesh asset.
- **Cycle 5 — Dock + trade**: DockingComponent state machine template replacing the 7-line stub (proximity → docked → `UpdateObjective(TEXT("Dock"), <station>)`); station greybox meshes + `RegisterComponent`/`SetStaticMesh` fixes via `generate_station_actor`; buy/sell at `StationTradingData` prices through the ship's inventory component.
- **Cycle 6 — Mission + HUD + save**: station-side accept/deliver (payout template already live from Phase 2); `generate_hud` → `ADeepSpaceTraderHUD` Canvas `DrawText` (zero UMG/BP — also the upgrade path if the kiosk's debug lines read crude in Session B); F5/F9 ship-side; third human session (flight temperature).
- Pre-declared escape hatch: if possession handover fails rehearsal, two-map `OpenLevel` split (yard map / flight map) — costs the continuous arc, saves the verdicts.

## 6. Observation Intake Plan

Run the witness during every session: `python -m core.witness --session A --out beats_A.json`. After the human plays and gives their temperature:

1. `python -m core.graphify_record playtest --notes "<their EXACT words>"` → save returned `<playtest_id>`.
2. Directly mentioned features: `python -m core.graphify_record observe --feature <X> --verdict <accepted|rejected> --notes "<their words>" --derived-from <playtest_id> --quote "<their exact phrase>" --loop <N>`
3. Exercised-but-unmentioned (witness timeline proves exercise): same command with `--verdict accepted --tacit` instead of `--quote`. Untouched: leave alone.
4. Present the attribution table for one-sentence overrules; end the report with it:

| Feature | Tier | Evidence (quote or witness timestamp) |
|---|---|---|
| e.g. Verb_Step | direct | "the walking feels floaty" |
| e.g. Ground_Rock_Surface | tacit | beats_A.json T+04:12 entered rock pad |

The handoff card given to the Gardener before each session pre-fills this skeleton (feature | expected beat | quote slot) plus the two pre-brief lines from §2. Agents never originate verdicts; rejections → `needs_refinement` (first-priority dream fodder). Witness downgrades any unexercised "tacit" claim to untouched.

## 7. Risks & Traps

| Trap / risk | Mitigation |
|---|---|
| Niagara authoring facade (fake success) | Spawn stock template per node recipe only; never author |
| `control_editor possess` fakes success | Placed-pawn AutoPossess (Phase 1) + DefaultPawnClass (Phase 2); verify via `runtime_report` |
| `success:true` lies | Every spawn/set followed by MCP read-back |
| Walkabout lost unsaved (happened once) | Save-proof ritual: `save_all` + md5 ≠ `B734...` + mtime + reopen/recount; GameMode self-assembles critical actors |
| GameMode double-spawn steals possession | Phase 1 WorldSettings override; Phase 2 deletes the block in the template |
| Exec-chain routing (verified flaw) | All verification via `ke <ActorName> <Func>`; human uses BindKey keys |
| `WorldSettings.DefaultGameMode` write unproven | Skip-condition + fallback: reorder Phase 2 first; playtest slips one cycle (accepted, honest) |
| `/Engine/BasicShapes/Plane` spawn unproven | `search_assets` fallback → `SM_Track_10M` (proven pathway 1) |
| Kiosk reads "debug bench" → sour temperature | Pre-brief framing line; Canvas HUD named upgrade path; accepted residual risk |
| Systems observed foot-side may need re-observation ship-side | **Accepted**: queue closure now outweighs perfect context; Titan Run re-exercises them and the protocol permits re-observation |
| H-13 (Economy C/F: partial coverage, unmeasured fps) | 7 criteria all `ke`-verified in-editor; foregrounded soak both phases |
| Audio empty (BLOCKED-ON-ASSETS) | Pre-brief "sound out of scope"; CC0 import stays a human task |
| Template drift C2039 on regen | Tests emitted with each template change; UBT file:line recorded verbatim |

**Top unknowns:** (1) BP_Astronaut input/camera completeness in PIE — collapses on day one via Phase 1 smoke, before any human minute; the display suit guarantees Model/Suit/Visor verdicts regardless; contingency capable-item: wire `IMC_Default`. (2) Verb trigger keys/targets — resolved by Phase 1 item 1 recipe fetch. (3) `ke` availability in the bridge's `console_command` — verify with `ke <T> DemoStatus` as the first Phase 3 call; failure → move Exec wrappers onto the GameMode (in the exec chain) via the template.

**Explicitly NOT in this demo (user scope):** no combat (weapon is a prop model only — no firing, no damage, no pirates); no ship flight until Titan Run; no UMG trade UI (Canvas HUD is the named path); no audio.

## 8. Provenance

Local-model draft absorbed for its economy/mission/trade beat structure; its fatal gaps (no input existed at all, no level content, no on-foot coverage, no observation protocol) drove the queue-first reframe. Panel winner D2 "Regolith Yard" provides the skeleton. Grafts applied: D4's demo_witness; D3's GameMode surgery (astronaut FClassFinder, double-spawn deletion, AStationActor spawns) and handoff-card skeleton; D1's mission-payout template (takes 19/20 → 20/20), self-assembling GameMode, migration discipline, Canvas HUD path, grep-first-verbatim rule, and honest-tacit rule; D3/D4's legacy-input-primary recipe and OpenLevel escape hatch for Titan Run. All judge fatal-flaw warnings fixed in-plan (`ke` exec routing, missions un-deferred, named Demo 2 for flight scope, unproven-pathway skip-conditions) or explicitly accepted with reason (foot-side systems context; one-cycle playtest slip if the WorldSettings write no-ops).
