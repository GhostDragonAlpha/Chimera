import os
import time
from pathlib import Path

# Graphify interface imports
try:
    from core.graphify_interface import query, mutate, load_dna_graph, save_dna_graph, graphify_mutate as record_visual_verification
except ImportError:
    try:
        from graphify_interface import query, mutate, load_dna_graph, save_dna_graph, graphify_mutate as record_visual_verification
    except ImportError:
        def mutate(*args, **kwargs): return "mutate_dummy"
        def load_dna_graph(): return {"nodes": [], "edges": []}
        def save_dna_graph(*args): pass
        def record_visual_verification(*args, **kwargs): return "mutation_dummy"

def capture_screenshot(project_path, screenshot_dir=None):
    """Capture a screenshot from the UE5 viewport after the game loads."""
    if screenshot_dir is None:
        # Use Saved/Screenshots/ directory relative to project path
        project_dir = Path(project_path).parent if Path(project_path).suffix == '.uproject' else Path(project_path)
        screenshot_dir = project_dir / "Saved" / "Screenshots"
    
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(time.time())
    screenshot_filename = f"screenshot_{timestamp}.png"
    screenshot_path = screenshot_dir / screenshot_filename
    
    # Try to capture via Unreal Python if available in editor context
    try:
        import unreal
        unreal.SystemLibrary.execute_console_command(
            None,
            f"shot {screenshot_path}"
        )
    except Exception as e:
        pass
    
    # Fallback: check for AutoScreenshot.png or recent screenshot
    if not screenshot_path.exists():
        auto_screenshot = project_dir / "Saved" / "Screenshots" / "AutoScreenshot.png"
        if auto_screenshot.exists():
            screenshot_path = auto_screenshot
        else:
            # Try to find any recent .png in Saved/Screenshots
            screenshots_folder = project_dir / "Saved" / "Screenshots"
            if screenshots_folder.exists():
                png_files = list(screenshots_folder.glob("*.png"))
                if png_files:
                    screenshot_path = max(png_files, key=lambda p: p.stat().st_mtime)
    
    return str(screenshot_path)

def analyze_screenshot(screenshot_path, lm_studio_host="localhost", lm_studio_port=1234):
    """Send screenshot to LM Studio for vision analysis."""
    if not os.path.exists(screenshot_path):
        print(f"[VISUAL_VERIFIER] Screenshot file not found: {screenshot_path}")
        return None
    
    # Import lmstudio_client functions
    try:
        import sys
        project_dir = Path(__file__).parent.parent
        python_dir = project_dir / "Python"
        if str(python_dir) not in sys.path:
            sys.path.insert(0, str(python_dir))
        
        from lmstudio_client import send_to_lmstudio
        
        prompt = (
            "You are an AI analyst reviewing a game screenshot from the player's perspective in a space simulation. "
            "Describe what's visible in the viewport: any ships, stations, space environment, vehicles, or world geometry. "
            "Be specific about what you see."
        )
        
        result = send_to_lmstudio(
            prompt=prompt,
            image_path=screenshot_path,
            model_id=None,
            temperature=0.3,
            max_tokens=1024,
            timeout=120
        )
        
        if result:
            content = result.get('content', '')
            reasoning_content = result.get('reasoning_content', '')
            
            description = content or reasoning_content or str(result)
            return description
        
        return None
    
    except Exception as e:
        print(f"[VISUAL_VERIFIER] Screenshot analysis failed: {e}")
        return None

def verify_world_visible(description):
    """Check for keywords confirming visible game objects."""
    if not description:
        return False, "No description available"
    
    desc_lower = description.lower()
    
    # Keywords to check
    keywords = ["ship", "station", "space", "vehicle", "world"]
    found_keywords = [kw for kw in keywords if kw in desc_lower]
    
    # Check for "Oh Wow" threshold: ship and stations visible
    has_ship = any(w in desc_lower for w in ["ship", "vessel", "craft"])
    has_station = any(w in desc_lower for w in ["station", "hub", "market", "port"])
    
    if has_ship and has_station:
        return True, f"Oh Wow threshold met: AI describes seeing ship and stations. Keywords found: {found_keywords}"
    
    if len(found_keywords) >= 3:
        return True, f"World visible confirmed. Keywords found: {found_keywords}"
    
    return False, f"Incomplete description. Keywords found: {found_keywords}"

def run_visual_verification(project_path):
    """Run the complete visual verification stage."""
    print("\n" + "=" * 60)
    print("STAGE 7: VISUAL VERIFICATION")
    print("=" * 60)
    
    # Step 1: Capture screenshot
    print("\n[VISUAL_VERIFIER] Capturing viewport screenshot...")
    screenshot_path = capture_screenshot(project_path)
    print(f"[VISUAL_VERIFIER] Screenshot captured at: {screenshot_path}")
    
    # Step 2: Analyze with LM Studio
    print("\n[VISUAL_VERIFIER] Sending to LM Studio for vision analysis...")
    description = analyze_screenshot(screenshot_path)
    
    if description:
        print(f"\n[LM_STUDIO ANALYSIS]\n{description}\n")
    else:
        print("[VISUAL_VERIFIER] No AI description returned from LM Studio.")
        return False, "No description"
    
    # Step 3: Verify world visible
    print("\n[VISUAL_VERIFIER] Verifying world visibility...")
    is_verified, verification_msg = verify_world_visible(description)
    
    if is_verified:
        print(f"[VISUAL_VERIFICATION] PASS: {verification_msg}")
        result = "pass"
    else:
        print(f"[VISUAL_VERIFICATION] INCOMPLETE: {verification_msg}")
        result = "incomplete"
    
    # Step 4: Record mutation
    try:
        record_visual_verification("visual_verification", result, details={"screenshot_path": screenshot_path, "description": description})
        print(f"[VISUAL_VERIFIER] Recorded visual_verification mutation: {result}")
    except Exception as e:
        print(f"[VISUAL_VERIFIER] Failed to record mutation: {e}")
    
    return is_verified, verification_msg
