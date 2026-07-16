"""
Sky loop orchestrator (Loop 3).

Idempotently realizes the Loop 3 Sky set in the live editor world by running the
individual setup scripts. Wire this into startup.py (or set it as the
PythonScriptPlugin startup script) so the Sky loop is realized automatically on
editor launch.

Entry points:
  run()      -> realize the full Sky loop (idempotent)
  startup()  -> PythonScriptPlugin auto-run entry (does NOT start PIE)

The module also executes run() at import time so that simply loading it (e.g. as the
PythonScriptPlugin StartupScript) realizes the Sky loop without any extra wiring.
"""

import os
import sys

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = r"E:/PythonChimera/Chimera/Python"
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from setup_starfield import run as _run_starfield
from setup_sky_atmosphere import run as _run_sky_atmosphere
from setup_sky_earth import run as _run_sky_earth
from setup_sky_moon import run as _run_sky_moon
from setup_sky_sun import run as _run_sky_sun


def run():
    _run_starfield()
    _run_sky_atmosphere()
    _run_sky_earth()
    _run_sky_moon()
    _run_sky_sun()


def startup():
    run()


# Auto-run on import (PythonScriptPlugin StartupScript=setup_sky executes this
# top-level code). Guarded so a missing unreal module (standalone execution)
# does not crash the importer.
try:
    run()
except Exception as _exc:
    try:
        import unreal

        unreal.log_warning(f"[setup_sky] auto-run skipped: {_exc}")
    except Exception:
        pass
