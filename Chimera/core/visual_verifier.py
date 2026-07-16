import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

# LM Studio configuration — align with Python/config.py.
# This path does NOT go through lm_gateway.lm_urlopen (it calls lmstudio_client
# directly), so it has to adopt the resident model itself: resolve_model() is
# what keeps vision on whatever model the operator actually loaded.
try:
    from core.lm_gateway import (LM_MODEL as LM_STUDIO_MODEL, LM_TIMEOUT,
                                 resolve_model, loaded_models)
except Exception:
    LM_STUDIO_MODEL = ""   # blank ON PURPOSE — see lm_gateway.LM_MODEL
    LM_TIMEOUT = 600

    def resolve_model() -> str:
        return LM_STUDIO_MODEL      # blank -> LM Studio errors loudly, which beats
                                    # silently pinning a model nobody chose

    def loaded_models() -> list:
        return []

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
    """LM Studio must be up with SOME model loaded — WHICH one is the operator's
    call, and the studio adopts it (lm_gateway.resolve_model).

    Deliberately does not demand a specific id: swapping the model for the whole
    operation is meant to be "load a different one in LM Studio", nothing more.
    Vision-capability is the operator's responsibility — LM Studio's llm/vlm
    labels are unreliable for these builds (vision was added after the fact).
    """
    try:
        resp = urllib.request.urlopen(
            urllib.parse.urljoin(LM_STUDIO_BASE_URL, "/v1/models"),
            timeout=5
        )
        if resp.status != 200:
            return False, "LM Studio not reachable"
    except Exception as e:
        return False, f"Cannot reach LM Studio at {LM_STUDIO_BASE_URL}: {e}"

    # Authoritative check: RESIDENT (state=loaded), the same source resolve_model
    # uses — /v1/models can list models that are merely on disk, and passing this
    # gate on those would only defer the failure to the first real call.
    resident = loaded_models()
    if not resident:
        return False, ("LM Studio is up but NO MODEL IS LOADED — load one "
                       "(vision-capable); the studio adopts it and never picks for you")

    return True, f"LM Studio up; the studio will use the loaded model '{resident[0]}'"


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
    """Capture a screenshot from the UE5 viewport using MCP control_editor screenshot mode=editor_viewport."""
    if screenshot_dir is None:
        # Use Saved/Screenshots/ directory relative to project path
        project_dir = Path(project_path).parent if Path(project_path).suffix == '.uproject' else Path(project_path)
        screenshot_dir = project_dir / "Saved" / "Screenshots"

    screenshot_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    screenshot_filename = f"screenshot_{timestamp}.png"
    screenshot_path = screenshot_dir / screenshot_filename

    # Use MCP control_editor screenshot mode=editor_viewport (H-2 prohibition: never verify from desktop screenshots)
    try:
        from core.telemetry_probe import MCPStdioClient
        client = MCPStdioClient()

        # Call control_editor screenshot with mode=editor_viewport
        result = client.call("control_editor", {
            "action": "screenshot",
            "filename": screenshot_filename,
            "mode": "editor_viewport"
        })

        client.close()

        # Check if the call was successful
        structured_content = result.get("result", {}).get("structuredContent", {})
        if structured_content.get("success"):
            print(f"[VISUAL_VERIFIER] Screenshot captured via MCP control_editor mode=editor_viewport: {screenshot_path}")
            return str(screenshot_path)
        else:
            error_msg = structured_content.get("message", "Unknown error")
            print(f"[VISUAL_VERIFIER] MCP screenshot failed: {error_msg}")
            # Fallback to recent screenshot
            screenshots_folder = project_dir / "Saved" / "Screenshots"
            if screenshots_folder.exists():
                png_files = [f for f in screenshots_folder.glob("screenshot_*.png") if f.stat().st_size > 10000]
                if png_files:
                    return str(max(png_files, key=lambda p: p.stat().st_mtime))
    except Exception as e:
        print(f"[VISUAL_VERIFIER] MCP control_editor screenshot failed: {e}")

    # Final fallback to recent screenshot
    screenshots_folder = project_dir / "Saved" / "Screenshots"
    if screenshots_folder.exists():
        png_files = [f for f in screenshots_folder.glob("screenshot_*.png") if f.stat().st_size > 10000]
        if png_files:
            return str(max(png_files, key=lambda p: p.stat().st_mtime))

    return None

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

        # H-3: Retry with larger token budget if LM response contains reasoning dump
        max_retry_attempts = 2
        current_max_tokens = 1024

        for attempt in range(max_retry_attempts + 1):
            result = send_to_lmstudio(
                prompt=prompt,
                image_path=screenshot_path,
                model_id=resolve_model(),      # whatever the operator has loaded
                temperature=0.3,
                max_tokens=current_max_tokens,
                timeout=LM_TIMEOUT   # reasoning model needs room to think (was 120s)
            )

            if result:
                content = result.get('content', '')
                reasoning_content = result.get('reasoning_content', '')
                has_reasoning_dump = result.get('has_reasoning_dump', False)

                # H-3: If reasoning dump detected, retry with larger token budget
                if has_reasoning_dump and attempt < max_retry_attempts:
                    current_max_tokens = min(current_max_tokens * 2, 4096)
                    print(f"[VISUAL_VERIFIER] LM response contains reasoning dump. Retry {attempt+1}/{max_retry_attempts} with max_tokens={current_max_tokens}")
                    continue
                elif has_reasoning_dump:
                    # Max retries reached, return error indicator
                    print("[VISUAL_VERIFIER] LM response contains reasoning dump after max retries - schema-validation failed")
                    return None

                description = content or reasoning_content or str(result)
                if description:
                    return description

            break  # No result or no reasoning dump, exit loop

        return None

    except Exception as e:
        print(f"[VISUAL_VERIFIER] Screenshot analysis failed: {e}")
        return None

def verify_world_visible(description):
    """REMOVED 2026-07-16. Kept as a refusal so no caller silently resurrects it.

    It grepped the model's prose for the words "ship"/"station" and called their presence
    proof. Substring matching for PRESENCE cannot express ABSENCE, so it read a flat
    denial as a triumph. Executed, verbatim:

        "I cannot see any ships or stations in this viewport. The screen is black."
            -> True, "Oh Wow threshold met: AI describes seeing ship and stations"
        "No ship is visible. No station is visible. The world failed to load."
            -> True, same message

    No keyword list fixes this; the shape is wrong. And it was worse than a bad parser,
    because the default prompt ASKED what "should be visible" and what is "likely
    rendered" while HANDING the model the words "ships, stations, space environment" --
    which the model repeated and this function grepped back out. The prompt wrote the
    answer and the grep read it. A closed loop that never looked at the viewport, in the
    gate whose whole promise is "the local model must have LOOKED at it."

    Its sibling `verify_against_checklist` in this same file had it right the whole time:
    structured per-item YES/NO, and "Unanswered items count as NO -- a verifier that
    skips a criterion has not verified it." The careful branch and the sloppy one lived
    forty lines apart, and the sloppy one was the DEFAULT.

    Use DEFAULT_CHECKLIST + verify_against_checklist. A checklist is the REFERENCE: no
    reference, no verdict.
    """
    raise NotImplementedError(
        "verify_world_visible was removed: it grepped for 'ship'/'station' and so read "
        "'I cannot see any ships or stations, the screen is black' as a PASS. Use "
        "verify_against_checklist(description, checklist or DEFAULT_CHECKLIST).")


# The honest form of the old "Oh Wow threshold": say what must be on screen, then make
# the model answer YES/NO to each. This is the REFERENCE the keyword grep never had --
# and note it asks what IS visible, never what "should be" or is "likely rendered".
DEFAULT_CHECKLIST = [
    "The viewport shows rendered 3D geometry (NOT a black, blank, or solid-colour screen)",
    "A ship, craft, or vehicle is actually visible in this image",
    "A station, hub, or built structure is actually visible in this image",
]

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
    # There is no "no checklist" path anymore (2026-07-16). It used a prompt that asked
    # what "should be visible" while supplying the keywords, then grepped them back out
    # of the reply — a closed loop that never looked at the screen. A verification with
    # no reference is not a weaker verification, it is a different thing wearing its
    # name. DEFAULT_CHECKLIST is the reference when the caller does not bring one.
    checklist = checklist or DEFAULT_CHECKLIST
    prompt = build_checklist_prompt(checklist)
    description = analyze_screenshot(screenshot_path, prompt=prompt)

    if description:
        print(f"\n[LM_STUDIO ANALYSIS]\n{description}\n")
    else:
        print("[VISUAL_VERIFIER] No AI description returned from LM Studio.")
        return False, "No description"

    # Step 3: Verify — ALWAYS the strict checklist. Unanswered counts as NO.
    print("\n[VISUAL_VERIFIER] Verifying world visibility...")
    is_verified, verification_msg = verify_against_checklist(description, checklist)
    
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
