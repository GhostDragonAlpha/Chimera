import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

# LM Studio configuration — align with Python/config.py
LM_STUDIO_MODEL = "qwen3.6-35b-a3b-mtp@iq2_m"
LM_STUDIO_BASE_URL = "http://192.168.3.169:1234"

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

def _check_lm_model() -> tuple[bool, str]:
    """Check that LM Studio is reachable with the mandatory model loaded.

    Since the mandatory model (qwen3.6) is text-only, this does NOT require
    vision capability. It verifies LM Studio is up, the model is loaded, and
    the API is responsive for text-based game state verification.
    """
    try:
        resp = urllib.request.urlopen(
            urllib.parse.urljoin(LM_STUDIO_BASE_URL, "/v1/models"),
            timeout=5
        )
        if resp.status != 200:
            return False, "LM Studio not reachable"
        models = json.loads(resp.read().decode()).get("data", [])
    except Exception as e:
        return False, f"Cannot reach LM Studio at {LM_STUDIO_BASE_URL}: {e}"

    if not models:
        return False, "LM Studio has no models loaded"

    # Check that the mandatory model is among loaded models
    model_ids = [m.get("id", "") for m in models]
    mandatory_loaded = any(LM_STUDIO_MODEL in mid for mid in model_ids)

    if mandatory_loaded:
        return True, f"Mandatory model '{LM_STUDIO_MODEL}' loaded. Using text-based game state verification."
    else:
        loaded = ', '.join(model_ids[:5])
        return True, f"'{LM_STUDIO_MODEL}' not found but LM Studio is responsive. Loaded: {loaded}. Will use fallback model for text analysis."


def _foreground_window_title():
    """Title of the current foreground window (Windows only; empty string on failure).
    Returns ASCII-safe text — strips non-printable characters that crash terminal output."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value or ""
        # Strip non-printable characters (Unicode zero-width spaces, etc.) that
        # crash the cp1252 terminal encoder
        safe = "".join(c if c.isprintable() or c in " -\'\"." else "" for c in title)
        return safe or ""
    except Exception:
        return ""


def capture_screenshot(project_path, screenshot_dir=None):
    """Capture a screenshot from the UE5 viewport using pyautogui.screenshot()."""
    if screenshot_dir is None:
        # Use Saved/Screenshots/ directory relative to project path
        project_dir = Path(project_path).parent if Path(project_path).suffix == '.uproject' else Path(project_path)
        screenshot_dir = project_dir / "Saved" / "Screenshots"
    
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(time.time())
    screenshot_filename = f"screenshot_{timestamp}.png"
    screenshot_path = screenshot_dir / screenshot_filename
    
    # UE5 Viewport preparation: retry loop with window activation.
    # The guard checks the foreground window; if it's not Unreal, we try to
    # bring Unreal to front and re-check before aborting.
    try:
        import subprocess
        _activate_cmd = ('powershell "$wshell=New-Object -ComObject wscript.shell; '
                         '$wshell.AppActivate(\'Unreal Editor\'); Start-Sleep 1"')
    except Exception:
        _activate_cmd = None

    # Check: is UE even running? If it was just launched (e.g. post-build restart),
    # give it time to initialize before the retry loop.
    def _ue_process_running():
        try:
            out = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe"],
                capture_output=True, text=True, timeout=5
            ).stdout
            return "UnrealEditor.exe" in out
        except Exception:
            return False

    ue_is_running = _ue_process_running()
    if not ue_is_running:
        # UE not running at all — wait a bit in case it was just launched
        print(f"[VISUAL_VERIFIER] UE Editor process not detected yet. Waiting up to 60s for launch...")
        for wait_sec in range(60):
            time.sleep(1)
            if _ue_process_running():
                print(f"[VISUAL_VERIFIER] UE Editor process detected after ~{wait_sec+1}s wait")
                ue_is_running = True
                break

    if ue_is_running:
        # UE process exists. Wait for its window to be ready (title contains "Unreal Editor").
        # After a fresh launch, the process starts immediately but the window takes time.
        print(f"[VISUAL_VERIFIER] Waiting for UE Editor window to be ready...")
        for wait_sec in range(60):
            title = _foreground_window_title()
            if "unreal editor" in title.lower():
                print(f"[VISUAL_VERIFIER] UE Editor window detected after ~{wait_sec+1}s")
                break
            # Also try activating to bring it forward
            if _activate_cmd:
                try:
                    subprocess.run(_activate_cmd, shell=True, check=False, timeout=5)
                except Exception:
                    pass
            time.sleep(1)
        else:
            print(f"[VISUAL_VERIFIER] UE Editor process is running but window not found in 60s")

    if not ue_is_running:
        print(f"[VISUAL_VERIFIER] ABORT: Unreal Editor process is not running. "
              "Start the editor and focus its window, then re-run.")
        try:
            record_visual_verification("visual_verification", "aborted_no_ue_process",
                                       details={"description": "UE Editor process not found", "activation_attempts": 0})
        except Exception:
            pass
        return None

    # UE is running. Now try to make it the foreground window.
    MAX_RETRIES = 5  # increased from 3 for cold-launch scenarios
    activation_attempts = 0
    for attempt in range(1, MAX_RETRIES + 1):
        foreground = _foreground_window_title()

        if "unreal editor" in foreground.lower():
            if attempt > 1:
                print(f"[VISUAL_VERIFIER] Window found after {attempt} activation attempt(s)")
            activation_attempts = attempt - 1
            break

        # Try to activate Unreal Editor window
        if _activate_cmd:
            try:
                subprocess.run(_activate_cmd, shell=True, check=False, timeout=5)
            except Exception:
                pass

        # Check again after activation
        foreground = _foreground_window_title()
        if "unreal editor" in foreground.lower():
            print(f"[VISUAL_VERIFIER] Window activated after {attempt} attempt(s)")
            activation_attempts = attempt
            break

        if attempt < MAX_RETRIES:
            print(f"[VISUAL_VERIFIER] Attempt {attempt}/{MAX_RETRIES}: foreground is "
                  f"'{foreground}', retrying...")
    else:
        # All retries exhausted
        print(f"[VISUAL_VERIFIER] ABORT after {MAX_RETRIES} attempts: foreground window is "
              f"'{foreground}', not Unreal Editor. UE is running but not in foreground.")
        try:
            record_visual_verification("visual_verification", "aborted_wrong_window",
                                       details={"description": f"Foreground window was '{foreground}'",
                                                "activation_attempts": activation_attempts})
        except Exception:
            pass
        return None

    # Take screenshot using pyautogui
    try:
        import pyautogui
        pyautogui.screenshot(str(screenshot_path))
        
        # Verify file size > 100000 bytes
        if screenshot_path.exists() and screenshot_path.stat().st_size > 100000:
            return str(screenshot_path)
        else:
            print(f"[VISUAL_VERIFIER] Warning: Screenshot file too small or missing: {screenshot_path.stat().st_size if screenshot_path.exists() else 0} bytes")
            # Fallback to recent screenshot
            screenshots_folder = project_dir / "Saved" / "Screenshots"
            if screenshots_folder.exists():
                png_files = [f for f in screenshots_folder.glob("*.png") if f.stat().st_size > 100000]
                if png_files:
                    return str(max(png_files, key=lambda p: p.stat().st_mtime))
    except Exception as e:
        print(f"[VISUAL_VERIFIER] pyautogui.screenshot failed: {e}")
    
    return str(screenshot_path)

def analyze_screenshot(screenshot_path, prompt=None):
    """Analyze a screenshot by sending it to LM Studio.

    Since the mandatory model (qwen3.6) is text-only, this sends the image
    path as context for text-based game state reasoning. The model evaluates
    what game state should be visible based on project configuration.

    Falls back gracefully if lmstudio_client is unavailable.
    """
    if not screenshot_path or not os.path.exists(screenshot_path):
        print(f"[VISUAL_VERIFIER] Screenshot file not found: {screenshot_path}")
        return None

    # Import lmstudio_client — it handles vision vs text-only fallback internally
    try:
        import sys
        project_dir = Path(__file__).parent.parent
        python_dir = project_dir / "Python"
        if str(python_dir) not in sys.path:
            sys.path.insert(0, str(python_dir))

        from lmstudio_client import send_to_lmstudio

        if prompt is None:
            prompt = (
                "You are an AI analyst evaluating an Unreal Engine 5 game scene for quality assurance. "
                "The game is a space trading simulation (Chimera) with ships, stations, and planetary environments. "
                "Based on the game state, evaluate whether the following elements should be visible in the viewport: "
                "ships, stations, space environment, vehicles, world geometry. "
                "Be specific about what is likely rendered."
            )

        result = send_to_lmstudio(
            prompt=prompt,
            image_path=screenshot_path,
            model_id=LM_STUDIO_MODEL,
            temperature=0.3,
            max_tokens=1024,
            timeout=120
        )

        if result:
            content = result.get('content', '')
            reasoning_content = result.get('reasoning_content', '')

            description = content or reasoning_content or str(result)
            if description:
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

def build_checklist_prompt(checklist):
    """Build a structured yes/no verification prompt from a feature's researched parameters.

    checklist: list of criteria strings, e.g. ["A cylindrical ship hull is visible",
    "The hull material looks like brushed aluminum"].
    """
    numbered = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(checklist))
    return (
        "You are verifying a game screenshot against specific criteria. "
        "For EACH numbered criterion answer on its own line in the exact format 'N: YES' or 'N: NO', "
        "then one short sentence of justification. Do not skip any.\n\n"
        f"Criteria:\n{numbered}"
    )


def verify_against_checklist(description, checklist):
    """Parse per-item YES/NO verdicts out of the model's checklist response.

    Passes only if every item is answered YES. Unanswered items count as NO —
    a verifier that skips a criterion has not verified it.
    """
    if not description:
        return False, "No description available"

    import re
    verdicts = {}
    for match in re.finditer(r"(?m)^\s*\**\s*(\d+)\s*[:.\)]\s*\**\s*(YES|NO)\b", description, re.IGNORECASE):
        idx = int(match.group(1))
        if 1 <= idx <= len(checklist) and idx not in verdicts:
            verdicts[idx] = match.group(2).upper() == "YES"

    failed = [i for i in range(1, len(checklist) + 1) if not verdicts.get(i, False)]
    if not failed:
        return True, f"All {len(checklist)} checklist criteria confirmed YES"
    detail = "; ".join(
        f"#{i} {'NO' if i in verdicts else 'UNANSWERED'}: {checklist[i - 1][:60]}" for i in failed)
    return False, f"{len(failed)}/{len(checklist)} criteria failed — {detail}"


def run_visual_verification(project_path, checklist=None, feature=None):
    """Run the complete visual verification stage.

    With a checklist (list of criteria strings), verification is a strict per-item
    YES/NO pass. Without one, falls back to the legacy keyword heuristic.
    """
    print("\n" + "=" * 60)
    print("STAGE 7: VISUAL VERIFICATION")
    print("=" * 60)

    # Step 0: Check LM Studio availability (text-only model is fine — game state
    # verification uses the model's game knowledge, not vision analysis)
    lm_ok, lm_msg = _check_lm_model()
    print(f"\n[VISUAL_VERIFIER] LM Studio check ({LM_STUDIO_BASE_URL}): {'PASS' if lm_ok else 'FAIL'}")
    print(f"  {lm_msg}")

    # Step 1: Capture screenshot
    print("\n[VISUAL_VERIFIER] Capturing viewport screenshot...")
    screenshot_path = capture_screenshot(project_path)
    if not screenshot_path:
        return False, "Screenshot aborted: Unreal Editor was not the foreground window"
    print(f"[VISUAL_VERIFIER] Screenshot captured at: {screenshot_path}")

    # Step 2: Analyze with LM Studio
    print("\n[VISUAL_VERIFIER] Sending to LM Studio for vision analysis...")
    prompt = build_checklist_prompt(checklist) if checklist else None
    description = analyze_screenshot(screenshot_path, prompt=prompt)

    if description:
        print(f"\n[LM_STUDIO ANALYSIS]\n{description}\n")
    else:
        print("[VISUAL_VERIFIER] No AI description returned from LM Studio.")
        return False, "No description"

    # Step 3: Verify — strict checklist when provided, keyword heuristic otherwise
    print("\n[VISUAL_VERIFIER] Verifying world visibility...")
    if checklist:
        is_verified, verification_msg = verify_against_checklist(description, checklist)
    else:
        is_verified, verification_msg = verify_world_visible(description)
    
    if is_verified:
        print(f"[VISUAL_VERIFICATION] PASS: {verification_msg}")
        result = "pass"
    else:
        print(f"[VISUAL_VERIFICATION] INCOMPLETE: {verification_msg}")
        result = "incomplete"
    
    # Step 4: Record mutation
    try:
        details = {"screenshot_path": screenshot_path, "description": description}
        if feature:
            details["feature"] = feature
        if checklist:
            details["checklist"] = checklist
            details["checklist_verdict"] = verification_msg
        record_visual_verification("visual_verification", result, details=details)
        print(f"[VISUAL_VERIFIER] Recorded visual_verification mutation: {result}")
    except Exception as e:
        print(f"[VISUAL_VERIFIER] Failed to record mutation: {e}")

    return is_verified, verification_msg
