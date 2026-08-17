# SPIACE operator window launcher — the ONE entry point for the human.
# The browser is retired as the viewer frontend (Chromium wedged machine-wide
# 2026-08-16: every Chrome/Edge/Playwright instance hung on ALL navigation
# while curl/Python flew — never our code). The operator window is now the
# native C++ exe: Win32 + wgpu-native + the relay over loopback HTTP.
#
#   python START_VIEWER.py            # relay (if down) + native window
#
# native/ChimeraEngine.exe also self-starts the relay if it is missing, so
# double-clicking the exe works too.

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXE = HERE / "native" / "ChimeraEngine.exe"

if not EXE.exists():
    sys.exit(f"build first: cd native && g++ -O2 -std=c++17 viewer.cpp "
             f"-I viewer3rd -o ChimeraEngine.exe viewer3rd/wgpu_native.dll "
             f"-lws2_32 -luser32 -lgdi32")

subprocess.Popen([str(EXE)], cwd=str(HERE / "native"))
print("ChimeraEngine.exe launched (native window; relay auto-starts if down)")
