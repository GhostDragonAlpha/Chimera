"""
Input Binding Generator — Creates Enhanced Input Action bindings for flight controls.
Generates Blueprint-compatible configuration files for UE Editor integration.
"""

import os


def generate_input_bindings():
    """Generate input action definitions for all flight controls."""
    
    print("=" * 60)
    print("INPUT BINDING GENERATOR")
    print("=" * 60)
    
    # Define all input actions needed for flight mode
    input_actions = [
        {
            "name": "ThrustForward",
            "category": "Flight|Movement",
            "description": "Apply forward thrust (W key)",
            "key": "W"
        },
        {
            "name": "ThrustReverse", 
            "category": "Flight|Movement",
            "description": "Apply reverse thrust (S key)",
            "key": "S"
        },
        {
            "name": "StrafeLeft",
            "category": "Flight|Movement",
            "description": "Strafe left (A key)",
            "key": "A"
        },
        {
            "name": "StrafeRight",
            "category": "Flight|Movement",
            "description": "Strafe right (D key)",
            "key": "D"
        },
        {
            "name": "StrafeUp",
            "category": "Flight|Movement",
            "description": "Strafe up (Q key)",
            "key": "Q"
        },
        {
            "name": "StrafeDown",
            "category": "Flight|Movement",
            "description": "Strafe down (E key)",
            "key": "E"
        },
        {
            "name": "PitchUp",
            "category": "Flight|Rotation",
            "description": "Pitch up (Mouse Y negative)",
            "key": "MouseY_Negative"
        },
        {
            "name": "PitchDown",
            "category": "Flight|Rotation",
            "description": "Pitch down (Mouse Y positive)",
            "key": "MouseY_Positive"
        },
        {
            "name": "YawLeft",
            "category": "Flight|Rotation",
            "description": "Yaw left (Mouse X negative)",
            "key": "MouseX_Negative"
        },
        {
            "name": "YawRight",
            "category": "Flight|Rotation",
            "description": "Yaw right (Mouse X positive)",
            "key": "MouseX_Positive"
        },
        {
            "name": "RollLeft",
            "category": "Flight|Rotation",
            "description": "Roll left (Q/E modifier)",
            "key": "Q"
        },
        {
            "name": "RollRight",
            "category": "Flight|Rotation",
            "description": "Roll right (Shift/Alt modifier)",
            "key": "R"
        },
        {
            "name": "ToggleFlightMode",
            "category": "Flight|System",
            "description": "Toggle flight mode on/off (F key)",
            "key": "F"
        }
    ]
    
    print("\n[STEP 1] Generating input action definitions...")
    
    # Generate C++ header for input actions
    source_dir = r"E:\PythonChimera\Chimera\Source\Chimera"
    input_actions_header = '''// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/ConstructorReference.h"
#include "FlightInputActions.generated.h"

/**
 * Input action definitions for flight controls.
 * These actions are bound in the Enhanced Input System.
 */
UENUM(BlueprintType)
enum class EFlightAction : uint8
{
    // Movement
    ThrustForward UMETA(DisplayName = "Thrust Forward"),
    ThrustReverse UMETA(DisplayName = "Thrust Reverse"),
    StrafeLeft UMETA(DisplayName = "Strafe Left"),
    StrafeRight UMETA(DisplayName = "Strafe Right"),
    StrafeUp UMETA(DisplayName = "Strafe Up"),
    StrafeDown UMETA(DisplayName = "Strafe Down"),
    
    // Rotation
    PitchUp UMETA(DisplayName = "Pitch Up"),
    PitchDown UMETA(DisplayName = "Pitch Down"),
    YawLeft UMETA(DisplayName = "Yaw Left"),
    YawRight UMETA(DisplayName = "Yaw Right"),
    RollLeft UMETA(DisplayName = "Roll Left"),
    RollRight UMETA(DisplayName = "Roll Right"),
    
    // System
    ToggleFlightMode UMETA(DisplayName = "Toggle Flight Mode")
};

'''
    
    input_actions_path = os.path.join(source_dir, "FlightInputActions.h")
    with open(input_actions_path, 'w', encoding='utf-8') as f:
        f.write(input_actions_header)
    
    print(f"  [OK] Generated FlightInputActions.h")
    
    # Generate input binding configuration (JSON format for UE Editor)
    print("\n[STEP 2] Generating input binding configuration...")
    
    config = {
        "class": "UInputSettings",
        "properties": {
            "ActionMappings": []
        }
    }
    
    for action in input_actions:
        mapping = {
            "actionName": f"IA_{action['name']}",
            "key": action["key"],
            "bShift": False,
            "bCtrl": False,
            "bAlt": False,
            "bCmd": False
        }
        config["properties"]["ActionMappings"].append(mapping)
    
    # Save configuration (for reference/documentation)
    config_path = os.path.join(source_dir, "FlightInputBindings.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(config, f, indent=2)
    
    print(f"  [OK] Generated FlightInputBindings.json")
    
    # Print summary
    print("\n[STEP 3] Input actions generated:")
    for action in input_actions:
        print(f"  - {action['name']}: {action['key']} ({action['description']})")
    
    print("\n" + "=" * 60)
    print("INPUT BINDINGS GENERATED SUCCESSFULLY")
    print("=" * 60)


def run_bindings():
    """Generate all input bindings."""
    generate_input_bindings()


if __name__ == "__main__":
    run_bindings()
