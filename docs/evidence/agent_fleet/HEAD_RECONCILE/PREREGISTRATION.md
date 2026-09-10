# fleet-head-reconcile-tool-01 preregistration

The contract, prediction, and falsifier are recorded in
`docs/THE_WORKTREE_RECONCILIATION.md` before implementation.

The bounded test matrix will use temporary Git repositories and retain failed
attempts in test output: evidence-only addition, source modification,
historical evidence modification/deletion, outside-scope change, divergent
HEAD, malformed or escaping paths, symlink escape, and an unstable read.

No controller, engine, GPU, network service, shared checkout, or existing
evidence file is used by the test harness.
