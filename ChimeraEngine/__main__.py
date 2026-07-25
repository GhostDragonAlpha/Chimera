"""`python -m ChimeraEngine` -- orient in the WORKFLOW ENGINE (the root identity).

Prints the engine's viewport: the current term, its gate progress, the hierarchy setting-first from
the seed, the codebook, and the ONE next move. (The older dialectical CLI now lives at its own
membrane: `python -m ChimeraEngine.dialectic.cli`.)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # flat import, same as mcp_server.py
import engine_state

print(engine_state.Engine().orient())
