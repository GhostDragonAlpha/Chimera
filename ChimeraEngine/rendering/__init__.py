"""ChimeraEngine.rendering -- the splat/particle RENDERING PIPELINE (a tenant of ChimeraEngine).

A SEPARATE system from the MCP workflow engine that lives at the ChimeraEngine root. This is the
LIGHT-view machinery: a canonical GaussianSplatCloud format (3DGS-compatible), budgeted-cut LOD by
screen-space error, a GPU-resident splat pool, and quality gates -- consolidated from WorldModel/
and ParticleEngine/. It does NOT own "proven"; that is the workflow engine's job. The two share a
folder but not an identity -- see ../README.md, the membrane index, for how they relate.
"""
