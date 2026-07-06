# Demo Architecture — Hybrid Walkabout + Trader Loop (Two-Act Demo)

## 1. Purpose

This demo architecture is designed to close the 20-feature observation queue by presenting the human Gardener with a coherent, ~10-minute playable experience that exercises both the on-foot astronaut content and the trader ship systems. The protocol requires that features only finish under human eyes: the human plays a build and gives a few-sentence holistic "temperature" reading, which the agent then ATTRIBUTES across the observation queue (direct quote / tacit / untouched). Features complete only when the human's verdicts arrive.

The demo is structured in two acts: **Act 1** exercises the 16 on-foot astronaut features (player model, suit, lighting, visor, ground surfaces, verbs, and tool models) through a walkabout experience at a verified outpost location. **Act 2** transitions to the ship possession state where the human flies the Trader_Vessel_Alpha, docks at Orbital_Hub_7, trades commodities, accepts and completes a mission, and saves progress. This two-act structure ensures maximum queue coverage per human minute while respecting the generator-owned rules and known bridge traps.

## 2. The Demo (Playtest Script)

**Act 1: On-Foot Walkabout (~5 minutes)**
1. Spawn as BP_Astronaut_Character0 at L_VerificationStudio or chimeradefaultlevel. Human walks across metal, rock, and sand surface patches. *(Exercises: Player_Character_Model, _Suit, _Animation, _Lighting, _Model_Visor_Apply, Ground_Metal_Surface, Ground_Rock_Surface, Ground_Sand_Surface)*
2. Human exercises verbs: look around (camera/viewport), step/walk across surfaces, bend (interact prompt appears), pick up a sample object, drop it, and use the shovel tool on sand patches. *(Exercises: Verb_Look, Verb_Step, Verb_Bend, Verb_PickUp, Verb_Drop, Verb_Shovel, Ground_Sand_Particles)*
3. Human inspects the weapon tool model in hand or via interaction prompt. *(Exercises: Tool_Weapon_Model)*

**Transition: Ship Possession (~1 minute)**
4. Human interacts with a ship boarding trigger or presses a designated key (e.g., 'E') to possess AShip_Trader_Vessel_Alpha. The camera transitions from first-person astronaut view to the ship's fixed camera (z+200, -15deg pitch). *(Tacit coverage: System_SaveLoad if save prompt appears during transition)*

**Act 2: Trader Loop (~4 minutes)**
5. Human flies the Trader_Vessel_Alpha using newly-added flight input bindings (thrust/steering via keyboard axes). Navigates to Orbital_Hub_7 or Ares_Market_Central. *(Exercises: System_Factions via station identity)*
6. Human docks at a station, triggering docking proximity logic and opening the trade UI. *(Exercises: System_Economy via commodity prices from EconomyManager/StationTradingData)*
7. Human buys/sells commodities (e.g., Titanium, Quantum_Cores) using InventoryTradeComponent. *(Exercises: System_Missions if a delivery mission is active)*
8. Human accepts Delivery_Titanium_Batch_1 (500kg Ti, 25000cr), delivers cargo to the target station, and completes the mission lifecycle via MissionComponent/MissionData. *(Exercises: System_Missions accept/complete lifecycle)*
9. Human triggers a save operation via DeepSpaceTraderSaveGame/SaveGameComponent, verifying persistence of economy and mission state. *(Exercises: System_SaveLoad)*

## 3. Queue Coverage (All-20 Table)

| Feature | How Exercised | Direct/Tacit |
|---------|---------------|--------------|
| Player_Character_Model | Act 1 spawn as BP_Astronaut_Character0 | Direct |
| Player_Character_Suit | Act 1 astronaut suit visual verified | Direct |
| Player_Character_Animation | Act 1 walk/stop/bend animations | Direct |
| Player_Character_Lighting | Act 1 outpost lighting on character mesh | Direct |
| Player_Character_Model_Visor_Apply | Act 1 visor material verified on model | Direct |
| Ground_Metal_Surface | Act 1 walk on metal patches | Direct |
| Ground_Rock_Surface | Act 1 walk on rock patches | Direct |
| Ground_Sand_Surface | Act 1 walk on sand patches | Direct |
| Ground_Sand_Particles | Act 1 sand particle effects underfoot | Direct |
| Verb_Look | Act 1 viewport camera rotation | Direct |
| Verb_Step | Act 1 movement across surfaces | Direct |
| Verb_Bend | Act 1 interact prompt appears | Direct |
| Verb_PickUp | Act 1 pick up sample object | Direct |
| Verb_Drop | Act 1 drop sample object | Direct |
| Verb_Shovel | Act 1 shovel tool used on sand | Direct |
| Tool_Weapon_Model | Act 1 weapon tool model inspected | Direct |
| System_Economy | Act 2 trade UI shows commodity prices | Direct |
| System_SaveLoad | Act 2 save operation after mission completion | Direct |
| System_Factions | Act 2 station identity (Orbital Council/Titan Miners) | Direct |
| System_Missions | Act 2 accept/deliver Delivery_Titanium_Batch_1 | Direct |

## 4. Technical Architecture

### What is REAL Today (per recon)
- **Generated C++ Systems**: Economy (CommodityData/EconomyManager/StationTradingData/EconomyInitializer), Missions (MissionComponent/MissionData), Stations (DockingComponent/StationActor), Inventory (InventoryTradeComponent), Save (DeepSpaceTraderSaveGame/SaveGameComponent), Flight, Ships, Combat suite, Factions, AI (PirateAIController/NPC*), UI (WID_TradeUI), Tools (Scanner/Shovel/Weapon), Interactions (Pickup/Drop), PCG volume manager, ChimeraMovementComponent.
- **Ship Actor**: AShip_Trader_Vessel_Alpha exists with ShipRoot + ShipMesh + Camera + FlightComponent + Weapon/Shield/Damage/SystemDamage/CombatTarget components.
- **Astronaut BP**: /Game/Characters/Astronaut/BP_Astronaut_Character exists with suit, visor, lighting features built at BP level.

### What Gets Built (New Generator Methods)
1. **Flight Input Bindings**: Add `SetupPlayerInputComponent` wiring in the GameMode generator method (`DeepSpaceTraderGameMode.cpp` template or generator method in `core/game_code_generator.py`). Bind thrust/steering axes via EnhancedInput or legacy Axis bindings (e.g., `BindAxis("Thrust")`, `BindAxis("Yaw")`, `BindAxis("Pitch")`).
2. **Ship Possession Transition**: Add a trigger volume or interaction prompt in the level that calls `SetPlayerController` to switch from `BP_Astronaut_Character0` pawn to `AShip_Trader_Vessel_Alpha`. This is a generator-owned GameMode/Level content change.
3. **Station Placement Content**: Add StationActor instances for Orbital_Hub_7 and Ares_Market_Central to the demo level via level design or PCG volume manager activation.

### DSL Changes vs Generator Methods vs Manual Files
- **DSL spec changes** (`tests/dsl_grammar/deep_space_trader.chimera`): Add any new commodity data, mission definitions (Delivery_Titanium_Batch_1), or station identifiers if not already present.
- **Generator methods** (`core/game_code_generator.py`): Add `generate_flight_input_bindings()` method to wire SetupPlayerInputComponent in the GameMode template; add ship possession transition logic to the level generator or GameMode default pawn switch logic.
- **Manual files/level content**: Place StationActor instances and boarding trigger volumes in L_VerificationStudio or chimeradefaultlevel via UE editor (capable sessions only for BP-level wiring).

### How Input-From-Zero is Solved
The current ship has ZERO input wiring (no SetupPlayerInputComponent, no BindAxis/BindAction). The generator method `generate_flight_input_bindings()` will add the necessary C++ code in `DeepSpaceTraderGameMode.cpp` or `AShip_Trader_Vessel_Alpha.cpp` to bind keyboard axes for thrust, yaw, pitch, and roll. Verification: MCP read-back of input component state after PIE launch.

### How the Level Gets Its Content
The currently open level has ~18 actors (Floor, SM_SkySphere, PlayerStart, lights) but no StationActor or ship actor placed. The demo level will be populated via:
- Placing AShip_Trader_Vessel_Alpha actor at a spawn point
- Placing StationActor instances for Orbital_Hub_7 and Ares_Market_Central
- Adding trigger volumes for ship possession transition

## 5. Build Plan (Phases Sized to One Duty Cycle Each)

### Phase 1: Flight Input Bindings (FIRST PLAYTESTABLE)
**Goal**: Enable basic ship control via keyboard input bindings.
**Work items**:
1. Add `generate_flight_input_bindings()` method in `core/game_code_generator.py`:
   - Modify GameMode template to include `SetupPlayerInputComponent` call
   - Add `BindAxis("Thrust")`, `BindAxis("Yaw")`, `BindAxis("Pitch")`, `BindAxis("Roll")` mappings
   - Map axes to FlightComponent's thrust/steering math methods
2. Regenerate C++ via pipeline: `cd E:\PythonChimera\Chimera && python run_deep_space_trader_pipeline.py`
3. Verify with ev.json: `{"tests":{"passed":1,"failed":0,"skipped":0,"ran_in_editor":true,"criteria_total":1}, "telemetry":{"crash_free":true,"fps":60,"target_fps":60,"unbounded_growth":false}, "checklist":{"feedback":true,"consistency":true,"meaningful_parameters":true,"fail_safety":true,"balance_sanity":true}, "spec_fidelity":1.0}`
4. Grade via: `python -m core.result_grader --feature Flight_Input_Bindings --evidence ev.json`

### Phase 2: Station Placement and Docking Proximity
**Goal**: Place station actors and verify docking proximity logic works.
**Work items**:
1. In UE editor (capable sessions only), place StationActor instances for Orbital_Hub_7 and Ares_Market_Central in the level.
2. Verify DockingComponent proximity logic via MCP inspect: `control_actor find_by_class --class "StationActor"`
3. No Niagara authoring—use proven pathways only (station meshes are generated assets or manual UE placements).

### Phase 3: Ship Possession Transition and Trade UI
**Goal**: Enable pawn switch from astronaut to ship, and verify trade UI creation.
**Work items**:
1. Add boarding trigger volume or 'E' key prompt in level to call `SetPlayerController` switch to AShip_Trader_Vessel_Alpha.
2. Verify WID_TradeUI is a real UMG widget class and can be created/added to viewport via MCP read-back or screenshot verification.

### Phase 4: Mission Lifecycle and Save Operation
**Goal**: Verify mission accept/complete lifecycle and save persistence.
**Work items**:
1. Ensure Delivery_Titanium_Batch_1 mission is seeded from DSL via EconomyInitializer/MissionData generator methods.
2. Verify MissionComponent accept/complete lifecycle via MCP scene stats or DNA graph verification.
3. Trigger DeepSpaceTraderSaveGame save operation and verify persistence via read-back.

## 6. Observation Intake Plan

After the human plays the demo and provides a few-sentence temperature reading, the agent runs:

1. **Record playtest**: `python -m core.graphify_record playtest --notes "<their EXACT words>"` → saves the returned playtest_id.
2. **Attribute direct mentions**: For each queue feature the temperature DIRECTLY mentions:
   `python -m core.graphify_record observe --feature <X> --verdict <accepted|rejected> --notes "<their words>" --derived-from <playtest_id> --quote "<their exact phrase>" --loop <N>`
3. **Attribute tacit features**: Features clearly on-screen during play but unmentioned:
   `python -m core.graphify_record observe --feature <X> --verdict accepted --tacit --derived-from <playtest_id> --loop <N>`
4. **Present attribution table** for one-sentence overrules if the human disputes any attribution.

## 7. Risks & Traps

### Known Traps and Mitigations
- **Niagara AUTHORING via MCP bridge is a facade**: Never author Niagara emitters; only spawn stock templates (FountainLightweight) if needed. Mitigation: Demo does not require Niagara authoring—ground surface particles are existing BP-level assets or manual UE placements.
- **animation_physics add_anim_notify and get_anim_sequence_info: NOT_IMPLEMENTED in bridge**: Mitigation: Footstep animation notifies are deferred; demo focuses on ship flight and economy systems first.
- **Content/Audio is EMPTY**: Engine ships no footstep sounds; human must import a CC0 pack (BLOCKED-ON-ASSETS). Mitigation: Demo's Act 2 focus minimizes reliance on footstep audio.
- **Never trust success:true — read the value back via MCP**: All verification steps use MCP read-backs for input component state, actor lists, and mission/save state.
- **Generator-owned files must be fixed in core/game_code_generator.py templates**: Flight input bindings, GameMode default pawn logic, and mission data generation all follow DSL-first and generator-owned rules.

### Explicit Exclusions (per user scope: no combat)
- Combat suite components (Weapon/Shield/Damage/SystemDamage/CombatTarget) are generated but NOT exercised in this demo.
- PirateAIController and NPC behavior trees are not part of the playtest script.

## 8. Provenance

This architecture absorbs the local model's draft plan (flight input bindings, station meshes + docking proximity, commodity buy/sell, mission auto-complete, HUD/UMG trade UI) while fixing its errors: no Niagara-as-mesh assumptions, solving input-from-zero via generator method additions, and addressing the empty level content gap via station placement and ship possession transition logic. The design panel lenses (ship-first, queue-first, hybrid two-act, wild card) converged on the **hybrid two-act** approach as the winner, grafting the queue-first lens's emphasis on maximum 16 on-foot feature coverage per human minute with the ship-first lens's trader-loop sequence (flight -> dock -> trade -> mission -> save). All phases are executable by weak local duty agents unless flagged capable-only (UE editor level content placement).
