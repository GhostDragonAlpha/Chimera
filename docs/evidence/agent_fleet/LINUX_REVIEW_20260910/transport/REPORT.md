# HTTP refusal and Linux baseline findings

Reviewed revision: cf27528166b7df1e20ddf474396624c8bf7f63a3. No live Windows state was inspected.

## T1 — malformed resource name closes the request without a named refusal

`control.py:387–388` calls `name.startswith` without first checking that the field is a string. `service.py:33–36` does not catch the resulting AttributeError. Executed missing-name and integer-name requests against a fresh authenticated loopback service: both produced RemoteDisconnected and server AttributeError. A string unknown resource produced the expected JSON refusal. All three left controller revision unchanged; subsequent snapshot requests succeeded. This is a transport-contract defect, **not a service-wide crash or unauthorized state mutation**.

Suggested correction: validate the resource type before string operations and preserve a named refusal. Do not merely blanket-catch programming exceptions and report success.

Reproduce: `python3 review/transport/reproduce.py` in the supplied isolated snapshot layout; see packaging instructions in the top-level report for repository evidence layout.

## L1 — Linux stop/restart is not implemented by the Windows lifecycle adapter

The exact-source suite in a Git checkout ran 66 tests: 64 passed and 2 failed (stop and restart in `test_bootstrap_fleet.py`). `bootstrap_fleet.py:197–214` resolves listeners using Windows netstat columns (`LISTENING`); `:351–389` issues taskkill unconditionally. Here listener lookup returns unavailable, so stop refuses instead of risking a foreign process. Both failures are lifecycle portability limits, not failed SQL claim serialization. Test teardown also calls this unsupported path and can fail to drain its child; a test harness must own and reliably reap test processes even when the production stop routine is under test.

Do not replace the guard with blind PID termination. A Linux backend needs owned process start identity and socket association, then a controlled stop and drain check. No Linux lifecycle fix was applied in this review.

## Preserved first-run instrument limitation

The first baseline used an archive without Git metadata and reported 63/66. The extra failure was `test_untracked_demo_shader_recorded`: a Git-index assertion cannot pass in a plain archive. Repeated the suite in a separate sparse Git checkout at the exact reviewed commit; the shader check passed, yielding the 64/66 result above. Both logs are retained. No production code or test tolerance changed.
