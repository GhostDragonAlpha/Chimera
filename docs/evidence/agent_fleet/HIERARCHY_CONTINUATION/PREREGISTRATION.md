# Preregistration — hierarchy continuation routing

STATEMENT: Completion of the current engine hierarchy is a local milestone and must route the operator to the canonical Master/controller for the next eligible READY task rather than ending the project.

PREDICTION: Orient text, `--json`, Engine status, and MCP status will expose a continuation record with current hierarchy completion plus canonical next-work ownership/eligibility, while preserving existing term/gate facts. A synthetic or storeless orientation will never fabricate a claimed owner.

FALSIFIER: Any complete hierarchy response says stop/end without continuation routing; JSON and text disagree; a READY task is presented as owned without controller evidence; or malformed/missing continuation data is silently treated as complete.

Checks: actual CLI and JSON outputs, Engine/MCP function return values, storeless/synthetic and completed-hierarchy fixtures, and negative tests for absent/invalid continuation fields. No live store, MCP, engine, GPU, or controller mutation.
