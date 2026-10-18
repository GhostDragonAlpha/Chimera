# Z Code: goal-aware peer workflow

Operator update, 2026-10-18. Read [the shared workflow](../tools/zcode/GAME_WORKFLOW.md)
and [the game plan](GAME_PLAN_ACTION_RPG.md). Qwen leads; Maya, Step, the flexible
worker and read-only researcher are available. Roles are defaults: the lead can
research or implement directly and choose any suitable available peer.

Give every child the game goal, current milestone/player benefit, task purpose
and decision/deliverable. Preserve these through compression, follow-up and resume.
Report game impact, evidence/limits, decision and next useful action. The lead
chooses proportionate verification and optimization, and may improve the process
itself through bounded reversible changes and observed results. Independent
physics requirements, source ownership and permissions remain in force.

Active workspace copies are D:/Chimera-Maintenance/.zcode and this repository's
.zcode directory. Their existing model selections, reasoning, tool restrictions
and timeout settings are preserved. Both startup orientations and all four
profiles carry the purpose/reporting rule. The researcher remains read-only.

The command hook source is [role_gate.py](../tools/zcode/role_gate.py); the deployed
copy and shared instructions are in Runtime/zcode-two-agent. The hook injects
purpose into Agent/Task and SendMessage without changing the target or task.
Existing conversations receive the new workflow at their next registered hook;
new/resumed sessions receive it at startup. Native goal continuation handles
completion; the old mandatory QWEN_DECISION marker and planner-only whitelist
are removed. Ordinary app permissions still apply.

[compression-goal-helper.cjs](../tools/zcode/compression-goal-helper.cjs) adds the
nearest .zcode/COMPACT_INSTRUCTIONS.md to native automatic/manual compaction.
It preserves explicit compact instructions and changes no model, quantization,
context or output cap. The installed CLI calls this helper; already-running
CLI processes load that code on their next normal restart. No agent is forcibly
restarted by this update. Updating these text files is not proof that a model
will obey every instruction; integration tests verify dispatch/compaction wiring.

Use [the lead prompt](ZCODE_LIEUTENANT_PROMPT.md) for a fresh assignment. Existing
construction, inspector, comparison and GPU tools remain the owners; create no
second workflow registry or mandatory specialist-model circuit.
