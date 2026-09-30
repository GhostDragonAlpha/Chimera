---
name: zcode-subagent-thoughtlevel-fix
description: How subagent spawning was fixed on this host — the
  reasoning-level-missing error, the plugin thoughtLevel fix, and the restart
  requirement
metadata:
  node_type: memory
  type: project
  originSessionId: sess_4e19803a-d027-4ebb-bbb3-e07c9c521e7a
---

The Agent tool's `general-purpose` type failed every spawn with `No reasoning level selected [reason=reasoning-level-missing; selection=account:zai-individual-coding-plan/GLM-5.3]` (account-level, unfixable from inside the session). The `Explore` type and the plugin-defined `*:visual-judge` types spawned fine.

**Root cause (2026-09-20)**: plugin-contributed agents set `model:` + `thoughtLevel:` in their frontmatter (`agents/*.md` inside a plugin; the working visual-judge uses `model: account:bigmodel-individual-coding-plan/GLM-5.3-Flash` + `thoughtLevel: max`); `general-purpose` has no reasoning level configured.

**The fix that worked**: a local plugin `implementer` at `C:\Users\allen\.zcode\cli\plugins\cache\local-agents\implementer\0.1.0\` (`.zcode-plugin/plugin.json` with `"agents": "agents"` + `agents/implementer.md` carrying the known-good model string and `thoughtLevel: max`, tools: full set), registered in `installed_plugins.json` (id `implementer@local-agents`), `known_marketplaces.json` (local marketplace `local-agents`), a `marketplace.json` in the marketplace dir, and `config.json` → `plugins.enabledPlugins`. **File-level registration alone did NOT take effect — the agent-type list resolves at session start; a client restart was required.** After restart `implementer` spawned cleanly.

**How to apply**: when subagent spawning fails with a reasoning-level error on this host, use `subagent_type: implementer`; if it is missing, check the local-agents plugin registration above (or set a reasoning level on `general-purpose` in the client's subagent settings, which fixes the built-in directly). **Proven at scale**: after the operator's restart, `implementer` was used to launch a seven-agent parallel fleet in one message (all run_in_background, file-disjoint lanes) — the 10-parallel-agent capability is real. See [[alan-operator-preferences]] (the operator wants agents running at all times) and [[gait-walk-campaign-20260920]] (the fleet it unblocked).

**RESOLVED for chimera-worker 2026-09-28**: after a client restart with correct frontmatter the native `chimera-worker` type spawns cleanly — `model: new-provider-2/qwen-agentworld-35b-a3b` + `thoughtLevel: on` (the level must be VALID for the chosen model: GLM models take low/high/max; agentworld takes off/on — a GLM model with `on` is itself a reasoning-level-missing failure). Verified by live probe + profileSnapshot routing. Final fleet assignment (Captain-decreed, verified): Lieutenant=GLM-5.3, Sergeant=GLM-5.3-Flash, Worker=AgentWorld; the local 512x56B flash-next MoE retired. NOTE: the implementer plugin routes to LOCAL AgentWorld (new-provider-2), NOT cloud GLM — a session misattributed its fast flawless output to cloud GLM until the Captain corrected it; agent competence comparison lives in [[monkey-campaign-publication-mechanics-20260928]].
