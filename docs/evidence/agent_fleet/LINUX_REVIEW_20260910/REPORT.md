# ASTRA independent Linux fleet review

Inspected source: **cf27528166b7df1e20ddf474396624c8bf7f63a3**.
Scope: isolated Linux source review and executed temporary-database/loopback tests. This review does not inspect Alan's current Windows processes, live registry, unpublished patches, or the five workers' progress. No production implementation, live fleet state, integration branch, or protected build path was changed.

## Outcome

The source's existing suite runs **64/66 PASS on Linux**. The two failures concern Windows-specific service stop/restart, not SQL transaction tests. Six targeted scheduler reproductions independently confirm **five correctness/policy problems plus one passing capacity control**. The HTTP probe confirms an additional malformed-input response defect. These results qualify the scope of previously reported happy-path coverage; they do not erase the successful Windows trials.

**Prioritize reservation ownership and acquisition ordering before broadening scheduler guarantees.** A grouped request can replace another task's retained engine reservation. Separate GPU and memory requests can leave two tasks indefinitely waiting on each other until a client or supervisor intervenes. Neither behavior requires a real GPU to reproduce.

## Executed findings and recommended dispositions

| ID | Finding | Evidence / consequence | Recommended disposition |
|---|---|---|---|
| R1 | Retained engine reservation overwritten | A grouped GPU+engine grant, GPU-only release, then B grouped grant replaces A's engine owner without its drain. Control-plane observation; no real overlapping engines launched. | Enforce chained release dependencies and reject replacement of another holder across both admission APIs. |
| R2 | Split acquisition hold-and-wait | A holds GPU, B all declared RAM; each requests the other's held resource and promotions cannot advance. Explicit release/revoke can recover. | Enforce complete resource bundles, acquisition order or another demonstrated deadlock-prevention rule; do not claim atomic groups alone solve incremental requests. |
| R3 | Stale memory snapshot | Final 1024 MB release leaves admitted_mb=1024 while actual holds total zero. Admission still recomputes from holds. | Recompute/cross-check the summary on every release/clear and expose invariant failure. This is not demonstrated over-allocation. |
| R4 | FIFO claim differs from grouped behavior | A later GPU-only request passes an older GPU+memory request blocked on memory. | Choose and document strict FIFO versus earliest-eligible scheduling with starvation protection. Work-conserving bypass may be desirable; code, tests and claims must agree. |
| R5 | In-place benchmark downgrade | Same task replaces benchmark reservation class with functionality without drain evidence. | Require explicit lifecycle transition or release/reacquire, retaining reservation provenance. No physical overlap measured. |
| T1 | Malformed resource disconnect | Missing/numeric resource name raises AttributeError; HTTP closes instead of returning named refusal. State unchanged and next snapshot succeeds. | Validate field type at boundary and return named rejection; do not mislabel as total service failure. |
| L1 | Linux lifecycle unsupported | Windows netstat parsing/taskkill path prevents two stop/restart tests from succeeding here. | Add an owned-process Linux backend with process identity and drain tests. Keep Windows behavior intact. |

Full line references and preconditions are in [resource review](resources/REPORT.md) and [transport/baseline review](transport/REPORT.md).

## Independent execution

Python 3.12.14, Linux. No NumPy, GPU, engine or Windows dependency is required for the targeted controller cases. The positive memory control admits exactly the declared budget, queues the extra byte-count unit (1 MB), and auto-promotes that same request on release. It establishes that basic declared-capacity admission works in this case.

The reproduction suite deliberately asserts the observed defective behavior. Its `OK` output means **the defect was reproduced**, not that the desired safety gate passed. On a future fixed source, these reproductions should cease matching; repair regression assertions should instead express the intended invariant.

From a checkout of the reviewed revision with this evidence package applied, run:

```sh
PYTHONPATH=tools/agent_fleet python3 docs/evidence/agent_fleet/LINUX_REVIEW_20260910/resources/reproduce.py
PYTHONPATH=tools/agent_fleet python3 docs/evidence/agent_fleet/LINUX_REVIEW_20260910/transport/reproduce.py
python3 -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v
```

The full suite starts isolated child services. Its Windows stop adapter fails on Linux, including in teardown; use an isolated execution environment with reliable child cleanup for that baseline. Targeted reproducers close their own ephemeral resources. No remaining service.py process was observed in this sandbox after execution. Do not run these probes against a live registry.

`SOURCE_MANIFEST.json` records exact hashes of all 18 fleet Python modules. `baseline_git.txt` is the real-Git baseline. `baseline.txt` preserves the first archive-only run: 63/66, including an extra Git-index assertion failure caused by the archive lacking Git metadata. A sparse Git checkout at the same revision removed that instrument failure. Sources and tolerances were unchanged.

`resources/results.txt` records the original legacy-acquisition case; `results_stronger.txt` records the strengthened grouped-only case. `packaged_rerun.txt` confirms the final reproducer also executes after relocation into the repository evidence layout. Transport has its own packaged rerun. Preregistrations predate their corresponding experiments.

## Reviews not executed

Two parallel review workers were stopped by automatic cybersecurity screening before executing ownership/publication counterexamples. The block was a generic possible-cybersecurity-risk classification, not a source finding. No attempt was made to bypass it. Their pre-run plans are retained under `ownership/` and `publication/`; **none of those predictions is an executed result**.

Source-only leads for an authorized reviewer: separate enrolled identity strings from privileged role tags; bind publication to immutable validated Git objects rather than mutable tracking references; verify provisioned repository/common-directory identity and recovered slot metadata. These require further review and/or execution. Do not infer a proven privilege escalation or a demonstrated incorrect remote push from this packet.

## Local lead handoff

1. Check whether these exact modules still match the reviewed source before applying findings to a newer checkout.
2. Reproduce R1/R2 first in a temporary registry, implement their invariants in the existing scheduler, and rerun the original plus new regression gates.
3. Resolve R4 as an explicit scheduling policy decision rather than silently teaching tests to accept existing behavior.
4. Repair R3/R5/T1 with bounded regressions. Treat Linux lifecycle work as its own platform increment.
5. Review the unexecuted identity/publication leads without treating this packet as acceptance or deployed repair.

This branch contains evidence only. Integration and any live migration remain with the authorized local lead. No worker should stop or take over another task merely because this report exists.
