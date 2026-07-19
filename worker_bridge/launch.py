#!/usr/bin/env python3
"""
Launch the PI Worker Bridge conveniently from bash / PowerShell.
Usage:
    python launch.py              # port 8888
    python launch.py 9999          # custom port
"""
import sys
import uvicorn
sys.path.insert(0, ".")  # ensure main can be imported

from main import app  # noqa: E402

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
