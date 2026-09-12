# fleet-maintenance-amendment-01 preregistration (2026-09-11, lead lane)

Task: `fleet-maintenance-amendment-01` generation 1, slot 1, worktree
`E:\ChimeraWork\slot-01`, base `ecc839ab` (integration tip; wave-3 PRs
#56–#59 merged). Bundle: the wave-3 Master amendment + the catalogue repin
in ONE PR (the recorded lesson: doc merges stale the pins, so the repin
rides the same branch, measured at the amended head).

- **STATEMENT**: the wave-3 Master amendment is append-only, and the
  catalogue count pins equal the builder output measured AT the amended tip
  (pins bind to measurement, never to expectation).
- **PREDICTION**: (a) the amendment lands as a single dated section with
  zero deleted lines; (b) a fresh `python tools/agent_fleet/master_catalogue.py`
  run at the amended head yields counts that, when pinned, make the full
  fleet suite pass (0 failures, 1 Windows-symlink skip); (c) the
  perturbation control (one appended dated line in a throwaway copy) moves
  the measured counts and the pins FAIL against perturbed output.
- **FALSIFIER**: history rewritten; pins changed without a fresh measured
  run at the amended tip; perturbation not demonstrated; or any test
  weakened.

Amendment content declared before writing: wave-3 integrations (PRs #56–#59
with their review chains); the engine Master-link append owed to
`engine-vulkan-cleanup-02` by lane agreement (its scopes excluded the Master
list by design — the unclaimable-task correction); dispositions
(`fleet-orient-continuation-01` closed via the authorized yield–recover
handoff with successor `-02` integrated; `engine-vulkan-cleanup-01`
superseded by `-02`, unclaimable by construction — Master scope made it
lead-only while the lead holds no engine caps); two controller gaps recorded
(no retire op for stale READY tasks; no supervisor op to retire an
unprovisionable RUNNING claim without agent revocation — candidate
`fleet-task-abandon-01`); followup ledger references (`5cfa9382` leaked
fixture child, `ec6bcffc` multi-instance yield note, `97b871b5` remnants,
engine-lane review notes: freeze-runner-before-baseline).
