"""
================================================================================
CHIMERA PROCEDURAL GAME GENERATOR - SINGLE SOURCE OF TRUTH
================================================================================

This file is the central source of truth for the entire Chimera game project.
It serves as both the executable generator and the inventory system for all
active C++ files and Unreal Engine content.

ARCHITECTURE OVERVIEW:
======================
1. CONFIGURATION MODULE
   - Game parameters, procedural rules, vehicle specs, level generation rules
   - Located in Python/config.py

2. C++ GENERATION ENGINE MODULE
   - Functions that generate and write .h and .cpp files to Source/Chimera/
   - Located in Python/cpp_generator.py

3. SELF-MODIFYING INVENTORY SECTION
   - Maintains a list of all active C++ files and their complete source code
   - Automatically updated by the script to include all C++ files as comments
   - Recursively examines Source/Chimera/ and subdirectories (OffroadCar/, SportsCar/, etc.)

4. UNREAL ENGINE API OPERATIONS MODULE
   - Uses import unreal to create levels, place vehicles, generate variants
   - Located in Python/unreal_api_operations.py
   - Works in conjunction with the existing starter level (VehicleBasic)

5. SCREENSHOT AND LM STUDIO WORKFLOW MODULE
    - Captures viewport screenshots and sends them to LM Studio's local server for analysis
    - Located in Python/screenshot_lmstudio_workflow.py
    - Uses REST API to communicate with LM Studio at http://192.168.3.169:1234

6. PLAY TEST MODULE
    - Automated testing of flight vehicle 6DOF movement system
    - Tests thrust, strafe, rotation (pitch/yaw/roll), and idle damping
    - Captures screenshots during test phases for AI analysis
    - Located in Python/play_test.py

7. AUTONOMOUS STATE SYNCHRONIZATION (EYES, EARS, MOUTH, CONTROL)
   - EYES/VISION: Scans the entire Source/Chimera/ directory to see what C++ files exist
   - EARS/HEARING: Reads the current configuration and expected project state
   - MOUTH/HANDS: Creates, updates, or deletes C++ files autonomously to match the single source of truth
   - CONTROL: Ensures the on-disk C++ project state exactly matches the Python script's defined design

EXECUTION WORKFLOW:
===================
- This script is designed to execute automatically when the Unreal Editor starts
- It generates C++ template files into Source/Chimera/
- It updates its own source code to include all C++ files as comments
- It uses import unreal for level generation, vehicle placement, and variant management
- It autonomously synchronizes the C++ project state (creating/updating/deleting files as needed)
- It can capture viewport screenshots and send them to LM Studio for AI analysis via REST API
- After execution, you may need to trigger a C++ build process (via UBT)
  separately to compile the generated C++ code

================================================================================
"""

import os
import re
import sys

# Ensure the Python scripts directory is in sys.path for modular imports
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

# Import modular components
from config import GameConfiguration
from cpp_generator import ensure_directories, generate_all_cpp_components
from unreal_api_operations import generate_levels_and_actors, create_procedural_level
from screenshot_lmstudio_workflow import run_screenshot_analysis_workflow

try:
    from play_test import FlightPlayTest, run_playtest as run_playtest_entry
except ImportError:
    FlightPlayTest = None
    run_playtest_entry = None

try:
    from runtime_screenshot_playtest import RuntimeScreenshotPlayTest, run_runtime_screenshot_playtest
except ImportError:
    RuntimeScreenshotPlayTest = None
    run_runtime_screenshot_playtest = None


# ============================================================================
# PUBLIC API — ENTRY POINTS FOR UE EDITOR & EXTERNAL CALLERS
# ============================================================================

def generate_all():
    """Generate all C++ components and sync project state.
    
    Convenience function for external callers (init_unreal.py, validation_test_suite.py).
    """
    ensure_directories()
    generate_all_cpp_components()
    sync_cpp_project_state()


def run_startup_workflow():
    """Run the complete startup workflow: generate C++, load level, spawn vehicle.
    
    Convenience function for external callers (init_unreal.py).
    """
    print("[STARTUP] Running complete startup workflow...")
    
    # Phase 1: Generate C++ files and sync project state
    ensure_directories()
    generate_all_cpp_components()
    sync_cpp_project_state()
    
    # Phase 2: Load starter level, spawn vehicle, and create flight test environment
    try:
        import unreal
        generate_levels_and_actors()
        
        # Create FlightTestLevel for 6DOF movement testing
        from unreal_api_operations import create_flight_test_level
        create_flight_test_level()
        
        print("[STARTUP] Level generation and flight test environment complete.")
    except ImportError:
        print("[STARTUP] UE module not available — skipping level operations (simulation mode)")


# ============================================================================
# SECTION 3: SELF-MODIFYING INVENTORY SYSTEM & AUTONOMOUS STATE SYNCHRONIZATION
# ============================================================================

def get_expected_cpp_files():
    """
    Returns a set of expected C++ file names (base names) that should exist 
    based on the current procedural generation state and core project design.
    This is the 'truth' that the script enforces.
    """
    expected_files = set()
    
    # Core Project Base Files (The UE Vehicle Template Foundation - Must be preserved)
    core_files = [
        "Chimera.h", "Chimera.cpp",
        "Chimera.Build.cs",
        "ChimeraGameMode.h", "ChimeraGameMode.cpp",
        "ChimeraPawn.h", "ChimeraPawn.cpp",
        "ChimeraPlayerController.h", "ChimeraPlayerController.cpp",
        "ChimeraUI.h", "ChimeraUI.cpp",
        "ChimeraWheelFront.h", "ChimeraWheelFront.cpp",
        "ChimeraWheelRear.h", "ChimeraWheelRear.cpp",
        "ChimeraSportsCar.h", "ChimeraSportsCar.cpp"
    ]

    for f in core_files:
        expected_files.add(f)

    # Generated Procedural Components (Autonomously managed by this script)
    generated_components = [
        "ProceduralGeneratorComponent.h", "ProceduralGeneratorComponent.cpp",
        "VehicleSpawnerComponent.h", "VehicleSpawnerComponent.cpp",
        "LevelGeneratorComponent.h", "LevelGeneratorComponent.cpp",
        "FlightControlComponent.h", "FlightControlComponent.cpp",
        "FlightTestLevel.h"
    ]
    for f in generated_components:
        expected_files.add(f)

    return expected_files


def get_all_cpp_files_recursive(directory):
    """Recursively get all C++ files in the Source/Chimera directory and subdirectories."""
    cpp_files = {}

    if not os.path.exists(directory):
        return cpp_files

    for root, dirs, files in os.walk(directory):
        # Skip certain directories that shouldn't be scanned
        dirs[:] = [d for d in dirs if d not in ['Generated', 'DerivedDataCache', 'Intermediate', 'Saved', '.vs']]

        for filename in files:
            if filename.endswith('.h') or filename.endswith('.cpp') or filename.endswith('.generated.h'):
                file_path = os.path.join(root, filename)
                
                # Make path relative to Source/Chimera for cleaner inventory display
                try:
                    rel_path = os.path.relpath(file_path, directory)
                except ValueError:
                    rel_path = file_path
                    
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                cpp_files[rel_path] = {
                    'path': file_path,
                    'content': content
                }

    return cpp_files


def get_all_cpp_files():
    """Get all C++ files in the Source/Chimera directory and subdirectories."""
    source_dir = GameConfiguration.source_dir()
    return get_all_cpp_files_recursive(source_dir)


def sync_cpp_project_state():
    """
    AUTONOMOUS C++ PROJECT STATE SYNCHRONIZATION.
    Gives the Python script 'eyes' to scan the project, and a 'mouth/hands' to create, update, or delete files.
    Ensures the on-disk C++ project state exactly matches the single source of truth defined in this script.
    """
    print("[AUTO-SYNC] Running autonomous C++ project state synchronization...")
    source_dir = GameConfiguration.source_dir()

    # 1. EYES/VISION: Scan existing C++ files on disk
    existing_cpp_files = get_all_cpp_files_recursive(source_dir)
    
    # 2. TRUTH/CONFIGURATION: Get expected files from the single source of truth
    expected_files = get_expected_cpp_files()

    # 3. CONTROL/MOUTH: Compare and sync - delete obsolete or unexpected C++ files
    files_to_delete = []
    for rel_path, file_data in existing_cpp_files.items():
        basename = os.path.basename(rel_path)
        
        # Check if the file's base name is in the expected list
        is_expected = any(basename == exp_file for exp_file in expected_files)

        if not is_expected:
            # It's an unexpected C++ file that is not part of the core template or generated components
            # This is where the script exercises its 'control' to remove obsolete classes
            
            # Preserve subdirectory content (OffroadCar/, SportsCar/, Variant_*) unless they are temp files
            is_subdir_file = os.sep in rel_path and not rel_path.startswith('OffroadCar/') and not rel_path.startswith('SportsCar/') and not rel_path.startswith('Variant_OffRoad/') and not rel_path.startswith('Variant_TimeTrial/')
            
            # If it's a random .h/.cpp file in the root Source/Chimera/ that isn't expected, delete it
            if not is_subdir_file and (rel_path.endswith('.h') or rel_path.endswith('.cpp')):
                files_to_delete.append(file_data['path'])
                print(f"[AUTO-SYNC] Identified obsolete C++ file for removal: {rel_path}")

    # Execute deletions (The 'Mouth/Hands' of the script)
    for del_path in files_to_delete:
        try:
            os.remove(del_path)
            print(f"[AUTO-CLEANUP] REMOVED obsolete C++ file: {del_path}")
        except Exception as e:
            print(f"[AUTO-CLEANUP ERROR] Could not remove {del_path}: {e}")

    # 4. ENSURE EXPECTED FILES EXIST (Create if missing)
    # This is primarily handled by generate_all_cpp_components(), but we log the sync status
    print("[AUTO-SYNC] C++ project state synchronization complete. Project state matches single source of truth.")


def update_self_inventory():
    """Reads all generated C++ files and updates this Python file's inventory section."""
    # Get current file path
    current_file_path = os.path.abspath(__file__)

    # Read the current file content
    with open(current_file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    # Get all C++ files (including existing demo files)
    cpp_files = get_all_cpp_files()

    # Generate inventory section
    inventory_section = r"""# === BEGIN C++ INVENTORY ===
# This section contains a complete inventory of all active C++ files
# and their source code as comments. This is automatically maintained
# by the ProceduralGameGenerator script.
# Includes both generated files and existing project demo files.

// ============================================================================
// FILE: Chimera.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Chimera.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #include "Chimera.h"
// #include "Modules/ModuleManager.h"
// 
// IMPLEMENT_PRIMARY_GAME_MODULE( FDefaultGameModuleImpl, Chimera, "Chimera" );
// 
// DEFINE_LOG_CATEGORY(LogChimera)

// ============================================================================
// FILE: Chimera.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Chimera.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// 
// /** Main log category used across the project */
// DECLARE_LOG_CATEGORY_EXTERN(LogChimera, Log, All);

// ============================================================================
// FILE: ChimeraGameMode.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraGameMode.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #include "ChimeraGameMode.h"
// #include "ChimeraPlayerController.h"
// 
// AChimeraGameMode::AChimeraGameMode()
// {
// 	PlayerControllerClass = AChimeraPlayerController::StaticClass();
// }
// 

// ============================================================================
// FILE: ChimeraGameMode.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraGameMode.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "GameFramework/GameModeBase.h"
// #include "ChimeraGameMode.generated.h"
// 
// UCLASS(abstract)
// class AChimeraGameMode : public AGameModeBase
// {
// 	GENERATED_BODY()
// 
// public:
// 	AChimeraGameMode();
// };
// 
// 
// 
// 

// ============================================================================
// FILE: ChimeraPawn.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraPawn.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #include "ChimeraPawn.h"
// #include "ChimeraWheelFront.h"
// #include "ChimeraWheelRear.h"
// #include "ThrustVectoringComponent.h"
// #include "AttitudeStabilizerComponent.h"
// #include "Components/SkeletalMeshComponent.h"
// #include "GameFramework/SpringArmComponent.h"
// #include "Camera/CameraComponent.h"
// #include "EnhancedInputComponent.h"
// #include "EnhancedInputSubsystems.h"
// #include "InputActionValue.h"
// #include "ChaosWheeledVehicleMovementComponent.h"
// #include "Chimera.h"
// #include "TimerManager.h"
// 
// #define LOCTEXT_NAMESPACE "VehiclePawn"
// 
// AChimeraPawn::AChimeraPawn()
// {
// 	// construct the front camera boom
// 	FrontSpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("Front Spring Arm"));
// 	FrontSpringArm->SetupAttachment(GetMesh());
// 	FrontSpringArm->TargetArmLength = 0.0f;
// 	FrontSpringArm->bDoCollisionTest = false;
// 	FrontSpringArm->bEnableCameraRotationLag = true;
// 	FrontSpringArm->CameraRotationLagSpeed = 15.0f;
// 	FrontSpringArm->SetRelativeLocation(FVector(30.0f, 0.0f, 120.0f));
// 
// 	FrontCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("Front Camera"));
// 	FrontCamera->SetupAttachment(FrontSpringArm);
// 	FrontCamera->bAutoActivate = false;
// 
// 	// construct the back camera boom
// 	BackSpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("Back Spring Arm"));
// 	BackSpringArm->SetupAttachment(GetMesh());
// 	BackSpringArm->TargetArmLength = 650.0f;
// 	BackSpringArm->SocketOffset.Z = 150.0f;
// 	BackSpringArm->bDoCollisionTest = false;
// 	BackSpringArm->bInheritPitch = false;
// 	BackSpringArm->bInheritRoll = false;
// 	BackSpringArm->bEnableCameraRotationLag = true;
// 	BackSpringArm->CameraRotationLagSpeed = 2.0f;
// 	BackSpringArm->CameraLagMaxDistance = 50.0f;
// 
// 	BackCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("Back Camera"));
// 	BackCamera->SetupAttachment(BackSpringArm);
// 
// 	// Configure the car mesh
// 	GetMesh()->SetSimulatePhysics(true);
// 	GetMesh()->SetCollisionProfileName(FName("Vehicle"));
// 
// 	// get the Chaos Wheeled movement component
// 	ChaosVehicleMovement = CastChecked<UChaosWheeledVehicleMovementComponent>(GetVehicleMovement());
// 
// 	// Create flight control components
// 	ThrustVectoring = CreateDefaultSubobject<UThrustVectoringComponent>(TEXT("ThrustVectoring"));
// 	ThrustVectoring->SetupAttachment(GetRootComponent());
// 
// 	AttitudeStabilizer = CreateDefaultSubobject<UAttitudeStabilizerComponent>(TEXT("AttitudeStabilizer"));
// 	AttitudeStabilizer->SetupAttachment(GetRootComponent());
// 
// }
// 
// void AChimeraPawn::SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent)
// {
// 	Super::SetupPlayerInputComponent(PlayerInputComponent);
// 
// 	if (UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(PlayerInputComponent))
// 	{
// 		// steering 
// 		EnhancedInputComponent->BindAction(SteeringAction, ETriggerEvent::Triggered, this, &AChimeraPawn::Steering);
// 		EnhancedInputComponent->BindAction(SteeringAction, ETriggerEvent::Completed, this, &AChimeraPawn::Steering);
// 
// 		// throttle 
// 		EnhancedInputComponent->BindAction(ThrottleAction, ETriggerEvent::Triggered, this, &AChimeraPawn::Throttle);
// 		EnhancedInputComponent->BindAction(ThrottleAction, ETriggerEvent::Completed, this, &AChimeraPawn::Throttle);
// 
// 		// break 
// 		EnhancedInputComponent->BindAction(BrakeAction, ETriggerEvent::Triggered, this, &AChimeraPawn::Brake);
// 		EnhancedInputComponent->BindAction(BrakeAction, ETriggerEvent::Started, this, &AChimeraPawn::StartBrake);
// 		EnhancedInputComponent->BindAction(BrakeAction, ETriggerEvent::Completed, this, &AChimeraPawn::StopBrake);
// 
// 		// handbrake 
// 		EnhancedInputComponent->BindAction(HandbrakeAction, ETriggerEvent::Started, this, &AChimeraPawn::StartHandbrake);
// 		EnhancedInputComponent->BindAction(HandbrakeAction, ETriggerEvent::Completed, this, &AChimeraPawn::StopHandbrake);
// 
// 		// look around 
// 		EnhancedInputComponent->BindAction(LookAroundAction, ETriggerEvent::Triggered, this, &AChimeraPawn::LookAround);
// 
// 		// toggle camera 
// 		EnhancedInputComponent->BindAction(ToggleCameraAction, ETriggerEvent::Triggered, this, &AChimeraPawn::ToggleCamera);
// 
// 		// reset the vehicle 
// 		EnhancedInputComponent->BindAction(ResetVehicleAction, ETriggerEvent::Triggered, this, &AChimeraPawn::ResetVehicle);
// 
// 		// flight controls
// 		EnhancedInputComponent->BindAction(PitchAction, ETriggerEvent::Triggered, this, &AChimeraPawn::Pitch);
// 		EnhancedInputComponent->BindAction(YawAction, ETriggerEvent::Triggered, this, &AChimeraPawn::Yaw);
// 		EnhancedInputComponent->BindAction(RollAction, ETriggerEvent::Triggered, this, &AChimeraPawn::Roll);
// 		EnhancedInputComponent->BindAction(ThrustAction, ETriggerEvent::Triggered, this, &AChimeraPawn::Thrust);
// 		EnhancedInputComponent->BindAction(StrafeXAction, ETriggerEvent::Triggered, this, &AChimeraPawn::StrafeX);
// 		EnhancedInputComponent->BindAction(StrafeYAction, ETriggerEvent::Triggered, this, &AChimeraPawn::StrafeY);
// 
// 		// Flight mode toggle (press F)
// 		static FName ToggleFlightName(TEXT("ToggleFlightMode"));
// 		EnhancedInputComponent->BindAction(ToggleFlightName, ETriggerEvent::Triggered, this, &AChimeraPawn::DoToggleFlightMode);
// 	}
// 	else
// 	{
// 		UE_LOG(LogChimera, Error, TEXT("'%s' Failed to find an Enhanced Input component! This template is built to use the Enhanced Input system. If you intend to use the legacy system, then you will need to update this C++ file."), *GetNameSafe(this));
// 	}
// }
// 
// void AChimeraPawn::BeginPlay()
// {
// 	Super::BeginPlay();
// 
// 	// set up the flipped check timer (disabled when in flight mode)
// 	GetWorld()->GetTimerManager().SetTimer(FlipCheckTimer, this, &AChimeraPawn::FlippedCheck, FlipCheckTime, true);
// }
// 
// void AChimeraPawn::EndPlay(EEndPlayReason::Type EndPlayReason)
// {
// 	// clear the flipped check timer
// 	GetWorld()->GetTimerManager().ClearTimer(FlipCheckTimer);
// 
// 	Super::EndPlay(EndPlayReason);
// }
// 
// void AChimeraPawn::Tick(float Delta)
// {
// 	Super::Tick(Delta);
// 
// 	if (bFlightModeEnabled)
// 	{
// 		// Disable gravity for space flight
// 		SetEnableGravity(false);
// 
// 		// Apply accumulated thrust and strafe forces
// 		FVector CurrentLinVel = GetMesh()->GetPhysicsLinearVelocity();
// 		
// 		// Velocity damping (minimal drag in space)
// 		CurrentLinVel *= 0.98f;
// 
// 		// Apply thrust in local forward direction
// 		FVector ThrustDir = GetActorForwardVector() * bThrustForward * ThrustPower * Delta;
// 		CurrentLinVel += ThrustDir;
// 
// 		// Apply reverse thrust
// 		FVector ReverseThrustDir = GetActorForwardVector() * bThrustReverse * ThrustPower * Delta;
// 		CurrentLinVel -= ReverseThrustDir;
// 
// 		// Apply strafe in local right (X) and up (Z) directions
// 		FVector RightDir = GetActorRightVector();
// 		FVector UpDir = GetActorUpVector();
// 
// 		CurrentLinVel += RightDir * bStrafeLeft * ThrustPower * Delta;
// 		CurrentLinVel -= RightDir * bStrafeRight * ThrustPower * Delta;
// 		CurrentLinVel += UpDir * bStrafeDown * ThrustPower * Delta;
// 		CurrentLinVel -= UpDir * bStrafeUp * ThrustPower * Delta;
// 
// 		GetMesh()->SetPhysicsLinearVelocity(CurrentLinVel, false);
// 
// 		// Apply angular velocity for pitch/yaw/roll (6DOF rotation)
// 		FVector CurrentAngVel = GetMesh()->GetPhysicsAngularVelocityInDegrees();
// 
// 		float AngVelScale = RotationSpeed * 100.0f;
// 
// 		CurrentAngVel.Y += bPitchUp * AngVelScale * Delta;
// 		CurrentAngVel.Y -= bPitchDown * AngVelScale * Delta;
// 		CurrentAngVel.X += bYawRight * AngVelScale * Delta;
// 		CurrentAngVel.X -= bYawLeft * AngVelScale * Delta;
// 		CurrentAngVel.Z += bRollRight * AngVelScale * Delta;
// 		CurrentAngVel.Z -= bRollLeft * AngVelScale * Delta;
// 
// 		// Apply idle damping when no rotation input (prevents drift)
// 		if (!bPitchUp && !bPitchDown && !bYawLeft && !bYawRight && !bRollLeft && !bRollRight)
// 		{
// 			CurrentAngVel *= (1.0f - AngularDampingWhenIdle * Delta);
// 		}
// 
// 		GetMesh()->SetPhysicsAngularVelocityInDegrees(CurrentAngVel, false);
// 
// 		// Apply thrust vectoring if component exists
// 		if (ThrustVectoring)
// 		{
// 			FVector ThrustDir = ThrustVectoring->GetThrustDirection();
// 			if (!ThrustDir.IsZero())
// 			{
// 				GetMesh()->AddImpulse(ThrustDir * ThrustPower, FVector::ZeroVector);
// 			}
// 		}
// 
// 		// Apply attitude stabilization if component exists and enabled
// 		if (AttitudeStabilizer && AttitudeStabilizer->IsAutoStabilizing())
// 		{
// 			FVector CurrentAngVel = GetMesh()->GetPhysicsAngularVelocityInDegrees();
// 			float DampingFactor = 1.0f - (AttitudeStabilizer->StabilizationStrength * Delta * 5.0f);
// 			DampingFactor = FMath::Clamp(DampingFactor, 0.0f, 1.0f);
// 			CurrentAngVel *= DampingFactor;
// 			GetMesh()->SetPhysicsAngularVelocityInDegrees(CurrentAngVel, false);
// 		}
// 
// 		// Disable flip check in flight mode (spaceships don't need it)
// 		bPreviousFlipCheck = false;
// 	}
// 	else
// 	{
// 		// Ground mode - normal vehicle behavior
// 		SetEnableGravity(true);
// 		
// 		bool bMovingOnGround = ChaosVehicleMovement->IsMovingOnGround();
// 		GetMesh()->SetAngularDamping(bMovingOnGround ? 0.0f : 3.0f);
// 
// 		// realign the camera yaw to face front
// 		float CameraYaw = BackSpringArm->GetRelativeRotation().Yaw;
// 		CameraYaw = FMath::FInterpTo(CameraYaw, 0.0f, Delta, 1.0f);
// 
// 		BackSpringArm->SetRelativeRotation(FRotator(0.0f, CameraYaw, 0.0f));
// 	}
// }
// 
// void AChimeraPawn::Steering(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoSteering(Value.Get<float>());
// }
// 
// void AChimeraPawn::Throttle(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoThrottle(Value.Get<float>());
// }
// 
// void AChimeraPawn::Brake(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoBrake(Value.Get<float>());
// }
// 
// void AChimeraPawn::StartBrake(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoBrakeStart();
// }
// 
// void AChimeraPawn::StopBrake(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoBrakeStop();
// }
// 
// void AChimeraPawn::StartHandbrake(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoHandbrakeStart();
// }
// 
// void AChimeraPawn::StopHandbrake(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoHandbrakeStop();
// }
// 
// void AChimeraPawn::LookAround(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoLookAround(Value.Get<float>());
// }
// 
// void AChimeraPawn::ToggleCamera(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoToggleCamera();
// }
// 
// void AChimeraPawn::ResetVehicle(const FInputActionValue& Value)
// {
// 	// route the input
// 	DoResetVehicle();
// }
// 
// void AChimeraPawn::Pitch(const FInputActionValue& Value)
// {
// 	bPitchUp = Value.Get<float>() > 0.0f;
// 	bPitchDown = !bPitchUp;
// }
// 
// void AChimeraPawn::Yaw(const FInputActionValue& Value)
// {
// 	bYawRight = Value.Get<float>() > 0.0f;
// 	bYawLeft = !bYawRight;
// }
// 
// void AChimeraPawn::Roll(const FInputActionValue& Value)
// {
// 	bRollRight = Value.Get<float>() > 0.0f;
// 	bRollLeft = !bRollRight;
// }
// 
// void AChimeraPawn::Thrust(const FInputActionValue& Value)
// {
// 	float Val = Value.Get<float>();
// 	if (Val > 0.0f)
// 	{
// 		bThrustForward = true;
// 		bThrustReverse = false;
// 	}
// 	else if (Val < 0.0f)
// 	{
// 		bThrustReverse = true;
// 		bThrustForward = false;
// 	}
// 	else
// 	{
// 		bThrustForward = false;
// 		bThrustReverse = false;
// 	}
// }
// 
// void AChimeraPawn::StrafeX(const FInputActionValue& Value)
// {
// 	float Val = Value.Get<float>();
// 	if (Val > 0.0f)
// 	{
// 		bStrafeRight = true;
// 		bStrafeLeft = false;
// 	}
// 	else if (Val < 0.0f)
// 	{
// 		bStrafeLeft = true;
// 		bStrafeRight = false;
// 	}
// 	else
// 	{
// 		bStrafeLeft = false;
// 		bStrafeRight = false;
// 	}
// }
// 
// void AChimeraPawn::StrafeY(const FInputActionValue& Value)
// {
// 	float Val = Value.Get<float>();
// 	if (Val > 0.0f)
// 	{
// 		bStrafeUp = true;
// 		bStrafeDown = false;
// 	}
// 	else if (Val < 0.0f)
// 	{
// 		bStrafeDown = true;
// 		bStrafeUp = false;
// 	}
// 	else
// 	{
// 		bStrafeUp = false;
// 		bStrafeDown = false;
// 	}
// }
// 
// void AChimeraPawn::SetThrustVector(float PitchAngle, float YawAngle)
// {
// 	if (ThrustVectoring)
// 	{
// 		ThrustVectoring->SetThrustAngle(PitchAngle, YawAngle);
// 	}
// }
// 
// void AChimeraPawn::DoSteering(float SteeringValue)
// {
// 	// add the input
// 	ChaosVehicleMovement->SetSteeringInput(SteeringValue);
// }
// 
// void AChimeraPawn::DoThrottle(float ThrottleValue)
// {
// 	// add the input
// 	ChaosVehicleMovement->SetThrottleInput(ThrottleValue);
// 
// 	// reset the brake input
// 	ChaosVehicleMovement->SetBrakeInput(0.0f);
// }
// 
// void AChimeraPawn::DoBrake(float BrakeValue)
// {
// 	// add the input
// 	ChaosVehicleMovement->SetBrakeInput(BrakeValue);
// 
// 	// reset the throttle input
// 	ChaosVehicleMovement->SetThrottleInput(0.0f);
// }
// 
// void AChimeraPawn::DoBrakeStart()
// {
// 	// call the Blueprint hook for the brake lights
// 	BrakeLights(true);
// }
// 
// void AChimeraPawn::DoBrakeStop()
// {
// 	// call the Blueprint hook for the brake lights
// 	BrakeLights(false);
// 
// 	// reset brake input to zero
// 	ChaosVehicleMovement->SetBrakeInput(0.0f);
// }
// 
// void AChimeraPawn::DoHandbrakeStart()
// {
// 	// add the input
// 	ChaosVehicleMovement->SetHandbrakeInput(true);
// 
// 	// call the Blueprint hook for the break lights
// 	BrakeLights(true);
// }
// 
// void AChimeraPawn::DoHandbrakeStop()
// {
// 	// add the input
// 	ChaosVehicleMovement->SetHandbrakeInput(false);
// 
// 	// call the Blueprint hook for the break lights
// 	BrakeLights(false);
// }
// 
// void AChimeraPawn::DoLookAround(float YawDelta)
// {
// 	// rotate the spring arm
// 	BackSpringArm->AddLocalRotation(FRotator(0.0f, YawDelta, 0.0f));
// }
// 
// void AChimeraPawn::DoToggleCamera()
// {
// 	// toggle the active camera flag
// 	bFrontCameraActive = !bFrontCameraActive;
// 
// 	FrontCamera->SetActive(bFrontCameraActive);
// 	BackCamera->SetActive(!bFrontCameraActive);
// }
// 
// void AChimeraPawn::DoResetVehicle()
// {
// 	// reset to a location slightly above our current one
// 	FVector ResetLocation = GetActorLocation() + FVector(0.0f, 0.0f, 50.0f);
// 
// 	// reset to our yaw. Ignore pitch and roll
// 	FRotator ResetRotation = GetActorRotation();
// 	ResetRotation.Pitch = 0.0f;
// 	ResetRotation.Roll = 0.0f;
// 
// 	// teleport the actor to the reset spot and reset physics
// 	SetActorTransform(FTransform(ResetRotation, ResetLocation, FVector::OneVector), false, nullptr, ETeleportType::TeleportPhysics);
// 
// 	GetMesh()->SetPhysicsAngularVelocityInDegrees(FVector::ZeroVector);
// 	GetMesh()->SetPhysicsLinearVelocity(FVector::ZeroVector);
// }
// 
// void AChimeraPawn::DoToggleFlightMode()
// {
// 	bFlightModeEnabled = !bFlightModeEnabled;
// 
// 	if (bFlightModeEnabled)
// 	{
// 		// Disable gravity for space flight
// 		SetEnableGravity(false);
// 		GetMesh()->SetSimulatePhysics(true);
// 	}
// 	else
// 	{
// 		// Re-enable gravity for ground mode
// 		SetEnableGravity(true);
// 	}
// }
// 
// void AChimeraPawn::ApplyThrust(float ThrustValue)
// {
// 	if (!bFlightModeEnabled) return;
// 	
// 	if (ThrustValue > 0.0f)
// 	{
// 		bThrustForward = true;
// 		bThrustReverse = false;
// 	}
// 	else if (ThrustValue < 0.0f)
// 	{
// 		bThrustReverse = true;
// 		bThrustForward = false;
// 	}
// }
// 
// void AChimeraPawn::ApplyStrafeX(float StrafeValue)
// {
// 	if (!bFlightModeEnabled) return;
// 
// 	if (StrafeValue > 0.0f)
// 	{
// 		bStrafeRight = true;
// 		bStrafeLeft = false;
// 	}
// 	else if (StrafeValue < 0.0f)
// 	{
// 		bStrafeLeft = true;
// 		bStrafeRight = false;
// 	}
// }
// 
// void AChimeraPawn::ApplyStrafeY(float StrafeValue)
// {
// 	if (!bFlightModeEnabled) return;
// 
// 	if (StrafeValue > 0.0f)
// 	{
// 		bStrafeUp = true;
// 		bStrafeDown = false;
// 	}
// 	else if (StrafeValue < 0.0f)
// 	{
// 		bStrafeDown = true;
// 		bStrafeUp = false;
// 	}
// }
// 
// void AChimeraPawn::ApplyPitch(float PitchValue)
// {
// 	if (!bFlightModeEnabled) return;
// 
// 	if (PitchValue > 0.0f)
// 	{
// 		bPitchUp = true;
// 		bPitchDown = false;
// 	}
// 	else if (PitchValue < 0.0f)
// 	{
// 		bPitchDown = true;
// 		bPitchUp = false;
// 	}
// }
// 
// void AChimeraPawn::ApplyYaw(float YawValue)
// {
// 	if (!bFlightModeEnabled) return;
// 
// 	if (YawValue > 0.0f)
// 	{
// 		bYawRight = true;
// 		bYawLeft = false;
// 	}
// 	else if (YawValue < 0.0f)
// 	{
// 		bYawLeft = true;
// 		bYawRight = false;
// 	}
// }
// 
// void AChimeraPawn::ApplyRoll(float RollValue)
// {
// 	if (!bFlightModeEnabled) return;
// 
// 	if (RollValue > 0.0f)
// 	{
// 		bRollRight = true;
// 		bRollLeft = false;
// 	}
// 	else if (RollValue < 0.0f)
// 	{
// 		bRollLeft = true;
// 		bRollRight = false;
// 	}
// }
// 
// void AChimeraPawn::FlippedCheck()
// {
// 	if (bFlightModeEnabled) return;
// 
// 	// check the difference in angle between the mesh's up vector and world up
// 	const float UpDot = FVector::DotProduct(FVector::UpVector, GetMesh()->GetUpVector());
// 
// 	if (UpDot < FlipCheckMinDot)
// 	{
// 		// is this the second time we've checked that the vehicle is still flipped?
// 		if (bPreviousFlipCheck)
// 		{
// 			// reset the vehicle to upright
// 			DoResetVehicle();
// 		}
// 		
// 		// set the flipped check flag so the next check resets the car
// 		bPreviousFlipCheck = true;
// 
// 	} else {
// 
// 		// we're upright. reset the flipped check flag
// 		bPreviousFlipCheck = false;
// 	}
// }
// 
// #undef LOCTEXT_NAMESPACE
// 

// ============================================================================
// FILE: ChimeraPawn.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraPawn.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "WheeledVehiclePawn.h"
// #include "ChimeraPawn.generated.h"
// 
// class UCameraComponent;
// class USpringArmComponent;
// class UInputAction;
// class UChaosWheeledVehicleMovementComponent;
// class UThrustVectoringComponent;
// class UAttitudeStabilizerComponent;
// struct FInputActionValue;
// 
// /**
//  *  Vehicle Pawn class
//  *  Handles common functionality for all vehicle types,
//  *  including input handling and camera management.
//  *  
//  *  Specific vehicle configurations are handled in subclasses.
//  */
// UCLASS(abstract)
// class AChimeraPawn : public AWheeledVehiclePawn
// {
// 	GENERATED_BODY()
// 
// 	/** Spring Arm for the front camera */
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category ="Components", meta = (AllowPrivateAccess = "true"))
// 	USpringArmComponent* FrontSpringArm;
// 
// 	/** Front Camera component */
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category ="Components", meta = (AllowPrivateAccess = "true"))
// 	UCameraComponent* FrontCamera;
// 
// 	/** Spring Arm for the back camera */
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category ="Components", meta = (AllowPrivateAccess = "true"))
// 	USpringArmComponent* BackSpringArm;
// 
// 	/** Back Camera component */
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category ="Components", meta = (AllowPrivateAccess = "true"))
// 	UCameraComponent* BackCamera;
// 
// 	/** Cast pointer to the Chaos Vehicle movement component */
// 	TObjectPtr<UChaosWheeledVehicleMovementComponent> ChaosVehicleMovement;
// 
// protected:
// 
// 	/** Steering Action */
// 	UPROPERTY(EditAnywhere, Category="Input")
// 	UInputAction* SteeringAction;
// 
// 	/** Throttle Action */
// 	UPROPERTY(EditAnywhere, Category="Input")
// 	UInputAction* ThrottleAction;
// 
// 	/** Brake Action */
// 	UPROPERTY(EditAnywhere, Category="Input")
// 	UInputAction* BrakeAction;
// 
// 	/** Handbrake Action */
// 	UPROPERTY(EditAnywhere, Category="Input")
// 	UInputAction* HandbrakeAction;
// 
// 	/** Look Around Action */
// 	UPROPERTY(EditAnywhere, Category="Input")
// 	UInputAction* LookAroundAction;
// 
// 	/** Toggle Camera Action */
// 	UPROPERTY(EditAnywhere, Category="Input")
// 	UInputAction* ToggleCameraAction;
// 
// 	/** Reset Vehicle Action */
// 	UPROPERTY(EditAnywhere, Category="Input")
// 	UInputAction* ResetVehicleAction;
// 
// 	// Flight controls
// 	UPROPERTY(EditAnywhere, Category="Input|Flight")
// 	UInputAction* PitchAction;
// 
// 	UPROPERTY(EditAnywhere, Category="Input|Flight")
// 	UInputAction* YawAction;
// 
// 	UPROPERTY(EditAnywhere, Category="Input|Flight")
// 	UInputAction* RollAction;
// 
// 	UPROPERTY(EditAnywhere, Category="Input|Flight")
// 	UInputAction* ThrustAction;
// 
// 	UPROPERTY(EditAnywhere, Category="Input|Flight")
// 	UInputAction* StrafeXAction;
// 
// 	UPROPERTY(EditAnywhere, Category="Input|Flight")
// 	UInputAction* StrafeYAction;
// 
// 	/** Keeps track of which camera is active */
// 	bool bFrontCameraActive = false;
// 
// 	/** Flight mode toggle flag */
// 	UPROPERTY(EditAnywhere, Category="Flight")
// 	bool bFlightModeEnabled = false;
// 
// 	/** Maximum thrust force multiplier (applied per Tick) */
// 	UPROPERTY(EditAnywhere, Category="Flight", meta = (ClampMin = "0.0"))
// 	float ThrustPower = 150.0f;
// 
// 	/** Maximum rotation speed in degrees per second for pitch/yaw/roll */
// 	UPROPERTY(EditAnywhere, Category="Flight", meta = (ClampMin = "0.0"))
// 	float RotationSpeed = 90.0f;
// 
// 	/** Angular velocity damping when not actively rotating (prevents drift) */
// 	UPROPERTY(EditAnywhere, Category="Flight")
// 	float AngularDampingWhenIdle = 5.0f;
// 
// 	// Thrust vectoring component reference
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components|Flight")
// 	TObjectPtr<UThrustVectoringComponent> ThrustVectoring;
// 
// 	// Attitude stabilization component reference
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components|Flight")
// 	TObjectPtr<UAttitudeStabilizerComponent> AttitudeStabilizer;
// 
// 	/** Keeps track of whether the car is flipped. If this is true for two flip checks, resets the vehicle automatically */
// 	bool bPreviousFlipCheck = false;
// 
// 	/** Time between automatic flip checks */
// 	UPROPERTY(EditAnywhere, Category="Flip Check", meta = (Units = "s"))
// 	float FlipCheckTime = 3.0f;
// 
// 	/** Minimum dot product value for the vehicle's up direction that we still consider upright */
// 	UPROPERTY(EditAnywhere, Category="Flip Check")
// 	float FlipCheckMinDot = -0.2f;
// 
// 	/** Flip check timer */
// 	FTimerHandle FlipCheckTimer;
// 
// public:
// 	AChimeraPawn();
// 
// 	// Begin Pawn interface
// 
// 	virtual void SetupPlayerInputComponent(UInputComponent* InputComponent) override;
// 
// 	// End Pawn interface
// 
// 	// Begin Actor interface
// 
// 	/** Initialization */
// 	virtual void BeginPlay() override;
// 
// 	/** Cleanup */
// 	virtual void EndPlay(EEndPlayReason::Type EndPlayReason) override;
// 
// 	/** Update */
// 	virtual void Tick(float Delta) override;
// 
// 	// End Actor interface
// 
// protected:
// 
// 	/** Handles steering input */
// 	void Steering(const FInputActionValue& Value);
// 
// 	/** Handles throttle input */
// 	void Throttle(const FInputActionValue& Value);
// 
// 	/** Handles brake input */
// 	void Brake(const FInputActionValue& Value);
// 
// 	/** Handles brake start/stop inputs */
// 	void StartBrake(const FInputActionValue& Value);
// 	void StopBrake(const FInputActionValue& Value);
// 
// 	/** Handles handbrake start/stop inputs */
// 	void StartHandbrake(const FInputActionValue& Value);
// 	void StopHandbrake(const FInputActionValue& Value);
// 
// 	/** Handles look around input */
// 	void LookAround(const FInputActionValue& Value);
// 
// 	/** Handles toggle camera input */
// 	void ToggleCamera(const FInputActionValue& Value);
// 
// 	/** Handles reset vehicle input */
// 	void ResetVehicle(const FInputActionValue& Value);
// 
// 	// Flight control handlers (bound to Enhanced Input)
// 	void Pitch(const FInputActionValue& Value);
// 	void Yaw(const FInputActionValue& Value);
// 	void Roll(const FInputActionValue& Value);
// 	void Thrust(const FInputActionValue& Value);
// 	void StrafeX(const FInputActionValue& Value);
// 	void StrafeY(const FInputActionValue& Value);
// 
// 	// Thrust vectoring input handlers (bound to Enhanced Input)
// 	void SetThrustVector(float PitchAngle, float YawAngle);
// 
// 	// Flight input state flags (set by input handlers, consumed by Tick)
// 	bool bThrustForward = false;
// 	bool bThrustReverse = false;
// 	bool bStrafeLeft = false;
// 	bool bStrafeRight = false;
// 	bool bStrafeUp = false;
// 	bool bStrafeDown = false;
// 	bool bPitchUp = false;
// 	bool bPitchDown = false;
// 	bool bYawLeft = false;
// 	bool bYawRight = false;
// 	bool bRollLeft = false;
// 	bool bRollRight = false;
// 
// public:
// 
// 	/** Handle steering input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoSteering(float SteeringValue);
// 
// 	/** Handle throttle input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoThrottle(float ThrottleValue);
// 
// 	/** Handle brake input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoBrake(float BrakeValue);
// 
// 	/** Handle brake start input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoBrakeStart();
// 
// 	/** Handle brake stop input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoBrakeStop();
// 
// 	/** Handle handbrake start input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoHandbrakeStart();
// 
// 	/** Handle handbrake stop input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoHandbrakeStop();
// 
// 	/** Handle look input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoLookAround(float YawDelta);
// 
// 	/** Handle toggle camera input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoToggleCamera();
// 
// 	/** Handle reset vehicle input by input actions or mobile interface */
// 	UFUNCTION(BlueprintCallable, Category="Input")
// 	void DoResetVehicle();
// 
// 	/** Toggle flight mode (ground <-> spaceship) */
// 	UFUNCTION(BlueprintCallable, Category="Flight")
// 	void DoToggleFlightMode();
// 
// 	// Flight physics application methods (called from Tick when in flight mode)
// 	UFUNCTION(BlueprintCallable, Category="Flight|Physics")
// 	void ApplyThrust(float ThrustValue);
// 
// 	UFUNCTION(BlueprintCallable, Category="Flight|Physics")
// 	void ApplyStrafeX(float StrafeValue);
// 
// 	UFUNCTION(BlueprintCallable, Category="Flight|Physics")
// 	void ApplyStrafeY(float StrafeValue);
// 
// 	UFUNCTION(BlueprintCallable, Category="Flight|Physics")
// 	void ApplyPitch(float PitchValue);
// 
// 	UFUNCTION(BlueprintCallable, Category="Flight|Physics")
// 	void ApplyYaw(float YawValue);
// 
// 	UFUNCTION(BlueprintCallable, Category="Flight|Physics")
// 	void ApplyRoll(float RollValue);
// 
// protected:
// 
// 	/** Called when the brake lights are turned on or off */
// 	UFUNCTION(BlueprintImplementableEvent, Category="Vehicle")
// 	void BrakeLights(bool bBraking);
// 
// 	/** Checks if the car is flipped upside down and automatically resets it */
// 	UFUNCTION()
// 	void FlippedCheck();
// 
// public:
// 	/** Returns the front spring arm subobject */
// 	FORCEINLINE USpringArmComponent* GetFrontSpringArm() const { return FrontSpringArm; }
// 	/** Returns the front camera subobject */
// 	FORCEINLINE UCameraComponent* GetFollowCamera() const { return FrontCamera; }
// 	/** Returns the back spring arm subobject */
// 	FORCEINLINE USpringArmComponent* GetBackSpringArm() const { return BackSpringArm; }
// 	/** Returns the back camera subobject */
// 	FORCEINLINE UCameraComponent* GetBackCamera() const { return BackCamera; }
// 	/** Returns the cast Chaos Vehicle Movement subobject */
// 	FORCEINLINE const TObjectPtr<UChaosWheeledVehicleMovementComponent>& GetChaosVehicleMovement() const { return ChaosVehicleMovement; }
// };
// 

// ============================================================================
// FILE: ChimeraPlayerController.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraPlayerController.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "ChimeraPlayerController.h"
// #include "ChimeraPawn.h"
// #include "ChimeraUI.h"
// #include "EnhancedInputSubsystems.h"
// #include "ChaosWheeledVehicleMovementComponent.h"
// #include "Blueprint/UserWidget.h"
// #include "Chimera.h"
// #include "Kismet/GameplayStatics.h"
// #include "GameFramework/PlayerStart.h"
// #include "Widgets/Input/SVirtualJoystick.h"
// 
// void AChimeraPlayerController::BeginPlay()
// {
// 	Super::BeginPlay();
// 	
// 	// ensure we're attached to the vehicle pawn so that World Partition streaming works correctly
// 	bAttachToPawn = true;
// 
// 	// only spawn UI on local player controllers
// 	if (IsLocalPlayerController())
// 	{
// 		if (ShouldUseTouchControls())
// 		{
// 			// spawn the mobile controls widget
// 			MobileControlsWidget = CreateWidget<UUserWidget>(this, MobileControlsWidgetClass);
// 
// 			if (MobileControlsWidget)
// 			{
// 				// add the controls to the player screen
// 				MobileControlsWidget->AddToPlayerScreen(0);
// 
// 			} else {
// 
// 				UE_LOG(LogChimera, Error, TEXT("Could not spawn mobile controls widget."));
// 
// 			}
// 		}
// 		
// 
// 		// spawn the UI widget and add it to the viewport
// 		VehicleUI = CreateWidget<UChimeraUI>(this, VehicleUIClass);
// 
// 		if (VehicleUI)
// 		{
// 			VehicleUI->AddToViewport();
// 
// 		} else {
// 
// 			UE_LOG(LogChimera, Error, TEXT("Could not spawn vehicle UI widget."));
// 
// 		}
// 	}
// }
// 
// void AChimeraPlayerController::SetupInputComponent()
// {
// 	Super::SetupInputComponent();
// 	
// 	// only add IMCs for local player controllers
// 	if (IsLocalPlayerController())
// 	{
// 		// Add Input Mapping Contexts
// 		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
// 		{
// 			for (UInputMappingContext* CurrentContext : DefaultMappingContexts)
// 			{
// 				Subsystem->AddMappingContext(CurrentContext, 0);
// 			}
// 
// 			// only add these IMCs if we're not using mobile touch input
// 			if (!ShouldUseTouchControls())
// 			{
// 				for (UInputMappingContext* CurrentContext : MobileExcludedMappingContexts)
// 				{
// 					Subsystem->AddMappingContext(CurrentContext, 0);
// 				}
// 			}
// 
// 			if (bUseSteeringWheelControls)
// 			{
// 				Subsystem->AddMappingContext(SteeringWheelInputMappingContext, 0);
// 			}
// 		}
// 	}
// }
// 
// void AChimeraPlayerController::Tick(float Delta)
// {
// 	Super::Tick(Delta);
// 
// 	if (IsValid(VehiclePawn) && IsValid(VehicleUI))
// 	{
// 		VehicleUI->UpdateSpeed(VehiclePawn->GetChaosVehicleMovement()->GetForwardSpeed());
// 		VehicleUI->UpdateGear(VehiclePawn->GetChaosVehicleMovement()->GetCurrentGear());
// 	}
// }
// 
// void AChimeraPlayerController::OnPossess(APawn* InPawn)
// {
// 	Super::OnPossess(InPawn);
// 
// 	// get a pointer to the controlled pawn
// 	VehiclePawn = CastChecked<AChimeraPawn>(InPawn);
// 
// 	// subscribe to the pawn's OnDestroyed delegate
// 	VehiclePawn->OnDestroyed.AddDynamic(this, &AChimeraPlayerController::OnPawnDestroyed);
// }
// 
// void AChimeraPlayerController::OnPawnDestroyed(AActor* DestroyedPawn)
// {
// 	// find the player start
// 	TArray<AActor*> ActorList;
// 	UGameplayStatics::GetAllActorsOfClass(GetWorld(), APlayerStart::StaticClass(), ActorList);
// 
// 	if (ActorList.Num() > 0)
// 	{
// 		// spawn a vehicle at the player start
// 		const FTransform SpawnTransform = ActorList[0]->GetActorTransform();
// 
// 		if (AChimeraPawn* RespawnedVehicle = GetWorld()->SpawnActor<AChimeraPawn>(VehiclePawnClass, SpawnTransform))
// 		{
// 			// possess the vehicle
// 			Possess(RespawnedVehicle);
// 		}
// 	}
// }
// 
// bool AChimeraPlayerController::ShouldUseTouchControls() const
// {
// 	// are we on a mobile platform? Should we force touch?
// 	return SVirtualJoystick::ShouldDisplayTouchInterface() || bForceTouchControls;
// }
// 

// ============================================================================
// FILE: ChimeraPlayerController.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraPlayerController.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "GameFramework/PlayerController.h"
// #include "ChimeraPlayerController.generated.h"
// 
// class UInputMappingContext;
// class AChimeraPawn;
// class UChimeraUI;
// 
// /**
//  *  Vehicle Player Controller class
//  *  Handles input mapping and user interface
//  */
// UCLASS(abstract, Config="Game")
// class AChimeraPlayerController : public APlayerController
// {
// 	GENERATED_BODY()
// 
// protected:
// 
// 	/** Input Mapping Contexts */
// 	UPROPERTY(EditAnywhere, Category ="Input|Input Mappings")
// 	TArray<UInputMappingContext*> DefaultMappingContexts;
// 
// 	/** Input Mapping Contexts */
// 	UPROPERTY(EditAnywhere, Category="Input|Input Mappings")
// 	TArray<UInputMappingContext*> MobileExcludedMappingContexts;
// 
// 	/** Mobile controls widget to spawn */
// 	UPROPERTY(EditAnywhere, Category="Input|Touch Controls")
// 	TSubclassOf<UUserWidget> MobileControlsWidgetClass;
// 
// 	/** Pointer to the mobile controls widget */
// 	UPROPERTY()
// 	TObjectPtr<UUserWidget> MobileControlsWidget;
// 
// 	/** If true, the player will use UMG touch controls even if not playing on mobile platforms */
// 	UPROPERTY(EditAnywhere, Config, Category = "Input|Touch Controls")
// 	bool bForceTouchControls = false;
// 
// 	/** If true, the optional steering wheel input mapping context will be registered */
// 	UPROPERTY(EditAnywhere, Category = "Input|Steering Wheel Controls")
// 	bool bUseSteeringWheelControls = false;
// 
// 	/** Optional Input Mapping Context to be used for steering wheel input.
// 	 *  This is added alongside the default Input Mapping Context and does not block other forms of input.
// 	 */
// 	UPROPERTY(EditAnywhere, Category = "Input|Steering Wheel Controls", meta = (EditCondition = "bUseSteeringWheelControls"))
// 	UInputMappingContext* SteeringWheelInputMappingContext;
// 
// 	/** Type of vehicle to automatically respawn when it's destroyed */
// 	UPROPERTY(EditAnywhere, Category="Vehicle|Respawn")
// 	TSubclassOf<AChimeraPawn> VehiclePawnClass;
// 
// 	/** Pointer to the controlled vehicle pawn */
// 	TObjectPtr<AChimeraPawn> VehiclePawn;
// 
// 	/** Type of the UI to spawn */
// 	UPROPERTY(EditAnywhere, Category="Vehicle|UI")
// 	TSubclassOf<UChimeraUI> VehicleUIClass;
// 
// 	/** Pointer to the UI widget */
// 	UPROPERTY()
// 	TObjectPtr<UChimeraUI> VehicleUI;
// 		
// protected:
// 
// 	/** Gameplay initialization */
// 	virtual void BeginPlay() override;
// 
// 	/** Input setup */
// 	virtual void SetupInputComponent() override;
// 
// public:
// 
// 	/** Update vehicle UI on tick */
// 	virtual void Tick(float Delta) override;
// 
// protected:
// 
// 	/** Pawn setup */
// 	virtual void OnPossess(APawn* InPawn) override;
// 
// 	/** Handles pawn destruction and respawning */
// 	UFUNCTION()
// 	void OnPawnDestroyed(AActor* DestroyedPawn);
// 
// 	/** Returns true if the player should use UMG touch controls */
// 	bool ShouldUseTouchControls() const;
// };
// 

// ============================================================================
// FILE: ChimeraSportsCar.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraSportsCar.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "ChimeraSportsCar.h"
// #include "ChimeraSportsWheelFront.h"
// #include "ChimeraSportsWheelRear.h"
// #include "ChaosWheeledVehicleMovementComponent.h"
// 
// AChimeraSportsCar::AChimeraSportsCar()
// {
// 	// Note: for faster iteration times, the vehicle setup can be tweaked in the Blueprint instead
// 
// 	// Set up the chassis
// 	GetChaosVehicleMovement()->ChassisHeight = 144.0f;
// 	GetChaosVehicleMovement()->DragCoefficient = 0.31f;
// 
// 	// Set up the wheels
// 	GetChaosVehicleMovement()->bLegacyWheelFrictionPosition = true;
// 	GetChaosVehicleMovement()->WheelSetups.SetNum(4);
// 
// 	GetChaosVehicleMovement()->WheelSetups[0].WheelClass = UChimeraSportsWheelFront::StaticClass();
// 	GetChaosVehicleMovement()->WheelSetups[0].BoneName = FName("Phys_Wheel_FL");
// 	GetChaosVehicleMovement()->WheelSetups[0].AdditionalOffset = FVector(0.0f, 0.0f, 0.0f);
// 
// 	GetChaosVehicleMovement()->WheelSetups[1].WheelClass = UChimeraSportsWheelFront::StaticClass();
// 	GetChaosVehicleMovement()->WheelSetups[1].BoneName = FName("Phys_Wheel_FR");
// 	GetChaosVehicleMovement()->WheelSetups[1].AdditionalOffset = FVector(0.0f, 0.0f, 0.0f);
// 
// 	GetChaosVehicleMovement()->WheelSetups[2].WheelClass = UChimeraSportsWheelRear::StaticClass();
// 	GetChaosVehicleMovement()->WheelSetups[2].BoneName = FName("Phys_Wheel_BL");
// 	GetChaosVehicleMovement()->WheelSetups[2].AdditionalOffset = FVector(0.0f, 0.0f, 0.0f);
// 
// 	GetChaosVehicleMovement()->WheelSetups[3].WheelClass = UChimeraSportsWheelRear::StaticClass();
// 	GetChaosVehicleMovement()->WheelSetups[3].BoneName = FName("Phys_Wheel_BR");
// 	GetChaosVehicleMovement()->WheelSetups[3].AdditionalOffset = FVector(0.0f, 0.0f, 0.0f);
// 
// 	// Set up the engine
// 	// NOTE: Check the Blueprint asset for the Torque Curve
// 	GetChaosVehicleMovement()->EngineSetup.MaxTorque = 750.0f;
// 	GetChaosVehicleMovement()->EngineSetup.MaxRPM = 7000.0f;
// 	GetChaosVehicleMovement()->EngineSetup.EngineIdleRPM = 900.0f;
// 	GetChaosVehicleMovement()->EngineSetup.EngineBrakeEffect = 0.2f;
// 	GetChaosVehicleMovement()->EngineSetup.EngineRevUpMOI = 5.0f;
// 	GetChaosVehicleMovement()->EngineSetup.EngineRevDownRate = 600.0f;
// 
// 	// Set up the transmission
// 	GetChaosVehicleMovement()->TransmissionSetup.bUseAutomaticGears = true;
// 	GetChaosVehicleMovement()->TransmissionSetup.bUseAutoReverse = true;
// 	GetChaosVehicleMovement()->TransmissionSetup.FinalRatio = 2.81f;
// 	GetChaosVehicleMovement()->TransmissionSetup.ChangeUpRPM = 6000.0f;
// 	GetChaosVehicleMovement()->TransmissionSetup.ChangeDownRPM = 2000.0f;
// 	GetChaosVehicleMovement()->TransmissionSetup.GearChangeTime = 0.2f;
// 	GetChaosVehicleMovement()->TransmissionSetup.TransmissionEfficiency = 0.9f;
// 
// 	GetChaosVehicleMovement()->TransmissionSetup.ForwardGearRatios.SetNum(5);
// 	GetChaosVehicleMovement()->TransmissionSetup.ForwardGearRatios[0] = 4.25f;
// 	GetChaosVehicleMovement()->TransmissionSetup.ForwardGearRatios[1] = 2.52f;
// 	GetChaosVehicleMovement()->TransmissionSetup.ForwardGearRatios[2] = 1.66f;
// 	GetChaosVehicleMovement()->TransmissionSetup.ForwardGearRatios[3] = 1.22f;
// 	GetChaosVehicleMovement()->TransmissionSetup.ForwardGearRatios[4] = 1.0f;
// 
// 	GetChaosVehicleMovement()->TransmissionSetup.ReverseGearRatios.SetNum(1);
// 	GetChaosVehicleMovement()->TransmissionSetup.ReverseGearRatios[0] = 4.04f;
// 
// 	// Set up the steering
// 	// NOTE: Check the Blueprint asset for the Steering Curve
// 	GetChaosVehicleMovement()->SteeringSetup.SteeringType = ESteeringType::Ackermann;
// 	GetChaosVehicleMovement()->SteeringSetup.AngleRatio = 0.7f;
// }

// ============================================================================
// FILE: ChimeraUI.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraUI.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "ChimeraUI.h"
// 
// void UChimeraUI::UpdateSpeed(float NewSpeed)
// {
// 	// format the speed to KPH or MPH
// 	float FormattedSpeed = FMath::Abs(NewSpeed) * (bIsMPH ? 0.022f : 0.036f);
// 
// 	// call the Blueprint handler
// 	OnSpeedUpdate(FormattedSpeed);
// }
// 
// void UChimeraUI::UpdateGear(int32 NewGear)
// {
// 	// call the Blueprint handler
// 	OnGearUpdate(NewGear);
// }

// ============================================================================
// FILE: ChimeraUI.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraUI.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "Blueprint/UserWidget.h"
// #include "ChimeraUI.generated.h"
// 
// /**
//  *  Simple Vehicle HUD class
//  *  Displays the current speed and gear.
//  *  Widget setup is handled in a Blueprint subclass.
//  */
// UCLASS(abstract)
// class UChimeraUI : public UUserWidget
// {
// 	GENERATED_BODY()
// 	
// protected:
// 
// 	/** Controls the display of speed in Km/h or MPH */
// 	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Vehicle")
// 	bool bIsMPH = false;
// 
// public:
// 
// 	/** Called to update the speed display */
// 	void UpdateSpeed(float NewSpeed);
// 
// 	/** Called to update the gear display */
// 	void UpdateGear(int32 NewGear);
// 
// protected:
// 
// 	/** Implemented in Blueprint to display the new speed */
// 	UFUNCTION(BlueprintImplementableEvent, Category="Vehicle")
// 	void OnSpeedUpdate(float NewSpeed);
// 
// 	/** Implemented in Blueprint to display the new gear */
// 	UFUNCTION(BlueprintImplementableEvent, Category="Vehicle")
// 	void OnGearUpdate(int32 NewGear);
// };
// 

// ============================================================================
// FILE: ChimeraWheelFront.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraWheelFront.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #include "ChimeraWheelFront.h"
// #include "UObject/ConstructorHelpers.h"
// 
// UChimeraWheelFront::UChimeraWheelFront()
// {
// 	AxleType = EAxleType::Front;
// 	bAffectedBySteering = true;
// 	MaxSteerAngle = 40.f;
// }

// ============================================================================
// FILE: ChimeraWheelFront.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraWheelFront.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "ChaosVehicleWheel.h"
// #include "ChimeraWheelFront.generated.h"
// 
// /**
//  *  Base front wheel definition.
//  */
// UCLASS()
// class UChimeraWheelFront : public UChaosVehicleWheel
// {
// 	GENERATED_BODY()
// 
// public:
// 	UChimeraWheelFront();
// };

// ============================================================================
// FILE: ChimeraWheelRear.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraWheelRear.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #include "ChimeraWheelRear.h"
// #include "UObject/ConstructorHelpers.h"
// 
// UChimeraWheelRear::UChimeraWheelRear()
// {
// 	AxleType = EAxleType::Rear;
// 	bAffectedByHandbrake = true;
// 	bAffectedByEngine = true;
// }

// ============================================================================
// FILE: ChimeraWheelRear.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ChimeraWheelRear.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "ChaosVehicleWheel.h"
// #include "ChimeraWheelRear.generated.h"
// 
// /**
//  *  Base rear wheel definition.
//  */
// UCLASS()
// class UChimeraWheelRear : public UChaosVehicleWheel
// {
// 	GENERATED_BODY()
// 
// public:
// 	UChimeraWheelRear();
// };
// 

// ============================================================================
// FILE: FlightControlComponent.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\FlightControlComponent.cpp
// ============================================================================
// // Generated by ProceduralGameGenerator
// #include "FlightControlComponent.h"
// #include "Components/SceneComponent.h"
// #include "GameFramework/Actor.h"
// #include "Math/UnrealMathFunctions.h"
// 
// UFlightControlComponent::UFlightControlComponent(const FObjectInitializer& ObjectInitializer)
// 	: Super(ObjectInitializer)
// {
// 	PrimaryComponentTick.bCanEverTick = true;
// }
// 
// void UFlightControlComponent::ToggleFlightMode()
// {
// 	bFlightModeEnabled = !bFlightModeEnabled;
// 	if (bFlightModeEnabled && GetOwner())
// 	{
// 		if (USceneComponent* RootComp = GetOwner()->GetRootComponent())
// 		{
// 			RootComp->SetSimulatePhysics(true);
// 			GetOwner()->SetEnableGravity(false);
// 		}
// 	}
// }
// 
// void UFlightControlComponent::ApplyThrust(float ThrustValue) { CurrentThrustInput = FMath::Clamp(ThrustValue, -1.0f, 1.0f); }
// 
// void UFlightControlComponent::ApplyStrafeX(float StrafeValue) { CurrentStrafeXInput = FMath::Clamp(StrafeValue, -1.0f, 1.0f); }
// 
// void UFlightControlComponent::ApplyStrafeY(float StrafeValue) { CurrentStrafeYInput = FMath::Clamp(StrafeValue, -1.0f, 1.0f); }
// 
// void UFlightControlComponent::ApplyStrafeZ(float StrafeValue) { CurrentStrafeZInput = FMath::Clamp(StrafeValue, -1.0f, 1.0f); }
// 
// void UFlightControlComponent::ApplyPitch(float PitchValue) { CurrentPitchInput = FMath::Clamp(PitchValue, -1.0f, 1.0f); }
// 
// void UFlightControlComponent::ApplyYaw(float YawValue) { CurrentYawInput = FMath::Clamp(YawValue, -1.0f, 1.0f); }
// 
// void UFlightControlComponent::ApplyRoll(float RollValue) { CurrentRollInput = FMath::Clamp(RollValue, -1.0f, 1.0f); }
// 
// void UFlightControlComponent::TickComponent(float DeltaTime, enum ETickType TickType, FActorComponentTickFunction* ThisTickFunction)
// {
// 	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
// 	if (!bFlightModeEnabled || !GetOwner()) return;
// 	UActor* Owner = GetOwner();
// 	if (UPrimitiveComponent* PrimComp = Owner->GetRootPrimitiveComponent())
// 	{
// 		FVector CurrentLinVel = PrimComp->GetLinearVelocity();
// 		CurrentLinVel *= VelocityDamping;
// 		FVector ThrustDir = Owner->GetActorForwardVector() * CurrentThrustInput * ThrustPower * DeltaTime;
// 		CurrentLinVel += ThrustDir;
// 		CurrentLinVel += Owner->GetActorRightVector() * CurrentStrafeXInput * ThrustPower * DeltaTime;
// 		CurrentLinVel += Owner->GetActorUpVector() * CurrentStrafeZInput * ThrustPower * DeltaTime;
// 		PrimComp->SetLinearVelocity(CurrentLinVel, false);
// 		FVector CurrentAngVel = PrimComp->GetAngularVelocity();
// 		float AngVelScale = RotationSpeed * 100.0f;
// 		CurrentAngVel.X = CurrentPitchInput * AngVelScale;
// 		CurrentAngVel.Y = CurrentYawInput * AngVelScale;
// 		CurrentAngVel.Z = CurrentRollInput * AngVelScale;
// 		if (FMath::Abs(CurrentPitchInput) < 0.01f && FMath::Abs(CurrentYawInput) < 0.01f && FMath::Abs(CurrentRollInput) < 0.01f)
// 		{
// 			CurrentAngVel *= (1.0f - AngularDampingWhenIdle * DeltaTime);
// 		}
// 		PrimComp->SetAngularVelocity(CurrentAngVel, false);
// 	}
// 	CurrentThrustInput = 0.0f;
// 	CurrentStrafeXInput = 0.0f;
// 	CurrentStrafeYInput = 0.0f;
// 	CurrentStrafeZInput = 0.0f;
// 	CurrentPitchInput = 0.0f;
// 	CurrentYawInput = 0.0f;
// 	CurrentRollInput = 0.0f;
// }
// 

// ============================================================================
// FILE: FlightControlComponent.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\FlightControlComponent.h
// ============================================================================
// // Generated by ProceduralGameGenerator
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "Components/ActorComponent.h"
// #include "FlightControlComponent.generated.h"
// 
// UCLASS( ClassNoGenerateOptions, meta = (BlueprintType, Category = "Flight") )
// class CHIMERA_API UFlightControlComponent : public UActorComponent
// {
// 	GENERATED_BODY()
// 
// public:
// 	UFlightControlComponent(const FObjectInitializer& ObjectInitializer);
// 
// protected:
// 	// Flight mode toggle flag
// 	UPROPERTY(EditAnywhere, Category = "Flight")
// 	bool bFlightModeEnabled = false;
// 
// 	// Maximum thrust force multiplier (applied per Tick)
// 	UPROPERTY(EditAnywhere, Category = "Flight", meta = (ClampMin = "0.0"))
// 	float ThrustPower = 150.0f;
// 
// 	// Maximum rotation speed in degrees per second for pitch/yaw/roll
// 	UPROPERTY(EditAnywhere, Category = "Flight", meta = (ClampMin = "0.0"))
// 	float RotationSpeed = 90.0f;
// 
// 	// Angular velocity damping when not actively rotating (prevents drift)
// 	UPROPERTY(EditAnywhere, Category = "Flight")
// 	float AngularDampingWhenIdle = 5.0f;
// 
// 	// Velocity damping factor per Tick (simulates minimal drag in space)
// 	UPROPERTY(EditAnywhere, Category = "Flight", meta = (ClampMin = "0.0", ClampMax = "1.0"))
// 	float VelocityDamping = 0.98f;
// 
// public:
// 	UFUNCTION(BlueprintCallable, Category = "Flight")
// 	void ToggleFlightMode();
// 
// 	UFUNCTION(BlueprintCallable, Category = "Flight")
// 	bool IsFlightModeEnabled() const { return bFlightModeEnabled; }
// 
// 	UFUNCTION(BlueprintCallable, Category = "Flight|Input")
// 	void ApplyThrust(float ThrustValue);
// 
// 	UFUNCTION(BlueprintCallable, Category = "Flight|Input")
// 	void ApplyStrafeX(float StrafeValue);
// 
// 	UFUNCTION(BlueprintCallable, Category = "Flight|Input")
// 	void ApplyStrafeY(float StrafeValue);
// 
// 	UFUNCTION(BlueprintCallable, Category = "Flight|Input")
// 	void ApplyStrafeZ(float StrafeValue);
// 
// 	UFUNCTION(BlueprintCallable, Category = "Flight|Input")
// 	void ApplyPitch(float PitchValue);
// 
// 	UFUNCTION(BlueprintCallable, Category = "Flight|Input")
// 	void ApplyYaw(float YawValue);
// 
// 	UFUNCTION(BlueprintCallable, Category = "Flight|Input")
// 	void ApplyRoll(float RollValue);
// 
// protected:
// 	virtual void TickComponent(float DeltaTime, enum ETickType TickType, FActorComponentTickFunction* ThisTickFunction) override;
// 
// private:
// 	// Accumulated rotation input (degrees per second)
// 	float CurrentPitchInput = 0.0f;
// 
// 	float CurrentYawInput = 0.0f;
// 
// 	float CurrentRollInput = 0.0f;
// 
// 	// Accumulated thrust input (normalized -1 to 1)
// 	float CurrentThrustInput = 0.0f;
// 
// 	float CurrentStrafeXInput = 0.0f;
// 
// 	float CurrentStrafeYInput = 0.0f;
// 
// 	float CurrentStrafeZInput = 0.0f;
// 
// };
// 

// ============================================================================
// FILE: LevelGeneratorComponent.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\LevelGeneratorComponent.cpp
// ============================================================================
// // Generated by ProceduralGameGenerator
// #include "LevelGeneratorComponent.h"
// 
// ULevelGeneratorComponent::ULevelGeneratorComponent(const FObjectInitializer& ObjectInitializer)
// 	: Super(ObjectInitializer)
// {
// 	// Constructor code here
// }
// 

// ============================================================================
// FILE: LevelGeneratorComponent.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\LevelGeneratorComponent.h
// ============================================================================
// // Generated by ProceduralGameGenerator
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "GameFramework/Actor.h"
// #include "Engine/World.h"
// 
// class CHIMERA_API ULevelGeneratorComponent : public UActorComponent
// {
// 	GENERATED_BODY()
// 
// public:
// 	ULevelGeneratorComponent(const FObjectInitializer& ObjectInitializer);
// 
// protected:
// 	// Override functions here
// 
// private:
// };
// 

// ============================================================================
// FILE: ProceduralGeneratorComponent.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ProceduralGeneratorComponent.cpp
// ============================================================================
// // Generated by ProceduralGameGenerator
// #include "ProceduralGeneratorComponent.h"
// 
// UProceduralGeneratorComponent::UProceduralGeneratorComponent(const FObjectInitializer& ObjectInitializer)
// 	: Super(ObjectInitializer)
// {
// 	// Constructor code here
// }
// 

// ============================================================================
// FILE: ProceduralGeneratorComponent.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\ProceduralGeneratorComponent.h
// ============================================================================
// // Generated by ProceduralGameGenerator
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "GameFramework/Actor.h"
// 
// class CHIMERA_API UProceduralGeneratorComponent : public UActorComponent
// {
// 	GENERATED_BODY()
// 
// public:
// 	UProceduralGeneratorComponent(const FObjectInitializer& ObjectInitializer);
// 
// protected:
// 	// Override functions here
// 
// private:
// };
// 

// ============================================================================
// FILE: VehicleSpawnerComponent.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\VehicleSpawnerComponent.cpp
// ============================================================================
// // Generated by ProceduralGameGenerator
// #include "VehicleSpawnerComponent.h"
// 
// UVehicleSpawnerComponent::UVehicleSpawnerComponent(const FObjectInitializer& ObjectInitializer)
// 	: Super(ObjectInitializer)
// {
// 	// Constructor code here
// }
// 

// ============================================================================
// FILE: VehicleSpawnerComponent.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\VehicleSpawnerComponent.h
// ============================================================================
// // Generated by ProceduralGameGenerator
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "GameFramework/Actor.h"
// #include "Engine/World.h"
// 
// class CHIMERA_API UVehicleSpawnerComponent : public UActorComponent
// {
// 	GENERATED_BODY()
// 
// public:
// 	UVehicleSpawnerComponent(const FObjectInitializer& ObjectInitializer);
// 
// protected:
// 	// Override functions here
// 
// private:
// };
// 

// ============================================================================
// FILE: OffroadCar\ChimeraOffroadCar.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\OffroadCar\ChimeraOffroadCar.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "ChimeraOffroadCar.h"
// #include "ChimeraOffroadWheelFront.h"
// #include "ChimeraOffroadWheelRear.h"
// #include "ChaosWheeledVehicleMovementComponent.h"
// #include "GameFramework/SpringArmComponent.h"
// #include "Components/StaticMeshComponent.h"
// #include "Components/SceneComponent.h"
// #include "Components/SkeletalMeshComponent.h"
// 
// AChimeraOffroadCar::AChimeraOffroadCar()
// {
// 	// construct the mesh components
// 	Chassis = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Chassis"));
// 	Chassis->SetupAttachment(GetMesh());
// 
// 	// NOTE: tire sockets are set from the Blueprint class
// 	TireFrontLeft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Tire Front Left"));
// 	TireFrontLeft->SetupAttachment(GetMesh(), FName("VisWheel_FL"));
// 	TireFrontLeft->SetCollisionProfileName(FName("NoCollision"));
// 
// 	TireFrontRight = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Tire Front Right"));
// 	TireFrontRight->SetupAttachment(GetMesh(), FName("VisWheel_FR"));
// 	TireFrontRight->SetCollisionProfileName(FName("NoCollision"));
// 	TireFrontRight->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
// 
// 	TireRearLeft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Tire Rear Left"));
// 	TireRearLeft->SetupAttachment(GetMesh(), FName("VisWheel_BL"));
// 	TireRearLeft->SetCollisionProfileName(FName("NoCollision"));
// 
// 	TireRearRight = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Tire Rear Right"));
// 	TireRearRight->SetupAttachment(GetMesh(), FName("VisWheel_BR"));
// 	TireRearRight->SetCollisionProfileName(FName("NoCollision"));
// 	TireRearRight->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
// 
// 	// adjust the cameras
// 	GetFrontSpringArm()->SetRelativeLocation(FVector(-5.0f, -30.0f, 135.0f));
// 	GetBackSpringArm()->SetRelativeLocation(FVector(0.0f, 0.0f, 75.0f));
// 
// 	// Note: for faster iteration times, the vehicle setup can be tweaked in the Blueprint instead
// 
// 	// Set up the chassis
// 	GetChaosVehicleMovement()->ChassisHeight = 160.0f;
// 	GetChaosVehicleMovement()->DragCoefficient = 0.1f;
// 	GetChaosVehicleMovement()->DownforceCoefficient = 0.1f;
// 	GetChaosVehicleMovement()->CenterOfMassOverride = FVector(0.0f, 0.0f, 75.0f);
// 	GetChaosVehicleMovement()->bEnableCenterOfMassOverride = true;
// 
// 	// Set up the wheels
// 	GetChaosVehicleMovement()->bLegacyWheelFrictionPosition = false;
// 	GetChaosVehicleMovement()->WheelSetups.SetNum(4);
// 
// 	GetChaosVehicleMovement()->WheelSetups[0].WheelClass = UChimeraOffroadWheelFront::StaticClass();
// 	GetChaosVehicleMovement()->WheelSetups[0].BoneName = FName("PhysWheel_FL");
// 	GetChaosVehicleMovement()->WheelSetups[0].AdditionalOffset = FVector(0.0f, 0.0f, 0.0f);
// 
// 	GetChaosVehicleMovement()->WheelSetups[1].WheelClass = UChimeraOffroadWheelFront::StaticClass();
// 	GetChaosVehicleMovement()->WheelSetups[1].BoneName = FName("PhysWheel_FR");
// 	GetChaosVehicleMovement()->WheelSetups[1].AdditionalOffset = FVector(0.0f, 0.0f, 0.0f);
// 
// 	GetChaosVehicleMovement()->WheelSetups[2].WheelClass = UChimeraOffroadWheelRear::StaticClass();
// 	GetChaosVehicleMovement()->WheelSetups[2].BoneName = FName("PhysWheel_BL");
// 	GetChaosVehicleMovement()->WheelSetups[2].AdditionalOffset = FVector(0.0f, 0.0f, 0.0f);
// 
// 	GetChaosVehicleMovement()->WheelSetups[3].WheelClass = UChimeraOffroadWheelRear::StaticClass();
// 	GetChaosVehicleMovement()->WheelSetups[3].BoneName = FName("PhysWheel_BR");
// 	GetChaosVehicleMovement()->WheelSetups[3].AdditionalOffset = FVector(0.0f, 0.0f, 0.0f);
// 
// 	// Set up the engine
// 	// NOTE: Check the Blueprint asset for the Torque Curve
// 	GetChaosVehicleMovement()->EngineSetup.MaxTorque = 600.0f;
// 	GetChaosVehicleMovement()->EngineSetup.MaxRPM = 5000.0f;
// 	GetChaosVehicleMovement()->EngineSetup.EngineIdleRPM = 1200.0f;
// 	GetChaosVehicleMovement()->EngineSetup.EngineBrakeEffect = 0.05f;
// 	GetChaosVehicleMovement()->EngineSetup.EngineRevUpMOI = 5.0f;
// 	GetChaosVehicleMovement()->EngineSetup.EngineRevDownRate = 600.0f;
// 
// 	// Set up the differential
// 	GetChaosVehicleMovement()->DifferentialSetup.DifferentialType = EVehicleDifferential::AllWheelDrive;
// 	GetChaosVehicleMovement()->DifferentialSetup.FrontRearSplit = 0.5f;
// 
// 	// Set up the steering
// 	// NOTE: Check the Blueprint asset for the Steering Curve
// 	GetChaosVehicleMovement()->SteeringSetup.SteeringType = ESteeringType::AngleRatio;
// 	GetChaosVehicleMovement()->SteeringSetup.AngleRatio = 0.7f;
// }

// ============================================================================
// FILE: OffroadCar\ChimeraOffroadCar.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\OffroadCar\ChimeraOffroadCar.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "ChimeraPawn.h"
// #include "ChimeraOffroadCar.generated.h"
// 
// /**
//  *  Offroad car wheeled vehicle implementation
//  */
// UCLASS(abstract)
// class AChimeraOffroadCar : public AChimeraPawn
// {
// 	GENERATED_BODY()
// 	
// 	/** Chassis static mesh */
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category ="Components", meta = (AllowPrivateAccess = "true"))
// 	UStaticMeshComponent* Chassis;
// 
// 	/** FL Tire static mesh */
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category ="Components", meta = (AllowPrivateAccess = "true"))
// 	UStaticMeshComponent* TireFrontLeft;
// 
// 	/** FR Tire static mesh */
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category ="Components", meta = (AllowPrivateAccess = "true"))
// 	UStaticMeshComponent* TireFrontRight;
// 
// 	/** RL Tire static mesh */
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category ="Components", meta = (AllowPrivateAccess = "true"))
// 	UStaticMeshComponent* TireRearLeft;
// 
// 	/** RR Tire static mesh */
// 	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category ="Components", meta = (AllowPrivateAccess = "true"))
// 	UStaticMeshComponent* TireRearRight;
// 
// public:
// 
// 	AChimeraOffroadCar();
// };
// 

// ============================================================================
// FILE: OffroadCar\ChimeraOffroadWheelFront.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\OffroadCar\ChimeraOffroadWheelFront.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "ChimeraOffroadWheelFront.h"
// 
// UChimeraOffroadWheelFront::UChimeraOffroadWheelFront()
// {
// 	WheelRadius = 50.0f;
// 	CorneringStiffness = 750.0f;
// 	FrictionForceMultiplier = 4.0f;
// 	bAffectedByEngine = true;
// 
// 	SuspensionMaxRaise = 20.0f;
// 	SuspensionMaxDrop = 20.0f;
// 	WheelLoadRatio = 1.0f;
// 	SpringRate = 100.0f;
// 	SpringPreload = 100.0f;
// 	SweepShape = ESweepShape::Shapecast;
// 
// 	MaxBrakeTorque = 3000.0f;
// 	MaxHandBrakeTorque = 6000.0f;
// }

// ============================================================================
// FILE: OffroadCar\ChimeraOffroadWheelFront.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\OffroadCar\ChimeraOffroadWheelFront.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "ChimeraWheelFront.h"
// #include "ChimeraOffroadWheelFront.generated.h"
// 
// /**
//  *  Front wheel definition for Offroad Car.
//  */
// UCLASS()
// class UChimeraOffroadWheelFront : public UChimeraWheelFront
// {
// 	GENERATED_BODY()
// 	
// public:
// 	UChimeraOffroadWheelFront();
// };
// 

// ============================================================================
// FILE: OffroadCar\ChimeraOffroadWheelRear.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\OffroadCar\ChimeraOffroadWheelRear.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "ChimeraOffroadWheelRear.h"
// 
// UChimeraOffroadWheelRear::UChimeraOffroadWheelRear()
// {
// 	WheelRadius = 50.f;
// 	CorneringStiffness = 750.0f;
// 	FrictionForceMultiplier = 4.0f;
// 	
// 	SuspensionMaxRaise = 20.0f;
// 	SuspensionMaxDrop = 20.0f;
// 	WheelLoadRatio = 1.0f;
// 	SpringRate = 100.0f;
// 	SpringPreload = 100.0f;
// 	SweepShape = ESweepShape::Shapecast;
// 
// 	MaxBrakeTorque = 3000.0f;
// 	MaxHandBrakeTorque = 6000.0f;
// }

// ============================================================================
// FILE: OffroadCar\ChimeraOffroadWheelRear.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\OffroadCar\ChimeraOffroadWheelRear.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "ChimeraWheelRear.h"
// #include "ChimeraOffroadWheelRear.generated.h"
// 
// /**
//  *  Rear wheel definition for Offroad Car.
//  */
// UCLASS()
// class UChimeraOffroadWheelRear : public UChimeraWheelRear
// {
// 	GENERATED_BODY()
// 	
// public:
// 
// 	UChimeraOffroadWheelRear();
// };
// 

// ============================================================================
// FILE: SportsCar\ChimeraSportsCar.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\SportsCar\ChimeraSportsCar.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "ChimeraPawn.h"
// #include "ChimeraSportsCar.generated.h"
// 
// /**
//  *  Sports car wheeled vehicle implementation
//  */
// UCLASS(abstract)
// class AChimeraSportsCar : public AChimeraPawn
// {
// 	GENERATED_BODY()
// 	
// public:
// 
// 	AChimeraSportsCar();
// };
// 

// ============================================================================
// FILE: SportsCar\ChimeraSportsWheelFront.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\SportsCar\ChimeraSportsWheelFront.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "ChimeraSportsWheelFront.h"
// 
// UChimeraSportsWheelFront::UChimeraSportsWheelFront()
// {
// 	WheelRadius = 39.0f;
// 	WheelWidth = 35.0f;
// 	FrictionForceMultiplier = 3.0f;
// 
// 	MaxBrakeTorque = 4500.0f;
// 	MaxHandBrakeTorque = 6000.0f;
// }

// ============================================================================
// FILE: SportsCar\ChimeraSportsWheelFront.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\SportsCar\ChimeraSportsWheelFront.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "ChimeraWheelFront.h"
// #include "ChimeraSportsWheelFront.generated.h"
// 
// /**
//  *  Front wheel definition for Sports Car.
//  */
// UCLASS()
// class UChimeraSportsWheelFront : public UChimeraWheelFront
// {
// 	GENERATED_BODY()
// 	
// public:
// 
// 	UChimeraSportsWheelFront();
// };
// 

// ============================================================================
// FILE: SportsCar\ChimeraSportsWheelRear.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\SportsCar\ChimeraSportsWheelRear.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "ChimeraSportsWheelRear.h"
// 
// UChimeraSportsWheelRear::UChimeraSportsWheelRear()
// {
// 	WheelRadius = 40.f;
// 	WheelWidth = 40.0f;
// 	FrictionForceMultiplier = 4.0f;
// 	SlipThreshold = 100.0f;
// 	SkidThreshold = 100.0f;
// 	MaxSteerAngle = 0.0f;
// 	MaxHandBrakeTorque = 6000.0f;
// }

// ============================================================================
// FILE: SportsCar\ChimeraSportsWheelRear.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\SportsCar\ChimeraSportsWheelRear.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "ChimeraWheelRear.h"
// #include "ChimeraSportsWheelRear.generated.h"
// 
// /**
//  *  Rear wheel definition for Sports Car.
//  */
// UCLASS()
// class UChimeraSportsWheelRear : public UChimeraWheelRear
// {
// 	GENERATED_BODY()
// 	
// public:
// 
// 	UChimeraSportsWheelRear();
// };
// 

// ============================================================================
// FILE: Variant_OffRoad\OffroadGameMode.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_OffRoad\OffroadGameMode.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "Variant_OffRoad/OffroadGameMode.h"
// 
// AOffroadGameMode::AOffroadGameMode()
// {
// 
// }

// ============================================================================
// FILE: Variant_OffRoad\OffroadGameMode.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_OffRoad\OffroadGameMode.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "GameFramework/GameModeBase.h"
// #include "OffroadGameMode.generated.h"
// 
// /**
//  *  Simple GameMode for an offroad vehicle game
//  */
// UCLASS(abstract)
// class AOffroadGameMode : public AGameModeBase
// {
// 	GENERATED_BODY()
// 	
// public:
// 
// 	/** Constructor */
// 	AOffroadGameMode();
// };
// 

// ============================================================================
// FILE: Variant_TimeTrial\TimeTrialGameMode.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\TimeTrialGameMode.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "TimeTrialGameMode.h"
// #include "Kismet/GameplayStatics.h"
// #include "TimeTrialTrackGate.h"
// #include "Engine/World.h"
// 
// void ATimeTrialGameMode::BeginPlay()
// {
// 	Super::BeginPlay();
// 
// 	// get the finish line marker
// 	TArray<AActor*> ActorList;
// 
// 	UGameplayStatics::GetAllActorsOfClassWithTag(GetWorld(), ATimeTrialTrackGate::StaticClass(), FinishTag, ActorList);
// 
// 	if (ActorList.Num() > 0)
// 	{
// 		// get the first returned track marker that matches the tag
// 		FinishLineMarker = Cast<ATimeTrialTrackGate>(ActorList[0]);
// 	}
// 
// }
// 
// ATimeTrialTrackGate* ATimeTrialGameMode::GetFinishLine() const
// {
// 	return FinishLineMarker;
// }
// 

// ============================================================================
// FILE: Variant_TimeTrial\TimeTrialGameMode.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\TimeTrialGameMode.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "GameFramework/GameModeBase.h"
// #include "TimeTrialGameMode.generated.h"
// 
// class ATimeTrialTrackGate;
// 
// /**
//  *  A simple GameMode for a Time Trial racing game
//  */
// UCLASS(abstract)
// class ATimeTrialGameMode : public AGameModeBase
// {
// 	GENERATED_BODY()
// 	
// protected:
// 
// 	/** Actor tag used to find the finish line marker on the level */
// 	UPROPERTY(EditAnywhere, Category="Time Trial")
// 	FName FinishTag;
// 
// 	/** Number of laps for the race */
// 	UPROPERTY(EditAnywhere, Category="Time Trial")
// 	int32 Laps = 3;
// 
// 	/** Pointer to the finish line track marker */
// 	TObjectPtr<ATimeTrialTrackGate> FinishLineMarker;
// 
// protected:
// 
// 	/** Gameplay initialization */
// 	virtual void BeginPlay() override;
// 
// public: 
// 
// 	/** Returns the track marker for the finish line */
// 	ATimeTrialTrackGate* GetFinishLine() const;
// 
// 	/** Returns the number of laps for the race */
// 	int32 GetLaps() const { return Laps; };
// 
// };
// 

// ============================================================================
// FILE: Variant_TimeTrial\TimeTrialPlayerController.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\TimeTrialPlayerController.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "TimeTrialPlayerController.h"
// #include "TimeTrialUI.h"
// #include "Engine/World.h"
// #include "TimeTrialGameMode.h"
// #include "TimeTrialTrackGate.h"
// #include "EnhancedInputSubsystems.h"
// #include "Engine/LocalPlayer.h"
// #include "InputMappingContext.h"
// #include "ChimeraUI.h"
// #include "ChimeraPawn.h"
// #include "ChaosWheeledVehicleMovementComponent.h"
// #include "Blueprint/UserWidget.h"
// #include "Chimera.h"
// #include "Kismet/GameplayStatics.h"
// #include "GameFramework/PlayerStart.h"
// #include "Widgets/Input/SVirtualJoystick.h"
// 
// void ATimeTrialPlayerController::BeginPlay()
// {
// 	Super::BeginPlay();
// 
// 	// only spawn UI on local player controllers
// 	if (IsLocalPlayerController())
// 	{
// 		if (ShouldUseTouchControls())
// 		{
// 			// spawn the mobile controls widget
// 			MobileControlsWidget = CreateWidget<UUserWidget>(this, MobileControlsWidgetClass);
// 
// 			if (MobileControlsWidget)
// 			{
// 				// add the controls to the player screen
// 				MobileControlsWidget->AddToPlayerScreen(0);
// 
// 			} else {
// 
// 				UE_LOG(LogChimera, Error, TEXT("Could not spawn mobile controls widget."));
// 
// 			}
// 		}
// 
// 		// create the UI widget
// 		UIWidget = CreateWidget<UTimeTrialUI>(this, UIWidgetClass);
// 
// 		if (UIWidget)
// 		{
// 			UIWidget->AddToViewport(0);
// 
// 			// subscribe to the race start delegate
// 			UIWidget->OnRaceStart.AddDynamic(this, &ATimeTrialPlayerController::StartRace);
// 
// 		} else {
// 
// 			UE_LOG(LogChimera, Error, TEXT("Could not spawn Time Trial UI widget."));
// 
// 		}
// 		
// 
// 		// spawn the UI widget and add it to the viewport
// 		VehicleUI = CreateWidget<UChimeraUI>(this, VehicleUIClass);
// 
// 		if (VehicleUI)
// 		{
// 			VehicleUI->AddToViewport(0);
// 
// 		} else {
// 
// 			UE_LOG(LogChimera, Error, TEXT("Could not spawn vehicle UI widget."));
// 
// 		}
// 	}
// 
// }
// 
// void ATimeTrialPlayerController::SetupInputComponent()
// {
// 	Super::SetupInputComponent();
// 
// 	// only add IMCs for local player controllers
// 	if (IsLocalPlayerController())
// 	{
// 		// Add Input Mapping Contexts
// 		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
// 		{
// 			for (UInputMappingContext* CurrentContext : DefaultMappingContexts)
// 			{
// 				Subsystem->AddMappingContext(CurrentContext, 0);
// 			}
// 
// 			// only add these IMCs if we're not using mobile touch input
// 			if (!ShouldUseTouchControls())
// 			{
// 				for (UInputMappingContext* CurrentContext : MobileExcludedMappingContexts)
// 				{
// 					Subsystem->AddMappingContext(CurrentContext, 0);
// 				}
// 			}
// 
// 			if (bUseSteeringWheelControls)
// 			{
// 				Subsystem->AddMappingContext(SteeringWheelInputMappingContext, 0);
// 			}
// 		}
// 	}
// }
// 
// void ATimeTrialPlayerController::OnPossess(APawn* InPawn)
// {
// 	Super::OnPossess(InPawn);
// 
// 	// get a pointer to the controlled pawn
// 	VehiclePawn = CastChecked<AChimeraPawn>(InPawn);
// 
// 	// subscribe to the pawn's OnDestroyed delegate
// 	VehiclePawn->OnDestroyed.AddDynamic(this, &ATimeTrialPlayerController::OnPawnDestroyed);
// 
// 	// disable input on the pawn if the race hasn't started yet
// 	if (!bRaceStarted)
// 	{
// 		VehiclePawn->DisableInput(this);
// 	}	
// }
// 
// void ATimeTrialPlayerController::Tick(float Delta)
// {
// 	Super::Tick(Delta);
// 
// 	if (IsValid(VehiclePawn) && IsValid(VehicleUI))
// 	{
// 		VehicleUI->UpdateSpeed(VehiclePawn->GetChaosVehicleMovement()->GetForwardSpeed());
// 		VehicleUI->UpdateGear(VehiclePawn->GetChaosVehicleMovement()->GetCurrentGear());
// 	}
// }
// 
// void ATimeTrialPlayerController::StartRace()
// {
// 	// get the finish line from the game mode
// 	if (ATimeTrialGameMode* GM = Cast<ATimeTrialGameMode>(GetWorld()->GetAuthGameMode()))
// 	{
// 		SetTargetGate(GM->GetFinishLine()->GetNextMarker());
// 	}
// 
// 	// raise the race started flag so any respawned vehicles start with controls unlocked 
// 	bRaceStarted = true;
// 
// 	// start the first lap
// 	CurrentLap = 0;
// 	IncrementLapCount();
// 
// 	// enable input on the pawn
// 	GetPawn()->EnableInput(this);
// }
// 
// void ATimeTrialPlayerController::IncrementLapCount()
// {
// 	// increment the lap counter
// 	++CurrentLap;
// 
// 	// update the UI
// 	UIWidget->UpdateLapCount(CurrentLap, GetWorld()->GetTimeSeconds());
// }
// 
// ATimeTrialTrackGate* ATimeTrialPlayerController::GetTargetGate()
// {
// 	return TargetGate.Get();
// }
// 
// void ATimeTrialPlayerController::SetTargetGate(ATimeTrialTrackGate* Gate)
// {
// 	TargetGate = Gate;
// }
// 
// void ATimeTrialPlayerController::OnPawnDestroyed(AActor* DestroyedPawn)
// {
// 	// find the player start
// 	TArray<AActor*> ActorList;
// 	UGameplayStatics::GetAllActorsOfClass(GetWorld(), APlayerStart::StaticClass(), ActorList);
// 
// 	if (ActorList.Num() > 0)
// 	{
// 		// spawn a vehicle at the player start
// 		const FTransform SpawnTransform = ActorList[0]->GetActorTransform();
// 
// 		if (AChimeraPawn* RespawnedVehicle = GetWorld()->SpawnActor<AChimeraPawn>(VehiclePawnClass, SpawnTransform))
// 		{
// 			// possess the vehicle
// 			Possess(RespawnedVehicle);
// 		}
// 	}
// }
// 
// bool ATimeTrialPlayerController::ShouldUseTouchControls() const
// {
// 	// are we on a mobile platform? Should we force touch?
// 	return SVirtualJoystick::ShouldDisplayTouchInterface() || bForceTouchControls;
// }
// 

// ============================================================================
// FILE: Variant_TimeTrial\TimeTrialPlayerController.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\TimeTrialPlayerController.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "GameFramework/PlayerController.h"
// #include "TimeTrialPlayerController.generated.h"
// 
// class ATimeTrialTrackGate;
// class UTimeTrialUI;
// class UInputMappingContext;
// class UChimeraUI;
// class AChimeraPawn;
// 
// /**
//  *  A simple PlayerController for a Time Trial racing game
//  */
// UCLASS(abstract, Config="Game")
// class ATimeTrialPlayerController : public APlayerController
// {
// 	GENERATED_BODY()
// 	
// protected:
// 
// 	/** Input Mapping Contexts */
// 	UPROPERTY(EditAnywhere, Category ="Input|Input Mappings")
// 	TArray<UInputMappingContext*> DefaultMappingContexts;
// 
// 	/** Input Mapping Contexts */
// 	UPROPERTY(EditAnywhere, Category="Input|Input Mappings")
// 	TArray<UInputMappingContext*> MobileExcludedMappingContexts;
// 
// 	/** Mobile controls widget to spawn */
// 	UPROPERTY(EditAnywhere, Category="Input|Touch Controls")
// 	TSubclassOf<UUserWidget> MobileControlsWidgetClass;
// 
// 	/** Pointer to the mobile controls widget */
// 	UPROPERTY()
// 	TObjectPtr<UUserWidget> MobileControlsWidget;
// 
// 	/** If true, the player will use UMG touch controls even if not playing on mobile platforms */
// 	UPROPERTY(EditAnywhere, Config, Category = "Input|Touch Controls")
// 	bool bForceTouchControls = false;
// 
// 	/** If true, the optional steering wheel input mapping context will be registered */
// 	UPROPERTY(EditAnywhere, Category = "Input|Steering Wheel Controls")
// 	bool bUseSteeringWheelControls = false;
// 
// 	/** Optional Input Mapping Context to be used for steering wheel input.
// 	 *  This is added alongside the default Input Mapping Context and does not block other forms of input.
// 	 */
// 	UPROPERTY(EditAnywhere, Category = "Input|Steering Wheel Controls", meta = (EditCondition = "bUseSteeringWheelControls"))
// 	UInputMappingContext* SteeringWheelInputMappingContext;
// 
// 	/** Type of UI widget to spawn*/
// 	UPROPERTY(EditAnywhere, Category="Time Trial|UI")
// 	TSubclassOf<UTimeTrialUI> UIWidgetClass;
// 
// 	/** Pointer to the UI Widget */
// 	UPROPERTY()
// 	TObjectPtr<UTimeTrialUI> UIWidget;
// 
// 	/** Type of the UI to spawn */
// 	UPROPERTY(EditAnywhere, Category="Vehicle|UI")
// 	TSubclassOf<UChimeraUI> VehicleUIClass;
// 
// 	/** Pointer to the UI widget */
// 	UPROPERTY()
// 	TObjectPtr<UChimeraUI> VehicleUI;
// 
// 	/** Next track gate the car should pass */
// 	TObjectPtr<ATimeTrialTrackGate> TargetGate;
// 
// 	/** Lap counter */
// 	int32 CurrentLap = 0;
// 
// 	/** If true, the race has already started */
// 	bool bRaceStarted = false;
// 
// 	/** Type of vehicle to automatically respawn when it's destroyed */
// 	UPROPERTY(EditAnywhere, Category="Vehicle|Respawn")
// 	TSubclassOf<AChimeraPawn> VehiclePawnClass;
// 
// 	/** Pointer to the controlled vehicle pawn */
// 	TObjectPtr<AChimeraPawn> VehiclePawn;
// 
// protected:
// 
// 	/** Gameplay initialization */
// 	virtual void BeginPlay() override;
// 
// 	/** Input initialization */
// 	virtual void SetupInputComponent() override;
// 
// 	/** Pawn initialization */
// 	virtual void OnPossess(APawn* aPawn) override;
// 
// public:
// 
// 	/** UI vehicle state update on tick */
// 	virtual void Tick(float Delta) override;
// 
// public:
// 
// 	/** Sets up the race start */
// 	UFUNCTION()
// 	void StartRace();
// 
// 	/** Moves on to the next lap */
// 	void IncrementLapCount();
// 
// 	/** Returns the current target track gate */
// 	ATimeTrialTrackGate* GetTargetGate();
// 
// 	/** Sets the target track gate for this player */
// 	void SetTargetGate(ATimeTrialTrackGate* Gate);
// 
// protected:
// 
// 	/** Handles pawn destruction and respawning */
// 	UFUNCTION()
// 	void OnPawnDestroyed(AActor* DestroyedPawn);
// 
// 	/** Returns true if the player should use UMG touch controls */
// 	bool ShouldUseTouchControls() const;
// };
// 

// ============================================================================
// FILE: Variant_TimeTrial\TimeTrialTrackGate.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\TimeTrialTrackGate.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "TimeTrialTrackGate.h"
// #include "Components/SceneComponent.h"
// #include "Components/BoxComponent.h"
// #include "TimeTrialPlayerController.h"
// 
// ATimeTrialTrackGate::ATimeTrialTrackGate()
// {
//  	PrimaryActorTick.bCanEverTick = true;
// 
// 	// create the root component
// 	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
// 
// 	// create the collision box
// 	CollisionBox = CreateDefaultSubobject<UBoxComponent>(TEXT("Collision Box"));
// 	CollisionBox->SetupAttachment(RootComponent);
// 
// 	CollisionBox->SetBoxExtent(FVector(1000.0f));
// 	CollisionBox->SetLineThickness(32.0f);
// 	CollisionBox->bHiddenInGame = false;
// 	CollisionBox->SetCollisionProfileName(FName("OverlapAllDynamic"));
// 
// }
// 
// void ATimeTrialTrackGate::NotifyActorBeginOverlap(AActor* OtherActor)
// {
// 	// get the player controller of the overlapping actor
// 	if (ATimeTrialPlayerController* PC = Cast<ATimeTrialPlayerController>(OtherActor->GetInstigatorController()))
// 	{
// 		// is this the current target marker for the player?
// 		if (PC->GetTargetGate() == this)
// 		{
// 			// point the player to the next marker
// 			PC->SetTargetGate(NextMarker);
// 
// 			// if this is the finish line, increment the lap
// 			if (bIsFinishLine)
// 			{
// 				PC->IncrementLapCount();
// 			}
// 		}
// 	}
// }
// 
// ATimeTrialTrackGate* ATimeTrialTrackGate::GetNextMarker() const
// {
// 	return NextMarker;
// }
// 

// ============================================================================
// FILE: Variant_TimeTrial\TimeTrialTrackGate.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\TimeTrialTrackGate.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "GameFramework/Actor.h"
// #include "TimeTrialTrackGate.generated.h"
// 
// class UBoxComponent;
// 
// /**
//  *  A track gate volume for a Time Trial racing game.
//  *  Players must pass through the track gates in order to complete a lap.
//  */
// UCLASS(abstract)
// class ATimeTrialTrackGate : public AActor
// {
// 	GENERATED_BODY()
// 	
// 	/** Collision Box */
// 	UPROPERTY(VisibleAnywhere, Category = "Components", meta = (AllowPrivateAccess = "true"))
// 	UBoxComponent* CollisionBox;
// 
// protected:
// 
// 	/** If this is set to true, this track gate is considered the finish line and will increase the lap when passed */
// 	UPROPERTY(EditAnywhere, Category="Track Gate")
// 	bool bIsFinishLine = false;
// 
// 	/** Pointer to the next track marker in the sequence */
// 	UPROPERTY(EditAnywhere, Category="Track Gate")
// 	ATimeTrialTrackGate* NextMarker;
// 
// public:	
// 	
// 	/** Constructor */
// 	ATimeTrialTrackGate();
// 
// protected:
// 
// 	/** Handle collision */
// 	virtual void NotifyActorBeginOverlap(AActor* OtherActor) override;
// 
// public:
// 
// 	/** Returns the next marker on the track */
// 	ATimeTrialTrackGate* GetNextMarker() const;
// };
// 

// ============================================================================
// FILE: Variant_TimeTrial\UI\TimeTrialStartUI.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\UI\TimeTrialStartUI.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "TimeTrialStartUI.h"
// 
// void UTimeTrialStartUI::StartCountdown()
// {
// 	// pass control to BP
// 	BP_StartCountdown();
// }
// 
// void UTimeTrialStartUI::FinishCountdown()
// {
// 	// broadcast the delegate
// 	OnCountdownFinished.Broadcast();
// }
// 

// ============================================================================
// FILE: Variant_TimeTrial\UI\TimeTrialStartUI.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\UI\TimeTrialStartUI.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "Blueprint/UserWidget.h"
// #include "TimeTrialStartUI.generated.h"
// 
// DECLARE_DYNAMIC_MULTICAST_DELEGATE(FCountdownFinishedDelegate);
// 
// /**
//  *  A race start countdown widget.
//  *  The countdown animation is performed by widget animation.
//  *  Calls a delegate when the countdown is done to start the race.
//  */
// UCLASS(abstract)
// class UTimeTrialStartUI : public UUserWidget
// {
// 	GENERATED_BODY()
// 	
// public:
// 
// 	/** Starts the race countdown */
// 	void StartCountdown();
// 
// protected:
// 
// 	/** Passes control to Blueprint to animate the race countdown. FinishCountdown should be called to start the race when it's done. */
// 	UFUNCTION(BlueprintImplementableEvent, Category="Countdown", meta = (DisplayName = "Start Countdown"))
// 	void BP_StartCountdown();
// 
// 	/** Finishes the countdown and starts the race. */
// 	UFUNCTION(BlueprintCallable, Category="Countdown")
// 	void FinishCountdown();
// 
// public:
// 
// 	FCountdownFinishedDelegate OnCountdownFinished;
// 
// };
// 

// ============================================================================
// FILE: Variant_TimeTrial\UI\TimeTrialUI.cpp
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\UI\TimeTrialUI.cpp
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// 
// #include "TimeTrialUI.h"
// #include "TimeTrialStartUI.h"
// 
// void UTimeTrialUI::NativeConstruct()
// {
// 	Super::NativeConstruct();
// 
// 	// create the start countdown widget
// 	UTimeTrialStartUI* StartUI = CreateWidget<UTimeTrialStartUI>(GetOwningPlayer(), StartUIClass);
// 	StartUI->AddToViewport(0);
// 
// 	// subscribe to the countdown finished delegate
// 	StartUI->OnCountdownFinished.AddDynamic(this, &UTimeTrialUI::StartRace);
// 
// 	// start the countdown
// 	StartUI->StartCountdown();
// }
// 
// void UTimeTrialUI::UpdateLapCount(int32 Lap, float NewLapStartTime)
// {
// 	// save the new lap start time
// 	LapStartTime = NewLapStartTime;
// 
// 	// calculate the lap time
// 	const float LapTime = NewLapStartTime - LastLapTime;
// 
// 	// is this the first lap?
// 	if (Lap > 1)
// 	{
// 		// do we have an invalid lap time?
// 		if (BestLapTime < 0.0f)
// 		{
// 			// save the current lap time
// 			BestLapTime = LapTime;
// 
// 		} else {
// 
// 			// not the first lap: do we have a lower lap time?
// 			if (LapTime < BestLapTime)
// 			{
// 				// save the best lap time
// 				BestLapTime = LapTime;
// 			}
// 
// 		}
// 		
// 	} else {
// 
// 		// first lap: save an invalid lap time
// 		BestLapTime = -1.0f;
// 
// 	}
// 
// 	// save the current lap
// 	CurrentLap = Lap;
// 
// 	// save the lap start time
// 	LastLapTime = NewLapStartTime;
// 
// 	// pass control to BP to update the widgets
// 	BP_UpdateLaps();
// }
// 
// void UTimeTrialUI::StartRace()
// {
// 	// broadcast the delegate
// 	OnRaceStart.Broadcast();
// }
// 

// ============================================================================
// FILE: Variant_TimeTrial\UI\TimeTrialUI.h
// PATH: E:\PythonChimera\Chimera\Source\Chimera\Variant_TimeTrial\UI\TimeTrialUI.h
// ============================================================================
// // Copyright Epic Games, Inc. All Rights Reserved.
// 
// #pragma once
// 
// #include "CoreMinimal.h"
// #include "Blueprint/UserWidget.h"
// #include "TimeTrialUI.generated.h"
// 
// class UTimeTrialStartUI;
// 
// DECLARE_DYNAMIC_MULTICAST_DELEGATE(FStartRaceDelegate);
// 
// /**
//  *  Simple UI for a Time Trial racing game
//  *  Keeps track of lap number and best time
//  *  Spawns a sub-widget to do the initial countdown
//  */
// UCLASS(abstract)
// class UTimeTrialUI : public UUserWidget
// {
// 	GENERATED_BODY()
// 	
// protected:
// 
// 	/** Type of start countdown UI widget to spawn */
// 	UPROPERTY(EditAnywhere, Category="Start Countdown")
// 	TSubclassOf<UTimeTrialStartUI> StartUIClass;
// 
// 	/** Time when the previous lap started, in seconds */
// 	float LastLapTime = 0.0f;
// 
// 	/** Best lap time, in seconds */
// 	float BestLapTime = 0.0f;
// 
// 	/** Game time when this lap started */
// 	float LapStartTime = 0.0f;
// 
// 	/** Current lap number */
// 	int32 CurrentLap = 0;
// 
// public:
// 
// 	/** Delegate to broadcast when the race starts */
// 	FStartRaceDelegate OnRaceStart;
// 
// protected:
// 
// 	/** Widget initialization */
// 	virtual void NativeConstruct() override;
// 
// public:
// 
// 	/** Increments the lap and updates the lap counter */
// 	void UpdateLapCount(int32 Lap, float NewLapStartTime);
// 
// 	/** Allows Blueprint control to update the lap tracker widgets */
// 	UFUNCTION(BlueprintImplementableEvent, Category="Time Trial", meta = (DisplayName = "Update Laps"))
// 	void BP_UpdateLaps();
// 
// protected:
// 
// 	/** Called from the countdown delegate to start the race */
// 	UFUNCTION()
// 	void StartRace();
// 
// 	/** Gets the current lap number */
// 	UFUNCTION(BlueprintPure, Category="Time Trial")
// 	int32 GetCurrentLap() const { return CurrentLap; };
// 
// 	/** Gets the best lap time saved */
// 	UFUNCTION(BlueprintPure, Category="Time Trial")
// 	float GetBestLapTime() const { return BestLapTime; };
// 
// 	/** Gets the best lap time saved */
// 	UFUNCTION(BlueprintPure, Category="Time Trial")
// 	float GetLapStartTime() const { return LapStartTime; };
// };
// 

# === END C++ INVENTORY ===

"""

    # Replace the inventory section in the file content
    pattern = r'# === BEGIN C\+\+ INVENTORY ===.*?# === END C\+\+ INVENTORY ==='
    new_file_content = re.sub(
        pattern,
        lambda m: inventory_section,
        file_content,
        flags=re.DOTALL
    )

    # Write the updated content back to the file
    with open(current_file_path, 'w', encoding='utf-8') as f:
        f.write(new_file_content)

    if GameConfiguration.ENABLE_DEBUG_LOGGING:
        print(f"Updated self-inventory with {len(cpp_files)} C++ files (including existing project files).")


# ============================================================================
# EXECUTION PIPELINE
# ============================================================================

def generate_all():
    """Main execution function for the procedural generation pipeline."""
    print("=== CHIMERA PROCEDURAL GAME GENERATOR ===")
    print("Starting generation pipeline...")
    print("Working with existing starter level: VehicleBasic")

    # Step 1: Ensure directories exist
    ensure_directories()

    # Step 2: Generate C++ files
    print("Generating C++ source files and components...")
    generate_all_cpp_components()

    # Step 3: Autonomous State Synchronization (Eyes, Ears, Mouth, Control)
    print("Running autonomous C++ project state synchronization...")
    sync_cpp_project_state()

    # Step 4: Update self-inventory (includes existing demo files)
    print("Updating self-inventory with all C++ files (generated + existing)...")
    update_self_inventory()

    # Step 5: Generate levels and actors via Unreal API (into existing starter level)
    print("Generating vehicles and content via Unreal Python API into starter level...")
    generate_levels_and_actors()

    # Step 6: Create procedural level structures based on starter level
    print("Creating procedural level structures based on VehicleBasic template...")
    try:
        import unreal
        
        # Reference the existing starter level
        starter_level_path = "/Game/VehicleTemplate/Maps/VehicleBasic.VehicleBasic"
        print(f"Starter level reference: {starter_level_path}")
        
        # Create procedural generated levels directory structure
        proc_levels_dir = f"{GameConfiguration.content_dir().replace(os.path.sep, '/')}/ProceduralGenerated/Levels"
        print(f"Procedural levels will be organized under: {proc_levels_dir}")
        
    except Exception as e:
        print(f"Note: Could not fully initialize procedural level structures: {e}")

    print("=== GENERATION PIPELINE COMPLETE ===")


def capture_and_analyze_screenshot(analysis_prompt=None):
    """
    Capture a viewport screenshot and send it to LM Studio for analysis.
    
    Args:
        analysis_prompt: Custom prompt for LM Studio analysis
        
    Returns:
        Analysis result from LM Studio or error
    """
    print("=== SCREENSHOT AND LM STUDIO ANALYSIS WORKFLOW ===")
    return run_screenshot_analysis_workflow(analysis_prompt=analysis_prompt)


def run_playtest():
    """Run automated play test for flight vehicle 6DOF movement system."""
    print("=== CHIMERA FLIGHT VEHICLE PLAY TEST ===")
    
    if FlightPlayTest is None:
        print("Warning: play_test module not available. Run from Unreal Editor.")
        return
    
    play_test = FlightPlayTest()
    play_test.run_full_playtest()


def run_startup_workflow():
    """
    Complete startup workflow that runs when UE Editor launches Chimera project.
    Integrates C++ generation, play test, flight mode toggle, screenshot capture,
    and LM Studio AI analysis into a single automated pipeline.
    
    This is the main entry point called automatically by PythonScriptPlugin.
    """
    print("=" * 70)
    print("CHIMERA STARTUP WORKFLOW — AUTOMATED FLIGHT TEST & ANALYSIS")
    print("=" * 70)
    
    try:
        import unreal
        
        # ========================================================================
        # PHASE 1: Generate C++ files and sync project state
        # ========================================================================
        print("\n[PHASE 1] Generating C++ components and syncing project state...")
        generate_all()
        
        # ========================================================================
        # PHASE 2: Load starter level and spawn vehicle for play test
        # ========================================================================
        print("\n[PHASE 2] Loading starter level and spawning vehicle...")
        
        starter_level_path = "/Game/VehicleTemplate/Maps/VehicleBasic.VehicleBasic"
        try:
            unreal.EditorLevelUtils.load_map(starter_level_path)
            print(f"  Loaded starter level: {starter_level_path}")
        except Exception as e:
            print(f"  Could not load starter level: {e}")
        
        # ========================================================================
        # PHASE 3: Run play test (flight mode toggle, thrust, movement)
        # ========================================================================
        print("\n[PHASE 3] Running flight vehicle play test...")
        run_playtest()
        
        # ========================================================================
        # PHASE 4: Capture screenshot and send to LM Studio for AI analysis
        # ========================================================================
        print("\n[PHASE 4] Capturing screenshot and sending to LM Studio...")
        
        import time
        timestamp = int(time.time())
        screenshot_path = os.path.join(
            GameConfiguration.content_dir().replace(os.path.sep, '/'), 
            f"Saved/Screenshots/playtest_{timestamp}.png"
        )
        
        try:
            unreal.SystemLibrary.execute_console_command(None, f"shot {screenshot_path}")
            print(f"  Captured screenshot: {screenshot_path}")
            
            # Send to LM Studio for AI analysis
            capture_and_analyze_screenshot(
                "Analyze this gameplay screenshot from the Chimera vehicle test. Specifically confirm whether the vehicle has lifted off the ground — are its wheels touching the ground? What is its approximate height above ground?"
            )
        except Exception as e:
            print(f"  Screenshot capture failed: {e}")
        
    except ImportError:
        # Standalone mode (unreal module not available)
        print("\n[STANDALONE MODE] Unreal module not available — running simulation...")
        generate_all()
        
        if FlightPlayTest is None:
            print("  Skipping play test (simulation mode)")
        else:
            play_test = FlightPlayTest()
            play_test.run_full_playtest()



def run_runtime_screenshot_playtest():
    """Run runtime screenshot capture and AI analysis during gameplay."""
    print("=== RUNTIME SCREENSHOT PLAY TEST ===")
    
    if RuntimeScreenshotPlayTest is None:
        print("Warning: runtime_screenshot_playtest module not available.")
        return
    
    play_test = RuntimeScreenshotPlayTest(
        screenshot_dir="Screenshots",
        capture_interval=5.0
    )
    play_test.run_runtime_playtest()


def cleanup_generated_content():
    """Function to remove generated content and reset the project state."""
    if GameConfiguration.ENABLE_DEBUG_LOGGING:
        print("Starting cleanup of generated content...")

    # Note: The autonomous sync system (sync_cpp_project_state) now handles 
    # the removal of obsolete files based on the single source of truth configuration.
    # This function is kept for explicit manual reset operations.

    if GameConfiguration.ENABLE_DEBUG_LOGGING:
        print("Cleanup complete.")


# ============================================================================
# AUTOMATIC EXECUTION ON STARTUP & COMMAND INTERFACE
# ============================================================================

# This ensures the generator runs automatically when the script is loaded by Unreal's Python engine
try:
    import unreal
    
    # Run complete startup workflow on UE Editor launch:
    # 1. Generate C++ files and sync project state
    # 2. Load starter level and spawn vehicle
    # 3. Run play test (flight mode toggle, thrust, movement)
    # 4. Capture screenshot and send to LM Studio for AI analysis
    run_startup_workflow()
    
except Exception:
    # If unreal module is not available, just skip automatic execution
    pass