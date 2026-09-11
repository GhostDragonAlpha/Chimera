# fleet-maintenance-amendment-02 preregistration (2026-09-11, lead lane)

Task: `fleet-maintenance-amendment-02` generation 1, slot 1, worktree
`E:\ChimeraWork\slot-01`, base `4c319997` (task record; integration tip at
claim time — the wave-3 close-out merge). Bundle: the wave-4/5 Master
amendment + the catalogue repin in ONE PR (the recorded lesson from
amendment-01: doc merges stale the pins, so the repin rides the same branch,
measured at the amended head). The supervisor `task_abandon` retirements of
the seven stale READY records execute ONLY after this PR integrates.

- **STATEMENT**: the wave-4/5 Master amendment is append-only, and the
  catalogue count pins equal the builder output measured AT the amended tip
  (pins bind to measurement, never to expectation).
- **PREDICTION**: (a) the amendment lands as a single dated section with
  zero deleted lines; (b) a fresh `python tools/agent_fleet/master_catalogue.py`
  run at the amended head yields counts that, when pinned, make the full
  fleet suite pass (0 failures, 1 Windows-symlink skip; the suite count at
  this era is 231 per the PR #68 regression sweep's measured correction F2
  — if the known intermittent capture-content flake fires, rerun once and
  retain both runs verbatim); (c) the perturbation control (one appended
  dated pipe-row in a throwaway copy of the Master at the amended commit)
  moves the measured counts and the pins FAIL against the perturbed output.
- **FALSIFIER**: history rewritten (any deletion in
  `docs/THE_MASTER_LIST.md`); pins changed without a fresh measured run at
  the amended tip; perturbation not demonstrated; any test weakened; or any
  stale-record retirement executed before this PR integrates.

Amendment content declared before writing:

1. **Wave-4/5 integrations** (each through independent adversarial review
   with pinned-head merge): PR #61 `fleet-task-abandon-01` (ABANDONED-state
   task retire op, 26 switch-sites coherent, claim_abandon without session
   revocation); PR #62 `fleet-evidence-hygiene-01` (evidence_log_guard +
   pre-commit stanza); PR #63 `fleet-slot-expansion-03` (on-demand slots:
   auto-spawn, supervisor spawn/retire, high-water persistence, SLOT_MAX
   fuse; gen-2 after delta review findings — kind echo, high-water persistence,
   preserved-provision retire gate, retained-run figures); PR #64
   `dyad-retained-reviews-01` (retained-review discipline for dyad lanes);
   PR #65 `studio-grid-depth-01` (Studio grid depth-tested in-scene with
   stencil occlusion, D32FS migration; APPROVE_WITH_FOLLOWUPS — splat-view
   doc declaration + accepted-pair manifests recorded to the followup
   backlog).
2. **On-demand-slots transition record**: deployment chain slot-binding
   `d012b4b1` → review-handoff `2c8fb069` → transport-limit `c1a1ec5a` →
   client-instance `5199d9c3` → slot-expansion `e1e0ab98` (live), each
   through the controlled transition (backup → fingerprint → quiescence →
   stop-old → start-new → ALL-EQUAL); slot registry high-water 11; live
   firsts — supervisor retire (slot 11, rev 757), supervisor spawn (slot 12,
   rev 770), retire busy-gate refusing a claimed-but-unprovisioned slot
   (slot 10, rev ~754-757 era).
3. **Dead-code regression discovery** (found LIVE by
   `instance-plane-live-smoke-01`, feedback `c4212657`, claim refusal
   `no_free_slot` at rev 767): `ReviewHandoffControl._dispatch` intercepts
   `claim` unconditionally and `_claim_with_detached_review_capacity` omits
   three base-claim behaviors — F1 auto-spawn (the PR #63 plane is dead
   code in production), F2 `owner_instance` binding (the instance fence
   never binds; header-less twin succeeds where it must refuse), F3 the
   enforced-mode `instance_binding_required` guard. Fix lane
   `fleet-review-handoff-claim-delegation-01` created rev 772; disposition
   PENDING integration; deployment transition to follow as a separate
   controlled procedure.
4. **Worker-03 boundary-violation disposition** (feedback `621d39fb`): prep
   written to the operator checkout `E:\PythonChimera\.tmp\` during
   `engine-feature-resource-lifetime-01`; relocated to
   `E:\ChimeraWork\preservations\feature-lifetime-prep-20260911\`; violation
   recorded; remediation confirmed in the worker's holding report (operator
   checkout writes ceased; all future work under `E:\ChimeraWork\` or
   `%TEMP%`).
5. **Stale-READY dispositions** (retire as supervisor `task_abandon` ops
   with these dispositions as evidence, ONLY after integration):
   `fleet-run-queue-01` superseded (work preserved on the run-queue lanes
   under `E:\ChimeraWork\run-queue-*`, branches preserved; record never
   claimed, stale base); `fleet-orient-continuation-01` CLOSED via the
   authorized yield–recover handoff (successor `-02` integrated as PR #59);
   `engine-vulkan-cleanup-01` superseded by `-02` (unclaimable by
   construction; `-02` integrated as PR #58); `window-capture-ownership-01`
   preserved + superseded (operator-authorized reset preserved the branch/
   evidence at `preservations/slot-02-window-capture-reset-20260910`;
   successor work integrated — bounded contract + synthetic falsifier 2/2);
   `fleet-controller-upgrade-01` realized as the deployment pipeline itself
   (five controlled transitions evidenced; no single code task remains);
   `fleet-slot-expansion-01` and `-02` superseded by `-03` (PR #63).
6. **Catalogue repin** to the builder output measured at this amended head
   (same PR; perturbation control retained under
   `docs/evidence/agent_fleet/MAINTENANCE_AMENDMENT_02/`).

Provision anomaly lesson (from `catalogue-packet-batch-01`, recorded):
a lead provision once left a slot with HEAD==base but an empty index and a
stale `index.lock`; provisioning procedure now verifies `git status` reads
a real index (ls-files non-zero) in addition to HEAD and clean status.
