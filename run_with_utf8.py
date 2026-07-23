#!/usr/bin/env python3
"""Run sequential workflow with UTF-8 console support."""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Try to set stdout encoding
    if not hasattr(sys.stdout, 'reconfigure'):
        # For older Python versions, try alternative methods
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

# Now import and run the sequential orchestrator
from sequential_orchestrator import run_continuous_sequential_workflow

if __name__ == "__main__":
    run_continuous_sequential_workflow()
