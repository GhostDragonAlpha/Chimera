# Hierarchy completion continues through the canonical controller

`Engine` and the `orient`/MCP surfaces report the completion of their local term hierarchy as a
resolution-level milestone. The completion message routes the operator to the canonical Master
and controller snapshot for the next eligible `READY` task. It intentionally reports no owner,
task, or eligibility facts because the engine does not own the fleet controller.

Use `python tools/orient.py --json` for the local state plus its `continuation` routing record.
Read the current canonical Master/controller state before claiming work. A local hierarchy
completion is never a project-wide stop signal.
