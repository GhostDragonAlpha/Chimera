# DS-STATE-INTEGRITY-01 recovered handoff and bounded review

Status: COMPLETE_REPORTED; uncommitted/unpublished deliverables require review.
The user recovered the handoff after the window disappeared. No work-loss or
process-failure claim follows from that UI event.

Reported: 18 state-path items, invariants I1-I10, 26 trace controls
(12 VALID / 13 VIOLATION / 1 INSUFFICIENT_EVIDENCE), five detected checker
fault injections, and real-evidence I9 INSUFFICIENT_EVIDENCE.
These were not independently rerun by ASTRA; local Windows files were not read.

## Source/history checks actually performed

Inspected source: bf0a62162008c8415b88091c671ac180dbb50193.

1. git merge-base --is-ancestor 7aba0ee72008897e188057eee81ecfa64d41d1bc
   bf0a62162008c8415b88091c671ac180dbb50193 returned 0.
   A normal fast-forward from those endpoints is possible. This does not prove
   which Git command somebody used, but the report does not establish a history
   rewrite. A local tracking-ref message alone does not prove a forbidden remote
   force-push. Preserve uncertainty rather than recording a policy breach.

2. tools/membrane_gpu_probe/probe.cpp::stale_fixture calls run_case with
   changed_pos, then separately evaluates the changed geometry freshly.
   In run_case's changed_pos branch, stage 0 is submitted and fence-waited;
   the same mapped position buffer is then changed; stages 1 and 2 run using
   retained stage-0 outputs without another face evaluation. The outputs are
   compared with the fresh run across faces, vertex forces, validity and energy.
   Therefore the blanket F5 assertion that no stale buffer is reused contradicts
   this inspected implementation. This is source review, not a new Vulkan rerun.
   It establishes the intentional stale-intermediate sequence, not certification
   of all possible production stale-frame or synchronization faults.

## Findings still to review

Applied acknowledgement is not by itself draw/completion identity; coordinate
precision and presentation transforms need distinct state/hash bindings.
Review I9 against the latest runtime source and exact captured sidecars when
GLM's crash task reaches its verification checkpoint. The bf0a6216 probe
does not by itself describe GLM's newly reported runtime implementation.
The reported creature-lane readback lifetime finding needs its full source path,
lifetime reasoning and teardown trace before repair or attribution to the crash.

No engine access, GPU execution, production source edit, task reassignment or
milestone acceptance occurred in this review.
