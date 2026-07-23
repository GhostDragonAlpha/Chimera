#!/usr/bin/env python3
"""Enable UTF-8 output for Windows console."""

import sys
import os

if sys.platform == 'win32':
    # Set PYTHONIOENCODING before importing anything else
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # For Python 3.7+, we can try to reconfigure stdout
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Also set locale
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Now run the sequential workflow
from sequential_orchestrator import run_continuous_sequential_workflow

if __name__ == "__main__":
    run_continuous_sequential_workflow()
