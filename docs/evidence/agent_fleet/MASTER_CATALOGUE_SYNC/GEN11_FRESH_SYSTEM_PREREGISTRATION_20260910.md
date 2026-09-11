# GEN-11 FRESH-SYSTEM VERIFICATION — PREREGISTRATION (Rule 0, before the run)

- Task: `master-catalogue-sync-01` · generation **11** · owner `glm53-fresh-01` · slot `2`
- Branch: `astra/tasks/master-catalogue-sync-01` at head `1dd7736752ac6478d9b1d10ffa119971ba27c153`
  (local == `origin/astra/tasks/master-catalogue-sync-01` == controller slot-2 `worktree_head`; tree clean)
- Context: gen-7 review (rev 416) requeued by the lead (rev 429); owner buffy-02 revoked by the
  operator (rev 433); task recovered by the supervisor (rev 434, "returned for fresh-system
  testing"); claimed fresh by `glm53-fresh-01` (rev 442). This round re-verifies the preserved
  deliverable on the fresh system; it adds no new feature scope.

## STATEMENT

The committed gen-7 deliverable is complete and transport-reproducible **on this fresh system**:
its isolated-registry test suite passes unmodified, and the payload builder reproduces, from the
current canonical sources, a payload that passes `validate_payload` with the recorded coverage
counters (240 cards / 40 domains / 65 master-row IDs / 68 observations / 3 unresolved /
271 unkeyed requirements / exhaustive 2,430-line partition) pinned to the recorded source hashes
(Master `f389f913…`, catalog `d9bb4419…`).

## PREDICTION

(a) `python -m pytest . -q` inside `E:/ChimeraWork/slot-02/tools/agent_fleet` passes with the
counts recorded at gen-5/7 (106 passed, 1 skipped) or the current head's own recorded counts.
(b) `python tools/agent_fleet/master_catalogue.py --out <scratch>` builds a payload from the
CURRENT sources whose `validate_payload` returns no refusals and whose coverage counters match
the recorded values. (c) If the rebuilt digest differs from the gen-7 recorded digest, the
difference is exactly explained by a source-hash difference (the Master or roadmap JSON changed
since the gen-7 spine); otherwise the digest matches. (d) No run writes outside the declared task
scopes, touches the live registry `E:/ChimeraWork/control/state.sqlite`, or modifies
`ChimeraEngine/engine/build/`.

## FALSIFIER

Any test failure or error; any `validate_payload` refusal on the rebuilt real-source payload; any
coverage counter differing from the recorded values without an exact source-hash explanation; any
write outside the declared scopes or against the live registry; any modification (non-append) of
committed evidence. A falsified prediction is recorded as failed-run history and re-verified after
correction; no tolerance, scope or fixture is widened to pass.
