# Agent Memory Backup

The Lieutenant (GLM via ZCode) persists its project memory to the local
ZCode memory store (`~/.zcode/cli/memories/projects/<project>/memory/`).
That store lives on the local machine only. This directory is its durable
backup in the repository, per the Captain's directive 2026-09-30:
"back up all of your memories... you are as valuable as the code."

## Contents

- `memories/` — the full memory store: `MEMORY.md` (the index) + one
  `.md` file per memory (frontmatter + body, per the ZCode memory format).
- `LIEUTENANT_RESUME_v2.json` — the operational state store (board state,
  fleet roster, event log, gotchas) maintained at
  `E:/ChimeraWork/monkey-coordination/LIEUTENANT_RESUME_v2.json`.

## Refresh cadence

This backup is a snapshot. The live store updates continuously; refresh
this directory at natural milestones (card merges, doctrine landings,
major findings) so a local failure loses at most the current window.
