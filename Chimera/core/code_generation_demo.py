"""
Code Generation Demo — Example usage of the Code Generation Orchestrator.

This script demonstrates how to use the CodeGenerationOrchestrator to:
1. Generate or repair C++ code based on natural language descriptions
2. Generate Blueprint design descriptions
3. Save generated code to files

Usage:
    python core/code_generation_demo.py
"""

import sys
from pathlib import Path

# Ensure UTF-8 encoding for stdout
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Fix import for CWD-independent execution
try:
    from core.code_generation_orchestrator import CodeGenerationOrchestrator
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.code_generation_orchestrator import CodeGenerationOrchestrator


def main():
    """Run the Code Generation Demo."""
    print("=" * 72)
    print("Code Generation Demo — Generating C++ and Blueprint designs")
    print("=" * 72)

    orchestrator = CodeGenerationOrchestrator()

    # Example 1: Generate a character class
    print("\n" + "-" * 72)
    print("[1] Generating C++ Character Class: 'SM_Astronaut'")
    print("-" * 72)

    character_result = orchestrator.generate_character_class(
        class_name="SM_Astronaut",
        parent_class="ACharacter",
        description=(
            "A space-faring astronaut character for the Chimera deep-space trading game. "
            "Features an EVA suit with gold visor, jetpack, and basic locomotion animations. "
            "Must have a spring-arm camera that follows the player, with standard movement input "
            "for WASD movement and mouse look."
        ),
        movement_components=[
            "CharacterMovementComponent with max walk speed 600 cm/s",
            "SpringArmComponent with 300 cm arm length, camera lag enabled",
            "CameraComponent attached to spring arm",
        ],
        animations=[
            "Idle animation loop",
            "Walk/Run blendspace based on speed",
            "Jump animation with anticipation and landing",
        ],
    )
    print(f"  Generated: {character_result}")
    print(f"  Files: {orchestrator.last_generated_files}")

    # Example 2: Generate a spaceship class
    print("\n" + "-" * 72)
    print("[2] Generating C++ Ship Class: 'AShipBase'")
    print("-" * 72)

    ship_result = orchestrator.generate_ship_class(
        class_name="AShipBase",
        ship_type="Freighter",
        description=(
            "A mid-size cargo freighter with QuantumDrive, ShieldGenerator, and CargoHold components. "
            "Supports basic flight physics with roll, pitch, yaw, and thrust controls. "
            "Interior has a cockpit, cargo bay, and airlock. "
            "Can dock with stations and other ships via DockingComponent."
        ),
        systems=[
            "Flight dynamics: max speed 8000 cm/s, acceleration 2000 cm/s², mass 50000 kg",
            "QuantumDrive: jump range 25 LY, cooldown 60 seconds, requires fuel",
            "ShieldGenerator: max shield 1000 HP, regen 50 HP/s, delay 5 seconds after hit",
            "CargoHold: 100 slots, supports standard containers (1m³ each)",
            "DockingComponent: proximity-based, 500 cm range, 10-second docking sequence",
        ],
        interior_rooms=["Cockpit", "Cargo Bay", "Airlock", "Crew Quarters"],
    )
    print(f"  Generated: {ship_result}")
    print(f"  Files: {orchestrator.last_generated_files}")

    # Example 3: Generate a station blueprint design
    print("\n" + "-" * 72)
    print("[3] Generating Station Blueprint Design: 'TitanTradeHub'")
    print("-" * 72)

    station_result = orchestrator.generate_blueprint_design(
        actor_name="BP_TitanTradeHub",
        actor_type="Station",
        description=(
            "A bustling deep-space trading station orbiting Titan. "
            "Features a main concourse with 12 docking bays, a market area with 12 NPC traders, "
            "a mission board with dynamic contracts, and a refueling depot. "
            "Interior lighting is warm and inviting, with large windows showing Saturn's rings. "
            "Components: TradeCenter, MissionBoard, RefuelingDepot, DockingSystem, LightingControl."
        ),
        components=[
            "TradeCenter component with EconomyManager reference",
            "MissionBoard component with dynamic mission generation",
            "RefuelingDepot with fuel pricing based on local supply/demand",
            "DockingSystem with 12 physical docking bay markers",
            "LightingControl for day/night cycle simulation",
            "AudioManager for ambient station sounds (hum, announcements, docking clamps)",
        ],
        interior_style="Sci-fi realistic with warm ambient lighting, metal panels, and holographic displays",
    )
    print(f"  Generated Blueprint Design: {station_result}")

    # Example 4: Generate code from natural language description
    print("\n" + "-" * 72)
    print("[4] Natural Language Code Generation: Cargo Scanner Component")
    print("-" * 72)

    nl_result = orchestrator.generate_from_description(
        description=(
            "Create a UCargoScannerComponent that can be attached to ships and stations. "
            "When activated, it scans nearby cargo containers within a configurable range (default 500m) "
            "and returns a list of scanned items with their contents, mass, and value. "
            "Higher scanner levels increase range and reduce scan time. "
            "Base scanning range: 100m, Level 2: 250m, Level 3: 500m. "
            "Scan time: 3 seconds base, Level 2: 2s, Level 3: 1s. "
            "Should have a visual scanning effect (Niagara particle system)."
        ),
        preferred_pattern="Observer + Strategy for scanner levels",
    )
    print(f"  Generated Component: {nl_result}")

    # Summary
    print("\n" + "=" * 72)
    print("Demo Complete!")
    print("=" * 72)
    print(f"\nTotal generations: 4")
    print(f"Check orchestrator.last_generated_files for full file list.")
    print(f"\nNote: This is a demonstration of code generation capabilities.")
    print(f"Generated files are written to the Chimera/Source directory.")


if __name__ == "__main__":
    main()