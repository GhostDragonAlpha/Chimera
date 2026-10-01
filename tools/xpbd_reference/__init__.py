"""The coupled XPBD volume solve — CPU reference model (B1x).

Reads:  docs/evidence/agent_fleet/SHIP/A1_XPBD/{PREREG,DIAGNOSTIC,DESIGN}.md
Owns:   this package + BATTERY_RESULTS.md in the same directory.
"""
from . import measured
from . import model
from . import solver
from . import battery

__all__ = ["measured", "model", "solver", "battery"]
