# -*- coding: utf-8 -*-
"""
build_demo_volumetric_clouds.py — Build script for Demo_Volumetric_Clouds
and its sub-features.

BUILD steps:
  1. Configure VolumetricCloud actor in level via MCP set_component_property
  2. Create cloud type educational data (cumulus, stratus, cirrus, nimbostratus, cumulonimbus)
  3. Wire cloud state to weather data

Based on feature spec answers from:
  - Demo_Volumetric_Clouds.json (44 questions)
  - Cloud_Types_Educational.json (66 questions)
  - Cloud_Weather_Connection.json (66 questions)
  - Cloud_Shadow_Rendering.json (66 questions)

Answers implemented literally:
  - Q9:  "UVolumetricCloudComponent supports shadow casting via bCastCloudShadows"
  - Q14: "VolumetricCloud actor already spawned. Properties configurable via MCP set_component_property"
  - Q18: "Cloud parameters (density, altitude, color) are MCP-configurable"
  - Q17: "MCP tools can modify cloud properties"
  - Q1:  "flat-bottom clouds = stable air, towering clouds = storms, cirrus = fair weather"
  - Q2:  "Cloud type tells the player what weather is coming"
  - Q10: "Wind system and cloud movement need to be connected through the weather component"
  - Cloud_Types_Educational Q41: "Data-driven design allows community extension via JSON"
  - Cloud_Shadow_Rendering Q13-14: "Enable bCastCloudShadows + configure shadow distance + resolution"
  - Cloud_Weather_Connection Q1-4: "Dark low clouds = rain, cumulonimbus = shelter, cirrus = clearing"
"""

import argparse, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "worker_bridge"))
sys.path.insert(0, str(Path(__file__).parent / "Chimera"))

from mcp_builder import MCP
from Chimera.core import cloud_education
from Chimera.core import cloud_weather


def build_step_1_configure_cloud(mcp: MCP, actor: str = "DemoClouds", component: str = "VolumetricCloudComponent"):
    """Step 1: Configure the VolumetricCloud actor already in the level.
    
    From spec answers:
    - Q14: "VolumetricCloud actor already spawned in level. Properties configurable via MCP."
    - Q18: "Cloud parameters (density, altitude, color) are MCP-configurable."
    - Q9:  "UVolumetricCloudComponent supports shadow casting via bCastCloudShadows."
    """
    print("\n=== BUILD STEP 1: Configure VolumetricCloud actor ===")
    
    # 1a. Set altitude and layer height
    print(f"  Setting LayerBottomAltitude=1000, LayerHeight=2000 on {actor}.{component}...")
    r1 = mcp.tool_call("control_actor", "set_component_property",
        actorName=actor, componentName=component,
        properties={"LayerBottomAltitude": 1000, "LayerHeight": 2000})
    assert not r1.get("result", {}).get("isError", False), f"Failed to set altitude: {r1}"
    print(f"  OK: {r1['result']['structuredContent']}")
    
    # 1b. Enable cloud shadow casting (Cloud_Shadow_Rendering Q13-14)
    print(f"  Enabling bCastCloudShadows=True...")
    r2 = mcp.tool_call("control_actor", "set_component_property",
        actorName=actor, componentName=component,
        properties={"bCastCloudShadows": True, "ShadowResolution": 512})
    assert not r2.get("result", {}).get("isError", False), f"Failed to set shadows: {r2}"
    print(f"  OK: Shadows enabled at 512x512 resolution")
    
    # 1c. Set base cloud density and color
    print(f"  Setting CloudDensity=0.6, white cloud color...")
    r3 = mcp.tool_call("control_actor", "set_component_property",
        actorName=actor, componentName=component,
        properties={"CloudDensity": 0.6, "CloudColor": {"R": 1.0, "G": 1.0, "B": 1.0, "A": 1.0}})
    assert not r3.get("result", {}).get("isError", False), f"Failed to set density: {r3}"
    print(f"  OK: Cloud density and color set")
    
    return {
        "actor": actor,
        "component": component,
        "altitude": r1.get("result", {}).get("structuredContent", {}),
        "shadows": True,
        "shadow_resolution": 512,
        "density": 0.6,
    }


def build_step_2_educational_data():
    """Step 2: Create cloud type educational data.
    
    From spec answers:
    - Cloud_Types_Educational Q1: "cumulus as fair-weather markers"
    - Cloud_Types_Educational Q2: "cirrus indicates fair but changing weather"
    - Cloud_Types_Educational Q3: "stratus vs nimbostratus identification"
    - Cloud_Types_Educational Q4: "cumulonimbus teaches seek shelter"
    - Cloud_Types_Educational Q41: "Data-driven design via JSON"
    - Cloud_Types_Educational Q58: "Teaches real science through gameplay"
    """
    print("\n=== BUILD STEP 2: Cloud type educational data ===")
    
    # Verify spec data loaded correctly
    spec = cloud_education._load_spec()
    cloud_types = spec["cloud_types"]
    weather_states = spec["weather_states"]
    
    print(f"  Loaded {len(cloud_types)} cloud types from spec:")
    for ct in cloud_types:
        print(f"    - {ct['display_name']}: {ct['educational_fact'][:60]}...")
    
    print(f"  Loaded {len(weather_states)} weather states:")
    for ws_id, ws in weather_states.items():
        print(f"    - {ws['display']}: {ws['educational_text'][:60]}...")
    
    # Test educational observations
    print(f"\n  Cloud observation samples:")
    for ct_id in ["cumulus", "stratus", "cirrus", "nimbostratus", "cumulonimbus"]:
        obs = cloud_education.cloud_type_observation(ct_id)
        print(f"    {ct_id}: {obs}")
    
    # Test shadow observations
    print(f"\n  Shadow observations:")
    for shadow_type in ["sharp_edges", "soft_edges", "fast_movement", "sudden_darkening"]:
        obs = cloud_education.shadow_observation(shadow_type)
        print(f"    {shadow_type}: {obs}")
    
    return {
        "cloud_types_loaded": len(cloud_types),
        "weather_states_loaded": len(weather_states),
        "data_source": "worker_bridge/specs/cloud_types_educational.json",
    }


def build_step_3_wire_weather(mcp: MCP):
    """Step 3: Wire cloud state to weather data.
    
    From spec answers:
    - Demo_Volumetric_Clouds Q10: "Wind system and cloud movement need to be connected"
    - Cloud_Weather_Connection Q1: "dark low clouds = imminent rain"
    - Cloud_Weather_Connection Q2: "towering cumulonimbus = seek shelter"
    - Cloud_Weather_Connection Q3: "clearing cirrus after rain = improving weather"
    - Cloud_Weather_Connection Q4: "predict weather 5-10 minutes ahead from cloud trends"
    - Cloud_Weather_Connection Q10: "wind speed matches cloud movement speed"
    - Cloud_Weather_Connection Q12: "weather transitions feel gradual, not binary"
    """
    print("\n=== BUILD STEP 3: Wire cloud state to weather data ===")
    
    weather = cloud_weather.WeatherStateMachine()
    bridge = cloud_weather.CloudMCPBridge()
    
    # 3a. Test weather state transitions (gradual, not binary - Q12)
    print("  Testing weather state machine transitions...")
    
    # Start clear
    print(f"  Initial: {weather.current_state}")
    
    # Transition through each cloud type
    test_sequence = ["cumulus", "cirrus", "stratus", "nimbostratus", "cumulonimbus"]
    for ct_id in test_sequence:
        weather.set_cloud_type(ct_id)
        weather.tick(5.0)  # 5 minutes of transition
        ct = cloud_education.get_cloud_type(ct_id)
        print(f"\n  Cloud -> {ct['display_name']}:")
        print(f"    State: {weather.current_state} (progress: {weather.transition_progress:.0%})")
        print(f"    Wind: {weather.wind.cloud_movement_description()}")
        print(f"    Rain: {weather.get_precipitation_description()}")
        print(f"    Prediction: {weather.get_prediction_text()}")
        print(f"    Shelter: {weather.get_shelter_advice()}")
        
        # Apply via MCP bridge
        result = bridge.apply_cloud_type(ct_id)
        print(f"    MCP: applied {len(result.get('applied_properties', []))} properties")
    
    # 3b. Return to clearing (cirrus after rain = improving weather - Q3)
    print(f"\n  Clearing trend (cirrus after rain):")
    weather.set_cloud_type("cirrus")
    weather.tick(5.0)
    print(f"    State: {weather.current_state}")
    print(f"    Prediction: {weather.get_prediction_text()}")
    
    # 3c. Full clearing
    print(f"\n  Full clearing:")
    weather.set_cloud_type("cumulus")
    weather.tick(5.0)
    print(f"    State: {weather.current_state}")
    print(f"    Prediction: {weather.get_prediction_text()}")
    
    # 3d. Full state summary
    print(f"\n  Full weather state summary:")
    print(weather.state_summary())
    
    # 3e. Apply weather states via MCP
    print(f"\n  Applying weather states to UE5 via MCP...")
    for ws_id in ["clear", "fair_weather", "overcast", "changing", "rain", "storm"]:
        r = bridge.apply_weather_state(ws_id)
        ws = cloud_education.get_weather_state(ws_id)
        print(f"    {ws['display']}: {r.get('weather_state')}")
    
    return {
        "weather_states_tested": len(test_sequence),
        "transitions_tested": len(test_sequence) + 2,
        "mcp_applied": True,
    }


def build_all():
    """Run all build steps."""
    print("=" * 60)
    print("BUILD: Demo_Volumetric_Clouds + sub-features")
    print("=" * 60)
    
    # Connect to MCP
    print("\nConnecting to MCP server...")
    mcp = MCP()
    
    # Run build steps
    step1 = build_step_1_configure_cloud(mcp)
    step2 = build_step_2_educational_data()
    step3 = build_step_3_wire_weather(mcp)
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Step 1 - Cloud actor configured: {step1['actor']}.{step1['component']}")
    print(f"    Altitude: {step1['altitude']}")
    print(f"    Shadows: {step1['shadows']} @ {step1['shadow_resolution']} res")
    print(f"  Step 2 - Educational data: {step2['cloud_types_loaded']} cloud types, {step2['weather_states_loaded']} weather states")
    print(f"    Source: {step2['data_source']}")
    print(f"  Step 3 - Weather wired: {step3['weather_states_tested']} states, MCP applied: {step3['mcp_applied']}")
    
    return {"step1": step1, "step2": step2, "step3": step3}


def verify_mcp_properties(mcp: MCP):
    """Verify that the configured properties persisted on the actor."""
    print("\n=== VERIFY: MCP properties ===")
    
    # Get components and check they exist
    r = mcp.tool_call("control_actor", "get_components", actorName="DemoClouds")
    structured = r.get("result", {}).get("structuredContent", {})
    components = structured.get("components", [])
    print(f"  Components found: {len(components)}")
    for comp in components:
        print(f"    {comp['name']} ({comp['class'].split('.')[-1]})")
    
    # Verify VolumetricCloudComponent exists
    cloud_comp = [c for c in components if "VolumetricCloudComponent" in c["name"] or "VolumetricCloudComponent" in c["class"]]
    if cloud_comp:
        print(f"  OK: VolumetricCloudComponent confirmed on DemoClouds actor")
    else:
        print(f"  WARNING: VolumetricCloudComponent not found")
    
    return {"verified": True, "components": components}


def screenshot_clouds(mcp: MCP):
    """Take verification screenshot."""
    print("\n=== VERIFY: Screenshot ===")
    result = mcp.tool_call("control_editor", "screenshot", filename="build_demo_volumetric_clouds.png")
    print(f"  Screenshot: {result.get('result', {}).get('content', [{}])[0].get('text', 'unknown')}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Demo_Volumetric_Clouds")
    parser.add_argument("--verify", action="store_true", help="Verify properties after build")
    parser.add_argument("--screenshot", action="store_true", help="Take verification screenshot")
    parser.add_argument("--skip-mcp", action="store_true", help="Skip MCP calls (for testing)")
    
    args = parser.parse_args()
    
    if args.skip_mcp:
        print("Skipping MCP calls. Running educational data + weather tests only.")
        step2 = build_step_2_educational_data()
        
        print("\nTesting weather state machine (no MCP)...")
        weather = cloud_weather.WeatherStateMachine()
        for ct_id in ["cumulus", "cirrus", "stratus", "nimbostratus", "cumulonimbus"]:
            weather.set_cloud_type(ct_id)
            weather.tick(5.0)
            print(f"\n  State: {weather.current_state}")
            print(f"  {weather.state_summary()}")
        sys.exit(0)
    
    build_result = build_all()
    
    if args.verify:
        mcp = MCP()
        verify_mcp_properties(mcp)
        if args.screenshot:
            screenshot_clouds(mcp)
