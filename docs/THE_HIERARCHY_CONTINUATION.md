# Hierarchy completion continues through the canonical controller

`Engine` and the `orient`/MCP surfaces report the completion of their local term hierarchy as a
resolution-level milestone. The completion message routes the operator through
`docs/AGENT_START.md` and the current canonical Master/controller snapshot: continue this session's
owned milestones first, and only if approved capacity remains request an authenticated claim for
an eligible `READY` task. It intentionally reports no owner, task, eligibility, or capacity facts
because the engine does not own the fleet controller.

Use `python tools/orient.py --json` for the local state plus its `continuation` routing record.
Read the current canonical Master/controller state before claiming work. A local hierarchy
completion is never a project-wide stop signal.
