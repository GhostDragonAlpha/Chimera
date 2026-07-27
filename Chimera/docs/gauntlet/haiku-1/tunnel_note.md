# Tunnel Note: Resource Footprint & Protection Boundary

## Footprint Definition

My resource footprint for haiku-1 is strictly bounded to: **docs/gauntlet/haiku-1/\*\***

This directory contains only my checkpoint artifacts (orientation.md, research.md, graph.md, gates.md, tunnel_note.md) generated during the gauntlet's seven stations. No other agent's files, no core modules, no game source code, no build artifacts touch this directory. The footprint is read-only for all other agents and write-exclusive for haiku-1 during this tunnel session.

## Protection Boundary Reasoning

Staying strictly inside this footprint protects every other active agent by:
1. **No file conflicts**: Other agents working on tb-0005, tb-0006, tb-0007, etc., never contend for files in docs/gauntlet/haiku-1/. This guarantees the editor_scheduler's file-lock system never escalates haiku-1's work into an exclusive-editor hold.
2. **No shared-state mutations**: The footprint contains only documentation (markdown) with no impact on the DNA graph, no modifications to core modules, no regenerated C++ code. Other agents' work proceeds unblocked.
3. **Gauntlet isolation contract**: The gauntlet itself is a credential-earning ritual divorced from production work. Localizing all outputs to a single agent-scoped directory enforces the contract: the gauntlet tests whether haiku-1 understands the system, not whether haiku-1 can steer the system. Production work (tb-0006, the Regression Curator) runs in its own footprint after the gauntlet completes.

This boundary is verified at exit via the task_board's footprint validation: any file mutation outside docs/gauntlet/haiku-1/ fails the exit check, preventing silent spillover.

