grammar ChimeraDSL;

// Top-level game specification
gameSpec: gameSettingsBlock? gameBlock narrativeBlock? gameplayBlock? worldBlock? uiBlock? audioBlock? technicalBlock? artDirectionBlock? celestialSystemsBlock? flightComponentsBlock? shipClassesBlock? economySystemsBlock? quantumTravelSystemsBlock? planetGenerationSystemsBlock? proceduralGenerationBlock? levelBlock? testsBlock? flightModelBlock? shipSystemsBlock? economySystems2Block? EOF;

// ============================================================================
// GAME SETTINGS BLOCK
// ============================================================================
gameSettingsBlock: 'game_settings' '{' gameSettingsBody '}';
gameSettingsBody: (cameraPerspective | gameModeType)*;
cameraPerspective: 'camera_perspective' '=' ('first_person' | 'third_person') ';';
gameModeType: 'game_mode' '=' ('single_player' | 'multiplayer') ';';

// ============================================================================
// GAME BLOCK
// ============================================================================
gameBlock: 'game' STRING '{' gameBody '}';
gameBody: (engineVersion | targetPlatforms)*;
engineVersion: 'engine_version' '=' STRING ';';
targetPlatforms: 'target_platforms' '=' '[' STRING (',' STRING)* ']';

// ============================================================================
// NARRATIVE BLOCK
// ============================================================================
narrativeBlock: 'narrative' '{' narrativeBody '}';
narrativeBody: (actDeclaration | dialogueTree | cutsceneDeclaration)*;

actDeclaration: 'act' STRING actBody;
actBody: ('start_dialogue' STRING ';' | 'on_complete' '{' actionList '}' | actionItem)+;

dialogueTree: 'dialogue_tree' STRING '{' dialogueNodes '}';
dialogueNodes: (dialogueNode | playerChoiceBranch)*;

dialogueNode: 'node' STRING '{' nodeProperties '}';
nodeProperties: (speakerProperty | textProperty | nextProperty | speakerProperty)*;
speakerProperty: 'speaker' '=' STRING ';';
textProperty: 'text' '=' STRING ';';
nextProperty: 'next' '=' STRING ';';

playerChoiceBranch: 'player_choice' '[' STRING (',' STRING)* ']' 'branches' '{' branchMappings '}';
branchMappings: (branchMapping)+;
branchMapping: STRING '->' 'node' STRING '{' nodeProperties '}';

cutsceneDeclaration: 'cutscene' STRING '{' cutsceneProperties '}';
cutsceneProperties: (cameraShot | characterAnimation | triggerEvent)*;
cameraShot: 'camera_shot' STRING ';';
characterAnimation: 'character_animation' STRING ';';
triggerEvent: 'trigger' STRING ';';

// ============================================================================
// GAMEPLAY BLOCK
// ============================================================================
gameplayBlock: 'gameplay' '{' gameplayBody '}';
gameplayBody: (characterDeclaration | abilityDeclaration | combatSystem | survivalStats | craftingSystems | inventorySystem | progressionSystem)*;

characterDeclaration: 'character' STRING inheritsClause? propertiesBlock;
inheritsClause: 'inherits' STRING;
propertiesBlock: '{' characterProperties '}';
characterProperties: (abilitySystemComponent | attributeSet | defaultAbilities)*;
abilitySystemComponent: 'ability_system_component' STRING ';';
attributeSet: 'attribute_set' STRING ';';
defaultAbilities: 'default_abilities' '=' '[' STRING (',' STRING)* ']';

abilityDeclaration: 'ability' STRING usesGAS? '{' abilityProperties '}';
usesGAS: 'uses GAS';
abilityProperties: (abilityTags | cooldownProperty | activationBlock)*;
abilityTags: 'ability_tags' '=' '[' STRING (',' STRING)* ']';
cooldownProperty: 'cooldown' expression 'via' STRING ';';
activationBlock: 'activation' '{' activationStatements '}';
activationStatements: (launchCharacter | playMontage | applyEffect | ifStatement)+;

launchCharacter: 'launch_character' '(' propertiesList ')';
playMontage: 'play_montage' '(' STRING (',' propertyAssignment)* ')';
applyEffect: 'apply_effect' '(' STRING ')';
ifStatement: 'if' '(' condition ')' '{' activationStatements '}';

combatSystem: 'combat_system' '{' combatProperties '}';
combatProperties: (damageFormulas | hitReactions | statusEffects)*;
damageFormulas: 'damage_formulas' '=' STRING ';';
hitReactions: 'hit_reactions' '=' BOOLEAN ';';
statusEffects: 'status_effects' '=' '[' STRING (',' STRING)* ']';

inventorySystem: 'inventory' '{' inventoryProperties '}';
inventoryProperties: (inventorySlots | equipmentSlots)*;
inventorySlots: 'slots' '=' INTEGER ';';
equipmentSlots: 'equipment_slots' '=' '[' STRING (',' STRING)* ']';

progressionSystem: 'progression' '{' progressionProperties '}';
progressionProperties: (levelCap | skillPointsPerLevel)*;
levelCap: 'level_cap' '=' INTEGER ';';
skillPointsPerLevel: 'skill_points_per_level' '=' INTEGER ';';

survivalStats: 'survival_stats' '{' survivalStatsProperties '}';
survivalStatsProperties: (hungerStat | thirstStat | temperatureStat)*;
hungerStat: 'hunger_stat' '=' BOOLEAN ','?;
thirstStat: 'thirst_stat' '=' BOOLEAN ','?;
temperatureStat: 'temperature_stat' '=' BOOLEAN ','?;

craftingSystems: 'crafting_systems' '{' craftingSystemsProperties '}';
craftingSystemsProperties: (recipeDeclaration | workstationDeclaration)*;

recipeDeclaration: 'recipe' STRING '{' recipeProperties '}';
recipeProperties: (inputItems | outputItem | quantityProperty)*;
inputItems: 'inputs' '=' '[' STRING (',' STRING)* ']';
outputItem: 'output' '=' STRING ','?;
quantityProperty: 'quantity' '=' INTEGER ','?;

workstationDeclaration: 'workstation' STRING '{' workstationProperties '}';
workstationProperties: (stationTypeProperty | radiusProperty)*;
stationTypeProperty: 'type' '=' STRING ','?;
radiusProperty: 'crafting_radius' '=' FLOAT ','?;

// ============================================================================
// WORLD BLOCK
// ============================================================================
worldBlock: 'world' '{' worldBody '}';
worldBody: (levelDeclaration | npcDeclaration)*;

levelDeclaration: 'level' STRING '{' levelProperties '}';
levelProperties: (environmentAssets | spawnPoint | scriptedEvent)*;
environmentAssets: 'environment' '(' environmentItems ')';
environmentItems: (STRING | 'using' WORLD_PARTITION)+;
WORLD_PARTITION: 'WorldPartition';

spawnPoint: 'spawn_point' STRING 'at' positionExpression ';';
positionExpression: '(' INTEGER ',' INTEGER ',' INTEGER ')';

scriptedEvent: 'scripted_event' STRING 'at' eventTimestamp ';';
eventTimestamp: TIMESTAMP;

npcDeclaration: 'npc' STRING '{' npcProperties '}';
npcProperties: (npcMesh | behaviorTreeProperty | dialogueTreeProperty | healthProperty | abilitiesList)*;
npcMesh: 'mesh' '=' STRING ','?;
behaviorTreeProperty: 'behavior_tree' STRING ','?;
dialogueTreeProperty: 'dialogue_tree' STRING ','?;
healthProperty: 'health' '=' INTEGER ','?;
abilitiesList: 'abilities' '=' '[' STRING (',' STRING)* ']';

// ============================================================================
// UI BLOCK
// ============================================================================
uiBlock: 'ui' '{' uiBody '}';
uiBody: (hudDeclaration | pauseMenuDeclaration)*;

hudDeclaration: 'hud' '{' hudContent '}';
hudContent: (widgetDeclaration | directHUDElements)*;

widgetDeclaration: 'widget' STRING '{' widgetProperties '}';
widgetProperties: (uiElement)+;
uiElement: STRING ','? ';'?;

directHUDElements: (hudElement)+;
hudElement: 'health_bar' | 'minimap' | 'ability_cooldowns' | 'quest_tracker';

pauseMenuDeclaration: 'pause_menu' '{' pauseMenuContent '}';
pauseMenuContent: (widgetDeclaration | menuActions)*;
menuActions: ('options_resume' | 'options_settings' | 'quit_to_main') ','? ';'?;

// ============================================================================
// AUDIO BLOCK
// ============================================================================
audioBlock: 'audio' '{' audioBody '}';
audioBody: (musicCueDeclaration | sfxDeclaration | dynamicMixingRules)*;

musicCueDeclaration: 'music_cue' STRING '{' musicProperties '}';
musicProperties: (loopProperty | volumeProperty)*;
loopProperty: 'loop' '=' BOOLEAN ','?;
volumeProperty: 'volume' '=' FLOAT ','?;

sfxDeclaration: 'sfx' STRING '{' sfxProperties '}';
sfxProperties: (pitchVariationProperty)*;
pitchVariationProperty: 'pitch_variation' '=' FLOAT ','?;

dynamicMixingRules: 'dynamic_mixing_rules' '{' mixingProperties '}';
mixingProperties: (prioritySystem | duckMusicProperty)*;
prioritySystem: 'priority_system' '=' BOOLEAN ','?;
duckMusicProperty: 'duck_music_on_damage' '=' BOOLEAN ','?;

// ============================================================================
// TECHNICAL BLOCK
// ============================================================================
technicalBlock: 'technical' '{' technicalBody '}';
technicalBody: (networkModel | replicationRules | performanceSettings | moduleDependencies)*;

networkModel: 'network_model' '=' STRING ';';

replicationRules: 'replication' '{' replicationProperties '}';
replicationProperties: (replicatedProperties | rpcDeclarations)*;
replicatedProperties: 'properties' ':' '[' replicationItem (',' replicationItem)* ']';
replicationItem: STRING;

rpcDeclarations: 'rpcs' ':' '[' rpcItem (',' rpcItem)* ']';
rpcItem: STRING;

performanceSettings: 'performance' '{' performanceProperties '}';
performanceProperties: (targetFPS | LODStrategy | cullingDistance)*;
targetFPS: 'target_fps' '=' INTEGER ','?;
LODStrategy: 'LOD_strategy' '=' STRING ','?;
cullingDistance: 'culling_distance_multiplier' '=' FLOAT ';';

moduleDependencies: 'module_dependencies' '=' '[' STRING (',' STRING)* ']';

// ============================================================================
// ART DIRECTION BLOCK
// ============================================================================
artDirectionBlock: 'art_direction' '{' artDirectionProperties '}';
artDirectionProperties: (styleProperty | colorPaletteProperty)*;
styleProperty: 'style' '=' STRING ';';
colorPaletteProperty: 'color_palette' '=' STRING ';';

// ============================================================================
// STAR CITIZEN SCALE BLOCKS
// ============================================================================

celestialSystemsBlock: 'celestial_systems' '{' celestialSystemsBody '}';
celestialSystemsBody: (celestialBodyDeclaration)*;

celestialBodyDeclaration: 'celestial_body' STRING '{' celestialBodyProperties '}';
celestialBodyProperties: (celestialType | radiusKm | atmosphereDensity | hasMoons | moonCount | atmosphericComposition | surfaceTemperatureMin | surfaceTemperatureMax | isArtificial | stationClass)*;
celestialType: 'type' '=' STRING ','?;
radiusKm: 'radius_km' '=' INTEGER ','?;
atmosphereDensity: 'atmosphere_density' '=' FLOAT ','?;
hasMoons: 'has_moons' '=' BOOLEAN ','?;
moonCount: 'moon_count' '=' INTEGER ','?;
atmosphericComposition: 'atmospheric_composition' '=' '[' STRING (',' STRING)* ']';
surfaceTemperatureMin: 'surface_temperature_min' '=' INTEGER ','?;
surfaceTemperatureMax: 'surface_temperature_max' '=' INTEGER ','?;
isArtificial: 'is_artificial' '=' BOOLEAN ','?;
stationClass: 'station_class' '=' STRING ','?;

flightComponentsBlock: 'flight_components' '{' flightComponentsBody '}';
flightComponentsBody: (flightComponentDeclaration)*;

flightComponentDeclaration: 'component' STRING '{' componentProperties '}';
componentProperties: (componentType | thrustForceNewtons | fuelConsumptionKgPerSec | fuelType | maxTemperatureKelvin | energyRequirementMegajoules | coolDownSeconds | requiresQuantumAnchor | maxRangeLightYears | shieldStrengthPoints | regenerationRatePerSec | energyDrainPerHit | shieldType | detectionRangeKm | scanModes | jammingResistanceLevel)*;
componentType: 'type' '=' STRING ','?;
thrustForceNewtons: 'thrust_force_newtons' '=' INTEGER ','?;
fuelConsumptionKgPerSec: 'fuel_consumption_kg_per_sec' '=' FLOAT ','?;
fuelType: 'fuel_type' '=' STRING ','?;
maxTemperatureKelvin: 'max_temperature_kelvin' '=' INTEGER ','?;
energyRequirementMegajoules: 'energy_requirement_megajoules' '=' INTEGER ','?;
coolDownSeconds: 'cool_down_seconds' '=' INTEGER ','?;
requiresQuantumAnchor: 'requires_quantum_anchor' '=' BOOLEAN ','?;
maxRangeLightYears: 'max_range_light_years' '=' INTEGER ','?;
shieldStrengthPoints: 'shield_strength_points' '=' INTEGER ','?;
regenerationRatePerSec: 'regeneration_rate_per_sec' '=' INTEGER ','?;
energyDrainPerHit: 'energy_drain_per_hit' '=' INTEGER ','?;
shieldType: 'shield_type' '=' STRING ','?;
detectionRangeKm: 'detection_range_km' '=' INTEGER ','?;
scanModes: 'scan_modes' '=' '[' STRING (',' STRING)* ']';
jammingResistanceLevel: 'jamming_resistance_level' '=' INTEGER ','?;

shipClassesBlock: 'ship_classes' '{' shipClassesBody '}';
shipClassesBody: (shipClassDeclaration)*;

shipClassDeclaration: 'ship_class' STRING '{' shipClassProperties '}';
shipClassProperties: (shipCategory | crewCapacity | cargoVolumeCubicMeters | hasQuantumDrive | hasWeaponSystems | weaponSlots | maxSpeedKmPerSec | shieldClass | maneuverabilityRating)*;
shipCategory: 'category' '=' STRING ','?;
crewCapacity: 'crew_capacity' '=' INTEGER ','?;
cargoVolumeCubicMeters: 'cargo_volume_cubic_meters' '=' INTEGER ','?;
hasQuantumDrive: 'has_quantum_drive' '=' BOOLEAN ','?;
hasWeaponSystems: 'has_weapon_systems' '=' BOOLEAN ','?;
weaponSlots: 'weapon_slots' '=' INTEGER ','?;
maxSpeedKmPerSec: 'max_speed_km_per_sec' '=' INTEGER ','?;
shieldClass: 'shield_class' '=' STRING ','?;
maneuverabilityRating: 'maneuverability_rating' '=' INTEGER ','?;

economySystemsBlock: 'economy_systems' '{' economySystemsBody '}';
economySystemsBody: (commodityDeclaration | tradeRouteDeclaration)*;

commodityDeclaration: 'commodity' STRING '{' commodityProperties '}';
commodityProperties: (commodityCategory | baseValueCredits | marketVolatility | productionLocations | consumptionRegions | tradeRestrictions)*;
commodityCategory: 'category' '=' STRING ','?;
baseValueCredits: 'base_value_credits' '=' INTEGER ','?;
marketVolatility: 'market_volatility' '=' FLOAT ','?;
productionLocations: 'production_locations' '=' '[' STRING (',' STRING)* ']';
consumptionRegions: 'consumption_regions' '=' '[' STRING (',' STRING)* ']';
tradeRestrictions: 'trade_restrictions' '=' '[' STRING (',' STRING)* ']';

tradeRouteDeclaration: 'trade_route' STRING '{' tradeRouteProperties '}';
tradeRouteProperties: (routeOrigin | routeDestinations | typicalCargoTypes | routeSafetyRating | pirateActivityLevel)*;
routeOrigin: 'origin_system' '=' STRING ','?;
routeDestinations: 'destination_systems' '=' '[' STRING (',' STRING)* ']';
typicalCargoTypes: 'typical_cargo_types' '=' '[' STRING (',' STRING)* ']';
routeSafetyRating: 'route_safety_rating' '=' FLOAT ','?;
pirateActivityLevel: 'pirate_activity_level' '=' STRING ','?;

quantumTravelSystemsBlock: 'quantum_travel_systems' '{' quantumTravelSystemsBody '}';
quantumTravelSystemsBody: (quantumAnchorDeclaration | quantumJumpPathDeclaration | quantumWeatherSystemDeclaration)*;

quantumAnchorDeclaration: 'quantum_anchor' STRING '{' quantumAnchorProperties '}';
quantumAnchorProperties: (anchorLocationCoordinates | anchorStrength | maxConcurrentJumps | rechargeRatePerSec | supportsShipClasses)*;
anchorLocationCoordinates: 'location_coordinates' '=' '[' FLOAT ',' FLOAT ',' FLOAT ']';
anchorStrength: 'anchor_strength' '=' INTEGER ','?;
maxConcurrentJumps: 'max_concurrent_jumps' '=' INTEGER ','?;
rechargeRatePerSec: 'recharge_rate_per_second' '=' FLOAT ','?;
supportsShipClasses: 'supports_ship_classes' '=' '[' STRING (',' STRING)* ']';

quantumJumpPathDeclaration: 'quantum_jump_path' STRING '{' quantumJumpPathProperties '}';
quantumJumpPathProperties: (jumpOriginAnchor | jumpDestinationAnchor | jumpDistanceLightYears | travelTimeSeconds | energyCostMegajoules | requiresFavorableNimbusConditions | nimbusConditionThreshold)*;
jumpOriginAnchor: 'origin_anchor' '=' STRING ','?;
jumpDestinationAnchor: 'destination_anchor' '=' STRING ','? | 'destination_anchor' '=' 'null' ','?;
jumpDistanceLightYears: 'distance_light_years' '=' FLOAT ','?;
travelTimeSeconds: 'travel_time_seconds' '=' INTEGER ','?;
energyCostMegajoules: 'energy_cost_megajoules' '=' INTEGER ','?;
requiresFavorableNimbusConditions: 'requires_favorable_nimbus_conditions' '=' BOOLEAN ','?;
nimbusConditionThreshold: 'nimbus_condition_threshold' '=' FLOAT ','?;

quantumWeatherSystemDeclaration: 'quantum_weather_system' '{' quantumWeatherProperties '}';
quantumWeatherProperties: (phenomenonName | affectsJumpSafety | safetyReductionPercentage | durationVariationMinutes | affectedRadiusLightYears)*;
phenomenonName: 'phenomenon' '=' STRING ','?;
affectsJumpSafety: 'affects_jump_safety' '=' BOOLEAN ','?;
safetyReductionPercentage: 'safety_reduction_percentage' '=' INTEGER ','?;
durationVariationMinutes: 'duration_variation_minutes' '=' '[' INTEGER ',' INTEGER ']';
affectedRadiusLightYears: 'affected_radius_light_years' '=' FLOAT ','?;

planetGenerationSystemsBlock: 'planet_generation_systems' '{' planetGenerationSystemsBody '}';
planetGenerationSystemsBody: (planetGeneratorDeclaration | biomeConfigDeclaration)*;

// ============================================================================
// LEVEL BLOCK
// ============================================================================
levelBlock: 'level' '{' levelBody '}';
levelBody: (levelName | playerStartLocation | skyboxType | lightDeclaration | worldBounds | stationPlacements | planetPlacements)*;

levelName: 'name' '=' STRING ','? ';'?;

playerStartLocation: 'player_start' '{' playerStartProperties '}';
playerStartProperties: locationProperty*;
locationProperty: 'location' '=' '[' FLOAT ',' FLOAT ',' FLOAT ']';

skyboxType: 'skybox_type' '=' STRING ','? ';'?;

lightDeclaration: 'light' '{' lightProperties '}';
lightProperties: (lightType | lightPosition | lightRotation | lightIntensity | lightColor)*;
lightType: 'type' '=' STRING ','? ';'?;
lightPosition: 'position' '=' '[' FLOAT ',' FLOAT ',' FLOAT ']';
lightRotation: 'rotation' '=' '[' FLOAT ',' FLOAT ',' FLOAT ']';
lightIntensity: 'intensity' '=' FLOAT ','? ';'?;
lightColor: 'color' '=' STRING ','? ';'?;

worldBounds: 'world_bounds' '{' worldBoundsProperties '}';
worldBoundsProperties: (minLocationProperty | maxLocationProperty)*;
minLocationProperty: 'min_location' '=' '[' FLOAT ',' FLOAT ',' FLOAT ']';
maxLocationProperty: 'max_location' '=' '[' FLOAT ',' FLOAT ',' FLOAT ']';

stationPlacements: 'station_placements' '{' stationPlacementItems '}';
stationPlacementItems: (stationPlacementItem)+;
stationPlacementItem: 'station_placement' STRING '{' stationPlacementProperties '}';
stationPlacementProperties: (stationNameProperty | stationLocationProperty)*;
stationNameProperty: 'name' '=' STRING ','? ';'?;
stationLocationProperty: 'location' '=' '[' FLOAT ',' FLOAT ',' FLOAT ']';

planetPlacements: 'planet_placements' '{' planetPlacementItems '}';
planetPlacementItems: (planetPlacementItem)+;
planetPlacementItem: 'planet_placement' STRING '{' planetPlacementProperties '}';
planetPlacementProperties: (planetNameProperty | planetLocationProperty | planetScaleProperty)*;
planetNameProperty: 'name' '=' STRING ','? ';'?;
planetLocationProperty: 'location' '=' '[' FLOAT ',' FLOAT ',' FLOAT ']';
planetScaleProperty: 'scale' '=' FLOAT ','? ';'?;


planetGeneratorDeclaration: 'planet_generator' STRING '{' generatorProperties '}';
generatorProperties: (generatorType | baseBiomes | terrainDetailLevels | supportsDynamicWeather | weatherSystems | cloudLayers | turbulenceFactor | colorGradients | hasRingSystem | clusterDensityPerCubicKm | sizeVariationMeters | compositionTypes | spawnResourceNodes)*;
generatorType: 'generator_type' '=' STRING ','?;
baseBiomes: 'base_biomes' '=' '[' STRING (',' STRING)* ']';
terrainDetailLevels: 'terrain_detail_levels' '=' '[' INTEGER (',' INTEGER)* ']';
supportsDynamicWeather: 'supports_dynamic_weather' '=' BOOLEAN ','?;
weatherSystems: 'weather_systems' '=' '[' STRING (',' STRING)* ']';
cloudLayers: 'cloud_layers' '=' INTEGER ','?;
turbulenceFactor: 'turbulence_factor' '=' FLOAT ','?;
colorGradients: 'color_gradients' '=' '[' STRING (',' STRING)* ']';
hasRingSystem: 'has_ring_system' '=' BOOLEAN ','?;
clusterDensityPerCubicKm: 'cluster_density_per_cubic_km' '=' FLOAT ','?;
sizeVariationMeters: 'size_variation_meters' '=' '[' INTEGER ',' INTEGER ']';
compositionTypes: 'composition_types' '=' '[' STRING (',' STRING)* ']';
spawnResourceNodes: 'spawn_resource_nodes' '=' BOOLEAN ','?;

biomeConfigDeclaration: 'biome_config' STRING '{' biomeConfigProperties '}';
biomeConfigProperties: (vegetationDensity | treeHeightRangeMeters | groundTextureTypes | wildlifeSpawns | resourceNodes | terrainRoughness)*;
vegetationDensity: 'vegetation_density' '=' FLOAT ','?;
treeHeightRangeMeters: 'tree_height_range_meters' '=' '[' INTEGER ',' INTEGER ']';
groundTextureTypes: 'ground_texture_types' '=' '[' STRING (',' STRING)* ']';
wildlifeSpawns: 'wildlife_spawns' '=' '[' STRING (',' STRING)* ']';
resourceNodes: 'resource_nodes' '=' '[' STRING (',' STRING)* ']';
terrainRoughness: 'terrain_roughness' '=' FLOAT ','?;

// ============================================================================
// PROCEDURAL GENERATION BLOCK
// ============================================================================
proceduralGenerationBlock: 'procedural_generation' '{' proceduralGenerationBody '}';
proceduralGenerationBody: (pcgGraphDeclaration)*;

pcgGraphDeclaration: 'pcg_graph' STRING '{' pcgGraphProperties '}';
pcgGraphProperties: (graphType | dataCollections | taggedDataItems | metadataDomains | attributeSelectors)*;
graphType: 'graph_type' '=' STRING ','? ';'?;

dataCollections: 'data_collections' '{' dataCollectionItems '}';
dataCollectionItems: (dataCollectionItem)+;
dataCollectionItem: 'collection' STRING '{' collectionProperties '}';
collectionProperties: (cancelExecutionOnEmpty | cancelExecution)*;
cancelExecutionOnEmpty: 'cancel_execution_on_empty' '=' BOOLEAN ','? ';'?;
cancelExecution: 'cancel_execution' '=' BOOLEAN ','? ';'?;

taggedDataItems: 'tagged_data_items' '{' taggedDataItemProperties '}';
taggedDataItemProperties: (taggedDataItemDeclaration)+;
taggedDataItemDeclaration: 'item' STRING '{' itemProperties '}';
itemProperties: (dataTags | pinProperty | bPinlessData | bIsUsedMultipleTimes)*;
dataTags: 'tags' '=' '[' STRING (',' STRING)* ']';
pinProperty: 'pin' '=' STRING ','? ';'?;
bPinlessData: 'b_pinless_data' '=' BOOLEAN ','? ';'?;
bIsUsedMultipleTimes: 'b_is_used_multiple_times' '=' BOOLEAN ','? ';'?;

metadataDomains: 'metadata_domains' '=' '[' STRING (',' STRING)* ']';
attributeSelectors: 'attribute_selectors' '=' '[' STRING (',' STRING)* ']';

// ============================================================================
// TESTS BLOCK
// ============================================================================
testsBlock: 'tests' '{' testDef+ '}';

testDef: TEST STRING '{' testBody '}';
testBody: (typeDecl | descriptionDecl | iterationsDecl | setupBlock | actionBlock | assertBlock | cleanupBlock)*;

typeDecl: TYPE '=' ('unit' | 'integration' | 'balance') ','? ';'?;
descriptionDecl: DESCRIPTION '=' STRING ','? ';'?;
iterationsDecl: ITERATIONS '=' INTEGER ','? ';'?;

setupBlock: SETUP '{' setupStatements '}';
setupStatements: (setupStatement)*;
setupStatement: setupAction ';' | setupAction ','? ';'?;
setupAction: SPAWN_ACTOR '(' paramsList ')' | GRANT_ABILITY '(' paramsList ')' | ADD_ITEM '(' paramsList ')' | SET_ATTRIBUTE '(' paramsList ')' | SET_STATUS '(' paramsList ')' | SET_BIOME '(' paramsList ')' | INITIALIZE_MARKET '(' paramsList ')';

actionBlock: ACTION '{' actionStatements '}';
actionStatements: (actionStatement)*;
actionStatement: actionAction ';' | actionAction ','? ';'?;
actionAction: ACTIVATE_ABILITY '(' paramsList ')' | NPC_ATTACK_TARGET '(' paramsList ')' | CRAFT_RECIPE '(' paramsList ')' | ADVANCE_MARKET_CYCLES '(' paramsList ')' | WAIT '(' durationExpr ')';

assertBlock: ASSERT '{' assertStatements '}';
assertStatements: (assertStatement)*;
assertStatement: assertionExpression ';';
assertionExpression: funcCall operator expression;
funcCall: ABILITY_ON_COOLDOWN '(' paramsList ')' | COOLDOWN_REMAINING '(' paramsList ')' | HEALTH_PERCENT '(' paramsList ')' | PLAYER_ALIVE '(' paramsList ')' | ATTRIBUTE_VALUE '(' paramsList ')' | INVENTORY_COUNT '(' paramsList ')' | INVENTORY_CONTAINS '(' paramsList ')' | STATUS_ACTIVE '(' paramsList ')' | ABILITY_ACTIVATED | PRICE_VOLATILITY '(' paramsList ')';
operator: '==' | '>=' | '<=' | '>' | '<' | '!=';
durationExpr: FLOAT 'sec' | INTEGER 'sec';

cleanupBlock: CLEANUP '{' cleanupStatements '}';
cleanupStatements: (cleanupStatement)*;
cleanupStatement: destroyAction ';' | destroyAction ','? ';'?;
destroyAction: DESTROY_ACTOR '(' STRING ')';

paramsList: (paramAssignment)+;
paramAssignment: paramKey '=' paramValue;
paramKey: STRING | IDENTIFIER;
paramValue: STRING | INTEGER | FLOAT | BOOLEAN | 'null';
IDENTIFIER: [a-zA-Z_][a-zA-Z0-9_]*;

// ============================================================================
// LEXER RULES
// ============================================================================

// Keywords
game_settings: 'game_settings';
game: 'game';
narrative: 'narrative';
gameplay: 'gameplay';
world: 'world';
ui: 'ui';
audio: 'audio';
technical: 'technical';
art_direction: 'art_direction';

camera_perspective: 'camera_perspective';
game_mode: 'game_mode';

engine_version: 'engine_version';
target_platforms: 'target_platforms';

act: 'act';
start_dialogue: 'start_dialogue';
on_complete: 'on_complete';
dialogue_tree: 'dialogue_tree';
cutscene: 'cutscene';

character: 'character';
inherits: 'inherits';
ability: 'ability';
uses: 'uses';
combat_system: 'combat_system';
survival_stats: 'survival_stats';
crafting_systems: 'crafting_systems';
inventory: 'inventory';
progression: 'progression';

level: 'level';
npc: 'npc';
environment: 'environment';
spawn_point: 'spawn_point';
scripted_event: 'scripted_event';

hud: 'hud';
pause_menu: 'pause_menu';
widget: 'widget';

music_cue: 'music_cue';
sfx: 'sfx';
dynamic_mixing_rules: 'dynamic_mixing_rules';

network_model: 'network_model';
replication: 'replication';
performance: 'performance';
module_dependencies: 'module_dependencies';

style: 'style';
color_palette: 'color_palette';

celestial_systems: 'celestial_systems';
flight_components: 'flight_components';
ship_classes: 'ship_classes';
economy_systems: 'economy_systems';
quantum_travel_systems: 'quantum_travel_systems';
planet_generation_systems: 'planet_generation_systems';
procedural_generation: 'procedural_generation';

// Identifiers and literals
STRING: '"' ~["\r\n]* '"';
INTEGER: [0-9]+;
FLOAT: [0-9]+ '.' [0-9]+;
BOOLEAN: 'true' | 'false';

TIMESTAMP: INTEGER 's';

// Whitespace and comments
WS: [ \t\r\n]+ -> skip;
COMMENT: '//' ~[\r\n]* -> skip;
BLOCK_COMMENT: '/*' .*? '*/' -> skip;
