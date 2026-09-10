# Bounded resource scheduler review — cf275281

Command: `python review/resources/reproduce.py`. Six isolated fresh-SQLite public-API cases complete successfully (assertions confirm five defects plus one positive control). No production code changes, live services, Git actions, runtime processes, or external side effects. Full evidence: results.txt and strengthened results_stronger.txt. These are control-plane observations; actual process contention is not tested.

## Findings

1. **High: existing engine_demo ownership overwritten without its drainage.** `control.py:186-188` checks only GPU dependency and `208-210` unconditionally replaces every non-memory resource. In strengthened case A receives GPU+engine_demo, then releases GPU. Release at `401` guards dyad_eye only, so engine_demo remains A's. B receives GPU+engine_demo and engine_demo changes to B without release/clear of A's engine_demo. Both owners could consequently have been authorized for exclusive runtime work, and A can no longer release its recorded hold. Preserve existing holders and validate dependencies across grant and release paths before rollout. This is reachable using grouped requests alone, not dependent on legacy unchained acquisition. No physical runtime was launched.

2. **Medium: promised strict same-resource FIFO is false under grouped contention.** `control.py:217-225` iterates past a stalled earlier request without reserving its wanted names against later requests. With 1024 MB held by A, B's GPU+1024 MB request stalls, then C's GPU-only request grants. Both want GPU. This contradicts `control.py:161-164` and `test_resources.py:19-20`; it does not depend on the conflicting prose phrase “priority-aging” in THE_AGENT_FLEET.md:429. Current FIFO fixture tests only requests stalled on an already-held GPU, so physical exclusivity happens to produce FIFO for that fixture.

3. **Medium: memory accounting becomes stale after final release.** `control.py:402-403` deletes a hold and promotes queues; recomputation exists only in successful grant at `212`. Sole 1024 MB reservation released with no pending grant leaves `memory.admitted_mb=1024` while sum of holds is 0. Admission itself uses actual holds at `194-195`, so this reproduction is a false snapshot total, not proved over-admission. The same source pattern exists in supervisor clear at `409-410` but that variant was not separately executed.

4. **Medium: split acquisitions can form a persistent hold-and-wait cycle.** A holds GPU; B holds the entire 1024 MB budget. A requests 1024 MB; B requests GPU. Both remain unserved after two explicit promotions (`resource_revoke_pending` from uninvolved C). Sources `173-197` refuse each request due to the other's retained resource; `412-422` accepts new requests while existing holds remain. Group atomicity alone is not deadlock freedom. Explicit release/revoke can recover; this is not an irreversible database deadlock. The unconditional deadlock-free statement in test_resources.py:13 is unsupported by its fixture suite.

5. **Low/medium: benchmark class can be changed without drainage.** A receives benchmark GPU, then requests functionality GPU. `control.py:173` treats same-task ownership as unblocked; benchmark guard at `175-179` applies only when the new request is benchmark. Grant at `208-210` replaces class with gpu_functionality without resource_release evidence. This proves loss of reservation-class provenance while a benchmark may remain in flight; no cross-task physical GPU overlap was demonstrated by this case.

## Positive result and limitations

Exact capacity works: A's 1024 MB allocation causes B's additional 1 MB request to remain pending; release auto-promotes B and records 1 MB. Thus this review did not find numeric over-budget admission of declared memory. Unknown memory is intentionally uncharged in the existing contract and is not presented as a newly discovered defect.

Existing memory fixture test_resources.py:180-184 re-requests 3000 MB after release has already auto-promoted its old request, resulting in two separate reservations; it only asserts the new response. It misses both auto-promotion identity and accurate final accounting. The new positive control inspects the original request id.

Preread limitations: supplied snapshot includes AGENTS.md, AGENT_START.md, THE_AGENT_FLEET.md and fleet sources/tests; AGENTS-referenced law, manual, compiler, onboarding, and triangle documents are absent. Original code preserved; review outputs are the only files written by this agent.
