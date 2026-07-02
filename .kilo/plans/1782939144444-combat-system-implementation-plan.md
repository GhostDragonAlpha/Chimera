# Combat System Implementation Plan

## Overview

Implement the full combat system for DeepSpaceTrader including:
- Weapon components with hardpoint management (fixed, gimbal, turret types)
- Projectile actors with collision and optional tracking
- Shield absorption component with regen mechanics
- Damage routing component
- Subsystem damage component with penalties
- Combat target component for AI targeting
- Pirate AI controller with state machine (Patrolling, Investigating, Engaging, Retreating)
- Behavior tree for pirate AI

## Files to Generate

### Source/{ProjectName}/Combat/
1. `WeaponComponent.h/.cpp` - UWeaponComponent managing weapon hardpoints and firing logic
2. `Projectile.h/.cpp` - AProjectile actor with collision, damage application, and optional tracking
3. `ShieldComponent.h/.cpp` - UShieldComponent for shield absorption and regen mechanics
4. `DamageComponent.h/.cpp` - UDamageComponent as central damage router
5. `SystemDamageComponent.h/.cpp` - USystemDamageComponent for subsystem health and penalties
6. `CombatTargetComponent.h/.cpp` - UCombatTargetComponent for AI targetability

### Source/{ProjectName}/AI/
7. `PirateAIController.h/.cpp` - APirateAIController with state machine
8. `PirateBehaviorTree.h/.json` or `.behaviortree` - Behavior tree asset for pirate AI

## DSL Context to Parse and Update

From `deep_space_trader.chimera`:

**combat_system block (in gameplay):**
```
combat_system {
    damage_formulas = "standard_gas_formula";
    hit_reactions = false;
    status_effects = ["shield_depletion", "system_damage"];
}
```

**factions block (in narrative):**
```
factions = [
    {"id": "faction_orbital_council", "name": "Orbital Council", "relation": "neutral"},
    {"id": "faction_titan_miners", "name": "Titan Miners Guild", "relation": "friendly"},
    {"id": "faction_pirate_syndicate", "name": "Void Syndicate", "relation": "hostile"}
];
```

**ship systems and hardpoints (to be added to ship_systems block):**
Each of the three ship classes must have:
- `hardpoints` block with weapon_slot definitions
- `shield_capacity`, `shield_regen_rate`, `hull_health` properties
- Different combat profiles:
  - Trader_Vessel_Alpha: tough (high hull/shield), lightly armed (2 forward cannons S2)
  - Scout_Vessel_Beta: fast but fragile (lower hull/shield), balanced weapons (1 turret S1 + 2 forward cannons S2)
  - Heavy_Freighter_Gamma: tank (very high hull/shield), minimal weapons (only remote turrets, no fixed cannons)

Example ship definition structure to add:
```
ship "Trader_Vessel_Alpha" inherits "ASpaceShip" {
    fuel_capacity_liters = 10000;
    cargo_capacity_kg = 50000;
    
    hardpoints {
        weapon_slot { name = "ForwardCannons"; size = "S2"; count = 2; type = "fixed"; }
        weapon_slot { name = "TurretTop"; size = "S1"; count = 1; type = "remote_turret"; }
    }
    
    shield_capacity = 1000.0;
    shield_regen_rate = 50.0;
    hull_health = 5000.0;
    
    system "Fuel_Tank" { ... }
    system "Quantum_Engine" { ... }
}
```

## VFX Placeholder Convention

For projectile impact VFX spawning, generate placeholder comments with Niagara naming convention:

```cpp
// TODO: Replace with actual Niagara system
// UNiagaraSystem* ImpactVFX = LoadObject<UNiagaraSystem>(nullptr, TEXT("/Game/VFX/NS_ProjectileImpact"));
// UNiagaraFunctionLibrary::SpawnSystemAtLocation(GetWorld(), ImpactVFX, HitLocation);
```

## Behavior Tree Format

Use the existing `.behaviortree` text format that the code generator already produces for NPC behavior trees. The PirateBehaviorTree should be generated as a `.behaviortree` file in `Content/ProceduralGenerated/AI/`.

## Implementation Steps

### Step 0: Update deep_space_trader.chimera DSL Spec (REQUIRED)

File: `Chimera/tests/dsl_grammar/deep_space_trader.chimera`

Update the ship_systems block to include hardpoints, shield values, and hull health for each of the three ship classes:

**Trader_Vessel_Alpha** (tough but lightly armed):
- fuel_capacity_liters = 10000; cargo_capacity_kg = 50000
- hardpoints: ForwardCannons (S2, count=2, type=fixed), TurretTop (S1, count=1, type=remote_turret)
- shield_capacity = 1000.0; shield_regen_rate = 50.0; hull_health = 5000.0

**Scout_Vessel_Beta** (fast but fragile):
- fuel_capacity_liters = 5000; cargo_capacity_kg = 10000
- hardpoints: ForwardCannons (S2, count=2, type=fixed), TurretTop (S1, count=1, type=remote_turret)
- shield_capacity = 600.0; shield_regen_rate = 30.0; hull_health = 3000.0

**Heavy_Freighter_Gamma** (tank with minimal weapons):
- fuel_capacity_liters = 25000; cargo_capacity_kg = 200000
- hardpoints: TurretTop (S1, count=2, type=remote_turret) - no fixed cannons
- shield_capacity = 1500.0; shield_regen_rate = 75.0; hull_health = 8000.0

### Step 1: Update DSL Parser to Parse combat_system and Hardpoints

File: `Chimera/core/dsl_game_parser.py`

Add parsing for:
- `combat_system` block in gameplay section (already partially implemented)
- Ensure factions array is parsed into `result["narrative"]["factions"]`
- Add hardpoint parsing inside ship definitions: weapon_slot blocks with name, size, count, type properties
- Parse shield_capacity, shield_regen_rate, hull_health from ship system blocks

### Step 2: Update Schema to Include Combat System Properties

File: `Chimera/schema/dsl_game_schema.json`

Ensure these properties are defined in the schema:
- `gameplay.combat_system`: damage_formulas, hit_reactions, status_effects
- `narrative.factions`: array of {id, name, relation}
- `ship_systems.ships.hardpoints`: object with weapon_slot arrays
- `ship_systems.ships.shield_capacity`, `shield_regen_rate`, `hull_health`: float properties

### Step 3: Generate Combat Components in game_code_generator.py

#### 3.1 WeaponComponent.h/.cpp

Properties from DSL ship hardpoints or defaults:
- WeaponSlots (TArray of structs with Name, Size, Count, Type, FireRate, DamagePerShot, ProjectileSpeed, Range)
- MissileRacks (TArray with RackName, Count, MissileType, Damage, TrackingStrength)
- CurrentTarget

**Default values for weapon combat stats based on size class:**
- S1 (light): FireRate=3.0, DamagePerShot=25.0, ProjectileSpeed=80000.0cm/s, Range=200000.0cm
- S2 (medium): FireRate=2.0, DamagePerShot=50.0, ProjectileSpeed=100000.0cm/s, Range=300000.0cm

If DSL hardpoints don't specify these combat stats, apply the size-class defaults above.

Methods:
- `FireWeapon(SlotName)` - check cooldown, spawn projectile based on type (fixed/gimbal/remote_turret)
- `FireMissile(RackName, Target)` - check count, spawn homing projectile
- `GetAvailableWeapons()` -> TArray of ready weapon names
- `GetMissileCount(RackName)` -> int

#### 3.2 Projectile.h/.cpp

Properties:
- Damage (float)
- Speed (float)
- Range (float)
- TrackingStrength (float, 0=unguided, 1=perfect)
- OwnerShip (AActor*)
- DistanceTraveled (float)

Methods:
- `BeginPlay()` - set up collision sphere, bind OnComponentHit, enable movement component
- `TickComponent(DeltaTime)` - if tracking > 0 and target valid, interpolate velocity toward target; check range and destroy if exceeded
- `OnHit(OtherActor)` - find UDamageComponent on OtherActor, call ApplyDamage, spawn VFX placeholder, destroy self

VFX Placeholder in OnHit:
```cpp
// TODO: Replace with actual Niagara system
// UNiagaraSystem* ImpactVFX = LoadObject<UNiagaraSystem>(nullptr, TEXT("/Game/VFX/NS_ProjectileImpact"));
// UNiagaraFunctionLibrary::SpawnSystemAtLocation(GetWorld(), ImpactVFX, HitLocation);
```

#### 3.3 ShieldComponent.h/.cpp
Properties:
- MaxShieldCapacity (float)
- CurrentShield (float)
- ShieldRegenRate (float per second)
- ShieldRegenDelay (float seconds after damage before regen starts)
- TimeSinceLastDamage (float)
- bShieldsDepleted (bool)

Methods:
- `AbsorbDamage(IncomingDamage)` -> float remaining - check if CurrentShield <= 0, calculate absorbed, update CurrentShield and TimeSinceLastDamage, set bShieldsDepleted if shields depleted, return remaining damage
- `TickComponent(DeltaTime)` - increment TimeSinceLastDamage, if >= ShieldRegenDelay and CurrentShield < MaxShieldCapacity, regen; if bShieldsDepleted and CurrentShield >= MaxShieldCapacity * 0.25, set bShieldsDepleted = false

#### 3.4 DamageComponent.h/.cpp
Properties:
- MaxHullHealth (float)
- CurrentHullHealth (float)
- bIsDestroyed (bool)

Methods:
- `ApplyDamage(IncomingDamage, Instigator)` - route to ShieldComponent->AbsorbDamage(), if remaining > 0 subtract from CurrentHullHealth and route to SystemDamageComponent; if CurrentHullHealth <= 0 set bIsDestroyed = true and trigger destruction sequence; if Instigator is player and target is NPC award credits
- `GetHullPercent()` -> float
- `IsDestroyed()` -> bool

#### 3.5 SystemDamageComponent.h/.cpp

Properties:
- SubsystemHealth (TMap<FName, float>)
- SubsystemMaxHealth (TMap<FName, float>)
- SubsystemDamageThreshold (float percentage of hull damage that propagates to subsystems)

**Subsystem naming convention:**
Use default subsystem keys: "Engines", "Weapons", "LifeSupport". Additionally, read system names from the ship's DSL definition and use those as additional subsystem keys. For example:
- If ship has `system "Fuel_Tank"`, include "Fuel_Tank" as a damageable subsystem
- If ship has `system "Quantum_Engine"`, include "Quantum_Engine" (or map to "QuantumDrive") as a damageable subsystem

Methods:
- `ApplySystemDamage(IncomingHullDamage)` - calculate subsystem damage = IncomingHullDamage * SubsystemDamageThreshold; select random subsystem weighted by health; apply damage; check thresholds and apply penalties based on subsystem type:
  - Engines/Fuel_Tank < 50%: reduce max speed by 40%
  - Engines/Fuel_Tank < 25%: reduce thrust to 30%
  - Engines/Fuel_Tank <= 0: ship cannot move
  - Quantum_Engine/QuantumDrive < 50%: double spool time
  - Quantum_Engine/QuantumDrive <= 0: cannot quantum jump
  - Weapons < 50%: double fire rate (slower)
  - Weapons <= 0: cannot fire
- `RepairSubsystem(SystemName, Amount)` - add repair amount, remove penalties when health crosses back above thresholds
- `GetSubsystemHealth(SystemName)` -> float
- `GetSubsystemStatus(SystemName)` -> enum (Operational, Damaged, Critical, Destroyed)

#### 3.6 CombatTargetComponent.h/.cpp
Properties:
- bIsTargetable (bool)
- TargetPriority (float higher = AI prefers targeting)

### Step 4: Generate Pirate AI Controller and Behavior Tree

#### 4.1 PirateAIController.h/.cpp

Properties:
- FactionName (FName, "Void_Syndicate")
- HostilityToPlayer (float 0=neutral, 1=hostile)
- DetectionRange (float)
- EngagementRange (float)
- CurrentState (enum: Patrolling, Investigating, Pursuing, Engaging, Retreating)

Methods - State Machine in `TickController(DeltaTime)`:

**Patrolling:**
- Move along patrol path between stations or random waypoints
- Scan for player within DetectionRange
- If player detected and HostilityToPlayer > 0.5: transition to Investigating

**Investigating:**
- Move toward player's last known position
- If player within EngagementRange and HostilityToPlayer > 0.7: transition to Engaging
- If player lost for > 30 seconds: transition to Patrolling

**Engaging:**
- Maintain optimal combat range (not too close, not too far)
- Iterate ship's weapon slots and fire the first available one with ready status (do NOT use hardcoded slot names like "ForwardCannons")
- If player beyond weapon arc: maneuver to bring weapons to bear
- If player fires missile: attempt evasive maneuvers
- If shields depleted and hull < 30%: transition to Retreating

**Retreating:**
- Full thrust away from player
- Attempt quantum jump if QuantumDrive functional
- If quantum jump succeeds: despawn
- If player disengages for > 60 seconds: transition to Patrolling

Helper methods:
- `ScanForPlayer()` - check distance to player ship, check if player has hostile faction standing, return true if valid target
- `EvaluateThreat()` - calculate threat based on player ship weapons, distance, hull status, return threat level 0-1

#### 4.2 PirateBehaviorTree

Generated behavior tree asset as a `.behaviortree` text file in `Content/ProceduralGenerated/AI/PirateBehaviorTree.behaviortree`.

Structure:
- Root: Selector
  - Sequence: IsDestroyed? → PlayDestructionSequence → Despawn
  - Sequence: HealthLow AND ShieldsDepleted? → SetState Retreating → RunEQS for escape vector → MoveTo
  - Sequence: HasTarget AND TargetInRange? → SetState Engaging → RunCombatRoutine
  - Sequence: HasTarget AND !TargetInRange? → SetState Investigating → MoveTo last known position
  - Default: SetState Patrolling → MoveTo random patrol point
