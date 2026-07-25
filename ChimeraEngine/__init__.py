"""ChimeraEngine -- THE AI's UNREAL: the workflow made into tooling.

The identity of this package IS the MCP WORKFLOW ENGINE at the root: an environment the agent works
THROUGH, whose structure is the PROVE workflow. `prove` owns "proven" and refuses until every gate
passes. Entry points: `mcp_server.py` (the MCP tool surface) over `engine_state.py` (the owned
state); `appearance.py` + `convergence.py` are the two-messenger proof -- the physics interior and
its projected surface must measurably agree. Docs: `MCP_ENGINE.md`, `ONBOARDING.md`; the readable
term list is `THE_TERMS.md`.

Three SEPARATE systems are tenants here, each sealed in its own membrane (its own folder = its own
attributable identity). They are NOT imported at this front door -- reach them by their path when a
task needs them, so `import ChimeraEngine` stays cheap and "what is ChimeraEngine" stays answerable:

  - `rendering/`  the splat/particle rendering pipeline (the light-view machinery)
  - `dialectic/`  the older particle-engine dialectical workflow (council/helm/beats/gates) -- the
                  pre-MCP precursor to this engine, kept for reference, not the current workflow
  - `vision/`     vision -> membrane labeling (photo patterns to classified membranes)

The membrane IS the boundary that makes each identity attributable -- the same law the workflow
proves with. See `README.md`, the membrane index, for how the four relate.
"""

__version__ = "0.2.0"
