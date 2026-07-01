"""
workflow_ai_deployment.py — AI Deployment Workflow

Spawns AI controllers in designated areas, assigns behavior trees and patrol routes,
configures perception ranges and alert levels, and validates AI placement coverage.

Usage (UE Editor): from workflow_ai_deployment import run_ai_deployment_workflow; run_ai_deployment_workflow()
Usage (standalone): python workflow_ai_deployment.py --areas 12 --perception 500 --alert cautious
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


CTRL_TYPES = {
    "patrol": {"class_path": "/Game/AI/AC_Patrol.ACPatrol_C", "behavior_tree": "patrol"},
    "guard": {"class_path": "/Game/AI/AC_Guard.ACGuard_C", "behavior_tree": "guard"},
    "ambush": {"class_path": "/Game/AI/AC_Ambush.ACAmbush_C", "behavior_tree": "ambush"},
}

BEHAVIOR_TREES = {
    "patrol": {"path": "/Game/AI/BT_Patrol.BT_Patrol", "tick_interval": 1.0},
    "guard": {"path": "/Game/AI/BT_Guard.BT_Guard", "tick_interval": 0.5},
    "chase": {"path": "/Game/AI/BT_Chase.BT_Chase", "tick_interval": 0.25},
    "ambush": {"path": "/Game/AI/BT_Ambush.BT_Ambush", "tick_interval": 2.0},
}

ALERT_LEVELS = {
    "passive": {"perception_radius": 100.0, "detection_time": 5.0, "attack_range": 0.0, "flee_chance": 0.0, "sound_hearing_range": 200.0},
    "cautious": {"perception_radius": 300.0, "detection_time": 2.0, "attack_range": 50.0, "flee_chance": 0.1, "sound_hearing_range": 400.0},
    "aggressive": {"perception_radius": 600.0, "detection_time": 0.5, "attack_range": 200.0, "flee_chance": 0.0, "sound_hearing_range": 800.0},
}

PATROL_POINTS = [
    {"name": "PatrolWaypoint_01", "offset_range": (200.0, 500.0)},
    {"name": "PatrolWaypoint_02", "offset_range": (300.0, 600.0)},
    {"name": "PatrolWaypoint_03", "offset_range": (150.0, 400.0)},
    {"name": "PatrolWaypoint_04", "offset_range": (250.0, 700.0)},
]


def spawn_ai_controllers(area_count: int, seed: int) -> list[dict]:
    random.seed(seed)
    controllers = []
    types = list(CTRL_TYPES.keys())
    weights = [0.5, 0.3, 0.2]
    for i in range(area_count):
        type_idx = random.choices([0, 1, 2], weights=weights)[0]
        ctrl_type = types[type_idx]
        zone_size = 800.0
        x = (i % 3) * zone_size + random.uniform(-zone_size*0.2, zone_size*0.2)
        y = (i // 3) * zone_size + random.uniform(-zone_size*0.2, zone_size*0.2)
        controllers.append({
            "controller_id": f"ai_ctrl_{seed:04d}_{i}",
            "type": ctrl_type,
            "class_path": CTRL_TYPES[ctrl_type]["class_path"],
            "position": {"x": x, "y": y, "z": 0.0},
            "area_id": f"deploy_area_{i % max(area_count//3, 1)}",
        })
    return controllers


def assign_behavior_trees(controllers: list[dict]) -> list[dict]:
    for ctrl in controllers:
        bt_key = CTRL_TYPES[ctrl["type"]]["behavior_tree"]
        bt = BEHAVIOR_TREES.get(bt_key, {"path": "/Game/AI/BT_Default.BT_Default", "tick_interval": 1.0})
        ctrl["behavior_tree"] = {"path": bt["path"], "tick_interval": bt["tick_interval"]}
        if ctrl["type"] == "patrol":
            base_x, base_y = ctrl["position"]["x"], ctrl["position"]["y"]
            route = []
            for pt in PATROL_POINTS:
                rng = pt["offset_range"]
                route.append({"name": f"{pt['name']}_for_{ctrl['controller_id']}",
                              "position": {"x": base_x + random.uniform(*rng),
                                           "y": base_y + random.uniform(*rng), "z": 0.0}})
            ctrl["patrol_route"] = route
    return controllers


def configure_perception(controllers: list[dict], alert_level: str, perception_override: float = None) -> list[dict]:
    cfg = ALERT_LEVELS.get(alert_level, ALERT_LEVELS["cautious"])
    for ctrl in controllers:
        config = dict(cfg)
        if perception_override is not None:
            config["perception_radius"] = perception_override
        ctrl["perception_config"] = {
            "alert_level": alert_level,
            "vision_radius": config.get("perception_radius", cfg["perception_radius"]),
            "detection_time": config["detection_time"],
            "attack_range": config["attack_range"],
            "flee_chance": config["flee_chance"],
            "sound_hearing_range": config["sound_hearing_range"],
        }
    return controllers


def validate_ai_coverage(controllers: list[dict], area_count: int) -> dict:
    area_counts = {}
    for ctrl in controllers:
        area_id = ctrl["area_id"]
        area_counts[area_id] = area_counts.get(area_id, 0) + 1
    expected = set(f"deploy_area_{i}" for i in range(max(area_count//3, 1)))
    missing = expected - set(area_counts.keys())
    errors, warnings = [], []
    if missing:
        errors.append(f"Areas without coverage: {', '.join(missing)}")
    for aid, cnt in area_counts.items():
        if cnt > 5:
            warnings.append(f"High density in '{aid}': {cnt} controllers")
    no_route = sum(1 for c in controllers if c["type"] == "patrol" and not c.get("patrol_route"))
    if no_route > 0:
        errors.append(f"{no_route} patrol controllers missing routes")
    return {
        "valid": len(errors) == 0,
        "errors": errors, "warnings": warnings,
        "coverage_stats": {"total_controllers": len(controllers), "areas_covered": len(area_counts),
                           "expected_areas": max(area_count//3, 1),
                           "min_per_area": min(area_counts.values()) if area_counts else 0,
                           "max_per_area": max(area_counts.values()) if area_counts else 0},
    }


def _simulate(area_count: int, perception_range: float, alert_level: str) -> dict:
    seed = GameConfiguration.GENERATION_SEED
    controllers = spawn_ai_controllers(area_count, seed)
    controllers = assign_behavior_trees(controllers)
    controllers = configure_perception(controllers, alert_level, perception_range)
    validation = validate_ai_coverage(controllers, area_count)
    output_dir = CHIMERA_CONTENT_DIR / "ProceduralGenerated" / "AI"
    os.makedirs(output_dir, exist_ok=True)
    spec_path = output_dir / f"ai_deployment_{alert_level}_{seed}.json"
    with open(spec_path, 'w') as f:
        json.dump({"area_count": area_count, "perception_range_override": perception_range,
                    "alert_level": alert_level, "controllers": controllers, "validation": validation}, f, indent=2)
    print(f"[SIM] Spec saved to: {spec_path}")
    return {"area_count": area_count}


def run_ai_deployment_workflow(area_count=8, perception_range=None, alert_level="cautious"):
    seed = GameConfiguration.GENERATION_SEED
    print("=" * 60); print("AI DEPLOYMENT WORKFLOW"); print("=" * 60)
    print(f"Areas: {area_count} | Perception: {perception_range or 'default'} | Alert: {alert_level}")
    try:
        import unreal
        controllers = spawn_ai_controllers(area_count, seed)
        print(f"\n[STEP 1] Spawned {len(controllers)} AI controllers"); print("[OK]")
        controllers = assign_behavior_trees(controllers)
        bt_types = set(c.get("behavior_tree", {}).get("path", "") for c in controllers)
        print(f"[STEP 2] Assigned {len(bt_types)} behavior tree configs"); print("[OK]")
        controllers = configure_perception(controllers, alert_level, perception_range)
        print(f"[STEP 3] Alert level '{alert_level}' applied to all controllers"); print("[OK]")
        validation = validate_ai_coverage(controllers, area_count)
        stats = validation.get("coverage_stats", {})
        covered = stats.get('areas_covered', 0)
        expected = stats.get('expected_areas', 0)
        print(f"\n[STEP 4] Coverage — {'PASS' if validation['valid'] else 'ISSUES'} ({covered}/{expected} areas)")
        for w in validation["warnings"]:
            print(f"[WARN] {w}")
    except ImportError:
        print("[WARN] unreal module not available — simulation mode")
        _simulate(area_count, perception_range or 300.0, alert_level)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Deployment Workflow")
    parser.add_argument("--areas", type=int, default=8)
    parser.add_argument("--perception", type=float, default=None)
    parser.add_argument("--alert", type=str, default="cautious", choices=["passive", "cautious", "aggressive"])
    args = parser.parse_args()
    run_ai_deployment_workflow(area_count=args.areas, perception_range=args.perception, alert_level=args.alert)
