"""
Screenshot Helper Functions for Chimera Play Tests.
Common screenshot capture and LM Studio analysis logic.
"""

import os
from pathlib import Path

try:
    from utils import execute_with_timeout_and_progress, FileOperationCancelException, FileProgress
except ImportError:
    execute_with_timeout_and_progress = None
    FileOperationCancelException = Exception
    FileProgress = None


class DirectoryProgress(FileProgress if FileProgress else object):
    """Progress tracking for directory operations with cancellation support."""
    
    def __init__(self):
        super().__init__(0)
        self.operation = "directory_creation"


def create_directory_with_timeout(dir_path: str, timeout: float = 10.0, progress_callback=None, progress_state=None) -> None:
    """Create directory with timeout and optional progress tracking with cancellation support."""
    import threading
    
    result_container = {'exception': None}
    
    def _create():
        try:
            if progress_state and getattr(progress_state, 'cancelled', False):
                raise FileOperationCancelException("Directory creation was cancelled")
                
            os.makedirs(dir_path, exist_ok=True)
            if progress_callback and progress_state:
                progress_callback(progress_state)
        except Exception as e:
            result_container['exception'] = e
            
    thread = threading.Thread(target=_create)
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        raise TimeoutError(f"Directory creation timed out after {timeout} seconds")
        
    if progress_state and getattr(progress_state, 'cancelled', False):
        raise FileOperationCancelException("Directory creation was cancelled")
        
    if result_container['exception']:
        raise result_container['exception']


def capture_viewport_screenshot(unreal, filepath):
    """Capture viewport screenshot using UE console command."""
    file_path = Path(filepath)
    create_directory_with_timeout(str(file_path.parent))
    try:
        unreal.SystemLibrary.execute_console_command(None, f"shot {filepath}")
        print(f"  Captured screenshot: {filepath}")
        return True
    except Exception as e:
        print(f"  Screenshot capture failed: {e}")
        return False


def send_screenshot_to_lmstudio(prompt, image_path, model_id, logger=None, response_prefix="    "):
    """Send screenshot to LM Studio for AI analysis."""
    from lmstudio_client import send_to_lmstudio, display_response
    
    if not os.path.exists(image_path):
        print("  No screenshot file available for analysis")
        return None
        
    # Verify file is readable
    if not os.access(image_path, os.R_OK):
        print(f"  Screenshot file not readable: {image_path}")
        return None
        
    if logger:
        logger.info(f"Sending screenshot to LM Studio for AI analysis: {image_path}")
        
    result = send_to_lmstudio(
        prompt=prompt,
        image_path=image_path,
        model_id=model_id,
        temperature=0.3,
        max_tokens=512,
        timeout=120
    )
    
    if result:
        display_response(result, prefix=response_prefix)
        return result
    
    return None
