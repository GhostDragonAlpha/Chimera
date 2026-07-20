"""Decode a trained genome into real UE5 game artifacts.

Takes a genome dict (from any trainable domain) and applies it to the live game
via MCP bridge, config writes, or beat generation.

The decoder IS the phenotype expression — same role as game_code_generator.py
but driven by trained genomes instead of DSL specs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def decode_erisaid_mirror(genome: dict) -> dict:
    """Decode the Erisaid mirror genome into MCP-spawnable configuration.

    Returns a dict of MCP commands that would realize this mirror config
    in the live level.
    """
    g = genome
    n_total = g["n_stars"] + g["n_pains"] + g["n_sacrifices"] + g["n_calls"]

    commands = []

    # 1. Spawn reflection points around the Erisaid at golden-angle bearings
    import math
    GA = math.radians(137.50776405003785)

    for i in range(n_total):
        bearing = (GA * i * g["bearing_spread"]) % (2 * math.pi)
        dist = 8.0  # reflection points hover 8m from shell center

        x = math.cos(bearing) * dist
        y = math.sin(bearing) * dist
        z = 150 + (i % 3) * 40  # stagger heights

        # Determine reflection type and brightness
        if i < g["n_stars"]:
            ref_type = "star"
            brightness = 1.0 - math.exp(-5.0 / max(0.001, g["brightness_k"]))
        elif i < g["n_stars"] + g["n_pains"]:
            ref_type = "pain"
            brightness = 0.2
        elif i < g["n_stars"] + g["n_pains"] + g["n_sacrifices"]:
            ref_type = "sacrifice"
            brightness = 1.0 - math.exp(-2.0 / max(0.001, g["brightness_k"]))
        else:
            ref_type = "call"
            brightness = 0.5

        if brightness < g["min_brightness_visible"]:
            continue  # too dim to spawn

        commands.append({
            "tool": "control_actor",
            "action": "spawn_actor",
            "name": f"Mirror_Reflection_{ref_type}_{i}",
            "classPath": "/Game/Chimera/Verbs/BP_Verb_PickUp.BP_Verb_PickUp",
            "x": x, "y": y, "z": z,
            "meta": {
                "reflection_type": ref_type,
                "brightness": round(brightness, 3),
                "bearing_deg": round(math.degrees(bearing), 1),
                "zone": "touching" if dist < g["zone_near"] else
                        "near" if dist < g["zone_approaching"] else
                        "approaching" if dist < g["zone_distant"] else "distant",
            },
        })

    # 2. Configure proximity zone thresholds (written to a config or console variable)
    commands.append({
        "tool": "config",
        "action": "write",
        "section": "Erisaid",
        "keys": {
            "ZoneDistant": g["zone_distant"],
            "ZoneApproaching": g["zone_approaching"],
            "ZoneNear": g["zone_near"],
            "BrightnessK": g["brightness_k"],
            "MinBrightnessVisible": g["min_brightness_visible"],
            "BearingSpread": g["bearing_spread"],
            "SelfReflectionScale": g["self_reflection_brightness_scale"],
        },
    })

    return {
        "domain": "erisaid_mirror",
        "reflections_spawned": len([c for c in commands if c.get("tool") == "control_actor"]),
        "config_keys": len([c for c in commands if c.get("tool") == "config"]),
        "commands": commands,
    }



def decode_npc_behavior(genome: dict) -> dict:
    g = genome
    commands = [
        {"tool": "console", "action": "set", "name": "ai.npc.ApproachRadius", "value": g["approach_radius"]},
        {"tool": "console", "action": "set", "name": "ai.npc.InteractRadius", "value": g["interact_radius"]},
        {"tool": "console", "action": "set", "name": "ai.npc.ReciprocityStrength", "value": g["reciprocity_strength"]},
        {"tool": "console", "action": "set", "name": "ai.npc.PirateAggression", "value": g["pirate_aggression"]},
        {"tool": "console", "action": "set", "name": "ai.npc.TraderGenerosity", "value": g["trader_generosity"]},
    ]
    for role, affinities in g.get("role_affinity", {}).items():
        for gesture, val in affinities.items():
            commands.append({"tool": "config", "action": "write", "section": f"NPC.Roles.{role}", "keys": {gesture: val}})
    return {"domain": "npc_behavior", "commands": commands}


def decode_economy_engine(genome: dict) -> dict:
    g = genome
    commands = [
        {"tool": "console", "action": "set", "name": "econ.SupplyElasticity", "value": g["supply_elasticity"]},
        {"tool": "console", "action": "set", "name": "econ.DemandElasticity", "value": g["demand_elasticity"]},
        {"tool": "console", "action": "set", "name": "econ.ArbitrageThreshold", "value": g["arbitrage_threshold"]},
        {"tool": "console", "action": "set", "name": "econ.Volatility", "value": g["volatility"]},
    ]
    return {"domain": "economy_engine", "commands": commands, "console_vars": 4}

def apply_genome(genome: dict, domain: str, dry_run: bool = True) -> dict:
    """Apply a trained genome to the live game.

    Args:
        genome: Trained genome dict
        domain: Domain name (must have a decode_<domain> function)
        dry_run: If True, return commands without executing

    Returns:
        Result dict with spawned_count, errors, commands
    """
    decoders = {
        "erisaid_mirror": decode_erisaid_mirror,
        "npc_behavior": decode_npc_behavior,
        "economy_engine": decode_economy_engine,
    }

    decoder = decoders.get(domain)
    if not decoder:
        return {"error": f"No decoder for domain '{domain}'. Available: {list(decoders.keys())}"}

    decoded = decoder(genome)

    if dry_run:
        return {"dry_run": True, "decoded": decoded}

    # Live application via MCP
    try:
        from core.telemetry_probe import MCPStdioClient
        mcp = MCPStdioClient()
    except Exception as e:
        return {"error": f"MCP not available: {e}", "decoded": decoded}

    results = []
    for cmd in decoded.get("commands", []):
        tool = cmd.get("tool")
        if tool != "control_actor":
            results.append({"cmd": cmd, "status": "skipped", "reason": f"tool {tool} not implemented for live apply"})
            continue

        try:
            r = mcp.call(tool, {
                "action": cmd["action"],
                "name": cmd["name"],
                "classPath": cmd.get("classPath", ""),
                "x": cmd.get("x", 0),
                "y": cmd.get("y", 0),
                "z": cmd.get("z", 130),
            })
            ok = r.get("result", {}).get("structuredContent", {}).get("success", False)
            results.append({"cmd": cmd, "status": "ok" if ok else "failed", "response": str(r)[:200]})
        except Exception as e:
            results.append({"cmd": cmd, "status": "error", "reason": str(e)})

    return {
        "domain": domain,
        "applied": sum(1 for r in results if r["status"] == "ok"),
        "failed": sum(1 for r in results if r["status"] != "ok"),
        "results": results,
    }


def decode_to_beat(genome: dict, domain: str, feature_name: str = "DecodedFeature") -> dict:
    """Decode a genome into a sleepwalker beat script.

    The beat exercises the feature the genome was trained for, producing
    a verifiable simtest.
    """
    
    if domain == "beat_generator":
        beats = []
        for i, beat in enumerate(genome.get("beats", [])[:4]):
            actions = []
            for a in beat.get("action_mix", ["wait"])[:beat.get("n_actions", 2)]:
                if a == "reset_position": actions.append({"reset_position": {"x": (i+1)*200, "y": 0, "z": 130}})
                elif a == "interact": actions.append({"interact": True, "hold_s": 1.0})
                elif a == "drop": actions.append({"drop": True, "hold_s": 1.0})
                elif a == "screenshot": actions.append({"screenshot": f"beat_{i}"})
                else: actions.append({"wait": 0.5})
            expects = []
            for e in beat.get("expect_mix", ["is_pie"])[:beat.get("n_expects", 3)]:
                if e == "is_pie": expects.append({"is_pie": True})
                elif e == "actor_exists": expects.append({"actor_exists": "Player_Astronaut"})
                elif e == "log_contains": expects.append({"log_contains": "GAMEMODE"})
                elif e == "pawn_class": expects.append({"pawn_class": "BP_Astronaut_Character_C"})
            beats.append({
                "name": f"trained_beat_{i}",
                "features": beat.get("features_tagged", ["Verb_Look"])[:2],
                "actions": actions,
                "expects": expects,
            })
        return {"demo": "beat_generator_trained", "loop": 0, "settle_s": genome.get("beats",[{}])[0].get("settle_s",4), "beats": beats}

    if domain == "erisaid_mirror":
        g = genome
        return {
            "demo": "erisaid_mirror_decoded",
            "loop": 0,
            "settle_s": 4,
            "_provenance": f"Decoded from trained erisaid_mirror genome (k={g['brightness_k']:.2f}, reflections={g['n_stars']+g['n_pains']+g['n_sacrifices']+g['n_calls']})",
            "beats": [
                {
                    "name": "mirror_proximity_test",
                    "features": [feature_name],
                    "actions": [
                        {"reset_position": {"x": g["zone_distant"] + 5, "y": 0, "z": 130}},
                        {"wait": 1.0},
                        {"reset_position": {"x": g["zone_approaching"] - 2, "y": 0, "z": 130}},
                        {"wait": 0.5},
                        {"reset_position": {"x": g["zone_near"] - 1, "y": 0, "z": 130}},
                        {"wait": 0.5},
                        {"reset_position": {"x": 1, "y": 0, "z": 130}},
                        {"wait": 0.5},
                        {"interact": True, "hold_s": 1.0},
                        {"screenshot": "erisaid_mirror_decoded"},
                    ],
                    "expects": [
                        {"is_pie": True},
                        {"log_contains": "Interact action triggered"},
                    ],
                }
            ],
        }
    return {"error": f"No beat decoder for domain '{domain}'"}


# CLI
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python decoder.py <genome.json> [--apply] [--domain erisaid_mirror]")
        print("       python decoder.py --beat <genome.json>")
        sys.exit(1)

    if sys.argv[1] == "--beat":
        genome = json.loads(Path(sys.argv[2]).read_text())
        beat = decode_to_beat(genome, "erisaid_mirror")
        print(json.dumps(beat, indent=2))
        sys.exit(0)

    genome_path = Path(sys.argv[1])
    genome = json.loads(genome_path.read_text())
    domain = "erisaid_mirror"
    apply = "--apply" in sys.argv

    result = apply_genome(genome, domain, dry_run=not apply)
    print(json.dumps(result, indent=2))
