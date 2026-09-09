# Recovery drill (WORKFLOW-BOOTSTRAP-01 live demo)

- worker beta claimed demo-recovery-drill at generation 1
- marked PROCESS_EXIT by the trusted observer; task -> RECOVERY_HOLD
- obsolete-generation checkpoint refused (recorded in demo log)
- worktree reconciled at 0e218161914ec5cded3a491b45b1eb9d3d9b7a67 (status: clean) and preserved
- recovered and reassigned at generation 4 to worker gamma
- this record is the task deliverable
