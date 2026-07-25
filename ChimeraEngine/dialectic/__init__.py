"""ChimeraEngine.dialectic -- the older particle-engine DIALECTICAL WORKFLOW (a tenant).

The pre-MCP precursor to the workflow engine at the ChimeraEngine root: the same idea -- a workflow
with gates, a council that questions, verification and steering -- but built around the GPU particle
engine, before it was rebuilt as the MCP server that OWNS "proven". Kept for reference and reuse; it
is NOT the current workflow. Pipeline: Council Q&A -> Beat scripts -> Simulation -> Gates -> Helm.

Run its CLI with `python -m ChimeraEngine.dialectic.cli`. Import submodules by path
(`from ChimeraEngine.dialectic.council import Council`); nothing is auto-imported here, so the
front door stays cheap and a broken tenant module cannot poison `import ChimeraEngine`.
"""
