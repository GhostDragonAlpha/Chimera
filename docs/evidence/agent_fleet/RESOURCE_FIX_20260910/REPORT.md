# Resource lifecycle fixes — executed Linux verification

Base: f2c4f7e850267f400ea3eb7441e7c67d7fdc4466, whose production modules equal cf275281. This change follows the independent review in PR #10. No live Windows registry, worker, engine or GPU was contacted.

## Implemented

- Grouped admission never replaces an existing non-memory reservation, including same-owner class changes.
- GPU release and supervisor clear require both DYAD and engine child reservations to be released first.
- A retained foreign child from an older inconsistent registry also blocks a GPU-only grant or legacy acquisition; no automatic clear is attempted.
- Legacy engine acquisition requires the same task's GPU parent. Legacy memory acquisition returns a named instruction to use grouped resource_request.
- Memory totals are recomputed after queue promotions/releases/clears and on reading older persisted state.
- Resource names are type-checked before string operations, yielding named JSON refusals.
- A contended request from a task already retaining resources becomes terminal/ungranted with dropped_reason=release_required. Actual holds remain untouched. The client must drain/release and request the complete bundle. Available extensions still grant immediately; nonholder requests still queue and auto-promote.
- The inaccurate strict-FIFO docstring is corrected. The scheduler still scans in arrival order and can bypass an infeasible group. Priority-weighted fairness/starvation protection is NOT implemented by this patch.

## Verification

Exact final command:

```sh
python3 -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v
```

Result: **78 tests, 76 pass, 2 existing failures**, recorded in final_suite.txt. The failures are the unchanged Windows-specific bootstrap stop/restart tests on Linux. The resource/lifecycle implementation has no new failure in this suite. All **12 new lifecycle regression tests pass**.

The same final 12 tests run against the original source produce **8 failures, 2 errors, 2 passes**, recorded in before_fix_final.txt. That comparison verifies the assertions distinguish the old behavior; the two errors are the original malformed-resource transport failure and legacy-memory raw error. Earlier before_fix.txt records the initial 11-test version. No original test expectations or tolerances were weakened.

Important compatibility change: consumers must inspect served/granted/dropped_reason. A release_required result will never auto-promote. Pending nonholder allocation refusals retain auto-promotion. Existing pre-repair blocked-holder records are terminalized when promotion next runs, without changing physical allocations. This is not an automatic live migration or authorization to restart the operator's controller.

## Linux lifecycle experiment — not integrated

I attempted a procfs/pidfd Linux lifecycle backend after preregistration. Tests exposed a sandbox namespace mismatch: os.getpid() reported 5 while /proc/self identified 879533. Thus direct /proc/<Popen PID> inspection could inspect the wrong process namespace or fail entirely. The prototype was removed from production; its code/diff and failed results are retained under linux_attempt/, full_suite_linux.txt and linux_identity.txt. No blind PID signaling fallback was added. bootstrap_fleet.py is byte-identical to the base.

The existing lifecycle tests fail closed when they cannot establish ownership; they are not converted to skips or PASS. A real Linux backend still needs verification in a matching process/procfs namespace. Windows behavior was not executed here.

Technical basis consulted: Python [pidfd_open](https://docs.python.org/3/library/os.html#os.pidfd_open) and [pidfd_send_signal](https://docs.python.org/3/library/signal.html#signal.pidfd_send_signal), and the Linux kernel [proc filesystem](https://docs.kernel.org/filesystems/proc.html) documentation. Candidate process control was tested only with local fixtures; it is not an engine/window port.

## Scope and remaining work

No physics law, shader, numerical budget or universal prompt changed. No identity/privilege or publication-race implementation was attempted. Unknown memory remains admitted per the existing contract and must not be represented as measured GPU capacity. Work-conserving scheduling still needs an explicit fairness policy and tests. The local lead owns Windows regression, client compatibility review and controlled deployment.

Production write scope: tools/agent_fleet/control.py, new test_resource_lifecycle.py, and append-only documentation. Failed candidate source is evidence only. Parent review evidence is preserved unchanged.
