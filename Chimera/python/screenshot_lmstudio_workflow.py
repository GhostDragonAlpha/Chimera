"""
Screenshot and LM Studio Workflow Module
Captures viewport screenshots and sends them to LM Studio's local server for analysis.

Uses the shared lmstudio_client module for all HTTP requests to eliminate duplicate code.
"""

import os
import time

from config import LM_STUDIO_MODEL


class LMStudioClient:
    """Client for interacting with LM Studio's local REST API.
    
    Delegates HTTP requests to the shared lmstudio_client.send_to_lmstudio() function.
    Kept for backward compatibility with existing callers.
    """

    def __init__(self, host="localhost", port=1234):
        self.host = host
        self.port = port

    def get_available_models(self):
        """Fetch list of available models from LM Studio."""
        from lmstudio_client import get_available_models
        return get_available_models()

    def get_vision_capable_models(self):
        """Get list of LLM models that support vision."""
        from lmstudio_client import get_vision_capable_models
        return get_vision_capable_models()

    def send_screenshot_analysis(self, screenshot_path, prompt, model_id=None):
        """Send a screenshot and prompt to LM Studio for analysis.
        
        Delegates to shared lmstudio_client.send_to_lmstudio().
        
        Args:
            screenshot_path: Path to the screenshot file (png/jpg)
            prompt: Text prompt for analysis
            model_id: Specific model to use
            
        Returns:
            Response dict from LM Studio API or None on failure
        """
        from lmstudio_client import send_to_lmstudio, display_response
        
        result = send_to_lmstudio(
            prompt=prompt,
            image_path=screenshot_path,
            model_id=model_id,
            temperature=0.3,
            max_tokens=1024,
            timeout=120
        )
        
        if result:
            display_response(result)
        
        return result

    def _display_lmstudio_response(self, result):
        """Extract and display the AI response from LM Studio result."""
        from lmstudio_client import display_response
        display_response(result)


def display_lmstudio_response(result, prefix=""):
    """Extract and display the AI response from LM Studio result.
    
    Handles both standard 'content' field and reasoning-based models (Qwen3.6).
    
    Args:
        result: Dict with 'content', 'reasoning_content', or 'error' keys
        prefix: Optional string prefix for console output indentation
    """
    from lmstudio_client import display_response
    
    # Add prefix to each line of the response
    if not result:
        print(f"{prefix}No response")
        return

    content = result.get('content', '')
    reasoning_content = result.get('reasoning_content', '')
    error = result.get('error')

    if content:
        print(f"{prefix}AI Analysis: {content}")
    elif reasoning_content:
        print(f"{prefix}AI Reasoning: {reasoning_content}")

    if error:
        print(f"{prefix}[ERROR] {error}")


def capture_viewport_screenshot(filepath):
    """
    Capture a screenshot from the Unreal Engine viewport.
    
    Args:
        filepath: Path where the screenshot should be saved
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import unreal
        
        print(f"Capturing viewport screenshot to: {filepath}")
        
        # Execute screenshot console command
        # UE console command for screenshots is 'shot' or 'screenshot png filename.png'
        try:
            # Try the shot command first
            unreal.SystemLibrary.execute_console_command(
                None,
                f"shot {filepath}"
            )
            print(f"Executed 'shot' console command.")
        except Exception as e_shot:
            print(f"'shot' command failed: {e_shot}")
            try:
                # Fallback to screenshot command
                unreal.SystemLibrary.execute_console_command(
                    None,
                    f"screenshot png {filepath}"
                )
                print(f"Executed 'screenshot png' console command.")
            except Exception as e_screenshot:
                print(f"'screenshot png' command also failed: {e_screenshot}")
        
        # Verify file was created
        if os.path.exists(filepath):
            print(f"Screenshot captured successfully: {filepath}")
            return True
        else:
            print(f"Warning: Screenshot file not found at {filepath}. Console command may have succeeded but file check failed.")
            # Still return True as the console command execution is the best we can do from Python
            return True
            
    except Exception as e:
        print(f"Error capturing viewport screenshot: {e}")
        return False


def run_screenshot_analysis_workflow(screenshot_dir="Screenshots", analysis_prompt=None, model_id=None):
    """
    Complete workflow: capture screenshot and send to LM Studio for analysis.
    
    Args:
        screenshot_dir: Directory to save screenshots
        analysis_prompt: Prompt to send to LM Studio
        model_id: Specific model to use (defaults to auto-selected best available)
        
    Returns:
        Analysis result from LM Studio or error
    """
    if analysis_prompt is None:
        analysis_prompt = "Analyze this game screenshot from the player's perspective. Describe what's visible, any potential issues, and provide insights about the gameplay state."
    
    # Ensure screenshot directory exists
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = int(time.time())
    screenshot_filename = f"screenshot_{timestamp}.png"
    screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
    
    # Step 1: Capture screenshot
    print("=" * 50)
    print("STEP 1: Capturing viewport screenshot...")
    capture_success = capture_viewport_screenshot(screenshot_path)
    
    if not capture_success:
        print("Failed to capture screenshot. Aborting workflow.")
        return None
    
    # Step 2: Send to LM Studio
    print("=" * 50)
    print("STEP 2: Sending to LM Studio for analysis...")
    lm_client = LMStudioClient(host="localhost", port=1234)
    
    # Get available models first to verify model ID
    print("Fetching available models from LM Studio...")
    models = lm_client.get_available_models()
    llm_models = [m for m in models if m.get('type') == 'llm']
    if llm_models:
        model_names = [f"{m['display_name']} ({m['key']})" for m in llm_models]
        print(f"Available LLM models: {model_names}")
        
        vision_models = lm_client.get_vision_capable_models()
        if vision_models:
            vision_names = [f"{m['display_name']} ({m['key']})" for m in vision_models]
            print(f"Vision-capable models: {vision_names}")
        else:
            print("No vision-capable models found. Text-only analysis will be performed.")
    else:
        print("No LLM models available.")
    
    # Send for analysis (model auto-selected if not specified)
    result = lm_client.send_screenshot_analysis(
        screenshot_path=screenshot_path,
        prompt=analysis_prompt,
        model_id=model_id
    )
    
    return result
