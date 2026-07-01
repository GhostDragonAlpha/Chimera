"""
workflow_vehicle_setup.py — Vehicle Configuration Workflow v2

Spawns vehicles from templates, applies part upgrades (engine, suspension, tires),
configures performance settings with tuning presets, and registers with race manager.

Usage (UE Editor): from workflows.workflow_vehicle_setup import run_vehicle_setup; run_vehicle_setup()
Usage (standalone): python -m workflows.workflow_vehicle_setup --template sports --upgrade engine,suspension --race True
"""

import os, sys, json, argparse, random
from pathlib import Path

try:
    from config import CHIMERA_CONTENT_DIR, GameConfiguration
except ImportError:
    CHIMERA_CONTENT_DIR = Path(r"E:\PythonChimera\Chimera\Content")
    class _GC:
        GENERATION_SEED = 42
    GameConfiguration = _GC


TEMPLATES = {
    "offroad": {"path": "/Game/Vehicles/OffroadCar/BP_OffroadCar.BP_OffroadCar_C", "spawn": (0, 0, 0),
                "chassis_height": 144.0, "drag": 0.35, "weight_kg": 1800},
    "sports": {"path": "/Game/Vehicles/SportsCar/BP_SportsCar.BP_SportsCar_C", "spawn": (300, 0, 0),
               "chassis_height": 120.0, "drag": 0.31, "weight_kg": 1400},
    "flight": {"path": "/Game/FlightVehicle/BP_FlightVehicle.BP_FlightVehicle_C", "spawn": (600, 0, 0),
               "chassis_height": 0.0, "drag": 0.15, "weight_kg": 2200},
}

UPGRADES = {
    "engine": {"stat_mods": {"max_rpm": 8500, "torque_multiplier": 1.3}, "power_increase": 20.0},
    "suspension": {"stat_mods": {"spring_rate": 1.4, "damping_ratio": 0.7}, "ride_quality_improvement": 15.0},
    "tires": {"stat_mods": {"friction_bias": 1.2, "lateral_stiffness": 1.3}, "grip_increase": 12.0},
    "aerodynamics": {"stat_mods": {"drag_coefficient_reduction": 0.85, "downforce_multiplier": 1.5}, "speed_bonus": 8.0},
    "transmission": {"stat_mods": {"gear_ratios_optimized": True, "shift_time_reduction": 0.6}, "acceleration_improvement": 10.0},
}

TUNING_PRESETS = {
    "balanced": {"power_factor": 1.0, "handling_factor": 1.0, "braking_factor": 1.0},
    "race": {"power_factor": 1.5, "handling_factor": 1.2, "braking_factor": 1.3},
    "drift": {"power_factor": 1.2, "handling_factor": 0.8, "braking_factor": 0.9},
}

RACE_CATEGORIES = {"offroad": "OffRoad", "sports": "Sports", "flight": "Exhibition"}


def spawn_vehicle(template_name: str, seed: int) -> dict:
    cfg = TEMPLATES.get(template_name, TEMPLATES["offroad"])
    random.seed(seed)
    loc = cfg["spawn"]
    jitter = lambda v: v + random.uniform(-50, 50)
    return {
        "vehicle_id": f"veh_{template_name}_{seed}",
        "template_path": cfg["path"],
        "transform": {"location": {"x": jitter(loc[0]), "y": jitter(loc[1]), "z": loc[2]},
                      "rotation": {"yaw": random.uniform(-5, 5)}},
        "base_stats": {
            "chassis_height": cfg["chassis_height"], "drag_coefficient": cfg["drag"],
            "weight_kg": cfg["weight_kg"],
        },
    }


def apply_part_upgrades(vehicle: dict, upgrade_types: list[str]) -> dict:
    current = dict(vehicle)
    current["upgrades_applied"] = []
    current["modified_stats"] = {}
    for key in upgrade_types:
        if key not in UPGRADES:
            print(f"[WARN] Unknown upgrade: {key}")
            continue
        upg = UPGRADES[key]
        current["upgrades_applied"].append(key)
        for stat_key, val in upg["stat_mods"].items():
            if isinstance(val, (int, float)):
                current["modified_stats"][stat_key] = val
    return current


def configure_performance(vehicle: dict, tuning_preset: str = "balanced", racing_mode: bool = False) -> dict:
    preset = TUNING_PRESETS.get(tuning_preset, TUNING_PRESETS["balanced"])
    total_power = sum(UPGRADES[k].get("power_increase", 0) for k in vehicle.get("upgrades_applied", []) if k in UPGRADES)
    current = dict(vehicle)
    current["performance_config"] = {
        "racing_mode": racing_mode,
        "tuning_preset": tuning_preset,
        "physics_tuning": {
            "total_power_bonus": round(total_power, 1),
            "power_factor": preset["power_factor"],
            "handling_factor": preset["handling_factor"],
            "braking_factor": preset["braking_factor"],
            "tire_pressure_boost": 1.1 if racing_mode else 1.0,
            "engine_remap": racing_mode,
        },
        "ai_behavior": "aggressive" if racing_mode else "passive",
    }
    return current


def register_race_manager(vehicle: dict, template_name: str) -> dict:
    category = RACE_CATEGORIES.get(template_name, "Exhibition")
    reg = {"vehicle_id": vehicle["vehicle_id"], "category": category,
           "race_class": "RC_Champion", "registered": True}
    print(f"[OK] Registered '{vehicle['vehicle_id']}' in category '{category}'")
    return reg


def _simulate(template_name: str, upgrades: list[str], tuning_preset: str, racing_mode: bool) -> dict:
    seed = GameConfiguration.GENERATION_SEED
    vehicle = spawn_vehicle(template_name, seed)
    vehicle = apply_part_upgrades(vehicle, upgrades)
    vehicle = configure_performance(vehicle, tuning_preset, racing_mode)
    if racing_mode:
        vehicle["registration"] = register_race_manager(vehicle, template_name)
    output_dir = CHIMERA_CONTENT_DIR / "ProceduralGenerated" / "Vehicles"
    os.makedirs(output_dir, exist_ok=True)
    spec_path = output_dir / f"vehicle_setup_v2_{template_name}_{seed}.json"
    with open(spec_path, 'w') as f:
        json.dump(vehicle, f, indent=2)
    print(f"[SIM] Spec saved to: {spec_path}")
    return vehicle


def run_vehicle_setup(template="offroad", upgrades=None, tuning_preset="balanced", racing_mode=False):
    seed = GameConfiguration.GENERATION_SEED
    print("=" * 60); print("VEHICLE SETUP WORKFLOW v2"); print("=" * 60)
    print(f"Template: {template} | Upgrades: {upgrades or 'all'} | Preset: {tuning_preset} | Race: {racing_mode}")
    try:
        import unreal
        vehicle = spawn_vehicle(template, seed)
        print(f"\n[STEP 1] Spawned '{vehicle['vehicle_id']}' at {vehicle['transform']['location']}"); print("[OK]")
        upgrade_types = upgrades or list(UPGRADES.keys())
        vehicle = apply_part_upgrades(vehicle, upgrade_types)
        print(f"[STEP 2] Applied {len(upgrade_types)} part upgrades"); print("[OK]")
        vehicle = configure_performance(vehicle, tuning_preset, racing_mode)
        print(f"[STEP 3] Performance configured (preset={tuning_preset}, racing={racing_mode})"); print("[OK]")
        if racing_mode:
            register_race_manager(vehicle, template)
            print("[STEP 4] Registered with race manager")
    except ImportError:
        print("[WARN] unreal module not available — simulation mode")
        _simulate(template, upgrades or list(UPGRADES.keys()), tuning_preset, racing_mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vehicle Configuration Workflow v2")
    parser.add_argument("--template", type=str, default="offroad", choices=list(TEMPLATES.keys()))
    parser.add_argument("--upgrade", type=str, nargs="+", default=None, choices=list(UPGRADES.keys()))
    parser.add_argument("--preset", type=str, default="balanced", choices=list(TUNING_PRESETS.keys()))
    parser.add_argument("--race", action="store_true", dest="racing_mode")
    args = parser.parse_args()
    run_vehicle_setup(template=args.template, upgrades=args.upgrade, tuning_preset=args.preset, racing_mode=args.racing_mode)
