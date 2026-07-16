"""
realize_sky_loop.py — apply the Loop 3 Sky realization to the LIVE editor world.

Idempotently runs Python/setup_sky.py (which realizes SM_StarSphere + SkyAtmosphere_Lunar)
in the editor's Python context via system_control.execute_python, then saves the level.
Because PIE copies the in-memory editor world, a subsequent witness session sees the
Sky actors. Re-run any time the level is reset.

Usage:
  python Python/realize_sky_loop.py
"""

import sys
import time
import json

sys.path.insert(0, r"E:/PythonChimera/Chimera")
sys.path.insert(0, r"E:/PythonChimera/Chimera/core")

from telemetry_probe import MCPStdioClient
from core.unblock import ensure_editor

SETUP_CODE = "import importlib.util as u, sys; sys.modules.pop('setup_starfield', None); sys.modules.pop('setup_sky_atmosphere', None); sys.modules.pop('setup_sky_earth', None); sys.modules.pop('setup_sky_moon', None); sys.modules.pop('setup_sky_sun', None); sys.modules.pop('setup_sky', None); sys.modules.pop('sk', None); p=r'E:/PythonChimera/Chimera/Python/setup_starfield.py'; s=u.spec_from_file_location('setup_starfield', p); m=u.module_from_spec(s); sys.modules['setup_starfield']=m; s.loader.exec_module(m); m.run(); p=r'E:/PythonChimera/Chimera/Python/setup_sky_atmosphere.py'; s=u.spec_from_file_location('setup_sky_atmosphere', p); m=u.module_from_spec(s); sys.modules['setup_sky_atmosphere']=m; s.loader.exec_module(m); m.run(); p=r'E:/PythonChimera/Chimera/Python/setup_sky_earth.py'; s=u.spec_from_file_location('setup_sky_earth', p); m=u.module_from_spec(s); sys.modules['setup_sky_earth']=m; s.loader.exec_module(m); m.run(); p=r'E:/PythonChimera/Chimera/Python/setup_sky_moon.py'; s=u.spec_from_file_location('setup_sky_moon', p); m=u.module_from_spec(s); sys.modules['setup_sky_moon']=m; s.loader.exec_module(m); m.run(); p=r'E:/PythonChimera/Chimera/Python/setup_sky_sun.py'; s=u.spec_from_file_location('setup_sky_sun', p); m=u.module_from_spec(s); sys.modules['setup_sky_sun']=m; s.loader.exec_module(m); m.run()"


def _bridge_up():
    try:
        c = MCPStdioClient()
        try:
            r = c.call("inspect", {"action": "runtime_report"})
            return bool((r.get("result") or {}).get("success"))
        finally:
            c.close()
    except Exception:
        return False


def wait_for_editor(timeout_s=300):
    ok, note = ensure_editor()
    if not ok:
        print(f"[realize_sky_loop] ensure_editor: {note}")
        return False
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _bridge_up():
            return True
        time.sleep(5)
    print("[realize_sky_loop] editor bridge not reachable within timeout")
    return False


def main():
    if not wait_for_editor():
        sys.exit(1)
    c = MCPStdioClient()
    try:
        res = c.call("system_control", {"action": "execute_python", "code": SETUP_CODE})
        print(json.dumps(res, indent=2, default=str)[:5000])
    finally:
        c.close()


if __name__ == "__main__":
    main()
