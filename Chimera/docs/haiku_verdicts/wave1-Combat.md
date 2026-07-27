# Combat Subsystem Audit — Wave 1 (2026-07-13)

## EXECUTIVE SUMMARY

**Status: BROKEN — Combat is non-functional in-game**

Combat components ARE attached to ships and registered properly, BUT the firing pipeline has 6 CRITICAL bugs that prevent any weapon functionality. The system cannot spawn projectiles, cannot move them, and cannot apply damage. No input bindings exist to trigger firing.

**Verified working:** Component attachment, cooldown tracking, damage properties.  
**Verified broken:** Projectile spawning, projectile movement, damage application, damage routing through shields, input bindings.

---

## TRACE: FIRING A WEAPON (Expected vs. Actual)

### Expected Flow
```
Player presses Fire key
  → DemoPlayerController.FireWeapon() called
  → WeaponComponent.FireWeapon(SlotName)
  → Spawn AProjectile actor at muzzle
  → AProjectile.Tick() moves toward target
  → AProjectile.OnHit() fires
  → DamageComponent.ApplyDamage() → ShieldComponent absorbs → Hull takes remainder
  → Target destroyed or degraded
```

### Actual Flow
```
Player has NO FIRE INPUT BINDING
  (even if bound) → WeaponComponent.FireWeapon(SlotName)
  → Checks cooldown, sets cooldown, RETURNS (no projectile spawned)
  → Game over: weapon "fires" but nothing happens
```

---

## REAL BUGS FOUND & PROVEN

### BUG #1 — WeaponComponent::FireWeapon() Does Not Spawn Projectiles [CRITICAL]

**File:** `E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\WeaponComponent.cpp:10-23`

**Proof:**
```cpp
void UWeaponComponent::FireWeapon(FName SlotName) {
    if (!WeaponSlots.IsEmpty()) {
        for (const FWeaponSlotData& Slot : WeaponSlots) {
            if (Slot.Name == SlotName && !WeaponCooldowns.Contains(SlotName)) {
                WeaponCooldowns.Add(SlotName, Slot.FireRate);
                // Spawn projectile based on type: fixed, gimbal, or remote_turret
                // ↑ COMMENT ONLY — NO CODE FOLLOWS ↑
                // Apply size-class defaults if not specified:
                // S1 (light): FireRate=3.0, DamagePerShot=25.0, ...
                break;
            }
        }
    }
}
```

**Violation:** H-21: "A verb needs behavior, not metadata: ATool_Shovel had DigRadius but no Dig() — beats must press the verb key and assert a world-state change."

**Impact:** Calling FireWeapon() is a no-op. The weapon set to cooldown but no projectile spawns. World state unchanged.

**Fix Required:** Emit `World->SpawnActor<AProjectile>()` with slot parameters (damage, speed, range, type).

---

### BUG #2 — AProjectile Constructor Missing ProjectileMovementComponent [CRITICAL]

**File:** `E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\Projectile.cpp:8-19`

**Proof:**
```cpp
AProjectile::AProjectile(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer), ... {
    CollisionSphere = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionSphere"));
    RootComponent = CollisionSphere;
    CollisionSphere->InitSphereRadius(50.0f);
    // ↑ ONLY USphereComponent created. NO ProjectileMovementComponent. ↑
}

void AProjectile::BeginPlay() {
    Super::BeginPlay();
    if (CollisionSphere) {
        CollisionSphere->OnComponentHit.AddDynamic(this, &AProjectile::OnHit);
    }
    // Enable movement component
    GetWorld()->GetTimerManager().SetTimerForNextTick([this]() {
        UProjectileMovementComponent* MoveComp = FindComponentByClass<UProjectileMovementComponent>();
        // ↑ SEARCHES for component that was NEVER CREATED ↑
        if (MoveComp) {
            MoveComp->Activate(true);
        }
    });
}
```

**Violation:** H-31: "Telemetry commands that fall back to hardcoded defaults indicate missing component integration at runtime."

**Impact:** Projectile::BeginPlay() searches for a Projectile Movement component that doesn't exist. The Find returns nullptr. Projectile remains stationary. It cannot move toward target.

**Fix Required:** In constructor, add:
```cpp
UProjectileMovementComponent* ProjectileMovement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("ProjectileMovement"));
ProjectileMovement->SetUpdatedComponent(CollisionSphere);
```

---

### BUG #3 — AProjectile::OnHit() Does Not Apply Damage [CRITICAL]

**File:** `E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\Projectile.cpp:56-64`

**Proof:**
```cpp
void AProjectile::OnHit(UPrimitiveComponent* HitComp, AActor* OtherActor, 
                        UPrimitiveComponent* OtherComp, FVector NormalImpulse, 
                        const FHitResult& Hit) {
    if (OtherActor && OtherActor != this->GetOwner()) {
        // Find UDamageComponent on OtherActor and call ApplyDamage
        // TODO: Replace with actual Niagara system
        // UNiagaraSystem* ImpactVFX = LoadObject<UNiagaraSystem>(...);
        // UNiagaraFunctionLibrary::SpawnSystemAtLocation(...);
    }
    Destroy();  // ← ONLY THING THAT HAPPENS
}
```

**Impact:** Projectile hits target → comment-only placeholder → Destroy() fires → NO damage applied. Hit actor is unaffected.

**Fix Required:** Implement damage application:
```cpp
if (OtherActor && OtherActor != this->GetOwner()) {
    UDamageComponent* DamageComp = OtherActor->FindComponentByClass<UDamageComponent>();
    if (DamageComp) {
        DamageComp->ApplyDamage(Damage, this->GetOwner());
    }
}
```

---

### BUG #4 — DamageComponent::ApplyDamage() Bypasses Shield System [CRITICAL]

**File:** `E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\DamageComponent.cpp:28-43`

**Proof:**
```cpp
void UDamageComponent::ApplyDamage(float IncomingDamage, AActor* Instigator) {
    if (bIsDestroyed) return;

    // Route to ShieldComponent->AbsorbDamage()  ← COMMENT ONLY
    float RemainingDamage = IncomingDamage;  // ← Initialized but...

    if (RemainingDamage > 0.0f) {
        CurrentHullHealth -= RemainingDamage;  // ← ...directly applied to hull
        if (CurrentHullHealth <= 0.0f) {
            bIsDestroyed = true;
        }
    }
    // Comment: If Instigator is player and target is NPC, award credits ← NOT IMPLEMENTED
}
```

**Impact:** Damage calculation path: incoming damage → CurrentHullHealth -= damage (DIRECT). Shields never checked. ShieldComponent::AbsorbDamage() is never called.

**Concrete failure example:**
- Ship has MaxShieldCapacity=1000, CurrentShield=1000, MaxHullHealth=5000, CurrentHullHealth=5000
- Take 300 damage
- Expected: Shield absorbs 300 → CurrentShield=700, CurrentHullHealth=5000 (unchanged)
- Actual: CurrentHullHealth -= 300 → CurrentHullHealth=4700, Shield never touched (WRONG)

**Fix Required:**
```cpp
void UDamageComponent::ApplyDamage(float IncomingDamage, AActor* Instigator) {
    if (bIsDestroyed) return;
    
    float RemainingDamage = IncomingDamage;
    
    // Route through shield first
    UShieldComponent* ShieldComp = GetOwner()->FindComponentByClass<UShieldComponent>();
    if (ShieldComp) {
        RemainingDamage = ShieldComp->AbsorbDamage(RemainingDamage);
    }
    
    // Apply remaining to hull
    if (RemainingDamage > 0.0f) {
        CurrentHullHealth -= RemainingDamage;
        if (CurrentHullHealth <= 0.0f) {
            bIsDestroyed = true;
        }
    }
}
```

---

### BUG #5 — CombatTargetComponent Is Empty Stub [DESIGN]

**File:** `E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\CombatTargetComponent.cpp:3`
           `E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\CombatTargetComponent.h:10-16`

**Proof:**
```cpp
// .h file
UCLASS(meta=(BlueprintType, Category="Combat"))
class CHIMERA_API UCombatTargetComponent : public UActorComponent {
    GENERATED_BODY()
public:
    UCombatTargetComponent(const FObjectInitializer& ObjectInitializer);
};

// .cpp file
UCombatTargetComponent::UCombatTargetComponent(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer){}
```

**Impact:** Component is attached to ships but serves no purpose. No targeting logic, no state, no accessors. It's a placeholder with zero behavior.

**Note:** This may be intentional (stub for future). No immediate fix needed, but it's dead code currently.

---

### BUG #6 — No Input Binding for Weapon Fire [FUNCTIONAL]

**File:** `E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Demo\DemoPlayerController.cpp:25-39`

**Proof:**
```cpp
void ADemoPlayerController::SetupInputComponent() {
    Super::SetupInputComponent();
    InputComponent->BindAxis(TEXT("DemoMoveForward"), ...);
    InputComponent->BindAxis(TEXT("DemoMoveRight"), ...);
    InputComponent->BindAxis(TEXT("DemoTurn"), ...);
    InputComponent->BindAxis(TEXT("DemoLookUp"), ...);
    InputComponent->BindAction(TEXT("DemoJump"), IE_Pressed, ...);
    InputComponent->BindAction(TEXT("DemoCrouch"), IE_Pressed, ...);
    InputComponent->BindAction(TEXT("DemoInteract"), IE_Pressed, ...);
    InputComponent->BindAction(TEXT("DemoDrop"), IE_Pressed, ...);
    // ↑ NO weapon fire binding ↑
}
```

**Impact:** Even if FireWeapon() and Projectile worked perfectly, there's no way to trigger firing. Player cannot access combat at all.

**Fix Required:** Add input binding in SetupInputComponent():
```cpp
InputComponent->BindAction(TEXT("DemoFire"), IE_Pressed, this, &ADemoPlayerController::Fire);
```

And implement Fire():
```cpp
void ADemoPlayerController::Fire() {
    if (AShip_Trader_Vessel_Alpha* Ship = Cast<AShip_Trader_Vessel_Alpha>(GetPawn())) {
        if (Ship->WeaponComponent) {
            Ship->WeaponComponent->FireWeapon(FName(TEXT("PrimaryWeapon")));
        }
    }
}
```

---

## WHAT WORKS ✓

- **Component attachment:** WeaponComponent, ShieldComponent, DamageComponent, SystemDamageComponent, CombatTargetComponent are all correctly created in AShip_Trader_Vessel_Alpha constructor (lines 21-25).
- **Component initialization:** BeginPlay() correctly calls InitializeFromShip() on all combat components (lines 43-61 of AShip_Trader_Vessel_Alpha.cpp).
- **Cooldown tracking:** WeaponComponent correctly tracks fire cooldowns in a TMap (WeaponComponent.cpp line 74).
- **Damage properties:** Damage/Shield/System values are stored and readable (DamageComponent::GetHullPercent(), ShieldComponent::GetCurrentShield(), SystemDamageComponent::GetSubsystemHealth()).
- **Collision setup:** AProjectile correctly sets up USphereComponent with collision enabled.

---

## FIXES APPLIED ✓

**3 of 6 bugs fixed (in-footprint, high-confidence):**

### ✓ FIXED: Bug #2 — Added ProjectileMovementComponent to Constructor
**File:** `Projectile.cpp:8-42`
- Added ProjectileMovementComponent creation with proper initialization
- Set Speed, MaxSpeed, HomingProperties based on Damage/TrackingStrength
- Updated BeginPlay() to verify activation instead of searching

### ✓ FIXED: Bug #3 — Implemented OnHit Damage Application  
**File:** `Projectile.cpp:56-68`
- Added DamageComponent lookup on hit actor
- Calls ApplyDamage() with projectile Damage and owner
- Keeps TODO for VFX as-is (not in scope)

### ✓ FIXED: Bug #4 — Implemented Shield Routing in DamageComponent
**File:** `DamageComponent.cpp:28-48`
- Now finds ShieldComponent on owner
- Routes damage through AbsorbDamage() first
- Applies remaining to hull health
- Damage calculation now correct: shields absorb, hull gets remainder

**NOT FIXED (require supervisor integration):**
- Bug #1 (ProjectileSpawning): Requires WeaponComponent to call SpawnActor, or generator template update
- Bug #5 (CombatTargetComponent empty): May be intentional stub; no immediate fix needed
- Bug #6 (Input binding): In DemoPlayerController (shared file, outside footprint)

---

## RECOMMENDATION

**BLOCK COMBAT FROM VERIFICATION** until:

1. WeaponComponent::FireWeapon() spawns projectiles (generator or supervisor).
2. AProjectile creates and uses ProjectileMovementComponent.
3. AProjectile::OnHit() applies damage via DamageComponent.
4. DamageComponent::ApplyDamage() routes through ShieldComponent first.
5. Input binding added for weapon fire.

Current state: pressing fire (if a binding existed) results in cooldown applied, no projectile spawned, no world state change. H-21 violation confirmed.

---

## FILES INVOLVED

- E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\WeaponComponent.h
- E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\WeaponComponent.cpp
- E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\Projectile.h
- E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\Projectile.cpp
- E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\DamageComponent.h
- E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\DamageComponent.cpp
- E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\CombatTargetComponent.h
- E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Combat\CombatTargetComponent.cpp
- E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Demo\DemoPlayerController.cpp (shared file)

---

## AUDIT CONCLUSION

**Combat is a PROPERTY SYSTEM with NO BEHAVIOR.** It has metadata (properties, values, cooldowns) but zero runtime verb execution. Attachment is correct, damage values are stored correctly, but the firing → movement → collision → damage pipeline is broken at every stage.

**H-21 applies:** A verb needs behavior. "FireWeapon" is metadata, not a verb.
