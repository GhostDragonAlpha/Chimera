# PR11 Windows lead integration review

Task fleet-resource-fixes-20260910, slot 1, generation 1, lead epoch 2.
Original candidate 8bf8f6436702475ae227b7d55c6ec5ce8541a0c8; reconciled head
4e7d074f9360f87afd67bfba27f444184f936616 incorporates integration base
99e7cc9c764c6d1227da0ce7a13eafbfcb637b5a without conflicts.

Before the run, the controller task packet registered the prediction that the
78-test Windows suite remains green, executable/test blobs remain identical
to the reviewed candidate, and both the new PR workflow and release_required
documentation survive. Failures, source drift or lost evidence falsify it.

`git diff --exit-code 8bf8f643 HEAD -- tools/agent_fleet` passed. No production
or test changes were introduced in reconciliation. Existing Linux failed
tests and abandoned lifecycle prototype remain evidence, not deployed code.

Independent read-only review of tracked Python grouped-resource callers found
no incompatible shipped caller. five_slot_coordination S3 releases coord-3's
GPU before its contended request, so it remains the unchanged nonholder case.
test_resource_lifecycle explicitly covers terminal release_required results.
Legacy runtime callers acquire GPU before children and release children first.
The generic adapter forwards the response; no general automatic retry loop
was found. External/untracked clients remain uninspected and require validation
before a controlled service deployment. No background/client deployment claim.

Nonblocking review follow-ups: strengthen the existing same-owner assertion
in test_resources to check served/dropped_reason as well as granted; its
older memory test also re-requests after automatic promotion. Neither is a
production change in this patch. Do not broaden this integration to change
resource policy or weaken any test expectation.

Command: `python -B -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v`.
Raw Windows output: suite.txt. Tests operate isolated temporary registries.
The running project controller remains on its original operator-checkout
source; source integration does not install this patch or restart that service.

Result: **78/78 pass**, 73.827 s on Windows, CPython 3.14.3. This includes the
Windows service stop/restart tests that did not pass in the remote Linux
environment. Test teardown stopped its own fixture processes. `git diff
--check` passes; no tracked implementation/test file changed during the run.
