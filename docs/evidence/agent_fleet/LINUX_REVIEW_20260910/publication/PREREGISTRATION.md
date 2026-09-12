# Offline publication and provisioning review

Target: supplied snapshot cf275281. Original sources remain untouched. All Git
mutations occur inside fresh temporary local repositories; no remote service,
GitHub, Windows path, engine, or existing checkout is modified.

Preregistered before execution:

1. STATEMENT: publication moves the exact validated task SHA. PREDICTION: moving
   its local tracking ref after validation but before push can instead publish
   a different descendant. FALSIFIER: immutable-SHA push or refusal before any
   remote-base mutation. Injection uses a wrapper around the original Git helper
   at its push boundary, executing real Git commands in a temporary local origin.
2. STATEMENT: verification binds the claimed task to its repository and head.
   PREDICTION: a separate repository with the expected branch spelling but an
   unrelated HEAD passes verify. FALSIFIER: rejection on common-dir or base/head
   identity before a successful provisioned result.
3. STATEMENT: supported provisioning excludes protected build paths, as fleet
   migration step 5 requires. PREDICTION: a tracked protected-path fixture is
   populated by create. FALSIFIER: refusal or successful worktree creation with
   protected path excluded. This measures checkout behavior, not mutation of an
   existing protected directory.

No parameter sweep; one directly derived counterexample per missing guard.
